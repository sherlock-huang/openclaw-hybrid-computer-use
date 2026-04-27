"""Skill 增量管理器

管理自愈修复经验的沉淀和复用。
- 固定 skill 文件，增量追加（不新建文件）
- 按 (failure_type, task_action, screen_context) 索引
- 高层模型成功后总结增量经验，低层模型下次优先使用
"""

import json
import logging
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SkillEntry:
    """单条修复经验"""
    id: str                          # 唯一标识
    failure_type: str                # 如 ELEMENT_NOT_FOUND
    task_action: str                 # 如 click, browser_click
    original_target: str             # 原始 target
    semantic_equivalents: List[str]  # 语义等价描述列表
    successful_strategy: str         # 成功策略名称
    successful_target: str           # 最终成功的 target
    successful_center: List[int]     # 成功坐标 [x, y]
    screen_context_hash: str         # 屏幕上下文指纹（简化版）
    recovery_success: bool
    vlm_diagnosis: str               # VLM 诊断摘要
    created_by_tier: str             # 哪层模型总结的: minimax/mimo/gpt5
    timestamp: float
    hit_count: int = 0               # 被成功复用次数
    last_used: float = 0.0


class SkillManager:
    """Skill 管理器"""

    SKILL_FILE = "skills/self_healing_skills.jsonl"

    def __init__(self, skill_file: Optional[str] = None):
        self.skill_file = Path(skill_file or self.SKILL_FILE)
        self.skill_file.parent.mkdir(parents=True, exist_ok=True)
        self._skills: List[SkillEntry] = []
        self._load_skills()

    def _load_skills(self):
        """加载已有 skill"""
        if not self.skill_file.exists():
            return
        try:
            with open(self.skill_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        self._skills.append(SkillEntry(**data))
                    except Exception:
                        continue
            logger.info(f"加载了 {len(self._skills)} 条 skill")
        except Exception as e:
            logger.warning(f"加载 skill 文件失败: {e}")

    def find_matching_skill(
        self,
        failure_type: str,
        task_action: str,
        original_target: str,
        screen_context_hash: Optional[str] = None,
    ) -> Optional[SkillEntry]:
        """查找匹配的 skill（按相关度排序）"""
        candidates = []
        for skill in self._skills:
            if skill.failure_type != failure_type:
                continue
            if skill.task_action != task_action:
                continue
            score = 0
            # target 完全匹配
            if skill.original_target == original_target:
                score += 3
            # 语义等价匹配
            if original_target in skill.semantic_equivalents:
                score += 2
            # 屏幕上下文匹配
            if screen_context_hash and skill.screen_context_hash == screen_context_hash:
                score += 2
            if score > 0:
                candidates.append((score, skill))

        if not candidates:
            return None

        # 按得分排序，取最高
        candidates.sort(key=lambda x: x[0], reverse=True)
        best = candidates[0][1]
        best.hit_count += 1
        best.last_used = time.time()
        self._save_skills()
        return best

    def add_skill(
        self,
        failure_type: str,
        task_action: str,
        original_target: str,
        semantic_equivalents: List[str],
        successful_strategy: str,
        successful_target: str,
        successful_center: List[int],
        screen_context_hash: str,
        recovery_success: bool,
        vlm_diagnosis: str,
        created_by_tier: str,
    ) -> SkillEntry:
        """增量添加一条 skill（追加到文件末尾）"""
        entry = SkillEntry(
            id=f"{failure_type}_{task_action}_{int(time.time())}",
            failure_type=failure_type,
            task_action=task_action,
            original_target=original_target,
            semantic_equivalents=semantic_equivalents,
            successful_strategy=successful_strategy,
            successful_target=successful_target,
            successful_center=successful_center,
            screen_context_hash=screen_context_hash,
            recovery_success=recovery_success,
            vlm_diagnosis=vlm_diagnosis,
            created_by_tier=created_by_tier,
            timestamp=time.time(),
        )
        self._skills.append(entry)
        self._append_to_file(entry)
        logger.info(f"新增 skill: {entry.id} (by {created_by_tier})")
        return entry

    def _append_to_file(self, entry: SkillEntry):
        """增量追加到 JSONL 文件（不覆盖）"""
        try:
            with open(self.skill_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")
        except Exception as e:
            logger.warning(f"追加 skill 失败: {e}")

    def _save_skills(self):
        """重写整个 skill 文件（用于更新 hit_count 等）"""
        try:
            with open(self.skill_file, "w", encoding="utf-8") as f:
                for skill in self._skills:
                    f.write(json.dumps(asdict(skill), ensure_ascii=False) + "\n")
        except Exception as e:
            logger.warning(f"保存 skill 失败: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """获取 skill 统计"""
        total = len(self._skills)
        by_tier = {}
        by_failure = {}
        for skill in self._skills:
            by_tier[skill.created_by_tier] = by_tier.get(skill.created_by_tier, 0) + 1
            by_failure[skill.failure_type] = by_failure.get(skill.failure_type, 0) + 1
        return {
            "total_skills": total,
            "by_tier": by_tier,
            "by_failure_type": by_failure,
            "most_used": sorted(
                [s for s in self._skills if s.hit_count > 0],
                key=lambda x: x.hit_count,
                reverse=True,
            )[:5],
        }

    def generate_skill_md(self, output_path: Optional[str] = None) -> str:
        """生成 skill 总结 Markdown 文件（供模型学习用）"""
        output_path = output_path or "skills/self_healing_skills.md"
        lines = ["# Self-Healing Skill Library\n", f"> 更新时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"]
        lines.append(f"> 总经验数: {len(self._skills)}\n")

        # 按 failure_type 分组
        grouped: Dict[str, List[SkillEntry]] = {}
        for skill in self._skills:
            grouped.setdefault(skill.failure_type, []).append(skill)

        for ft, skills in grouped.items():
            lines.append(f"\n## {ft}\n")
            for s in skills:
                lines.append(f"### {s.original_target} → {s.successful_target}")
                lines.append(f"- 策略: {s.successful_strategy}")
                lines.append(f"- 坐标: {s.successful_center}")
                lines.append(f"- 语义等价: {', '.join(s.semantic_equivalents)}")
                lines.append(f"- 来源: {s.created_by_tier}")
                lines.append(f"- 复用次数: {s.hit_count}")
                lines.append("")

        md = "\n".join(lines)
        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(output_path).write_text(md, encoding="utf-8")
        except Exception as e:
            logger.warning(f"生成 skill md 失败: {e}")
        return md
