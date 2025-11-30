"""
KURSORIN Application

Entry point for the GUI application.
"""

import sys
import tkinter as tk
from loguru import logger

from kursorin.config import load_config
from kursorin.core.kursorin_engine import KursorinEngine
from kursorin.ui.app_window import AppWindow
from kursorin.utils.logger import setup_logging


def main():
    """Run the KURSORIN GUI application."""
    try:
        # Load configuration
        config = load_config()
        
        # Setup logging
        setup_logging(config)
        
        logger.info("Starting KURSORIN application...")
        
        # Initialize engine
        engine = KursorinEngine(config)
        
        # Initialize UI
        app = AppWindow(engine, config)
        
        # Run application
        app.run()
        
    except Exception as e:
        logger.exception("Application crashed")
        sys.exit(1)


if __name__ == "__main__":
    main()
