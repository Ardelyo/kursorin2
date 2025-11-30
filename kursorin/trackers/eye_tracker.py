"""
Eye Tracker

Implements eye gaze tracking using MediaPipe Face Mesh iris landmarks.
"""

import cv2
import mediapipe as mp
import numpy as np

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
        # We assume FaceMesh is handled externally or we create a new one if needed.
        # Ideally, we should share the FaceMesh instance with HeadTracker to avoid double processing.
        # For this implementation, we'll create a new one if not provided, but in a real system
        # we might want to pass the landmarks from HeadTracker to EyeTracker.
        # However, to keep trackers independent as per BaseTracker interface, we'll re-initialize
        # or we could modify the architecture to pass landmarks.
        # Let's assume independent for now, but note the performance cost.
        
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        
        # Calibration data (placeholder)
        self.calibration_matrix = None

    def process(self, frame: np.ndarray) -> TrackerResult:
        """
        Process frame to estimate gaze.
        """
        # Note: In an optimized system, we would receive landmarks from a shared source.
        # Here we re-process.
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        
        if not results.multi_face_landmarks:
            return TrackerResult(valid=False)
            
        landmarks = results.multi_face_landmarks[0]
        h, w, _ = frame.shape
        
        # Calculate Eye Aspect Ratio (EAR) for blink detection
        left_ear = self._calculate_ear(landmarks, LEFT_EYE_EAR_LANDMARKS, w, h)
        right_ear = self._calculate_ear(landmarks, RIGHT_EYE_EAR_LANDMARKS, w, h)
        avg_ear = (left_ear + right_ear) / 2.0
        
        # Gaze estimation (simplified using iris center relative to eye corners)
        # This is a basic implementation. A robust one requires calibration.
        
        # Left eye gaze
        left_gaze = self._get_iris_position(landmarks, LEFT_IRIS_LANDMARKS, LEFT_EYE_EAR_LANDMARKS, w, h)
        # Right eye gaze
        right_gaze = self._get_iris_position(landmarks, RIGHT_IRIS_LANDMARKS, RIGHT_EYE_EAR_LANDMARKS, w, h)
        
        # Average gaze
        avg_gaze_x = (left_gaze[0] + right_gaze[0]) / 2.0
        avg_gaze_y = (left_gaze[1] + right_gaze[1]) / 2.0
        
        # Apply sensitivity / Active Range
        # We want to map the active range (e.g. center +/- 0.3) to 0-1
        range_x = self.config.tracking.eye_active_range_x
        range_y = self.config.tracking.eye_active_range_y
        
        # norm = 0.5 + (val - 0.5) * (1 / range)
        # If range is 1.0, we use full 0-1. If range is 0.5, we use 0.25-0.75 mapped to 0-1.
        
        norm_x = 0.5 + (avg_gaze_x - 0.5) * (1.0 / range_x)
        norm_y = 0.5 + (avg_gaze_y - 0.5) * (1.0 / range_y)
        
        norm_x = max(0.0, min(1.0, norm_x))
        norm_y = max(0.0, min(1.0, norm_y))
        
        return TrackerResult(
            valid=True,
            position=np.array([norm_x, norm_y]),
            confidence=1.0,
            landmarks=landmarks,
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
        v1 = dist(landmarks.landmark[indices[1]], landmarks.landmark[indices[5]])
        v2 = dist(landmarks.landmark[indices[2]], landmarks.landmark[indices[4]])
        
        # Horizontal distance
        h_dist = dist(landmarks.landmark[indices[0]], landmarks.landmark[indices[3]])
        
        if h_dist == 0:
            return 0.0
            
        return (v1 + v2) / (2.0 * h_dist)

    def _get_iris_position(self, landmarks, iris_indices, eye_indices, w, h):
        """
        Calculate iris position ratio within the eye.
        Returns (x_ratio, y_ratio) where 0 is left/top and 1 is right/bottom.
        """
        # Iris center
        iris_center = landmarks.landmark[iris_indices[0]]
        
        # Eye corners
        inner = landmarks.landmark[eye_indices[3]] # Inner corner (approx)
        outer = landmarks.landmark[eye_indices[0]] # Outer corner (approx)
        
        # Eye top/bottom
        top = landmarks.landmark[eye_indices[1]] # Top (approx)
        bottom = landmarks.landmark[eye_indices[4]] # Bottom (approx)
        
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
        self.face_mesh.close()
