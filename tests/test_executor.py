"""任务执行引擎测试"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import (
    TaskExecutor,
    Task,
    TaskSequence,
)
from src.core.models import ExecutionState
from src.core.recovery_strategy import RecoveryResult


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


class TestTaskExecutorFailurePaths:
    """测试 TaskExecutor 的失败和异常路径"""

    def test_execute_empty_sequence(self):
        """空任务序列应直接成功完成"""
        executor = TaskExecutor()
        sequence = TaskSequence("empty", tasks=[])

        result = executor.execute(sequence)

        assert result.success is True
        assert result.completed_steps == 0

    def test_execute_task_failure_exhausts_retries(self):
        """任务持续失败、重试用尽后序列应标记为失败"""
        executor = TaskExecutor()
        # 将 max_retries 设为 0，失败后立即终止
        executor.config.max_retries = 0

        sequence = TaskSequence("fail_test", [
            Task("nonexistent_action_that_will_fail"),
        ])

        result = executor.execute(sequence)

        assert result.success is False
        assert result.error is not None

    def test_execute_catches_claw_desktop_error(self):
        """ClawDesktopError 应被捕获并转为失败结果"""
        executor = TaskExecutor()
        from src.utils.exceptions import ValidationError

        # Mock _execute_single_task 抛出 ValidationError
        executor._execute_single_task = MagicMock(
            side_effect=ValidationError("Invalid task configuration")
        )

        sequence = TaskSequence("error_test", [
            Task("browser_goto", value="invalid"),
        ])

        result = executor.execute(sequence)

        assert result.success is False
        assert "Invalid task configuration" in result.error

    def test_execute_catches_unexpected_exception(self):
        """未预期的异常应被捕获并转为失败结果"""
        executor = TaskExecutor()
        executor._execute_single_task = MagicMock(
            side_effect=RuntimeError("Something went wrong")
        )
        # 禁用 Self-Healing 修复，确保异常被正确捕获
        executor.recovery_strategy.attempt_recovery = MagicMock(
            return_value=RecoveryResult(success=False)
        )

        sequence = TaskSequence("unexpected", [
            Task("click", target="100,100"),
        ])

        result = executor.execute(sequence)

        assert result.success is False
        assert "Something went wrong" in result.error

    def test_handle_failure_retries(self):
        """_handle_failure 在重试次数内返回 True"""
        executor = TaskExecutor()
        executor.config.max_retries = 3
        executor.config.retry_delay = 0.01  # 缩短等待时间

        task = Task("click", target="100,100")
        # retry_count=0 < max_retries=3，应返回 True
        assert executor._handle_failure(task, 0) is True
        assert executor._handle_failure(task, 1) is True
        assert executor._handle_failure(task, 2) is True
        # retry_count=3 >= max_retries=3，应返回 False
        assert executor._handle_failure(task, 3) is False

    def test_execute_partial_failure(self):
        """序列中部分任务失败后应停止并记录已完成步骤"""
        executor = TaskExecutor()
        executor.config.max_retries = 0
        # 禁用 Self-Healing 修复，确保部分失败后停止
        executor.recovery_strategy.attempt_recovery = MagicMock(
            return_value=RecoveryResult(success=False)
        )

        call_count = 0

        def side_effect(task, screenshot):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                return False  # 第二个任务失败
            return True

        executor._execute_single_task = MagicMock(side_effect=side_effect)

        sequence = TaskSequence("partial", [
            Task("wait", delay=0),
            Task("click", target="100,100"),
            Task("wait", delay=0),
        ])

        result = executor.execute(sequence)

        assert result.success is False
        # 第一个任务成功，第二个失败，序列终止
        # current_step 在任务执行前设为 i+1，所以失败时 completed_steps=2
        assert result.completed_steps == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
