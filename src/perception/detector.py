"""UI元素检测器 (基于YOLOv8)"""

import logging
import uuid
from typing import List, Optional
from pathlib import Path

import numpy as np

from ..core.config import Config
from ..core.models import UIElement, BoundingBox, ElementType


class ElementDetector:
    """UI元素检测器"""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.logger = logging.getLogger(__name__)
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """加载YOLO模型"""
        try:
            from ultralytics import YOLO
            
            model_path = self.config.yolo_model_path
            
            # 如果模型不存在，下载预训练模型
            if not Path(model_path).exists():
                self.logger.warning(f"模型文件不存在: {model_path}，尝试下载 yolov8n")
                # 使用 ultralytics 的预训练模型
                self.model = YOLO("yolov8n.pt")
                # 保存到指定路径
                Path(model_path).parent.mkdir(parents=True, exist_ok=True)
                self.model.save(model_path)
            else:
                self.model = YOLO(model_path)
            
            self.logger.info(f"YOLO模型加载成功: {model_path}")
            
        except ImportError:
            self.logger.error("ultralytics not installed. Run: pip install ultralytics")
            raise
        except Exception as e:
            self.logger.error(f"模型加载失败: {e}")
            raise
    
    def detect(self, image: np.ndarray) -> List[UIElement]:
        """
        检测图像中的所有UI元素
        
        Args:
            image: BGR格式的numpy数组
            
        Returns:
            UIElement列表，按置信度排序
        """
        if self.model is None:
            self.logger.error("模型未加载")
            return []
        
        try:
            # 运行检测
            results = self.model(
                image, 
                conf=self.config.yolo_conf_threshold,
                iou=self.config.yolo_nms_threshold,
                verbose=False
            )
            
            # 解析结果
            elements = self._parse_results(results[0])
            
            # 按置信度排序
            elements.sort(key=lambda x: x.confidence, reverse=True)
            
            self.logger.debug(f"检测到 {len(elements)} 个元素")
            return elements
            
        except Exception as e:
            self.logger.error(f"检测失败: {e}")
            return []
    
    def _parse_results(self, result) -> List[UIElement]:
        """解析YOLO检测结果"""
        elements = []
        
        if result.boxes is None:
            return elements
        
        boxes = result.boxes
        
        for i, box in enumerate(boxes):
            # 获取坐标
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
            
            # 获取置信度
            confidence = float(box.conf[0].cpu().numpy())
            
            # 获取类别
            cls_id = int(box.cls[0].cpu().numpy())
            
            # 映射类别到元素类型
            # 注意：YOLOv8默认的COCO类别不包含UI元素
            # 这里需要根据实际训练的模型来映射
            element_type = self._map_class_to_type(cls_id)
            
            element = UIElement(
                id=f"elem_{i:03d}",
                bbox=BoundingBox(x1, y1, x2, y2),
                element_type=element_type,
                confidence=confidence,
            )
            elements.append(element)
        
        return elements
    
    def _map_class_to_type(self, cls_id: int) -> ElementType:
        """
        将YOLO类别ID映射到元素类型
        
        注意：这是针对通用YOLOv8的临时映射
        实际使用时应该用专门训练的UI检测模型
        """
        # COCO类别到UI元素类型的临时映射
        # 这只是一个示例，实际需要专门的UI检测模型
        mapping = {
            # 可以根据需要调整映射
            0: ElementType.ICON,    # person -> icon (临时)
            1: ElementType.BUTTON,  # bicycle -> button (临时)
            2: ElementType.INPUT,   # car -> input (临时)
        }
        
        return mapping.get(cls_id, ElementType.BUTTON)
    
    def detect_by_type(self, image: np.ndarray, element_type: ElementType) -> List[UIElement]:
        """
        按类型筛选元素
        
        Args:
            image: 输入图像
            element_type: 目标元素类型
            
        Returns:
            匹配的元素列表
        """
        elements = self.detect(image)
        return [e for e in elements if e.element_type == element_type]
    
    def find_element_by_text(self, image: np.ndarray, text: str) -> Optional[UIElement]:
        """
        通过文字查找元素 (需要OCR配合)
        
        Args:
            image: 输入图像
            text: 目标文字
            
        Returns:
            匹配的元素，未找到返回None
        """
        # 这里可以先运行OCR，然后匹配文字位置
        # 暂时返回None，需要配合OCR模块实现
        return None
