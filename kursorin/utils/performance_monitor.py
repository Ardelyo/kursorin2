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

    def __init__(self, history_size: int = 30, target_fps: int = 30):
        self.history_size = history_size
        self.frame_times = deque(maxlen=history_size)
        self.latencies = deque(maxlen=history_size)
        self.last_frame_time = time.time()
        self._drop_count: int = 0
        # Budget: max ms allowed per frame before it counts as a drop.
        self._frame_budget_ms: float = 1000.0 / max(target_fps, 1)

    def frame_complete(self) -> None:
        """Call at the end of each frame."""
        now = time.time()
        dt = now - self.last_frame_time
        self.last_frame_time = now
        self.frame_times.append(dt)

    def record_latency(self, latency_ms: float) -> None:
        """Record processing latency for a frame."""
        self.latencies.append(latency_ms)
        if latency_ms > self._frame_budget_ms:
            self._drop_count += 1

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

    @property
    def drop_count(self) -> int:
        """Number of frames that exceeded the target frame budget."""
        return self._drop_count
