"""WeChatSmartSender 测试"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.wechat_smart_sender import WeChatSmartSender, SafetyLevel, send_wechat_message_safe


class MockValidationResult:
    def __init__(self, success, found_text="", screenshot_path=None):
        self.success = success
        self.found_text = found_text
        self.screenshot_path = screenshot_path


class TestWeChatSmartSender(unittest.TestCase):
    def setUp(self):
        self.sender = WeChatSmartSender(safety_level=SafetyLevel.STRICT)
    
    def test_init_strict(self):
        sender = WeChatSmartSender(safety_level=SafetyLevel.STRICT)
        self.assertEqual(sender.safety_level, SafetyLevel.STRICT)
    
    def test_init_normal(self):
        sender = WeChatSmartSender(safety_level=SafetyLevel.NORMAL)
        self.assertEqual(sender.safety_level, SafetyLevel.NORMAL)
    
    @patch.object(WeChatSmartSender, "_search_and_select", return_value=(True, "", None))
    def test_send_dry_run_success(self, mock_search):
        """测试 dry-run 成功"""
        self.sender.helper.window_rect = (0, 0, 1000, 800)
        with patch("src.utils.wechat_smart_sender.WindowLockGuard") as MockGuard:
            instance = MockGuard.return_value
            instance.check_or_fail.return_value = True
            with patch.object(self.sender.helper, "activate_wechat", return_value=True):
                with patch.object(self.sender.validator, "validate_chat_contact", return_value=MockValidationResult(True)):
                    with patch.object(self.sender.validator, "pre_send_final_check", return_value=MockValidationResult(True)):
                        with patch("src.utils.wechat_smart_sender.pyautogui.click"):
                            with patch("src.utils.wechat_smart_sender.pyautogui.typewrite"):
                                result = self.sender.send("文件传输助手", "测试", dry_run=True)
                                self.assertTrue(result.success)
                                self.assertIn("DRY-RUN", result.error)
                                self.assertEqual(result.step_reached, "pre_send_final_check")
    
    def test_send_contact_validation_fail(self):
        """测试聊天对象验证失败时不发送"""
        self.sender.helper.window_rect = (0, 0, 1000, 800)
        with patch("src.utils.wechat_smart_sender.WindowLockGuard") as MockGuard:
            instance = MockGuard.return_value
            instance.check_or_fail.return_value = True
            with patch.object(self.sender.helper, "activate_wechat", return_value=True):
                with patch.object(self.sender, "_search_and_select", return_value=(True, "", None)):
                    with patch.object(self.sender.validator, "validate_chat_contact", return_value=MockValidationResult(False, "李四", "logs/fail.png")):
                        with patch("src.utils.wechat_smart_sender.pyautogui.click"):
                            result = self.sender.send("张三", "Hello", dry_run=False)
                            self.assertFalse(result.success)
                            self.assertIn("李四", result.error)
                            self.assertEqual(result.screenshot_path, "logs/fail.png")
                            self.assertEqual(result.step_reached, "validate_chat_contact")
    
    def test_send_pre_send_check_fail(self):
        """测试发送前最终确认失败时不发送"""
        self.sender.helper.window_rect = (0, 0, 1000, 800)
        with patch("src.utils.wechat_smart_sender.WindowLockGuard") as MockGuard:
            instance = MockGuard.return_value
            instance.check_or_fail.return_value = True
            with patch.object(self.sender.helper, "activate_wechat", return_value=True):
                with patch.object(self.sender, "_search_and_select", return_value=(True, "", None)):
                    with patch.object(self.sender.validator, "validate_chat_contact", return_value=MockValidationResult(True)):
                        with patch.object(self.sender.validator, "pre_send_final_check", return_value=MockValidationResult(False, "王五", "logs/presend_fail.png")):
                            with patch("src.utils.wechat_smart_sender.pyautogui.click"):
                                with patch("src.utils.wechat_smart_sender.pyautogui.typewrite"):
                                    result = self.sender.send("张三", "Hello", dry_run=False)
                                    self.assertFalse(result.success)
                                    self.assertIn("王五", result.error)
                                    self.assertEqual(result.screenshot_path, "logs/presend_fail.png")
                                    self.assertEqual(result.step_reached, "pre_send_final_check")
    
    def test_send_wechat_message_safe_helper(self):
        """测试快速函数"""
        with patch("src.utils.wechat_smart_sender.WeChatSmartSender") as MockSender:
            instance = MockSender.return_value
            instance.send.return_value = MagicMock(success=True, error="ok", step_reached="done", warnings=[])
            result = send_wechat_message_safe("张三", "Hello", safety_level="strict", dry_run=False)
            MockSender.assert_called_once_with(safety_level=SafetyLevel.STRICT)
            instance.send.assert_called_once_with("张三", "Hello", dry_run=False, require_confirm=True, confirm_summary=None)


class TestWeChatSmartSenderNormalMode(unittest.TestCase):
    def test_normal_mode_allows_fuzzy(self):
        """普通模式允许模糊匹配"""
        sender = WeChatSmartSender(safety_level=SafetyLevel.NORMAL)
        sender.helper.window_rect = (0, 0, 1000, 800)
        with patch("src.utils.wechat_smart_sender.WindowLockGuard") as MockGuard:
            instance = MockGuard.return_value
            instance.check_or_fail.return_value = True
            with patch.object(sender.helper, "activate_wechat", return_value=True):
                with patch.object(sender.selector, "find_contact_in_list", return_value=MagicMock(matched=False, all_texts=[])):
                    with patch("src.utils.wechat_smart_sender.pyautogui.press"):
                        with patch.object(sender.validator, "validate_chat_contact", return_value=MockValidationResult(True)):
                            with patch.object(sender.validator, "pre_send_final_check", return_value=MockValidationResult(True)):
                                with patch.object(sender.validator, "validate_message_sent", return_value=MockValidationResult(True)):
                                    with patch("src.utils.wechat_smart_sender.pyautogui.click"):
                                        with patch("src.utils.wechat_smart_sender.pyautogui.typewrite"):
                                            result = sender.send("张三", "Hello", require_confirm=False)
                                            self.assertTrue(result.success)


if __name__ == "__main__":
    unittest.main(verbosity=2)
