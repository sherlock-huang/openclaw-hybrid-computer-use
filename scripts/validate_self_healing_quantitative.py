"""Self-Healing 量化验证框架。

通过 mock 预设场景，统计 RecoveryStrategy 各层级修复指标：
- 整体成功率
- 分层分布（Skill / Traditional / VLM / Human）
- 各层延迟
- Skill 命中率

用法:
    python scripts/validate_self_healing_quantitative.py

输出:
    reports/self_healing_metrics.json
    reports/self_healing_metrics.md
"""

import json
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import MagicMock, patch

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.failure_analyzer import FailureType
from src.core.recovery_strategy import RecoveryStrategy, RecoveryResult
from src.core.models import Task
from src.core.human_intervention import HumanDecision


# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------

@dataclass
class ScenarioResult:
    """单个场景的执行结果。"""

    scenario_name: str
    failure_type: str
    success: bool
    action_taken: str
    tier: str
    latency_ms: float
    detail: str = ""


@dataclass
class ValidationMetrics:
    """量化验证指标聚合器。"""

    total_scenarios: int = 0
    total_successes: int = 0
    overall_success_rate: float = 0.0
    by_tier: Dict[str, Dict[str, int]] = field(default_factory=dict)
    by_failure_type: Dict[str, Dict[str, int]] = field(default_factory=dict)
    tier_latency_ms: Dict[str, List[float]] = field(default_factory=dict)
    skill_attempts: int = 0
    skill_hits: int = 0
    skill_hit_rate: float = 0.0
    baseline_comparison: Dict[str, Any] = field(default_factory=dict)
    results: List[ScenarioResult] = field(default_factory=list)

    def add(self, result: ScenarioResult) -> None:
        """记录一条场景结果。"""
        self.results.append(result)
        self.total_scenarios += 1
        if result.success:
            self.total_successes += 1

        # 按 failure_type 聚合
        ft = result.failure_type
        if ft not in self.by_failure_type:
            self.by_failure_type[ft] = {"total": 0, "success": 0}
        self.by_failure_type[ft]["total"] += 1
        if result.success:
            self.by_failure_type[ft]["success"] += 1

        # 按 tier 聚合
        tier = result.tier
        if tier not in self.by_tier:
            self.by_tier[tier] = {"total": 0, "success": 0}
        self.by_tier[tier]["total"] += 1
        if result.success:
            self.by_tier[tier]["success"] += 1

        # 延迟
        if tier not in self.tier_latency_ms:
            self.tier_latency_ms[tier] = []
        self.tier_latency_ms[tier].append(result.latency_ms)

        # Skill 命中率
        if tier == "skill":
            self.skill_attempts += 1
            if result.success:
                self.skill_hits += 1

    def finalize(self) -> None:
        """计算派生指标。"""
        if self.total_scenarios > 0:
            self.overall_success_rate = self.total_successes / self.total_scenarios
        if self.skill_attempts > 0:
            self.skill_hit_rate = self.skill_hits / self.skill_attempts

        # 基线对比（预设期望值）
        self.baseline_comparison = {
            "overall_success_rate": {
                "actual": round(self.overall_success_rate, 3),
                "baseline": 0.60,
                "status": "PASS" if self.overall_success_rate >= 0.60 else "FAIL",
            },
            "skill_hit_rate": {
                "actual": round(self.skill_hit_rate, 3),
                "baseline": 0.80,
                "status": "PASS" if self.skill_hit_rate >= 0.80 else "FAIL",
            },
            "traditional_success_rate": {
                "actual": round(self._tier_rate("traditional"), 3),
                "baseline": 0.50,
                "status": "PASS" if self._tier_rate("traditional") >= 0.50 else "FAIL",
            },
            "vlm_success_rate": {
                "actual": round(self._tier_rate("vlm"), 3),
                "baseline": 0.50,
                "status": "PASS" if self._tier_rate("vlm") >= 0.50 else "FAIL",
            },
        }

    def _tier_rate(self, tier: str) -> float:
        data = self.by_tier.get(tier, {"total": 0, "success": 0})
        if data["total"] == 0:
            return 0.0
        return data["success"] / data["total"]

    def _avg_latency(self, tier: str) -> float:
        latencies = self.tier_latency_ms.get(tier, [])
        if not latencies:
            return 0.0
        return sum(latencies) / len(latencies)

    def to_dict(self) -> Dict[str, Any]:
        """导出为可 JSON 序列化的字典。"""
        return {
            "total_scenarios": self.total_scenarios,
            "total_successes": self.total_successes,
            "overall_success_rate": round(self.overall_success_rate, 4),
            "by_tier": {
                k: {**v, "rate": round(v["success"] / v["total"], 4) if v["total"] else 0.0}
                for k, v in self.by_tier.items()
            },
            "by_failure_type": {
                k: {**v, "rate": round(v["success"] / v["total"], 4) if v["total"] else 0.0}
                for k, v in self.by_failure_type.items()
            },
            "tier_latency_ms_avg": {
                tier: round(self._avg_latency(tier), 2)
                for tier in self.tier_latency_ms
            },
            "skill_hit_rate": round(self.skill_hit_rate, 4),
            "skill_attempts": self.skill_attempts,
            "skill_hits": self.skill_hits,
            "baseline_comparison": self.baseline_comparison,
            "results": [asdict(r) for r in self.results],
        }

    def generate_markdown(self) -> str:
        """生成 Markdown 报告。"""
        lines = [
            "# Self-Healing 量化验证报告",
            "",
            f"> 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"> 总场景数: {self.total_scenarios}",
            "",
            "## 总体指标",
            "",
            f"| 指标 | 数值 |",
            f"| --- | --- |",
            f"| 整体成功率 | {self.overall_success_rate:.1%} |",
            f"| Skill 命中率 | {self.skill_hit_rate:.1%} |",
            "",
            "## 基线对比",
            "",
            "| 指标 | 实际值 | 基线 | 状态 |",
            "| --- | --- | --- | --- |",
        ]
        for name, data in self.baseline_comparison.items():
            lines.append(
                f"| {name} | {data['actual']:.1%} | {data['baseline']:.0%} | {data['status']} |"
            )

        lines.extend([
            "",
            "## 分层分布",
            "",
            "| 层级 | 总次数 | 成功次数 | 成功率 | 平均延迟(ms) |",
            "| --- | --- | --- | --- | --- |",
        ])
        for tier, data in sorted(self.by_tier.items()):
            rate = data["success"] / data["total"] if data["total"] else 0.0
            avg_lat = self._avg_latency(tier)
            lines.append(
                f"| {tier} | {data['total']} | {data['success']} | {rate:.1%} | {avg_lat:.1f} |"
            )

        lines.extend([
            "",
            "## 按失败类型分布",
            "",
            "| 失败类型 | 总次数 | 成功次数 | 成功率 |",
            "| --- | --- | --- | --- |",
        ])
        for ft, data in sorted(self.by_failure_type.items()):
            rate = data["success"] / data["total"] if data["total"] else 0.0
            lines.append(f"| {ft} | {data['total']} | {data['success']} | {rate:.1%} |")

        lines.extend([
            "",
            "## 场景明细",
            "",
            "| 场景 | FailureType | 结果 | 层级 | 延迟(ms) | 动作 |",
            "| --- | --- | --- | --- | --- | --- |",
        ])
        for r in self.results:
            status = "✅" if r.success else "❌"
            lines.append(
                f"| {r.scenario_name} | {r.failure_type} | {status} | {r.tier} | {r.latency_ms:.1f} | {r.action_taken} |"
            )

        lines.append("")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def infer_tier(action_taken: str) -> str:
    """根据 action_taken 推断修复层级。"""
    if action_taken.startswith("skill:"):
        return "skill"
    if action_taken.startswith("vlm:") or action_taken == "vlm_diagnosis_failed":
        return "vlm"
    if action_taken.startswith("human_"):
        return "human"
    if action_taken in (
        "all_methods_exhausted",
        "fix_parameters",
        "manual_intervention_required",
        "exception",
    ):
        return "none"
    return "traditional"


def create_mock_executor() -> MagicMock:
    """构造一个 mock executor，提供必要的属性。"""
    executor = MagicMock()
    executor.mouse = MagicMock()
    executor.keyboard = MagicMock()
    executor.screen = MagicMock()
    executor.screen.capture.return_value = np.zeros((1080, 1920, 3), dtype=np.uint8)
    executor.detector = MagicMock()
    executor.detector.detect.return_value = []
    executor.browser_handler = MagicMock()
    return executor


# ---------------------------------------------------------------------------
# 预设场景
# ---------------------------------------------------------------------------

def run_scenario_skill_hit() -> ScenarioResult:
    """L1: Skill 历史经验命中并修复。"""
    strategy = RecoveryStrategy(skill_manager=MagicMock())
    mock_skill = MagicMock()
    mock_skill.successful_strategy = "ocr_text_search"
    mock_skill.successful_center = [500, 300]
    mock_skill.id = "skill_001"
    strategy.skill_manager.find_matching_skill.return_value = mock_skill

    executor = create_mock_executor()
    task = Task("click", target="搜索按钮")

    start = time.time()
    result = strategy.attempt_recovery(
        FailureType.ELEMENT_NOT_FOUND, task, None, executor
    )
    latency = (time.time() - start) * 1000

    return ScenarioResult(
        scenario_name="skill_hit",
        failure_type="ELEMENT_NOT_FOUND",
        success=result.success,
        action_taken=result.action_taken,
        tier=infer_tier(result.action_taken),
        latency_ms=latency,
        detail=result.detail,
    )


def run_scenario_ocr_success() -> ScenarioResult:
    """L2-Traditional: OCR 文本搜索修复元素未找到。"""
    strategy = RecoveryStrategy(skill_manager=MagicMock())
    strategy.skill_manager.find_matching_skill.return_value = None

    executor = create_mock_executor()
    task = Task("click", target="搜索")
    screenshot = np.zeros((1080, 1920, 3), dtype=np.uint8)

    with patch("src.perception.ocr.TextRecognizer") as MockRec:
        mock_rec = MagicMock()
        mock_rec.find_text.return_value = (500, 400)
        MockRec.return_value = mock_rec

        start = time.time()
        result = strategy.attempt_recovery(
            FailureType.ELEMENT_NOT_FOUND, task, screenshot, executor
        )
        latency = (time.time() - start) * 1000

    return ScenarioResult(
        scenario_name="ocr_success",
        failure_type="ELEMENT_NOT_FOUND",
        success=result.success,
        action_taken=result.action_taken,
        tier=infer_tier(result.action_taken),
        latency_ms=latency,
        detail=result.detail,
    )


def run_scenario_timing_success() -> ScenarioResult:
    """L2-Traditional: 增加等待后重试成功。"""
    strategy = RecoveryStrategy(skill_manager=MagicMock())
    strategy.skill_manager.find_matching_skill.return_value = None

    executor = create_mock_executor()
    executor._execute_single_task.return_value = True
    task = Task("click", target="btn")
    screenshot = np.zeros((1080, 1920, 3), dtype=np.uint8)

    start = time.time()
    result = strategy.attempt_recovery(
        FailureType.TIMING_ISSUE, task, screenshot, executor
    )
    latency = (time.time() - start) * 1000

    return ScenarioResult(
        scenario_name="timing_success",
        failure_type="TIMING_ISSUE",
        success=result.success,
        action_taken=result.action_taken,
        tier=infer_tier(result.action_taken),
        latency_ms=latency,
        detail=result.detail,
    )


def run_scenario_ui_changed_success() -> ScenarioResult:
    """L2-Traditional: YOLO 检测到元素文本匹配成功。"""
    strategy = RecoveryStrategy(skill_manager=MagicMock())
    strategy.skill_manager.find_matching_skill.return_value = None

    executor = create_mock_executor()
    task = Task("click", target="设置")
    screenshot = np.zeros((1080, 1920, 3), dtype=np.uint8)

    with patch("src.perception.detector.ElementDetector") as MockDet:
        mock_elem = MagicMock()
        mock_elem.text = "设置"
        mock_elem.center = (600, 400)
        mock_elem.element_type = "button"
        mock_det = MagicMock()
        mock_det.detect.return_value = [mock_elem]
        MockDet.return_value = mock_det

        start = time.time()
        result = strategy.attempt_recovery(
            FailureType.UI_CHANGED, task, screenshot, executor
        )
        latency = (time.time() - start) * 1000

    return ScenarioResult(
        scenario_name="ui_changed_success",
        failure_type="UI_CHANGED",
        success=result.success,
        action_taken=result.action_taken,
        tier=infer_tier(result.action_taken),
        latency_ms=latency,
        detail=result.detail,
    )


def run_scenario_vlm_success() -> ScenarioResult:
    """L3-VLM: VLM 诊断推荐坐标并成功修复。"""
    strategy = RecoveryStrategy(skill_manager=MagicMock())
    strategy.skill_manager.find_matching_skill.return_value = None

    mock_diag = MagicMock()
    report = MagicMock()
    report.suggested_target = {"type": "coordinate", "value": "", "center": [500, 400]}
    report.suggested_action = "click"
    report.reasoning = "VLM 诊断通过"
    report.fallback_strategy = ""
    report.semantic_equivalents = []
    report.target_presence = "found"
    report.confidence = 0.92
    tier_result = MagicMock()
    tier_result.tier = "minimax"

    mock_diag.diagnose.return_value = (report, tier_result)
    mock_diag.verify.return_value = {"success": True}
    strategy.diagnostician = mock_diag

    executor = create_mock_executor()
    task = Task("click", target="btn")
    screenshot = np.zeros((1080, 1920, 3), dtype=np.uint8)

    start = time.time()
    result = strategy.attempt_recovery(
        FailureType.ELEMENT_NOT_FOUND, task, screenshot, executor
    )
    latency = (time.time() - start) * 1000

    return ScenarioResult(
        scenario_name="vlm_success",
        failure_type="ELEMENT_NOT_FOUND",
        success=result.success,
        action_taken=result.action_taken,
        tier=infer_tier(result.action_taken),
        latency_ms=latency,
        detail=result.detail,
    )


def run_scenario_vlm_fallback() -> ScenarioResult:
    """L3-VLM: VLM 诊断成功但 Verify 失败，fallback 也失败。"""
    strategy = RecoveryStrategy(skill_manager=MagicMock())
    strategy.skill_manager.find_matching_skill.return_value = None

    mock_diag = MagicMock()
    report = MagicMock()
    report.suggested_target = {"type": "coordinate", "value": "", "center": [500, 400]}
    report.suggested_action = "click"
    report.reasoning = "VLM 诊断"
    report.fallback_strategy = "esc"
    report.semantic_equivalents = []
    report.target_presence = "found"
    report.confidence = 0.85
    tier_result = MagicMock()
    tier_result.tier = "minimax"

    mock_diag.diagnose.return_value = (report, tier_result)
    mock_diag.verify.return_value = {"success": False}
    strategy.diagnostician = mock_diag

    executor = create_mock_executor()
    # fallback 中重试仍失败
    executor._execute_single_task.return_value = False
    task = Task("click", target="btn")
    screenshot = np.zeros((1080, 1920, 3), dtype=np.uint8)

    start = time.time()
    result = strategy.attempt_recovery(
        FailureType.UI_CHANGED, task, screenshot, executor
    )
    latency = (time.time() - start) * 1000

    return ScenarioResult(
        scenario_name="vlm_fallback",
        failure_type="UI_CHANGED",
        success=result.success,
        action_taken=result.action_taken,
        tier=infer_tier(result.action_taken),
        latency_ms=latency,
        detail=result.detail,
    )


def run_scenario_human_skip() -> ScenarioResult:
    """L4-Human: 权限不足触发人机协作，用户选择跳过。"""
    mock_human = MagicMock()
    mock_decision = MagicMock()
    mock_decision.decision = HumanDecision.SKIP
    mock_decision.user_notes = "用户选择跳过"
    mock_human.intervene.return_value = mock_decision

    strategy = RecoveryStrategy(skill_manager=MagicMock(), human_handler=mock_human)
    strategy.skill_manager.find_matching_skill.return_value = None
    strategy.diagnostician = None  # 跳过 VLM

    executor = create_mock_executor()
    task = Task("click", target="btn")
    screenshot = np.zeros((1080, 1920, 3), dtype=np.uint8)

    start = time.time()
    result = strategy.attempt_recovery(
        FailureType.PERMISSION_DENIED, task, screenshot, executor
    )
    latency = (time.time() - start) * 1000

    return ScenarioResult(
        scenario_name="human_skip",
        failure_type="PERMISSION_DENIED",
        success=result.success,
        action_taken=result.action_taken,
        tier=infer_tier(result.action_taken),
        latency_ms=latency,
        detail=result.detail,
    )


def run_scenario_permission_denied() -> ScenarioResult:
    """权限不足：自动修复直接失败（不触发人机协作）。"""
    strategy = RecoveryStrategy()
    executor = create_mock_executor()
    task = Task("click", target="btn")

    start = time.time()
    result = strategy.attempt_recovery(
        FailureType.PERMISSION_DENIED, task, None, executor
    )
    latency = (time.time() - start) * 1000

    return ScenarioResult(
        scenario_name="permission_denied",
        failure_type="PERMISSION_DENIED",
        success=result.success,
        action_taken=result.action_taken,
        tier=infer_tier(result.action_taken),
        latency_ms=latency,
        detail=result.detail,
    )


def run_scenario_validation_error() -> ScenarioResult:
    """参数验证错误：不可自动修复。"""
    strategy = RecoveryStrategy()
    executor = create_mock_executor()
    task = Task("launch")  # 缺少 target

    start = time.time()
    result = strategy.attempt_recovery(
        FailureType.VALIDATION_ERROR, task, None, executor
    )
    latency = (time.time() - start) * 1000

    return ScenarioResult(
        scenario_name="validation_error",
        failure_type="VALIDATION_ERROR",
        success=result.success,
        action_taken=result.action_taken,
        tier=infer_tier(result.action_taken),
        latency_ms=latency,
        detail=result.detail,
    )


def run_scenario_unknown_success() -> ScenarioResult:
    """L2-Traditional: 未知错误通用重试成功。"""
    strategy = RecoveryStrategy(skill_manager=MagicMock())
    strategy.skill_manager.find_matching_skill.return_value = None

    executor = create_mock_executor()
    executor._execute_single_task.return_value = True
    task = Task("click", target="btn")
    screenshot = np.zeros((1080, 1920, 3), dtype=np.uint8)

    start = time.time()
    result = strategy.attempt_recovery(
        FailureType.UNKNOWN, task, screenshot, executor
    )
    latency = (time.time() - start) * 1000

    return ScenarioResult(
        scenario_name="unknown_success",
        failure_type="UNKNOWN",
        success=result.success,
        action_taken=result.action_taken,
        tier=infer_tier(result.action_taken),
        latency_ms=latency,
        detail=result.detail,
    )


def run_scenario_network_success() -> ScenarioResult:
    """L2-Traditional: 网络错误等待后浏览器重试成功。"""
    strategy = RecoveryStrategy(skill_manager=MagicMock())
    strategy.skill_manager.find_matching_skill.return_value = None

    executor = create_mock_executor()
    executor._execute_single_task.return_value = True
    task = Task("browser_goto", value="https://example.com")
    screenshot = np.zeros((1080, 1920, 3), dtype=np.uint8)

    start = time.time()
    result = strategy.attempt_recovery(
        FailureType.NETWORK_ERROR, task, screenshot, executor
    )
    latency = (time.time() - start) * 1000

    return ScenarioResult(
        scenario_name="network_success",
        failure_type="NETWORK_ERROR",
        success=result.success,
        action_taken=result.action_taken,
        tier=infer_tier(result.action_taken),
        latency_ms=latency,
        detail=result.detail,
    )


# ---------------------------------------------------------------------------
# 主控
# ---------------------------------------------------------------------------

SCENARIO_FUNCTIONS = [
    run_scenario_skill_hit,
    run_scenario_ocr_success,
    run_scenario_timing_success,
    run_scenario_ui_changed_success,
    run_scenario_vlm_success,
    run_scenario_vlm_fallback,
    run_scenario_human_skip,
    run_scenario_permission_denied,
    run_scenario_validation_error,
    run_scenario_unknown_success,
    run_scenario_network_success,
]


def run_all_scenarios() -> ValidationMetrics:
    """运行全部预设场景并返回指标。"""
    metrics = ValidationMetrics()

    for scenario_fn in SCENARIO_FUNCTIONS:
        start = time.time()
        try:
            result = scenario_fn()
        except Exception as e:
            result = ScenarioResult(
                scenario_name=scenario_fn.__name__,
                failure_type="ERROR",
                success=False,
                action_taken="exception",
                tier="none",
                latency_ms=(time.time() - start) * 1000,
                detail=str(e),
            )
        metrics.add(result)

    metrics.finalize()
    return metrics


def main() -> int:
    print("=" * 60)
    print("Self-Healing Quantitative Validation")
    print("=" * 60)

    metrics = run_all_scenarios()

    # 输出 JSON
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    json_path = reports_dir / "self_healing_metrics.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(metrics.to_dict(), f, ensure_ascii=False, indent=2)

    # 输出 Markdown
    md_path = reports_dir / "self_healing_metrics.md"
    md_path.write_text(metrics.generate_markdown(), encoding="utf-8")

    # 终端摘要
    print(f"\n总场景: {metrics.total_scenarios} | 成功: {metrics.total_successes}")
    print(f"整体成功率: {metrics.overall_success_rate:.1%}")
    print(f"Skill 命中率: {metrics.skill_hit_rate:.1%}")
    print("\n基线对比:")
    for name, data in metrics.baseline_comparison.items():
        status_icon = "✅" if data["status"] == "PASS" else "❌"
        print(f"  {status_icon} {name}: {data['actual']:.1%} (基线 {data['baseline']:.0%})")

    print(f"\nJSON:  {json_path}")
    print(f"Markdown: {md_path}")

    # 返回码：全部基线通过则 0，否则 1
    all_pass = all(d["status"] == "PASS" for d in metrics.baseline_comparison.values())
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
