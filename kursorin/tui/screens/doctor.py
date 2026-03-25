"""
KURSORIN TUI — Doctor Screen

Animated diagnostics with sequential check animations.
"""

import importlib.util
import platform
import sys
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import Static, Button, Rule, ProgressBar


class DoctorScreen(Container):
    """System diagnostics view."""

    DEFAULT_CSS = """
    DoctorScreen {
        height: 100%;
    }
    #doctor-results {
        height: 1fr;
        background: #070a14;
        border: round #1e3a5f;
        padding: 1 2;
        overflow-y: auto;
    }
    #doctor-summary {
        height: auto;
        padding: 1 0;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static(
            "[bold #3b82f6]🩺 Doctor[/]  [#64748b]System diagnostics & health check[/]",
            classes="section-title"
        )
        yield Rule()

        yield Button(
            "▶  Run Diagnostics",
            id="btn-run-doctor",
            classes="action-btn -primary"
        )

        yield Static("")
        yield ProgressBar(total=100, show_eta=False, id="doctor-progress")
        yield Static("")

        with VerticalScroll(id="doctor-results"):
            yield Static("", id="doctor-log")
            yield Static("", id="doctor-status")

        yield Static("", id="doctor-summary")

    async def run_diagnostics(self) -> None:
        """Run all diagnostic checks with animated output."""
        results_container = self.query_one("#doctor-results", VerticalScroll)
        summary_widget = self.query_one("#doctor-summary", Static)
        progress = self.query_one("#doctor-progress", ProgressBar)

        log_panel = self.query_one("#doctor-log", Static)
        status_panel = self.query_one("#doctor-status", Static)
        
        # Clear previous results
        results_container.remove_children()
        summary_widget.update("")
        progress.update(progress=0)
        log_panel.update("")
        status_panel.update("")
        
        class DiagResults:
            total = 0
            passed = 0
            fixes = []
            log = ""

        results = DiagResults()

        def add_log(msg: str, log_type: str = "info"):
            results.total += 1
            icon = "✅" if log_type == "pass" else "❌" if log_type == "fail" else "🔵"
            color = "#22c55e" if log_type == "pass" else "#ef4444" if log_type == "fail" else "#3b82f6"
            
            if log_type == "pass":
                results.passed += 1
            
            results.log += f"[{color}]{icon} {msg}[/]\n"
            log_panel.update(results.log)
            status_panel.update(f"Progress: {results.passed}/{results.total} checks passed")

        async def check(name: str, test_fn, fix_msg: str, step: int):
            try:
                result = test_fn()
                if result:
                    add_log(name, log_type="pass")
                else:
                    add_log(name, log_type="fail")
                    results.fixes.append(fix_msg)
            except Exception as e:
                add_log(f"{name} ([#64748b]{e}[/])", log_type="fail")
                results.fixes.append(fix_msg)
            progress.update(progress=step)

        # 1. OS
        await check(
            "OS Compatibility",
            lambda: platform.system() in ("Windows", "Darwin", "Linux"),
            "Unsupported OS.",
            10
        )

        # 2. Python
        await check(
            f"Python {sys.version_info.major}.{sys.version_info.minor}",
            lambda: sys.version_info >= (3, 8),
            "Upgrade Python to 3.8+.",
            20
        )

        # 3. Dependencies
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
            "customtkinter": "pip install customtkinter",
            "textual": "pip install textual",
        }

        step = 20
        step_inc = 60 / len(deps)
        for mod, fix in deps.items():
            await check(
                f"Module: {mod}",
                lambda m=mod: importlib.util.find_spec(m) is not None,
                f"Missing {mod}: {fix}",
                int(step)
            )
            step += step_inc

        # 4. Camera
        def check_cam():
            import cv2
            c = cv2.VideoCapture(0)
            ret = c.isOpened()
            c.release()
            return ret

        await check(
            "Camera accessible",
            check_cam,
            "Camera not accessible. Ensure webcam is connected.",
            90
        )

        # 5. Data dir
        await check(
            "Data directory (~/.kursorin)",
            lambda: (Path.home() / ".kursorin").exists(),
            "Data directory missing (will be created on first run).",
            90
        )

        # 6. Auto-Update Readiness (Git)
        def check_git_ready():
            from kursorin.utils.updater import GitUpdater
            updater = GitUpdater()
            if not updater.check_git_installed():
                return False
            if not updater.is_git_repo():
                success, _ = updater.auto_convert_to_git()
                return success
            return True

        await check(
            "Auto-Update System (Git Tracking)",
            check_git_ready,
            "Git missing or could not track updates. Install Git to enable.",
            100
        )

        # Final status
        if results.passed == results.total:
            status_panel.update("[bold #22c55e]PASS: System is healthy![/]")
            summary_widget.update(
                f"\n[bold #22c55e]✓ All {results.total} checks passed.[/]\n"
                "[#64748b]Your system is ready to run KURSORIN.[/]"
            )
        else:
            status_panel.update(f"[bold #ef4444]FAIL: {results.total - results.passed} issues found[/]")
            fix_text = "\n".join(f"  • {m}" for m in results.fixes)
            summary_widget.update(
                f"\n[bold #ef4444]⚠ {results.passed}/{results.total} checks passed.[/]\n\n"
                f"[bold]Recommended fixes:[/]\n{fix_text}"
            )
