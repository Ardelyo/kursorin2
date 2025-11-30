"""
Camera Manager

Handles webcam initialization, reading, and cleanup.
"""

import cv2
import numpy as np
from typing import Optional

from kursorin.exceptions import CameraNotFoundError, CameraReadError


class CameraManager:
    """
    Manages video capture device.
    """
    
    def __init__(self, camera_index: int = 0, width: int = 1280, height: int = 720, fps: int = 30):
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.fps = fps
        self.cap: Optional[cv2.VideoCapture] = None
        
    def open(self) -> None:
        """
        Open the camera device.
        
        Raises:
            CameraNotFoundError: If camera cannot be opened.
        """
        if self.cap is not None and self.cap.isOpened():
            return
            
        self.cap = cv2.VideoCapture(self.camera_index)
        
        if not self.cap.isOpened():
            raise CameraNotFoundError(self.camera_index)
            
        # Set properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)
        
        # Verify settings
        actual_w = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_h = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        
        # Update if different (some cameras don't support requested resolution)
        self.width = int(actual_w)
        self.height = int(actual_h)
        
    def read(self) -> Optional[np.ndarray]:
        """
        Read a frame from the camera.
        
        Returns:
            Frame (BGR) or None if failed.
            
        Raises:
            CameraReadError: If reading fails repeatedly.
        """
        if self.cap is None or not self.cap.isOpened():
            return None
            
        ret, frame = self.cap.read()
        
        if not ret:
            # Could raise error or return None
            return None
            
        return frame
        
    def close(self) -> None:
        """Release the camera."""
        if self.cap:
            self.cap.release()
            self.cap = None
