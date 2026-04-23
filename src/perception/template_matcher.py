"""通用模板匹配器 (OpenCV)

支持多尺度模板匹配、多目标检测、最佳匹配筛选。
"""

import cv2
import numpy as np
import logging
from typing import List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class TemplateMatcher:
    """模板匹配器"""

    def __init__(self, threshold: float = 0.8, method: int = cv2.TM_CCOEFF_NORMED):
        self.threshold = threshold
        self.method = method
        self.logger = logging.getLogger(__name__)

    def find(self, screenshot: np.ndarray, template: np.ndarray) -> Optional[Tuple[int, int]]:
        """单目标匹配，返回中心点坐标"""
        if screenshot.shape[0] < template.shape[0] or screenshot.shape[1] < template.shape[1]:
            return None
        result = cv2.matchTemplate(screenshot, template, self.method)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val >= self.threshold:
            h, w = template.shape[:2]
            return (max_loc[0] + w // 2, max_loc[1] + h // 2)
        return None

    def find_all(self, screenshot: np.ndarray, template: np.ndarray,
                 max_results: int = 10) -> List[Tuple[int, int, float]]:
        """多目标匹配，返回 [(x, y, confidence), ...]"""
        results = []
        if screenshot.shape[0] < template.shape[0] or screenshot.shape[1] < template.shape[1]:
            return results
        res = cv2.matchTemplate(screenshot, template, self.method)
        loc = np.where(res >= self.threshold)
        h, w = template.shape[:2]
        for pt in zip(*loc[::-1]):
            conf = float(res[pt[1], pt[0]])
            cx, cy = pt[0] + w // 2, pt[1] + h // 2
            # 去重：距离过近视为同一个目标
            if all(abs(cx - rx) > w // 2 or abs(cy - ry) > h // 2 for rx, ry, _ in results):
                results.append((cx, cy, conf))
            if len(results) >= max_results:
                break
        results.sort(key=lambda x: x[2], reverse=True)
        return results

    def find_scaled(self, screenshot: np.ndarray, template: np.ndarray,
                    scales: List[float] = None) -> Optional[Tuple[int, int, float]]:
        """多尺度匹配，返回最佳匹配 (x, y, scale)"""
        if scales is None:
            scales = [0.8, 0.9, 1.0, 1.1, 1.2]
        best = None
        best_val = 0.0
        for scale in scales:
            resized = cv2.resize(template, None, fx=scale, fy=scale)
            result = cv2.matchTemplate(screenshot, resized, self.method)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            if max_val > best_val and max_val >= self.threshold:
                best_val = max_val
                h, w = resized.shape[:2]
                best = (max_loc[0] + w // 2, max_loc[1] + h // 2, scale)
        return best

    def load_template(self, path: str) -> Optional[np.ndarray]:
        """加载模板图像"""
        p = Path(path)
        if not p.exists():
            self.logger.warning(f"模板文件不存在: {path}")
            return None
        img = cv2.imread(str(p))
        if img is None:
            self.logger.warning(f"无法读取模板: {path}")
        return img