---
phase: GB-21-cgb-game-progress-and-scene-regressions
plan: "02"
subsystem: testing
tags: [CGB, acceptance-runner, RGB555, PCM, source-pinned-evidence]
requires:
  - phase: GB-21-cgb-game-progress-and-scene-regressions
    provides:
      - Native CGB progress tracer and loaded-mode refusal control
      - Synthetic-only candidate evidence contracts
provides:
  - Discriminating CGB progress controls for missing input, wrong input, and impossible predicates
  - Same-run observation and receipt binding with independent RGB555 checkpoint and PPM checks
  - Fresh bounded RGB555 failure-image control with stale-image rejection
affects: [GB-21-04, GB-21-05, GB-21-07, CGB progress evidence]
actuals:
  tokens: 13440.5
  tasks: 2
  commits: 6
tech-stack:
  added: []
  patterns:
    - Source-pinned runner evidence carries exact ROM, input script, predicate, mode, budget, checkpoint, PCM, and build identities
    - Independent source-authored RGB555 colors validate pixels; reruns establish reproducibility only
key-files:
  created:
    - .planning/phases/GB-21-cgb-game-progress-and-scene-regressions/deferred-items.md
  modified:
    - src/runner/acceptance.c
    - tests/scripts/verify-cgb-progress.py
    - tests/acceptance/CMakeLists.txt
    - tests/acceptance/cases-cgb-colour.txt
    - tests/test_acceptance_lib.c
    - tests/expected-tests.txt
    - tests/ci/test-budget-allowlist
key-decisions:
  - "Emit the CGB receipt alongside --observe so both records describe the same runner execution; compare a separate repeat only for reproducibility."
  - "Keep all newly added CGB tests within the existing 60-second policy and remove the allowlist entry for the retired refusal test."
patterns-established:
  - "CGB evidence controls use generated original ROM/input data in private temporary directories and validate source identity before runner execution."
  - "Checkpoint PPMs are checked byte-for-byte against independently authored RGB555 colors, including failure-image freshness."
metrics:
  duration: 25min
  completed: 2026-11-02
status: complete
commits: 6
plan_head_before: a7578d9aea32022b3db2ff5ac8d8929395dbbc6f
plan_head_after: 703d8f84e134b3330241084c376a16273f88395a
requirements-completed: [GAME-01, GAME-02]
coverage:
  - id: D1
    description: Native CGB progress requires the intended RIGHT input and predicate; no-input, LEFT input, and impossible-predicate cases fail for predicate-not-reached.
    requirement: GAME-01
    verification:
      - kind: unit
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^acceptance_predicate_cgb_(truth_table|anchors)$'"
        status: pass
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^acceptance_cgb_progress_discrimination$'"
        status: pass
    human_judgment: false
  - id: D2
    description: Native CGB receipts and sorted observations bind the same run's identities, times, RGB555 digests, PCM results, and independently checked checkpoint/failure PPM pixels.
    requirement: GAME-02
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^acceptance_cgb_progress_observations$'"
        status: pass
      - kind: other
        ref: "python3 -I tests/scripts/verify-cgb-progress.py --self-test --repo-root ."
        status: pass
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^(acceptance_digest_rgb555_vectors|cgb_runner_profile_dmg_identity_acceptance|dmg_baseline)$'"
        status: pass
    human_judgment: false
---

# Phase GB-21 Plan 21-02: CGB Progress Discrimination and Observation Summary

**CGB progress now rejects vacuous and wrong-input success while binding same-run receipts, checkpoint pixels, timing, and PCM to source-qualified observations.**

## Performance

- **Duration:** 25 minutes
- **Started:** 2026-11-02T02:41:19Z
- **Completed:** 2026-11-02T03:06:11Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- Added real-runner controls proving the authored native-CGB positive requires RIGHT input and the registered progress predicate. Missing input, LEFT instead of RIGHT, and the impossible predicate fail as `predicate-not-reached`; strict expected-failure and unexpected-pass behavior are checked separately.
- Added CGB predicate truth-table and source-anchor tests. Removed the obsolete colour-progress refusal registration and retained the Libbet case with the corrected generated compatibility-control semantics. The DMG baseline remains unchanged.
- Bound CGB observation rows and receipts to the same execution. Both include ROM and script identities, predicate, CGB mode/profile, frame format, budget and hit/end times, requested/completion checkpoint times and digests, rolling digest, PCM digest/sample count/audibility, and build revision/qualification.
- Independently checked every checkpoint PPM against the authored uniform RGB555 sequence: `0x001f` before input and `0x03e0` after RIGHT input. A second run checks reproducibility separately. A stale CGB failure image is replaced with a bounded RGB555 PPM matching the no-input blue frame.
- Added mutation controls for identity, times, digests, PCM fields, stale/missing/wrong-format dumps, altered expected colors, stale source revisions, and missing committed source evidence.

## TDD Gate Compliance

- **Task 1 RED:** Commit `86920a1b` added the discrimination assertion. The intended CTest failed because the checker lacked the wrong-input evidence marker; raw JUnit is retained at `build/gsd/21-02-task1-red.xml`, and `gsd_run check tdd-red-evidence` returned `RED_EVIDENCE_OK`.
- **Task 1 GREEN:** Commit `1946284e` added no-input, wrong-input, impossible-predicate, strict-xfail, and unexpected-pass controls. The focused CGB tracer/mode/predicate/color selection passed, including the positive route and all intended negative outcomes.
- **Task 2 RED:** Commit `30cb5f80` added the observation-contract assertion. Its intended CTest failed because the checker did not yet emit the observation marker; raw JUnit is retained at `build/gsd/21-02-task2-red.xml`, and the evidence classifier returned `RED_EVIDENCE_OK`. The independent checker-control self-test passed.
- **Task 2 GREEN:** Commits `cd6bca0f`, `ec5c361a`, and `703d8f84` completed receipt/dump validation and corrected the test-budget and stale-source controls. The final source-pinned CGB tests, DMG baseline, profile identity, and RGB555 digest vectors passed.

## Source-Qualified Evidence

The final runner/checker CTests used the committed source revision recorded by CMake. The generated control ROM digest is `17822873ec8641280d9504229d96850414e872bc90de5431469a498e5271db7e`; the positive RIGHT script digest is `0ccfce12e082a0d6bf52ee6a0867b62beb096f5b9403d715e0c5b354c3b14fc2`.

- Raw final focused-run evidence: `build/gsd/21-02-task2-green.xml`.
- The source-authored control sets palette color zero to `0x001f` before input and `0x03e0` after RIGHT. The checker independently expands the 5-bit channels and compares every PPM pixel as well as the canonical RGB555 digest.
- PCM observations truthfully report samples and digest with `pcm_audible=false` and zero channel changes/peak-to-peak values.
- The fixed CGB test timeouts are at most 60 seconds. No test-budget allowlist entry was added.

## Checks Run

- `cmake --preset phase1` and `cmake --build --preset phase1` passed after the task commits.
- `python3 -I tests/scripts/verify-cgb-progress.py --self-test --repo-root .` passed observation, identity, timing, digest, PCM, dump, and source-revision mutation controls.
- The final focused CTest selection ran 12 tests: all 10 CGB, RGB555, profile-identity, and DMG-baseline tests passed; `test_budget_controls` passed. `test_budget` failed only on the unrelated existing `phase21_fixture_admission_contract` (120 s) and `phase21_fixture_admission_controls` (180 s) timeout declarations, which exceed the current 60-second policy without allowlist rows. The CGB tests added here no longer trigger a budget finding.
- The full suite was not run; final full-suite/platform qualification remains assigned to Plan 21-07.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Keep the registered CTest inventory synchronized**
- **Found during:** Task 1 configure
- **Issue:** CMake's required test inventory rejected the new CGB predicate tests until their names were added and the retired test name removed.
- **Fix:** Updated `tests/expected-tests.txt` with the added truth-table/anchor tests and removed obsolete refusal registration.
- **Files modified:** `tests/expected-tests.txt`, `tests/acceptance/CMakeLists.txt`
- **Commit:** `1946284e`

**2. [Rule 1 - Bug] Fix receipt emission scope and source-revision control**
- **Found during:** Task 2 build and source-bound CTest
- **Issue:** The new same-run receipt branch referenced a block-local policy variable, and the first stale-source negative control assumed `HEAD^` differed even when a follow-up commit reused the same checker.
- **Fix:** Check the predicate policy directly and select an actual ancestor containing different checker bytes.
- **Files modified:** `src/runner/acceptance.c`, `tests/scripts/verify-cgb-progress.py`
- **Commits:** `cd6bca0f`, `703d8f84`

**3. [Rule 3 - Blocking] Align CGB tests with the existing budget policy**
- **Found during:** Task 2 focused verification
- **Issue:** The new tests used 90-second timeouts and the retired CGB refusal test still had a stale allowlist row.
- **Fix:** Bound the new CGB tests to 60 seconds and removed the obsolete allowlist row. Recorded the remaining unrelated Phase 21 fixture timeout failures for their owning work.
- **Files modified:** `tests/acceptance/CMakeLists.txt`, `tests/ci/test-budget-allowlist`, `.planning/phases/GB-21-cgb-game-progress-and-scene-regressions/deferred-items.md`
- **Commit:** `ec5c361a`

**Total deviations:** 3 auto-fixed. No product scope or candidate attempts were added.

## Issues and Limitations

- The `test_budget` failure is deferred because both over-budget fixture admission tests belong to other Phase 21 work. Details are recorded in [deferred-items.md](deferred-items.md); this plan did not change their timeouts or add budget exceptions.
- The plan's flagged GAME-02 edge probe remains unclassified. These discrimination and identity controls do not claim exhaustive edge classification.
- CMake reported that a matching Clang libFuzzer runtime was unavailable; deterministic sanitizer regressions remained enabled.

## Task Commits

1. **Task 1 RED — CGB discrimination assertion** — `86920a1b`
2. **Task 1 GREEN — wrong-input and strict-failure controls** — `1946284e`
3. **Task 2 RED — observation contract assertion** — `30cb5f80`
4. **Task 2 GREEN — bound CGB observations and checkpoint dumps** — `cd6bca0f`
5. **Budget correction and deferred issue record** — `ec5c361a`
6. **Source-revision mutation control correction** — `703d8f84`

## Threat Flags

None. Changes extend test-runner evidence output and checker behavior; they add no public API, network route, or persistent guest image.

## Next Phase Readiness

Plan 21-02 is complete. The source-bound progress controls do not decide either candidate attempt or claim game compatibility. No later plan or phase was started.

---
*Phase: GB-21-cgb-game-progress-and-scene-regressions*
*Completed: 2026-11-02*

## Self-Check: PASSED

- Summary file exists at the planned phase path.
- All six measured task commits are ancestors of the current plan head.
- The measured ledger base, plan head, commit count, and automated coverage metadata match the repository state.
