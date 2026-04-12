"""VLM 客户端 - 封装多模态 AI 调用

支持 OpenAI 和 Anthropic 提供商，包含重试和验证机制。
"""

import base64
import json
import logging
import re
import time
from typing import Optional, Dict, Any, List
from io import BytesIO

import numpy as np
from PIL import Image

# 导入提示词模块
from . import prompts

logger = logging.getLogger(__name__)


class VLMClient:
    """视觉语言模型客户端"""
    
    SUPPORTED_PROVIDERS = {"openai", "anthropic", "kimi", "kimi-coding"}
    
    def __init__(
        self, 
        provider: str = "openai", 
        api_key: Optional[str] = None, 
        model: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        mode: str = "browser"
    ):
        """
        初始化 VLM 客户端
        
        Args:
            provider: "openai", "anthropic", "kimi" 或 "kimi-coding"
            api_key: API 密钥，默认从环境变量读取
            model: 模型名称，默认使用 provider 的推荐模型
            max_retries: 最大重试次数
            retry_delay: 重试间隔（秒）
            mode: 操作模式 "browser" 或 "desktop"
        """
        if provider not in self.SUPPORTED_PROVIDERS:
            raise ValueError(f"不支持的 provider: {provider}. 支持: {self.SUPPORTED_PROVIDERS}")
        
        self.provider = provider
        self.api_key = api_key or self._get_api_key_from_env()
        self.model = model or self._get_default_model()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.mode = mode
        
        self._client = None
        self._init_client()
        
        logger.info(f"VLMClient 初始化: provider={provider}, model={self.model}, mode={mode}")
    
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
        elif self.provider == "kimi":
            key = os.getenv("KIMI_API_KEY")
            if not key:
                raise ValueError("未设置 KIMI_API_KEY 环境变量")
            return key
        elif self.provider == "kimi-coding":
            key = os.getenv("KIMI_CODING_API_KEY")
            if not key:
                raise ValueError("未设置 KIMI_CODING_API_KEY 环境变量")
            return key
    
    def _get_default_model(self) -> str:
        """获取默认模型"""
        if self.provider == "openai":
            return "gpt-4-vision-preview"
        elif self.provider == "anthropic":
            return "claude-3-sonnet-20240229"
        elif self.provider == "kimi":
            return "moonshot-v1-8k-vision-preview"
        elif self.provider == "kimi-coding":
            return "k2p5"
    
    def _init_client(self):
        """初始化底层客户端"""
        if self.provider == "openai":
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
        elif self.provider == "anthropic":
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.api_key)
        elif self.provider == "kimi":
            from openai import OpenAI
            # Kimi API 兼容 OpenAI 格式
            self._client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.moonshot.cn/v1"
            )
        elif self.provider == "kimi-coding":
            # Kimi Coding 使用 Anthropic API 格式
            import anthropic
            self._client = anthropic.Anthropic(
                api_key=self.api_key,
                base_url="https://api.kimi.com/coding/"
            )
    
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
    
    def chat(self, messages: List[Dict], max_tokens: int = 1024, temperature: float = 0.2) -> str:
        """
        发送对话请求
        
        Args:
            messages: 消息列表，支持文本和图像
            max_tokens: 最大返回 token 数
            temperature: 温度参数（0-1，越低越确定性）
            
        Returns:
            AI 回复文本
        """
        if self.provider == "openai":
            return self._chat_openai(messages, max_tokens, temperature)
        elif self.provider == "anthropic":
            return self._chat_anthropic(messages, max_tokens, temperature)
    
    def _chat_openai(self, messages: List[Dict], max_tokens: int, temperature: float) -> str:
        """OpenAI GPT-4V 调用"""
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API 调用失败: {e}")
            raise
    
    def _chat_anthropic(self, messages: List[Dict], max_tokens: int, temperature: float) -> str:
        """Anthropic Claude 3 调用"""
        try:
            # 转换消息格式
            system_msg = None
            anthropic_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_msg = msg["content"]
                else:
                    anthropic_messages.append(msg)
            
            kwargs = {
                "model": self.model,
                "messages": anthropic_messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            if system_msg:
                kwargs["system"] = system_msg
            
            response = self._client.messages.create(**kwargs)
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API 调用失败: {e}")
            raise
    
    def analyze_screen(
        self, 
        screenshot: np.ndarray, 
        instruction: str, 
        history: Optional[List] = None
    ) -> Dict[str, Any]:
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
        
        # 构建用户消息
        content = [
            {"type": "text", "text": f"任务指令: {instruction}\n\n请分析当前屏幕并提供下一步操作。"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
        ]
        
        # 添加历史上下文
        if history:
            history_text = self._format_history(history)
            content[0]["text"] += f"\n\n历史操作:\n{history_text}"
        
        # 构建消息
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ]
        
        # 调用 API
        response = self.chat(messages)
        
        # 解析响应
        return self._parse_response(response)
    
    def analyze_screen_with_fallback(
        self,
        screenshot: np.ndarray,
        instruction: str,
        history: Optional[List] = None,
        validate: bool = True,
        auto_fix: bool = True
    ) -> Dict[str, Any]:
        """
        分析屏幕截图，带重试和验证机制
        
        Args:
            screenshot: 屏幕截图
            instruction: 用户指令
            history: 历史操作记录
            validate: 是否验证决策
            auto_fix: 是否自动修复无效决策
            
        Returns:
            解析后的决策字典
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"分析屏幕尝试 {attempt + 1}/{self.max_retries}")
                
                # 调用基础分析
                decision = self.analyze_screen(screenshot, instruction, history)
                
                # 验证决策
                if validate:
                    is_valid, issues = self._validate_decision(decision)
                    
                    if not is_valid:
                        logger.warning(f"决策验证失败: {issues}")
                        
                        if auto_fix:
                            # 尝试修复
                            fixed_decision = prompts.fix_decision(decision, issues, self.mode)
                            logger.info(f"自动修复决策: {decision} -> {fixed_decision}")
                            return fixed_decision
                        else:
                            # 不重试，直接返回带有警告的决策
                            decision["_validation_issues"] = issues
                            decision["_valid"] = False
                            return decision
                
                # 添加元数据
                decision["_attempt"] = attempt + 1
                decision["_valid"] = True
                
                return decision
                
            except Exception as e:
                last_error = e
                logger.warning(f"第 {attempt + 1} 次尝试失败: {e}")
                
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (attempt + 1)
                    logger.info(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
        
        # 所有重试都失败，返回错误决策
        logger.error(f"所有 {self.max_retries} 次尝试都失败")
        return {
            "observation": f"API 调用失败: {str(last_error)}",
            "thought": "多次尝试后仍然失败，需要人工干预",
            "action": "screenshot",
            "target": "",
            "value": "",
            "delay": 2.0,
            "is_task_complete": False,
            "confidence": 0.0,
            "_error": str(last_error),
            "_attempt": self.max_retries,
            "_valid": False
        }
    
    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        return prompts.get_system_prompt(mode=self.mode, include_examples=True)
    
    def _format_history(self, history: List[Dict]) -> str:
        """格式化历史记录为文本"""
        lines = []
        for i, item in enumerate(history[-5:], 1):  # 只保留最近5条
            action = item.get("decision", {}).get("action", "unknown")
            target = item.get("decision", {}).get("target", "")
            thought = item.get("decision", {}).get("thought", "")
            lines.append(f"{i}. {action}(target={target}) - {thought[:50]}...")
        return "\n".join(lines) if lines else "无"
    
    def _parse_response(self, response: Optional[str]) -> Dict[str, Any]:
        """解析 AI 响应，提取 JSON"""
        if not response:
            logger.error("API 返回空响应")
            return self._get_default_response("API 返回空响应")
        
        try:
            # 寻找 JSON 代码块
            json_match = re.search(r'```json\s*\n(.*?)\n```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试直接解析（可能是纯JSON）
                json_match = re.search(r'(\{.*\})', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_str = response
            
            result = json.loads(json_str)
            
            # 确保必要字段存在
            if "action" not in result:
                result["action"] = "screenshot"
            if "target" not in result:
                result["target"] = ""
            if "value" not in result:
                result["value"] = ""
            if "delay" not in result:
                result["delay"] = 2.0
            if "is_task_complete" not in result:
                result["is_task_complete"] = False
            if "observation" not in result:
                result["observation"] = ""
            if "thought" not in result:
                result["thought"] = ""
            if "confidence" not in result:
                result["confidence"] = 0.5
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"解析 JSON 失败: {e}")
            logger.error(f"原始响应: {response[:500]}")
            
            # 尝试从文本中提取关键信息
            return self._extract_from_text(response)
    
    def _extract_from_text(self, response: str) -> Dict[str, Any]:
        """从非JSON响应中提取关键信息"""
        result = {
            "observation": "无法解析为JSON格式",
            "thought": response[:200] if response else "AI 返回了非JSON格式",
            "action": "screenshot",
            "target": "",
            "value": "",
            "delay": 2.0,
            "is_task_complete": False,
            "confidence": 0.3,
            "_parse_error": True
        }
        
        # 尝试识别 action
        action_patterns = [
            (r'\bclick\b', 'click'),
            (r'\btype\b|\binput\b|\benter\b', 'type'),
            (r'\bscroll\b', 'scroll'),
            (r'\bwait\b', 'wait'),
            (r'\bfinish\b|\bcomplete\b|\bdone\b', 'finish'),
        ]
        
        response_lower = response.lower()
        for pattern, action in action_patterns:
            if re.search(pattern, response_lower):
                result["action"] = action
                result["thought"] = f"[从文本推断] {response[:200]}"
                break
        
        return result
    
    def _validate_decision(self, decision: Dict[str, Any]) -> tuple[bool, List[str]]:
        """验证决策有效性
        
        Args:
            decision: 决策字典
            
        Returns:
            (是否有效, 问题列表)
        """
        return prompts.validate_decision(decision, self.mode)
    
    def validate_and_reflect(
        self,
        decision: Dict[str, Any],
        screenshot_before: np.ndarray,
        screenshot_after: np.ndarray,
        expected_effect: str
    ) -> Dict[str, Any]:
        """验证操作结果并反思
        
        Args:
            decision: 执行的决策
            screenshot_before: 操作前的截图
            screenshot_after: 操作后的截图
            expected_effect: 预期效果描述
            
        Returns:
            反思结果
        """
        # 编码两张截图
        before_b64 = self._encode_image(screenshot_before)
        after_b64 = self._encode_image(screenshot_after)
        
        # 构建反思提示
        reflection_prompt = prompts.get_reflection_prompt(decision, expected_effect)
        
        messages = [
            {"role": "system", "content": "你是操作验证助手，负责验证自动化操作是否成功执行。"},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": reflection_prompt},
                    {"type": "text", "text": "操作前截图:"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{before_b64}"}},
                    {"type": "text", "text": "操作后截图:"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{after_b64}"}}
                ]
            }
        ]
        
        try:
            response = self.chat(messages, max_tokens=512)
            
            # 尝试解析JSON响应
            try:
                json_match = re.search(r'(\{.*\})', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))
            except:
                pass
            
            # 返回文本响应
            return {
                "success": "success" in response.lower() or "成功" in response,
                "observation": response[:500],
                "adjustment_needed": "fail" in response.lower() or "失败" in response or "error" in response.lower(),
                "new_strategy": ""
            }
            
        except Exception as e:
            logger.error(f"验证反思失败: {e}")
            return {
                "success": False,
                "observation": f"验证过程出错: {str(e)}",
                "adjustment_needed": True,
                "new_strategy": "重试操作"
            }
    
    def switch_mode(self, mode: str):
        """切换操作模式
        
        Args:
            mode: "browser" 或 "desktop"
        """
        if mode not in ("browser", "desktop"):
            raise ValueError(f"无效的模式: {mode}，必须是 'browser' 或 'desktop'")
        
        self.mode = mode
        logger.info(f"切换到 {mode} 模式")
    
    def get_token_estimate(self, image: np.ndarray) -> int:
        """估算图像的 token 数量
        
        Args:
            image: numpy 图像数组
            
        Returns:
            估算的 token 数量
        """
        h, w = image.shape[:2]
        
        # OpenAI vision 计费规则：
        # 图片先缩放到 2048x2048 以内（保持比例）
        # 然后短边调整到 768px
        # 每 512x512 区域约 85 tokens
        
        # 简化估算：
        # 1024x1024 ~ 765 tokens
        # 512x512 ~ 255 tokens
        
        if h > 1024 or w > 1024:
            return 1000
        elif h > 512 or w > 512:
            return 500
        else:
            return 300

    def _get_default_response(self, reason: str = "未知错误") -> Dict[str, Any]:
        """获取默认响应"""
        return {
            "observation": reason,
            "thought": "使用默认安全操作",
            "action": "screenshot",
            "target": "",
            "value": "",
            "delay": 2.0,
            "is_task_complete": False,
            "confidence": 0.1
        }
