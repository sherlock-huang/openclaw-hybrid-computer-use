"""浏览器录制器 - 录制网页操作"""

import logging
import time
from typing import Optional, Dict, Any
from pathlib import Path

from playwright.sync_api import sync_playwright

from ..browser.controller import BrowserController
from ..core.models import RecordingEvent, RecordingMode

logger = logging.getLogger(__name__)


class BrowserRecorder:
    """浏览器录制器"""
    
    def __init__(self, user_data_dir: str = "browser_data"):
        self.user_data_dir = user_data_dir
        self._controller: Optional[BrowserController] = None
        self._page = None
        
        logger.info(f"BrowserRecorder 初始化: user_data_dir={user_data_dir}")
    
    @property
    def is_connected(self) -> bool:
        return self._page is not None
    
    def connect(self) -> bool:
        """连接到现有浏览器"""
        try:
            self._controller = BrowserController(
                browser_type="chromium",
                headless=False,
                user_data_dir=self.user_data_dir
            )
            self._controller.launch()
            self._page = self._controller.page
            
            self._inject_listeners()
            logger.info("BrowserRecorder 已连接到浏览器")
            return True
        except Exception as e:
            logger.error(f"连接浏览器失败: {e}")
            return False
    
    def disconnect(self):
        if self._controller:
            self._controller.close()
            self._controller = None
        self._page = None
        logger.info("BrowserRecorder 已断开连接")
    
    def _inject_listeners(self):
        if not self._page:
            return
        
        self._page.evaluate("""
            (function() {
                if (window.__browserRecorderInjected) return;
                window.__browserRecorderInjected = true;
                window.__lastBrowserEvent = null;
                
                function getSelector(element) {
                    if (!element) return null;
                    if (element.id) return '#' + element.id;
                    if (element.dataset.e2e) return `[data-e2e="${element.dataset.e2e}"]`;
                    if (element.className) {
                        const classes = element.className.split(' ').filter(c => c.length > 0);
                        if (classes.length > 0) return '.' + classes[0];
                    }
                    return element.tagName.toLowerCase();
                }
                
                document.addEventListener('click', function(e) {
                    window.__lastBrowserEvent = {
                        type: 'click',
                        selector: getSelector(e.target),
                        x: e.clientX,
                        y: e.clientY,
                        timestamp: Date.now()
                    };
                }, true);
                
                document.addEventListener('input', function(e) {
                    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                        window.__lastBrowserEvent = {
                            type: 'input',
                            selector: getSelector(e.target),
                            value: e.target.value,
                            timestamp: Date.now()
                        };
                    }
                }, true);
            })();
        """)
        logger.debug("事件监听脚本已注入")
    
    def get_last_event(self) -> Optional[RecordingEvent]:
        if not self._page:
            return None
        
        try:
            event_data = self._page.evaluate("window.__lastBrowserEvent")
            if not event_data:
                return None
            
            action_map = {'click': 'browser_click', 'input': 'browser_type'}
            action = action_map.get(event_data['type'], event_data['type'])
            
            return RecordingEvent(
                action=action,
                timestamp=time.time(),
                target=event_data.get('selector'),
                position=(event_data.get('x', 0), event_data.get('y', 0)),
                value=event_data.get('value'),
                recording_mode=RecordingMode.BROWSER,
                css_selector=event_data.get('selector')
            )
        except Exception as e:
            logger.error(f"获取事件失败: {e}")
            return None
    
    def clear_last_event(self):
        if self._page:
            self._page.evaluate("window.__lastBrowserEvent = null")
