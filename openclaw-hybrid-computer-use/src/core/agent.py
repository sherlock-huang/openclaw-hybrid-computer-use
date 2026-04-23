"""ComputerUseAgent 主类"""

import logging
from typing import Optional, Dict, Any

from .config import Config
from .executor import TaskExecutor
from .models import Task, TaskSequence, ExecutionResult
from .tasks_predefined import get_predefined_task, list_predefined_tasks


class ComputerUseAgent:
    """Computer-Use Agent 主类"""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.config.ensure_dirs()
        
        # 设置日志
        from ..utils.logger import setup_logger
        setup_logger(self.config.log_level, self.config.log_dir)
        
        self.logger = logging.getLogger(__name__)
        self.executor = TaskExecutor(self.config)
        
        self.logger.info("ComputerUseAgent 初始化完成")
    
    def execute(self, sequence: TaskSequence) -> ExecutionResult:
        """
        执行任务序列
        
        Args:
            sequence: 任务序列
            
        Returns:
            ExecutionResult: 执行结果
        """
        return self.executor.execute(sequence)
    
    def execute_task(self, task_name: str, **kwargs) -> ExecutionResult:
        """
        执行预定义任务
        
        Args:
            task_name: 任务名称
            **kwargs: 任务参数
            
        Returns:
            ExecutionResult: 执行结果
        """
        sequence = self._get_predefined_task(task_name, **kwargs)
        return self.execute(sequence)
    
    def detect_screen(self) -> Dict[str, Any]:
        """
        检测屏幕元素
        
        Returns:
            检测结果字典
        """
        screenshot = self.executor.screen.capture()
        elements = self.executor.detector.detect(screenshot)
        
        return {
            "element_count": len(elements),
            "elements": [e.to_dict() for e in elements],
        }
    
    def _get_predefined_task(self, name: str, **kwargs) -> TaskSequence:
        """获取预定义任务"""
        return get_predefined_task(name, **kwargs)
    
    def list_tasks(self) -> list:
        """列出所有预定义任务"""
        return list_predefined_tasks()
