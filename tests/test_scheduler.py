"""任务调度器单元测试"""

import os
import sys
import tempfile
import threading
import time
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.batch_models import BatchTaskConfig, BatchTaskItem
from src.core.scheduler import TaskScheduler, run_scheduler_cli
from src.utils.exceptions import ValidationError


class FakeExecutor:
    """不执行实际任务的假执行器，用于测试。"""

    def __init__(self, results=None):
        self.results = results or []
        self.call_count = 0

    def run(self, config):
        idx = min(self.call_count, len(self.results) - 1)
        result = self.results[idx] if self.results else _make_ok_result(config)
        self.call_count += 1
        return result


def _make_ok_result(config):
    from src.core.batch_models import BatchTaskResult, BatchItemResult
    from src.core.models import ExecutionResult

    items = []
    for it in config.items:
        items.append(
            BatchItemResult(
                item=it,
                result=ExecutionResult(success=True, completed_steps=1, duration=0.1),
                started_at=datetime.now(),
                finished_at=datetime.now(),
            )
        )
    return BatchTaskResult(
        config=config,
        items=items,
        started_at=datetime.now(),
        finished_at=datetime.now(),
    )


class TestTaskScheduler(unittest.TestCase):
    def _make_scheduler(self, executor=None):
        config = BatchTaskConfig(name="test_scheduler", items=[BatchTaskItem(task_name="noop")])
        return TaskScheduler(config, executor=executor or FakeExecutor())

    def test_init(self):
        sched = self._make_scheduler()
        self.assertFalse(sched.is_running)
        self.assertEqual(sched.run_count, 0)

    def test_run_once(self):
        executor = FakeExecutor()
        sched = self._make_scheduler(executor=executor)
        sched.run_once()
        self.assertEqual(sched.run_count, 1)
        self.assertEqual(executor.call_count, 1)

    def test_run_once_at_past_time_raises(self):
        sched = self._make_scheduler()
        past = datetime.now() - timedelta(seconds=10)
        with self.assertRaises(ValidationError):
            sched.run_once_at(past)

    def test_start_interval_runs_multiple_times(self):
        executor = FakeExecutor()
        sched = self._make_scheduler(executor=executor)
        sched.start_interval(0.05)  # 50ms 间隔
        time.sleep(0.18)  # 足够跑 2~3 次
        sched.stop()
        self.assertGreaterEqual(executor.call_count, 2)
        self.assertEqual(sched.run_count, executor.call_count)
        self.assertFalse(sched.is_running)

    def test_stop_idempotent(self):
        sched = self._make_scheduler()
        sched.stop()  # 未启动时停止不应报错
        self.assertFalse(sched.is_running)

    def test_double_start_raises(self):
        sched = self._make_scheduler()
        sched.start_interval(1.0)
        try:
            with self.assertRaises(RuntimeError):
                sched.start_interval(1.0)
        finally:
            sched.stop()

    def test_cron_mode(self):
        # 使用每秒都触发的 cron 表达式做快速测试
        executor = FakeExecutor()
        sched = self._make_scheduler(executor=executor)
        sched.start_cron("* * * * * *")  # 每秒（croniter 支持 6 位）
        time.sleep(1.3)
        sched.stop()
        self.assertGreaterEqual(executor.call_count, 1)


class TestRunSchedulerCli(unittest.TestCase):
    def test_once_mode(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            cfg = BatchTaskConfig(name="cli_test", items=[BatchTaskItem(task_name="noop")])
            import json

            json.dump(cfg.to_dict(), f)
            path = f.name
        try:
            # 不应抛出异常
            run_scheduler_cli(path, "once", "", once=True)
        finally:
            os.unlink(path)

    def test_at_mode_past_time(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            cfg = BatchTaskConfig(name="cli_test", items=[])
            import json

            json.dump(cfg.to_dict(), f)
            path = f.name
        try:
            past = (datetime.now() - timedelta(minutes=1)).isoformat()
            with self.assertRaises(ValidationError):
                run_scheduler_cli(path, "at", past, once=True)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
