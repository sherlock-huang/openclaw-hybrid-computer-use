# M4b Development Package — Self-Healing Real-UI Validation

## Goal

在真实 Windows 桌面环境中运行可控的自动化任务，通过 Executor 层失败注入验证 Self-Healing 的实际修复效果，并与 M4a mock 基线对比校准。

## Non-Goal

1. 不涉及微信/邮件/银行等敏感应用操作
2. 不改变真实 UI（不移动窗口、不遮挡元素、不修改系统设置）
3. 不启动 Option G（GUI 编辑器 Web 化）
4. 不修改生产环境配置或 CI/CD 流程
5. 不引入新的外部依赖

## User/Product Problem

M4a 的 mock 验证证明 Self-Healing 逻辑在理想条件下可达 72.7% 成功率，但 mock 环境与真实桌面存在差距：
- 真实 OCR 可能因字体/分辨率/背景干扰而失败
- 真实 YOLO 检测存在误检/漏检
- 真实 VLM API 有网络延迟和调用成本
- 真实鼠标/键盘操作有系统级阻塞和焦点竞争

产品需要知道：M4a 的基线在实际桌面环境中是否仍然成立？如果不成立，偏差有多大？

## Current Architecture Context

M4a 完成后，核心模块状态：
- `TaskExecutor`：`_execute_single_task` → `_resolve_target` → 定位/执行
- `RecoveryStrategy`：4 层修复（Skill → Traditional → VLM → Human）
- `FailureAnalyzer`：关键字+异常分类
- `ExecutionDiary`：JSONL 持久化日志
- `Config`：含 `vlm_diagnosis_enabled`、`health_monitor_enabled` 等开关

M4a 未触及的架构点：
- `_resolve_target` 没有外部可控的失败注入点
- `Config` 没有测试专用配置段
- 真实执行没有沙盒或安全护栏

## Researched Options

### 选项 A：Executor 层失败注入（推荐）

在 `TaskExecutor._resolve_target()` 开头增加可控拦截逻辑：

```python
if self.config.failure_injection_enabled:
    scenario = self.config.failure_injection_scenario
    if scenario.matches(task, target):
        raise NotFoundError(f"[INJECTED] Target not found: {target}")
```

- **优点**：不改变真实 UI，安全可控，可精确控制失败时机和类型，可复现
- **缺点**：只覆盖定位失败（ELEMENT_NOT_FOUND），不直接模拟时机问题（TIMING_ISSUE）

### 选项 B：真实 UI 扰动

程序自动移动测试窗口位置、临时遮挡元素、改变 DPI 缩放。

- **优点**：最接近真实失败场景
- **缺点**：安全风险高，可能误操作用户其他窗口；难以复现；需要窗口句柄操作权限

### 选项 C：Hybrid（定位拦截 + 可控延迟）

选项 A 为基础，在 `Config` 中增加 `failure_injection_delay` 字段。当配置匹配时，先 `time.sleep(delay)` 再抛出异常，模拟 TIMING_ISSUE。

- **优点**：覆盖 ELEMENT_NOT_FOUND 和 TIMING_ISSUE，仍不改变 UI
- **缺点**：延迟是人工的，不等于真实系统负载延迟

**推荐方案：选项 C（Hybrid）**。理由：在不改变真实 UI 的前提下，最大化覆盖失败类型，安全可复现。

## Module Boundaries

```
scripts/validate_self_healing_realui.py
  ├─ 依赖 → src.core.executor.TaskExecutor (只读调用 + Config 注入)
  ├─ 依赖 → src.core.failure_analyzer.FailureAnalyzer (只读)
  ├─ 依赖 → src.core.recovery_strategy.RecoveryStrategy (只读观察)
  ├─ 依赖 → src.core.execution_diary.ExecutionDiary (写入日志)
  ├─ 依赖 → src.core.config.Config (扩展 failure_injection 字段)
  └─ 不依赖 → src.perception.* 直接调用（通过 Executor 间接使用）
       不依赖 → src.action.* 直接调用（通过 Executor 间接使用）
```

## Dependency Direction

验证框架 → core 模块（单向）
- `scripts/validate_self_healing_realui.py` 依赖 `src.core.*`
- `src.core.*` 不知道验证框架存在
- `Config` 新增字段属于扩展而非侵入修改

## Data Flow

```
预设 Scenario（应用名称 + target + action + 期望失败类型 + 注入配置）
   ↓
TaskExecutor 创建（注入 failure_injection Config）
   ↓
启动真实应用窗口（notepad / calc / browser）
   ↓
执行 Task → _resolve_target 检查注入配置
   ↓
[注入分支] 匹配 → 抛出 NotFoundError / 延迟后抛出
   ↓
FailureAnalyzer 分类 → FailureType
   ↓
RecoveryStrategy.attempt_recovery() → 真实修复尝试
   ↓
MetricsCollector 记录（成功/失败/层级/延迟）
   ↓
关闭应用窗口，恢复桌面状态
   ↓
JSON/Markdown 校准报告（vs M4a mock 数据）
```

## State Ownership

- **Failure Injection 配置**：归 `Config` 所有，验证脚本只读写入初始值
- **应用窗口状态**：归操作系统，验证脚本负责启动和清理
- **Metrics 数据**：归 `ValidationMetrics`，内存聚合后输出到文件
- **ExecutionDiary 日志**：归 `ExecutionDiary`，追加到 JSONL

## Failure Behavior Design

| 场景 | 行为 | fail open/closed |
|---|---|---|
| bad input（非法注入配置） | 拒绝执行该场景，记录 error，继续下一个场景 | open |
| timeout（真实任务执行超时） | 强制终止任务，关闭应用窗口，记录为失败 | closed |
| partial failure（某场景失败） | 不影响其他场景继续运行 | open |
| retry exhaustion（Self-Healing 全失败） | 记录为失败，关闭应用，继续下一场景 | open |
| dependency unavailable（YOLO/OCR 未安装） | 传统修复层跳过，直接降级到 VLM/人工 | open |
| 应用窗口启动失败 | 跳过该场景，记录为 error | open |
| 桌面状态恢复失败 | 告警日志，不影响测试结论 | open |

默认策略：**fail open**（单个场景失败不终止整个验证流程）。

## Security / Redaction Considerations

1. **不涉及敏感应用**：测试场景仅限记事本、计算器、浏览器空白页等低风险应用
2. **不涉及真实数据输入**：测试文本使用占位符（"test_123"、"hello_world"），避免剪贴板/输入框残留敏感信息
3. **窗口隔离**：每个场景独立启动和关闭应用，场景结束后强制关闭窗口，避免状态泄漏
4. **桌面恢复**：测试前后截图对比，若桌面状态未恢复则告警
5. **微信/邮件绝对禁止**：即使测试框架被误配置，也通过硬编码黑名单拒绝 `wechat_send`/`email_*` 等 action

## Test Strategy

### 风险矩阵

| Risk | Scenario | Required Test | Evidence |
|---|---|---|---|
| 失败注入不触发 | injected_not_found | 验证 _resolve_target 拦截生效 | pytest |
| 真实 OCR 修复失效 | real_ocr_healing | 记事本中 OCR 定位文字 | pytest + 截图 |
| 真实 YOLO 修复失效 | real_yolo_healing | 计算器按钮 YOLO 检测 | pytest + 截图 |
| 延迟注入不生效 | injected_timing | 验证 sleep 后抛出异常 | pytest |
| 应用窗口未清理 | cleanup_failure | 验证 teardown 关闭窗口 | pytest |
| 敏感 action 被误触发 | blacklist_guard | 验证 wechat_send 被拒绝 | pytest |
| 校准报告格式错误 | report_generation | 验证 JSON/Markdown 结构 | pytest |

### 不测试什么

- **真实 VLM API 调用**：VLM 层在真实验证中仍使用 mock（避免 API 费用和延迟）
- **Human-in-the-loop**：真实测试中跳过人工干预层，超时自动记录为失败
- **多显示器**：当前环境为单显示器，多显示器场景留待后续
- **浏览器复杂交互**：仅测试 browser_goto 到空白页，不测试登录/表单等复杂场景

## Migration / Rollback Plan

- **Config 新增字段** 有默认值 `failure_injection_enabled=False`，不影响现有代码
- **新增脚本** 不修改现有 core 模块（除 Config 扩展外）
- **回滚**：删除脚本 + 恢复 Config 即可

## Iteration Decomposition（3 个迭代）

### 迭代 1：基础设施（失败注入 + 安全策略 + 场景框架）
- Config 扩展 `failure_injection_enabled`、`failure_injection_scenario`、`failure_injection_delay`
- `_resolve_target` 增加注入拦截逻辑
- 应用窗口启动/关闭/恢复工具函数
- 敏感 action 黑名单硬编码

### 迭代 2：真实场景执行
- 场景 A：记事本 click（ELEMENT_NOT_FOUND 注入）→ 观察 OCR 修复
- 场景 B：计算器 click（ELEMENT_NOT_FOUND 注入）→ 观察 YOLO 修复
- 场景 C：浏览器 goto（TIMING_ISSUE 延迟注入）→ 观察 delay_and_retry
- 记录真实成功率、延迟、修复层级

### 迭代 3：数据汇总与校准
- 汇总真实数据 vs M4a mock 数据
- 输出校准报告（JSON + Markdown）
- 识别并修复真实环境中暴露的问题
- 补充 pytest 测试，更新 EVIDENCE_LEDGER

## Constraints

- Python 标准库 + 已有依赖（pytest、numpy、PIL）
- 修改范围限于 `src/core/config.py`（扩展字段）和新增脚本/测试
- 每个场景执行时间控制在 30 秒内（含应用启动/关闭）

## Minimal-Change Strategy

- 新增 1 个脚本文件
- 新增 1 个测试文件
- 修改 `src/core/config.py`（新增 3 个可选字段，不影响现有行为）
- 修改 `src/core/executor.py`（在 `_resolve_target` 增加 5 行注入逻辑）

## Documentation Impact

- 新增 `docs/M4b-development-package.md`
- 更新 `docs/EVIDENCE_LEDGER.md`
- 更新 `docs/PROJECT_SOP.md` Current Phase 为 M4b

## Evidence Plan

- pytest 终端输出（28+ cases）
- `reports/self_healing_realui_metrics.json` 和 `.md`
- `reports/self_healing_mock_vs_real_comparison.md`（校准报告）
- 关键场景执行前后截图（evidence/ 目录）
- Commit 记录和 diff
