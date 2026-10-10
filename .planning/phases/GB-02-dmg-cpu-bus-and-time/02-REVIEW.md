---
phase: GB-02-dmg-cpu-bus-and-time
reviewed: 2026-10-10T12:51:20Z
depth: standard
files_reviewed: 2
files_reviewed_list:
  - .github/workflows/ci.yml
  - .gitignore
findings:
  critical: 0
  warning: 0
  info: 1
  total: 1
status: issues_found
---

# Phase 2: Code Review Report (verification-freshness re-review)

**Reviewed:** 2026-10-10T12:51:20Z
**Depth:** standard
**Files Reviewed:** 2
**Status:** issues_found (one informational item)

## Summary

Incremental review of `git diff b10b5b9 HEAD` for the two Phase 2-owned files, read in the context of the full files. Static inspection only; no remote runs were executed.

Phase 2's CI guarantees are preserved:

- **Test inventory:** The `native-linux`, `native-macos`, `native-windows` and `linux-sanitizers` jobs are unchanged. Each runs `ctest --no-tests=error --output-junit` and then `verify-test-inventory.sh` against `tests/expected-tests.txt`. That script still rejects `<failure>`, `<error>` and `<skipped>` cases (lines 15-21).
- **Required contexts:** `required-native` still needs all five original jobs and requires `success` from each, so skipped, failed and timed-out results are rejected. It runs under `if: always()`.
- **Push vs pull_request:** The `macos-player-package` job is now gated on `github.event_name == 'pull_request'`, and `PLAYER_REQUESTED` uses the same expression. On pull requests the player job must succeed. On pushes it is skipped, and the else-branch accepts `skipped` or `success`. The expression evaluates to the string `true`, which matches the `== true` shell comparison. No path lets a failed or cancelled player job pass.
- **Trigger narrowing:** Dropping `labeled` removes a re-run trigger and shrinks the surface. Nothing else depends on the `run-macos-player` label; the only remaining references are historical planning documents.
- **`.gitignore`:** `__pycache__/` matches the untracked `tests/scripts/__pycache__` and hides no source. `git ls-files` shows no tracked pycache.

The change turns the Phase 3 player lane into a hard dependency of `required-native` on every pull request. This is intended (GB-03) and does not weaken any Phase 2 guarantee, but it widens what can block a Phase 2-style change.

## Narrative Findings (AI reviewer)

### IN-01: Player-gating condition duplicated in two places

**File:** `.github/workflows/ci.yml:123,167`
**Issue:** The `pull_request` condition appears both as the job-level `if:` and as the `PLAYER_REQUESTED` expression. If one is edited without the other, the aggregate could demand `success` from a skipped job. That would fail closed (safe) or, in the opposite drift, accept `skipped` on a pull request. Today they agree, so this is a maintainability note only.
**Fix:** Add a short YAML comment tying the two together. Alternatively, derive `PLAYER_REQUESTED` from one shared source, or require `PLAYER_RESULT == success` whenever `github.event_name == 'pull_request'` directly in the script.

---

_Reviewed: 2026-10-10T12:51:20Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

---

# Prior Review Record (preserved)

The review below was recorded on 2026-10-07 for the original Phase 2 test files and is preserved unchanged.

---
phase: GB-02-dmg-cpu-bus-and-time
reviewed: 2026-10-07T12:21:59Z
depth: standard
files_reviewed: 3
files_reviewed_list:
  - tests/test_cpu.c
  - tests/CMakeLists.txt
  - tests/expected-tests.txt
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 2: Code Review Report

**Reviewed:** 2026-10-07T12:21:59Z
**Depth:** standard
**Files Reviewed:** 3
**Status:** clean

## Summary

The legal base-opcode matrix derives expected values from authored setup state and fixed test ROM contents; it does not seed its oracle from core traces. Conditional branch tests explicitly enumerate all 32 family/condition/outcome combinations, and additional vectors cover arithmetic boundaries, memory effects, and timed observer events. Fixed trace and bus-event buffers are sized for their asserted workloads. CTest names and the required inventory match for the added cases. No correctness or test-reliability defect was found in the scoped files.

## Narrative Findings (AI reviewer)

No findings.

---

_Reviewed: 2026-10-07T12:21:59Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
