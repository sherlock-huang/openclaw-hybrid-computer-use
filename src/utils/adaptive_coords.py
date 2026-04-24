"""自适应坐标映射模块

本模块解决"不同分辨率/窗口大小下固定坐标失效"的问题，主要特性：
    - AnchorPoint（锚点）：通过 "窗口相对比例 + 像素偏移" 双重定位
        * rel_x / rel_y：目标点在窗口矩形中的相对比例（0.0 ~ 1.0）
        * offset_x / offset_y：在相对比例计算结果上叠加的像素级微调
        例如：AnchorPoint(0.0, 0.0, offset_x=130, offset_y=50) 表示从窗口左上角
        向右下偏移 (130, 50) 像素，适用于左侧固定宽度面板内的元素。
    - 模板匹配回退（fallback）：当基于锚点计算出的坐标超出窗口合理范围时，
      自动尝试加载预置的模板图片进行 OpenCV 模板匹配，进一步提升定位鲁棒性。

使用示例：
    >>> mapper = AdaptiveCoordinateMapper()
    >>> point = mapper.get_point("wechat_search_box", (100, 100, 1200, 800))
    >>> safe_point = mapper.get_point_safe("wechat_search_box", rect, screenshot)
"""

import cv2
import numpy as np
from pathlib import Path

from .exceptions import ValidationError
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class AnchorPoint:
    """锚点定义：基于窗口相对比例 + 像素偏移的混合定位方式

    计算逻辑：
        1. 根据窗口矩形 (left, top, right, bottom) 计算窗口宽高
        2. x = left + int(width  * rel_x) + offset_x
        3. y = top  + int(height * rel_y) + offset_y

    Attributes:
        rel_x: 窗口宽度方向上的相对比例（0.0 = 左边缘，1.0 = 右边缘）
        rel_y: 窗口高度方向上的相对比例（0.0 = 上边缘，1.0 = 下边缘）
        offset_x: x 轴像素偏移（正值向右）
        offset_y: y 轴像素偏移（正值向下）
    """
    rel_x: float  # 0.0 ~ 1.0
    rel_y: float
    offset_x: int = 0
    offset_y: int = 0

    def to_abs(self, rect: Tuple[int, int, int, int]) -> Tuple[int, int]:
        """将锚点转换为屏幕绝对坐标

        Args:
            rect: 窗口矩形，格式为 (left, top, right, bottom)

        Returns:
            (abs_x, abs_y) 的整数屏幕坐标
        """
        # rect[2] - rect[0] 得到窗口宽度，rect[3] - rect[1] 得到窗口高度
        width = rect[2] - rect[0]
        height = rect[3] - rect[1]
        # 先按比例定位到窗口内的相对位置，再加上像素级偏移进行微调
        x = rect[0] + int(width * self.rel_x) + self.offset_x
        y = rect[1] + int(height * self.rel_y) + self.offset_y
        return (x, y)


class AdaptiveCoordinateMapper:
    """自适应坐标映射器

    针对同一程序在不同分辨率或窗口大小下的 UI 元素定位需求，
    提供基于锚点比例 + 模板匹配双保险的坐标获取能力。
    """

    # 模板图片的默认存放目录（相对于工作目录）
    TEMPLATE_DIR = Path("templates/wechat")

    # 预定义锚点表：将语义化名称映射到 AnchorPoint 实例
    # 注释中说明了每个锚点的实际指向及设计原因
    ANCHORS = {
        # 微信搜索框：位于左侧固定宽度面板（约 280px）顶部
        # 使用 (0.0, 0.0) 作为基准，再通过 offset 向右下微调，
        # 这样即使窗口高度变化，水平位置仍能保持稳定
        "wechat_search_box": AnchorPoint(0.0, 0.0, offset_x=130, offset_y=50),
        "wechat_input_box": AnchorPoint(0.65, 0.92),        # 微信输入框（右下区域）
        "wechat_send_button": AnchorPoint(0.95, 0.92),      # 微信发送按钮（输入框右侧）
    }

    # 模板文件名映射：与 ANCHORS 的 key 一一对应，用于模板匹配回退
    TEMPLATE_FILES = {
        "wechat_search_box": "wechat_search_box.png",
        "wechat_input_box": "wechat_input_box.png",
        "wechat_send_button": "wechat_send_button.png",
    }

    def __init__(self):
        """初始化映射器

        logger 采用延迟初始化策略，避免在导入阶段就创建日志记录器。
        """
        self.logger = None  # 延迟初始化

    def _get_logger(self):
        """获取日志记录器（懒加载）"""
        if self.logger is None:
            import logging
            self.logger = logging.getLogger(__name__)
        return self.logger

    def get_point(self, name: str, rect: Tuple[int, int, int, int]) -> Tuple[int, int]:
        """根据锚点名称获取对应的屏幕绝对坐标

        直接使用预定义 AnchorPoint 进行相对比例 + 偏移计算，不做边界校验。

        Args:
            name: 锚点名称（如 "wechat_search_box"）
            rect: 窗口矩形 (left, top, right, bottom)

        Returns:
            屏幕绝对坐标 (x, y)

        Raises:
            ValueError: 若 name 不在 ANCHORS 中
        """
        anchor = self.ANCHORS.get(name)
        if not anchor:
            raise ValidationError(f"Unknown anchor: {name}")
        return anchor.to_abs(rect)

    def get_point_safe(self, name: str, rect: Tuple[int, int, int, int],
                       screenshot: Optional[np.ndarray] = None,
                       threshold: float = 0.8) -> Optional[Tuple[int, int]]:
        """安全获取坐标，支持模板匹配 fallback

        执行流程：
            1. 通过锚点计算出候选坐标
            2. 检查坐标是否在窗口合理范围内（距离各边缘至少 margin 像素）
            3. 若在范围内，直接返回；若越界，尝试模板匹配定位
            4. 若模板匹配也失败，则回退到原始坐标并记录警告

        Args:
            name: 锚点名称
            rect: 窗口矩形 (left, top, right, bottom)
            screenshot: 可选，提供窗口截图用于模板匹配（BGR 格式）
            threshold: 模板匹配相似度阈值（0.0 ~ 1.0），越高越严格

        Returns:
            坐标元组 (x, y)，或在极端情况下返回 None
        """
        logger = self._get_logger()
        anchor = self.ANCHORS.get(name)
        if not anchor:
            logger.warning(f"Unknown anchor: {name}")
            return None

        x, y = anchor.to_abs(rect)
        width = rect[2] - rect[0]
        height = rect[3] - rect[1]

        # 检查坐标是否合理：是否严格位于窗口内部，且距离边缘不要太近（避免点到边框外）
        margin = 10
        in_bounds = (rect[0] + margin <= x <= rect[2] - margin) and \
                    (rect[1] + margin <= y <= rect[3] - margin)

        if in_bounds:
            return (x, y)

        logger.warning(f"Anchor {name} coordinate ({x}, {y}) out of bounds, trying template match...")

        # 尝试模板匹配回退：加载对应模板图片，在截图中搜索最匹配位置
        template_path = self.TEMPLATE_DIR / self.TEMPLATE_FILES.get(name, "")
        if template_path.exists():
            if screenshot is not None:
                # 提供截图时直接在当前截图上做模板匹配
                matched = self.find_by_template(screenshot, str(template_path), threshold)
                if matched:
                    logger.info(f"Template match found {name} @ {matched}")
                    return matched
            else:
                # 未提供截图时，临时使用 pyautogui 截取当前屏幕区域再做匹配
                try:
                    import pyautogui
                    # pyautogui 返回 RGB，需转为 BGR 以与模板保持一致
                    screenshot = cv2.cvtColor(np.array(pyautogui.screenshot(region=rect)), cv2.COLOR_RGB2BGR)
                    matched = self.find_by_template(screenshot, str(template_path), threshold)
                    if matched:
                        # matched 是相对于 rect 的坐标，需要加上 rect 左上角得到绝对坐标
                        abs_x = rect[0] + matched[0]
                        abs_y = rect[1] + matched[1]
                        logger.info(f"Template match found {name} @ ({abs_x}, {abs_y})")
                        return (abs_x, abs_y)
                except Exception as e:
                    logger.warning(f"Failed to capture screen for template matching: {e}")
        else:
            logger.debug(f"Template file not found: {template_path}")

        # 模板匹配也失败，但返回原始坐标（某些元素在极窄窗口下确实会出现在边缘）
        logger.warning(f"Template match failed for {name}, returning raw coordinate")
        return (x, y)

    def find_by_template(self, screenshot: np.ndarray, template_path: str,
                         threshold: float = 0.8) -> Optional[Tuple[int, int]]:
        """使用 OpenCV 模板匹配找到目标位置

        采用 cv2.TM_CCOEFF_NORMED（归一化相关系数）作为匹配指标，
        对亮度变化具有一定鲁棒性。

        Args:
            screenshot: 待搜索的源图像（BGR 格式）
            template_path: 模板图片的磁盘路径
            threshold: 匹配度阈值，仅当最大值 >= threshold 时才视为匹配成功

        Returns:
            匹配位置的中心点坐标 (center_x, center_y)，坐标系与 screenshot 一致；
            若未找到或模板加载失败则返回 None。
        """
        template = cv2.imread(template_path)
        if template is None:
            return None

        # 安全校验：模板尺寸不能大于截图，否则 matchTemplate 会报错
        if screenshot.shape[0] < template.shape[0] or screenshot.shape[1] < template.shape[1]:
            return None

        # TM_CCOEFF_NORMED 返回值范围约 -1 ~ 1，1 表示完全匹配
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= threshold:
            h, w = template.shape[:2]
            # 返回模板中心点，而非左上角，便于直接用于点击操作
            return (max_loc[0] + w // 2, max_loc[1] + h // 2)
        return None

    @classmethod
    def ensure_templates(cls) -> dict:
        """确保模板目录存在，返回现有/缺失的模板文件清单

        用于启动时自检，提醒用户补充缺失的模板图片。

        Returns:
            {"existing": [已存在的锚点名称列表], "missing": [缺失的锚点名称列表]}
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
