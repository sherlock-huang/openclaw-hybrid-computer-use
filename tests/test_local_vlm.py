"""本地 VLM 测试"""

import pytest
import numpy as np

from claw_desktop.vision.local_vlm import LocalVLMClient


class TestLocalVLMClient:
    def test_init_not_loaded(self):
        client = LocalVLMClient()
        assert client._is_loaded is False
        assert client.model_name == "Qwen/Qwen2-VL-2B-Instruct"

    def test_get_model_info(self):
        client = LocalVLMClient(model_name="test-model", load_in_4bit=True)
        info = client.get_model_info()
        assert info["model_name"] == "test-model"
        assert info["quantization"] == "4bit"
        assert info["loaded"] is False

    def test_parse_response_json(self):
        client = LocalVLMClient()
        response = '"""json\n{"action": "click", "target": "button", "confidence": 0.9}\n"""'
        result = client._parse_response(response)
        assert result["action"] == "click"
        assert result["target"] == "button"
        assert result["confidence"] == 0.9

    def test_parse_response_plain_text(self):
        client = LocalVLMClient()
        result = client._parse_response("just some text")
        assert result["action"] == "screenshot"
        assert "_parse_error" not in result  # fallback to screenshot

    def test_messages_to_prompt(self):
        client = LocalVLMClient()
        messages = [
            {"role": "system", "content": "You are a helper."},
            {"role": "user", "content": "Hello"},
        ]
        prompt = client._messages_to_prompt(messages)
        assert "<|system|>" in prompt
        assert "<|user|>" in prompt
        assert "<|assistant|>" in prompt
        assert "Hello" in prompt