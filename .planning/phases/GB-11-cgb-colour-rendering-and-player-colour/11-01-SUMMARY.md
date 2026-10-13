---
phase: 11-cgb-colour-rendering-and-player-colour
plan: 01
subsystem: colour-test-safety-net
tags: [dmg-identity, mutant-harness, priority-oracle, truth-table, d-25, d-22, d-35]
requires:
  - phase: 10-cgb-profile-banking-and-register-visibility
    provides: "CGB profile, banking, gbb_banking_mutant precedent"
provides:
  - "cgb_dmg_identity_shade_pin: FNV-1a 64 pins of the DMG frame for demo, libbet and tracer"
  - "gbb_colour_mutant: configure-time exactly-once mutant harness (white-box and public)"
  - "tests/data/cgb-priority-truth.inc: 6144 rows from an independent Pan Docs oracle"
  - "cgb_colour_copy_frame_unsupported: D-16 pin of gbb_copy_frame on the CGB profile"
affects: [11-03, 11-04, 11-05]
actuals:
  tokens: 45000
  tasks: 2
  commits: 2
key-files:
  created:
    - tests/test_cgb_colour_internal.c
    - tests/test_cgb_colour.c
    - tests/scripts/gen-cgb-priority-truth.py
    - tests/data/cgb-priority-truth.inc
  modified:
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
key-decisions:
  - "libbet is pinned at 900 frames because it renders a blank frame for its first several hundred frames; the tracer ROM is genuinely blank, so its pin guards blank-stays-blank"
  - "The shade pins are regression pins recorded at the pre-phase head, not hardware evidence"
  - "ASan preset is Linux-only (CMake refuses it on this host), so phase1-asan was not run locally; no core C was touched"
requirements-completed: [CGB-04]
coverage:
  - id: D1
    description: "DMG shade-identity pin over three ROMs is proven able to fail by a shade-flip core mutant while its control case passes"
    human_judgment: false
    verification:
      - kind: unit
        ref: "cgb_dmg_identity_shade_pin"
        status: pass
      - kind: unit
        ref: "cgb_dmg_identity_mutant_shade_flip"
        status: pass
      - kind: unit
        ref: "cgb_dmg_identity_mutant_shade_flip_control"
        status: pass
  - id: D2
    description: "gbb_copy_frame stays unsupported on the CGB profile in CGB and compat mode and works on DMG"
    human_judgment: false
    verification:
      - kind: unit
        ref: "cgb_colour_copy_frame_unsupported"
        status: pass
  - id: D3
    description: "Independent 6144-row priority truth table is regenerable, byte-compared, sensitivity-checked and fails on an altered row"
    human_judgment: false
    verification:
      - kind: unit
        ref: "cgb_priority_truth_regen"
        status: pass
      - kind: unit
        ref: "cgb_priority_truth_selftest"
        status: pass
      - kind: unit
        ref: "cgb_priority_truth_regen_mutated"
        status: pass
  - id: D4
    description: "Table shape, uniqueness of every input combination and eight hand-written golden rows agree with the oracle"
    human_judgment: false
    verification:
      - kind: unit
        ref: "cgb_priority_table_shape"
        status: pass
  - id: D5
    description: "No production core change and the DMG baseline is intact"
    human_judgment: false
    verification:
      - kind: other
        ref: "bash tests/scripts/verify-dmg-baseline.sh"
        status: pass
status: complete
commits: 2
plan_head_before: 124029a8b96e65f62db3a2dac794f862b8d4086c
plan_head_after: 452c1918340922253e5e182a245ad1d0c9cb29b4
duration: 25 min
completed: 2026-10-12
---

# Phase 11 Plan 01: Colour safety net Summary

A DMG shade-identity digest pin, a generalised configure-time colour mutant harness proven by a failing shade-flip mutant, and an independent Pan Docs priority oracle with a committed 6144-row truth table, all landed before any colour code.

## Accomplishments

- cgb_dmg_identity_shade_pin hashes frame_completed for demo.gb (60 frames), libbet.gb (900 frames) and tracer.gb (60 frames) on DMG-CPU-B; the constants are regression pins from the unmodified core.
- gbb_colour_mutant supports a white-box source (mutated copy included through GBB_COLOUR_CORE_SOURCE) or a public source (STATIC mutant library). The shade-flip mutant makes the pin fail with "observed"; its control exits 0.
- gen-cgb-priority-truth.py writes, checks and self-tests the table (9 inputs sensitive, three oracle mutants detected). It contains no reference to the core.
- cgb_priority_table_shape checks the count, ranges, uniqueness and eight golden rows.

## Deviations from Plan

**1. [Rule 1 - Bug] libbet pin frame count.** Found during Task 1: libbet and tracer both produced the all-zero frame digest at 120 frames, so the pin was vacuous for libbet. libbet was moved to 900 frames, where it draws graphics. The tracer ROM stays blank by nature, and the comment says so.

**2. [Rule 1 - Bug] copy-frame test run-stop check.** A zero-filled ROM does not stop with BUDGET or HALTED_IDLE, so the case now only forbids INVALID_STATE.

**3. [Rule 3 - Blocker] phase1-asan unavailable.** CMake restricts GABBABOY_ENABLE_SANITIZERS to Linux, so the ASan run was not possible on this host. No core C changed.

**Total deviations:** 3 (2 auto-fixed, 1 environment limit). **Impact:** none on scope.

## Verification

- `ctest --preset phase1`: 552/552 passed.
- `bash tests/scripts/verify-dmg-baseline.sh`: baseline status=pass.
- `git diff --name-only -- src/core/gabbaboy.c` is empty; tests/ only.

## Known Stubs

None.

## Self-Check: PASSED

All created files exist and both task commits (eb50c03, 452c191) are ancestors of HEAD.
