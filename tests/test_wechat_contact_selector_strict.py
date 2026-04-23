"""WeChatContactSelector 严格模式 & 相似联系人检测测试"""

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


class TestFindSimilarNames(unittest.TestCase):
    def test_exact_match_no_conflict(self):
        selector = WeChatContactSelector()
        result = selector.find_similar_names("张三", ["张三", "李四", "王五"])
        self.assertEqual(result, [])
    
    def test_similar_name_conflict(self):
        selector = WeChatContactSelector()
        result = selector.find_similar_names("张三", ["张三", "张三-工作群", "李四"])
        self.assertIn("张三-工作群", result)
    
    def test_substring_conflict(self):
        selector = WeChatContactSelector()
        result = selector.find_similar_names("张三", ["张三", "张三三", "李四"])
        # "张三三" 包含 "张三"，视为冲突
        self.assertIn("张三三", result)
    
    def test_no_conflict_unrelated(self):
        selector = WeChatContactSelector()
        result = selector.find_similar_names("张三", ["张三", "李四", "王五"])
        self.assertEqual(result, [])


class TestFindContactInListStrict(unittest.TestCase):
    @patch("src.utils.wechat_contact_selector.win32gui.GetWindowRect", return_value=(0, 0, 1000, 800))
    def test_strict_exact_match_success(self, mock_rect):
        selector = WeChatContactSelector()
        mock_box = MockTextBox("文件传输助手", [10, 20, 150, 40])
        
        with patch.object(selector.screen, "capture", return_value=MagicMock()):
            with patch.object(selector.ocr, "recognize", return_value=[mock_box]):
                success, match_result, conflicts = selector.find_contact_in_list_strict(12345, "文件传输助手")
                self.assertTrue(success)
                self.assertIsNotNone(match_result)
                self.assertTrue(match_result.matched)
                self.assertEqual(conflicts, [])
    
    @patch("src.utils.wechat_contact_selector.win32gui.GetWindowRect", return_value=(0, 0, 1000, 800))
    def test_strict_conflict_detected(self, mock_rect):
        selector = WeChatContactSelector()
        boxes = [
            MockTextBox("张三", [10, 20, 80, 40]),
            MockTextBox("张三-工作群", [10, 70, 180, 40]),
        ]
        
        with patch.object(selector.screen, "capture", return_value=MagicMock()):
            with patch.object(selector.ocr, "recognize", return_value=boxes):
                success, match_result, conflicts = selector.find_contact_in_list_strict(12345, "张三")
                self.assertFalse(success)
                self.assertIsNone(match_result)
                self.assertIn("张三-工作群", conflicts)
    
    @patch("src.utils.wechat_contact_selector.win32gui.GetWindowRect", return_value=(0, 0, 1000, 800))
    def test_strict_no_exact_match(self, mock_rect):
        selector = WeChatContactSelector()
        mock_box = MockTextBox("李四", [10, 20, 80, 40])
        
        with patch.object(selector.screen, "capture", return_value=MagicMock()):
            with patch.object(selector.ocr, "recognize", return_value=[mock_box]):
                success, match_result, conflicts = selector.find_contact_in_list_strict(12345, "张三")
                self.assertFalse(success)
                self.assertIsNotNone(match_result)
                self.assertFalse(match_result.matched)
                self.assertEqual(conflicts, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
