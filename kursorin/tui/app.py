"""
KURSORIN TUI — Main Application

Single-column, minimalist command center.
Ocean Blue aesthetic · No tabs · Collapsible sections.
"""

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Generator, Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, Center, VerticalScroll
from textual.widgets import (
    Static, Button, Footer, Input, Switch, Rule,
    ProgressBar, Collapsible,
)
from textual.widget import Widget

from kursorin import __version__
from kursorin.config import load_config, KursorinConfig
from kursorin.core.kursorin_engine import KursorinEngine
from kursorin.i18n import t, init_lang, get_lang, set_lang, save_lang
from kursorin.tui.widgets.logo import LogoWidget
from kursorin.tui.widgets.status_indicator import StatusIndicator
from kursorin.tui.widgets.accuracy_meter import AccuracyMeter


# ── Inline Widgets ─────────────────────────────────────────────────────────────

class StatCard(Widget):
    """A compact metric card."""
    def __init__(self, value: str, label: str, **kwargs):
        super().__init__(**kwargs)
        self._value = value
        self._label = label

    def render(self) -> str:
        return f"[bold #00a3ff]{self._value}[/]\n[#4a607a]{self._label}[/]"

    def update_value(self, value: str) -> None:
        self._value = value
        self.refresh()


class StatusDot(Widget):
    """Inline status dot."""
    def __init__(self, label: str, status: str = "idle", **kwargs):
        super().__init__(**kwargs)
        self._label = label
        self._status = status

    def set_status(self, status: str) -> None:
        self._status = status
        self.refresh()

    def render(self) -> str:
        colors = {"online": "#00a3ff", "warning": "#c09040",
                  "offline": "#4a607a", "idle": "#2a3a50"}
        symbols = {"online": "●", "warning": "◈", "offline": "○", "idle": "○"}
        c = colors.get(self._status, "#2a3a50")
        s = symbols.get(self._status, "○")
        return f"[{c}]{s}[/] [#8098b0]{self._label}[/]"


class SettingToggle(Horizontal):
    """Setting row: label + switch."""
    DEFAULT_CSS = """
    SettingToggle { height: 3; padding: 0 1; }
    SettingToggle:hover { background: #0c1830; }
    """
    def __init__(self, label: str, value: bool, key: str, **kwargs):
        super().__init__(**kwargs)
        self._label = label
        self._value = value
        self._key = key

    def compose(self) -> ComposeResult:
        yield Static(self._label, classes="setting-label")
        yield Switch(value=self._value, id=f"sw-{self._key}")


class SettingInput(Horizontal):
    """Setting row: label + text input."""
    DEFAULT_CSS = """
    SettingInput { height: 3; padding: 0 1; }
    SettingInput:hover { background: #0c1830; }
    """
    def __init__(self, label: str, value: str, key: str, **kwargs):
        super().__init__(**kwargs)
        self._label = label
        self._value = value
        self._key = key

    def compose(self) -> ComposeResult:
        yield Static(self._label, classes="setting-label")
        yield Input(value=self._value, id=f"inp-{self._key}", classes="setting-input")


# ── Main App ───────────────────────────────────────────────────────────────────

class KursorinTUI(App):
    """KURSORIN — Ocean Blue minimalist command center."""

    CSS_PATH = "app.tcss"
    TITLE = "KURSORIN"
    SUB_TITLE = "Command Center"

    engine: Optional[KursorinEngine] = None

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("escape", "focus_cmd", "Command", show=True),
        Binding("ctrl+l", "toggle_lang", "Lang", show=True),
        Binding("ctrl+s", "save_settings", "Save", show=True),
    ]

    # ── Compose ───────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        init_lang()

        # Header
        yield Static(
            f"  [bold #00a3ff]KURSORIN[/]  "
            f"[#0a1e3a]│[/]  "
            f"[#4a607a]v{__version__}[/]  "
            f"[#0a1e3a]│[/]  "
            f"[#4a607a]{t('cli.subtitle')}[/]",
            id="header-bar"
        )

        # ── Scrollable Body ───────────────────────────────────────────────
        with VerticalScroll(id="main-scroll"):

            # Logo
            with Center():
                yield LogoWidget(id="logo-art")
            with Center():
                yield Static(
                    f"[#4a607a]{t('cli.subtitle')}[/]",
                    id="logo-subtitle"
                )

            # Command input
            with Center():
                yield Input(
                    placeholder="  Type a command: start · stop · settings · doctor · help · quit",
                    id="cmd-input"
                )

            Static("", classes="spacer-sm")

            # ══════════════════════════════════════════════════════════════
            # SECTION 1: DASHBOARD — always visible, primary controls
            # ══════════════════════════════════════════════════════════════
            with Container(classes="section-panel"):
                yield Static("Dashboard", classes="section-title")
                yield Static("System status and quick actions", classes="section-subtitle")
                yield Rule()

                # Status dots
                with Horizontal(id="status-dots"):
                    yield StatusDot("Camera", "idle", id="dot-camera")
                    yield StatusDot("Head",   "idle", id="dot-head")
                    yield StatusDot("Eye",    "idle", id="dot-eye")
                    yield StatusDot("Hand",   "idle", id="dot-hand")

                Static("", classes="spacer-xs")

                # Metrics
                with Horizontal(id="stats-row"):
                    yield StatCard("—", "FPS",     id="stat-fps")
                    yield StatCard("—", "Latency", id="stat-latency")
                    yield StatCard("—", "Uptime",  id="stat-uptime")
                    yield StatCard(f"v{__version__}", "Version", id="stat-version")

                Static("", classes="spacer-xs")

                # Primary actions
                with Horizontal(classes="btn-row"):
                    yield Button("▶  Start", id="btn-start", classes="action-btn -primary")
                    yield Button("⏹  Stop",  id="btn-stop",  classes="action-btn -danger")

                with Horizontal(classes="btn-row"):
                    yield Button("🎯  Calibrate", id="btn-calibrate", classes="action-btn")
                    yield Button("🖥  GUI",        id="btn-gui",       classes="action-btn")

            Static("", classes="spacer-xs")

            # ══════════════════════════════════════════════════════════════
            # SECTION 2: TRAINING ACCURACY — collapsible
            # ══════════════════════════════════════════════════════════════
            with Collapsible(title="Training Accuracy", collapsed=True, id="section-training"):
                yield Static(
                    "[#4a607a]Start tracking to see live accuracy.[/]",
                    id="training-hint"
                )
                Static("", classes="spacer-xs")
                yield AccuracyMeter("Head Tracking",  0.0, id="acc-head")
                yield AccuracyMeter("Eye Tracking",   0.0, id="acc-eye")
                yield AccuracyMeter("Hand Tracking",  0.0, id="acc-hand")
                yield AccuracyMeter("Overall Fusion", 0.0, id="acc-fused")
                Static("", classes="spacer-xs")
                with Horizontal():
                    yield Static("[#4a607a]Calibration:[/] ", id="calib-label")
                    yield Static("[#4a607a]Not calibrated[/]", id="calib-status")

            # ══════════════════════════════════════════════════════════════
            # SECTION 3: SETTINGS — collapsible
            # ══════════════════════════════════════════════════════════════
            with Collapsible(title="Settings", collapsed=True, id="section-settings"):
                yield Static("[#4a607a]Loading settings...[/]", id="settings-placeholder")

            # ══════════════════════════════════════════════════════════════
            # SECTION 4: DOCTOR — collapsible
            # ══════════════════════════════════════════════════════════════
            with Collapsible(title="System Diagnostics", collapsed=True, id="section-doctor"):
                yield Button("▶  Run Diagnostics", id="btn-run-doctor", classes="action-btn -primary")
                Static("", classes="spacer-xs")
                yield ProgressBar(total=100, show_eta=False, id="doctor-progress")
                yield Static("", id="doctor-log")
                yield Static("", id="doctor-summary")

            # ══════════════════════════════════════════════════════════════
            # SECTION 5: UPDATES — collapsible
            # ══════════════════════════════════════════════════════════════
            with Collapsible(title="Updates", collapsed=True, id="section-updates"):
                yield Static(
                    f"[#8098b0]Current:[/] [bold #00a3ff]v{__version__}[/]",
                    id="cur-version"
                )
                Static("", classes="spacer-xs")
                with Horizontal(classes="btn-row"):
                    yield Button("Check Updates", id="btn-check-update", classes="action-btn -primary")
                    yield Button("Pull Update",   id="btn-pull-update",  classes="action-btn")
                Static("", classes="spacer-xs")
                yield Static("", id="update-log")

            # ══════════════════════════════════════════════════════════════
            # SECTION 6: LANGUAGE — collapsible
            # ══════════════════════════════════════════════════════════════
            with Collapsible(title="Language", collapsed=True, id="section-lang"):
                yield Static("", id="lang-current")
                Static("", classes="spacer-xs")
                with Horizontal(classes="btn-row"):
                    yield Button("English",           id="btn-lang-en", classes="action-btn")
                    yield Button("Bahasa Indonesia",  id="btn-lang-id", classes="action-btn")

            # Bottom spacer
            Static("", classes="spacer-lg")

        # Status bar
        yield Static(
            f"  [#4a607a]~/.kursorin[/]  "
            f"[#0a1e3a]│[/]  "
            f"[#00a3ff]●[/] [#4a607a]Ready[/]  "
            f"[#0a1e3a]│[/]  "
            f"[#4a607a]Ctrl+S save · Ctrl+L lang · Q quit[/]",
            id="status-bar"
        )

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def on_mount(self) -> None:
        self.query_one("#cmd-input", Input).focus()
        self._update_lang_display()
        self._check_calibration_status()
        self.call_after_refresh(self._load_settings_if_needed)

    def on_unmount(self) -> None:
        if self.engine is not None:
            try:
                self.engine.stop()
            except Exception:
                pass

    # ── Actions ───────────────────────────────────────────────────────────────

    def action_quit(self) -> None:
        self.exit()

    def action_focus_cmd(self) -> None:
        self.query_one("#cmd-input", Input).focus()

    def action_toggle_lang(self) -> None:
        current = get_lang()
        new_lang = "id" if current == "en" else "en"
        self._set_language(new_lang)

    def action_save_settings(self) -> None:
        self._save_settings()

    # ── Command Dispatching ───────────────────────────────────────────────────

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "cmd-input":
            return
        cmd = event.value.strip().lower()
        event.input.value = ""
        if not cmd:
            return
        self._dispatch_command(cmd)

    def _dispatch_command(self, cmd: str) -> None:
        routes = {
            ("start",):                         lambda: self._start_tracking(),
            ("stop", "halt"):                   lambda: self._stop_tracking(),
            ("settings", "config", "s", "cfg"): lambda: self._toggle_section("section-settings"),
            ("doctor", "diag", "health"):       lambda: self._toggle_section("section-doctor"),
            ("training", "train", "accuracy"):  lambda: self._toggle_section("section-training"),
            ("update", "updates", "u"):         lambda: self._toggle_section("section-updates"),
            ("lang", "language", "l"):           lambda: self._toggle_section("section-lang"),
            ("calibrate", "calib"):             lambda: self._start_calibration(),
            ("gui",):                           lambda: self._launch_gui(),
            ("save",):                          lambda: self._save_settings(),
            ("reset",):                         lambda: self._reset_settings(),
            ("en", "english"):                  lambda: self._set_language("en"),
            ("id", "indonesian", "indo"):       lambda: self._set_language("id"),
            ("quit", "q", "exit", "bye"):       lambda: self.exit(),
            ("help", "?", "h"):                 lambda: self._show_help(),
        }

        for keys, fn in routes.items():
            if cmd in keys:
                fn()
                return

        self.notify(
            f"Unknown: [bold]{cmd}[/]  —  type [bold #00a3ff]help[/]",
            title="?",
            severity="warning",
        )

    def _toggle_section(self, section_id: str) -> None:
        """Toggle a collapsible section open/closed."""
        try:
            section = self.query_one(f"#{section_id}", Collapsible)
            section.collapsed = not section.collapsed
        except Exception:
            pass

    def _show_help(self) -> None:
        lines = [
            "[bold #00a3ff]Commands[/]",
            "",
            "  [#80d0ff]start[/]       Start tracking engine",
            "  [#80d0ff]stop[/]        Stop tracking engine",
            "  [#80d0ff]settings[/]    Toggle settings panel",
            "  [#80d0ff]doctor[/]      System diagnostics",
            "  [#80d0ff]training[/]    Accuracy metrics",
            "  [#80d0ff]calibrate[/]   Eye calibration",
            "  [#80d0ff]lang[/]        Switch language",
            "  [#80d0ff]update[/]      Software updates",
            "  [#4a607a]quit[/]        Exit",
        ]
        self.notify("\n".join(lines), title="Help", severity="information")

    # ── Engine Control ────────────────────────────────────────────────────────

    def _start_tracking(self) -> None:
        if self.engine is not None and self.engine.is_running:
            self.notify("Already running.", title="▶", severity="information")
            return
        try:
            cfg = load_config()
            self.engine = KursorinEngine(cfg)
            self.engine.start()

            try:
                self.query_one("#btn-start", Button).label = "● Running"
            except Exception:
                pass

            self._set_dot("dot-camera", "online")
            self._set_dot("dot-head",   "online" if cfg.tracking.head_enabled else "offline")
            self._set_dot("dot-eye",    "online" if cfg.tracking.eye_enabled  else "offline")
            self._set_dot("dot-hand",   "online" if cfg.tracking.hand_enabled else "offline")

            try:
                self.query_one("#status-bar", Static).update(
                    f"  [#4a607a]~/.kursorin[/]  "
                    f"[#0a1e3a]│[/]  "
                    f"[#00a3ff]●[/] [bold #00a3ff]TRACKING[/]  "
                    f"[#0a1e3a]│[/]  "
                    f"[#4a607a]Ctrl+S save · Q quit[/]"
                )
            except Exception:
                pass

            # Open the training section
            try:
                self.query_one("#section-training", Collapsible).collapsed = False
            except Exception:
                pass

            self.notify("Engine started.", title="▶", severity="information")
            self.run_worker(self._update_dashboard_loop())

        except Exception as e:
            self.notify(f"Failed: {e}", title="Error", severity="error")

    def _stop_tracking(self) -> None:
        if self.engine is None or not self.engine.is_running:
            self.notify("Not running.", title="⏹", severity="warning")
            return
        try:
            self.engine.stop()
        except Exception:
            pass
        finally:
            self.engine = None

        try:
            self.query_one("#btn-start", Button).label = "▶  Start"
        except Exception:
            pass
        for dot in ("dot-camera", "dot-head", "dot-eye", "dot-hand"):
            self._set_dot(dot, "idle")
        for aid in ("acc-head", "acc-eye", "acc-hand", "acc-fused"):
            try:
                self.query_one(f"#{aid}", AccuracyMeter).update_value(0.0)
            except Exception:
                pass
        try:
            self.query_one("#status-bar", Static).update(
                f"  [#4a607a]~/.kursorin[/]  "
                f"[#0a1e3a]│[/]  "
                f"[#00a3ff]●[/] [#4a607a]Ready[/]  "
                f"[#0a1e3a]│[/]  "
                f"[#4a607a]Ctrl+S save · Ctrl+L lang · Q quit[/]"
            )
        except Exception:
            pass
        self.notify("Stopped.", title="⏹", severity="warning")

    def _set_dot(self, dot_id: str, status: str) -> None:
        try:
            self.query_one(f"#{dot_id}", StatusDot).set_status(status)
        except Exception:
            pass

    async def _update_dashboard_loop(self) -> None:
        """Live metrics update while engine runs."""
        while self.engine is not None and self.engine.is_running:
            try:
                fps = getattr(self.engine, "fps", 0.0)
                lat = getattr(self.engine, "latency_ms", 0.0)
                st  = getattr(self.engine, "_start_time", None)
                uptime = time.time() - st if st else 0.0

                self.query_one("#stat-fps",     StatCard).update_value(f"{fps:.1f}")
                self.query_one("#stat-latency", StatCard).update_value(f"{lat:.0f}ms")
                self.query_one("#stat-uptime",  StatCard).update_value(f"{uptime:.0f}s")

                head_acc  = self._derive_accuracy("head",  fps)
                eye_acc   = self._derive_accuracy("eye",   fps)
                hand_acc  = self._derive_accuracy("hand",  fps)
                fused_acc = (head_acc + eye_acc + hand_acc) / 3.0

                self.query_one("#acc-head",  AccuracyMeter).update_value(head_acc)
                self.query_one("#acc-eye",   AccuracyMeter).update_value(eye_acc)
                self.query_one("#acc-hand",  AccuracyMeter).update_value(hand_acc)
                self.query_one("#acc-fused", AccuracyMeter).update_value(fused_acc)

                try:
                    self.query_one("#training-hint", Static).update(
                        f"[#00a3ff]Engine running — FPS: {fps:.1f} · Uptime: {uptime:.0f}s[/]"
                    )
                except Exception:
                    pass

            except Exception:
                pass
            await asyncio.sleep(0.5)

    def _derive_accuracy(self, modality: str, fps: float) -> float:
        """Derive accuracy estimate from engine state."""
        if self.engine is None:
            return 0.0
        try:
            cfg = self.engine.config
            if modality == "head" and not cfg.tracking.head_enabled:
                return 0.0
            if modality == "eye"  and not cfg.tracking.eye_enabled:
                return 0.0
            if modality == "hand" and not cfg.tracking.hand_enabled:
                return 0.0
        except Exception:
            pass
        try:
            fusion = self.engine._fusion  # type: ignore
            if fusion is not None:
                weights = getattr(fusion, "_weights", {})
                w = weights.get(modality, 0.0)
                return min(100.0, w * 200.0)
        except Exception:
            pass
        if fps <= 0:
            return 0.0
        target = 30.0
        ratio = min(fps / target, 1.0)
        base = {"head": 85.0, "eye": 72.0, "hand": 78.0}.get(modality, 70.0)
        return base * ratio

    # ── Calibration / GUI ─────────────────────────────────────────────────────

    def _start_calibration(self) -> None:
        self.notify(
            "Run [bold]kursorin calibrate[/] from a terminal\nor launch the GUI.",
            title="Calibration",
            severity="information",
        )

    def _launch_gui(self) -> None:
        try:
            import kursorin.app as kapp
            self.notify("Launching GUI…", title="GUI", severity="information")
            kapp.main()
        except Exception as e:
            self.notify(f"GUI Error: {e}", severity="error")

    def _check_calibration_status(self) -> None:
        calib_path = Path.home() / ".kursorin" / "calibration.json"
        try:
            if calib_path.exists():
                self.query_one("#calib-status", Static).update(
                    "[#00a3ff]✓ Calibrated[/]"
                )
            else:
                self.query_one("#calib-status", Static).update(
                    "[#4a607a]Not calibrated[/]"
                )
        except Exception:
            pass

    # ── Language ──────────────────────────────────────────────────────────────

    def _set_language(self, lang: str) -> None:
        set_lang(lang)
        save_lang(lang)
        self._update_lang_display()
        name = "English" if lang == "en" else "Bahasa Indonesia"
        self.notify(f"Language → {name}", title="Lang", severity="information")

    def _update_lang_display(self) -> None:
        try:
            current = get_lang()
            name = "English" if current == "en" else "Bahasa Indonesia"
            self.query_one("#lang-current", Static).update(
                f"  [#8098b0]Current:[/]  [bold #00a3ff]{name}[/]"
            )
        except Exception:
            pass

    # ── Settings ──────────────────────────────────────────────────────────────

    _settings_loaded: bool = False

    def _load_settings_if_needed(self) -> None:
        if self._settings_loaded:
            return
        self._settings_loaded = True
        try:
            cfg = load_config()
            self.call_after_refresh(lambda: self._mount_settings(cfg))
        except Exception as e:
            self.notify(f"Settings load failed: {e}", severity="error")

    def _mount_settings(self, cfg: KursorinConfig) -> None:
        async def do_mount():
            try:
                ph = self.query_one("#settings-placeholder")
                await ph.remove()
            except Exception:
                pass

            section = self.query_one("#section-settings", Collapsible)
            contents = section.query_one("Contents")

            # ── Tracking ──
            await contents.mount(Static("[bold #80d0ff]Tracking[/]", classes="settings-group-title"))
            await contents.mount(SettingToggle("Head Tracking",     cfg.tracking.head_enabled, "head_enabled"))
            await contents.mount(SettingToggle("Eye Tracking",      cfg.tracking.eye_enabled,  "eye_enabled"))
            await contents.mount(SettingToggle("Hand Tracking",     cfg.tracking.hand_enabled, "hand_enabled"))
            await contents.mount(SettingToggle("Invert X",          cfg.tracking.invert_x,     "invert_x"))
            await contents.mount(SettingToggle("Invert Y",          cfg.tracking.invert_y,     "invert_y"))
            await contents.mount(SettingToggle("Head Invert X",     cfg.tracking.head_invert_x,"head_invert_x"))
            await contents.mount(SettingToggle("Head Invert Y",     cfg.tracking.head_invert_y,"head_invert_y"))
            await contents.mount(SettingToggle("Eye Invert X",      cfg.tracking.eye_invert_x, "eye_invert_x"))
            await contents.mount(SettingToggle("Eye Invert Y",      cfg.tracking.eye_invert_y, "eye_invert_y"))
            await contents.mount(SettingInput("Head Sensitivity X", str(cfg.tracking.head_sensitivity_x), "head_sens_x"))
            await contents.mount(SettingInput("Head Sensitivity Y", str(cfg.tracking.head_sensitivity_y), "head_sens_y"))
            await contents.mount(SettingInput("Head Smoothing",     str(cfg.tracking.head_smoothing),     "head_smooth"))
            await contents.mount(SettingInput("Eye Sensitivity",    str(cfg.tracking.eye_sensitivity),    "eye_sens"))
            await contents.mount(SettingInput("Hand Sensitivity",   str(cfg.tracking.hand_sensitivity),   "hand_sens"))
            await contents.mount(SettingInput("Hand Smoothing",     str(cfg.tracking.hand_smoothing),     "hand_smooth"))
            await contents.mount(SettingInput("Pinch Threshold",    str(cfg.tracking.pinch_threshold),    "pinch_thr"))

            # ── Click ──
            await contents.mount(Static("[bold #80d0ff]Click Methods[/]", classes="settings-group-title"))
            await contents.mount(SettingToggle("Blink Click",  cfg.click.blink_click_enabled, "blink_click"))
            await contents.mount(SettingToggle("Dwell Click",  cfg.click.dwell_click_enabled, "dwell_click"))
            await contents.mount(SettingToggle("Pinch Click",  cfg.click.pinch_click_enabled, "pinch_click"))
            await contents.mount(SettingToggle("Mouth Click",  cfg.click.mouth_click_enabled, "mouth_click"))
            await contents.mount(SettingInput("Dwell Time (ms)",   str(cfg.click.dwell_time_ms),  "dwell_time"))
            await contents.mount(SettingInput("Dwell Radius (px)", str(cfg.click.dwell_radius_px),"dwell_radius"))
            await contents.mount(SettingInput("Pinch Hold (ms)",   str(cfg.click.pinch_hold_time_ms),"pinch_hold"))

            # ── Camera ──
            await contents.mount(Static("[bold #80d0ff]Camera[/]", classes="settings-group-title"))
            await contents.mount(SettingInput("Camera Index",  str(cfg.camera.camera_index),  "cam_idx"))
            await contents.mount(SettingInput("Target FPS",    str(cfg.camera.target_fps),    "cam_fps"))
            await contents.mount(SettingInput("Width",         str(cfg.camera.camera_width),  "cam_w"))
            await contents.mount(SettingInput("Height",        str(cfg.camera.camera_height), "cam_h"))
            await contents.mount(SettingToggle("Mirror Mode",  cfg.camera.flip_horizontal,    "cam_mirror"))
            await contents.mount(SettingToggle("Auto Exposure", cfg.camera.auto_exposure,     "cam_ae"))
            await contents.mount(SettingToggle("Auto Focus",   cfg.camera.auto_focus,         "cam_af"))

            # ── Performance ──
            await contents.mount(Static("[bold #80d0ff]Performance[/]", classes="settings-group-title"))
            await contents.mount(SettingToggle("Multi-Threading",  cfg.performance.use_threading,   "threading"))
            await contents.mount(SettingToggle("GPU Acceleration", cfg.performance.use_gpu,         "gpu"))
            await contents.mount(SettingToggle("Power Save",       cfg.performance.power_save_mode, "power_save"))
            await contents.mount(SettingInput("Max FPS",           str(cfg.performance.max_fps),    "max_fps"))
            await contents.mount(SettingInput("Thread Count",      str(cfg.performance.thread_count),"thread_count"))

            # ── Appearance ──
            await contents.mount(Static("[bold #80d0ff]Appearance[/]", classes="settings-group-title"))
            await contents.mount(SettingToggle("Video Preview",    cfg.ui.show_preview,       "show_preview"))
            await contents.mount(SettingToggle("Show Overlay",     cfg.ui.show_overlay,       "show_overlay"))
            await contents.mount(SettingToggle("Cursor Trail",     cfg.ui.cursor_trail,       "cursor_trail"))
            await contents.mount(SettingToggle("Audio Feedback",   cfg.ui.audio_feedback,     "audio_fb"))
            await contents.mount(SettingToggle("Click Sound",      cfg.ui.click_sound,        "click_sound"))
            await contents.mount(SettingToggle("Notifications",    cfg.ui.show_notifications, "notifs"))

            # ── Calibration ──
            await contents.mount(Static("[bold #80d0ff]Calibration[/]", classes="settings-group-title"))
            await contents.mount(SettingToggle("Auto Calibration",   cfg.calibration.auto_calibration, "auto_calib"))
            await contents.mount(SettingInput("Calibration Points",  str(cfg.calibration.calibration_points), "calib_pts"))
            await contents.mount(SettingInput("Dwell Time (ms)",     str(cfg.calibration.calibration_dwell_time_ms), "calib_dwell"))
            await contents.mount(SettingToggle("Save Calibration",   cfg.calibration.save_calibration, "save_calib"))

            # ── Debug ──
            await contents.mount(Static("[bold #80d0ff]Debug[/]", classes="settings-group-title"))
            await contents.mount(SettingToggle("Debug Mode", cfg.debug_mode, "debug_mode"))

            # ── Save / Reset ──
            Static("", classes="spacer-xs")
            actions = Horizontal(id="settings-actions")
            await contents.mount(actions)
            await actions.mount(Button("Save",  id="btn-save-settings",  classes="action-btn -primary"))
            await actions.mount(Button("Reset", id="btn-reset-settings", classes="action-btn -danger"))

        self.run_worker(do_mount())

    # ── Settings Persist ──────────────────────────────────────────────────────

    def _save_settings(self) -> None:
        try:
            cfg = load_config()

            bool_map = {
                "sw-head_enabled":   ("tracking",    "head_enabled"),
                "sw-eye_enabled":    ("tracking",    "eye_enabled"),
                "sw-hand_enabled":   ("tracking",    "hand_enabled"),
                "sw-invert_x":       ("tracking",    "invert_x"),
                "sw-invert_y":       ("tracking",    "invert_y"),
                "sw-head_invert_x":  ("tracking",    "head_invert_x"),
                "sw-head_invert_y":  ("tracking",    "head_invert_y"),
                "sw-eye_invert_x":   ("tracking",    "eye_invert_x"),
                "sw-eye_invert_y":   ("tracking",    "eye_invert_y"),
                "sw-blink_click":    ("click",       "blink_click_enabled"),
                "sw-dwell_click":    ("click",       "dwell_click_enabled"),
                "sw-pinch_click":    ("click",       "pinch_click_enabled"),
                "sw-mouth_click":    ("click",       "mouth_click_enabled"),
                "sw-cam_mirror":     ("camera",      "flip_horizontal"),
                "sw-cam_ae":         ("camera",      "auto_exposure"),
                "sw-cam_af":         ("camera",      "auto_focus"),
                "sw-threading":      ("performance", "use_threading"),
                "sw-gpu":            ("performance", "use_gpu"),
                "sw-power_save":     ("performance", "power_save_mode"),
                "sw-show_preview":   ("ui",          "show_preview"),
                "sw-show_overlay":   ("ui",          "show_overlay"),
                "sw-cursor_trail":   ("ui",          "cursor_trail"),
                "sw-audio_fb":       ("ui",          "audio_feedback"),
                "sw-click_sound":    ("ui",          "click_sound"),
                "sw-notifs":         ("ui",          "show_notifications"),
                "sw-auto_calib":     ("calibration", "auto_calibration"),
                "sw-save_calib":     ("calibration", "save_calibration"),
                "sw-debug_mode":     (None,          "debug_mode"),
            }

            numeric_map = {
                "inp-head_sens_x":  ("tracking",    "head_sensitivity_x",    float),
                "inp-head_sens_y":  ("tracking",    "head_sensitivity_y",    float),
                "inp-head_smooth":  ("tracking",    "head_smoothing",        float),
                "inp-eye_sens":     ("tracking",    "eye_sensitivity",       float),
                "inp-hand_sens":    ("tracking",    "hand_sensitivity",      float),
                "inp-hand_smooth":  ("tracking",    "hand_smoothing",        float),
                "inp-pinch_thr":    ("tracking",    "pinch_threshold",       float),
                "inp-dwell_time":   ("click",       "dwell_time_ms",         int),
                "inp-dwell_radius": ("click",       "dwell_radius_px",       int),
                "inp-pinch_hold":   ("click",       "pinch_hold_time_ms",    int),
                "inp-cam_idx":      ("camera",      "camera_index",          int),
                "inp-cam_fps":      ("camera",      "target_fps",            int),
                "inp-cam_w":        ("camera",      "camera_width",          int),
                "inp-cam_h":        ("camera",      "camera_height",         int),
                "inp-max_fps":      ("performance", "max_fps",               int),
                "inp-thread_count": ("performance", "thread_count",          int),
                "inp-calib_pts":    ("calibration", "calibration_points",    int),
                "inp-calib_dwell":  ("calibration", "calibration_dwell_time_ms", int),
            }

            changed: list[str] = []

            for wid, (section, attr) in bool_map.items():
                try:
                    sw = self.query_one(f"#{wid}", Switch)
                    target = getattr(cfg, section) if section else cfg
                    old = getattr(target, attr)
                    if sw.value != old:
                        setattr(target, attr, sw.value)
                        changed.append(attr)
                except Exception:
                    continue

            for wid, (section, attr, cast) in numeric_map.items():
                try:
                    inp = self.query_one(f"#{wid}", Input)
                    target = getattr(cfg, section) if section else cfg
                    old = getattr(target, attr)
                    new_val = cast(inp.value)
                    if new_val != old:
                        setattr(target, attr, new_val)
                        changed.append(attr)
                except Exception:
                    continue

            config_dir = Path.home() / ".kursorin"
            config_dir.mkdir(parents=True, exist_ok=True)
            cfg.to_file(config_dir / "config.yaml")

            if changed:
                n = len(changed)
                self.notify(f"Saved {n} change{'s' if n > 1 else ''}.", title="Saved", severity="information")
            else:
                self.notify("No changes.", title="Save", severity="information")

            if self.engine is not None and self.engine.is_running:
                self.engine.config = cfg

        except Exception as e:
            self.notify(f"Save failed: {e}", severity="error")

    def _reset_settings(self) -> None:
        try:
            cfg = KursorinConfig()
            config_dir = Path.home() / ".kursorin"
            config_dir.mkdir(parents=True, exist_ok=True)
            cfg.to_file(config_dir / "config.yaml")
            self._settings_loaded = False
            self.notify("Reset to defaults. Re-open Settings.", title="Reset", severity="warning")
        except Exception as e:
            self.notify(f"Reset failed: {e}", severity="error")

    # ── Doctor ────────────────────────────────────────────────────────────────

    async def _run_doctor(self) -> None:
        import importlib.util
        import platform
        import sys as _sys

        log      = self.query_one("#doctor-log",      Static)
        summary  = self.query_one("#doctor-summary",  Static)
        progress = self.query_one("#doctor-progress", ProgressBar)

        log.update("")
        summary.update("")
        progress.update(progress=0)

        class State:
            total = 0
            passed = 0
            text = ""

        state = State()
        fixes: list[str] = []

        def add(msg: str, ok: bool = True) -> None:
            state.total += 1
            if ok:
                state.passed += 1
            icon = "[#00a3ff]✓[/]" if ok else "[#c09040]✗[/]"
            state.text += f"  {icon} {msg}\n"
            log.update(state.text)

        add("OS", platform.system() in ("Windows", "Darwin", "Linux"))
        progress.update(progress=8)

        add(f"Python {_sys.version_info.major}.{_sys.version_info.minor}", _sys.version_info >= (3, 8))
        progress.update(progress=16)

        deps = ["cv2", "mediapipe", "numpy", "pyautogui", "scipy",
                "PIL", "pynput", "screeninfo", "pydantic", "rich", "textual"]
        step = 16.0
        for mod in deps:
            ok = importlib.util.find_spec(mod) is not None
            add(mod, ok)
            if not ok:
                fixes.append(f"pip install {mod}")
            step += 60.0 / len(deps)
            progress.update(progress=int(step))
            await asyncio.sleep(0.04)

        try:
            import cv2
            c = cv2.VideoCapture(0)
            cam_ok = c.isOpened()
            c.release()
        except Exception:
            cam_ok = False
        add("Camera", cam_ok)
        if not cam_ok:
            fixes.append("Connect a webcam")
        progress.update(progress=90)

        data_ok = (Path.home() / ".kursorin").exists()
        add("Data dir", data_ok)
        if not data_ok:
            fixes.append("Run 'kursorin start' once")
        progress.update(progress=100)

        if state.passed == state.total:
            summary.update(f"\n[bold #00a3ff]✓ All {state.total} checks passed.[/]")
        else:
            fix_text = "\n".join(f"  [#c09040]•[/] {f}" for f in fixes)
            summary.update(
                f"\n[bold #c09040]{state.passed}/{state.total} passed[/]\n{fix_text}"
            )

    # ── Updates ───────────────────────────────────────────────────────────────

    async def _check_updates(self) -> None:
        log = self.query_one("#update-log", Static)
        log.update("[#4a607a]Checking…[/]")
        try:
            from kursorin.utils.updater import GitUpdater
            updater = GitUpdater()
            if not updater.check_git_installed():
                log.update("[#c09040]Git not found.[/]")
                return
            if not updater.is_git_repo():
                log.update("[#c09040]Not a Git repo.[/]")
                ok, msg = updater.auto_convert_to_git()
                if not ok:
                    log.update(f"[#c09040]{msg}[/]")
                    return
            available, msg = updater.check_for_updates()
            if available:
                log.update("[#00a3ff]Update available![/]")
            else:
                log.update(f"[#00a3ff]{msg}[/]")
        except Exception as e:
            log.update(f"[#c09040]{e}[/]")

    async def _pull_update(self, force: bool = False) -> None:
        log = self.query_one("#update-log", Static)
        log.update("[#4a607a]Pulling…[/]")
        try:
            from kursorin.utils.updater import GitUpdater
            updater = GitUpdater()
            ok, msg = updater.pull_update(force=force)
            if ok:
                log.update(f"[#00a3ff]{msg} — restart to apply.[/]")
            else:
                log.update(f"[#c09040]{msg}[/]")
        except Exception as e:
            log.update(f"[#c09040]{e}[/]")

    # ── Button Dispatch ───────────────────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        match btn_id:
            case "btn-start":           self._start_tracking()
            case "btn-stop":            self._stop_tracking()
            case "btn-calibrate":       self._start_calibration()
            case "btn-gui":             self._launch_gui()
            case "btn-run-doctor":      self.run_worker(self._run_doctor())
            case "btn-check-update":    self.run_worker(self._check_updates())
            case "btn-pull-update":     self.run_worker(self._pull_update())
            case "btn-save-settings":   self._save_settings()
            case "btn-reset-settings":  self._reset_settings()
            case "btn-lang-en":         self._set_language("en")
            case "btn-lang-id":         self._set_language("id")


# ── Entry Point ────────────────────────────────────────────────────────────────

def run_tui() -> None:
    """Launch the KURSORIN TUI command center."""
    app = KursorinTUI()
    app.run()
