"""
KURSORIN Main Entry Point

Typing 'kursorin' launches the TUI command center directly.
Use 'kursorin-cli' for the CLI subcommand interface.
"""

import sys
import os


def main():
    """Main entry point — launches TUI command center."""

    # Force UTF-8 on Windows
    if os.name == "nt" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    # --gui flag: launch legacy GUI directly
    if "--gui" in sys.argv:
        sys.argv.remove("--gui")
        from kursorin.app import main as run_gui
        run_gui()
        return

    # Any other subcommand / --help → route to CLI
    if len(sys.argv) > 1:
        from kursorin.cli import main as run_cli
        run_cli()
        return

    # No arguments → launch the TUI
    try:
        from kursorin.tui import run_tui
        run_tui()
    except ImportError as e:
        # Textual not installed: fall back to CLI help display
        from kursorin.cli import main as run_cli
        run_cli()


if __name__ == "__main__":
    main()
