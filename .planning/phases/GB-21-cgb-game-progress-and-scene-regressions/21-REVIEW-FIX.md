---
phase: GB-21-cgb-game-progress-and-scene-regressions
fixed_at: 2026-11-02T16:45:17Z
review_path: .planning/phases/GB-21-cgb-game-progress-and-scene-regressions/21-REVIEW.md
iteration: 1
findings_in_scope: 3
fixed: 3
skipped: 0
status: all_fixed
---

# Phase GB-21: Code Review Fix Report

**Fixed at:** 2026-11-02T16:45:17Z
**Source review:** `.planning/phases/GB-21-cgb-game-progress-and-scene-regressions/21-REVIEW.md`
**Iteration:** 1

**Summary:**
- Findings in scope: 3
- Fixed: 3
- Skipped: 0

## Fixed Issues

### CR-01: Admitted candidate replay cannot run on the CGB profile

**Files modified:** `tests/scripts/verify-cgb-candidates.py`
**Commit:** `dae8461a`
**Applied fix:** Replay now selects `--model cgb-cpu-e` and parses the runner's acceptance and receipt lines, requiring the actual `profile=CGB-CPU-E` and `execution_mode=cgb` fields.

### CR-02: Replay accepts a runner that only prints success markers

**Files modified:** `tests/scripts/verify-cgb-candidates.py`
**Commit:** `e581ecbe`
**Applied fix:** Replay binds both recorded runner hashes to the supplied executable, checks that the executable did not change during replay, and strictly parses the CGB acceptance and receipt field sets. It compares the emitted case, ROM, input, predicate, profile, mode, budget, and pass outcome with the pinned case and admitted record. Synthetic controls reject an executable hash mismatch and a marker-only runner whose hash is otherwise recorded as valid.

### CR-03: Replay executes mutable case and input files instead of their pinned blobs

**Files modified:** `tests/scripts/verify-cgb-candidates.py`
**Commit:** `d24e4c66`
**Applied fix:** Validation now compares the working-tree case and input bytes with the exact Git blobs named by the admitted receipt before the optional replay. Synthetic controls mutate each working copy and confirm validation rejects it before invoking the runner.

## Verification

All checks ran in the isolated Phase 21 review-fix worktree. The controls used only generated synthetic records, a synthetic ROM, and a synthetic runner; no candidate game ROM, candidate upstream build code, or actual third-party source was run or used.

- `python3 -c "import ast; ast.parse(open('tests/scripts/verify-cgb-candidates.py').read())"` — passed after each finding.
- `git diff --check` — passed after each finding.
- `python3 tests/scripts/verify-cgb-candidates.py --self-test-controls` — passed after CR-01 with 30 synthetic negative controls, after CR-02 with 32, and after CR-03 with 34.

---

_Fixed: 2026-11-02T16:45:17Z_  
_Fixer: the agent (gsd-code-fixer)_  
_Iteration: 1_
