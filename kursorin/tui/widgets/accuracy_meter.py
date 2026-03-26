"""
KURSORIN TUI — Accuracy Meter Widget

Live tracking accuracy bar for Head, Eye, and Hand modalities.
"""

from textual.widget import Widget
from textual.reactive import reactive


class AccuracyMeter(Widget):
    """A labeled accuracy bar showing 0–100%."""

    value: reactive[float] = reactive(0.0)
    label: reactive[str] = reactive("Modality")

    def __init__(self, label: str = "Modality", value: float = 0.0, **kwargs):
        super().__init__(**kwargs)
        self.label = label
        self.value = value

    def update_value(self, value: float) -> None:
        self.value = max(0.0, min(100.0, value))
        self.refresh()

    def render(self) -> str:
        v = self.value
        pct = int(v)

        # Color gradient: red → amber → teal based on value
        if v < 40:
            bar_color = "#e84040"
            txt_color = "#e84040"
        elif v < 70:
            bar_color = "#f0a030"
            txt_color = "#f0a030"
        else:
            bar_color = "#0dccb0"
            txt_color = "#0dccb0"

        # Bar
        bar_width = 30
        filled = int(bar_width * v / 100)
        empty = bar_width - filled
        bar = f"[{bar_color}]{'█' * filled}[/][#1a2030]{'░' * empty}[/]"

        if pct == 0:
            pct_str = "[#384050]—[/]"
        else:
            pct_str = f"[{txt_color} bold]{pct}%[/]"

        return f"[#8090a0]{self.label}[/]\n{bar} {pct_str}"
