"""录制模块 - 支持桌面和浏览器操作录制"""

from .hybrid_recorder import HybridRecorder
from .browser_recorder import BrowserRecorder
from .window_detector import (
    get_active_window_title,
    is_browser_window,
    get_current_recording_mode,
)

__all__ = [
    "HybridRecorder",
    "BrowserRecorder",
    "get_active_window_title",
    "is_browser_window",
    "get_current_recording_mode",
]
