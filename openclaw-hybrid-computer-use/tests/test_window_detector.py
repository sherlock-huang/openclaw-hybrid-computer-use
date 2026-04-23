"""WindowDetector 测试"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestWindowDetector:
    """WindowDetector 测试类"""
    
    def test_is_browser_window_chrome(self):
        """测试识别 Chrome 窗口"""
        from claw_desktop.recording.window_detector import is_browser_window
        
        assert is_browser_window("抖音 - Google Chrome") is True
        assert is_browser_window("GitHub: Let's build from here - Chrome") is True
    
    def test_is_browser_window_edge(self):
        """测试识别 Edge 窗口"""
        from claw_desktop.recording.window_detector import is_browser_window
        
        assert is_browser_window("Bing - Microsoft Edge") is True
    
    def test_is_browser_window_notepad(self):
        """测试识别非浏览器窗口"""
        from claw_desktop.recording.window_detector import is_browser_window
        
        assert is_browser_window("无标题 - 记事本") is False
        assert is_browser_window("计算器") is False
    
    def test_get_active_window_title(self):
        """测试获取当前窗口标题"""
        from claw_desktop.recording.window_detector import get_active_window_title
        
        title = get_active_window_title()
        assert isinstance(title, str) or title is None

