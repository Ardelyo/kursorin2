"""
Calibration Window — KURSORIN
"""

import tkinter as tk
import math
import time
from typing import Callable, List, Tuple

from kursorin.core.kursorin_engine import KursorinEngine
from kursorin.constants import CALIBRATION_POINTS_3X3
from kursorin.ui.theme import PALETTE
from kursorin.i18n import t


class CalibrationWindow:
    def __init__(self, parent, engine: KursorinEngine, on_complete: Callable):
        self.parent = parent
        self.engine = engine
        self.on_complete = on_complete

        # Animation constants
        self.DOT_RADIUS_BASE = 14
        self.DOT_RADIUS_PULSE = 4
        self.PULSE_SPEED = 3.0           # Cycles per second
        self.TRANSITION_MS = 400         # Time between points

        self.window = tk.Toplevel(parent)
        self.window.title(t('calib.title'))
        self.window.attributes("-fullscreen", True)
        self.window.configure(bg=PALETTE.bg_deepest)
        
        # Bring to front
        self.window.attributes('-topmost', True)
        self.window.after(100, lambda: self.window.attributes('-topmost', False))

        self.canvas = tk.Canvas(
            self.window,
            bg=PALETTE.bg_deepest,
            highlightthickness=0,
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.points = list(CALIBRATION_POINTS_3X3)
        self.current_idx = 0
        self.total = len(self.points)

        self._anim_start = time.time()
        self._animating = True
        self._dot_id = None
        self._ring_id = None
        self._text_id = None
        self._progress_text_id = None

        self.window.bind("<Escape>", lambda e: self._cancel())

        # Start after brief delay
        self.window.after(600, self._start)

    def _start(self):
        if not self._animating: return
        self.canvas.bind("<Button-1>", self._on_click)
        self._draw_chrome()
        self._show_point()
        self._animate()

    def _draw_chrome(self):
        try:
            w = self.window.winfo_width()
            self.canvas.create_text(
                w // 2, 40,
                text=t('calib.title'),
                fill=PALETTE.fg_primary,
                font=("Segoe UI", 20, "bold"),
            )
            self.canvas.create_text(
                w // 2, 72,
                text=t('calib.instruction'),
                fill=PALETTE.fg_muted,
                font=("Segoe UI", 11),
            )
            self._progress_text_id = self.canvas.create_text(
                w // 2, 100,
                text=f"1 / {self.total}",
                fill=PALETTE.accent_cyan,
                font=("Cascadia Code", 13, "bold"),
            )
        except tk.TclError:
            pass

    def _show_point(self):
        if not self._animating: return
        if self.current_idx >= self.total:
            self._finish()
            return
            
        try:
            for item_id in (self._dot_id, self._ring_id):
                if item_id is not None:
                    self.canvas.delete(item_id)

            px, py = self.points[self.current_idx]
            w = self.window.winfo_width()
            h = self.window.winfo_height()
            
            if w <= 1 or h <= 1:
                # Window not fully initialized
                w = self.window.winfo_screenwidth()
                h = self.window.winfo_screenheight()
                
            cx = int(px * w)
            cy = int(py * h)

            r = self.DOT_RADIUS_BASE + self.DOT_RADIUS_PULSE
            self._ring_id = self.canvas.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                outline=PALETTE.accent_cyan,
                width=2,
            )

            r_inner = self.DOT_RADIUS_BASE - 2
            self._dot_id = self.canvas.create_oval(
                cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner,
                fill=PALETTE.accent_red,
                outline=PALETTE.fg_primary,
                width=2,
            )

            self.canvas.itemconfig(
                self._progress_text_id,
                text=f"{self.current_idx + 1} / {self.total}",
            )

            self._anim_start = time.time()
        except tk.TclError:
            pass

    def _animate(self):
        if not self._animating or self.current_idx >= self.total:
            return

        try:
            t_curr = time.time() - self._anim_start
            pulse = math.sin(t_curr * self.PULSE_SPEED * 2 * math.pi) * 0.5 + 0.5
            r = self.DOT_RADIUS_BASE + int(pulse * self.DOT_RADIUS_PULSE)

            px, py = self.points[self.current_idx]
            w = self.window.winfo_width()
            h = self.window.winfo_height()
            
            if w > 1 and h > 1:
                cx = int(px * w)
                cy = int(py * h)

                if self._ring_id:
                    self.canvas.coords(
                        self._ring_id,
                        cx - r, cy - r, cx + r, cy + r,
                    )

            self.window.after(16, self._animate)
        except tk.TclError:
            pass

    def _on_click(self, event):
        if not self._animating or self.current_idx >= self.total:
            return

        px, py = self.points[self.current_idx]
        
        try:
            self.engine.record_calibration_point(px, py)
        except Exception:
            pass

        try:
            if self._dot_id:
                self.canvas.itemconfig(self._dot_id, fill=PALETTE.status_online)

            self.current_idx += 1
            self.window.after(self.TRANSITION_MS, self._show_point)
        except tk.TclError:
            pass

    def _finish(self):
        self._animating = False
        try:
            self.canvas.delete("all")
            w = self.window.winfo_width()
            h = self.window.winfo_height()

            self.canvas.create_text(
                w // 2, h // 2 - 30,
                text="✓",
                fill=PALETTE.accent_cyan,
                font=("Segoe UI", 48, "bold"),
            )
            self.canvas.create_text(
                w // 2, h // 2 + 30,
                text=t('calib.complete'),
                fill=PALETTE.fg_primary,
                font=("Segoe UI", 22, "bold"),
            )
            self.canvas.create_text(
                w // 2, h // 2 + 65,
                text=t('calib.closing'),
                fill=PALETTE.fg_muted,
                font=("Segoe UI", 12),
            )
            self.window.after(2000, self._close)
        except tk.TclError:
            self._close()

    def _cancel(self):
        self._animating = False
        try:
            self.window.destroy()
        except tk.TclError:
            pass
        finally:
            if self.on_complete:
                self.on_complete()

    def _close(self):
        self._animating = False
        try:
            self.window.destroy()
        except tk.TclError:
            pass
        finally:
            if self.on_complete:
                self.on_complete()
