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
        # Monotonic timestamp counter required by MediaPipe VIDEO mode.
        # time.time() can produce the same ms value on two back-to-back calls on
        # fast hardware, causing MediaPipe to silently discard frames.
        self._last_timestamp_ms: int = 0

    def process(self, frame: np.ndarray, **kwargs) -> TrackerResult:
        """
        Process frame to track hand and gestures.
        """
        if self.detector is None:
            return TrackerResult(valid=False)

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        # Guarantee strict monotonic increase required by MediaPipe VIDEO mode.
        wall_ms = int(time.time() * 1000)
        timestamp_ms = max(wall_ms, self._last_timestamp_ms + 1)
        self._last_timestamp_ms = timestamp_ms
        results = self.detector.detect_for_video(mp_image, timestamp_ms)
        
        if not results.hand_landmarks:
            return TrackerResult(valid=False)
            
        landmarks = results.hand_landmarks[0]
        
        # Get index finger tip position for cursor control
        index_tip = landmarks[HandLandmark.INDEX_TIP]
        
        # Calculate pinch distance (Thumb tip to Index tip)
        thumb_tip = landmarks[HandLandmark.THUMB_TIP]
        raw_pinch_dist = np.sqrt(
            (thumb_tip.x - index_tip.x)**2 + 
            (thumb_tip.y - index_tip.y)**2
        )
        
        # Normalize pinch distance by hand width (Index MCP to Pinky MCP)
        index_mcp = landmarks[HandLandmark.INDEX_MCP]
        pinky_mcp = landmarks[HandLandmark.PINKY_MCP]
        hand_size = np.sqrt(
            (index_mcp.x - pinky_mcp.x)**2 + 
            (index_mcp.y - pinky_mcp.y)**2
        )
        hand_size = max(hand_size, 1e-6)  # Prevent division by zero
        
        pinch_dist = raw_pinch_dist / hand_size
        
        # Recognize gesture
        gesture = self._recognize_gesture(landmarks, pinch_dist)
        
        # Apply modality-specific and global inversion
        pos_x = index_tip.x
        pos_y = index_tip.y

        if self.config.tracking.invert_x ^ self.config.tracking.hand_invert_x:
            pos_x = 1.0 - pos_x
        if self.config.tracking.invert_y ^ self.config.tracking.hand_invert_y:
            pos_y = 1.0 - pos_y

        # Apply sensitivity scaling to match the coordinate space of head/eye trackers.
        # Without this, hand position is raw 0-1 camera space while head/eye are scaled
        # by their active-range ratios, making weighted fusion inconsistent.
        sensitivity = self.config.tracking.hand_sensitivity
        rel_x = (pos_x - 0.5) * sensitivity
        rel_y = (pos_y - 0.5) * sensitivity
        pos_x = max(0.0, min(1.0, 0.5 + rel_x))
        pos_y = max(0.0, min(1.0, 0.5 + rel_y))

        return TrackerResult(
            valid=True,
            position=np.array([pos_x, pos_y]),
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
