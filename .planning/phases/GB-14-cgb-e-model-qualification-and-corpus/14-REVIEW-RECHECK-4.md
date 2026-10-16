---
phase: GB-14-cgb-e-model-qualification-and-corpus
reviewed: 2026-10-16T03:08:57Z
depth: standard
files_reviewed: 3
files_reviewed_list:
  - tests/CMakeLists.txt
  - tests/scripts/verify-age-phase14-contract.py
  - tests/scripts/test_age_phase14_inherited_contract.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 14: CR-08 Fix Recheck

**Reviewed:** 2026-10-16T03:08:57Z
**Depth:** standard
**Files Reviewed:** 3
**Status:** clean

## Summary

The three-file CR-08 fix propagates a sanitizer-scaled timeout from CMake to every bounded AGE guest subprocess. Input validation and timeout failure handling remain enforced. No new correctness, security, or test-reliability issue was found in this focused delta. The hosted sanitizer rerun remains pending; the macOS host's rejection of the Linux-only sanitizer preset is not treated as an ASan result.

## Narrative Findings (AI reviewer)

### Original Finding Disposition

**CR-08: AGE child deadline ignores sanitizer slowdown — FIXED** in commit `e373b3f2b32292035531ba0aad1d05e5a4a009d9`.

In `tests/CMakeLists.txt:1357-1367`, the assertion-identity CTest passes a 15-second child limit normally and a 45-second limit when sanitizers are enabled. This matches the project's threefold outer CTest scaling. In `tests/scripts/verify-age-phase14-contract.py:226-230, 359-379, 597-607`, the selected value is strictly checked as an integer in range 1–45 and is used for every guest subprocess. `subprocess.run()` raises `TimeoutExpired` on deadline, and the script's main handler returns failure rather than admitting partial output.

The control in `tests/scripts/test_age_phase14_inherited_contract.py:25-59` asserts the 45-second timeout on all 13 child calls, rejects zero, out-of-range, boolean, and fractional limits, and confirms timeout propagation. The fix report records a pre-fix RED regression, the live AGE identity and inherited-contract CTests passing 2/2, and 13 cases/142 rows passing with the 45-second limit; I did not rerun those tests during this focused review. This closes the bounded-execution gap relevant to T-14-20 without changing guest budgets or expected observations.

The original ASan failure was in job `116778422483` in Actions run `38840242246`; the local macOS environment cannot run the Linux-only sanitizer preset. No hosted sanitizer pass is claimed for this commit.

The cumulative historical finding remains in [14-REVIEW.md](14-REVIEW.md), with the earlier CR-08 state superseded by this recheck. The detailed fix evidence is in [14-REVIEW-FIX.iter4.md](14-REVIEW-FIX.iter4.md).

---

_Reviewed: 2026-10-16T03:08:57Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
