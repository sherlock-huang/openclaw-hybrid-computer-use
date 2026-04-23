"""WeChatContactSelector 测试"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.wechat_contact_selector import WeChatContactSelector, ContactMatchResult


class MockTextBox:
    def __init__(self, text, bbox, confidence=0.95):
        self.text = text
        self.bbox = bbox
        self.confidence = confidence
    
    @property
    def center(self):
        return ((self.bbox[0] + self.bbox[2]) // 2, (self.bbox[1] + self.bbox[3]) // 2)


class TestContactMatchResult(unittest.TestCase):
    def test_creation(self):
        r = ContactMatchResult(True, 100, 200, "张三", ["张三", "李四"])
        self.assertTrue(r.matched)
        self.assertEqual(r.x, 100)
        self.assertEqual(r.y, 200)


class TestWeChatContactSelector(unittest.TestCase):
    def test_find_contact_exact_match(self):
        selector = WeChatContactSelector()
        mock_box = MockTextBox("文件传输助手", [10, 20, 150, 40])
        
        with patch("src.utils.wechat_contact_selector.win32gui.GetWindowRect", return_value=(0, 0, 1000, 800)):
            with patch.object(selector.screen, "capture", return_value=MagicMock()):
                with patch.object(selector.ocr, "recognize", return_value=[mock_box]):
                    result = selector.find_contact_in_list(12345, "文件传输助手")
                    self.assertTrue(result.matched)
                    self.assertEqual(result.matched_text, "文件传输助手")
                    # x = 窗口x(0) + 列表x(0) + bbox中心x(80) = 80
                    self.assertEqual(result.x, 80)
                    # y = 窗口y(0) + 列表y(100) + bbox中心y(30) = 130
                    self.assertEqual(result.y, 130)

    def test_find_contact_fuzzy_match(self):
        selector = WeChatContactSelector()
        mock_box = MockTextBox("文件传输助手 (3)", [10, 20, 180, 40])
        
        with patch("src.utils.wechat_contact_selector.win32gui.GetWindowRect", return_value=(0, 0, 1000, 800)):
            with patch.object(selector.screen, "capture", return_value=MagicMock()):
                with patch.object(selector.ocr, "recognize", return_value=[mock_box]):
                    result = selector.find_contact_in_list(12345, "文件传输助手")
                    self.assertTrue(result.matched)
                    self.assertIn("文件传输助手", result.matched_text)

    def test_find_contact_no_match(self):
        selector = WeChatContactSelector()
        mock_box = MockTextBox("李四", [10, 20, 100, 40])
        
        with patch("src.utils.wechat_contact_selector.win32gui.GetWindowRect", return_value=(0, 0, 1000, 800)):
            with patch.object(selector.screen, "capture", return_value=MagicMock()):
                with patch.object(selector.ocr, "recognize", return_value=[mock_box]):
                    result = selector.find_contact_in_list(12345, "张三")
                    self.assertFalse(result.matched)
                    self.assertIn("李四", result.all_texts)

    def test_click_contact(self):
        selector = WeChatContactSelector()
        mock_box = MockTextBox("张三", [10, 20, 80, 40])
        
        with patch("src.utils.wechat_contact_selector.win32gui.GetWindowRect", return_value=(0, 0, 1000, 800)):
            with patch.object(selector.screen, "capture", return_value=MagicMock()):
                with patch.object(selector.ocr, "recognize", return_value=[mock_box]):
                    with patch("src.utils.wechat_contact_selector.pyautogui.click") as mock_click:
                        success = selector.click_contact(12345, "张三")
                        self.assertTrue(success)
                        mock_click.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
