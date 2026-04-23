"""TaskLearningEngine 单元测试"""

import pytest
from unittest.mock import MagicMock, patch

from src.core.models import RecordingEvent, RecordingSession, RecordingMode
from src.core.task_learner import TaskLearner, TaskPattern
from src.core.task_learning_engine import (
    CoordinateAdapter,
    PatternExtractor,
    TaskRecommender,
    TaskLearningEngine,
)


def _isolated_learner() -> TaskLearner:
    """创建一个不加载/保存文件的隔离 TaskLearner"""
    import tempfile
    from pathlib import Path
    learner = TaskLearner.__new__(TaskLearner)
    learner.patterns = {}
    learner.LEARN_FILE = Path(tempfile.mktemp(suffix=".json"))
    return learner


# ============================================================================
# CoordinateAdapter
# ============================================================================
class TestCoordinateAdapter:
    def test_adapt_event_browser_mode(self):
        """浏览器模式：保留原始坐标"""
        adapter = CoordinateAdapter()
        event = RecordingEvent(
            action="browser_click",
            timestamp=0,
            position=(100, 200),
            css_selector="#btn",
        )
        result = adapter.adapt_event(event, screenshot=None, window_rect=None)
        assert result == (100, 200)

    def test_adapt_event_window_scale(self):
        """窗口内坐标直接返回"""
        adapter = CoordinateAdapter()
        event = RecordingEvent(
            action="click",
            timestamp=0,
            position=(150, 250),
        )
        result = adapter.adapt_event(event, screenshot=None, window_rect=(100, 200, 500, 400))
        assert result == (150, 250)

    def test_adapt_event_no_window_rect(self):
        """无窗口矩形但有截图尺寸时，在范围内直接返回"""
        adapter = CoordinateAdapter()
        event = RecordingEvent(
            action="click",
            timestamp=0,
            position=(100, 100),
        )
        fake_screenshot = MagicMock()
        fake_screenshot.shape = (1080, 1920, 3)
        result = adapter.adapt_event(event, screenshot=fake_screenshot, window_rect=None)
        assert result == (100, 100)

    def test_adapt_event_outside_screen(self):
        """超出屏幕范围时返回 None"""
        adapter = CoordinateAdapter()
        event = RecordingEvent(
            action="click",
            timestamp=0,
            position=(9999, 9999),
        )
        fake_screenshot = MagicMock()
        fake_screenshot.shape = (1080, 1920, 3)
        result = adapter.adapt_event(event, screenshot=fake_screenshot, window_rect=None)
        assert result is None

    @patch("src.core.task_learning_engine.TaskSequence")
    def test_adapt_recording(self, mock_seq_cls):
        """将整个录制适配为任务序列"""
        adapter = CoordinateAdapter()
        session = RecordingSession(
            name="test_recording",
            start_time=MagicMock(),
            events=[
                RecordingEvent(action="click", timestamp=0, position=(100, 200)),
                RecordingEvent(action="type", timestamp=1, position=(100, 200), value="hello"),
            ],
        )
        fake_screenshot = MagicMock()
        fake_screenshot.shape = (1080, 1920, 3)

        # 创建 mock TaskSequence 实例
        mock_seq = MagicMock()
        mock_seq_cls.return_value = mock_seq

        result = adapter.adapt_recording(session, fake_screenshot)
        assert mock_seq_cls.called
        _, kwargs = mock_seq_cls.call_args
        assert kwargs["name"] == "test_recording"
        assert len(kwargs["tasks"]) == 2
        assert kwargs["tasks"][0].action == "click"
        assert kwargs["tasks"][0].target == "100,200"
        assert kwargs["tasks"][1].value == "hello"


# ============================================================================
# PatternExtractor
# ============================================================================
class TestPatternExtractor:
    def test_lcs_two(self):
        """两序列 LCS"""
        extractor = PatternExtractor()
        a = ["click", "type", "click", "press"]
        b = ["click", "click", "press"]
        result = extractor._lcs_two(a, b)
        assert result == ["click", "click", "press"]

    def test_lcs_multiple(self):
        """多序列 LCS"""
        extractor = PatternExtractor()
        seqs = [
            ["open", "click", "type", "click", "save"],
            ["open", "click", "click", "save"],
            ["open", "click", "type", "save"],
        ]
        result = extractor._lcs_multiple(seqs)
        assert result == ["open", "click", "save"]

    def test_extract_common_pattern(self):
        """从录制中提取通用模式"""
        extractor = PatternExtractor()
        sessions = [
            RecordingSession(
                name="r1",
                start_time=MagicMock(),
                events=[
                    RecordingEvent(action="open", timestamp=0),
                    RecordingEvent(action="click", timestamp=1),
                    RecordingEvent(action="type", timestamp=2),
                    RecordingEvent(action="save", timestamp=3),
                ],
            ),
            RecordingSession(
                name="r2",
                start_time=MagicMock(),
                events=[
                    RecordingEvent(action="open", timestamp=0),
                    RecordingEvent(action="click", timestamp=1),
                    RecordingEvent(action="click", timestamp=2),
                    RecordingEvent(action="save", timestamp=3),
                ],
            ),
        ]
        pattern = extractor.extract_common_pattern(sessions)
        assert pattern is not None
        assert pattern["actions"] == ["open", "click", "save"]
        assert pattern["source_count"] == 2
        assert 0 < pattern["coverage"] <= 1

    def test_extract_common_pattern_single(self):
        """单个录制不提取"""
        extractor = PatternExtractor()
        sessions = [
            RecordingSession(
                name="r1",
                start_time=MagicMock(),
                events=[RecordingEvent(action="click", timestamp=0)],
            ),
        ]
        pattern = extractor.extract_common_pattern(sessions)
        assert pattern is None

    def test_find_similar_recordings(self):
        """查找相似录制"""
        extractor = PatternExtractor()
        target = RecordingSession(
            name="target",
            start_time=MagicMock(),
            events=[
                RecordingEvent(action="open", timestamp=0),
                RecordingEvent(action="click", timestamp=1),
                RecordingEvent(action="save", timestamp=2),
            ],
        )
        candidates = [
            target,
            RecordingSession(
                name="similar",
                start_time=MagicMock(),
                events=[
                    RecordingEvent(action="open", timestamp=0),
                    RecordingEvent(action="click", timestamp=1),
                    RecordingEvent(action="save", timestamp=2),
                ],
            ),
            RecordingSession(
                name="different",
                start_time=MagicMock(),
                events=[
                    RecordingEvent(action="click", timestamp=0),
                    RecordingEvent(action="scroll", timestamp=1),
                ],
            ),
        ]
        similar = extractor.find_similar_recordings(target, candidates)
        assert len(similar) == 1
        assert similar[0].name == "similar"


# ============================================================================
# TaskRecommender
# ============================================================================
class TestTaskRecommender:
    def test_recommend_by_window(self):
        """基于窗口标题推荐"""
        learner = _isolated_learner()
        # 手动注入模式
        learner.patterns["wechat:send_msg"] = TaskPattern(
            task_type="wechat_send",
            target_signature="send_msg",
            actions=[{"action": "click"}],
            success_count=9,
            fail_count=1,
        )
        recommender = TaskRecommender(learner)
        # 窗口标题包含 task_type 关键词
        recs = recommender.recommend_by_window("wechat_send - 聊天窗口")
        assert len(recs) == 1
        assert recs[0]["task_type"] == "wechat_send"
        assert recs[0]["success_rate"] == 0.9

    def test_recommend_by_window_no_match(self):
        """无匹配时返回空"""
        learner = _isolated_learner()
        # 注入一个低成功率模式，确保评分不足以被推荐
        learner.patterns["other:task"] = TaskPattern(
            task_type="other",
            target_signature="task",
            actions=[],
            success_count=1,
            fail_count=9,  # 10% 成功率
        )
        recommender = TaskRecommender(learner)
        recs = recommender.recommend_by_window("完全不相关的窗口标题")
        # score = 0 + 0 + 0.1*0.3 = 0.03 < 0.25
        assert recs == []

    def test_recommend_by_history(self):
        """基于历史操作推荐"""
        learner = _isolated_learner()
        learner.patterns["auto:login"] = TaskPattern(
            task_type="auto_login",
            target_signature="login",
            actions=[
                {"action": "open"},
                {"action": "click"},
                {"action": "type"},
                {"action": "click"},
            ],
        )
        recommender = TaskRecommender(learner)
        recs = recommender.recommend_by_history(["open", "click"])
        assert len(recs) == 1
        assert recs[0]["next_actions"] == ["type", "click"]

    def test_recommend_by_history_no_match(self):
        """历史无匹配"""
        learner = _isolated_learner()
        recommender = TaskRecommender(learner)
        recs = recommender.recommend_by_history(["unknown_action"])
        assert recs == []


# ============================================================================
# TaskLearningEngine
# ============================================================================
class TestTaskLearningEngine:
    def test_init(self):
        """引擎初始化"""
        engine = TaskLearningEngine(learner=_isolated_learner())
        assert engine.learner is not None
        assert engine.adapter is not None
        assert engine.extractor is not None
        assert engine.recommender is not None

    def test_extract_pattern(self):
        """引擎提取模式"""
        engine = TaskLearningEngine(learner=_isolated_learner())
        sessions = [
            RecordingSession(
                name="r1",
                start_time=MagicMock(),
                events=[
                    RecordingEvent(action="open", timestamp=0),
                    RecordingEvent(action="click", timestamp=1),
                    RecordingEvent(action="save", timestamp=2),
                ],
            ),
            RecordingSession(
                name="r2",
                start_time=MagicMock(),
                events=[
                    RecordingEvent(action="open", timestamp=0),
                    RecordingEvent(action="click", timestamp=1),
                    RecordingEvent(action="close", timestamp=2),
                ],
            ),
        ]
        pattern = engine.extract_pattern(sessions)
        assert pattern is not None
        assert pattern["actions"] == ["open", "click"]

    def test_recommend_combined(self):
        """综合推荐"""
        engine = TaskLearningEngine(learner=_isolated_learner())
        # 注入模式
        engine.learner.patterns["test:action"] = TaskPattern(
            task_type="test",
            target_signature="action",
            actions=[{"action": "open"}, {"action": "click"}],
            success_count=10,
            fail_count=0,
        )
        result = engine.recommend(window_title="test window", recent_actions=["open"])
        assert "by_window" in result
        assert "by_history" in result

    def test_learn_from_recording(self):
        """从录制学习"""
        engine = TaskLearningEngine(learner=_isolated_learner())
        session = RecordingSession(
            name="my_recording",
            start_time=MagicMock(),
            events=[
                RecordingEvent(action="click", timestamp=0),
                RecordingEvent(action="type", timestamp=1, value="hello"),
            ],
        )
        engine.learn_from_recording(session, success=True, duration=2.5)
        pattern = engine.learner.suggest("recorded", "my_recording")
        assert pattern is not None
        assert pattern.success_count == 1
        assert pattern.avg_duration == 2.5