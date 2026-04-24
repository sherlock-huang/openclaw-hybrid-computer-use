"""异常体系单元测试"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.exceptions import (
    ClawDesktopError,
    ConfigError,
    ValidationError,
    ResourceError,
    ExecutionError,
    BrowserError,
    DesktopError,
    WeChatError,
    OfficeError,
    TaskExecutionError,
    PerceptionError,
    ScreenCaptureError,
    DetectionError,
    OCRError,
    TemplateMatchError,
    PluginError,
    NotFoundError,
)


class TestExceptionHierarchy(unittest.TestCase):
    """验证异常继承层次"""

    def test_all_inherit_from_claw_desktop_error(self):
        exceptions = [
            ConfigError("msg"),
            ValidationError("msg"),
            ResourceError("msg"),
            ExecutionError("msg"),
            BrowserError("msg"),
            DesktopError("msg"),
            WeChatError("msg"),
            OfficeError("msg"),
            TaskExecutionError("msg"),
            PerceptionError("msg"),
            ScreenCaptureError("msg"),
            DetectionError("msg"),
            OCRError("msg"),
            TemplateMatchError("msg"),
            PluginError("msg"),
            NotFoundError("msg"),
        ]
        for exc in exceptions:
            self.assertIsInstance(exc, ClawDesktopError)

    def test_execution_subclasses(self):
        self.assertIsInstance(BrowserError("x"), ExecutionError)
        self.assertIsInstance(DesktopError("x"), ExecutionError)
        self.assertIsInstance(WeChatError("x"), ExecutionError)
        self.assertIsInstance(OfficeError("x"), ExecutionError)
        self.assertIsInstance(TaskExecutionError("x"), ExecutionError)

    def test_perception_subclasses(self):
        self.assertIsInstance(ScreenCaptureError("x"), PerceptionError)
        self.assertIsInstance(DetectionError("x"), PerceptionError)
        self.assertIsInstance(OCRError("x"), PerceptionError)
        self.assertIsInstance(TemplateMatchError("x"), PerceptionError)

    def test_catch_base_class(self):
        """用基类可以捕获所有子类异常"""
        caught = []
        for exc_cls in [ValidationError, BrowserError, NotFoundError]:
            try:
                raise exc_cls("test")
            except ClawDesktopError as e:
                caught.append(type(e).__name__)
        self.assertEqual(len(caught), 3)

    def test_message_and_details(self):
        exc = ValidationError("bad param", details={"field": "name"})
        self.assertEqual(exc.message, "bad param")
        self.assertEqual(exc.details, {"field": "name"})
        self.assertIn("bad param", str(exc))

    def test_task_execution_error_context(self):
        exc = TaskExecutionError(
            "failed",
            task_name="demo",
            task_action="click",
            task_index=2,
            details={"retry": 1},
        )
        self.assertEqual(exc.task_name, "demo")
        self.assertEqual(exc.task_action, "click")
        self.assertEqual(exc.task_index, 2)
        self.assertEqual(exc.details, {"retry": 1})


if __name__ == "__main__":
    unittest.main()
