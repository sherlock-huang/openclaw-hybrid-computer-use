"""任务执行引擎"""

import time
import logging
from typing import Optional, Tuple
import numpy as np

from .models import Task, TaskSequence, ExecutionResult, ExecutionState
from .config import Config
from .task_learner import TaskLearner
from .task_learning_engine import TaskLearningEngine
from ..perception.screen import ScreenCapture
from ..perception.detector import ElementDetector
from ..action.mouse import MouseController
from ..action.keyboard import KeyboardController
from ..action.app_manager import ApplicationManager
from ..browser.controller import BrowserController
from ..browser.actions import BrowserActionHandler
from ..action.office_automation import OfficeAutomationManager


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
        self.learner = TaskLearner()
        self.learning_engine = TaskLearningEngine(self.learner)
        
        # 浏览器相关
        self.browser_controller: Optional[BrowserController] = None
        self.browser_handler: Optional[BrowserActionHandler] = None
        
        # Office 自动化
        self.office = OfficeAutomationManager()
        
        # 智能定位
        from ..perception.smart_locator import SmartLocator
        self.locator = SmartLocator()
        
        # 插件系统
        from ..plugins.loader import PluginLoader
        self.plugin_loader = PluginLoader()
        self.plugin_loader.load_builtin_plugins()
        self.plugin_loader.load_user_plugins()
        self.last_location = None
    
    def execute(self, sequence: TaskSequence) -> ExecutionResult:
        """
        执行任务序列
        
        执行流程:
        1. 初始化状态
        2. 对每个任务: 截图感知 -> 解析目标 -> 执行操作 -> 验证结果
        3. 返回执行结果
        """
        start_time = time.time()
        
        # 自动应用学习到的配置
        adjusted_tasks = []
        extra_retries = 0
        for task in sequence.tasks:
            task_dict = task.to_dict()
            adjusted = self.learner.apply_learned_settings(task.action, task.target or "", task_dict)
            adjusted.pop("_extra_retries", None)
            adjusted_tasks.append(Task(**adjusted))
            extra_retries = max(extra_retries, adjusted.get("_extra_retries", 0))
        
        sequence = TaskSequence(
            name=sequence.name,
            tasks=adjusted_tasks,
            max_retries=sequence.max_retries + extra_retries
        )
        
        # 尝试从学习器获取推荐
        if sequence.tasks:
            pattern = self.learner.suggest(
                sequence.tasks[0].action,
                sequence.tasks[0].target or ""
            )
            if pattern and pattern.success_rate > 0.8:
                self.logger.info(f"Using learned pattern: {pattern.task_type}")
        
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
                        result = self.state.fail(f"Task {i+1} failed: {task.action}")
                        self._record_learning(sequence, result, start_time)
                        return result
                
                # 等待
                if task.delay > 0:
                    time.sleep(task.delay)
            
            self.logger.info(f"任务序列完成: {sequence.name}")
            result = self.state.complete()
            self._record_learning(sequence, result, start_time)
            return result
            
        except Exception as e:
            self.logger.exception("执行失败")
            result = self.state.fail(str(e))
            self._record_learning(sequence, result, start_time)
            return result
        finally:
            # 确保浏览器关闭
            if self.browser_controller and self.browser_controller.is_running:
                self.browser_controller.close()
            # 确保 Office 资源释放
            self.office.close_all()
    
    def _execute_single_task(self, task: Task, screenshot: np.ndarray) -> bool:
        """执行单个任务"""
        
        try:
            # 浏览器相关 actions
            if task.action == "browser_launch":
                browser_type = task.value or "chromium"
                headless = getattr(self.config, 'browser_headless', False)
                user_data_dir = getattr(self.config, 'browser_user_data_dir', None)
                self.browser_controller = BrowserController(
                    browser_type=browser_type,
                    headless=headless,
                    user_data_dir=user_data_dir
                )
                self.browser_controller.launch()
                self.browser_handler = BrowserActionHandler(self.browser_controller)
                self.logger.info(f"Browser launched, user_data_dir: {user_data_dir}")
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

            elif task.action == "browser_press":
                key = task.value or task.target
                if not key:
                    raise ValueError("browser_press requires value or target (key)")
                self.browser_handler.press(key)
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
            
            elif task.action == "wechat_send":
                """微信发送消息"""
                from ..utils.wechat_helper import WeChatHelper
                
                contact = task.target
                message = task.value
                
                if not contact:
                    raise ValueError("wechat_send requires target (contact name)")
                if not message:
                    raise ValueError("wechat_send requires value (message)")
                
                helper = WeChatHelper()
                
                # 从策略提示中提取推荐的选人策略
                strategy_hints = getattr(task, '_strategy_hints', None) or {}
                use_ocr = strategy_hints.get("wechat_selector") != "legacy"
                
                success = helper.send_message_to_contact(contact, message)
                
                # 记录学习时附带策略提示
                hint = {"wechat_selector": "ocr" if success and use_ocr else "legacy"}
                if success:
                    hint = {"wechat_selector": "ocr"}
                self._record_learning_with_hints(
                    Task(action="wechat_send", target=contact, value=message, delay=task.delay),
                    success, hint
                )
                return success
            
            # Office 自动化 actions
            elif task.action == "excel_create":
                if not task.value:
                    raise ValueError("excel_create requires value (filepath)")
                self.office.excel_create(task.value)
                return True
            
            elif task.action == "excel_open":
                if not task.value:
                    raise ValueError("excel_open requires value (filepath)")
                self.office.excel_open(task.value)
                return True
            
            elif task.action == "excel_read_cell":
                if not self.office.excel:
                    raise ValueError("No Excel workbook open")
                parts = (task.target or "").split("!")
                sheet = parts[0] if len(parts) > 1 else None
                cell = parts[-1] if parts else (task.value or "A1")
                val = self.office.excel.read_cell(cell, sheet_name=sheet)
                self.logger.info(f"Excel read: {val}")
                return True
            
            elif task.action == "excel_write_cell":
                if not self.office.excel:
                    raise ValueError("No Excel workbook open")
                parts = (task.target or "").split("!")
                sheet = parts[0] if len(parts) > 1 else None
                cell = parts[-1] if parts else "A1"
                self.office.excel.write_cell(cell, task.value, sheet_name=sheet)
                return True
            
            elif task.action == "excel_write_range":
                if not self.office.excel:
                    raise ValueError("No Excel workbook open")
                import json
                data = json.loads(task.value or "[]")
                start_cell = task.target or "A1"
                self.office.excel.write_range(start_cell, data)
                return True
            
            elif task.action == "excel_chart":
                if not self.office.excel:
                    raise ValueError("No Excel workbook open")
                import json
                cfg = json.loads(task.value or "{}")
                self.office.excel.create_chart(
                    chart_type=cfg.get("type", "bar"),
                    data_range=cfg.get("data_range", "A1:B5"),
                    title=cfg.get("title", "Chart"),
                    position=cfg.get("position"),
                    categories_range=cfg.get("categories_range"),
                )
                return True
            
            elif task.action == "excel_save":
                if not self.office.excel:
                    raise ValueError("No Excel workbook open")
                self.office.excel.save(filepath=task.value)
                return True
            
            elif task.action == "word_create":
                if not task.value:
                    raise ValueError("word_create requires value (filepath)")
                self.office.word_create(task.value)
                return True
            
            elif task.action == "word_open":
                if not task.value:
                    raise ValueError("word_open requires value (filepath)")
                self.office.word_open(task.value)
                return True
            
            elif task.action == "word_write":
                if not self.office.word:
                    raise ValueError("No Word document open")
                style = task.target
                self.office.word.add_paragraph(task.value or "", style=style)
                return True
            
            elif task.action == "word_heading":
                if not self.office.word:
                    raise ValueError("No Word document open")
                level = int(task.target or "1")
                self.office.word.add_heading(task.value or "", level=level)
                return True
            
            elif task.action == "word_table":
                if not self.office.word:
                    raise ValueError("No Word document open")
                import json
                cfg = json.loads(task.value or "{}")
                rows = cfg.get("rows", 2)
                cols = cfg.get("cols", 2)
                data = cfg.get("data")
                self.office.word.add_table(rows, cols, data=data)
                return True
            
            elif task.action == "word_fill":
                if not self.office.word:
                    raise ValueError("No Word document open")
                import json
                mapping = json.loads(task.value or "{}")
                self.office.word.fill_template(mapping)
                return True
            
            elif task.action == "word_save":
                if not self.office.word:
                    raise ValueError("No Word document open")
                self.office.word.save(filepath=task.value)
                return True
            # 通用工具 actions
            elif task.action == "file_copy":
                import shutil
                if not task.target or not task.value:
                    raise ValueError("file_copy requires target (src) and value (dst)")
                shutil.copy2(task.target, task.value)
                self.logger.info(f"文件复制: {task.target} -> {task.value}")
                return True
            
            elif task.action == "file_move":
                import shutil
                if not task.target or not task.value:
                    raise ValueError("file_move requires target (src) and value (dst)")
                shutil.move(task.target, task.value)
                self.logger.info(f"文件移动: {task.target} -> {task.value}")
                return True
            
            elif task.action == "file_delete":
                import os, shutil
                if not task.target:
                    raise ValueError("file_delete requires target (path)")
                path = task.target
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                self.logger.info(f"文件删除: {path}")
                return True
            
            elif task.action == "file_rename":
                import os
                if not task.target or not task.value:
                    raise ValueError("file_rename requires target (old) and value (new)")
                os.rename(task.target, task.value)
                self.logger.info(f"文件重命名: {task.target} -> {task.value}")
                return True
            
            elif task.action == "folder_create":
                from pathlib import Path
                if not task.target:
                    raise ValueError("folder_create requires target (path)")
                Path(task.target).mkdir(parents=True, exist_ok=True)
                self.logger.info(f"创建文件夹: {task.target}")
                return True
            
            elif task.action == "shell":
                import subprocess
                cmd = task.value or task.target
                if not cmd:
                    raise ValueError("shell requires value or target (command)")
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
                self.logger.info(f"Shell 执行: {cmd}")
                if result.stdout:
                    self.logger.info(result.stdout[:500])
                return True
            
            elif task.action == "clipboard_copy":
                try:
                    import pyperclip
                    pyperclip.copy(task.value or "")
                except ImportError:
                    import ctypes
                    from ctypes import wintypes
                    user32 = ctypes.windll.user32
                    kernel32 = ctypes.windll.kernel32
                    text = task.value or ""
                    user32.OpenClipboard(0)
                    user32.EmptyClipboard()
                    hGlobal = kernel32.GlobalAlloc(0x2002, len(text.encode("utf-16-le")) + 2)
                    pGlobal = kernel32.GlobalLock(hGlobal)
                    ctypes.memmove(pGlobal, text.encode("utf-16-le"), len(text.encode("utf-16-le")))
                    kernel32.GlobalUnlock(hGlobal)
                    user32.SetClipboardData(13, hGlobal)
                    user32.CloseClipboard()
                self.logger.info("剪贴板复制完成")
                return True
            
            elif task.action == "system_lock":
                import ctypes
                ctypes.windll.user32.LockWorkStation()
                self.logger.info("系统锁定")
                return True
            
            elif task.action == "screenshot_save":
                path = task.value or task.target or "screenshot.png"
                img = self.screen.capture()
                from PIL import Image
                Image.fromarray(img).save(path)
                self.logger.info(f"截图保存: {path}")
                return True
            # 智能定位 actions
            elif task.action == "locate_image":
                if not task.target:
                    raise ValueError("locate_image requires target (template_path)")
                screenshot = self.screen.capture()
                result = self.locator.locate_by_image(screenshot, task.target)
                if result:
                    self.last_location = (result.x, result.y)
                    self.logger.info(f"图像定位成功: {task.target} @ {self.last_location}")
                    return True
                self.logger.error(f"图像定位失败: {task.target}")
                return False
            
            elif task.action == "locate_text":
                if not task.target:
                    raise ValueError("locate_text requires target (text)")
                screenshot = self.screen.capture()
                result = self.locator.locate_by_text(screenshot, task.target)
                if result:
                    self.last_location = (result.x, result.y)
                    self.logger.info(f"文字定位成功: {task.target} @ {self.last_location}")
                    return True
                self.logger.error(f"文字定位失败: {task.target}")
                return False
            
            elif task.action == "click_relative":
                import json
                ref = self.last_location
                if task.target and task.target != "last_located":
                    if "," in task.target:
                        ref = tuple(int(v.strip()) for v in task.target.split(","))
                if not ref:
                    raise ValueError("click_relative requires a previous locate or target coordinate")
                offset = json.loads(task.value or "{}")
                x = ref[0] + offset.get("x", 0)
                y = ref[1] + offset.get("y", 0)
                self.mouse.click(x, y)
                self.logger.info(f"相对点击: {ref} + {offset} -> ({x}, {y})")
                return True
            
            elif task.action == "wait_for_image":
                import time
                if not task.target:
                    raise ValueError("wait_for_image requires target (template_path)")
                timeout = float(task.value) if task.value else 10.0
                end = time.time() + timeout
                while time.time() < end:
                    screenshot = self.screen.capture()
                    result = self.locator.locate_by_image(screenshot, task.target)
                    if result:
                        self.last_location = (result.x, result.y)
                        self.logger.info(f"等待图像出现: {task.target} @ {self.last_location}")
                        return True
                    time.sleep(0.5)
                self.logger.error(f"等待图像超时: {task.target}")
                return False
            
            elif task.action == "wait_for_text":
                import time
                if not task.target:
                    raise ValueError("wait_for_text requires target (text)")
                timeout = float(task.value) if task.value else 10.0
                end = time.time() + timeout
                while time.time() < end:
                    screenshot = self.screen.capture()
                    result = self.locator.locate_by_text(screenshot, task.target)
                    if result:
                        self.last_location = (result.x, result.y)
                        self.logger.info(f"等待文字出现: {task.target} @ {self.last_location}")
                        return True
                    time.sleep(0.5)
                self.logger.error(f"等待文字超时: {task.target}")
                return False
            
            elif task.action == "locate_relation":
                import json
                if not task.target:
                    raise ValueError("locate_relation requires target (reference_text)")
                cfg = json.loads(task.value or "{}")
                target_text = cfg.get("target_text", "")
                direction = cfg.get("direction", "below")
                screenshot = self.screen.capture()
                result = self.locator.locate_relation(screenshot, task.target, target_text, direction)
                if result:
                    self.last_location = (result.x, result.y)
                    self.logger.info(f"关系链定位成功: {task.target} {direction} {target_text} @ {self.last_location}")
                    return True
                self.logger.error(f"关系链定位失败")
                return False
            # 插件系统 actions
            elif task.action == "plugin_invoke":
                if not task.target:
                    raise ValueError("plugin_invoke requires target (plugin_name.action_name)")
                parts = task.target.split(".", 1)
                if len(parts) != 2:
                    raise ValueError("target format: plugin_name.action_name")
                plugin_name, action_name = parts[0], parts[1]
                return self.plugin_loader.invoke_action(plugin_name, action_name, task)
            elif task.action == "plugin_list":
                plugins = self.plugin_loader.list_plugins()
                for p in plugins:
                    self.logger.info(f"  插件: {p["name"]} v{p["version"]} — actions: {p["actions"]}")
                return True
            else:
                self.logger.warning(f"未知的action类型: {task.action}")
                return False
                return False
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
    
    def _record_learning(self, sequence: TaskSequence, result: ExecutionResult, start_time: float):
        """记录学习结果"""
        duration = time.time() - start_time
        for task in sequence.tasks:
            self.learner.learn(
                task.action,
                task.target or "",
                [{"action": task.action, "target": task.target, "value": task.value}],
                result.success,
                duration
            )
    
    def _record_learning_with_hints(self, task: Task, success: bool, hints: dict):
        """记录带策略提示的学习结果"""
        self.learner.learn(
            task.action,
            task.target or "",
            [{"action": task.action, "target": task.target, "value": task.value}],
            success,
            0.0,
            strategy_hints=hints
        )









