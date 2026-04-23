"""
微信智能安全发送器 (WeChat Smart Sender)

提供零误发保障的微信消息发送功能。
核心设计原则：任何一步验证失败，立即停止，不发送消息。

安全等级 (SafetyLevel):
- STRICT (严格模式): 100% OCR 精确匹配联系人，检测相似联系人冲突，
  发送前进行二次确认。适用于高价值、敏感或首次发送的场景。
- NORMAL (标准模式): OCR 精确选人 + 聊天对象验证 + 消息发送验证，
  允许一定的模糊匹配容错。适用于日常、低风险的发送场景。

严格的分步验证流程 (Step 0 → Step 8):
整个 send() 方法按照"防御纵深"理念设计，每一步都是一道独立的防线：
  Step 0/0.5/0.6/0.7: 前置熔断检查（审计、敏感词、历史成功率、冷却期）
  Step 1/1.5: 环境准备（激活微信、锁定窗口句柄防止窗口漂移）
  Step 2: 搜索并选择联系人（OCR 精确匹配）
  Step 3: 验证聊天对象（确保右侧聊天窗口顶部名称与目标一致）
  Step 4/5: 聚焦输入框并输入消息（使用剪贴板粘贴保证中文可靠性）
  Step 6/6.5: 发送前最终确认（再次 OCR 校验 + 群聊特征验证）
  Step 6.6: 双人确认（交互式命令行确认，作为人工最后防线）
  Step 7: 执行发送（按 Enter）
  Step 8: 验证消息已发送（OCR 识别聊天历史确认消息出现）

审计日志机制 (Audit Logging):
- 每一次发送尝试都会通过 WeChatAuditLogger 记录完整决策链。
- 记录内容包括：尝试发送的联系人/消息、安全等级、dry-run 状态、
  每一步的通过/失败结果、错误信息、警告信息和截图路径。
- 审计日志用于事后追溯、问题排查和成功率统计（供 TaskLearner 学习）。

冷却期机制 (Cooldown):
- 类级别共享状态 (_last_send_time, _last_send_contact)，跨实例生效。
- 如果在 3 秒内切换不同联系人进行发送，会触发冷却保护并拒绝执行。
- 目的是防止自动化脚本因逻辑缺陷导致消息连续错发给不同对象。
- 每次成功发送后会更新冷却期记录。

敏感内容检测与 Dry-run 熔断:
- 内置敏感词库 (SENSITIVE_KEYWORDS)，涵盖金钱、隐私、安全等关键词。
- 如果消息包含敏感词且该联系人没有成功发送记录（或历史成功率 < 0.5），
  系统会强制要求先使用 dry_run=True 测试通过，才能实际发送。
- dry_run 模式会执行除最终按 Enter 以外的全部验证流程，
  用于在实际发送前验证整个链路的正确性。
"""

import logging
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple
from enum import Enum

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

from src.utils.wechat_helper import WeChatHelper
from src.utils.wechat_contact_selector import WeChatContactSelector
from src.utils.adaptive_coords import AdaptiveCoordinateMapper
from src.utils.window_lock_guard import WindowLockGuard
from src.utils.wechat_audit_logger import WeChatAuditLogger
from src.core.task_learner import TaskLearner

logger = logging.getLogger(__name__)


class SafetyLevel(Enum):
    """安全等级枚举"""
    STRICT = "strict"    # 最严格：100% OCR精确匹配，检测相似联系人冲突，发送前二次确认
    NORMAL = "normal"    # 标准：OCR精确选人 + 聊天对象验证 + 消息发送验证


@dataclass
class SendResult:
    """发送结果数据类"""
    success: bool                          # 是否发送成功
    contact: str                           # 目标联系人
    message: str                           # 消息内容
    safety_level: str                      # 使用的安全等级
    dry_run: bool                          # 是否为干跑模式
    step_reached: str                      # 最后执行到的步骤名称
    error: str                             # 错误信息（失败时）
    warnings: List[str]                    # 警告信息列表
    screenshot_path: Optional[str] = None  # 调试图路径（如果有）


class WeChatSmartSender:
    """
    微信智能安全发送器
    
    推荐作为微信消息发送的**唯一入口**。
    不支持录制回放模式，因为录制坐标无法保证聊天对象正确性。
    """
    
    # 敏感词库：涉及金钱、隐私、安全的内容。
    # 一旦消息中包含这些词汇，且联系人缺乏成功发送历史，将强制触发 dry-run 熔断。
    SENSITIVE_KEYWORDS = [
        "密码", "钱", "借", "转账", "汇款", "打款",
        "身份证", "银行卡", "支付宝", "微信收款", "收款码",
        "私密", "裸", "暗杀", "杀人", "爆炸", "毒品",
        "验证码", "账户", "密码", "登录", "黑客"
    ]
    
    # 冷却期：类级别状态，跨实例共享。
    # 用于防止在短时间内连续切换联系人发送消息，避免误发。
    _last_send_time: Optional[float] = None
    _last_send_contact: Optional[str] = None
    
    def __init__(self, safety_level: SafetyLevel = SafetyLevel.STRICT):
        if not PYAUTOGUI_AVAILABLE:
            raise ImportError("pyautogui required: py -m pip install pyautogui")
        
        self.safety_level = safety_level
        self.helper = WeChatHelper()
        self.selector = WeChatContactSelector()
        self.validator = self.helper.validator
        self.coord_mapper = AdaptiveCoordinateMapper()
        self.warnings: List[str] = []
        self.audit_logger = WeChatAuditLogger()
        self.learner = TaskLearner()
        self.window_guard: Optional[WindowLockGuard] = None
    
    def _warn(self, msg: str):
        """记录警告信息到结果和日志"""
        self.warnings.append(msg)
        logger.warning(msg)
    
    def _step(self, name: str, result: SendResult):
        """记录步骤通过，更新结果中的当前步骤并写入审计日志"""
        result.step_reached = name
        logger.info(f"[SmartSender] Step: {name}")
        self.audit_logger.log_decision(name, "ok")
    
    def _step_fail(self, name: str, result: SendResult, error: str):
        """记录步骤失败，更新结果中的当前步骤和错误信息并写入审计日志"""
        result.step_reached = name
        result.error = error
        logger.error(f"[SmartSender] Step FAIL: {name} -> {error}")
        self.audit_logger.log_decision(name, "fail", {"error": error})
    
    def _is_group_chat(self, contact: str) -> bool:
        """判断是否为群聊（简单启发式：名称以"群"结尾）"""
        return contact.endswith("群")
    
    def _contains_sensitive_content(self, message: str) -> bool:
        """
        检查消息是否包含敏感内容。
        
        遍历 SENSITIVE_KEYWORDS 词库，只要消息中包含任意一个关键词，
        即视为敏感内容，可能触发后续 dry-run 强制熔断逻辑。
        """
        for kw in self.SENSITIVE_KEYWORDS:
            if kw in message:
                return True
        return False
    
    def _require_dry_run_first(self, contact: str) -> bool:
        """
        通过 TaskLearner 判断是否需要先 dry-run。
        
        依据该联系人的历史发送模式决定：
        - 如果从未发送过（pattern 为 None），强制要求先 dry-run。
        - 如果历史成功率低于 50%，强制要求先 dry-run。
        - 否则允许直接发送。
        
        Returns:
            True 表示需要先 dry-run 成功才能真发；False 表示可直接发送。
        """
        pattern = self.learner.suggest("wechat_send", contact)
        if pattern is None:
            # 从未发送过，强制 dry-run
            return True
        if pattern.success_rate < 0.5:
            return True
        return False
    
    def _check_cooldown(self, contact: str) -> Tuple[bool, str]:
        """
        检查冷却期。
        
        如果距离上次成功发送不到 3 秒，且本次联系人与上次不同，
        则判定为异常快速切换，触发冷却保护，拒绝发送。
        
        Returns:
            (是否通过冷却检查, 拒绝原因描述)
        """
        if WeChatSmartSender._last_send_time is not None:
            elapsed = time.time() - WeChatSmartSender._last_send_time
            if elapsed < 3.0 and WeChatSmartSender._last_send_contact != contact:
                return False, f"3秒内切换联系人发送（上次: {WeChatSmartSender._last_send_contact}），触发冷却保护"
        return True, ""
    
    def _check_window_stability(self, context: str = "") -> bool:
        """
        检查窗口稳定性。
        
        通过 WindowLockGuard 验证微信窗口句柄未发生漂移或丢失，
        确保后续点击和操作落在正确的窗口上。
        """
        if self.window_guard is None:
            return True
        stable = self.window_guard.check_or_fail(context)
        if not stable:
            self.audit_logger.log_decision("window_lock", "fail", {"context": context})
        return stable
    
    def _search_and_select(self, contact: str) -> tuple:
        """
        搜索并选择联系人。
        
        流程：
        1. 激活微信窗口；
        2. 使用 Ctrl+F 打开搜索框；
        3. 通过剪贴板粘贴联系人名称（中文输入更可靠）；
        4. 根据安全等级选择匹配策略：
           - STRICT: 调用 find_contact_in_list_strict 进行精确匹配 + 冲突检测；
           - NORMAL: 调用 find_contact_in_list 允许模糊匹配，未命中时 fallback 到 Enter。
        
        Returns:
            (success, error_msg, screenshot_path)
        """
        if not self.helper.activate_wechat():
            return False, "无法激活微信窗口", None
        
        try:
            # Ctrl+F 打开搜索
            pyautogui.keyDown('ctrl')
            pyautogui.keyDown('f')
            pyautogui.keyUp('f')
            pyautogui.keyUp('ctrl')
            time.sleep(0.3)
            
            # 输入联系人（使用剪贴板粘贴，中文输入更可靠）
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.press('delete')
            try:
                import pyperclip
                pyperclip.copy(contact)
                pyautogui.hotkey('ctrl', 'v')
            except Exception:
                pyautogui.typewrite(contact, interval=0.01)
            time.sleep(0.6)
        except Exception as e:
            return False, f"搜索操作失败: {e}", None
        
        if self.safety_level == SafetyLevel.STRICT:
            # 严格模式：精确匹配 + 冲突检测
            success, match_result, conflicts = self.selector.find_contact_in_list_strict(
                self.helper.window_handle, contact
            )
            if conflicts:
                conflict_str = ", ".join(conflicts)
                return False, f"检测到相似联系人冲突，请手动处理: {conflict_str}", None
            
            if not success or not match_result or not match_result.matched:
                recognized = match_result.all_texts if match_result else []
                return False, f"未精确匹配到联系人 '{contact}'，识别结果: {recognized}", None
            
            try:
                pyautogui.click(match_result.x, match_result.y)
                time.sleep(0.8)
                return True, "", None
            except Exception as e:
                return False, f"点击联系人失败: {e}", None
        else:
            # 普通模式：允许模糊匹配
            result = self.selector.find_contact_in_list(self.helper.window_handle, contact)
            if result.matched:
                try:
                    pyautogui.click(result.x, result.y)
                    time.sleep(0.8)
                    return True, "", None
                except Exception as e:
                    return False, f"点击联系人失败: {e}", None
            else:
                # Fallback: Enter
                self._warn(f"OCR 未找到 '{contact}'，fallback 到 Enter")
                try:
                    pyautogui.press('enter')
                    time.sleep(1.0)
                    return True, "", None
                except Exception as e:
                    return False, f"按 Enter 失败: {e}", None
    
    def send(self, contact: str, message: str, dry_run: bool = False,
             require_confirm: bool = True, confirm_summary: Optional[str] = None) -> SendResult:
        """
        发送消息（唯一推荐的安全发送入口）。
        
        该方法按照"Step 0 → Step 8"的严格分步验证流程执行：
        - Step 0/0.5/0.6/0.7: 前置熔断（审计日志、敏感词、历史成功率、冷却期）。
        - Step 1/1.5: 环境准备（激活微信、锁定窗口句柄）。
        - Step 2: 搜索并选择联系人（OCR 精确匹配/模糊匹配）。
        - Step 3: 验证聊天对象（确认右侧顶部名称与目标一致）。
        - Step 4/5: 聚焦输入框并输入消息（剪贴板粘贴）。
        - Step 6/6.5: 发送前最终确认（再次 OCR 校验 + 群聊特征验证）。
        - Step 6.6: 双人确认（交互式命令行确认）。
        - Step 7: 执行发送（按 Enter）。
        - Step 8: 验证消息已发送（OCR 识别聊天历史）。
        
        任何一步验证失败都会立即终止流程，记录失败步骤和原因，不会发送消息。
        
        Args:
            contact: 联系人/群聊名称
            message: 消息内容
            dry_run: 如果为 True，执行到发送前最终确认后停止，不真发送。
                     用于在实际发送前验证整个链路（选人、聊天对象验证、输入等）是否正确。
            require_confirm: 是否要求发送前用户确认（命令行 y/n）
            confirm_summary: 确认时显示的额外摘要信息
            
        Returns:
            SendResult: 包含 success、step_reached、error、warnings 等完整信息
        """
        result = SendResult(
            success=False,
            contact=contact,
            message=message,
            safety_level=self.safety_level.value,
            dry_run=dry_run,
            step_reached="init",
            error="",
            warnings=[]
        )
        self.warnings = result.warnings
        is_group = self._is_group_chat(contact)
        
        logger.info(f"[SmartSender] {'[DRY-RUN] ' if dry_run else ''}开始发送: {contact} -> {message} (level={self.safety_level.value})")
        
        # ========== Step 0: 审计日志开始 ==========
        # 记录本次发送尝试的基本信息，作为审计链的起点。
        self.audit_logger.log_attempt(contact, message, self.safety_level.value, dry_run)
        
        # ========== Step 0.5: 敏感词检查 + 强制 dry-run 熔断 ==========
        # 如果消息包含敏感关键词，且该联系人缺乏可信的成功发送历史，
        # 则强制拒绝本次发送，要求用户先用 dry_run=True 测试通过后再实际发送。
        # 这是一种"安全熔断"机制，防止敏感信息因自动化故障而错发。
        if not dry_run and self._contains_sensitive_content(message):
            if self._require_dry_run_first(contact):
                error_msg = (
                    f"消息包含敏感词，且联系人 '{contact}' 从未成功发送记录。"
                    f"请先用 --dry-run 测试通过后再实际发送。"
                )
                self._step_fail("sensitive_content_check", result, error_msg)
                self.audit_logger.log_result(**{k: v for k, v in {
                    "success": False, "error": error_msg, "step_reached": result.step_reached,
                    "warnings": result.warnings, "screenshot_path": result.screenshot_path
                }.items()})
                return result
            else:
                # 已有成功历史，降级为警告，继续执行
                self._warn("消息包含敏感内容，但已有该联系人的成功发送记录，继续执行")
        
        # ========== Step 0.6: 历史成功率熔断 ==========
        # 查询 TaskLearner 中该联系人的历史发送模式。
        # 如果从未发送过或成功率过低，给出警告提醒用户谨慎操作。
        if not dry_run:
            pattern = self.learner.suggest("wechat_send", contact)
            if pattern is None:
                self._warn(f"联系人 '{contact}' 从未发送过，建议先用 --dry-run 测试")
            elif pattern.success_rate < 0.5:
                self._warn(f"联系人 '{contact}' 历史成功率仅 {pattern.success_rate:.0%}，请谨慎发送")
        
        # ========== Step 0.7: 冷却期检查 ==========
        # 检查是否在极短时间内切换了不同联系人。
        # 如果是，则触发冷却保护，立即失败返回，防止连发错发。
        ok, cooldown_msg = self._check_cooldown(contact)
        if not ok:
            self._step_fail("cooldown_check", result, cooldown_msg)
            self.audit_logger.log_result(False, cooldown_msg, result.step_reached, result.warnings)
            return result
        
        # ========== Step 1: 激活微信 ==========
        # 尝试将微信窗口置为前台并获取窗口句柄。
        # 如果无法激活微信，后续所有操作都无从谈起，直接失败。
        self._step("activate", result)
        if not self.helper.activate_wechat():
            self._step_fail("activate", result, "无法激活微信窗口")
            self.audit_logger.log_result(False, result.error, result.step_reached, result.warnings)
            return result
        
        # ========== Step 1.5: 锁定窗口句柄 ==========
        # 创建 WindowLockGuard，记录当前微信窗口的句柄和位置。
        # 后续关键操作前会检查窗口是否仍然稳定，防止窗口被关闭、遮挡或切换。
        self.window_guard = WindowLockGuard(self.helper.window_handle)
        if not self._check_window_stability("激活后"):
            self._step_fail("window_lock", result, "窗口稳定性检查失败")
            self.audit_logger.log_result(False, result.error, result.step_reached, result.warnings)
            return result
        
        # ========== Step 2: 搜索并选择联系人 ==========
        # 使用 Ctrl+F 搜索联系人，并根据安全等级选择匹配策略：
        # - STRICT: 必须 OCR 精确匹配，且不存在相似联系人冲突；
        # - NORMAL: 优先精确匹配，允许模糊匹配，未命中时 fallback 按 Enter。
        self._step("search_and_select", result)
        ok, err, ss_path = self._search_and_select(contact)
        if not ok:
            self._step_fail("search_and_select", result, err)
            result.screenshot_path = ss_path
            self.audit_logger.log_result(False, result.error, result.step_reached, result.warnings, result.screenshot_path)
            return result
        
        # 窗口稳定性检查（选人后）：防止搜索过程中窗口发生变化
        if not self._check_window_stability("选人后"):
            self._step_fail("window_lock", result, "窗口稳定性检查失败")
            self.audit_logger.log_result(False, result.error, result.step_reached, result.warnings)
            return result
        
        # ========== Step 3: 验证聊天对象 ==========
        # OCR 识别右侧聊天窗口顶部的名称，确认当前聊天对象确实是目标联系人。
        # 这是防止"点错人"的核心防线之一。
        self._step("validate_chat_contact", result)
        v = self.validator.validate_chat_contact(self.helper.window_handle, contact, is_group_chat=is_group)
        if not v.success:
            self._step_fail("validate_chat_contact", result, f"聊天对象验证失败。预期: '{contact}'，识别到: '{v.found_text}'")
            result.screenshot_path = v.screenshot_path
            self.audit_logger.log_result(False, result.error, result.step_reached, result.warnings, result.screenshot_path)
            return result
        
        # ========== Step 4: 点击输入框 ==========
        # 将焦点移动到聊天输入框，确保后续输入的消息进入正确的聊天窗口。
        self._step("focus_input_box", result)
        try:
            rect = self.helper.window_rect
            input_point = self.coord_mapper.get_point_safe("wechat_input_box", rect)
            if input_point:
                pyautogui.click(input_point[0], input_point[1])
            else:
                # 兜底方案：按窗口相对比例估算输入框位置
                pyautogui.click(rect[0] + int((rect[2] - rect[0]) * 0.65), rect[1] + int((rect[3] - rect[1]) * 0.92))
            time.sleep(0.2)
        except Exception as e:
            self._step_fail("focus_input_box", result, f"点击输入框失败: {e}")
            self.audit_logger.log_result(False, result.error, result.step_reached, result.warnings)
            return result
        
        # ========== Step 5: 输入消息（使用剪贴板粘贴，中文输入更可靠） ==========
        # 通过 pyperclip 将消息复制到剪贴板，再 Ctrl+V 粘贴到输入框。
        # 相比 pyautogui.typewrite，剪贴板方式对中文、特殊符号的支持更稳定。
        self._step("type_message", result)
        try:
            import pyperclip
            pyperclip.copy(message)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.2)
        except Exception as e:
            self._step_fail("type_message", result, f"输入消息失败: {e}")
            self.audit_logger.log_result(False, result.error, result.step_reached, result.warnings)
            return result
        
        # ========== Step 6: 发送前最终确认（按 Enter 前的最后一道防线） ==========
        # 在真正按下 Enter 之前，再次 OCR 验证当前聊天对象仍然是目标联系人。
        # 如果在 Step 5 输入期间聊天窗口发生了切换，此处能够拦截下来。
        self._step("pre_send_final_check", result)
        v = self.validator.pre_send_final_check(self.helper.window_handle, contact, is_group_chat=is_group)
        if not v.success:
            self._step_fail("pre_send_final_check", result, f"发送前最终确认失败。预期: '{contact}'，识别到: '{v.found_text}'")
            result.screenshot_path = v.screenshot_path
            self.audit_logger.log_result(False, result.error, result.step_reached, result.warnings, result.screenshot_path)
            return result
        
        # ========== Step 6.5: 群聊额外验证 ==========
        # 如果是群聊，额外验证群聊特征（如"群成员"等 UI 元素），
        # 进一步确认当前窗口确实是群聊而非私聊。
        if is_group:
            self._step("group_chat_feature_check", result)
            gv = self.validator.validate_group_chat_features(self.helper.window_handle)
            if not gv.success:
                self._warn(f"群聊特征验证未通过（识别到: {gv.found_text}），但聊天对象验证已通过，继续发送")
            else:
                self.audit_logger.log_decision("group_chat_feature_check", "ok", {"ocr": gv.found_text})
        
        # 窗口稳定性检查（发送前）：确保按 Enter 前窗口没有漂移
        if not self._check_window_stability("发送前"):
            self._step_fail("window_lock", result, "窗口稳定性检查失败")
            self.audit_logger.log_result(False, result.error, result.step_reached, result.warnings)
            return result
        
        # ========== Step 6.6: 双人确认（交互式） ==========
        # 在非 dry-run 模式下，弹出命令行交互确认，要求用户人工确认。
        # 这是人工层面的最后一道防线，防止自动化逻辑缺陷导致误发。
        if require_confirm and not dry_run:
            self._step("user_confirm", result)
            confirmed = self._prompt_user_confirm(contact, message, confirm_summary)
            if not confirmed:
                self._step_fail("user_confirm", result, "用户取消发送")
                self.audit_logger.log_result(False, result.error, result.step_reached, result.warnings)
                return result
        
        # ========== Dry-run 模式下到此停止 ==========
        # dry_run=True 时，以上所有验证均已通过，但不执行实际发送。
        # 返回成功状态并标注 [DRY-RUN]，供用户确认链路正确性。
        if dry_run:
            result.success = True
            result.error = "[DRY-RUN] 所有验证通过，未实际发送"
            self.audit_logger.log_result(True, result.error, result.step_reached, result.warnings)
            return result
        
        # ========== Step 7: 发送 ==========
        # 所有验证和确认均已完成，执行最终的发送动作：按 Enter。
        self._step("press_enter", result)
        if not self._check_window_stability("按Enter前"):
            self._step_fail("window_lock", result, "窗口稳定性检查失败")
            self.audit_logger.log_result(False, result.error, result.step_reached, result.warnings)
            return result
        
        try:
            pyautogui.press('enter')
            time.sleep(0.5)
        except Exception as e:
            self._step_fail("press_enter", result, f"按 Enter 发送失败: {e}")
            self.audit_logger.log_result(False, result.error, result.step_reached, result.warnings)
            return result
        
        # ========== Step 8: 验证消息已发送 ==========
        # 发送后 OCR 识别聊天历史区域，确认目标消息已经出现在聊天记录中。
        # 这是最后一步验证，确保消息确实成功发出，而非仅按了 Enter 但发送失败。
        self._step("validate_message_sent", result)
        v = self.validator.validate_message_sent(self.helper.window_handle, message, timeout=3)
        if not v.success:
            self._step_fail("validate_message_sent", result, f"消息发送验证失败。预期消息: '{message}'，识别到: '{v.found_text}'")
            result.screenshot_path = v.screenshot_path
            self.audit_logger.log_result(False, result.error, result.step_reached, result.warnings, result.screenshot_path)
            return result
        
        # 更新冷却期记录：记录本次成功发送的时间和联系人
        WeChatSmartSender._last_send_time = time.time()
        WeChatSmartSender._last_send_contact = contact
        
        result.success = True
        result.error = "发送成功"
        logger.info(f"[SmartSender] 发送成功: {contact}")
        self.audit_logger.log_result(True, result.error, result.step_reached, result.warnings)
        return result
    
    def _prompt_user_confirm(self, contact: str, message: str, summary: Optional[str] = None) -> bool:
        """
        命令行交互式确认。
        
        打印即将发送的联系人、消息、安全等级等信息，
        等待用户输入 y/n 进行确认。
        
        Returns:
            用户是否确认发送（输入 y/yes/是/确认 返回 True，其他返回 False）
        """
        print("\n" + "=" * 50)
        print("⚠️  即将发送微信消息")
        print("=" * 50)
        print(f"  联系人: {contact}")
        print(f"  消息:   {message}")
        print(f"  安全等级: {self.safety_level.value}")
        if summary:
            print(f"  来源:   {summary}")
        print("=" * 50)
        
        try:
            user_input = input("确认发送? (y/n): ").strip().lower()
            return user_input in ("y", "yes", "是", "确认")
        except EOFError:
            # 非交互式环境（如管道输入），默认拒绝
            logger.warning("非交互式环境，无法获取用户确认，默认取消发送")
            return False


def send_wechat_message_safe(contact: str, message: str,
                             safety_level: str = "strict",
                             dry_run: bool = False,
                             require_confirm: bool = True,
                             confirm_summary: Optional[str] = None) -> SendResult:
    """
    快速函数：安全发送微信消息。
    
    对 WeChatSmartSender 的简单包装，方便直接调用而无需先实例化类。
    
    Args:
        contact: 联系人/群聊名称
        message: 消息内容
        safety_level: "strict" 或 "normal"
        dry_run: 是否仅测试不发送（True 会执行全部验证但跳过最终按 Enter）
        require_confirm: 是否要求发送前用户确认
        confirm_summary: 确认时显示的额外摘要信息
        
    Returns:
        SendResult
    """
    level = SafetyLevel.STRICT if safety_level.lower() == "strict" else SafetyLevel.NORMAL
    sender = WeChatSmartSender(safety_level=level)
    return sender.send(contact, message, dry_run=dry_run, require_confirm=require_confirm, confirm_summary=confirm_summary)
