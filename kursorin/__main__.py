"""
KURSORIN Main Entry Point

Routes to CLI or GUI based on arguments.
"""

import sys


def main():
    """Main entry point for KURSORIN."""
    # If no arguments or --gui flag, launch GUI
    # Otherwise, route to the CLI
    if len(sys.argv) == 1:
        # Default: launch GUI
        from kursorin.app import main as run_gui
        run_gui()
    elif "--gui" in sys.argv:
        sys.argv.remove("--gui")
        from kursorin.app import main as run_gui
        run_gui()
    else:
        # Route everything else to the rich CLI
        from kursorin.cli import main as run_cli
        run_cli()


if __name__ == "__main__":
    main()
