"""本地视觉语言模型客户端

基于 transformers 的本地 VLM 推理，支持 Qwen2-VL 系列模型。
支持 CPU/GPU 推理，可选 4-bit/8-bit 量化。
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class LocalVLMClient:
    """本地 VLM 客户端"""

    # 推荐的轻量级模型（按优先级排序）
    RECOMMENDED_MODELS = {
        "qwen2-vl-2b": "Qwen/Qwen2-VL-2B-Instruct",
        "qwen2-vl-7b": "Qwen/Qwen2-VL-7B-Instruct",
        "minicpm-v-2.6": "openbmb/MiniCPM-V-2_6",
    }

    def __init__(
        self,
        model_name: str = "Qwen/Qwen2-VL-2B-Instruct",
        device: str = "auto",
        load_in_4bit: bool = False,
        load_in_8bit: bool = False,
        max_new_tokens: int = 512,
        cache_dir: Optional[str] = None,
    ):
        """
        初始化本地 VLM 客户端

        Args:
            model_name: HuggingFace 模型名或本地路径
            device: 运行设备 auto/cpu/cuda
            load_in_4bit: 是否使用 4-bit 量化（需要 bitsandbytes）
            load_in_8bit: 是否使用 8-bit 量化（需要 bitsandbytes）
            max_new_tokens: 最大生成 token 数
            cache_dir: 模型缓存目录
        """
        self.model_name = model_name
        self.device = device
        self.load_in_4bit = load_in_4bit
        self.load_in_8bit = load_in_8bit
        self.max_new_tokens = max_new_tokens
        self.cache_dir = cache_dir or os.path.expanduser("~/.cache/openclaw/models")

        # 延迟初始化
        self._processor = None
        self._model = None
        self._is_loaded = False

        logger.info(f"LocalVLMClient 初始化: model={model_name}, device={device}, 4bit={load_in_4bit}")

    def _load_model(self):
        """延迟加载模型"""
        if self._is_loaded:
            return

        try:
            from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
            import torch
        except ImportError as e:
            raise RuntimeError(
                f"本地 VLM 依赖未安装: {e}. "
                "请运行: pip install transformers accelerate qwen-vl-utils"
            )

        logger.info(f"正在加载模型: {self.model_name}...")

        # 量化配置
        quantization_config = None
        if self.load_in_4bit or self.load_in_8bit:
            try:
                from transformers import BitsAndBytesConfig
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=self.load_in_4bit,
                    load_in_8bit=self.load_in_8bit,
                    bnb_4bit_compute_dtype=torch.float16 if self.load_in_4bit else None,
                )
                logger.info(f"启用量化: 4bit={self.load_in_4bit}, 8bit={self.load_in_8bit}")
            except ImportError:
                logger.warning("bitsandbytes 未安装，跳过量化。运行: pip install bitsandbytes")

        # 加载处理器和模型
        self._processor = AutoProcessor.from_pretrained(
            self.model_name,
            cache_dir=self.cache_dir,
            trust_remote_code=True,
        )

        self._model = Qwen2VLForConditionalGeneration.from_pretrained(
            self.model_name,
            cache_dir=self.cache_dir,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map=self.device if self.device != "auto" else "auto",
            quantization_config=quantization_config,
            trust_remote_code=True,
            low_cpu_mem_usage=True,
        )

        self._is_loaded = True
        logger.info("模型加载完成")

    def chat(self, messages: List[Dict], max_tokens: Optional[int] = None, temperature: float = 0.2) -> str:
        """
        发送对话请求（兼容 VLMClient 接口）

        Args:
            messages: OpenAI 格式的消息列表
            max_tokens: 最大生成 token 数
            temperature: 温度参数（当前模型可能不支持动态调节）

        Returns:
            AI 回复文本
        """
        self._load_model()
        max_tokens = max_tokens or self.max_new_tokens

        # 构建文本提示
        text_prompt = self._messages_to_prompt(messages)

        # 处理消息中的图像
        images = []
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, list):
                for item in content:
                    if item.get("type") == "image_url":
                        img = self._decode_image_url(item["image_url"]["url"])
                        if img is not None:
                            images.append(img)

        # 构建输入
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

        # 移动到模型所在设备
        inputs = {k: v.to(self._model.device) for k, v in inputs.items()}

        # 生成
        import torch
        with torch.no_grad():
            generated_ids = self._model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                do_sample=temperature > 0,
                temperature=temperature if temperature > 0 else None,
            )

        # 解码输出
        generated_ids_trimmed = [
            out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs["input_ids"], generated_ids)
        ]
        output_text = self._processor.batch_decode(
            generated_ids_trimmed,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )[0]

        return output_text

    def analyze_screen(
        self,
        screenshot: np.ndarray,
        instruction: str,
        history: Optional[List] = None
    ) -> Dict[str, Any]:
        """
        分析屏幕截图（兼容 VLMClient.analyze_screen 接口）

        Args:
            screenshot: 屏幕截图 (numpy 数组)
            instruction: 用户指令
            history: 历史操作记录

        Returns:
            解析后的决策字典
        """
        from . import prompts

        system_prompt = prompts.get_system_prompt(mode="desktop", include_examples=True)

        content = [
            {"type": "text", "text": f"任务指令: {instruction}\n\n请分析当前屏幕并提供下一步操作。"},
            {"type": "image_url", "image_url": {"url": self._encode_image(screenshot)}},
        ]

        if history:
            history_text = self._format_history(history)
            content[0]["text"] += f"\n\n历史操作:\n{history_text}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content},
        ]

        response = self.chat(messages)
        return self._parse_response(response)

    def _messages_to_prompt(self, messages: List[Dict]) -> str:
        """将 OpenAI 格式消息转为纯文本提示"""
        lines = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if isinstance(content, list):
                text_parts = [item.get("text", "") for item in content if item.get("type") == "text"]
                content = "\n".join(text_parts)
            lines.append(f"<|{role}|>\n{content}")
        lines.append("<|assistant|>")
        return "\n".join(lines)

    def _encode_image(self, image: np.ndarray) -> str:
        """将 numpy 图像转为 base64 data URL"""
        pil_image = Image.fromarray(image)
        max_size = (1024, 1024)
        pil_image.thumbnail(max_size, Image.Resampling.LANCZOS)
        import io
        buffer = io.BytesIO()
        pil_image.save(buffer, format="JPEG", quality=85)
        base64_data = buffer.getvalue().hex() if hasattr(buffer, 'hex') else buffer.getvalue()
        # 实际上 qwen processor 需要 PIL Image 对象，不需要 base64
        return "data:image/jpeg;base64," + buffer.getvalue().decode('latin1')

    def _decode_image_url(self, url: str) -> Optional[Image.Image]:
        """从 data URL 解码图像"""
        if url.startswith("data:image"):
            import base64
            base64_data = url.split(",")[1]
            img_data = base64.b64decode(base64_data)
            return Image.open(io.BytesIO(img_data)).convert("RGB")
        return None

    def _format_history(self, history: List[Dict]) -> str:
        """格式化历史记录"""
        lines = []
        for i, item in enumerate(history[-5:], 1):
            action = item.get("decision", {}).get("action", "unknown")
            target = item.get("decision", {}).get("target", "")
            thought = item.get("decision", {}).get("thought", "")
            lines.append(f"{i}. {action}(target={target}) - {thought[:50]}...")
        return "\n".join(lines) if lines else "无"

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """解析响应，提取 JSON"""
        import re
        try:
            json_match = re.search(r'```json\s*\n(.*?)\n```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_match = re.search(r'(\{.*\})', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_str = response
            result = json.loads(json_str)
            for key in ["action", "target", "value", "delay", "is_task_complete", "observation", "thought", "confidence"]:
                if key not in result:
                    result[key] = "" if key in ("target", "value", "observation", "thought") else (
                        2.0 if key == "delay" else (False if key == "is_task_complete" else (0.5 if key == "confidence" else "screenshot"))
                    )
                    if key == "action":
                        result[key] = "screenshot"
            return result
        except json.JSONDecodeError:
            return {
                "observation": "无法解析为JSON",
                "thought": response[:200],
                "action": "screenshot",
                "target": "",
                "value": "",
                "delay": 2.0,
                "is_task_complete": False,
                "confidence": 0.3,
            }

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "quantization": "4bit" if self.load_in_4bit else ("8bit" if self.load_in_8bit else "none"),
            "loaded": self._is_loaded,
            "cache_dir": self.cache_dir,
        }