---
phase: 07-dmg-game-acceptance-and-regression-baseline
plan: 13
subsystem: testing
tags: [baseline, comparator, cmake-script, junit, negative-controls, evid-02]

requires:
  - phase: 07-11
    provides: runner --observe output for acceptance and Mooneye, expected-tests inventories
provides:
  - cmake/VerifyDmgBaseline.cmake text-only comparator with check, print-candidate and junit modes
  - tests/scripts/verify-dmg-baseline.sh single entry point (delegates through cmake -P, no logic of its own)
  - Synthetic self-test fixtures under tests/baseline/selftest/
  - Twenty dmg_baseline_* CTest names, a registered control for every failure token
affects: [07-14, 07-15, 07-16]

status: complete
actuals:
  tokens: 21000
  tasks: 3
  commits: 5
plan_head_before: 1d44abc0a60018998b96fd9cb3c521cc818132df
plan_head_after: 674c3d6f9075d1258fd43aa19abb68925f5f793e

tech-stack:
  added: []
  patterns:
    - "Ledgers are key<TAB>value lines in LC_ALL=C order; frozen_body_sha256 anchors the whole non-header body"
    - "No update mode: print-candidate writes stdout only, so a baseline moves only by a reviewed ledger edit plus a CHANGES row"
    - "CMake map idiom: ${prefix}V_<key> variables from gbb_parse_text, shared by body hashing and reverse-apply"

key-files:
  created:
    - cmake/VerifyDmgBaseline.cmake
    - tests/scripts/verify-dmg-baseline.sh
    - tests/baseline/selftest/observed.txt
    - tests/baseline/selftest/ledger.txt
    - tests/baseline/selftest/CHANGES.md
    - tests/baseline/selftest/junit.xml
  modified:
    - tests/CMakeLists.txt
    - tests/expected-tests.txt

key-decisions:
  - "Structural failures (empty-ledger, malformed-line, duplicate-key, unsorted-ledger, header-invalid, empty-section, empty-observations) stop with one 'baseline status=fail <tokens>' line before the category lines; diff and changes findings use the per-category lines"
  - "Category findings print as kind:key tokens (modified:, missing:, extra:, removed:), so a control's regex matches only its own cause"
  - "Rows with empty reason/evidence/approver, wrong cell count, a header key, or a missing CHANGES file report changes-inconsistent (no new token, no extra control)"
  - "CMake regexes lack {n} quantifiers, so hex lengths (40, 64) are checked with string(LENGTH)"
  - "Observed or ledger values containing a semicolon are rejected as malformed-line (CMake list element split)"

requirements-completed: [EVID-02]

coverage:
  - id: D1
    description: "Comparator recomputes live observations and prints a sorted candidate ledger to stdout only"
    requirement: EVID-02
    verification:
      - kind: integration
        ref: "bash tests/scripts/verify-dmg-baseline.sh --print-candidate (332 lines, LC_ALL=C sort -c clean, 237 inventory.core lines, one pcm_sha256 line)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Check mode, approved-change protocol and JUnit mode each have a registered failing control per failure token"
    requirement: EVID-02
    verification:
      - kind: unit
        ref: "ctest --test-dir build -R '^dmg_baseline_' (20/20)"
        status: pass
      - kind: integration
        ref: "ctest --test-dir build (257/257)"
        status: pass
    human_judgment: false

duration: 75min
completed: 2026-10-10
---

# Phase 07 Plan 13: DMG Baseline Comparator Summary

**A cmake -P baseline comparator (check, print-candidate, junit) behind one bash entry point, with all 17 failure tokens proven to fire by 20 registered CTest controls and no ledger-rewriting mode.**

## Accomplishments

- print-candidate recomputes the acceptance and Mooneye observations through `gabbaboy-runner --observe`, the tracer `measure_core` digest and workload, and both inventories, then prints a sorted candidate to stdout. It never writes `GBB_LEDGER` (acceptance grep counts of `--update` and ledger `file(WRITE` are 0).
- check mode: structure and header validation, per-section comparison (modified, missing, extra; inventory is a monotonic superset reporting `removed`), and the CHANGES protocol (noop, inconsistent, reverse-apply to `frozen_body_sha256`, else `unrecorded-change`).
- junit mode: every frozen inventory name needs a testcase with no skipped, failure or error child (`junit-missing`, `junit-skipped`, `junit-failed`). Applying it to real CI reports belongs to Plan 07-15.

## TDD record

- Task 1 (tracer): implemented check (without the CHANGES protocol) and print-candidate; `dmg_baseline_selftest_pass` passed. Commit 6cee9c8.
- Task 2 RED (196c683): 16 tests registered. 13 passed immediately because the tracer already implemented those categories (characterization controls; each was also run by hand and printed its own token). Three genuine REDs: `changes_unrecorded`, `changes_noop`, `changes_inconsistent` failed with "expected exit code 1 but the command returned '0'" (CHANGES protocol absent, semantic assessment: the target tests ran and failed on the planned assertion). GREEN 57a7fea.
- Task 3 RED (9ee1a62): four junit tests failed with `unknown-mode GBB_MODE=junit` (target ran, intended behavior absent). GREEN 674c3d6.
- No refactor commit.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Body hash read the wrong variables**
- **Found during:** Task 2 GREEN (`changes_unrecorded` kept passing)
- **Issue:** `gbb_body_text` was called with prefix `OV`/`WV`, so it read `OVV_<key>`/`WVV_<key>` (undefined); every body hashed as empty values and the first self-test ledger digest was meaningless.
- **Fix:** Call with prefixes `O` and `W`; regenerated the self-test ledger digest and confirmed it against an independent Python SHA-256 of the sorted observed lines (02b87043...819f).
- **Files modified:** cmake/VerifyDmgBaseline.cmake, tests/baseline/selftest/ledger.txt
- **Commit:** 57a7fea

**2. [Rule 1 - Bug] changes_inconsistent variant built a no-op row**
- **Found during:** Task 2 GREEN
- **Issue:** Variant row had old equal to new, so it exercised `changes-noop` instead of `changes-inconsistent`.
- **Fix:** Row now has old `cccc...`, new `bbbb...` against ledger value `aaaa...`.
- **Files modified:** tests/CMakeLists.txt
- **Commit:** 57a7fea

**3. [Rule 3 - Blocker] CMake regex limits**
- `{40}`/`{64}` quantifiers are unsupported; lengths are checked with `string(LENGTH)`. A semicolon in the synthetic `coverage` value also split a list element; the value now uses a comma and `;` in ledgers is rejected explicitly.

**4. Task 1 scope split.** To get genuine REDs, Task 1 implemented check mode without the CHANGES protocol (printing `baseline changes=skipped`); Task 2 completed it. Net result matches the plan.

**Total deviations:** 4 (2 bugs, 1 blocker, 1 sequencing). **Impact:** none on scope; the hashing bug was caught by the negative control it was meant to protect.

## Known limitations and notes for later plans

- `inventory.core.*` observations are the full `tests/expected-tests.txt`, including the `installed_*` names that `.github/scripts/verify-test-inventory.sh --core-only` strips. Plan 07-15 must account for this when it applies junit mode to CI core reports (core reports without an installed prefix would report `junit-missing`).
- `tests/scripts/verify-dmg-baseline.sh` check/junit modes use the default ledger `tests/baseline/dmg-cpu-b-v1.txt`, which does not exist until the 07-15 freeze; before that they correctly fail with `empty-ledger`. The wrapper has no ledger override by design; self-tests call the cmake script directly.
- The `coverage` candidate line is a placeholder for the freeze to replace; it is a header key excluded from the body hash.
- No stubs, no threat flags (no new network, auth or file-trust surface).

## Verification evidence

- `ctest --test-dir build -R '^dmg_baseline_'`: 20/20 pass; `-N` reports Total Tests: 20; `grep -c '^dmg_baseline_' tests/expected-tests.txt` = 20.
- Full suite: `ctest --test-dir build --no-tests=error -j4`: 257/257 pass.
- `bash tests/scripts/verify-dmg-baseline.sh --print-candidate | grep -c acceptance.libbet.pcm_sha256` = 1; output is `LC_ALL=C` sorted and starts with the required keys.

## Self-Check: PASSED

- Files exist: cmake/VerifyDmgBaseline.cmake, tests/scripts/verify-dmg-baseline.sh, tests/baseline/selftest/{observed.txt,ledger.txt,CHANGES.md,junit.xml}.
- Commits in history: 6cee9c8, 196c683, 57a7fea, 9ee1a62, 674c3d6.
