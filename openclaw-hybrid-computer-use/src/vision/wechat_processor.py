"""
微信自然语言处理器

解析用户的自然语言指令，执行微信发送消息操作。

支持的自然语言示例：
- "给张三发消息说晚上好"
- "告诉李四明天开会"
- "给工作群发收到"
- "发个消息给王五，内容是项目完成了"
- "通知技术群上线发布了"
"""

import sys
import re
import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# 修复编码（延迟执行，避免导入时出错）
def _fix_encoding():
    if sys.platform == "win32":
        try:
            import io
            if sys.stdout and hasattr(sys.stdout, 'buffer'):
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        except:
            pass


@dataclass
class WeChatCommand:
    """解析后的微信命令"""
    contact: str          # 联系人/群聊名称
    message: str          # 消息内容
    confidence: float     # 解析置信度 (0-1)
    raw_text: str         # 原始文本


class WeChatNaturalLanguageProcessor:
    """微信自然语言处理器"""
    
    # 匹配模式
    PATTERNS = [
        # 模式1: 给XXX发消息说XXX
        r'给\s*([^发说,，。\s]+)\s*(?:发消息|发微信|发信息)?\s*(?:说|告诉|讲)?\s*[,，:：]?\s*(.+)',
        
        # 模式2: 告诉XXX XXX
        r'告诉\s*([^说,，。\s]+)\s*[,，:：]?\s*(.+)',
        
        # 模式3: 通知XXX XXX
        r'通知\s*([^说,，。\s]+)\s*[,，:：]?\s*(.+)',
        
        # 模式4: 跟XXX说 XXX
        r'跟\s*([^说,，。\s]+)\s*(?:说|讲|告诉)?\s*[,，:：]?\s*(.+)',
    ]
    
    # 常见联系人别名映射
    CONTACT_ALIASES = {
        '文件传输助手': ['文件助手', '传输助手', '文件传输', '自己'],
        '我': ['文件传输助手', '我自己'],
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def parse(self, text: str) -> Optional[WeChatCommand]:
        """
        解析自然语言指令
        
        Args:
            text: 用户输入的自然语言
            
        Returns:
            解析成功返回 WeChatCommand，失败返回 None
        """
        text = text.strip()
        self.logger.info(f"解析指令: {text}")
        
        # 尝试所有模式
        for i, pattern in enumerate(self.PATTERNS):
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                contact = match.group(1).strip()
                message = match.group(2).strip()
                
                # 清理标点
                contact = contact.rstrip('，。！？,!?')
                message = message.rstrip('，。')
                
                # 检查别名
                contact = self._resolve_alias(contact)
                
                confidence = 0.9 if i < 3 else 0.7  # 前3个模式更可靠
                
                self.logger.info(f"匹配模式 {i+1}: contact={contact}, message={message}")
                
                return WeChatCommand(
                    contact=contact,
                    message=message,
                    confidence=confidence,
                    raw_text=text
                )
        
        # 如果都没匹配，尝试简单提取
        return self._fallback_parse(text)
    
    def _resolve_alias(self, name: str) -> str:
        """解析联系人别名"""
        for real_name, aliases in self.CONTACT_ALIASES.items():
            if name in aliases or name == real_name:
                return real_name
        return name
    
    def _fallback_parse(self, text: str) -> Optional[WeChatCommand]:
        """备用解析策略"""
        # 尝试找出"给"和"说"之间的内容
        if '给' in text and ('说' in text or '发' in text):
            parts = text.split('给', 1)
            if len(parts) == 2:
                rest = parts[1]
                # 找分隔点
                for sep in ['说', '发消息', '发信息', '发微信', '告诉']:
                    if sep in rest:
                        contact_part, message_part = rest.split(sep, 1)
                        contact = contact_part.strip('，。！？,!?')
                        message = message_part.strip('，。！？,!?')
                        if contact and message:
                            return WeChatCommand(
                                contact=contact,
                                message=message,
                                confidence=0.5,
                                raw_text=text
                            )
        return None
    
    def parse_with_llm(self, text: str, vlm_client=None) -> Optional[WeChatCommand]:
        """
        使用 LLM 解析（当规则匹配失败时使用）
        
        Args:
            text: 用户输入
            vlm_client: VLM 客户端（可选）
            
        Returns:
            WeChatCommand 或 None
        """
        # 先尝试规则匹配
        result = self.parse(text)
        if result and result.confidence >= 0.7:
            return result
        
        # 如果规则匹配失败或置信度低，使用 LLM
        if vlm_client:
            return self._parse_with_llm_helper(text, vlm_client)
        
        return result
    
    def _parse_with_llm_helper(self, text: str, vlm_client) -> Optional[WeChatCommand]:
        """使用 LLM 辅助解析"""
        prompt = f"""
解析用户的微信发送消息指令。

用户指令: "{text}"

请提取以下信息并以 JSON 格式返回:
{{
    "contact": "联系人或群聊名称",
    "message": "要发送的消息内容",
    "is_wechat_command": true/false
}}

注意:
- contact 应该是微信中的实际显示名称
- message 应该是完整的消息内容
- 如果不是微信发送消息指令，is_wechat_command 设为 false
"""
        try:
            # 这里简化处理，实际应该调用 vlm_client
            # 暂时返回 None，让系统提示用户使用标准格式
            return None
        except Exception as e:
            self.logger.error(f"LLM 解析失败: {e}")
            return None


def parse_wechat_command(text: str) -> Optional[Tuple[str, str]]:
    """
    快速解析函数
    
    Args:
        text: 自然语言指令
        
    Returns:
        (contact, message) 元组，解析失败返回 None
        
    Example:
        >>> parse_wechat_command("给张三发消息说晚上好")
        ('张三', '晚上好')
    """
    processor = WeChatNaturalLanguageProcessor()
    result = processor.parse(text)
    
    if result:
        return (result.contact, result.message)
    return None


# 测试
if __name__ == "__main__":
    import sys
    
    processor = WeChatNaturalLanguageProcessor()
    
    # 测试用例
    test_cases = [
        "给张三发消息说晚上好",
        "告诉李四明天开会",
        "给工作群发收到",
        "发个消息给王五，内容是项目完成了",
        "通知技术群上线发布了",
        "跟小明说晚上一起吃饭",
        "给文件传输助手发测试消息",
        "告诉老板会议改期了",
    ]
    
    print("=" * 60)
    print("微信自然语言处理器测试")
    print("=" * 60)
    
    for text in test_cases:
        result = processor.parse(text)
        if result:
            print(f"\n输入: {text}")
            print(f"  → 联系人: {result.contact}")
            print(f"  → 消息: {result.message}")
            print(f"  → 置信度: {result.confidence}")
        else:
            print(f"\n输入: {text}")
            print(f"  → 解析失败")
    
    print("\n" + "=" * 60)
    
    # 交互测试
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
        print(f"\n测试: {text}")
        result = processor.parse(text)
        if result:
            print(f"解析结果:")
            print(f"  联系人: {result.contact}")
            print(f"  消息: {result.message}")
        else:
            print("无法解析，请使用格式: 给XXX发消息说XXX")
