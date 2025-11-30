"""
Cursor Smoother

Applies smoothing algorithms to cursor movement to reduce jitter.
"""

from typing import Tuple
import numpy as np

from kursorin.config import KursorinConfig


from kursorin.utils.one_euro_filter import OneEuroFilter

class CursorSmoother:
    """
    Smooths cursor movement using One Euro Filter.
    """
    
    def __init__(self, config: KursorinConfig):
        self.config = config
        self.prev_pos = None
        
        # Initialize filters for X and Y
        self.filter_x = OneEuroFilter(
            min_cutoff=config.smoothing.one_euro_min_cutoff,
            beta=config.smoothing.one_euro_beta
        )
        self.filter_y = OneEuroFilter(
            min_cutoff=config.smoothing.one_euro_min_cutoff,
            beta=config.smoothing.one_euro_beta
        )
        
    def smooth(self, position: Tuple[float, float]) -> Tuple[float, float]:
        """
        Apply smoothing to the raw position.
        
        Args:
            position: Raw (x, y) position (normalized).
            
        Returns:
            Smoothed (x, y) position.
        """
        x, y = position
        
        # Update filter parameters in case config changed
        self.filter_x.min_cutoff = self.config.smoothing.one_euro_min_cutoff
        self.filter_x.beta = self.config.smoothing.one_euro_beta
        self.filter_y.min_cutoff = self.config.smoothing.one_euro_min_cutoff
        self.filter_y.beta = self.config.smoothing.one_euro_beta
        
        # Filter
        smoothed_x = self.filter_x.filter(x)
        smoothed_y = self.filter_y.filter(y)
        
        return (smoothed_x, smoothed_y)
