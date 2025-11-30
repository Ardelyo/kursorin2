"""
Cursor Controller

Controls the system mouse cursor using PyAutoGUI.
"""

from typing import Tuple
import pyautogui
import screeninfo

from kursorin.config import KursorinConfig
from kursorin.constants import ClickType


class CursorController:
    """
    Interface for controlling the mouse cursor.
    """
    
    def __init__(self, config: KursorinConfig):
        self.config = config
        pyautogui.FAILSAFE = False  # Disable failsafe for now
        
        # Get screen dimensions
        try:
            screen = screeninfo.get_monitors()[0]
            self.screen_width = screen.width
            self.screen_height = screen.height
        except Exception:
            self.screen_width, self.screen_height = pyautogui.size()
            
    def move_to(self, position: Tuple[float, float]):
        """
        Move cursor to normalized position (0-1).
        """
        x, y = position
        
        # Map to screen coordinates
        if self.config.tracking.invert_x:
            x = 1.0 - x
        if self.config.tracking.invert_y:
            y = 1.0 - y
            
        screen_x = int(x * self.screen_width)
        screen_y = int(y * self.screen_height)
        
        # Clamp
        screen_x = max(0, min(self.screen_width - 1, screen_x))
        screen_y = max(0, min(self.screen_height - 1, screen_y))
        
        pyautogui.moveTo(screen_x, screen_y)
        
    def click(self, click_type: ClickType):
        """
        Perform a click action.
        """
        if click_type == ClickType.LEFT_CLICK:
            pyautogui.click()
        elif click_type == ClickType.RIGHT_CLICK:
            pyautogui.rightClick()
        elif click_type == ClickType.DOUBLE_CLICK:
            pyautogui.doubleClick()
        # Add other click types as needed
