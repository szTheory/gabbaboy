---
phase: 13-cgb-hdma
plan: "04"
subsystem: core-timing
tags: [cgb, hdma, partition, lifecycle, resource-bounds, fuzz, ctest]

requires:
  - phase: "13-03"
    provides: "Real guest HALT wake, independent HDMA and speed residuals, and selected stop/order policies"
provides:
  - "Private full-field HDMA partition oracle for CPU-programmed transfers, cuts, and timestamped output"
  - "HDMA lifecycle, instance-isolation, finite-work headroom, capacity, and bounded hostile-seed regressions"
affects: [phase-13-remaining-plans, phase-14-model-qualification]

actuals:
  tokens: 18377
  tasks: 2
  commits: 4
commits: 4
plan_head_before: 533dddfc89fedb7e6e8d2310132f2faea4e8cb9d
plan_head_after: f8aeacae7b6a10888e90143d311e8f353ee7c196

tech-stack:
  added: []
  patterns:
    - "Explicit private state digests compare uninterrupted and split execution without exposing a save-state format"
    - "Preflight CPU and interrupt writes that may start FF55 work before mutating machine or output state"
    - "Deterministic bounded HDMA seeds are run in CTest when a matching libFuzzer runtime is unavailable"

key-files:
  created:
    - tests/test_cgb_hdma_partition.c
  modified:
    - tests/test_cgb_partition.c
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - src/core/gabbaboy.c
    - tests/test_cgb_hdma_internal.c
    - tests/fuzz_core.c
    - docs/model-gates.md

key-decisions:
  - "A valid FF55 start must fit its instruction cost plus count×64 finite byte-work half-dots in the remaining master-time counter; arbitrary HBlank waits are not forecast."
  - "All HDMA snapshot fields are explicitly hashed and compared; no raw structure dump or public/save-state API is introduced."
  - "Hostile-seed coverage is reported as deterministic CTest seed regression only; no libFuzzer campaign ran because the matching Clang runtime is unavailable."
  - "CGB-07 remains open until the remaining Phase 13 plan completes."

task_commits:
  - task: 1
    stage: RED
    hash: b5e26fc3be1208e2424d00b162bbd00f178e5647
  - task: 1
    stage: GREEN
    hash: 2bc342303ee6bc470acd0857088d789e4b4d6bcd
  - task: 2
    stage: RED
    hash: 8f3c5e0ab01b359f06b8a21ff1e969bd07ac368b
  - task: 2
    stage: GREEN
    hash: f8aeacae7b6a10888e90143d311e8f353ee7c196

requirements-completed: []

coverage:
  - id: D1
    description: "CPU-programmed HDMA produces equal explicit state, guest memory, and timestamped output across critical cuts, both speed directions, and deterministic multi-cut schedules; lost-phase and ordering controls detect their named defects."
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build -R '^(cgb_hdma_partition_|cgb_partition_|cgb_hdma_guest_|summary_coverage)' --output-on-failure --no-tests=error"
        status: pass
  - id: D2
    description: "Create, reset, successful and failed load, and independent instances clear, preserve, or isolate every HDMA field as specified."
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build -R '^(cgb_hdma_(lifecycle|resource_bounds|hostile_seeds|partition_)|api_|cgb_instance_isolation$|summary_coverage)' --output-on-failure --no-tests=error"
        status: pass
  - id: D3
    description: "Finite transfer headroom, maximum block work, trace/audio/diagnostic capacities, and deterministic FF51–55 seeds stay bounded and non-mutating on named rejection controls."
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build -R '^(cgb_hdma_(lifecycle|resource_bounds|hostile_seeds|partition_)|api_|cgb_instance_isolation$|summary_coverage)' --output-on-failure --no-tests=error"
        status: pass
      - kind: other
        ref: "bash tests/scripts/verify-dmg-baseline.sh"
        status: pass
  - id: D4
    description: "The model-gate source and documentation stay in bijection and the complete inherited regression suite passes."
    human_judgment: false
    verification:
      - kind: other
        ref: "python3 -I tests/scripts/verify-model-gates.py"
        status: pass
      - kind: other
        ref: "ctest --test-dir build --parallel 4 --output-on-failure"
        status: pass

duration: 30min
completed: 2026-10-14
status: complete
---

# Phase 13 Plan 04: Partition, lifecycle and hostile-resource invariants Summary

**A full-field private oracle proves split HDMA execution and output match; checked headroom bounds accepted FF55 work before it can overflow master time.**

## Performance

- **Duration:** about 30 minutes
- **Started:** 2026-10-14 (plan execution; first RED receipt committed at 16:49 EDT)
- **Completed:** 2026-10-14T17:13:11-04:00
- **Tasks:** 2
- **Implementation and test files changed:** 8

## Accomplishments

- Extended the private explicit partition digest to include every HDMA latch, cursor, pending edge, byte phase, VBK sample, and independent stall remainder. Real CPU-programmed transfers now match uninterrupted state, guest output, and timestamped records across critical cuts in both speed directions.
- Added lifecycle and isolation checks for create, reset, successful/failed load, and independent instances, plus bounded capacity and deterministic FF51–55 seed regressions with named defect controls.
- Added a preflight guard for CPU and interrupt stack writes that may start FF55. It checks widened instruction cost plus finite count×64 byte work, and rejects without changing CPU, DMA, trace, or output state when headroom is insufficient.
- Kept the frozen DMG baseline unchanged and recorded the new CGB-only model gate and its finite-work policy.

## Task Commits

Each TDD task has a semantic RED and a passing GREEN commit:

| Task | Stage | Commit | Message |
| --- | --- | --- | --- |
| 1 | RED | `b5e26fc` | Add HDMA digest completeness red |
| 1 | GREEN | `2bc3423` | Add HDMA split-run partition oracle |
| 2 | RED | `8f3c5e0` | Add HDMA lifecycle and headroom regressions |
| 2 | GREEN | `f8aeaca` | Guard finite HDMA work against time overflow |

Machine-readable references to the same task commits above:

1. **Task 1: Recorded execution commits** — `b5e26fc`, `2bc3423`.
2. **Task 2: Recorded execution commits** — `8f3c5e0`, `f8aeaca`.

## Verification Receipts

- `build/13-04-task1-verify.xml` — required-name enumeration and 33/33 partition, inherited guest, and summary-coverage checks.
- `build/13-04-task2-verify.xml` — six required names present exactly once and 16/16 lifecycle, resource, hostile-seed, partition, API, instance, and summary-coverage checks.
- `build/13-04-full-ctest.xml` — full CTest suite, 940/940 passed after the model-gate documentation fix.
- `build/13-04-task2-red.xml` and `build/13-04-task2-red-evidence.json` — semantic RED showing a 3-block FF55 request was accepted with 215 half-dots of headroom, one short of the required 216.
- `build/Testing/Temporary/LastTest.log` — final full-suite CTest log.

The DMG baseline reports inventory 313, Mooneye 15, acceptance 20, benchmark 2, zero changed rows, and `baseline status=pass`. No matching Clang libFuzzer runtime was available, so only deterministic bounded seed tests ran; this is not reported as a fuzz campaign. No hardware evidence is implied.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical model-gate metadata] Added the finite-headroom gate to its source/document contract.**

- **Found during:** Task 2 full-suite verification
- **Issue:** The core’s new CGB-only guard introduced GATE-99, but the required model-gate table lacked its source row; two helper definitions also needed the shared model-neutral function tag. The model-gate checks rejected the new source until the documentation and tags matched.
- **Fix:** Added GATE-99 to the canonical table and Phase 13 disposition, documented the finite byte-work rule, and tagged the model-neutral CPU store resolvers.
- **Files modified:** `src/core/gabbaboy.c`, `docs/model-gates.md`
- **Verification:** `python3 -I tests/scripts/verify-model-gates.py`; `model_gates`, `model_gates_real_deleted_tag`, and `model_gates_real_untagged_function` all pass; final full CTest passes 940/940.
- **Committed in:** `f8aeaca`

**Total deviations:** 1 auto-fixed model-gate contract omission.
**Impact on plan:** Required documentation and source annotations were added; no public API, dependency, or Phase 14 work was introduced.

## Issues Encountered

The first full run exposed three model-gate failures tied to the new source tag. After adding the canonical documentation and helper tags, CMake was reconfigured so the generated mutation fixtures used the final source; all three focused model-gate checks and the complete 940-test suite then passed.

## User Setup Required

None.

## Next Phase Readiness

Plan 13-04 is complete. Phase 13 remains active and CGB-07 remains open. The remaining Phase 13 plan is **13-08: Original visible DMA guest and existing player smoke**; the owner chooses when to continue with **`/gsd-execute-phase 13`**. Stop before Phase 14.

---
*Phase: 13-cgb-hdma*
*Completed: 2026-10-14*

## Self-Check: PASSED

- SUMMARY file exists at the required plan path.
- All four task commits are ancestors of the current branch head.
- The strict `summary_coverage` CTest passed against this file.
