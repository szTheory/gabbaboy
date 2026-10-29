---
phase: GB-18-player-save-slots-and-host-contract
plan: "01"
subsystem: host-contract
tags: [host, runner, posix, persistence, atomic-write, bounded-reader]
requires: []
provides:
  - gabbaboy_host static library (SDL-free, public-API-only, names no core) under src/host
  - gabbaboy-runner host mode: --rom P --save-dir D [--profile dmg|cgb] [--frames N]
  - host_save_io_replace, the frozen dir-fd atomic writer (all seven D-09 steps)
  - bounded 8 MiB ROM reader with rom-size, rom-unreadable and rom-not-regular tokens
  - D-07 stem rule with strict UTF-8 validator (tests land in 18-02)
  - host_fixture.py ROM generator and test_host_mode.py scenario harness
affects: [18-02, 18-04, 18-05, 18-07, 18-08, 18-09]
actuals:
  tokens: 11306
  tasks: 2
  commits: 3
commits: 3
plan_head_before: 7c1f257dd47fec77380f410b93a488bb1a5695cd
plan_head_after: 8261d35f2321a3d72ec7b654b6ff6b5e11fe7545
tech-stack:
  added: []
  patterns:
    - Contract logic lives in a core-free static library; the executable supplies GabbaBoy::core once.
    - POSIX bodies sit inside #ifndef _WIN32 with ISO C stubs so MSVC compiles every target.
    - Scenario harnesses run python3 -I, load host_fixture.py by path and pin exit code plus reason token.
key-files:
  created:
    - src/host/gbb_host.h
    - src/host/host_run.c
    - src/host/host_save_io.c
    - src/host/host_basename.c
    - tests/cmake/host.cmake
    - tests/scripts/host_fixture.py
    - tests/scripts/test_host_mode.py
  modified:
    - src/runner/main.c
    - CMakeLists.txt
    - tests/CMakeLists.txt
    - tests/acceptance/CMakeLists.txt
    - tests/cmake/areas.cmake
    - tests/expected-tests.txt
    - cmake/ExpectedTests.cmake
    - .github/scripts/verify-test-inventory.sh
key-decisions:
  - "Host mode is dispatched as the first statement of main, before the argc==2 tracer route; all logic stays in gabbaboy_host."
  - "A grammar defect is reported by its first occurrence in argv order, then missing-rom and missing-save-dir; a value that is itself a flag is missing-value."
  - "open_dir distinguishes ENOTDIR (save-dir-not-directory) from every other failure (save-dir-missing); HOST_IO_ENOTDIR was added to the I/O code enum for this."
  - "The temp-name sequence is a local counter restarted per call, so the writer holds no hidden global."
requirements-completed: []
coverage:
  - id: D1
    description: "A real runner process imports an exact-size raw .sav, runs N fixed frames and atomically publishes the battery image; a second process continues from it (fresh 01, then 02, preloaded 41 then 42) with no temp left and no absolute path in diagnostics."
    requirement: HOST-01
    human_judgment: false
    verification:
      - kind: e2e
        ref: "ctest -R ^host_continuation$ (tests/scripts/test_host_mode.py --scenario continuation)"
        status: pass
  - id: D2
    description: "The host ROM bound is the core's 8 MiB at both edges: an 8,388,608 B MBC5 ROM runs, 8,388,609 B is refused with rom-size (not rom-unsupported), and a missing ROM is refused with rom-unreadable."
    requirement: HOST-01
    human_judgment: false
    verification:
      - kind: e2e
        ref: "ctest -R ^host_rom_max_size$"
        status: pass
      - kind: e2e
        ref: "ctest -R ^host_rom_oversize$"
        status: pass
      - kind: e2e
        ref: "ctest -R ^host_rom_unreadable$"
        status: pass
  - id: D3
    description: "The inventory bookkeeping keeps the POSIX-only host names out of the Windows expectation in both lists and the self-test proves it."
    human_judgment: false
    verification:
      - kind: other
        ref: "bash .github/scripts/verify-test-inventory.sh --self-test"
        status: pass
  - id: D4
    description: "The runner dispatch did not disturb existing runner behaviour or core linkage."
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest -R ^(runner_|core_linkage_|acceptance_core_mutant|instance_lifecycle|tracer_smoke)"
        status: pass
duration: 15min
completed: 2026-10-28
status: complete
---

# Phase 18 Plan 01: Host-Mode Tracer Summary

**Headless `gabbaboy-runner --rom --save-dir --frames` with a core-free `gabbaboy_host` library: bounded 8 MiB ROM reader, exact-size `.sav` import, dir-fd atomic writer, proven by a two-process counter continuation (01 then 02, preloaded 41 then 42).**

## Performance

- **Duration:** about 15 min
- **Started:** 2026-10-28T22:43:00-04:00
- **Completed:** 2026-10-28T22:58:00-04:00
- **Tasks:** 2
- **Files modified:** 15 (7 created, 8 modified, excluding planning files)

## Accomplishments

- `gabbaboy_host` static library with the D-02 grammar (all eleven tokens), D-07 stem rule, bounded ROM reader, exact-size import and the frozen `host_save_io_replace` (temp `O_EXCL|O_NOFOLLOW`, EINTR-safe write, `F_FULLFSYNC`-then-`fsync` never retried, checked `close`, `fstatat` target check, `renameat`, tolerant directory `fsync`).
- Runner dispatch is one line at the top of `main`; the acceptance grammar and its 0/1/2/3/4 codes are untouched.
- D-11 flush rule: `last_persisted` starts as the imported bytes or `none`; the final flush writes iff the exported image differs, and `flush=` reports that flush (`written`, `unchanged`, `none`).
- XFER-002 continuation proven end to end, including an import-sensitive assertion (exactly `02`, exactly `42`, untouched bytes preserved).
- ROM bound proven at both edges with distinct tokens.

## Task Commits

1. **Task 1: Tracer, host mode loads, imports, runs, publishes** - `d130c2b` (test, RED) then `eda1789` (feat, GREEN)
2. **Task 2: Bounded ROM reader edges** - `8261d35` (test; the reader shipped in `eda1789`)

**Plan metadata:** recorded in the following docs commit.

## Files Created/Modified

- `src/host/gbb_host.h` - constants, enums, prototypes; includes only the public header and libc
- `src/host/host_run.c` - grammar, bounded reader, frame loop, final flush, `gbb-host:` diagnostics
- `src/host/host_save_io.c` - dir-fd open, exact-size bounded import, atomic replace; `_WIN32` stubs
- `src/host/host_basename.c` - D-07 stem rule and strict UTF-8 DFA
- `src/runner/main.c` - host dispatch before the tracer route
- `CMakeLists.txt` - `gabbaboy_host` target, runner link, dirty-list entries
- `tests/cmake/host.cmake`, `tests/cmake/areas.cmake` - CTest registration, POSIX-only
- `tests/scripts/host_fixture.py`, `tests/scripts/test_host_mode.py` - ROM generator, bounded runner helper, scenarios
- `tests/expected-tests.txt`, `cmake/ExpectedTests.cmake`, `.github/scripts/verify-test-inventory.sh` - inventory bookkeeping
- `tests/CMakeLists.txt`, `tests/acceptance/CMakeLists.txt` - link `gabbaboy_host` into the two targets that compile `src/runner/main.c`

## Decisions Made

- Grammar defects are reported in argv order; after the loop `missing-rom` then `missing-save-dir`. A value beginning with `--` is `missing-value`, so a flag can never be swallowed as a path. An `=` in any `--` argument is `equals-form`, which gives each 18-02 input exactly one token.
- Added `HOST_IO_ENOTDIR` (-14) to the I/O enum so `save-dir-not-directory` and `save-dir-missing` stay distinguishable without exposing errno to callers.
- The writer keeps no global state: the temp sequence is a per-call local, so concurrent callers in one process cannot collide on a counter.
- Core stop in the frame loop still attempts the final flush, then prints `exit status=core-stop` and returns 1.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Two other targets compile `src/runner/main.c`**
- **Found during:** Task 1 (first full build after the dispatch edit)
- **Issue:** `test_runner` (embeds `main.c`) and `gabbaboy-runner-joyp-mutant` (compiles it with its own mutant core) failed with `gbb_host.h not found` and would fail to link `gbb_host_main`.
- **Fix:** Linked `gabbaboy_host` into both. It names no core, so the mutant runner still links exactly one (the mutant) core and `core_linkage_*` stays green.
- **Files modified:** `tests/CMakeLists.txt`, `tests/acceptance/CMakeLists.txt`
- **Verification:** full build clean; `runner_*`, `core_linkage_*`, `acceptance_core_mutant` pass.
- **Committed in:** `eda1789`

**2. [Process] TDD ordering for Task 2**
- The bounded reader was written in Task 1 (the plan places the ROM-read step in `host_run.c` there), so Task 2's tests were green on first run. The RED evidence is instead two seeded mutants built in scratch space (not committed): a 32 KiB-capped host failed `rom-max` (`exit 2, expected 0: refused reason=rom-size`) and a 16 MiB-capped host failed `rom-oversize` (`missing 'refused reason=rom-size': ... reason=rom-unsupported`). Logs: `build/18-01-task2-mutant-cap.log`. For Task 1, the harness was run against a runner built from the plan base and failed with `exit 2, expected 0: 'invalid-arguments: use --help for usage'` (`build/18-01-red-continuation.log`).

---

**Total deviations:** 1 auto-fixed (1 blocking), 1 process note
**Impact on plan:** The link additions are required for any target that compiles runner `main.c`; no scope creep.

## Planner Deviations Carried

1. Serial waves for inventory-sharing plans: 18-01 edits the shared inventories alone in its wave and 18-02 follows it (GB-CART-003).
2. The D-07 stem rule and the full D-02 grammar are implemented here; their per-token negative CTests belong to 18-02.

## Issues Encountered

- The first full-suite run reported 6 failures, all environmental and unrelated to the code: four tests (`cgb_corpus_report_tracer`, `cgb_corpus_report_controls`, `state_purity`, `state_fuzz_controls`) compare the live tree with the HEAD revision recorded at configure time, which was one commit stale after Task 2; re-running `cmake --preset phase1` at the new HEAD made them pass. `state_pin_planning` (and its dependant `state_portable_pins`) failed on a stale CMake cache entry `GBB_STATE_PIN_BASE_REV=f192100...` left in the ignored `build/` directory by a Phase 17 configure (that commit is not an ancestor of this branch). Reconfiguring with `-DGBB_STATE_PIN_BASE_REV=7c1f257...` made both pass. Final result at HEAD `8261d35`: 1500/1500 effective (1494 first run plus the 6 re-run). Full log: `build/18-01-full-ctest.txt`.
- Revision-pinned tests fail again after any later commit until the build is reconfigured; the single final-head re-verification (AGENTS, D-105) should reconfigure first.

## Known Stubs

None. Paced mode (no `--frames`) runs unpaced frames until killed, as the plan specifies; pacing and signal handling land in 18-07.

## Threat Flags

None. All new surface (argv, save directory, ROM file) is covered by the plan's threat model T-18-02, T-18-03 and T-18-05.

## Next Phase Readiness

- Next plan: 18-02 (Grammar, stem and Windows-gate negatives; D-04 API-surface and dirty-list checks). It does not change `src/host/*` unless a token mismatch is found.
- HOST-01 is only partly delivered here (end-to-end path and ROM bound); it is not marked complete in REQUIREMENTS.md because hostile-file safety (18-04) and the closing traceability (18-09) remain.
- Local proxy for the Windows build rule passes: `cc -std=c17 -fsyntax-only -Werror=implicit-function-declaration -D_WIN32 -Iinclude -Isrc/host` on `src/host/*.c`.

## Self-Check: PASSED

- FOUND: src/host/gbb_host.h, src/host/host_run.c, src/host/host_save_io.c, src/host/host_basename.c, tests/cmake/host.cmake, tests/scripts/host_fixture.py, tests/scripts/test_host_mode.py
- FOUND commits: d130c2b, eda1789, 8261d35

---
*Phase: GB-18-player-save-slots-and-host-contract*
*Completed: 2026-10-28*
