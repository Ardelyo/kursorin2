import numpy as np
import time
import cv2

from kursorin.config import KursorinConfig
from kursorin.constants import (
    FaceLandmark,
    FACE_3D_MODEL_POINTS,
    FACE_MODEL_LANDMARK_INDICES,
)
from kursorin.trackers.base_tracker import BaseTracker
from kursorin.trackers.tracker_result import TrackerResult
from kursorin.exceptions import TrackingError


class HeadTracker(BaseTracker):
    """
    Estimates head pose (pitch, yaw, roll) from face landmarks.
    """
    
    def __init__(self, config: KursorinConfig):
        super().__init__(config)
        
        # Legacy FaceMesh is no longer used, we consume shared results from FaceLandmarker
        self.face_mesh = None 
        
        # 3D model points for PnP
        self.model_points = np.array([
            FACE_3D_MODEL_POINTS["nose_tip"],
            FACE_3D_MODEL_POINTS["chin"],
            FACE_3D_MODEL_POINTS["left_eye_corner"],
            FACE_3D_MODEL_POINTS["right_eye_corner"],
            FACE_3D_MODEL_POINTS["left_mouth_corner"],
            FACE_3D_MODEL_POINTS["right_mouth_corner"],
        ], dtype=np.float64)
        
        # Camera matrix (will be updated on first frame)
        self.camera_matrix = None
        self.dist_coeffs = np.zeros((4, 1))
    
    def process(self, frame: np.ndarray, **kwargs) -> TrackerResult:
        """
        Process frame to estimate head pose.
        
        Returns:
            TrackerResult with position (x, y) mapped from head pose.
        """
        h, w, _ = frame.shape
        
        # Initialize camera matrix if needed
        if self.camera_matrix is None:
            focal_length = w
            center = (w / 2, h / 2)
            self.camera_matrix = np.array(
                [[focal_length, 0, center[0]],
                 [0, focal_length, center[1]],
                 [0, 0, 1]], dtype=np.float64
            )
        
        # Check if results are provided by a shared FaceMesh provider
        face_mesh_results = kwargs.get("face_mesh_results")
        if face_mesh_results is not None:
            results = face_mesh_results
        else:
            # Independent processing is deprecated in this engine version, 
            # as FaceLandmarker setup is complex. Return invalid for now.
            return TrackerResult(valid=False)
        
        # FaceLandmarkerResult has .face_landmarks list
        if not hasattr(results, 'face_landmarks') or not results.face_landmarks:
            return TrackerResult(valid=False)
        
        # Landmarks for first face
        face_landmarks = results.face_landmarks[0]
        
        # Extract 2D image points
        image_points = []
        for key in [
            "nose_tip", "chin", "left_eye_corner", "right_eye_corner",
            "left_mouth_corner", "right_mouth_corner"
        ]:
            idx = FACE_MODEL_LANDMARK_INDICES[key]
            lm = face_landmarks[idx] # In Tasks API, face_landmarks[0] is a list of landmark objects
            image_points.append((lm.x * w, lm.y * h))
            
        image_points = np.array(image_points, dtype=np.float64)
        
        # Solve PnP
        success, rotation_vector, translation_vector = cv2.solvePnP(
            self.model_points,
            image_points,
            self.camera_matrix,
            self.dist_coeffs,
            flags=cv2.SOLVEPNP_ITERATIVE
        )
        
        if not success:
            return TrackerResult(valid=False)
            
        # Project nose tip to get 2D position
        nose_end_point2D, _ = cv2.projectPoints(
            np.array([(0.0, 0.0, 500.0)]),  # Project forward from nose
            rotation_vector,
            translation_vector,
            self.camera_matrix,
            self.dist_coeffs
        )
        
        # Calculate cursor position based on head rotation (simplified)
        # In a real implementation, we would map rotation angles (yaw, pitch) to screen coordinates
        # Here we use the projected nose tip as a proxy for direction
        
        # Get rotation matrix and angles
        rmat, _ = cv2.Rodrigues(rotation_vector)
        angles, _, _, _, _, _ = cv2.RQDecomp3x3(rmat)
        
        pitch, yaw, roll = angles[0], angles[1], angles[2]
        
        # Map yaw/pitch to screen coordinates using Active Range
        range_x = self.config.tracking.head_active_range_x
        range_y = self.config.tracking.head_active_range_y
        
        # Calculate raw ratios [-1, 1] (clamped to prevent massive overshoot)
        raw_x = max(-1.0, min(1.0, yaw / range_x))
        raw_y = max(-1.0, min(1.0, pitch / range_y))
        
import numpy as np
import time
import cv2

from kursorin.config import KursorinConfig
from kursorin.constants import (
    FaceLandmark,
    FACE_3D_MODEL_POINTS,
    FACE_MODEL_LANDMARK_INDICES,
)
from kursorin.trackers.base_tracker import BaseTracker
from kursorin.trackers.tracker_result import TrackerResult
from kursorin.exceptions import TrackingError


class HeadTracker(BaseTracker):
    """
    Estimates head pose (pitch, yaw, roll) from face landmarks.
    """
    
    def __init__(self, config: KursorinConfig):
        super().__init__(config)
        
        # Legacy FaceMesh is no longer used, we consume shared results from FaceLandmarker
        self.face_mesh = None 
        
        # 3D model points for PnP
        self.model_points = np.array([
            FACE_3D_MODEL_POINTS["nose_tip"],
            FACE_3D_MODEL_POINTS["chin"],
            FACE_3D_MODEL_POINTS["left_eye_corner"],
            FACE_3D_MODEL_POINTS["right_eye_corner"],
            FACE_3D_MODEL_POINTS["left_mouth_corner"],
            FACE_3D_MODEL_POINTS["right_mouth_corner"],
        ], dtype=np.float64)
        
        # Camera matrix (will be updated on first frame)
        self.camera_matrix = None
        self.dist_coeffs = np.zeros((4, 1))
    
    def process(self, frame: np.ndarray, **kwargs) -> TrackerResult:
        """
        Process frame to estimate head pose.
        
        Returns:
            TrackerResult with position (x, y) mapped from head pose.
        """
        h, w, _ = frame.shape
        
        # Initialize camera matrix if needed
        if self.camera_matrix is None:
            focal_length = w
            center = (w / 2, h / 2)
            self.camera_matrix = np.array(
                [[focal_length, 0, center[0]],
                 [0, focal_length, center[1]],
                 [0, 0, 1]], dtype=np.float64
            )
        
        # Check if results are provided by a shared FaceMesh provider
        face_mesh_results = kwargs.get("face_mesh_results")
        if face_mesh_results is not None:
            results = face_mesh_results
        else:
            # Independent processing is deprecated in this engine version, 
            # as FaceLandmarker setup is complex. Return invalid for now.
            return TrackerResult(valid=False)
        
        # FaceLandmarkerResult has .face_landmarks list
        if not hasattr(results, 'face_landmarks') or not results.face_landmarks:
            return TrackerResult(valid=False)
        
        # Landmarks for first face
        face_landmarks = results.face_landmarks[0]
        
        # Extract 2D image points
        image_points = []
        for key in [
            "nose_tip", "chin", "left_eye_corner", "right_eye_corner",
            "left_mouth_corner", "right_mouth_corner"
        ]:
            idx = FACE_MODEL_LANDMARK_INDICES[key]
            lm = face_landmarks[idx] # In Tasks API, face_landmarks[0] is a list of landmark objects
            image_points.append((lm.x * w, lm.y * h))
            
        image_points = np.array(image_points, dtype=np.float64)
        
        # Solve PnP
        success, rotation_vector, translation_vector = cv2.solvePnP(
            self.model_points,
            image_points,
            self.camera_matrix,
            self.dist_coeffs,
            flags=cv2.SOLVEPNP_ITERATIVE
        )
        
        if not success:
            return TrackerResult(valid=False)
            
        # Project nose tip to get 2D position
        nose_end_point2D, _ = cv2.projectPoints(
            np.array([(0.0, 0.0, 500.0)]),  # Project forward from nose
            rotation_vector,
            translation_vector,
            self.camera_matrix,
            self.dist_coeffs
        )
        
        # Calculate cursor position based on head rotation (simplified)
        # In a real implementation, we would map rotation angles (yaw, pitch) to screen coordinates
        # Here we use the projected nose tip as a proxy for direction
        
        # Get rotation matrix and angles
        rmat, _ = cv2.Rodrigues(rotation_vector)
        angles, _, _, _, _, _ = cv2.RQDecomp3x3(rmat)
        
        pitch, yaw, roll = angles[0], angles[1], angles[2]
        
        # Map yaw/pitch to screen coordinates using Active Range
        range_x = self.config.tracking.head_active_range_x
        range_y = self.config.tracking.head_active_range_y
        
        # Calculate raw ratios [-1, 1] (clamped to prevent massive overshoot)
        raw_x = max(-1.0, min(1.0, yaw / range_x))
        raw_y = max(-1.0, min(1.0, pitch / range_y))
        
        # Apply non-linear curve (signed quadratic: x * abs(x)) for better precise control
        scaled_x = raw_x * abs(raw_x)
        scaled_y = raw_y * abs(raw_y)
        
        # Normalize to [0, 1] and apply sensitivity
        norm_x = 0.5 + (scaled_x / 2.0) * self.config.tracking.head_sensitivity_x
        norm_y = 0.5 + (scaled_y / 2.0) * self.config.tracking.head_sensitivity_y
        
        # Clamp final screen coordinates
        norm_x = max(0.0, min(1.0, norm_x))
        norm_y = max(0.0, min(1.0, norm_y))
        
        return TrackerResult(
            valid=True,
            position=np.array([norm_x, norm_y]),
            confidence=1.0, 
            landmarks=face_landmarks,
            timestamp=time.time(),
            metadata={
                "pitch": pitch,
                "yaw": yaw,
            }
        )
    
    def close(self) -> None:
        """Release resources."""
        pass
