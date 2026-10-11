---
phase: 07-dmg-game-acceptance-and-regression-baseline
plan: 02
subsystem: testing
tags: [acceptance, gbinput, deadline-stepper, predicate, sha256, libbet, ctest, c17]

requires:
  - phase: 07-01
    provides: digest-pinned Libbet ROM, manifest predicate addresses and anchors, exact CTest inventory
provides:
  - gabbaboy_accept static library (src/accept) shared by the runner and the player smoke
  - gbinput 1 parser, deadline stepper, replay driver with callbacks, compiled libbet-tutorial-cleared predicate
  - tests/acceptance/inputs/libbet-tutorial.input (D-13 script)
  - Five acceptance_* CTests in the exact inventory
affects: [07-03, 07-04, 07-05, 07-12]

status: complete
actuals:
  tokens: 16700
  tasks: 3
  commits: 3
plan_head_before: 2fd4ae8cebc15801c9ef115bb8657031908337f1
plan_head_after: ff331010985e80ebb52b493e22359e456b26b99d

tech-stack:
  added: []
  patterns:
    - "Acceptance logic lives in one internal static library; host adapters pass callbacks, the library reads no clock"
    - "Parser rejects all-or-nothing and zeroes its output; every error is 'invalid-script: line N: reason'"
    - "Predicate rows carry derivation text and ROM anchors; the digest is checked before any anchor"
    - "tests/acceptance/CMakeLists.txt is include()d (not add_subdirectory) so ExpectedTests.cmake sees its tests"

key-files:
  created:
    - src/accept/gbb_accept.h
    - src/accept/sha256.c
    - src/accept/input_script.c
    - src/accept/stepper.c
    - src/accept/predicate.c
    - tests/acceptance/CMakeLists.txt
    - tests/acceptance/inputs/libbet-tutorial.input
    - tests/test_acceptance_lib.c
  modified:
    - CMakeLists.txt
    - src/runner/main.c
    - tests/CMakeLists.txt
    - tests/expected-tests.txt

key-decisions:
  - "gbb_accept_drive reports end_half_dots as the last logical deadline; the actual instance time (up to 48 half-dots earlier) stays in stepper->actual_half_dots"
  - "gbb_accept_predicate_anchors_ok checks the SHA-256 first; a separate anchors_match exists so tests can prove anchor checking independently of the digest"
  - "Drive callbacks share one context pointer; max_batch is validated to 1..64 and callers should leave headroom (the replay uses 32) because events stamped exactly at a window end may still be queued"
  - "Parser error line for whole-file failures (file over 64 KiB) is 0; for a button still held at EOF it is the line of the press"

patterns-established:
  - "Mutation evidence for tests whose implementation already exists: revert-able source mutants must each fail the new tests"

requirements-completed: [GAME-02, EVID-01]

coverage:
  - id: D1
    description: "Shared library replays the D-13 script on the pinned Libbet ROM (DMG-CPU-B) to the D-08 predicate hit at 896f"
    requirement: GAME-02
    verification:
      - kind: unit
        ref: "ctest -R '^acceptance_lib_libbet_replay$' -> lib_replay status=hit t_hit_half_dots=125841408"
        status: pass
    human_judgment: false
  - id: D2
    description: "gbinput 1 parser limits pinned on both sides and every D-12 malformation rejected with the right line"
    requirement: EVID-01
    verification:
      - kind: unit
        ref: "ctest -R '^acceptance_parse_script_' (2 tests)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Predicate truth table, consecutive-boundary rule and ROM digest-then-anchor binding"
    requirement: GAME-02
    verification:
      - kind: unit
        ref: "ctest -R '^acceptance_predicate_' (2 tests)"
        status: pass
    human_judgment: false
  - id: D4
    description: "SHA-256 moved out of the runner with identical output; runner, Mooneye and tracer results unchanged"
    requirement: EVID-01
    verification:
      - kind: unit
        ref: "ctest -R '^(runner_|mooneye_|tracer_)' and full suite 200/200"
        status: pass
    human_judgment: false

duration: 40 min
completed: 2026-10-10
---

# Phase 7 Plan 02: Shared acceptance library Summary

**Shared C library (gbinput 1 parser, deadline stepper, replay driver, ROM-bound predicate) replays the Libbet tutorial script on DMG-CPU-B to a guest-memory predicate hit at 896 frames, with parser and predicate boundaries pinned by mutation-checked tests.**

## Accomplishments

- `gabbaboy_accept` static library (internal, not installed) with `gbb_accept_*` API: SHA-256, script parse/free, stepper, drive, predicate find/anchors/eval/track.
- Tracer: `acceptance_lib_libbet_replay` prints `lib_replay status=hit t_hit_half_dots=125841408` (896f, matching the research estimate of about f894) before the 3600f budget.
- Runner SHA-256 moved to `src/accept/sha256.c`; `main.c` keeps static `hash_matches`/`read_bounded` wrappers, `MOONEYE_MANIFEST_SHA256` untouched.
- Five CTest names registered in `tests/expected-tests.txt`; `verify-test-inventory.sh ... --installed` reports 200 executed, none skipped.

## Task Commits

| Task | Name | Commit |
| ---- | ---- | ------ |
| 1 | Tracer: library replays Libbet script to predicate hit | ff4a436 |
| 2 | gbinput 1 parser boundary matrix and error table | 5a9b1fd |
| 3 | Predicate truth table and ROM-anchor tests | ff33101 |

## Verification Run

- `cmake --preset phase1 && cmake --build --preset phase1` clean, no warnings.
- `ctest -R '^(acceptance_lib_libbet_replay|runner_|mooneye_|tracer_)'`: 25/25 passed.
- `ctest -R '^acceptance_parse_script_'`: 2/2; `ctest -R '^acceptance_(predicate_|lib_)'`: 3/3.
- Full suite: 200/200 passed (9.2 s). `verify-test-inventory.sh <junit> tests/expected-tests.txt --installed`: "Verified 200 executed CTest cases; none skipped."
- Acceptance greps: `sha_update` in main.c = 0; no `time(`/`clock(`/`gettimeofday`/`clock_gettime` in src/accept; `GBB_STOP_HALTED_IDLE` and `GBB_STOP_OUTPUT_FULL` present in stepper.c; `gbb_accept_predicate_track` used in stepper.c.

## TDD Gate Compliance

Task 1 mandated a full parser/predicate implementation (D-10..D-12), so the Task 2 and Task 3 tests were green on first correct run; no RED commit with a failing target exists for them (unexpected-green gate, investigated and explained, not a test error). The first Task 2 run did fail once, but because of a bug in the test's line builder, which is INVALID_RED and not counted as evidence. Instead, sensitivity was proven by mutation: 12 parser mutants (line, byte and line-width limits, 600 s ceiling, unchecked multiply, duplicate label, held at EOF, double press, CR handling, NUL, non-ASCII, line numbering) and 8 predicate mutants (attract, score equality, max_score, hw, single-true hit, T_hit choice, anchor byte, digest-first) were applied one at a time and each failed the intended test; sources were restored byte-identical (`cmp`). Commits are `test(07-02)` for tasks 2 and 3 with no `feat` after them.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Plan inconsistency] 16384-event cap is unreachable**
- **Found during:** Task 2
- **Issue:** Each line yields at most 2 events (tap) and the file is capped at 4096 lines, so at most 8190 events can exist; "16384 accepted, 16385 rejected" cannot be exercised through the parser.
- **Fix:** The cap is implemented as a defensive bound; the test pins the densest legal script (4095 taps = 8190 events) instead and records the reason in the commit message.
- **Files modified:** tests/test_acceptance_lib.c
- **Commit:** 5a9b1fd

**2. [Rule 3 - Blocking] Duplicate-library linker warning**
- **Found during:** Task 1
- **Issue:** Linking both `GabbaBoy::core` and `gabbaboy_accept` (which exposes core PUBLIC) produced `ld: ignoring duplicate libraries`.
- **Fix:** runner and test_runner link only `gabbaboy_accept`.
- **Commit:** ff4a436

**3. [Rule 1 - Wording] Renamed `parse_time` to `parse_duration`**
- The plan's acceptance grep for `time(` would have matched the helper name.

**Total deviations:** 3 auto-fixed. **Impact:** none on behavior or scope.

## Issues Encountered

None blocking. `verify-test-inventory.sh --core-only` flags the locally registered `installed_*` tests; `--installed` is the matching mode for this build and passes.

## Known Stubs

None.

## Threat Flags

None. T-07-06/07 (checked arithmetic, caps, all-or-nothing parse), T-07-40 (iteration guard, every non-continuable stop surfaces, no host clock) are mitigated and tested.

## Next Phase Readiness

Plan 07-03 onward can consume `gabbaboy_accept`; the Mooneye stack buffers are untouched for Plan 07-05 (D-27). Phase 7 continues; do not advance past it automatically.

## Self-Check: PASSED

Created files verified on disk; commits ff4a436, 5a9b1fd, ff33101 are ancestors of HEAD.
