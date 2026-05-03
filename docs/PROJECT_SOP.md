# Project SOP — OHCU

> 采用 Agent Collaboration SOP (ACS) 进行双 Agent 协作。
> ACS 规范位于：`D:\workspace\agent-collaboration-sop`
> 本文档由 Owner 鲲鹏 批准，Executor CCK 写入。

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

- **Executor Agent:** Claude Code KIMI
- **Executor Short Name:** CCK
- **Reviewer Agent:** Claude Code Qwen
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

## Reviewer Authority

- [x] 有权阻止进入下一阶段
- [x] 有权要求补测试、补文档、补截图、补证据
- [x] 可以指出项目目标/架构/产品方向偏离
- [x] 可以要求重新讨论范围

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
