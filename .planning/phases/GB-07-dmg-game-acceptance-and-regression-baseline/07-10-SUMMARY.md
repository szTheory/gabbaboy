---
phase: 07-dmg-game-acceptance-and-regression-baseline
plan: 10
subsystem: testing
tags: [acceptance, controls, mutation, joypad, libbet, strict-xfail]

requires:
  - phase: 07-08
    provides: strict model_fail/xfail semantics and suite counting
  - phase: 07-17
    provides: unchanged JOYP anchor line and Start-tap timing
provides:
  - N1 libbet-no-input and N2 libbet-select strict-xfail control cases with raw-verdict assertions
  - --raw-verdict and --mutate drop:<BUTTON> runner options; final_* state fields on non-pass lines
  - test-only JOYP core mutant library and runner built from an exact-once anchor replace
affects: [07-15, 07-16]

status: complete
actuals:
  tokens: 9000
  tasks: 2
  commits: 2
plan_head_before: 7330094dad50b92a0b67c5e4e0a8c110eb3ae0c7
plan_head_after: 7d0c394bee16564b8a0b31ee55e0a8ed15de8fbf

tech-stack:
  added: []
  patterns:
    - "Raw verdict and strict-xfail mapping asserted separately per control"
    - "Configure-time exact-once source replace into a generated, never-installed mutant target"

key-files:
  created:
    - tests/acceptance/inputs/libbet-no-input.input
    - tests/acceptance/inputs/libbet-select.input
  modified:
    - tests/acceptance/cases.txt
    - tests/acceptance/CMakeLists.txt
    - tests/expected-tests.txt
    - src/runner/acceptance.c
    - src/runner/acceptance.h
    - src/runner/main.c

key-decisions:
  - "Control CTest regexes match the real status line (status=fail model=dmg-cpu-b reason=...) instead of the plan's shortened form, leaving the existing output format unchanged"
  - "final_* fields print on every predicate-run non-pass line, not only under --receipt, so a failure always shows the reached state"

requirements-completed: [GAME-02]

coverage:
  - id: D1
    description: "No-input and SELECT-instead-of-START runs exit 1 raw with reason=predicate-not-reached and map to strict xfail exit 0; suite counts xfail=2"
    requirement: GAME-02
    verification:
      - kind: integration
        ref: "ctest acceptance_libbet-no-input_raw, acceptance_libbet-select_raw, acceptance_libbet-no-input, acceptance_libbet-select, acceptance_suite"
        status: pass
    human_judgment: false
  - id: D2
    description: "Dropped-START run and JOYP-inverted core mutant both exit 1 with reason=predicate-not-reached"
    requirement: GAME-02
    verification:
      - kind: integration
        ref: "ctest acceptance_libbet_drop_start, acceptance_core_mutant"
        status: pass
    human_judgment: false

duration: 35min
completed: 2026-10-10
---

# Phase 7 Plan 10: Acceptance discrimination controls Summary

**Four control runs now prove the Libbet gate can fail: no input and SELECT-for-START exit 1 raw and map to strict xfail, a dropped START exits 1, and a core with the JOYP select test inverted (built into a test-only library and runner) exits 1 - all with reason=predicate-not-reached.**

## Accomplishments

- N1 (`libbet-no-input`, no button events) ends with attract mode 0 and a zeroed floor; N2 (`libbet-select`) reaches attract mode (`final_attract=04`, score 00/14) and still never clears the tutorial. Both lines are `model_fail=dmg-cpu-b expect_fail_reason=predicate-not-reached`, budget 1200f.
- `--raw-verdict` (`--case` only; `raw-verdict-requires-case` otherwise) skips the D-22 mapping so the same run prints `status=fail` and exits 1 with `raw_verdict=1`. Each control has two CTests, the raw exit-1 assertion and the strict-xfail exit-0 mapping; neither replaces the other. A pass would be unexpected-pass exit 1 (07-08 semantics, unchanged).
- Non-pass predicate lines carry `final_hw/attract/floor/score/size` read from guest RAM after the run.
- `--mutate drop:<BUTTON>` (case and suite, not `--observe`; `invalid-mutate` for anything else) removes that button's press and release events after script validation and before replay.
- `tests/acceptance/CMakeLists.txt` reads `src/core/gabbaboy.c`, requires `if ((m->joypad_select & 0x20u) == 0)` exactly once (forward/reverse FIND must agree, else configure fails naming `core-mutant pattern`), writes the `!= 0` copy to the build tree, and builds `gabbaboy_core_joyp_mutant` plus `gabbaboy-runner-joyp-mutant`. Nothing is installed and `GabbaBoy::core` is untouched; `src/core/gabbaboy.c` has no diff.
- `acceptance_suite` now expects `suite eligible=3 executed=3 excluded=0 xfail=2 status=pass` with `--expect-excluded 0`.

## Task Commits

1. **Task 1: no-input and SELECT controls (tracer)** - `8d7699d` (feat)
2. **Task 2: dropped-START and JOYP core-mutant controls** - `7d0c394` (feat)

## Decisions Made

- Applicability of the controls is dmg-cpu-b only (the only executable model this phase); the expected-failure reason is the single declared reason, so any other failure class exits 1.
- Tracer gate: Task 1's `<verify>` was run and passed before Task 2 expanded (auto-mode off, `end-of-phase`, automated-only verify).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Control regexes use the real status-line form**
- **Found during:** Task 1
- **Issue:** The plan's regex `status=fail reason=predicate-not-reached` cannot match the existing line `status=fail model=dmg-cpu-b reason=...`, which the 07-08 xfail format and existing tests already use.
- **Fix:** Regexes read `status=fail model=dmg-cpu-b reason=predicate-not-reached` (and the xfail equivalent). The status line format is unchanged. The plan's acceptance `grep` and exit-code assertions are otherwise as written.
- **Files modified:** tests/acceptance/CMakeLists.txt
- **Verification:** all six control tests pass.
- **Committed in:** 8d7699d

**Total deviations:** 1 auto-fixed (Rule 3). **Impact:** wording only; no behavior change.

## Issues Encountered

None. The mutant and the real core were both exercised: the real core passes `acceptance_libbet`, the mutant exits 1 on the same case, and the generated copy differs from the source by exactly the one `==` to `!=` line.

## Verification Run

- `cmake --preset phase1 && cmake --build --preset phase1`: clean.
- `ctest -R '^acceptance_(libbet-no-input|libbet-select|libbet-no-input_raw|libbet-select_raw|suite)$'`: 5/5 pass (Task 1).
- `ctest -R '^acceptance_(libbet|core_mutant|suite)'`: 15/15 pass (Task 2).
- `ctest -N -R` over the six control names: `Total Tests: 6`.
- Full `ctest --test-dir build --no-tests=error -j4`: 235/235 pass (includes the expected-tests inventory check).
- Manual: `--case libbet-select --receipt` prints `status=xfail ... final_attract=04`, rc 0; with `--raw-verdict` rc 1; `--suite --raw-verdict` rc 2; `--mutate drop:X` rc 2.
- `grep -c 'install(' tests/acceptance/CMakeLists.txt` is 0; `git diff --quiet src/core/gabbaboy.c` clean.

## Known Stubs

None.

## Threat Flags

None. T-07-20: mutant is a test-only static library and runner, never installed or linked into `GabbaBoy::core`; configure fails if the anchor is absent or repeated. T-07-42: six named control assertions in the inventory.

## Next Phase Readiness

Controls are in place for the Plan 07-16 docs (`docs/game-acceptance.md` should state the raw-exit-1 versus xfail-mapping split). The GAME-02 discrimination claim holds locally; remote CI evidence is out of scope for this plan.

## Self-Check: PASSED

- Commits 8d7699d and 7d0c394 are ancestors of HEAD; both input scripts and this file exist.
