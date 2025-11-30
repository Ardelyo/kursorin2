"""
KURSORIN Exceptions

Custom exception classes for error handling in the KURSORIN system.
"""

from typing import Optional, Any


class KursorinError(Exception):
    """Base exception class for all KURSORIN errors."""
    
    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Any] = None
    ):
        self.message = message
        self.code = code
        self.details = details
        super().__init__(self.message)
    
    def __str__(self) -> str:
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, code={self.code!r})"


class CameraError(KursorinError):
    """Exception raised for camera-related errors."""
    
    def __init__(
        self,
        message: str,
        camera_index: Optional[int] = None,
        **kwargs
    ):
        self.camera_index = camera_index
        super().__init__(message, code="CAMERA_ERROR", **kwargs)


class CameraNotFoundError(CameraError):
    """Exception raised when camera device is not found."""
    
    def __init__(self, camera_index: int = 0):
        super().__init__(
            message=f"Camera device not found at index {camera_index}",
            camera_index=camera_index,
        )


class CameraPermissionError(CameraError):
    """Exception raised when camera access is denied."""
    
    def __init__(self, camera_index: int = 0):
        super().__init__(
            message=f"Permission denied for camera at index {camera_index}",
            camera_index=camera_index,
        )


class CameraReadError(CameraError):
    """Exception raised when reading from camera fails."""
    
    def __init__(self, camera_index: int = 0, reason: Optional[str] = None):
        message = f"Failed to read from camera at index {camera_index}"
        if reason:
            message += f": {reason}"
        super().__init__(message=message, camera_index=camera_index)


class TrackingError(KursorinError):
    """Exception raised for tracking-related errors."""
    
    def __init__(self, message: str, tracker: Optional[str] = None, **kwargs):
        self.tracker = tracker
        super().__init__(message, code="TRACKING_ERROR", **kwargs)


class FaceNotDetectedError(TrackingError):
    """Exception raised when face is not detected."""
    
    def __init__(self, message: str = "No face detected in frame"):
        super().__init__(message=message, tracker="face")


class HandNotDetectedError(TrackingError):
    """Exception raised when hand is not detected."""
    
    def __init__(self, message: str = "No hand detected in frame"):
        super().__init__(message=message, tracker="hand")


class LandmarkExtractionError(TrackingError):
    """Exception raised when landmark extraction fails."""
    
    def __init__(self, message: str, landmark_type: str = "unknown"):
        self.landmark_type = landmark_type
        super().__init__(message=message, tracker=landmark_type)


class PoseEstimationError(TrackingError):
    """Exception raised when pose estimation fails."""
    
    def __init__(self, message: str = "Failed to estimate pose"):
        super().__init__(message=message, tracker="pose")


class CalibrationError(KursorinError):
    """Exception raised for calibration-related errors."""
    
    def __init__(self, message: str, stage: Optional[str] = None, **kwargs):
        self.stage = stage
        super().__init__(message, code="CALIBRATION_ERROR", **kwargs)


class CalibrationDataError(CalibrationError):
    """Exception raised for invalid calibration data."""
    
    def __init__(self, message: str = "Invalid or corrupted calibration data"):
        super().__init__(message=message, stage="data")


class CalibrationIncompleteError(CalibrationError):
    """Exception raised when calibration is incomplete."""
    
    def __init__(self, points_collected: int, points_required: int):
        self.points_collected = points_collected
        self.points_required = points_required
        super().__init__(
            message=f"Calibration incomplete: {points_collected}/{points_required} points",
            stage="collection",
        )


class CalibrationFailedError(CalibrationError):
    """Exception raised when calibration validation fails."""
    
    def __init__(self, error_value: float, threshold: float):
        self.error_value = error_value
        self.threshold = threshold
        super().__init__(
            message=f"Calibration failed: error {error_value:.2f} > threshold {threshold:.2f}",
            stage="validation",
        )


class ConfigurationError(KursorinError):
    """Exception raised for configuration-related errors."""
    
    def __init__(self, message: str, parameter: Optional[str] = None, **kwargs):
        self.parameter = parameter
        super().__init__(message, code="CONFIG_ERROR", **kwargs)


class InvalidConfigValueError(ConfigurationError):
    """Exception raised for invalid configuration values."""
    
    def __init__(self, parameter: str, value: Any, expected: str):
        self.value = value
        self.expected = expected
        super().__init__(
            message=f"Invalid value for '{parameter}': {value!r}. Expected: {expected}",
            parameter=parameter,
        )


class ConfigFileNotFoundError(ConfigurationError):
    """Exception raised when configuration file is not found."""
    
    def __init__(self, path: str):
        self.path = path
        super().__init__(
            message=f"Configuration file not found: {path}",
            parameter="config_file",
        )


class ConfigParseError(ConfigurationError):
    """Exception raised when configuration file cannot be parsed."""
    
    def __init__(self, path: str, reason: Optional[str] = None):
        self.path = path
        message = f"Failed to parse configuration file: {path}"
        if reason:
            message += f" ({reason})"
        super().__init__(message=message, parameter="config_file")


class FusionError(KursorinError):
    """Exception raised for fusion-related errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, code="FUSION_ERROR", **kwargs)


class NoValidModalityError(FusionError):
    """Exception raised when no valid tracking modality is available."""
    
    def __init__(self):
        super().__init__(
            message="No valid tracking modality available for fusion"
        )


class SystemError(KursorinError):
    """Exception raised for system-level errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, code="SYSTEM_ERROR", **kwargs)


class InsufficientResourcesError(SystemError):
    """Exception raised when system resources are insufficient."""
    
    def __init__(self, resource: str, required: Any, available: Any):
        self.resource = resource
        self.required = required
        self.available = available
        super().__init__(
            message=f"Insufficient {resource}: required {required}, available {available}"
        )


class DependencyError(SystemError):
    """Exception raised when a required dependency is missing."""
    
    def __init__(self, dependency: str, message: Optional[str] = None):
        self.dependency = dependency
        msg = f"Missing required dependency: {dependency}"
        if message:
            msg += f" ({message})"
        super().__init__(message=msg)


# =============================================================================
# Error Handlers
# =============================================================================

def handle_camera_error(error: CameraError) -> dict:
    """Handle camera errors and return appropriate response."""
    return {
        "error_type": "camera",
        "message": str(error),
        "camera_index": error.camera_index,
        "suggestions": [
            "Check if camera is connected",
            "Verify camera permissions",
            "Try a different camera index",
            "Restart the application",
        ],
    }


def handle_tracking_error(error: TrackingError) -> dict:
    """Handle tracking errors and return appropriate response."""
    return {
        "error_type": "tracking",
        "message": str(error),
        "tracker": error.tracker,
        "suggestions": [
            "Ensure good lighting conditions",
            "Position yourself clearly in frame",
            "Check if face/hand is visible",
            "Reduce background complexity",
        ],
    }


def handle_calibration_error(error: CalibrationError) -> dict:
    """Handle calibration errors and return appropriate response."""
    return {
        "error_type": "calibration",
        "message": str(error),
        "stage": error.stage,
        "suggestions": [
            "Complete all calibration points",
            "Hold steady during calibration",
            "Ensure consistent lighting",
            "Restart calibration process",
        ],
    }
