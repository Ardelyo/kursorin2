import numpy as np
import time
import cv2

from kursorin.config import KursorinConfig
from kursorin.constants import (
    FaceLandmark,
    LEFT_IRIS_LANDMARKS,
    RIGHT_IRIS_LANDMARKS,
    LEFT_EYE_EAR_LANDMARKS,
    RIGHT_EYE_EAR_LANDMARKS,
)
from kursorin.trackers.base_tracker import BaseTracker
from kursorin.trackers.tracker_result import TrackerResult


class EyeTracker(BaseTracker):
    """
    Estimates gaze direction and detects blinks.
    """
    
    def __init__(self, config: KursorinConfig):
        super().__init__(config)
        
        # Legacy FaceMesh is no longer used, we consume shared results from FaceLandmarker
        self.face_mesh = None
        
        # Calibration data (placeholder)
        self.calibration_matrix = None
        
        # State for EMA smoothing
        self.smoothed_gaze = None

    def process(self, frame: np.ndarray, **kwargs) -> TrackerResult:
        """
        Process frame to estimate gaze.
        """
        # Get shared results if provided, otherwise run independently
        face_mesh_results = kwargs.get("face_mesh_results")
        if face_mesh_results is not None:
            results = face_mesh_results
        else:
            # Independent processing is deprecated in this engine version
            return TrackerResult(valid=False)
        
        # FaceLandmarkerResult has .face_landmarks list
        if not hasattr(results, 'face_landmarks') or not results.face_landmarks:
            return TrackerResult(valid=False)
            
        face_landmarks = results.face_landmarks[0]
        h, w, _ = frame.shape
        
        # Calculate Eye Aspect Ratio (EAR) for blink detection
        left_ear = self._calculate_ear(face_landmarks)
        right_ear = self._calculate_ear(face_landmarks, is_right=True)
        avg_ear = (left_ear + right_ear) / 2.0
        
        # Gaze estimation (simplified using iris center relative to eye corners)
        # This is a basic implementation. A robust one requires calibration.
        
        # Left eye gaze
        left_gaze = self._get_iris_position(face_landmarks, LEFT_IRIS_LANDMARKS, LEFT_EYE_EAR_LANDMARKS, w, h)
        # Right eye gaze
        right_gaze = self._get_iris_position(face_landmarks, RIGHT_IRIS_LANDMARKS, RIGHT_EYE_EAR_LANDMARKS, w, h)
        
        # Average gaze
        avg_gaze_x = (left_gaze[0] + right_gaze[0]) / 2.0
        avg_gaze_y = (left_gaze[1] + right_gaze[1]) / 2.0
        
        # Apply EMA Smoothing to reduce jitter
        alpha = 0.15
        if hasattr(self.config, 'smoothing') and hasattr(self.config.smoothing, 'eye_ema_alpha'):
            alpha = self.config.smoothing.eye_ema_alpha
            
        smoothed = self.smoothed_gaze
        if smoothed is None:
            self.smoothed_gaze = np.array([avg_gaze_x, avg_gaze_y])
            smoothed = self.smoothed_gaze
        else:
            self.smoothed_gaze = smoothed * (1 - alpha) + np.array([avg_gaze_x, avg_gaze_y]) * alpha
            smoothed = self.smoothed_gaze
            
        avg_gaze_x, avg_gaze_y = smoothed[0], smoothed[1]
        
        # Apply sensitivity / Active Range
        range_x = self.config.tracking.eye_active_range_x
        range_y = self.config.tracking.eye_active_range_y
        
        # Apply modality-specific and global inversion
        rel_x = (avg_gaze_x - 0.5)
        rel_y = (avg_gaze_y - 0.5)
        
        if self.config.tracking.invert_x ^ self.config.tracking.eye_invert_x:
            rel_x = -rel_x
        if self.config.tracking.invert_y ^ self.config.tracking.eye_invert_y:
            rel_y = -rel_y
            
        norm_x = 0.5 + rel_x * (1.0 / range_x)
        norm_y = 0.5 + rel_y * (1.0 / range_y)
        
        norm_x = max(0.0, min(1.0, norm_x))
        norm_y = max(0.0, min(1.0, norm_y))
        
        return TrackerResult(
            valid=True,
            position=np.array([norm_x, norm_y]),
            confidence=1.0,
            landmarks=face_landmarks,
            timestamp=time.time(),
            metadata={
                "ear": avg_ear,
                "left_ear": left_ear,
                "right_ear": right_ear,
                "gaze_x": avg_gaze_x,
                "gaze_y": avg_gaze_y
            }
        )

    def _calculate_ear(self, landmarks, is_right=False):
        """Calculate Eye Aspect Ratio."""
        indices = RIGHT_EYE_EAR_LANDMARKS if is_right else LEFT_EYE_EAR_LANDMARKS
        
        def dist(i, j):
            p1 = landmarks[indices[i]]
            p2 = landmarks[indices[j]]
            return np.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)
            
        # Vertical distances
        v1 = dist(1, 5)
        v2 = dist(2, 4)
        
        # Horizontal distance
        h_dist = dist(0, 3)
        
        if h_dist == 0:
            return 0.0
            
        return (v1 + v2) / (2.0 * h_dist)

    def _get_iris_position(self, landmarks, iris_indices, eye_indices, w, h):
        """
        Calculate iris position ratio within the eye.
        Returns (x_ratio, y_ratio) where 0 is left/top and 1 is right/bottom.
        """
        # Iris center
        iris_center = landmarks[iris_indices[0]]
        
        # Eye corners
        inner = landmarks[eye_indices[3]] # Inner corner
        outer = landmarks[eye_indices[0]] # Outer corner
        
        # Eye top/bottom
        top = landmarks[eye_indices[1]]
        bottom = landmarks[eye_indices[4]]
        
        # Horizontal ratio
        eye_width = abs(inner.x - outer.x)
        if eye_width == 0:
            x_ratio = 0.5
        else:
            dist_x = abs(iris_center.x - outer.x)
            x_ratio = dist_x / eye_width
            
        # Vertical ratio
        eye_height = abs(bottom.y - top.y)
        if eye_height == 0:
            y_ratio = 0.5
        else:
            dist_y = abs(iris_center.y - top.y)
            y_ratio = dist_y / eye_height
            
        return (x_ratio, y_ratio)

    def close(self) -> None:
        """Release resources."""
        pass
