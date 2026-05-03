# CCK -> CCQ: Phase 0 Initialization Handoff (ACS v2026-05-03)

> 本地协作文档，不提交 GitHub。
> 由 Owner 鲲鹏 转发给 CCQ 后，CCQ 以此为基础开展 Reviewer 工作。
>
> **注意：ACS 规范已更新至 2026-05-03 版本，新增 `docs/technical-design-rules.md`。**
> 本次 Phase 0 草案已按最新规则调整。

---

## 1. 协作背景

我们（OHCU 项目）现在正式采用 **Agent Collaboration SOP (ACS)** 进行双 Agent 协作。

- **Owner:** 鲲鹏
- **Executor:** CCK (我，当前 Claude Code session)
- **Reviewer:** CCQ (你，另一个 Agent session)

ACS 完整规范位于本地：`D:\workspace\agent-collaboration-sop`

**本次采用的 ACS 版本包含新增规则：**
- `docs/technical-design-rules.md`：非平凡改动编码前必须有设计笔记，含技术调研、选项对比、模块边界、依赖方向、数据流、故障行为
- `templates/executor-handoff.md` / `templates/reviewer-report.md`：新增 Technical Design Review 章节
- `templates/project-sop.md`：新增红线规则 #15~17（架构影响工作必须有技术调研；模块必须解耦；设计必须说明边界/依赖/数据流/故障行为）

---

## 2. 项目身份 (OHCU)

| 项 | 内容 |
|---|---|
| 正式名称 | openclaw-hybrid-computer-use |
| 简称 | OHCU |
| 仓库 | https://github.com/sherlock-huang/openclaw-hybrid-computer-use |
| 开源状态 | 开源 |
| 短期目标 | 完成 Self-Healing Phase 2 全部功能并验证 |
| 长期目标 | 成为稳定的 Windows 桌面自动化 Agent 框架（微信、网页、远期游戏/视频剪辑） |

---

## 3. 当前阶段草案 (M4a)

**阶段名:** `M4a-SelfHealing-Quantitative-Validation`

**背景:** Self-Healing Phase 2 已完成 A~E（Skill Manager、坐标适配、健康监控、Key Manager、API 联调验证），当前进入 **Option F：预设任务 × Self-Healing 量化验证**。

**允许范围:**
1. 设计并实现 `scripts/validate_self_healing_quantitative.py` 量化验证框架
2. 定义测试场景（ELEMENT_NOT_FOUND、TIMING_ISSUE、UI_CHANGED 等失败类型的 mock 验证）
3. 收集并统计 Self-Healing 核心指标：成功率、分层分布、延迟、Skill 命中率
4. 运行本地 pytest 验证脚本正确性
5. 生成 metrics 报告（JSON + Markdown）
6. 提交代码到 main 并推送

**明确不允许 (Non-Scope):**
1. 启动 Option G（GUI 编辑器 Web 化）
2. 修改生产环境配置或 CI/CD 流程
3. 未经批准的架构改动
4. 引入新的外部依赖（无需额外 pip 包）

**完成标准:**
1. 量化验证脚本本地可运行
2. 生成完整的 Self-Healing 成功率报告（含基线对比）
3. 证据链完整：测试命令输出、metrics 截图/日志、证据台账
4. Reviewer CCQ 审核通过（`pass`）
5. Owner 鲲鹏 确认批准

**必须提供的测试与证据:**
- 本地 pytest 通过记录
- metrics 输出（JSON + 终端截图）
- 与预设基线的对比数据
- 代码 diff / commit 记录
- Reviewer 报告

---

## 4. Reviewer 权限（已获 Owner 批准）

- [x] 有权阻止进入下一阶段
- [x] 有权要求补测试、补文档、补截图、补证据
- [x] 可以指出项目目标/架构/产品方向偏离
- [x] 可以要求重新讨论范围

---

## 5. 需要你 (CCQ) 现在做什么

作为 Reviewer，你的第一步任务是：

**审核本阶段草案和 PROJECT_SOP 设计。**

请从以下维度检查（按 ACS 最新 Reviewer Quality Bar）：

### 5.1 项目目标对齐
- 阶段范围是否支持 OHCU 短期目标（完成 Self-Healing Phase 2）？
- 是否有隐藏的范围膨胀？

### 5.2 计划与设计对齐
- Non-Scope 是否足够明确？
- 完成标准是否可验证？
- 证据要求是否充分？

### 5.3 架构衔接
- 与前期已完成的 A~E 是否衔接合理？
- M4a 是否触及需提前设计的架构边界？

### 5.4 质量与风险
- 测试策略是否覆盖主路径和失败路径？
- 是否有安全/凭证泄露风险？（本阶段无新 API Key 引入，但需确认）

### 5.5 技术设计规则确认
根据 ACS 新增 `technical-design-rules.md`，本阶段实现前 CCK 将补充：
- 技术调研（现有 executor + recovery_strategy 代码分析）
- 选项对比（mock 方式 vs 真实任务 runner 方式）
- 模块边界（验证框架与现有 core 模块的耦合关系）
- 依赖方向（验证框架依赖 executor，executor 不反向依赖验证框架）
- 数据流（mock screenshot → executor → recovery_strategy → metrics）
- 故障行为（mock 失败时如何优雅降级）

请确认：本阶段范围是否**需要**在 Phase 0 就完成上述设计笔记，还是可以在 Phase 1 执行前补充？

**输出要求:**
- 如果你认为草案 OK，回复 `pass`，并附上简要的共识确认。
- 如果你认为需要修改，回复 `needs changes`，并列出 **Blocking / Non-blocking findings**。
- 请使用 `templates/reviewer-report.md` 格式输出（Technical Design Review 章节可留空，待 Phase 1 执行后填写）。

---

## 6. 附件：PROJECT_SOP.md 完整草案（ACS v2026-05-03 版）

```markdown
# Project SOP — OHCU

## Project Identity

- **Project Name:** openclaw-hybrid-computer-use
- **Project Short Name:** OHCU
- **Repository:** https://github.com/sherlock-huang/openclaw-hybrid-computer-use
- **Open Source Status:** 开源

## Owner

- **Owner Title:** 鲲鹏
- **Owner Decision Items:**
  - 新阶段开始
  - 范围变更
  - 发布部署
  - 上游 PR
  - 客户可见输出
  - 凭证或敏感配置使用

## Agents

- **Executor Agent:** Claude Code (当前 session)
- **Executor Short Name:** CCK
- **Reviewer Agent:** 另一个 Agent
- **Reviewer Short Name:** CCQ

## Current Phase

- **Phase Name:** M4a-SelfHealing-Quantitative-Validation
- **Approved Scope:**
  1. 设计并实现量化验证框架 `scripts/validate_self_healing_quantitative.py`
  2. 定义测试场景（ELEMENT_NOT_FOUND、TIMING_ISSUE、UI_CHANGED 等）
  3. 收集 Self-Healing 核心指标：成功率、分层分布、延迟、Skill 命中率
  4. 运行本地 pytest 验证
  5. 生成 metrics 报告（JSON + Markdown）
  6. 提交代码到 main 并推送
- **Explicit Non-Scope:**
  1. 启动 Option G（GUI 编辑器 Web 化）
  2. 修改生产环境配置或 CI/CD 流程
  3. 未经批准的架构改动
  4. 引入新的外部依赖
- **Exit Criteria:**
  1. 量化验证脚本本地可运行
  2. 生成完整的 Self-Healing 成功率报告（含基线对比）
  3. 证据链完整
  4. Reviewer CCQ 审核通过
  5. Owner 鲲鹏 确认批准
- **Required Verification:**
  - 本地 pytest 通过记录
  - metrics 输出（JSON + 终端截图）
  - 与预设基线的对比数据
  - 代码 diff / commit 记录
  - Reviewer 报告

## Redline Rules

1. Executor 不能自批。
2. Reviewer 必须审核代码、架构、工程结构、项目目标对齐、测试、安全、证据、发布风险。
3. 下一阶段不能在 Reviewer 共识报告和 Owner 批准前开始。
4. 范围变更需要书面讨论和 Owner 批准。
5. 公开发布、部署、上游 PR、客户报告或凭证使用需要 Owner 批准。
6. 所有重要声明需要证据。
7. 重要代码和模块方法必须包含人类可调试的注释。
8. 任何测试、验证、审核、部署、上游 PR 或客户可见输出必须有可追溯的台账条目。
9. 视觉、公开、远程、CI、部署、PR、论坛、博客或客户可见证据在可行时必须包含截图。
10. 每个非平凡的开发单元必须有计划、设计说明、测试用例、约束、最小改动策略、文档影响和证据计划。
11. Executor 必须保持改动最小化和有范围。不相关的重构需要单独批准。
12. Reviewer 必须在要求 Owner 批准前验证证据链。
13. Reviewer 必须挑战测试覆盖率。仅覆盖成功路径的测试对有风险的工作不足够。
14. Reviewer 必须在代码运行且测试通过时仍然标记设计、计划、架构或项目目标偏离。
15. 架构影响工作编码前必须有技术调研和设计笔记。
16. 模块必须合理解耦。Reviewer 必须拒绝可避免的紧耦合。
17. 设计必须说明模块边界、依赖方向、数据流、故障行为。

## Development Package Requirements

Before non-trivial implementation, Executor must prepare:

- plan
- design notes
- technical/architecture research
- module boundaries
- dependency direction
- data flow
- failure behavior
- test cases
- constraints
- explicit non-scope
- minimal-change strategy
- documentation impact
- evidence plan
- rollback/recovery notes when relevant

Reviewer must approve the package before implementation when work is:

- architecture-affecting
- cross-module
- high-risk
- public/upstream/customer-visible
- security or credential related

## Handoff Rules

Executor must submit:

- development package reference
- changed files
- summary
- tests run
- verification evidence and screenshots
- risks
- explicit review request

Reviewer must submit:

- pass / needs changes
- findings
- verification
- test coverage assessment
- design/plan drift assessment
- technical design and decoupling assessment
- ledger links and screenshot/evidence references
- risks
- Owner decision items

## Evidence Locations

- **Evidence directory:** `evidence/`
- **Ledger file:** `docs/EVIDENCE_LEDGER.md`
- **Decision log:** `docs/DECISION_LOG.md`
```

---

*文档由 CCK (Executor) 按 ACS v2026-05-03 起草，待 CCQ (Reviewer) 审核。*
