"""
KURSORIN TUI — Main Application

Single-view command center with tab-based navigation.
Surveillance/Industrial aesthetic.
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
    ProgressBar, TabbedContent, TabPane,
)
from textual.widget import Widget

from kursorin import __version__
from kursorin.config import load_config, KursorinConfig
from kursorin.core.kursorin_engine import KursorinEngine
from kursorin.i18n import t, init_lang, get_lang, set_lang, save_lang
from kursorin.tui.widgets.logo import LogoWidget
from kursorin.tui.widgets.status_indicator import StatusIndicator
from kursorin.tui.widgets.accuracy_meter import AccuracyMeter


CSS_PATH = Path(__file__).parent / "app.tcss"

# ── Inline compact widgets ─────────────────────────────────────────────────────

class StatCard(Widget):
    """A compact metric card."""
    def __init__(self, value: str, label: str, **kwargs):
        super().__init__(**kwargs)
        self._value = value
        self._label = label

    def render(self) -> str:
        return f"[bold #0dccb0]{self._value}[/]\n[#384050]{self._label}[/]"

    def update_value(self, value: str) -> None:
        self._value = value
        self.refresh()


class StatusDot(Widget):
    """Inline status indicator (compact, no pulsing)."""
    def __init__(self, label: str, status: str = "idle", **kwargs):
        super().__init__(**kwargs)
        self._label = label
        self._status = status

    def set_status(self, status: str) -> None:
        self._status = status
        self.refresh()

    def render(self) -> str:
        colors = {"online": "#0dccb0", "warning": "#f0a030",
                  "offline": "#e84040", "idle": "#384050"}
        symbols = {"online": "●", "warning": "◈", "offline": "✖", "idle": "○"}
        c = colors.get(self._status, "#384050")
        s = symbols.get(self._status, "○")
        return f"[{c}]{s}[/] [#8090a0]{self._label}[/]"


class SettingToggle(Horizontal):
    """A setting row with label + switch."""
    DEFAULT_CSS = """
    SettingToggle { height: 3; padding: 0 1; }
    SettingToggle:hover { background: #0c1018; }
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
    """A setting row with label + text input."""
    DEFAULT_CSS = """
    SettingInput { height: 3; padding: 0 1; }
    SettingInput:hover { background: #0c1018; }
    """
    def __init__(self, label: str, value: str, key: str, **kwargs):
        super().__init__(**kwargs)
        self._label = label
        self._value = value
        self._key = key

    def compose(self) -> Generator[Widget, None, None]:
        yield Static(self._label, classes="setting-label")
        yield Input(value=self._value, id=f"inp-{self._key}", classes="setting-input")


# ── Main App ───────────────────────────────────────────────────────────────────

class KursorinTUI(App):
    """KURSORIN — Surveillance-grade single-view command center."""

    CSS_PATH = "app.tcss"
    TITLE = "KURSORIN"
    SUB_TITLE = "HCI Command Center"

    engine: Optional[KursorinEngine] = None

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("escape", "focus_cmd", "Command", show=True),
        Binding("ctrl+l", "toggle_lang", "Language", show=True),
        Binding("ctrl+s", "save_settings", "Save", show=True),
        Binding("ctrl+d", "switch_dashboard", "Dashboard", show=False),
    ]

    # ── Compose ───────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        init_lang()

        # Header
        yield Static(
            f"  [bold #0dccb0]⬡ KURSORIN[/]  "
            f"[#0d2922]│[/]  "
            f"[#384050]v{__version__}[/]  "
            f"[#0d2922]│[/]  "
            f"[#384050]{t('cli.subtitle')}[/]",
            id="header-bar"
        )

        # Scrollable body
        with VerticalScroll(id="main-scroll"):

            # Logo (animated)
            with Center():
                yield LogoWidget(id="logo-art")
            with Center():
                yield Static(
                    f"[#384050]{t('cli.subtitle')}[/]",
                    id="logo-subtitle"
                )

            # Command input
            with Center():
                yield Input(
                    placeholder=(
                        "  Type a command:  "
                        "start · stop · settings · doctor · training · update · lang · quit"
                    ),
                    id="cmd-input"
                )

            # Hint chips
            with Center():
                yield Static(
                    "[#0d2922]── [/]"
                    "[#0dccb0]start[/] [#384050]·[/] "
                    "[#0dccb0]stop[/] [#384050]·[/] "
                    "[#0dccb0]settings[/] [#384050]·[/] "
                    "[#0dccb0]doctor[/] [#384050]·[/] "
                    "[#0dccb0]training[/] [#384050]·[/] "
                    "[#0dccb0]update[/] [#384050]·[/] "
                    "[#f0a030]calibrate[/] [#384050]·[/] "
                    "[#e84040]quit[/]"
                    " [#0d2922]──[/]",
                    id="hint-chips"
                )

            Static("", classes="spacer-xs")

            # ── TABBED CONTENT ──
            with TabbedContent(
                "Dashboard", "Settings", "Doctor", "Training", "Updates", "Language",
                id="main-tabs"
            ):

                # ── TAB 1: DASHBOARD ──────────────────────────────────────
                with TabPane("Dashboard", id="tab-dashboard"):
                    with Container(classes="panel"):
                        yield Static(
                            "[bold #0dccb0]⬡ Dashboard[/]  [#384050]System overview & quick actions[/]",
                            classes="panel-title"
                        )
                        yield Rule()

                        # Status dots row
                        with Horizontal(id="status-dots"):
                            yield StatusDot("Camera", "idle", id="dot-camera")
                            yield StatusDot("Head",   "idle", id="dot-head")
                            yield StatusDot("Eye",    "idle", id="dot-eye")
                            yield StatusDot("Hand",   "idle", id="dot-hand")

                        Static("", classes="spacer-xs")

                        # Metric cards
                        with Horizontal(id="stats-row"):
                            yield StatCard("—",           "FPS",     id="stat-fps")
                            yield StatCard("—",           "Latency", id="stat-latency")
                            yield StatCard("—",           "Uptime",  id="stat-uptime")
                            yield StatCard(f"v{__version__}", "Version", id="stat-version")

                        Static("", classes="spacer-xs")

                        # Actions
                        yield Button("▶  Start Tracking",  id="btn-start",     classes="action-btn -primary")
                        yield Button("⏹  Stop Tracking",   id="btn-stop",      classes="action-btn -danger")
                        yield Button("🎯  Calibrate Eyes",  id="btn-calibrate", classes="action-btn -amber")
                        yield Button("🖥  Launch GUI",      id="btn-gui",       classes="action-btn")

                # ── TAB 2: SETTINGS ──────────────────────────────────────
                with TabPane("Settings", id="tab-settings"):
                    with Container(classes="panel"):
                        yield Static(
                            "[bold #f0a030]⚙  Settings[/]  [#384050]Configure KURSORIN — press Ctrl+S to save[/]",
                            classes="panel-title"
                        )
                        yield Rule()
                        yield Static("[#384050]Loading settings...[/]", id="settings-placeholder")

                # ── TAB 3: DOCTOR ─────────────────────────────────────────
                with TabPane("Doctor", id="tab-doctor"):
                    with Container(classes="panel"):
                        yield Static(
                            "[bold #0dccb0]🩺 Doctor[/]  [#384050]System diagnostics[/]",
                            classes="panel-title"
                        )
                        yield Rule()
                        yield Button("▶  Run Diagnostics", id="btn-run-doctor", classes="action-btn -primary")
                        Static("", classes="spacer-xs")
                        yield ProgressBar(total=100, show_eta=False, id="doctor-progress")
                        yield Static("", id="doctor-log")
                        yield Static("", id="doctor-summary")

                # ── TAB 4: TRAINING ───────────────────────────────────────
                with TabPane("Training", id="tab-training"):
                    with Container(classes="panel"):
                        yield Static(
                            "[bold #f0a030]◎ Training Accuracy[/]  [#384050]Live modality tracking quality[/]",
                            classes="panel-title"
                        )
                        yield Rule()
                        yield Static(
                            "[#384050]Start tracking to see live accuracy metrics.[/]",
                            id="training-hint"
                        )
                        Static("", classes="spacer-xs")
                        with Vertical(id="accuracy-grid"):
                            yield AccuracyMeter("Head Tracking",  0.0, id="acc-head")
                            yield AccuracyMeter("Eye Tracking",   0.0, id="acc-eye")
                            yield AccuracyMeter("Hand Tracking",  0.0, id="acc-hand")
                            yield AccuracyMeter("Overall Fusion", 0.0, id="acc-fused")
                        Static("", classes="spacer-xs")
                        with Horizontal():
                            yield Static(
                                "[#384050]Calibration:[/] ",
                                id="calib-label"
                            )
                            yield Static(
                                "[#e84040]Not calibrated[/]",
                                id="calib-status"
                            )
                        Static("", classes="spacer-xs")
                        yield Button("🎯  Run Calibration", id="btn-calib-training", classes="action-btn -amber")

                # ── TAB 5: UPDATES ────────────────────────────────────────
                with TabPane("Updates", id="tab-updates"):
                    with Container(classes="panel"):
                        yield Static(
                            "[bold #0dccb0]🔄 Updates[/]  [#384050]Keep KURSORIN current[/]",
                            classes="panel-title"
                        )
                        yield Rule()
                        yield Static(
                            f"[#8090a0]Current:[/] [bold #0dccb0]v{__version__}[/]",
                            id="cur-version"
                        )
                        Static("", classes="spacer-xs")
                        yield Button("🔍  Check for Updates", id="btn-check-update",  classes="action-btn -primary")
                        yield Button("⬇   Pull Update",       id="btn-pull-update",   classes="action-btn")
                        yield Button("⚠   Force Update",      id="btn-force-update",  classes="action-btn -danger")
                        Static("", classes="spacer-xs")
                        yield Static("", id="update-log")

                # ── TAB 6: LANGUAGE ───────────────────────────────────────
                with TabPane("Language", id="tab-lang"):
                    with Container(classes="panel"):
                        yield Static(
                            "[bold #0dccb0]🌐 Language[/]  [#384050]Switch interface language[/]",
                            classes="panel-title"
                        )
                        yield Rule()
                        yield Static("", id="lang-current")
                        Static("", classes="spacer-xs")
                        yield Button("🇺🇸  English",          id="btn-lang-en", classes="action-btn")
                        yield Button("🇮🇩  Bahasa Indonesia",  id="btn-lang-id", classes="action-btn")

            # Bottom spacer
            Static("", classes="spacer-lg")

        # Status bar
        yield Static(
            f"  [#384050]~/.kursorin[/]  "
            f"[#0d2922]│[/]  "
            f"[#0dccb0]⬡[/] [#384050]Ready[/]  "
            f"[#0d2922]│[/]  "
            f"[#384050]Ctrl+S save · Ctrl+L lang · Q quit[/]",
            id="status-bar"
        )

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def on_mount(self) -> None:
        self.query_one("#cmd-input", Input).focus()
        self._update_lang_display()
        self._check_calibration_status()
        # Load settings lazily
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

    def action_switch_dashboard(self) -> None:
        self._switch_tab("tab-dashboard")

    # ── Tab Switching ─────────────────────────────────────────────────────────

    def _switch_tab(self, tab_id: str) -> None:
        try:
            tabs = self.query_one("#main-tabs", TabbedContent)
            tabs.active = tab_id
        except Exception:
            pass

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
            ("settings", "config", "s", "cfg"): lambda: self._switch_tab("tab-settings"),
            ("doctor", "diag", "health"):        lambda: self._switch_tab("tab-doctor"),
            ("training", "train", "accuracy"):   lambda: self._switch_tab("tab-training"),
            ("update", "updates", "u"):          lambda: self._switch_tab("tab-updates"),
            ("lang", "language", "l"):           lambda: self._switch_tab("tab-lang"),
            ("dashboard", "home", "d", "dash"):  lambda: self._switch_tab("tab-dashboard"),
            ("calibrate", "calib"):              lambda: self._start_calibration(),
            ("gui",):                            lambda: self._launch_gui(),
            ("save",):                           lambda: self._save_settings(),
            ("reset",):                          lambda: self._reset_settings(),
            ("en", "english"):                   lambda: self._set_language("en"),
            ("id", "indonesian", "indo"):         lambda: self._set_language("id"),
            ("quit", "q", "exit", "bye"):         lambda: self.exit(),
            ("help", "?", "h"):                  lambda: self._show_help(),
        }

        for keys, fn in routes.items():
            if cmd in keys:
                fn()
                return

        self.notify(
            f"Unknown command: [bold]{cmd}[/]\nType [bold #0dccb0]help[/] for commands.",
            title="⬡",
            severity="warning",
        )

    def _show_help(self) -> None:
        lines = [
            "[bold #0dccb0]Available commands[/]",
            "  [#f0a030]start[/] · [#f0a030]stop[/]  — Toggle tracking engine",
            "  [#0dccb0]settings[/]          — Configuration panel",
            "  [#0dccb0]doctor[/]            — System diagnostics",
            "  [#0dccb0]training[/]          — Live accuracy metrics",
            "  [#0dccb0]update[/]            — Software updates",
            "  [#0dccb0]calibrate[/]         — Eye calibration",
            "  [#0dccb0]lang[/]              — Switch language",
            "  [#e84040]quit[/]              — Exit KURSORIN",
        ]
        self.notify("\n".join(lines), title="Help", severity="information")

    # ── Engine Control ────────────────────────────────────────────────────────

    def _start_tracking(self) -> None:
        if self.engine is not None and self.engine.is_running:
            self.notify("Engine already running.", title="▶", severity="information")
            return
        try:
            cfg = load_config()
            self.engine = KursorinEngine(cfg)
            self.engine.start()

            # Update button labels
            try:
                self.query_one("#btn-start", Button).label = "● Running…"
            except Exception:
                pass

            # Update dots
            self._set_dot("dot-camera", "online")
            self._set_dot("dot-head",   "online" if cfg.tracking.head_enabled else "offline")
            self._set_dot("dot-eye",    "online" if cfg.tracking.eye_enabled  else "offline")
            self._set_dot("dot-hand",   "online" if cfg.tracking.hand_enabled else "offline")

            # Update status bar
            try:
                self.query_one("#status-bar", Static).update(
                    f"  [#384050]~/.kursorin[/]  "
                    f"[#0d2922]│[/]  "
                    f"[#0dccb0]●[/] [bold #0dccb0]TRACKING[/]  "
                    f"[#0d2922]│[/]  "
                    f"[#384050]Ctrl+S save · Q quit[/]"
                )
            except Exception:
                pass

            self.notify("Engine started!", title="▶ Tracking", severity="information")
            self.run_worker(self._update_dashboard_loop())

        except Exception as e:
            self.notify(f"Failed to start: {e}", title="Error", severity="error")

    def _stop_tracking(self) -> None:
        if self.engine is None or not self.engine.is_running:
            self.notify("Engine is not running.", title="⏹", severity="warning")
            return
        try:
            self.engine.stop()
        except Exception:
            pass
        finally:
            self.engine = None

        # Reset UI
        try:
            self.query_one("#btn-start", Button).label = "▶  Start Tracking"
        except Exception:
            pass
        for dot in ("dot-camera", "dot-head", "dot-eye", "dot-hand"):
            self._set_dot(dot, "idle")

        # Reset accuracy meters
        for aid in ("acc-head", "acc-eye", "acc-hand", "acc-fused"):
            try:
                self.query_one(f"#{aid}", AccuracyMeter).update_value(0.0)
            except Exception:
                pass

        # Reset status bar
        try:
            self.query_one("#status-bar", Static).update(
                f"  [#384050]~/.kursorin[/]  "
                f"[#0d2922]│[/]  "
                f"[#0dccb0]⬡[/] [#384050]Ready[/]  "
                f"[#0d2922]│[/]  "
                f"[#384050]Ctrl+S save · Ctrl+L lang · Q quit[/]"
            )
        except Exception:
            pass

        self.notify("Engine stopped.", title="⏹ Tracking", severity="warning")

    def _set_dot(self, dot_id: str, status: str) -> None:
        try:
            self.query_one(f"#{dot_id}", StatusDot).set_status(status)
        except Exception:
            pass

    async def _update_dashboard_loop(self) -> None:
        """Live update of metrics and accuracy while engine is running."""
        while self.engine is not None and self.engine.is_running:
            try:
                fps = getattr(self.engine, "fps", 0.0)
                lat = getattr(self.engine, "latency_ms", 0.0)
                st  = getattr(self.engine, "_start_time", None)
                uptime = time.time() - st if st else 0.0

                self.query_one("#stat-fps",     StatCard).update_value(f"{fps:.1f}")
                self.query_one("#stat-latency", StatCard).update_value(f"{lat:.0f}ms")
                self.query_one("#stat-uptime",  StatCard).update_value(f"{uptime:.0f}s")

                # Accuracy estimates
                # Use engine state/confidence if available, else derive from fps
                head_acc  = self._derive_accuracy("head",  fps)
                eye_acc   = self._derive_accuracy("eye",   fps)
                hand_acc  = self._derive_accuracy("hand",  fps)
                fused_acc = (head_acc + eye_acc + hand_acc) / 3.0

                self.query_one("#acc-head",  AccuracyMeter).update_value(head_acc)
                self.query_one("#acc-eye",   AccuracyMeter).update_value(eye_acc)
                self.query_one("#acc-hand",  AccuracyMeter).update_value(hand_acc)
                self.query_one("#acc-fused", AccuracyMeter).update_value(fused_acc)

                # Training hint
                try:
                    self.query_one("#training-hint", Static).update(
                        f"[#0dccb0]Engine running — FPS: {fps:.1f} · Uptime: {uptime:.0f}s[/]"
                    )
                except Exception:
                    pass

            except Exception:
                pass
            await asyncio.sleep(0.4)

    def _derive_accuracy(self, modality: str, fps: float) -> float:
        """
        Derive a rough accuracy estimate from engine state.
        If the engine exposes per-modality confidence, use it.
        Otherwise estimates quality from FPS stability.
        """
        if self.engine is None:
            return 0.0

        # Try to get real confidence values from engine/trackers
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

        # Attempt to read from engine fusion state
        try:
            fusion = self.engine._fusion  # type: ignore
            if fusion is not None:
                weights = getattr(fusion, "_weights", {})
                w = weights.get(modality, 0.0)
                return min(100.0, w * 200.0)
        except Exception:
            pass

        # Fallback: derive from FPS (rough proxy for tracking quality)
        if fps <= 0:
            return 0.0
        target = 30.0
        ratio = min(fps / target, 1.0)
        base = {
            "head": 85.0,
            "eye":  72.0,
            "hand": 78.0,
        }.get(modality, 70.0)
        return base * ratio

    # ── Calibration / GUI ─────────────────────────────────────────────────────

    def _start_calibration(self) -> None:
        self.notify(
            "Run [bold]kursorin calibrate[/] from a terminal\n"
            "or use the GUI for the full calibration flow.",
            title="🎯 Calibration",
            severity="information",
        )

    def _launch_gui(self) -> None:
        try:
            import kursorin.app as kapp
            self.notify("Launching GUI…", title="🖥", severity="information")
            kapp.main()
        except Exception as e:
            self.notify(f"GUI Error: {e}", severity="error")

    def _check_calibration_status(self) -> None:
        calib_path = Path.home() / ".kursorin" / "calibration.json"
        try:
            if calib_path.exists():
                self.query_one("#calib-status", Static).update(
                    "[#0dccb0]✓ Calibration file found[/]"
                )
            else:
                self.query_one("#calib-status", Static).update(
                    "[#e84040]Not calibrated — run 'kursorin calibrate'[/]"
                )
        except Exception:
            pass

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
                f"  [#8090a0]Current language:[/]  {flag} [bold #0dccb0]{name}[/]"
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
            panel = self.query_one("#tab-settings")
            self.call_after_refresh(lambda: self._mount_settings(panel, cfg))
        except Exception as e:
            self.notify(f"Failed to load settings: {e}", severity="error")

    def _mount_settings(self, panel, cfg: KursorinConfig) -> None:
        async def do_mount():
            try:
                ph = panel.query_one("#settings-placeholder")
                await ph.remove()
            except Exception:
                pass

            container = panel.query_one(Container)

            sections = Vertical(id="settings-sections")
            await container.mount(sections)

            # ── Tracking ──
            await sections.mount(Static("[bold #f0a030]━━ Tracking[/]", classes="settings-section-title"))
            await sections.mount(SettingToggle("Head Tracking",      cfg.tracking.head_enabled, "head_enabled"))
            await sections.mount(SettingToggle("Eye Tracking",       cfg.tracking.eye_enabled,  "eye_enabled"))
            await sections.mount(SettingToggle("Hand Tracking",      cfg.tracking.hand_enabled, "hand_enabled"))
            await sections.mount(SettingToggle("Invert X (Global)",  cfg.tracking.invert_x,     "invert_x"))
            await sections.mount(SettingToggle("Invert Y (Global)",  cfg.tracking.invert_y,     "invert_y"))
            await sections.mount(SettingToggle("Head: Invert X",     cfg.tracking.head_invert_x,"head_invert_x"))
            await sections.mount(SettingToggle("Head: Invert Y",     cfg.tracking.head_invert_y,"head_invert_y"))
            await sections.mount(SettingToggle("Eye: Invert X",      cfg.tracking.eye_invert_x, "eye_invert_x"))
            await sections.mount(SettingToggle("Eye: Invert Y",      cfg.tracking.eye_invert_y, "eye_invert_y"))
            await sections.mount(SettingInput("Head Sensitivity X",  str(cfg.tracking.head_sensitivity_x), "head_sens_x"))
            await sections.mount(SettingInput("Head Sensitivity Y",  str(cfg.tracking.head_sensitivity_y), "head_sens_y"))
            await sections.mount(SettingInput("Head Smoothing",      str(cfg.tracking.head_smoothing),     "head_smooth"))
            await sections.mount(SettingInput("Eye Sensitivity",     str(cfg.tracking.eye_sensitivity),    "eye_sens"))
            await sections.mount(SettingInput("Hand Sensitivity",    str(cfg.tracking.hand_sensitivity),   "hand_sens"))
            await sections.mount(SettingInput("Hand Smoothing",      str(cfg.tracking.hand_smoothing),     "hand_smooth"))
            await sections.mount(SettingInput("Pinch Threshold",     str(cfg.tracking.pinch_threshold),    "pinch_thr"))

            # ── Click ──
            await sections.mount(Static("[bold #f0a030]━━ Click Methods[/]", classes="settings-section-title"))
            await sections.mount(SettingToggle("Blink Click",  cfg.click.blink_click_enabled, "blink_click"))
            await sections.mount(SettingToggle("Dwell Click",  cfg.click.dwell_click_enabled, "dwell_click"))
            await sections.mount(SettingToggle("Pinch Click",  cfg.click.pinch_click_enabled, "pinch_click"))
            await sections.mount(SettingToggle("Mouth Click",  cfg.click.mouth_click_enabled, "mouth_click"))
            await sections.mount(SettingInput("Dwell Time (ms)",   str(cfg.click.dwell_time_ms),  "dwell_time"))
            await sections.mount(SettingInput("Dwell Radius (px)", str(cfg.click.dwell_radius_px),"dwell_radius"))
            await sections.mount(SettingInput("Pinch Hold (ms)",   str(cfg.click.pinch_hold_time_ms),"pinch_hold"))

            # ── Camera ──
            await sections.mount(Static("[bold #f0a030]━━ Camera[/]", classes="settings-section-title"))
            await sections.mount(SettingInput("Camera Index",   str(cfg.camera.camera_index),  "cam_idx"))
            await sections.mount(SettingInput("Target FPS",     str(cfg.camera.target_fps),    "cam_fps"))
            await sections.mount(SettingInput("Width",          str(cfg.camera.camera_width),  "cam_w"))
            await sections.mount(SettingInput("Height",         str(cfg.camera.camera_height), "cam_h"))
            await sections.mount(SettingToggle("Mirror Mode",   cfg.camera.flip_horizontal,    "cam_mirror"))
            await sections.mount(SettingToggle("Auto Exposure", cfg.camera.auto_exposure,      "cam_ae"))
            await sections.mount(SettingToggle("Auto Focus",    cfg.camera.auto_focus,         "cam_af"))

            # ── Performance ──
            await sections.mount(Static("[bold #f0a030]━━ Performance[/]", classes="settings-section-title"))
            await sections.mount(SettingToggle("Multi-Threading",   cfg.performance.use_threading,    "threading"))
            await sections.mount(SettingToggle("GPU Acceleration",  cfg.performance.use_gpu,          "gpu"))
            await sections.mount(SettingToggle("Power Save Mode",   cfg.performance.power_save_mode,  "power_save"))
            await sections.mount(SettingInput("Max FPS",            str(cfg.performance.max_fps),     "max_fps"))
            await sections.mount(SettingInput("Thread Count",       str(cfg.performance.thread_count),"thread_count"))

            # ── Appearance / UI ──
            await sections.mount(Static("[bold #f0a030]━━ Appearance[/]", classes="settings-section-title"))
            await sections.mount(SettingToggle("Show Video Preview", cfg.ui.show_preview,       "show_preview"))
            await sections.mount(SettingToggle("Show Overlay",       cfg.ui.show_overlay,       "show_overlay"))
            await sections.mount(SettingToggle("Cursor Trail",        cfg.ui.cursor_trail,       "cursor_trail"))
            await sections.mount(SettingToggle("Audio Feedback",      cfg.ui.audio_feedback,     "audio_fb"))
            await sections.mount(SettingToggle("Click Sound",         cfg.ui.click_sound,        "click_sound"))
            await sections.mount(SettingToggle("High Contrast",       cfg.ui.high_contrast,      "high_contrast"))
            await sections.mount(SettingToggle("Show Notifications",  cfg.ui.show_notifications, "notifs"))

            # ── Calibration ──
            await sections.mount(Static("[bold #f0a030]━━ Calibration[/]", classes="settings-section-title"))
            await sections.mount(SettingToggle("Auto Calibration",   cfg.calibration.auto_calibration, "auto_calib"))
            await sections.mount(SettingInput("Calibration Points",  str(cfg.calibration.calibration_points), "calib_pts"))
            await sections.mount(SettingInput("Dwell Time (ms)",     str(cfg.calibration.calibration_dwell_time_ms), "calib_dwell"))
            await sections.mount(SettingToggle("Save Calibration",   cfg.calibration.save_calibration, "save_calib"))

            # ── Debug ──
            await sections.mount(Static("[bold #f0a030]━━ Debug[/]", classes="settings-section-title"))
            await sections.mount(SettingToggle("Debug Mode", cfg.debug_mode, "debug_mode"))

            # ── Actions ──
            await sections.mount(Static("", classes="spacer-xs"))
            actions = Horizontal(id="settings-actions")
            await sections.mount(actions)
            await actions.mount(Button("💾  Save", id="btn-save-settings", classes="action-btn -primary"))
            await actions.mount(Button("↺  Reset to Defaults", id="btn-reset-settings", classes="action-btn -danger"))

        self.run_worker(do_mount())

    # ── Settings Persistence ──────────────────────────────────────────────────

    def _save_settings(self) -> None:
        try:
            cfg = load_config()

            # Boolean switch map
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
                "sw-high_contrast":  ("ui",          "high_contrast"),
                "sw-notifs":         ("ui",          "show_notifications"),
                "sw-auto_calib":     ("calibration", "auto_calibration"),
                "sw-save_calib":     ("calibration", "save_calibration"),
                "sw-debug_mode":     (None,           "debug_mode"),
            }

            # Numeric input map
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

            changed = []

            for wid, (section, attr) in bool_map.items():
                try:
                    sw = self.query_one(f"#{wid}", Switch)
                    target = getattr(cfg, section) if section else cfg
                    old = getattr(target, attr)
                    if sw.value != old:
                        setattr(target, attr, sw.value)
                        changed.append(f"{attr}={sw.value}")
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
                        changed.append(f"{attr}={new_val}")
                except Exception:
                    continue

            # Write to disk
            config_dir = Path.home() / ".kursorin"
            config_dir.mkdir(parents=True, exist_ok=True)
            cfg.to_file(config_dir / "config.yaml")

            if changed:
                summary = ", ".join(changed[0:3])
                if len(changed) > 3:
                    summary += f" +{len(changed) - 3} more"
                self.notify(
                    f"Saved [{summary}]",
                    title="💾 Settings Saved",
                    severity="information",
                )
            else:
                self.notify("No changes detected.", title="💾", severity="information")

            # Apply to live engine if running
            if self.engine is not None and self.engine.is_running:
                self.engine.config = cfg

        except Exception as e:
            self.notify(f"Save failed: {e}", severity="error")

    def _reset_settings(self) -> None:
        """Reset config to defaults and persist."""
        try:
            from kursorin.config import KursorinConfig as KC
            cfg = KC()
            config_dir = Path.home() / ".kursorin"
            config_dir.mkdir(parents=True, exist_ok=True)
            cfg.to_file(config_dir / "config.yaml")

            # Force settings reload next time
            self._settings_loaded = False

            self.notify(
                "All settings have been reset to factory defaults.\n"
                "Re-open the Settings tab to see changes.",
                title="↺ Reset",
                severity="warning",
            )
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

        class DoctorState:
            total = 0
            passed = 0
            text = ""

        state = DoctorState()
        fixes: list[str] = []

        def add(msg: str, ok: bool = True) -> None:
            state.total += 1
            if ok:
                state.passed += 1
            icon = "[#0dccb0]✓[/]" if ok else "[#e84040]✗[/]"
            state.text += f"  {icon} {msg}\n"
            log.update(state.text)

        add("OS Compatibility", platform.system() in ("Windows", "Darwin", "Linux"))
        progress.update(progress=8)

        add(f"Python {_sys.version_info.major}.{_sys.version_info.minor}", _sys.version_info >= (3, 8))
        progress.update(progress=16)

        deps = ["cv2", "mediapipe", "numpy", "pyautogui", "scipy",
                "PIL", "pynput", "screeninfo", "pydantic", "rich", "textual"]
        step = 16
        for mod in deps:
            ok = importlib.util.find_spec(mod) is not None
            add(f"Module: {mod}", ok)
            if not ok:
                fixes.append(f"pip install {mod}")
            step += 60 / len(deps)
            progress.update(progress=int(step))
            await asyncio.sleep(0.05)

        # Camera
        try:
            import cv2
            c = cv2.VideoCapture(0)
            cam_ok = c.isOpened()
            c.release()
        except Exception:
            cam_ok = False
        add("Camera accessible", cam_ok)
        if not cam_ok:
            fixes.append("Connect a webcam and ensure no other app is using it")
        progress.update(progress=90)

        # Data dir
        data_ok = (Path.home() / ".kursorin").exists()
        add("Data directory (~/.kursorin)", data_ok)
        if not data_ok:
            fixes.append("Run 'kursorin start' once to create the data directory")
        progress.update(progress=100)

        if state.passed == state.total:
            summary.update(f"\n[bold #0dccb0]✓ All {state.total} checks passed — system is healthy.[/]")
        else:
            fix_text = "\n".join(f"  [#f0a030]•[/] {f}" for f in fixes)
            summary.update(
                f"\n[bold #e84040]⚠ {state.passed}/{state.total} checks passed[/]\n"
                f"[#8090a0]Recommended fixes:[/]\n{fix_text}"
            )

    # ── Updates ───────────────────────────────────────────────────────────────

    async def _check_updates(self) -> None:
        log = self.query_one("#update-log", Static)
        log.update("[#384050]Checking for updates…[/]")
        try:
            from kursorin.utils.updater import GitUpdater
            updater = GitUpdater()
            if not updater.check_git_installed():
                log.update("[#e84040]✗ Git not found.[/]")
                return
            if not updater.is_git_repo():
                log.update("[#f0a030]⚠ Not a Git repo. Converting…[/]")
                ok, msg = updater.auto_convert_to_git()
                if not ok:
                    log.update(f"[#e84040]✗ {msg}[/]")
                    return
            available, msg = updater.check_for_updates()
            if available:
                log.update("[#0dccb0]✓ Update available! Click Pull Update.[/]")
            else:
                log.update(f"[#0dccb0]✓ {msg}[/]")
        except Exception as e:
            log.update(f"[#e84040]✗ {e}[/]")

    async def _pull_update(self, force: bool = False) -> None:
        log = self.query_one("#update-log", Static)
        mode = "force" if force else "normal"
        log.update(f"[#384050]Pulling ({mode})…[/]")
        try:
            from kursorin.utils.updater import GitUpdater
            updater = GitUpdater()
            ok, msg = updater.pull_update(force=force)
            if ok:
                log.update(f"[#0dccb0]✓ {msg}\nRestart KURSORIN to apply.[/]")
            else:
                log.update(f"[#e84040]✗ {msg}[/]")
        except Exception as e:
            log.update(f"[#e84040]✗ {e}[/]")

    # ── Button Dispatch ───────────────────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        match btn_id:
            case "btn-start":               self._start_tracking()
            case "btn-stop":                self._stop_tracking()
            case "btn-calibrate":           self._start_calibration()
            case "btn-calib-training":      self._start_calibration()
            case "btn-gui":                 self._launch_gui()
            case "btn-run-doctor":          self.run_worker(self._run_doctor())
            case "btn-check-update":        self.run_worker(self._check_updates())
            case "btn-pull-update":         self.run_worker(self._pull_update(force=False))
            case "btn-force-update":        self.run_worker(self._pull_update(force=True))
            case "btn-save-settings":       self._save_settings()
            case "btn-reset-settings":      self._reset_settings()
            case "btn-lang-en":             self._set_language("en")
            case "btn-lang-id":             self._set_language("id")


# ── Entry Point ────────────────────────────────────────────────────────────────

def run_tui() -> None:
    """Launch the KURSORIN TUI command center."""
    app = KursorinTUI()
    app.run()
