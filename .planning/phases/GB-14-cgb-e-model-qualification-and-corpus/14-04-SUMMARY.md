---
phase: 14-cgb-e-model-qualification-and-corpus
plan: "04"
subsystem: testing
tags: [CGB-E, APU, CH3, audio, fuzzing]
plan_head_before: b7044289ccae28d48a02f70a51ef7ec791357c21
plan_head_after: 7635b3886664fb5f08e93bfb3aa842fc9dc10fc7
commits: 4
requires:
  - phase: 14-03
    provides: [CGB APU latch and fetch behavior, CGB trigger and length sequencing]
provides:
  - CGB-08 APU lifecycle and bounded-execution test evidence
  - CH3 fetch split/rejoin and output-pressure regression coverage
affects: [Phase 14 corpus qualification, CGB APU test contracts]
actuals:
  tokens: 13734.5
  tasks: 2
  commits: 4
tech-stack:
  added: []
  patterns: [field-by-field private state digests, bounded deterministic guest fuzzing, host-output invariance checks]
key-files:
  created: []
  modified:
    - tests/test_cgb_partition.c
    - tests/test_cgb_apu.c
    - tests/fuzz_core.c
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
key-decisions:
  - Kept lifecycle and pressure qualification test-side because the existing core passed the new reset, load, failure, and isolation contracts.
  - Kept the evidence scoped to the CGB-E software model; it does not claim hardware or game-level proof.
patterns-established:
  - Compare split guest observations field-by-field without serializing or hashing structure padding.
  - Give hostile APU seeds explicit operation, run-call, half-dot, and terminal-verdict bounds.
requirements-completed: []
coverage:
  - id: D1
    description: CH3 fetch and PCM guest observations remain equal across split runs at normal and double speed.
    human_judgment: false
    verification:
      - kind: integration
        ref: ctest --test-dir build -R '^(cgb_apu_partition_fetch|cgb_apu_partition_speed|cgb_apu_partition_controls|cgb_partition_snapshot_fidelity)$' --output-on-failure --no-tests=error
        status: pass
  - id: D2
    description: Reset, successful load, failed-load preservation, and separate-instance isolation cover APU and IR state.
    human_judgment: false
    verification:
      - kind: unit
        ref: ctest --test-dir build -R '^(cgb_apu_lifecycle|cgb_apu_lifecycle_controls)$' --output-on-failure --no-tests=error
        status: pass
  - id: D3
    description: Guest PCM and bus observations are invariant under absent, full, and drained host audio output through DIV, speed-switch, and HDMA transitions.
    human_judgment: false
    verification:
      - kind: integration
        ref: ctest --test-dir build -R '^cgb_apu_output_pressure$' --output-on-failure --no-tests=error
        status: pass
  - id: D4
    description: Deterministic hostile APU seeds exercise truncated and oversized loader inputs with bounded guest operations and terminal observations.
    human_judgment: false
    verification:
      - kind: unit
        ref: ctest --test-dir build -R '^cgb_apu_hostile_seeds$' --output-on-failure --no-tests=error
        status: pass
  - id: D5
    description: Shared HDMA and speed identity seams remain green and the frozen DMG baseline stays unchanged.
    human_judgment: false
    verification:
      - kind: integration
        ref: ctest --test-dir build -R '^(cgb_hdma_partition_midbyte|cgb_hdma_lifecycle|cgb_hdma_competing_stalls|cgb_speed_identity_pin)$' --output-on-failure --no-tests=error
        status: pass
      - kind: other
        ref: bash tests/scripts/verify-dmg-baseline.sh
        status: pass
duration: 19min
completed: 2026-10-15
status: complete
---

# Phase 14 Plan 04: CGB-E Model Qualification and Corpus Summary

**CH3 fetch partitioning, APU lifecycle and bounded hostile-seed regressions now verify CGB-E guest observations across host audio-output modes.**

## Performance

- **Duration:** 19 minutes
- **Started:** 2026-10-15T15:34:27-04:00
- **Completed:** 2026-10-15T19:53:52Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Added a field-by-field CH3 sample-latch digest and split/rejoin guest checks around fetch boundaries at normal and double speed, with lost-remainder and duplicate-fetch controls.
- Verified APU/IR state across create, reset, successful ROM replacement, failed ROM replacement, and independent instances; the failed-load case preserves the full machine digest and subsequent audio output.
- Compared PCM bytes and timestamped guest bus events with no host output, a full output buffer, and one-frame draining through NR52, DIV, KEY1 speed switching, and GDMA.
- Added a deterministic CGB APU fuzz route with truncated and oversized ROM probes, a 16-operation cap, at most 16 run slices, an 8,192-half-dot limit, and an explicit terminal verdict.

## Task Commits

1. **Task 1: CH3 fetch partition tracer** — `0de393e` (TDD RED), `bccf33f` (feat).
2. **Task 2: APU lifecycle, output pressure, and hostile seeds** — `b140e91` (TDD RED), `7635b38` (feat).

The summary and plan metadata are recorded in a separate documentation commit after self-check.

## Files Created/Modified

- `tests/test_cgb_partition.c` — private CH3-state digest, split checks, lifecycle behavior, and sensitivity controls.
- `tests/test_cgb_apu.c` — exact guest PCM/bus comparisons across host-buffer modes and bounded APU seed assertions.
- `tests/fuzz_core.c` — deterministic CGB APU route with bounded hostile loader probes and guest execution.
- `tests/CMakeLists.txt`, `tests/expected-tests.txt` — exact new CTest registrations and inventory entries.

## Decisions Made

- No production core or public API change was needed: lifecycle and host-output regressions passed against the existing implementation.
- The pressure guest uses a 200,000-half-dot execution budget to cross the modeled 131,076-half-dot normal-to-double speed-switch stall. CTest timeout settings were unchanged.
- CGB-08 test evidence is recorded here; requirement-ledger marking remains with the phase orchestrator.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking issue] Placed the CH3 guest body beyond the ROM header checksum.**
- **Found during:** Task 1 (CH3 fetch partition tracer)
- **Issue:** The authored guest body overlapped the ROM header checksum when execution began at `$0100`, causing the fixture to fail ROM validation.
- **Fix:** Added a jump at `$0100` to `$0150` and placed the guest body after the header.
- **Files modified:** `tests/test_cgb_partition.c`
- **Verification:** Full Phase 1 configure/build and focused partition tests passed.
- **Committed in:** `bccf33f`.

**Total deviations:** 1 auto-fixed blocking issue.
**Impact on plan:** The fixture correction made the planned guest executable; no scope or public behavior changed.

## TDD Evidence

- Task 1 RED: `cgb_partition_snapshot_fidelity` failed on the intended missing-field assertion, `partition-inert-input cgb-apu-wave-sample-buffer`; the digest then included the CH3 sample buffer.
- Task 2 RED: `cgb_apu_hostile_seeds` executed and failed because the APU fuzz route was absent. `gsd-tools check tdd-red-evidence` returned `RED_EVIDENCE_OK`; the new route and bounds made the test pass.
- Negative controls detected lost fetch remainder, duplicate fetch, reset sample-phase leakage, failed-load clearing, and a mutated host-output PCM value (`0x0f` expected, `0x0e` control).

## Validation

- `cmake --preset phase1 && cmake --build --preset phase1` — passed.
- Exact CTest inventory check — no required test names missing.
- Focused APU, partition, HDMA, and speed group — 12/12 passed with two workers.
- `bash tests/scripts/verify-dmg-baseline.sh` — passed; inventories remained keys 313, Mooneye 15, acceptance 20, benchmark 2; baseline changes were 0 rows.
- Hostile-seed observations: 11 ops / 3 runs / 592 half-dots; truncated seed 0 ops / 1 run / 152 half-dots; repeated-transition seed 7 ops / 2 runs / 432 half-dots; full-size input 16 ops / 4 runs / 792 half-dots. Every case reached a terminal verdict within its bound.
- Pressure guest read PCM `0x0f, 0x07, 0x0f, 0x00, 0x00` and KEY1 `0xfe`; 761 audio frames and 51 bus events matched across the host-output variants.

## Issues Encountered

The initial pressure-run budget stopped before the speed-switch stall completed. The guest now uses a bounded 200,000-half-dot budget and asserts the observed KEY1 read follows the modeled stall. No CTest timeout was increased.

## User Setup Required

None.

## Next Phase Readiness

Plan 14-04 supplies the APU lifecycle, partition, and bounded-execution evidence for the remaining Phase 14 corpus/reporting work. The result qualifies the software model only; it does not claim physical-hardware or commercial-game proof.

---
*Phase: 14-cgb-e-model-qualification-and-corpus*
*Completed: 2026-10-15*

## Self-Check: PASSED

- Summary file exists at the plan output path.
- All four task commits are ancestors of `plan_head_after`.
- Coverage classifier auto-covered 5/5 deliverables; the `summary_coverage` CTest passed.
