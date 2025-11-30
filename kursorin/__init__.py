"""
KURSORIN - Affordable Webcam-Based Human-Computer Interaction System

A comprehensive hands-free computer control system using head, hand, and eye tracking.
Designed to work with standard webcams without specialized hardware.

Example usage:
    >>> from kursorin import Kursorin
    >>> app = Kursorin()
    >>> app.start()

For more information, visit: https://github.com/yourusername/kursorin
"""

__version__ = "1.0.0"
__author__ = "Ardellio Satria Anindito"
__email__ = "email.ardellio@contoh.com"
__license__ = "MIT"

from kursorin.core.kursorin_engine import KursorinEngine as Kursorin
from kursorin.config import KursorinConfig
from kursorin.exceptions import (
    KursorinError,
    CameraError,
    TrackingError,
    CalibrationError,
    ConfigurationError,
)

# Public API
__all__ = [
    # Main class
    "Kursorin",
    # Configuration
    "KursorinConfig",
    # Exceptions
    "KursorinError",
    "CameraError",
    "TrackingError",
    "CalibrationError",
    "ConfigurationError",
    # Version info
    "__version__",
    "__author__",
    "__email__",
]


def get_version() -> str:
    """Return the current version of KURSORIN."""
    return __version__


def get_info() -> dict:
    """Return package information as a dictionary."""
    return {
        "name": "kursorin",
        "version": __version__,
        "author": __author__,
        "email": __email__,
        "license": __license__,
        "description": "Webcam-Based Human-Computer Interaction System",
    }
