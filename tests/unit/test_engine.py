"""
Tests for Kursorin Engine
"""

import pytest
from unittest.mock import MagicMock, patch
from kursorin.constants import TrackingState


def test_engine_initialization(engine):
    assert engine.state == TrackingState.IDLE
    assert not engine.is_running


@patch("kursorin.core.kursorin_engine.CameraManager")
@patch("kursorin.core.kursorin_engine.HeadTracker")
@patch("kursorin.core.kursorin_engine.EyeTracker")
@patch("kursorin.core.kursorin_engine.HandTracker")
def test_engine_start_stop(mock_hand, mock_eye, mock_head, mock_camera, engine):
    # Mock components
    engine._camera = MagicMock()
    engine._head_tracker = MagicMock()
    
    # Start
    engine.start()
    assert engine.is_running
    assert engine.state == TrackingState.TRACKING
    
    # Stop
    engine.stop()
    assert not engine.is_running
    assert engine.state == TrackingState.IDLE
