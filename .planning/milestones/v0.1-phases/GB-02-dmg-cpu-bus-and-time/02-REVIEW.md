---
phase: GB-02-dmg-cpu-bus-and-time
reviewed: 2026-10-10T15:55:45Z
depth: standard
files_reviewed: 2
files_reviewed_list:
  - .github/workflows/ci.yml
  - .github/scripts/check-player-result.sh
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 2: Code Review Report (verification-freshness re-review after Phase 06.1)

**Reviewed:** 2026-10-10T15:55:45Z
**Depth:** standard
**Files Reviewed:** 2
**Status:** clean

## Summary

Re-review of `git diff f03e9b1 HEAD -- .github/workflows/ci.yml` (Phase 06.1 PR #54, squash merge ab76d09), read in the context of the full file. `.github/scripts/check-player-result.sh` was read because `required-native` calls it. Static inspection plus a local run of `bash .github/scripts/check-player-result.sh --self-test`, which printed `PASS: player result self-test (14 cases)`. No remote CI was run.

The new `player-gate` job and the `check-player-result.sh` fail-closed logic are correct. No Phase 2 guarantee is weakened.

## Prior findings recheck

**IN-01 (player-gating condition duplicated in two places): resolved.**
- `github.event_name == 'pull_request'` now appears exactly once, at `.github/workflows/ci.yml:136`. It is evaluated inside the `player-gate` job, step `decide`, and exported as the job output `player_required` (`ci.yml:129-130`).
- `macos-player-package` consumes the output at `ci.yml:141` (`needs.player-gate.outputs.player_required == 'true'`).
- `required-native` consumes the same output at `ci.yml:189` (`PLAYER_REQUIRED`).
- The two consumers can no longer drift apart. The comment at `ci.yml:132-133` documents the single source. The expression yields only the literal `true` or `false`, so interpolating it into the `run:` line is not an injection vector.

**Phase 2 inventory guarantees: intact.**
- `native-linux` (`ci.yml:31-34`), `native-macos` (`ci.yml:51-54`) and `native-windows` (`ci.yml:82-86`) each run `ctest --test-dir build --output-on-failure --no-tests=error --output-junit ctest.xml`, then `verify-test-inventory.sh build/ctest.xml tests/expected-tests.txt --installed`.
- `linux-sanitizers` (`ci.yml:106-109`) runs `ctest --preset phase1-asan --output-on-failure --no-tests=error --output-junit ctest.xml`, then `verify-test-inventory.sh build-asan/ctest.xml tests/expected-tests.txt`.
- Under `if: always()` (`ci.yml:167`), `required-native` still requires `success` from native-linux, native-macos, native-windows, linux-sanitizers and cmake-floor-3-25-3 (`ci.yml:192-197`). It also requires `success` from `player-gate`. Skipped, failed, cancelled and timed-out results are rejected.

## Gating-logic verification

- Fail-closed on gate failure: if `player-gate` fails, `macos-player-package` is skipped (its implicit `success()` fails) and `PLAYER_REQUIRED` is empty. This is rejected twice, by the loop at `ci.yml:192-197` and by `check-player-result.sh:13-16`. The self-test rows `failure||skipped`, `cancelled||skipped` and `skipped||skipped` cover this.
- Pull request: `true:success` is the only accepting state. `true:skipped`, `true:failure` and `true:cancelled` hit the `true:*` arm (`check-player-result.sh:19-22`) and fail.
- Push: `false:skipped` and `false:success` are accepted. Any other combination, including an empty `required`, reaches the `*` arm and fails (`check-player-result.sh:23-26`).
- Argument handling: the env values are passed quoted at `ci.yml:198`, so an empty `PLAYER_REQUIRED` still counts as three arguments. The `$# -ne 3` check cannot be bypassed by an empty value. `set -euo pipefail` makes the final `decide` return value the exit status.
- The reported hosted result is consistent with this logic: on the main push, `required-native` passes with `macos-player-package` skipped, because `player_required=false`.

## Narrative Findings (AI reviewer)

No findings.

---

_Reviewed: 2026-10-10T15:55:45Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

---

# Prior Review Record 2026-10-10T12:51:20Z (preserved)

The review below was recorded earlier on 2026-10-10 against `git diff b10b5b9 HEAD`. It is preserved with finding headings demoted to `####` so the disposition parser does not treat them as current findings. IN-01 below is resolved by the recheck above.

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

#### IN-01: Player-gating condition duplicated in two places

**File:** `.github/workflows/ci.yml:123,167`
**Issue:** The `pull_request` condition appears both as the job-level `if:` and as the `PLAYER_REQUESTED` expression. If one is edited without the other, the aggregate could demand `success` from a skipped job. That would fail closed (safe) or, in the opposite drift, accept `skipped` on a pull request. Today they agree, so this is a maintainability note only.
**Fix:** Add a short YAML comment tying the two together. Alternatively, derive `PLAYER_REQUESTED` from one shared source, or require `PLAYER_RESULT == success` whenever `github.event_name == 'pull_request'` directly in the script.

---

_Reviewed: 2026-10-10T12:51:20Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

---

# Prior Review Record 2026-10-07 (preserved)

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
