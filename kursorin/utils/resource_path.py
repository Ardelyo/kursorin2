"""
Resource Path Utility

Resolves paths to bundled assets correctly whether running from source
or from a PyInstaller frozen .exe bundle.
"""

import os
import sys


def get_resource_path(*relative_parts: str) -> str:
    """
    Return the absolute path to a bundled resource.

    When running as a PyInstaller .exe, files are extracted to a temp
    directory stored in ``sys._MEIPASS``.  When running from source,
    paths are resolved relative to the package root
    (``kursorin/`` directory).

    Usage
    -----
    >>> from kursorin.utils.resource_path import get_resource_path
    >>> model = get_resource_path("assets", "models", "face_landmarker.task")
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # PyInstaller frozen bundle — all data files land in _MEIPASS
        base = sys._MEIPASS  # type: ignore[attr-defined]
        return os.path.join(base, *relative_parts)
    else:
        # Running from source — relative to the kursorin package root
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base, *relative_parts)
