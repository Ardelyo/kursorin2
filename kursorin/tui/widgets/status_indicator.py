"""
KURSORIN TUI — Status Indicator Widget

Animated status dot for system component states.
"""

from textual.widget import Widget
from textual.reactive import reactive


_PULSE_FRAMES = ["●", "◉", "●", "○"]


class StatusIndicator(Widget):
    """A colored pulsing status dot with label."""

    DEFAULT_CSS = """
    StatusIndicator {
        height: 1;
        layout: horizontal;
    }
    """

    status = reactive("idle")   # online, warning, offline, idle, tracking
    label = reactive("System")
    _pulse_idx: reactive[int] = reactive(0)

    COLORS = {
        "online":   "#0dccb0",
        "tracking": "#0dccb0",
        "warning":  "#f0a030",
        "offline":  "#e84040",
        "idle":     "#384050",
    }

    def __init__(self, label: str = "System", status: str = "idle", **kwargs):
        super().__init__(**kwargs)
        self.label = label
        self.status = status

    def on_mount(self) -> None:
        self.set_interval(0.6, self._pulse)

    def _pulse(self) -> None:
        if self.status in ("online", "tracking"):
            self._pulse_idx = (self._pulse_idx + 1) % len(_PULSE_FRAMES)

    def set_status(self, status: str) -> None:
        self.status = status
        self._pulse_idx = 0
        self.refresh()

    def render(self) -> str:
        color = self.COLORS.get(self.status, "#384050")
        if self.status in ("online", "tracking"):
            symbol = _PULSE_FRAMES[self._pulse_idx]
        elif self.status == "warning":
            symbol = "◈"
        elif self.status == "offline":
            symbol = "✖"
        else:
            symbol = "○"
        return f"[{color}]{symbol}[/] [#8090a0]{self.label}[/]"
