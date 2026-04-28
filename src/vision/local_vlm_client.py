"""本地轻量 VLM 客户端（离线兜底）

使用 Qwen2-VL-2B-Instruct 或类似轻量模型，
在离线/网络不可用/预算耗尽时提供基础视觉诊断能力。

特性：
- 延迟加载（首次使用时才加载模型）
- CPU 运行支持（无 GPU 也能用，只是慢）
- 统一接口与 MinimaxClient/MimoClient
- 可选 4-bit/8-bit 量化减少内存
"""

import base64
import io
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class LocalVLMClient:
    """本地视觉语言模型客户端

    默认模型: Qwen/Qwen2-VL-2B-Instruct (~4GB)
    CPU 推理速度: ~30-60s/张图（取决于硬件）
    """

    DEFAULT_MODEL = "Qwen/Qwen2-VL-2B-Instruct"
    DEFAULT_DEVICE = "auto"
    DEFAULT_MAX_TOKENS = 1024
    DEFAULT_TEMPERATURE = 0.2

    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
        cache_dir: Optional[str] = None,
        load_in_8bit: bool = False,
        load_in_4bit: bool = False,
        trust_remote_code: bool = True,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
    ):
        """
        初始化本地 VLM 客户端（延迟加载模型）

        Args:
            model_name: HuggingFace 模型名，默认 Qwen2-VL-2B-Instruct
            device: 运行设备 ("cuda", "cpu", "auto")
            cache_dir: 模型缓存目录
            load_in_8bit: 是否 8-bit 量化（减少显存）
            load_in_4bit: 是否 4-bit 量化（最小显存）
            trust_remote_code: 是否信任远程代码（Qwen 模型需要）
            max_tokens: 最大生成 token 数
            temperature: 采样温度
        """
        self.model_name = model_name or self.DEFAULT_MODEL
        self.device = device or self.DEFAULT_DEVICE
        self.cache_dir = cache_dir
        self.load_in_8bit = load_in_8bit
        self.load_in_4bit = load_in_4bit
        self.trust_remote_code = trust_remote_code
        self.max_tokens = max_tokens
        self.temperature = temperature

        # 延迟加载的组件
        self._processor = None
        self._model = None
        self._device_actual = None

        logger.info(
            f"LocalVLMClient 初始化: model={self.model_name}, "
            f"device={self.device}, 4bit={load_in_4bit}, 8bit={load_in_8bit}"
        )

    def _ensure_model(self):
        """延迟加载模型和处理器"""
        if self._model is not None and self._processor is not None:
            return

        logger.info(f"正在加载本地模型: {self.model_name} (首次使用，可能需要几分钟)...")
        start = time.time()

        try:
            from transformers import (
                Qwen2VLForConditionalGeneration,
                AutoProcessor,
            )
        except ImportError as e:
            raise RuntimeError(
                f"transformers 未安装或版本不兼容: {e}. "
                "请运行: pip install transformers>=4.40.0 accelerate qwen-vl-utils"
            ) from e

        # 构建加载参数
        load_kwargs = {
            "trust_remote_code": self.trust_remote_code,
        }
        if self.cache_dir:
            load_kwargs["cache_dir"] = self.cache_dir

        # 量化配置
        if self.load_in_4bit or self.load_in_8bit:
            try:
                from transformers import BitsAndBytesConfig
                load_kwargs["quantization_config"] = BitsAndBytesConfig(
                    load_in_4bit=self.load_in_4bit,
                    load_in_8bit=self.load_in_8bit,
                    bnb_4bit_compute_dtype="float16" if self.load_in_4bit else None,
                )
            except ImportError:
                logger.warning("bitsandbytes 未安装，量化不可用。请运行: pip install bitsandbytes")

        # 自动选择设备
        if self.device == "auto":
            try:
                import torch
                self._device_actual = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                self._device_actual = "cpu"
        else:
            self._device_actual = self.device

        logger.info(f"加载模型到设备: {self._device_actual}")

        try:
            self._processor = AutoProcessor.from_pretrained(
                self.model_name,
                trust_remote_code=self.trust_remote_code,
                cache_dir=self.cache_dir,
            )
            self._model = Qwen2VLForConditionalGeneration.from_pretrained(
                self.model_name,
                device_map=self._device_actual if self._device_actual != "cpu" else None,
                **load_kwargs,
            )
            if self._device_actual == "cpu":
                self._model = self._model.cpu()

            elapsed = time.time() - start
            logger.info(f"模型加载完成，耗时 {elapsed:.1f}s")

        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            raise RuntimeError(f"本地模型 {self.model_name} 加载失败: {e}") from e

    def _encode_image(self, image: np.ndarray) -> Image.Image:
        """将 numpy 图像转为 PIL Image"""
        if image is None:
            raise ValueError("image is required")
        # 确保是 uint8
        if image.dtype != np.uint8:
            image = (image * 255).astype(np.uint8) if image.max() <= 1.0 else image.astype(np.uint8)
        return Image.fromarray(image)

    def chat(
        self,
        messages: List[Dict],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """发送对话请求（支持多模态）

        messages 格式与 OpenAI API 兼容：
        [
            {"role": "user", "content": [
                {"type": "image", "image": PIL.Image},
                {"type": "text", "text": "..."}
            ]}
        ]
        """
        self._ensure_model()

        max_new_tokens = max_tokens or self.max_tokens
        temp = temperature if temperature is not None else self.temperature

        # 合并所有消息为单一 prompt
        # Qwen2-VL 使用 processor.apply_chat_template
        text_parts = []
        images = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if isinstance(content, list):
                for item in content:
                    if item.get("type") == "image_url":
                        # 解析 base64 图片
                        url = item.get("image_url", {}).get("url", "")
                        if url.startswith("data:image"):
                            b64 = url.split(",")[1]
                            img_data = base64.b64decode(b64)
                            images.append(Image.open(io.BytesIO(img_data)))
                    elif item.get("type") == "image":
                        images.append(item.get("image"))
                    elif item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
            else:
                text_parts.append(str(content))

        full_text = "\n".join(text_parts)

        # 构建 Qwen2-VL 的输入格式
        if images:
            content_list = []
            for img in images:
                content_list.append({"type": "image", "image": img})
            content_list.append({"type": "text", "text": full_text})
            conversation = [{"role": "user", "content": content_list}]
        else:
            conversation = [{"role": "user", "content": full_text}]

        # 应用 chat template
        try:
            text_prompt = self._processor.apply_chat_template(
                conversation,
                tokenize=False,
                add_generation_prompt=True,
            )
        except Exception as e:
            logger.warning(f"apply_chat_template 失败，回退到简单拼接: {e}")
            text_prompt = full_text

        # 处理输入
        if images:
            inputs = self._processor(
                text=[text_prompt],
                images=images,
                return_tensors="pt",
                padding=True,
            )
        else:
            inputs = self._processor(
                text=[text_prompt],
                return_tensors="pt",
                padding=True,
            )

        # 移动到设备
        if self._device_actual != "cpu":
            inputs = {k: v.to(self._model.device) for k, v in inputs.items()}

        # 生成
        start = time.time()
        with logger.debug("本地 VLM 推理中..."):
            generated_ids = self._model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temp,
                do_sample=temp > 0,
            )

        # 解码输出
        # 去掉输入部分的 token
        generated_ids_trimmed = [
            out_ids[len(in_ids):]
            for in_ids, out_ids in zip(inputs["input_ids"], generated_ids)
        ]
        output_text = self._processor.batch_decode(
            generated_ids_trimmed,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )[0]

        latency = time.time() - start
        logger.info(f"本地 VLM 推理完成，耗时 {latency:.1f}s")

        return output_text

    def analyze_screen(
        self,
        screenshot: np.ndarray,
        instruction: str,
        system_prompt: Optional[str] = None,
        history: Optional[List] = None,
    ) -> Dict[str, Any]:
        """分析屏幕截图，返回结构化决策"""
        pil_image = self._encode_image(screenshot)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            messages.extend(history)
        messages.append({
            "role": "user",
            "content": [
                {"type": "image", "image": pil_image},
                {"type": "text", "text": instruction},
            ],
        })

        response = self.chat(messages)
        return self._parse_response(response)

    def diagnose_failure(
        self,
        screenshot: np.ndarray,
        annotated_screenshot: Optional[np.ndarray],
        instruction: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        """诊断失败原因（返回原始文本响应）"""
        pil_image = self._encode_image(screenshot)

        content = [
            {"type": "image", "image": pil_image},
            {"type": "text", "text": instruction},
        ]
        if annotated_screenshot is not None:
            content.insert(1, {"type": "image", "image": self._encode_image(annotated_screenshot)})

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
        """验证修复前后截图"""
        before_img = self._encode_image(screenshot_before)
        after_img = self._encode_image(screenshot_after)

        content = [
            {"type": "text", "text": "操作前截图:"},
            {"type": "image", "image": before_img},
            {"type": "text", "text": "操作后截图:"},
            {"type": "image", "image": after_img},
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
