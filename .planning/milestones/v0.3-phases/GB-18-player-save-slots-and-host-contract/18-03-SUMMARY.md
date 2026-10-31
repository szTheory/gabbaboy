---
phase: GB-18-player-save-slots-and-host-contract
plan: "03"
subsystem: core-api
tags: [core-api, input, abi, host-contract]
requires:
  - phase: GB-18-player-save-slots-and-host-contract
    provides: "18-01 and 18-02 host library, runner host mode, expected-tests append order (D-27)"
provides:
  - "gbb_input_clock, GBB_INPUT_CLOCK_SIZE_V1 (24u) and gbb_get_input_clock in the public header"
  - "gbb_get_input_clock in the core: read-only, struct_size handshake, MODEL-tagged, static-asserted against sizeof"
  - "test_input_clock with handshake, queue and after_load cases, built from run-time ROMs and states"
  - "gbb_input_clock_mutant(): one-edit core copy linked alone into a copy of the test, with a control per mutant"
  - "input_clock_consumer_symbols and its selftest over both installed consumers"
affects: [18-05, 18-06, 18-07, 18-08, 18-09]
actuals:
  tokens: 5561
  tasks: 2
  commits: 4
commits: 4
plan_head_before: a43159ae26bb160467b0eaaac1735ea4aca05b8d
plan_head_after: 6a52d617d159025ca0c435fea230dbdb81a17dfb
tech-stack:
  added: []
  patterns:
    - "A mutant core is a build-tree copy of src/core/gabbaboy.c built as its own static library and linked alone, so no executable links two cores."
    - "A configure-time copy of a consumer source registers the source in CMAKE_CONFIGURE_DEPENDS, so an edit regenerates the copy a selftest checks."
key-files:
  created:
    - tests/test_input_clock.c
    - tests/cmake/input-clock.cmake
  modified:
    - include/gabbaboy/gabbaboy.h
    - src/core/gabbaboy.c
    - tests/cmake/areas.cmake
    - tests/expected-tests.txt
    - tests/consumers/c/main.c
    - tests/consumers/cpp/main.cpp
    - docs/native-integration.md
key-decisions:
  - "The getter reports last_queued_half_dots as the instance time when the queue is empty, which is the value gbb_queue_events uses as its ordering floor, so max(now, last) is always the earliest admissible time."
  - "The getter reads the same fields gbb_queue_events reads; it adds no field, no state byte and no core-private constant to the public header."
  - "The RED commit carries the header declaration and a core stub that always refuses, so the three cases fail at runtime and the tree still builds and links at every commit."
requirements-completed: []
coverage:
  - id: D1
    description: "gbb_get_input_clock is public, static-asserted to 24 bytes and MODEL-tagged; sizes 0, 1 and 23, a NULL instance and a NULL output are refused with every byte unchanged, the exact size succeeds with struct_size 24, and a larger caller struct keeps its trailing bytes."
    requirement: PLAY-01
    human_judgment: false
    verification:
      - kind: unit
        ref: "ctest -R ^input_clock_handshake$ (tests/test_input_clock.c case handshake)"
        status: pass
      - kind: integration
        ref: "ctest -R ^model_gates (verify-model-gates.py sees the tagged function)"
        status: pass
  - id: D2
    description: "A fresh instance reports no queue and last equal to now; three queued events give count 3 and last equal to the third time without moving now; the getter leaves the saved state byte-identical; consumed events return last to now."
    requirement: PLAY-01
    human_judgment: false
    verification:
      - kind: unit
        ref: "ctest -R ^input_clock_queue$ (tests/test_input_clock.c case queue)"
        status: pass
  - id: D3
    description: "After gbb_load_state of a later-time and of an earlier-time state the getter reports the restored time and queue; an event at the stale pre-load cursor is refused with GBB_INVALID_EVENT and an event at max(now, last) is accepted."
    requirement: PLAY-01
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest -R ^input_clock_after_load$ (tests/test_input_clock.c case after_load)"
        status: pass
  - id: D4
    description: "Removing the struct_size guard makes the handshake case fail with FAIL handshake at exit 1, and storing now in place of the last queued time makes the queue case fail with FAIL queue at exit 1; each mutant has a control that runs the unmutated case and exits 0."
    requirement: PLAY-01
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest -R ^input_clock_mutant_short_size_writes(_control)?$"
        status: pass
      - kind: integration
        ref: "ctest -R ^input_clock_mutant_last_is_now(_control)?$"
        status: pass
  - id: D5
    description: "Both installed C and C++ consumers call gbb_get_input_clock and name gbb_input_clock and GBB_INPUT_CLOCK_SIZE_V1, and link and run against the installed prefix; a consumer copy with the call renamed fails with consumer-symbol-missing gbb_get_input_clock."
    requirement: PLAY-01
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest -R ^input_clock_consumer_symbols(_selftest)?$"
        status: pass
      - kind: e2e
        ref: "ctest -R ^installed_consumer_(c|cpp)$ against build/state-prefix"
        status: pass
  - id: D6
    description: "The native integration guide documents the getter without naming any identifier the header does not declare, and the only core diff is the getter, its MODEL tag and its static assert; state bytes, pins, inventory and tracer checkers pass at the committed revision."
    requirement: PLAY-01
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest -R ^(native_guide_.*|doc_contract_.*)$"
        status: pass
      - kind: integration
        ref: "ctest -R ^state_(format_contract|portable_pins|inventory|tracer|globals|identity|codec_matrix)$"
        status: pass
duration: 9min
completed: 2026-10-28
status: complete
---

# Phase 18 Plan 03: Input Clock Getter Summary

**`gbb_get_input_clock` reads the instance time, queue depth and last queued event time through a struct_size handshake so a player can re-anchor input after a slot load; two core mutants, both installed consumers and the unchanged state checkers pin it.**

## Performance

- **Duration:** about 9 min
- **Started:** 2026-10-29T03:13:16Z
- **Completed:** 2026-10-29T03:22:05Z
- **Tasks:** 2
- **Files modified:** 9 (2 created, 7 modified, excluding planning files)

## Accomplishments

- `gbb_input_clock { struct_size, queued_count, now_half_dots, last_queued_half_dots }` and `GBB_INPUT_CLOCK_SIZE_V1 == 24u` sit beside the `gbb_info` block, with a doc comment that states the read-only contract, the empty-queue rule and the handshake. The core carries a matching `_Static_assert` and the `/* MODEL: BOTH GATE-00 basis=host-api */` tag directly above the function (rule R1).
- `gbb_get_input_clock` computes the cursor exactly as `gbb_queue_events` computes `previous`, stores field by field and sets `struct_size` last. `git diff` of `src/core/gabbaboy.c` against the plan base shows only the static assert, the tag and the function (18 added lines, none removed).
- `test_input_clock` has three cases. `handshake` covers sizes 0, 1 and 23, NULL instance and output, the exact size and a 16-byte tail kept at 0xA7. `queue` covers the fresh instance, three queued events, a byte-identical saved state after repeated reads, and the return of `last` to `now` once events are consumed. `after_load` saves an early state (two queued events) and a state 600 frames later, then loads each into an instance sitting at the other time: the getter reports the restored clock, the stale cursor is refused and `max(now, last)` is accepted.
- `gbb_input_clock_mutant(name anchor replacement case)` requires a unique anchor, builds the edited core as its own library and links it alone. `short_size_writes` (guard replaced by `0`) fails `handshake` with `FAIL handshake` at exit 1; `last_is_now` fails `queue` with `FAIL queue` at exit 1; both controls exit 0.
- Both consumers gain an input clock block after their `gbb_get_info` use: success with `struct_size == GBB_INPUT_CLOCK_SIZE_V1`, `queued_count == 0`, `last == now`, then `GBB_INVALID_ARGUMENT` for size 23. `installed_consumer_c` and `installed_consumer_cpp` pass against an installed prefix.
- `docs/native-integration.md` documents the getter under "API and errors" (purpose, handshake, empty-queue rule, queue at or after `max(now, last)`), naming only declared identifiers.

## Task Commits

1. **Task 1 (tracer): header to core to running test** - `2f8816eb` (test, RED: declaration plus an always-refusing core stub; all three cases failed at runtime) then `ac215cf9` (feat, GREEN)
2. **Task 2: mutants, consumers, docs** - `6249a275` (test: mutant factory and instances, consumer blocks, symbol pair, inventory names) and `6a52d617` (docs)

**Plan metadata:** recorded in the following docs commit.

## Files Created/Modified

- `include/gabbaboy/gabbaboy.h`, `src/core/gabbaboy.c` - the getter, its type, size macro, static assert and MODEL tag
- `tests/test_input_clock.c` - handshake, queue and after_load cases (run-time ROM, no committed state bytes)
- `tests/cmake/input-clock.cmake`, `tests/cmake/areas.cmake` - registration, mutant factory, consumer symbol pair
- `tests/expected-tests.txt` - nine new names appended after the 18-02 names
- `tests/consumers/c/main.c`, `tests/consumers/cpp/main.cpp` - input clock blocks
- `docs/native-integration.md` - API bullet

## Decisions Made

- The cursor is the instance time when nothing is queued, so a host always computes `max(now, last)` without a special case for the empty queue.
- The tracer's RED commit includes an always-refusing stub in the core so every commit builds and links, while the plan-base diff still shows only the finished getter.
- The consumer selftest copy is made at configure time, so the consumer source is added to `CMAKE_CONFIGURE_DEPENDS`; otherwise an edit to the consumer left a stale copy that passed vacuously (see deviation 2).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Self-inflicted test bound**
- **Found during:** Task 1 (first GREEN run)
- **Issue:** `queue` required `now >= FRAME_HALF_DOTS` after running one frame, but a run stops at an instruction boundary and may fall just short of its budget.
- **Fix:** The bound is `now > 0` in `queue` and `now > T1 + 599 frames` in `after_load`. The getter was right; the assumption was wrong.
- **Files modified:** `tests/test_input_clock.c`
- **Commit:** `ac215cf9`

**2. [Rule 2 - Missing critical] Stale configure-time copy made the selftest vacuous**
- **Found during:** Task 2
- **Issue:** The selftest copy of `c/main.c` is written at configure time. After the consumers gained the call, a build without a reconfigure kept the old copy (which already lacked the symbol), so the selftest passed without discriminating.
- **Fix:** `set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS ...)` on the consumer source, and a check that the regenerated copy holds zero `gbb_get_input_clock` occurrences while the source holds two.
- **Files modified:** `tests/cmake/input-clock.cmake`
- **Commit:** `6249a275`

**3. [Process] TDD shape for Task 2**
- The mutants test the Task 1 getter and passed on first run; the committed RED for Task 2 is `input_clock_consumer_symbols` failing with `consumer-symbol-missing gbb_get_input_clock` before the consumers were edited (`build/18-03-task2-red.log`). The mutants are the discriminating evidence for the core.

---

**Total deviations:** 2 auto-fixed (1 bug, 1 missing critical), 1 process note
**Impact on plan:** None on scope. No core change beyond the getter, so no D-24 rescope trigger.

## Evidence Recorded for the Acceptance Criteria

- Task 1 RED log `build/18-03-task1-red.log` (3 failed), GREEN log `build/18-03-task1-green.log` (3 passed).
- Mutants, run directly: `short_size_writes handshake` prints `FAIL handshake` and exits 1; `last_is_now queue` prints `FAIL queue` and exits 1.
- `ctest -R ^input_clock_` lists 9 tests, all passed. `input_clock_consumer_symbols` prints `consumer-symbol-coverage pass`; the selftest passes on `consumer-symbol-missing gbb_get_input_clock`.
- Install and consumers: `cmake --install` into `build/state-prefix`, then `installed_consumer_c`, `installed_consumer_cpp`, `preview_package_smoke` and `state_tracer` passed (`build/18-03-task2-verify2.log`).
- Checkers at the committed revision after reconfiguring with `-DGBB_STATE_PIN_BASE_REV=7c1f257dd47fec77380f410b93a488bb1a5695cd`: `state_format_contract`, `state_portable_pins`, `state_inventory`, `state_tracer`, `native_guide_*`, `doc_contract_*`, `model_gates*`, `core_linkage_links` all passed (38/38, `build/18-03-task2-verify1.log`).
- Full suite at `6a52d617`: 1535/1535 passed (1526 from 18-02 plus 9 new). Log: `build/18-03-full-ctest.txt`.

## Issues Encountered

None.

## Known Stubs

None. The RED-only stub in `2f8816eb` was replaced in `ac215cf9`.

## Threat Flags

None. T-18-06 (out-pointer writes) is mitigated by the handshake, field-by-field store, unchanged outputs on error and the `short_size_writes` mutant. T-18-07 (header disclosure) is mitigated: only instance time, queue depth and last queued time are exposed, and the guide names no undeclared identifier.

## Next Phase Readiness

- Next plan: 18-04 (hostile-file safety). The getter is the PLAY-01 prerequisite the player slot plans (18-05 onward) call after `gbb_load_state`.
- PLAY-01 is not complete: slot save and load in the player remain.

## Self-Check: PASSED

- FOUND: tests/test_input_clock.c, tests/cmake/input-clock.cmake, include/gabbaboy/gabbaboy.h, docs/native-integration.md
- FOUND commits: 2f8816eb, ac215cf9, 6249a275, 6a52d617

---
*Phase: GB-18-player-save-slots-and-host-contract*
*Completed: 2026-10-28*
