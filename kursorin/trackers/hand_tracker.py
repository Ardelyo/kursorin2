"""
Hand Tracker

Implements hand gesture tracking using MediaPipe Hands.
"""

import cv2
import mediapipe as mp
import numpy as np

from kursorin.config import KursorinConfig
from kursorin.constants import Gesture, HandLandmark
from kursorin.trackers.base_tracker import BaseTracker
from kursorin.trackers.tracker_result import TrackerResult


class HandTracker(BaseTracker):
    """
    Tracks hand position and recognizes gestures.
    """
    
    def __init__(self, config: KursorinConfig):
        super().__init__(config)
        
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5,
        )
    
    def process(self, frame: np.ndarray) -> TrackerResult:
        """
        Process frame to track hand and gestures.
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        
        if not results.multi_hand_landmarks:
            return TrackerResult(valid=False)
            
        landmarks = results.multi_hand_landmarks[0]
        
        # Get index finger tip position for cursor control
        index_tip = landmarks.landmark[HandLandmark.INDEX_TIP]
        
        # Recognize gesture
        gesture = self._recognize_gesture(landmarks)
        
        # Calculate pinch distance (Thumb tip to Index tip)
        thumb_tip = landmarks.landmark[HandLandmark.THUMB_TIP]
        pinch_dist = np.sqrt(
            (thumb_tip.x - index_tip.x)**2 + 
            (thumb_tip.y - index_tip.y)**2
        )
        
        return TrackerResult(
            valid=True,
            position=np.array([index_tip.x, index_tip.y]),
            confidence=1.0, # Simplified
            landmarks=landmarks,
            metadata={
                "gesture": gesture,
                "pinch_distance": pinch_dist
            }
        )
    
    def _recognize_gesture(self, landmarks) -> Gesture:
        """
        Simple rule-based gesture recognition.
        """
        # This is a placeholder for more complex logic
        # Check if fingers are extended
        
        # Example: Check if index is extended and others are closed -> POINTING
        # For now, return NONE or implement basic checks
        
        return Gesture.NONE

    def close(self) -> None:
        self.hands.close()
