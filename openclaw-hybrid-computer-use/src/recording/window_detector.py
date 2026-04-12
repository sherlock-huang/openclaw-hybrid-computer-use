"""窗口检测器 - 检测当前活动窗口类型"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# 浏览器窗口关键词
BROWSER_KEYWORDS = [
    "chrome", "谷歌浏览器", "chromium",
    "edge", "microsoft edge",
    "firefox", "火狐",
    "safari",
]


def get_active_window_title() -> Optional[str]:
    """
    获取当前活动窗口的标题
    
    Returns:
        窗口标题，如果获取失败返回 None
    """
    try:
        # Windows 平台
        import win32gui
        window = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(window)
        return title
    except ImportError:
        logger.warning("win32gui 未安装，尝试使用 pygetwindow")
    
    try:
        import pygetwindow as gw
        window = gw.getActiveWindow()
        if window:
            return window.title
    except Exception as e:
        logger.error(f"获取窗口标题失败: {e}")
    
    return None


def is_browser_window(title: Optional[str]) -> bool:
    """
    判断窗口标题是否为浏览器
    
    Args:
        title: 窗口标题
        
    Returns:
        是否为浏览器窗口
    """
    if not title:
        return False
    
    title_lower = title.lower()
    return any(keyword in title_lower for keyword in BROWSER_KEYWORDS)


def get_current_recording_mode() -> str:
    """
    获取当前应该使用的录制模式
    
    Returns:
        "browser" 或 "desktop"
    """
    title = get_active_window_title()
    mode = "browser" if is_browser_window(title) else "desktop"
    logger.debug(f"当前窗口: {title}, 模式: {mode}")
    return mode
