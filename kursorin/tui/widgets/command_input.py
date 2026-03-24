"""
KURSORIN TUI — Command Input Widget

The central command prompt bar for navigating and controlling KURSORIN.
"""

from textual.widgets import Input
from textual.message import Message


# Known commands with descriptions
COMMANDS = {
    "start": "Start tracking engine",
    "dashboard": "Show dashboard",
    "settings": "Open settings",
    "doctor": "Run diagnostics",
    "update": "Check for updates",
    "calibrate": "Calibrate eye tracking",
    "gui": "Launch GUI app",
    "lang": "Toggle language",
    "home": "Return to home",
    "back": "Return to home",
    "quit": "Exit KURSORIN",
    "q": "Exit KURSORIN",
}


class CommandInput(Input):
    """A command prompt input bar for the TUI."""

    class CommandSubmitted(Message):
        """Posted when a command is submitted."""
        def __init__(self, command: str) -> None:
            self.command = command.strip().lower()
            super().__init__()

    DEFAULT_CSS = """
    CommandInput {
        width: 100%;
        height: 3;
        background: #111827;
        color: #e2e8f0;
        border: tall #1e3a5f;
        padding: 0 1;
    }
    CommandInput:focus {
        border: tall #3b82f6;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(
            placeholder="Type a command... (start, settings, doctor, update, quit)",
            **kwargs
        )

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key — dispatch command."""
        cmd = self.value.strip().lower()
        if cmd:
            self.post_message(self.CommandSubmitted(cmd))
            self.value = ""
