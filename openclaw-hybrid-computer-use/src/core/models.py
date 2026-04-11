"""数据模型定义"""

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
from pathlib import Path
import numpy as np


class ElementType(Enum):
    """UI元素类型"""
    BUTTON = "button"
    INPUT = "input"
    ICON = "icon"
    WINDOW = "window"


@dataclass
class BoundingBox:
    """边界框"""
    x1: int
    y1: int
    x2: int
    y2: int
    
    @property
    def width(self) -> int:
        return self.x2 - self.x1
    
    @property
    def height(self) -> int:
        return self.y2 - self.y1
    
    @property
    def center(self) -> Tuple[int, int]:
        return ((self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2)
    
    def to_tuple(self) -> Tuple[int, int, int, int]:
        return (self.x1, self.y1, self.x2, self.y2)


@dataclass
class UIElement:
    """UI元素"""
    id: str
    bbox: BoundingBox
    element_type: ElementType
    confidence: float
    text: Optional[str] = None
    
    @property
    def center(self) -> Tuple[int, int]:
        return self.bbox.center
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "bbox": self.bbox.to_tuple(),
            "type": self.element_type.value,
            "confidence": self.confidence,
            "text": self.text,
            "center": self.center,
        }


@dataclass
class Task:
    """原子任务定义"""
    action: str  # "click", "type", "launch", "wait", "press"
    target: Optional[str] = None  # 元素ID、坐标或应用名
    value: Optional[str] = None  # 输入值
    delay: float = 1.0  # 执行后等待时间
    
    def to_dict(self) -> Dict:
        return {
            "action": self.action,
            "target": self.target,
            "value": self.value,
            "delay": self.delay,
        }


@dataclass
class TaskSequence:
    """任务序列"""
    name: str
    tasks: List[Task]
    max_retries: int = 3
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "tasks": [t.to_dict() for t in self.tasks],
            "max_retries": self.max_retries,
        }


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    completed_steps: int
    duration: float
    error: Optional[str] = None
    screenshots: List[np.ndarray] = field(default_factory=list)
    logs: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "completed_steps": self.completed_steps,
            "duration": self.duration,
            "error": self.error,
            "screenshot_count": len(self.screenshots),
            "log_count": len(self.logs),
        }


@dataclass
class RecordingEvent:
    """录制的事件"""
    action: str                    # "click", "type", "hotkey"
    timestamp: float              # 相对于录制开始的时间(秒)
    target: Optional[str] = None  # 元素ID
    position: Optional[Tuple[int, int]] = None  # 坐标 (x, y)
    value: Optional[str] = None   # 输入值 (用于type)
    element_type: Optional[str] = None  # 元素类型
    
    def to_dict(self) -> Dict:
        """转换为字典，用于JSON序列化"""
        return {
            "action": self.action,
            "timestamp": self.timestamp,
            "target": self.target,
            "position": self.position,
            "value": self.value,
            "element_type": self.element_type,
        }


@dataclass
class RecordingSession:
    """录制会话"""
    name: str
    start_time: datetime
    events: List[RecordingEvent]
    
    def to_task_sequence(self) -> "TaskSequence":
        """转换为可执行的任务序列"""
        tasks = []
        for event in self.events:
            # 如果检测到元素，用元素ID；否则用坐标
            target = event.target
            if target is None and event.position is not None:
                target = f"{event.position[0]},{event.position[1]}"
            
            task = Task(
                action=event.action,
                target=target,
                value=event.value,
                delay=0.5  # 默认延迟
            )
            tasks.append(task)
        return TaskSequence(name=self.name, tasks=tasks)
    
    def save_to_file(self, filepath: str):
        """保存为JSON文件"""
        import json
        from pathlib import Path
        
        sequence = self.to_task_sequence()
        
        data = {
            "name": self.name,
            "recorded_at": self.start_time.isoformat(),
            "tasks": [task.to_dict() for task in sequence.tasks]
        }
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


class ExecutionState:
    """执行状态管理"""
    
    def __init__(self):
        self.sequence: Optional[TaskSequence] = None
        self.current_step: int = 0
        self.screenshots: List[np.ndarray] = []
        self.logs: List[Dict] = []
        self.start_time: Optional[float] = None
        self.status: str = "idle"  # idle, running, success, failed
    
    def start(self, sequence: TaskSequence):
        """开始执行"""
        self.sequence = sequence
        self.current_step = 0
        self.start_time = time.time()
        self.status = "running"
        self.screenshots = []
        self.logs = []
    
    def add_screenshot(self, image: np.ndarray):
        """添加截图"""
        self.screenshots.append(image.copy())
    
    def log(self, action: str, details: Dict[str, Any]):
        """记录日志"""
        self.logs.append({
            "timestamp": time.time(),
            "action": action,
            "details": details,
        })
    
    def next_step(self):
        """进入下一步"""
        self.current_step += 1
    
    def complete(self) -> ExecutionResult:
        """标记完成"""
        self.status = "success"
        return ExecutionResult(
            success=True,
            completed_steps=self.current_step,
            duration=time.time() - self.start_time if self.start_time else 0,
            screenshots=self.screenshots,
            logs=self.logs,
        )
    
    def fail(self, error: str) -> ExecutionResult:
        """标记失败"""
        self.status = "failed"
        return ExecutionResult(
            success=False,
            error=error,
            completed_steps=self.current_step,
            duration=time.time() - self.start_time if self.start_time else 0,
            screenshots=self.screenshots,
            logs=self.logs,
        )
