"""
OpenClaw Computer-Use Agent (ClawDesktop)

一个开源的桌面自动化 Agent，支持屏幕感知、元素检测和任务执行。
"""

import sys

__version__ = "0.1.0"
__author__ = "OpenClaw Team"


def fix_windows_encoding():
    """修复 Windows 控制台中文乱码。

    注意：此函数应在 CLI 入口显式调用，不要在模块导入时执行，
    否则会破坏 pytest 的 capture 机制。
    """
    if sys.platform != "win32":
        return
    import io
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleCP(65001)  # UTF-8 input
    kernel32.SetConsoleOutputCP(65001)  # UTF-8 output

    # 仅在 stdout/stderr 仍是原始文件对象时重定向（跳过 pytest capture）
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    try:
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


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
    "fix_windows_encoding",
]
