"""智能元素定位器

整合多种定位策略：
1. 图像模板匹配 (TemplateMatcher)
2. 文字 OCR 定位 (TextRecognizer)
3. 相对坐标定位 (基于锚点偏移)
4. 元素关系链定位 (如 "在 XXX 下方的 YYY")
"""

import logging
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass
from enum import Enum

import numpy as np

from .template_matcher import TemplateMatcher
from .ocr import TextRecognizer
from ..core.config import Config


class LocateStrategy(Enum):
    """定位策略"""
    TEMPLATE = "template"      # 图像模板匹配
    OCR = "ocr"                # 文字识别
    RELATIVE = "relative"      # 相对坐标
    RELATION = "relation"      # 关系链


@dataclass
class LocatedElement:
    """定位结果"""
    x: int
    y: int
    strategy: LocateStrategy
    confidence: float
    metadata: Dict = None  # 额外信息

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class SmartLocator:
    """智能元素定位器"""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.logger = logging.getLogger(__name__)
        self.matcher = TemplateMatcher()
        self.ocr = TextRecognizer(config)

    # ==================== 图像匹配定位 ====================

    def locate_by_image(self, screenshot: np.ndarray, template_path: str,
                        threshold: float = 0.8) -> Optional[LocatedElement]:
        """通过模板图像定位元素"""
        template = self.matcher.load_template(template_path)
        if template is None:
            return None
        result = self.matcher.find(screenshot, template)
        if result:
            self.logger.info(f"图像匹配定位成功: {template_path} @ {result}")
            return LocatedElement(
                x=result[0], y=result[1],
                strategy=LocateStrategy.TEMPLATE,
                confidence=1.0,  # matcher 内部已过滤
                metadata={"template": template_path}
            )
        self.logger.warning(f"图像匹配失败: {template_path}")
        return None

    def locate_all_by_image(self, screenshot: np.ndarray, template_path: str,
                            threshold: float = 0.8) -> List[LocatedElement]:
        """定位所有匹配图像的元素"""
        template = self.matcher.load_template(template_path)
        if template is None:
            return []
        results = self.matcher.find_all(screenshot, template)
        return [
            LocatedElement(x=r[0], y=r[1], strategy=LocateStrategy.TEMPLATE,
                           confidence=r[2], metadata={"template": template_path})
            for r in results
        ]

    # ==================== 文字 OCR 定位 ====================

    def locate_by_text(self, screenshot: np.ndarray, text: str,
                       fuzzy: bool = True) -> Optional[LocatedElement]:
        """通过 OCR 文字定位元素

        Args:
            screenshot: 屏幕截图
            text: 目标文字
            fuzzy: 是否模糊匹配（包含即可）
        """
        boxes = self.ocr.recognize(screenshot)
        for box in boxes:
            matched = text in box.text if fuzzy else box.text == text
            if matched:
                cx, cy = box.center
                self.logger.info(f"OCR 定位成功: '{text}' @ ({cx}, {cy})")
                return LocatedElement(
                    x=cx, y=cy,
                    strategy=LocateStrategy.OCR,
                    confidence=box.confidence,
                    metadata={"text": box.text}
                )
        self.logger.warning(f"OCR 定位失败: '{text}'")
        return None

    def locate_all_by_text(self, screenshot: np.ndarray, text: str,
                           fuzzy: bool = True) -> List[LocatedElement]:
        """定位所有匹配文字的元素"""
        boxes = self.ocr.recognize(screenshot)
        results = []
        for box in boxes:
            matched = text in box.text if fuzzy else box.text == text
            if matched:
                cx, cy = box.center
                results.append(LocatedElement(
                    x=cx, y=cy,
                    strategy=LocateStrategy.OCR,
                    confidence=box.confidence,
                    metadata={"text": box.text}
                ))
        return results

    # ==================== 相对坐标定位 ====================

    def locate_relative(self, anchor: Tuple[int, int],
                        offset_x: int = 0, offset_y: int = 0) -> LocatedElement:
        """相对锚点定位

        Args:
            anchor: 锚点坐标 (x, y)
            offset_x: X 轴偏移（正数向右）
            offset_y: Y 轴偏移（正数向下）
        """
        x = anchor[0] + offset_x
        y = anchor[1] + offset_y
        return LocatedElement(
            x=x, y=y,
            strategy=LocateStrategy.RELATIVE,
            confidence=1.0,
            metadata={"anchor": anchor, "offset": (offset_x, offset_y)}
        )

    # ==================== 元素关系链定位 ====================

    def locate_relation(self, screenshot: np.ndarray,
                        reference_text: str, target_text: str,
                        direction: str = "below") -> Optional[LocatedElement]:
        """关系链定位：基于参考元素找到目标元素

        Args:
            screenshot: 屏幕截图
            reference_text: 参考文字（如 "用户名"）
            target_text: 目标文字（如输入框旁的占位符）
            direction: 相对方向 - below, above, left, right, nearest

        Returns:
            目标元素坐标
        """
        ref = self.locate_by_text(screenshot, reference_text)
        if ref is None:
            self.logger.warning(f"关系链定位：找不到参考元素 '{reference_text}'")
            return None

        targets = self.locate_all_by_text(screenshot, target_text)
        if not targets:
            self.logger.warning(f"关系链定位：找不到目标元素 '{target_text}'")
            return None

        if direction == "nearest":
            best = min(targets, key=lambda t: abs(t.x - ref.x) + abs(t.y - ref.y))
        elif direction == "below":
            candidates = [t for t in targets if t.y > ref.y]
            best = min(candidates, key=lambda t: abs(t.x - ref.x) + (t.y - ref.y)) if candidates else None
        elif direction == "above":
            candidates = [t for t in targets if t.y < ref.y]
            best = min(candidates, key=lambda t: abs(t.x - ref.x) + (ref.y - t.y)) if candidates else None
        elif direction == "right":
            candidates = [t for t in targets if t.x > ref.x]
            best = min(candidates, key=lambda t: (t.x - ref.x) + abs(t.y - ref.y)) if candidates else None
        elif direction == "left":
            candidates = [t for t in targets if t.x < ref.x]
            best = min(candidates, key=lambda t: (ref.x - t.x) + abs(t.y - ref.y)) if candidates else None
        else:
            best = targets[0]

        if best:
            self.logger.info(f"关系链定位成功: '{reference_text}' -> {direction} -> '{target_text}' @ ({best.x}, {best.y})")
            best.strategy = LocateStrategy.RELATION
            best.metadata.update({"reference": reference_text, "direction": direction})
        return best

    # ==================== 复合定位策略 ====================

    def locate(self, screenshot: np.ndarray, target: str,
               strategy: str = "auto",
               template_path: Optional[str] = None) -> Optional[LocatedElement]:
        """统一入口：智能选择定位策略

        Args:
            screenshot: 屏幕截图
            target: 目标描述（文字或标识）
            strategy: 策略 - auto, template, ocr, relative
            template_path: 模板图像路径（strategy=template 时必填）
        """
        if strategy == "template" and template_path:
            return self.locate_by_image(screenshot, template_path)
        elif strategy == "ocr":
            return self.locate_by_text(screenshot, target)
        elif strategy == "auto":
            # 先尝试 OCR（通常更快）
            result = self.locate_by_text(screenshot, target)
            if result:
                return result
            # 再尝试模板匹配
            if template_path:
                result = self.locate_by_image(screenshot, template_path)
                if result:
                    return result
            self.logger.error(f"所有定位策略均失败: {target}")
            return None
        else:
            self.logger.warning(f"未知定位策略: {strategy}")
            return None