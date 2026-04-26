"""核心引擎模块"""

from .agent import ComputerUseAgent
from .executor import TaskExecutor, ExecutionResult
from .models import Task, TaskSequence, ExecutionState
from .config import Config
from .task_learner import TaskLearner
from .task_learning_engine import TaskLearningEngine, CoordinateAdapter, PatternExtractor, TaskRecommender
from .batch_models import (
    BatchTaskConfig,
    BatchTaskItem,
    BatchTaskResult,
    BatchReportGenerator,
    ExecutionMode,
    ReportFormat,
)
from .batch_executor import BatchExecutor
from .scheduler import TaskScheduler
from .failure_analyzer import FailureAnalyzer, FailureType
from .recovery_strategy import RecoveryStrategy, RecoveryResult
from .execution_diary import ExecutionDiary

__all__ = [
    "ComputerUseAgent",
    "TaskExecutor",
    "ExecutionResult",
    "Task",
    "TaskSequence",
    "ExecutionState",
    "Config",
    "TaskLearner",
    "TaskLearningEngine",
    "CoordinateAdapter",
    "PatternExtractor",
    "TaskRecommender",
    # batch
    "BatchTaskConfig",
    "BatchTaskItem",
    "BatchTaskResult",
    "BatchReportGenerator",
    "BatchExecutor",
    "ExecutionMode",
    "ReportFormat",
    # scheduler
    "TaskScheduler",
    # self-healing
    "FailureAnalyzer",
    "FailureType",
    "RecoveryStrategy",
    "RecoveryResult",
    "ExecutionDiary",
]
