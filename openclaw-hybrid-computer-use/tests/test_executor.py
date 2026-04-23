"""任务执行引擎测试"""

import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import (
    TaskExecutor,
    Task,
    TaskSequence,
)
from src.core.models import ExecutionState


class TestExecutionState:
    """测试执行状态管理"""
    
    def test_initial_state(self):
        """测试初始状态"""
        state = ExecutionState()
        assert state.status == "idle"
        assert state.current_step == 0
    
    def test_start_execution(self):
        """测试开始执行"""
        state = ExecutionState()
        sequence = TaskSequence("test", [Task("wait", delay=0)])
        
        state.start(sequence)
        
        assert state.status == "running"
        assert state.sequence == sequence
        assert state.start_time is not None
    
    def test_complete_execution(self):
        """测试完成执行"""
        state = ExecutionState()
        sequence = TaskSequence("test", [])
        
        state.start(sequence)
        result = state.complete()
        
        assert result.success is True
        assert state.status == "success"
    
    def test_fail_execution(self):
        """测试失败执行"""
        state = ExecutionState()
        sequence = TaskSequence("test", [])
        
        state.start(sequence)
        result = state.fail("test error")
        
        assert result.success is False
        assert result.error == "test error"
        assert state.status == "failed"


class TestTaskExecutor:
    """测试任务执行器"""
    
    def test_executor_initialization(self):
        """测试执行器初始化"""
        executor = TaskExecutor()
        
        assert executor.screen is not None
        assert executor.mouse is not None
        assert executor.keyboard is not None
    
    def test_execute_wait_task(self):
        """测试执行等待任务"""
        executor = TaskExecutor()
        sequence = TaskSequence("wait_test", [
            Task("wait", delay=0.1)
        ])
        
        result = executor.execute(sequence)
        
        assert result.success is True
        assert result.completed_steps >= 1


class TestTaskExecutorLearningIntegration:
    """测试任务执行器与学习系统集成"""
    
    def test_apply_learned_delay(self, monkeypatch, tmp_path):
        """测试自动应用学习到的 delay"""
        import tempfile
        import json
        from pathlib import Path
        
        # 创建临时学习文件，模拟高成功率记录
        learn_file = tmp_path / "task_patterns.json"
        data = {
            "wait:": {
                "task_type": "wait",
                "target_signature": "",
                "actions": [],
                "success_count": 10,
                "fail_count": 0,
                "last_used": 0,
                "avg_duration": 0.5,
                "optimal_delay": 0.5,
                "environment_key": "1920x1080_default",
                "strategy_hints": {}
            }
        }
        learn_file.write_text(json.dumps(data), encoding="utf-8")
        
        from src.core.task_learner import TaskLearner
        original_file = TaskLearner.LEARN_FILE
        TaskLearner.LEARN_FILE = str(learn_file)
        
        try:
            executor = TaskExecutor()
            sequence = TaskSequence("learn_test", [
                Task("wait", delay=1.0)
            ])
            
            result = executor.execute(sequence)
            assert result.success is True
            # 高成功率应缩短 delay 到 0.6
        finally:
            TaskLearner.LEARN_FILE = original_file


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
