"""屏幕截图功能"""

import logging
from typing import Optional, Tuple
from pathlib import Path

import numpy as np

from ..core.config import Config


class ScreenCapture:
    """屏幕截图管理器"""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.logger = logging.getLogger(__name__)
        
        # 延迟导入，避免在没有GUI的环境中报错
        self._mss = None
        self._pil = None
    
    def _get_mss(self):
        """获取 mss 库实例"""
        if self._mss is None:
            try:
                import mss
                self._mss = mss.mss()
            except ImportError:
                self.logger.warning("mss not installed, using PIL instead")
                self._mss = False
        return self._mss
    
    def capture(self, region: Optional[Tuple[int, int, int, int]] = None) -> np.ndarray:
        """
        截取屏幕
        
        Args:
            region: (x, y, w, h) 可选，None则全屏
            
        Returns:
            numpy array (H, W, 3) - BGR格式
        """
        if region is None:
            region = self.config.capture_region
        
        # 优先使用 mss (更快)
        mss_instance = self._get_mss()
        if mss_instance:
            return self._capture_with_mss(region, mss_instance)
        else:
            return self._capture_with_pil(region)
    
    def _capture_with_mss(self, region: Optional[Tuple], mss_instance) -> np.ndarray:
        """使用 mss 截图"""
        if region:
            monitor = {"left": region[0], "top": region[1], 
                      "width": region[2], "height": region[3]}
        else:
            monitor = mss_instance.monitors[0]  # 全屏
        
        screenshot = mss_instance.grab(monitor)
        # mss 返回的是 BGRA，转换为 BGR
        import numpy as np
        img = np.array(screenshot)
        return img[:, :, :3]  # 去掉 alpha 通道
    
    def _capture_with_pil(self, region: Optional[Tuple]) -> np.ndarray:
        """使用 PIL 截图"""
        from PIL import ImageGrab
        
        if region:
            bbox = (region[0], region[1], region[0] + region[2], region[1] + region[3])
            img = ImageGrab.grab(bbox=bbox)
        else:
            img = ImageGrab.grab()
        
        # PIL 返回的是 RGB，转换为 BGR
        import numpy as np
        img_array = np.array(img)
        return img_array[:, :, ::-1]  # RGB to BGR
    
    def save(self, image: np.ndarray, path: Path) -> Path:
        """
        保存截图用于调试
        
        Args:
            image: 截图数组
            path: 保存路径
            
        Returns:
            保存的路径
        """
        import cv2
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(path), image)
        self.logger.debug(f"截图已保存: {path}")
        return path
