"""
Overlay Widget

Draws tracking visualization on the video frame.
"""

import cv2
import numpy as np
from typing import Optional

from kursorin.config import KursorinConfig
from kursorin.core.kursorin_engine import FrameResult
from kursorin.constants import Color


class Overlay:
    """
    Handles drawing visual feedback on frames.
    """
    
    def __init__(self, config: KursorinConfig):
        self.config = config
        
    def draw(self, frame: np.ndarray, result: FrameResult) -> np.ndarray:
        """
        Draw visualization on the frame.
        """
        if not self.config.ui.show_overlay:
            return frame
            
        vis_frame = frame.copy()
        h, w, _ = vis_frame.shape
        
        # Draw Head Tracking
        if result.head_result and result.head_result.valid and self.config.ui.show_tracking_points:
            # Draw nose tip or head pose indicator
            # Simplified: Draw a circle at the nose tip if available
            # Ideally we project 3D axes
            pass
            
        # Draw Eye Tracking
        if result.eye_result and result.eye_result.valid and self.config.ui.show_tracking_points:
            # Draw gaze point
            gaze_x = result.eye_result.metadata.get("gaze_x", 0.5)
            gaze_y = result.eye_result.metadata.get("gaze_y", 0.5)
            
            # Map to screen (this is gaze on screen, but we want to visualize on camera frame)
            # Visualizing gaze on camera frame is tricky without calibration mapping back to camera space
            # So we might just draw iris landmarks
            pass
            
        # Draw Hand Tracking
        if result.hand_result and result.hand_result.valid and self.config.ui.show_hand_skeleton:
            # Draw hand landmarks
            # MediaPipe has drawing utils, but we can do simple drawing here
            landmarks = result.hand_result.landmarks
            if landmarks:
                # Draw index tip
                # We need to convert normalized landmarks to pixel coordinates
                pass
                
        # Draw Cursor Position (if mapped back to frame, or just an indicator)
        if result.cursor_position:
            cx, cy = result.cursor_position
            # Draw a small circle representing cursor position (mapped to frame size)
            # This is just for feedback
            px = int(cx * w)
            py = int(cy * h)
            cv2.circle(vis_frame, (px, py), 10, Color.FUSED_COLOR, -1)
            
        return vis_frame
