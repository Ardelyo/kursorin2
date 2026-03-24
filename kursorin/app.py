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
        
        # Determine if we need to onboard (no calibration found)
        # Note: AppWindow initializes main tk.Tk() instance.
        calib_loaded = engine.load_calibration()
        if not calib_loaded:
            logger.info("No calibration found. Launching Onboarding Wizard.")
            from kursorin.ui.onboarding_wizard import show_onboarding_wizard
            
            # Hide main app window temporarily for cleaner wizard presentation
            app.root.withdraw()
            needs_calibration = show_onboarding_wizard(app.root, engine, config)
            app.root.deiconify()
            
            if needs_calibration:
                logger.info("Onboarding requested calibration. Starting engine...")
                app._toggle_tracking()
                app.root.after(500, app._start_calibration)
        
        # Run application
        app.run()
        
    except Exception as e:
        logger.exception("Application crashed")
        sys.exit(1)


if __name__ == "__main__":
    main()
