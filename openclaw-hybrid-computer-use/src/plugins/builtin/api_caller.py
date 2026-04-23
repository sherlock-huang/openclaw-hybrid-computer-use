"""API 调用插件 — 内置示例

支持 GET/POST/PUT/DELETE HTTP 请求。
"""

import json
import logging
from typing import Dict, Callable

try:
    from ...plugins.base import PluginInterface
    from ...core.models import Task
except ImportError:
    from claw_desktop.plugins.base import PluginInterface
    from claw_desktop.core.models import Task

logger = logging.getLogger(__name__)


class APIPlugin(PluginInterface):
    """API 调用插件"""

    @property
    def name(self) -> str:
        return "api"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "HTTP API 调用插件（GET/POST/PUT/DELETE）"

    @property
    def actions(self) -> Dict[str, Callable]:
        return {
            "get": self.action_get,
            "post": self.action_post,
            "put": self.action_put,
            "delete": self.action_delete,
        }

    def _request(self, method: str, url: str, data: Dict = None, headers: Dict = None) -> bool:
        try:
            import requests
            kwargs = {"headers": headers or {}}
            if data:
                kwargs["json"] = data
            response = requests.request(method, url, timeout=30, **kwargs)
            response.raise_for_status()
            logger.info(f"API {method.upper()} {url} -> {response.status_code}")
            try:
                result = response.json()
                logger.info(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)[:500]}")
            except Exception:
                logger.info(f"响应: {response.text[:500]}")
            return True
        except ImportError:
            logger.error("requests 未安装，运行: pip install requests")
            return False
        except Exception as e:
            logger.error(f"API 请求失败: {e}")
            return False

    def action_get(self, task: Task) -> bool:
        """GET 请求: target=URL"""
        return self._request("get", task.target)

    def action_post(self, task: Task) -> bool:
        """POST 请求: target=URL, value=JSON body"""
        data = json.loads(task.value or "{}")
        return self._request("post", task.target, data=data)

    def action_put(self, task: Task) -> bool:
        """PUT 请求: target=URL, value=JSON body"""
        data = json.loads(task.value or "{}")
        return self._request("put", task.target, data=data)

    def action_delete(self, task: Task) -> bool:
        """DELETE 请求: target=URL"""
        return self._request("delete", task.target)
