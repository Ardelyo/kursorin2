"""
KURSORIN Application

Entry point for the GUI application.
Uses CustomTkinter for a modern, themed interface.
"""

import sys
from loguru import logger

from kursorin.config import load_config
from kursorin.core.kursorin_engine import KursorinEngine
from kursorin.ui.theme import apply_theme


def main():
    """Run the KURSORIN GUI application."""
    try:
        # Apply theme early
        apply_theme()

        # Load configuration
        config = load_config()

        # Setup logging
        from kursorin.utils.logger import setup_logging
        setup_logging(config)

        logger.info("Starting KURSORIN application...")

        # Initialize engine
        engine = KursorinEngine(config)

        # Initialize UI (imports here to avoid issues if CTk isn't available)
        from kursorin.ui.app_window import AppWindow
        app = AppWindow(engine, config)

        # Determine if we need to onboard (no calibration found)
        calib_loaded = engine.load_calibration()
        if not calib_loaded:
            logger.info("No calibration found. Launching Onboarding Wizard.")
            from kursorin.ui.onboarding_wizard import show_onboarding_wizard

            # Hide main app window temporarily
            app.root.withdraw()
            needs_calibration = show_onboarding_wizard(app.root, engine, config)
            app.root.deiconify()

            if needs_calibration:
                logger.info("Onboarding requested calibration. Starting engine...")
                app._toggle_tracking()
                app.root.after(500, app._start_calibration)

        # Run application
        app.run()

    except ImportError as e:
        # Graceful fallback message
        print(f"\n[KURSORIN] Missing dependency: {e}")
        print("  Run: pip install -r requirements.txt\n")
        sys.exit(1)
    except Exception as e:
        logger.exception("Application crashed")
        sys.exit(1)


if __name__ == "__main__":
    main()
