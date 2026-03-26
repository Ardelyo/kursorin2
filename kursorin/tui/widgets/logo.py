"""
KURSORIN TUI — Logo Widget

Animated ASCII logo with color cycling for the command-center.
"""

from textual.widget import Widget
from textual.reactive import reactive


KURSORIN_LOGO = """\
██╗  ██╗██╗   ██╗██████╗ ███████╗ ██████╗ ██████╗ ██╗███╗   ██╗
██║ ██╔╝██║   ██║██╔══██╗██╔════╝██╔═══██╗██╔══██╗██║████╗  ██║
█████╔╝ ██║   ██║██████╔╝███████╗██║   ██║██████╔╝██║██╔██╗ ██║
██╔═██╗ ██║   ██║██╔══██╗╚════██║██║   ██║██╔══██╗██║██║╚██╗██║
██║  ██╗╚██████╔╝██║  ██║███████║╚██████╔╝██║  ██║██║██║ ╚████║
╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝"""

# Color palettes for animation cycling
_PALETTES = [
    # Teal phase
    ("#0dccb0", "#0aa88e", "#077060", "#0d2922"),
    # Amber phase
    ("#f0a030", "#c07818", "#8a5008", "#2a1800"),
    # Bright phase
    ("#5eeada", "#0dccb0", "#0aa88e", "#0d2922"),
]


class LogoWidget(Widget):
    """Animated ASCII logo with teal/amber color cycling."""

    DEFAULT_CSS = """
    LogoWidget {
        height: auto;
        text-align: center;
        padding: 0 1;
    }
    """

    _phase: reactive[int] = reactive(0)

    def on_mount(self) -> None:
        self.set_interval(1.5, self._cycle_color)

    def _cycle_color(self) -> None:
        self._phase = (self._phase + 1) % len(_PALETTES)

    def render(self) -> str:
        p = _PALETTES[self._phase]
        lines = KURSORIN_LOGO.split("\n")
        colored_lines = []
        for i, line in enumerate(lines):
            # Alternate colors across line groups
            col_idx = min(i // 2, len(p) - 1)
            colored_lines.append(f"[bold {p[col_idx]}]{line}[/]")
        return "\n".join(colored_lines)
