"""OCR文字识别 (基于PaddleOCR)"""

import logging
from typing import List, Optional, Tuple
from dataclasses import dataclass

import numpy as np

from ..core.config import Config


@dataclass
class TextBox:
    """文字框"""
    text: str
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    confidence: float
    
    @property
    def center(self) -> Tuple[int, int]:
        return ((self.bbox[0] + self.bbox[2]) // 2, 
                (self.bbox[1] + self.bbox[3]) // 2)


class TextRecognizer:
    """文字识别器"""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.logger = logging.getLogger(__name__)
        self.ocr = None

        # 延迟加载：首次 recognize 时再初始化
    
    def _load_model(self):
        """加载PaddleOCR模型"""
        try:
            from paddleocr import PaddleOCR
            
            self.ocr = PaddleOCR(
                use_angle_cls=True,
                lang=self.config.ocr_lang,
                use_gpu=self.config.ocr_use_gpu,
                show_log=False,  # 减少日志输出
            )
            self.logger.info(f"PaddleOCR 加载成功 (lang={self.config.ocr_lang})")
            
        except ImportError:
            self.logger.error("paddleocr not installed. Run: pip install paddleocr")
            self.ocr = None
        except Exception as e:
            self.logger.error(f"PaddleOCR 加载失败: {e}")
            self.ocr = None
    
    def recognize(self, image: np.ndarray) -> List[TextBox]:
        """
        识别图像中的所有文字
        
        Args:
            image: BGR格式的numpy数组
            
        Returns:
            TextBox列表
        """
        if self.ocr is None:
            self._load_model()
        
        if self.ocr is None:
            self.logger.error("OCR模型未加载")
            return []
        
        try:
            # PaddleOCR需要RGB格式
            if len(image.shape) == 3 and image.shape[2] == 3:
                image_rgb = image[:, :, ::-1]  # BGR to RGB
            else:
                image_rgb = image
            
            result = self.ocr.ocr(image_rgb, cls=True)
            
            text_boxes = []
            if result and result[0]:
                for line in result[0]:
                    if line:
                        bbox = line[0]  # 四个角点坐标
                        text = line[1][0]  # 文字内容
                        confidence = line[1][1]  # 置信度
                        
                        # 转换为矩形边界框
                        xs = [p[0] for p in bbox]
                        ys = [p[1] for p in bbox]
                        x1, y1, x2, y2 = int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))
                        
                        text_boxes.append(TextBox(
                            text=text,
                            bbox=(x1, y1, x2, y2),
                            confidence=confidence
                        ))
            
            self.logger.debug(f"OCR识别到 {len(text_boxes)} 处文字")
            return text_boxes
            
        except Exception as e:
            self.logger.error(f"OCR识别失败: {e}")
            return []
    
    def find_text(self, image: np.ndarray, target: str) -> Optional[Tuple[int, int]]:
        """
        查找指定文字的位置
        
        Args:
            image: 输入图像
            target: 目标文字
            
        Returns:
            文字中心点坐标 (x, y)，未找到返回None
        """
        text_boxes = self.recognize(image)
        
        for box in text_boxes:
            if target in box.text:
                self.logger.debug(f"找到文字 '{target}' @ {box.center}")
                return box.center
        
        return None
    
    def recognize_region(self, image: np.ndarray, region: Tuple[int, int, int, int]) -> str:
        """
        识别指定区域的文字
        
        Args:
            image: 输入图像
            region: (x, y, w, h) 区域
            
        Returns:
            识别的文字
        """
        x, y, w, h = region
        roi = image[y:y+h, x:x+w]
        
        text_boxes = self.recognize(roi)
        
        # 合并区域内的所有文字
        texts = [box.text for box in text_boxes]
        return " ".join(texts)

