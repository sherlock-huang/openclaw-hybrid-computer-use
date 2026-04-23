"""屏幕截图测试"""

import pytest
import numpy as np
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from claw_desktop import ScreenCapture


class TestScreenCapture:
    """测试 ScreenCapture 类"""
    
    def test_capture_returns_array(self):
        """测试截图返回numpy数组"""
        capture = ScreenCapture()
        image = capture.capture()
        
        assert isinstance(image, np.ndarray)
        assert len(image.shape) == 3  # H, W, C
        assert image.shape[2] == 3    # BGR
    
    def test_capture_shape_reasonable(self):
        """测试截图尺寸合理"""
        capture = ScreenCapture()
        image = capture.capture()
        
        h, w = image.shape[:2]
        assert w > 100 and h > 100  # 合理的屏幕尺寸
        assert w < 10000 and h < 10000  # 不是异常值
    
    def test_save_screenshot(self, tmp_path):
        """测试保存截图"""
        capture = ScreenCapture()
        image = capture.capture()
        
        save_path = tmp_path / "test_screenshot.png"
        result = capture.save(image, save_path)
        
        assert result.exists()
        assert result.stat().st_size > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
