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
from .skill_manager import SkillManager, SkillEntry
from .model_tier_manager import ModelTierManager, TierResult
from .visual_diagnostician import VisualDiagnostician, VisualContextBuilder, DiagnosisReport
from .human_intervention import HumanInterventionHandler, HumanDecision, InterventionResult

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
    # self-healing Phase 1
    "FailureAnalyzer",
    "FailureType",
    "RecoveryStrategy",
    "RecoveryResult",
    "ExecutionDiary",
    # self-healing Phase 2
    "SkillManager",
    "SkillEntry",
    "ModelTierManager",
    "TierResult",
    "VisualDiagnostician",
    "VisualContextBuilder",
    "DiagnosisReport",
    # human-in-the-loop
    "HumanInterventionHandler",
    "HumanDecision",
    "InterventionResult",
]
