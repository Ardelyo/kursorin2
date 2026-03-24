import numpy as np
import time

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
        self.gesture_history = []
    
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
        
        # Calculate pinch distance (Thumb tip to Index tip)
        thumb_tip = landmarks.landmark[HandLandmark.THUMB_TIP]
        pinch_dist = np.sqrt(
            (thumb_tip.x - index_tip.x)**2 + 
            (thumb_tip.y - index_tip.y)**2
        )
        
        # Recognize gesture
        gesture = self._recognize_gesture(landmarks, pinch_dist)
        
        return TrackerResult(
            valid=True,
            position=np.array([index_tip.x, index_tip.y]),
            confidence=1.0, # Simplified
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
        # Assuming typical camera feed where y increases downwards (tip.y < pip.y = extended)
        tips = [HandLandmark.INDEX_TIP, HandLandmark.MIDDLE_TIP, HandLandmark.RING_TIP, HandLandmark.PINKY_TIP]
        pips = [HandLandmark.INDEX_PIP, HandLandmark.MIDDLE_PIP, HandLandmark.RING_PIP, HandLandmark.PINKY_PIP]
        
        for tip, pip in zip(tips, pips):
            if landmarks.landmark[tip].y < landmarks.landmark[pip].y:
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
        self.hands.close()
