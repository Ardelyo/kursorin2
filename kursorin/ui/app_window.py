"""
Main Application Window

Tkinter-based GUI for KURSORIN.
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2
import threading
import time

from kursorin.config import KursorinConfig
from kursorin.core.kursorin_engine import KursorinEngine, FrameResult
from kursorin.ui.overlay import Overlay
from kursorin.ui.calibration_window import CalibrationWindow


class AppWindow:
    """
    Main GUI window.
    """
    
    def __init__(self, engine: KursorinEngine, config: KursorinConfig):
        self.engine = engine
        self.config = config
        self.root = tk.Tk()
        self.root.title("KURSORIN")
        self.root.geometry("800x600")
        
        self.overlay = Overlay(config)
        
        self._setup_ui()
        
        # Connect engine callbacks
        self.engine.on_frame(self._on_frame)
        
        # Handle close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
    def _setup_ui(self):
        """Setup UI components."""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Video Preview
        self.video_label = ttk.Label(main_frame)
        self.video_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Controls
        controls_frame = ttk.Frame(main_frame, width=200)
        controls_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10)
        
        # Start/Stop Button
        self.btn_start = ttk.Button(controls_frame, text="Start", command=self._toggle_tracking)
        self.btn_start.pack(fill=tk.X, pady=5)
        
        # Status Label
        self.lbl_status = ttk.Label(controls_frame, text="Status: Idle")
        self.lbl_status.pack(fill=tk.X, pady=5)
        
        # Settings (Simplified)
        ttk.Label(controls_frame, text="Sensitivity").pack(fill=tk.X, pady=(20, 5))
        self.scale_sens = ttk.Scale(controls_frame, from_=0.1, to=5.0, value=self.config.tracking.head_sensitivity_x)
        self.scale_sens.pack(fill=tk.X)

        # Calibration Button
        self.btn_calibrate = ttk.Button(controls_frame, text="Calibrate", command=self._start_calibration)
        self.btn_calibrate.pack(fill=tk.X, pady=20)
        
        # Mirroring Controls
        mirror_frame = ttk.LabelFrame(controls_frame, text="Mirroring")
        mirror_frame.pack(fill=tk.X, pady=10)
        
        self.var_invert_x = tk.BooleanVar(value=self.config.tracking.invert_x)
        self.chk_invert_x = ttk.Checkbutton(mirror_frame, text="Invert X", variable=self.var_invert_x, command=self._update_config)
        self.chk_invert_x.pack(anchor=tk.W)
        
        self.var_invert_y = tk.BooleanVar(value=self.config.tracking.invert_y)
        self.chk_invert_y = ttk.Checkbutton(mirror_frame, text="Invert Y", variable=self.var_invert_y, command=self._update_config)
        self.chk_invert_y.pack(anchor=tk.W)
        
        # Accessibility Scenarios
        scenario_frame = ttk.LabelFrame(controls_frame, text="Scenario")
        scenario_frame.pack(fill=tk.X, pady=10)
        
        self.scenarios = ["Default", "Hands-Free", "No Head Tracking"]
        self.cmb_scenario = ttk.Combobox(scenario_frame, values=self.scenarios, state="readonly")
        self.cmb_scenario.current(0)
        self.cmb_scenario.pack(fill=tk.X, pady=5)
        self.cmb_scenario.bind("<<ComboboxSelected>>", self._on_scenario_change)
        
    def _toggle_tracking(self):
        if self.engine.is_running:
            self.engine.stop()
            self.btn_start.configure(text="Start")
            self.lbl_status.configure(text="Status: Stopped")
        else:
            try:
                self.engine.start()
                self.btn_start.configure(text="Stop")
                self.lbl_status.configure(text="Status: Running")
            except Exception as e:
                self.lbl_status.configure(text=f"Error: {str(e)}")

    def _start_calibration(self):
        """Start the calibration process."""
        if not self.engine.is_running:
            self.lbl_status.configure(text="Error: Start engine first")
            return
            
        self.engine.start_calibration()
        CalibrationWindow(self.root, self.engine, self._on_calibration_complete)
        
    def _on_calibration_complete(self):
        """Handle calibration completion."""
        self.engine.stop_calibration()
        self.lbl_status.configure(text="Status: Calibration Complete")
        
    def _update_config(self):
        """Update configuration from UI."""
        self.config.tracking.invert_x = self.var_invert_x.get()
        self.config.tracking.invert_y = self.var_invert_y.get()
        
    def _on_scenario_change(self, event):
        """Handle scenario change."""
        scenario = self.cmb_scenario.get()
        
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
            
        elif scenario == "No Head Tracking":
            self.config.tracking.head_enabled = False
            self.config.tracking.eye_enabled = True
            self.config.tracking.hand_enabled = True
            self.config.click.pinch_click_enabled = True
            
        logger.info(f"Switched to scenario: {scenario}")
                
    def _on_frame(self, result: FrameResult):
        """Handle new frame from engine."""
        if result.frame is not None:
            # Draw overlay
            vis_frame = self.overlay.draw(result.frame, result)
            
            # Convert to Tkinter image
            rgb_frame = cv2.cvtColor(vis_frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb_frame)
            
            # Resize if needed to fit label
            # For now, just display
            imgtk = ImageTk.PhotoImage(image=img)
            
            # Update label (must be thread safe, use after)
            self.root.after(0, self._update_video_label, imgtk)
            
    def _update_video_label(self, imgtk):
        self.video_label.configure(image=imgtk)
        self.video_label.image = imgtk # Keep reference
        
    def _on_close(self):
        if self.engine.is_running:
            self.engine.stop()
        self.root.destroy()
        
    def run(self):
        self.root.mainloop()
