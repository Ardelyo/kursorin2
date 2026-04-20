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
        pyautogui.FAILSAFE = True  # Enable failsafe (top-left corner to stop)
        pyautogui.PAUSE = 0.0      # No artificial pause — FAILSAFE is sufficient protection
        
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

        Note: invert_x / invert_y are already handled inside each tracker via
        XOR logic before fusion. The controller must NOT re-apply them or the
        global inversion flag ends up applied twice (double-flip = no effect at
        best, wrong direction at worst).
        """
        x, y = position

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
        
    def mouse_down(self):
        """
        Press and hold the left mouse button for dragging.
        """
        pyautogui.mouseDown()
        
    def mouse_up(self):
        """
        Release the left mouse button.
        """
        pyautogui.mouseUp()
        
    def scroll(self, amount: int):
        """
        Scroll vertically by given amount (positive=up, negative=down).
        """
        pyautogui.scroll(amount)
