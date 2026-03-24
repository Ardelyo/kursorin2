"""
Onboarding Wizard for KURSORIN.

Provides a guided setup experience for first-time users.
"""

import tkinter as tk
from tkinter import ttk
from loguru import logger

from kursorin.config import KursorinConfig
from kursorin.core.kursorin_engine import KursorinEngine


class OnboardingWizard:
    def __init__(self, parent: tk.Tk, engine: KursorinEngine, config: KursorinConfig):
        self.parent = parent
        self.engine = engine
        self.config = config
        
        self.window = tk.Toplevel(parent)
        self.window.title("Welcome to KURSORIN Setup")
        self.window.geometry("500x350")
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()  # Make it modal
        
        # Center window over parent
        self.window.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 500) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 350) // 2
        self.window.geometry(f"+{x}+{y}")
        
        self.needs_calibration = False
        self.frames = {}
        
        self._build_ui()
        self._show_frame("welcome")

    def _build_ui(self):
        # PAGE 1: Welcome
        f_welcome = ttk.Frame(self.window, padding=20)
        self.frames["welcome"] = f_welcome
        
        ttk.Label(f_welcome, text="Welcome to KURSORIN", font=("Helvetica", 16, "bold")).pack(pady=10)
        ttk.Label(
            f_welcome, 
            text=(
                "KURSORIN is a hands-free mouse control system.\n\n"
                "Let's get you set up to use your face and hands\n"
                "as a virtual cursor. This quick setup will configure your\n"
                "environment and calibrate eye tracking."
            ),
            justify="center"
        ).pack(pady=20)
        ttk.Button(f_welcome, text="Start Setup", command=lambda: self._show_frame("camera")).pack(pady=20)
        
        # PAGE 2: Camera Check
        f_camera = ttk.Frame(self.window, padding=20)
        self.frames["camera"] = f_camera
        
        ttk.Label(f_camera, text="Step 1: Environment Check", font=("Helvetica", 14, "bold")).pack(pady=10)
        ttk.Label(
            f_camera, 
            text=(
                "Please ensure you are in a well-lit room.\n"
                "Position your webcam so it can see your face \n"
                "and hands clearly without obstruction.\n\n"
                f"We are using Camera Index: {self.config.camera.camera_index}"
            ), 
            justify="center"
        ).pack(pady=20)
        
        btn_frame1 = ttk.Frame(f_camera)
        btn_frame1.pack(pady=20)
        ttk.Button(btn_frame1, text="Back", command=lambda: self._show_frame("welcome")).pack(side="left", padx=5)
        ttk.Button(btn_frame1, text="Next", command=lambda: self._show_frame("calibration")).pack(side="left", padx=5)
        
        # PAGE 3: Calibration info
        f_calib = ttk.Frame(self.window, padding=20)
        self.frames["calibration"] = f_calib
        
        ttk.Label(f_calib, text="Step 2: Eye Calibration", font=("Helvetica", 14, "bold")).pack(pady=10)
        ttk.Label(
            f_calib, 
            text=(
                "To map your gaze accurately to the screen, we must calibrate.\n\n"
                "When you click start, dots will appear on the screen.\n"
                "Look at each dot continuously until it moves.\n"
                "Keep your head relatively still during this process."
            ), 
            justify="center"
        ).pack(pady=20)
        
        btn_frame2 = ttk.Frame(f_calib)
        btn_frame2.pack(pady=20)
        ttk.Button(btn_frame2, text="Back", command=lambda: self._show_frame("camera")).pack(side="left", padx=5)
        
        btn_start_calib = ttk.Button(
            btn_frame2, 
            text="Start Calibration", 
            command=self._start_calibration
        )
        btn_start_calib.pack(side="left", padx=5)

    def _show_frame(self, name: str):
        for frame in self.frames.values():
            frame.pack_forget()
        self.frames[name].pack(fill="both", expand=True)
        
    def _start_calibration(self):
        self.needs_calibration = True
        self.window.destroy()


def show_onboarding_wizard(parent: tk.Tk, engine: KursorinEngine, config: KursorinConfig) -> bool:
    """
    Shows the modal onboarding wizard.
    Blocks until the wizard is closed.
    
    Returns True if calibration was requested.
    """
    wizard = OnboardingWizard(parent, engine, config)
    parent.wait_window(wizard.window)
    return wizard.needs_calibration
