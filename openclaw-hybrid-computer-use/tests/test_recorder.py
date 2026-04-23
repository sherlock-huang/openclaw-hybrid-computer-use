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
        """测试转换为 TaskSequence - 优先使用坐标"""
        from src.core.models import RecordingSession, RecordingEvent
        
        events = [
            # 有坐标时应该使用坐标作为target
            RecordingEvent(action="click", timestamp=0.5, target="button_1", position=(100, 200)),
            # 没有坐标时才使用元素ID
            RecordingEvent(action="click", timestamp=1.0, target="button_2"),
            RecordingEvent(action="type", timestamp=2.0, value="hello")
        ]
        
        session = RecordingSession(
            name="Test Session",
            start_time=datetime.now(),
            events=events
        )
        
        sequence = session.to_task_sequence()
        
        assert sequence.name == "Test Session"
        assert len(sequence.tasks) == 3
        # 有坐标时优先使用坐标
        assert sequence.tasks[0].action == "click"
        assert sequence.tasks[0].target == "100,200", "应该优先使用坐标而非元素ID"
        # 没有坐标时才用元素ID
        assert sequence.tasks[1].action == "click"
        assert sequence.tasks[1].target == "button_2"
        assert sequence.tasks[2].action == "type"
        assert sequence.tasks[2].value == "hello"
    
    def test_save_to_file_includes_metadata(self, tmp_path):
        """测试保存文件包含metadata"""
        from src.core.models import RecordingSession, RecordingEvent
        import json
        
        events = [
            RecordingEvent(action="click", timestamp=0.5, target="button_1", 
                         position=(100, 200), element_type="button"),
        ]
        
        session = RecordingSession(
            name="Test Session",
            start_time=datetime.now(),
            events=events
        )
        
        filepath = tmp_path / "test_recording.json"
        session.save_to_file(str(filepath))
        
        # 读取并验证
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data["name"] == "Test Session"
        assert len(data["tasks"]) == 1
        task = data["tasks"][0]
        # target 应该是坐标
        assert task["target"] == "100,200"
        # 包含metadata
        assert "_metadata" in task
        assert task["_metadata"]["element_id"] == "button_1"
        assert task["_metadata"]["element_type"] == "button"
        assert task["_metadata"]["recorded_position"] == [100, 200]


class TestTaskRecorder:
    """TaskRecorder 测试"""
    
    def test_recorder_lifecycle(self):
        """Test recorder start/stop lifecycle"""
        from src.core.recorder import TaskRecorder
        
        recorder = TaskRecorder()
        
        # 初始状态
        assert recorder.is_recording == False
        
        # 开始录制
        recorder.start_recording("test_session")
        assert recorder.is_recording == True
        assert len(recorder._events) == 0
        
        # 停止录制
        session = recorder.stop_recording()
        assert recorder.is_recording == False
        assert session is not None
        assert session.name == "test_session"
    
    def test_recorder_duplicate_start_raises(self):
        """Test that starting twice raises error"""
        from src.core.recorder import TaskRecorder
        import pytest
        
        recorder = TaskRecorder()
        recorder.start_recording()
        
        with pytest.raises(RuntimeError):
            recorder.start_recording()
        
        recorder.stop_recording()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
