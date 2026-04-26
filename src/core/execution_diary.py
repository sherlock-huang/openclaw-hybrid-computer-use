"""执行日记 —— 记录每次任务执行的详细上下文与结果。

为 Self-Healing 提供数据支撑，也为后续阶段二/三的分析提供历史数据。
"""

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from .failure_analyzer import FailureType
from .models import Task


@dataclass
class DiaryEntry:
    """单条执行日记记录。"""

    timestamp: str
    task_sequence_name: str
    step_index: int
    action: str
    target: Optional[str]
    value: Optional[str]
    success: bool
    failure_type: Optional[str] = None
    recovery_action: Optional[str] = None
    recovery_success: Optional[bool] = None
    error_message: Optional[str] = None
    duration_ms: Optional[float] = None
    environment: Dict[str, Any] = field(default_factory=dict)


class ExecutionDiary:
    """执行日记管理器。

    将每次执行结果持久化到 JSONL 文件，支持按条件查询和统计。
    """

    DIARY_FILE: Path = Path("logs/execution_diary.jsonl")
    MAX_ENTRIES_IN_MEMORY: int = 1000

    def __init__(self, diary_file: Optional[Path] = None):
        self.diary_file = diary_file or self.DIARY_FILE
        self.logger = logging.getLogger(__name__)
        self._entries: List[DiaryEntry] = []
        self._ensure_dir()
        self._load_recent()

    def _ensure_dir(self):
        """确保日志目录存在。"""
        self.diary_file.parent.mkdir(parents=True, exist_ok=True)

    def _load_recent(self):
        """加载最近的日记记录到内存。"""
        if not self.diary_file.exists():
            return

        try:
            with self.diary_file.open("r", encoding="utf-8") as f:
                lines = f.readlines()
            # 只保留最近 N 条
            for line in lines[-self.MAX_ENTRIES_IN_MEMORY :]:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    self._entries.append(DiaryEntry(**data))
                except Exception:
                    continue
            self.logger.info(f"加载了 {len(self._entries)} 条执行日记")
        except Exception as e:
            self.logger.warning(f"加载执行日记失败: {e}")

    def record(
        self,
        task_sequence_name: str,
        step_index: int,
        task: Task,
        success: bool,
        failure_type: Optional[FailureType] = None,
        recovery_action: Optional[str] = None,
        recovery_success: Optional[bool] = None,
        error_message: Optional[str] = None,
        duration_ms: Optional[float] = None,
        screenshot: Optional[np.ndarray] = None,
    ):
        """记录一次执行结果。

        Args:
            task_sequence_name: 任务序列名称。
            step_index: 步骤索引（从0开始）。
            task: 执行的任务对象。
            success: 是否成功。
            failure_type: 失败类型（成功时为 None）。
            recovery_action: 采取的修复动作（成功时为 None）。
            recovery_success: 修复是否成功（成功时为 None）。
            error_message: 错误信息（成功时为 None）。
            duration_ms: 执行耗时（毫秒）。
            screenshot: 屏幕截图（可选，用于后续分析）。
        """
        env = self._capture_environment(screenshot)

        entry = DiaryEntry(
            timestamp=datetime.now().isoformat(),
            task_sequence_name=task_sequence_name,
            step_index=step_index,
            action=task.action,
            target=task.target,
            value=task.value,
            success=success,
            failure_type=failure_type.name if failure_type else None,
            recovery_action=recovery_action,
            recovery_success=recovery_success,
            error_message=error_message,
            duration_ms=duration_ms,
            environment=env,
        )

        self._entries.append(entry)
        if len(self._entries) > self.MAX_ENTRIES_IN_MEMORY:
            self._entries.pop(0)

        self._append_to_file(entry)

        # 成功时记录积极反馈
        if success:
            self.logger.info(
                f"日记记录: [{task_sequence_name}] 步骤 {step_index} ({task.action}) 成功"
            )
        else:
            self.logger.info(
                f"日记记录: [{task_sequence_name}] 步骤 {step_index} ({task.action}) 失败"
                f" - {failure_type.name if failure_type else 'UNKNOWN'}"
            )

    def _capture_environment(self, screenshot: Optional[np.ndarray]) -> Dict[str, Any]:
        """捕获执行环境信息。"""
        env: Dict[str, Any] = {
            "screen_resolution": self._get_screen_resolution(),
            "timestamp_unix": time.time(),
        }
        if screenshot is not None:
            env["screenshot_shape"] = list(screenshot.shape)
        return env

    def _get_screen_resolution(self) -> str:
        """获取屏幕分辨率。"""
        try:
            import pyautogui

            w, h = pyautogui.size()
            return f"{w}x{h}"
        except Exception:
            return "unknown"

    def _append_to_file(self, entry: DiaryEntry):
        """追加单条记录到文件。"""
        try:
            with self.diary_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")
        except Exception as e:
            self.logger.warning(f"写入执行日记失败: {e}")

    def query(
        self,
        task_sequence_name: Optional[str] = None,
        action: Optional[str] = None,
        failure_type: Optional[str] = None,
        recovery_success: Optional[bool] = None,
        limit: int = 100,
    ) -> List[DiaryEntry]:
        """按条件查询日记记录。"""
        results = self._entries[:]

        if task_sequence_name:
            results = [e for e in results if e.task_sequence_name == task_sequence_name]
        if action:
            results = [e for e in results if e.action == action]
        if failure_type:
            results = [e for e in results if e.failure_type == failure_type]
        if recovery_success is not None:
            results = [e for e in results if e.recovery_success == recovery_success]

        return results[-limit:]

    def get_success_rate(
        self,
        task_sequence_name: Optional[str] = None,
        action: Optional[str] = None,
    ) -> float:
        """计算成功率。"""
        entries = self.query(
            task_sequence_name=task_sequence_name, action=action, limit=1000
        )
        if not entries:
            return 0.0
        successes = sum(1 for e in entries if e.success)
        return successes / len(entries)

    def get_top_failure_reasons(
        self,
        task_sequence_name: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 5,
    ) -> List[tuple]:
        """获取最常见的失败原因及次数。"""
        entries = self.query(
            task_sequence_name=task_sequence_name,
            action=action,
            limit=1000,
        )
        failures = [e for e in entries if not e.success and e.failure_type]

        from collections import Counter

        counts = Counter(e.failure_type for e in failures)
        return counts.most_common(limit)

    def get_recovery_effectiveness(
        self,
        failure_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """统计修复策略的有效性。"""
        entries = self.query(failure_type=failure_type, limit=1000)
        recovery_attempts = [e for e in entries if e.recovery_action is not None]

        if not recovery_attempts:
            return {"total": 0, "success_rate": 0.0}

        successes = sum(1 for e in recovery_attempts if e.recovery_success)
        return {
            "total": len(recovery_attempts),
            "successes": successes,
            "success_rate": successes / len(recovery_attempts),
            "by_action": self._group_by_action(recovery_attempts),
        }

    def _group_by_action(self, entries: List[DiaryEntry]) -> Dict[str, Dict[str, int]]:
        """按修复动作分组统计。"""
        from collections import defaultdict

        stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {"total": 0, "success": 0})
        for e in entries:
            action = e.recovery_action or "unknown"
            stats[action]["total"] += 1
            if e.recovery_success:
                stats[action]["success"] += 1
        return dict(stats)

    def generate_report(self) -> str:
        """生成执行日记摘要报告。"""
        total = len(self._entries)
        if total == 0:
            return "暂无执行记录"

        successes = sum(1 for e in self._entries if e.success)
        failures = total - successes
        overall_rate = successes / total if total > 0 else 0.0

        lines = [
            "=== 执行日记摘要 ===",
            f"总记录数: {total}",
            f"成功: {successes} | 失败: {failures} | 成功率: {overall_rate:.1%}",
            "",
            "Top 5 失败原因:",
        ]

        for reason, count in self.get_top_failure_reasons(limit=5):
            lines.append(f"  - {reason}: {count} 次")

        recovery = self.get_recovery_effectiveness()
        lines.extend([
            "",
            f"修复策略尝试: {recovery['total']} 次",
            f"修复成功率: {recovery['success_rate']:.1%}",
        ])

        return "\n".join(lines)
