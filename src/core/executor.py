"""任务执行引擎"""

import time
import logging
import subprocess
import sys
from typing import Optional, Tuple
import numpy as np

from .models import Task, TaskSequence, ExecutionResult, ExecutionState
from .config import Config
from .task_learner import TaskLearner
from .task_learning_engine import TaskLearningEngine
from .failure_analyzer import FailureAnalyzer, FailureType
from .recovery_strategy import RecoveryStrategy, RecoveryResult
from .skill_manager import SkillManager
from .execution_diary import ExecutionDiary
from ..perception.screen import ScreenCapture
from ..perception.detector import ElementDetector
from ..action.mouse import MouseController
from ..action.keyboard import KeyboardController
from ..action.app_manager import ApplicationManager
from ..browser.controller import BrowserController
from ..browser.actions import BrowserActionHandler
from ..action.office_automation import OfficeAutomationManager
from ..utils.exceptions import (
    ValidationError,
    ResourceError,
    NotFoundError,
    ClawDesktopError,
    TaskExecutionError,
)


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

        # Self-Healing 组件
        self.failure_analyzer = FailureAnalyzer()
        self.execution_diary = ExecutionDiary()
        self.skill_manager = SkillManager(skill_file=self.config.skill_file)
        # 延迟初始化 diagnostician（需要 API key）
        self._diagnostician = None
        self.human_handler = None  # 延迟初始化人机协作
        self.recovery_strategy = RecoveryStrategy(
            logger=self.logger,
            skill_manager=self.skill_manager,
        )
        self.plugin_loader.load_user_plugins()
        self.last_location = None

    @property
    def diagnostician(self):
        if self._diagnostician is None:
            from .visual_diagnostician import VisualDiagnostician
            self._diagnostician = VisualDiagnostician(config=self.config)
            self.recovery_strategy.diagnostician = self._diagnostician
        return self._diagnostician

    @property
    def human_intervention(self):
        if self.human_handler is None:
            from .human_intervention import HumanInterventionHandler
            self.human_handler = HumanInterventionHandler()
            self.recovery_strategy.human_handler = self.human_handler
        return self.human_handler
    
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
                
                # 执行任务（带自我修复）
                success, error_msg = self._execute_with_recovery(
                    task, screenshot, i, sequence.name
                )

                # Self-Healing 失败后，尝试传统重试
                retry_count = 0
                while not success and retry_count < self.config.max_retries:
                    if not self._handle_failure(task, retry_count):
                        break
                    retry_count += 1
                    # 重新截图后重试
                    if not task.action.startswith("browser_"):
                        screenshot = self.screen.capture()
                        self.state.add_screenshot(screenshot)
                    try:
                        success = self._execute_single_task(task, screenshot)
                    except Exception as e:
                        error_msg = str(e)
                        success = False

                if not success:
                    self.logger.error(f"任务 {i+1} 执行失败: {error_msg}")
                    result = self.state.fail(f"Task {i+1} failed: {task.action} - {error_msg}")
                    self._record_learning(sequence, result, start_time)
                    return result
                
                # 等待
                if task.delay > 0:
                    time.sleep(task.delay)
            
            self.logger.info(f"任务序列完成: {sequence.name}")
            result = self.state.complete()
            self._record_learning(sequence, result, start_time)
            return result
            
        except ClawDesktopError as e:
            self.logger.error(f"执行失败: {e.message}")
            result = self.state.fail(e.message)
            self._record_learning(sequence, result, start_time)
            return result
        except Exception as e:
            self.logger.exception("未预期的执行失败")
            result = self.state.fail(f"Unexpected error: {e}")
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
                    raise ValidationError("browser_goto requires value (URL)")
                self.browser_handler.goto(task.value)
                return True

            elif task.action == "browser_click":
                if not task.target:
                    raise ValidationError("browser_click requires target (selector)")
                self.browser_handler.click(task.target)
                return True

            elif task.action == "browser_type":
                if not task.target:
                    raise ValidationError("browser_type requires target (selector)")
                self.browser_handler.type(task.target, task.value or "")
                return True

            elif task.action == "browser_clear":
                if not task.target:
                    raise ValidationError("browser_clear requires target (selector)")
                self.browser_handler.clear(task.target)
                return True

            elif task.action == "browser_wait":
                if not task.target:
                    raise ValidationError("browser_wait requires target (selector)")
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
                    raise ValidationError("browser_evaluate requires value (JavaScript)")
                self.browser_handler.evaluate(task.value)
                return True

            elif task.action == "browser_press":
                key = task.value or task.target
                if not key:
                    raise ValidationError("browser_press requires value or target (key)")
                self.browser_handler.press(key)
                return True

            # 桌面相关 actions
            elif task.action == "launch":
                if not task.target:
                    raise ValidationError("launch action requires target")
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
                    raise ValidationError("press action requires value or target")
                self.keyboard.press_key(key)
                return True
            
            elif task.action == "hotkey":
                if not task.value:
                    raise ValidationError("hotkey action requires value")
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
                    raise ValidationError("wechat_send requires target (contact name)")
                if not message:
                    raise ValidationError("wechat_send requires value (message)")
                
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
                    raise ValidationError("excel_create requires value (filepath)")
                self.office.excel_create(task.value)
                return True
            
            elif task.action == "excel_open":
                if not task.value:
                    raise ValidationError("excel_open requires value (filepath)")
                self.office.excel_open(task.value)
                return True
            
            elif task.action == "excel_read_cell":
                if not self.office.excel:
                    raise ResourceError("No Excel workbook open")
                parts = (task.target or "").split("!")
                sheet = parts[0] if len(parts) > 1 else None
                cell = parts[-1] if parts else (task.value or "A1")
                val = self.office.excel.read_cell(cell, sheet_name=sheet)
                self.logger.info(f"Excel read: {val}")
                return True
            
            elif task.action == "excel_write_cell":
                if not self.office.excel:
                    raise ResourceError("No Excel workbook open")
                parts = (task.target or "").split("!")
                sheet = parts[0] if len(parts) > 1 else None
                cell = parts[-1] if parts else "A1"
                self.office.excel.write_cell(cell, task.value, sheet_name=sheet)
                return True
            
            elif task.action == "excel_write_range":
                if not self.office.excel:
                    raise ResourceError("No Excel workbook open")
                import json
                data = json.loads(task.value or "[]")
                start_cell = task.target or "A1"
                self.office.excel.write_range(start_cell, data)
                return True
            
            elif task.action == "excel_chart":
                if not self.office.excel:
                    raise ResourceError("No Excel workbook open")
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
                    raise ResourceError("No Excel workbook open")
                self.office.excel.save(filepath=task.value)
                return True
            
            elif task.action == "word_create":
                if not task.value:
                    raise ValidationError("word_create requires value (filepath)")
                self.office.word_create(task.value)
                return True
            
            elif task.action == "word_open":
                if not task.value:
                    raise ValidationError("word_open requires value (filepath)")
                self.office.word_open(task.value)
                return True
            
            elif task.action == "word_write":
                if not self.office.word:
                    raise ResourceError("No Word document open")
                style = task.target
                self.office.word.add_paragraph(task.value or "", style=style)
                return True
            
            elif task.action == "word_heading":
                if not self.office.word:
                    raise ResourceError("No Word document open")
                level = int(task.target or "1")
                self.office.word.add_heading(task.value or "", level=level)
                return True
            
            elif task.action == "word_table":
                if not self.office.word:
                    raise ResourceError("No Word document open")
                import json
                cfg = json.loads(task.value or "{}")
                rows = cfg.get("rows", 2)
                cols = cfg.get("cols", 2)
                data = cfg.get("data")
                self.office.word.add_table(rows, cols, data=data)
                return True
            
            elif task.action == "word_fill":
                if not self.office.word:
                    raise ResourceError("No Word document open")
                import json
                mapping = json.loads(task.value or "{}")
                self.office.word.fill_template(mapping)
                return True
            
            elif task.action == "word_save":
                if not self.office.word:
                    raise ResourceError("No Word document open")
                self.office.word.save(filepath=task.value)
                return True
            # 通用工具 actions
            elif task.action == "file_copy":
                import shutil
                if not task.target or not task.value:
                    raise ValidationError("file_copy requires target (src) and value (dst)")
                shutil.copy2(task.target, task.value)
                self.logger.info(f"文件复制: {task.target} -> {task.value}")
                return True
            
            elif task.action == "file_move":
                import shutil
                if not task.target or not task.value:
                    raise ValidationError("file_move requires target (src) and value (dst)")
                shutil.move(task.target, task.value)
                self.logger.info(f"文件移动: {task.target} -> {task.value}")
                return True
            
            elif task.action == "file_delete":
                import os, shutil
                if not task.target:
                    raise ValidationError("file_delete requires target (path)")
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
                    raise ValidationError("file_rename requires target (old) and value (new)")
                os.rename(task.target, task.value)
                self.logger.info(f"文件重命名: {task.target} -> {task.value}")
                return True
            
            elif task.action == "folder_create":
                from pathlib import Path
                if not task.target:
                    raise ValidationError("folder_create requires target (path)")
                Path(task.target).mkdir(parents=True, exist_ok=True)
                self.logger.info(f"创建文件夹: {task.target}")
                return True
            
            elif task.action == "shell":
                import subprocess
                cmd = task.value or task.target
                if not cmd:
                    raise ValidationError("shell requires value or target (command)")
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
                    if sys.platform == "win32":
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
                    else:
                        self.logger.warning("pyperclip 未安装，剪贴板操作在非 Windows 平台不可用")
                self.logger.info("剪贴板复制完成")
                return True

            elif task.action == "system_lock":
                if sys.platform == "win32":
                    import ctypes
                    ctypes.windll.user32.LockWorkStation()
                elif sys.platform == "darwin":
                    subprocess.run(["pmset", "displaysleepnow"], check=False)
                else:
                    # Linux: 优先 loginctl，回退到 gnome-screensaver-command
                    result = subprocess.run(["loginctl", "lock-session"], capture_output=True)
                    if result.returncode != 0:
                        subprocess.run(["gnome-screensaver-command", "-l"], check=False)
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
                    raise ValidationError("locate_image requires target (template_path)")
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
                    raise ValidationError("locate_text requires target (text)")
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
                    raise ValidationError("click_relative requires a previous locate or target coordinate")
                offset = json.loads(task.value or "{}")
                x = ref[0] + offset.get("x", 0)
                y = ref[1] + offset.get("y", 0)
                self.mouse.click(x, y)
                self.logger.info(f"相对点击: {ref} + {offset} -> ({x}, {y})")
                return True
            
            elif task.action == "wait_for_image":
                import time
                if not task.target:
                    raise ValidationError("wait_for_image requires target (template_path)")
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
                    raise ValidationError("wait_for_text requires target (text)")
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
                    raise ValidationError("locate_relation requires target (reference_text)")
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
                    raise ValidationError("plugin_invoke requires target (plugin_name.action_name)")
                parts = task.target.split(".", 1)
                if len(parts) != 2:
                    raise ValidationError("target format: plugin_name.action_name")
                plugin_name, action_name = parts[0], parts[1]
                return self.plugin_loader.invoke_action(plugin_name, action_name, task)
            elif task.action == "plugin_list":
                plugins = self.plugin_loader.list_plugins()
                for p in plugins:
                    self.logger.info(f"  插件: {p['name']} v{p['version']} — actions: {p['actions']}")
                return True
            else:
                self.logger.warning(f"未知的action类型: {task.action}")
                return False
                
        except ClawDesktopError as e:
            self.logger.error(f"执行任务失败 [{task.action}]: {e.message}")
            return False
        except Exception as e:
            self.logger.exception(f"未预期的任务执行失败 [{task.action}]")
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
            raise ValidationError("target is required")
        
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
        
        raise NotFoundError(f"Target not found: {target}")

    def _execute_with_recovery(
        self, task: Task, screenshot: Optional[np.ndarray], index: int, sequence_name: str
    ) -> Tuple[bool, str]:
        """执行任务，失败时尝试自我修复。

        Returns:
            (success, error_message)
        """
        step_start = time.time()
        error_msg = ""

        try:
            success = self._execute_single_task(task, screenshot)
            if not success:
                error_msg = f"Task {task.action} returned False"
        except Exception as e:
            error_msg = str(e)
            success = False

        if success:
            # 记录成功
            self.execution_diary.record(
                task_sequence_name=sequence_name,
                step_index=index,
                task=task,
                success=True,
                duration_ms=(time.time() - step_start) * 1000,
                screenshot=screenshot,
            )
            return True, ""

        # 失败：分析原因并尝试修复
        failure_type = self.failure_analyzer.analyze(error_msg, task)
        self.logger.info(f"失败分析: {failure_type.name} - {self.failure_analyzer.get_suggestion(failure_type)}")

        recovery_result = self.recovery_strategy.attempt_recovery(
            failure_type, task, screenshot, self
        )

        # 记录修复尝试
        self.execution_diary.record(
            task_sequence_name=sequence_name,
            step_index=index,
            task=task,
            success=recovery_result.success,
            failure_type=failure_type,
            recovery_action=recovery_result.action_taken,
            recovery_success=recovery_result.success,
            error_message=error_msg,
            duration_ms=(time.time() - step_start) * 1000,
            screenshot=screenshot,
        )

        if recovery_result.success:
            self.logger.info(f"自我修复成功: {recovery_result.action_taken} - {recovery_result.detail}")
            return True, ""

        return False, error_msg

    def _handle_failure(self, task: Task, retry_count: int) -> bool:
        """处理任务失败，尝试重试

        Args:
            retry_count: 当前已重试的次数（从0开始）
        """
        if retry_count < self.config.max_retries:
            self.logger.warning(f"任务失败，第 {retry_count + 1} 次重试...")
            time.sleep(self.config.retry_delay * (retry_count + 1))
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









