"""
KURSORIN Command Line Interface

A premium terminal interface for managing the KURSORIN engine,
configuration, and diagnostics.
"""

import sys
import time
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.live import Live
from rich.tree import Tree
from loguru import logger

from kursorin.core.kursorin_engine import KursorinEngine
from kursorin.config import load_config
from kursorin import __version__
from kursorin.i18n import t, init_lang, set_lang, get_lang, save_lang


# Initialize rich console with UTF-8 force if on Windows
import os
if os.name == 'nt':
    import sys
    # Force UTF-8 for standard output to avoid CP1252 issues with Rich/Unicode
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

console = Console(force_terminal=True)

# Arctic Terminal Palette
COLORS = {
    "primary": "white",
    "secondary": "bright_blue",
    "accent": "cyan",
    "success": "green",
    "warning": "yellow",
    "error": "red",
    "muted": "bright_black"
}

BANNER = f"""[{COLORS['accent']}]
  ██╗  ██╗██╗   ██╗██████╗ ███████╗ ██████╗ ██████╗ ██╗███╗   ██╗
  ██║ ██╔╝██║   ██║██╔══██╗██╔════╝██╔═══██╗██╔══██╗██║████╗  ██║
  █████╔╝ ██║   ██║██████╔╝███████╗██║   ██║██████╔╝██║██╔██╗ ██║
  ██╔═██╗ ██║   ██║██╔══██╗╚════██║██║   ██║██╔══██╗██║██║╚██╗██║
  ██║  ██╗╚██████╔╝██║  ██║███████║╚██████╔╝██║  ██║██║██║ ╚████║
  ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝[/]

  [{COLORS['secondary']}]{t('cli.subtitle')}[/]
  [{COLORS['muted']}]{t('cli.version_line')}[/]
"""


# ─── MAIN ENTRY ───────────────────────────────────────────────────────────────

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """
    KURSORIN — Webcam-based hands-free computer control.
    """
    init_lang()

    # If no subcommand provided, launch interactive TUI
    if ctx.invoked_subcommand is None:
        try:
            from kursorin.tui.app import run_tui
            run_tui()
        except ImportError:
            # Fallback to static help if textual not installed
            console.print(BANNER)
            
            table = Table(title=t('cli.quick_ref'), show_header=True, header_style="bold cyan")
            table.add_column("Command", style="cyan", width=20)
            table.add_column("Description", style="white")
            
            table.add_row("kursorin start", t('cli.cmd.start'))
            table.add_row("kursorin gui", t('cli.cmd.gui'))
            table.add_row("kursorin config", t('cli.cmd.config'))
            table.add_row("kursorin status", t('cli.cmd.status'))
            table.add_row("kursorin doctor", t('cli.cmd.doctor'))
            table.add_row("kursorin calibrate", t('cli.cmd.calibrate'))
            table.add_row("kursorin lang", t('cli.cmd.lang'))
            table.add_row("kursorin update", t('cli.cmd.update'))
            table.add_row("kursorin info", t('cli.cmd.info'))
            
            console.print(Panel(table, border_style=COLORS['accent'], expand=False))
            console.print(f"\n[{COLORS['muted']}]{t('cli.run_help')}[/]")
        except Exception as e:
            console.print(f"[{COLORS['error']}]TUI Error: {e}[/]")
            console.print(f"[{COLORS['muted']}]Falling back to CLI mode. Use 'kursorin start' etc.[/]")


# ─── START ────────────────────────────────────────────────────────────────────

@cli.command()
@click.option('--scenario', type=click.Choice(['default', 'hands-free', 'no-head']), default='default', help='Tracking scenario preset.')
def start(scenario):
    """Start the KURSORIN tracking engine."""
    init_lang()
    from kursorin.utils.logger import setup_logging
    
    console.print(BANNER)
    console.print(f"[{COLORS['muted']}]{t('start.loading_config')}[/]")
    
    config = load_config()
    setup_logging(config)

    # Optional update check
    try:
        from kursorin.utils.updater import GitUpdater
        updater = GitUpdater()
        if updater.check_git_installed() and updater.is_git_repo():
            available, _ = updater.check_for_updates()
            if available:
                console.print(f"\n[bold yellow]! {t('update.available')}[/]\n")
    except Exception:
        pass

    # Apply scenario
    if scenario == 'hands-free':
        config.tracking.hand_enabled = False
        config.click.pinch_click_enabled = False
    elif scenario == 'no-head':
        config.tracking.head_enabled = False

    engine = KursorinEngine(config)

    console.print(f"[{COLORS['accent']}]{t('start.starting')}[/]")
    console.print(f"[{COLORS['warning']}]{t('start.press_ctrl_c')}[/]\n")

    layout = _create_dashboard_layout()
    engine.start()

    try:
        with Live(layout, refresh_per_second=4) as live:
            while engine.is_running:
                _update_dashboard(layout, engine, config)
                time.sleep(0.25)
    except KeyboardInterrupt:
        console.print(f"\n[{COLORS['warning']}]{t('start.stopped')}[/]")
    except Exception as e:
        console.print(f"\n[{COLORS['error']}]{t('start.engine_error')}: {e}[/]")
        logger.exception("Engine crashed")
    finally:
        engine.stop()


def _create_dashboard_layout() -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
    )
    layout["main"].split_row(
        Layout(name="metrics", ratio=1),
        Layout(name="config", ratio=1),
    )
    return layout


def _update_dashboard(layout: Layout, engine: KursorinEngine, config):
    # Header
    state_color = "green" if engine.state.name == "TRACKING" else "yellow"
    header_content = f"[{state_color} bold]● {engine.state.name}[/] | [dim]{time.strftime('%H:%M:%S')}[/]"
    layout["header"].update(Panel(header_content, border_style=state_color, title=f"[bold]{t('start.live_dashboard')}[/]"))

    # Metrics
    metrics_table = Table(show_header=False, expand=True, box=None)
    metrics_table.add_column("Metric", style=COLORS['muted'])
    metrics_table.add_column("Value", style=COLORS['primary'], justify="right")
    
    metrics_table.add_row(t('metric.fps'), f"[bold {COLORS['accent']}]{engine.fps:.1f}[/]")
    metrics_table.add_row(t('metric.latency'), f"{engine.latency_ms:.0f} ms")
    metrics_table.add_row(t('metric.frames'), str(engine._frame_count))
    uptime = time.time() - engine._start_time if engine._start_time else 0
    metrics_table.add_row(t('metric.uptime'), f"{uptime:.1f}s")

    layout["metrics"].update(Panel(metrics_table, title=f"[{COLORS['secondary']}]{t('status.title')}[/]", border_style=COLORS['secondary']))

    # Config Summary
    cfg_table = Table(show_header=False, expand=True, box=None)
    cfg_table.add_column("Key", style=COLORS['muted'])
    cfg_table.add_column("Val", style="white")
    
    cfg_table.add_row(t('settings.head_tracking'), "[green]ON[/]" if config.tracking.head_enabled else "[red]OFF[/]")
    cfg_table.add_row(t('settings.eye_tracking'), "[green]ON[/]" if config.tracking.eye_enabled else "[red]OFF[/]")
    cfg_table.add_row(t('settings.hand_tracking'), "[green]ON[/]" if config.tracking.hand_enabled else "[red]OFF[/]")
    cfg_table.add_row(t('settings.camera_index'), str(config.camera.camera_index))

    layout["config"].update(Panel(cfg_table, title=f"[{COLORS['secondary']}]{t('start.config_summary')}[/]", border_style=COLORS['secondary']))


# ─── CONFIGURATION ────────────────────────────────────────────────────────────

@cli.group()
def config():
    """Show or edit configuration."""
    init_lang()
    pass


@config.command(name='path')
def config_path():
    from pathlib import Path
    cp = Path.home() / ".kursorin" / "config.yaml"
    if cp.exists():
        console.print(f"[{COLORS['muted']}]{t('config.config_file')}:[/]\n[{COLORS['accent']}]{cp}[/]")
    else:
        console.print(f"[{COLORS['muted']}]{t('config.config_file')}:[/]\n[dim]{cp}[/] ( [{COLORS['error']}]{t('status.not_found')}[/] )")


@config.command(name='reset')
def config_reset():
    from kursorin.config import KursorinConfig
    from pathlib import Path
    cfg = KursorinConfig()
    cfg.to_file(Path.home() / ".kursorin" / "config.yaml")
    console.print(f"[{COLORS['success']}]✓ {t('config.reset_ok')}[/]")


@config.command(name='set')
@click.argument('key')
@click.argument('value')
def config_set(key, value):
    from pathlib import Path
    config_path = Path.home() / ".kursorin" / "config.yaml"
    cfg = load_config()
    _set_nested(cfg, key, value)
    cfg.to_file(config_path)
    console.print(f"[{COLORS['success']}]✓ {t('config.set_ok')} {key} = {value}[/]")


@config.command(name='show')
def config_show():
    cfg = load_config()
    _print_full_config(cfg)


def _set_nested(obj, key, value):
    parts = key.split(".")
    target = obj
    for part in parts[:-1]:
        target = getattr(target, part)

    attr_name = parts[-1]
    current_val = getattr(target, attr_name)

    if isinstance(current_val, bool):
        coerced = value.lower() in ("true", "1", "yes")
    elif isinstance(current_val, int):
        coerced = int(value)
    elif isinstance(current_val, float):
        coerced = float(value)
    else:
        coerced = value

    setattr(target, attr_name, coerced)


def _print_full_config(cfg):
    tree = Tree(
        f"[bold cyan]⚙ {t('config.title')}[/]",
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
    """Show system status."""
    import platform
    import sys
    import importlib.util
    from pathlib import Path
    init_lang()

    console.print(BANNER)

    table = Table(title=t('status.title'), show_header=True, header_style="bold cyan")
    table.add_column(t('status.component'), style="white", width=22)
    table.add_column(t('status.title'), style="cyan")

    table.add_row("OS", f"{platform.system()} {platform.release()}")
    table.add_row("Python", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    table.add_row("Architecture", platform.machine())

    # Check camera basics
    try:
        import cv2
        cam = cv2.VideoCapture(0)
        table.add_row("Camera", f"[green]● {t('status.available')}[/]" if cam.isOpened() else f"[red]○ {t('status.not_found')}[/]")
        cam.release()
    except ImportError:
        table.add_row("Camera", f"[red]○ {t('status.missing')}[/]")

    # Dependencies
    deps = [
        "opencv-python", "mediapipe", "numpy", "pyautogui", 
        "scipy", "pillow", "pynput", "screeninfo", "pydantic", 
        "loguru", "rich", "customtkinter"
    ]
    
    for dep in deps:
        # Convert pip name to module name roughly
        mod_name = dep.replace("-python", "").replace("-", "_")
        if mod_name == "pillow": mod_name = "PIL"
        if mod_name == "opencv_python": mod_name = "cv2"
        
        spec = importlib.util.find_spec(mod_name)
        if spec is not None:
            table.add_row(f"  {dep}", f"[green]● {t('status.installed')}[/]")
        else:
            table.add_row(f"  {dep}", f"[red]○ {t('status.missing')}[/]")

    # Files
    cfg_path = Path.home() / ".kursorin" / "config.yaml"
    calib_path = Path.home() / ".kursorin" / "calibration.json"
    
    table.add_row("Config File", f"[green]● {t('status.saved')}[/]" if cfg_path.exists() else f"[dim]○ {t('status.not_created')}[/]")
    table.add_row("Calibration", f"[green]● {t('status.saved')}[/]" if calib_path.exists() else f"[dim]○ {t('status.not_calibrated')}[/]")

    console.print(Panel(table, border_style=COLORS['secondary'], expand=False))


# ─── DOCTOR ───────────────────────────────────────────────────────────────────

@cli.command()
def doctor():
    """Diagnose system health and fix common issues."""
    import platform
    import importlib.util
    from pathlib import Path
    init_lang()
    
    # Use a dict for mutable state in the closure
    state = {"passed": 0, "total": 0}
    issues = []

    def check(name: str, test_fn, fix_msg: str):
        state["total"] += 1
        try:
            if test_fn():
                console.print(f"  [green]✓[/] {name}")
                state["passed"] += 1
            else:
                console.print(f"  [red]✖[/] {name}")
                issues.append(fix_msg)
        except Exception as e:
            console.print(f"  [red]✖[/] {name} ({e})")
            issues.append(fix_msg)

    # 1. Check OS
    check("OS Compatibility", lambda: platform.system() in ("Windows", "Darwin", "Linux"), "Unsupported OS. KURSORIN requires Windows, macOS, or Linux.")
    
    # 2. Check Python
    import sys
    check("Python Version", lambda: sys.version_info >= (3, 8), "Upgrade Python to 3.8 or newer.")

    # 3. Check Dependencies
    deps = {
        "cv2": "pip install opencv-python",
        "mediapipe": "pip install mediapipe",
        "numpy": "pip install numpy",
        "pyautogui": "pip install pyautogui",
        "scipy": "pip install scipy",
        "PIL": "pip install pillow",
        "pynput": "pip install pynput",
        "screeninfo": "pip install screeninfo",
        "pydantic": "pip install pydantic",
        "rich": "pip install rich",
        "customtkinter": "pip install customtkinter"
    }

    for mod, fix in deps.items():
        check(f"Module: {mod}", lambda m=mod: importlib.util.find_spec(m) is not None, f"Missing {mod}: Run '{fix}'")

    # 4. Check Camera Camera
    def check_cam():
        import cv2
        c = cv2.VideoCapture(0)
        ret = c.isOpened()
        c.release()
        return ret
    check(t('doctor.camera_ok'), check_cam, f"{t('doctor.camera_fail')} -> Ensure webcam is connected and not used by another app.")

    # 5. Check Dirs
    def check_dir():
        d = Path.home() / ".kursorin"
        return d.exists()
    check(t('doctor.data_dir_ok'), check_dir, f"{t('doctor.data_dir_missing')}")

    console.print()

    if state["passed"] == state["total"]:
        success = Panel(
            f"{t('doctor.all_passed', n=state['total'])}\n{t('doctor.system_ready')}",
            title=f"[bold green]✓ {t('doctor.health_check')}[/]",
            border_style="green"
        )
        console.print(success)
    else:
        err = Panel(
            f"[red]{t('doctor.passed_n', passed=state['passed'], total=state['total'])}[/]\n\n[bold]{t('doctor.recommended_fixes')}:[/]\n" + 
            "\n".join(f"  • {msg}" for msg in set(issues)),
            title=f"[bold red]⚠ {t('doctor.issues_found')}[/]",
            border_style="red"
        )
        console.print(err)


# ─── CALIBRATE ────────────────────────────────────────────────────────────────

@cli.command()
def calibrate():
    """Run eye calibration."""
    init_lang()
    from kursorin.core.kursorin_engine import KursorinEngine
    import tkinter as tk
    
    console.print(BANNER)
    console.print(f"[{COLORS['accent']}]{t('calibrate.starting')}[/]")
    console.print(f"[{COLORS['muted']}]{t('calibrate.instruction')}[/]")

    cfg = load_config()
    engine = KursorinEngine(cfg)
    
    # Needs a Tk root since we are not in app_window
    root = tk.Tk()
    root.withdraw() # hide root
    
    engine.start()
    engine.start_calibration()
    
    def on_complete():
        engine.stop_calibration()
        engine.save_calibration()
        engine.stop()
        console.print(f"\n[{COLORS['success']}]✓ {t('calibrate.complete')}[/]")
        root.quit()
        
    try:
        from kursorin.ui.calibration_window import CalibrationWindow
        win = CalibrationWindow(root, engine, on_complete)
        root.mainloop()
    except KeyboardInterrupt:
        console.print(f"\n[{COLORS['warning']}]{t('start.stopped')}[/]")
        engine.stop()
        root.destroy()
    except Exception as e:
        console.print(f"\n[{COLORS['error']}]{t('calibrate.failed')}: {e}[/]")
        engine.stop()
        root.destroy()


# ─── GUI ──────────────────────────────────────────────────────────────────────

@cli.command()
def gui():
    """Launch GUI application."""
    import kursorin.app
    kursorin.app.main()


# ─── LANG (I18N) ──────────────────────────────────────────────────────────────

@cli.command()
@click.argument('language', required=False, type=click.Choice(['en', 'id']))
def lang(language):
    """Switch language (en/id)."""
    init_lang()
    if not language:
        # Show current
        console.print(f"[{COLORS['primary']}]{t('lang.current')}[/]")
        return
        
    set_lang(language)
    save_lang(language)
    
    # Reload lang name for feedback
    lang_name = t('lang.english') if language == 'en' else t('lang.indonesian')
    console.print(f"[{COLORS['success']}]✓ {t('lang.switched')} {lang_name}[/]")


# ─── INFO ─────────────────────────────────────────────────────────────────────

@cli.command()
def stop():
    """Emergency stop: kills all running KURSORIN processes."""
    import psutil
    import os
    init_lang()
    
    found = False
    current_pid = os.getpid()
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline')
            if not cmdline: continue
            
            # Check for "python -m kursorin" or similar
            cmd_str = " ".join(cmdline).lower()
            if ("kursorin" in cmd_str) and (proc.info['pid'] != current_pid):
                console.print(f"[{COLORS['warning']}]Terminating process {proc.info['pid']} ({proc.info['name']})...[/]")
                proc.terminate()
                found = True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
            
    if found:
        console.print(f"[{COLORS['success']}]✓ {t('status.stopped')}[/]")
    else:
        console.print(f"[{COLORS['muted']}]{t('status.not_running')}[/]")

@cli.command()
def info():
    """Show detailed system info."""
    init_lang()
    cfg = load_config()
    
    console.print(f"[bold cyan]{t('info.title')}[/]")
    
    # Module States
    table = Table(show_header=True, header_style="bold white")
    table.add_column(t('module.module'), style="cyan")
    table.add_column(t('metric.state'), style="white")
    table.add_column("Details", style="dim")
    
    table.add_row(t('module.tracking'), "[green]ON[/]" if cfg.tracking.head_enabled or cfg.tracking.eye_enabled or cfg.tracking.hand_enabled else "[red]OFF[/]", f"Head:{cfg.tracking.head_enabled} Eye:{cfg.tracking.eye_enabled} Hand:{cfg.tracking.hand_enabled}")
    table.add_row(t('module.click'), "[green]ON[/]", f"Blink:{cfg.click.blink_click_enabled} Dwell:{cfg.click.dwell_click_enabled} Pinch:{cfg.click.pinch_click_enabled}")
    table.add_row(t('module.camera'), "[green]ON[/]", f"Idx:{cfg.camera.camera_index} FPS:{cfg.camera.target_fps}")
    table.add_row(t('module.performance'), "Configured", f"Threads:{cfg.performance.use_threading} GPU:{cfg.performance.use_gpu}")
    
    console.print(table)


# ─── UPDATE ───────────────────────────────────────────────────────────────────

@cli.command()
@click.option('--force', is_flag=True, help='Force update and overwrite local changes.')
def update(force):
    """Check and pull updates via git."""
    init_lang()
    from kursorin.utils.updater import GitUpdater
    updater = GitUpdater()

    console.print(BANNER)
    
    with console.status(f"[{COLORS['accent']}]{t('update.checking')}[/]", spinner="dots"):
        if not updater.check_git_installed():
            console.print(f"[{COLORS['error']}]✖ {t('update.error_git')}[/]")
            return
        
        if not updater.is_git_repo():
            console.print(f"[{COLORS['warning']}]⚠ Not a Git repository. Attempting auto-conversion to Git...[/]")
            success, git_msg = updater.auto_convert_to_git()
            if not success:
                console.print(f"[{COLORS['error']}]✖ Auto-conversion failed: {git_msg}[/]")
                return
            console.print(f"[{COLORS['success']}]✓ Successfully converted to a tracked Git repository![/]")

        available, msg = updater.check_for_updates()
        
    if not available:
        if "Up to date" in msg:
            console.print(f"[{COLORS['success']}]✓ {t('update.up_to_date')}[/]")
        else:
            console.print(f"[{COLORS['warning']}]! {msg}[/]")
        return

    # If update available, pull it
    with console.status(f"[{COLORS['accent']}]{t('update.pulling')}[/]", spinner="dots"):
        success, pull_msg = updater.pull_update(force=force)

    if success:
        console.print(f"[{COLORS['success']}]✓ {t('update.success')}[/]")
    else:
        if "Local changes detected" in pull_msg:
            console.print(f"[{COLORS['error']}]✖ {t('update.error_local')}[/]")
        else:
            console.print(f"[{COLORS['error']}]✖ {pull_msg}[/]")


def main():
    cli()

if __name__ == "__main__":
    main()
