---
phase: 10-cgb-profile-banking-and-register-visibility
plan: 17
subsystem: benchmark-harness
tags: [benchmark, ab, dmg, banking, d-22, advisory]
requires:
  - phase: 10-cgb-profile-banking-and-register-visibility
    provides: "10-16 CGB runner suite; banking indirection on the DMG path"
provides:
  - "tests/scripts/measure-release-baseline.sh --ab BASE HEAD interleaved A/B mode with digest check, receipt writer and validator"
  - "CTest cgb_bench_ab_selftest, cgb_bench_ab_wrong_digest, cgb_bench_ab_missing_field (not WIN32)"
  - "10-BENCH.md and 10-BENCH.json: three-build evidence against the frozen Phase 7 baseline"
affects: [18, 19, 20]
actuals:
  tokens: 14000
  tasks: 2
  commits: 3
key-files:
  created:
    - .planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-BENCH.md
    - .planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-BENCH.json
  modified:
    - tests/scripts/measure-release-baseline.sh
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - cmake/ExpectedTests.cmake
key-decisions:
  - "Review trigger fired: three headline runs put Phase 10 at 105.6 to 107.3 percent of the frozen baseline time (lower margin bound above 100); owner decides under D-016, no optimisation done (owner veto item 5)"
  - "Windows skips the bash-only bench tests by removing them from the expected inventory in cmake/ExpectedTests.cmake"
requirements-completed: []
status: complete
commits: 3
plan_head_before: 17386dc6369a3a0c75f3313fe71e23d72009438a
plan_head_after: c961c3f73c996d2b7ef4c5bad50d6a18f7c5bf79
duration: 35 min
completed: 2026-10-12
coverage:
  - id: D1
    description: "--ab mode proves both builds print the frozen digest and writes a validated receipt, from CTest without asserting time"
    human_judgment: false
    verification:
      - {kind: ctest, ref: "cgb_bench_ab_selftest", status: pass}
  - id: D2
    description: "Wrong digest and a receipt missing a field fail with their named reasons"
    human_judgment: false
    verification:
      - {kind: ctest, ref: "cgb_bench_ab_wrong_digest", status: pass}
      - {kind: ctest, ref: "cgb_bench_ab_missing_field", status: pass}
  - id: D3
    description: "Banking-indirection DMG cost recorded against the Phase 7 baseline with uncertainty and attribution"
    human_judgment: true
    rationale: "Whether a roughly 6 to 7 percent advisory cost needs performance work is an owner decision under D-016"
---

# Phase 10 Plan 17: DMG banking-indirection A/B benchmark Summary

Advisory `--ab` mode for the release-measure script (interleaved pairs, digest-checked, privacy-safe validated receipt) plus a three-build run showing the Phase 10 DMG path at about 106 to 107 percent of the frozen Phase 7 baseline time, so the D-22 review trigger fired.

## Accomplishments

- `--ab BASE HEAD`: 30 interleaved pairs (default; bounds 3..30, warm-ups 3, bounds 1..20) with alternating order, every run must print `correctness_digest_fnv1a64=4c7a57ff3d50d228` (else `ab-digest-mismatch`), receipt fields validated (`ab-receipt-missing`), receipt rejects `/Users/` or `/home/` paths. Existing default and `--self-test` paths are unchanged.
- CTest `cgb_bench_ab_selftest` (3 samples, 1 warm-up, same binary twice) plus two exact-exit negative controls; all three are registered only off Windows and removed from the Windows expected inventory.
- Evidence (macOS arm64, Apple M5 Pro class, Release -O3, Apple clang 21): headline vs 5a55f19 median 107.28 / 105.59 / 105.98 percent over three runs; attribution vs d7e2e0a median 100.67 percent (within noise, min-of-n 103.52).

## Owner veto item 5 (flagged)

The +5% review trigger fired on the headline comparison in all three runs. The per-access bank indirection costs roughly 6 to 7 percent of DMG workload time against the frozen baseline. The attribution run cannot cleanly split Phase 9 from Phase 10. The host was loaded (load average about 10 to 11), per-pair SD was 9 to 11 percent, so the figures are advisory. No optimisation was added; `tests/baseline` is untouched. The owner decides under D-016.

## Deviations from Plan

None - plan executed as written. The tracer commit registered the self-test only; the two controls came in the second commit (task 2), as planned. The headline was run three times instead of once because the first run was noisy; all three are in 10-BENCH.json.

## Verification

- `ctest -R '^cgb_bench_ab_'`: 3/3 pass. Full suite: 527 tests, 525 passed in the first run; `mooneye_mbc_case_mbc2_bits_ramg` and `dmg_baseline` timed out under heavy host load (concurrent benchmark builds on a shared machine) and both pass on rerun (1.4 s and 4.1 s).
- Acceptance greps: ab-digest-mismatch and ab-receipt-missing present; inventory names present once each; no `/Users/` or `/home/` in 10-BENCH.json; `git diff main -- tests/baseline` empty; worktrees removed (only the main tree remains).

## Known Stubs

None.

## Threat Flags

None. T-10-24 mitigated: receipt records only `uname`-class hardware and CPU brand, validated against home paths.

## Self-Check: PASSED
