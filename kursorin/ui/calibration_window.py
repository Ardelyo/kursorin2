"""
Calibration Window

UI for eye tracking calibration.
"""

import tkinter as tk
from tkinter import ttk
import time
from typing import Callable, List, Tuple

from kursorin.config import KursorinConfig
from kursorin.constants import CALIBRATION_POINTS_3X3, Color


class CalibrationWindow:
    """
    Window for performing 9-point calibration.
    """
    
    def __init__(self, parent, config: KursorinConfig, on_complete: Callable):
        self.parent = parent
        self.config = config
        self.on_complete = on_complete
        
        self.window = tk.Toplevel(parent)
        self.window.title("Calibration")
        self.window.attributes("-fullscreen", True)
        self.window.configure(bg="black")
        
        self.canvas = tk.Canvas(self.window, bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.points = CALIBRATION_POINTS_3X3
        self.current_point_idx = 0
        
        self.window.after(1000, self._start_calibration)
        
    def _start_calibration(self):
        self._show_next_point()
        
    def _show_next_point(self):
        if self.current_point_idx >= len(self.points):
            self._finish()
            return
            
        # Clear canvas
        self.canvas.delete("all")
        
        # Get point coordinates
        px, py = self.points[self.current_point_idx]
        w = self.window.winfo_width()
        h = self.window.winfo_height()
        
        cx = int(px * w)
        cy = int(py * h)
        
        # Draw point
        radius = 20
        self.canvas.create_oval(
            cx - radius, cy - radius, cx + radius, cy + radius,
            fill="red", outline="white", width=2
        )
        
        # Animate shrinking
        self._animate_point(cx, cy, radius)
        
    def _animate_point(self, cx, cy, radius):
        if radius <= 5:
            # Point captured
            # In a real system, we would collect gaze data here
            self.current_point_idx += 1
            self.window.after(500, self._show_next_point)
            return
            
        self.canvas.delete("all")
        self.canvas.create_oval(
            cx - radius, cy - radius, cx + radius, cy + radius,
            fill="red", outline="white", width=2
        )
        
        self.window.after(50, lambda: self._animate_point(cx, cy, radius - 1))
        
    def _finish(self):
        self.window.destroy()
        if self.on_complete:
            self.on_complete()
