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
        background: #050a12;
        border: round #0d2137;
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
            "[bold #06d6a0]🩺 Doctor[/]  [#576574]System diagnostics & health check[/]",
            classes="section-title"
        )
        yield Rule(style="#0d2137")

        yield Button(
            "▶  Run Diagnostics",
            id="btn-run-doctor",
            classes="action-btn -primary"
        )

        yield Static("")
        yield ProgressBar(total=100, show_eta=False, id="doctor-progress")
        yield Static("")

        yield VerticalScroll(id="doctor-results")
        yield Static("", id="doctor-summary")

    async def run_diagnostics(self) -> None:
        """Run all diagnostic checks with animated output."""
        results_container = self.query_one("#doctor-results", VerticalScroll)
        summary_widget = self.query_one("#doctor-summary", Static)
        progress = self.query_one("#doctor-progress", ProgressBar)

        # Clear previous results
        results_container.remove_children()
        summary_widget.update("")
        progress.update(progress=0)

        checks = []
        passed = 0
        total = 0

        async def check(name: str, test_fn, fix_msg: str, step: int):
            nonlocal passed, total
            total += 1
            try:
                result = test_fn()
                if result:
                    await results_container.mount(
                        Static(f"  [#06d6a0]✓[/] {name}")
                    )
                    passed += 1
                else:
                    await results_container.mount(
                        Static(f"  [#ee5a6f]✖[/] {name}")
                    )
                    checks.append(fix_msg)
            except Exception as e:
                await results_container.mount(
                    Static(f"  [#ee5a6f]✖[/] {name} [#576574]({e})[/]")
                )
                checks.append(fix_msg)
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
            100
        )

        # Summary
        if passed == total:
            summary_widget.update(
                f"\n[bold #06d6a0]✓ All {total} checks passed.[/]\n"
                "[#576574]Your system is ready to run KURSORIN.[/]"
            )
        else:
            fix_text = "\n".join(f"  • {m}" for m in checks)
            summary_widget.update(
                f"\n[bold #ee5a6f]⚠ {passed}/{total} checks passed.[/]\n\n"
                f"[bold]Recommended fixes:[/]\n{fix_text}"
            )
