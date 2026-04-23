"""鼠标控制器 (基于PyAutoGUI)"""

import logging
from typing import Tuple, Optional

import pyautogui

from ..core.config import Config


class MouseController:
    """鼠标控制器"""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.logger = logging.getLogger(__name__)
        
        # 配置PyAutoGUI
        pyautogui.FAILSAFE = self.config.mouse_failsafe
        pyautogui.PAUSE = 0.1
        
        # 获取屏幕尺寸
        self.screen_width, self.screen_height = pyautogui.size()
        self.logger.debug(f"屏幕尺寸: {self.screen_width}x{self.screen_height}")
    
    def move_to(self, x: int, y: int, duration: Optional[float] = None):
        """
        平滑移动鼠标到指定坐标
        
        Args:
            x: 目标X坐标
            y: 目标Y坐标
            duration: 移动动画时长，None则使用配置默认值
        """
        if duration is None:
            duration = self.config.mouse_default_duration
        
        # 确保坐标在屏幕范围内
        x = max(0, min(x, self.screen_width - 1))
        y = max(0, min(y, self.screen_height - 1))
        
        self.logger.debug(f"移动鼠标到 ({x}, {y}), 时长={duration}s")
        pyautogui.moveTo(x, y, duration=duration)
    
    def click(self, x: int, y: int, button: str = "left", clicks: int = 1):
        """
        在指定坐标点击
        
        Args:
            x: X坐标
            y: Y坐标
            button: 鼠标按钮 (left, right, middle)
            clicks: 点击次数
        """
        self.logger.debug(f"点击 ({x}, {y}), 按钮={button}, 次数={clicks}")
        pyautogui.click(x, y, button=button, clicks=clicks)
    
    def double_click(self, x: int, y: int):
        """双击指定坐标"""
        self.logger.debug(f"双击 ({x}, {y})")
        pyautogui.doubleClick(x, y)
    
    def right_click(self, x: int, y: int):
        """右键点击指定坐标"""
        self.logger.debug(f"右键点击 ({x}, {y})")
        pyautogui.rightClick(x, y)
    
    def middle_click(self, x: int, y: int):
        """中键点击指定坐标"""
        self.logger.debug(f"中键点击 ({x}, {y})")
        pyautogui.middleClick(x, y)
    
    def scroll(self, clicks: int, x: Optional[int] = None, y: Optional[int] = None):
        """
        滚动鼠标
        
        Args:
            clicks: 滚动量 (正数向上，负数向下)
            x: 可选，先移动到的X坐标
            y: 可选，先移动到的Y坐标
        """
        if x is not None and y is not None:
            self.move_to(x, y)
        
        self.logger.debug(f"滚动 {clicks} 单位")
        pyautogui.scroll(clicks)
    
    def drag_to(self, x: int, y: int, duration: Optional[float] = None, button: str = "left"):
        """
        拖拽到指定坐标
        
        Args:
            x: 目标X坐标
            y: 目标Y坐标
            duration: 拖拽时长
            button: 拖拽使用的按钮
        """
        if duration is None:
            duration = self.config.mouse_default_duration
        
        self.logger.debug(f"拖拽到 ({x}, {y})")
        pyautogui.dragTo(x, y, duration=duration, button=button)
    
    def drag_rel(self, x_offset: int, y_offset: int, duration: Optional[float] = None):
        """
        相对拖拽
        
        Args:
            x_offset: X方向偏移
            y_offset: Y方向偏移
            duration: 拖拽时长
        """
        if duration is None:
            duration = self.config.mouse_default_duration
        
        self.logger.debug(f"相对拖拽 ({x_offset}, {y_offset})")
        pyautogui.dragRel(x_offset, y_offset, duration=duration)
    
    def get_position(self) -> Tuple[int, int]:
        """
        获取当前鼠标位置
        
        Returns:
            (x, y) 坐标
        """
        return pyautogui.position()
    
    def move_rel(self, x_offset: int, y_offset: int, duration: Optional[float] = None):
        """
        相对移动
        
        Args:
            x_offset: X方向偏移
            y_offset: Y方向偏移
            duration: 移动时长
        """
        if duration is None:
            duration = self.config.mouse_default_duration
        
        pyautogui.moveRel(x_offset, y_offset, duration=duration)
