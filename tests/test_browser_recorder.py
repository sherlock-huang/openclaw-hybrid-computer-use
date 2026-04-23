"""BrowserRecorder 测试"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestBrowserRecorder:
    """BrowserRecorder 测试类"""
    
    def test_recorder_creation(self):
        from src.recording.browser_recorder import BrowserRecorder
        recorder = BrowserRecorder(user_data_dir="browser_data")
        assert recorder.user_data_dir == "browser_data"
        assert recorder.is_connected is False
