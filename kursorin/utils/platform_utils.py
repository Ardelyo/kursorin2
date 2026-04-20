import os
import platform
import sys

def is_windows() -> bool:
    """Check if the current platform is Windows."""
    return platform.system() == "Windows"

def is_admin() -> bool:
    """
    Check if the process is running with administrative privileges.
    On Windows, uses ctypes to check integrity level.
    On other platforms, checks if EUID is 0.
    """
    if is_windows():
        import ctypes
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    else:
        # For Linux/macOS
        try:
            return os.geteuid() == 0
        except AttributeError:
            # Fallback for platforms without geteuid
            return False
