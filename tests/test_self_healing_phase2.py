"""Self-Healing Phase 2 测试 —— 三层模型 + Skill 沉淀"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.skill_manager import SkillManager, SkillEntry
from src.core.model_tier_manager import ModelTierManager, TierResult
from src.core.visual_diagnostician import (
    VisualContextBuilder,
    VisualDiagnostician,
    DiagnosisReport,
)
from src.core.failure_analyzer import FailureType
from src.core.models import Task


class TestSkillManager:
    """测试 Skill 增量管理器"""

    def setup_method(self):
        self.tmp_file = Path("test_skills.jsonl")
        if self.tmp_file.exists():
            self.tmp_file.unlink()
        self.manager = SkillManager(skill_file=self.tmp_file)

    def teardown_method(self):
        if self.tmp_file.exists():
            self.tmp_file.unlink()
        md_file = Path("skills/self_healing_skills.md")
        if md_file.exists():
            md_file.unlink()

    def test_add_and_find_skill(self):
        self.manager.add_skill(
            failure_type="ELEMENT_NOT_FOUND",
            task_action="click",
            original_target="搜索按钮",
            semantic_equivalents=["搜索", "Search"],
            successful_strategy="ocr_text_search",
            successful_target="搜索",
            successful_center=[500, 300],
            screen_context_hash="abc123",
            recovery_success=True,
            vlm_diagnosis="通过 OCR 找到文字",
            created_by_tier="minimax",
        )
        skill = self.manager.find_matching_skill(
            failure_type="ELEMENT_NOT_FOUND",
            task_action="click",
            original_target="搜索按钮",
        )
        assert skill is not None
        assert skill.successful_center == [500, 300]
        assert skill.hit_count == 1

    def test_persistence(self):
        self.manager.add_skill(
            failure_type="ELEMENT_NOT_FOUND",
            task_action="click",
            original_target="btn",
            semantic_equivalents=[],
            successful_strategy="yolo_match",
            successful_target="btn",
            successful_center=[100, 200],
            screen_context_hash="hash1",
            recovery_success=True,
            vlm_diagnosis="ok",
            created_by_tier="gpt5",
        )
        manager2 = SkillManager(skill_file=self.tmp_file)
        skill = manager2.find_matching_skill(
            failure_type="ELEMENT_NOT_FOUND",
            task_action="click",
            original_target="btn",
        )
        assert skill is not None
        assert skill.created_by_tier == "gpt5"

    def test_generate_md(self):
        self.manager.add_skill(
            failure_type="ELEMENT_NOT_FOUND",
            task_action="click",
            original_target="提交",
            semantic_equivalents=["Submit"],
            successful_strategy="ocr_text_search",
            successful_target="提交",
            successful_center=[800, 600],
            screen_context_hash="h1",
            recovery_success=True,
            vlm_diagnosis="ok",
            created_by_tier="mimo",
        )
        md = self.manager.generate_skill_md("test_skills.md")
        assert "Self-Healing Skill Library" in md
        assert "提交" in md
        assert "mimo" in md


class TestVisualContextBuilder:
    """测试视觉上下文构建器"""

    def test_rank_by_semantic_relevance(self):
        builder = VisualContextBuilder()
        candidates = [
            {"type": "ocr", "text": "搜索", "element_type": "text", "confidence": 0.9, "center": [100, 100]},
            {"type": "ocr", "text": "设置", "element_type": "text", "confidence": 0.8, "center": [200, 200]},
            {"type": "yolo", "text": "", "element_type": "button", "confidence": 0.7, "center": [300, 300]},
        ]
        ranked = builder._rank_by_semantic_relevance("搜索", candidates)
        assert ranked[0]["text"] == "搜索"


class TestModelTierManager:
    """测试三层模型管理器"""

    def test_tier_fallback_minimax_success(self):
        mock_minimax = MagicMock()
        mock_minimax.diagnose_failure.return_value = json.dumps({
            "root_cause": "元素偏移",
            "confidence": 0.9,
            "target_presence": "found_similar",
            "suggested_target": {"type": "coordinate", "value": "", "center": [500, 400]},
            "suggested_action": "click",
            "reasoning": "test",
            "fallback_strategy": "",
            "semantic_equivalents": ["搜索"],
        })

        manager = ModelTierManager(minimax_client=mock_minimax)
        result = manager.diagnose_with_fallback(
            failure_type="ELEMENT_NOT_FOUND",
            task_action="click",
            original_target="btn",
            screenshot=MagicMock(),
            annotated_screenshot=None,
            system_prompt="test",
            instruction="test",
        )
        assert result.tier == "minimax"
        assert result.success is True

    def test_tier_fallback_minimax_fails_mimo_takes_over(self):
        mock_minimax = MagicMock()
        # Minimax 返回不理想（confidence 低）
        mock_minimax.diagnose_failure.return_value = json.dumps({
            "root_cause": "未知",
            "confidence": 0.3,
            "target_presence": "unknown",
        })

        mock_mimo = MagicMock()
        mock_mimo.diagnose_failure.return_value = json.dumps({
            "root_cause": "弹窗遮挡",
            "confidence": 0.92,
            "target_presence": "obscured",
            "suggested_target": {"type": "coordinate", "value": "", "center": [500, 400]},
            "suggested_action": "click",
            "reasoning": "test",
            "fallback_strategy": "",
            "semantic_equivalents": [],
        })

        manager = ModelTierManager(minimax_client=mock_minimax, mimo_client=mock_mimo)
        result = manager.diagnose_with_fallback(
            failure_type="ELEMENT_NOT_FOUND",
            task_action="click",
            original_target="btn",
            screenshot=MagicMock(),
            annotated_screenshot=None,
            system_prompt="test",
            instruction="test",
        )
        assert result.tier == "mimo"
        assert result.success is True

    def test_distill_skill(self):
        mock_minimax = MagicMock()
        manager = ModelTierManager(minimax_client=mock_minimax)
        entry = manager.distill_skill(
            tier="gpt5",
            failure_type="ELEMENT_NOT_FOUND",
            task_action="click",
            original_target="btn",
            successful_strategy="ocr_text_search",
            successful_target="搜索",
            successful_center=[100, 200],
            screen_context_hash="hash",
            vlm_diagnosis="通过 OCR 找到",
            semantic_equivalents=["搜索", "Search"],
        )
        assert entry.created_by_tier == "gpt5"
        assert "搜索" in entry.semantic_equivalents


class TestVisualDiagnostician:
    """测试视觉诊断器"""

    def test_parse_diagnosis_valid_json(self):
        diag = VisualDiagnostician()
        text = json.dumps({
            "root_cause": "弹窗遮挡",
            "confidence": 0.9,
            "target_presence": "obscured",
            "suggested_target": {"type": "coordinate", "center": [100, 200]},
            "suggested_action": "click",
            "reasoning": "test",
            "fallback_strategy": "esc",
            "semantic_equivalents": ["搜索"],
        })
        report = diag._parse_diagnosis(text, "minimax")
        assert report.root_cause == "弹窗遮挡"
        assert report.confidence == 0.9
        assert report.tier_used == "minimax"

    def test_parse_diagnosis_invalid(self):
        diag = VisualDiagnostician()
        report = diag._parse_diagnosis("not json", "minimax")
        assert report.confidence == 0.0
        assert report.target_presence == "unknown"


class TestRecoveryStrategyPhase2:
    """测试 RecoveryStrategy 的 Phase 2 集成"""

    def test_skill_recovery_hit(self):
        from src.core.recovery_strategy import RecoveryStrategy

        mock_skill_mgr = MagicMock()
        mock_skill = MagicMock()
        mock_skill.successful_strategy = "ocr_text_search"
        mock_skill.successful_center = [500, 400]
        mock_skill.id = "skill_1"
        mock_skill_mgr.find_matching_skill.return_value = mock_skill

        strategy = RecoveryStrategy(skill_manager=mock_skill_mgr)
        mock_executor = MagicMock()
        task = Task("click", target="搜索")

        result = strategy._try_skill_recovery(
            FailureType.ELEMENT_NOT_FOUND, task, None, mock_executor
        )
        assert result is not None
        assert result.success is True
        assert "skill" in result.action_taken

    def test_skill_recovery_miss(self):
        from src.core.recovery_strategy import RecoveryStrategy

        mock_skill_mgr = MagicMock()
        mock_skill_mgr.find_matching_skill.return_value = None

        strategy = RecoveryStrategy(skill_manager=mock_skill_mgr)
        task = Task("click", target="不存在")

        result = strategy._try_skill_recovery(
            FailureType.ELEMENT_NOT_FOUND, task, None, MagicMock()
        )
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
