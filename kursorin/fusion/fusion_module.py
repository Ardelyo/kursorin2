"""
Fusion Module

Combines tracking data from multiple sources (Head, Eye, Hand)
using adaptive weighting based on reliability.
"""

from typing import Optional, Tuple, List
import numpy as np

from kursorin.config import KursorinConfig
from kursorin.trackers.tracker_result import TrackerResult
from kursorin.exceptions import NoValidModalityError


class FusionModule:
    """
    Fuses multiple tracking inputs into a single cursor position.
    """
    
    def __init__(self, config: KursorinConfig):
        self.config = config
        self.history: List[Tuple[float, float]] = []
        
    def fuse(
        self,
        head_result: Optional[TrackerResult],
        eye_result: Optional[TrackerResult],
        hand_result: Optional[TrackerResult]
    ) -> Tuple[float, float]:
        """
        Fuse tracking results.
        
        Args:
            head_result: Result from head tracker
            eye_result: Result from eye tracker
            hand_result: Result from hand tracker
            
        Returns:
            Fused (x, y) position (normalized 0-1)
            
        Raises:
            NoValidModalityError: If no valid input is available.
        """
        # Collect valid inputs and their weights
        positions = []
        weights = []
        
        # 1. Head Tracking
        if head_result and head_result.valid and self.config.tracking.head_enabled:
            base_weight = self.config.fusion.weight_head
            # Adaptive weighting based on confidence
            confidence = getattr(head_result, 'confidence', 1.0)
            weight = base_weight * confidence
            
            positions.append(head_result.position)
            weights.append(weight)
            
        # 2. Eye Tracking
        if eye_result and eye_result.valid and self.config.tracking.eye_enabled:
            base_weight = self.config.fusion.weight_eye
            confidence = getattr(eye_result, 'confidence', 1.0)
            weight = base_weight * confidence
            
            positions.append(eye_result.position)
            weights.append(weight)
            
        # 3. Hand Tracking
        if hand_result and hand_result.valid and self.config.tracking.hand_enabled:
            base_weight = self.config.fusion.weight_hand
            confidence = getattr(hand_result, 'confidence', 1.0)
            weight = base_weight * confidence
            
            positions.append(hand_result.position)
            weights.append(weight)
            
        if not positions:
            raise NoValidModalityError()

        positions_arr = np.array(positions)   # shape (N, 2)
        weights_arr = np.array(weights, dtype=float)

        total_weight = weights_arr.sum()
        if total_weight <= 0:
            # Fallback: equal weights
            weights_arr = np.ones(len(positions))
            total_weight = float(len(positions))

        fused_pos = np.average(positions_arr, axis=0, weights=weights_arr)
        return tuple(fused_pos)
