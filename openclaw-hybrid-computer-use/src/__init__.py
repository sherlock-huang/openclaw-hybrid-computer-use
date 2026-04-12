"""
OpenClaw Computer-Use Agent (ClawDesktop)

一个开源的桌面自动化 Agent，支持屏幕感知、元素检测和任务执行。
"""

# 修复 Windows 控制台中文乱码
import sys
import io

if sys.platform == "win32":
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleCP(65001)  # UTF-8 input
    kernel32.SetConsoleOutputCP(65001)  # UTF-8 output
    
    # 重新设置 stdout/stderr 编码
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

__version__ = "0.1.0"
__author__ = "OpenClaw Team"

# 主要接口导出
from .core.agent import ComputerUseAgent
from .core.executor import TaskExecutor, ExecutionResult
from .core.models import Task, TaskSequence
from .perception.screen import ScreenCapture
from .perception.detector import ElementDetector
from .action.mouse import MouseController
from .action.keyboard import KeyboardController
from .action.app_manager import ApplicationManager

__all__ = [
    "ComputerUseAgent",
    "TaskExecutor",
    "ExecutionResult",
    "Task",
    "TaskSequence",
    "ScreenCapture",
    "ElementDetector",
    "MouseController",
    "KeyboardController",
    "ApplicationManager",
]
