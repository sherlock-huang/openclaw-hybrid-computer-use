"""可视化调试工具"""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from ..core.models import UIElement, ExecutionResult, Task


class ExecutionVisualizer:
    """执行过程可视化器"""
    
    def __init__(self, output_dir: str = "output/visualizations"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.step = 0
    
    def visualize_detection(self, image: np.ndarray, 
                           elements: List[UIElement],
                           title: str = "Detection") -> Path:
        """
        可视化检测结果
        
        Args:
            image: 原始图像
            elements: 检测到的元素
            title: 图像标题
            
        Returns:
            保存路径
        """
        from .image import draw_elements
        
        result = draw_elements(image, elements, draw_text=True)
        
        # 添加标题
        cv2.putText(result, title, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # 保存
        timestamp = datetime.now().strftime("%H%M%S")
        path = self.output_dir / f"detection_{self.step:03d}_{timestamp}.png"
        cv2.imwrite(str(path), result)
        
        self.step += 1
        return path
    
    def visualize_task_execution(self, image: np.ndarray,
                                  task: Task,
                                  elements: List[UIElement],
                                  highlight_id: Optional[str] = None) -> Path:
        """
        可视化任务执行
        
        Args:
            image: 屏幕截图
            task: 当前任务
            elements: 检测到的元素
            highlight_id: 要高亮显示的元素ID
            
        Returns:
            保存路径
        """
        from .image import draw_elements
        
        result = image.copy()
        
        # 绘制所有元素
        for elem in elements:
            color = (0, 255, 0)  # 默认绿色
            
            # 高亮目标元素
            if elem.id == highlight_id or elem.element_type.value == task.target:
                color = (0, 0, 255)  # 红色高亮
                # 绘制目标标记
                cv2.circle(result, elem.center, 10, (0, 0, 255), 2)
            
            cv2.rectangle(result, 
                         (elem.bbox.x1, elem.bbox.y1),
                         (elem.bbox.x2, elem.bbox.y2),
                         color, 2)
            
            # 标签
            label = f"{elem.id}: {elem.element_type.value}"
            cv2.putText(result, label,
                       (elem.bbox.x1, elem.bbox.y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # 添加任务信息
        task_text = f"Task: {task.action}"
        if task.target:
            task_text += f" -> {task.target}"
        
        # 背景条
        cv2.rectangle(result, (0, 0), (result.shape[1], 40), (0, 0, 0), -1)
        cv2.putText(result, task_text, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # 保存
        timestamp = datetime.now().strftime("%H%M%S")
        path = self.output_dir / f"task_{self.step:03d}_{task.action}_{timestamp}.png"
        cv2.imwrite(str(path), result)
        
        self.step += 1
        return path
    
    def create_execution_report(self, result: ExecutionResult,
                                output_path: Optional[Path] = None) -> Path:
        """
        创建执行报告（拼接所有截图）
        
        Args:
            result: 执行结果
            output_path: 输出路径，None则自动生成
            
        Returns:
            报告路径
        """
        if not result.screenshots:
            return None
        
        # 计算布局
        n_images = len(result.screenshots)
        cols = min(4, n_images)
        rows = (n_images + cols - 1) // cols
        
        # 统一尺寸
        target_width = 400
        target_height = 300
        
        # 创建画布
        canvas_width = cols * target_width
        canvas_height = rows * target_height + 100  # 顶部留空给标题
        canvas = np.ones((canvas_height, canvas_width, 3), dtype=np.uint8) * 255
        
        # 添加标题
        title = f"Execution Report: {'Success' if result.success else 'Failed'}"
        cv2.putText(canvas, title, (20, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        info = f"Steps: {result.completed_steps} | Duration: {result.duration:.2f}s"
        if result.error:
            info += f" | Error: {result.error}"
        cv2.putText(canvas, info, (20, 80),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        
        # 放置截图
        for i, img in enumerate(result.screenshots):
            row = i // cols
            col = i % cols
            
            # 调整大小
            resized = cv2.resize(img, (target_width, target_height))
            
            # 放置到画布
            y_offset = row * target_height + 100
            x_offset = col * target_width
            canvas[y_offset:y_offset+target_height, 
                   x_offset:x_offset+target_width] = resized
            
            # 添加步骤号
            cv2.putText(canvas, f"Step {i+1}",
                       (x_offset + 10, y_offset + 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # 保存
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"report_{timestamp}.png"
        
        cv2.imwrite(str(output_path), canvas)
        return output_path


def visualize_mouse_path(start: tuple, end: tuple, 
                        screen_size: tuple = (1920, 1080),
                        output_path: str = "output/mouse_path.png"):
    """
    可视化鼠标移动路径
    
    Args:
        start: 起点坐标 (x, y)
        end: 终点坐标 (x, y)
        screen_size: 屏幕尺寸
        output_path: 输出路径
    """
    # 创建画布（缩小显示）
    scale = 0.5
    canvas = np.ones((int(screen_size[1]*scale), int(screen_size[0]*scale), 3), dtype=np.uint8) * 240
    
    # 缩放坐标
    s = (int(start[0]*scale), int(start[1]*scale))
    e = (int(end[0]*scale), int(end[1]*scale))
    
    # 绘制路径
    cv2.line(canvas, s, e, (255, 0, 0), 2)
    
    # 绘制起点和终点
    cv2.circle(canvas, s, 8, (0, 255, 0), -1)
    cv2.circle(canvas, e, 8, (0, 0, 255), -1)
    
    # 标注
    cv2.putText(canvas, f"Start {start}", (s[0]+10, s[1]),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    cv2.putText(canvas, f"End {end}", (e[0]+10, e[1]),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    
    # 保存
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(output_path, canvas)
    
    return output_path
