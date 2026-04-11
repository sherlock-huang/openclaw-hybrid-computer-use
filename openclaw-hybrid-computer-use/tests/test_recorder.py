"""TaskRecorder 测试"""

import pytest
from datetime import datetime
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestRecordingEvent:
    """RecordingEvent 测试"""
    
    def test_recording_event_creation(self):
        """测试创建 RecordingEvent"""
        from src.core.models import RecordingEvent
        
        event = RecordingEvent(
            action="click",
            timestamp=1.5,
            target="elem_001",
            position=(100, 200),
            element_type="button"
        )
        
        assert event.action == "click"
        assert event.timestamp == 1.5
        assert event.target == "elem_001"
        assert event.position == (100, 200)
        assert event.element_type == "button"
    
    def test_recording_event_to_dict(self):
        """测试 RecordingEvent 序列化"""
        from src.core.models import RecordingEvent
        
        event = RecordingEvent(
            action="type",
            timestamp=2.0,
            value="Hello World"
        )
        
        data = event.to_dict()
        assert data["action"] == "type"
        assert data["value"] == "Hello World"
        assert data["timestamp"] == 2.0


class TestRecordingSession:
    """RecordingSession 测试"""
    
    def test_session_creation(self):
        """测试创建 RecordingSession"""
        from src.core.models import RecordingSession, RecordingEvent
        
        events = [
            RecordingEvent(action="click", timestamp=0.5),
            RecordingEvent(action="type", timestamp=1.0, value="test")
        ]
        
        session = RecordingSession(
            name="Test Session",
            start_time=datetime.now(),
            events=events
        )
        
        assert session.name == "Test Session"
        assert len(session.events) == 2
    
    def test_session_to_task_sequence(self):
        """测试转换为 TaskSequence"""
        from src.core.models import RecordingSession, RecordingEvent
        
        events = [
            RecordingEvent(action="click", timestamp=0.5, target="button_1"),
            RecordingEvent(action="type", timestamp=1.0, value="hello")
        ]
        
        session = RecordingSession(
            name="Test Session",
            start_time=datetime.now(),
            events=events
        )
        
        sequence = session.to_task_sequence()
        
        assert sequence.name == "Test Session"
        assert len(sequence.tasks) == 2
        assert sequence.tasks[0].action == "click"
        assert sequence.tasks[0].target == "button_1"
        assert sequence.tasks[1].action == "type"
        assert sequence.tasks[1].value == "hello"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
