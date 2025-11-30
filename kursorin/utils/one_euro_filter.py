"""
One Euro Filter

A simple and efficient low-pass filter with adaptive cutoff frequency.
It minimizes jitter at low speeds while maintaining low latency at high speeds.
Reference: http://cristal.univ-lille.fr/~casiez/1euro/
"""

import math
import time

class LowPassFilter:
    def __init__(self, alpha, init_val=0.0):
        self.__y = init_val
        self.__s = None

    def filter(self, value, alpha):
        if self.__s is None:
            self.__s = value
        else:
            self.__s = alpha * value + (1.0 - alpha) * self.__s
        return self.__s

    def last_value(self):
        return self.__s

class OneEuroFilter:
    def __init__(self, min_cutoff=1.0, beta=0.0, d_cutoff=1.0):
        """
        Initialize the One Euro Filter.
        
        Args:
            min_cutoff: Minimum cutoff frequency (Hz). Lower = more smoothing at low speeds.
            beta: Speed coefficient. Higher = less lag at high speeds.
            d_cutoff: Cutoff frequency for the derivative (Hz).
        """
        self.min_cutoff = float(min_cutoff)
        self.beta = float(beta)
        self.d_cutoff = float(d_cutoff)
        
        self.x_filter = LowPassFilter(alpha=1.0)
        self.dx_filter = LowPassFilter(alpha=1.0)
        self.last_time = None

    def filter(self, x, timestamp=None):
        """
        Filter the signal.
        
        Args:
            x: Current signal value.
            timestamp: Current timestamp (seconds). If None, uses time.time().
        """
        # Get timestamp
        if timestamp is None:
            timestamp = time.time()
            
        # Initialize on first call
        if self.last_time is None:
            self.last_time = timestamp
            return self.x_filter.filter(x, alpha=1.0)
            
        # Calculate dt
        dt = timestamp - self.last_time
        self.last_time = timestamp
        
        # Avoid division by zero
        if dt <= 0:
            return self.x_filter.last_value()

        # Compute rate of change (derivative)
        dx = (x - self.x_filter.last_value()) / dt
        edx = self.dx_filter.filter(dx, alpha=self._alpha(dt, self.d_cutoff))
        
        # Compute cutoff frequency
        cutoff = self.min_cutoff + self.beta * abs(edx)
        
        # Filter signal
        return self.x_filter.filter(x, alpha=self._alpha(dt, cutoff))

    def _alpha(self, dt, cutoff):
        tau = 1.0 / (2 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / dt)
