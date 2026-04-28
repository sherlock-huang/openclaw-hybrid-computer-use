"""批量任务执行器

支持顺序/并行执行多个任务序列，并生成汇总报告。
"""

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import TaskSequence
from .executor import TaskExecutor
from .tasks_predefined import get_predefined_task
from .batch_models import (
    BatchTaskConfig,
    BatchTaskItem,
    BatchItemResult,
    BatchTaskResult,
    BatchReportGenerator,
    ExecutionMode,
)
from ..utils.exceptions import NotFoundError, ValidationError
from ..utils.logger import get_logger


logger = get_logger(__name__)


class BatchExecutor:
    """批量任务执行器

    示例::

        config = BatchTaskConfig.from_json("batch_config.json")
        executor = BatchExecutor()
        result = executor.run(config)
        print(f"成功率: {result.success_rate * 100:.1f}%")
    """

    def __init__(self, task_executor: Optional[TaskExecutor] = None):
        self.task_executor = task_executor or TaskExecutor()
        self.logger = get_logger(__name__)

    # ------------------------------------------------------------------
    # 核心入口
    # ------------------------------------------------------------------

    def run(self, config: BatchTaskConfig) -> BatchTaskResult:
        """执行批量任务配置，返回完整结果。"""
        self.logger.info(
            f"开始批量任务: {config.name}, "
            f"模式={config.mode.value}, 任务数={len(config.items)}"
        )
        started_at = datetime.now()
        enabled_items = [item for item in config.items if item.enabled]

        if config.mode == ExecutionMode.SEQUENTIAL:
            item_results = self._run_sequential(enabled_items, config)
        else:
            item_results = self._run_parallel(enabled_items, config)

        finished_at = datetime.now()
        result = BatchTaskResult(
            config=config,
            items=item_results,
            started_at=started_at,
            finished_at=finished_at,
        )
        self.logger.info(
            f"批量任务完成: {result.success_count}/{result.total_count} 成功, "
            f"耗时 {result.duration:.2f}s"
        )
        return result

    def run_and_report(self, config: BatchTaskConfig) -> str:
        """执行并自动生成报告，返回报告文件路径。"""
        result = self.run(config)
        report = BatchReportGenerator(result)
        path = report.save()
        self.logger.info(f"报告已保存: {path}")
        return path

    # ------------------------------------------------------------------
    # 执行策略
    # ------------------------------------------------------------------

    def _run_sequential(
        self, items: List[BatchTaskItem], config: BatchTaskConfig
    ) -> List[BatchItemResult]:
        results: List[BatchItemResult] = []
        for item in items:
            item_result = self._execute_item(item)
            results.append(item_result)
            if not item_result.result.success and config.stop_on_error:
                self.logger.warning(
                    f"任务 '{item.label}' 失败且 stop_on_error=True, 终止后续执行"
                )
                break
        return results

    def _run_parallel(
        self, items: List[BatchTaskItem], config: BatchTaskConfig
    ) -> List[BatchItemResult]:
        results_map: Dict[int, BatchItemResult] = {}
        with ThreadPoolExecutor(max_workers=config.max_workers) as pool:
            futures = {
                pool.submit(self._execute_item, item): idx
                for idx, item in enumerate(items)
            }
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    item_result = future.result()
                except Exception as e:
                    self.logger.exception(f"并行任务 #{idx} 发生未预期异常")
                    item_result = self._wrap_unexpected_error(items[idx], e)
                results_map[idx] = item_result
        return [results_map[i] for i in range(len(items)) if i in results_map]

    # ------------------------------------------------------------------
    # 单任务执行
    # ------------------------------------------------------------------

    def _execute_item(self, item: BatchTaskItem) -> BatchItemResult:
        started_at = datetime.now()
        self.logger.info(f"执行任务: {item.label or item.task_name}")
        try:
            sequence = self._resolve_task(item)
        except Exception as e:
            self.logger.error(f"任务解析失败 [{item.task_name}]: {e}")
            from .models import ExecutionResult
            result = ExecutionResult(
                success=False,
                error=str(e),
                completed_steps=0,
                duration=0.0,
            )
            return BatchItemResult(
                item=item,
                result=result,
                started_at=started_at,
                finished_at=datetime.now(),
            )

        exec_result = self.task_executor.execute_sequence(sequence)
        finished_at = datetime.now()
        status = "成功" if exec_result.success else "失败"
        self.logger.info(
            f"任务完成 [{item.label}]: {status}, "
            f"步骤={exec_result.completed_steps}, 耗时={exec_result.duration:.2f}s"
        )
        return BatchItemResult(
            item=item,
            result=exec_result,
            started_at=started_at,
            finished_at=finished_at,
        )

    def _resolve_task(self, item: BatchTaskItem) -> TaskSequence:
        """将 BatchTaskItem 解析为可执行的 TaskSequence。"""
        task_name = item.task_name
        # 1. 预定义任务
        try:
            return get_predefined_task(task_name, **item.params)
        except NotFoundError:
            pass  # 不是预定义任务，继续尝试文件
        except TypeError as e:
            raise ValidationError(f"预定义任务 '{task_name}' 参数错误: {e}")

        # 2. JSON 任务文件
        path = Path(task_name)
        if path.suffix == ".json" and path.exists():
            return self._load_task_from_json(str(path))

        raise NotFoundError(
            f"无法解析任务: '{task_name}' 不是已知的预定义任务，"
            f"也不是有效的 JSON 任务文件"
        )

    def _load_task_from_json(self, filepath: str) -> TaskSequence:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        from .models import Task
        tasks = [Task(**t) for t in data.get("tasks", [])]
        return TaskSequence(
            name=data.get("name", Path(filepath).stem),
            tasks=tasks,
            max_retries=data.get("max_retries", 3),
        )

    def _wrap_unexpected_error(self, item: BatchTaskItem, exc: Exception) -> BatchItemResult:
        from .models import ExecutionResult
        return BatchItemResult(
            item=item,
            result=ExecutionResult(
                success=False,
                error=f"Unexpected error: {exc}",
                completed_steps=0,
                duration=0.0,
            ),
            started_at=datetime.now(),
            finished_at=datetime.now(),
        )
