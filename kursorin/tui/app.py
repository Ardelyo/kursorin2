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

            # Collect all switch and input values
            switch_map = {
                "sw-head_enabled": ("tracking", "head_enabled"),
                "sw-invert_x": ("tracking", "invert_x"),
                "sw-invert_y": ("tracking", "invert_y"),
                "sw-eye_enabled": ("tracking", "eye_enabled"),
                "sw-hand_enabled": ("tracking", "hand_enabled"),
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
                "sw-click_sound": ("ui", "click_sound"),
                "sw-high_contrast": ("ui", "high_contrast"),
                "sw-large_ui": ("ui", "large_ui"),
                "sw-notifs": ("ui", "show_notifications"),
            }

            for widget_id, (section, key) in switch_map.items():
                try:
                    sw = self.query_one(f"#{widget_id}", Switch)
                    section_obj = getattr(cfg, section)
                    setattr(section_obj, key, sw.value)
                except Exception:
                    pass

            # Save
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
