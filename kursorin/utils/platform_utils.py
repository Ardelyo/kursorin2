"""
Platform Utilities

Cross-platform helpers for privilege detection and automatic
administrator elevation on Windows.
"""

import os
import platform
import sys


def is_windows() -> bool:
    """Return True if running on Windows."""
    return platform.system() == "Windows"


def is_admin() -> bool:
    """
    Return True if the process is running with administrator privileges.

    - Windows : uses ``ctypes.windll.shell32.IsUserAnAdmin()``
    - Linux/macOS : checks ``os.geteuid() == 0``
    """
    if is_windows():
        import ctypes
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    else:
        try:
            return os.geteuid() == 0
        except AttributeError:
            return False


def request_admin(reason: str = "KURSORIN requires administrator privileges to control system windows.") -> None:
    """
    Ensure the process is running as administrator on Windows.

    If already admin, returns immediately.
    If NOT admin, re-launches the current process with the ``runas``
    ShellExecute verb (triggers the Windows UAC prompt) and exits the
    current (unprivileged) process so the elevated copy takes over.

    On non-Windows platforms this function is a no-op.

    Parameters
    ----------
    reason : str
        Human-readable message logged before the elevation attempt.
    """
    if not is_windows():
        return  # Nothing to do on Linux/macOS

    if is_admin():
        return  # Already elevated — proceed normally

    import ctypes
    from loguru import logger

    logger.info(f"Not running as administrator. Requesting elevation: {reason}")

    # Build the argument string, quoting each argv element.
    # For frozen .exe bundles sys.executable IS the .exe, so we pass
    # sys.executable directly.  For source runs we pass the interpreter
    # and the script path.
    executable = sys.executable

    if getattr(sys, "frozen", False):
        # Running as a PyInstaller bundle — the exe IS the entry point
        params = " ".join(f'"{a}"' for a in sys.argv[1:])
    else:
        # Running as a Python script
        params = " ".join(f'"{a}"' for a in sys.argv)

    ret = ctypes.windll.shell32.ShellExecuteW(
        None,       # parent hwnd
        "runas",    # verb — triggers UAC prompt
        executable,
        params,
        None,       # working directory (inherit)
        1,          # SW_SHOWNORMAL
    )

    if ret <= 32:
        # ShellExecuteW returns a value > 32 on success
        logger.error(
            f"Failed to request administrator privileges (ShellExecuteW returned {ret}). "
            "Try running the terminal as Administrator manually."
        )
        # Continue as non-admin rather than crashing
        return

    # The elevated process is now starting — exit this one.
    sys.exit(0)
