"""
Logger Configuration

Configures the Loguru logger for the application.
"""

import sys
from pathlib import Path
from loguru import logger

from kursorin.config import KursorinConfig


def setup_logging(config: KursorinConfig = None):
    """
    Configure logging based on configuration.
    """
    # Remove default handler
    logger.remove()
    
    # Add console handler
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # Add file handler if configured
    if config:
        log_path = config.get_data_path() / "kursorin.log"
        logger.add(
            log_path,
            rotation="10 MB",
            retention="1 week",
            level="DEBUG" if config.debug_mode else "INFO"
        )
