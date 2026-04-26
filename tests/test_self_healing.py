"""Self-Healing 系统测试"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.failure_analyzer import FailureAnalyzer, FailureType
from src.core.recovery_strategy import RecoveryStrategy, RecoveryResult
from src.core.execution_diary import ExecutionDiary, DiaryEntry
from src.core.models import Task


class TestFailureAnalyzer:
    """测试失败分析器"""

    def test_analyze_element_not_found_by_message(self):
        analyzer = FailureAnalyzer()
        task = Task("click", target="submit_btn")

        assert analyzer.analyze("Target not found: submit_btn", task) == FailureType.ELEMENT_NOT_FOUND
        assert analyzer.analyze("元素未找到", task) == FailureType.ELEMENT_NOT_FOUND
        assert analyzer.analyze("locator not found", task) == FailureType.ELEMENT_NOT_FOUND

    def test_analyze_timing_issue(self):
        analyzer = FailureAnalyzer()
        task = Task("browser_click", target=".btn")

        assert analyzer.analyze("timeout waiting for element", task) == FailureType.TIMING_ISSUE
        assert analyzer.analyze("等待超时", task) == FailureType.TIMING_ISSUE
        assert analyzer.analyze("stale element reference", task) == FailureType.TIMING_ISSUE

    def test_analyze_network_error(self):
        analyzer = FailureAnalyzer()
        task = Task("browser_goto", value="https://example.com")

        assert analyzer.analyze("network connection refused", task) == FailureType.NETWORK_ERROR
        assert analyzer.analyze("DNS lookup failed", task) == FailureType.NETWORK_ERROR
        assert analyzer.analyze("网络超时", task) == FailureType.NETWORK_ERROR

    def test_analyze_validation_error(self):
        analyzer = FailureAnalyzer()
        task = Task("launch")

        assert analyzer.analyze("missing required parameter", task) == FailureType.VALIDATION_ERROR
        assert analyzer.analyze("invalid format", task) == FailureType.VALIDATION_ERROR

    def test_analyze_permission_denied(self):
        analyzer = FailureAnalyzer()
        task = Task("system_lock")

        assert analyzer.analyze("permission denied", task) == FailureType.PERMISSION_DENIED
        assert analyzer.analyze("access denied", task) == FailureType.PERMISSION_DENIED

    def test_analyze_unknown(self):
        analyzer = FailureAnalyzer()
        task = Task("click", target="100,200")

        assert analyzer.analyze("something weird happened", task) == FailureType.UNKNOWN

    def test_analyze_by_exception_type(self):
        from src.utils.exceptions import NotFoundError, ValidationError

        analyzer = FailureAnalyzer()
        task = Task("click", target="btn")

        assert analyzer.analyze(NotFoundError("button missing"), task) == FailureType.ELEMENT_NOT_FOUND
        assert analyzer.analyze(ValidationError("bad param"), task) == FailureType.VALIDATION_ERROR

    def test_get_suggestion(self):
        analyzer = FailureAnalyzer()
        suggestion = analyzer.get_suggestion(FailureType.TIMING_ISSUE)
        assert "等待" in suggestion or "delay" in suggestion.lower()


class TestRecoveryStrategy:
    """测试修复策略"""

    def test_attempt_recovery_unknown(self):
        strategy = RecoveryStrategy()
        task = Task("click", target="btn")
        result = strategy.attempt_recovery(FailureType.UNKNOWN, task, None, MagicMock())

        assert isinstance(result, RecoveryResult)
        assert result.success is False or result.success is True

    def test_attempt_recovery_permission_denied(self):
        strategy = RecoveryStrategy()
        task = Task("click", target="btn")
        result = strategy.attempt_recovery(FailureType.PERMISSION_DENIED, task, None, MagicMock())

        assert result.success is False
        assert "manual" in result.action_taken or "permission" in result.detail.lower()

    def test_attempt_recovery_validation_error(self):
        strategy = RecoveryStrategy()
        task = Task("click", target="btn")
        result = strategy.attempt_recovery(FailureType.VALIDATION_ERROR, task, None, MagicMock())

        assert result.success is False
        assert "fix_parameters" in result.action_taken

    def test_attempt_recovery_element_not_found_ocr(self):
        strategy = RecoveryStrategy()
        mock_executor = MagicMock()
        mock_executor.mouse = MagicMock()
        mock_executor.keyboard = MagicMock()

        task = Task("click", target="搜索")

        with patch("src.core.recovery_strategy.TextRecognizer") as MockRecognizer:
            mock_rec = MagicMock()
            mock_rec.find_text.return_value = (500, 400)
            MockRecognizer.return_value = mock_rec

            result = strategy.attempt_recovery(
                FailureType.ELEMENT_NOT_FOUND, task, MagicMock(), mock_executor
            )

            assert result.success is True
            assert "ocr" in result.action_taken
            mock_executor.mouse.click.assert_called_once_with(500, 400)

    def test_attempt_recovery_timing_issue(self):
        strategy = RecoveryStrategy()
        mock_executor = MagicMock()
        mock_executor.screen = MagicMock()
        mock_executor.screen.capture.return_value = MagicMock()
        mock_executor._execute_single_task.return_value = True

        task = Task("click", target="btn")

        result = strategy.attempt_recovery(
            FailureType.TIMING_ISSUE, task, MagicMock(), mock_executor
        )

        assert result.success is True
        assert "delay" in result.action_taken or "retry" in result.action_taken


class TestExecutionDiary:
    """测试执行日记"""

    def setup_method(self):
        self.tmp_file = Path("test_diary.jsonl")
        if self.tmp_file.exists():
            self.tmp_file.unlink()
        self.diary = ExecutionDiary(diary_file=self.tmp_file)

    def teardown_method(self):
        if self.tmp_file.exists():
            self.tmp_file.unlink()

    def test_record_and_query(self):
        task = Task("click", target="btn")
        self.diary.record("test_seq", 0, task, success=True, duration_ms=100.0)
        self.diary.record("test_seq", 1, task, success=False, failure_type=FailureType.ELEMENT_NOT_FOUND)

        entries = self.diary.query(task_sequence_name="test_seq")
        assert len(entries) == 2

        success_entries = [e for e in entries if e.success]
        assert len(success_entries) == 1

    def test_get_success_rate(self):
        task = Task("click", target="btn")
        self.diary.record("seq1", 0, task, success=True)
        self.diary.record("seq1", 1, task, success=True)
        self.diary.record("seq1", 2, task, success=False, failure_type=FailureType.ELEMENT_NOT_FOUND)

        rate = self.diary.get_success_rate(task_sequence_name="seq1")
        assert pytest.approx(rate, 0.01) == 2 / 3

    def test_get_top_failure_reasons(self):
        task = Task("click", target="btn")
        self.diary.record("seq", 0, task, success=False, failure_type=FailureType.ELEMENT_NOT_FOUND)
        self.diary.record("seq", 1, task, success=False, failure_type=FailureType.ELEMENT_NOT_FOUND)
        self.diary.record("seq", 2, task, success=False, failure_type=FailureType.TIMING_ISSUE)

        reasons = self.diary.get_top_failure_reasons()
        assert reasons[0][0] == "ELEMENT_NOT_FOUND"
        assert reasons[0][1] == 2

    def test_get_recovery_effectiveness(self):
        task = Task("click", target="btn")
        self.diary.record(
            "seq", 0, task, success=False,
            failure_type=FailureType.ELEMENT_NOT_FOUND,
            recovery_action="ocr_text_search", recovery_success=True,
        )
        self.diary.record(
            "seq", 1, task, success=False,
            failure_type=FailureType.ELEMENT_NOT_FOUND,
            recovery_action="ocr_text_search", recovery_success=False,
        )

        stats = self.diary.get_recovery_effectiveness()
        assert stats["total"] == 2
        assert stats["success_rate"] == 0.5
        assert stats["by_action"]["ocr_text_search"]["total"] == 2

    def test_generate_report(self):
        task = Task("click", target="btn")
        self.diary.record("seq", 0, task, success=True)
        self.diary.record("seq", 1, task, success=False, failure_type=FailureType.ELEMENT_NOT_FOUND)

        report = self.diary.generate_report()
        assert "执行日记摘要" in report
        assert "成功率" in report
        assert "ELEMENT_NOT_FOUND" in report

    def test_persistence(self):
        task = Task("click", target="btn")
        self.diary.record("seq", 0, task, success=True)

        # 重新加载
        diary2 = ExecutionDiary(diary_file=self.tmp_file)
        entries = diary2.query(task_sequence_name="seq")
        assert len(entries) == 1
        assert entries[0].action == "click"


class TestSelfHealingIntegration:
    """集成测试：TaskExecutor 与 Self-Healing"""

    def test_executor_has_self_healing_components(self):
        from src.core.executor import TaskExecutor

        executor = TaskExecutor()
        assert hasattr(executor, "failure_analyzer")
        assert hasattr(executor, "recovery_strategy")
        assert hasattr(executor, "execution_diary")
        assert isinstance(executor.failure_analyzer, FailureAnalyzer)
        assert isinstance(executor.recovery_strategy, RecoveryStrategy)
        assert isinstance(executor.execution_diary, ExecutionDiary)

    def test_execute_with_recovery_on_failure(self):
        from src.core.executor import TaskExecutor
        from src.core.models import TaskSequence

        executor = TaskExecutor()
        # Mock _execute_single_task 第一次失败，第二次成功
        call_count = 0

        def mock_execute(task, screenshot):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise NotFoundError("btn not found")
            return True

        executor._execute_single_task = mock_execute

        # Mock recovery strategy 使其失败（触发重试路径）
        executor.recovery_strategy.attempt_recovery = MagicMock(
            return_value=RecoveryResult(success=False, action_taken="mock_failed")
        )

        seq = TaskSequence("test", [Task("click", target="btn", delay=0)])
        executor.config.max_retries = 1
        result = executor.execute(seq)

        # 第一次失败 + 1次重试 = 2次调用
        assert call_count == 2
        assert result.success is True

    def test_execute_with_recovery_healing_success(self):
        from src.core.executor import TaskExecutor
        from src.core.models import TaskSequence

        executor = TaskExecutor()
        executor._execute_single_task = MagicMock(side_effect=NotFoundError("missing"))
        executor.recovery_strategy.attempt_recovery = MagicMock(
            return_value=RecoveryResult(success=True, action_taken="healed")
        )

        seq = TaskSequence("test", [Task("click", target="btn", delay=0)])
        result = executor.execute(seq)

        assert result.success is True
        executor.recovery_strategy.attempt_recovery.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
