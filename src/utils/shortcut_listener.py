"""全局快捷键监听器"""

from pynput import keyboard
from typing import Callable, Optional
import threading


class ShortcutListener:
    """全局快捷键监听器"""
    
    def __init__(self, 
                 toggle_callback: Callable[[], None],
                 shortcut: str = "<ctrl>+r"):
        """
        Args:
            toggle_callback: 快捷键触发时的回调函数
            shortcut: 快捷键组合，默认 "<ctrl>+r"
        """
        self.toggle_callback = toggle_callback
        self.shortcut = shortcut
        self.is_listening = False
        self._listener: Optional[keyboard.Listener] = None
        self._hotkey = None
    
    def start(self):
        """开始监听快捷键"""
        if self.is_listening:
            return
        
        self.is_listening = True
        
        # 创建热键
        self._hotkey = keyboard.HotKey(
            keyboard.HotKey.parse(self.shortcut),
            self.toggle_callback
        )
        
        # 按键处理函数
        def on_press(key):
            self._hotkey.press(key)
        
        def on_release(key):
            self._hotkey.release(key)
        
        # 启动监听器
        self._listener = keyboard.Listener(
            on_press=on_press,
            on_release=on_release,
            suppress=False  # 不阻止按键传递到系统
        )
        self._listener.start()
    
    def stop(self):
        """停止监听"""
        self.is_listening = False
        if self._listener:
            self._listener.stop()
            self._listener = None
        self._hotkey = None
