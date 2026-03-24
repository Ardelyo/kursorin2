"""
KURSORIN TUI — Main Application

A minimalist blue-themed command-center TUI powered by Textual.
Launch with: kursorin (no arguments)
"""

from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, Center, Middle
from textual.widgets import Static, Button, Footer, Input
from textual.widget import Widget

from kursorin import __version__
from kursorin.tui.screens.dashboard import DashboardScreen
from kursorin.tui.screens.settings import SettingsScreen
from kursorin.tui.screens.doctor import DoctorScreen
from kursorin.tui.screens.update import UpdateScreen
from kursorin.tui.widgets.command_input import CommandInput
from kursorin.config import load_config, KursorinConfig


CSS_PATH = Path(__file__).parent / "app.tcss"

# ── ASCII Logo ────────────────────────────────────────────────────────────────

LOGO_ART = """\
[bold #3b82f6]██╗  ██╗[#60a5fa]██╗   ██╗[#3b82f6]██████╗ [#60a5fa]███████╗[#3b82f6] ██████╗ [#60a5fa]██████╗ [#3b82f6]██╗[#60a5fa]███╗   ██╗[/]
[bold #3b82f6]██║ ██╔╝[#60a5fa]██║   ██║[#3b82f6]██╔══██╗[#60a5fa]██╔════╝[#3b82f6]██╔═══██╗[#60a5fa]██╔══██╗[#3b82f6]██║[#60a5fa]████╗  ██║[/]
[bold #3b82f6]█████╔╝ [#60a5fa]██║   ██║[#3b82f6]██████╔╝[#60a5fa]███████╗[#3b82f6]██║   ██║[#60a5fa]██████╔╝[#3b82f6]██║[#60a5fa]██╔██╗ ██║[/]
[bold #3b82f6]██╔═██╗ [#60a5fa]██║   ██║[#3b82f6]██╔══██╗[#60a5fa]╚════██║[#3b82f6]██║   ██║[#60a5fa]██╔══██╗[#3b82f6]██║[#60a5fa]██║╚██╗██║[/]
[bold #3b82f6]██║  ██╗[#60a5fa]╚██████╔╝[#3b82f6]██║  ██║[#60a5fa]███████║[#3b82f6]╚██████╔╝[#60a5fa]██║  ██║[#3b82f6]██║[#60a5fa]██║ ╚████║[/]
[bold #3b82f6]╚═╝  ╚═╝[#60a5fa] ╚═════╝ [#3b82f6]╚═╝  ╚═╝[#60a5fa]╚══════╝[#3b82f6] ╚═════╝ [#60a5fa]╚═╝  ╚═╝[#3b82f6]╚═╝[#60a5fa]╚═╝  ╚═══╝[/]"""

SUBTITLE = "[#64748b]Webcam-Based HCI System[/]"


# ── Hint Chips ────────────────────────────────────────────────────────────────

HINT_CHIPS = (
    "[#3b82f6]start[/][#64748b] tracking  ·  [/]"
    "[#3b82f6]settings[/][#64748b]  ·  [/]"
    "[#3b82f6]doctor[/][#64748b]  ·  [/]"
    "[#3b82f6]update[/][#64748b]  ·  [/]"
    "[#3b82f6]gui[/][#64748b]  ·  [/]"
    "[#3b82f6]calibrate[/][#64748b]  ·  [/]"
    "[#3b82f6]lang[/][#64748b]  ·  [/]"
    "[#3b82f6]quit[/]"
)


class KursorinTUI(App):
    """KURSORIN Interactive Terminal Interface — Command Center."""

    CSS_PATH = "app.tcss"

    TITLE = "KURSORIN"
    SUB_TITLE = "Webcam-Based HCI System"

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("d", "go_screen('dashboard')", "Dashboard", show=True),
        Binding("s", "go_screen('settings')", "Settings", show=True),
        Binding("x", "go_screen('doctor')", "Doctor", show=True),
        Binding("u", "go_screen('update')", "Updates", show=True),
        Binding("escape", "go_home", "Home", show=True),
        Binding("ctrl+p", "command_palette", "Commands", show=True),
    ]

    current_view = "home"

    def compose(self) -> ComposeResult:
        # ── Top header bar ──
        yield Static(
            f"  [bold #3b82f6]⬡ KURSORIN[/]  "
            f"[#1e3a5f]│[/]  "
            f"[#64748b]v{__version__}[/]  "
            f"[#1e3a5f]│[/]  "
            f"[#64748b]Webcam-Based HCI[/]",
            id="header-bar"
        )

        # ── Home screen (centered logo + command bar) ──
        with Container(id="home-screen"):
            with Center():
                with Middle():
                    with Vertical(id="home-content"):
                        yield Static(LOGO_ART, id="logo-art")
                        yield Static(SUBTITLE, id="logo-subtitle")
                        yield Static("", id="spacer-1")
                        yield CommandInput(id="cmd-input")
                        yield Static(HINT_CHIPS, id="hint-chips")

        # ── Screen panels (hidden by default) ──
        with Container(id="screen-panels"):
            # Back bar
            yield Static(
                "[#3b82f6]◀ [bold]ESC[/] back[/]  "
                "[#1e3a5f]│[/]  "
                "[#64748b]Type [bold #3b82f6]home[/bold #3b82f6] or press ESC to return[/]",
                id="back-bar"
            )
            with Container(id="content-area"):
                yield DashboardScreen(id="screen-dashboard")
                yield SettingsScreen(id="screen-settings")
                yield DoctorScreen(id="screen-doctor")
                yield UpdateScreen(id="screen-update")

        # ── Bottom status bar ──
        yield Static(
            f"  [#64748b]~/.kursorin[/]  "
            f"[#1e3a5f]│[/]  "
            f"[#3b82f6]●[/] [#64748b]Ready[/]  "
            f"[#1e3a5f]│[/]  "
            f"[#64748b]v{__version__}[/]",
            id="status-bar"
        )

    def on_mount(self) -> None:
        """Start on home screen — focus the command input."""
        self._show_home()
        self.query_one("#cmd-input", CommandInput).focus()

    # ── View switching ────────────────────────────────────────────────────────

    def _show_home(self) -> None:
        """Show the home/command-center view."""
        self.current_view = "home"
        self.query_one("#home-screen").display = True
        self.query_one("#screen-panels").display = False
        try:
            self.query_one("#cmd-input", CommandInput).focus()
        except Exception:
            pass

    def _show_screen(self, screen_id: str) -> None:
        """Show a specific content screen."""
        self.current_view = screen_id
        self.query_one("#home-screen").display = False
        self.query_one("#screen-panels").display = True

        for sid in ("dashboard", "settings", "doctor", "update"):
            widget = self.query_one(f"#screen-{sid}", Container)
            widget.display = (sid == screen_id)

    # ── Command handling ──────────────────────────────────────────────────────

    def on_command_input_command_submitted(self, event: CommandInput.CommandSubmitted) -> None:
        """Route commands from the command bar."""
        cmd = event.command

        if cmd in ("quit", "q", "exit"):
            self.exit()
        elif cmd in ("home", "back", "h"):
            self._show_home()
        elif cmd in ("dashboard", "dash", "d"):
            self._show_screen("dashboard")
        elif cmd in ("settings", "config", "s"):
            self._show_screen("settings")
        elif cmd in ("doctor", "diag", "x"):
            self._show_screen("doctor")
        elif cmd in ("update", "u"):
            self._show_screen("update")
        elif cmd == "start":
            self._start_tracking()
        elif cmd == "calibrate":
            self._start_calibration()
        elif cmd == "gui":
            self._launch_gui()
        elif cmd == "lang":
            self._toggle_language()
        else:
            self.notify(
                f"Unknown command: [bold]{cmd}[/]\n"
                "Try: start, settings, doctor, update, calibrate, gui, lang, quit",
                title="Command",
                severity="warning"
            )

    # ── Actions (keyboard shortcuts) ──────────────────────────────────────────

    def action_go_screen(self, screen_id: str) -> None:
        self._show_screen(screen_id)

    def action_go_home(self) -> None:
        self._show_home()

    # ── Button handling (from screens) ────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle all button presses from screens."""
        btn_id = event.button.id or ""

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

    # ── Core actions ──────────────────────────────────────────────────────────

    def _toggle_language(self) -> None:
        from kursorin.i18n import get_lang, set_lang, save_lang
        current = get_lang()
        new_lang = "id" if current == "en" else "en"
        set_lang(new_lang)
        save_lang(new_lang)
        self.notify(
            f"Language → {'Bahasa Indonesia' if new_lang == 'id' else 'English'}",
            title="Language",
            severity="information"
        )

    def _start_tracking(self) -> None:
        self.notify(
            "Starting tracking engine...\nUse 'kursorin start' from terminal.",
            title="Tracking",
            severity="information"
        )

    def _start_calibration(self) -> None:
        self.notify(
            "Starting calibration...\nUse 'kursorin calibrate' from terminal.",
            title="Calibration",
            severity="information"
        )

    def _launch_gui(self) -> None:
        self.notify(
            "Launching GUI...\nUse 'kursorin gui' from terminal.",
            title="GUI",
            severity="information"
        )

    def _save_settings(self) -> None:
        try:
            from textual.widgets import Switch, Input
            cfg = load_config()

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

            cfg_path = Path.home() / ".kursorin" / "config.yaml"
            cfg.to_file(cfg_path)

            self.notify(
                "Settings saved!",
                title="Settings",
                severity="information"
            )
        except Exception as e:
            self.notify(f"Failed to save: {e}", title="Error", severity="error")

    def _reset_settings(self) -> None:
        try:
            cfg = KursorinConfig()
            cfg_path = Path.home() / ".kursorin" / "config.yaml"
            cfg.to_file(cfg_path)
            self.notify(
                "Settings reset. Restart TUI to see changes.",
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
