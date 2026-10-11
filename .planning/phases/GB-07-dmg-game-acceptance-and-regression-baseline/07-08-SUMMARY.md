---
phase: 07-dmg-game-acceptance-and-regression-baseline
plan: 08
subsystem: testing
tags: [acceptance, applicability, xfail, suite, exclusion, runner-cli]

requires:
  - phase: 07-07
    provides: --observe surface and observe-only flag rejection
provides:
  - gbb_case_applicability (expect-pass, strict expect-fail, unsupported-model and target-revision exclusions)
  - Runner --suite with mandatory --expect-excluded, --model, --revision, exit 4
  - Strict xfail / unexpected-pass handling for model_fail cases
  - Eleven named CTests and two negative case files
affects: [07-09, 07-10, 07-15]

status: complete
actuals:
  tokens: 9000
  tasks: 2
  commits: 3
plan_head_before: 48fdd296d02b6e21e3bbe6569b404e0f1b9c20d6
plan_head_after: e92498850e9eab6f655bb02eebe4e00193024cb1

tech-stack:
  added: []
  patterns:
    - "Declared-exclusion denominator: suite verdict compares the excluded count with the count registered at CTest time"
    - "Exclusion is exit 4 with its own reason; CTest's skip-return-code mechanism is never used"

key-files:
  created:
    - tests/acceptance/negative/suite-exclusion.txt
    - tests/acceptance/negative/applicability.txt
  modified:
    - src/runner/acceptance.h
    - src/runner/cases.c
    - src/runner/acceptance.c
    - src/runner/main.c
    - tests/acceptance/CMakeLists.txt
    - tests/verify_runner_help.cmake
    - tests/expected-tests.txt

key-decisions:
  - "Enum type is gbb_case_applicability_kind because a typedef cannot share the function name gbb_case_applicability"
  - "Model applicability is decided before target revision; model_fail wins over model_pass; only dmg-cpu-b executes (cgb-cpu-e eligible case exits 3 unsupported-profile)"

requirements-completed: [EVID-01]

coverage:
  - id: D1
    description: "Exclusions (unsupported-model, target-revision) exit 4 with their reason; unknown model exits 2"
    requirement: EVID-01
    verification:
      - kind: integration
        ref: "ctest -R '^acceptance_(libbet_excluded_cgb-cpu-e|libbet-cgb-only_excluded_dmg-cpu-b|target_revision_excluded|unknown_model)$'"
        status: pass
    human_judgment: false
  - id: D2
    description: "Suite fails unless excluded count equals the declared --expect-excluded; undeclared exclusion is a registered negative control"
    requirement: EVID-01
    verification:
      - kind: integration
        ref: "ctest -R '^acceptance_suite'"
        status: pass
    human_judgment: false
  - id: D3
    description: "Strict expected failure: unexpected pass exits 1; observe-only flags without --observe exit 2; help lists the new usage lines"
    requirement: EVID-01
    verification:
      - kind: integration
        ref: "ctest -R '^(acceptance_(unexpected_pass|observe_only_flag)|runner_help)$'"
        status: pass
    human_judgment: false
---

# Phase 7 Plan 08: Model applicability and declared-exclusion suite Summary

**The runner now decides expect-pass, strict expect-fail, unsupported-model and target-revision per case (exit 4 for exclusions), and `--suite` fails unless its excluded count equals the `--expect-excluded` count declared at CTest registration, with a registered negative control proving a silently excluded case is caught.**

## Accomplishments

- `gbb_case_applicability(c, model, revision)` in `src/runner/cases.c` returns `GBB_CASE_EXPECT_PASS | EXPECT_FAIL | EXCLUDED_MODEL | EXCLUDED_REVISION`; `gbb_case_model_known` accepts `dmg-cpu-b` and `cgb-cpu-e`.
- `--case` on an excluded case prints `status=excluded reason=unsupported-model|target-revision` and exits 4. An eligible non-dmg model exits 3 `unsupported-profile`.
- `--suite --expect-excluded <n>` runs cases in file order and prints `suite eligible= executed= excluded= xfail= status=`. Failure reasons: `no-eligible-cases`, `excluded-count-mismatch expected=<n> observed=<m>` (exit 1). Missing flag exits 2 `expect-excluded-required`; malformed or above 128 exits 2 `invalid-expect-excluded`.
- `model_fail` cases are strict: the declared `expect_fail_reason` prints `status=xfail` (counts toward xfail, exit 0); a pass prints `status=unexpected-pass` (exit 1); any other failure reason stays exit 1.
- Observe-only flags without `--observe` exit 2 `reason=observe-only-flag`; unknown `--model` exits 2 `reason=unknown-model`; `--model/--revision/--expect-excluded` outside `--acceptance` are rejected.
- `--help` lists the acceptance and observe usage lines; `runner_help` requires both plus the two manifest lines.
- Model applicability declaration: this phase executes only `dmg-cpu-b` (DMG-CPU-B software model, regression class). `cgb-cpu-e` is a recognised token but excluded or unsupported-profile; no CGB behavior is claimed.

## TDD Gate Compliance

- **RED (Task 1):** `c7d5f6b` registered six tests; all six failed (unknown flags exit 2 `invalid-arguments`, or missing regex on the exit-2 test). Semantic assessment: targets ran and failed for the planned reason (feature absent).
- **GREEN (Task 1):** `14e84e7`; the six pass. Because the tracer implemented the whole applicability and CLI surface, Task 2 behavior already existed.
- **Task 2 RED not observable:** the new tests passed on first run (unexpected green, investigated). Substitute evidence: two scratch mutations (unexpected-pass printed as `pass`; revision comparison disabled) made `acceptance_unexpected_pass` and `acceptance_target_revision_excluded` fail; files restored with `git checkout -- <file>`. Commit `e924988` is therefore `test(...)` only. REFACTOR: none.

## Deviations from Plan

**1. [Rule 1 - Bug] target_revision=dmg-cpu-b-rev-x is rejected by the case parser**
- **Found during:** Task 2 planning
- **Issue:** the parser requires a 40 or 64 digit lowercase hex `target_revision` (`bad-revision`), so the literal value in the plan would exit 2.
- **Fix:** `libbet-rev-x` uses `target_revision=0123456789abcdef0123456789abcdef01234567`, which differs from the effective revision `dmg-cpu-b`, so exclusion still triggers.
- **Files modified:** tests/acceptance/negative/applicability.txt

**2. [Rule 3 - Blocking] Enum typedef name collides with the function name**
- **Fix:** typedef is `gbb_case_applicability_kind`; function keeps the plan name `gbb_case_applicability`.

**3. [Rule 2 - Missing critical] Test for invalid-expect-excluded**
- Added `acceptance_suite_invalid_expect_excluded` (exit 2) so the malformed-count reason has a named test; eleven names total instead of ten.

**4. Plan acceptance wording:** `grep -c SKIP_RETURN_CODE` must be 0; a code comment initially spelled the token and was reworded. `verify-test-inventory.sh` was run with `--installed` because the phase1 preset also executes the `installed_*` tests (the default `--core-only` mode strips them from the expected list and reports them as extra).

**Total deviations:** 4 (1 bug, 1 blocking, 1 critical addition, 1 procedural). **Impact:** none on scope.

## Verification Run

- `cmake --preset phase1 && cmake --build --preset phase1 && ctest -R '^acceptance_(libbet_excluded|libbet-cgb-only_excluded|suite)'`: 6/6 pass.
- `ctest -R '^(acceptance_(target_revision|unexpected_pass|unknown_model|observe_only|suite_invalid)|runner_help)'`: 6/6 pass.
- Full `ctest -j4`: 225/225 pass; `verify-test-inventory.sh build/ctest.xml tests/expected-tests.txt --installed` reports 225 executed, none skipped.
- Acceptance greps: `SKIP_RETURN_CODE` 0 in both CMake files; `gbb_case_applicability` present in cases.c; `--expect-excluded` 4 lines in tests/acceptance/CMakeLists.txt and 1 in verify_runner_help.cmake; `build/gabbaboy-runner --acceptance tests/acceptance/cases.txt --case libbet --model cgb-cpu-e` exits 4; `ctest -N` reports Total Tests: 4 for the four Task 2 names.

## Known Stubs

None.

## Threat Flags

None. T-07-35 mitigated (mandatory `--expect-excluded`, `acceptance_suite_undeclared_exclusion`); T-07-36 mitigated (strict xfail, `acceptance_unexpected_pass`).

## Next Phase Readiness

Plan 07-09 can rely on exit 4 semantics and the suite summary line; case files for new games must declare any exclusions at CTest registration.

## Self-Check: PASSED

- Created files present: tests/acceptance/negative/suite-exclusion.txt, tests/acceptance/negative/applicability.txt.
- Commits c7d5f6b, 14e84e7, e924988 are ancestors of HEAD; `commits: 3` measured from the ledger.
