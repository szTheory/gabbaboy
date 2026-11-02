---
phase: GB-21-cgb-game-progress-and-scene-regressions
reviewed: 2026-11-02T18:13:04Z
depth: standard
files_reviewed: 25
files_reviewed_list:
  - CMakeLists.txt
  - docs/cgb-game-candidates.md
  - docs/cgb-profile.md
  - docs/game-acceptance.md
  - docs/scene-feedback.md
  - docs/support/unreleased.md
  - src/accept/gbb_accept.h
  - src/accept/predicate.c
  - src/runner/acceptance.c
  - tests/CMakeLists.txt
  - tests/acceptance/CMakeLists.txt
  - tests/acceptance/cases-cgb-colour.txt
  - tests/ci/test-budget-allowlist
  - tests/cmake/game-evidence.cmake
  - tests/data/cgb-candidates/potion-panic.json
  - tests/data/cgb-candidates/ucity-1.3.json
  - tests/data/state-forks.json
  - tests/expected-tests.txt
  - tests/scripts/test_cgb_candidate_order.py
  - tests/scripts/verify-cgb-candidates.py
  - tests/scripts/verify-cgb-game-evidence.py
  - tests/scripts/verify-cgb-progress.py
  - tests/scripts/verify-fixture-admission.py
  - tests/scripts/verify-scene-report.py
  - tests/test_acceptance_lib.c
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
source_revision: abed700d77e490f2de2ea1635234b65b68d2e9d4
status: clean
---

# Phase GB-21: Code Review Report

**Reviewed:** 2026-11-02T18:13:04Z  
**Depth:** standard  
**Files Reviewed:** 25  
**Source boundary:** `abed700d77e490f2de2ea1635234b65b68d2e9d4`  
**Status:** clean

## Summary

The original evaluation scope contained 24 explicit source files and was reported `degraded` solely because the resolver had no task-commit rows; it used `phase-range` from base `a0b81749e19056bf0d8555256e5d64da89017555`. Plan 21-08 adds `CMakeLists.txt` to the phase diff, so this review covered the full 25-file source union. I also inspected the two transitive runner inputs added by CR-06, `src/core/gbb_accept_input.h` and `cmake/StateVersion.cmake`.

All prior review findings are closed at this boundary:

- **CR-01 closed:** replay requires the CGB CPU E model and validates exact acceptance and receipt field sets, CGB profile, native CGB mode, and shared hit time.
- **CR-02 closed:** the supplied runner must match the independently qualified canonical CMake target and stay byte-identical through replay; structured observations are parsed and checked, so success-marker-only output is rejected.
- **CR-03 closed:** replay loads case and input bytes from the admitted historical Git revision and requires the working copies to match before candidate execution.
- **CR-04 closed:** historical receipt source IDs and runner hashes remain immutable. Current replay uses a separate qualification bound to the selected source revision, build qualification, input hashes, writer, canonical runner path, and runner digest.
- **CR-05 closed:** replay compares checkpoint timing/RGB555 and all supported aggregate end-time, rolling RGB555, and PCM values. Synthetic valid-but-changed observations are rejected with the observation-mismatch reason.
- **CR-06 closed:** CMake and Python each contain the same 24 unique runner inputs. The compiled runner dependency closure has no project-local C/C++ input missing from the manifest; the root CMake file's runner-relevant local include is the listed `cmake/StateVersion.cmake`. Both newly added inputs have separate dirty-source and post-qualification drift controls, which verify rejection before runner invocation.

The synthetic control suite passed with 69 negative controls and six positive replay controls. I configured and rebuilt only `gabbaboy-runner` at the exact review boundary, generated its current qualification receipt, and independently validated that receipt at `abed700d`; no candidate game ROM or candidate upstream source was executed. The current receipt binds the exact 24 inputs and the runner artifact. `21-08-SUMMARY.md` now lists only `GAME-02` as completed and explicitly says `FIXT-01` remains Pending; the requirements ledger also retains that pending status.

## Narrative Findings (AI reviewer)

No findings. The reviewed source scope meets the phase contracts at the stated boundary.

---

_Reviewed: 2026-11-02T18:13:04Z_  
_Reviewer: the agent (gsd-code-reviewer)_  
_Depth: standard_

## Supplemental Delta Review

**Reviewed source:** `ca17216b22d0d9f2fb742c8baed3e1543bc307e1`  
**Scope:** the post-review fixture-control optimization in `tests/scripts/verify-cgb-candidates.py`.  
**Status:** clean; no correctness or security findings.

All 17 runner text controls still execute `_run_admitted_candidate` and check their expected rejection codes, including optional validator detail suffixes; this count includes the separate `unqualified-build` mutation. Existing CLI and end-to-end controls remain registered. The focused synthetic control test passed with 69 negative controls and six replay positives. No candidate ROM or upstream source was executed.

The delta review made no source edits.

## Supplemental Delta Review — Windows CMake paths and fixture bytes

**Reviewed source:** `bbd8f8390cb197840ad4091de8bd70170015516a` (delta from `ca17216b22d0d9f2fb742c8baed3e1543bc307e1`).
**Scope:** `tests/scripts/verify-cgb-candidates.py` and `tests/scripts/test_cgb_candidate_order.py`; Windows CMake path matching and synthetic fixture byte serialization are the changed behavior.
**Result at reviewed HEAD:** 1 warning; the current working-diff follow-up below resolves it.

The supplied local full-suite evidence is 1,718/1,718 CTests at this HEAD. That local result does not qualify Windows behavior.

### WARNING — Path keys fold case on case-sensitive filesystems

**File:** `tests/scripts/verify-cgb-candidates.py:2245-2247,2444-2449`
**Issue:** `cmake_source_path_key` case-folds every path, including POSIX paths where case distinguishes files. If a compile database contains distinct case-only source paths, the `next` lookup can select the wrong translation unit and inspect its `GBB_BUILD_QUALIFIED` flag. The new unit control rejects a different suffix, but does not test a case-only neighbor.
**Fix:** Normalize slash styles, then use `os.path.normcase(PureWindowsPath(...).as_posix())` so case folding follows the host platform. Add a case-only neighbor negative control.

The LF-byte changes write the synthetic JSON, case file, runner, and admission pin as explicit bytes, avoiding Windows text-mode newline translation before Git pinning. Existing synthetic fixture controls exercise those files. The Windows path unit control covers slash variants and a non-case-only neighbor. **Pre-existing context:** subprocess timeout cleanup still targets only the direct child, and its unit control uses a single sleeping child; both are unchanged from the prior reviewed source and excluded from delta findings. No Windows qualification is claimed here.

### Follow-up — case-aware path normalization

The current working diff resolves the warning above: `cmake_source_path_key` now applies `os.path.normcase` after slash normalization with `PureWindowsPath`. Its unit control asserts that backslash and forward-slash variants match, a different suffix does not match, case variants match on Windows, and case variants remain distinct on POSIX.

Focused unit evidence after this edit: 11 tests passed. A full CTest rerun is pending. The earlier 1,718/1,718 result predates this working edit and does not qualify it or establish Windows qualification.
