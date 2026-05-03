"""窗口管理器 —— 应用启动、定位、关闭、状态恢复。

M4b 真实 UI 验证使用：
- 启动低风险应用（记事本、计算器、浏览器空白页）
- 获取窗口位置和大小
- 测试结束后关闭窗口，恢复桌面状态
- 支持 graceful close 和 force kill
"""

import logging
import subprocess
import time
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# 应用命令映射（Windows）
APP_COMMANDS = {
    "notepad": "notepad.exe",
    "calc": "calc.exe",
    "mspaint": "mspaint.exe",
    "browser": "msedge.exe",
}


class WindowInfo:
    """窗口信息。"""

    def __init__(self, hwnd: int, title: str, rect: Tuple[int, int, int, int]):
        self.hwnd = hwnd
        self.title = title
        self.rect = rect  # (left, top, right, bottom)

    @property
    def center(self) -> Tuple[int, int]:
        left, top, right, bottom = self.rect
        return ((left + right) // 2, (top + bottom) // 2)

    def __repr__(self) -> str:
        return f"WindowInfo(hwnd={self.hwnd}, title={self.title!r}, rect={self.rect})"


def _get_pyautogui_windows() -> List:
    """获取 pyautogui 窗口列表。"""
    try:
        import pyautogui
        return pyautogui.getAllWindows()
    except Exception as e:
        logger.debug(f"pyautogui getAllWindows failed: {e}")
        return []


def find_windows(title_substring: str) -> List[WindowInfo]:
    """按标题子串查找窗口。"""
    results = []
    for win in _get_pyautogui_windows():
        try:
            if title_substring.lower() in win.title.lower():
                results.append(
                    WindowInfo(
                        hwnd=getattr(win, "_hWnd", 0),
                        title=win.title,
                        rect=(win.left, win.top, win.right, win.bottom),
                    )
                )
        except Exception:
            continue
    return results


def launch_app(app_name: str, args: Optional[List[str]] = None, wait_sec: float = 1.0) -> bool:
    """启动应用并等待窗口出现。

    Args:
        app_name: 应用名称（notepad / calc / mspaint / browser）
        args: 额外命令行参数
        wait_sec: 启动后等待窗口出现的时间

    Returns:
        是否成功启动
    """
    cmd = APP_COMMANDS.get(app_name, app_name)
    full_cmd = [cmd] + (args or [])

    try:
        subprocess.Popen(full_cmd, shell=True)
        logger.info(f"启动应用: {full_cmd}")
        time.sleep(wait_sec)
        return True
    except Exception as e:
        logger.error(f"启动应用失败: {full_cmd} — {e}")
        return False


def close_window_by_title(title_substring: str, timeout_sec: float = 3.0) -> bool:
    """按标题子串关闭窗口（graceful）。"""
    windows = find_windows(title_substring)
    if not windows:
        logger.warning(f"未找到窗口: {title_substring}")
        return False

    closed = False
    for info in windows:
        try:
            # 尝试通过 pyautogui 关闭
            for win in _get_pyautogui_windows():
                if getattr(win, "_hWnd", 0) == info.hwnd:
                    win.close()
                    closed = True
                    logger.info(f"关闭窗口: {info.title}")
                    break
        except Exception as e:
            logger.debug(f"graceful close failed for {info.title}: {e}")

    # 等待确认关闭
    start = time.time()
    while time.time() - start < timeout_sec:
        remaining = find_windows(title_substring)
        if not remaining:
            return True
        time.sleep(0.2)

    return closed


def force_kill_app(app_name: str) -> bool:
    """强制结束应用进程。"""
    cmd = APP_COMMANDS.get(app_name, app_name)
    try:
        subprocess.run(["taskkill", "/F", "/IM", cmd], check=False, capture_output=True)
        logger.info(f"强制结束进程: {cmd}")
        return True
    except Exception as e:
        logger.error(f"强制结束进程失败: {cmd} — {e}")
        return False


def cleanup_apps(app_names: Optional[List[str]] = None) -> None:
    """清理所有测试应用窗口。

    先尝试 graceful close，失败后 force kill。
    """
    apps = app_names or list(APP_COMMANDS.keys())
    for app in apps:
        # 先尝试 graceful close（按标题子串）
        title_map = {
            "notepad": "Notepad",
            "calc": "Calculator",
            "mspaint": "Paint",
            "browser": "Edge",
        }
        title = title_map.get(app, app)
        if not close_window_by_title(title, timeout_sec=2.0):
            # graceful 失败，强制结束
            force_kill_app(app)
        time.sleep(0.5)


def is_app_running(app_name: str) -> bool:
    """检查应用是否仍在运行。"""
    title_map = {
        "notepad": "Notepad",
        "calc": "Calculator",
        "mspaint": "Paint",
        "browser": "Edge",
    }
    title = title_map.get(app_name, app_name)
    return len(find_windows(title)) > 0


def get_app_window_rect(app_name: str) -> Optional[Tuple[int, int, int, int]]:
    """获取应用窗口的矩形区域。

    Returns:
        (left, top, right, bottom) or None
    """
    title_map = {
        "notepad": "Notepad",
        "calc": "Calculator",
        "mspaint": "Paint",
        "browser": "Edge",
    }
    title = title_map.get(app_name, app_name)
    windows = find_windows(title)
    if windows:
        return windows[0].rect
    return None
