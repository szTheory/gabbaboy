---
phase: 09-mbc3-deterministic-rtc-and-cartridge-persistence
plan: 16
subsystem: player-persistence
tags: [rtc, catch-up, battery, player, continuation, clock-injection]
requires:
  - phase: 09-11
    provides: player_catch_up_policy and format_status, gbb_rtc_catch_up
  - phase: 09-13
    provides: save envelope v2 with saved_at, player_session_set_clock, clock adapter
provides:
  - player_session_apply_catch_up (once per open, D-22 status text)
  - Loaded saved_at tracking on the save identity
  - --clock-unix for battery smoke modes only (D-21)
  - Fresh-process continuation for MBC2, MBC3+RTC and MBC5 with an injected clock
affects: [09-17, 09-18]
status: complete
commits: 2
plan_head_before: defda30d93bfa1bd992a11c2abec40ad718eca0b
plan_head_after: 54770996ad963e19c70bb8a62ecdb91a33ccc9c6
actuals:
  tokens: 45000
  tasks: 3
  commits: 2
requirements-completed: []
key-files:
  created:
    - tests/player/clock_flag_scope.cmake
  modified:
    - src/player/session.c
    - src/player/session.h
    - src/player/main.c
    - src/player/limitations.h
    - CMakeLists.txt
    - tests/player/test_continuation.c
    - tests/player/test_limitations.c
    - tests/player/test_session.c
    - tests/player/CMakeLists.txt
    - tests/player/expected-tests.txt
key-decisions:
  - "Catch-up runs only when the cartridge has a timer and a save file was accepted; a fresh or rejected save keeps the clock the core holds and reports nothing"
  - "The injected clock lives in the player struct and is set from argv before create_machine; player_clock_now(app) is still the only host clock read"
  - "Continuation children report C000..C006 and the status line through a result file in the pref directory, so the parent compares exact clock registers"
duration: 70 min
completed: 2026-10-11
coverage:
  - id: D1
    description: Catch-up, fresh-process continuation, and injected-clock flag scope
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build/phase3-player/gabbaboy --output-on-failure --no-tests=error -R '^(player_session_v2_.*|player_session_v1_(corpus_load|mbc1_write_identical)|player_session_classification_drift|player_session_rom_cap_8mib|player_continuation_mbc3_.*|player_continuation_mbc2_resume|player_continuation_mbc5_resume|player_session_clock_flag_scope)$'"
        status: pass
---

# Phase 9 Plan 16: Catch-up on reopen, --clock-unix scope and fresh-process continuation Summary

A reopened MBC3 timer save now advances the game clock once by the wall-clock time since its stored `saved_at`, reports it on the status line, never moves it backwards, and the MBC2, MBC3+RTC and MBC5 originals continue across fresh processes with exact clock deltas.

## Accomplishments

- `player_session_apply_catch_up` (session.c): the identity records the accepted v2 file's `saved_at` and validity; the call applies `player_catch_up_policy`, reads the live DH register (block byte 13) before and after `gbb_rtc_catch_up` to detect the carry becoming set and a halted clock, and formats the status through `player_catch_up_format_status`. A `catch_up_done` flag makes it once per open; `replace_rom` clears it.
- `main.c`: `create_machine` and `replace_session_rom` call it after the battery load (rejected-save warning keeps status precedence). `--clock-unix <i64>` is parsed with `strtoll` plus full-consumption and `ERANGE` checks and is accepted only as argv[3..4] of `--battery-smoke-store/-resume`; any other use exits 2 with the usage line. No new `getenv`.
- `test_continuation.c` generalised: `--child <mode> <rom> <pref> <clock|none>`, independent file-name rule (`-mbc1-` vs `-cart-`), v1/v2 header checks, per-child result file. New scenarios: RTC resume (also kills a child with SIGSTOP before the rename and proves the last good file is byte-identical and still resumes), delta for N in 0, 1, 59, 3600, 86400, 44236860 (carry set, "(day counter overflowed)"), rollback (file bytes unchanged), halted (seeded mode byte, DH `$40`), no clock (unavailable, and a store without a stamp), wrong ROM (rejected and preserved, original still resumes), MBC2, MBC5 (64 + 131072 bytes).
- `player_session_clock_flag_scope`: a CMake `-P` driver runs the real player through 12 negative cases (exit 2 and `usage:`) and one store/resume pair at an injected clock.
- Limitations text now says the clock catches up from the save time and that time paused while the player stays open is not recovered.
- Mutation check: changing the applied delta by +1 fails `rtc_resume`, `rtc_delta` and `wrong_rom`.

## Task Commits

1. Tasks 1 and 2 (session API, generalised continuation test, all eight scenarios): `3ba4ac0`
2. Task 3 (app catch-up, `--clock-unix` scope, limitations, flag-scope test, test fix): `5477099`

## Deviations from Plan

**1. [Ordering] Tasks 1 and 2 landed in one commit**
- Both rewrite `tests/player/test_continuation.c` and its CMake regex; the tracer's helpers are the scenarios' helpers, so they were not separable without a throwaway intermediate.

**2. [Rule 1 - Bug] Flaky `player_session_v2_max_size` (Plan 09-13 test)**
- **Found during:** Task 3 gate run (failed on about half of the runs)
- **Issue:** the test chose the preserved recovery file by `readdir` order, which is not creation order.
- **Fix:** select the recovery file whose size matches the damaged variant. 20 consecutive runs pass.
- **Files modified:** tests/player/test_session.c
- **Commit:** `5477099`

**3. [Rule 3 - Blocking] Newer guests park in HALT**
- The MBC2/MBC3/MBC5 fixtures stop with `GBB_STOP_HALTED_IDLE`, not the budget stop the MBC1 child required; the child accepts either (as the in-app battery smoke already does).

**Total deviations:** 1 bug fix, 1 blocking fix, 1 ordering note.

## Known Stubs

None.

## Verification

- `cmake --build --preset phase1` then full `ctest`: 401/401 pass; `verify-test-inventory.sh ... --installed` verified 401 cases, none skipped.
- `bash tests/scripts/verify-phase3-player.sh --build-package`: 79/79 player tests pass, inventory exact, package smoke passed (candidate sha256 `b9cfa4d3...8779e`).
- Acceptance greps: `--clock-unix` appears 5 times in main.c, `paused` in limitations.h, the eight new continuation names are in the inventory, `getenv` count equals main's, no `time(` in `src/core`.
- Stash count remains 1; nothing pushed.

## Threat Flags

None beyond the register. T-09-31 (flag scope, negative cases), T-09-32 (rollback and missing-stamp keep totals and bytes) and T-09-33 (once per open, delta test cancels emulated time) are mitigated and tested.

## Requirement status

RTC-03, CART-06 and RTC-02 are not marked complete here because sibling plans 09-17 and 09-18 still share these IDs.

## Self-Check: PASSED

Modified files exist; commits 3ba4ac0 and 5477099 are on the branch.

## Fresh Focused Evidence (15.1-12)

- Reused the existing player build tree. The referenced catch-up, continuation, and clock-scope selection passed 22/22 CTest cases in 1.43 seconds.
- No full suite, package rebuild, hosted check, or hardware result was rerun or inferred.
