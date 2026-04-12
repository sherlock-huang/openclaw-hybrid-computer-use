"""浏览器操作处理器 - 封装 Playwright 操作"""

import logging
import time
from typing import Optional, Dict, Any, Union
from pathlib import Path

from .controller import BrowserController

logger = logging.getLogger(__name__)


class BrowserActionHandler:
    """浏览器操作处理器"""
    
    def __init__(self, controller: BrowserController):
        self.controller = controller
        logger.info("BrowserActionHandler 初始化完成")
    
    def _get_page(self):
        if not self.controller.is_running:
            raise RuntimeError("浏览器未启动，请先调用 browser_launch")
        return self.controller.page
    
    def goto(self, url: str, timeout: int = 60) -> None:
        page = self._get_page()
        logger.info(f"导航到: {url}")
        try:
            page.goto(url, timeout=timeout * 1000, wait_until="networkidle")
            logger.info(f"页面加载完成: {page.title()}")
        except Exception as e:
            logger.error(f"页面加载失败: {e}")
            raise
    
    def click(self, selector: str, options: Optional[Dict] = None) -> None:
        page = self._get_page()
        opts = options or {}
        timeout = opts.get("timeout", 30) * 1000
        force = opts.get("force", False)
        button = opts.get("button", "left")
        
        logger.info(f"点击元素: {selector}")
        try:
            page.click(selector, timeout=timeout, force=force, button=button)
            logger.debug(f"点击成功: {selector}")
        except Exception as e:
            logger.error(f"点击失败 {selector}: {e}")
            raise
    
    def type(self, selector: str, text: str, options: Optional[Dict] = None) -> None:
        page = self._get_page()
        opts = options or {}
        timeout = opts.get("timeout", 30) * 1000
        clear_first = opts.get("clear_first", True)
        
        logger.info(f"在 {selector} 输入文字: {text}")
        try:
            if clear_first:
                page.fill(selector, text, timeout=timeout)
            else:
                page.type(selector, text, timeout=timeout)
            logger.debug(f"输入完成: {selector}")
        except Exception as e:
            logger.error(f"输入失败 {selector}: {e}")
            raise
    
    def clear(self, selector: str, timeout: int = 30) -> None:
        page = self._get_page()
        logger.info(f"清空输入框: {selector}")
        try:
            page.fill(selector, "", timeout=timeout * 1000)
        except Exception as e:
            logger.error(f"清空失败 {selector}: {e}")
            raise
    
    def wait_for(self, selector: str, state: str = "visible", timeout: int = 60) -> None:
        page = self._get_page()
        logger.info(f"等待元素 {selector} 状态: {state}")
        valid_states = ["visible", "hidden", "attached", "detached"]
        if state not in valid_states:
            raise ValueError(f"无效的状态: {state}")
        try:
            page.wait_for_selector(selector, state=state, timeout=timeout * 1000)
            logger.debug(f"元素 {selector} 已 {state}")
        except Exception as e:
            logger.error(f"等待元素失败 {selector}: {e}")
            raise
    
    def scroll(self, amount: int, direction: str = "vertical") -> None:
        page = self._get_page()
        logger.info(f"滚动页面: {direction} {amount}px")
        try:
            if direction == "vertical":
                page.evaluate(f"() => window.scrollBy(0, {amount})")
            elif direction == "horizontal":
                page.evaluate(f"() => window.scrollBy({amount}, 0)")
            else:
                raise ValueError(f"无效的滚动方向: {direction}")
            time.sleep(0.5)
        except Exception as e:
            logger.error(f"滚动失败: {e}")
            raise
    
    def screenshot(self, path: Optional[str] = None) -> bytes:
        page = self._get_page()
        logger.info("截图...")
        try:
            screenshot_bytes = page.screenshot(path=path, full_page=True)
            logger.info(f"截图完成{' 保存到: ' + path if path else ''}")
            return screenshot_bytes
        except Exception as e:
            logger.error(f"截图失败: {e}")
            raise
    
    def evaluate(self, script: str) -> Any:
        page = self._get_page()
        logger.info(f"执行脚本: {script[:50]}...")
        try:
            result = page.evaluate(script)
            return result
        except Exception as e:
            logger.error(f"脚本执行失败: {e}")
            raise
    
    def press(self, key: str) -> None:
        """
        按下键盘按键
        
        Args:
            key: 按键名称 (Enter, Escape, Tab, ArrowDown 等)
        """
        page = self._get_page()
        logger.info(f"按下按键: {key}")
        try:
            page.keyboard.press(key)
            logger.debug(f"按键 {key} 已按下")
        except Exception as e:
            logger.error(f"按键失败 {key}: {e}")
            raise
