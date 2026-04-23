"""智能定位测试"""

import numpy as np
import pytest

from claw_desktop.perception.smart_locator import SmartLocator, LocateStrategy


class TestSmartLocator:
    def test_locate_relative(self):
        locator = SmartLocator()
        result = locator.locate_relative((100, 200), offset_x=50, offset_y=-30)
        assert result.x == 150
        assert result.y == 170
        assert result.strategy == LocateStrategy.RELATIVE

    def test_locate_by_text_mock(self, monkeypatch):
        locator = SmartLocator()
        # Mock OCR recognize to avoid PaddleOCR dependency
        def mock_recognize(image):
            from claw_desktop.perception.ocr import TextBox
            return [TextBox(text="Login", bbox=(10, 10, 50, 30), confidence=0.95)]
        monkeypatch.setattr(locator.ocr, "recognize", mock_recognize)

        screenshot = np.zeros((100, 100, 3), dtype=np.uint8)
        result = locator.locate_by_text(screenshot, "Login")
        assert result is not None
        assert result.strategy == LocateStrategy.OCR
        assert result.x == 30  # center of bbox
        assert result.y == 20

    def test_locate_relation_mock(self, monkeypatch):
        locator = SmartLocator()
        from claw_desktop.perception.ocr import TextBox
        boxes = [
            TextBox(text="Username", bbox=(10, 10, 80, 30), confidence=0.95),
            TextBox(text="Input", bbox=(10, 50, 80, 70), confidence=0.90),
        ]
        monkeypatch.setattr(locator.ocr, "recognize", lambda img: boxes)

        screenshot = np.zeros((100, 100, 3), dtype=np.uint8)
        result = locator.locate_relation(screenshot, "Username", "Input", "below")
        assert result is not None
        assert result.strategy == LocateStrategy.RELATION
        assert result.y > 20  # below Username