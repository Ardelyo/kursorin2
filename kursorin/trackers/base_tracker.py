"""
Base Tracker

Abstract base class for all tracking modules.
"""

from abc import ABC, abstractmethod
from typing import Optional, Any

import numpy as np

from kursorin.config import KursorinConfig
from kursorin.trackers.tracker_result import TrackerResult


class BaseTracker(ABC):
    """
    Abstract base class for trackers.
    
    All specific trackers (Head, Eye, Hand) must inherit from this class
    and implement the process method.
    """
    
    def __init__(self, config: KursorinConfig):
        """
        Initialize the tracker.
        
        Args:
            config: Global configuration object.
        """
        self.config = config
    
    @abstractmethod
    def process(self, frame: np.ndarray) -> TrackerResult:
        """
        Process a single video frame.
        
        Args:
            frame: Input image frame (BGR).
            
        Returns:
            TrackerResult object containing tracking data.
        """
        pass
    
    def close(self) -> None:
        """Release any resources held by the tracker."""
        pass
