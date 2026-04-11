"""浏览器控制器 - 管理浏览器生命周期"""

import logging
from typing import Optional, Any
from playwright.sync_api import sync_playwright, Page, Browser

logger = logging.getLogger(__name__)


class BrowserController:
    """浏览器控制器"""
    
    SUPPORTED_BROWSERS = {"chromium", "firefox", "webkit"}
    
    def __init__(self, browser_type: str = "chromium", headless: bool = False):
        if browser_type not in self.SUPPORTED_BROWSERS:
            raise ValueError(f"不支持的浏览器类型: {browser_type}. 支持: {self.SUPPORTED_BROWSERS}")
        
        self.browser_type = browser_type
        self.headless = headless
        
        self._playwright: Optional[Any] = None
        self._browser: Optional[Browser] = None
        self._page: Optional[Page] = None
        
        logger.info(f"BrowserController 初始化: {browser_type}, headless={headless}")
    
    @property
    def is_running(self) -> bool:
        return self._browser is not None and self._page is not None
    
    @property
    def page(self) -> Optional[Page]:
        return self._page
    
    def launch(self) -> None:
        if self.is_running:
            logger.warning("浏览器已在运行")
            return
        
        try:
            self._playwright = sync_playwright().start()
            browser_launcher = getattr(self._playwright, self.browser_type)
            self._browser = browser_launcher.launch(headless=self.headless)
            self._page = self._browser.new_page()
            self._page.set_viewport_size({"width": 1920, "height": 1080})
            logger.info(f"浏览器启动成功: {self.browser_type}")
        except Exception as e:
            logger.error(f"浏览器启动失败: {e}")
            self.close()
            raise
    
    def close(self) -> None:
        logger.info("关闭浏览器...")
        
        if self._page:
            try:
                self._page.close()
            except:
                pass
            finally:
                self._page = None
        
        if self._browser:
            try:
                self._browser.close()
            except:
                pass
            finally:
                self._browser = None
        
        if self._playwright:
            try:
                self._playwright.stop()
            except:
                pass
            finally:
                self._playwright = None
        
        logger.info("浏览器已关闭")
    
    def __enter__(self):
        self.launch()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
