"""
Tests for Configuration
"""

import pytest
from kursorin.config import KursorinConfig


def test_default_config():
    config = KursorinConfig()
    assert config.tracking.head_enabled is True
    assert config.tracking.eye_enabled is True
    assert config.tracking.hand_enabled is True
    assert config.camera.target_fps == 30


def test_config_validation():
    config = KursorinConfig()
    
    # Valid update
    config.tracking.head_sensitivity_x = 3.0
    assert config.tracking.head_sensitivity_x == 3.0
    
    # Invalid update (should raise error)
    with pytest.raises(ValueError):
        config.tracking.head_sensitivity_x = 10.0  # Max is 5.0
