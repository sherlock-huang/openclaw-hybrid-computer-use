"""WeChatSmartSender 增强功能测试（敏感词、冷却期、群聊、窗口锁、审计日志）"""

import unittest
import sys
import os
import time
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.wechat_smart_sender import WeChatSmartSender, SafetyLevel, send_wechat_message_safe


class MockValidationResult:
    def __init__(self, success, found_text="", screenshot_path=None):
        self.success = success
        self.found_text = found_text
        self.screenshot_path = screenshot_path


class TestSensitiveContentBlock(unittest.TestCase):
    """测试敏感内容拦截 + 强制 dry-run"""
    
    @patch.object(WeChatSmartSender, "_search_and_select", return_value=(True, "", None))
    def test_sensitive_blocks_without_history(self, mock_search):
        """包含敏感词且无历史记录时，强制拒绝真发"""
        sender = WeChatSmartSender(safety_level=SafetyLevel.STRICT)
        sender.helper.window_rect = (0, 0, 1000, 800)
        
        with patch.object(sender.helper, "activate_wechat", return_value=True):
            with patch.object(sender.validator, "validate_chat_contact", return_value=MockValidationResult(True)):
                with patch.object(sender.validator, "pre_send_final_check", return_value=MockValidationResult(True)):
                    with patch("src.utils.wechat_smart_sender.pyautogui.click"):
                        with patch("src.utils.wechat_smart_sender.pyautogui.typewrite"):
                            result = sender.send("张三", "借钱", dry_run=False)
                            self.assertFalse(result.success)
                            self.assertIn("敏感词", result.error)
                            self.assertIn("dry-run", result.error)
    
    @patch.object(WeChatSmartSender, "_search_and_select", return_value=(True, "", None))
    def test_sensitive_allows_with_history(self, mock_search):
        """包含敏感词但有成功历史记录时，允许发送"""
        sender = WeChatSmartSender(safety_level=SafetyLevel.STRICT)
        sender.helper.window_rect = (0, 0, 1000, 800)
        # 伪造学习记录：该联系人已有高成功率记录
        sender.learner.learn("wechat_send", "张三", [], True, 1.0)
        
        try:
            with patch("src.utils.wechat_smart_sender.WindowLockGuard") as MockGuard:
                instance = MockGuard.return_value
                instance.check_or_fail.return_value = True
                with patch.object(sender.helper, "activate_wechat", return_value=True):
                    with patch.object(sender.validator, "validate_chat_contact", return_value=MockValidationResult(True)):
                        with patch.object(sender.validator, "pre_send_final_check", return_value=MockValidationResult(True)):
                            with patch.object(sender.validator, "validate_message_sent", return_value=MockValidationResult(True)):
                                with patch("src.utils.wechat_smart_sender.pyautogui.click"):
                                    with patch("src.utils.wechat_smart_sender.pyautogui.typewrite"):
                                        with patch("src.utils.wechat_smart_sender.pyautogui.press"):
                                            # 跳过用户确认
                                            result = sender.send("张三", "借钱", dry_run=False, require_confirm=False)
                                            self.assertTrue(result.success)
        finally:
            sender.learner.reset_pattern("wechat_send", "张三")
    
    def test_sensitive_dry_run_passes(self):
        """dry-run 模式下敏感词不拦截"""
        sender = WeChatSmartSender(safety_level=SafetyLevel.STRICT)
        sender.helper.window_rect = (0, 0, 1000, 800)
        with patch("src.utils.wechat_smart_sender.WindowLockGuard") as MockGuard:
            instance = MockGuard.return_value
            instance.check_or_fail.return_value = True
            with patch.object(sender.helper, "activate_wechat", return_value=True):
                with patch.object(sender, "_search_and_select", return_value=(True, "", None)):
                    with patch.object(sender.validator, "validate_chat_contact", return_value=MockValidationResult(True)):
                        with patch.object(sender.validator, "pre_send_final_check", return_value=MockValidationResult(True)):
                            with patch("src.utils.wechat_smart_sender.pyautogui.click"):
                                with patch("src.utils.wechat_smart_sender.pyautogui.typewrite"):
                                    result = sender.send("张三", "借钱", dry_run=True)
                                    self.assertTrue(result.success)
                                    self.assertIn("DRY-RUN", result.error)


class TestCooldownProtection(unittest.TestCase):
    """测试冷却期保护"""
    
    def setUp(self):
        WeChatSmartSender._last_send_time = None
        WeChatSmartSender._last_send_contact = None
    
    def tearDown(self):
        WeChatSmartSender._last_send_time = None
        WeChatSmartSender._last_send_contact = None
    
    def test_cooldown_blocks_switch_contact(self):
        sender = WeChatSmartSender(safety_level=SafetyLevel.STRICT)
        WeChatSmartSender._last_send_time = time.time()
        WeChatSmartSender._last_send_contact = "李四"
        
        ok, msg = sender._check_cooldown("张三")
        self.assertFalse(ok)
        self.assertIn("冷却", msg)
    
    def test_cooldown_allows_same_contact(self):
        sender = WeChatSmartSender(safety_level=SafetyLevel.STRICT)
        WeChatSmartSender._last_send_time = time.time()
        WeChatSmartSender._last_send_contact = "张三"
        
        ok, msg = sender._check_cooldown("张三")
        self.assertTrue(ok)
        self.assertEqual(msg, "")
    
    def test_cooldown_allows_after_timeout(self):
        sender = WeChatSmartSender(safety_level=SafetyLevel.STRICT)
        WeChatSmartSender._last_send_time = time.time() - 10
        WeChatSmartSender._last_send_contact = "李四"
        
        ok, msg = sender._check_cooldown("张三")
        self.assertTrue(ok)


class TestGroupChatHandling(unittest.TestCase):
    """测试群聊特殊处理"""
    
    def test_is_group_chat(self):
        sender = WeChatSmartSender()
        self.assertTrue(sender._is_group_chat("技术群"))
        self.assertFalse(sender._is_group_chat("张三"))
    
    def test_group_chat_feature_validation(self):
        from src.utils.wechat_helper import WeChatOCRValidator
        validator = WeChatOCRValidator()
        with patch("src.utils.wechat_helper.win32gui.GetWindowRect", return_value=(0, 0, 1000, 800)):
            with patch.object(validator.screen, "capture", return_value=MagicMock()):
                with patch.object(validator.ocr, "recognize", return_value=[MagicMock(text="群成员(5)", confidence=0.9)]):
                    result = validator.validate_group_chat_features(12345)
                    self.assertTrue(result.success)
    
    def test_group_chat_contact_match_loose(self):
        from src.utils.wechat_helper import WeChatOCRValidator
        validator = WeChatOCRValidator()
        # 群聊模式下，"技术交流群" 应该匹配 "技术交流"
        self.assertTrue(validator._contact_match("技术交流群", "技术交流", is_group_chat=True))
        # 非群聊模式下不匹配
        self.assertFalse(validator._contact_match("技术交流群", "技术交流", is_group_chat=False))
        # 前4字匹配
        self.assertTrue(validator._contact_match("产品研发讨论群", "产品研发", is_group_chat=True))


class TestWindowLockIntegration(unittest.TestCase):
    """测试窗口锁集成"""
    
    def test_window_lock_fail_stops_send(self):
        sender = WeChatSmartSender(safety_level=SafetyLevel.STRICT)
        sender.helper.window_rect = (0, 0, 1000, 800)
        
        with patch("src.utils.wechat_smart_sender.WindowLockGuard") as MockGuard:
            instance = MockGuard.return_value
            instance.check_or_fail.return_value = False
            with patch.object(sender.helper, "activate_wechat", return_value=True):
                result = sender.send("张三", "Hello", dry_run=False, require_confirm=False)
                self.assertFalse(result.success)
                self.assertIn("窗口稳定性", result.error)


if __name__ == "__main__":
    unittest.main(verbosity=2)
