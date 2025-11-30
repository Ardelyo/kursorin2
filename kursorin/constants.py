"""
KURSORIN Constants

Defines all constant values used throughout the KURSORIN system.
"""

from enum import Enum, IntEnum, auto
from typing import Dict, List, Tuple


# =============================================================================
# Version Information
# =============================================================================

VERSION = "1.0.0"
VERSION_TUPLE = (1, 0, 0)
BUILD_DATE = "2024-01-15"


# =============================================================================
# MediaPipe Face Mesh Landmarks
# =============================================================================

class FaceLandmark(IntEnum):
    """Face mesh landmark indices for key facial features."""
    
    # Nose
    NOSE_TIP = 1
    NOSE_BOTTOM = 2
    NOSE_RIGHT = 129
    NOSE_LEFT = 358
    
    # Left Eye
    LEFT_EYE_INNER = 133
    LEFT_EYE_OUTER = 33
    LEFT_EYE_TOP = 159
    LEFT_EYE_BOTTOM = 145
    LEFT_EYE_CENTER = 468  # Iris center (refined landmarks)
    
    # Right Eye
    RIGHT_EYE_INNER = 362
    RIGHT_EYE_OUTER = 263
    RIGHT_EYE_TOP = 386
    RIGHT_EYE_BOTTOM = 374
    RIGHT_EYE_CENTER = 473  # Iris center (refined landmarks)
    
    # Eyebrows
    LEFT_EYEBROW_INNER = 107
    LEFT_EYEBROW_OUTER = 46
    RIGHT_EYEBROW_INNER = 336
    RIGHT_EYEBROW_OUTER = 276
    
    # Mouth
    UPPER_LIP_TOP = 13
    UPPER_LIP_BOTTOM = 14
    LOWER_LIP_TOP = 17
    LOWER_LIP_BOTTOM = 18
    MOUTH_LEFT = 61
    MOUTH_RIGHT = 291
    
    # Face outline
    CHIN = 152
    LEFT_CHEEK = 234
    RIGHT_CHEEK = 454
    FOREHEAD = 10
    
    # For pose estimation
    LEFT_EAR = 234
    RIGHT_EAR = 454


# Eye landmarks for EAR calculation (6 points per eye)
LEFT_EYE_EAR_LANDMARKS = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_EAR_LANDMARKS = [362, 385, 387, 263, 373, 380]

# Iris landmarks (when using refined landmarks)
LEFT_IRIS_LANDMARKS = list(range(468, 473))
RIGHT_IRIS_LANDMARKS = list(range(473, 478))


# =============================================================================
# MediaPipe Hand Landmarks
# =============================================================================

class HandLandmark(IntEnum):
    """Hand landmark indices."""
    
    WRIST = 0
    
    THUMB_CMC = 1
    THUMB_MCP = 2
    THUMB_IP = 3
    THUMB_TIP = 4
    
    INDEX_MCP = 5
    INDEX_PIP = 6
    INDEX_DIP = 7
    INDEX_TIP = 8
    
    MIDDLE_MCP = 9
    MIDDLE_PIP = 10
    MIDDLE_DIP = 11
    MIDDLE_TIP = 12
    
    RING_MCP = 13
    RING_PIP = 14
    RING_DIP = 15
    RING_TIP = 16
    
    PINKY_MCP = 17
    PINKY_PIP = 18
    PINKY_DIP = 19
    PINKY_TIP = 20


# Finger tip landmarks
FINGER_TIPS = [
    HandLandmark.THUMB_TIP,
    HandLandmark.INDEX_TIP,
    HandLandmark.MIDDLE_TIP,
    HandLandmark.RING_TIP,
    HandLandmark.PINKY_TIP,
]

# Finger PIP landmarks (for finger state detection)
FINGER_PIPS = [
    HandLandmark.THUMB_IP,  # Use IP for thumb
    HandLandmark.INDEX_PIP,
    HandLandmark.MIDDLE_PIP,
    HandLandmark.RING_PIP,
    HandLandmark.PINKY_PIP,
]


# =============================================================================
# Gesture Types
# =============================================================================

class Gesture(Enum):
    """Recognized hand gestures."""
    
    NONE = auto()
    POINTING = auto()        # Index finger extended
    PINCH = auto()           # Thumb and index close
    FIST = auto()            # All fingers closed
    OPEN_PALM = auto()       # All fingers extended
    PEACE = auto()           # Index and middle extended
    THUMBS_UP = auto()       # Thumb up, others closed
    THUMBS_DOWN = auto()     # Thumb down, others closed
    OK = auto()              # OK sign
    THREE = auto()           # Three fingers
    FOUR = auto()            # Four fingers
    ROCK = auto()            # Index and pinky extended
    CALL = auto()            # Thumb and pinky extended
    
    # Navigation gestures
    SWIPE_LEFT = auto()
    SWIPE_RIGHT = auto()
    SWIPE_UP = auto()
    SWIPE_DOWN = auto()


class ClickType(Enum):
    """Types of click events."""
    
    NONE = auto()
    LEFT_CLICK = auto()
    RIGHT_CLICK = auto()
    DOUBLE_CLICK = auto()
    MIDDLE_CLICK = auto()
    DRAG_START = auto()
    DRAG_END = auto()
    SCROLL_UP = auto()
    SCROLL_DOWN = auto()


class TrackingMode(Enum):
    """Active tracking modes."""
    
    HEAD = auto()
    EYE = auto()
    HAND = auto()
    FUSED = auto()


class TrackingState(Enum):
    """Tracking system states."""
    
    IDLE = auto()
    TRACKING = auto()
    PAUSED = auto()
    CALIBRATING = auto()
    ERROR = auto()


# =============================================================================
# 3D Face Model Points
# =============================================================================

# 3D model points for head pose estimation (in mm, canonical face model)
FACE_3D_MODEL_POINTS = {
    "nose_tip": (0.0, 0.0, 0.0),
    "chin": (0.0, -330.0, -65.0),
    "left_eye_corner": (-225.0, 170.0, -135.0),
    "right_eye_corner": (225.0, 170.0, -135.0),
    "left_mouth_corner": (-150.0, -150.0, -125.0),
    "right_mouth_corner": (150.0, -150.0, -125.0),
}

# Corresponding landmark indices
FACE_MODEL_LANDMARK_INDICES = {
    "nose_tip": FaceLandmark.NOSE_TIP,
    "chin": FaceLandmark.CHIN,
    "left_eye_corner": FaceLandmark.LEFT_EYE_OUTER,
    "right_eye_corner": FaceLandmark.RIGHT_EYE_OUTER,
    "left_mouth_corner": FaceLandmark.MOUTH_LEFT,
    "right_mouth_corner": FaceLandmark.MOUTH_RIGHT,
}


# =============================================================================
# Default Thresholds
# =============================================================================

# Eye Aspect Ratio thresholds
EAR_BLINK_THRESHOLD = 0.2
EAR_CLOSED_THRESHOLD = 0.15
EAR_OPEN_THRESHOLD = 0.25

# Blink timing (seconds)
BLINK_DURATION_MIN = 0.05
BLINK_DURATION_MAX = 0.4
BLINK_COOLDOWN = 0.3

# Mouth Aspect Ratio thresholds
MAR_OPEN_THRESHOLD = 0.5
MAR_SMILE_THRESHOLD = 0.3

# Pinch detection
PINCH_DISTANCE_THRESHOLD = 0.05  # Normalized distance
PINCH_HOLD_TIME = 0.3  # Seconds

# Dwell click
DWELL_TIME_DEFAULT = 1.0  # Seconds
DWELL_RADIUS_DEFAULT = 30  # Pixels

# Smoothing
SMOOTHING_FACTOR_DEFAULT = 0.7
DEAD_ZONE_DEFAULT = 5  # Pixels

# Fusion
FUSION_TEMPERATURE_DEFAULT = 2.0


# =============================================================================
# Color Definitions (BGR for OpenCV)
# =============================================================================

class Color:
    """Color constants in BGR format."""
    
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (0, 0, 255)
    GREEN = (0, 255, 0)
    BLUE = (255, 0, 0)
    YELLOW = (0, 255, 255)
    CYAN = (255, 255, 0)
    MAGENTA = (255, 0, 255)
    ORANGE = (0, 165, 255)
    PINK = (203, 192, 255)
    PURPLE = (128, 0, 128)
    GRAY = (128, 128, 128)
    LIGHT_GRAY = (200, 200, 200)
    DARK_GRAY = (50, 50, 50)
    
    # Tracking visualization colors
    HEAD_COLOR = CYAN
    EYE_COLOR = GREEN
    HAND_COLOR = ORANGE
    FUSED_COLOR = MAGENTA
    
    # UI colors
    SUCCESS = GREEN
    WARNING = YELLOW
    ERROR = RED
    INFO = BLUE


# =============================================================================
# UI Constants
# =============================================================================

# Window sizes
DEFAULT_PREVIEW_WIDTH = 640
DEFAULT_PREVIEW_HEIGHT = 480
OVERLAY_WIDTH = 200
OVERLAY_HEIGHT = 100

# Fonts
FONT_FACE = 0  # cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 0.5
FONT_THICKNESS = 1

# Drawing
LANDMARK_RADIUS = 2
CONNECTION_THICKNESS = 1
CURSOR_SIZE = 10

# Animation
DWELL_ANIMATION_SEGMENTS = 60
TRANSITION_DURATION_MS = 200


# =============================================================================
# Performance Constants
# =============================================================================

# Frame rate limits
MIN_FPS = 15
MAX_FPS = 120
TARGET_FPS = 30

# Processing
MAX_PROCESSING_TIME_MS = 50
FRAME_SKIP_THRESHOLD_MS = 33  # Skip if processing takes > 1 frame at 30fps

# Buffer sizes
POSITION_HISTORY_SIZE = 10
VELOCITY_HISTORY_SIZE = 5
RELIABILITY_HISTORY_SIZE = 10

# Kalman filter defaults
KALMAN_PROCESS_NOISE = 0.03
KALMAN_MEASUREMENT_NOISE = 0.1


# =============================================================================
# Calibration Constants
# =============================================================================

# Calibration grid
CALIBRATION_POINTS_3X3 = [
    (0.1, 0.1), (0.5, 0.1), (0.9, 0.1),
    (0.1, 0.5), (0.5, 0.5), (0.9, 0.5),
    (0.1, 0.9), (0.5, 0.9), (0.9, 0.9),
]

CALIBRATION_POINTS_4X4 = [
    (0.1, 0.1), (0.37, 0.1), (0.63, 0.1), (0.9, 0.1),
    (0.1, 0.37), (0.37, 0.37), (0.63, 0.37), (0.9, 0.37),
    (0.1, 0.63), (0.37, 0.63), (0.63, 0.63), (0.9, 0.63),
    (0.1, 0.9), (0.37, 0.9), (0.63, 0.9), (0.9, 0.9),
]

# Validation points (different from calibration)
VALIDATION_POINTS = [
    (0.25, 0.25), (0.75, 0.25),
    (0.25, 0.75), (0.75, 0.75),
]

# Calibration timing
CALIBRATION_DWELL_TIME = 2.0  # Seconds per point
CALIBRATION_TRANSITION_TIME = 0.5  # Seconds between points


# =============================================================================
# File Paths
# =============================================================================

# Default data directory
DEFAULT_DATA_DIR = "~/.kursorin"

# Configuration files
CONFIG_FILE = "config.yaml"
CALIBRATION_FILE = "calibration.json"
SESSION_FILE = "session.json"

# Log files
LOG_FILE = "kursorin.log"

# Asset paths (relative to package)
ASSETS_DIR = "assets"
ICONS_DIR = f"{ASSETS_DIR}/icons"
SOUNDS_DIR = f"{ASSETS_DIR}/sounds"
