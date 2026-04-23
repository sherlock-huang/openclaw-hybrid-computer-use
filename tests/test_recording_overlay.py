"""录制指示器 UI 测试"""

import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_overlay_initial_state():
    """Test overlay initial state"""
    from src.utils.recording_overlay import RecordingOverlay
    
    overlay = RecordingOverlay()
    assert overlay.is_recording == False
    assert overlay.elapsed_time == 0
    assert overlay.root is None


def test_overlay_has_required_methods():
    """Test that required methods exist"""
    from src.utils.recording_overlay import RecordingOverlay
    
    overlay = RecordingOverlay()
    assert hasattr(overlay, 'show')
    assert hasattr(overlay, 'hide')
    assert hasattr(overlay, '_update_timer')
