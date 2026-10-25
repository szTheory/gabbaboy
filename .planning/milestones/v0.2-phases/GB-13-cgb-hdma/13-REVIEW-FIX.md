---
phase: GB-13-cgb-hdma
fixed_at: "2026-10-15T02:13:53Z"
review_path: .planning/phases/GB-13-cgb-hdma/13-REVIEW.md
iteration: 1
findings_in_scope: 4
fixed: 4
skipped: 0
status: all_fixed
---

# Phase 13: Code Review Fix Report

**Fixed at:** 2026-10-15T02:13:53Z
**Source review:** `.planning/phases/GB-13-cgb-hdma/13-REVIEW.md`
**Iteration:** 1

**Summary:**
- Findings in scope: 2
- Fixed: 2
- Skipped: 0

## Fixed Issues

### CR-01: Remote check evidence can pass with omitted, wrong-event, or contradictory results

**Files modified:** `.planning/phases/GB-13-cgb-hdma/verify-hdma-closure.py`, `tests/CMakeLists.txt`, `tests/expected-tests.txt`, `tests/scripts/test_hdma_remote_evidence.py`
**Commit:** `ec54205` (test-only RED commit: `42e330f`)
**Status:** fixed; independently re-reviewed at `774ee6c`, positive and 16 negative controls passed automatically.
**Applied fix:** Require the fixed aggregate contexts `required-native`, `fixture-repro`, and `preview-package-smoke`, with their workflow provenance, `pull_request` event, exact head, unique bounded run IDs and attempts, completed status, and successful conclusion. Reject missing, duplicate, unrecognized, malformed, oversized, or contradictory receipt data. The optional local receipt is diagnostic only; GitHub's actual required PR checks remain the merge authority. Added a Python-only positive control and 16 negative controls.

### WR-01: Player help compresses support claims and exclusions into one hard-to-scan paragraph

**Files modified:** `src/player/main.c`
**Commit:** `f052ea3`
**Applied fix:** Split the CGB claims into labeled Models, Video, Audio, Speed, Transfers, and Limits lines. Existing model, palette, colour-correction, audio, double-speed, HDMA, mode-3, hardware, and compatibility qualifications remain intact, so the existing phrase contract continues to apply unchanged.

## Verification

All checks below ran in the isolated review-fix worktree.

- Test-only RED: `python3 -I tests/scripts/test_hdma_remote_evidence.py` exited 1 before the fix and reported accepted invalid receipts: contradictory duplicate, unrecognized context, wrong event, wrong workflow provenance, and invalid run provenance.
- GREEN: the same driver reported `hdma-remote-evidence controls pass positive=1 negative=16 contexts=3`.
- `python3 -I .planning/phases/GB-13-cgb-hdma/verify-hdma-closure.py --lane` passed with six Python-only targets, 92 core HDMA cases, and two player HDMA cases.
- `python3 -I .planning/phases/GB-13-cgb-hdma/verify-hdma-closure.py --lane-self-test` passed all three lane negative controls.
- `python3 -I tests/scripts/verify-cgb-hdma-claims.py --native-player` passed all eight claim surfaces after the help edit.
- Python AST checks for both changed Python files and `git diff --check` passed.

The full closure self-test was not run. Its existing source-revision guard intentionally rejects behavior and test changes beyond the historical `13-BENCH.md` binding; that record remains pinned to `690c081e3714aa1039263255d572b6d0d06dad8e` and was not changed. Parent closeout must rebind and re-audit the evidence, then verify actual required GitHub PR checks at the final head. This report does not claim remote checks or merge readiness.

---

_Fixed: 2026-10-15T02:13:53Z_
_Fixer: the agent (gsd-code-fixer)_
_Iteration: 1_

## Focused UAT supplement — 2026-10-15

CR-UAT-01 and WR-UAT-01 are fixed in `eeb1ce9` and `0f1bb34`, independently re-reviewed by the original reviewer. The UAT checker rejects the original hidden manual heading; the handoff rejects duplicate and compound stages. Actual complete UAT passes 45 mappings, all 17 closure controls pass, Node continuity passes 3/3 and source gate controls pass 27/27. These two findings supplement the original two fixes above (four fixed, zero skipped/open); their original timestamps and RED/GREEN evidence remain historical.
