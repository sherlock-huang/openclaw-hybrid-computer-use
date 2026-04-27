"""小米 Mimo 多模态客户端（预留）

支持模型: mimi-v2-omini, mimo-v2.5-pro
API 格式待补充，当前按 OpenAI 兼容格式预留。
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


class MimoClient:
    """小米 Mimo 多模态客户端

    当前按 OpenAI 兼容格式实现，如果实际 API 格式不同，
    请修改 _ensure_client 和 chat 方法。
    """

    DEFAULT_ENDPOINT = "https://token-plan-cn.xiaomimimo.com/v1/chat/completions"
    DEFAULT_MODEL = "mimo-v2-omni"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        endpoint: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        self.api_key = api_key or self._get_api_key()
        self.model = model or self.DEFAULT_MODEL
        self.endpoint = endpoint or self.DEFAULT_ENDPOINT
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._client = None
        logger.info(f"MimoClient 初始化: model={self.model}, endpoint={self.endpoint}")

    def _get_api_key(self) -> str:
        import os
        key = os.getenv("MIMO_API_KEY")
        if not key:
            raise ConfigError("未设置 MIMO_API_KEY 环境变量")
        return key

    def _ensure_client(self):
        if self._client is not None:
            return
        try:
            from openai import OpenAI
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.endpoint.replace("/v1/chat/completions", "/v1"),
            )
        except ImportError:
            raise RuntimeError("openai SDK 未安装，请运行: pip install openai")

    def _encode_image(self, image: np.ndarray) -> str:
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
        self._ensure_client()
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                return response.choices[0].message.content
            except Exception as e:
                last_error = e
                logger.warning(f"Mimo API 第 {attempt + 1} 次调用失败: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
        logger.error(f"Mimo API 所有重试失败: {last_error}")
        raise RuntimeError(f"Mimo API 调用失败: {last_error}")

    def diagnose_failure(
        self,
        screenshot: np.ndarray,
        annotated_screenshot: Optional[np.ndarray],
        instruction: str,
        system_prompt: Optional[str] = None,
    ) -> str:
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
