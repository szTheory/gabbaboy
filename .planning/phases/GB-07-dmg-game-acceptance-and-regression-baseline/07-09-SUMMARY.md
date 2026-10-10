---
phase: 07-dmg-game-acceptance-and-regression-baseline
plan: 09
subsystem: testing
tags: [acceptance, ld-b-b, frame-digest, mooneye, observe, regression-class]

requires:
  - phase: 07-07
    provides: --observe surface, --dump-checkpoints, canonical D-24 digest and stdlib digest vectors
  - phase: 07-08
    provides: model applicability and strict xfail handling
provides:
  - gbb_runner_capture_ldbb shared LD B,B capture helper
  - frame-digest@ldbb and frame-digest@t oracles (class=regression verdicts, PPM on mismatch)
  - Mooneye --observe lines (registers, result_pc, ldbb_half_dots, frame_generation, frame)
  - tests/acceptance/ldbb-controls.txt with configure-enforced stdlib reference digest
  - expect_exit.cmake file-existence and size assertions
affects: [07-13, 07-15]

status: complete
actuals:
  tokens: 14000
  tasks: 2
  commits: 3
plan_head_before: 201c84d9e947541d76f5373d2763fd7fb8cd917a
plan_head_after: 5cdb263a5698a3560f3bac3ca0f754c274b5a8d0

tech-stack:
  added: []
  patterns:
    - "One capture helper for the case-file oracle and Mooneye observe, so both yield one digest"
    - "Latest frame completed at or before the LD B,B time, chosen from the frame held before the chunk and the one seen after it"
    - "Reference digests in a controls file must equal a stdlib-computed digest, enforced at configure time"

key-files:
  created:
    - tests/acceptance/ldbb-controls.txt
  modified:
    - src/runner/acceptance.c
    - src/runner/acceptance.h
    - src/runner/main.c
    - tests/acceptance/CMakeLists.txt
    - tests/expect_exit.cmake
    - tests/expected-tests.txt

key-decisions:
  - "The daa LD B,B digest is never a case-file reference; it is a regression-class observation (mooneye.daa.frame) for the EVID-02 ledger (D-26)"
  - "A LD B,B that never executes within budget is reason=ldbb-not-reached (exit 1), distinct from frame-not-ready"
  - "Frame-digest cases reject --input-script, --frame-digest-at and --pcm-digest with reason observe-flag-not-applicable rather than ignoring them"

requirements-completed: [EVID-01]

coverage:
  - id: D1
    description: "LD B,B frame captured as a canonical D-24 digest through one shared helper; image only on mismatch or explicit dump"
    requirement: EVID-01
    verification:
      - kind: integration
        ref: "ctest -R '^acceptance_ldbb_(observe_daa|mismatch_ppm|mooneye_observe)$'"
        status: pass
    human_judgment: false
  - id: D2
    description: "Missing frame is frame-not-ready (exit 1), never an all-zero frame; Mooneye observe records not-ready as an observation"
    requirement: EVID-01
    verification:
      - kind: integration
        ref: "ctest -R '^acceptance_ldbb_(not_ready|mooneye_observe)$'"
        status: pass
    human_judgment: false
  - id: D3
    description: "Controls file reference digests are stdlib-provenance only, enforced by a configure failure"
    requirement: EVID-01
    verification:
      - kind: command
        ref: "cmake --preset phase1 (also run with one digest replaced by 64 zeros: configure failed with the file and digest named)"
        status: pass
    human_judgment: false
---

# Phase 7 Plan 09: LD B,B frame capture Summary

**The runner captures the frame at the first executed LD B,B as a canonical D-24 digest through one shared helper used by both the `frame-digest@ldbb` case-file oracle and Mooneye `--observe`, writes a PPM only on mismatch or explicit dump, and keeps every frame-digest verdict `class=regression` with no self-captured reference committed.**

## Performance

- **Tasks:** 2 (tracer plus one TDD task), 3 commits
- **Files:** 7 (1 created, 6 modified)

## Accomplishments

- `gbb_runner_capture_ldbb` (acceptance.h/.c) runs bounded 2048-half-dot chunks with a 128-record trace, detects the first record with opcode 0x40, and selects the latest frame completed at or before that instruction. It reports not-ready distinctly.
- `frame-digest@ldbb` and `frame-digest@t=<n>` oracles: pass, `frame-mismatch` (prints `reason=frame-mismatch class=regression observed=<hex>` and writes `<failure-dir>/<id>.ppm`), `frame-not-ready`, `ldbb-not-reached`. Applicability and strict xfail from 07-08 apply.
- `--observe` for frame-digest cases prints sorted `acceptance.<id>.class`, `.ldbb_half_dots`, `.checkpoint.ldbb.completion_half_dots`, `.checkpoint.ldbb.frame`; `--dump-checkpoints` writes `<id>.ldbb.ppm` (69135 bytes, verified).
- `--observe` on `--manifest` paths prints `mooneye.<alias>.{frame,frame_generation,ldbb_half_dots,registers,result_pc}`; tim00 and tim00-div-trigger report `not-ready`. The `cases[]` table, `MOONEYE_MANIFEST_SHA256` and non-observe output are unchanged.
- `tests/acceptance/ldbb-controls.txt` holds two controls (`daa-ldbb` mismatch, `tim00-ldbb` not-ready) whose only reference is the stdlib `--uniform 3` digest; configure fails otherwise (proven with a doctored copy).
- Four CTests: `acceptance_ldbb_observe_daa`, `acceptance_ldbb_mismatch_ppm`, `acceptance_ldbb_not_ready`, `acceptance_ldbb_mooneye_observe`.

## Observations (not references)

- daa LD B,B digest, case-file `--observe`: `29cd364f8864891441c22d4f4cfe953153dedf38470dd4cd5cac5c2ebdf873ff` (completion 1676256 half-dots, LD B,B at 1804576, generation 12).
- Mooneye `--observe` `mooneye.daa.frame`: identical digest, so the two paths agree through the one helper.
- `rgb-digest-vector.py --uniform 0` is `29cd364f...873ff`, so the daa frame equals an all-shade-0 frame. This is a model observation (bootless DMG-CPU-B, zeroed VRAM, post-boot BGP), recorded only; it is not used as a reference.
- `frame-digest@t=300000` on daa (scratch case, not committed) captured the first frame at or after t (completion 412224), same digest.

## TDD

- RED (5bf1182): registered the three Task 2 tests and `GBB_EXPECT_FILE*` support. Target `acceptance_ldbb_mooneye_observe` failed on exit code (expected 0, got 2, `invalid-arguments`: observe rejected on the manifest path), the planned behavior gap. `acceptance_ldbb_mismatch_ppm` and `acceptance_ldbb_not_ready` already passed because Task 1's helper and oracle implemented that behavior; semantic assessment: the single RED is genuine and for the intended reason, the other two are regression guards for Task 1. `gsd_run check tdd-red-evidence` was not run (CTest/CMake output is not a supported report format).
- GREEN (5cdb263): `--observe` on the manifest path via the shared helper; all four pass.
- No REFACTOR commit.

## Task Commits

1. Task 1 (tracer): b7753f3 `feat(07-09): LD B,B frame capture helper and regression-class frame-digest oracle`. Tracer `<verify>` re-run end to end (configure, build, `acceptance_ldbb_observe_daa`, `grep -c 'uniform 3'` = 1): passed.
2. Task 2 RED: 5bf1182; GREEN: 5cdb263.

## Verification run

- `ctest -R '^(acceptance_ldbb_|mooneye_|runner_)'`: 22/22 pass. `ctest -j4 -R '^acceptance_'`: 34/34 pass. Full `ctest -j4`: 229/229 pass. `verify-test-inventory.sh build/ctest.xml tests/expected-tests.txt --installed`: "Verified 229 executed CTest cases; none skipped" (without `--installed` it reports the installed_* tests as extra, the same as CI's non-installed form, so the flag is required for a full local run).
- `ctest -N -R '^acceptance_ldbb_'`: Total Tests: 4. `grep -c MOONEYE_MANIFEST_SHA256 "98a1799b` in main.c: 1. No change inside `cases[]`; `src/runner/cases.c` untouched (D-21 whitelist unchanged).

## Deviations from Plan

**1. [Rule 1 - Bug] Test regex order** - Found during Task 1 and Task 2: the CTest regexes assumed an output order that differs from the runner's (observe lines sort `checkpoint.*` before `class`; Mooneye cases print in `cases[]` order daa, tim00, tim00-div-trigger). Fixed the regexes; no runner change. Commits b7753f3, 5cdb263.

**2. [Minor] Configure-failure message names the file and the offending digest but not the line number** (`file(STRINGS)` does not return line numbers). The failure was verified.

**Total deviations:** 1 auto-fixed, 1 minor. **Impact:** none on behavior.

## Known Stubs

None.

## Threat Flags

None. T-07-19 and T-07-41 mitigations are in place as planned.

## Next

Ready for 07-10.

## Self-Check: PASSED

- Files exist: ldbb-controls.txt, acceptance.c/.h, main.c, CMakeLists.txt, expect_exit.cmake
- Commits b7753f3, 5bf1182, 5cdb263 are on the branch
