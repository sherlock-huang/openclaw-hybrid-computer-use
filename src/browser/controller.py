"""浏览器控制器 - 管理浏览器生命周期"""

import logging
from typing import Optional, Any
from playwright.sync_api import sync_playwright, Page, Browser

from ..utils.exceptions import ConfigError

logger = logging.getLogger(__name__)


class BrowserController:
    """浏览器控制器"""
    
    SUPPORTED_BROWSERS = {"chromium", "firefox", "webkit"}
    
    def __init__(self, browser_type: str = "chromium", headless: bool = False, 
                 user_data_dir: Optional[str] = None):
        """
        初始化浏览器控制器
        
        Args:
            browser_type: 浏览器类型 ("chromium" | "firefox" | "webkit")
            headless: 是否无头模式
            user_data_dir: 用户数据目录，用于保存登录状态、cookies等
        """
        if browser_type not in self.SUPPORTED_BROWSERS:
            raise ConfigError(f"不支持的浏览器类型: {browser_type}. "
                           f"支持: {self.SUPPORTED_BROWSERS}")
        
        self.browser_type = browser_type
        self.headless = headless
        self.user_data_dir = user_data_dir
        
        self._playwright: Optional[Any] = None
        self._browser: Optional[Browser] = None
        self._page: Optional[Page] = None
        
        logger.info(f"BrowserController 初始化: {browser_type}, headless={headless}, "
                   f"user_data_dir={user_data_dir}")
    
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
            
            # 启动参数
            launch_args = {"headless": self.headless}
            
            # 如果指定了用户数据目录，使用 persistent context
            if self.user_data_dir:
                logger.info(f"使用用户数据目录: {self.user_data_dir}")
                context = browser_launcher.launch_persistent_context(
                    self.user_data_dir,
                    **launch_args,
                    viewport={"width": 1920, "height": 1080}
                )
                self._browser = context.browser
                # persistent context 已经包含 page
                pages = context.pages
                if pages:
                    self._page = pages[0]
                else:
                    self._page = context.new_page()
            else:
                # 普通模式（无痕）
                self._browser = browser_launcher.launch(**launch_args)
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
