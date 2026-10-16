---
phase: GB-14-cgb-e-model-qualification-and-corpus
reviewed: 2026-10-16T03:03:22Z
depth: standard
files_reviewed: 2
files_reviewed_list:
  - tests/CMakeLists.txt
  - tests/scripts/test-cgb-corpus-report.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 14: CR-07 Fix Recheck

**Reviewed:** 2026-10-16T03:03:22Z
**Depth:** standard
**Files Reviewed:** 2
**Status:** clean

## Summary

The two-file CR-07 fix consistently binds corpus stamp generation and consumers to the configured CTest executable. The focused source delta adds no new correctness, security, or test-reliability issue. The actual hosted Windows and exact CMake 3.25.3 checks remain pending; no result from those environments is claimed here.

## Narrative Findings (AI reviewer)

### Original Finding Disposition

**CR-07: Build stamp fingerprints a different CTest than its consumers — FIXED** in commit `f3b7ed4e3b03fa04d4e74dd9609705a530e676e9`.

In `tests/CMakeLists.txt:1701-1706`, the stamp target now invokes `cmake -E env` with `GBB_CTEST_COMMAND=${CMAKE_CTEST_COMMAND}`. The same configured executable is therefore selected by `full_build_identity()` when producing the stamp and when report consumers recompute identity. The added control at `tests/scripts/test-cgb-corpus-report.py:493-504` verifies the actual stamp against the configured identity, substitutes a different executable path for identity calculation, checks that its CTest digest changes, and requires `verify_build_stamp()` to reject it as `build-input-stamp-mismatch`.

The control directly covers the former identity divergence and fails closed when the tool digest differs. This closes the T-14-21 receipt-identity gap. The CTest pipe timeout/termination behavior relevant to T-14-22 is unchanged by this two-file fix. The fix report records a RED decoy-CTest reproduction before the change, a GREEN reproduction after it, three focused report CTests, and all 13 report-contract tests passing; these results are sourced from [14-REVIEW-FIX.iter3.md](14-REVIEW-FIX.iter3.md), not rerun during this focused review.

The cumulative finding remains documented in [14-REVIEW.md](14-REVIEW.md) as a historical blocker with its fixed disposition. The earlier open observation in [14-REVIEW-RECHECK-2.md](14-REVIEW-RECHECK-2.md) is superseded by this recheck.

---

_Reviewed: 2026-10-16T03:03:22Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
