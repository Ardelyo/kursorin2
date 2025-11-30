"""
Calibration Window

UI for eye tracking calibration.
"""

import tkinter as tk
from tkinter import ttk
import time
from typing import Callable, List, Tuple

from kursorin.core.kursorin_engine import KursorinEngine
from kursorin.constants import CALIBRATION_POINTS_3X3, Color


class CalibrationWindow:
    """
    Window for performing 9-point calibration.
    """
    
    def __init__(self, parent, engine: KursorinEngine, on_complete: Callable):
        self.parent = parent
        self.engine = engine
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
        # Bind mouse click
        self.canvas.bind("<Button-1>", self._on_click)
        self._show_next_point()
        
    def _on_click(self, event):
        """Handle mouse click on calibration point."""
        # Get current target point
        if self.current_point_idx >= len(self.points):
            return
            
        px, py = self.points[self.current_point_idx]
        w = self.window.winfo_width()
        h = self.window.winfo_height()
        cx = int(px * w)
        cy = int(py * h)
        
        # Check if click is near the target (optional, but good for UX)
        # For now, we assume the user is trying to click the dot
        
        # Record data with GROUND TRUTH (mouse position)
        # Ideally we use the target center (px, py) as ground truth
        self.engine.record_calibration_point(px, py)
        
        # Visual feedback
        self.canvas.itemconfig(self.dot, fill="green")
        
        # Move to next point after short delay
        self.current_point_idx += 1
        self.window.after(200, self._show_next_point)

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
        radius = 15
        self.dot = self.canvas.create_oval(
            cx - radius, cy - radius, cx + radius, cy + radius,
            fill="red", outline="white", width=2
        )
        
        # Instruction
        self.canvas.create_text(
            w/2, 50,
            text=f"Klik titik merah ({self.current_point_idx + 1}/{len(self.points)})",
            fill="white", font=("Arial", 20)
        )
        
    def _finish(self):
        self.window.destroy()
        if self.on_complete:
            self.on_complete()
