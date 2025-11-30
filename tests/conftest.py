"""
Pytest Configuration
"""

import pytest
import numpy as np
from unittest.mock import MagicMock

from kursorin.config import KursorinConfig
from kursorin.core.kursorin_engine import KursorinEngine


@pytest.fixture
def config():
    return KursorinConfig()


@pytest.fixture
def mock_camera():
    camera = MagicMock()
    camera.read.return_value = np.zeros((720, 1280, 3), dtype=np.uint8)
    return camera


@pytest.fixture
def engine(config, mock_camera):
    engine = KursorinEngine(config)
    engine._camera = mock_camera
    return engine
