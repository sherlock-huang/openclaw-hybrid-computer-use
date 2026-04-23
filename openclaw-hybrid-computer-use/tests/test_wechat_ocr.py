"""
WeChat OCR Validator tests
"""

import unittest
import sys
import os
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.wechat_helper import WeChatOCRValidator, ValidationResult


class MockTextBox:
    def __init__(self, text, confidence, bbox=None):
        self.text = text
        self.confidence = confidence
        self.bbox = bbox or (0, 0, 100, 20)
    
    @property
    def center(self):
        return ((self.bbox[0] + self.bbox[2]) // 2, (self.bbox[1] + self.bbox[3]) // 2)


class TestValidationResult(unittest.TestCase):
    def test_dataclass_creation(self):
        result = ValidationResult(success=True, found_text="hello", confidence=0.9)
        self.assertTrue(result.success)
        self.assertEqual(result.found_text, "hello")
        self.assertAlmostEqual(result.confidence, 0.9)
        self.assertIsNone(result.screenshot_path)


class TestWeChatOCRValidator(unittest.TestCase):
    def test_validator_initialization(self):
        validator = WeChatOCRValidator()
        self.assertIsNotNone(validator.screen)
        self.assertIsNotNone(validator.ocr)

    @patch("src.utils.wechat_helper.win32gui.GetWindowRect", return_value=(0, 0, 1000, 800))
    def test_validate_chat_contact_success(self, mock_rect):
        validator = WeChatOCRValidator()
        mock_box = MockTextBox("Test Contact", 0.95)
        with patch.object(validator.screen, "capture", return_value=MagicMock()) as mock_cap:
            with patch.object(validator.ocr, "recognize", return_value=[mock_box]) as mock_ocr:
                result = validator.validate_chat_contact(12345, "Test")
                self.assertTrue(result.success)
                self.assertEqual(result.found_text, "Test Contact")
                self.assertAlmostEqual(result.confidence, 0.95)
                mock_cap.assert_called_once_with(region=(280, 0, 720, 80))

    @patch("src.utils.wechat_helper.win32gui.GetWindowRect", return_value=(0, 0, 1000, 800))
    def test_validate_chat_contact_failure(self, mock_rect):
        validator = WeChatOCRValidator()
        with patch.object(validator.screen, "capture", return_value=np.zeros((10, 10, 3), dtype=np.uint8)) as mock_cap:
            with patch.object(validator.ocr, "recognize", return_value=[]) as mock_ocr:
                with patch.object(validator, "_save_debug_screenshot", return_value="logs/test.png"):
                    result = validator.validate_chat_contact(12345, "Test")
                    self.assertFalse(result.success)
                    self.assertEqual(result.confidence, 0.0)

    @patch("src.utils.wechat_helper.win32gui.GetWindowRect", return_value=(0, 0, 1000, 800))
    @patch("time.sleep")
    def test_validate_message_sent_success(self, mock_sleep, mock_rect):
        validator = WeChatOCRValidator()
        mock_box = MockTextBox("Hello world", 0.88)
        with patch.object(validator.screen, "capture", return_value=MagicMock()) as mock_cap:
            with patch.object(validator.ocr, "recognize", return_value=[mock_box]) as mock_ocr:
                result = validator.validate_message_sent(12345, "Hello", timeout=1)
                self.assertTrue(result.success)
                self.assertEqual(result.found_text, "Hello world")
                self.assertAlmostEqual(result.confidence, 0.88)
                mock_cap.assert_called_with(region=(280, 100, 720, 600))

    @patch("src.utils.wechat_helper.win32gui.GetWindowRect", return_value=(0, 0, 1000, 800))
    @patch("time.sleep")
    def test_validate_message_sent_failure(self, mock_sleep, mock_rect):
        validator = WeChatOCRValidator()
        with patch.object(validator.screen, "capture", return_value=np.zeros((10, 10, 3), dtype=np.uint8)) as mock_cap:
            with patch.object(validator.ocr, "recognize", return_value=[]) as mock_ocr:
                with patch.object(validator, "_save_debug_screenshot", return_value="logs/test.png"):
                    result = validator.validate_message_sent(12345, "Hello", timeout=0)
                    self.assertFalse(result.success)
                    self.assertEqual(result.confidence, 0.0)

    @patch("src.utils.wechat_helper.win32gui.GetWindowRect", return_value=(0, 0, 1000, 800))
    def test_validate_chat_contact_saves_screenshot_on_fail(self, mock_rect):
        validator = WeChatOCRValidator()
        fake_image = np.zeros((10, 10, 3), dtype=np.uint8)
        with patch.object(validator.screen, "capture", return_value=fake_image):
            with patch.object(validator.ocr, "recognize", return_value=[]):
                with patch.object(validator.screen, "save", return_value=Path("logs/test.png")) as mock_save:
                    result = validator.validate_chat_contact(12345, "Test", save_screenshot_on_fail=True)
                    self.assertFalse(result.success)
                    mock_save.assert_called_once()
                    self.assertIn("logs", str(result.screenshot_path))


if __name__ == "__main__":
    unittest.main(verbosity=2)
