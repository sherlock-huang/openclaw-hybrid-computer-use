"""Self-Healing 量化验证脚本测试"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from scripts.validate_self_healing_quantitative import (
    ValidationMetrics,
    ScenarioResult,
    infer_tier,
    create_mock_executor,
    run_all_scenarios,
    SCENARIO_FUNCTIONS,
)
from src.core.failure_analyzer import FailureType
from src.core.recovery_strategy import RecoveryStrategy, RecoveryResult
from src.core.models import Task


class TestInferTier:
    """测试层级推断函数"""

    def test_skill_tier(self):
        assert infer_tier("skill:ocr_text_search") == "skill"
        assert infer_tier("skill:coordinate_offset") == "skill"

    def test_vlm_tier(self):
        assert infer_tier("vlm:coordinate") == "vlm"
        assert infer_tier("vlm_diagnosis_failed") == "vlm"

    def test_human_tier(self):
        assert infer_tier("human_skip") == "human"
        assert infer_tier("human_continue") == "human"

    def test_traditional_tier(self):
        assert infer_tier("ocr_text_search") == "traditional"
        assert infer_tier("delay_and_retry") == "traditional"
        assert infer_tier("generic_retry") == "traditional"

    def test_none_tier(self):
        assert infer_tier("all_methods_exhausted") == "none"
        assert infer_tier("fix_parameters") == "none"
        assert infer_tier("exception") == "none"


class TestCreateMockExecutor:
    """测试 mock executor 构造"""

    def test_has_required_attributes(self):
        executor = create_mock_executor()
        assert hasattr(executor, "mouse")
        assert hasattr(executor, "keyboard")
        assert hasattr(executor, "screen")
        assert hasattr(executor, "detector")
        assert hasattr(executor, "browser_handler")

    def test_screenshot_return_value(self):
        import numpy as np
        executor = create_mock_executor()
        img = executor.screen.capture()
        assert img.shape == (1080, 1920, 3)
        assert img.dtype == np.uint8


class TestValidationMetrics:
    """测试指标聚合器"""

    def test_add_and_count(self):
        metrics = ValidationMetrics()
        metrics.add(ScenarioResult("s1", "ELEMENT_NOT_FOUND", True, "ocr", "traditional", 100.0))
        metrics.add(ScenarioResult("s2", "ELEMENT_NOT_FOUND", False, "failed", "none", 50.0))

        assert metrics.total_scenarios == 2
        assert metrics.total_successes == 1

    def test_by_tier_aggregation(self):
        metrics = ValidationMetrics()
        metrics.add(ScenarioResult("s1", "A", True, "skill:hit", "skill", 10.0))
        metrics.add(ScenarioResult("s2", "A", True, "ocr", "traditional", 20.0))
        metrics.add(ScenarioResult("s3", "A", False, "fail", "none", 30.0))

        assert metrics.by_tier["skill"]["total"] == 1
        assert metrics.by_tier["skill"]["success"] == 1
        assert metrics.by_tier["traditional"]["total"] == 1
        assert metrics.by_tier["none"]["total"] == 1

    def test_skill_hit_rate(self):
        metrics = ValidationMetrics()
        metrics.add(ScenarioResult("s1", "A", True, "skill:hit", "skill", 10.0))
        metrics.add(ScenarioResult("s2", "A", True, "skill:hit2", "skill", 10.0))
        metrics.finalize()

        assert metrics.skill_attempts == 2
        assert metrics.skill_hits == 2
        assert metrics.skill_hit_rate == 1.0

    def test_finalize_success_rate(self):
        metrics = ValidationMetrics()
        metrics.add(ScenarioResult("s1", "A", True, "a", "traditional", 10.0))
        metrics.add(ScenarioResult("s2", "A", False, "b", "none", 10.0))
        metrics.finalize()

        assert metrics.overall_success_rate == 0.5

    def test_baseline_comparison(self):
        metrics = ValidationMetrics()
        # 构造足够数据使 overall 达到基线
        for _ in range(6):
            metrics.add(ScenarioResult("s", "A", True, "a", "traditional", 10.0))
        for _ in range(4):
            metrics.add(ScenarioResult("s", "A", False, "b", "none", 10.0))
        metrics.finalize()

        assert metrics.baseline_comparison["overall_success_rate"]["status"] == "PASS"

    def test_to_dict_serializable(self):
        metrics = ValidationMetrics()
        metrics.add(ScenarioResult("s1", "A", True, "a", "traditional", 10.0))
        metrics.finalize()

        data = metrics.to_dict()
        # 应能 JSON 序列化
        json_str = json.dumps(data)
        assert len(json_str) > 0
        parsed = json.loads(json_str)
        assert parsed["total_scenarios"] == 1

    def test_generate_markdown_contains_sections(self):
        metrics = ValidationMetrics()
        metrics.add(ScenarioResult("s1", "A", True, "a", "traditional", 10.0))
        metrics.finalize()

        md = metrics.generate_markdown()
        assert "# Self-Healing" in md
        assert "总体指标" in md
        assert "基线对比" in md
        assert "分层分布" in md
        assert "场景明细" in md


class TestScenarioFunctions:
    """测试各预设场景"""

    def test_skill_hit_returns_success(self):
        from scripts.validate_self_healing_quantitative import run_scenario_skill_hit
        result = run_scenario_skill_hit()
        assert result.success is True
        assert result.tier == "skill"

    def test_ocr_success_returns_success(self):
        from scripts.validate_self_healing_quantitative import run_scenario_ocr_success
        result = run_scenario_ocr_success()
        assert result.success is True
        assert result.tier == "traditional"
        assert "ocr" in result.action_taken

    def test_timing_success_returns_success(self):
        from scripts.validate_self_healing_quantitative import run_scenario_timing_success
        result = run_scenario_timing_success()
        assert result.success is True
        assert result.tier == "traditional"

    def test_ui_changed_success_returns_success(self):
        from scripts.validate_self_healing_quantitative import run_scenario_ui_changed_success
        result = run_scenario_ui_changed_success()
        assert result.success is True
        assert result.tier == "traditional"
        assert "yolo" in result.action_taken

    def test_vlm_success_returns_success(self):
        from scripts.validate_self_healing_quantitative import run_scenario_vlm_success
        result = run_scenario_vlm_success()
        assert result.success is True
        assert result.tier == "vlm"

    def test_vlm_fallback_returns_failure(self):
        from scripts.validate_self_healing_quantitative import run_scenario_vlm_fallback
        result = run_scenario_vlm_fallback()
        assert result.success is False

    def test_human_skip_returns_success(self):
        from scripts.validate_self_healing_quantitative import run_scenario_human_skip
        result = run_scenario_human_skip()
        assert result.success is True
        assert result.tier == "human"

    def test_permission_denied_returns_failure(self):
        from scripts.validate_self_healing_quantitative import run_scenario_permission_denied
        result = run_scenario_permission_denied()
        assert result.success is False
        assert result.tier == "none"

    def test_validation_error_returns_failure(self):
        from scripts.validate_self_healing_quantitative import run_scenario_validation_error
        result = run_scenario_validation_error()
        assert result.success is False
        assert result.tier == "none"

    def test_unknown_success_returns_success(self):
        from scripts.validate_self_healing_quantitative import run_scenario_unknown_success
        result = run_scenario_unknown_success()
        assert result.success is True
        assert result.tier == "traditional"

    def test_network_success_returns_success(self):
        from scripts.validate_self_healing_quantitative import run_scenario_network_success
        result = run_scenario_network_success()
        assert result.success is True
        assert result.tier == "traditional"


class TestRunAllScenarios:
    """测试完整运行"""

    def test_runs_all_scenarios(self):
        metrics = run_all_scenarios()
        assert metrics.total_scenarios == len(SCENARIO_FUNCTIONS)
        assert metrics.total_successes >= 0
        assert metrics.total_successes <= metrics.total_scenarios

    def test_generates_valid_metrics(self):
        metrics = run_all_scenarios()
        metrics.finalize()
        data = metrics.to_dict()

        assert "overall_success_rate" in data
        assert "by_tier" in data
        assert "by_failure_type" in data
        assert "baseline_comparison" in data
        assert "results" in data
        assert len(data["results"]) == len(SCENARIO_FUNCTIONS)


class TestMainOutput:
    """测试主函数输出"""

    def test_outputs_json_and_md(self, tmp_path):
        from scripts.validate_self_healing_quantitative import main
        import os

        # 临时切换工作目录以避免污染项目根目录
        original_cwd = os.getcwd()
        os.chdir(str(tmp_path))
        try:
            # main 使用 reports/ 目录
            exit_code = main()

            assert (tmp_path / "reports" / "self_healing_metrics.json").exists()
            assert (tmp_path / "reports" / "self_healing_metrics.md").exists()

            # JSON 应可解析
            json_data = json.loads(
                (tmp_path / "reports" / "self_healing_metrics.json").read_text(encoding="utf-8")
            )
            assert json_data["total_scenarios"] == len(SCENARIO_FUNCTIONS)
        finally:
            os.chdir(original_cwd)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
