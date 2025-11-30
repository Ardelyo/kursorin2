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
            weight = self.config.fusion.weight_head
            # Adjust weight based on confidence/reliability if needed
            positions.append(head_result.position)
            weights.append(weight)
            
        # 2. Eye Tracking
        if eye_result and eye_result.valid and self.config.tracking.eye_enabled:
            weight = self.config.fusion.weight_eye
            positions.append(eye_result.position)
            weights.append(weight)
            
        # 3. Hand Tracking
        if hand_result and hand_result.valid and self.config.tracking.hand_enabled:
            weight = self.config.fusion.weight_hand
            positions.append(hand_result.position)
            weights.append(weight)
            
        if not positions:
            raise NoValidModalityError()
            
        # Normalize weights
        total_weight = sum(weights)
        if total_weight == 0:
             # Fallback: equal weights
             weights = [1.0 / len(positions)] * len(positions)
        else:
            weights = [w / total_weight for w in weights]
            
        # Weighted average
        fused_pos = np.zeros(2)
        for pos, w in zip(positions, weights):
            fused_pos += pos * w
            
        return tuple(fused_pos)
