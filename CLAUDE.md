# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

## Agent Collaboration SOP (ACS)

本项目采用双 Agent 协作模式（Executor CCK / Reviewer CCQ），由 Owner 鲲鹏 最终决策。

协作规范位于：`D:\workspace\agent-collaboration-sop`
项目 SOP 位于：`docs/PROJECT_SOP.md`

作为 Executor Agent（CCK），我必须遵守：
- 不自批、不擅自进入下一阶段
- 非平凡改动编码前准备开发包（含设计笔记、技术调研、模块边界、故障行为）
- 改动最小化，不混入无关重构
- 重要声明必须有证据（台账条目 + 截图）
- 完成后向 Reviewer（CCQ）提交 executor handoff

作为 Reviewer Agent（CCQ），CCQ 必须：
- 不止审核代码，还要审核架构、目标对齐、测试覆盖、证据、发布风险
- 不因测试通过就忽略设计/架构/目标偏离
- 审核通过后向 Owner 提交共识报告，等待批准

证据存放于 `evidence/`，台账位于 `docs/EVIDENCE_LEDGER.md`，决策记录位于 `docs/DECISION_LOG.md`。
