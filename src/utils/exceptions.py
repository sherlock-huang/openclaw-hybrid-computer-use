"""统一异常体系

所有自定义异常继承自 ClawDesktopError，便于调用方按层次捕获。
"""


class ClawDesktopError(Exception):
    """所有自定义异常的基类。"""

    def __init__(self, message: str = "", *, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


# ---------------------------------------------------------------------------
# 配置与验证
# ---------------------------------------------------------------------------

class ConfigError(ClawDesktopError):
    """配置错误（缺少必需配置项、配置值非法等）。"""
    pass


class ValidationError(ClawDesktopError):
    """输入或参数验证失败（如缺少必需字段、格式错误）。"""
    pass


class ResourceError(ClawDesktopError):
    """资源未准备好（如 Excel workbook 尚未打开）。"""
    pass


# ---------------------------------------------------------------------------
# 执行层
# ---------------------------------------------------------------------------

class ExecutionError(ClawDesktopError):
    """任务执行过程中发生的通用错误。"""
    pass


class BrowserError(ExecutionError):
    """浏览器操作失败。"""
    pass


class DesktopError(ExecutionError):
    """桌面操作失败（鼠标、键盘、应用启动等）。"""
    pass


class WeChatError(ExecutionError):
    """微信自动化操作失败。"""
    pass


class OfficeError(ExecutionError):
    """Office 自动化操作失败。"""
    pass


class TaskExecutionError(ExecutionError):
    """具体任务步骤执行失败，携带任务上下文。"""

    def __init__(
        self,
        message: str = "",
        *,
        task_name: str = "",
        task_action: str = "",
        task_index: int = -1,
        details: dict | None = None,
    ):
        super().__init__(message, details=details)
        self.task_name = task_name
        self.task_action = task_action
        self.task_index = task_index


# ---------------------------------------------------------------------------
# 感知层
# ---------------------------------------------------------------------------

class PerceptionError(ClawDesktopError):
    """屏幕感知层通用错误。"""
    pass


class ScreenCaptureError(PerceptionError):
    """截图失败。"""
    pass


class DetectionError(PerceptionError):
    """元素检测失败。"""
    pass


class OCRError(PerceptionError):
    """OCR 文字识别失败。"""
    pass


class TemplateMatchError(PerceptionError):
    """模板匹配失败。"""
    pass


# ---------------------------------------------------------------------------
# 插件与查找
# ---------------------------------------------------------------------------

class PluginError(ClawDesktopError):
    """插件加载或调用失败。"""
    pass


class NotFoundError(ClawDesktopError):
    """元素、窗口、文件或联系人未找到。"""
    pass
