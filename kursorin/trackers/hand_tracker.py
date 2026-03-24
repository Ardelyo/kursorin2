import numpy as np
import time
import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
import os

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
        
        # Initialize HandLandmarker (Tasks API)
        model_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "assets", "models", "hand_landmarker.task"
        )
        
        # Note: If hand_landmarker.task is missing, we'll need to download it 
        # but for now we'll assume it's either present or hand tracking is disabled.
        # kursorin_engine usually manages model availability.
        
        if os.path.exists(model_path):
            base_options = mp_python.BaseOptions(model_asset_path=model_path)
            options = mp_vision.HandLandmarkerOptions(
                base_options=base_options,
                running_mode=mp_vision.RunningMode.VIDEO,
                num_hands=1,
                min_hand_detection_confidence=0.7,
                min_hand_presence_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            self.detector = mp_vision.HandLandmarker.create_from_options(options)
        else:
            self.detector = None
            
        self.gesture_history = []
    
    def process(self, frame: np.ndarray, **kwargs) -> TrackerResult:
        """
        Process frame to track hand and gestures.
        """
        if self.detector is None:
            return TrackerResult(valid=False)
            
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        # Use current timestamp for VIDEO mode
        timestamp_ms = int(time.time() * 1000)
        results = self.detector.detect_for_video(mp_image, timestamp_ms)
        
        if not results.hand_landmarks:
            return TrackerResult(valid=False)
            
        landmarks = results.hand_landmarks[0]
        
        # Get index finger tip position for cursor control
        index_tip = landmarks[HandLandmark.INDEX_TIP]
        
        # Calculate pinch distance (Thumb tip to Index tip)
        thumb_tip = landmarks[HandLandmark.THUMB_TIP]
        pinch_dist = np.sqrt(
            (thumb_tip.x - index_tip.x)**2 + 
            (thumb_tip.y - index_tip.y)**2
        )
        
        # Recognize gesture
        gesture = self._recognize_gesture(landmarks, pinch_dist)
        
        return TrackerResult(
            valid=True,
            position=np.array([index_tip.x, index_tip.y]),
            confidence=1.0, 
            landmarks=landmarks,
            timestamp=time.time(),
            metadata={
                "gesture": gesture,
                "pinch_distance": pinch_dist
            }
        )
    
    def _recognize_gesture(self, landmarks, pinch_dist: float) -> Gesture:
        """
        Rule-based gesture recognition with smoothing.
        """
        fingers_up = []
        
        # Check fingers (Index, Middle, Ring, Pinky)
        tips = [HandLandmark.INDEX_TIP, HandLandmark.MIDDLE_TIP, HandLandmark.RING_TIP, HandLandmark.PINKY_TIP]
        pips = [HandLandmark.INDEX_PIP, HandLandmark.MIDDLE_PIP, HandLandmark.RING_PIP, HandLandmark.PINKY_PIP]
        
        for tip, pip in zip(tips, pips):
            if landmarks[tip].y < landmarks[pip].y:
                fingers_up.append(1)
            else:
                fingers_up.append(0)
                
        if pinch_dist < self.config.tracking.pinch_threshold:
            raw_gesture = Gesture.PINCH
        elif sum(fingers_up) == 4:
            raw_gesture = Gesture.OPEN_PALM
        elif sum(fingers_up) == 0:
            raw_gesture = Gesture.FIST
        elif fingers_up == [1, 0, 0, 0]:
            raw_gesture = Gesture.POINTING
        else:
            raw_gesture = Gesture.NONE
            
        # Smoothing (last 5 frames)
        self.gesture_history.append(raw_gesture)
        if len(self.gesture_history) > 5:
            self.gesture_history.pop(0)
            
        # Return most common
        from collections import Counter
        most_common = Counter(self.gesture_history).most_common(1)
        return most_common[0][0] if most_common else Gesture.NONE

    def close(self) -> None:
        if self.detector:
            self.detector.close()
