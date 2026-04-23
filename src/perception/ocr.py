"""OCR 文字识别模块（基于 PaddleOCR）

本模块提供图像中的文字检测与识别能力，主要特性：
    - PaddleOCR 懒加载：模型体积较大，首次调用 recognize() 时才初始化，
      避免在导入阶段占用过多内存和时间。
    - TextBox 数据结构：封装了识别结果的文字内容、矩形边界框 (x1,y1,x2,y2)
      以及置信度，并提供 center 属性快速获取文字中心坐标。
    - 自动颜色空间转换：PaddleOCR 内部使用 RGB，而本项目的图像管道默认
      使用 BGR（OpenCV 格式），因此在送入 OCR 前会自动执行 BGR -> RGB 转换。

依赖安装：
    pip install paddleocr

使用示例：
    >>> recognizer = TextRecognizer()
    >>> boxes = recognizer.recognize(image)  # image 为 BGR numpy 数组
    >>> for box in boxes:
    ...     print(box.text, box.center, box.confidence)
"""

import logging
from typing import List, Optional, Tuple
from dataclasses import dataclass

import numpy as np

from ..core.config import Config


@dataclass
class TextBox:
    """文字检测结果的数据容器

    Attributes:
        text: 识别出的文字内容
        bbox: 文字区域的轴对齐矩形边界框，格式为 (x1, y1, x2, y2)
              其中 (x1, y1) 为左上角，(x2, y2) 为右下角（均包含在内）
        confidence: 识别置信度，范围 0.0 ~ 1.0，越高越可信
    """
    text: str
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    confidence: float

    @property
    def center(self) -> Tuple[int, int]:
        """计算文字框的几何中心点坐标

        Returns:
            (center_x, center_y) 的整数元组，可用于点击定位
        """
        return ((self.bbox[0] + self.bbox[2]) // 2,
                (self.bbox[1] + self.bbox[3]) // 2)


class TextRecognizer:
    """文字识别器

    封装 PaddleOCR 的初始化、推理与后处理流程，对外提供简洁的文本识别接口。
    """

    def __init__(self, config: Optional[Config] = None):
        """初始化文字识别器

        Args:
            config: 全局配置对象；为 None 时自动创建默认 Config 实例
        """
        self.config = config or Config()
        self.logger = logging.getLogger(__name__)
        self.ocr = None  # 延迟加载占位，首次 recognize 时通过 _load_model 初始化

        # 延迟加载：首次调用 recognize() 时才初始化 PaddleOCR 模型，
        # 避免在导入模块时因加载深度学习模型导致启动缓慢或内存飙升。

    def _load_model(self):
        """加载 PaddleOCR 模型（懒加载）

        根据配置中的语言、GPU 等参数初始化 PaddleOCR 实例。
        若 paddleocr 未安装或初始化失败，会将 self.ocr 设为 None，
        后续识别调用会返回空列表并记录错误日志。
        """
        try:
            from paddleocr import PaddleOCR

            self.ocr = PaddleOCR(
                use_angle_cls=True,               # 启用方向分类，支持旋转文本
                lang=self.config.ocr_lang,        # 语言模型，如 'ch', 'en'
                use_gpu=self.config.ocr_use_gpu,  # 是否使用 GPU 加速
                show_log=False,                   # 关闭 PaddleOCR 冗余日志
            )
            self.logger.info(f"PaddleOCR 加载成功 (lang={self.config.ocr_lang})")

        except ImportError:
            self.logger.error("paddleocr not installed. Run: pip install paddleocr")
            self.ocr = None
        except Exception as e:
            self.logger.error(f"PaddleOCR 加载失败: {e}")
            self.ocr = None

    def recognize(self, image: np.ndarray) -> List[TextBox]:
        """识别图像中的所有文字

        执行流程：
            1. 若模型未加载，先调用 _load_model() 初始化
            2. 将输入的 BGR 图像转为 RGB（PaddleOCR 要求）
            3. 调用 PaddleOCR 推理，解析返回的四边形与文本信息
            4. 将四边形转换为轴对齐矩形 (x1,y1,x2,y2)，封装为 TextBox 列表

        Args:
            image: BGR 格式的 numpy 数组，形状通常为 (H, W, 3)

        Returns:
            TextBox 列表，每个元素包含文字、边界框和置信度；
            若模型未加载或识别失败则返回空列表。
        """
        if self.ocr is None:
            self._load_model()

        if self.ocr is None:
            self.logger.error("OCR 模型未加载")
            return []

        try:
            # PaddleOCR 需要 RGB 格式；若输入为 3 通道 BGR，通过 ::-1 翻转通道轴
            if len(image.shape) == 3 and image.shape[2] == 3:
                image_rgb = image[:, :, ::-1]  # BGR to RGB：逆序排列最后一维（通道轴）
            else:
                # 非 3 通道图像（如灰度图）直接原样传入
                image_rgb = image

            result = self.ocr.ocr(image_rgb, cls=True)

            text_boxes = []
            # PaddleOCR 返回的 result 结构为：
            # result[0] -> 每行检测结果的列表
            # 每行 line -> [bbox, (text, confidence)]
            # 其中 bbox 为 4 个角点坐标 [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
            if result and result[0]:
                for line in result[0]:
                    if line:
                        bbox = line[0]           # 四个角点坐标列表
                        text = line[1][0]        # 识别出的文字字符串
                        confidence = line[1][1]  # 文字置信度分数

                        # 将任意四边形转换为轴对齐矩形（最小外接矩形）
                        # 通过分别取所有角点的 x/y 的最小值和最大值得到
                        xs = [p[0] for p in bbox]
                        ys = [p[1] for p in bbox]
                        x1, y1, x2, y2 = int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))

                        text_boxes.append(TextBox(
                            text=text,
                            bbox=(x1, y1, x2, y2),
                            confidence=confidence
                        ))

            self.logger.debug(f"OCR 识别到 {len(text_boxes)} 处文字")
            return text_boxes

        except Exception as e:
            self.logger.error(f"OCR 识别失败: {e}")
            return []

    def find_text(self, image: np.ndarray, target: str) -> Optional[Tuple[int, int]]:
        """查找指定文字的位置

        先对整张图像做 OCR，然后在结果中搜索包含 target 子串的文本，
        返回首个匹配项的中心点坐标。

        Args:
            image: 输入图像（BGR 格式）
            target: 目标文字（支持子串匹配）

        Returns:
            匹配文字的中心点坐标 (x, y)；未找到则返回 None
        """
        text_boxes = self.recognize(image)

        for box in text_boxes:
            # 使用子串匹配（in）而非完全相等，提升容错性
            if target in box.text:
                self.logger.debug(f"找到文字 '{target}' @ {box.center}")
                return box.center

        return None

    def recognize_region(self, image: np.ndarray, region: Tuple[int, int, int, int]) -> str:
        """识别指定区域内的所有文字

        先根据 (x, y, w, h) 从原图裁剪 ROI，再对 ROI 执行 OCR，
        最后将所有识别结果按空格拼接为单个字符串。

        Args:
            image: 输入图像（BGR 格式）
            region: 感兴趣区域，格式为 (x, y, w, h)

        Returns:
            区域内识别到的文字，多个文本框之间以空格分隔；
            若未识别到文字则返回空字符串。
        """
        x, y, w, h = region
        # 使用 numpy 切片裁剪 ROI（注意：OpenCV 坐标中 y 为行轴，x 为列轴）
        roi = image[y:y+h, x:x+w]

        text_boxes = self.recognize(roi)

        # 合并区域内的所有文字为一个字符串，顺序为 PaddleOCR 的检测顺序
        texts = [box.text for box in text_boxes]
        return " ".join(texts)
