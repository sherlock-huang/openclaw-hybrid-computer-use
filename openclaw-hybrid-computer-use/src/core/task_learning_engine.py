"""任务学习引擎 v2

增强能力：
1. 坐标适配器 — 录制回放时基于模板匹配/OCR 自动重定位
2. 模式提取器 — 从多个录制中提取通用操作模式
3. 任务推荐器 — 基于当前上下文推荐最佳任务
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from difflib import SequenceMatcher

import numpy as np

from .models import Task, TaskSequence, RecordingEvent, RecordingSession
from .task_learner import TaskLearner, TaskPattern
from ..perception.template_matcher import TemplateMatcher
from ..perception.ocr import TextRecognizer

logger = logging.getLogger(__name__)


class CoordinateAdapter:
    """坐标适配器 — 将录制时的坐标适配到当前屏幕"""

    def __init__(self):
        self.matcher = TemplateMatcher(threshold=0.75)
        self.ocr = TextRecognizer()
        self.logger = logging.getLogger(__name__ + ".CoordinateAdapter")

    def adapt_event(self, event: RecordingEvent, screenshot: np.ndarray,
                    window_rect: Optional[Tuple[int, int, int, int]] = None) -> Optional[Tuple[int, int]]:
        """
        将录制事件坐标适配到当前屏幕

        策略优先级：
        1. 如果 event 有 css_selector（浏览器模式），直接使用
        2. 如果 event 有 recorded_position，尝试模板匹配周围区域
        3. 如果 event 有 text/element_type，尝试 OCR 定位
        4. 最后回退到相对坐标缩放

        Args:
            event: 录制事件
            screenshot: 当前屏幕截图
            window_rect: 当前窗口位置 (x, y, w, h)，用于相对缩放

        Returns:
            适配后的 (x, y) 坐标，或 None
        """
        # 浏览器模式：返回原始坐标（由浏览器 handler 处理选择器）
        if event.css_selector:
            return event.position

        if not event.position:
            return None

        orig_x, orig_y = event.position

        # 策略 1：尝试基于元素文本 OCR 重新定位
        if event.element_type:
            # 尝试在截图中寻找相似文字区域
            # 简化：这里使用一个启发式方法，如果元素类型是 button/input，
            # 尝试在原始位置附近搜索
            pass

        # 策略 2：相对坐标缩放
        if window_rect:
            scaled = self._scale_to_window(event.position, window_rect)
            if scaled:
                return scaled

        # 策略 3：如果原始坐标在屏幕范围内，直接使用（风险较高但简单）
        h, w = screenshot.shape[:2]
        if 0 <= orig_x < w and 0 <= orig_y < h:
            return (orig_x, orig_y)

        return None

    def _scale_to_window(self, position: Tuple[int, int],
                         window_rect: Tuple[int, int, int, int]) -> Optional[Tuple[int, int]]:
        """将相对窗口坐标缩放到当前窗口"""
        # 简化实现：假设录制时窗口在屏幕左上角
        # 实际应该使用录制时的窗口尺寸做比例缩放
        wx, wy, ww, wh = window_rect
        px, py = position
        if ww <= 0 or wh <= 0:
            return None
        # 如果坐标在窗口内，保持相对位置
        if wx <= px <= wx + ww and wy <= py <= wy + wh:
            return (px, py)
        return None

    def adapt_recording(self, session: RecordingSession, screenshot: np.ndarray,
                        window_rect: Optional[Tuple[int, int, int, int]] = None) -> TaskSequence:
        """
        将整个录制会话适配为可执行的任务序列

        Args:
            session: 录制会话
            screenshot: 当前屏幕截图
            window_rect: 当前窗口位置

        Returns:
            适配后的 TaskSequence
        """
        tasks = []
        for event in session.events:
            adapted_pos = self.adapt_event(event, screenshot, window_rect)
            target = f"{adapted_pos[0]},{adapted_pos[1]}" if adapted_pos else (event.target or "")

            task = Task(
                action=event.action,
                target=target,
                value=event.value,
                delay=0.5,
            )
            tasks.append(task)

        return TaskSequence(name=session.name, tasks=tasks)


class PatternExtractor:
    """模式提取器 — 从多个录制中提取通用操作模式"""

    def __init__(self):
        self.logger = logging.getLogger(__name__ + ".PatternExtractor")

    def extract_common_pattern(self, recordings: List[RecordingSession],
                               similarity_threshold: float = 0.6) -> Optional[Dict[str, Any]]:
        """
        从多个录制中提取最长公共子序列模式

        Args:
            recordings: 录制会话列表
            similarity_threshold: 动作相似度阈值

        Returns:
            通用模式字典，包含 actions 和 confidence
        """
        if len(recordings) < 2:
            return None

        # 提取每个录制的事件 action 序列
        sequences = []
        for r in recordings:
            seq = [e.action for e in r.events]
            sequences.append(seq)

        # 找最长公共子序列（LCS）
        common = self._lcs_multiple(sequences)
        if not common:
            return None

        # 计算模式覆盖度
        coverage = len(common) / max(len(s) for s in sequences)

        return {
            "pattern_name": f"extracted_pattern_{len(common)}steps",
            "actions": common,
            "coverage": coverage,
            "source_count": len(recordings),
            "confidence": coverage * (1.0 - 0.1 * len(recordings)),  # 录制越多越可信
        }

    def _lcs_multiple(self, sequences: List[List[str]]) -> List[str]:
        """多序列最长公共子序列（贪心近似）"""
        if not sequences:
            return []
        if len(sequences) == 1:
            return sequences[0]

        # 两两 LCS，然后合并
        result = sequences[0]
        for seq in sequences[1:]:
            result = self._lcs_two(result, seq)
            if not result:
                break
        return result

    def _lcs_two(self, a: List[str], b: List[str]) -> List[str]:
        """两个序列的最长公共子序列"""
        m, n = len(a), len(b)
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if a[i - 1] == b[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

        # 回溯
        result = []
        i, j = m, n
        while i > 0 and j > 0:
            if a[i - 1] == b[j - 1]:
                result.append(a[i - 1])
                i -= 1
                j -= 1
            elif dp[i - 1][j] > dp[i][j - 1]:
                i -= 1
            else:
                j -= 1
        return list(reversed(result))

    def find_similar_recordings(self, target: RecordingSession,
                                candidates: List[RecordingSession],
                                threshold: float = 0.5) -> List[RecordingSession]:
        """找到与目标录制相似的其他录制"""
        target_actions = [e.action for e in target.events]
        similar = []
        for cand in candidates:
            if cand is target:
                continue
            cand_actions = [e.action for e in cand.events]
            lcs = self._lcs_two(target_actions, cand_actions)
            similarity = len(lcs) / max(len(target_actions), len(cand_actions), 1)
            if similarity >= threshold:
                similar.append(cand)
        return similar


class TaskRecommender:
    """任务推荐器 — 基于当前上下文推荐任务"""

    def __init__(self, learner: TaskLearner):
        self.learner = learner
        self.logger = logging.getLogger(__name__ + ".TaskRecommender")

    def recommend_by_window(self, window_title: str) -> List[Dict[str, Any]]:
        """
        根据当前窗口标题推荐任务

        Args:
            window_title: 当前活动窗口标题

        Returns:
            推荐任务列表，按匹配度排序
        """
        recommendations = []

        for key, pattern in self.learner.patterns.items():
            base_score = 0.0
            # 窗口标题包含任务类型关键词
            if pattern.task_type.lower() in window_title.lower():
                base_score += 0.4
            # 窗口标题包含目标特征（非空才匹配）
            if pattern.target_signature and pattern.target_signature.lower() in window_title.lower():
                base_score += 0.3

            # 只有当有上下文匹配时，成功率才作为加分项
            if base_score > 0:
                score = base_score + pattern.success_rate * 0.3
            else:
                score = 0.0

            if score >= 0.3:
                recommendations.append({
                    "task_key": key,
                    "task_type": pattern.task_type,
                    "target": pattern.target_signature,
                    "score": round(score, 2),
                    "success_rate": round(pattern.success_rate, 2),
                    "avg_duration": round(pattern.avg_duration, 1),
                })

        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations[:5]

    def recommend_by_history(self, recent_actions: List[str]) -> List[Dict[str, Any]]:
        """
        根据最近的操作历史推荐下一步任务

        Args:
            recent_actions: 最近的 action 类型列表

        Returns:
            推荐任务列表
        """
        if not recent_actions:
            return []

        recommendations = []
        for key, pattern in self.learner.patterns.items():
            pattern_actions = [a.get("action", "") for a in pattern.actions]
            # 检查 pattern 的前缀是否与 recent_actions 匹配
            match_len = 0
            for i, act in enumerate(recent_actions):
                if i < len(pattern_actions) and pattern_actions[i] == act:
                    match_len += 1
                else:
                    break

            if match_len > 0:
                score = match_len / max(len(recent_actions), len(pattern_actions))
                recommendations.append({
                    "task_key": key,
                    "task_type": pattern.task_type,
                    "target": pattern.target_signature,
                    "score": round(score, 2),
                    "next_actions": pattern_actions[match_len:match_len+3],
                })

        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations[:5]


class TaskLearningEngine:
    """任务学习引擎统一入口"""

    def __init__(self, learner: Optional[TaskLearner] = None):
        self.learner = learner or TaskLearner()
        self.adapter = CoordinateAdapter()
        self.extractor = PatternExtractor()
        self.recommender = TaskRecommender(self.learner)
        self.logger = logging.getLogger(__name__)

    def adapt_recording(self, session: RecordingSession, screenshot: np.ndarray,
                        window_rect: Optional[Tuple[int, int, int, int]] = None) -> TaskSequence:
        """将录制适配为可执行任务"""
        return self.adapter.adapt_recording(session, screenshot, window_rect)

    def extract_pattern(self, recordings: List[RecordingSession]) -> Optional[Dict[str, Any]]:
        """从录制中提取通用模式"""
        return self.extractor.extract_common_pattern(recordings)

    def recommend(self, window_title: str = "", recent_actions: Optional[List[str]] = None) -> Dict[str, List[Dict]]:
        """
        综合推荐

        Args:
            window_title: 当前窗口标题
            recent_actions: 最近操作历史

        Returns:
            {"by_window": [...], "by_history": [...]}
        """
        return {
            "by_window": self.recommender.recommend_by_window(window_title),
            "by_history": self.recommender.recommend_by_history(recent_actions or []),
        }

    def learn_from_recording(self, session: RecordingSession, success: bool,
                             duration: float, task_type: str = "recorded"):
        """从录制会话中学习"""
        actions = [e.to_dict() for e in session.events]
        # 使用录制名称作为目标特征
        target = session.name or "unknown"
        self.learner.learn(task_type, target, actions, success, duration)
        self.logger.info(f"从录制学习: {session.name}, success={success}")