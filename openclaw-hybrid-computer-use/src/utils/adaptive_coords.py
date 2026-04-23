import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class AnchorPoint:
    """锚点定义：基于窗口相对比例 + 偏移"""
    rel_x: float  # 0.0 ~ 1.0
    rel_y: float
    offset_x: int = 0
    offset_y: int = 0

    def to_abs(self, rect: Tuple[int, int, int, int]) -> Tuple[int, int]:
        width = rect[2] - rect[0]
        height = rect[3] - rect[1]
        x = rect[0] + int(width * self.rel_x) + self.offset_x
        y = rect[1] + int(height * self.rel_y) + self.offset_y
        return (x, y)


class AdaptiveCoordinateMapper:
    """自适应坐标映射器"""

    TEMPLATE_DIR = Path("templates/wechat")

    # 预定义锚点
    ANCHORS = {
        # 微信搜索框：位于左侧固定宽度面板(~280px)顶部，使用固定偏移更稳定
        "wechat_search_box": AnchorPoint(0.0, 0.0, offset_x=130, offset_y=50),
        "wechat_input_box": AnchorPoint(0.65, 0.92),        # 微信输入框
        "wechat_send_button": AnchorPoint(0.95, 0.92),      # 微信发送按钮
    }

    # 模板文件名映射
    TEMPLATE_FILES = {
        "wechat_search_box": "wechat_search_box.png",
        "wechat_input_box": "wechat_input_box.png",
        "wechat_send_button": "wechat_send_button.png",
    }

    def __init__(self):
        self.logger = None  # 延迟初始化

    def _get_logger(self):
        if self.logger is None:
            import logging
            self.logger = logging.getLogger(__name__)
        return self.logger

    def get_point(self, name: str, rect: Tuple[int, int, int, int]) -> Tuple[int, int]:
        anchor = self.ANCHORS.get(name)
        if not anchor:
            raise ValueError(f"Unknown anchor: {name}")
        return anchor.to_abs(rect)

    def get_point_safe(self, name: str, rect: Tuple[int, int, int, int],
                       screenshot: Optional[np.ndarray] = None,
                       threshold: float = 0.8) -> Optional[Tuple[int, int]]:
        """
        安全获取坐标，支持模板匹配 fallback
        
        Args:
            name: 锚点名称
            rect: 窗口矩形
            screenshot: 可选，提供窗口截图用于模板匹配
            threshold: 模板匹配阈值
            
        Returns:
            坐标元组，或 None（如果坐标看起来不合理且模板匹配也失败）
        """
        logger = self._get_logger()
        anchor = self.ANCHORS.get(name)
        if not anchor:
            logger.warning(f"Unknown anchor: {name}")
            return None

        x, y = anchor.to_abs(rect)
        width = rect[2] - rect[0]
        height = rect[3] - rect[1]

        # 检查坐标是否合理（是否在窗口内，且距离边缘不要太近）
        margin = 10
        in_bounds = (rect[0] + margin <= x <= rect[2] - margin) and \
                    (rect[1] + margin <= y <= rect[3] - margin)

        if in_bounds:
            return (x, y)

        logger.warning(f"Anchor {name} coordinate ({x}, {y}) out of bounds, trying template match...")

        # 尝试模板匹配
        template_path = self.TEMPLATE_DIR / self.TEMPLATE_FILES.get(name, "")
        if template_path.exists():
            if screenshot is not None:
                matched = self.find_by_template(screenshot, str(template_path), threshold)
                if matched:
                    logger.info(f"Template match found {name} @ {matched}")
                    return matched
            else:
                # 如果没有提供 screenshot，尝试读取当前屏幕
                try:
                    import pyautogui
                    screenshot = cv2.cvtColor(np.array(pyautogui.screenshot(region=rect)), cv2.COLOR_RGB2BGR)
                    matched = self.find_by_template(screenshot, str(template_path), threshold)
                    if matched:
                        # matched 是相对于 rect 的，转换为绝对坐标
                        abs_x = rect[0] + matched[0]
                        abs_y = rect[1] + matched[1]
                        logger.info(f"Template match found {name} @ ({abs_x}, {abs_y})")
                        return (abs_x, abs_y)
                except Exception as e:
                    logger.warning(f"Failed to capture screen for template matching: {e}")
        else:
            logger.debug(f"Template file not found: {template_path}")

        # 模板匹配也失败，但返回原始坐标（可能某些窗口就是边缘）
        logger.warning(f"Template match failed for {name}, returning raw coordinate")
        return (x, y)

    def find_by_template(self, screenshot: np.ndarray, template_path: str,
                         threshold: float = 0.8) -> Optional[Tuple[int, int]]:
        """使用模板匹配找到目标位置（返回相对于 screenshot 的坐标）"""
        template = cv2.imread(template_path)
        if template is None:
            return None

        # 确保尺寸兼容
        if screenshot.shape[0] < template.shape[0] or screenshot.shape[1] < template.shape[1]:
            return None

        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= threshold:
            h, w = template.shape[:2]
            return (max_loc[0] + w // 2, max_loc[1] + h // 2)
        return None

    @classmethod
    def ensure_templates(cls) -> dict:
        """
        确保模板目录存在，返回缺失的模板文件列表
        
        Returns:
            {"existing": [...], "missing": [...]}
        """
        cls.TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
        existing = []
        missing = []
        for name, filename in cls.TEMPLATE_FILES.items():
            path = cls.TEMPLATE_DIR / filename
            if path.exists():
                existing.append(name)
            else:
                missing.append(name)
        return {"existing": existing, "missing": missing}
