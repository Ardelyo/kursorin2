"""
Overlay Widget

Draws tracking visualization on the video frame.
"""

import cv2
import numpy as np
from typing import Optional, Tuple

from kursorin.config import KursorinConfig
from kursorin.core.kursorin_engine import FrameResult
from kursorin.constants import Color


class Overlay:
    """
    Handles drawing visual feedback on frames.
    """
    
    def __init__(self, config: KursorinConfig):
        self.config = config
        self.click_animation_frames = 0
        self.click_position: Tuple[int, int] = (0, 0)
        
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
            # Draw nose tip as a small circle in camera frame
            face_landmarks = result.head_result.landmarks
            if face_landmarks:
                # Nose tip is at index 4 in Mediapipe Face Mesh
                nose_tip = face_landmarks[4]
                nx, ny = int(nose_tip.x * w), int(nose_tip.y * h)
                cv2.circle(vis_frame, (nx, ny), 3, Color.HEAD_COLOR, -1)
            
        # Draw Eye Tracking
        if result.eye_result and result.eye_result.valid and self.config.ui.show_tracking_points:
            face_landmarks = result.eye_result.landmarks
            if face_landmarks:
                # Draw Iris landmarks
                from kursorin.constants import LEFT_IRIS_LANDMARKS, RIGHT_IRIS_LANDMARKS
                for idx in LEFT_IRIS_LANDMARKS + RIGHT_IRIS_LANDMARKS:
                    lm = face_landmarks[idx]
                    ix, iy = int(lm.x * w), int(lm.y * h)
                    cv2.circle(vis_frame, (ix, iy), 1, Color.EYE_COLOR, -1)
            
        # Draw Hand Tracking
        if result.hand_result and result.hand_result.valid and self.config.ui.show_hand_skeleton:
            # Draw hand landmarks
            landmarks = result.hand_result.landmarks
            if landmarks:
                # Draw index tip and thumb tip
                from kursorin.constants import HandLandmark
                for idx in [HandLandmark.INDEX_TIP, HandLandmark.THUMB_TIP]:
                    lm = landmarks[idx]
                    hx, hy = int(lm.x * w), int(lm.y * h)
                    cv2.circle(vis_frame, (hx, hy), 4, Color.HAND_COLOR, -1)
                
                # Draw simple bones (Thumb-Index)
                thumb = landmarks[HandLandmark.THUMB_TIP]
                index = landmarks[HandLandmark.INDEX_TIP]
                cv2.line(vis_frame, 
                         (int(thumb.x * w), int(thumb.y * h)), 
                         (int(index.x * w), int(index.y * h)), 
                         Color.HAND_COLOR, 1)
                
        # Draw Cursor Position (Fused)
        if result.cursor_position:
            cx, cy = result.cursor_position
            
            # Map to frame coordinates (approximate, since frame != screen)
            # We assume frame covers the screen for visualization purposes
            px = int(cx * w)
            py = int(cy * h)
            
            # Draw Fused Point
            cv2.circle(vis_frame, (px, py), 10, Color.FUSED_COLOR, -1)
            cv2.putText(vis_frame, "Cursor", (px + 15, py), cv2.FONT_HERSHEY_SIMPLEX, 0.5, Color.FUSED_COLOR, 1)
            
            # Draw lines from individual trackers to fused point
            if result.head_result and result.head_result.valid:
                hx, hy = result.head_result.position
                hpx, hpy = int(hx * w), int(hy * h)
                cv2.line(vis_frame, (hpx, hpy), (px, py), Color.HEAD_COLOR, 1)
                cv2.circle(vis_frame, (hpx, hpy), 5, Color.HEAD_COLOR, -1)
                
            if result.eye_result and result.eye_result.valid:
                ex, ey = result.eye_result.position
                epx, epy = int(ex * w), int(ey * h)
                cv2.line(vis_frame, (epx, epy), (px, py), Color.EYE_COLOR, 1)
                cv2.circle(vis_frame, (epx, epy), 5, Color.EYE_COLOR, -1)
                
        # Draw Click Visual Feedback
        from kursorin.constants import ClickType
        if result.click_event and result.click_event != ClickType.NONE:
            self.click_animation_frames = 15
            if result.cursor_position:
                self.click_position = (int(result.cursor_position[0] * w), int(result.cursor_position[1] * h))
                
        if self.click_animation_frames > 0:
            radius = 10 + (15 - self.click_animation_frames) * 3
            thickness = max(1, self.click_animation_frames // 3)
            
            cv2.circle(vis_frame, self.click_position, radius, Color.SUCCESS, thickness)
            cv2.putText(vis_frame, "CLICK!", (self.click_position[0] + 15, self.click_position[1] - 15), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, Color.SUCCESS, 2)
            
            self.click_animation_frames -= 1
            
        return vis_frame
