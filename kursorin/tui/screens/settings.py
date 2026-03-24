"""
KURSORIN TUI — Settings Screen

Interactive configuration panel with toggles, sliders, and tabs.
"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from textual.widgets import (
    Static, Button, Switch, Input, Label, Rule,
    TabbedContent, TabPane,
)

from kursorin.config import load_config, KursorinConfig
from pathlib import Path


class SettingRow(Horizontal):
    """A single setting with label and control."""

    DEFAULT_CSS = """
    SettingRow {
        height: 3;
        padding: 0 1;
        background: transparent;
    }
    SettingRow:hover {
        background: #0d1a2e;
    }
    .setting-label {
        width: 1fr;
        content-align: left middle;
        color: #e2e8f0;
    }
    """

    def __init__(self, label: str, **kwargs):
        super().__init__(**kwargs)
        self._label = label

    def compose(self) -> ComposeResult:
        yield Static(self._label, classes="setting-label")


class ToggleRow(SettingRow):
    """A setting row with a toggle switch."""

    def __init__(self, label: str, value: bool = False, setting_key: str = "", **kwargs):
        super().__init__(label=label, **kwargs)
        self._value = value
        self.setting_key = setting_key

    def compose(self) -> ComposeResult:
        yield Static(self._label, classes="setting-label")
        yield Switch(value=self._value, id=f"sw-{self.setting_key}")


class InputRow(SettingRow):
    """A setting row with a text input."""

    def __init__(self, label: str, value: str = "", setting_key: str = "", **kwargs):
        super().__init__(label=label, **kwargs)
        self._value = value
        self.setting_key = setting_key

    def compose(self) -> ComposeResult:
        yield Static(self._label, classes="setting-label")
        yield Input(value=self._value, id=f"inp-{self.setting_key}")


class SettingsScreen(Container):
    """Interactive settings view."""

    DEFAULT_CSS = """
    SettingsScreen {
        height: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static(
            "[bold #3b82f6]⚙  Settings[/]  [#64748b]Configure KURSORIN[/]",
            classes="section-title"
        )
        yield Rule()

        cfg = load_config()

        with TabbedContent():
            # ── Tracking Tab ──
            with TabPane("Tracking", id="tab-tracking"):
                with VerticalScroll():
                    yield Static("[bold #3b82f6]Head Tracking[/]", classes="settings-group-title")
                    yield ToggleRow("Enable Head Tracking", cfg.tracking.head_enabled, "head_enabled")
                    yield InputRow("Sensitivity X", str(cfg.tracking.head_sensitivity_x), "head_sens_x")
                    yield InputRow("Sensitivity Y", str(cfg.tracking.head_sensitivity_y), "head_sens_y")
                    yield InputRow("Smoothing", str(cfg.tracking.head_smoothing), "head_smooth")
                    yield ToggleRow("Invert X", cfg.tracking.invert_x, "invert_x")
                    yield ToggleRow("Invert Y", cfg.tracking.invert_y, "invert_y")

                    yield Rule()
                    yield Static("[bold #3b82f6]Eye Tracking[/]", classes="settings-group-title")
                    yield ToggleRow("Enable Eye Tracking", cfg.tracking.eye_enabled, "eye_enabled")
                    yield InputRow("Blink Threshold", str(cfg.tracking.eye_blink_threshold), "blink_thresh")

                    yield Rule()
                    yield Static("[bold #3b82f6]Hand Tracking[/]", classes="settings-group-title")
                    yield ToggleRow("Enable Hand Tracking", cfg.tracking.hand_enabled, "hand_enabled")
                    yield InputRow("Pinch Threshold", str(cfg.tracking.pinch_threshold), "pinch_thresh")

            # ── Click Tab ──
            with TabPane("Click", id="tab-click"):
                with VerticalScroll():
                    yield ToggleRow("Blink Click", cfg.click.blink_click_enabled, "blink_click")
                    yield ToggleRow("Dwell Click", cfg.click.dwell_click_enabled, "dwell_click")
                    yield InputRow("Dwell Time (ms)", str(cfg.click.dwell_time_ms), "dwell_time")
                    yield InputRow("Dwell Radius (px)", str(cfg.click.dwell_radius_px), "dwell_radius")
                    yield ToggleRow("Pinch Click", cfg.click.pinch_click_enabled, "pinch_click")
                    yield ToggleRow("Mouth Click", cfg.click.mouth_click_enabled, "mouth_click")

            # ── Camera Tab ──
            with TabPane("Camera", id="tab-camera"):
                with VerticalScroll():
                    yield InputRow("Camera Index", str(cfg.camera.camera_index), "cam_index")
                    yield InputRow("Width", str(cfg.camera.camera_width), "cam_width")
                    yield InputRow("Height", str(cfg.camera.camera_height), "cam_height")
                    yield InputRow("Target FPS", str(cfg.camera.target_fps), "cam_fps")
                    yield ToggleRow("Mirror Mode", cfg.camera.flip_horizontal, "cam_mirror")
                    yield ToggleRow("Auto Exposure", cfg.camera.auto_exposure, "cam_ae")
                    yield ToggleRow("Auto Focus", cfg.camera.auto_focus, "cam_af")

            # ── Performance Tab ──
            with TabPane("Performance", id="tab-perf"):
                with VerticalScroll():
                    yield InputRow("Max FPS", str(cfg.performance.max_fps), "max_fps")
                    yield ToggleRow("Multi-Threading", cfg.performance.use_threading, "threading")
                    yield InputRow("Thread Count", str(cfg.performance.thread_count), "thread_count")
                    yield ToggleRow("GPU Acceleration", cfg.performance.use_gpu, "gpu")
                    yield ToggleRow("Power Save Mode", cfg.performance.power_save_mode, "power_save")

            # ── Appearance Tab ──
            with TabPane("Appearance", id="tab-appearance"):
                with VerticalScroll():
                    yield ToggleRow("Show Video Preview", cfg.ui.show_preview, "show_preview")
                    yield ToggleRow("Show Overlay", cfg.ui.show_overlay, "show_overlay")
                    yield ToggleRow("Cursor Trail", cfg.ui.cursor_trail, "cursor_trail")
                    yield ToggleRow("Audio Feedback", cfg.ui.audio_feedback, "audio_fb")
                    yield ToggleRow("Click Sound", cfg.ui.click_sound, "click_sound")
                    yield ToggleRow("High Contrast", cfg.ui.high_contrast, "high_contrast")
                    yield ToggleRow("Large UI", cfg.ui.large_ui, "large_ui")
                    yield ToggleRow("Notifications", cfg.ui.show_notifications, "notifs")

        yield Static("")
        with Horizontal(id="settings-actions"):
            yield Button("💾  Save Settings", id="btn-save-settings", classes="action-btn -primary")
            yield Button("↺  Reset Defaults", id="btn-reset-settings", classes="action-btn -danger")
