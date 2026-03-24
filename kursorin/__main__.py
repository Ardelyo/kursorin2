"""
KURSORIN Main Entry Point

Routes to CLI by default. CLI handles --help and subcommands.
"""

import sys


def main():
    """Main entry point for KURSORIN."""
    from kursorin.cli import main as run_cli
    
    # Check if user passed --gui to maintain backwards compatibility
    if "--gui" in sys.argv:
        sys.argv.remove("--gui")
        from kursorin.app import main as run_gui
        run_gui()
    else:
        # Route everything to the rich CLI
        run_cli()


if __name__ == "__main__":
    main()
