"""BrowserActionHandler 测试"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestBrowserActionHandler:
    """BrowserActionHandler 测试类"""
    
    @pytest.fixture
    def handler(self):
        """创建测试用的 handler"""
        from src.browser.controller import BrowserController
        from src.browser.actions import BrowserActionHandler
        
        controller = BrowserController(headless=True)
        controller.launch()
        
        handler = BrowserActionHandler(controller)
        yield handler
        
        controller.close()
    
    def test_goto(self, handler):
        """测试导航到 URL"""
        handler.goto("https://example.com")
        assert "Example Domain" in handler.controller.page.title()
    
    def test_click(self, handler):
        """测试点击元素"""
        handler.goto("https://example.com")
        handler.click("a")
        assert "iana.org" in handler.controller.page.url
    
    def test_type(self, handler):
        """测试输入文字"""
        handler.goto("https://httpbin.org/forms/post")
        handler.type("input[name='custname']", "Test User")
        value = handler.controller.page.input_value("input[name='custname']")
        assert value == "Test User"
    
    def test_scroll(self, handler):
        """测试滚动页面"""
        # 先设置一个可滚动的页面内容
        handler.goto("data:text/html,<body style='height: 2000px;'><h1>Scroll Test</h1></body>")
        handler.scroll(500)
        scroll_y = handler.controller.page.evaluate("() => window.scrollY")
        assert scroll_y == 500
    
    def test_screenshot(self, handler, tmp_path):
        """测试截图"""
        handler.goto("https://example.com")
        screenshot_path = tmp_path / "test.png"
        data = handler.screenshot(str(screenshot_path))
        assert screenshot_path.exists()
        assert data is not None
        assert len(data) > 0
