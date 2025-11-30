"""
KURSORIN Engine

Main engine class that orchestrates all tracking modules,
fusion, and cursor control.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

import cv2
import numpy as np
from loguru import logger

from kursorin.config import KursorinConfig
from kursorin.constants import TrackingState, TrackingMode, ClickType
from kursorin.exceptions import (
    KursorinError,
    CameraError,
    CameraNotFoundError,
    NoValidModalityError,
)
# These imports will work once the modules are implemented in subsequent phases
from kursorin.trackers import HeadTracker, EyeTracker, HandTracker, TrackerResult
from kursorin.fusion import FusionModule, CursorSmoother
from kursorin.core.cursor_controller import CursorController
from kursorin.core.click_detector import ClickDetector
from kursorin.utils.camera_manager import CameraManager
from kursorin.utils.performance_monitor import PerformanceMonitor


@dataclass
class FrameResult:
    """Result of processing a single frame."""
    
    timestamp: float
    cursor_position: Optional[Tuple[float, float]]
    click_event: Optional[ClickType]
    head_result: Optional[TrackerResult]
    eye_result: Optional[TrackerResult]
    hand_result: Optional[TrackerResult]
    processing_time_ms: float
    frame: Optional[np.ndarray] = None
    
    @property
    def valid(self) -> bool:
        """Check if frame processing produced a valid result."""
        return self.cursor_position is not None


class KursorinEngine:
    """
    Main KURSORIN engine class.
    
    Coordinates all tracking modules, fusion, and cursor control
    to provide hands-free computer interaction.
    
    Attributes:
        config: Configuration settings
        is_running: Whether the engine is currently running
        state: Current tracking state
        
    Example:
        >>> from kursorin import Kursorin
        >>> engine = Kursorin()
        >>> engine.start()
        >>> # ... run until done ...
        >>> engine.stop()
    """
    
    def __init__(self, config: Optional[KursorinConfig] = None):
        """
        Initialize the KURSORIN engine.
        
        Args:
            config: Configuration settings. Uses defaults if None.
        """
        self.config = config or KursorinConfig()
        
        # State management
        self._state = TrackingState.IDLE
        self._is_running = False
        self._is_paused = False
        self._lock = threading.RLock()
        
        # Initialize components
        self._camera: Optional[CameraManager] = None
        self._head_tracker: Optional[HeadTracker] = None
        self._eye_tracker: Optional[EyeTracker] = None
        self._hand_tracker: Optional[HandTracker] = None
        self._fusion: Optional[FusionModule] = None
        self._smoother: Optional[CursorSmoother] = None
        self._cursor_controller: Optional[CursorController] = None
        self._click_detector: Optional[ClickDetector] = None
        self._performance_monitor: Optional[PerformanceMonitor] = None
        
        # Processing thread
        self._processing_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Callbacks
        self._frame_callbacks: List[Callable[[FrameResult], None]] = []
        self._state_callbacks: List[Callable[[TrackingState], None]] = []
        self._error_callbacks: List[Callable[[Exception], None]] = []
        
        # Statistics
        self._frame_count = 0
        self._start_time = 0.0
        
        logger.info("KURSORIN engine initialized")
    
    @property
    def state(self) -> TrackingState:
        """Get current tracking state."""
        return self._state
    
    @state.setter
    def state(self, value: TrackingState):
        """Set tracking state and notify callbacks."""
        if self._state != value:
            old_state = self._state
            self._state = value
            logger.debug(f"State changed: {old_state.name} -> {value.name}")
            for callback in self._state_callbacks:
                try:
                    callback(value)
                except Exception as e:
                    logger.error(f"Error in state callback: {e}")
    
    @property
    def is_running(self) -> bool:
        """Check if engine is running."""
        return self._is_running
    
    @property
    def is_paused(self) -> bool:
        """Check if tracking is paused."""
        return self._is_paused
    
    @property
    def fps(self) -> float:
        """Get current frames per second."""
        if self._performance_monitor:
            return self._performance_monitor.fps
        return 0.0
    
    @property
    def latency_ms(self) -> float:
        """Get current processing latency in milliseconds."""
        if self._performance_monitor:
            return self._performance_monitor.avg_latency_ms
        return 0.0
    
    def initialize(self) -> None:
        """
        Initialize all components.
        
        Raises:
            CameraError: If camera initialization fails
            KursorinError: If component initialization fails
        """
        logger.info("Initializing KURSORIN components...")
        
        with self._lock:
            try:
                # Initialize camera
                self._camera = CameraManager(
                    camera_index=self.config.camera.camera_index,
                    width=self.config.camera.camera_width,
                    height=self.config.camera.camera_height,
                    fps=self.config.camera.target_fps,
                )
                self._camera.open()
                logger.info(f"Camera initialized: {self._camera.width}x{self._camera.height} @ {self._camera.fps}fps")
                
                # Initialize trackers
                if self.config.tracking.head_enabled:
                    self._head_tracker = HeadTracker(self.config)
                    logger.info("Head tracker initialized")
                
                if self.config.tracking.eye_enabled:
                    self._eye_tracker = EyeTracker(self.config)
                    logger.info("Eye tracker initialized")
                
                if self.config.tracking.hand_enabled:
                    self._hand_tracker = HandTracker(self.config)
                    logger.info("Hand tracker initialized")
                
                # Initialize fusion
                self._fusion = FusionModule(self.config)
                logger.info("Fusion module initialized")
                
                # Initialize smoother
                self._smoother = CursorSmoother(self.config)
                logger.info("Cursor smoother initialized")
                
                # Initialize cursor controller
                self._cursor_controller = CursorController(self.config)
                logger.info("Cursor controller initialized")
                
                # Initialize click detector
                self._click_detector = ClickDetector(self.config)
                logger.info("Click detector initialized")
                
                # Initialize performance monitor
                self._performance_monitor = PerformanceMonitor()
                logger.info("Performance monitor initialized")
                
                self.state = TrackingState.IDLE
                logger.info("KURSORIN components initialized successfully")
                
            except CameraNotFoundError:
                raise
            except Exception as e:
                logger.exception("Failed to initialize components")
                raise KursorinError(f"Initialization failed: {e}")
    
    def start(self) -> None:
        """
        Start the tracking engine.
        
        Raises:
            KursorinError: If starting fails
        """
        if self._is_running:
            logger.warning("Engine already running")
            return
        
        logger.info("Starting KURSORIN engine...")
        
        # Initialize if not already done
        if self._camera is None:
            self.initialize()
        
        self._is_running = True
        self._is_paused = False
        self._stop_event.clear()
        self._frame_count = 0
        self._start_time = time.time()
        
        # Start processing thread
        self._processing_thread = threading.Thread(
            target=self._processing_loop,
            name="KursorinProcessing",
            daemon=True,
        )
        self._processing_thread.start()
        
        self.state = TrackingState.TRACKING
        logger.info("KURSORIN engine started")
    
    def stop(self) -> None:
        """Stop the tracking engine."""
        if not self._is_running:
            return
        
        logger.info("Stopping KURSORIN engine...")
        
        self._is_running = False
        self._stop_event.set()
        
        # Wait for processing thread to finish
        if self._processing_thread and self._processing_thread.is_alive():
            self._processing_thread.join(timeout=2.0)
        
        # Release resources
        self._cleanup()
        
        self.state = TrackingState.IDLE
        logger.info("KURSORIN engine stopped")
    
    def pause(self) -> None:
        """Pause tracking without stopping."""
        if not self._is_running:
            return
        
        self._is_paused = True
        self.state = TrackingState.PAUSED
        logger.info("Tracking paused")
    
    def resume(self) -> None:
        """Resume tracking from pause."""
        if not self._is_running:
            return
        
        self._is_paused = False
        self.state = TrackingState.TRACKING
        logger.info("Tracking resumed")
    
    def toggle_pause(self) -> bool:
        """Toggle pause state. Returns new paused state."""
        if self._is_paused:
            self.resume()
        else:
            self.pause()
        return self._is_paused
    
    def _processing_loop(self) -> None:
        """Main processing loop running in separate thread."""
        logger.debug("Processing loop started")
        
        # Camera warmup
        warmup_frames = self.config.camera.warmup_frames
        for _ in range(warmup_frames):
            if self._stop_event.is_set():
                break
            self._camera.read()
        
        while not self._stop_event.is_set():
            try:
                # Process frame
                result = self._process_frame()
                
                if result and result.valid:
                    # Update cursor position
                    if not self._is_paused:
                        self._cursor_controller.move_to(result.cursor_position)
                    
                    # Handle click events
                    if result.click_event and result.click_event != ClickType.NONE:
                        if not self._is_paused:
                            self._cursor_controller.click(result.click_event)
                
                # Notify callbacks
                for callback in self._frame_callbacks:
                    try:
                        callback(result)
                    except Exception as e:
                        logger.error(f"Error in frame callback: {e}")
                
                # Frame rate limiting
                self._performance_monitor.frame_complete()
                
            except Exception as e:
                logger.exception("Error in processing loop")
                self._handle_error(e)
        
        logger.debug("Processing loop ended")
    
    def _process_frame(self) -> Optional[FrameResult]:
        """Process a single frame and return result."""
        start_time = time.time()
        
        # Read frame from camera
        frame = self._camera.read()
        if frame is None:
            return None
        
        # Flip frame if configured (mirror mode)
        if self.config.camera.flip_horizontal:
            frame = cv2.flip(frame, 1)
        
        self._frame_count += 1
        timestamp = time.time()
        
        # Process with each tracker
        head_result = None
        eye_result = None
        hand_result = None
        
        if self._head_tracker and not self._is_paused:
            head_result = self._head_tracker.process(frame)
        
        if self._eye_tracker and not self._is_paused:
            eye_result = self._eye_tracker.process(frame)
        
        if self._hand_tracker and not self._is_paused:
            hand_result = self._hand_tracker.process(frame)
        
        # Fuse results
        cursor_position = None
        if not self._is_paused:
            try:
                cursor_position = self._fusion.fuse(
                    head_result,
                    eye_result,
                    hand_result,
                )
                
                # Apply smoothing
                if cursor_position is not None:
                    cursor_position = self._smoother.smooth(cursor_position)
                    
            except NoValidModalityError:
                # No valid tracking data, keep cursor stationary
                pass
        
        # Detect clicks
        click_event = None
        if not self._is_paused:
            click_event = self._click_detector.detect(
                eye_result,
                hand_result,
                cursor_position,
            )
        
        processing_time_ms = (time.time() - start_time) * 1000
        self._performance_monitor.record_latency(processing_time_ms)
        
        return FrameResult(
            timestamp=timestamp,
            cursor_position=cursor_position,
            click_event=click_event,
            head_result=head_result,
            eye_result=eye_result,
            hand_result=hand_result,
            processing_time_ms=processing_time_ms,
            frame=frame if self.config.ui.show_preview else None,
        )
    
    def _handle_error(self, error: Exception) -> None:
        """Handle errors during processing."""
        self.state = TrackingState.ERROR
        
        for callback in self._error_callbacks:
            try:
                callback(error)
            except Exception as e:
                logger.error(f"Error in error callback: {e}")
        
        # Attempt recovery for certain errors
        if isinstance(error, CameraError):
            logger.warning("Attempting camera recovery...")
            try:
                self._camera.close()
                time.sleep(0.5)
                self._camera.open()
                self.state = TrackingState.TRACKING
                logger.info("Camera recovered")
            except Exception:
                logger.error("Camera recovery failed")
    
    def _cleanup(self) -> None:
        """Clean up resources."""
        with self._lock:
            if self._camera:
                self._camera.close()
                self._camera = None
            
            if self._head_tracker:
                self._head_tracker.close()
                self._head_tracker = None
            
            if self._eye_tracker:
                self._eye_tracker.close()
                self._eye_tracker = None
            
            if self._hand_tracker:
                self._hand_tracker.close()
                self._hand_tracker = None
    
    # =========================================================================
    # Callback Registration
    # =========================================================================
    
    def on_frame(self, callback: Callable[[FrameResult], None]) -> None:
        """Register callback for frame processing results."""
        self._frame_callbacks.append(callback)
    
    def on_state_change(self, callback: Callable[[TrackingState], None]) -> None:
        """Register callback for state changes."""
        self._state_callbacks.append(callback)
    
    def on_error(self, callback: Callable[[Exception], None]) -> None:
        """Register callback for error handling."""
        self._error_callbacks.append(callback)
    
    def remove_callback(self, callback: Callable) -> bool:
        """Remove a registered callback."""
        for callback_list in [
            self._frame_callbacks,
            self._state_callbacks,
            self._error_callbacks,
        ]:
            if callback in callback_list:
                callback_list.remove(callback)
                return True
        return False
