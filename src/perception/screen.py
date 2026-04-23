"""屏幕截图功能模块

本模块提供基于 numpy 数组的高性能屏幕截图能力。
主要特性：
    - 双后端支持：优先使用 mss（C 级性能，更快），未安装时自动回退到 PIL（ImageGrab）
    - 区域截图：支持指定 (x, y, w, h) 格式的矩形区域，None 表示全屏
    - 统一输出格式：始终返回 (H, W, 3) 的 uint8 numpy 数组，通道顺序为 BGR
      （OpenCV 默认格式；mss 原生返回 BGRA，PIL 原生返回 RGB，均会在此转换）
    - 延迟导入：GUI 库（mss/PIL）在首次截图时才导入，避免纯后台环境报错

使用示例：
    >>> cap = ScreenCapture()
    >>> img = cap.capture()          # 全屏截图
    >>> img = cap.capture((0, 0, 800, 600))  # 截取左上角 800x600 区域
"""

import logging
from typing import Optional, Tuple
from pathlib import Path

import numpy as np

from ..core.config import Config


class ScreenCapture:
    """屏幕截图管理器

    封装了截图、格式转换与保存的完整流程，对外屏蔽后端差异。
    """

    def __init__(self, config: Optional[Config] = None):
        """初始化截图管理器

        Args:
            config: 全局配置对象；为 None 时自动创建默认 Config 实例
        """
        self.config = config or Config()
        self.logger = logging.getLogger(__name__)

        # 延迟导入占位：避免在 __init__ 阶段就引入 GUI 库
        # _mss = None  表示尚未尝试导入；_mss = False 表示导入失败或不可用
        self._mss = None
        self._pil = None

    def _get_mss(self):
        """获取 mss 库实例（懒加载）

        首次调用时尝试导入 mss 并创建实例；若未安装则标记为 False，后续使用 PIL 回退。

        Returns:
            mss.mss() 实例，或 False（表示不可用）
        """
        if self._mss is None:
            try:
                import mss
                self._mss = mss.mss()
            except ImportError:
                self.logger.warning("mss not installed, using PIL instead")
                self._mss = False
        return self._mss

    def capture(self, region: Optional[Tuple[int, int, int, int]] = None) -> np.ndarray:
        """截取屏幕

        优先使用 mss 后端；若 mss 不可用则回退到 PIL (ImageGrab)。

        Args:
            region: 截图区域，格式为 (x, y, w, h)，其中 x/y 为左上角坐标，
                    w/h 为宽度和高度。传入 None 则截取全屏（由配置决定）。

        Returns:
            numpy.ndarray: 形状为 (H, W, 3) 的 uint8 数组，通道顺序为 BGR
                           （兼容 OpenCV 的默认格式）。
        """
        if region is None:
            region = self.config.capture_region

        # 优先使用 mss（基于 ctypes 调用操作系统 API，速度更快，支持多显示器）
        mss_instance = self._get_mss()
        if mss_instance:
            return self._capture_with_mss(region, mss_instance)
        else:
            # 回退：使用 PIL ImageGrab（兼容性更好，但性能略差）
            return self._capture_with_pil(region)

    def _capture_with_mss(self, region: Optional[Tuple], mss_instance) -> np.ndarray:
        """使用 mss 截图（内部方法）

        mss 返回的原始数据为 BGRA 四通道，需要去掉 Alpha 通道并保留 BGR。

        Args:
            region: (x, y, w, h) 区域；None 表示全屏
            mss_instance: 已初始化的 mss.mss() 对象

        Returns:
            BGR 格式的 numpy 数组 (H, W, 3)
        """
        if region:
            # mss 的 monitor 字典使用 left/top/width/height，与 (x,y,w,h) 一一对应
            monitor = {"left": region[0], "top": region[1],
                      "width": region[2], "height": region[3]}
        else:
            monitor = mss_instance.monitors[0]  # monitors[0] 代表全屏虚拟显示器

        screenshot = mss_instance.grab(monitor)
        # mss 返回的是 BGRA（每像素 4 字节），通过切片 [:, :, :3] 去掉 alpha 通道
        # 得到的即为标准 BGR 格式，无需额外颜色空间转换
        import numpy as np
        img = np.array(screenshot)
        return img[:, :, :3]  # 去掉 alpha 通道，保留 BGR

    def _capture_with_pil(self, region: Optional[Tuple]) -> np.ndarray:
        """使用 PIL 截图（内部方法）

        PIL.ImageGrab 返回的原始数据为 RGB 三通道，需要转换为 BGR 以统一接口。

        Args:
            region: (x, y, w, h) 区域；None 表示全屏

        Returns:
            BGR 格式的 numpy 数组 (H, W, 3)
        """
        from PIL import ImageGrab

        if region:
            # PIL 使用绝对边界框 bbox = (left, top, right, bottom)
            # 因此需要将 (x, y, w, h) 转换为 (x, y, x+w, y+h)
            bbox = (region[0], region[1], region[0] + region[2], region[1] + region[3])
            img = ImageGrab.grab(bbox=bbox)
        else:
            img = ImageGrab.grab()

        # PIL 返回的是 RGB，通过 ::-1 逆序切片将通道顺序翻转为 BGR
        import numpy as np
        img_array = np.array(img)
        return img_array[:, :, ::-1]  # RGB to BGR

    def save(self, image: np.ndarray, path: Path) -> Path:
        """保存截图到文件（常用于调试）

        使用 OpenCV 的 imwrite 直接写入 BGR 数组，无需额外转换。

        Args:
            image: 截图数组，BGR 格式 (H, W, 3)
            path: 保存路径（若父目录不存在会自动创建）

        Returns:
            实际保存的 Path 对象
        """
        import cv2
        path = Path(path)
        # 自动创建父目录，避免写入时报 FileNotFoundError
        path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(path), image)
        self.logger.debug(f"截图已保存: {path}")
        return path
