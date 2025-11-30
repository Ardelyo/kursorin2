"""
KURSORIN Configuration Module

Handles all configuration settings for the KURSORIN system,
including tracking parameters, UI settings, and calibration data.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml
from pydantic import BaseModel, Field, validator


class TrackingConfig(BaseModel):
    """Configuration for tracking modules."""
    
    # Head tracking
    head_enabled: bool = True
    head_sensitivity_x: float = Field(default=2.5, ge=0.5, le=5.0)
    head_sensitivity_y: float = Field(default=2.0, ge=0.5, le=5.0)
    head_dead_zone: float = Field(default=0.02, ge=0.0, le=0.1)
    head_smoothing: float = Field(default=0.8, ge=0.0, le=0.99)
    
    # Eye tracking
    eye_enabled: bool = True
    eye_sensitivity: float = Field(default=1.0, ge=0.5, le=2.0)
    eye_calibrated: bool = False
    eye_blink_threshold: float = Field(default=0.2, ge=0.1, le=0.4)
    eye_blink_duration_min: float = Field(default=0.05, ge=0.02, le=0.2)
    eye_blink_duration_max: float = Field(default=0.4, ge=0.2, le=1.0)
    
    # Hand tracking
    hand_enabled: bool = True
    hand_sensitivity: float = Field(default=1.5, ge=0.5, le=3.0)
    hand_smoothing: float = Field(default=0.6, ge=0.0, le=0.99)
    pinch_threshold: float = Field(default=0.05, ge=0.02, le=0.15)
    hand_visibility_threshold: float = Field(default=0.7, ge=0.5, le=1.0)


class FusionConfig(BaseModel):
    """Configuration for multi-modal fusion."""
    
    fusion_enabled: bool = True
    fusion_temperature: float = Field(default=2.0, ge=0.5, le=5.0)
    reliability_weight_confidence: float = Field(default=0.6, ge=0.0, le=1.0)
    reliability_weight_jitter: float = Field(default=0.4, ge=0.0, le=1.0)
    history_length: int = Field(default=10, ge=5, le=50)
    
    # Modality weights (manual override)
    manual_weights_enabled: bool = False
    weight_head: float = Field(default=0.4, ge=0.0, le=1.0)
    weight_eye: float = Field(default=0.3, ge=0.0, le=1.0)
    weight_hand: float = Field(default=0.3, ge=0.0, le=1.0)


class ClickConfig(BaseModel):
    """Configuration for click detection."""
    
    # Blink click
    blink_click_enabled: bool = True
    blink_click_eye: str = Field(default="left", pattern="^(left|right|both)$")
    
    # Dwell click
    dwell_click_enabled: bool = True
    dwell_time_ms: int = Field(default=1000, ge=300, le=5000)
    dwell_radius_px: int = Field(default=30, ge=10, le=100)
    dwell_show_progress: bool = True
    
    # Pinch click
    pinch_click_enabled: bool = True
    pinch_hold_time_ms: int = Field(default=500, ge=200, le=2000)
    
    # Mouth click
    mouth_click_enabled: bool = False
    mouth_open_threshold: float = Field(default=0.5, ge=0.3, le=0.8)
    
    # Double click
    double_click_interval_ms: int = Field(default=300, ge=100, le=500)


class SmoothingConfig(BaseModel):
    """Configuration for cursor smoothing and stabilization."""
    
    enabled: bool = True
    smoothing_factor: float = Field(default=0.7, ge=0.0, le=0.99)
    dead_zone_px: int = Field(default=5, ge=0, le=30)
    
    # Kalman filter settings
    use_kalman: bool = True
    kalman_process_noise: float = Field(default=0.03, ge=0.001, le=0.1)
    kalman_measurement_noise: float = Field(default=0.1, ge=0.01, le=1.0)
    
    # Velocity-based smoothing
    velocity_adaptive: bool = True
    velocity_threshold_low: float = Field(default=50.0, ge=10.0, le=200.0)
    velocity_threshold_high: float = Field(default=500.0, ge=100.0, le=1000.0)


class CameraConfig(BaseModel):
    """Configuration for camera settings."""
    
    camera_index: int = Field(default=0, ge=0)
    camera_width: int = Field(default=1280, ge=320)
    camera_height: int = Field(default=720, ge=240)
    target_fps: int = Field(default=30, ge=15, le=120)
    auto_exposure: bool = True
    auto_focus: bool = True
    flip_horizontal: bool = True  # Mirror mode
    
    # Buffer settings
    buffer_size: int = Field(default=1, ge=1, le=5)
    
    # Warmup
    warmup_frames: int = Field(default=30, ge=0, le=120)


class UIConfig(BaseModel):
    """Configuration for user interface."""
    
    show_gui: bool = True
    show_overlay: bool = True
    show_preview: bool = True
    preview_scale: float = Field(default=0.5, ge=0.25, le=1.0)
    
    theme: str = Field(default="dark", pattern="^(dark|light|system)$")
    
    start_minimized: bool = False
    minimize_to_tray: bool = True
    show_notifications: bool = True
    
    # Overlay settings
    overlay_opacity: float = Field(default=0.8, ge=0.1, le=1.0)
    overlay_position: str = Field(default="bottom-right", 
                                   pattern="^(top-left|top-right|bottom-left|bottom-right)$")
    
    # Visual feedback
    show_tracking_points: bool = True
    show_gaze_point: bool = True
    show_hand_skeleton: bool = True
    cursor_trail: bool = False
    
    # Accessibility
    high_contrast: bool = False
    large_ui: bool = False
    
    # Audio feedback
    audio_feedback: bool = True
    click_sound: bool = True


class PerformanceConfig(BaseModel):
    """Configuration for performance optimization."""
    
    max_fps: int = Field(default=60, ge=15, le=120)
    frame_skip_threshold: int = Field(default=15, ge=5, le=30)
    resolution_scale: float = Field(default=1.0, ge=0.5, le=1.0)
    
    # Threading
    use_threading: bool = True
    thread_count: int = Field(default=4, ge=1, le=16)
    
    # GPU acceleration
    use_gpu: bool = False
    gpu_device: int = Field(default=0, ge=0)
    
    # Caching
    cache_landmarks: bool = True
    cache_size: int = Field(default=10, ge=1, le=100)
    
    # Power saving
    power_save_mode: bool = False
    idle_timeout_sec: int = Field(default=300, ge=60, le=3600)


class CalibrationConfig(BaseModel):
    """Configuration for calibration."""
    
    auto_calibration: bool = False
    calibration_points: int = Field(default=9, ge=4, le=16)
    calibration_dwell_time_ms: int = Field(default=2000, ge=1000, le=5000)
    
    # Calibration validation
    validation_points: int = Field(default=4, ge=2, le=9)
    max_validation_error_px: int = Field(default=50, ge=20, le=150)
    
    # Calibration data storage
    save_calibration: bool = True
    calibration_file: str = "calibration.json"
    
    # Recalibration triggers
    auto_recalibrate: bool = False
    recalibrate_threshold: float = Field(default=0.3, ge=0.1, le=0.5)


class KursorinConfig(BaseModel):
    """Main configuration class for KURSORIN."""
    
    # Sub-configurations
    tracking: TrackingConfig = Field(default_factory=TrackingConfig)
    fusion: FusionConfig = Field(default_factory=FusionConfig)
    click: ClickConfig = Field(default_factory=ClickConfig)
    smoothing: SmoothingConfig = Field(default_factory=SmoothingConfig)
    camera: CameraConfig = Field(default_factory=CameraConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    calibration: CalibrationConfig = Field(default_factory=CalibrationConfig)
    
    # General settings
    debug_mode: bool = False
    data_directory: str = "~/.kursorin"
    
    # Convenience properties to access nested config
    @property
    def head_enabled(self) -> bool:
        return self.tracking.head_enabled
    
    @head_enabled.setter
    def head_enabled(self, value: bool):
        self.tracking.head_enabled = value
    
    @property
    def eye_enabled(self) -> bool:
        return self.tracking.eye_enabled
    
    @eye_enabled.setter
    def eye_enabled(self, value: bool):
        self.tracking.eye_enabled = value
    
    @property
    def hand_enabled(self) -> bool:
        return self.tracking.hand_enabled
    
    @hand_enabled.setter
    def hand_enabled(self, value: bool):
        self.tracking.hand_enabled = value
    
    @property
    def camera_index(self) -> int:
        return self.camera.camera_index
    
    @camera_index.setter
    def camera_index(self, value: int):
        self.camera.camera_index = value
    
    @property
    def camera_width(self) -> int:
        return self.camera.camera_width
    
    @camera_width.setter
    def camera_width(self, value: int):
        self.camera.camera_width = value
    
    @property
    def camera_height(self) -> int:
        return self.camera.camera_height
    
    @camera_height.setter
    def camera_height(self, value: int):
        self.camera.camera_height = value
    
    @property
    def target_fps(self) -> int:
        return self.camera.target_fps
    
    @target_fps.setter
    def target_fps(self, value: int):
        self.camera.target_fps = value
    
    @property
    def show_gui(self) -> bool:
        return self.ui.show_gui
    
    @show_gui.setter
    def show_gui(self, value: bool):
        self.ui.show_gui = value
    
    @property
    def show_overlay(self) -> bool:
        return self.ui.show_overlay
    
    @show_overlay.setter
    def show_overlay(self, value: bool):
        self.ui.show_overlay = value
    
    @property
    def show_preview(self) -> bool:
        return self.ui.show_preview
    
    @show_preview.setter
    def show_preview(self, value: bool):
        self.ui.show_preview = value
    
    @property
    def theme(self) -> str:
        return self.ui.theme
    
    @theme.setter
    def theme(self, value: str):
        self.ui.theme = value
    
    @property
    def start_minimized(self) -> bool:
        return self.ui.start_minimized
    
    @start_minimized.setter
    def start_minimized(self, value: bool):
        self.ui.start_minimized = value
    
    @property
    def smoothing_factor(self) -> float:
        return self.smoothing.smoothing_factor
    
    @smoothing_factor.setter
    def smoothing_factor(self, value: float):
        self.smoothing.smoothing_factor = value
    
    def get_data_path(self) -> Path:
        """Get the data directory path, creating it if necessary."""
        path = Path(self.data_directory).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @classmethod
    def from_file(cls, path: Union[str, Path]) -> "KursorinConfig":
        """Load configuration from a file (YAML or JSON)."""
        path = Path(path)
        
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")
        
        with open(path, "r") as f:
            if path.suffix in (".yaml", ".yml"):
                data = yaml.safe_load(f)
            elif path.suffix == ".json":
                data = json.load(f)
            else:
                raise ValueError(f"Unsupported configuration format: {path.suffix}")
        
        return cls(**data)
    
    def to_file(self, path: Union[str, Path]) -> None:
        """Save configuration to a file (YAML or JSON)."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        data = self.dict()
        
        with open(path, "w") as f:
            if path.suffix in (".yaml", ".yml"):
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            elif path.suffix == ".json":
                json.dump(data, f, indent=2)
            else:
                raise ValueError(f"Unsupported configuration format: {path.suffix}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return self.dict()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KursorinConfig":
        """Create configuration from dictionary."""
        return cls(**data)
    
    def merge_with(self, other: "KursorinConfig") -> "KursorinConfig":
        """Merge this configuration with another, other takes precedence."""
        self_dict = self.dict()
        other_dict = other.dict()
        
        def deep_merge(base: dict, override: dict) -> dict:
            result = base.copy()
            for key, value in override.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result
        
        merged = deep_merge(self_dict, other_dict)
        return KursorinConfig(**merged)
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True
        extra = "forbid"


# Default configuration instance
DEFAULT_CONFIG = KursorinConfig()


def load_config(
    config_path: Optional[Union[str, Path]] = None,
    env_prefix: str = "KURSORIN_"
) -> KursorinConfig:
    """
    Load configuration from multiple sources with priority:
    1. Explicit config file (if provided)
    2. Environment variables
    3. User config file (~/.kursorin/config.yaml)
    4. Default values
    """
    config = KursorinConfig()
    
    # Load from user config file if exists
    user_config_path = Path.home() / ".kursorin" / "config.yaml"
    if user_config_path.exists():
        try:
            user_config = KursorinConfig.from_file(user_config_path)
            config = config.merge_with(user_config)
        except Exception:
            pass
    
    # Load from explicit config file
    if config_path:
        file_config = KursorinConfig.from_file(config_path)
        config = config.merge_with(file_config)
    
    # Override from environment variables
    # Example: KURSORIN_TRACKING__HEAD_ENABLED=false
    for key, value in os.environ.items():
        if key.startswith(env_prefix):
            config_key = key[len(env_prefix):].lower()
            # Handle nested keys (using __ as separator)
            # Implementation would set nested values
            pass
    
    return config
