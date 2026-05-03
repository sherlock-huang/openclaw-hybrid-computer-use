# M4a Development Package — Self-Healing Quantitative Validation

## Goal

设计并实现 `scripts/validate_self_healing_quantitative.py`，通过预设 mock 场景量化验证 Self-Healing 系统的核心指标。

## Non-Goal

- 不启动 Option G（GUI 编辑器 Web 化）
- 不修改生产环境配置或 CI/CD
- 不引入新的外部依赖
- 不做真实 UI 自动化（保持可重复性）

## Technical Research

现有核心模块分析：
- `failure_analyzer.py` — 关键词+异常类型分类，输出 `FailureType`
- `recovery_strategy.py` — 4 层修复：Skill → Traditional → VLM → Human
- `execution_diary.py` — JSONL 持久化，支持 query 和统计
- `skill_manager.py` — SkillEntry JSONL 增量管理
- `executor.py` — `_execute_with_recovery()` 桥接 analyzer + strategy + diary

## Option Comparison

| 维度 | Mock Runner（选中） | Real UI Runner |
|---|---|---|
| 可重复性 | 高，完全确定 | 低，受环境干扰 |
| 执行速度 | 快（毫秒级） | 慢（秒~分钟级） |
| 覆盖范围 | 覆盖所有 FailureType | 只能触发部分场景 |
| 基线对比 | 可精确控制预期值 | 预期值随环境波动 |
| 缺点 | 不验证真实截图/VLM | 不稳定，不适合量化基准 |

结论：Mock 方式适合本阶段量化基准建立。真实 UI 验证在后续 E2E 阶段补充。

## Module Boundaries

```
scripts/validate_self_healing_quantitative.py
  ├─ 依赖 → src.core.failure_analyzer (只读)
  ├─ 依赖 → src.core.recovery_strategy (只读)
  ├─ 依赖 → src.core.execution_diary (读写日志)
  ├─ 依赖 → src.core.models.Task (只读)
  └─ 不依赖 → src.core.executor (避免启动完整执行引擎)
       不依赖 → src.perception.* (避免真实视觉)
       不依赖 → src.action.* (避免真实控制)
```

## Dependency Direction

验证框架 → core 模块（单向）
core 模块不知道验证框架存在。

## Data Flow

```
预设 Scenario（FailureType + Task + mock_setup）
   ↓
Mock Executor（MagicMock 提供 mouse/keyboard/screen/detector）
   ↓
FailureAnalyzer.analyze() → FailureType
   ↓
RecoveryStrategy.attempt_recovery() → RecoveryResult
   ↓
MetricsCollector.record() → 按 tier / failure_type 聚合
   ↓
JSON report + Markdown report
```

## Failure Behavior

- mock 中某场景异常 → 记录为 `error`，不影响其他场景继续运行
- 无 API key 的 VLM 场景 → 用 MagicMock 模拟 diagnostician
- 输出目录不存在 → 自动创建

## Test Strategy Matrix

| Risk | Scenario | FailureType | 预期层级 | Required Test | Evidence |
|---|---|---|---|---|---|
| Skill 经验不可复用 | skill_hit | ELEMENT_NOT_FOUND | L1-Skill | mock | pytest output |
| OCR 传统修复失效 | ocr_success | ELEMENT_NOT_FOUND | L2-Traditional | mock | pytest output |
| 时机问题未缓解 | timing_success | TIMING_ISSUE | L2-Traditional | mock | pytest output |
| YOLO 元素漂移 | ui_changed_success | UI_CHANGED | L2-Traditional | mock | pytest output |
| VLM 诊断失败 | vlm_fallback | UI_CHANGED | L3→fallback | mock | pytest output |
| 人机协作兜底 | human_skip | PERMISSION_DENIED | L4-Human | mock | pytest output |
| 权限问题误报 | permission_denied | PERMISSION_DENIED | 直接失败 | mock | pytest output |
| 参数错误误报 | validation_error | VALIDATION_ERROR | 直接失败 | mock | pytest output |
| 未知错误重试 | unknown_success | UNKNOWN | L2-Traditional | mock | pytest output |
| 网络恢复超时 | network_success | NETWORK_ERROR | L2-Traditional | mock | pytest output |

## Constraints

- Python 标准库 + pytest + numpy（已有依赖）
- 不修改 `src/core/*` 任何文件
- 不启动真实浏览器/Office/微信

## Minimal-Change Strategy

- 新增 1 个脚本文件
- 新增 1 个测试文件
- 新增 1 个开发包文档（本文件）
- 复用现有 `RecoveryStrategy` 和 `FailureAnalyzer` 的 public API

## Documentation Impact

- 新增 `docs/M4a-development-package.md`
- 更新 `docs/EVIDENCE_LEDGER.md`
- 无需修改 `README.md`

## Evidence Plan

- pytest 终端输出截图
- `reports/self_healing_metrics.json` 和 `.md`
- 与预设基线的对比表格
