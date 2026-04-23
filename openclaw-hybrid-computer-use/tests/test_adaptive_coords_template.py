"""AdaptiveCoordinateMapper 模板匹配测试"""

import unittest
import sys
import os
import numpy as np
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.adaptive_coords import AdaptiveCoordinateMapper, AnchorPoint


class TestAnchorPoint(unittest.TestCase):
    def test_to_abs(self):
        anchor = AnchorPoint(0.5, 0.5)
        x, y = anchor.to_abs((0, 0, 1000, 800))
        self.assertEqual(x, 500)
        self.assertEqual(y, 400)


class TestAdaptiveCoordinateMapperTemplate(unittest.TestCase):
    def test_get_point_safe_in_bounds(self):
        mapper = AdaptiveCoordinateMapper()
        point = mapper.get_point_safe("wechat_input_box", (0, 0, 1920, 1080))
        self.assertIsNotNone(point)

    def test_get_point_safe_out_of_bounds_triggers_template(self):
        mapper = AdaptiveCoordinateMapper()
        # 创建一个假的模板文件，让模板匹配能够执行
        template_path = AdaptiveCoordinateMapper.TEMPLATE_DIR / "wechat_input_box.png"
        template_path.parent.mkdir(parents=True, exist_ok=True)
        # 写入一个极小的假 PNG 图片 (1x1 像素)
        import cv2
        cv2.imwrite(str(template_path), np.zeros((1, 1, 3), dtype=np.uint8))
        
        try:
            # 窗口非常小 (20x20)，比例坐标计算结果会超出边界，触发模板匹配
            with patch.object(mapper, "find_by_template", return_value=(10, 10)) as mock_template:
                point = mapper.get_point_safe("wechat_input_box", (0, 0, 20, 20))
                # 由于边界检查会失败，应该触发模板匹配
                mock_template.assert_called_once()
                self.assertEqual(point, (10, 10))
        finally:
            if template_path.exists():
                template_path.unlink()

    def test_find_by_template_success(self):
        mapper = AdaptiveCoordinateMapper()
        # 创建假的截图和模板
        screenshot = np.zeros((200, 200, 3), dtype=np.uint8)
        
        with patch("src.utils.adaptive_coords.cv2.imread", return_value=np.zeros((50, 50, 3), dtype=np.uint8)):
            with patch("src.utils.adaptive_coords.cv2.matchTemplate", return_value=None) as mock_match:
                # cv2.minMaxLoc 需要特殊处理
                def fake_minmaxloc(result):
                    return (0.0, 0.9, (0, 0), (75, 75))
                
                with patch("src.utils.adaptive_coords.cv2.minMaxLoc", side_effect=fake_minmaxloc):
                    result = mapper.find_by_template(screenshot, "dummy.png")
                    self.assertEqual(result, (100, 100))  # 75 + 50//2 = 100

    def test_ensure_templates(self):
        result = AdaptiveCoordinateMapper.ensure_templates()
        self.assertIn("existing", result)
        self.assertIn("missing", result)
        # 至少应该创建目录
        self.assertTrue(AdaptiveCoordinateMapper.TEMPLATE_DIR.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
