"""
Onboarding Wizard — KURSORIN

Guided first-time setup with step indicators, styled panels,
and camera environment check.
"""

import customtkinter as ctk
from typing import Optional

from loguru import logger
from kursorin.config import KursorinConfig
from kursorin.core.kursorin_engine import KursorinEngine
from kursorin.ui.theme import PALETTE, TYPO, SPACING, apply_theme


class OnboardingWizard:
    """Modal onboarding wizard for first-time users."""

    STEPS = [
        {"key": "welcome", "title": "Welcome"},
        {"key": "camera", "title": "Environment"},
        {"key": "calibration", "title": "Calibration"},
    ]

    def __init__(self, parent, engine: KursorinEngine, config: KursorinConfig):
        self.parent = parent
        self.engine = engine
        self.config = config
        self.needs_calibration = False
        self.current_step = 0

        apply_theme()

        # ── Modal window ──────────────────────────────────────────────────
        self.window = ctk.CTkToplevel(parent)
        self.window.title("KURSORIN Setup")
        self.window.geometry("560x440")
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()
        self.window.configure(fg_color=PALETTE.bg_deepest)

        # Center over parent
        self.window.update_idletasks()
        try:
            x = parent.winfo_x() + (parent.winfo_width() - 560) // 2
            y = parent.winfo_y() + (parent.winfo_height() - 440) // 2
            self.window.geometry(f"+{max(0,x)}+{max(0,y)}")
        except Exception:
            pass

        # ── Step indicator ────────────────────────────────────────────────
        self.indicator_frame = ctk.CTkFrame(
            self.window, fg_color="transparent", height=48,
        )
        self.indicator_frame.pack(fill="x", padx=SPACING.xxl, pady=(SPACING.xl, SPACING.sm))
        self.indicator_frame.pack_propagate(False)

        self.step_dots = []
        self.step_labels = []

        dot_container = ctk.CTkFrame(self.indicator_frame, fg_color="transparent")
        dot_container.place(relx=0.5, rely=0.5, anchor="center")

        for i, step in enumerate(self.STEPS):
            # Connector line (before dot, except first)
            if i > 0:
                line = ctk.CTkFrame(
                    dot_container,
                    fg_color=PALETTE.border_subtle,
                    height=2, width=50,
                )
                line.pack(side="left", pady=(0, 14))

            # Dot + label column
            col = ctk.CTkFrame(dot_container, fg_color="transparent")
            col.pack(side="left")

            dot = ctk.CTkFrame(
                col,
                width=28, height=28,
                corner_radius=14,
                fg_color=PALETTE.bg_elevated,
                border_width=2,
                border_color=PALETTE.border_subtle,
            )
            dot.pack()
            dot.pack_propagate(False)

            num = ctk.CTkLabel(
                dot, text=str(i + 1),
                font=(TYPO.family_mono, TYPO.size_tiny, TYPO.weight_bold),
                text_color=PALETTE.fg_muted,
            )
            num.place(relx=0.5, rely=0.5, anchor="center")

            lbl = ctk.CTkLabel(
                col, text=step["title"],
                font=(TYPO.family_body, TYPO.size_tiny),
                text_color=PALETTE.fg_muted,
            )
            lbl.pack(pady=(2, 0))

            self.step_dots.append((dot, num))
            self.step_labels.append(lbl)

        # ── Content container ─────────────────────────────────────────────
        self.content = ctk.CTkFrame(
            self.window,
            fg_color=PALETTE.bg_surface,
            corner_radius=SPACING.radius_lg,
            border_width=1,
            border_color=PALETTE.border_subtle,
        )
        self.content.pack(fill="both", expand=True, padx=SPACING.xl, pady=(0, SPACING.lg))

        # ── Build pages ───────────────────────────────────────────────────
        self.pages = {}
        self._build_welcome_page()
        self._build_camera_page()
        self._build_calibration_page()

        # Show first step
        self._show_step(0)

    # ── Page builders ─────────────────────────────────────────────────────

    def _build_welcome_page(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        self.pages["welcome"] = page

        # Icon
        icon = ctk.CTkLabel(
            page, text="◉",
            font=(TYPO.family_display, 48),
            text_color=PALETTE.accent_cyan,
        )
        icon.pack(pady=(SPACING.xxl, SPACING.md))

        title = ctk.CTkLabel(
            page, text="Welcome to KURSORIN",
            font=(TYPO.family_display, TYPO.size_h1, TYPO.weight_bold),
            text_color=PALETTE.fg_primary,
        )
        title.pack()

        desc = ctk.CTkLabel(
            page,
            text=(
                "Control your computer hands-free using\n"
                "head movements, hand gestures, and eye tracking.\n\n"
                "This quick setup will configure your environment\n"
                "and calibrate eye tracking for best accuracy."
            ),
            font=(TYPO.family_body, TYPO.size_body),
            text_color=PALETTE.fg_secondary,
            justify="center",
        )
        desc.pack(pady=SPACING.lg)

        btn = ctk.CTkButton(
            page, text="Get Started →",
            font=(TYPO.family_body, TYPO.size_body, TYPO.weight_bold),
            fg_color=PALETTE.accent_cyan,
            hover_color=PALETTE.accent_cyan_hover,
            text_color=PALETTE.fg_inverse,
            corner_radius=SPACING.radius_md,
            height=40, width=180,
            command=lambda: self._show_step(1),
        )
        btn.pack(pady=SPACING.lg)

    def _build_camera_page(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        self.pages["camera"] = page

        icon = ctk.CTkLabel(
            page, text="📷",
            font=(TYPO.family_display, 36),
        )
        icon.pack(pady=(SPACING.xl, SPACING.sm))

        title = ctk.CTkLabel(
            page, text="Environment Check",
            font=(TYPO.family_display, TYPO.size_h2, TYPO.weight_bold),
            text_color=PALETTE.fg_primary,
        )
        title.pack()

        tips = ctk.CTkLabel(
            page,
            text=(
                "For the best experience, please ensure:\n\n"
                "  •  You are in a well-lit room\n"
                "  •  Your webcam can see your face and hands clearly\n"
                "  •  There is minimal background clutter\n\n"
                f"Camera Index: {self.config.camera.camera_index}"
            ),
            font=(TYPO.family_body, TYPO.size_body),
            text_color=PALETTE.fg_secondary,
            justify="left",
        )
        tips.pack(pady=SPACING.md, padx=SPACING.xxl)

        btn_row = ctk.CTkFrame(page, fg_color="transparent")
        btn_row.pack(pady=SPACING.lg)

        ctk.CTkButton(
            btn_row, text="← Back",
            font=(TYPO.family_body, TYPO.size_body),
            fg_color=PALETTE.bg_elevated,
            hover_color=PALETTE.border_default,
            text_color=PALETTE.fg_secondary,
            corner_radius=SPACING.radius_md,
            height=36, width=100,
            command=lambda: self._show_step(0),
        ).pack(side="left", padx=SPACING.sm)

        ctk.CTkButton(
            btn_row, text="Next →",
            font=(TYPO.family_body, TYPO.size_body, TYPO.weight_bold),
            fg_color=PALETTE.accent_cyan,
            hover_color=PALETTE.accent_cyan_hover,
            text_color=PALETTE.fg_inverse,
            corner_radius=SPACING.radius_md,
            height=36, width=100,
            command=lambda: self._show_step(2),
        ).pack(side="left", padx=SPACING.sm)

    def _build_calibration_page(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        self.pages["calibration"] = page

        icon = ctk.CTkLabel(
            page, text="🎯",
            font=(TYPO.family_display, 36),
        )
        icon.pack(pady=(SPACING.xl, SPACING.sm))

        title = ctk.CTkLabel(
            page, text="Eye Calibration",
            font=(TYPO.family_display, TYPO.size_h2, TYPO.weight_bold),
            text_color=PALETTE.fg_primary,
        )
        title.pack()

        desc = ctk.CTkLabel(
            page,
            text=(
                "Calibrating your eye tracking improves accuracy.\n\n"
                "When calibration starts, dots will appear on screen.\n"
                "Look at each dot steadily until it moves.\n"
                "Keep your head relatively still during this process."
            ),
            font=(TYPO.family_body, TYPO.size_body),
            text_color=PALETTE.fg_secondary,
            justify="center",
        )
        desc.pack(pady=SPACING.md)

        btn_row = ctk.CTkFrame(page, fg_color="transparent")
        btn_row.pack(pady=SPACING.lg)

        ctk.CTkButton(
            btn_row, text="← Back",
            font=(TYPO.family_body, TYPO.size_body),
            fg_color=PALETTE.bg_elevated,
            hover_color=PALETTE.border_default,
            text_color=PALETTE.fg_secondary,
            corner_radius=SPACING.radius_md,
            height=36, width=100,
            command=lambda: self._show_step(1),
        ).pack(side="left", padx=SPACING.sm)

        ctk.CTkButton(
            btn_row, text="Skip",
            font=(TYPO.family_body, TYPO.size_body),
            fg_color="transparent",
            hover_color=PALETTE.bg_elevated,
            text_color=PALETTE.fg_muted,
            corner_radius=SPACING.radius_md,
            height=36, width=80,
            command=self._skip,
        ).pack(side="left", padx=SPACING.sm)

        ctk.CTkButton(
            btn_row, text="Start Calibration",
            font=(TYPO.family_body, TYPO.size_body, TYPO.weight_bold),
            fg_color=PALETTE.accent_cyan,
            hover_color=PALETTE.accent_cyan_hover,
            text_color=PALETTE.fg_inverse,
            corner_radius=SPACING.radius_md,
            height=36, width=160,
            command=self._start_calibration,
        ).pack(side="left", padx=SPACING.sm)

    # ── Navigation ────────────────────────────────────────────────────────

    def _show_step(self, index: int):
        self.current_step = index

        # Update step indicator
        for i, (dot, num) in enumerate(self.step_dots):
            if i < index:
                # Completed
                dot.configure(fg_color=PALETTE.accent_cyan, border_color=PALETTE.accent_cyan)
                num.configure(text="✓", text_color=PALETTE.fg_inverse)
                self.step_labels[i].configure(text_color=PALETTE.accent_cyan)
            elif i == index:
                # Active
                dot.configure(fg_color=PALETTE.bg_elevated, border_color=PALETTE.accent_cyan)
                num.configure(text=str(i + 1), text_color=PALETTE.accent_cyan)
                self.step_labels[i].configure(text_color=PALETTE.fg_primary)
            else:
                # Upcoming
                dot.configure(fg_color=PALETTE.bg_elevated, border_color=PALETTE.border_subtle)
                num.configure(text=str(i + 1), text_color=PALETTE.fg_muted)
                self.step_labels[i].configure(text_color=PALETTE.fg_muted)

        # Show correct page
        for page in self.pages.values():
            page.pack_forget()

        key = self.STEPS[index]["key"]
        self.pages[key].pack(fill="both", expand=True)

    def _start_calibration(self):
        self.needs_calibration = True
        self.window.destroy()

    def _skip(self):
        self.needs_calibration = False
        self.window.destroy()


def show_onboarding_wizard(parent, engine: KursorinEngine, config: KursorinConfig) -> bool:
    """
    Shows the modal onboarding wizard.
    Blocks until the wizard is closed.

    Returns True if calibration was requested.
    """
    wizard = OnboardingWizard(parent, engine, config)
    parent.wait_window(wizard.window)
    return wizard.needs_calibration
