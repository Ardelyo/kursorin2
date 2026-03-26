"""
KURSORIN TUI — Main Application

A single-view command-center TUI. Everything lives in one scrollable view.
Type commands in the prompt bar to reveal dynamic panels below.
"""

from pathlib import Path
from typing import Optional, Generator

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, Center, VerticalScroll
from textual.widgets import (
    Static, Button, Footer, Input, Switch, Rule,
    ProgressBar, TabbedContent, TabPane,
)
from textual.widget import Widget
from textual.reactive import reactive

from kursorin import __version__
from kursorin.config import load_config, KursorinConfig
from kursorin.core.kursorin_engine import KursorinEngine
from kursorin.i18n import t, init_lang, get_lang, set_lang, save_lang
import asyncio
import time


CSS_PATH = Path(__file__).parent / "app.tcss"

# ── ASCII Logo ────────────────────────────────────────────────────────────────

LOGO_ART = """\
[bold #3b82f6]██╗  ██╗[#2563eb]██╗   ██╗[#3b82f6]██████╗ [#2563eb]███████╗[#3b82f6] ██████╗ [#2563eb]██████╗ [#3b82f6]██╗[#2563eb]███╗   ██╗[/]
[bold #3b82f6]██║ ██╔╝[#2563eb]██║   ██║[#3b82f6]██╔══██╗[#2563eb]██╔════╝[#3b82f6]██╔═══██╗[#2563eb]██╔══██╗[#3b82f6]██║[#2563eb]████╗  ██║[/]
[bold #60a5fa]█████╔╝ [#3b82f6]██║   ██║[#60a5fa]██████╔╝[#3b82f6]███████╗[#60a5fa]██║   ██║[#3b82f6]██████╔╝[#60a5fa]██║[#3b82f6]██╔██╗ ██║[/]
[bold #3b82f6]██╔═██╗ [#2563eb]██║   ██║[#3b82f6]██╔══██╗[#2563eb]╚════██║[#3b82f6]██║   ██║[#2563eb]██╔══██╗[#3b82f6]██║[#2563eb]██║╚██╗██║[/]
[bold #3b82f6]██║  ██╗[#2563eb]╚██████╔╝[#3b82f6]██║  ██║[#2563eb]███████║[#3b82f6]╚██████╔╝[#2563eb]██║  ██║[#3b82f6]██║[#2563eb]██║ ╚████║[/]
[bold #1e3a5f]╚═╝  ╚═╝[#1e3a5f] ╚═════╝ [#1e3a5f]╚═╝  ╚═╝[#1e3a5f]╚══════╝[#1e3a5f] ╚═════╝ [#1e3a5f]╚═╝  ╚═╝[#1e3a5f]╚═╝[#1e3a5f]╚═╝  ╚═══╝[/]"""


# ── Inline widgets ────────────────────────────────────────────────────────────

class StatCard(Widget):
    """A compact metric card."""
    def __init__(self, value: str, label: str, **kwargs):
        super().__init__(**kwargs)
        self._value = value
        self._label = label

    def render(self) -> str:
        return f"[bold #3b82f6]{self._value}[/]\n[#64748b]{self._label}[/]"

    def update_value(self, value: str):
        self._value = value
        self.refresh()


class StatusDot(Widget):
    """Inline status indicator."""
    def __init__(self, label: str, status: str = "idle", **kwargs):
        super().__init__(**kwargs)
        self._label = label
        self._status = status

    def render(self) -> str:
        colors = {"online": "#22c55e", "warning": "#f59e0b", "offline": "#ef4444", "idle": "#64748b"}
        symbols = {"online": "●", "warning": "●", "offline": "●", "idle": "○"}
        c = colors.get(self._status, "#64748b")
        s = symbols.get(self._status, "○")
        return f"[{c}]{s}[/] [#94a3b8]{self._label}[/]"


class SettingToggle(Horizontal):
    """A setting row with label + switch."""
    DEFAULT_CSS = """
    SettingToggle { height: 3; padding: 0 1; }
    SettingToggle:hover { background: #0f1e33; }
    """
    def __init__(self, label: str, value: bool, key: str, **kwargs):
        super().__init__(**kwargs)
        self._label = label
        self._value = value
        self._key = key

    def compose(self) -> Generator[Widget, None, None]:
        yield Static(self._label, classes="setting-label")
        yield Switch(value=self._value, id=f"sw-{self._key}")


class SettingInput(Horizontal):
    """A setting row with label + input."""
    DEFAULT_CSS = """
    SettingInput { height: 3; padding: 0 1; }
    SettingInput:hover { background: #0f1e33; }
    """
    def __init__(self, label: str, value: str, key: str, **kwargs):
        super().__init__(**kwargs)
        self._label = label
        self._value = value
        self._key = key

    def compose(self) -> Generator[Widget, None, None]:
        yield Static(self._label, classes="setting-label")
        yield Input(value=self._value, id=f"inp-{self._key}", classes="setting-input")


# ── Main App ──────────────────────────────────────────────────────────────────

class KursorinTUI(App):
    """KURSORIN — Single-view command center."""

    CSS_PATH = "app.tcss"
    TITLE = "KURSORIN"
    SUB_TITLE = "Webcam-Based HCI System"
    
    engine: Optional[KursorinEngine] = None
    _engine_worker = None

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("escape", "collapse_all", "Collapse", show=True),
        Binding("ctrl+l", "toggle_lang", "Language", show=True),
        Binding("ctrl+p", "command_palette", "Commands", show=True),
    ]

    def compose(self) -> Generator[Widget, None, None]:
        init_lang()

        # ── Header ──
        yield Static(
            f"  [bold #3b82f6]⬡ KURSORIN[/]  "
            f"[#1e3a5f]│[/]  "
            f"[#64748b]v{__version__}[/]  "
            f"[#1e3a5f]│[/]  "
            f"[#64748b]{t('cli.subtitle')}[/]",
            id="header-bar"
        )

        # ── Scrollable body ──
        with VerticalScroll(id="main-scroll"):

            # Logo
            with Center():
                yield Static(LOGO_ART, id="logo-art")
            with Center():
                yield Static(
                    f"[#64748b]{t('cli.subtitle')}[/]",
                    id="logo-subtitle"
                )
            
            # Command input
            yield Static("", classes="spacer-sm")
            with Center():
                yield Input(
                    placeholder=f"  {t('cli.quick_ref')}:  start · settings · doctor · update · lang · quit",
                    id="cmd-input"
                )

            # Hint chips
            with Center():
                yield Static(
                    "[#1e3a5f]─── [/]"
                    "[#3b82f6]start[/] [#475569]·[/] "
                    "[#3b82f6]settings[/] [#475569]·[/] "
                    "[#3b82f6]doctor[/] [#475569]·[/] "
                    "[#3b82f6]update[/] [#475569]·[/] "
                    "[#3b82f6]calibrate[/] [#475569]·[/] "
                    "[#3b82f6]gui[/] [#475569]·[/] "
                    "[#3b82f6]lang[/] [#475569]·[/] "
                    "[#3b82f6]quit[/]"
                    " [#1e3a5f]───[/]",
                    id="hint-chips"
                )

            yield Static("", classes="spacer-sm")

            # ── DASHBOARD PANEL ──
            with Center():
                with Container(id="panel-dashboard", classes="panel"):
                    yield Static("[bold #3b82f6]⬡ Dashboard[/]  [#64748b]System overview & quick actions[/]", classes="panel-title")
                    yield Rule()
                    with Horizontal(id="status-dots"):
                        yield StatusDot("Camera", "idle", id="dot-camera")
                        yield Static("  ")
                        yield StatusDot("Head", "idle", id="dot-head")
                        yield Static("  ")
                        yield StatusDot("Eye", "idle", id="dot-eye")
                        yield Static("  ")
                        yield StatusDot("Hand", "idle", id="dot-hand")
                    yield Static("", classes="spacer-xs")
                    with Horizontal(id="stats-row"):
                        yield StatCard("—", "FPS", id="stat-fps")
                        yield StatCard("—", "Latency", id="stat-latency")
                        yield StatCard("—", "Uptime", id="stat-uptime")
                        yield StatCard(f"v{__version__}", "Version", id="stat-version")
                    yield Static("", classes="spacer-xs")
                    yield Button("▶  Start Tracking", id="btn-start", classes="action-btn -primary")
                    yield Button("🎯  Calibrate Eyes", id="btn-calibrate", classes="action-btn")
                    yield Button("🖥  Launch GUI", id="btn-gui", classes="action-btn")

            # ── SETTINGS PANEL ──
            with Center():
                with Container(id="panel-settings", classes="panel"):
                    yield Static("[bold #3b82f6]⚙  Settings[/]  [#64748b]Configure KURSORIN[/]", classes="panel-title")
                    yield Rule()
                    # Settings content is loaded on demand
                    yield Static("[#64748b]Loading settings...[/]", id="settings-placeholder")

            # ── DOCTOR PANEL ──
            with Center():
                with Container(id="panel-doctor", classes="panel"):
                    yield Static("[bold #3b82f6]🩺 Doctor[/]  [#64748b]System diagnostics[/]", classes="panel-title")
                    yield Rule()
                    yield Button("▶  Run Diagnostics", id="btn-run-doctor", classes="action-btn -primary")
                    yield Static("", classes="spacer-xs")
                    yield ProgressBar(total=100, show_eta=False, id="doctor-progress")
                    yield Static("", id="doctor-log")
                    yield Static("", id="doctor-summary")

            # ── UPDATE PANEL ──
            with Center():
                with Container(id="panel-update", classes="panel"):
                    yield Static("[bold #3b82f6]🔄 Updates[/]  [#64748b]Keep KURSORIN up to date[/]", classes="panel-title")
                    yield Rule()
                    yield Static(f"[#e2e8f0]Current:[/] [bold #3b82f6]v{__version__}[/]", id="cur-version")
                    yield Static("", classes="spacer-xs")
                    yield Button("🔍  Check for Updates", id="btn-check-update", classes="action-btn -primary")
                    yield Button("⬇  Pull Update", id="btn-pull-update", classes="action-btn")
                    yield Button("⚠  Force Update", id="btn-force-update", classes="action-btn -danger")
                    yield Static("", classes="spacer-xs")
                    yield Static("", id="update-log")

            # ── LANGUAGE PANEL ──
            with Center():
                with Container(id="panel-lang", classes="panel"):
                    yield Static("[bold #3b82f6]🌐 Language[/]  [#64748b]Switch interface language[/]", classes="panel-title")
                    yield Rule()
                    yield Static("", id="lang-current")
                    yield Static("", classes="spacer-xs")
                    yield Button("🇺🇸  English", id="btn-lang-en", classes="action-btn")
                    yield Button("🇮🇩  Bahasa Indonesia", id="btn-lang-id", classes="action-btn")

            # Bottom spacer
            yield Static("", classes="spacer-lg")

        # ── Status Bar ──
        yield Static(
            f"  [#64748b]~/.kursorin[/]  "
            f"[#1e3a5f]│[/]  "
            f"[#3b82f6]●[/] [#64748b]Ready[/]  "
            f"[#1e3a5f]│[/]  "
            f"[#64748b]v{__version__}[/]  "
            f"[#1e3a5f]│[/]  "
            f"[#64748b]Ctrl+L lang[/]",
            id="status-bar"
        )

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def on_unmount(self) -> None:
        if self.engine is not None:
            self.engine.stop()

    def action_quit(self) -> None:
        self.exit()

    def on_mount(self) -> None:
        """Hide all panels initially, focus command input."""
        self._collapse_all()
        self.query_one("#cmd-input", Input).focus()
        self._update_lang_display()

    # ── Panel visibility ──────────────────────────────────────────────────────

    def _collapse_all(self) -> None:
        """Hide all panels."""
        for panel_id in ("panel-dashboard", "panel-settings", "panel-doctor", "panel-update", "panel-lang"):
            try:
                self.query_one(f"#{panel_id}").display = False
            except Exception:
                pass

    def _show_panel(self, panel_id: str) -> None:
        """Show a specific panel, collapse others."""
        self._collapse_all()
        try:
            panel = self.query_one(f"#{panel_id}")
            panel.display = True
            panel.scroll_visible(animate=True)
        except Exception:
            pass

    def _toggle_panel(self, panel_id: str) -> None:
        """Toggle a panel — if visible, hide it. If hidden, show it (collapse others)."""
        try:
            panel = self.query_one(f"#{panel_id}")
            if panel.display:
                panel.display = False
            else:
                self._show_panel(panel_id)
        except Exception:
            pass

    # ── Command Handling ──────────────────────────────────────────────────────

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "cmd-input":
            return
        cmd = event.value.strip().lower()
        event.input.value = ""
        if not cmd:
            return
        self._dispatch_command(cmd)

    def _dispatch_command(self, cmd: str) -> None:
        if cmd in ("quit", "q", "exit"):
            self.exit()
        elif cmd in ("dashboard", "dash", "d", "home"):
            self._toggle_panel("panel-dashboard")
        elif cmd in ("settings", "config", "s"):
            self._load_settings_if_needed()
            self._toggle_panel("panel-settings")
        elif cmd in ("doctor", "diag", "x"):
            self._toggle_panel("panel-doctor")
        elif cmd in ("update", "u"):
            self._toggle_panel("panel-update")
        elif cmd in ("lang", "language", "l"):
            self._toggle_panel("panel-lang")
        elif cmd == "start":
            self._start_tracking()
        elif cmd == "calibrate":
            self._start_calibration()
        elif cmd == "gui":
            self._launch_gui()
        elif cmd in ("en", "english"):
            self._set_language("en")
        elif cmd in ("id", "indonesian", "indo"):
            self._set_language("id")
        elif cmd in ("collapse", "close", "hide"):
            self._collapse_all()
        else:
            self.notify(
                f"Unknown: [bold]{cmd}[/]\n"
                "Commands: start, settings, doctor, update, lang, quit",
                title="?",
                severity="warning"
            )

    def action_collapse_all(self) -> None:
        self._collapse_all()

    def action_toggle_lang(self) -> None:
        current = get_lang()
        new = "id" if current == "en" else "en"
        self._set_language(new)

    # ── Language ──────────────────────────────────────────────────────────────

    def _set_language(self, lang: str) -> None:
        set_lang(lang)
        save_lang(lang)
        self._update_lang_display()
        name = "English" if lang == "en" else "Bahasa Indonesia"
        self.notify(f"Language → {name}", title="🌐", severity="information")

    def _update_lang_display(self) -> None:
        try:
            current = get_lang()
            name = "English" if current == "en" else "Bahasa Indonesia"
            flag = "🇺🇸" if current == "en" else "🇮🇩"
            self.query_one("#lang-current", Static).update(
                f"  [#e2e8f0]Current language:[/]  {flag} [bold #3b82f6]{name}[/]"
            )
        except Exception:
            pass

    # ── Settings lazy-load ────────────────────────────────────────────────────

    _settings_loaded = False

    def _load_settings_if_needed(self) -> None:
        if self._settings_loaded:
            return
        self._settings_loaded = True

        try:
            panel = self.query_one("#panel-settings")
            placeholder = self.query_one("#settings-placeholder", Static)

            cfg = load_config()

            # Build settings content
            self.call_after_refresh(lambda: self._mount_settings(panel, cfg))
        except Exception as e:
            self.notify(f"Failed to load settings: {e}", severity="error")

    def _mount_settings(self, panel, cfg) -> None:
        """Mount settings content into the panel."""
        async def do_mount():
            placeholder = None
            try:
                placeholder = panel.query_one("#settings-placeholder")
            except Exception:
                pass

            if placeholder:
                await placeholder.remove()

            sections = Vertical(id="settings-sections")
            await panel.mount(sections)

            # Tracking
            await sections.mount(Static("[bold #60a5fa]━━ Tracking[/]", classes="settings-section-title"))
            await sections.mount(SettingToggle("Head Tracking", cfg.tracking.head_enabled, "head_enabled"))
            await sections.mount(SettingToggle("Eye Tracking", cfg.tracking.eye_enabled, "eye_enabled"))
            await sections.mount(SettingToggle("Hand Tracking", cfg.tracking.hand_enabled, "hand_enabled"))
            await sections.mount(SettingToggle("Invert X (Global)", cfg.tracking.invert_x, "invert_x"))
            await sections.mount(SettingToggle("Invert Y (Global)", cfg.tracking.invert_y, "invert_y"))
            await sections.mount(SettingToggle("Head: Invert X", cfg.tracking.head_invert_x, "head_invert_x"))
            await sections.mount(SettingToggle("Head: Invert Y", cfg.tracking.head_invert_y, "head_invert_y"))
            await sections.mount(SettingToggle("Eye: Invert X", cfg.tracking.eye_invert_x, "eye_invert_x"))
            await sections.mount(SettingToggle("Eye: Invert Y", cfg.tracking.eye_invert_y, "eye_invert_y"))

            # Click
            await sections.mount(Static("[bold #60a5fa]━━ Click Methods[/]", classes="settings-section-title"))
            await sections.mount(SettingToggle("Blink Click", cfg.click.blink_click_enabled, "blink_click"))
            await sections.mount(SettingToggle("Dwell Click", cfg.click.dwell_click_enabled, "dwell_click"))
            await sections.mount(SettingToggle("Pinch Click", cfg.click.pinch_click_enabled, "pinch_click"))
            await sections.mount(SettingToggle("Mouth Click", cfg.click.mouth_click_enabled, "mouth_click"))

            # Camera
            await sections.mount(Static("[bold #60a5fa]━━ Camera[/]", classes="settings-section-title"))
            await sections.mount(SettingToggle("Mirror Mode", cfg.camera.flip_horizontal, "cam_mirror"))
            await sections.mount(SettingToggle("Auto Exposure", cfg.camera.auto_exposure, "cam_ae"))
            await sections.mount(SettingToggle("Auto Focus", cfg.camera.auto_focus, "cam_af"))

            # Performance
            await sections.mount(Static("[bold #60a5fa]━━ Performance[/]", classes="settings-section-title"))
            await sections.mount(SettingToggle("Multi-Threading", cfg.performance.use_threading, "threading"))
            await sections.mount(SettingToggle("GPU Acceleration", cfg.performance.use_gpu, "gpu"))
            await sections.mount(SettingToggle("Power Save", cfg.performance.power_save_mode, "power_save"))

            # UI
            await sections.mount(Static("[bold #60a5fa]━━ Appearance[/]", classes="settings-section-title"))
            await sections.mount(SettingToggle("Show Preview", cfg.ui.show_preview, "show_preview"))
            await sections.mount(SettingToggle("Show Overlay", cfg.ui.show_overlay, "show_overlay"))
            await sections.mount(SettingToggle("Cursor Trail", cfg.ui.cursor_trail, "cursor_trail"))
            await sections.mount(SettingToggle("Audio Feedback", cfg.ui.audio_feedback, "audio_fb"))
            await sections.mount(SettingToggle("Notifications", cfg.ui.show_notifications, "notifs"))

            # Actions
            await sections.mount(Static("", classes="spacer-xs"))
            actions_h = Horizontal(id="settings-actions")
            await sections.mount(actions_h)
            await actions_h.mount(Button("💾  Save", id="btn-save-settings", classes="action-btn -primary"))
            await actions_h.mount(Button("↺  Reset", id="btn-reset-settings", classes="action-btn -danger"))

        self.run_worker(do_mount())

    # ── Button handling ───────────────────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""

        if btn_id == "btn-start":
            self._start_tracking()
        elif btn_id == "btn-calibrate":
            self._start_calibration()
        elif btn_id == "btn-gui":
            self._launch_gui()
        elif btn_id == "btn-run-doctor":
            self.run_worker(self._run_doctor())
        elif btn_id == "btn-check-update":
            self.run_worker(self._check_updates())
        elif btn_id == "btn-pull-update":
            self.run_worker(self._pull_update(force=False))
        elif btn_id == "btn-force-update":
            self.run_worker(self._pull_update(force=True))
        elif btn_id == "btn-save-settings":
            self._save_settings()
        elif btn_id == "btn-reset-settings":
            self._reset_settings()
        elif btn_id == "btn-lang-en":
            self._set_language("en")
        elif btn_id == "btn-lang-id":
            self._set_language("id")

    # ── Core actions ──────────────────────────────────────────────────────────

    def _start_tracking(self) -> None:
        if self.engine and self.engine.is_running:
            self.engine.stop()
            self.query_one("#btn-start", Button).label = "▶  Start Tracking"
            self.query_one("#btn-start", Button).remove_class("-danger")
            self.query_one("#btn-start", Button).add_class("-primary")
            self.notify("Engine stopped.", title="⏹ Tracking", severity="warning")
            return

        try:
            cfg = load_config()
            self.engine = KursorinEngine(cfg)
            self.engine.start()
            self.query_one("#btn-start", Button).label = "⏹  Stop Tracking"
            self.query_one("#btn-start", Button).remove_class("-primary")
            self.query_one("#btn-start", Button).add_class("-danger")
            self.notify("Engine started!", title="▶ Tracking", severity="information")
            
            # Start dashboard update loop
            self.run_worker(self._update_dashboard_loop())
        except Exception as e:
            self.notify(f"Start failed: {e}", title="Error", severity="error")

    async def _update_dashboard_loop(self) -> None:
        while self.engine is not None and self.engine.is_running:
            try:
                # Update status dots
                state_colors = {"IDLE": "idle", "INITIALIZING": "warning", "TRACKING": "online", "CALIBRATING": "warning", "ERROR": "offline"}
                state = self.engine.state.name
                
                # Update Metrics
                self.query_one("#stat-fps", StatCard).update_value(f"{self.engine.fps:.1f}")
                self.query_one("#stat-latency", StatCard).update_value(f"{self.engine.latency_ms:.0f}ms")
                uptime = time.time() - self.engine._start_time if self.engine._start_time else 0
                self.query_one("#stat-uptime", StatCard).update_value(f"{uptime:.1f}s")
                
            except Exception:
                pass
            await asyncio.sleep(0.5)

    def _start_calibration(self) -> None:
        self.notify("Use 'kursorin calibrate' from terminal.", title="🎯 Calibration", severity="information")

    def _launch_gui(self) -> None:
        self.notify("Use 'kursorin gui' from terminal.", title="🖥 GUI", severity="information")

    # ── Doctor ────────────────────────────────────────────────────────────────

    async def _run_doctor(self) -> None:
        import importlib.util
        import platform
        import sys as _sys

        log = self.query_one("#doctor-log", Static)
        summary = self.query_one("#doctor-summary", Static)
        progress = self.query_one("#doctor-progress", ProgressBar)

        log.update("")
        summary.update("")
        progress.update(progress=0)

        class DiagResults:
            total = 0
            passed = 0
            fixes = []
            text = ""

        results = DiagResults()

        def add(msg, ok=True):
            results.total += 1
            if ok:
                results.passed += 1
            icon = "[#22c55e]✓[/]" if ok else "[#ef4444]✗[/]"
            results.text += f"  {icon} {msg}\n"
            log.update(results.text)

        # Checks
        add("OS Compatibility", platform.system() in ("Windows", "Darwin", "Linux"))
        progress.update(progress=10)

        add(f"Python {_sys.version_info.major}.{_sys.version_info.minor}", _sys.version_info >= (3, 8))
        progress.update(progress=20)

        deps = ["cv2", "mediapipe", "numpy", "pyautogui", "scipy", "PIL",
                "pynput", "screeninfo", "pydantic", "rich", "textual"]
        step = 20
        for mod in deps:
            ok = importlib.util.find_spec(mod) is not None
            add(f"Module: {mod}", ok)
            if not ok:
                results.fixes.append(f"pip install {mod}")
            step += 60 / len(deps)
            progress.update(progress=int(step))

        # Camera
        try:
            import cv2
            c = cv2.VideoCapture(0)
            cam_ok = c.isOpened()
            c.release()
        except Exception:
            cam_ok = False
        add("Camera accessible", cam_ok)
        progress.update(progress=90)

        add("Data directory (~/.kursorin)", (Path.home() / ".kursorin").exists())
        progress.update(progress=100)

        if results.passed == results.total:
            summary.update(f"\n[bold #22c55e]✓ All {results.total} checks passed — system healthy.[/]")
        else:
            fix_text = "\n".join(f"  • {f}" for f in results.fixes)
            summary.update(
                f"\n[bold #ef4444]⚠ {results.passed}/{results.total} passed[/]\n"
                f"[#94a3b8]Fixes:[/]\n{fix_text}"
            )

    # ── Update ────────────────────────────────────────────────────────────────

    async def _check_updates(self) -> None:
        log = self.query_one("#update-log", Static)
        log.update("[#64748b]Checking for updates...[/]")
        try:
            from kursorin.utils.updater import GitUpdater
            updater = GitUpdater()
            if not updater.check_git_installed():
                log.update("[#ef4444]✗ Git not found.[/]")
                return
            if not updater.is_git_repo():
                log.update("[#f59e0b]⚠ Not a Git repo. Converting...[/]")
                ok, msg = updater.auto_convert_to_git()
                if not ok:
                    log.update(f"[#ef4444]✗ {msg}[/]")
                    return
                log.update("[#22c55e]✓ Converted to Git repo.[/]\n")
            available, msg = updater.check_for_updates()
            if available:
                log.update("[#22c55e]✓ Update available![/]")
            else:
                log.update(f"[#22c55e]✓ {msg}[/]")
        except Exception as e:
            log.update(f"[#ef4444]✗ {e}[/]")

    async def _pull_update(self, force: bool = False) -> None:
        log = self.query_one("#update-log", Static)
        mode = "force" if force else "normal"
        log.update(f"[#64748b]Pulling ({mode})...[/]")
        try:
            from kursorin.utils.updater import GitUpdater
            updater = GitUpdater()
            ok, msg = updater.pull_update(force=force)
            if ok:
                log.update(f"[#22c55e]✓ {msg}\nRestart KURSORIN to apply.[/]")
            else:
                log.update(f"[#ef4444]✗ {msg}[/]")
        except Exception as e:
            log.update(f"[#ef4444]✗ {e}[/]")

    # ── Settings Persistence ──────────────────────────────────────────────────

    def _save_settings(self) -> None:
        try:
            cfg = load_config()
            
            # Map widget IDs to config values
            # (In a real app, this would be more dynamic)
            map_keys = {
                "sw-head_enabled": ("tracking", "head_enabled"),
                "sw-eye_enabled": ("tracking", "eye_enabled"),
                "sw-hand_enabled": ("tracking", "hand_enabled"),
                "sw-invert_x": ("tracking", "invert_x"),
                "sw-invert_y": ("tracking", "invert_y"),
                "sw-head_invert_x": ("tracking", "head_invert_x"),
                "sw-head_invert_y": ("tracking", "head_invert_y"),
                "sw-eye_invert_x": ("tracking", "eye_invert_x"),
                "sw-eye_invert_y": ("tracking", "eye_invert_y"),
                "sw-blink_click": ("click", "blink_click_enabled"),
                "sw-dwell_click": ("click", "dwell_click_enabled"),
                "sw-pinch_click": ("click", "pinch_click_enabled"),
                "sw-mouth_click": ("click", "mouth_click_enabled"),
                "sw-cam_mirror": ("camera", "flip_horizontal"),
                "sw-cam_ae": ("camera", "auto_exposure"),
                "sw-cam_af": ("camera", "auto_focus"),
                "sw-threading": ("performance", "use_threading"),
                "sw-gpu": ("performance", "use_gpu"),
                "sw-power_save": ("performance", "power_save_mode"),
                "sw-show_preview": ("ui", "show_preview"),
                "sw-show_overlay": ("ui", "show_overlay"),
                "sw-cursor_trail": ("ui", "cursor_trail"),
                "sw-audio_fb": ("ui", "audio_feedback"),
                "sw-notifs": ("ui", "show_notifications"),
            }

            for wid, (section_name, attr_name) in map_keys.items():
                try:
                    sw = self.query_one(f"#{wid}", Switch)
                    section = getattr(cfg, section_name)
                    setattr(section, attr_name, sw.value)
                except Exception:
                    continue

            # Save to file
            config_dir = Path.home() / ".kursorin"
            config_dir.mkdir(parents=True, exist_ok=True)
            cfg.to_file(config_dir / "config.yaml")

            self.notify("Settings saved successfully.", title="💾", severity="information")
            
            # If engine is running, update it
            if self.engine and self.engine.is_running:
                self.engine.config = cfg
                
        except Exception as e:
            self.notify(f"Save failed: {e}", severity="error")

    def _reset_settings(self) -> None:
        self.notify("Settings reset to defaults (stub).", title="↺", severity="warning")
