"""批量任务模型单元测试"""

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.batch_models import (
    BatchTaskConfig,
    BatchTaskItem,
    BatchItemResult,
    BatchTaskResult,
    BatchReportGenerator,
    ExecutionMode,
    ReportFormat,
)
from src.core.models import ExecutionResult


class TestBatchTaskItem(unittest.TestCase):
    def test_defaults(self):
        item = BatchTaskItem(task_name="calculator_add")
        self.assertEqual(item.params, {})
        self.assertTrue(item.enabled)
        self.assertEqual(item.retries, 0)
        self.assertIsNone(item.label)

    def test_to_dict_roundtrip(self):
        item = BatchTaskItem(
            task_name="notepad_type",
            params={"text": "hello"},
            label="test",
            enabled=False,
            retries=2,
        )
        d = item.to_dict()
        restored = BatchTaskItem.from_dict(d)
        self.assertEqual(restored.task_name, "notepad_type")
        self.assertEqual(restored.params, {"text": "hello"})
        self.assertEqual(restored.label, "test")
        self.assertFalse(restored.enabled)
        self.assertEqual(restored.retries, 2)


class TestBatchTaskConfig(unittest.TestCase):
    def test_defaults(self):
        cfg = BatchTaskConfig(name="demo", items=[])
        self.assertEqual(cfg.mode, ExecutionMode.SEQUENTIAL)
        self.assertEqual(cfg.max_workers, 4)
        self.assertFalse(cfg.stop_on_error)
        self.assertEqual(cfg.report_format, ReportFormat.MARKDOWN)

    def test_json_roundtrip(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            original = BatchTaskConfig(
                name="test_cfg",
                items=[
                    BatchTaskItem(task_name="a", params={"x": 1}),
                    BatchTaskItem(task_name="b", enabled=False),
                ],
                mode=ExecutionMode.PARALLEL,
                max_workers=2,
                stop_on_error=True,
            )
            json.dump(original.to_dict(), f)
            path = f.name
        try:
            restored = BatchTaskConfig.from_json(path)
            self.assertEqual(restored.name, "test_cfg")
            self.assertEqual(restored.mode, ExecutionMode.PARALLEL)
            self.assertEqual(len(restored.items), 2)
            self.assertFalse(restored.items[1].enabled)
        finally:
            os.unlink(path)


class TestBatchTaskResult(unittest.TestCase):
    def _make_result(self, successes):
        cfg = BatchTaskConfig(name="demo", items=[])
        items = []
        for ok in successes:
            item = BatchTaskItem(task_name="t")
            er = ExecutionResult(success=ok, completed_steps=1, duration=1.0)
            items.append(
                BatchItemResult(
                    item=item,
                    result=er,
                    started_at=datetime.now(),
                    finished_at=datetime.now(),
                )
            )
        return BatchTaskResult(
            config=cfg,
            items=items,
            started_at=datetime.now(),
            finished_at=datetime.now(),
        )

    def test_counts(self):
        r = self._make_result([True, True, False, True])
        self.assertEqual(r.total_count, 4)
        self.assertEqual(r.success_count, 3)
        self.assertEqual(r.failed_count, 1)
        self.assertEqual(r.success_rate, 0.75)

    def test_empty(self):
        r = self._make_result([])
        self.assertEqual(r.success_rate, 0.0)

    def test_to_dict(self):
        r = self._make_result([True])
        d = r.to_dict()
        self.assertEqual(d["total"], 1)
        self.assertEqual(d["success"], 1)
        self.assertIn("items", d)


class TestBatchReportGenerator(unittest.TestCase):
    def _make_generator(self):
        cfg = BatchTaskConfig(name="report_test", items=[])
        items = [
            BatchItemResult(
                item=BatchTaskItem(task_name="ok_task", label="ok"),
                result=ExecutionResult(success=True, completed_steps=3, duration=2.5),
                started_at=datetime.now(),
                finished_at=datetime.now() + timedelta(seconds=2),
            ),
            BatchItemResult(
                item=BatchTaskItem(task_name="fail_task", label="fail"),
                result=ExecutionResult(
                    success=False,
                    completed_steps=1,
                    duration=0.5,
                    error="Something went wrong",
                ),
                started_at=datetime.now(),
                finished_at=datetime.now() + timedelta(seconds=1),
            ),
        ]
        result = BatchTaskResult(
            config=cfg,
            items=items,
            started_at=datetime.now(),
            finished_at=datetime.now() + timedelta(seconds=3),
        )
        return BatchReportGenerator(result)

    def test_markdown_output(self):
        gen = self._make_generator()
        md = gen.generate(ReportFormat.MARKDOWN)
        self.assertIn("report_test", md)
        self.assertIn("ok", md)
        self.assertIn("fail", md)
        self.assertIn("Something went wrong", md)

    def test_json_output(self):
        gen = self._make_generator()
        text = gen.generate(ReportFormat.JSON)
        data = json.loads(text)
        self.assertEqual(data["config_name"], "report_test")
        self.assertEqual(data["total"], 2)

    def test_html_output(self):
        gen = self._make_generator()
        html = gen.generate(ReportFormat.HTML)
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("report_test", html)
        self.assertIn("success", html)
        self.assertIn("fail", html)

    def test_save(self):
        gen = self._make_generator()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = gen.save(os.path.join(tmpdir, "report.md"))
            self.assertTrue(os.path.exists(path))
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("report_test", content)


if __name__ == "__main__":
    unittest.main()
