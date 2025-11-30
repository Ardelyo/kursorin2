"""
KURSORIN Main Entry Point

Handles command-line arguments and launches the application.
"""

import sys
import argparse
from kursorin.app import main as run_gui


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="KURSORIN - Webcam-Based HCI")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode (headless)")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    
    args = parser.parse_args()
    
    if args.cli:
        print("CLI mode not yet implemented. Running GUI.")
        run_gui()
    else:
        run_gui()


if __name__ == "__main__":
    main()
