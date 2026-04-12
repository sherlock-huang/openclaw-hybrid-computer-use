"""VLM 客户端 - 封装多模态 AI 调用"""

import base64
import logging
from typing import Optional, Dict, Any, List
from io import BytesIO
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class VLMClient:
    """视觉语言模型客户端"""
    
    SUPPORTED_PROVIDERS = {"openai", "anthropic"}
    
    def __init__(self, provider: str = "openai", api_key: Optional[str] = None, model: Optional[str] = None):
        """
        初始化 VLM 客户端
        
        Args:
            provider: "openai" 或 "anthropic"
            api_key: API 密钥，默认从环境变量读取
            model: 模型名称，默认使用 provider 的推荐模型
        """
        if provider not in self.SUPPORTED_PROVIDERS:
            raise ValueError(f"不支持的 provider: {provider}. 支持: {self.SUPPORTED_PROVIDERS}")
        
        self.provider = provider
        self.api_key = api_key or self._get_api_key_from_env()
        self.model = model or self._get_default_model()
        
        self._client = None
        self._init_client()
        
        logger.info(f"VLMClient 初始化: provider={provider}, model={self.model}")
    
    def _get_api_key_from_env(self) -> str:
        """从环境变量获取 API Key"""
        import os
        if self.provider == "openai":
            key = os.getenv("OPENAI_API_KEY")
            if not key:
                raise ValueError("未设置 OPENAI_API_KEY 环境变量")
            return key
        elif self.provider == "anthropic":
            key = os.getenv("ANTHROPIC_API_KEY")
            if not key:
                raise ValueError("未设置 ANTHROPIC_API_KEY 环境变量")
            return key
    
    def _get_default_model(self) -> str:
        """获取默认模型"""
        if self.provider == "openai":
            return "gpt-4-vision-preview"
        elif self.provider == "anthropic":
            return "claude-3-sonnet-20240229"
    
    def _init_client(self):
        """初始化底层客户端"""
        if self.provider == "openai":
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
        elif self.provider == "anthropic":
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.api_key)
    
    def _encode_image(self, image: np.ndarray) -> str:
        """
        将 numpy 图像转为 base64 字符串
        
        Args:
            image: numpy 数组 (H, W, C)
            
        Returns:
            base64 编码的图像
        """
        # 转换为 PIL Image
        pil_image = Image.fromarray(image)
        
        # 压缩以节省 token
        max_size = (1024, 1024)
        pil_image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # 转为 base64
        buffer = BytesIO()
        pil_image.save(buffer, format="JPEG", quality=85)
        base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return base64_image
    
    def chat(self, messages: List[Dict], max_tokens: int = 1024) -> str:
        """
        发送对话请求
        
        Args:
            messages: 消息列表，支持文本和图像
            max_tokens: 最大返回 token 数
            
        Returns:
            AI 回复文本
        """
        if self.provider == "openai":
            return self._chat_openai(messages, max_tokens)
        elif self.provider == "anthropic":
            return self._chat_anthropic(messages, max_tokens)
    
    def _chat_openai(self, messages: List[Dict], max_tokens: int) -> str:
        """OpenAI GPT-4V 调用"""
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.2  # 低温度，更确定性
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API 调用失败: {e}")
            raise
    
    def _chat_anthropic(self, messages: List[Dict], max_tokens: int) -> str:
        """Anthropic Claude 3 调用"""
        try:
            # 转换消息格式
            anthropic_messages = self._convert_to_anthropic_format(messages)
            
            response = self._client.messages.create(
                model=self.model,
                messages=anthropic_messages,
                max_tokens=max_tokens,
                temperature=0.2
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API 调用失败: {e}")
            raise
    
    def _convert_to_anthropic_format(self, messages: List[Dict]) -> List[Dict]:
        """将 OpenAI 格式转为 Anthropic 格式"""
        # 简化处理，实际可能需要更复杂的转换
        return messages
    
    def analyze_screen(self, screenshot: np.ndarray, instruction: str, history: Optional[List] = None) -> Dict[str, Any]:
        """
        分析屏幕截图，返回操作建议
        
        Args:
            screenshot: 屏幕截图 (numpy 数组)
            instruction: 用户指令
            history: 历史操作记录
            
        Returns:
            解析后的决策字典
        """
        # 编码图像
        base64_image = self._encode_image(screenshot)
        
        # 构建系统提示词
        system_prompt = self._build_system_prompt()
        
        # 构建消息
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user", 
                "content": [
                    {"type": "text", "text": f"任务指令: {instruction}"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ]
        
        # 调用 API
        response = self.chat(messages)
        
        # 解析响应
        return self._parse_response(response)
    
    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        return """你是 OpenClaw，一个智能桌面自动化助手。

你的任务是分析屏幕截图，帮助用户完成指定的任务。

可用操作：
1. click(x, y) 或 click(selector) - 点击元素
2. type(text) - 输入文字
3. scroll(amount) - 滚动页面（正数向下，负数向上）
4. wait(seconds) - 等待
5. screenshot() - 截图
6. finish() - 任务完成

返回格式必须是 JSON：
{
    "observation": "描述当前屏幕状态",
    "thought": "分析思考过程，为什么选择这个操作",
    "action": "click/type/scroll/wait/screenshot/finish",
    "target": "选择器如 #search-input，或坐标如 500,300",
    "value": "输入的文字（仅type操作）",
    "delay": 2.0,
    "is_task_complete": false
}

重要：
- 每次只执行一个操作
- 优先使用 ID 选择器，其次 class，最后坐标
- 操作后等待页面响应
- 任务完成时必须设置 is_task_complete: true"""
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """解析 AI 响应，提取 JSON"""
        import json
        import re
        
        # 尝试提取 JSON
        try:
            # 寻找 JSON 代码块
            json_match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试直接解析
                json_str = response
            
            result = json.loads(json_str)
            
            # 验证必要字段
            required_fields = ["action", "target"]
            for field in required_fields:
                if field not in result:
                    result[field] = ""
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"解析 JSON 失败: {e}")
            logger.error(f"原始响应: {response}")
            # 返回默认操作
            return {
                "observation": "解析失败",
                "thought": "AI 返回格式不正确",
                "action": "screenshot",
                "target": "",
                "value": "",
                "delay": 1.0,
                "is_task_complete": False
            }
