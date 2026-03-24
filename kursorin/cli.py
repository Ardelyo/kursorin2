"""
KURSORIN CLI — Rich Terminal Interface

Full-featured command-line interface for KURSORIN with styled output,
diagnostics, configuration management, and live tracking dashboard.
"""

import sys
import time
import platform
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.tree import Tree
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.live import Live
from rich.layout import Layout
from rich.columns import Columns
from rich import box
from loguru import logger


console = Console()

# ─── Brand ────────────────────────────────────────────────────────────────────

BANNER = r"""
[bold cyan]
  ██╗  ██╗██╗   ██╗██████╗ ███████╗ ██████╗ ██████╗ ██╗███╗   ██╗
  ██║ ██╔╝██║   ██║██╔══██╗██╔════╝██╔═══██╗██╔══██╗██║████╗  ██║
  █████╔╝ ██║   ██║██████╔╝███████╗██║   ██║██████╔╝██║██╔██╗ ██║
  ██╔═██╗ ██║   ██║██╔══██╗╚════██║██║   ██║██╔══██╗██║██║╚██╗██║
  ██║  ██╗╚██████╔╝██║  ██║███████║╚██████╔╝██║  ██║██║██║ ╚████║
  ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝
[/bold cyan]
[dim]  Webcam-Based Human-Computer Interaction System[/dim]
[dim]  v1.0.0 · Hands-free cursor control via head, hand & eye tracking[/dim]
"""

COLORS = {
    "primary": "cyan",
    "accent": "#06d6a0",
    "warn": "#f59e0b",
    "error": "#ef4444",
    "success": "#06d6a0",
    "muted": "dim",
    "bg": "#0a0f1a",
}


def _print_banner():
    console.print(BANNER)


def _status_badge(ok: bool, label_ok: str = "OK", label_fail: str = "FAIL") -> str:
    if ok:
        return f"[bold {COLORS['success']}]● {label_ok}[/]"
    return f"[bold {COLORS['error']}]○ {label_fail}[/]"


# ─── CLI Group ────────────────────────────────────────────────────────────────

@click.group(invoke_without_command=True)
@click.option("--version", is_flag=True, help="Show version and exit.")
@click.pass_context
def cli(ctx, version):
    """KURSORIN — Webcam-based hands-free computer control."""
    if version:
        from kursorin import __version__
        console.print(f"[bold cyan]KURSORIN[/] v{__version__}")
        return
    if ctx.invoked_subcommand is None:
        _print_banner()
        console.print(
            Panel(
                "[bold]Commands:[/]\n\n"
                "  [cyan]start[/]      Start tracking engine\n"
                "  [cyan]config[/]     Show or edit configuration\n"
                "  [cyan]calibrate[/]  Run eye calibration\n"
                "  [cyan]status[/]     Show system status\n"
                "  [cyan]doctor[/]     Diagnose system health\n"
                "  [cyan]gui[/]        Launch the GUI application\n\n"
                "[dim]Run [bold]kursorin <command> --help[/bold] for more info.[/dim]",
                title="[bold cyan]⌘ Quick Reference[/]",
                border_style="cyan",
                padding=(1, 2),
            )
        )


# ─── START ────────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--config", "config_path", default=None, type=click.Path(exists=True),
              help="Path to configuration file (YAML/JSON).")
@click.option("--headless", is_flag=True, help="Run without video preview window.")
@click.option("--scenario", type=click.Choice(["default", "hands-free", "no-head"]),
              default="default", help="Tracking scenario preset.")
def start(config_path, headless, scenario):
    """Start the KURSORIN tracking engine."""
    _print_banner()

    from kursorin.config import load_config, KursorinConfig

    # Load config
    with console.status("[cyan]Loading configuration...[/]", spinner="dots"):
        config = load_config(config_path)
        time.sleep(0.3)

    # Apply scenario
    if scenario == "hands-free":
        config.tracking.hand_enabled = False
        config.click.pinch_click_enabled = False
    elif scenario == "no-head":
        config.tracking.head_enabled = False

    if headless:
        config.ui.show_preview = False
        config.ui.show_gui = False

    # Show config summary
    _show_config_summary(config)

    console.print()
    console.print(
        f"[bold {COLORS['success']}]▶ Starting engine...[/]  "
        f"[dim](Press Ctrl+C to stop)[/dim]"
    )
    console.print()

    # Start engine
    try:
        from kursorin.core.kursorin_engine import KursorinEngine
        engine = KursorinEngine(config)
        engine.start()

        # Live dashboard
        _run_live_dashboard(engine)

    except KeyboardInterrupt:
        console.print(f"\n[{COLORS['warn']}]⏹ Stopped by user.[/]")
    except Exception as e:
        console.print(f"\n[{COLORS['error']}]✖ Engine error: {e}[/]")
        logger.exception("Engine crashed")
        sys.exit(1)


def _show_config_summary(config):
    """Show a compact config summary table."""
    table = Table(
        title="[bold cyan]Configuration Summary[/]",
        box=box.ROUNDED,
        border_style="cyan",
        show_header=True,
        header_style="bold cyan",
        padding=(0, 1),
    )
    table.add_column("Module", style="bold white", min_width=12)
    table.add_column("Setting", style="white")
    table.add_column("Value", justify="right")

    # Tracking
    table.add_row(
        "🎯 Tracking",
        "Head / Eye / Hand",
        f"{_bool_icon(config.tracking.head_enabled)} / "
        f"{_bool_icon(config.tracking.eye_enabled)} / "
        f"{_bool_icon(config.tracking.hand_enabled)}",
    )
    table.add_row(
        "", "Sensitivity X/Y",
        f"{config.tracking.head_sensitivity_x:.1f} / {config.tracking.head_sensitivity_y:.1f}",
    )

    # Click
    methods = []
    if config.click.blink_click_enabled:
        methods.append("Blink")
    if config.click.dwell_click_enabled:
        methods.append("Dwell")
    if config.click.pinch_click_enabled:
        methods.append("Pinch")
    if config.click.mouth_click_enabled:
        methods.append("Mouth")
    table.add_row("👆 Click", "Methods", ", ".join(methods) or "None")

    # Camera
    table.add_row(
        "📷 Camera",
        "Resolution / FPS",
        f"{config.camera.camera_width}×{config.camera.camera_height} @ {config.camera.target_fps}fps",
    )

    # Performance
    table.add_row(
        "⚡ Perf",
        "Threading / GPU",
        f"{_bool_icon(config.performance.use_threading)} / {_bool_icon(config.performance.use_gpu)}",
    )

    console.print(table)


def _bool_icon(val: bool) -> str:
    return f"[{COLORS['success']}]✓[/]" if val else f"[{COLORS['muted']}]✗[/]"


def _run_live_dashboard(engine):
    """Live-updating terminal dashboard while engine runs."""
    from rich.table import Table as RichTable

    try:
        while engine.is_running:
            table = RichTable(
                box=box.SIMPLE_HEAVY,
                border_style="cyan",
                show_header=False,
                padding=(0, 2),
            )
            table.add_column("Metric", style="bold white", min_width=18)
            table.add_column("Value", justify="right", min_width=12)

            table.add_row("FPS", f"[bold cyan]{engine.fps:.1f}[/]")
            table.add_row("Latency", f"[bold]{engine.latency_ms:.1f}[/] ms")
            table.add_row("Frames", f"{engine._frame_count}")
            table.add_row(
                "State",
                f"[bold {COLORS['success']}]{engine.state.name}[/]",
            )

            uptime = time.time() - engine._start_time if engine._start_time else 0
            mins, secs = divmod(int(uptime), 60)
            table.add_row("Uptime", f"{mins:02d}:{secs:02d}")

            console.clear()
            _print_banner()
            console.print(
                Panel(
                    table,
                    title="[bold cyan]◉ Live Dashboard[/]",
                    border_style="cyan",
                    padding=(1, 2),
                )
            )
            console.print(f"[dim]Press Ctrl+C to stop[/dim]")

            time.sleep(1.0)

    except KeyboardInterrupt:
        engine.stop()
        raise


# ─── CONFIG ───────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("action", required=False, default="show",
                type=click.Choice(["show", "set", "reset", "path"]))
@click.argument("key", required=False)
@click.argument("value", required=False)
def config(action, key, value):
    """Show or edit configuration.

    \b
    Examples:
      kursorin config              Show all settings
      kursorin config show         Show all settings
      kursorin config set tracking.head_sensitivity_x 3.0
      kursorin config path         Show config file path
      kursorin config reset        Reset to defaults
    """
    from kursorin.config import load_config, KursorinConfig

    config_path = Path.home() / ".kursorin" / "config.yaml"

    if action == "path":
        console.print(f"[bold cyan]Config file:[/] {config_path}")
        console.print(
            f"{_status_badge(config_path.exists(), 'exists', 'not found')}"
        )
        return

    if action == "reset":
        cfg = KursorinConfig()
        cfg.to_file(config_path)
        console.print(f"[{COLORS['success']}]✓ Configuration reset to defaults[/]")
        return

    if action == "set":
        if not key or value is None:
            console.print(f"[{COLORS['error']}]Usage: kursorin config set <key> <value>[/]")
            return
        cfg = load_config()
        _set_nested(cfg, key, value)
        cfg.to_file(config_path)
        console.print(f"[{COLORS['success']}]✓ Set {key} = {value}[/]")
        return

    # action == "show"
    cfg = load_config()
    _print_full_config(cfg)


def _set_nested(obj, key: str, value: str):
    """Set a nested attribute like 'tracking.head_sensitivity_x'."""
    parts = key.split(".")
    for part in parts[:-1]:
        obj = getattr(obj, part)

    attr_name = parts[-1]
    current = getattr(obj, attr_name)

    # Type coerce
    if isinstance(current, bool):
        coerced = value.lower() in ("true", "1", "yes")
    elif isinstance(current, int):
        coerced = int(value)
    elif isinstance(current, float):
        coerced = float(value)
    else:
        coerced = value

    setattr(obj, attr_name, coerced)


def _print_full_config(cfg):
    """Print full config as a rich tree."""
    tree = Tree(
        "[bold cyan]⚙ KURSORIN Configuration[/]",
        guide_style="cyan",
    )

    try:
        data = cfg.model_dump()
    except AttributeError:
        data = cfg.dict()

    def _add_branch(parent, d, depth=0):
        for k, v in d.items():
            if isinstance(v, dict):
                branch = parent.add(f"[bold white]{k}[/]")
                _add_branch(branch, v, depth + 1)
            else:
                style = COLORS['accent'] if not isinstance(v, bool) else (
                    COLORS['success'] if v else COLORS['muted']
                )
                parent.add(f"[dim]{k}[/] = [{style}]{v}[/]")

    _add_branch(tree, data)
    console.print(tree)


# ─── STATUS ───────────────────────────────────────────────────────────────────

@cli.command()
def status():
    """Show system status and environment info."""
    _print_banner()

    table = Table(
        title="[bold cyan]System Status[/]",
        box=box.ROUNDED,
        border_style="cyan",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Component", style="bold white", min_width=20)
    table.add_column("Status", min_width=30)

    # Platform
    table.add_row("OS", f"{platform.system()} {platform.release()}")
    table.add_row("Python", f"{platform.python_version()}")
    table.add_row("Architecture", f"{platform.machine()}")

    # Camera check
    camera_ok = _check_camera()
    table.add_row("Camera", _status_badge(camera_ok, "Available", "Not found"))

    # Dependencies
    deps = _check_dependencies()
    for name, ok in deps.items():
        table.add_row(f"  {name}", _status_badge(ok, "Installed", "Missing"))

    # Config
    cfg_path = Path.home() / ".kursorin" / "config.yaml"
    table.add_row("Config File", _status_badge(cfg_path.exists(), str(cfg_path), "Not created"))

    # Calibration
    calib_path = Path.home() / ".kursorin" / "calibration.json"
    table.add_row("Calibration", _status_badge(calib_path.exists(), "Saved", "Not calibrated"))

    console.print(table)


# ─── DOCTOR ───────────────────────────────────────────────────────────────────

@cli.command()
def doctor():
    """Diagnose system health and fix common issues."""
    _print_banner()
    console.print("[bold cyan]🩺 Running diagnostics...[/]\n")

    issues = []
    checks_passed = 0
    total_checks = 0

    # 1. Python version
    total_checks += 1
    py_ver = sys.version_info
    if py_ver >= (3, 8):
        console.print(f"  [{COLORS['success']}]✓[/] Python {py_ver.major}.{py_ver.minor}.{py_ver.micro}")
        checks_passed += 1
    else:
        console.print(f"  [{COLORS['error']}]✗[/] Python {py_ver.major}.{py_ver.minor} (requires 3.8+)")
        issues.append("Upgrade Python to 3.8+")

    # 2. Dependencies
    deps = _check_dependencies()
    for name, ok in deps.items():
        total_checks += 1
        if ok:
            console.print(f"  [{COLORS['success']}]✓[/] {name}")
            checks_passed += 1
        else:
            console.print(f"  [{COLORS['error']}]✗[/] {name} [dim](pip install {name})[/dim]")
            issues.append(f"Install {name}: pip install {name}")

    # 3. Camera
    total_checks += 1
    camera_ok = _check_camera()
    if camera_ok:
        console.print(f"  [{COLORS['success']}]✓[/] Camera accessible")
        checks_passed += 1
    else:
        console.print(f"  [{COLORS['error']}]✗[/] Camera not accessible")
        issues.append("Connect a webcam or check permissions")

    # 4. Data directory
    total_checks += 1
    data_dir = Path.home() / ".kursorin"
    if data_dir.exists():
        console.print(f"  [{COLORS['success']}]✓[/] Data directory exists")
        checks_passed += 1
    else:
        console.print(f"  [{COLORS['warn']}]![/] Data directory missing [dim](will be created on first run)[/dim]")
        checks_passed += 1  # Not a blocker

    # Summary
    console.print()
    if checks_passed == total_checks:
        console.print(
            Panel(
                f"[bold {COLORS['success']}]All {total_checks} checks passed.[/]\n"
                f"[dim]Your system is ready to run KURSORIN.[/dim]",
                title="[bold green]✓ Health Check[/]",
                border_style="green",
            )
        )
    else:
        issue_text = "\n".join(f"  • {i}" for i in issues)
        console.print(
            Panel(
                f"[bold {COLORS['warn']}]{checks_passed}/{total_checks} checks passed.[/]\n\n"
                f"[bold]Recommended fixes:[/]\n{issue_text}",
                title=f"[bold {COLORS['warn']}]⚠ Issues Found[/]",
                border_style=COLORS['warn'],
            )
        )


# ─── CALIBRATE ────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--points", default=9, type=click.IntRange(4, 16),
              help="Number of calibration points (default: 9).")
def calibrate(points):
    """Run eye calibration (launches calibration UI)."""
    _print_banner()
    console.print("[bold cyan]Starting calibration...[/]\n")
    console.print(
        f"  Calibration points: [bold]{points}[/]\n"
        f"  [dim]A fullscreen calibration window will open.[/dim]\n"
        f"  [dim]Look at each dot until it moves to the next position.[/dim]\n"
    )

    try:
        from kursorin.config import load_config
        from kursorin.core.kursorin_engine import KursorinEngine

        config = load_config()
        config.calibration.calibration_points = points

        engine = KursorinEngine(config)
        engine.start()

        # Launch calibration UI
        import tkinter as tk
        from kursorin.ui.calibration_window import CalibrationWindow

        root = tk.Tk()
        root.withdraw()

        def on_done():
            engine.stop_calibration()
            engine.save_calibration()
            console.print(f"\n[{COLORS['success']}]✓ Calibration complete and saved.[/]")
            root.destroy()

        engine.start_calibration()
        CalibrationWindow(root, engine, on_done)
        root.mainloop()

        engine.stop()

    except Exception as e:
        console.print(f"\n[{COLORS['error']}]✖ Calibration failed: {e}[/]")
        sys.exit(1)


# ─── GUI ──────────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--config", "config_path", default=None, type=click.Path(exists=True),
              help="Path to configuration file.")
def gui(config_path):
    """Launch the KURSORIN GUI application."""
    console.print(f"[bold cyan]Launching KURSORIN GUI...[/]")
    from kursorin.app import main
    main()


# ─── Utilities ────────────────────────────────────────────────────────────────

def _check_camera() -> bool:
    """Quick camera availability check."""
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        ok = cap.isOpened()
        cap.release()
        return ok
    except Exception:
        return False


def _check_dependencies() -> dict:
    """Check if required packages are installed."""
    packages = {
        "opencv-python": "cv2",
        "mediapipe": "mediapipe",
        "numpy": "numpy",
        "pyautogui": "pyautogui",
        "scipy": "scipy",
        "pillow": "PIL",
        "pynput": "pynput",
        "screeninfo": "screeninfo",
        "pydantic": "pydantic",
        "loguru": "loguru",
        "rich": "rich",
        "customtkinter": "customtkinter",
    }

    results = {}
    for display_name, import_name in packages.items():
        try:
            __import__(import_name)
            results[display_name] = True
        except ImportError:
            results[display_name] = False

    return results


# ─── Entry Point ──────────────────────────────────────────────────────────────

def main():
    cli()


if __name__ == "__main__":
    main()
