# CCQ Development Package Review — M4b-SelfHealing-RealUI-Validation

**Project:** OHCU
**Phase:** M4b-SelfHealing-RealUI-Validation
**Reviewer:** CCQ (Claude Code Qwen)
**Date:** 2026-05-04

---

## Result: PASS

Development package approved for implementation. CCK may proceed with Iteration 1.

---

## Review Against ACS Technical Design Rules

### Rule 1: Design Before Implementation ✅ PASS

| Requirement | Status |
|---|---|
| Goal / non-goal | ✅ Clearly stated |
| User/product problem | ✅ M4a mock vs real UI gap identified |
| Current architecture context | ✅ 6 core modules analyzed, 3 gaps identified |
| Researched options (2-3) | ✅ 3 options (A/B/C) with pros/cons |
| Recommended option + why | ✅ Option C (Hybrid) with clear rationale |
| Module boundaries | ✅ Clear boundaries with dependency map |
| Dependency direction | ✅ Unidirectional (scripts → core) |
| Data flow | ✅ Full pipeline documented |
| State ownership | ✅ 4 state owners identified |
| Failure behavior | ✅ 7 scenarios with fail open/closed matrix |
| Security/redaction | ✅ 5 security measures documented |
| Test strategy | ✅ Risk matrix with 7 risks + explicit non-testing |
| Migration/rollback | ✅ Config fields have defaults, rollback = delete |

### Rule 2: Required Design Inputs ✅ PASS

All 12 required inputs present in `docs/M4b-development-package.md`.

### Rule 3: Modular Design And Decoupling ✅ PASS

- Each module has one clear responsibility: validation script only collects metrics, core modules unchanged
- Dependencies point inward: scripts → core (read-only), core unaware of scripts
- No cross-layer reaching: scripts use public API only
- No bypass of approved gates: Config extension is additive

### Rule 4: Stability And Failure Design ✅ PASS

| Scenario | Behavior | Correct? |
|---|---|---|
| Bad input | Reject scenario, continue next | ✅ fail open |
| Timeout | Force terminate, close app, record failure | ✅ fail closed |
| Partial failure | Continue other scenarios | ✅ fail open |
| Retry exhaustion | Record failure, close app, continue | ✅ fail open |
| Dependency unavailable | Skip traditional, degrade to VLM | ✅ fail open |
| App launch failure | Skip scenario, record error | ✅ fail open |
| Desktop recovery failure | Log warning, don't fail test | ✅ fail open |

Default strategy: **fail open** (single scenario failure doesn't stop pipeline) — appropriate for validation tool.

### Rule 5: Design Verification ✅ PASS

| Check | Result |
|---|---|
| Matches approved plan? | ✅ Matches Owner-approved M4b scope |
| Module boundaries reasonable? | ✅ scripts → core (unidirectional) |
| Decoupling sufficient? | ✅ Config extension is additive, no core logic changes |
| Dependencies correct direction? | ✅ No circular dependencies |
| Failure behavior explicit? | ✅ 7 scenarios documented |
| Safety gates preserved? | ✅ Blacklist, placeholders, window isolation |
| Test strategy aligned with risks? | ✅ 7 risks mapped to test types |
| Human-debuggable? | ✅ Design is readable and maintainable |

### Rule 6: Design Evidence ✅ PASS

Design evidence stored in:
- `docs/M4b-development-package.md` (full design note)
- `docs/PROJECT_SOP.md` (phase scope)
- `docs/DECISION_LOG.md` (to be updated)

---

## Engineering Governance Review

### Governance Rule 1: Human-Debuggable Code ️ PENDING

Will be checked at Iteration 1 code review.

### Governance Rule 2: Traceable Verification ⚠️ NOTE

- pytest output must be recorded in evidence ledger
- Metrics JSON/MD must be committed as evidence
- Screenshot evidence for real UI scenarios is required

### Governance Rule 3: Development Package ✅ PASS

Package meets all requirements. Approved for Iteration 1.

### Governance Rule 4: Minimal Change ✅ PASS

- 1 new script
- 1 new test file
- Config.py: 3 optional fields with defaults (non-breaking)
- executor.py: ~5 lines in `_resolve_target` (non-breaking)
- Total: minimal, scoped, no unrelated changes

### Governance Rule 5: Reviewer Audit Duty ✅ PASS

All 12 audit dimensions covered in this review.

### Governance Rule 6: Owner Evidence Chain ️ PENDING

Will be completed at phase end.

---

## Specific Findings

### Non-blocking #1: Config extension naming

Consider prefixing new Config fields with `test_` (e.g., `test_failure_injection_enabled`) to make it clear these are test-specific, not production features. This prevents confusion for future developers who might wonder why `failure_injection_enabled` exists in a production config.

### Non-blocking #2: Blacklist implementation location

The action blacklist (rejecting `wechat_send`/`email_*`/`bank_*`) should be in a separate module (e.g., `src/core/safety.py`) rather than inline in the validation script. This makes it reusable for future features and easier to audit.

### Non-blocking #3: `_resolve_target` injection placement

The 5-line injection in `_resolve_target` should be at the very top of the method, before any coordinate parsing or YOLO/OCR calls. Ensure it doesn't interfere with the resolution logic when injection is disabled (which is the default).

### Non-blocking #4: Sensitive text detection for future WeChat

Owner requires sensitive text detection for future WeChat operations. The current approach (regex for phone/ID + keyword list) is acceptable for M4b's test data. But for production WeChat, consider:
- Adding a `src/core/sensitive_text_detector.py` module
- Support for configurable keyword lists (not hardcoded)
- False positive handling (don't block "test" in "test_123")

### Non-blocking #5: M4a mock data access

The calibration comparison needs access to M4a mock data (`reports/self_healing_metrics.json`). Ensure the script reads from the correct path regardless of working directory.

---

## Iteration Readiness

### Iteration 1: READY ✅

Can proceed. Focus areas for Iteration 1 review:
- Config field naming (see Non-blocking #1)
- Blacklist module placement (see Non-blocking #2)
- `_resolve_target` injection correctness (see Non-blocking #3)
- App launch/cleanup tool functions safety

### Iteration 2: READY (after Iteration 1 approval)

### Iteration 3: READY (after Iteration 2 approval)

---

## Next Steps

1. CCK proceeds with Iteration 1 (infrastructure)
2. CCK submits Iteration 1 handoff when complete
3. CCQ reviews Iteration 1 code
4. If PASS, CCK proceeds to Iteration 2
5. Repeat for Iterations 3
6. Final phase handoff → CCQ code review → Owner consensus report → Owner approval

---

**Review Standard:** ACS Technical Design Rules (6 rules) + Engineering Governance Rules (6 rules)
**Evidence Chain:** `docs/EVIDENCE_LEDGER.md` (to be updated)
**Decision Log:** `docs/DECISION_LOG.md` (to be updated)
