"""任务执行引擎"""

import time
import logging
from typing import Optional, Tuple
import numpy as np

from .models import Task, TaskSequence, ExecutionResult, ExecutionState
from .config import Config
from ..perception.screen import ScreenCapture
from ..perception.detector import ElementDetector
from ..action.mouse import MouseController
from ..action.keyboard import KeyboardController
from ..action.app_manager import ApplicationManager
from ..browser.controller import BrowserController
from ..browser.actions import BrowserActionHandler


class TaskExecutor:
    """任务执行引擎"""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.screen = ScreenCapture(self.config)
        self.detector = ElementDetector(self.config)
        self.mouse = MouseController(self.config)
        self.keyboard = KeyboardController(self.config)
        self.app_manager = ApplicationManager(self.config)
        self.state = ExecutionState()
        self.logger = logging.getLogger(__name__)
        
        # 浏览器相关
        self.browser_controller: Optional[BrowserController] = None
        self.browser_handler: Optional[BrowserActionHandler] = None
    
    def execute(self, sequence: TaskSequence) -> ExecutionResult:
        """
        执行任务序列
        
        执行流程:
        1. 初始化状态
        2. 对每个任务: 截图感知 -> 解析目标 -> 执行操作 -> 验证结果
        3. 返回执行结果
        """
        self.state.start(sequence)
        self.logger.info(f"开始执行任务序列: {sequence.name}")
        
        try:
            for i, task in enumerate(sequence.tasks):
                self.state.current_step = i + 1
                self.logger.info(f"执行任务 {i+1}/{len(sequence.tasks)}: {task.action}")
                
                # 浏览器 action 不需要截图
                if not task.action.startswith("browser_"):
                    # 执行前截图
                    screenshot = self.screen.capture()
                    self.state.add_screenshot(screenshot)
                else:
                    screenshot = None
                
                # 执行任务
                success = self._execute_single_task(task, screenshot)
                
                if not success:
                    self.logger.error(f"任务 {i+1} 执行失败")
                    if not self._handle_failure(task, i):
                        return self.state.fail(f"Task {i+1} failed: {task.action}")
                
                # 等待
                if task.delay > 0:
                    time.sleep(task.delay)
            
            self.logger.info(f"任务序列完成: {sequence.name}")
            return self.state.complete()
            
        except Exception as e:
            self.logger.exception("执行失败")
            return self.state.fail(str(e))
        finally:
            # 确保浏览器关闭
            if self.browser_controller and self.browser_controller.is_running:
                self.browser_controller.close()
    
    def _execute_single_task(self, task: Task, screenshot: np.ndarray) -> bool:
        """执行单个任务"""
        
        try:
            # 浏览器相关 actions
            if task.action == "browser_launch":
                browser_type = task.value or "chromium"
                headless = getattr(self.config, 'browser_headless', False)
                self.browser_controller = BrowserController(
                    browser_type=browser_type,
                    headless=headless
                )
                self.browser_controller.launch()
                self.browser_handler = BrowserActionHandler(self.browser_controller)
                return True

            elif task.action == "browser_close":
                if self.browser_controller:
                    self.browser_controller.close()
                    self.browser_controller = None
                    self.browser_handler = None
                return True

            elif task.action == "browser_goto":
                if not task.value:
                    raise ValueError("browser_goto requires value (URL)")
                self.browser_handler.goto(task.value)
                return True

            elif task.action == "browser_click":
                if not task.target:
                    raise ValueError("browser_click requires target (selector)")
                self.browser_handler.click(task.target)
                return True

            elif task.action == "browser_type":
                if not task.target:
                    raise ValueError("browser_type requires target (selector)")
                self.browser_handler.type(task.target, task.value or "")
                return True

            elif task.action == "browser_clear":
                if not task.target:
                    raise ValueError("browser_clear requires target (selector)")
                self.browser_handler.clear(task.target)
                return True

            elif task.action == "browser_wait":
                if not task.target:
                    raise ValueError("browser_wait requires target (selector)")
                state = task.value or "visible"
                self.browser_handler.wait_for(task.target, state=state)
                return True

            elif task.action == "browser_scroll":
                amount = int(task.value) if task.value else 500
                self.browser_handler.scroll(amount)
                return True

            elif task.action == "browser_screenshot":
                path = task.value
                self.browser_handler.screenshot(path)
                return True

            elif task.action == "browser_evaluate":
                if not task.value:
                    raise ValueError("browser_evaluate requires value (JavaScript)")
                self.browser_handler.evaluate(task.value)
                return True

            # 桌面相关 actions
            elif task.action == "launch":
                if not task.target:
                    raise ValueError("launch action requires target")
                return self.app_manager.launch(task.target)
            
            elif task.action == "click":
                x, y = self._resolve_target(task.target, screenshot)
                self.mouse.click(x, y)
                return True
            
            elif task.action == "double_click":
                x, y = self._resolve_target(task.target, screenshot)
                self.mouse.double_click(x, y)
                return True
            
            elif task.action == "right_click":
                x, y = self._resolve_target(task.target, screenshot)
                self.mouse.right_click(x, y)
                return True
            
            elif task.action == "type":
                if task.target:
                    x, y = self._resolve_target(task.target, screenshot)
                    self.mouse.click(x, y)  # 先聚焦
                if task.value:
                    self.keyboard.type_text(task.value)
                return True
            
            elif task.action == "press":
                key = task.value or task.target
                if not key:
                    raise ValueError("press action requires value or target")
                self.keyboard.press_key(key)
                return True
            
            elif task.action == "hotkey":
                if not task.value:
                    raise ValueError("hotkey action requires value")
                keys = task.value.split("+")
                self.keyboard.hotkey(*keys)
                return True
            
            elif task.action == "wait":
                # 等待时间已经在execute中处理
                return True
            
            elif task.action == "scroll":
                amount = int(task.value) if task.value else 3
                if task.target:
                    x, y = self._resolve_target(task.target, screenshot)
                    self.mouse.scroll(amount, x, y)
                else:
                    self.mouse.scroll(amount)
                return True
            
            else:
                self.logger.warning(f"未知的action类型: {task.action}")
                return False
                
        except Exception as e:
            self.logger.error(f"执行任务失败: {e}")
            return False
    
    def _resolve_target(self, target: Optional[str], screenshot: np.ndarray) -> Tuple[int, int]:
        """
        解析目标为屏幕坐标
        
        target可以是:
        - 坐标: "100,200"
        - 元素ID: "elem_001"
        - 元素类型: "button"
        """
        if not target:
            raise ValueError("target is required")
        
        # 解析坐标 (格式: "x,y")
        if "," in target:
            parts = target.split(",")
            if len(parts) == 2:
                try:
                    x, y = int(parts[0].strip()), int(parts[1].strip())
                    return x, y
                except ValueError:
                    pass
        
        # 检测元素
        elements = self.detector.detect(screenshot)
        
        # 匹配元素ID
        for elem in elements:
            if elem.id == target:
                self.logger.debug(f"找到元素 {target} @ {elem.center}")
                return elem.center
        
        # 匹配元素类型（返回第一个匹配的）
        for elem in elements:
            if elem.element_type.value == target:
                self.logger.debug(f"找到类型 {target} 元素 @ {elem.center}")
                return elem.center
        
        raise ValueError(f"Target not found: {target}")
    
    def _handle_failure(self, task: Task, index: int) -> bool:
        """处理任务失败，尝试重试"""
        if index < self.config.max_retries:
            self.logger.warning(f"任务失败，第 {index + 1} 次重试...")
            time.sleep(self.config.retry_delay * (index + 1))
            return True
        return False
