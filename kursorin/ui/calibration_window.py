"""
Calibration Window — KURSORIN

Fullscreen calibration with animated pulsing dots,
progress counter, visual feedback, and smooth transitions.
"""

import tkinter as tk
import math
import time
from typing import Callable, List, Tuple

from kursorin.core.kursorin_engine import KursorinEngine
from kursorin.constants import CALIBRATION_POINTS_3X3
from kursorin.ui.theme import PALETTE


class CalibrationWindow:
    """
    Fullscreen calibration with animated dots and progress.
    """

    # Animation constants
    DOT_RADIUS_BASE = 14
    DOT_RADIUS_PULSE = 4
    PULSE_SPEED = 3.0           # Cycles per second
    TRANSITION_MS = 400         # Time between points
    SUCCESS_FLASH_MS = 200

    def __init__(self, parent, engine: KursorinEngine, on_complete: Callable):
        self.parent = parent
        self.engine = engine
        self.on_complete = on_complete

        self.window = tk.Toplevel(parent)
        self.window.title("Calibration")
        self.window.attributes("-fullscreen", True)
        self.window.configure(bg=PALETTE.bg_deepest)

        # Canvas
        self.canvas = tk.Canvas(
            self.window,
            bg=PALETTE.bg_deepest,
            highlightthickness=0,
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.points = list(CALIBRATION_POINTS_3X3)
        self.current_idx = 0
        self.total = len(self.points)

        # Animation state
        self._anim_start = time.time()
        self._animating = True
        self._dot_id = None
        self._ring_id = None
        self._text_id = None
        self._progress_text_id = None

        # Escape to cancel
        self.window.bind("<Escape>", lambda e: self._cancel())

        # Start after brief delay
        self.window.after(600, self._start)

    def _start(self):
        self.canvas.bind("<Button-1>", self._on_click)
        self._draw_chrome()
        self._show_point()
        self._animate()

    def _draw_chrome(self):
        """Draw persistent UI chrome (instructions, progress)."""
        w = self.window.winfo_width()

        # Title
        self.canvas.create_text(
            w // 2, 40,
            text="Eye Calibration",
            fill=PALETTE.fg_primary,
            font=("Segoe UI", 20, "bold"),
        )

        # Instruction
        self.canvas.create_text(
            w // 2, 72,
            text="Click each dot to calibrate  •  Press ESC to cancel",
            fill=PALETTE.fg_muted,
            font=("Segoe UI", 11),
        )

        # Progress text
        self._progress_text_id = self.canvas.create_text(
            w // 2, 100,
            text=f"1 / {self.total}",
            fill=PALETTE.accent_cyan,
            font=("Cascadia Code", 13, "bold"),
        )

    def _show_point(self):
        """Draw the current calibration point."""
        if self.current_idx >= self.total:
            self._finish()
            return

        # Remove old dot elements
        for item_id in (self._dot_id, self._ring_id):
            if item_id is not None:
                self.canvas.delete(item_id)

        # Get position
        px, py = self.points[self.current_idx]
        w = self.window.winfo_width()
        h = self.window.winfo_height()
        cx = int(px * w)
        cy = int(py * h)

        # Outer ring (will pulse)
        r = self.DOT_RADIUS_BASE + self.DOT_RADIUS_PULSE
        self._ring_id = self.canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            outline=PALETTE.accent_cyan,
            width=2,
        )

        # Inner dot
        r_inner = self.DOT_RADIUS_BASE - 2
        self._dot_id = self.canvas.create_oval(
            cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner,
            fill=PALETTE.accent_red,
            outline=PALETTE.fg_primary,
            width=2,
        )

        # Update progress
        self.canvas.itemconfig(
            self._progress_text_id,
            text=f"{self.current_idx + 1} / {self.total}",
        )

        # Reset animation timer
        self._anim_start = time.time()

    def _animate(self):
        """Animate the pulsing ring around the current dot."""
        if not self._animating or self.current_idx >= self.total:
            return

        t = time.time() - self._anim_start
        pulse = math.sin(t * self.PULSE_SPEED * 2 * math.pi) * 0.5 + 0.5
        r = self.DOT_RADIUS_BASE + int(pulse * self.DOT_RADIUS_PULSE)

        px, py = self.points[self.current_idx]
        w = self.window.winfo_width()
        h = self.window.winfo_height()
        cx = int(px * w)
        cy = int(py * h)

        if self._ring_id:
            self.canvas.coords(
                self._ring_id,
                cx - r, cy - r, cx + r, cy + r,
            )

        self.window.after(16, self._animate)  # ~60fps

    def _on_click(self, event):
        """Handle click on calibration point."""
        if self.current_idx >= self.total:
            return

        px, py = self.points[self.current_idx]

        # Record calibration data
        self.engine.record_calibration_point(px, py)

        # Flash green
        if self._dot_id:
            self.canvas.itemconfig(self._dot_id, fill=PALETTE.status_online)

        self.current_idx += 1
        self.window.after(self.TRANSITION_MS, self._show_point)

    def _finish(self):
        """Calibration complete."""
        self._animating = False
        self.canvas.delete("all")

        w = self.window.winfo_width()
        h = self.window.winfo_height()

        # Success message
        self.canvas.create_text(
            w // 2, h // 2 - 30,
            text="✓",
            fill=PALETTE.accent_cyan,
            font=("Segoe UI", 48, "bold"),
        )
        self.canvas.create_text(
            w // 2, h // 2 + 30,
            text="Calibration Complete",
            fill=PALETTE.fg_primary,
            font=("Segoe UI", 22, "bold"),
        )
        self.canvas.create_text(
            w // 2, h // 2 + 65,
            text="Closing in 2 seconds...",
            fill=PALETTE.fg_muted,
            font=("Segoe UI", 12),
        )

        self.window.after(2000, self._close)

    def _cancel(self):
        self._animating = False
        self.window.destroy()

    def _close(self):
        self._animating = False
        self.window.destroy()
        if self.on_complete:
            self.on_complete()
