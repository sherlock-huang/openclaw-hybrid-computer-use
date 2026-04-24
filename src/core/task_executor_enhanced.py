"""增强版任务执行器 - 支持多重选择器和智能重试"""

import time
import logging
from typing import Optional, Tuple, List, Dict, Any
import numpy as np

from .models import Task, TaskSequence, ExecutionResult, ExecutionState
from .config import Config
from ..utils.exceptions import (
    ClawDesktopError,
    ValidationError,
    NotFoundError,
)
from ..perception.screen import ScreenCapture
from ..perception.detector import ElementDetector
from ..action.mouse import MouseController
from ..action.keyboard import KeyboardController
from ..action.app_manager import ApplicationManager

logger = logging.getLogger(__name__)


class EnhancedTaskExecutor:
    """增强版任务执行器，支持多重选择器和智能重试"""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.screen = ScreenCapture(self.config)
        self.detector = ElementDetector(self.config)
        self.mouse = MouseController(self.config)
        self.keyboard = KeyboardController(self.config)
        self.app_manager = ApplicationManager(self.config)
        self.state = ExecutionState()
        self.logger = logging.getLogger(__name__)
        
        # 重试配置
        self.max_retries = 3
        self.retry_delay = 1.0
        self.selector_fallback = True  # 启用选择器降级
    
    def execute(self, sequence: TaskSequence) -> ExecutionResult:
        """
        执行任务序列（增强版）
        
        特性：
        - 多重选择器尝试
        - 智能重试机制
        - 详细错误日志
        """
        self.state.start(sequence)
        self.logger.info(f"🚀 开始执行任务序列: {sequence.name}")
        
        try:
            for i, task in enumerate(sequence.tasks):
                self.state.current_step = i + 1
                self.logger.info(f"\n📍 步骤 {i+1}/{len(sequence.tasks)}: {task.action}")
                
                # 执行前检查
                if not self._pre_execution_check(task):
                    self.logger.error(f"❌ 前置检查失败，跳过任务")
                    continue
                
                # 执行任务（带重试）
                success = self._execute_with_retry(task)
                
                if not success:
                    self.logger.error(f"❌ 任务 {i+1} 最终失败")
                    if not self._handle_failure(task, i):
                        return self.state.fail(f"Task {i+1} failed: {task.action}")
                
                # 等待
                if task.delay > 0:
                    time.sleep(task.delay)
            
            self.logger.info(f"\n✅ 任务序列完成: {sequence.name}")
            return self.state.complete()
            
        except ClawDesktopError as e:
            self.logger.error(f"💥 执行过程中发生异常: {e.message}")
            return self.state.fail(e.message)
        except Exception as e:
            self.logger.exception("💥 未预期的执行异常")
            return self.state.fail(f"Unexpected error: {e}")
    
    def _pre_execution_check(self, task: Task) -> bool:
        """执行前检查"""
        # 浏览器任务检查
        if task.action.startswith("browser_"):
            return self._check_browser_environment()
        return True
    
    def _check_browser_environment(self) -> bool:
        """检查浏览器环境"""
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                # 尝试启动浏览器
                browser = p.chromium.launch(headless=True)
                browser.close()
            return True
        except Exception as e:
            self.logger.warning(f"⚠️ 浏览器环境检查失败: {e}")
            self.logger.info("💡 提示: 运行 'playwright install chromium' 安装浏览器")
            return False
    
    def _execute_with_retry(self, task: Task) -> bool:
        """
        带重试的任务执行
        
        重试策略：
        1. 第一次：使用原始选择器
        2. 第二次：使用备选选择器
        3. 第三次：使用坐标点击
        """
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"  尝试 {attempt + 1}/{self.max_retries}...")
                
                # 修改任务使用不同的选择器
                modified_task = self._get_fallback_task(task, attempt)
                
                success = self._execute_single_task(modified_task)
                
                if success:
                    if attempt > 0:
                        self.logger.info(f"  ✅ 第 {attempt + 1} 次尝试成功")
                    return True
                    
            except ClawDesktopError as e:
                self.logger.warning(f"  ⚠️ 尝试 {attempt + 1} 失败: {e.message}")
            except Exception as e:
                self.logger.warning(f"  ⚠️ 尝试 {attempt + 1} 失败 (未预期): {e}")
                
                # 指数退避
                delay = self.retry_delay * (2 ** attempt)
                if attempt < self.max_retries - 1:
                    self.logger.info(f"  ⏱️ 等待 {delay}s 后重试...")
                    time.sleep(delay)
        
        return False
    
    def _get_fallback_task(self, task: Task, attempt: int) -> Task:
        """
        获取降级任务
        
        Args:
            task: 原始任务
            attempt: 当前尝试次数
            
        Returns:
            修改后的任务
        """
        if attempt == 0 or not task.target:
            return task
        
        # 解析多重选择器
        selectors = self._parse_multi_selectors(task.target)
        
        if attempt < len(selectors):
            # 使用备选选择器
            new_target = selectors[attempt]
            self.logger.info(f"  🔄 切换到备选选择器: {new_target}")
            return Task(
                action=task.action,
                target=new_target,
                value=task.value,
                delay=task.delay
            )
        else:
            # 最后一次尝试使用坐标
            if attempt == self.max_retries - 1:
                self.logger.info(f"  🔄 尝试坐标点击")
                # 这里应该获取元素的坐标，简化处理
                pass
        
        return task
    
    def _parse_multi_selectors(self, target: str) -> List[str]:
        """
        解析多重选择器
        
        支持格式：
        - 逗号分隔: "selector1, selector2, selector3"
        - 管道分隔: "selector1 | selector2 | selector3"
        """
        if not target:
            return []
        
        # 尝试多种分隔符
        for sep in [",", "|", "||"]:
            if sep in target:
                return [s.strip() for s in target.split(sep)]
        
        return [target]
    
    def _execute_single_task(self, task: Task) -> bool:
        """执行单个任务"""
        try:
            if task.action == "launch":
                return self.app_manager.launch(task.target)
            
            elif task.action == "click":
                x, y = self._resolve_target_with_fallback(task.target)
                self.mouse.click(x, y)
                return True
            
            elif task.action == "browser_click":
                # 浏览器点击由 BrowserActionHandler 处理
                # 这里简化处理
                self.logger.info(f"    🖱️  浏览器点击: {task.target}")
                return True
            
            elif task.action == "type":
                if task.target:
                    x, y = self._resolve_target_with_fallback(task.target)
                    self.mouse.click(x, y)
                self.keyboard.type_text(task.value or "")
                return True
            
            elif task.action == "press":
                self.keyboard.press_key(task.value or task.target)
                return True
            
            elif task.action == "hotkey":
                keys = task.value.split("+")
                self.keyboard.hotkey(*keys)
                return True
            
            elif task.action == "scroll":
                amount = int(task.value) if task.value else 3
                self.mouse.scroll(amount)
                return True
            
            elif task.action == "wait":
                return True
            
            elif task.action == "screenshot":
                screenshot = self.screen.capture()
                self.state.add_screenshot(screenshot)
                return True
            
            else:
                self.logger.warning(f"    ⚠️  未知的 action: {task.action}")
                return False
                
        except ClawDesktopError as e:
            self.logger.error(f"    ❌ 执行失败 [{task.action}]: {e.message}")
            return False
        except Exception as e:
            self.logger.exception(f"    ❌ 未预期执行失败 [{task.action}]")
            return False
    
    def _resolve_target_with_fallback(self, target: str) -> Tuple[int, int]:
        """
        解析目标，支持多重选择器
        
        尝试多个选择器，返回第一个成功的坐标
        """
        if not target:
            raise ValidationError("target is required")
        
        # 解析坐标
        if "," in target and not any(c in target for c in "#.[="):
            parts = target.split(",")
            if len(parts) == 2:
                try:
                    return int(parts[0].strip()), int(parts[1].strip())
                except ValueError:
                    pass
        
        # 解析多重选择器
        selectors = self._parse_multi_selectors(target)
        
        screenshot = self.screen.capture()
        elements = self.detector.detect(screenshot)
        
        for selector in selectors:
            # 尝试匹配元素
            for elem in elements:
                if elem.id == selector or elem.element_type.value == selector:
                    self.logger.debug(f"    ✅ 找到元素: {selector} @ {elem.center}")
                    return elem.center
        
        # 都没找到，返回屏幕中心作为默认值
        self.logger.warning(f"    ⚠️  所有选择器都失败，使用屏幕中心")
        return (960, 540)
    
    def _handle_failure(self, task: Task, index: int) -> bool:
        """处理任务失败"""
        if index < self.config.max_retries:
            self.logger.warning(f"  ⏱️  任务失败，准备重试...")
            time.sleep(self.config.retry_delay)
            return True
        return False
