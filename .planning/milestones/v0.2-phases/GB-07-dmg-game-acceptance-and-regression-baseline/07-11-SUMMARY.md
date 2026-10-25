---
phase: 07-dmg-game-acceptance-and-regression-baseline
plan: 11
subsystem: testing
tags: [acceptance, sgb, stall-report, ci, cross-os, pcm-calibration, libbet]

requires:
  - phase: 07-10
    provides: discrimination controls, libbet-no-input case, --mutate and --raw-verdict
  - phase: 07-07
    provides: --failure-dir PPM and --observe output
provides:
  - D-17 SGB probe: libbet receipt carries hw_f90 and sgb_reset_pulses from a gbb_run_ex diagnostics replay
  - D-18 bounded two-pass stall report (<id>.stall.txt, at most 65536 bytes) plus the failure PPM on exit 1 and exit 3
  - CI step "Record acceptance and Mooneye observations" in the three native jobs
  - D-16 calibration record and D-33 cross-OS identity at an exact head
affects: [07-12, 07-13, 07-15, 07-16]

status: complete
actuals:
  tokens: 8800
  tasks: 3
  commits: 7
plan_head_before: 1619675e85c529483b079fba78082c06dda5d7b9
plan_head_after: 89c624321b960ead69476a3d50dd95be67963df7

tech-stack:
  added: []
  patterns:
    - "Second deterministic pass on a fresh instance with gbb_run_ex; the main run stays on gbb_run_audio and never traces"
    - "Reserve the size of fixed report sections first so a full trace ring can only shorten the trace"

key-files:
  created: []
  modified:
    - src/accept/gbb_accept.h
    - src/accept/predicate.c
    - src/runner/acceptance.c
    - tests/expect_exit.cmake
    - tests/acceptance/CMakeLists.txt
    - tests/expected-tests.txt
    - tests/test_acceptance_lib.c
    - .github/workflows/ci.yml
    - .planning/context/LESSONS.md

key-decisions:
  - "Calibration branch is unchanged: O is far above both thresholds, so 2048 and 4800 stay and no digest is blessed here"
  - "The stall report keeps the most recent trace lines if truncation ever occurs; in practice 4096 x 15 bytes plus the fixed sections is about 63 KB"
  - "Exit-3 outcomes (guest stopped, step guard, frame errors) also write the failure PPM and the stall report"

requirements-completed: [GAME-02]

coverage:
  - id: D1
    description: "libbet receipt shows hw_f90=00 and at least one FF00 reset pulse (observed sgb_reset_pulses=2), so SGB detection ran and the guest did not hang"
    requirement: GAME-02
    verification:
      - kind: integration
        ref: "ctest acceptance_sgb_tolerance"
        status: pass
    human_judgment: false
  - id: D2
    description: "A failing run with --failure-dir writes a deterministic <id>.stall.txt of at most 65536 bytes and the failure PPM"
    requirement: GAME-02
    verification:
      - kind: integration
        ref: "ctest acceptance_stall_diagnosis (file 1984 bytes, two runs byte-identical, PPM byte-identical)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Exact-head CI is green and acceptance and Mooneye observations are byte-identical on Linux, macOS and Windows"
    requirement: GAME-02
    verification:
      - kind: ci
        ref: "run 38097373433 head b6f982b (observation comparison) and run 38098478728 head 89c6243, required-native success"
        status: pass
    human_judgment: false

duration: 130min
completed: 2026-10-11
---

# Phase 7 Plan 11: SGB tolerance, stall report and first exact-head CI calibration Summary

**Libbet receipt now proves SGB detection ran (hw_f90=00, 2 FF00 reset pulses), failed acceptance runs write a bounded deterministic stall report, and exact-head CI shows identical observations on Linux, macOS and Windows with the PCM thresholds left unchanged by the calibration rule.**

## Accomplishments

- **Task 1 (tracer, D-17).** `gbb_accept_predicate.sgb_probe_frames = 90` on `libbet-tutorial-cleared`. After a predicate hit the runner replays the first 90 frames on a fresh instance with `gbb_run_ex` (4096-record diagnostic buffer, continues on `GBB_STOP_OUTPUT_FULL`), counts FF00 writes where select bits `00` are later followed by `11`, and peeks `hw_capability` at the 90f boundary. Failure reason `sgb-probe`. The receipt ends with `hw_f90=00 sgb_reset_pulses=2`. The replay never touches the main instance or its PCM stream.
- **Task 2 (D-18).** On exit 1 or 3 with `--failure-dir`, a second pass replays to `T_end - 140448` without buffers, then collects the last 4096 trace records (15-byte `tttttt pppp oo` lines), the last 64 writes to FF00/FF0F/FFFF/FF40/FF41 and an 8-entry PC histogram into `<id>.stall.txt` (header with `trace_truncated`, sections `trace`, `io_writes`, `pc_histogram`). Fixed sections are sized first, so the file cannot exceed 65536 bytes. Exit-3 outcomes now also write the D-24 failure PPM. `tests/expect_exit.cmake` gained `GBB_EXPECT_FILE_MAX_SIZE`. Observed: 1984-byte stall file for the dropped-START case; two runs produce byte-identical stall text and PPM; no `--failure-dir` writes nothing.
- **Task 3 (CI evidence, D-33, D-16).** Step "Record acceptance and Mooneye observations" added to native-linux-x64, native-macos-arm64 and native-windows-x64 (three occurrences). Observation output is identical across the three OSes and equals a local run.

## TDD record

- RED SGB: `62cfd65` `acceptance_sgb_tolerance` failed because the output did not match `hw_f90=00 sgb_reset_pulses=[1-9]` (exit code 0 was right; the planned assertion failed). GREEN `ce6ab7f`.
- RED stall: `608fa85` `acceptance_stall_diagnosis` failed with "libbet.stall.txt was not written" (the planned behavior was absent, not a harness fault). GREEN `eb7844e`.
- No refactor commit.

## Exact-head CI evidence

- First CI run (head `da2a028`, run 38096251361): `native-windows-x64` failed in an unrelated test, `acceptance_parse_script_errors` at `tests/test_acceptance_lib.c:262` (raw `memcmp` over `gbb_input_event`, which has padding). Cycle 1 of the allowed 3.
- Fix `b6f982b` (field-wise comparison). Run 38097373433, head `b6f982b0b32e769f7ae6ec03a614e99d688a02db`, https://github.com/szTheory/gabbaboy/actions/runs/38097373433 : native-windows-x64, native-linux-x64, native-macos-arm64, linux-asan-ubsan, cmake-floor-3.25.3, player-gate, macos-player-package and required-native all `success`; `wait-exact-head-ci.py` printed PASS. Observations were extracted from the three native job logs, CRs stripped: 58 lines each, SHA-256 of the extracted text `cb66a7bee3b40d3822ebae579e80a4e0439921df1041087be4a1aa9f56c37503` on all three, `cmp` identical, and identical to a local run.
- Final code head `89c624321b960ead69476a3d50dd95be67963df7` (comment and LESSONS only), run 38098478728, https://github.com/szTheory/gabbaboy/actions/runs/38098478728 : all jobs `success` (native-linux-x64, native-windows-x64, native-macos-arm64, linux-asan-ubsan, cmake-floor-3.25.3, player-gate, macos-player-package, required-native); gate PASS run_id=38098478728 run_attempt=1.
- linux-asan-ubsan took 18 min 16 s (run 38097373433) and 20 min 6 s (run 38098478728) of a 30 min limit. The 22 min raise threshold was not reached, so `timeout-minutes` and the acceptance `TIMEOUT` values are unchanged. Headroom on the second run is about 33 percent; watch it.
- Docs-only commits pushed after this SUMMARY create newer heads whose CI is not yet read here.

### Observation lines (identical on Linux, macOS, Windows; head b6f982b)

```
acceptance.libbet.t_hit_half_dots 125841408
acceptance.libbet.checkpoint.title.frame 8097d8c74059d69c48c9df868827dae4bbf5f6979e1456955433dc7bc5d04778
acceptance.libbet.checkpoint.play_start.frame 3d9c9f27e7241bf325401af73d632030d5253a5dc4a49b5a3701af741b361f62
acceptance.libbet.checkpoint.mid.frame a07a58d626ed63d8775239e518e1eec036ce6e310c7f0e972cf48105ead85071
acceptance.libbet.checkpoint.hit.frame fb5e3bc3a584b029032abf2b75a79d5fdf555c3a6da812cb372195551f71c61c
acceptance.libbet.frame.rolling 3c08f4dc4490c1befed922b4c216ff61e7b7a54319dc57c8d0016d64de4d1b1f
acceptance.libbet.pcm_sha256 3d051cb0a0a4ced82706126c5cbcaddcd22dbe2cc2e61c92d0c5717f1e8aaae5
acceptance.libbet.pcm.window.{left,right}.peak_to_peak 20290 / changes 164822
acceptance.libbet-no-input.t_hit_half_dots none
acceptance.libbet-no-input.frame.rolling d964fb0cc85cd1ca3245f595e05abad11f0de5fd9b1e976997af77890b226c56
acceptance.libbet-no-input.pcm_sha256 8752c1431d5a84514382754ca76d8e93512d2162379bee48b85182775905d754
acceptance.libbet-no-input.pcm.window.* peak_to_peak 0, changes 0
mooneye.daa.frame 29cd364f8864891441c22d4f4cfe953153dedf38470dd4cd5cac5c2ebdf873ff
mooneye.tim00.frame not-ready ; mooneye.tim00-div-trigger.frame not-ready
(all 58 lines: build comparison files were extracted from the job logs; per-case half-dot, register and result_pc lines also matched)
```

## D-16 calibration (branch: unchanged)

| Statistic | T (old) | O (libbet gameplay, min of L/R) | N (libbet-no-input, max of L/R) | F | T (new) |
|-----------|---------|----------------------------------|---------------------------------|---|---------|
| peak_to_peak | 2048 | 20290 | 0 | 512 | 2048 |
| changes | 4800 | 164822 | 0 | 1200 | 4800 |

O >= T for both, so the rule leaves them unchanged. The record sits beside the constants in `src/accept/gbb_accept.h`. No digest or threshold was blessed by this plan.

## Deviations from Plan

**1. [Rule 1 - Bug] Padding-sensitive memcmp failed native-windows-x64**
- **Found during:** Task 3 (first exact-head CI run)
- **Issue:** `tests/test_acceptance_lib.c:262` compared `gbb_input_event` arrays with `memcmp`; padding bytes differ on MSVC.
- **Fix:** field-wise comparison of `at_half_dots`, `kind`, `value`.
- **Files modified:** tests/test_acceptance_lib.c (not in the plan's file list)
- **Commit:** b6f982b. LESSONS row GB-GAME-003 added (the plan listed LESSONS.md for the weak-audio branch only).

**2. [Rule 3 - Blocking] Runner PPM on exit-3 paths**
- Exit-3 outcomes previously wrote no image; D-18 requires the D-24 PPM on exit 1 or 3, so `write_failure_ppm` was factored out of `fail_run` and reused. Commit eb7844e.

**3. Wait-gate invocation:** the plan's verify command omits the script's mandatory `--require required-native`; it was supplied.

**Total deviations:** 3 (1 bug fix, 1 blocking/required addition, 1 command correction). **Impact:** none on scope; one extra CI cycle.

## Known Stubs

None.

## Threat Flags

None. The stall report writes only inside the validated `--failure-dir`, bounded by the 4096-record ring, 64-write ring, fixed 15-byte lines and the 65536-byte cap (T-07-21); cross-OS evidence came from an exact-head run compared byte for byte (T-07-22); thresholds were not eroded (T-07-37); no package installs (T-07-SC).

## Self-Check: PASSED

All modified files exist; commits 62cfd65, ce6ab7f, 608fa85, eb7844e, da2a028, b6f982b, 89c6243 are ancestors of HEAD; full local CTest (237 tests) passed after Task 2; `grep -c 'Record acceptance and Mooneye observations' .github/workflows/ci.yml` is 3; thresholds 2048 and 4800 are at or above the 512 and 1200 floors.
