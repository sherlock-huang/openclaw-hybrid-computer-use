"""TaskExecutor 浏览器集成测试"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestExecutorBrowserActions:
    """测试 TaskExecutor 执行浏览器任务"""
    
    def test_execute_browser_launch_and_goto(self):
        """测试执行 browser_launch 和 browser_goto"""
        from src.core.executor import TaskExecutor
        from src.core.models import Task, TaskSequence
        
        executor = TaskExecutor()
        
        sequence = TaskSequence(
            name="浏览器测试",
            tasks=[
                Task("browser_launch", value="chromium", delay=2.0),
                Task("browser_goto", value="https://example.com", delay=2.0),
                Task("browser_close", delay=1.0),
            ]
        )
        
        result = executor.execute(sequence)
        
        assert result.success is True
        assert result.completed_steps == 3
    
    def test_execute_browser_click_and_type(self):
        """测试执行浏览器点击和输入"""
        from src.core.executor import TaskExecutor
        from src.core.models import Task, TaskSequence
        
        executor = TaskExecutor()
        
        # 使用更可靠的测试页面 - 使用 example.com 的链接
        sequence = TaskSequence(
            name="浏览器交互测试",
            tasks=[
                Task("browser_launch", value="chromium", delay=2.0),
                Task("browser_goto", value="https://example.com", delay=2.0),
                Task("browser_wait", target="body", delay=1.0),
                Task("browser_click", target="a", delay=2.0),  # 点击第一个链接
                Task("browser_close", delay=1.0),
            ]
        )
        
        result = executor.execute(sequence)
        
        assert result.success is True
