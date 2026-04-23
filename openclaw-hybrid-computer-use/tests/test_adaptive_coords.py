import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np

from src.utils.adaptive_coords import AdaptiveCoordinateMapper, AnchorPoint


class TestAnchorPoint(unittest.TestCase):
    def test_anchor_to_abs(self):
        anchor = AnchorPoint(0.5, 0.5)
        rect = (0, 0, 1000, 800)
        x, y = anchor.to_abs(rect)
        self.assertEqual(x, 500)
        self.assertEqual(y, 400)

    def test_anchor_to_abs_with_offset(self):
        anchor = AnchorPoint(0.5, 0.5, offset_x=10, offset_y=-20)
        rect = (0, 0, 1000, 800)
        x, y = anchor.to_abs(rect)
        self.assertEqual(x, 510)
        self.assertEqual(y, 380)

    def test_anchor_to_abs_with_window_offset(self):
        anchor = AnchorPoint(0.25, 0.25)
        rect = (100, 200, 500, 600)  # 400x400 window
        x, y = anchor.to_abs(rect)
        self.assertEqual(x, 200)   # 100 + 400 * 0.25
        self.assertEqual(y, 300)   # 200 + 400 * 0.25


class TestAdaptiveCoordinateMapper(unittest.TestCase):
    def test_get_point_search_box(self):
        mapper = AdaptiveCoordinateMapper()
        rect = (0, 0, 1000, 1000)
        x, y = mapper.get_point("wechat_search_box", rect)
        self.assertEqual(x, 150)
        self.assertEqual(y, 80)

    def test_get_point_input_box(self):
        mapper = AdaptiveCoordinateMapper()
        rect = (100, 100, 1100, 1100)
        x, y = mapper.get_point("wechat_input_box", rect)
        self.assertEqual(x, 750)
        self.assertEqual(y, 1020)

    def test_get_point_send_button(self):
        mapper = AdaptiveCoordinateMapper()
        rect = (0, 0, 1000, 1000)
        x, y = mapper.get_point("wechat_send_button", rect)
        self.assertEqual(x, 950)
        self.assertEqual(y, 920)

    def test_get_point_unknown_anchor(self):
        mapper = AdaptiveCoordinateMapper()
        rect = (0, 0, 1000, 1000)
        with self.assertRaises(ValueError) as context:
            mapper.get_point("unknown_anchor", rect)
        self.assertIn("Unknown anchor", str(context.exception))

    def test_find_by_template_match(self):
        mapper = AdaptiveCoordinateMapper()
        # Create a screenshot with a patterned red square at (50,50)
        screenshot = np.zeros((200, 200, 3), dtype=np.uint8)
        pattern = np.zeros((50, 50, 3), dtype=np.uint8)
        # Use a checkerboard pattern to ensure non-zero standard deviation
        for i in range(50):
            for j in range(50):
                if (i + j) % 2 == 0:
                    pattern[i, j] = [0, 0, 255]
                else:
                    pattern[i, j] = [0, 0, 128]
        screenshot[50:100, 50:100] = pattern

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            template_path = f.name
            cv2.imwrite(template_path, pattern)

        try:
            result = mapper.find_by_template(screenshot, template_path, threshold=0.8)
            self.assertIsNotNone(result)
            self.assertEqual(result[0], 75)
            self.assertEqual(result[1], 75)
        finally:
            os.remove(template_path)

    def test_find_by_template_no_match(self):
        mapper = AdaptiveCoordinateMapper()
        # Screenshot with a black/white checkerboard
        screenshot = np.zeros((200, 200, 3), dtype=np.uint8)
        for i in range(200):
            for j in range(200):
                if (i // 10 + j // 10) % 2 == 0:
                    screenshot[i, j] = [255, 255, 255]

        # Template with a red/green checkerboard (no match)
        template = np.zeros((50, 50, 3), dtype=np.uint8)
        for i in range(50):
            for j in range(50):
                if (i + j) % 2 == 0:
                    template[i, j] = [0, 255, 0]
                else:
                    template[i, j] = [0, 0, 255]

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            template_path = f.name
            cv2.imwrite(template_path, template)

        try:
            result = mapper.find_by_template(screenshot, template_path, threshold=0.8)
            self.assertIsNone(result)
        finally:
            os.remove(template_path)

    def test_find_by_template_missing_file(self):
        mapper = AdaptiveCoordinateMapper()
        screenshot = np.zeros((200, 200, 3), dtype=np.uint8)
        result = mapper.find_by_template(screenshot, "nonexistent_template.png")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
