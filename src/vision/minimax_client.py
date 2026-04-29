"""Minimax 多模态客户端

兼容 OpenAI Chat Completions API 格式，支持图片输入。
Endpoint: https://api.minimaxi.com/v1/chat/completions
"""

import base64
import json
import logging
import time
from io import BytesIO
from typing import Dict, Any, List, Optional

import numpy as np
from PIL import Image

from ..utils.exceptions import ConfigError

logger = logging.getLogger(__name__)


class MinimaxClient:
    """Minimax M2.7 多模态客户端"""

    DEFAULT_ENDPOINT = "https://api.minimaxi.com/v1/chat/completions"
    DEFAULT_MODEL = "MiniMax-M2.7"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        endpoint: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        key_manager=None,
    ):
        """
        初始化 Minimax 客户端

        Args:
            api_key: API Key，默认从 MINIMAX_API_KEY 环境变量读取
            model: 模型名称，默认 MiniMax-M2.7
            endpoint: API 端点，默认 https://api.minimaxi.com/v1/chat/completions
            max_retries: 最大重试次数
            retry_delay: 重试间隔（秒）
            key_manager: KeyManager 实例，用于统一 Key 管理和轮询
        """
        self.key_manager = key_manager
        self._explicit_api_key = api_key

        if key_manager is not None:
            self.api_key = key_manager.get_key("minimax") or api_key or self._get_api_key()
        else:
            self.api_key = api_key or self._get_api_key()

        self.model = model or self.DEFAULT_MODEL
        self.endpoint = endpoint or self.DEFAULT_ENDPOINT
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # 延迟初始化 openai client
        self._client = None
        logger.info(f"MinimaxClient 初始化: model={self.model}, endpoint={self.endpoint}")

    def _get_api_key(self) -> str:
        import os
        key = os.getenv("MINIMAX_API_KEY")
        if not key:
            raise ConfigError("未设置 MINIMAX_API_KEY 环境变量")
        return key

    def _ensure_client(self):
        if self._client is not None:
            return
        # 如果 key_manager 存在，每次确保客户端时重新获取最新 Key
        if self.key_manager is not None:
            fresh_key = self.key_manager.get_key("minimax") or self._explicit_api_key or self._get_api_key()
            self.api_key = fresh_key
        try:
            from openai import OpenAI
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.endpoint.replace("/v1/chat/completions", "/v1"),
            )
        except ImportError:
            raise RuntimeError("openai SDK 未安装，请运行: pip install openai")

    def _encode_image(self, image: np.ndarray) -> str:
        """将 numpy 图像转为 base64 data URL"""
        pil_image = Image.fromarray(image)
        max_size = (1024, 1024)
        pil_image.thumbnail(max_size, Image.Resampling.LANCZOS)
        buffer = BytesIO()
        pil_image.save(buffer, format="JPEG", quality=85)
        b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{b64}"

    def chat(
        self,
        messages: List[Dict],
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> str:
        """发送对话请求（支持多模态）"""
        self._ensure_client()
        last_error = None
        current_key = self.api_key

        for attempt in range(self.max_retries):
            try:
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                # 报告成功
                if self.key_manager is not None:
                    self.key_manager.report_result("minimax", current_key, success=True)
                return response.choices[0].message.content
            except Exception as e:
                last_error = e
                error_msg = str(e)
                logger.warning(f"Minimax API 第 {attempt + 1} 次调用失败: {e}")
                # 报告失败
                if self.key_manager is not None:
                    self.key_manager.report_result("minimax", current_key, success=False, error=error_msg)
                    # 尝试获取下一个 Key 进行重试
                    next_key = self.key_manager.get_key("minimax")
                    if next_key and next_key != current_key:
                        logger.info(f"MinimaxClient 切换到备用 Key 重试")
                        current_key = next_key
                        self.api_key = next_key
                        try:
                            from openai import OpenAI
                            self._client = OpenAI(
                                api_key=current_key,
                                base_url=self.endpoint.replace("/v1/chat/completions", "/v1"),
                            )
                        except Exception:
                            pass
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))

        logger.error(f"Minimax API 所有重试失败: {last_error}")
        raise RuntimeError(f"Minimax API 调用失败: {last_error}")

    def analyze_screen(
        self,
        screenshot: np.ndarray,
        instruction: str,
        system_prompt: Optional[str] = None,
        history: Optional[List] = None,
    ) -> Dict[str, Any]:
        """分析屏幕截图，返回结构化决策"""
        image_url = self._encode_image(screenshot)

        content = [
            {"type": "image_url", "image_url": {"url": image_url}},
            {"type": "text", "text": instruction},
        ]

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": content})

        response = self.chat(messages)
        return self._parse_response(response)

    def diagnose_failure(
        self,
        screenshot: np.ndarray,
        annotated_screenshot: Optional[np.ndarray],
        instruction: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        """诊断失败原因（返回 VLM 的原始文本响应）"""
        content = [
            {"type": "image_url", "image_url": {"url": self._encode_image(screenshot)}},
        ]
        if annotated_screenshot is not None:
            content.append(
                {"type": "image_url", "image_url": {"url": self._encode_image(annotated_screenshot)}}
            )
        content.append({"type": "text", "text": instruction})

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": content})

        return self.chat(messages)

    def verify_result(
        self,
        screenshot_before: np.ndarray,
        screenshot_after: np.ndarray,
        instruction: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        """验证修复前后截图，返回 VLM 判断结果"""
        content = [
            {"type": "text", "text": "操作前截图:"},
            {"type": "image_url", "image_url": {"url": self._encode_image(screenshot_before)}},
            {"type": "text", "text": "操作后截图:"},
            {"type": "image_url", "image_url": {"url": self._encode_image(screenshot_after)}},
            {"type": "text", "text": instruction},
        ]

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": content})

        return self.chat(messages, max_tokens=512)

    def _parse_response(self, response: Optional[str]) -> Dict[str, Any]:
        """解析 JSON 响应，失败则返回默认结构"""
        if not response:
            return self._default_response("空响应")

        import re
        try:
            # 尝试提取 JSON 代码块
            json_match = re.search(r"```json\s*\n(.*?)\n```", response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_match = re.search(r"(\{.*\})", response, re.DOTALL)
                json_str = json_match.group(1) if json_match else response

            result = json.loads(json_str)
            for key, default in [
                ("action", "screenshot"),
                ("target", ""),
                ("value", ""),
                ("delay", 2.0),
                ("is_task_complete", False),
                ("observation", ""),
                ("thought", ""),
                ("confidence", 0.5),
            ]:
                result.setdefault(key, default)
            return result
        except (json.JSONDecodeError, AttributeError):
            return self._default_response(f"无法解析 JSON: {response[:200]}")

    def _default_response(self, reason: str) -> Dict[str, Any]:
        return {
            "observation": reason,
            "thought": "解析失败，使用安全默认操作",
            "action": "screenshot",
            "target": "",
            "value": "",
            "delay": 2.0,
            "is_task_complete": False,
            "confidence": 0.1,
        }
