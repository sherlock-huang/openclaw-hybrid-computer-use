"""插件基础接口"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional

from ..core.config import Config


class PluginInterface(ABC):
    """插件接口 v1

    所有插件必须继承此类并实现 name、version 和 actions。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """插件唯一标识名（英文小写+下划线）"""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """版本号，如 1.0.0"""
        pass

    @property
    def description(self) -> str:
        """插件描述"""
        return ""

    @property
    def actions(self) -> Dict[str, Callable]:
        """返回插件支持的 action 映射

        格式: {"action_name": handler_func}
        handler_func 签名: handler(task: Task) -> bool
        """
        return {}

    def initialize(self, config: Optional[Config] = None) -> None:
        """初始化插件，在加载后调用一次"""
        pass

    def shutdown(self) -> None:
        """清理资源，在卸载前调用"""
        pass

    def health_check(self) -> bool:
        """健康检查，返回插件是否可用"""
        return True


class PluginContext:
    """插件上下文，传递运行时信息和共享状态"""

    def __init__(self):
        self.variables: Dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)

    def set(self, key: str, value: Any):
        self.variables[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.variables.get(key, default)