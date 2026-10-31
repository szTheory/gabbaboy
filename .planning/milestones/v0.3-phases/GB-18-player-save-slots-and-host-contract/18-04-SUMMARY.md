---
phase: GB-18-player-save-slots-and-host-contract
plan: "04"
subsystem: host-contract
tags: [host, persistence, cadence, posix, hostile-input, fault-injection]
requires:
  - phase: GB-18-player-save-slots-and-host-contract
    provides: "18-01 host library, atomic writer, exact-size reader; 18-02 mutant library factory and API-surface checker; 18-03 expected-tests append order (D-27)"
provides:
  - "host_cadence: pure flush state machine (16 quiet, 300 age, 3,600 export-compare, generation compared with !=, 16-frame retry back-off)"
  - "host mode flushes mid-run on a generation change and every 3,600 frames, through the 18-01 D-11 write-iff-different rule"
  - "host_save_io_sweep: removes only .<stem>.sav.tmp- entries, links unfollowed, once after every refusal check"
  - "gabbaboy_host_testing and GBB_HOST_TESTING one-shot fault seams at all seven writer stages, absent from the shipped library and runner"
  - "test_host_cadence, test_host_save_io and 17 hostile-shape harness scenarios through the real runner"
  - "gbb_host_mutant_runner: three host-only mutant runners (ignore_import, mkdir, follow), each failing its own scenario"
  - "CheckHostApiSymbols.cmake GBB_FORBID_DEFINED: shipped artifacts may define no test seam"
affects: [18-05, 18-07, 18-08, 18-09]
actuals:
  tokens: 18522
  tasks: 3
  commits: 6
commits: 6
plan_head_before: 6cd9bb2ea446a64019f6a44e527d694dadb79def
plan_head_after: 8335fbafa79d8439d073e7ce794040c95adabe72
tech-stack:
  added: []
  patterns:
    - "A pure state machine takes frame and generation as arguments, so thresholds are proven by boundary tables instead of waiting thousands of frames."
    - "A one-shot file-static fault seam compiled only into a test twin of the library; a nm check on the shipped archive and executable plus a control on the twin keeps it out of shipped code."
    - "Mutant-runner CTests pin the failure reason, not just the FAIL prefix, so a harness crash cannot satisfy them."
key-files:
  created:
    - src/host/host_cadence.c
    - tests/test_host_cadence.c
    - tests/test_host_save_io.c
  modified:
    - src/host/gbb_host.h
    - src/host/host_run.c
    - src/host/host_save_io.c
    - CMakeLists.txt
    - cmake/CheckHostApiSymbols.cmake
    - cmake/ExpectedTests.cmake
    - tests/cmake/host.cmake
    - tests/scripts/test_host_mode.py
    - tests/expected-tests.txt
    - .github/scripts/verify-test-inventory.sh
key-decisions:
  - "D-11 discretion: a failed flush is retried 16 frames later (retry_after_frame = frame + 16), the next cadence point; within about a quarter second but unable to spin on a full disk."
  - "A failed export-compare write marks the image dirty, so the retry path covers RTC-only drift as well as generation changes."
  - "A sweep failure is reported (result=failed) but never fatal: a leftover temp cannot corrupt the .sav."
  - "The seam stage check is a static injected() helper that is constant false without GBB_HOST_TESTING, so the writer body has no per-stage ifdefs and no seam symbol ships."
requirements-completed: []
coverage:
  - id: D1
    description: "The cadence is a pure function: a generation change flushes after exactly 16 quiet frames (116 for a change at 100) or when the first unflushed change is 300 frames old, a clean image is compared every 3,600 frames, a decrease counts as a change, and a failed flush is retried 16 frames later with flushed advancing only after success; the != to > mutant and the quiet off-by-one mutant each fail their own case at exit 1."
    requirement: HOST-01
    human_judgment: false
    verification:
      - kind: unit
        ref: "ctest -R ^host_cadence_(quiet|age|rtc_compare|generation_compare|retry)$ (tests/test_host_cadence.c)"
        status: pass
      - kind: unit
        ref: "ctest -R ^host_cadence_mutant_(gt|quiet_off_by_one)$"
        status: pass
  - id: D2
    description: "A real runner flushes a guest write once, mid-run, between frames 16 and 24 of a 120-frame run, creates the first image at the final flush for an untouched battery cart, and leaves the .sav inode and mtime unchanged on an identical rerun."
    requirement: HOST-01
    human_judgment: false
    verification:
      - kind: e2e
        ref: "ctest -R ^host_(periodic_flush|first_write|idempotent_rerun)$ (tests/scripts/test_host_mode.py)"
        status: pass
  - id: D3
    description: "The stale-temp sweep removes only entries with the exact prefix .<stem>.sav.tmp- without following a symlink, keeps near-miss names and the symlink target, runs once after every refusal check and before ready, and a refused start leaves all pre-existing temps in place."
    requirement: HOST-01
    human_judgment: false
    verification:
      - kind: e2e
        ref: "ctest -R ^host_sweep_after_checks$ (tests/scripts/test_host_mode.py scenario sweep)"
        status: pass
      - kind: unit
        ref: "ctest -R ^host_sweep_exact_prefix$ (tests/test_host_save_io.c)"
        status: pass
  - id: D4
    description: "Each writer stage failure (temp, write, sync, close, target, rename) returns that stage's code and leaves the previous .sav byte- and inode-identical with no temp entry; a dir-sync failure reports failure with the new bytes already in place; EIO from sync is attempted exactly once; 16 EEXIST collisions fail with the temp stage and one collision moves to the next sequence; a directory or symlink target is refused."
    requirement: HOST-01
    human_judgment: false
    verification:
      - kind: unit
        ref: "ctest -R ^host_writer_(fault_(temp|write|sync|close|target|rename|dirsync)|eio_no_retry|eexist|target_not_regular)$ (tests/test_host_save_io.c)"
        status: pass
  - id: D5
    description: "Host mode applies no wall-clock RTC catch-up: an MBC3+RTC run persists RTC-only drift at the final flush as a 32,789-byte image, and a second run on a file aged by a day continues from the persisted clock with unchanged SRAM and a different 21-byte RTC block."
    requirement: HOST-01
    human_judgment: false
    verification:
      - kind: e2e
        ref: "ctest -R ^host_rtc_final_compare$ (tests/scripts/test_host_mode.py scenario rtc-final-compare)"
        status: pass
  - id: D6
    description: "The save directory is never created: a missing path exits 2 save-dir-missing and still does not exist, a regular file exits 2 save-dir-not-directory and is unchanged, a symlinked path (explicit link and /tmp) is accepted and the image lands in the real directory; a runner that creates the directory fails savedir-missing."
    requirement: HOST-01
    human_judgment: false
    verification:
      - kind: e2e
        ref: "ctest -R ^host_savedir_(missing|not_directory|symlink_path)$"
        status: pass
      - kind: e2e
        ref: "ctest -R ^host_savedir_mutant_mkdir$"
        status: pass
  - id: D7
    description: "A hostile .sav is refused before the first frame with its own token and no mutation: sizes 0, N-1, N+1, the mGBA 32,816-byte footer file and 8 MiB+1 give save-size, a corrupted RTC magic gives save-rtc-block, a live or dangling symlink gives save-symlink, a FIFO (within 10 s) and a directory give save-not-regular, and a device at the .sav path is not-regular at the reader; an exact valid image imports; a symlink-following runner fails import-symlink."
    requirement: HOST-01
    human_judgment: false
    verification:
      - kind: e2e
        ref: "ctest -R ^host_import_(exact|zero|short|long|mgba_footer|oversize|bad_rtc|symlink|dangling_symlink|fifo|directory)$"
        status: pass
      - kind: unit
        ref: "ctest -R ^host_import_device$ (tests/test_host_save_io.c)"
        status: pass
      - kind: e2e
        ref: "ctest -R ^host_import_mutant_follow$"
        status: pass
  - id: D8
    description: "A stray .sav (regular file, FIFO or symlink) next to a no-battery cartridge is never opened: the run exits 0 with flush=none inside 10 s and the entry, its link target and the listing are unchanged; a FIFO or directory passed as --rom exits 2 with rom-not-regular inside 10 s, never rom-unreadable or rom-size, with the save directory untouched."
    requirement: HOST-01
    human_judgment: false
    verification:
      - kind: e2e
        ref: "ctest -R ^host_import_stray_nobattery$"
        status: pass
      - kind: e2e
        ref: "ctest -R ^host_rom_(fifo|directory)$"
        status: pass
  - id: D9
    description: "An import-ignoring runner (the single gbb_import_battery call short-circuited to GBB_OK) fails the two-process continuation scenario with FAIL continuation because the second run restarts the counter at 01."
    requirement: HOST-01
    human_judgment: false
    verification:
      - kind: e2e
        ref: "ctest -R ^host_continuation_mutant_ignore_import$"
        status: pass
  - id: D10
    description: "No fault seam ships: the shipped gabbaboy_host archive and the gabbaboy-runner executable define no host_save_io_test_ symbol, while the same check on gabbaboy_host_testing is rejected with host-test-seam-shipped naming host_save_io_test_fail_next."
    requirement: HOST-01
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest -R ^host_no_test_seams_shipped(_control)?$"
        status: pass
  - id: D11
    description: "The 39 new POSIX-only names are in tests/expected-tests.txt and removed from the Windows expectation in both cmake/ExpectedTests.cmake and the inventory script; the inventory self-test passes, the registered set matches the expected set, and the full suite is green at the plan head."
    requirement: HOST-01
    human_judgment: false
    verification:
      - kind: other
        ref: "bash .github/scripts/verify-test-inventory.sh --self-test"
        status: pass
      - kind: integration
        ref: "ctest -j8 over the full phase1 build at 8335fbaf: 1581 of 1581 passed"
        status: pass
duration: 20min
completed: 2026-10-28
status: complete
---

# Phase 18 Plan 04: Cadence, Sweep and Hostile-File Safety Summary

**Host mode now flushes `.sav` files mid-run through a pure 16/300/3,600-frame cadence, sweeps only its own stale temps, and refuses every hostile save-dir, import and `--rom` shape with its own reason; seams for all seven writer stages exist only in a test twin of the library and are proven absent from shipped code.**

## Performance

- **Duration:** about 20 min
- **Started:** 2026-10-29T03:24:33Z
- **Completed:** 2026-10-29T03:45Z
- **Tasks:** 3
- **Files modified:** 13 (3 created, 10 modified, excluding planning files)

## Accomplishments

- `host_cadence_step` is a pure function of `(frame, generation)`. A generation change (compared with `!=`, so a decrease counts) is flushed after 16 quiet frames or when the first unflushed change is 300 frames old, and a clean image is exported and compared every 3,600 frames. Unsigned guards keep a frame below a stored mark from wrapping. `host_run.c` calls it after every frame and flushes through one shared `flush_battery`, which writes only when the export differs from `last_persisted`; `imported` advances only after the writer succeeds.
- A real runner flushes `write5a` once at frame 17, long before the 3,600-frame compare, then reports `final ... result=unchanged`. An untouched battery cart gets its first image at the final flush, and an identical rerun leaves inode and mtime alone.
- `host_save_io_sweep` iterates a duplicated, rewound dirfd and `unlinkat`s names starting with exactly `.<stem>.sav.tmp-`. A symlink entry is removed itself; its target survives. A refused start prints no sweep line and keeps all five seeded entries.
- `gabbaboy_host_testing` (POSIX-only, tests only) compiles one-shot seams at temp, write, sync, close, target, rename and dir-sync. Every stage fault returns its own code, keeps the old file byte- and inode-identical and leaves no temp; dir-sync reports failure with the new bytes already in place; EIO from sync is a single sync call.
- 17 harness scenarios drive the real runner through hostile shapes (missing, non-directory and symlinked save dirs; sizes 0, N-1, N+1, 32,816 and 8 MiB+1; bad RTC magic; live and dangling symlink; FIFO; directory; stray `.sav` next to a no-battery cart; FIFO and directory as `--rom`). Each asserts its own token, no `ready`, and unchanged lstat identity, content and listing. FIFO rows run under a 10 s bound.
- Three host-only mutant runners fail their own scenario: `ignore_import` (`FAIL continuation`, second run counter 0x01), `mkdir` (`FAIL savedir-missing`, exit 0) and `follow` (`FAIL import-symlink`).
- `CheckHostApiSymbols.cmake` gains `GBB_FORBID_DEFINED`; the shipped archive and executable pass, the test twin is rejected with `host-test-seam-shipped: _host_save_io_test_fail_next`.

## Task Commits

1. **Task 1 (tracer): cadence flush, first write, rerun, sweep through a real runner** - `a41d518e` (test, RED: periodic-flush and sweep failed) then `d499a722` (feat, GREEN)
2. **Task 2: cadence tables, RTC final compare, writer fault seams** - `0241818c` (test: cadence cases and mutants, fault cases against inert seam stubs, rtc scenario) then `728474f3` (feat: the seams)
3. **Task 3: hostile save-dir, import and --rom sweep, mutant runners, no shipped seams** - `1d7177cf` (test) and `8335fbaf` (fix: runner naming, see deviation 1)

**Plan metadata:** recorded in the following docs commit.

## Files Created/Modified

- `src/host/host_cadence.c`, `src/host/gbb_host.h` - the pure cadence, its constants, `host_save_io_sweep` and the test-only seam declarations
- `src/host/host_run.c` - cadence wiring, shared `flush_battery`, sweep call before `ready`
- `src/host/host_save_io.c` - sweep (with a `_WIN32` stub), `GBB_HOST_TESTING` seams, `injected()` stage helper
- `CMakeLists.txt` - `host_cadence.c` in the library and dirty list, `gabbaboy_host_testing` inside `BUILD_TESTING` and `NOT WIN32`
- `cmake/CheckHostApiSymbols.cmake` - `GBB_FORBID_DEFINED`, shared `gbb_run_nm`
- `tests/test_host_cadence.c`, `tests/test_host_save_io.c`, `tests/scripts/test_host_mode.py`, `tests/cmake/host.cmake` - the tests, scenarios and mutants
- `tests/expected-tests.txt`, `cmake/ExpectedTests.cmake`, `.github/scripts/verify-test-inventory.sh` - 46 new names, 39 of them POSIX-only in both Windows lists

## Decisions Made

- **16-frame retry back-off (recorded D-11 discretion).** D-11 says a failed flush is retried "at the next cadence point". The cadence has no fixed point after a failure, so `host_cadence_flush_failed` sets `retry_after_frame = frame + 16`: a retry within about a quarter second that cannot spin on a full disk. `flushed` advances only after the writer succeeds; a periodic failure never stops the run and only the final flush decides exit 1.
- A failed write on the export-compare path marks the image dirty, so the same back-off covers RTC-only drift.
- A sweep failure prints `sweep removed=0 result=failed` and continues; a leftover temp cannot corrupt the `.sav`, so refusing to start would be disproportionate.
- The seam check is one static `injected(stage)` helper that is constant false when `GBB_HOST_TESTING` is absent, instead of per-stage ifdefs inside the writer.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Mutant-runner executable names tripped the core-linkage rule**
- **Found during:** Task 3 full-suite run
- **Issue:** `core_linkage_links` and `core_linkage_controls` failed. `verify-core-linkage.py` requires every executable whose name contains `mutant` to link a mutant core. The plan's `gabbaboy-runner-mutant-<name>` runners mutate only the host library and link the normal core, so all three were reported as `wrong-core`.
- **Fix:** The executables are named `gabbaboy-runner-hostvariant-<name>`; the CTest names (`host_*_mutant_*`) are unchanged. The core-linkage checker was not edited.
- **Files modified:** `tests/cmake/host.cmake`
- **Verification:** `core_linkage_*` pass; full suite 1581/1581.
- **Commit:** `8335fbaf`

**2. [Rule 2 - Missing critical] Mutant-scenario regex could be satisfied by a harness crash**
- **Found during:** Task 3 (manual mutant run)
- **Issue:** A first manual run used a wrong runner path and printed `FAIL continuation: FileNotFoundError ...`, which matches the plan's `FAIL continuation` regex. A missing or renamed mutant runner would therefore have passed the test without exercising the mutant.
- **Fix:** `gbb_add_host_mutant_scenario` takes a reason: `continuation` requires `second run counter is 0x01, expected 0x02`, `savedir-missing` requires `exit 0, expected 2`, `import-symlink` requires `exit [01], expected 2`. Each still contains the plan's `FAIL <scenario>` text.
- **Files modified:** `tests/cmake/host.cmake`
- **Commit:** `1d7177cf`

**3. [Process] TDD shape**
- Task 1 RED (`build/18-04-task1-red.log`): `host_periodic_flush` and `host_sweep_after_checks` failed on the planned assertions; `host_first_write` and `host_idempotent_rerun` already passed against the 18-01 runner and pin that behaviour. Task 2 RED (`build/18-04-task2-red.log`): the eight seam cases (seven faults, eio_no_retry) failed against inert stubs; the cadence cases, cadence mutants, eexist, target_not_regular, sweep and RTC rows passed on arrival because the cadence and writer already existed from Task 1 and 18-01. Task 3: the 17 scenarios passed on arrival because 18-01 already implements every refusal; no reader fix was needed. Its discriminating evidence is the three mutant runners (`build/18-04-task3-mutants.log`) and `build/18-04-task3-red-oldcheck.log`, where the pre-change checker returns `host-api pass` for the seam-bearing archive, so the control could not reject it.

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 missing critical), 1 process note
**Impact on plan:** No scope change. No file outside `files_modified` was edited except `tests/cmake/host.cmake`, which is the registration file the plan already names.

## Evidence Recorded for the Acceptance Criteria

- Task 1: `host_periodic_flush`, `host_first_write`, `host_idempotent_rerun`, `host_sweep_after_checks`, `host_continuation` pass. `grep -cE '\bgeneration\s*>\s*' src/host/host_cadence.c` prints 0; the file includes neither `<time.h>`, `<unistd.h>` nor `<stdio.h>`. The `-D_WIN32` syntax proxy exits 0 for all four `src/host/*.c`.
- Task 2: the 19 tests matching `^(host_cadence_.*|host_rtc_final_compare|host_writer_.*|host_sweep_exact_prefix)$` pass. `gabbaboy_host_testing` appears in `CMakeLists.txt` only inside `BUILD_TESTING` and `if(NOT WIN32)`; `test_host_save_io` is built inside `if(NOT WIN32)` and `test_host_cadence` outside it; both `host_save_io_test_` definitions sit inside `#ifdef GBB_HOST_TESTING`; `nm build/gabbaboy-runner | grep -c host_save_io_test_` prints 0.
- Mutants, run directly: `test_host_cadence_mutant_gt generation_compare` prints `FAIL generation_compare`, exit 1, and passes `quiet` (control); `quiet_off_by_one quiet` prints `FAIL quiet`, exit 1.
- Task 3: 23 tests match `^(host_savedir_.*|host_import_.*|host_no_test_seams_shipped.*|host_rom_(fifo|directory)|host_continuation_mutant_ignore_import)$` and all pass; the 23-name loop prints no `MISSING`; `ctest -R ^host_` passes 76 of 76; `verify-test-inventory.sh --self-test` passes.
- Full suite at `8335fbaf` after `cmake --preset phase1` (pin base `7c1f257`): 1581 of 1581 passed (1535 from 18-03 plus 46 new). Log `build/18-04-full-ctest.txt`.
- ASan spot check: not run locally (no sanitizer build tree); the `linux-asan-ubsan` CI lane runs the host tests at the PR head.

## Issues Encountered

- The first full run failed `core_linkage_links` and `core_linkage_controls`; fixed as deviation 1.

## Known Stubs

None. The RED-only inert seam stubs in `0241818c` were replaced in `728474f3`.

## Threat Flags

None. T-18-08 through T-18-13 are mitigated as planned: dirfd plus `O_NOFOLLOW` import with the follow mutant (T-18-08), `O_NONBLOCK` plus `S_ISREG` plus exact size with FIFO, directory, device, 8 MiB+1, no-battery-stray and `--rom` FIFO/directory rows (T-18-09), per-stage fault cases (T-18-10), exact-prefix sweep with near-miss and symlink-target rows (T-18-11), cadence tables and mutants plus the mid-run flush row (T-18-12), and the shipped-seam check with its control (T-18-13).

## Next Phase Readiness

- Next plan: 18-05 (player slot library). HOST-01 is not marked complete: signals and exit codes (18-07), the HOST-03 corpus and the closing traceability (18-09) remain.
- One writer per (save dir, stem) stays the documented contract; there are no lock files. The SIGKILL storm for the old-or-new guarantee is 18-07.

## Self-Check: PASSED

- FOUND: src/host/host_cadence.c, tests/test_host_cadence.c, tests/test_host_save_io.c, src/host/host_save_io.c, tests/cmake/host.cmake, cmake/CheckHostApiSymbols.cmake
- FOUND commits: a41d518e, d499a722, 0241818c, 728474f3, 1d7177cf, 8335fbaf

---
*Phase: GB-18-player-save-slots-and-host-contract*
*Completed: 2026-10-28*
