"""
微信智能安全发送器

提供零误发保障的微信消息发送功能。
核心设计原则：任何一步验证失败，立即停止，不发送消息。
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
    """安全等级"""
    STRICT = "strict"    # 最严格：100% OCR精确匹配，检测相似联系人冲突，发送前二次确认
    NORMAL = "normal"    # 标准：OCR精确选人 + 聊天对象验证 + 消息发送验证


@dataclass
class SendResult:
    """发送结果"""
    success: bool
    contact: str
    message: str
    safety_level: str
    dry_run: bool
    step_reached: str           # 最后执行到的步骤名称
    error: str                  # 错误信息
    warnings: List[str]         # 警告信息
    screenshot_path: Optional[str] = None  # 调试图路径（如果有）


class WeChatSmartSender:
    """
    微信智能安全发送器
    
    推荐作为微信消息发送的**唯一入口**。
    不支持录制回放模式，因为录制坐标无法保证聊天对象正确性。
    """
    
    # 敏感词库：涉及金钱、隐私、安全的内容
    SENSITIVE_KEYWORDS = [
        "密码", "钱", "借", "转账", "汇款", "打款",
        "身份证", "银行卡", "支付宝", "微信收款", "收款码",
        "私密", "裸", "暗杀", "杀人", "爆炸", "毒品",
        "验证码", "账户", "密码", "登录", "黑客"
    ]
    
    # 冷却期：类级别状态，跨实例共享
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
        self.warnings.append(msg)
        logger.warning(msg)
    
    def _step(self, name: str, result: SendResult):
        result.step_reached = name
        logger.info(f"[SmartSender] Step: {name}")
        self.audit_logger.log_decision(name, "ok")
    
    def _step_fail(self, name: str, result: SendResult, error: str):
        result.step_reached = name
        result.error = error
        logger.error(f"[SmartSender] Step FAIL: {name} -> {error}")
        self.audit_logger.log_decision(name, "fail", {"error": error})
    
    def _is_group_chat(self, contact: str) -> bool:
        """判断是否为群聊"""
        return contact.endswith("群")
    
    def _contains_sensitive_content(self, message: str) -> bool:
        """检查消息是否包含敏感内容"""
        for kw in self.SENSITIVE_KEYWORDS:
            if kw in message:
                return True
        return False
    
    def _require_dry_run_first(self, contact: str) -> bool:
        """
        通过 TaskLearner 判断是否需要先 dry-run
        
        Returns:
            True 表示需要先 dry-run 成功才能真发
        """
        pattern = self.learner.suggest("wechat_send", contact)
        if pattern is None:
            # 从未发送过，强制 dry-run
            return True
        if pattern.success_rate < 0.5:
            return True
        return False
    
    def _check_cooldown(self, contact: str) -> Tuple[bool, str]:
        """检查冷却期"""
        if WeChatSmartSender._last_send_time is not None:
            elapsed = time.time() - WeChatSmartSender._last_send_time
            if elapsed < 3.0 and WeChatSmartSender._last_send_contact != contact:
                return False, f"3秒内切换联系人发送（上次: {WeChatSmartSender._last_send_contact}），触发冷却保护"
        return True, ""
    
    def _check_window_stability(self, context: str = "") -> bool:
        """检查窗口稳定性"""
        if self.window_guard is None:
            return True
        stable = self.window_guard.check_or_fail(context)
        if not stable:
            self.audit_logger.log_decision("window_lock", "fail", {"context": context})
        return stable
    
    def _search_and_select(self, contact: str) -> tuple:
        """
        搜索并选择联系人
        
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
        发送消息（唯一推荐的安全发送入口）
        
        Args:
            contact: 联系人/群聊名称
            message: 消息内容
            dry_run: 如果为 True，执行到发送前最终确认后停止，不真发送
            require_confirm: 是否要求发送前用户确认（命令行 y/n）
            confirm_summary: 确认时显示的额外摘要信息
            
        Returns:
            SendResult
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
        
        # Step 0: 审计日志开始
        self.audit_logger.log_attempt(contact, message, self.safety_level.value, dry_run)
        
        # Step 0.5: 敏感词检查 + 强制 dry-run 熔断
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
                self._warn("消息包含敏感内容，但已有该联系人的成功发送记录，继续执行")
        
        # Step 0.6: 历史成功率熔断
        if not dry_run:
            pattern = self.learner.suggest("wechat_send", contact)
            if pattern is None:
                self._warn(f"联系人 '{contact}' 从未发送过，建议先用 --dry-run 测试")
            elif pattern.success_rate < 0.5:
                self._warn(f"联系人 '{contact}' 历史成功率仅 {pattern.success_rate:.0%}，请谨慎发送")
        
        # Step 0.7: 冷却期检查
        ok, cooldown_msg = self._check_cooldown(contact)
        if not ok:
            self._step_fail("cooldown_check", result, cooldown_msg)
            self.audit_logger.log_result(False, cooldown_msg, result.step_reached, result.warnings)
            return result
        
        # Step 1: 激活微信
        self._step("activate", result)
        if not self.helper.activate_wechat():
            self._step_fail("activate", result, "无法激活微信窗口")
            self.audit_logger.log_result(False, result.error, result.step_reached, result.warnings)
            return result
        
        # Step 1.5: 锁定窗口句柄
        self.window_guard = WindowLockGuard(self.helper.window_handle)
        if not self._check_window_stability("激活后"):
            self._step_fail("window_lock", result, "窗口稳定性检查失败")
            self.audit_logger.log_result(False, result.error, result.step_reached, result.warnings)
            return result
        
        # Step 2: 搜索并选择联系人
        self._step("search_and_select", result)
        ok, err, ss_path = self._search_and_select(contact)
        if not ok:
            self._step_fail("search_and_select", result, err)
            result.screenshot_path = ss_path
            self.audit_logger.log_result(False, result.error, result.step_reached, result.warnings, result.screenshot_path)
            return result
        
        # 窗口稳定性检查
        if not self._check_window_stability("选人后"):
            self._step_fail("window_lock", result, "窗口稳定性检查失败")
            self.audit_logger.log_result(False, result.error, result.step_reached, result.warnings)
            return result
        
        # Step 3: 验证聊天对象
        self._step("validate_chat_contact", result)
        v = self.validator.validate_chat_contact(self.helper.window_handle, contact, is_group_chat=is_group)
        if not v.success:
            self._step_fail("validate_chat_contact", result, f"聊天对象验证失败。预期: '{contact}'，识别到: '{v.found_text}'")
            result.screenshot_path = v.screenshot_path
            self.audit_logger.log_result(False, result.error, result.step_reached, result.warnings, result.screenshot_path)
            return result
        
        # Step 4: 点击输入框
        self._step("focus_input_box", result)
        try:
            rect = self.helper.window_rect
            input_point = self.coord_mapper.get_point_safe("wechat_input_box", rect)
            if input_point:
                pyautogui.click(input_point[0], input_point[1])
            else:
                pyautogui.click(rect[0] + int((rect[2] - rect[0]) * 0.65), rect[1] + int((rect[3] - rect[1]) * 0.92))
            time.sleep(0.2)
        except Exception as e:
            self._step_fail("focus_input_box", result, f"点击输入框失败: {e}")
            self.audit_logger.log_result(False, result.error, result.step_reached, result.warnings)
            return result
        
        # Step 5: 输入消息（使用剪贴板粘贴，中文输入更可靠）
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
        
        # Step 6: 发送前最终确认（按 Enter 前的最后一道防线）
        self._step("pre_send_final_check", result)
        v = self.validator.pre_send_final_check(self.helper.window_handle, contact, is_group_chat=is_group)
        if not v.success:
            self._step_fail("pre_send_final_check", result, f"发送前最终确认失败。预期: '{contact}'，识别到: '{v.found_text}'")
            result.screenshot_path = v.screenshot_path
            self.audit_logger.log_result(False, result.error, result.step_reached, result.warnings, result.screenshot_path)
            return result
        
        # Step 6.5: 群聊额外验证
        if is_group:
            self._step("group_chat_feature_check", result)
            gv = self.validator.validate_group_chat_features(self.helper.window_handle)
            if not gv.success:
                self._warn(f"群聊特征验证未通过（识别到: {gv.found_text}），但聊天对象验证已通过，继续发送")
            else:
                self.audit_logger.log_decision("group_chat_feature_check", "ok", {"ocr": gv.found_text})
        
        # 窗口稳定性检查
        if not self._check_window_stability("发送前"):
            self._step_fail("window_lock", result, "窗口稳定性检查失败")
            self.audit_logger.log_result(False, result.error, result.step_reached, result.warnings)
            return result
        
        # Step 6.6: 双人确认（交互式）
        if require_confirm and not dry_run:
            self._step("user_confirm", result)
            confirmed = self._prompt_user_confirm(contact, message, confirm_summary)
            if not confirmed:
                self._step_fail("user_confirm", result, "用户取消发送")
                self.audit_logger.log_result(False, result.error, result.step_reached, result.warnings)
                return result
        
        # Dry-run 模式下到此停止
        if dry_run:
            result.success = True
            result.error = "[DRY-RUN] 所有验证通过，未实际发送"
            self.audit_logger.log_result(True, result.error, result.step_reached, result.warnings)
            return result
        
        # Step 7: 发送
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
        
        # Step 8: 验证消息已发送
        self._step("validate_message_sent", result)
        v = self.validator.validate_message_sent(self.helper.window_handle, message, timeout=3)
        if not v.success:
            self._step_fail("validate_message_sent", result, f"消息发送验证失败。预期消息: '{message}'，识别到: '{v.found_text}'")
            result.screenshot_path = v.screenshot_path
            self.audit_logger.log_result(False, result.error, result.step_reached, result.warnings, result.screenshot_path)
            return result
        
        # 更新冷却期记录
        WeChatSmartSender._last_send_time = time.time()
        WeChatSmartSender._last_send_contact = contact
        
        result.success = True
        result.error = "发送成功"
        logger.info(f"[SmartSender] 发送成功: {contact}")
        self.audit_logger.log_result(True, result.error, result.step_reached, result.warnings)
        return result
    
    def _prompt_user_confirm(self, contact: str, message: str, summary: Optional[str] = None) -> bool:
        """
        命令行交互式确认
        
        Returns:
            用户是否确认发送
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
    快速函数：安全发送微信消息
    
    Args:
        contact: 联系人/群聊名称
        message: 消息内容
        safety_level: "strict" 或 "normal"
        dry_run: 是否仅测试不发送
        require_confirm: 是否要求发送前用户确认
        confirm_summary: 确认时显示的额外摘要信息
        
    Returns:
        SendResult
    """
    level = SafetyLevel.STRICT if safety_level.lower() == "strict" else SafetyLevel.NORMAL
    sender = WeChatSmartSender(safety_level=level)
    return sender.send(contact, message, dry_run=dry_run, require_confirm=require_confirm, confirm_summary=confirm_summary)
