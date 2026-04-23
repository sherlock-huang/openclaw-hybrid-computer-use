"""键盘控制器"""

import logging
from typing import List, Optional

import pyautogui

from ..core.config import Config


class KeyboardController:
    """键盘控制器"""
    
    # 常用按键映射
    KEY_MAPPING = {
        "enter": "return",
        "return": "return",
        "esc": "escape",
        "escape": "escape",
        "space": "space",
        "tab": "tab",
        "backspace": "backspace",
        "delete": "delete",
        "ctrl": "ctrl",
        "control": "ctrl",
        "alt": "alt",
        "shift": "shift",
        "win": "win",
        "command": "command",
        "up": "up",
        "down": "down",
        "left": "left",
        "right": "right",
        "home": "home",
        "end": "end",
        "pageup": "pageup",
        "pagedown": "pagedown",
        "f1": "f1", "f2": "f2", "f3": "f3", "f4": "f4",
        "f5": "f5", "f6": "f6", "f7": "f7", "f8": "f8",
        "f9": "f9", "f10": "f10", "f11": "f11", "f12": "f12",
    }
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.logger = logging.getLogger(__name__)
    
    def type_text(self, text: str, interval: float = 0.01):
        """
        输入文字
        
        Args:
            text: 要输入的文字
            interval: 每个字符之间的间隔(秒)
        """
        self.logger.debug(f"输入文字: {text[:20]}..." if len(text) > 20 else f"输入文字: {text}")
        pyautogui.typewrite(text, interval=interval)
    
    def press_key(self, key: str):
        """
        按下并释放单个键
        
        Args:
            key: 按键名称
        """
        key = self._normalize_key(key)
        self.logger.debug(f"按键: {key}")
        pyautogui.press(key)
    
    def hotkey(self, *keys: str):
        """
        按下组合键
        
        Args:
            *keys: 要按下的键序列，如 ('ctrl', 'c')
        """
        normalized_keys = [self._normalize_key(k) for k in keys]
        self.logger.debug(f"组合键: {'+'.join(normalized_keys)}")
        pyautogui.hotkey(*normalized_keys)
    
    def hold_key(self, key: str):
        """
        按住某个键 (配合release使用)
        
        Args:
            key: 按键名称
        """
        key = self._normalize_key(key)
        pyautogui.keyDown(key)
    
    def release_key(self, key: str):
        """
        释放某个键
        
        Args:
            key: 按键名称
        """
        key = self._normalize_key(key)
        pyautogui.keyUp(key)
    
    def press_sequence(self, keys: List[str], interval: float = 0.1):
        """
        按顺序按下多个键
        
        Args:
            keys: 按键列表
            interval: 按键间隔
        """
        for key in keys:
            self.press_key(key)
            if interval > 0:
                import time
                time.sleep(interval)
    
    def select_all(self):
        """全选 (Ctrl+A)"""
        self.hotkey("ctrl", "a")
    
    def copy(self):
        """复制 (Ctrl+C)"""
        self.hotkey("ctrl", "c")
    
    def paste(self):
        """粘贴 (Ctrl+V)"""
        self.hotkey("ctrl", "v")
    
    def cut(self):
        """剪切 (Ctrl+X)"""
        self.hotkey("ctrl", "x")
    
    def undo(self):
        """撤销 (Ctrl+Z)"""
        self.hotkey("ctrl", "z")
    
    def save(self):
        """保存 (Ctrl+S)"""
        self.hotkey("ctrl", "s")
    
    def _normalize_key(self, key: str) -> str:
        """标准化按键名称"""
        key = key.lower().strip()
        return self.KEY_MAPPING.get(key, key)
