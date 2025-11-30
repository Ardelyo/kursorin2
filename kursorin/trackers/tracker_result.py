"""
Tracker Result

Data structure for holding the results of a tracking operation.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import numpy as np


@dataclass
class TrackerResult:
    """
    Result from a single tracker for a single frame.
    
    Attributes:
        valid: Whether the tracking was successful
        position: Normalized screen coordinates (x, y) if applicable
        confidence: Confidence score of the tracking (0.0 - 1.0)
        landmarks: Raw landmarks or keypoints detected
        timestamp: Time of the result
        metadata: Additional tracker-specific data
    """
    
    valid: bool = False
    position: Optional[np.ndarray] = None  # [x, y] normalized
    confidence: float = 0.0
    landmarks: Optional[Any] = None
    timestamp: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
