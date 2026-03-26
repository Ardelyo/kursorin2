"""
KURSORIN TUI — Status Indicator Widget

Clean Ocean Blue status dot.
"""

from textual.widget import Widget


class StatusIndicator(Widget):
    """A colored status dot with label — Ocean Blue theme."""

    DEFAULT_CSS = """
    StatusIndicator {
        height: 1;
        layout: horizontal;
    }
    """

    COLORS = {
        "online":   "#00a3ff",
        "tracking": "#80d0ff",
        "warning":  "#c09040",
        "offline":  "#4a607a",
        "idle":     "#2a3a50",
    }

    SYMBOLS = {
        "online":   "●",
        "tracking": "●",
        "warning":  "◈",
        "offline":  "○",
        "idle":     "○",
    }

    def __init__(self, label: str = "System", status: str = "idle", **kwargs):
        super().__init__(**kwargs)
        self._label = label
        self._status = status

    def set_status(self, status: str) -> None:
        self._status = status
        self.refresh()

    def render(self) -> str:
        color = self.COLORS.get(self._status, "#2a3a50")
        symbol = self.SYMBOLS.get(self._status, "○")
        return f"[{color}]{symbol}[/] [#8098b0]{self._label}[/]"
