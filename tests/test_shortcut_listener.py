"""快捷键监听器测试"""

import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_shortcut_listener_creation():
    """Test creating ShortcutListener"""
    from src.utils.shortcut_listener import ShortcutListener
    
    callback_called = False
    
    def callback():
        nonlocal callback_called
        callback_called = True
    
    listener = ShortcutListener(callback, shortcut="<ctrl>+r")
    
    assert listener.toggle_callback == callback
    assert listener.shortcut == "<ctrl>+r"
    assert listener.is_listening == False


def test_shortcut_listener_start_stop():
    """Test start and stop methods exist"""
    from src.utils.shortcut_listener import ShortcutListener
    
    listener = ShortcutListener(lambda: None)
    
    assert hasattr(listener, 'start')
    assert hasattr(listener, 'stop')
