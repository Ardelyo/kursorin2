"""
KURSORIN TUI — Main Application

The interactive terminal interface powered by Textual.
Launch with: kursorin (no arguments)
"""

from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static, Button, Footer, Rule
from textual.widget import Widget

from kursorin import __version__
from kursorin.tui.screens.dashboard import DashboardScreen
from kursorin.tui.screens.settings import SettingsScreen
from kursorin.tui.screens.doctor import DoctorScreen
from kursorin.tui.screens.update import UpdateScreen
from kursorin.config import load_config, KursorinConfig


CSS_PATH = Path(__file__).parent / "app.tcss"

SIDEBAR_LOGO = """\
[bold #06d6a0]⬡ KURSORIN[/]
[#576574]v{version}[/]""" 

NAV_ITEMS = [
    ("📊", "Dashboard", "dashboard"),
    ("⚙ ", "Settings", "settings"),
    ("🩺", "Doctor", "doctor"),
    ("🔄", "Updates", "update"),
]


class NavButton(Button):
    def __init__(self, icon: str, label: str, screen_id: str, **kwargs):
        super().__init__(f"{icon}  {label}", **kwargs)
        self.screen_id = screen_id


class KursorinTUI(App):
    """KURSORIN Interactive Terminal Interface."""

    CSS_PATH = "app.tcss"

    TITLE = "KURSORIN"
    SUB_TITLE = "Webcam-Based HCI System"

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("d", "switch_screen('dashboard')", "Dashboard", show=True),
        Binding("s", "switch_screen('settings')", "Settings", show=True),
        Binding("x", "switch_screen('doctor')", "Doctor", show=True),
        Binding("u", "switch_screen('update')", "Updates", show=True),
        Binding("ctrl+p", "command_palette", "Commands", show=True),
    ]

    current_screen_id = "dashboard"

    def compose(self) -> ComposeResult:
        # Header
        yield Static(
            f"  [bold #06d6a0]⬡ KURSORIN[/]  "
            f"[#576574]│[/]  "
            f"[#c8d6e5]Webcam-Based HCI System[/]  "
            f"[#576574]│[/]  "
            f"[#576574]v{__version__}[/]",
            id="header-bar"
        )

        with Horizontal():
            # Sidebar
            with Vertical(id="sidebar"):
                yield Static(
                    SIDEBAR_LOGO.format(version=__version__),
                    id="sidebar-logo"
                )
                yield Rule()

                for icon, label, screen_id in NAV_ITEMS:
                    cls = "nav-btn -active" if screen_id == "dashboard" else "nav-btn"
                    yield NavButton(icon, label, screen_id, classes=cls)

                # Spacer to push lang to bottom
                yield Static("", classes="spacer")
                yield Rule()
                yield NavButton("🌐", "Language", "lang", classes="nav-btn")

            # Main content
            with Container(id="content-area"):
                yield DashboardScreen(id="screen-dashboard")
                yield SettingsScreen(id="screen-settings")
                yield DoctorScreen(id="screen-doctor")
                yield UpdateScreen(id="screen-update")

        # Footer
        yield Footer()

    def on_mount(self) -> None:
        """Initialize: show dashboard, hide others."""
        self._show_screen("dashboard")

    def _show_screen(self, screen_id: str) -> None:
        """Switch visible content screen."""
        self.current_screen_id = screen_id

        for _, _, sid in NAV_ITEMS:
            widget = self.query_one(f"#screen-{sid}", Container)
            widget.display = (sid == screen_id)

        # Update nav button active state
        for btn in self.query(".nav-btn"):
            if isinstance(btn, NavButton):
                if btn.screen_id == screen_id:
                    btn.add_class("-active")
                else:
                    btn.remove_class("-active")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle all button presses."""
        btn_id = event.button.id or ""

        # Navigation buttons
        if btn_id.startswith("nav-"):
            screen_id = btn_id.replace("nav-", "")
            if screen_id == "lang":
                self._toggle_language()
            else:
                self._show_screen(screen_id)
            return

        # Dashboard actions
        if btn_id == "btn-start":
            self._start_tracking()
        elif btn_id == "btn-calibrate":
            self._start_calibration()
        elif btn_id == "btn-gui":
            self._launch_gui()

        # Doctor actions
        elif btn_id == "btn-run-doctor":
            doctor = self.query_one("#screen-doctor", DoctorScreen)
            self.run_worker(doctor.run_diagnostics())

        # Update actions
        elif btn_id == "btn-check-update":
            update = self.query_one("#screen-update", UpdateScreen)
            self.run_worker(update.check_updates())
        elif btn_id == "btn-pull-update":
            update = self.query_one("#screen-update", UpdateScreen)
            self.run_worker(update.pull_update(force=False))
        elif btn_id == "btn-force-update":
            update = self.query_one("#screen-update", UpdateScreen)
            self.run_worker(update.pull_update(force=True))

        # Settings actions
        elif btn_id == "btn-save-settings":
            self._save_settings()
        elif btn_id == "btn-reset-settings":
            self._reset_settings()

    def action_switch_screen(self, screen_id: str) -> None:
        """Keyboard-driven screen switch."""
        self._show_screen(screen_id)

    def _toggle_language(self) -> None:
        """Toggle between en and id."""
        from kursorin.i18n import get_lang, set_lang, save_lang
        current = get_lang()
        new_lang = "id" if current == "en" else "en"
        set_lang(new_lang)
        save_lang(new_lang)
        self.notify(
            f"Language switched to {'Bahasa Indonesia' if new_lang == 'id' else 'English'}",
            title="Language",
            severity="information"
        )

    def _start_tracking(self) -> None:
        """Start tracking engine (exits TUI, runs in terminal)."""
        self.notify(
            "Starting tracking engine...\nPlease use 'kursorin start' from terminal.",
            title="Tracking",
            severity="information"
        )

    def _start_calibration(self) -> None:
        """Start calibration."""
        self.notify(
            "Starting calibration...\nPlease use 'kursorin calibrate' from terminal.",
            title="Calibration",
            severity="information"
        )

    def _launch_gui(self) -> None:
        """Launch the GUI app."""
        self.notify(
            "Launching GUI...\nPlease use 'kursorin gui' from terminal.",
            title="GUI",
            severity="information"
        )

    def _save_settings(self) -> None:
        """Save current settings to config file."""
        try:
            from textual.widgets import Switch, Input
            cfg = load_config()

            # Mapping of widget prefixes and IDs to (section, key, type)
            # types: bool, int, float
            config_map = {
                "sw-head-enabled": ("tracking", "head_enabled", bool),
                "sw-invert-x": ("tracking", "invert_x", bool),
                "sw-invert-y": ("tracking", "invert_y", bool),
                "sw-eye-enabled": ("tracking", "eye_enabled", bool),
                "sw-hand-enabled": ("tracking", "hand_enabled", bool),
                "sw-blink-click": ("click", "blink_click_enabled", bool),
                "sw-dwell-click": ("click", "dwell_click_enabled", bool),
                "sw-pinch-click": ("click", "pinch_click_enabled", bool),
                "sw-mouth-click": ("click", "mouth_click_enabled", bool),
                "sw-cam-mirror": ("camera", "flip_horizontal", bool),
                "sw-cam-ae": ("camera", "auto_exposure", bool),
                "sw-cam-af": ("camera", "auto_focus", bool),
                "sw-threading": ("performance", "use_threading", bool),
                "sw-gpu": ("performance", "use_gpu", bool),
                "sw-power-save": ("performance", "power_save_mode", bool),
                "sw-show-preview": ("ui", "show_preview", bool),
                "sw-show-overlay": ("ui", "show_overlay", bool),
                "sw-cursor-trail": ("ui", "cursor_trail", bool),
                "sw-audio-fb": ("ui", "audio_feedback", bool),
                "sw-click-sound": ("ui", "click_sound", bool),
                "sw-high-contrast": ("ui", "high_contrast", bool),
                "sw-large-ui": ("ui", "large_ui", bool),
                "sw-notifs": ("ui", "show_notifications", bool),
                
                # Inputs
                "inp-head-sens-x": ("tracking", "head_sensitivity_x", float),
                "inp-head-sens-y": ("tracking", "head_sensitivity_y", float),
                "inp-head-smooth": ("tracking", "head_smoothing", float),
                "inp-blink-thresh": ("tracking", "eye_blink_threshold", float),
                "inp-pinch-thresh": ("tracking", "pinch_threshold", float),
                "inp-dwell-time": ("click", "dwell_time_ms", int),
                "inp-dwell-radius": ("click", "dwell_radius_px", int),
                "inp-cam-index": ("camera", "camera_index", int),
                "inp-cam-width": ("camera", "camera_width", int),
                "inp-cam-height": ("camera", "camera_height", int),
                "inp-cam-fps": ("camera", "target_fps", int),
                "inp-max-fps": ("performance", "max_fps", int),
                "inp-thread-count": ("performance", "thread_count", int),
            }

            for widget_id, (section, key, val_type) in config_map.items():
                try:
                    section_obj = getattr(cfg, section)
                    if val_type == bool:
                        sw = self.query_one(f"#{widget_id}", Switch)
                        setattr(section_obj, key, sw.value)
                    else:
                        inp = self.query_one(f"#{widget_id}", Input)
                        if inp.value.strip():
                            setattr(section_obj, key, val_type(inp.value))
                except Exception:
                    continue

            # Save to disk
            cfg_path = Path.home() / ".kursorin" / "config.yaml"
            cfg.to_file(cfg_path)

            self.notify(
                "Settings saved successfully!",
                title="Settings",
                severity="information"
            )
        except Exception as e:
            self.notify(
                f"Failed to save: {e}",
                title="Error",
                severity="error"
            )

    def _reset_settings(self) -> None:
        """Reset settings to defaults."""
        try:
            cfg = KursorinConfig()
            cfg_path = Path.home() / ".kursorin" / "config.yaml"
            cfg.to_file(cfg_path)
            self.notify(
                "Settings reset to defaults. Restart TUI to see changes.",
                title="Settings",
                severity="warning"
            )
        except Exception as e:
            self.notify(f"Failed to reset: {e}", title="Error", severity="error")


def run_tui():
    """Entry point to launch the TUI."""
    app = KursorinTUI()
    app.run()


if __name__ == "__main__":
    run_tui()
