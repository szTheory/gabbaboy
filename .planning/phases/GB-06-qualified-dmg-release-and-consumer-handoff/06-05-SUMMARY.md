---
phase: GB-06-qualified-dmg-release-and-consumer-handoff
plan: 05
subsystem: testing
tags: [C17, CMake, CTest, ASan, UBSan, libFuzzer]
requires:
  - phase: GB-02-dmg-cpu-bus-and-time
    provides: bounded ROM loader, battery API, deterministic run behavior
provides:
  - Exact-limit, over-limit, malformed, and failure-atomic loader regressions
  - Deterministic battery/API seed replay and minimized fuzz regression
  - Bounded compiler-integrated loader and stateful battery/API fuzz target
  - CI sanitizer workflow invocation with explicit unavailable-runtime reporting
affects: [release-qualification, CI, security-regressions]
actuals:
  tokens: 5459
  tasks: 2
  commits: 4
tech-stack:
  added: []
  patterns:
    - Optional compiler-integrated libFuzzer target, enabled only when the matching Clang runtime links
    - Fixed deterministic CTest regressions remain mandatory when libFuzzer is unavailable
key-files:
  created:
    - tests/test_loader_fuzz.c
    - tests/fuzz_core.c
    - tests/test_fuzz_core.c
    - tests/scripts/run-bounded-fuzz.sh
  modified:
    - tests/test_battery_fuzz.c
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - .github/workflows/ci.yml
key-decisions:
  - "Use compiler-integrated libFuzzer with no additional project dependency; keep deterministic regressions as the cross-toolchain requirement."
  - "Bound fuzz inputs to 64 KiB, decoded operations to 16, per-run work to 2048 half-dots, and total per-input work to 8192 half-dots."
  - "Retain longer-run corpus reductions and crash artifacts under the build directory for inspection and regression promotion."
patterns-established:
  - "Every fuzz-discovered crash is reduced to a fixed CTest case using the same input-processing function."
  - "A missing compiler runtime is reported as unsupported, never as a fuzz pass."
requirements-completed: [SHIP-07]
coverage:
  - id: D1
    description: Loader and battery/API boundary failures remain bounded and preserve live state and output guards.
    requirement: SHIP-07
    verification:
      - kind: unit
        ref: "CTest battery_api_fuzz, loader_*, fuzz_core_regressions under Clang 18 ASan/UBSan (16/16 passed)"
        status: pass
    human_judgment: false
  - id: D2
    description: Compiler-integrated fuzzing has explicit input, work, time, memory, and worker limits with a reproducible seed.
    requirement: SHIP-07
    verification:
      - kind: unit
        ref: "tests/scripts/run-bounded-fuzz.sh --self-test"
        status: pass
      - kind: unit
        ref: "tests/scripts/run-bounded-fuzz.sh --fast (128 runs)"
        status: pass
      - kind: unit
        ref: "tests/scripts/run-bounded-fuzz.sh --explore (60 seconds; 9,449 executions)"
        status: pass
    human_judgment: false
duration: 19min
completed: 2026-10-08
status: complete
plan_head_before: 23878867ea89799cc718e1322024fe77480311ef
plan_head_after: c73b6ef903b15ac2fe70d821ac828176f3a35fb1
commits: 4
---

# Phase GB-06 Plan 05: Bounded Boundary Fuzzing Summary

**Loader and battery/API boundaries now have exact-limit regressions, deterministic replay, and bounded sanitizer-backed compiler-integrated fuzzing.**

## Performance

- **Duration:** 19 min
- **Started:** 2026-10-08T22:45:00Z (approximate)
- **Completed:** 2026-10-08T23:03:16Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- Added loader coverage for null/empty, truncated, exact 2 MiB maximum, one-byte over, and `SIZE_MAX` requests. Rejected replacements leave the currently loaded tracer usable.
- Extended fixed battery/API sequences to assert `SIZE_MAX` import failure atomicity and compare deterministic result digests across two runs of the same seed.
- Added a Clang libFuzzer target for ROM loading and stateful battery/API operations. It rejects inputs over 64 KiB, decodes at most 16 operations, bounds each emulated run to 2048 half-dots and total input work to 8192 half-dots, and caps time, RSS, jobs, and workers.
- The first 60-second sanitizer-guided exploration found a heap-buffer-overflow in the new fuzz input decoder. Fixed the cursor bound and promoted the exact 10-byte minimized input to `fuzz_core_regressions` in the required CTest inventory.
- Longer exploration now retains its minimized input corpus under the build directory; crash reproducers are written to the adjacent artifact directory.

## Task Commits

1. **Task 1: Lock loader and battery/API boundary regressions** - `6721261` (test)
2. **Task 1 follow-up: Verify battery fuzz replay invariants** - `2cbea45` (test)
3. **Task 2: Run bounded loader and stateful API fuzz targets** - `61074d6` (feat)
4. **Task 2 fix: Bound decoder and preserve minimized finding** - `c73b6ef` (fix)

**Plan metadata:** pending parent phase orchestration.

## Files Created/Modified

- `tests/test_loader_fuzz.c` - Exact and over-limit ROM loading plus rejection atomicity.
- `tests/test_battery_fuzz.c` - Oversized battery import checks and same-seed outcome digest replay.
- `tests/fuzz_core.c` - Shared bounded loader/stateful API input processor and libFuzzer entry point.
- `tests/test_fuzz_core.c` - Fixed regression for the minimized decoder overflow input and size caps.
- `tests/scripts/run-bounded-fuzz.sh` - Runtime honesty check, deterministic fast mode, bounded exploration, and retained findings.
- `tests/CMakeLists.txt`, `tests/expected-tests.txt` - Optional instrumented target and fixed deterministic inventory entries.
- `.github/workflows/ci.yml` - Run fuzz self-test and deterministic regressions in the Linux sanitizer job.

## Decisions Made

- Used the compiler-integrated Clang runtime when available, with no third-party fuzz dependency. Deterministic ASan/UBSan regressions remain the required fallback.
- Bound work per fuzz input and run. Long exploration uses one worker, 60 seconds, a 2-second per-input timeout, and a 512 MiB RSS cap.
- Kept generated corpus reductions and reproducer artifacts in the build directory rather than adding generated files to the repository.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed fuzz input decoder read past the end of input**
- **Found during:** Task 2 bounded exploration
- **Issue:** The stateful decoder computed an operation count from input length but continued reading a selector after the cursor reached the input end.
- **Fix:** Stop decoding when the cursor reaches the input length; add the 10-byte minimized reproducer as a deterministic CTest using the same fuzz processing function.
- **Files modified:** `tests/fuzz_core.c`, `tests/test_fuzz_core.c`, `tests/CMakeLists.txt`, `tests/expected-tests.txt`
- **Verification:** The reproducer passes under Clang 18 ASan/UBSan; 128-run fast fuzz and a subsequent 60-second exploration (9,449 executions) completed without a sanitizer finding.
- **Committed in:** `c73b6ef`

**Total deviations:** 1 auto-fixed bug.
**Impact on plan:** The finding was directly caused by the new fuzz harness and was converted into permanent fast regression coverage.

## Issues Encountered

- The host is macOS and the project's sanitizer preset explicitly supports Linux only. A temporary Ubuntu 24.04 container with Clang 18 was used for ASan/UBSan and libFuzzer checks; the repository was mounted read-only and build output stayed under container `/tmp`.
- An initial fuzz run wrote libFuzzer job logs into the read-only source working directory. The runner now executes from the build directory, keeping logs and findings in the configured build output.
- Hosted GitHub Actions for this branch were not triggered here; the local Linux container ran the same configured sanitizer and script commands. Exact-head hosted evidence remains for the normal repository CI workflow.

## TDD Gate Compliance

The project-level `workflow.tdd_mode` is false and this is an execute plan rather than a `type: tdd` plan. The boundary tests characterize behavior already implemented in the core, so they passed before core code changes were needed. The new decoder regression was backed by an actual pre-fix ASan/libFuzzer crash and then replayed after the fix in fixed-inventory CTest.

## Known Stubs

None. A compiler without a matching libFuzzer runtime reports `unsupported`; deterministic sanitizer regressions still run.

## Self-Check: PASSED

- All eight implementation files are present and committed.
- Task commits `6721261`, `2cbea45`, `61074d6`, and `c73b6ef` are ancestors of the current phase branch head.
- All plan tasks are complete. Release publication and tagging remain gated by Plan 06-06.

## Next Phase Readiness

Plan 06-05 is complete and provides repeatable SHIP-07 boundary and fuzz evidence. Continue Phase 6 in dependency order; no release or tag was published.

---
*Phase: GB-06-qualified-dmg-release-and-consumer-handoff*
*Completed: 2026-10-08*
