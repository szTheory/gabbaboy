---
phase: GB-18-player-save-slots-and-host-contract
plan: "07"
subsystem: host-contract
tags: [host, signals, posix, exit-codes, pacing, crash-safety, decoys]
requires:
  - phase: GB-18-player-save-slots-and-host-contract
    provides: "18-01 host runner and atomic writer; 18-02 mutant-library helper; 18-04 cadence, sweep, test twin of the host library and the shipped-seam check"
provides:
  - "host_signal.c: sigaction handlers (SA_RESTART|SA_RESETHAND, empty mask) whose body is `g_host_stop = sig;`, SIGPIPE ignored, TERM/INT/HUP unblocked, inherited SIG_IGN honoured for INT and HUP, relative-nanosleep pacing that returns on EINTR, ISO C stubs for _WIN32"
  - "host_exit.h: GBB_HOST_EXIT_TABLE X-macro (0 clean, 1 failure, 2 refusal), generated GBB_HOST_EXIT_* constants and host_exit_name"
  - "host_run.c: handlers before load, ready after load, frame-boundary stop with final flush, stop before the first frame writes nothing, failed final flush and core stop exit 1, paced mode at 16,742,706 ns per frame"
  - "test_host_signals.py: ten real-signal scenarios with a watchdog-bounded child helper; four build-tree decoy runners that each fail their own row"
  - "test_host_run: disposition, exit_table and stop_before_first_frame cases (POSIX-only executable)"
  - "CheckCoreNoHostClock.cmake denies signal, sigaction, raise, kill, sigprocmask, pthread_sigmask, alarm and setitimer at source and object layers, with seeded strict-C17 controls"
affects: [18-08, 18-09]
actuals:
  tokens: 15614
  tasks: 3
  commits: 5
commits: 5
plan_head_before: b20609bd09ce829c5f7de46e7f589fc3d11b5c61
plan_head_after: 64c6749b7ad53d2863e1921a223d955ec8da7abc
tech-stack:
  added: []
  patterns:
    - "A signal handler only stores into a file-static volatile sig_atomic_t; every flush, print and free runs in ordinary code at the next frame boundary."
    - "A real-signal harness waits for a flushed ready line under a watchdog, sends exactly one signal per row and proves the stop landed on a whole frame by replaying `--frames K` byte for byte."
    - "A host decoy that must fail a row needs a deterministic trigger: the partial-frame decoy removes the boundary poll and polls between half frames, so every stop is mid-frame."
    - "SA_RESETHAND is proven by behaviour (disposition back to SIG_DFL after one delivery) because Darwin does not report that flag from a sigaction query."
key-files:
  created:
    - src/host/host_signal.c
    - src/host/host_exit.h
    - tests/scripts/test_host_signals.py
    - tests/test_host_run.c
  modified:
    - src/host/gbb_host.h
    - src/host/host_run.c
    - CMakeLists.txt
    - cmake/CheckCoreNoHostClock.cmake
    - tests/scripts/host_fixture.py
    - tests/cmake/host.cmake
    - tests/expected-tests.txt
    - cmake/ExpectedTests.cmake
    - .github/scripts/verify-test-inventory.sh
key-decisions:
  - "The exit table row is X(code, IDENT, \"name\", \"meaning\"): an X-macro cannot upper-case a token, so the constant suffix is an explicit second field instead of the plan's three-field spelling."
  - "The boundary poll sits after the frame, its cadence flush and the pacing wait, plus once before the first frame; a signal that arrives during start-up is therefore kept and honoured at frame 0."
  - "A failed final flush reports `status=failure reason=flush` and exits 1; a core stop reports `status=failure reason=core-stop stop=<n>`; the earlier `status=core-stop` spelling from 18-01 is gone."
  - "host_signal_install failure is the refusal token signal-install (exit 2, before any save mutation)."
  - "The SIGKILL storm sets RLIMIT_CORE=0 on the harness process (children inherit it) rather than in preexec_fn, keeping Python code out of the fork path while reader threads exist."
  - "The storm checks the inode right after the first completed flush of every round against the inode left by the previous round; a crash-safe writer must differ because the old and new files exist together."
patterns-established:
  - "gbb_host_mutant_library accepts extra anchor/replacement pairs through ARGV<n> (a CMake list would split C replacements at the semicolons)."
requirements-completed: [HOST-02]
coverage:
  - id: D1
    description: "A real SIGTERM to a paced runner exits 0 with status=clean reason=SIGTERM, flushes the save, and a fresh --frames K batch run reproduces the signalled .sav byte for byte, so the stop landed on a whole frame; in non-sanitizer lanes kill-to-wait is under 2.0 s."
    requirement: HOST-02
    human_judgment: false
    verification:
      - kind: e2e
        ref: "ctest -R ^host_signal_term$ (tests/scripts/test_host_signals.py --scenario term)"
        status: pass
  - id: D2
    description: "SIGINT stops the runner cleanly with reason=SIGINT and a flushed save, and a SIGINT inherited as SIG_IGN is ignored for 0.5 s until a SIGTERM ends the run with exit 0."
    requirement: HOST-02
    human_judgment: false
    verification:
      - kind: e2e
        ref: "ctest -R ^host_signal_(int|inherited_ign)$"
        status: pass
  - id: D3
    description: "The host exit table has exactly the rows 0 clean, 1 failure and 2 refusal, declared once in host_exit.h; host_exit_name is NULL for 3, 4, 77, -1 and 256, and the --frames end, the failed final flush on a read-only save dir, a core stop and a refusal each exit with their own code and token."
    requirement: HOST-02
    human_judgment: false
    verification:
      - kind: unit
        ref: "ctest -R ^host_exit_table_codes$ (tests/test_host_run.c exit_table)"
        status: pass
      - kind: e2e
        ref: "ctest -R ^host_exit_(frames_clean|failure_readonly|core_stop|refusal)$"
        status: pass
  - id: D4
    description: "After host_signal_install TERM, INT and HUP carry a non-default handler with SA_RESTART and an empty mask, the first delivery stores the signal and restores the default action, SIGPIPE is ignored, an inherited SIG_IGN on INT and HUP stays ignored, and TERM, INT and HUP are unblocked even if they were blocked before."
    requirement: HOST-02
    human_judgment: false
    verification:
      - kind: unit
        ref: "ctest -R ^host_signal_disposition$ (tests/test_host_run.c disposition)"
        status: pass
  - id: D5
    description: "A signal pending at the first boundary stops the run with stopped_at_frame=0 flush=none, exit 0, and a battery cartridge gets no .sav."
    requirement: HOST-02
    human_judgment: false
    verification:
      - kind: unit
        ref: "ctest -R ^host_run_stop_before_first_frame$ (tests/test_host_run.c)"
        status: pass
  - id: D6
    description: "Six SIGKILLs at pseudo-random moments against an MBC3+RTC cartridge always leave an exact 32,789-byte .sav with a structurally valid GBRT version-1 block, every completed flush replaces the inode, and a final normal start sweeps the temps."
    requirement: HOST-02
    human_judgment: false
    verification:
      - kind: e2e
        ref: "ctest -R ^host_exit_crash_storm$ (tests/scripts/test_host_signals.py --scenario crash-storm)"
        status: pass
  - id: D7
    description: "Four build-tree decoy runners fail the harness for their own reason: no final flush fails term with 'SIGTERM left no .sav', a partial-frame stop fails term with a replay mismatch, exit 0 after a failed final flush fails failure-readonly with 'exit 0, expected 1', and an in-place writer fails crash-storm on a kept inode."
    requirement: HOST-02
    human_judgment: false
    verification:
      - kind: e2e
        ref: "ctest -R ^host_signal_decoy_(no_flush|partial_frame|exit0_after_failed_flush|in_place_write)$"
        status: pass
  - id: D8
    description: "No test hook ships: the shipped gabbaboy_host archive and gabbaboy-runner define no host_save_io_test_ or host_run_test_ symbol, while the test twin is rejected naming host_run_test_set_after_ready_hook."
    requirement: HOST-02
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest -R ^host_no_test_seams_shipped(_control|_run_control)?$"
        status: pass
  - id: D9
    description: "The core is mechanically free of signal code: the deny lists add signal, sigaction, raise, kill, sigprocmask, pthread_sigmask, alarm and setitimer at the source and object layers, the real core still passes, a strict-C17 object importing kill fails with no-host-clock-symbol: kill and a source calling sigaction fails with a call token."
    requirement: HOST-02
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest -R ^no_host_clock(_selftest|_symbol_selftest|_comment_selftest|_signal_selftest|_signal_call_selftest)?$"
        status: pass
  - id: D10
    description: "The 17 new names are in tests/expected-tests.txt, the 15 POSIX-only ones are removed from the Windows expectation in both cmake/ExpectedTests.cmake and the inventory script, and the full phase1 suite is green at the plan head."
    requirement: HOST-02
    human_judgment: false
    verification:
      - kind: other
        ref: "bash .github/scripts/verify-test-inventory.sh --self-test"
        status: pass
      - kind: integration
        ref: "ctest --preset phase1 -j8 at 64c6749b: 1628 of 1628 passed"
        status: pass
duration: 18min
completed: 2026-10-29
status: complete
---

# Phase 18 Plan 07: Signals, Exit Table and Core No-Signal Check Summary

**A paced `gabbaboy-runner` now stops on SIGTERM/SIGINT/SIGHUP at a frame boundary, flushes, and exits 0 in well under 2 s, with a three-row exit table (0 clean, 1 failure, 2 refusal), proven by real signals sent to real processes (replay, ceiling, read-only failure, SIGKILL storm) and by four decoy runners that each fail their own row; the core is denied signal code at source and object layers.**

## Performance

- **Duration:** about 18 min
- **Started:** 2026-10-29T04:43:13Z
- **Completed:** 2026-10-29T05:01Z
- **Tasks:** 3
- **Files modified:** 13 (4 created, 9 modified, excluding planning files)

## Accomplishments

- `host_signal.c` installs handlers only in host mode. The handler body is the single assignment `g_host_stop = sig;`. SIGTERM is always handled; SIGINT and SIGHUP are skipped when inherited as SIG_IGN (nohup, background jobs); SIGPIPE is ignored; TERM/INT/HUP are unblocked after the handlers exist. `SA_RESETHAND` makes a second signal take the default action.
- `host_run.c` installs handlers before it opens the save dir or reads the ROM, prints `gbb-host: ready` only afterwards, polls the flag once before frame 0 and after every frame (after its cadence flush and pacing wait), and runs the final flush on a stop. A stop before frame 0 prints `stopped_at_frame=0 flush=none` and writes nothing. A failed final flush and a core stop exit 1; every literal 0/1/2 now comes from `GBB_HOST_EXIT_*`.
- Paced mode (no `--frames`) holds a CLOCK_MONOTONIC deadline advanced by `GBB_HOST_FRAME_NS` (16,742,706 ns), resynchronises when more than 8 frames behind, and sleeps once with relative `nanosleep` that returns on EINTR. A manual run showed 60 frames in 1.0 s. Batch mode is unpaced. Clock and sleep code sit inside `#ifndef _WIN32` with ISO C stubs; the `-D_WIN32` syntax proxy exits 0 for every `src/host/*.c`.
- The harness proves each exit-table row with a real process. The `term` row replays `--frames K` in a fresh directory and requires a byte-identical `.sav`, so a partial frame would show. The failure row uses a spin-increment MBC3+RTC image that changes every frame, so the D-11 final flush must attempt a write; with the directory made 0500 after `ready` it asserts `flush reason=final ... result=failed stage=temp`, `status=failure reason=flush`, exit 1, the old `.sav` byte-identical and no temp.
- The SIGKILL storm (six rounds, fixed RNG seed 1807) always finds an exact 32,789-byte `.sav` with a valid GBRT block, sees a new inode after the first completed flush of every round, and a final normal start sweeps the temps.
- Four decoys (no flush, partial frame, exit 0 after a failed flush, in-place writer) each fail their own row. They are build-tree executables named `gabbaboy-runner-hostvariant-*`, never installed.
- `CheckCoreNoHostClock.cmake` gains the eight signal and process-control names in both deny lists. The real core still passes; a strict-C17 `kill` object and a `sigaction` source fail for their own token.

## Task Commits

1. **Task 1 (tracer): real SIGTERM, frame-boundary stop, replay proof** - `f70b08e4` (test, RED: `FAIL term: exit -15, expected 0`) then `ccdfb85d` (feat, GREEN). Tracer gate: `host_signal_term` re-run end to end before expansion; 15 of 15 repeated runs passed. Tracer verified end-to-end, expanding.
2. **Task 2: every exit row, dispositions, stop-before-first-frame, storm, four decoys** - `c1ffeacf` (test; see the process note)
3. **Task 3: core no-signal check with seeded controls** - `8031759c` (test, RED: both selftests failed) then `64c6749b` (feat, GREEN)

**Plan metadata:** recorded in the following docs commit.

## Files Created/Modified

- `src/host/host_signal.c`, `src/host/host_exit.h` - the signal flag, handler install, paced wait and the exit table
- `src/host/host_run.c`, `src/host/gbb_host.h` - boundary poll, final flush on stop, pacing, the after-ready test hook, `GBB_HOST_FRAME_NS`
- `CMakeLists.txt` - `host_signal.c` in the library, `host_exit.h` and `host_signal.c` in the qualified-build dirty list
- `cmake/CheckCoreNoHostClock.cmake` - the D-18 deny names
- `tests/scripts/test_host_signals.py`, `tests/scripts/host_fixture.py` - the harness and the `spin-increment` and `illegal-opcode` ROM kinds
- `tests/test_host_run.c`, `tests/cmake/host.cmake` - in-process cases, registrations, decoys, seeded controls
- `tests/expected-tests.txt`, `cmake/ExpectedTests.cmake`, `.github/scripts/verify-test-inventory.sh` - inventory bookkeeping (17 names, 15 POSIX-only in both Windows lists)

## Decisions Made

- **Exit table row shape.** `X(code, IDENT, "name", "meaning")`. An X-macro cannot upper-case a token, so the enum suffix is an explicit field; the row set (0, 1, 2 and their names) is as planned.
- **Poll placement.** The flag is read before frame 0 and after each frame's cadence flush and pacing wait. A signal that arrives during start-up, between polls, or while the pacing sleep is interrupted is honoured at the next boundary; no frame starts once it is set.
- **Exit line shapes.** `status=clean reason=<SIGTERM|SIGINT|SIGHUP|frames>`, `status=failure reason=core-stop stop=<n>`, `status=failure reason=flush`, each with `stopped_at_frame=K flush=<written|unchanged|none|failed>`. The 18-01 `status=core-stop` form was replaced; no test pinned it.
- **Storm limits.** `RLIMIT_CORE=0` is set on the harness process; the inode assertion compares each round's first completed flush with the inode left by the previous round, which holds on filesystems that reuse inode numbers.
- **Pacing evidence.** The only wall-clock assertion is the documented 2.0 s kill-to-wait ceiling in non-sanitizer lanes (D-105). No test asserts the pacing rate; the manual run is a sanity note, not evidence.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `gbb_host_mutant_library` could replace only one anchor**
- **Found during:** Task 2 (partial-frame decoy)
- **Issue:** The partial-frame decoy needs two coordinated edits in `host_run.c` (remove the boundary poll and poll between half frames). With one edit, a signal that arrives while the paced runner sleeps is seen by the boundary poll first, so the decoy would almost never stop mid-frame and the row could not fail deterministically.
- **Fix:** The helper takes extra anchor/replacement pairs, read through `ARGV<n>` because C replacements contain `;`. Every pair is still required to occur exactly once, and the existing callers are unchanged.
- **Files modified:** `tests/cmake/host.cmake`
- **Verification:** the six repeated decoy runs all failed with `replay --frames K differs`; the four prior mutant libraries still build and pass.
- **Commit:** `c1ffeacf`

**2. [Rule 1 - Bug] The disposition case asserted a flag Darwin does not report**
- **Found during:** Task 2
- **Issue:** `sigaction(sig, NULL, &old)` on macOS returns `SA_RESTART` but never `SA_RESETHAND`, so asserting the flag failed although the behaviour is right.
- **Fix:** `host_signal_disposition` asserts `SA_RESTART` by query and `SA_RESETHAND` by behaviour: raise each signal, require the stored number and a disposition back at `SIG_DFL`.
- **Files modified:** `tests/test_host_run.c`
- **Commit:** `c1ffeacf`

**3. [Rule 2 - Missing critical] The widened `host_run_test_` pattern had no control of its own**
- **Found during:** Task 2
- **Issue:** The existing control only names `host_save_io_test_fail_next`, so a pattern typo for `host_run_test_` would never be noticed.
- **Fix:** Added `host_no_test_seams_shipped_run_control`, which must reject the test twin naming `host_run_test_set_after_ready_hook`. It is POSIX-only and in the inventory and both Windows lists (one name beyond the plan's list).
- **Files modified:** `tests/cmake/host.cmake`, the three inventory files
- **Commit:** `c1ffeacf`

**4. [Process] Planned-form differences**
- Exit table rows use four fields (see Decisions). `RLIMIT_CORE` is set on the harness rather than in `preexec_fn`. The sanitizer flag is passed through a configure-time variable (`--sanitized` or nothing) instead of the generator expression, because an empty unquoted generator expression in `add_test` is not reliably dropped.
- **TDD shape.** Task 1 and Task 3 have RED commits (`build/18-07-task1-red.log`: `FAIL term: exit -15, expected 0`; `build/18-07-task3-red.log`: both selftests failed). Task 2's scenarios and in-process cases passed on arrival because Task 1 already implements the behaviour; its discriminating evidence is the four decoys, which fail for their own reason (`build/18-07-task2-decoys.log`: six runs of each of no_flush, partial_frame and exit0_after_failed_flush; the in-place writer fails `round 1: a completed flush kept inode`).

---

**Total deviations:** 3 auto-fixed (1 blocking, 1 bug, 1 missing critical), 1 process note
**Impact on plan:** No scope change. One extra CTest name; every edited file is in the plan's `files_modified` list.

## Evidence Recorded for the Acceptance Criteria

- Task 1: `host_signal_term` prints `host-signals scenario=term pass`; `grep 'static void host_on_signal' src/host/host_signal.c` shows the one-statement body; `grep -nE 'return +[0-9]+ *;' src/host/host_run.c` prints nothing; the `-D_WIN32` syntax proxy exits 0 for all five `src/host/*.c`; `verify-test-inventory.sh --self-test` passes.
- Task 2: the 10-test fast line and the 5-test storm and decoy line pass (15 tests, same set as `^(host_signal_.*|host_exit_.*|host_run_stop_before_first_frame)$`); `nm build/gabbaboy-runner | grep -c host_run_test_` prints 0; `test_host_run` and the four decoy targets are created inside `if(NOT WIN32)`; the failure row asserts `reason=final` with `result=failed stage=temp`.
- Task 3: six `no_host_clock*` tests pass (four existing, two new); `grep -c sigaction cmake/CheckCoreNoHostClock.cmake` prints 3; the seed library uses `C_EXTENSIONS OFF`.
- Plan verification: `ctest -R '^(host_signal_|host_exit_|host_run_|no_host_clock)'` 21 of 21; full phase1 suite after `cmake --preset phase1 -DGBB_STATE_PIN_BASE_REV=7c1f257...`: 1628 of 1628 at `64c6749b` (`build/18-07-full-ctest.txt`).
- Local wall time of each real-signal test at -j8 against the 60 s budget: `host_signal_term` 0.71 s, `host_signal_int` 0.56 s, `host_signal_inherited_ign` 0.78 s, `host_exit_failure_readonly` 0.56 s, `host_exit_crash_storm` 9.20 s (7.6 to 8.3 s alone), `host_exit_frames_clean` 0.22 s, `host_exit_core_stop` 0.07 s, `host_exit_refusal` 0.06 s, decoys 0.52 to 3.05 s. The storm is the longest at under 16% of the budget, below the 75% guardrail.
- ASan lane: not run locally (macOS host, no sanitizer tree); the `linux-asan-ubsan` lane runs the same rows with `--sanitized` (replay and exit assertions only, no 2.0 s ceiling).

## Issues Encountered

None beyond the deviations above. The revision-pinned tests were judged only after reconfiguring at the new head with the pin base `7c1f257`.

## Known Stubs

None.

## Threat Flags

None. T-18-22 (handler stores only to `volatile sig_atomic_t`), T-18-23 (storm with size, structure and inode checks, in-place decoy fails), T-18-24 (failed final flush exits 1, exit-0 decoy fails), T-18-25 (hook only under `GBB_HOST_TESTING`, decoys build-tree only, `host_run_test_` symbol check with its own control) and T-18-26 (deny lists with seeded controls) are mitigated as planned.

## Next Phase Readiness

- Next plan: 18-08 (host contract documentation and format table). It can cite the exit table from `src/host/host_exit.h` and the exit-line shapes above. HOST-02 is complete; HOST-01 and HOST-03 stay open until 18-09's closing traceability.
- Windows remains declared exempt (D-05): all real-signal tests are POSIX-only in both exclusion lists and no console control handler exists.

## Self-Check: PASSED

- FOUND: src/host/host_signal.c, src/host/host_exit.h, tests/scripts/test_host_signals.py, tests/test_host_run.c, cmake/CheckCoreNoHostClock.cmake
- FOUND commits: f70b08e4, ccdfb85d, c1ffeacf, 8031759c, 64c6749b

---
*Phase: GB-18-player-save-slots-and-host-contract*
*Completed: 2026-10-29*
