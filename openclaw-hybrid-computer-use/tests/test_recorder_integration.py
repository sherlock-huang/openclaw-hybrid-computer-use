"""录制器集成测试"""

import pytest
import json
import tempfile
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestRecorderIntegration:
    """录制器集成测试"""
    
    def test_record_and_save(self):
        """测试录制并保存文件"""
        from src.core.recorder import TaskRecorder
        from datetime import datetime
        from src.core.models import RecordingSession, RecordingEvent
        
        # 创建录制会话（直接构造，避免实际录制）
        session = RecordingSession(
            name="integration_test",
            start_time=datetime.now(),
            events=[
                RecordingEvent(action="click", timestamp=0.5, target="button_1"),
                RecordingEvent(action="type", timestamp=1.0, value="hello")
            ]
        )
        
        # 保存到临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name
        
        try:
            session.save_to_file(filepath)
            
            # 验证文件存在且内容正确
            assert os.path.exists(filepath)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert data['name'] == "integration_test"
            assert 'tasks' in data
            assert len(data['tasks']) == 2
            
            # 验证第一个任务是点击
            assert data['tasks'][0]['action'] == 'click'
            assert data['tasks'][0]['target'] == 'button_1'
            
            # 验证第二个任务是输入
            assert data['tasks'][1]['action'] == 'type'
            assert data['tasks'][1]['value'] == 'hello'
            
        finally:
            os.unlink(filepath)
    
    def test_task_sequence_conversion(self):
        """测试 TaskSequence 转换"""
        from src.core.models import RecordingSession, RecordingEvent, TaskSequence
        from datetime import datetime
        
        session = RecordingSession(
            name="conversion_test",
            start_time=datetime.now(),
            events=[
                RecordingEvent(action="click", timestamp=0.5, target="elem_001"),
                RecordingEvent(action="type", timestamp=1.0, value="test input"),
                RecordingEvent(action="press", timestamp=2.0, value="enter")
            ]
        )
        
        sequence = session.to_task_sequence()
        
        assert isinstance(sequence, TaskSequence)
        assert sequence.name == "conversion_test"
        assert len(sequence.tasks) == 3
        
        # 验证任务属性
        assert sequence.tasks[0].action == "click"
        assert sequence.tasks[0].target == "elem_001"
        
        assert sequence.tasks[1].action == "type"
        assert sequence.tasks[1].value == "test input"
        
        assert sequence.tasks[2].action == "press"
        assert sequence.tasks[2].value == "enter"
    
    def test_coordinate_fallback(self):
        """测试坐标 fallback（当元素检测失败时）"""
        from src.core.models import RecordingSession, RecordingEvent
        from datetime import datetime
        
        session = RecordingSession(
            name="coordinate_test",
            start_time=datetime.now(),
            events=[
                RecordingEvent(action="click", timestamp=0.5, position=(100, 200))
            ]
        )
        
        sequence = session.to_task_sequence()
        
        # 当 target 为 None 但有 position 时，应该使用坐标
        assert sequence.tasks[0].target == "100,200"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
