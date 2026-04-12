"""HybridRecorder 集成测试"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestHybridRecorder:
    """HybridRecorder 测试"""
    
    def test_recorder_creation(self):
        from src.recording.hybrid_recorder import HybridRecorder
        from src.core.models import RecordingMode
        
        recorder = HybridRecorder(mode=RecordingMode.HYBRID)
        assert recorder.mode == RecordingMode.HYBRID
        assert recorder.is_recording is False
    
    def test_recorder_lifecycle(self):
        from src.recording.hybrid_recorder import HybridRecorder
        from src.core.models import RecordingMode
        
        recorder = HybridRecorder(mode=RecordingMode.DESKTOP)
        
        # 开始录制
        recorder.start_recording("test_session")
        assert recorder.is_recording is True
        
        # 停止录制
        session = recorder.stop_recording()
        assert recorder.is_recording is False
        assert session.name == "test_session"
