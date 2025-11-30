"""
Performance Monitor

Tracks FPS and processing latency.
"""

import time
from collections import deque


class PerformanceMonitor:
    """
    Monitors system performance (FPS, Latency).
    """
    
    def __init__(self, history_size: int = 30):
        self.history_size = history_size
        self.frame_times = deque(maxlen=history_size)
        self.latencies = deque(maxlen=history_size)
        self.last_frame_time = time.time()
        
    def frame_complete(self) -> None:
        """Call at the end of each frame."""
        now = time.time()
        dt = now - self.last_frame_time
        self.last_frame_time = now
        self.frame_times.append(dt)
        
    def record_latency(self, latency_ms: float) -> None:
        """Record processing latency for a frame."""
        self.latencies.append(latency_ms)
        
    @property
    def fps(self) -> float:
        """Calculate current FPS."""
        if not self.frame_times:
            return 0.0
        avg_dt = sum(self.frame_times) / len(self.frame_times)
        if avg_dt == 0:
            return 0.0
        return 1.0 / avg_dt
        
    @property
    def avg_latency_ms(self) -> float:
        """Calculate average latency."""
        if not self.latencies:
            return 0.0
        return sum(self.latencies) / len(self.latencies)
