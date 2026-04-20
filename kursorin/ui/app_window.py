"""
Main Application Window — KURSORIN
"""

import customtkinter as ctk
from PIL import Image, ImageTk
import cv2
import threading
import time
from typing import Optional

from loguru import logger
from kursorin.config import KursorinConfig
from kursorin.core.kursorin_engine import KursorinEngine, FrameResult
from kursorin.ui.theme import PALETTE, TYPO, SPACING, apply_theme
from kursorin.ui.overlay import Overlay
from kursorin.ui.calibration_window import CalibrationWindow
from kursorin.ui.settings_panel import SettingsPanel
from kursorin.i18n import t
from kursorin import __version__


class AppWindow:
    """Main KURSORIN GUI application window."""

    def __init__(self, engine: KursorinEngine, config: KursorinConfig):
        self.engine = engine
        self.config = config
        self.overlay = Overlay(config)

        apply_theme()

        self.root = ctk.CTk()
        self.root.title("KURSORIN")
        self.root.geometry("1020x680")
        self.root.minsize(800, 520)
        self.root.configure(fg_color=PALETTE.bg_deepest)

        try:
            self.root.iconbitmap("kursorin/assets/icons/kursorin.ico")
        except Exception:
            pass

        self._current_view = "home"
        self._photo_image = None
        self._video_after_id = None

        self._build_sidebar()
        self._build_content_area()
        self._build_status_bar()
        self._build_home_view()

        self.engine.on_frame(self._on_frame)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self.root, width=200, corner_radius=0,
            fg_color=PALETTE.bg_deep, border_width=0,
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=72)
        logo_frame.pack(fill="x", padx=SPACING.lg, pady=(SPACING.xl, SPACING.sm))
        logo_frame.pack_propagate(False)

        brand = ctk.CTkLabel(
            logo_frame, text="◉ KURSORIN",
            font=(TYPO.family_display, TYPO.size_h2, TYPO.weight_bold),
            text_color=PALETTE.accent_cyan, anchor="w",
        )
        brand.pack(side="top", anchor="w")

        subtitle = ctk.CTkLabel(
            logo_frame, text=t('app.subtitle'),
            font=(TYPO.family_body, TYPO.size_small),
            text_color=PALETTE.fg_muted, anchor="w",
        )
        subtitle.pack(side="top", anchor="w")

        ctk.CTkFrame(self.sidebar, fg_color=PALETTE.border_subtle, height=1).pack(
            fill="x", padx=SPACING.lg, pady=SPACING.sm,
        )

        self.nav_buttons = {}
        nav_items = [
            ("home", f"🏠  {t('nav.home')}"),
            ("settings", f"⚙  {t('nav.settings')}"),
        ]

        for key, label in nav_items:
            btn = ctk.CTkButton(
                self.sidebar, text=label,
                font=(TYPO.family_body, TYPO.size_body),
                fg_color="transparent", hover_color=PALETTE.bg_elevated,
                text_color=PALETTE.fg_secondary, anchor="w",
                height=38, corner_radius=SPACING.radius_md,
                command=lambda k=key: self._switch_view(k),
            )
            btn.pack(fill="x", padx=SPACING.sm, pady=2)
            self.nav_buttons[key] = btn

        self._highlight_nav("home")

        bottom = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", padx=SPACING.lg, pady=SPACING.lg)

        self.btn_toggle = ctk.CTkButton(
            bottom, text=f"▶  {t('dashboard.start_tracking')}",
            font=(TYPO.family_body, TYPO.size_body, TYPO.weight_bold),
            fg_color=PALETTE.accent_cyan, hover_color=PALETTE.accent_cyan_hover,
            text_color=PALETTE.fg_inverse, corner_radius=SPACING.radius_md,
            height=40, command=self._toggle_tracking,
        )
        self.btn_toggle.pack(fill="x", pady=(0, SPACING.sm))

        self.btn_calibrate = ctk.CTkButton(
            bottom, text=f"🎯  {t('dashboard.calibrate')}",
            font=(TYPO.family_body, TYPO.size_body),
            fg_color=PALETTE.bg_elevated, hover_color=PALETTE.border_default,
            text_color=PALETTE.fg_secondary, corner_radius=SPACING.radius_md,
            height=36, command=self._start_calibration,
        )
        self.btn_calibrate.pack(fill="x")

        ctk.CTkFrame(bottom, fg_color=PALETTE.border_subtle, height=1).pack(
            fill="x", pady=SPACING.md,
        )

        scenario_label = ctk.CTkLabel(
            bottom, text=t('dashboard.scenario'), font=(TYPO.family_body, TYPO.size_small),
            text_color=PALETTE.fg_muted, anchor="w",
        )
        scenario_label.pack(fill="x")

        self.scenario_var = ctk.StringVar(value="Default")
        self.scenario_menu = ctk.CTkSegmentedButton(
            bottom, values=["Default", "Hands-Free", "No Head"],
            variable=self.scenario_var, font=(TYPO.family_body, TYPO.size_tiny),
            selected_color=PALETTE.accent_cyan, selected_hover_color=PALETTE.accent_cyan_hover,
            unselected_color=PALETTE.bg_input, unselected_hover_color=PALETTE.bg_elevated,
            text_color=PALETTE.fg_inverse, text_color_disabled=PALETTE.fg_muted,
            corner_radius=SPACING.radius_sm, height=28,
            command=self._on_scenario_change,
        )
        self.scenario_menu.pack(fill="x", pady=(SPACING.xs, 0))

    def _highlight_nav(self, active_key: str):
        for key, btn in self.nav_buttons.items():
            if key == active_key:
                btn.configure(fg_color=PALETTE.bg_elevated, text_color=PALETTE.accent_cyan)
            else:
                btn.configure(fg_color="transparent", text_color=PALETTE.fg_secondary)

    def _build_content_area(self):
        self.content = ctk.CTkFrame(self.root, fg_color=PALETTE.bg_deepest, corner_radius=0)
        self.content.pack(side="left", fill="both", expand=True)

        self.view_container = ctk.CTkFrame(self.content, fg_color="transparent")
        self.view_container.pack(fill="both", expand=True)

    def _build_home_view(self):
        self.home_frame = ctk.CTkFrame(self.view_container, fg_color="transparent")

        header = ctk.CTkFrame(self.home_frame, fg_color="transparent", height=50)
        header.pack(fill="x", padx=SPACING.xl, pady=(SPACING.lg, SPACING.sm))
        header.pack_propagate(False)

        title = ctk.CTkLabel(
            header, text=t('nav.home'),
            font=(TYPO.family_display, TYPO.size_h1, TYPO.weight_bold),
            text_color=PALETTE.fg_primary, anchor="w",
        )
        title.pack(side="left")

        self.video_frame = ctk.CTkFrame(
            self.home_frame, fg_color=PALETTE.bg_surface,
            corner_radius=SPACING.radius_lg, border_width=1, border_color=PALETTE.border_subtle,
        )
        self.video_frame.pack(fill="both", expand=True, padx=SPACING.xl, pady=(0, SPACING.md))

        self.video_placeholder = ctk.CTkLabel(
            self.video_frame,
            text=f"◉\n\n{t('dashboard.camera_preview')}",
            font=(TYPO.family_body, TYPO.size_body),
            text_color=PALETTE.fg_muted, justify="center",
        )
        self.video_placeholder.place(relx=0.5, rely=0.5, anchor="center")

        self.video_label = ctk.CTkLabel(self.video_frame, text="", fg_color="transparent")

        self.metrics_frame = ctk.CTkFrame(
            self.home_frame, fg_color=PALETTE.bg_surface,
            corner_radius=SPACING.radius_lg, border_width=1, border_color=PALETTE.border_subtle,
            height=70,
        )
        self.metrics_frame.pack(fill="x", padx=SPACING.xl, pady=(0, SPACING.lg))
        self.metrics_frame.pack_propagate(False)

        self.metric_labels = {}
        metrics = [
            ("fps", t('metric.fps'), "0.0"),
            ("latency", t('metric.latency'), "0 ms"),
            ("state", t('metric.state'), t('metric.idle')),
            ("frames", t('metric.frames'), "0"),
        ]

        for i, (key, label, default) in enumerate(metrics):
            card = ctk.CTkFrame(self.metrics_frame, fg_color="transparent")
            card.pack(side="left", fill="both", expand=True, padx=SPACING.lg, pady=SPACING.sm)

            name_lbl = ctk.CTkLabel(
                card, text=label, font=(TYPO.family_body, TYPO.size_tiny),
                text_color=PALETTE.fg_muted, anchor="w",
            )
            name_lbl.pack(anchor="w")

            val_lbl = ctk.CTkLabel(
                card, text=default, font=(TYPO.family_mono, TYPO.size_h3, TYPO.weight_bold),
                text_color=PALETTE.accent_cyan, anchor="w",
            )
            val_lbl.pack(anchor="w")
            self.metric_labels[key] = val_lbl

            if i < len(metrics) - 1:
                sep = ctk.CTkFrame(self.metrics_frame, fg_color=PALETTE.border_subtle, width=1)
                sep.pack(side="left", fill="y", pady=SPACING.md)

        self.home_frame.pack(fill="both", expand=True)

    def _build_settings_view(self):
        if hasattr(self, 'settings_frame'):
            return
        self.settings_frame = SettingsPanel(
            self.view_container, self.config, on_save=self._on_settings_saved,
        )

    def _build_status_bar(self):
        self.status_bar = ctk.CTkFrame(
            self.root, height=28, fg_color=PALETTE.bg_deep, corner_radius=0,
        )
        self.status_bar.pack(side="bottom", fill="x")
        self.status_bar.pack_propagate(False)

        self.lbl_status = ctk.CTkLabel(
            self.status_bar, text=f"  {t('status.ready')}",
            font=(TYPO.family_body, TYPO.size_tiny),
            text_color=PALETTE.fg_muted, anchor="w",
        )
        self.lbl_status.pack(side="left", padx=SPACING.sm)

        ver_label = ctk.CTkLabel(
            self.status_bar, text=f"v{__version__}  ",
            font=(TYPO.family_mono, TYPO.size_tiny),
            text_color=PALETTE.fg_muted, anchor="e",
        )
        ver_label.pack(side="right", padx=SPACING.sm)

        # Admin privilege check (Windows specific)
        if self.engine.is_windows and not self.engine.is_admin:
            self.admin_warning = ctk.CTkLabel(
                self.status_bar, text=f"⚠ {t('gui.limited_control')}",
                font=(TYPO.family_body, TYPO.size_tiny, TYPO.weight_bold),
                text_color=PALETTE.accent_amber, cursor="hand2"
            )
            self.admin_warning.pack(side="right", padx=SPACING.md)
            
            # Simple tooltip-like behavior (could be improved with a real tooltip library)
            from tkinter import messagebox
            def show_admin_info(event):
                messagebox.showinfo(t('gui.admin_warning'), t('gui.admin_tooltip'))
            
            self.admin_warning.bind("<Button-1>", show_admin_info)

    def _switch_view(self, view_name: str):
        self._current_view = view_name
        self._highlight_nav(view_name)
        for child in self.view_container.winfo_children():
            child.pack_forget()

        if view_name == "home":
            self.home_frame.pack(fill="both", expand=True)
        elif view_name == "settings":
            self._build_settings_view()
            self.settings_frame.pack(fill="both", expand=True)

    def _toggle_tracking(self):
        if self.engine.is_running:
            self.engine.stop()
            self.btn_toggle.configure(
                text=f"▶  {t('dashboard.start_tracking')}",
                fg_color=PALETTE.accent_cyan, hover_color=PALETTE.accent_cyan_hover,
            )
            self.lbl_status.configure(text=f"  {t('dashboard.stopped')}")
            self.video_label.pack_forget()
            self.video_placeholder.place(relx=0.5, rely=0.5, anchor="center")
            for key, lbl in self.metric_labels.items():
                if key == "state":
                    lbl.configure(text=t('metric.idle'), text_color=PALETTE.fg_muted)
                elif key == "latency":
                    lbl.configure(text="0 ms")
                elif key == "fps":
                    lbl.configure(text="0.0")
                else:
                    lbl.configure(text="0")
        else:
            try:
                self.engine.start()
                self.btn_toggle.configure(
                    text=f"⏹  {t('dashboard.stop_tracking')}",
                    fg_color=PALETTE.accent_red, hover_color="#dc2626",
                )
                self.lbl_status.configure(text=f"  ● {t('dashboard.tracking_active')}")
                self.video_placeholder.place_forget()
                self.video_label.pack(fill="both", expand=True, padx=2, pady=2)
                self._update_metrics()
            except Exception as e:
                self.lbl_status.configure(text=f"  ✖ {t('doctor.issues_found')}: {str(e)[:50]}")

    def _start_calibration(self):
        if not self.engine.is_running:
            self.lbl_status.configure(text=f"  {t('calib.instruction')}")
            return
        self.engine.start_calibration()
        CalibrationWindow(self.root, self.engine, self._on_calibration_complete)

    def _on_calibration_complete(self):
        self.engine.stop_calibration()
        self.engine.save_calibration()
        self.lbl_status.configure(text=f"  ✓ {t('calib.complete')}")

    def _on_scenario_change(self, scenario: str):
        if scenario == "Default":
            self.config.tracking.head_enabled = True
            self.config.tracking.eye_enabled = True
            self.config.tracking.hand_enabled = True
            self.config.click.pinch_click_enabled = True
        elif scenario == "Hands-Free":
            self.config.tracking.head_enabled = True
            self.config.tracking.eye_enabled = True
            self.config.tracking.hand_enabled = False
            self.config.click.pinch_click_enabled = False
        elif scenario == "No Head":
            self.config.tracking.head_enabled = False
            self.config.tracking.eye_enabled = True
            self.config.tracking.hand_enabled = True
            self.config.click.pinch_click_enabled = True

        self.lbl_status.configure(text=f"  {t('dashboard.scenario')}: {scenario}")
        logger.info(f"Switched to scenario: {scenario}")

    def _on_settings_saved(self):
        self.lbl_status.configure(text=f"  ✓ {t('config.set_ok')}")

    def _on_frame(self, result: FrameResult):
        if result.frame is not None and self._current_view == "home":
            vis_frame = self.overlay.draw(result.frame, result)
            rgb = cv2.cvtColor(vis_frame, cv2.COLOR_BGR2RGB)
            try:
                vw = self.video_frame.winfo_width() - 4
                vh = self.video_frame.winfo_height() - 4
                if vw > 10 and vh > 10:
                    h, w = rgb.shape[:2]
                    scale = min(vw / w, vh / h)
                    new_w, new_h = int(w * scale), int(h * scale)
                    rgb = cv2.resize(rgb, (new_w, new_h))
            except Exception:
                pass
            from PIL import Image
            img = Image.fromarray(rgb)
            self.root.after(0, self._update_video, img)

    def _update_video(self, img):
        try:
            from PIL import ImageTk
            photo = ImageTk.PhotoImage(image=img)
            self.video_label.configure(image=photo, text="")
            self._photo_image = photo
        except Exception:
            pass

    def _update_metrics(self):
        if not self.engine.is_running:
            return
        try:
            self.metric_labels["fps"].configure(text=f"{self.engine.fps:.1f}")
            self.metric_labels["latency"].configure(text=f"{self.engine.latency_ms:.0f} ms")
            self.metric_labels["frames"].configure(text=f"{self.engine._frame_count}")
            self.metric_labels["state"].configure(
                text=self.engine.state.name,
                text_color=PALETTE.accent_cyan if self.engine.state.name == "TRACKING" else PALETTE.accent_amber,
            )
        except Exception:
            pass
        self.root.after(500, self._update_metrics)

    def _on_close(self):
        if self.engine.is_running:
            self.engine.stop()
        self.root.destroy()

    def run(self):
        self.root.mainloop()

