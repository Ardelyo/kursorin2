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
import pyautogui

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
import os
import json
from loguru import logger

try:
    from pynput import keyboard
    HAS_PYNPUT = True
except ImportError:
    HAS_PYNPUT = False

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
from kursorin.core.calibration_model import CalibrationModel
from kursorin.utils.camera_manager import CameraManager
from kursorin.utils.performance_monitor import PerformanceMonitor
from kursorin.utils.platform_utils import is_admin, is_windows


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
        
        # Optimization caches
        self._brightness_counter = 0
        self._cached_alpha = 1.0
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
        self._calibration_model: Optional[CalibrationModel] = None
        
        # Shared FaceMesh for performance
        self.shared_face_mesh = None
        
        # Cache for calibration
        self._latest_eye_result: Optional[TrackerResult] = None
        
        # Processing thread
        self._processing_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._hotkey_listener = None
        
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
        pm = self._performance_monitor
        if pm is not None:
            return pm.fps
        return 0.0
    
    @property
    def latency_ms(self) -> float:
        """Get current processing latency in milliseconds."""
        pm = self._performance_monitor
        if pm is not None:
            return pm.avg_latency_ms
        return 0.0

    @property
    def is_admin(self) -> bool:
        """Check if the engine is running with admin privileges."""
        return is_admin()

    @property
    def is_windows(self) -> bool:
        """Check if the engine is running on Windows."""
        return is_windows()
    
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
                camera = CameraManager(
                    camera_index=self.config.camera.camera_index,
                    width=self.config.camera.camera_width,
                    height=self.config.camera.camera_height,
                    fps=self.config.camera.target_fps,
                )
                self._camera = camera
                camera.open()
                logger.info(f"Camera initialized: {camera.width}x{camera.height} @ {camera.fps}fps")
                
                # Initialize shared FaceLandmarker (replacement for FaceMesh)
                model_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)), 
                    "assets", "models", "face_landmarker.task"
                )
                
                if not os.path.exists(model_path):
                    logger.warning(f"Model file not found at {model_path}. Starting fallback download...")
                    # TODO: Robust downloader, but for now we expect it to exist since we just downloaded it
                
                base_options = mp_python.BaseOptions(model_asset_path=model_path)
                options = mp_vision.FaceLandmarkerOptions(
                    base_options=base_options,
                    running_mode=mp_vision.RunningMode.VIDEO,
                    num_faces=1,
                    min_face_detection_confidence=0.5,
                    min_face_presence_confidence=0.5,
                    min_tracking_confidence=0.5,
                    output_face_blendshapes=True,
                    output_facial_transformation_matrixes=True,
                )
                self.shared_face_mesh = mp_vision.FaceLandmarker.create_from_options(options)
                logger.info("Shared FaceLandmarker initialized (Tasks API)")
                
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
                
                # Initialize fusion and smoother
                self._fusion = FusionModule(self.config)
                self._smoother = CursorSmoother(self.config)
                
                # Initialize controllers and detectors
                self._cursor_controller = CursorController(self.config)
                self._click_detector = ClickDetector(self.config)
                self._performance_monitor = PerformanceMonitor()
                
                # Initialize calibration
                self._calibration_model = CalibrationModel()
                self.load_calibration()
                
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
        thread = threading.Thread(
            target=self._processing_loop,
            name="KursorinProcessing",
            daemon=True,
        )
        self._processing_thread = thread
        thread.start()
        
        # Setup Panic Key (Global Hotkey)
        if HAS_PYNPUT:
            def on_panic():
                logger.warning("Panic Key triggered! Stopping KURSORIN...")
                # We use threading.Thread to avoid blocking the hotkey listener thread itself
                threading.Thread(target=self.stop, daemon=True).start()
                
            self._hotkey_listener = keyboard.GlobalHotKeys({'<ctrl>+q': on_panic})
            self._hotkey_listener.start()
            logger.info("Global Panic Key (Ctrl+Q) registered")
        
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
        thread = self._processing_thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=2.0)
        
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

    def start_calibration(self) -> None:
        """Enter calibration mode."""
        self.state = TrackingState.CALIBRATING
        logger.info("Started calibration")

    def stop_calibration(self) -> None:
        """Exit calibration mode and compute matrix."""
        calib = self._calibration_model
        if calib:
            success = calib.compute()
            if success:
                logger.info("Calibration computed successfully")
            else:
                logger.warning("Calibration computation failed or lacked points")
        
        self.state = TrackingState.TRACKING
        logger.info("Stopped calibration")

    def record_calibration_point(self, x: float, y: float) -> None:
        """
        Record data for a calibration point.
        
        Args:
            x: Normalized X coordinate (0-1) (Target point on screen)
            y: Normalized Y coordinate (0-1) (Target point on screen)
        """
        if self.state != TrackingState.CALIBRATING:
            logger.warning("Ignored calibration point (not in calibration mode)")
            return
            
        latest_eye = self._latest_eye_result
        if latest_eye is None or not latest_eye.valid:
            logger.warning("No valid eye data available to record calibration point")
            return
            
        # Get raw iris position (before any calibration mapping)
        # Note: In _process_frame we mapped eye_result.position if calibrated,
        # but the original raw values are in the metadata.
        # Let's ensure we use the metadata gaze values for calibration source
        assert latest_eye is not None
        metadata = latest_eye.metadata
        if metadata is None:
            logger.warning("Latest eye result missing metadata")
            return
        raw_x = metadata.get("gaze_x", 0.5)
        raw_y = metadata.get("gaze_y", 0.5)
            
        logger.info(f"Recording calibration point: Screen({x:.2f}, {y:.2f}) -> Gaze({raw_x:.2f}, {raw_y:.2f})")
        calib = self._calibration_model
        if calib:
            calib.add_point((raw_x, raw_y), (x, y))
    
    def _processing_loop(self) -> None:
        """Main processing loop running in separate thread."""
        logger.debug("Processing loop started")
        
        camera = self._camera
        if camera is None:
            return
            
        # Camera warmup
        warmup_frames = self.config.camera.warmup_frames
        for _ in range(warmup_frames):
            if self._stop_event.is_set():
                break
            camera.read()
        
        cc = self._cursor_controller
        pm = self._performance_monitor
        
        while not self._stop_event.is_set():
            try:
                # Process frame
                result = self._process_frame()
                
                if result and result.valid:
                    # Update cursor position
                    if not self._is_paused and cc is not None:
                        cc.move_to(result.cursor_position)
                    
                    # Handle click events
                    if result.click_event and result.click_event != ClickType.NONE:
                        if not self._is_paused and cc is not None:
                            evt = result.click_event
                            if evt == ClickType.DRAG_START:
                                cc.mouse_down()
                            elif evt == ClickType.DRAG_END:
                                cc.mouse_up()
                            elif evt == ClickType.SCROLL_UP:
                                cc.scroll(100)  # Scroll up amount
                            elif evt == ClickType.SCROLL_DOWN:
                                cc.scroll(-100) # Scroll down amount
                            else:
                                cc.click(evt)
                
                # Notify callbacks
                if result is not None:
                    for callback in self._frame_callbacks:
                        try:
                            callback(result)
                        except Exception as e:
                            logger.error(f"Error in frame callback: {e}")
                
                # Frame rate limiting
                current_pm = self._performance_monitor
                if current_pm is not None:
                    current_pm.frame_complete()
                
            except pyautogui.FailSafeException:
                logger.warning("Fail-safe triggered (mouse at corner). Stopping KURSORIN...")
                self.stop()
                break
            except Exception as e:
                logger.exception("Error in processing loop")
                self._handle_error(e)
        
        logger.debug("Processing loop ended")
    
    def _process_frame(self) -> Optional[FrameResult]:
        """Process a single frame and return result."""
        start_time = time.time()
        
        camera = self._camera
        if camera is None:
            return None
        
        # Read frame from camera
        frame = camera.read()
        if frame is None:
            return None
        
        # Flip frame if configured (mirror mode)
        if self.config.camera.flip_horizontal:
            frame = cv2.flip(frame, 1)
            
        # [LOW-END OPTIMIZATION] Ultra-lightweight low-light enhancement
        if self.config.camera.auto_exposure:
            self._brightness_counter += 1
            if self._brightness_counter >= 30: # Check roughly every ~1 second
                self._brightness_counter = 0
                # Downsample heavily for near-zero cost brightness checking
                small = cv2.resize(frame, (64, 48))
                gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
                mean_val = gray.mean()
                
                # If room is dark, calculate a boost multiplier
                if mean_val < 70:
                    self._cached_alpha = max(1.0, min(1.8, 70 / max(mean_val, 1)))
                else:
                    self._cached_alpha = 1.0
                    
            # Only apply enhancement (which has CPU cost) if it's genuinely needed
            if self._cached_alpha > 1.0:
                frame = cv2.convertScaleAbs(frame, alpha=self._cached_alpha, beta=10)
        
        self._frame_count += 1
        timestamp = time.time()
        
        # Process shared FaceMesh
        face_mesh_results = None
        face_mesh = self.shared_face_mesh
        if (self._head_tracker or self._eye_tracker) and not self._is_paused and face_mesh is not None:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            timestamp_ms = int(timestamp * 1000)
            face_mesh_results = face_mesh.detect_for_video(mp_image, timestamp_ms)
        
        # Process with each tracker
        head_result = None
        eye_result = None
        hand_result = None
        
        head_tracker = self._head_tracker
        if head_tracker is not None and not self._is_paused:
            head_result = head_tracker.process(frame, face_mesh_results=face_mesh_results)
        
        eye_tracker = self._eye_tracker
        calib = self._calibration_model
        if eye_tracker is not None and not self._is_paused:
            eye_result = eye_tracker.process(frame, face_mesh_results=face_mesh_results)
            self._latest_eye_result = eye_result
            
            # Map eye coordinates using calibration if available
            if eye_result and eye_result.valid and calib is not None and calib.is_calibrated:
                px, py = eye_result.position
                mapped_pos = calib.map((px, py))
                eye_result.position = np.array([mapped_pos[0], mapped_pos[1]])
        
        hand_tracker = self._hand_tracker
        if hand_tracker is not None and not self._is_paused:
            hand_result = hand_tracker.process(frame)
        
        # Fuse results
        cursor_position = None
        fusion = self._fusion
        if fusion is not None and not self._is_paused:
            try:
                cursor_position = fusion.fuse(
                    head_result,
                    eye_result,
                    hand_result,
                )
                
                smoother = self._smoother
                # Apply smoothing
                if cursor_position is not None and smoother is not None:
                    cursor_position = smoother.smooth(cursor_position)
                    
            except NoValidModalityError:
                # No valid tracking data, keep cursor stationary
                pass
        
        # Detect clicks
        click_event = None
        cd = self._click_detector
        if cd is not None and not self._is_paused:
            click_event = cd.detect(
                eye_result,
                hand_result,
                cursor_position,
            )
        
        processing_time_ms = (time.time() - start_time) * 1000
        pm = self._performance_monitor
        if pm is not None:
            pm.record_latency(processing_time_ms)
        
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
            camera = self._camera
            if camera is not None:
                try:
                    camera.close()
                    time.sleep(0.5)
                    camera.open()
                    self.state = TrackingState.TRACKING
                    logger.info("Camera recovered")
                except Exception:
                    logger.error("Camera recovery failed")
    
    def _cleanup(self) -> None:
        """Clean up resources."""
        with self._lock:
            face_mesh = self.shared_face_mesh
            if face_mesh is not None:
                face_mesh.close()
                self.shared_face_mesh = None
                
            camera = self._camera
            if camera is not None:
                camera.close()
                self._camera = None
            
            head_tracker = self._head_tracker
            if head_tracker is not None:
                head_tracker.close()
                self._head_tracker = None
            
            eye_tracker = self._eye_tracker
            if eye_tracker is not None:
                eye_tracker.close()
                self._eye_tracker = None
            
            hand_tracker = self._hand_tracker
            if hand_tracker is not None:
                hand_tracker.close()
                self._hand_tracker = None
                
            if self._hotkey_listener is not None:
                try:
                    self._hotkey_listener.stop()
                except Exception:
                    pass
                self._hotkey_listener = None
    
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
        
    def save_calibration(self, filename: str = "calibration.json") -> bool:
        """Save calibration data to disk."""
        calib = self._calibration_model
        if calib is None:
            return False
        try:
            config_dir = os.path.expanduser("~/.kursorin")
            os.makedirs(config_dir, exist_ok=True)
            filepath = os.path.join(config_dir, filename)
            
            data = calib.to_dict()
            with open(filepath, "w") as f:
                json.dump(data, f)
            logger.info("Calibration saved to disk")
            return True
        except Exception as e:
            logger.error(f"Failed to save calibration: {e}")
            return False
            
    def load_calibration(self, filename: str = "calibration.json") -> bool:
        """Load calibration data from disk."""
        calib = self._calibration_model
        if calib is None:
            return False
        try:
            filepath = os.path.join(os.path.expanduser("~/.kursorin"), filename)
            if not os.path.exists(filepath):
                return False
                
            with open(filepath, "r") as f:
                data = json.load(f)
            
            calib.from_dict(data)
            logger.info("Calibration loaded from disk")
            return True
        except Exception as e:
            logger.error(f"Failed to load calibration: {e}")
            return False
