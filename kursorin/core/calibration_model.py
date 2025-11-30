"""
Calibration Model

Handles the mapping between raw eye gaze data and screen coordinates.
"""

import numpy as np
import cv2
from typing import List, Tuple, Optional
from loguru import logger

class CalibrationModel:
    """
    Maps raw gaze coordinates to screen coordinates using Homography or Polynomial Regression.
    """
    
    def __init__(self):
        self.raw_points: List[Tuple[float, float]] = []
        self.screen_points: List[Tuple[float, float]] = []
        self.matrix: Optional[np.ndarray] = None
        self.is_calibrated = False
        
    def add_point(self, raw_gaze: Tuple[float, float], screen_target: Tuple[float, float]):
        """Add a calibration point pair."""
        self.raw_points.append(raw_gaze)
        self.screen_points.append(screen_target)
        
    def compute(self) -> bool:
        """Compute the calibration matrix."""
        if len(self.raw_points) < 4:
            logger.warning("Not enough points for calibration (min 4)")
            return False
            
        try:
            src = np.array(self.raw_points, dtype=np.float32).reshape(-1, 1, 2)
            dst = np.array(self.screen_points, dtype=np.float32).reshape(-1, 1, 2)
            
            # Use Homography for mapping 2D plane to 2D plane
            self.matrix, mask = cv2.findHomography(src, dst, cv2.RANSAC, 5.0)
            
            if self.matrix is None:
                logger.error("Failed to compute homography matrix")
                return False
                
            self.is_calibrated = True
            logger.info("Calibration successful")
            return True
            
        except Exception as e:
            logger.error(f"Calibration computation failed: {e}")
            return False
            
    def map(self, raw_gaze: Tuple[float, float]) -> Tuple[float, float]:
        """Map raw gaze to screen coordinates."""
        if not self.is_calibrated or self.matrix is None:
            return raw_gaze
            
        try:
            src = np.array([[raw_gaze]], dtype=np.float32)
            dst = cv2.perspectiveTransform(src, self.matrix)
            return tuple(dst[0][0])
        except Exception:
            return raw_gaze
            
    def reset(self):
        """Reset calibration data."""
        self.raw_points = []
        self.screen_points = []
        self.matrix = None
        self.is_calibrated = False
