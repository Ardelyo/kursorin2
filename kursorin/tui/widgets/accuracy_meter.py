"""
KURSORIN TUI — Accuracy Meter Widget

Ocean Blue gradient accuracy bar.
"""

from textual.widget import Widget
from textual.reactive import reactive


class AccuracyMeter(Widget):
    """A labeled accuracy bar — Ocean Blue gradient."""

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

        # Blue gradient: deep → ocean → bright
        if v < 40:
            bar_color = "#003060"
            txt_color = "#005fa3"
        elif v < 70:
            bar_color = "#005fa3"
            txt_color = "#00a3ff"
        else:
            bar_color = "#00a3ff"
            txt_color = "#80d0ff"

        bar_width = 30
        filled = int(bar_width * v / 100)
        empty = bar_width - filled
        bar = f"[{bar_color}]{'█' * filled}[/][#0a1e3a]{'░' * empty}[/]"

        if pct == 0:
            pct_str = "[#4a607a]—[/]"
        else:
            pct_str = f"[{txt_color} bold]{pct}%[/]"

        return f"[#8098b0]{self.label}[/]\n{bar} {pct_str}"
