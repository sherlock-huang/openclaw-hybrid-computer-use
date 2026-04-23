"""BrowserController 测试"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestBrowserController:
    """BrowserController 测试类"""
    
    def test_controller_creation(self):
        """测试创建 BrowserController"""
        from src.browser.controller import BrowserController
        
        controller = BrowserController(browser_type="chromium", headless=True)
        
        assert controller.browser_type == "chromium"
        assert controller.headless is True
        assert controller.is_running is False
    
    def test_controller_launch_and_close(self):
        """测试启动和关闭浏览器"""
        from src.browser.controller import BrowserController
        
        controller = BrowserController(headless=True)
        
        # 启动前状态
        assert controller.is_running is False
        
        # 启动
        controller.launch()
        assert controller.is_running is True
        assert controller.page is not None
        
        # 关闭
        controller.close()
        assert controller.is_running is False
