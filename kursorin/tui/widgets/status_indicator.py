"""
KURSORIN TUI — Status Indicator Widget

Pulsing status dot for system component states.
"""

from textual.widget import Widget
from textual.reactive import reactive


class StatusIndicator(Widget):
    """A colored status dot with label."""

    DEFAULT_CSS = """
    StatusIndicator {
        height: 1;
        layout: horizontal;
    }
    """

    status = reactive("idle")  # online, warning, offline, idle
    label = reactive("System")

    INDICATORS = {
        "online": ("●", "#06d6a0"),
        "warning": ("●", "#f0932b"),
        "offline": ("●", "#ee5a6f"),
        "idle": ("○", "#576574"),
    }

    def __init__(self, label: str = "System", status: str = "idle", **kwargs):
        super().__init__(**kwargs)
        self.label = label
        self.status = status

    def render(self) -> str:
        symbol, color = self.INDICATORS.get(self.status, ("○", "#576574"))
        return f"[{color}]{symbol}[/] {self.label}"
