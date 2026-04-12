"""视觉任务规划器 - 将自然语言转为 TaskSequence"""

import logging
import time
from typing import Optional, List, Dict, Any
import numpy as np

from ..core.models import Task, TaskSequence, RecordingMode
from ..browser.controller import BrowserController
from ..browser.actions import BrowserActionHandler
from .llm_client import VLMClient

logger = logging.getLogger(__name__)


class VisionTaskPlanner:
    """视觉任务规划器"""
    
    def __init__(self, vlm_client: Optional[VLMClient] = None, max_steps: int = 20):
        """
        初始化任务规划器
        
        Args:
            vlm_client: VLM 客户端，默认创建新的
            max_steps: 最大执行步数
        """
        self.vlm = vlm_client or VLMClient()
        self.max_steps = max_steps
        self.history: List[Dict] = []
        
        # 浏览器控制
        self.browser_controller: Optional[BrowserController] = None
        self.browser_handler: Optional[BrowserActionHandler] = None
        
        logger.info(f"VisionTaskPlanner 初始化: max_steps={max_steps}")
    
    def execute_instruction(self, instruction: str, start_browser: bool = True) -> TaskSequence:
        """
        执行自然语言指令
        
        Args:
            instruction: 用户指令，如"在淘宝上搜索蓝牙耳机"
            start_browser: 是否自动启动浏览器
            
        Returns:
            执行的任务序列
        """
        logger.info(f"开始执行指令: {instruction}")
        
        tasks = []
        
        # 启动浏览器
        if start_browser:
            self._ensure_browser_running()
            tasks.append(Task("browser_launch", value="chromium", delay=2.0))
        
        # 主循环
        for step in range(self.max_steps):
            logger.info(f"Step {step + 1}/{self.max_steps}")
            
            # 截图
            screenshot = self._capture_screenshot()
            
            # VLM 决策
            decision = self.vlm.analyze_screen(screenshot, instruction, self.history)
            
            logger.info(f"VLM 决策: {decision}")
            
            # 检查是否完成
            if decision.get("is_task_complete") or decision.get("action") == "finish":
                logger.info("任务完成")
                break
            
            # 转换为 Task
            task = self._decision_to_task(decision)
            if task:
                tasks.append(task)
                
                # 执行操作
                self._execute_task(task)
                
                # 记录历史
                self.history.append({
                    "step": step,
                    "decision": decision,
                    "task": task.to_dict()
                })
            
            # 等待
            delay = decision.get("delay", 2.0)
            time.sleep(delay)
        
        # 关闭浏览器
        if self.browser_controller:
            tasks.append(Task("browser_close", delay=1.0))
            self.browser_controller.close()
        
        # 创建任务序列
        sequence = TaskSequence(
            name=f"VLM: {instruction[:50]}",
            tasks=tasks,
            max_retries=2
        )
        
        return sequence
    
    def _ensure_browser_running(self):
        """确保浏览器正在运行"""
        if not self.browser_controller or not self.browser_controller.is_running:
            self.browser_controller = BrowserController(
                browser_type="chromium",
                headless=False,
                user_data_dir="browser_data"
            )
            self.browser_controller.launch()
            self.browser_handler = BrowserActionHandler(self.browser_controller)
    
    def _capture_screenshot(self) -> np.ndarray:
        """捕获屏幕截图"""
        if self.browser_controller and self.browser_controller.is_running:
            # 浏览器页面截图
            from PIL import Image
            import io
            
            screenshot_bytes = self.browser_controller.page.screenshot()
            image = Image.open(io.BytesIO(screenshot_bytes))
            return np.array(image)
        else:
            # 桌面截图
            from ..perception.screen import ScreenCapture
            screen = ScreenCapture()
            return screen.capture()
    
    def _decision_to_task(self, decision: Dict[str, Any]) -> Optional[Task]:
        """将 VLM 决策转为 Task"""
        action = decision.get("action")
        target = decision.get("target", "")
        value = decision.get("value", "")
        delay = decision.get("delay", 2.0)
        
        if action == "click":
            return Task("browser_click" if self._is_browser_selector(target) else "click",
                       target=target, delay=delay)
        elif action == "type":
            return Task("browser_type" if self._is_browser_selector(target) else "type",
                       target=target, value=value, delay=delay)
        elif action == "scroll":
            return Task("browser_scroll", value=str(value), delay=delay)
        elif action == "wait":
            return Task("wait", delay=float(value) if value else delay)
        elif action == "screenshot":
            return Task("browser_screenshot", value=f"vlm_step_{len(self.history)}.png", delay=delay)
        
        return None
    
    def _is_browser_selector(self, target: str) -> bool:
        """判断是否为浏览器选择器"""
        if not target:
            return False
        # 浏览器选择器特征
        browser_patterns = ["#", ".", "[", "input", "button", "a", "div"]
        return any(pattern in target for pattern in browser_patterns)
    
    def _execute_task(self, task: Task):
        """执行单个任务"""
        if not self.browser_handler:
            return
        
        try:
            if task.action == "browser_click":
                self.browser_handler.click(task.target)
            elif task.action == "browser_type":
                self.browser_handler.type(task.target, task.value or "")
            elif task.action == "browser_scroll":
                amount = int(task.value) if task.value else 500
                self.browser_handler.scroll(amount)
            elif task.action == "browser_screenshot":
                self.browser_handler.screenshot(task.value)
        except Exception as e:
            logger.error(f"执行任务失败: {e}")
