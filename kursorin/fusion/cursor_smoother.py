"""
Cursor Smoother

Applies smoothing algorithms to cursor movement to reduce jitter.
"""

from typing import Tuple
import numpy as np

from kursorin.config import KursorinConfig


class CursorSmoother:
    """
    Smooths cursor movement using exponential smoothing or Kalman filter.
    """
    
    def __init__(self, config: KursorinConfig):
        self.config = config
        self.prev_pos = None
        
    def smooth(self, position: Tuple[float, float]) -> Tuple[float, float]:
        """
        Apply smoothing to the raw position.
        
        Args:
            position: Raw (x, y) position (normalized).
            
        Returns:
            Smoothed (x, y) position.
        """
        current_pos = np.array(position)
        
        if self.prev_pos is None:
            self.prev_pos = current_pos
            return tuple(current_pos)
            
        # Simple Exponential Smoothing
        alpha = 1.0 - self.config.smoothing.smoothing_factor
        
        # Dynamic smoothing could be implemented here based on velocity
        
        smoothed_pos = alpha * current_pos + (1 - alpha) * self.prev_pos
        self.prev_pos = smoothed_pos
        
        return tuple(smoothed_pos)
