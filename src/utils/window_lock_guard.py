"""
窗口稳定性守卫

确保微信发送过程中窗口不被切换、覆盖或最小化。
"""

import logging

try:
    import win32gui
    import win32con
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

logger = logging.getLogger(__name__)

WECHAT_TITLE_KEYWORDS = ["微信", "WeChat"]


class WindowLockGuard:
    """
    窗口稳定性守卫
    
    在自动化操作期间监控指定窗口是否保持稳定：
    1. 句柄是否仍然有效
    2. 是否仍然可见
    3. 是否仍然在前台
    4. 窗口标题是否仍然是微信
    """
    
    def __init__(self, hwnd: int):
        self.hwnd = hwnd
        self.logger = logging.getLogger(__name__)
    
    def check(self) -> tuple:
        """
        检查窗口稳定性
        
        Returns:
            (stable: bool, reason: str)
        """
        if not WIN32_AVAILABLE:
            return True, "win32gui 不可用，跳过窗口锁检查"
        
        # 1. 检查句柄是否有效
        if not win32gui.IsWindow(self.hwnd):
            return False, "窗口句柄已失效"
        
        # 2. 检查是否可见
        if not win32gui.IsWindowVisible(self.hwnd):
            return False, "窗口已不可见"
        
        # 3. 检查窗口标题是否仍是微信
        try:
            title = win32gui.GetWindowText(self.hwnd)
        except Exception:
            return False, "无法获取窗口标题"
        
        if not any(kw in title for kw in WECHAT_TITLE_KEYWORDS):
            return False, f"窗口标题已变化: '{title}'"
        
        # 4. 检查是否在前台（可选严格检查）
        try:
            foreground_hwnd = win32gui.GetForegroundWindow()
            if foreground_hwnd != self.hwnd:
                return False, "窗口已失去前台焦点"
        except Exception:
            return False, "无法获取前台窗口"
        
        return True, ""
    
    def check_or_fail(self, context: str = "") -> bool:
        """
        检查窗口稳定性，失败时记录日志
        
        Args:
            context: 当前操作上下文（如"发送前"）
            
        Returns:
            是否稳定
        """
        stable, reason = self.check()
        if not stable:
            msg = f"窗口稳定性检查失败 [{context}]: {reason}"
            self.logger.error(msg)
            return False
        return True
