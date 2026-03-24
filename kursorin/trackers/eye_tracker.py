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
        left_ear = self._calculate_ear(face_landmarks, LEFT_EYE_EAR_LANDMARKS, w, h)
        right_ear = self._calculate_ear(face_landmarks, RIGHT_EYE_EAR_LANDMARKS, w, h)
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
        
        # Apply sensitivity / Active Range
        range_x = self.config.tracking.eye_active_range_x
        range_y = self.config.tracking.eye_active_range_y
        
        norm_x = 0.5 + (avg_gaze_x - 0.5) * (1.0 / range_x)
        norm_y = 0.5 + (avg_gaze_y - 0.5) * (1.0 / range_y)
        
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

    def _calculate_ear(self, landmarks, indices, w, h):
        """Calculate Eye Aspect Ratio."""
        # Euclidean distance function
        def dist(p1, p2):
            return np.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)
            
        # Vertical distances
        v1 = dist(landmarks[indices[1]], landmarks[indices[5]])
        v2 = dist(landmarks[indices[2]], landmarks[indices[4]])
        
        # Horizontal distance
        h_dist = dist(landmarks[indices[0]], landmarks[indices[3]])
        
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
        inner = landmarks[eye_indices[3]] # Inner corner (approx)
        outer = landmarks[eye_indices[0]] # Outer corner (approx)
        
        # Eye top/bottom
        top = landmarks[eye_indices[1]] # Top (approx)
        bottom = landmarks[eye_indices[4]] # Bottom (approx)
        
        # Horizontal ratio
        eye_width = abs(inner.x - outer.x)
        if eye_width == 0:
            x_ratio = 0.5
        else:
            # Distance from outer corner
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
        if self.face_mesh:
            self.face_mesh.close()
