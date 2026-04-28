"""本地 VLM 客户端测试"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from PIL import Image

from src.vision.local_vlm_client import LocalVLMClient
from src.core.config import Config


class TestLocalVLMClient:
    """测试本地 VLM 客户端"""

    def test_initialization(self):
        """测试初始化（延迟加载，不触发模型加载）"""
        client = LocalVLMClient(
            model_name="Qwen/Qwen2-VL-2B-Instruct",
            device="cpu",
            load_in_4bit=False,
        )
        assert client.model_name == "Qwen/Qwen2-VL-2B-Instruct"
        assert client.device == "cpu"
        assert client._model is None
        assert client._processor is None

    def test_default_values(self):
        """测试默认值"""
        client = LocalVLMClient()
        assert client.model_name == LocalVLMClient.DEFAULT_MODEL
        assert client.device == "auto"
        assert client.max_tokens == 1024
        assert client.temperature == 0.2

    def test_encode_image(self):
        """测试图像编码"""
        client = LocalVLMClient()
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        pil_img = client._encode_image(img)
        assert isinstance(pil_img, Image.Image)
        assert pil_img.size == (100, 100)

    def test_encode_image_float(self):
        """测试浮点图像编码"""
        client = LocalVLMClient()
        img = np.random.rand(50, 50, 3).astype(np.float32)
        pil_img = client._encode_image(img)
        assert isinstance(pil_img, Image.Image)

    def test_parse_response_valid_json(self):
        """测试解析有效的 JSON 响应"""
        client = LocalVLMClient()
        response = json.dumps({"action": "click", "target": "100,200", "confidence": 0.85})
        result = client._parse_response(response)
        assert result["action"] == "click"
        assert result["target"] == "100,200"
        assert result["confidence"] == 0.85

    def test_parse_response_with_code_block(self):
        """测试解析带有代码块的 JSON 响应"""
        client = LocalVLMClient()
        response = '```json\n{"action": "scroll", "value": "500"}\n```'
        result = client._parse_response(response)
        assert result["action"] == "scroll"
        assert result["value"] == "500"

    def test_parse_response_invalid(self):
        """测试解析无效的响应"""
        client = LocalVLMClient()
        result = client._parse_response("not json")
        assert result["confidence"] == 0.1
        assert result["action"] == "screenshot"

    def test_parse_response_empty(self):
        """测试解析空响应"""
        client = LocalVLMClient()
        result = client._parse_response("")
        assert result["confidence"] == 0.1

    def test_default_response(self):
        """测试默认响应"""
        client = LocalVLMClient()
        result = client._default_response("test error")
        assert result["observation"] == "test error"
        assert result["confidence"] == 0.1
        assert result["is_task_complete"] is False

    def test_config_integration(self):
        """测试 Config 集成"""
        config = Config()
        assert config.local_vlm_enabled is True
        assert config.local_vlm_model == "Qwen/Qwen2-VL-2B-Instruct"
        assert config.local_vlm_device == "auto"
        assert config.local_vlm_cache_dir == "models/cache"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
