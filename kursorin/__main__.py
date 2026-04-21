"""
KURSORIN Main Entry Point

Typing 'kursorin' (or running the .exe) launches the TUI command center.
Use 'kursorin-cli' for the CLI subcommand interface.
"""

import sys
import os


def main():
    """Main entry point — auto-elevates to admin then launches TUI or CLI."""

    # ── 1. Force UTF-8 on Windows terminals ──────────────────────────────────
    if os.name == "nt" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if os.name == "nt" and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    # ── 2. Automatic administrator elevation (Windows only) ───────────────────
    # Do this BEFORE importing any GUI / engine code so the elevated process
    # starts fresh.  On non-Windows, request_admin() is a no-op.
    # Skip elevation for `--help`, `--version`, `lang`, `update`, `status`,
    # `doctor` — these don't need admin rights.
    _no_admin_cmds = {"--help", "-h", "--version", "lang", "update", "status", "doctor"}
    _needs_admin = not any(a in _no_admin_cmds for a in sys.argv[1:])

    if _needs_admin:
        from kursorin.utils.platform_utils import request_admin
        request_admin(
            "KURSORIN needs administrator privileges to move the mouse cursor "
            "and control system windows."
        )
    # If we reach here we are either admin or the user declined UAC.

    # ── 3. Route to correct entry point ──────────────────────────────────────

    # --gui flag: launch legacy Tkinter GUI directly
    if "--gui" in sys.argv:
        sys.argv.remove("--gui")
        from kursorin.app import main as run_gui
        run_gui()
        return

    # Any CLI subcommand / --help → route to Click CLI
    if len(sys.argv) > 1:
        from kursorin.cli import main as run_cli
        run_cli()
        return

    # No arguments → launch the Textual TUI
    try:
        from kursorin.tui import run_tui
        run_tui()
    except ImportError:
        # Textual not installed: fall back to CLI help
        from kursorin.cli import main as run_cli
        run_cli()


if __name__ == "__main__":
    main()
