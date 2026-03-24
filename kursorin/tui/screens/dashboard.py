"""
KURSORIN TUI — Dashboard Screen

Home view with system status, quick-start actions, and live metrics.
"""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.widgets import Static, Button, Label, Rule
from textual.widget import Widget

from kursorin import __version__
from kursorin.tui.widgets.status_indicator import StatusIndicator


class StatCard(Widget):
    """A compact metric card."""

    DEFAULT_CSS = """
    StatCard {
        height: 5;
        background: #0a1628;
        border: round #0d2137;
        padding: 1 2;
        content-align: center middle;
    }
    StatCard:hover {
        border: round #06d6a0 40%;
    }
    """

    def __init__(self, value: str, label: str, **kwargs):
        super().__init__(**kwargs)
        self._value = value
        self._label = label

    def render(self) -> str:
        return f"[bold #06d6a0]{self._value}[/]\n[#576574]{self._label}[/]"

    def update_value(self, value: str):
        self._value = value
        self.refresh()


class DashboardScreen(Container):
    """Main dashboard view."""

    DEFAULT_CSS = """
    DashboardScreen {
        height: 100%;
        padding: 0;
    }
    """

    def compose(self) -> ComposeResult:
        # Header
        yield Static(
            "[bold #06d6a0]⬡ Dashboard[/]  [#576574]System overview & quick actions[/]",
            classes="section-title"
        )
        yield Rule()

        # Status row
        with Horizontal(id="status-row"):
            yield StatusIndicator("Camera", "idle", id="cam-status")
            yield Static("  ")
            yield StatusIndicator("Head Tracking", "idle", id="head-status")
            yield Static("  ")
            yield StatusIndicator("Eye Tracking", "idle", id="eye-status")
            yield Static("  ")
            yield StatusIndicator("Hand Tracking", "idle", id="hand-status")

        yield Static("")  # spacer

        # Stat cards grid
        with Grid(id="stats-grid"):
            yield StatCard("—", "FPS", id="stat-fps")
            yield StatCard("—", "Latency", id="stat-latency")
            yield StatCard("—", "Uptime", id="stat-uptime")
            yield StatCard(f"v{__version__}", "Version", id="stat-version")

        yield Static("")  # spacer

        # Quick actions
        yield Static("[bold #06d6a0]⚡ Quick Actions[/]", classes="section-title")
        yield Rule()

        with Vertical(id="actions"):
            yield Button(
                "▶  Start Tracking",
                id="btn-start",
                classes="action-btn -primary"
            )
            yield Button(
                "🎯  Calibrate Eyes",
                id="btn-calibrate",
                classes="action-btn"
            )
            yield Button(
                "🖥  Launch GUI",
                id="btn-gui",
                classes="action-btn"
            )

        yield Static("")

        # Activity log
        yield Static("[bold #06d6a0]📋 Activity Log[/]", classes="section-title")
        yield Rule()
        yield Static(
            "[#576574]System initialized. Ready for tracking.[/]\n"
            "[#576574]Run diagnostics with [bold]Doctor[/bold] screen.[/]",
            id="activity-log",
            classes="log-panel"
        )
