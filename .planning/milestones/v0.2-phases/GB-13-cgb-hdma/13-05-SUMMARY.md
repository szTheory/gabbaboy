---
phase: 13-cgb-hdma
plan: "05"
subsystem: testing
tags: [cgb, hdma, runtime-mutation, ctest, timing-sensitivity]

requires:
  - phase: "13-04"
    provides: "Bounded HDMA state, lifecycle and partition behavior to protect with targeted mutants"
provides:
  - "One shared runtime-mask core with predicate-specific HDMA fault and mask-zero control pairs"
  - "Unique Phase 13 source anchors and inherited P12 anchor/mutation sensitivity"
  - "Signed timing-offset sensitivity checks with an explicit software-model blind window"
affects: [phase-13-wave-6, phase-13-wave-7, phase-12-mutation-regressions]

actuals:
  tokens: 10239
  tasks: 2
  commits: 4
commits: 4
plan_head_before: 70721be0dc428e4683a5ebda7dfab1271f1fc5b1
plan_head_after: 4f1e3dfcacdfc63d2eaf4bee31c5351006716449

tech-stack:
  added: []
  patterns:
    - "A single generated test-only runtime-mask core serves public, internal, and partition harnesses."
    - "Each injected fault must emit its exact behavioral diagnostic while a mask-zero twin passes."
    - "Timing sensitivity uses a bounded signed offset series, not a Cartesian sweep."

key-files:
  created:
    - cmake/P13Mutants.cmake
  modified:
    - cmake/P12Mutants.cmake
    - src/core/gabbaboy.c
    - tests/test_cgb_hdma.c
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - tests/test_cgb_hdma_internal.c
    - tests/test_cgb_hdma_partition.c

key-decisions:
  - "Production uses a zero mutation mask and exposes no runtime mutation API or mutable test global."
  - "P13-05-M01 through P13-05-M14 are count-checked source anchors; P12 anchor and disposition semantics remain guarded."
  - "The guest no-steal predicate detects full CPU progress loss; sub-byte cadence sensitivity is covered only by the internal timing oracle."
  - "CGB-07 remains open; this plan adds mutation evidence and does not qualify physical CGB-E behavior."

requirements-completed: []

coverage:
  - id: p13-05-runtime-fault-pairs
    description: "The shared runtime mask causes every selected HDMA fault, including no-steal and no-copy, to fail its named behavioral predicate; each mask-zero control and the anchor guard pass."
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build -R '^cgb_hdma_mutant_' --output-on-failure --no-tests=error (29/29)"
        status: pass
      - kind: integration
        ref: "ctest --test-dir build -R '^(cgb_hdma_mutant_|cgb_hdma_timing_policy|cgb_speed_mutant_|cgb_partition_mutant_)' --output-on-failure --no-tests=error (123/123)"
        status: pass
      - kind: other
        ref: "ctest --test-dir build -R '^(cgb_hdma_mutant_no_steal|cgb_hdma_mutant_no_steal_control|cgb_hdma_mutant_no_copy|cgb_hdma_mutant_no_copy_control)$' --output-on-failure --no-tests=error (4/4; each case 0.01s)"
        status: pass
  - id: p13-05-timing-sensitivity
    description: "Signed timing offsets exercise the internal byte-commit predicate, and the public guest discriminator's sub-byte blind window is stated explicitly."
    human_judgment: false
    verification:
      - kind: unit
        ref: "ctest --test-dir build -R '^cgb_hdma_timing_sensitivity$' --output-on-failure --no-tests=error"
        status: pass
  - id: p13-05-inherited-regression
    description: "Inherited P12 mutation anchors and the complete native suite retain their registered behavior, including the frozen DMG baseline."
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build --parallel 4 --output-on-failure (971/971)"
        status: pass
      - kind: other
        ref: "ctest --test-dir build -R '^(model_gates|dmg_baseline)$' --output-on-failure --no-tests=error (2/2)"
        status: pass
      - kind: other
        ref: "cmake --preset phase1 && cmake --build --preset phase1 --parallel 4 (166 build actions; real 3.65s)"
        status: pass

duration: 12min
completed: 2026-10-14
status: complete
---

# Phase 13 Plan 05: Bounded runtime mutation sensitivity and inherited anchors Summary

**One shared runtime-mask core now detects 13 selected HDMA faults through named behavioral predicates, with passing mask-zero twins and preserved P12 anchors.**

## Performance

- **Duration:** about 12 minutes
- **Started:** 2026-10-14T21:50:49Z
- **Completed:** 2026-10-14T22:02:36Z
- **Tasks:** 2
- **Implementation and test files changed:** 8
- **Native Debug build:** 166 build actions, 3.65 seconds wall time with parallelism 4. The generated mutant core is one static library shared by three HDMA harness executables; no per-mask core clones were produced.
- **Focused mutant runtime:** the no-steal and no-copy fault/control cases each completed in 0.01 seconds; their four-case CTest run took 0.04 seconds wall time.

## Accomplishments

- Added one generated runtime-mask mutant core shared by the public, internal, and partition HDMA harnesses. Its zero-mask path follows production behavior, and the installed public header gains no mutation API or mutable test global.
- Added 13 selected predicate-specific fault pairs, including no-copy, duplicate copy, bank/address/count/cancel errors, speed-scaled cadence, HALT and trigger errors, DMA loss at IRQ, speed realignment, commit order, and dropped partition phase. Together with the no-steal pair, the anchor guard and mask-zero controls, all 29 P13 mutation lane checks pass.
- Added fourteen unique P13-05 source anchors and retained the P12 anchor checks. The inherited selected mutation and timing lane passes 123/123.
- Added a signed duration-offset sensitivity series at -8, -4, -2, -1, +1, +2, +4, and +8 half-dots. It checks byte-commit timing in one normal-speed master-time series; double-speed cadence remains a separate predicate.
- The public guest no-steal predicate proves full CPU no-steal detection while retaining the data path. Sub-byte shifts remain outside that guest predicate and are checked only by the internal timing oracle. Physical CGB-E timing remains UNKNOWN.

## TDD Evidence

Both tasks produced semantic RED evidence before implementation. Task 1's public guest reported ordinary passing behavior because the no-steal runtime bit was not yet wired; its missing named timing diagnostic made the mutant wrapper fail. Task 2's internal harness copied all 16 bytes because the no-copy bit was not yet implemented; the required no-copy predicate therefore failed. Neither RED was caused by build discovery, a missing test, a crash, or an arbitrary exit. The ignored evidence records are `build/13-05-red-task1.json` and `build/13-05-red-task2.json`.

## Task Commits

| Task | Stage | Commit | Message |
| --- | --- | --- | --- |
| 1 | RED | `e892b11` | Add runtime-mask HDMA mutant RED test |
| 1 | GREEN | `cebca68` | Enable runtime no-steal mask |
| 2 | RED | `27e6583` | Add no-copy mutant RED predicate |
| 2 | GREEN | `4f1e3df` | Add bounded HDMA runtime fault pairs |

The SUMMARY and state/roadmap handoff are recorded separately in the final plan-metadata commit.

Machine-readable references to the same task commits above:

1. **Task 1: Recorded execution commits** — `e892b11`, `cebca68`.
2. **Task 2: Recorded execution commits** — `27e6583`, `4f1e3df`.

## Verification Receipts

- `cmake --preset phase1` and `cmake --build --preset phase1 --parallel 4` passed; the full native build completed 166 actions in 3.65 seconds wall time.
- `ctest --test-dir build -R '^cgb_hdma_mutant_' --output-on-failure --no-tests=error` passed 29/29. Each fault wrapper required its specific diagnostic and exit code, while its mask-zero control passed; the missing/duplicate anchor guard passed.
- `ctest --test-dir build -R '^(cgb_hdma_mutant_|cgb_hdma_timing_policy|cgb_speed_mutant_|cgb_partition_mutant_)' --output-on-failure --no-tests=error` passed 123/123 across P13 and affected inherited P12 groups.
- `ctest --test-dir build -R '^cgb_hdma_timing_sensitivity$' --output-on-failure --no-tests=error` passed. The selected signed offsets observed commits at 1, 1, 2, 3, 5, 6, 8, and 12 half-dots for offsets -8 through +8 in the configured sequence.
- `ctest --test-dir build --parallel 4 --output-on-failure` passed 971/971. `ctest --test-dir build -R '^(model_gates|dmg_baseline)$' --output-on-failure --no-tests=error` passed 2/2; the frozen DMG baseline has zero changed rows.
- The matching Clang libFuzzer runtime remains unavailable. No fuzz campaign or physical hardware result is claimed.

## Files Created/Modified

- `cmake/P13Mutants.cmake` — shared runtime-mask core generation, exact mutation wrappers, and anchor guard.
- `cmake/P12Mutants.cmake` — reusable exact unique-anchor check with inherited P12 behavior preserved.
- `src/core/gabbaboy.c` — zero-default test-only mutation branches at uniquely tagged predicates.
- `tests/test_cgb_hdma.c` — runtime-mask argument handling in the public guest harness.
- `tests/CMakeLists.txt` and `tests/expected-tests.txt` — exact mutation/control test registration and timing-sensitivity inventory.
- `tests/test_cgb_hdma_internal.c` — targeted fault predicates and signed timing-offset checks.
- `tests/test_cgb_hdma_partition.c` — partition-phase fault predicate and control.

## Decisions Made

- Keep the generated runtime mask confined to the test core. Production defaults to a zero mask and retains no mutation state or public setter.
- Keep public guest coverage for full CPU no-steal behavior and use an internal oracle for sub-byte timing sensitivity; do not infer hardware cadence from this emulator-only seam.
- CGB-07 remains open until the remaining Phase 13 behaviors and requirement evidence are complete.

## Deviations from Plan

None. The implementation stays within the declared core, CMake, and three HDMA harness ownership.

## Issues Encountered

A provisional anchor label collided with an existing marker during configure. It was replaced with the unique `P13-05-M01` through `P13-05-M14` names; the exact-count anchor guard and mutation suite pass.

## Known Limitations

The public guest timing predicate cannot resolve sub-byte cadence shifts. Those shifts have an internal deterministic test oracle, but the current evidence does not qualify physical CGB-E timing. No matching Clang libFuzzer runtime was available, so only the bounded CTest fault/control set was executed.

## Next Phase Readiness

Phase 13 remains active and CGB-07 remains open. Wave 5 is closed; the next stage is **Phase 13 Wave 6, plan 13-07 — Magen HDMA admission and structural differential oracle**, via **`/gsd-execute-phase 13 --wave 6`**. Stop after Phase 13; Phase 14 remains unstarted. Both auto-advance flags remain false.

---
*Phase: 13-cgb-hdma*
*Completed: 2026-10-14*

## Self-Check: PASSED

- The implementation files named above exist and the four task commits are ancestors of the current plan head.
- The measured plan commit count is 4 from base `70721be0dc428e4683a5ebda7dfab1271f1fc5b1` through `4f1e3dfcacdfc63d2eaf4bee31c5351006716449`.
- No task changes remain unstaged; owner-owned `.planning/config.json`, `.planning/state.json`, and `.planning/milestone.lock` remain untouched.
