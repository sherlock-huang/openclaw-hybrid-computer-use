"""鼠标键盘控制测试"""

import pytest
import time
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from claw_desktop import MouseController, KeyboardController


class TestMouseController:
    """测试鼠标控制"""
    
    def test_get_position(self):
        """测试获取鼠标位置"""
        mouse = MouseController()
        x, y = mouse.get_position()
        
        assert isinstance(x, int)
        assert isinstance(y, int)
        assert x >= 0 and y >= 0
    
    def test_move_to(self):
        """测试移动鼠标"""
        mouse = MouseController()
        
        # 移动到屏幕中心
        x, y = mouse.screen_width // 2, mouse.screen_height // 2
        mouse.move_to(x, y, duration=0.1)
        
        # 验证位置
        new_x, new_y = mouse.get_position()
        assert abs(new_x - x) < 5  # 允许小误差
        assert abs(new_y - y) < 5


class TestKeyboardController:
    """测试键盘控制"""
    
    def test_normalize_key(self):
        """测试按键名称标准化"""
        kb = KeyboardController()
        
        assert kb._normalize_key("ENTER") == "return"
        assert kb._normalize_key("esc") == "escape"
        assert kb._normalize_key("Ctrl") == "ctrl"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
