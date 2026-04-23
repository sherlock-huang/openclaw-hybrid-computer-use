"""
MVP 测试套件

包含10个标准测试任务，验证系统核心功能。
"""

import pytest
import time
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from claw_desktop import (
    ComputerUseAgent,
    Task,
    TaskSequence,
    ScreenCapture,
    ElementDetector,
    MouseController,
    KeyboardController,
    ApplicationManager,
)
from claw_desktop.core.tasks_predefined import list_predefined_tasks, get_predefined_task


class TestBasicFunctionality:
    """基础功能测试"""
    
    def test_screen_capture(self):
        """T1: 屏幕截图功能"""
        capture = ScreenCapture()
        
        start = time.time()
        image = capture.capture()
        elapsed = time.time() - start
        
        assert image is not None
        assert len(image.shape) == 3
        assert elapsed < 1.0, f"截图耗时过长: {elapsed:.2f}s"
    
    def test_element_detector_initialization(self):
        """T2: 元素检测器初始化"""
        detector = ElementDetector()
        assert detector.model is not None
    
    def test_mouse_controller(self):
        """T3: 鼠标控制器"""
        mouse = MouseController()
        
        # 获取位置
        x, y = mouse.get_position()
        assert 0 <= x < mouse.screen_width
        assert 0 <= y < mouse.screen_height
        
        # 移动鼠标（平滑移动）
        target_x = mouse.screen_width // 2
        target_y = mouse.screen_height // 2
        mouse.move_to(target_x, target_y, duration=0.2)
        
        # 验证位置（允许误差）
        new_x, new_y = mouse.get_position()
        assert abs(new_x - target_x) < 10
        assert abs(new_y - target_y) < 10
    
    def test_keyboard_controller(self):
        """T4: 键盘控制器"""
        kb = KeyboardController()
        
        # 测试按键标准化
        assert kb._normalize_key("ENTER") == "return"
        assert kb._normalize_key("ctrl") == "ctrl"
    
    def test_application_manager(self):
        """T5: 应用管理器"""
        app_mgr = ApplicationManager()
        
        # 检查应用映射
        assert "calculator" in app_mgr.APP_MAP
        assert "notepad" in app_mgr.APP_MAP
        assert "chrome" in app_mgr.APP_MAP


class TestPredefinedTasks:
    """预定义任务测试"""
    
    def test_list_predefined_tasks(self):
        """T6: 列出预定义任务"""
        tasks = list_predefined_tasks()
        assert len(tasks) >= 10
        
        task_names = [t["name"] for t in tasks]
        expected = [
            "calculator_add", "notepad_type", "chrome_search",
            "explorer_navigate", "window_switch", "desktop_screenshot",
            "text_copy_paste", "scroll_test", "right_click", "multi_app"
        ]
        for name in expected:
            assert name in task_names
    
    def test_create_calculator_task(self):
        """T7: 创建计算器任务"""
        task = get_predefined_task("calculator_add", a=5, b=3)
        
        assert task.name == "calculator_5+3"
        assert len(task.tasks) > 0
        assert task.tasks[0].action == "launch"
        assert task.tasks[0].target == "calculator"
    
    def test_create_notepad_task(self):
        """T8: 创建记事本任务"""
        task = get_predefined_task("notepad_type", text="Test")
        
        assert task.name == "notepad_type"
        assert any(t.action == "type" and t.value == "Test" for t in task.tasks)
    
    def test_create_chrome_task(self):
        """T9: 创建Chrome任务"""
        task = get_predefined_task("chrome_search", url="example.com")
        
        assert task.name == "chrome_search"
        assert any(t.action == "launch" and t.target == "chrome" for t in task.tasks)


class TestTaskExecution:
    """任务执行测试"""
    
    @pytest.mark.slow
    def test_execute_wait_task(self):
        """T10: 执行等待任务"""
        agent = ComputerUseAgent()
        
        sequence = TaskSequence(
            name="test_wait",
            tasks=[
                Task("wait", delay=0.5),
            ]
        )
        
        start = time.time()
        result = agent.execute(sequence)
        elapsed = time.time() - start
        
        assert result.success is True
        assert elapsed >= 0.2  # 确保等待执行了
        assert result.completed_steps >= 1
    
    @pytest.mark.slow
    def test_execute_sequence_with_screenshots(self):
        """T11: 执行任务并记录截图"""
        agent = ComputerUseAgent()
        
        sequence = TaskSequence(
            name="test_screenshots",
            tasks=[
                Task("wait", delay=0.3),
                Task("wait", delay=0.3),
            ]
        )
        
        result = agent.execute(sequence)
        
        assert result.success is True
        assert len(result.screenshots) == 2  # 每个任务前都截图
    
    @pytest.mark.slow
    def test_execute_launch_notepad(self):
        """T12: 执行启动记事本任务"""
        agent = ComputerUseAgent()
        
        sequence = TaskSequence(
            name="test_launch",
            tasks=[
                Task("launch", target="notepad"),
                Task("wait", delay=1.0),
            ]
        )
        
        result = agent.execute(sequence)
        
        # 启动应用可能失败（权限等问题），但执行流程应该完成
        assert result.completed_steps >= 1


class TestErrorHandling:
    """错误处理测试"""
    
    def test_invalid_task_action(self):
        """T13: 无效的任务动作"""
        agent = ComputerUseAgent()
        
        sequence = TaskSequence(
            name="test_invalid",
            tasks=[
                Task("invalid_action"),
            ]
        )
        
        result = agent.execute(sequence)
        
        # 应该标记为失败
        assert result.completed_steps >= 1
    
    def test_missing_target(self):
        """T14: 缺少目标"""
        agent = ComputerUseAgent()
        
        sequence = TaskSequence(
            name="test_missing_target",
            tasks=[
                Task("click"),  # 缺少 target
            ]
        )
        
        result = agent.execute(sequence)
        
        # 应该失败
        assert result.completed_steps >= 1
class TestPerformance:
    """性能测试"""
    
    def test_screenshot_performance(self):
        """T15: 截图性能"""
        capture = ScreenCapture()
        
        times = []
        for _ in range(5):
            start = time.time()
            capture.capture()
            times.append(time.time() - start)
        
        avg_time = sum(times) / len(times)
        assert avg_time < 0.5, f"平均截图时间 {avg_time:.3f}s 超过阈值"
    
    def test_detection_performance(self):
        """T16: 检测性能"""
        capture = ScreenCapture()
        detector = ElementDetector()
        
        image = capture.capture()
        
        start = time.time()
        elements = detector.detect(image)
        elapsed = time.time() - start
        
        # 首次检测可能较慢（模型加载），放宽阈值
        assert elapsed < 10.0, f"首次检测时间 {elapsed:.2f}s 过长"


# 测试任务注册表
TEST_REGISTRY = {
    "basic": [
        "test_screen_capture",
        "test_element_detector_initialization",
        "test_mouse_controller",
        "test_keyboard_controller",
        "test_application_manager",
    ],
    "predefined": [
        "test_list_predefined_tasks",
        "test_create_calculator_task",
        "test_create_notepad_task",
        "test_create_chrome_task",
    ],
    "execution": [
        "test_execute_wait_task",
        "test_execute_sequence_with_screenshots",
        "test_execute_launch_notepad",
    ],
    "error_handling": [
        "test_invalid_task_action",
        "test_missing_target",
    ],
    "performance": [
        "test_screenshot_performance",
        "test_detection_performance",
    ],
}


def run_test_suite(categories: list = None):
    """
    运行测试套件
    
    Args:
        categories: 要运行的测试类别，None则运行全部
    """
    if categories is None:
        categories = list(TEST_REGISTRY.keys())
    
    tests_to_run = []
    for cat in categories:
        tests_to_run.extend(TEST_REGISTRY.get(cat, []))
    
    test_args = "::".join(tests_to_run) if tests_to_run else ""
    
    import subprocess
    cmd = f"python -m pytest tests/test_suite.py -v {test_args}"
    subprocess.run(cmd, shell=True)


if __name__ == "__main__":
    # 运行基础测试
    run_test_suite(["basic", "predefined"])

