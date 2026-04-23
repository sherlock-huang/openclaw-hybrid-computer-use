"""任务学习引擎 v2

本模块是录制回放系统的核心智能层，提供三大能力：
    1. CoordinateAdapter（坐标适配器）
       — 录制时的绝对坐标往往因分辨率/窗口位置变化而失效，
         适配器通过浏览器 CSS 选择器、相对窗口缩放等策略将录制坐标映射到当前屏幕。
    2. PatternExtractor（模式提取器）
       — 从多个录制会话中提取通用的操作模式。核心算法为最长公共子序列（LCS）：
         先对每对序列做两两 LCS（动态规划实现），再逐次合并得到多序列公共子序列。
         LCS 结果越长，说明操作模式越通用。
    3. TaskRecommender（任务推荐器）
       — 基于当前上下文（窗口标题、近期操作历史）对已知任务模式进行打分排序：
         * 窗口标题匹配：包含任务类型 +0.4 分，包含目标特征 +0.3 分
         * 成功率加权：有上下文匹配时，再叠加 success_rate * 0.3
         * 历史前缀匹配：将最近操作序列与模式前缀比对，匹配长度越长分数越高

模块结构：
    CoordinateAdapter  -> 单事件/整会话的坐标适配
    PatternExtractor   -> 多录制的公共模式提取（LCS）
    TaskRecommender    -> 基于上下文评分的任务推荐
    TaskLearningEngine -> 统一门面，聚合上述三大组件
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
    """坐标适配器 — 将录制时的坐标适配到当前屏幕

    核心思想：录制环境（分辨率、窗口大小、DPI）与回放环境往往不同，
    直接复用原始绝对坐标会导致点错位置。适配器按以下优先级尝试修正：
        1. 浏览器模式：若 event 带有 css_selector，直接返回原始坐标
           （浏览器端 handler 会基于选择器重新定位元素）
        2. 相对坐标缩放：若提供了当前 window_rect，按窗口位置做简单缩放
        3. 原始坐标回退：若原始坐标仍在当前截图范围内，直接复用
    """

    def __init__(self):
        self.matcher = TemplateMatcher(threshold=0.75)
        self.ocr = TextRecognizer()
        self.logger = logging.getLogger(__name__ + ".CoordinateAdapter")

    def adapt_event(self, event: RecordingEvent, screenshot: np.ndarray,
                    window_rect: Optional[Tuple[int, int, int, int]] = None) -> Optional[Tuple[int, int]]:
        """将单个录制事件的坐标适配到当前屏幕

        策略优先级：
            1. 若 event 有 css_selector（浏览器自动化模式），直接返回原始坐标
            2. 若 event 有 recorded_position，尝试基于 window_rect 做相对缩放
            3. 若原始坐标在当前 screenshot 范围内，直接复用（风险较高但简单）

        Args:
            event: 单个录制事件，可能包含 position、css_selector、element_type 等信息
            screenshot: 当前屏幕截图（BGR 格式），用于边界校验
            window_rect: 当前窗口位置 (x, y, w, h)，用于相对坐标缩放；None 则跳过

        Returns:
            适配后的 (x, y) 整数坐标，或 None（无法适配时）
        """
        # 浏览器模式：返回原始坐标，由上层浏览器 handler 根据 css_selector 重新定位
        if event.css_selector:
            return event.position

        if not event.position:
            return None

        orig_x, orig_y = event.position

        # 策略 1（预留扩展）：尝试基于元素文本 OCR 重新定位
        # 启发式思路：如果 element_type 是 button/input，可在原始位置附近做 OCR 搜索
        if event.element_type:
            # TODO: 实现基于 OCR 的附近文本搜索，目前先保持占位
            pass

        # 策略 2：相对坐标缩放 —— 假设录制时窗口在屏幕左上角，按当前窗口做比例映射
        if window_rect:
            scaled = self._scale_to_window(event.position, window_rect)
            if scaled:
                return scaled

        # 策略 3：若原始坐标仍在当前截图尺寸范围内，直接复用
        # 适用于分辨率未发生变化的场景，但窗口移动后可能偏差
        h, w = screenshot.shape[:2]
        if 0 <= orig_x < w and 0 <= orig_y < h:
            return (orig_x, orig_y)

        return None

    def _scale_to_window(self, position: Tuple[int, int],
                         window_rect: Tuple[int, int, int, int]) -> Optional[Tuple[int, int]]:
        """将录制坐标按当前窗口做相对缩放（内部方法）

        当前实现为简化策略：假设录制时窗口也在屏幕左上角，
        仅检查坐标是否落入当前窗口矩形内；若落入则保持原样，否则返回 None。
        未来可扩展为：使用录制时的窗口尺寸与当前尺寸做真正的比例映射。

        Args:
            position: 录制时的 (x, y) 坐标
            window_rect: 当前窗口 (x, y, w, h)

        Returns:
            缩放后的坐标，或 None（若坐标在窗口外）
        """
        wx, wy, ww, wh = window_rect
        px, py = position
        # 防御性校验：窗口宽高必须为正数
        if ww <= 0 or wh <= 0:
            return None
        # 简化策略：若原始坐标在当前窗口矩形内，则认为仍有效
        if wx <= px <= wx + ww and wy <= py <= wy + wh:
            return (px, py)
        return None

    def adapt_recording(self, session: RecordingSession, screenshot: np.ndarray,
                        window_rect: Optional[Tuple[int, int, int, int]] = None) -> TaskSequence:
        """将整个录制会话适配为可执行的任务序列

        遍历 session 中的所有事件，逐个调用 adapt_event 进行坐标适配，
        然后将结果封装为 TaskSequence。

        Args:
            session: 录制会话，包含一系列 RecordingEvent
            screenshot: 当前屏幕截图
            window_rect: 当前窗口位置（可选）

        Returns:
            适配后的 TaskSequence，每个 Task 的 target 字段为 "x,y" 坐标字符串
        """
        tasks = []
        for event in session.events:
            adapted_pos = self.adapt_event(event, screenshot, window_rect)
            # 若坐标适配成功，target 为 "x,y"；否则回退到 event.target
            target = f"{adapted_pos[0]},{adapted_pos[1]}" if adapted_pos else (event.target or "")

            task = Task(
                action=event.action,
                target=target,
                value=event.value,
                delay=0.5,  # 默认延迟 0.5 秒，避免操作过快导致 UI 未响应
            )
            tasks.append(task)

        return TaskSequence(name=session.name, tasks=tasks)


class PatternExtractor:
    """模式提取器 — 从多个录制中提取通用操作模式

    核心算法为最长公共子序列（LCS, Longest Common Subsequence）：
        - 两两 LCS：使用经典动态规划（O(m*n)），通过 dp 表记录前缀匹配长度，
          再回溯得到最长公共子序列。
        - 多序列 LCS：采用贪心近似 —— 先取第一个序列作为基准，
          然后依次与后续序列做两两 LCS，结果逐步收敛为公共部分。
    LCS 长度越长、覆盖度越高，说明该模式在多次录制中越通用。
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__ + ".PatternExtractor")

    def extract_common_pattern(self, recordings: List[RecordingSession],
                               similarity_threshold: float = 0.6) -> Optional[Dict[str, Any]]:
        """从多个录制中提取最长公共子序列模式

        执行流程：
            1. 将每个录制会话转换为 action 类型字符串列表
            2. 对多个序列执行多序列 LCS，得到公共 action 序列
            3. 计算覆盖度（公共序列长度 / 最长录制长度）
            4. 综合覆盖度和录制数量计算 confidence 分数

        Args:
            recordings: 录制会话列表，至少包含 2 个会话才有提取意义
            similarity_threshold: 动作相似度阈值（当前实现中预留，未来用于模糊匹配）

        Returns:
            包含模式名称、actions、覆盖度、来源数量及置信度的字典；
            若录制数不足或不存在公共子序列则返回 None。
        """
        if len(recordings) < 2:
            return None

        # 提取每个录制的事件 action 序列，例如 ["click", "type", "click"]
        sequences = []
        for r in recordings:
            seq = [e.action for e in r.events]
            sequences.append(seq)

        # 找多序列的最长公共子序列（贪心近似）
        common = self._lcs_multiple(sequences)
        if not common:
            return None

        # 覆盖度 = 公共序列长度 / 最长录制序列长度，越高说明模式越完整
        coverage = len(common) / max(len(s) for s in sequences)

        # 置信度公式：coverage * (1.0 - 0.1 * 录制数)
        # 含义：覆盖度越高越可信；但录制数过多时惩罚 0.1/个，避免过度泛化
        return {
            "pattern_name": f"extracted_pattern_{len(common)}steps",
            "actions": common,
            "coverage": coverage,
            "source_count": len(recordings),
            "confidence": coverage * (1.0 - 0.1 * len(recordings)),
        }

    def _lcs_multiple(self, sequences: List[List[str]]) -> List[str]:
        """多序列最长公共子序列（贪心近似算法）

        策略：
            - 若只有一个序列，公共子序列即其自身
            - 否则以第一个序列为基准，依次与剩余序列做两两 LCS，
              每次用 LCS 结果替换当前基准，逐步收敛到多序列公共部分

        Args:
            sequences: 多个字符串序列的列表

        Returns:
            所有序列的最长公共子序列（近似解）
        """
        if not sequences:
            return []
        if len(sequences) == 1:
            return sequences[0]

        # 两两 LCS 然后合并
        result = sequences[0]
        for seq in sequences[1:]:
            result = self._lcs_two(result, seq)
            if not result:
                break  # 若中间结果为空，后续必然也为空，提前退出
        return result

    def _lcs_two(self, a: List[str], b: List[str]) -> List[str]:
        """两个序列的最长公共子序列（经典动态规划实现）

        算法步骤：
            1. 构建 (m+1) x (n+1) 的 dp 表，dp[i][j] 表示 a[:i] 与 b[:j] 的 LCS 长度
            2. 递推：
               - 若 a[i-1] == b[j-1]，则 dp[i][j] = dp[i-1][j-1] + 1
               - 否则 dp[i][j] = max(dp[i-1][j], dp[i][j-1])
            3. 从 dp[m][n] 回溯，重构出 LCS 序列

        时间复杂度：O(m * n)，空间复杂度：O(m * n)

        Args:
            a: 第一个字符串序列
            b: 第二个字符串序列

        Returns:
            a 与 b 的最长公共子序列列表
        """
        m, n = len(a), len(b)
        # dp[i][j] 表示 a 的前 i 个元素与 b 的前 j 个元素的 LCS 长度
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        # 自底向上填充 dp 表
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if a[i - 1] == b[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

        # 从右下角回溯，重构 LCS 序列（因为是从后往前收集，最后需要 reverse）
        result = []
        i, j = m, n
        while i > 0 and j > 0:
            if a[i - 1] == b[j - 1]:
                result.append(a[i - 1])
                i -= 1
                j -= 1
            elif dp[i - 1][j] > dp[i][j - 1]:
                # 上方值更大，说明 LCS 来自 a 的前 i-1 项与 b 的前 j 项
                i -= 1
            else:
                # 左侧值更大或相等，说明 LCS 来自 a 的前 i 项与 b 的前 j-1 项
                j -= 1
        return list(reversed(result))

    def find_similar_recordings(self, target: RecordingSession,
                                candidates: List[RecordingSession],
                                threshold: float = 0.5) -> List[RecordingSession]:
        """找到与目标录制相似的其他录制

        相似度定义：两个录制 action 序列的 LCS 长度 / max(len(a), len(b))

        Args:
            target: 目标录制会话
            candidates: 候选录制会话列表
            threshold: 相似度阈值（0.0 ~ 1.0），高于此值才视为相似

        Returns:
            相似录制会话列表（不包含 target 自身）
        """
        target_actions = [e.action for e in target.events]
        similar = []
        for cand in candidates:
            if cand is target:
                continue
            cand_actions = [e.action for e in cand.events]
            lcs = self._lcs_two(target_actions, cand_actions)
            # 使用 max(..., 1) 避免除以 0
            similarity = len(lcs) / max(len(target_actions), len(cand_actions), 1)
            if similarity >= threshold:
                similar.append(cand)
        return similar


class TaskRecommender:
    """任务推荐器 — 基于当前上下文推荐最佳任务

    评分机制：
        - 窗口标题匹配（recommend_by_window）：
            * task_type 出现在窗口标题中 → +0.4
            * target_signature 出现在窗口标题中 → +0.3
            * 若以上任一项命中，再叠加 success_rate * 0.3 作为成功率加权
            * 最终分数 >= 0.3 才会进入推荐列表
        - 历史前缀匹配（recommend_by_history）：
            * 将最近的操作序列与每个模式的前缀逐位比对
            * 匹配长度 / max(len(历史), len(模式)) 作为分数
            * 同时返回接下来可能执行的 next_actions
    """

    def __init__(self, learner: TaskLearner):
        """初始化推荐器

        Args:
            learner: TaskLearner 实例，提供已学习的任务模式库
        """
        self.learner = learner
        self.logger = logging.getLogger(__name__ + ".TaskRecommender")

    def recommend_by_window(self, window_title: str) -> List[Dict[str, Any]]:
        """根据当前窗口标题推荐任务

        遍历 learner 中已学习的所有 pattern，按窗口标题关键词匹配打分，
        返回分数最高的前 5 个推荐。

        Args:
            window_title: 当前活动窗口标题字符串

        Returns:
            推荐任务字典列表，按 score 降序排列，最多 5 条；
            每条字典包含 task_key、task_type、target、score、success_rate、avg_duration
        """
        recommendations = []

        for key, pattern in self.learner.patterns.items():
            base_score = 0.0
            # 窗口标题包含任务类型关键词（如 "wechat", "browser"）
            if pattern.task_type.lower() in window_title.lower():
                base_score += 0.4
            # 窗口标题包含目标特征（非空才匹配，避免空字符串误命中）
            if pattern.target_signature and pattern.target_signature.lower() in window_title.lower():
                base_score += 0.3

            # 只有当有上下文匹配时，成功率才作为加分项；否则直接 discard（score=0）
            if base_score > 0:
                score = base_score + pattern.success_rate * 0.3
            else:
                score = 0.0

            # 仅推荐分数达到一定门槛的任务，避免无意义推荐
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
        """根据最近的操作历史推荐下一步任务

        将 recent_actions 与每个已学习模式的前缀进行逐位比对，
        匹配长度越长说明当前执行路径越接近该模式，推荐优先级越高。

        Args:
            recent_actions: 最近执行的 action 类型列表（如 ["click", "type"]）

        Returns:
            推荐任务字典列表，按 score 降序排列，最多 5 条；
            每条字典包含 task_key、task_type、target、score、next_actions
        """
        if not recent_actions:
            return []

        recommendations = []
        for key, pattern in self.learner.patterns.items():
            pattern_actions = [a.get("action", "") for a in pattern.actions]
            # 检查 pattern 的前缀是否与 recent_actions 逐位相等
            match_len = 0
            for i, act in enumerate(recent_actions):
                if i < len(pattern_actions) and pattern_actions[i] == act:
                    match_len += 1
                else:
                    break

            if match_len > 0:
                # 分数 = 匹配长度 / max(历史长度, 模式长度)，归一化到 0~1
                score = match_len / max(len(recent_actions), len(pattern_actions))
                recommendations.append({
                    "task_key": key,
                    "task_type": pattern.task_type,
                    "target": pattern.target_signature,
                    "score": round(score, 2),
                    # 附带接下来可能执行的最多 3 个动作，便于前端展示
                    "next_actions": pattern_actions[match_len:match_len+3],
                })

        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations[:5]


class TaskLearningEngine:
    """任务学习引擎统一入口（门面模式）

    聚合 CoordinateAdapter、PatternExtractor、TaskRecommender 三大组件，
    为上层提供简洁的 adapt_recording / extract_pattern / recommend / learn_from_recording 接口。
    """

    def __init__(self, learner: Optional[TaskLearner] = None):
        """初始化任务学习引擎

        Args:
            learner: TaskLearner 实例；为 None 时自动创建默认实例
        """
        self.learner = learner or TaskLearner()
        self.adapter = CoordinateAdapter()
        self.extractor = PatternExtractor()
        self.recommender = TaskRecommender(self.learner)
        self.logger = logging.getLogger(__name__)

    def adapt_recording(self, session: RecordingSession, screenshot: np.ndarray,
                        window_rect: Optional[Tuple[int, int, int, int]] = None) -> TaskSequence:
        """将录制适配为可执行任务序列

        委托给 CoordinateAdapter.adapt_recording 实现。
        """
        return self.adapter.adapt_recording(session, screenshot, window_rect)

    def extract_pattern(self, recordings: List[RecordingSession]) -> Optional[Dict[str, Any]]:
        """从录制中提取通用模式

        委托给 PatternExtractor.extract_common_pattern 实现。
        """
        return self.extractor.extract_common_pattern(recordings)

    def recommend(self, window_title: str = "", recent_actions: Optional[List[str]] = None) -> Dict[str, List[Dict]]:
        """综合推荐

        同时基于窗口标题和操作历史进行推荐，返回双通道结果。

        Args:
            window_title: 当前窗口标题
            recent_actions: 最近操作历史（可选）

        Returns:
            {"by_window": [窗口推荐列表], "by_history": [历史推荐列表]}
        """
        return {
            "by_window": self.recommender.recommend_by_window(window_title),
            "by_history": self.recommender.recommend_by_history(recent_actions or []),
        }

    def learn_from_recording(self, session: RecordingSession, success: bool,
                             duration: float, task_type: str = "recorded"):
        """从录制会话中学习并更新模式库

        将录制事件序列提交给 TaskLearner，使其能根据后续执行结果优化推荐策略。

        Args:
            session: 录制会话
            success: 本次回放是否成功
            duration: 执行耗时（秒）
            task_type: 任务分类标签，默认为 "recorded"
        """
        actions = [e.to_dict() for e in session.events]
        # 使用录制名称作为目标特征标识，便于后续按窗口标题匹配推荐
        target = session.name or "unknown"
        self.learner.learn(task_type, target, actions, success, duration)
        self.logger.info(f"从录制学习: {session.name}, success={success}")
