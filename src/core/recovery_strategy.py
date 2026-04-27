"""修复策略 —— 根据失败类型自动选择并执行修复动作。

Phase 1: 传统修复（OCR、YOLO、重试）
Phase 2: Skill 经验修复 + VLM 融合诊断（三层模型储备）

保守模式：每种失败类型只尝试一次最可能有效的修复策略，
成功则继续执行，失败则退回原有重试逻辑。
"""

import time
from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np

from .failure_analyzer import FailureType
from .models import Task
from .skill_manager import SkillManager
from .visual_diagnostician import VisualDiagnostician, DiagnosisReport
from ..utils.exceptions import NotFoundError


@dataclass
class RecoveryResult:
    """修复结果。"""
    success: bool
    action_taken: str = ""
    detail: str = ""


class RecoveryStrategy:
    """修复策略引擎。

    针对不同的 FailureType，执行对应的修复动作。
    所有修复动作都接收 (task, screenshot, executor) 参数。
    """

    def __init__(self, logger=None, skill_manager=None, diagnostician=None):
        self.logger = logger
        self.skill_manager = skill_manager or SkillManager()
        self.diagnostician = diagnostician

    def attempt_recovery(
        self,
        failure_type: FailureType,
        task: Task,
        screenshot: Optional[np.ndarray],
        executor,
    ) -> RecoveryResult:
        """尝试一次修复（Phase 1 + Phase 2 融合）。

        修复层级：
        1. Skill 经验修复（查历史成功记录）
        2. 传统修复（OCR/YOLO/重试）
        3. VLM 融合诊断（Minimax → Mimo → GPT-5）
        """
        if self.logger:
            self.logger.info(f"尝试修复: {failure_type.name}, 任务: {task.action}")

        # 第一层：Skill 经验修复
        skill_result = self._try_skill_recovery(failure_type, task, screenshot, executor)
        if skill_result and skill_result.success:
            return skill_result

        # 第二层：传统修复
        handler = self._get_handler(failure_type)
        if handler:
            try:
                result = handler(task, screenshot, executor)
                if result.success:
                    return result
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"传统修复失败: {e}")

        # 第三层：VLM 融合诊断（Phase 2）
        if self.diagnostician and screenshot is not None:
            try:
                return self._try_vlm_recovery(failure_type, task, screenshot, executor)
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"VLM 诊断修复失败: {e}")

        # 全部失败
        return RecoveryResult(
            success=False,
            action_taken="all_methods_exhausted",
            detail="所有修复层级均失败",
        )

    def _try_skill_recovery(
        self, failure_type: FailureType, task: Task, screenshot, executor
    ) -> Optional[RecoveryResult]:
        """尝试用 Skill 历史经验修复"""
        if not self.skill_manager:
            return None
        skill = self.skill_manager.find_matching_skill(
            failure_type=failure_type.name,
            task_action=task.action,
            original_target=task.target or "",
        )
        if skill is None:
            return None

        if self.logger:
            self.logger.info(f"命中 Skill: {skill.id} -> {skill.successful_target}")

        try:
            # 根据 skill 的成功策略执行修复
            if skill.successful_strategy in ("ocr_text_search", "yolo_text_match", "yolo_type_match"):
                x, y = skill.successful_center
                if task.action in ("click", "double_click", "right_click"):
                    executor.mouse.click(x, y)
                elif task.action == "type":
                    executor.mouse.click(x, y)
                    if task.value:
                        executor.keyboard.type_text(task.value)
                return RecoveryResult(
                    success=True,
                    action_taken=f"skill:{skill.successful_strategy}",
                    detail=f"通过 Skill 历史经验修复: {skill.id}",
                )
            elif skill.successful_strategy in ("coordinate_offset",):
                # 坐标偏移策略
                x, y = skill.successful_center
                if task.action in ("click", "double_click", "right_click"):
                    executor.mouse.click(x, y)
                return RecoveryResult(
                    success=True,
                    action_taken="skill:coordinate_offset",
                    detail=f"Skill 坐标偏移修复: {skill.id}",
                )
        except Exception as e:
            if self.logger:
                self.logger.debug(f"Skill 修复执行失败: {e}")
        return None

    def _try_vlm_recovery(
        self, failure_type: FailureType, task: Task, screenshot, executor
    ) -> RecoveryResult:
        """VLM 融合诊断修复"""
        if self.logger:
            self.logger.info("进入 VLM 融合诊断...")

        # 获取 YOLO + OCR 结果
        yolo_elements = []
        ocr_texts = []
        try:
            if hasattr(executor, "detector") and executor.detector:
                yolo_elements = executor.detector.detect(screenshot)
        except Exception:
            pass
        try:
            if hasattr(executor, "locator") and executor.locator:
                from ..perception.ocr import TextRecognizer
                recognizer = TextRecognizer()
                ocr_texts = recognizer.recognize(screenshot)
        except Exception:
            pass

        # 执行诊断
        report, tier_result = self.diagnostician.diagnose(
            failure_type=failure_type,
            task=task,
            screenshot=screenshot,
            yolo_elements=yolo_elements,
            ocr_texts=ocr_texts,
            error_message="",
        )

        if self.logger:
            self.logger.info(
                f"VLM 诊断完成: tier={tier_result.tier}, "
                f"presence={report.target_presence}, confidence={report.confidence}"
            )

        # 根据诊断结果执行修复
        recovery_result = self._execute_diagnosis_report(report, task, screenshot, executor)

        # Verify Loop：修复后验证
        if recovery_result.success and self.diagnostician:
            time.sleep(1.0)  # 等待界面响应
            try:
                new_screenshot = executor.screen.capture()
                verify = self.diagnostician.verify(
                    tier=tier_result.tier,
                    screenshot_before=screenshot,
                    screenshot_after=new_screenshot,
                    task=task,
                )
                if not verify.get("success", False):
                    if self.logger:
                        self.logger.warning(f"Verify 失败: {verify.get('observation', '')}")
                    # Verify 失败，尝试 fallback_strategy
                    if report.fallback_strategy:
                        recovery_result = self._execute_fallback(
                            report, task, new_screenshot, executor
                        )
                else:
                    if self.logger:
                        self.logger.info("Verify 通过")
            except Exception as e:
                if self.logger:
                    self.logger.debug(f"Verify 异常: {e}")

        # 如果最终成功，沉淀 Skill
        if recovery_result.success and self.skill_manager:
            try:
                center = report.suggested_target.get("center", [0, 0])
                self.diagnostician.distill_skill(
                    tier=tier_result.tier,
                    failure_type=failure_type,
                    task=task,
                    report=report,
                    successful_center=center,
                    screen_context_hash=self._hash_screen(screenshot),
                )
                # 同时生成 skill md 供模型学习
                self.skill_manager.generate_skill_md()
            except Exception as e:
                if self.logger:
                    self.logger.debug(f"Skill 沉淀失败: {e}")

        return recovery_result

    def _execute_diagnosis_report(
        self, report: DiagnosisReport, task: Task, screenshot, executor
    ) -> RecoveryResult:
        """根据诊断报告执行修复"""
        st = report.suggested_target
        st_type = st.get("type", "")
        st_value = st.get("value", "")
        center = st.get("center", [0, 0])

        try:
            if st_type == "coordinate" and center:
                x, y = center
                if task.action in ("click", "double_click", "right_click"):
                    executor.mouse.click(x, y)
                elif task.action == "type":
                    executor.mouse.click(x, y)
                    if task.value:
                        executor.keyboard.type_text(task.value)
                return RecoveryResult(
                    success=True,
                    action_taken=f"vlm:{report.suggested_action}",
                    detail=f"VLM 推荐坐标 ({x},{y}): {report.reasoning[:100]}",
                )

            elif st_type in ("ocr_text", "yolo_element") and st_value:
                # 尝试用推荐值重新定位
                task_copy = Task(task.action, target=st_value, value=task.value, delay=task.delay)
                success = executor._execute_single_task(task_copy, screenshot)
                if success:
                    return RecoveryResult(
                        success=True,
                        action_taken=f"vlm:relocate_to_{st_type}",
                        detail=f"VLM 推荐重定位到 '{st_value}': {report.reasoning[:100]}",
                    )

            # 语义等价描述逐一尝试
            for equiv in report.semantic_equivalents:
                try:
                    task_copy = Task(task.action, target=equiv, value=task.value, delay=task.delay)
                    success = executor._execute_single_task(task_copy, screenshot)
                    if success:
                        return RecoveryResult(
                            success=True,
                            action_taken="vlm:semantic_equivalent",
                            detail=f"语义等价匹配 '{equiv}': {report.reasoning[:100]}",
                        )
                except Exception:
                    continue

        except Exception as e:
            if self.logger:
                self.logger.debug(f"诊断修复执行失败: {e}")

        return RecoveryResult(
            success=False,
            action_taken="vlm_diagnosis_failed",
            detail=f"VLM 诊断建议无法执行: {report.reasoning[:100]}",
        )

    def _execute_fallback(
        self, report: DiagnosisReport, task: Task, screenshot, executor
    ) -> RecoveryResult:
        """执行 fallback_strategy"""
        fallback = report.fallback_strategy.lower()
        try:
            if "esc" in fallback or "关闭弹窗" in fallback:
                executor.keyboard.press("esc")
                time.sleep(0.5)
                success = executor._execute_single_task(task, screenshot)
                if success:
                    return RecoveryResult(success=True, action_taken="vlm:fallback_esc")
            elif "scroll" in fallback or "滚动" in fallback:
                executor.mouse.scroll(500)
                time.sleep(0.5)
                new_screenshot = executor.screen.capture()
                success = executor._execute_single_task(task, new_screenshot)
                if success:
                    return RecoveryResult(success=True, action_taken="vlm:fallback_scroll")
        except Exception:
            pass
        return RecoveryResult(success=False, action_taken="vlm:fallback_failed")

    def _hash_screen(self, screenshot: np.ndarray) -> str:
        """生成屏幕上下文指纹（简化版：缩略图平均哈希）"""
        import hashlib
        try:
            small = cv2.resize(screenshot, (32, 32))
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY) if len(small.shape) == 3 else small
            avg = gray.mean()
            bits = "".join("1" if p > avg else "0" for row in gray for p in row)
            return hashlib.md5(bits.encode()).hexdigest()[:16]
        except Exception:
            return "unknown"

    def _get_handler(self, failure_type: FailureType):
        """获取对应失败类型的修复处理器。"""
        handlers = {
            FailureType.ELEMENT_NOT_FOUND: self._heal_element_not_found,
            FailureType.TIMING_ISSUE: self._heal_timing_issue,
            FailureType.UI_CHANGED: self._heal_ui_changed,
            FailureType.NETWORK_ERROR: self._heal_network_error,
            FailureType.PERMISSION_DENIED: self._heal_permission_denied,
            FailureType.VALIDATION_ERROR: self._heal_validation_error,
            FailureType.RESOURCE_ERROR: self._heal_resource_error,
            FailureType.WRONG_ELEMENT: self._heal_wrong_element,
            FailureType.UNKNOWN: self._heal_unknown,
        }
        return handlers.get(failure_type)

    # ------------------------------------------------------------------
    # 各失败类型的修复处理器
    # ------------------------------------------------------------------

    def _heal_element_not_found(
        self, task: Task, screenshot: Optional[np.ndarray], executor
    ) -> RecoveryResult:
        """元素未找到：尝试 OCR 文本搜索。"""
        if not task.target:
            return RecoveryResult(success=False, action_taken="skip_no_target")

        # 策略1：如果 target 看起来像文本（不含坐标逗号），尝试 OCR 定位
        if "," not in task.target and not task.target.replace("-", "").isdigit():
            try:
                from ..perception.ocr import TextRecognizer

                recognizer = TextRecognizer()
                if screenshot is not None:
                    pos = recognizer.find_text(screenshot, task.target)
                    if pos:
                        x, y = pos
                        if task.action in ("click", "double_click", "right_click"):
                            executor.mouse.click(x, y)
                        elif task.action == "type":
                            executor.mouse.click(x, y)
                            if task.value:
                                executor.keyboard.type_text(task.value)
                        elif task.action == "scroll":
                            amount = int(task.value) if task.value else 3
                            executor.mouse.scroll(amount, x, y)
                        return RecoveryResult(
                            success=True,
                            action_taken="ocr_text_search",
                            detail=f"通过 OCR 找到 '{task.target}' 并执行 {task.action}",
                        )
            except Exception as e:
                if self.logger:
                    self.logger.debug(f"OCR 修复失败: {e}")

        # 策略2：如果 target 是坐标，尝试在坐标附近小幅偏移搜索
        if "," in task.target:
            try:
                parts = task.target.split(",")
                if len(parts) == 2:
                    base_x, base_y = int(parts[0]), int(parts[1])
                    # 尝试在 20px 范围内随机偏移（简单启发式）
                    offsets = [(0, 0), (10, 0), (-10, 0), (0, 10), (0, -10)]
                    for dx, dy in offsets:
                        x, y = base_x + dx, base_y + dy
                        try:
                            if task.action in ("click", "double_click", "right_click"):
                                executor.mouse.click(x, y)
                            elif task.action == "type":
                                executor.mouse.click(x, y)
                                if task.value:
                                    executor.keyboard.type_text(task.value)
                            return RecoveryResult(
                                success=True,
                                action_taken="coordinate_offset",
                                detail=f"坐标偏移 ({dx},{dy}) 后执行成功",
                            )
                        except Exception:
                            continue
            except Exception:
                pass

        return RecoveryResult(success=False, action_taken="element_not_found_fallback")

    def _heal_timing_issue(
        self, task: Task, screenshot: Optional[np.ndarray], executor
    ) -> RecoveryResult:
        """时机问题：增加等待时间后重试。"""
        extra_delay = 2.0  # 保守增加 2 秒
        time.sleep(extra_delay)

        # 如果是浏览器操作，尝试等待元素出现
        if task.action.startswith("browser_") and task.target:
            try:
                executor.browser_handler.wait_for(task.target, timeout=5)
                return RecoveryResult(
                    success=True,
                    action_taken="browser_wait",
                    detail=f"等待元素 {task.target} 出现后成功",
                )
            except Exception:
                pass

        # 桌面操作：再次截图后重试
        if not task.action.startswith("browser_"):
            try:
                new_screenshot = executor.screen.capture()
                success = executor._execute_single_task(task, new_screenshot)
                if success:
                    return RecoveryResult(
                        success=True,
                        action_taken="delay_and_retry",
                        detail=f"等待 {extra_delay}s 后重试成功",
                    )
            except Exception:
                pass

        return RecoveryResult(success=False, action_taken="timing_fallback")

    def _heal_ui_changed(
        self, task: Task, screenshot: Optional[np.ndarray], executor
    ) -> RecoveryResult:
        """UI 变化：尝试使用智能定位（YOLO 检测 + OCR）重新查找。"""
        if not task.target or screenshot is None:
            return RecoveryResult(success=False, action_taken="skip_no_context")

        try:
            from ..perception.detector import ElementDetector

            detector = ElementDetector()
            elements = detector.detect(screenshot)

            # 尝试匹配目标文本或类型
            for elem in elements:
                if elem.text and task.target.lower() in elem.text.lower():
                    x, y = elem.center
                    if task.action in ("click", "double_click", "right_click"):
                        executor.mouse.click(x, y)
                    elif task.action == "type":
                        executor.mouse.click(x, y)
                        if task.value:
                            executor.keyboard.type_text(task.value)
                    return RecoveryResult(
                        success=True,
                        action_taken="yolo_text_match",
                        detail=f"YOLO 检测到包含 '{task.target}' 的元素",
                    )

            # 尝试按元素类型匹配
            for elem in elements:
                if elem.element_type and task.target.lower() in elem.element_type.lower():
                    x, y = elem.center
                    if task.action in ("click", "double_click", "right_click"):
                        executor.mouse.click(x, y)
                    return RecoveryResult(
                        success=True,
                        action_taken="yolo_type_match",
                        detail=f"YOLO 检测到类型 '{elem.element_type}' 的元素",
                    )
        except Exception as e:
            if self.logger:
                self.logger.debug(f"YOLO 修复失败: {e}")

        return RecoveryResult(success=False, action_taken="ui_changed_fallback")

    def _heal_network_error(
        self, task: Task, screenshot: Optional[np.ndarray], executor
    ) -> RecoveryResult:
        """网络错误：短暂等待后重试浏览器操作。"""
        if not task.action.startswith("browser_"):
            return RecoveryResult(success=False, action_taken="not_browser_task")

        time.sleep(3.0)  # 等待网络恢复
        try:
            success = executor._execute_single_task(task, screenshot)
            if success:
                return RecoveryResult(
                    success=True,
                    action_taken="network_wait_retry",
                    detail="等待 3s 后网络恢复，重试成功",
                )
        except Exception:
            pass

        return RecoveryResult(success=False, action_taken="network_fallback")

    def _heal_permission_denied(
        self, task: Task, screenshot: Optional[np.ndarray], executor
    ) -> RecoveryResult:
        """权限不足：目前无法自动修复，需要人工干预。"""
        return RecoveryResult(
            success=False,
            action_taken="manual_intervention_required",
            detail="权限问题需要人工处理，建议以管理员身份运行",
        )

    def _heal_validation_error(
        self, task: Task, screenshot: Optional[np.ndarray], executor
    ) -> RecoveryResult:
        """参数验证错误：无法自动修复。"""
        return RecoveryResult(
            success=False,
            action_taken="fix_parameters",
            detail="请检查任务参数是否完整且格式正确",
        )

    def _heal_resource_error(
        self, task: Task, screenshot: Optional[np.ndarray], executor
    ) -> RecoveryResult:
        """资源未就绪：尝试初始化资源后重试。"""
        # 例如 Excel/Word 操作前确保已启动
        if task.action.startswith("excel_") or task.action == "word_document":
            try:
                if hasattr(executor, "office") and executor.office:
                    # 尝试重新初始化
                    time.sleep(1.0)
                    success = executor._execute_single_task(task, screenshot)
                    if success:
                        return RecoveryResult(
                            success=True,
                            action_taken="resource_reinit",
                            detail="资源重新初始化后成功",
                        )
            except Exception:
                pass

        return RecoveryResult(
            success=False,
            action_taken="resource_fallback",
            detail="资源未就绪，无法自动修复",
        )

    def _heal_wrong_element(
        self, task: Task, screenshot: Optional[np.ndarray], executor
    ) -> RecoveryResult:
        """找错了元素：尝试更精确的定位。"""
        # 目前策略与 ELEMENT_NOT_FOUND 类似：用 OCR/YOLO 重新定位
        return self._heal_ui_changed(task, screenshot, executor)

    def _heal_unknown(
        self, task: Task, screenshot: Optional[np.ndarray], executor
    ) -> RecoveryResult:
        """未知错误：尝试一次通用重试。"""
        time.sleep(1.0)
        try:
            if not task.action.startswith("browser_"):
                new_screenshot = executor.screen.capture()
                success = executor._execute_single_task(task, new_screenshot)
            else:
                success = executor._execute_single_task(task, screenshot)
            if success:
                return RecoveryResult(
                    success=True,
                    action_taken="generic_retry",
                    detail="通用重试成功",
                )
        except Exception:
            pass

        return RecoveryResult(success=False, action_taken="unknown_fallback")
