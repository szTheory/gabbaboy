---
phase: 11-cgb-colour-rendering-and-player-colour
plan: 05
subsystem: cgb-priority-truth-table
tags: [truth-table, mutants, d-22, d-06, d-07, d-08, d-39, d-05, d-25]
requires:
  - phase: 11-cgb-colour-rendering-and-player-colour
    provides: "11-01 independent priority oracle, 11-03 CGB pixel path, 11-04 compat renderer"
provides:
  - "cgb_priority_truth_table: all 6144 oracle rows through ppu_pixel_cgb and ppu_pixel_compat"
  - "cgb_priority_truth_frames: 64-row whole-frame sample through real OAM and dispatch"
  - "cgb_priority_opri_no_effect and twelve mutants with controls"
affects: [11-06]
requirements-completed: []
actuals:
  tokens: 30000
  tasks: 3
  commits: 2
coverage:
  - id: C1
    description: "Every one of the 6144 oracle rows matches the colour the real CGB-mode and compat-mode pixel functions produce, and the checked count is asserted"
    human_judgment: false
    verification:
      - kind: unit
        ref: "cgb_priority_truth_table"
        status: pass
  - id: C2
    description: "A deterministic sample of 64 rows rendered through whole frames with real OAM matches the oracle"
    human_judgment: false
    verification:
      - kind: integration
        ref: "cgb_priority_truth_frames"
        status: pass
  - id: C3
    description: "Each composer input (BG attribute bit 7, OAM bit 7, LCDC.0, the BG index 0 rule) is shown able to break the table"
    human_judgment: false
    verification:
      - kind: unit
        ref: "cgb_priority_mutant_ignore_bg_attr7"
        status: pass
      - kind: unit
        ref: "cgb_priority_mutant_ignore_obj_attr7"
        status: pass
      - kind: unit
        ref: "cgb_priority_mutant_lcdc0_inverted"
        status: pass
      - kind: unit
        ref: "cgb_priority_mutant_no_index0_rule"
        status: pass
  - id: C4
    description: "CGB-mode objects order by OAM index only and OPRI has no effect: an X-order mutant fails the table and an OPRI-live mutant fails the no-effect case"
    human_judgment: false
    verification:
      - kind: unit
        ref: "cgb_priority_opri_no_effect"
        status: pass
      - kind: unit
        ref: "cgb_priority_mutant_cgb_x_order"
        status: pass
      - kind: unit
        ref: "cgb_priority_mutant_opri_live"
        status: pass
  - id: C5
    description: "Compat renderer semantics (LCDC.0 as BG enable, objects through their own palette sets) are mutation-checked on the compat rows"
    human_judgment: false
    verification:
      - kind: unit
        ref: "cgb_priority_mutant_compat_lcdc0_ignored"
        status: pass
      - kind: unit
        ref: "cgb_priority_mutant_compat_bg_set_for_objects"
        status: pass
  - id: C6
    description: "Attribute bank, flip bits and VBK independence each have a detected mutant"
    human_judgment: false
    verification:
      - kind: unit
        ref: "cgb_attr_mutant_ignore_bank"
        status: pass
      - kind: unit
        ref: "cgb_attr_mutant_swap_flips"
        status: pass
      - kind: unit
        ref: "cgb_attr_mutant_reads_vbk"
        status: pass
      - kind: unit
        ref: "cgb_attr_mutant_obj_bank_ignored"
        status: pass
  - id: C7
    description: "No core source was edited and DMG output stays byte-identical"
    human_judgment: false
    verification:
      - kind: other
        ref: "bash tests/scripts/verify-dmg-baseline.sh"
        status: pass
status: complete
commits: 2
plan_head_before: 7568d6ea56f68e6f15819fa848784c5b66737ae5
plan_head_after: a64f6870bb2d4a38bf40ca6e574882cae01a1783
duration: 30 min
completed: 2026-10-12
---

# Phase 11 Plan 05: Priority truth table and mutants Summary

The independent 6144-row priority oracle now drives the real CGB-mode and compat pixel functions, a 64-row frame sample confirms it above the dispatch, and twelve per-input mutants each make a case fail.

## Accomplishments

- Per-row setup helper in `tests/test_cgb_colour_internal.c` sets VRAM, attributes, OAM, selected-object state, CRAM and the compat palette. Expected colours come from the row's expectation via distinct palette words, never from a core function.
- `cgb_priority_truth_table` prints `rows=6144`; `cgb_priority_opri_no_effect` reruns the full table after writing OPRI through `write8`.
- Eight priority/compat/OPRI mutants and four attribute mutants, each with a `_control` twin, all with exactly-once anchors.
- The implementation matched the oracle on the first run: no core bug was found and no oracle row was touched.

## Deviations from Plan

**1. [Interpretation] Tasks 2 and 3 share one commit.** Both only add registrations to the same CMake block and inventory, so they were committed together (a64f687); task 1 is 9734687. `commits: 2` is the measured count.

**2. [Interpretation] Truth-table print.** The case prints its own `pass rows=6144` line and the dispatcher also prints the generic `pass` line; both appear in the output.

**Total deviations:** 2, none affecting scope.

## Verification

- `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error`: 625/625 passed.
- `ctest -R '^(cgb_attr_|cgb_priority_|cgb_dmg_identity_)'`: 48/48 passed.
- `bash tests/scripts/verify-dmg-baseline.sh`: baseline status=pass. `git diff` on `src/core` is empty.
- `phase1-asan` is Linux-only (CMake refuses sanitizers on this macOS host); it runs in CI.

## Known Stubs

None.

## Threat Flags

None.

## Self-Check: PASSED

Modified files exist and commits 9734687 and a64f687 are ancestors of HEAD.
