"""图像处理工具"""

from typing import List
from pathlib import Path

import cv2
import numpy as np

from ..core.models import UIElement


def draw_elements(image: np.ndarray, elements: List[UIElement], 
                  draw_text: bool = True) -> np.ndarray:
    """
    在图像上绘制检测到的元素
    
    Args:
        image: 原始图像 (BGR格式)
        elements: 元素列表
        draw_text: 是否绘制文字标签
        
    Returns:
        标注后的图像
    """
    # 复制图像
    result = image.copy()
    
    # 颜色映射
    color_map = {
        "button": (0, 255, 0),    # 绿色
        "input": (255, 0, 0),     # 蓝色
        "icon": (0, 0, 255),      # 红色
        "window": (255, 255, 0),  # 青色
    }
    
    for elem in elements:
        # 获取颜色
        color = color_map.get(elem.element_type.value, (128, 128, 128))
        
        # 绘制边界框
        bbox = elem.bbox
        cv2.rectangle(result, (bbox.x1, bbox.y1), (bbox.x2, bbox.y2), color, 2)
        
        # 绘制标签
        if draw_text:
            label = f"{elem.id}: {elem.element_type.value} ({elem.confidence:.2f})"
            
            # 计算标签位置
            label_y = bbox.y1 - 10 if bbox.y1 > 20 else bbox.y2 + 20
            
            # 绘制标签背景
            (text_width, text_height), _ = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
            )
            cv2.rectangle(
                result,
                (bbox.x1, label_y - text_height - 4),
                (bbox.x1 + text_width, label_y),
                color,
                -1
            )
            
            # 绘制文字
            cv2.putText(
                result, label,
                (bbox.x1, label_y - 2),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1
            )
        
        # 绘制中心点
        center = elem.center
        cv2.circle(result, center, 3, (0, 0, 255), -1)
    
    return result


def save_debug_image(image: np.ndarray, path: Path, elements: List[UIElement] = None):
    """
    保存调试图像
    
    Args:
        image: 图像数组
        path: 保存路径
        elements: 可选，要标注的元素
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    if elements:
        image = draw_elements(image, elements)
    
    cv2.imwrite(str(path), image)


def resize_for_display(image: np.ndarray, max_width: int = 1280, max_height: int = 720) -> np.ndarray:
    """
    调整图像大小以适应显示
    
    Args:
        image: 原始图像
        max_width: 最大宽度
        max_height: 最大高度
        
    Returns:
        调整后的图像
    """
    h, w = image.shape[:2]
    
    # 计算缩放比例
    scale_w = max_width / w
    scale_h = max_height / h
    scale = min(scale_w, scale_h, 1.0)  # 不放大
    
    if scale < 1.0:
        new_w = int(w * scale)
        new_h = int(h * scale)
        return cv2.resize(image, (new_w, new_h))
    
    return image


def crop_region(image: np.ndarray, bbox: tuple) -> np.ndarray:
    """
    裁剪图像区域
    
    Args:
        image: 原始图像
        bbox: (x1, y1, x2, y2) 边界框
        
    Returns:
        裁剪后的图像
    """
    x1, y1, x2, y2 = bbox
    return image[y1:y2, x1:x2]
