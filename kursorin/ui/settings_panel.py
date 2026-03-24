"""
KURSORIN Settings Panel

Organized settings interface with tabs for Tracking, Click Methods,
Camera, Performance, and Appearance.
"""

import customtkinter as ctk
from typing import Optional, Callable

from kursorin.config import KursorinConfig
from kursorin.ui.theme import PALETTE, TYPO, SPACING


class SettingsPanel(ctk.CTkFrame):
    """Tabbed settings panel for KURSORIN configuration."""

    def __init__(self, parent, config: KursorinConfig, on_save: Optional[Callable] = None):
        super().__init__(
            parent,
            fg_color=PALETTE.bg_deep,
            corner_radius=0,
        )
        self.config = config
        self.on_save = on_save
        self._vars = {}

        self._build_ui()

    def _build_ui(self):
        # Header
        header = ctk.CTkLabel(
            self,
            text="⚙  Settings",
            font=(TYPO.family_display, TYPO.size_h2, TYPO.weight_bold),
            text_color=PALETTE.fg_primary,
            anchor="w",
        )
        header.pack(fill="x", padx=SPACING.xl, pady=(SPACING.xl, SPACING.md))

        # Tabview
        self.tabview = ctk.CTkTabview(
            self,
            fg_color=PALETTE.bg_surface,
            segmented_button_fg_color=PALETTE.bg_elevated,
            segmented_button_selected_color=PALETTE.accent_cyan,
            segmented_button_selected_hover_color=PALETTE.accent_cyan_hover,
            segmented_button_unselected_color=PALETTE.bg_elevated,
            segmented_button_unselected_hover_color=PALETTE.bg_input,
            text_color=PALETTE.fg_primary,
            corner_radius=SPACING.radius_lg,
        )
        self.tabview.pack(fill="both", expand=True, padx=SPACING.lg, pady=(0, SPACING.lg))

        # Create tabs
        self._build_tracking_tab()
        self._build_click_tab()
        self._build_camera_tab()
        self._build_performance_tab()
        self._build_appearance_tab()

        # Save button
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=SPACING.xl, pady=(0, SPACING.xl))

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Save Settings",
            font=(TYPO.family_body, TYPO.size_body, TYPO.weight_bold),
            fg_color=PALETTE.accent_cyan,
            hover_color=PALETTE.accent_cyan_hover,
            text_color=PALETTE.fg_inverse,
            corner_radius=SPACING.radius_md,
            height=36,
            command=self._save,
        )
        save_btn.pack(side="right")

        reset_btn = ctk.CTkButton(
            btn_frame,
            text="Reset Defaults",
            font=(TYPO.family_body, TYPO.size_body),
            fg_color=PALETTE.bg_elevated,
            hover_color=PALETTE.border_default,
            text_color=PALETTE.fg_secondary,
            corner_radius=SPACING.radius_md,
            height=36,
            command=self._reset,
        )
        reset_btn.pack(side="right", padx=(0, SPACING.sm))

    # ── Tab builders ──────────────────────────────────────────────────────

    def _build_tracking_tab(self):
        tab = self.tabview.add("Tracking")
        tab.configure(fg_color=PALETTE.bg_surface)

        # Toggle switches
        self._add_switch(tab, "Head Tracking", "tracking.head_enabled", self.config.tracking.head_enabled)
        self._add_switch(tab, "Eye Tracking", "tracking.eye_enabled", self.config.tracking.eye_enabled)
        self._add_switch(tab, "Hand Tracking", "tracking.hand_enabled", self.config.tracking.hand_enabled)

        self._add_separator(tab)

        # Sliders
        self._add_slider(tab, "Head Sensitivity X", "tracking.head_sensitivity_x",
                         self.config.tracking.head_sensitivity_x, 0.5, 5.0)
        self._add_slider(tab, "Head Sensitivity Y", "tracking.head_sensitivity_y",
                         self.config.tracking.head_sensitivity_y, 0.5, 5.0)
        self._add_slider(tab, "Smoothing", "tracking.head_smoothing",
                         self.config.tracking.head_smoothing, 0.0, 0.99)

        self._add_separator(tab)

        self._add_switch(tab, "Invert X", "tracking.invert_x", self.config.tracking.invert_x)
        self._add_switch(tab, "Invert Y", "tracking.invert_y", self.config.tracking.invert_y)

    def _build_click_tab(self):
        tab = self.tabview.add("Click")
        tab.configure(fg_color=PALETTE.bg_surface)

        self._add_switch(tab, "Blink Click", "click.blink_click_enabled", self.config.click.blink_click_enabled)
        self._add_switch(tab, "Dwell Click", "click.dwell_click_enabled", self.config.click.dwell_click_enabled)
        self._add_switch(tab, "Pinch Click", "click.pinch_click_enabled", self.config.click.pinch_click_enabled)
        self._add_switch(tab, "Mouth Click", "click.mouth_click_enabled", self.config.click.mouth_click_enabled)

        self._add_separator(tab)

        self._add_slider(tab, "Dwell Time (ms)", "click.dwell_time_ms",
                         self.config.click.dwell_time_ms, 300, 5000)
        self._add_slider(tab, "Dwell Radius (px)", "click.dwell_radius_px",
                         self.config.click.dwell_radius_px, 10, 100)

    def _build_camera_tab(self):
        tab = self.tabview.add("Camera")
        tab.configure(fg_color=PALETTE.bg_surface)

        self._add_slider(tab, "Camera Index", "camera.camera_index",
                         self.config.camera.camera_index, 0, 5)
        self._add_slider(tab, "Target FPS", "camera.target_fps",
                         self.config.camera.target_fps, 15, 120)

        self._add_separator(tab)

        self._add_switch(tab, "Mirror Mode", "camera.flip_horizontal", self.config.camera.flip_horizontal)
        self._add_switch(tab, "Auto Exposure", "camera.auto_exposure", self.config.camera.auto_exposure)
        self._add_switch(tab, "Auto Focus", "camera.auto_focus", self.config.camera.auto_focus)

    def _build_performance_tab(self):
        tab = self.tabview.add("Performance")
        tab.configure(fg_color=PALETTE.bg_surface)

        self._add_slider(tab, "Max FPS", "performance.max_fps",
                         self.config.performance.max_fps, 15, 120)
        self._add_switch(tab, "Multi-Threading", "performance.use_threading",
                         self.config.performance.use_threading)
        self._add_switch(tab, "GPU Acceleration", "performance.use_gpu",
                         self.config.performance.use_gpu)
        self._add_switch(tab, "Power Save Mode", "performance.power_save_mode",
                         self.config.performance.power_save_mode)

    def _build_appearance_tab(self):
        tab = self.tabview.add("Appearance")
        tab.configure(fg_color=PALETTE.bg_surface)

        self._add_switch(tab, "Show Video Preview", "ui.show_preview", self.config.ui.show_preview)
        self._add_switch(tab, "Show Overlay", "ui.show_overlay", self.config.ui.show_overlay)
        self._add_switch(tab, "Cursor Trail", "ui.cursor_trail", self.config.ui.cursor_trail)
        self._add_switch(tab, "Audio Feedback", "ui.audio_feedback", self.config.ui.audio_feedback)
        self._add_switch(tab, "Click Sound", "ui.click_sound", self.config.ui.click_sound)

        self._add_separator(tab)

        self._add_switch(tab, "High Contrast", "ui.high_contrast", self.config.ui.high_contrast)
        self._add_switch(tab, "Large UI", "ui.large_ui", self.config.ui.large_ui)
        self._add_switch(tab, "Show Notifications", "ui.show_notifications", self.config.ui.show_notifications)

    # ── Widget helpers ────────────────────────────────────────────────────

    def _add_switch(self, parent, label: str, key: str, initial: bool):
        row = ctk.CTkFrame(parent, fg_color="transparent", height=40)
        row.pack(fill="x", padx=SPACING.lg, pady=SPACING.xs)
        row.pack_propagate(False)

        lbl = ctk.CTkLabel(
            row, text=label,
            font=(TYPO.family_body, TYPO.size_body),
            text_color=PALETTE.fg_primary, anchor="w",
        )
        lbl.pack(side="left", fill="x", expand=True)

        var = ctk.BooleanVar(value=initial)
        sw = ctk.CTkSwitch(
            row, text="", variable=var,
            onvalue=True, offvalue=False,
            progress_color=PALETTE.accent_cyan,
            button_color=PALETTE.fg_primary,
            button_hover_color=PALETTE.accent_cyan_hover,
            fg_color=PALETTE.bg_input,
            width=44, height=22,
        )
        sw.pack(side="right")
        self._vars[key] = var

    def _add_slider(self, parent, label: str, key: str, initial: float,
                    from_: float, to_: float):
        row = ctk.CTkFrame(parent, fg_color="transparent", height=50)
        row.pack(fill="x", padx=SPACING.lg, pady=SPACING.xs)
        row.pack_propagate(False)

        top_row = ctk.CTkFrame(row, fg_color="transparent")
        top_row.pack(fill="x")

        lbl = ctk.CTkLabel(
            top_row, text=label,
            font=(TYPO.family_body, TYPO.size_body),
            text_color=PALETTE.fg_primary, anchor="w",
        )
        lbl.pack(side="left")

        val_lbl = ctk.CTkLabel(
            top_row, text=f"{initial:.1f}" if isinstance(initial, float) else str(initial),
            font=(TYPO.family_mono, TYPO.size_small),
            text_color=PALETTE.accent_cyan, anchor="e", width=50,
        )
        val_lbl.pack(side="right")

        var = ctk.DoubleVar(value=float(initial))

        def on_change(val):
            display = f"{float(val):.1f}" if isinstance(initial, float) else str(int(float(val)))
            val_lbl.configure(text=display)

        sl = ctk.CTkSlider(
            row, from_=from_, to=to_, variable=var,
            command=on_change,
            progress_color=PALETTE.accent_cyan,
            button_color=PALETTE.fg_primary,
            button_hover_color=PALETTE.accent_cyan_hover,
            fg_color=PALETTE.bg_input,
            height=16,
        )
        sl.pack(fill="x", pady=(SPACING.xs, 0))
        self._vars[key] = var

    def _add_separator(self, parent):
        sep = ctk.CTkFrame(parent, fg_color=PALETTE.border_subtle, height=1)
        sep.pack(fill="x", padx=SPACING.lg, pady=SPACING.md)

    # ── Actions ───────────────────────────────────────────────────────────

    def _save(self):
        """Apply vars back to config and notify."""
        for key, var in self._vars.items():
            parts = key.split(".")
            obj = self.config
            for p in parts[:-1]:
                obj = getattr(obj, p)

            value = var.get()
            attr = parts[-1]
            current = getattr(obj, attr)

            # Type coerce
            if isinstance(current, int) and not isinstance(current, bool):
                value = int(value)
            elif isinstance(current, float):
                value = float(value)

            setattr(obj, attr, value)

        # Persist
        from pathlib import Path
        cfg_path = Path.home() / ".kursorin" / "config.yaml"
        self.config.to_file(cfg_path)

        if self.on_save:
            self.on_save()

    def _reset(self):
        """Reset to default config."""
        default = KursorinConfig()
        # Re-read defaults back into vars
        for key, var in self._vars.items():
            parts = key.split(".")
            obj = default
            for p in parts[:-1]:
                obj = getattr(obj, p)
            var.set(getattr(obj, parts[-1]))

        self._save()
