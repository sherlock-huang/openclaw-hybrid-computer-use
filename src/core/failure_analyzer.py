"""失败分析器 —— 基于错误信息对执行失败进行结构化分类。

轻量版实现：基于关键词匹配，无需外部模型依赖。
"""

from enum import Enum, auto
from typing import Union

from .models import Task


class FailureType(Enum):
    """失败类型枚举。"""

    ELEMENT_NOT_FOUND = auto()      # 目标元素未找到
    WRONG_ELEMENT = auto()          # 找到了但点错了元素
    TIMING_ISSUE = auto()           # 页面/界面未加载完成
    UI_CHANGED = auto()             # UI 布局或选择器发生变化
    NETWORK_ERROR = auto()          # 网络超时或连接失败
    PERMISSION_DENIED = auto()      # 权限不足（管理员、剪贴板等）
    VALIDATION_ERROR = auto()       # 参数验证失败
    RESOURCE_ERROR = auto()         # 资源未就绪（Excel/Word 未打开等）
    UNKNOWN = auto()                # 未知原因


class FailureAnalyzer:
    """失败分析器。

    基于异常类型和错误消息关键词，将失败归类为可处理的 FailureType。
    """

    # 关键词到失败类型的映射
    KEYWORD_MAP: dict[FailureType, list[str]] = {
        FailureType.ELEMENT_NOT_FOUND: [
            "not found",
            "找不到",
            "未找到",
            "target not found",
            "element not found",
            "selector not found",
            "no element",
            "locator not found",
            "无法定位",
            "定位失败",
        ],
        FailureType.WRONG_ELEMENT: [
            "wrong element",
            "错误的元素",
            "点击到了错误",
            "unexpected element",
            "mismatch",
        ],
        FailureType.TIMING_ISSUE: [
            "timeout",
            "timed out",
            "超时",
            "not visible",
            "not ready",
            "未就绪",
            "not loaded",
            "waiting",
            "等待",
            "detach",
            "stale element",
        ],
        FailureType.UI_CHANGED: [
            "ui changed",
            "layout changed",
            "selector invalid",
            "invalid selector",
            "deprecated",
            "removed",
            "样式变化",
        ],
        FailureType.NETWORK_ERROR: [
            "network",
            "connection",
            "connect",
            "refused",
            "dns",
            "offline",
            "unreachable",
            "net::",
            "err_",
            "网络",
            "连接",
        ],
        FailureType.PERMISSION_DENIED: [
            "permission",
            "denied",
            "access denied",
            "unauthorized",
            "forbidden",
            "管理员",
            "权限",
            "拒绝访问",
        ],
        FailureType.VALIDATION_ERROR: [
            "validation",
            "invalid",
            "required",
            "missing",
            "格式错误",
            "缺少",
            "必填",
            "不合法",
        ],
        FailureType.RESOURCE_ERROR: [
            "resource",
            "not ready",
            "未打开",
            "未初始化",
            "workbook",
            "document",
            "file not open",
        ],
    }

    # 异常类型到失败类型的快速映射
    EXCEPTION_MAP: dict[type, FailureType] = {
        # 这些异常类型会在 utils.exceptions 中导入
    }

    def __init__(self):
        self._init_exception_map()

    def _init_exception_map(self):
        """延迟导入并建立异常类型映射，避免循环导入。"""
        try:
            from ..utils.exceptions import (
                NotFoundError,
                ValidationError,
                ResourceError,
                BrowserError,
                PerceptionError,
            )

            self.EXCEPTION_MAP = {
                NotFoundError: FailureType.ELEMENT_NOT_FOUND,
                ValidationError: FailureType.VALIDATION_ERROR,
                ResourceError: FailureType.RESOURCE_ERROR,
                BrowserError: FailureType.NETWORK_ERROR,
                PerceptionError: FailureType.ELEMENT_NOT_FOUND,
            }
        except ImportError:
            self.EXCEPTION_MAP = {}

    def analyze(self, error: Union[Exception, str], task: Task) -> FailureType:
        """分析失败原因，返回结构化失败类型。

        Args:
            error: 异常对象或错误消息字符串。
            task: 当前执行的任务，用于上下文判断。

        Returns:
            FailureType 枚举值。
        """
        # 1. 基于异常类型快速判断
        if isinstance(error, Exception):
            error_type = type(error)
            if error_type in self.EXCEPTION_MAP:
                return self.EXCEPTION_MAP[error_type]

        # 2. 基于错误消息关键词匹配
        message = str(error).lower()
        scores: dict[FailureType, int] = {}

        for failure_type, keywords in self.KEYWORD_MAP.items():
            score = sum(1 for kw in keywords if kw.lower() in message)
            if score > 0:
                scores[failure_type] = score

        if scores:
            # 取匹配关键词最多的类型
            return max(scores, key=scores.get)

        # 3. 基于任务上下文启发式判断
        return self._heuristic_by_task(task, message)

    def _heuristic_by_task(self, task: Task, message: str) -> FailureType:
        """基于任务上下文的启发式判断。"""
        action = task.action if task else ""

        if action in ("click", "double_click", "right_click", "type", "scroll"):
            if task.target and ("," in task.target or task.target.isdigit()):
                # 目标是坐标，坐标点击失败通常是元素未找到或时机问题
                return FailureType.ELEMENT_NOT_FOUND
            return FailureType.UNKNOWN

        if action.startswith("browser_"):
            # 浏览器操作失败，默认先怀疑时机问题
            if "navigating" in message or "load" in message:
                return FailureType.TIMING_ISSUE
            return FailureType.UNKNOWN

        return FailureType.UNKNOWN

    def get_suggestion(self, failure_type: FailureType) -> str:
        """获取针对失败类型的简要修复建议。"""
        suggestions = {
            FailureType.ELEMENT_NOT_FOUND: "尝试扩大搜索范围、使用OCR文本搜索或增加等待时间",
            FailureType.WRONG_ELEMENT: "检查选择器是否精确匹配目标，避免模糊匹配",
            FailureType.TIMING_ISSUE: "增加delay等待页面/界面加载完成",
            FailureType.UI_CHANGED: "检查网站/应用是否更新，更新对应的选择器配置",
            FailureType.NETWORK_ERROR: "检查网络连接，增加超时时间或稍后重试",
            FailureType.PERMISSION_DENIED: "以管理员身份运行或检查系统权限设置",
            FailureType.VALIDATION_ERROR: "检查任务参数是否完整且格式正确",
            FailureType.RESOURCE_ERROR: "确保所需资源（Excel/Word等）已正确初始化",
            FailureType.UNKNOWN: "记录日志并尝试通用重试策略",
        }
        return suggestions.get(failure_type, suggestions[FailureType.UNKNOWN])
