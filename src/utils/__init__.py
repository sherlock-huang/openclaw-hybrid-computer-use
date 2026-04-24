"""工具函数模块"""

from .logger import setup_logger, get_logger
from .image import draw_elements, save_debug_image
from .visualizer import ExecutionVisualizer, visualize_mouse_path
from .exceptions import (
    ClawDesktopError,
    ConfigError,
    ValidationError,
    ResourceError,
    ExecutionError,
    BrowserError,
    DesktopError,
    WeChatError,
    OfficeError,
    TaskExecutionError,
    PerceptionError,
    ScreenCaptureError,
    DetectionError,
    OCRError,
    TemplateMatchError,
    PluginError,
    NotFoundError,
)

__all__ = [
    "setup_logger",
    "get_logger",
    "draw_elements",
    "save_debug_image",
    "ExecutionVisualizer",
    "visualize_mouse_path",
    # exceptions
    "ClawDesktopError",
    "ConfigError",
    "ValidationError",
    "ResourceError",
    "ExecutionError",
    "BrowserError",
    "DesktopError",
    "WeChatError",
    "OfficeError",
    "TaskExecutionError",
    "PerceptionError",
    "ScreenCaptureError",
    "DetectionError",
    "OCRError",
    "TemplateMatchError",
    "PluginError",
    "NotFoundError",
]
