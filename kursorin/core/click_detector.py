"""
Click Detector

Detects click events from various inputs (Blink, Dwell, Pinch).
"""

import time
from typing import Optional, Tuple
import numpy as np

from kursorin.config import KursorinConfig
from kursorin.constants import ClickType, Gesture
from kursorin.trackers.tracker_result import TrackerResult


class ClickDetector:
    """
    Detects clicks based on configured methods.
    """
    
    def __init__(self, config: KursorinConfig):
        self.config = config
        
        # State for dwell clicking
        self.dwell_start_time: Optional[float] = None
        self.dwell_position = None
        
        # State for blink clicking
        self.blink_start_time: Optional[float] = None
        
        # State for pinch clicking
        self.pinch_start_time: Optional[float] = None
        self.is_pinching = False
        self.pinch_clicked = False
        self.is_dragging = False

        
    def detect(
        self,
        eye_result: Optional[TrackerResult],
        hand_result: Optional[TrackerResult],
        cursor_position: Optional[Tuple[float, float]]
    ) -> ClickType:
        """
        Detect click event from current state.
        """
        click_type = ClickType.NONE
        
        # 1. Blink Click
        if self.config.click.blink_click_enabled and eye_result and eye_result.valid:
            click_type = self._check_blink(eye_result)
            if click_type != ClickType.NONE:
                return click_type
                
        # 2. Pinch Click
        if self.config.click.pinch_click_enabled and hand_result and hand_result.valid:
            click_type = self._check_pinch(hand_result)
            if click_type != ClickType.NONE:
                return click_type
                
        # 3. Dwell Click
        if self.config.click.dwell_click_enabled and cursor_position:
            click_type = self._check_dwell(cursor_position)
            if click_type != ClickType.NONE:
                return click_type

        # 4. Scroll Checks
        if hand_result and hand_result.valid:
            gesture = hand_result.metadata.get("gesture", Gesture.NONE)
            if gesture == Gesture.THUMBS_UP:
                return ClickType.SCROLL_UP
            elif gesture == Gesture.THUMBS_DOWN:
                return ClickType.SCROLL_DOWN
            
        return click_type
        
    def _check_blink(self, result: TrackerResult) -> ClickType:
        """Check for blink click."""
        ear = result.metadata.get("ear", 1.0)
        threshold = self.config.tracking.eye_blink_threshold
        
        if ear < threshold:
            if self.blink_start_time is None:
                self.blink_start_time = time.time()
        else:
            blink_time = self.blink_start_time
            if blink_time is not None:
                duration = time.time() - blink_time
                self.blink_start_time = None
                
                min_dur = self.config.tracking.eye_blink_duration_min
                max_dur = self.config.tracking.eye_blink_duration_max
                
                if min_dur <= duration <= max_dur:
                    return ClickType.LEFT_CLICK
                    
        return ClickType.NONE
        
    def _check_pinch(self, result: TrackerResult) -> ClickType:
        """Check for pinch click using hand gesture. Emits Drag events for long holds."""
        gesture = result.metadata.get("gesture", Gesture.NONE)
        
        if gesture == Gesture.PINCH:
            if not self.is_pinching:
                self.is_pinching = True
                self.pinch_start_time = time.time()
                self.pinch_clicked = False
                self.is_dragging = False
            else:
                pinch_time = self.pinch_start_time
                if pinch_time is not None:
                    duration = time.time() - pinch_time
                    pinch_hold_sec = self.config.click.pinch_hold_time_ms / 1000.0
                    
                    if duration > pinch_hold_sec:
                        if not self.is_dragging:
                            self.is_dragging = True
                            return ClickType.DRAG_START
        else:
            if self.is_pinching:
                # Was pinching, just released
                self.is_pinching = False
                if self.is_dragging:
                    self.is_dragging = False
                    return ClickType.DRAG_END
                elif self.pinch_start_time is not None:
                    # Short pinch = left click
                    pinch_time = self.pinch_start_time
                    assert pinch_time is not None
                    duration = time.time() - pinch_time
                    if duration <= (self.config.click.pinch_hold_time_ms / 1000.0):
                        return ClickType.LEFT_CLICK
                        
            self.pinch_start_time = None
            self.pinch_clicked = False
            self.is_dragging = False
            
        return ClickType.NONE
        
    def _check_dwell(self, position: Tuple[float, float]) -> ClickType:
        """Check for dwell click."""
        pos = np.array(position)
        
        if self.dwell_position is None:
            self.dwell_position = pos
            self.dwell_start_time = time.time()
            return ClickType.NONE
            
        # Calculate distance moved
        # Note: position is normalized, so distance is relative to screen size
        # Ideally convert to pixels, but for now use normalized threshold approx
        dist = np.linalg.norm(pos - self.dwell_position)
        
        # Threshold approx (normalized): dwell_radius_px / approx_screen_width
        dwell_radius_normalized = self.config.click.dwell_radius_px / 1920.0
        if dist > dwell_radius_normalized:
            # Moved too much, reset
            self.dwell_position = pos
            self.dwell_start_time = time.time()
        else:
            # Held steady
            dwell_time = self.dwell_start_time
            if dwell_time is not None and (time.time() - dwell_time > self.config.click.dwell_time_ms / 1000.0):
                self.dwell_position = None # Reset
                self.dwell_start_time = None
                return ClickType.LEFT_CLICK
                
        return ClickType.NONE
