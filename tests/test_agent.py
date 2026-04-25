"""ComputerUseAgent 单元测试"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.agent import ComputerUseAgent
from src.core.models import Task, TaskSequence, ExecutionResult


class TestComputerUseAgent:
    """测试 ComputerUseAgent 主类"""

    @patch("src.core.agent.setup_logger")
    @patch("src.core.agent.TaskExecutor")
    def test_initialization(self, mock_executor_cls, mock_setup_logger):
        """Agent 初始化应创建 Config 和 TaskExecutor"""
        agent = ComputerUseAgent()
        assert agent.config is not None
        mock_executor_cls.assert_called_once_with(agent.config)
        assert agent.executor is mock_executor_cls.return_value

    @patch("src.core.agent.setup_logger")
    @patch("src.core.agent.TaskExecutor")
    def test_execute(self, mock_executor_cls, mock_setup_logger):
        """execute 应委托给 executor.execute"""
        agent = ComputerUseAgent()
        mock_executor = mock_executor_cls.return_value
        mock_executor.execute.return_value = ExecutionResult(
            success=True, completed_steps=2, duration=1.0
        )

        sequence = TaskSequence("test_seq", [Task("wait", delay=0)])
        result = agent.execute(sequence)

        mock_executor.execute.assert_called_once_with(sequence)
        assert result.success is True

    @patch("src.core.agent.setup_logger")
    @patch("src.core.agent.TaskExecutor")
    @patch("src.core.agent.get_predefined_task")
    def test_execute_task(self, mock_get_task, mock_executor_cls, mock_setup_logger):
        """execute_task 应获取预定义任务后执行"""
        agent = ComputerUseAgent()
        mock_executor = mock_executor_cls.return_value
        mock_executor.execute.return_value = ExecutionResult(
            success=True, completed_steps=1, duration=0.5
        )

        expected_seq = TaskSequence("notepad", [Task("click", target="100,100")])
        mock_get_task.return_value = expected_seq

        result = agent.execute_task("notepad", text="Hello")

        mock_get_task.assert_called_once_with("notepad", text="Hello")
        mock_executor.execute.assert_called_once_with(expected_seq)
        assert result.success is True

    @patch("src.core.agent.setup_logger")
    @patch("src.core.agent.TaskExecutor")
    def test_detect_screen(self, mock_executor_cls, mock_setup_logger):
        """detect_screen 应返回元素检测结果"""
        agent = ComputerUseAgent()
        mock_executor = mock_executor_cls.return_value

        # Mock screen capture
        fake_screenshot = MagicMock()
        fake_screenshot.shape = (1080, 1920, 3)
        mock_executor.screen.capture.return_value = fake_screenshot

        # Mock detector
        mock_element = MagicMock()
        mock_element.to_dict.return_value = {"id": 1, "type": "button"}
        mock_executor.detector.detect.return_value = [mock_element]

        result = agent.detect_screen()

        assert result["element_count"] == 1
        assert result["elements"] == [{"id": 1, "type": "button"}]

    @patch("src.core.agent.setup_logger")
    @patch("src.core.agent.TaskExecutor")
    @patch("src.core.agent.list_predefined_tasks")
    def test_list_tasks(self, mock_list_tasks, mock_executor_cls, mock_setup_logger):
        """list_tasks 应返回预定义任务列表"""
        agent = ComputerUseAgent()
        mock_list_tasks.return_value = [
            {"name": "calculator", "description": "计算器"},
            {"name": "notepad", "description": "记事本"},
        ]

        tasks = agent.list_tasks()

        assert len(tasks) == 2
        assert tasks[0]["name"] == "calculator"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
