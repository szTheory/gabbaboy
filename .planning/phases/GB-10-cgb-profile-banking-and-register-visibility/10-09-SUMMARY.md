---
phase: 10-cgb-profile-banking-and-register-visibility
plan: 09
subsystem: core-io
tags: [cgb, io-registers, visibility, deferred-latch, ie-gate, banking]
requires: [10-08]
provides: [io_visibility table, CGB FF4C-FF7F decode, bus_unsupported latch, IE gate, guest VBK/SVBK banking]
affects: [10-10]
key-files:
  created: [tests/test_cgb_visibility.c]
  modified: [src/core/gabbaboy.c, docs/model-gates.md, docs/cgb-profile.md, tests/test_cgb_tables.c, tests/CMakeLists.txt, tests/expected-tests.txt, .planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-CONTEXT.md]
requirements-completed: []
status: complete
commits: 1
plan_head_before: 11813e48272c5fe3fdd03d4146dce29378a6a2e5
plan_head_after: 47b4c27
actuals:
  tokens: 30000
  tasks: 3
  commits: 1
duration: 40 min
completed: 2026-10-12
coverage:
  - id: "10-09-vbk-decode"
    description: "VBK selects CGB VRAM banks while compatibility and DMG behavior stay bounded"
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build/phase15_1_18 -R '^cgb_visibility_vbk_tracer$' --output-on-failure --no-tests=error"
        status: pass
  - id: "10-09-svbk-decode"
    description: "SVBK selects CGB WRAM banks and is ignored in compatibility mode"
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build/phase15_1_18 -R '^cgb_visibility_svbk_select$' --output-on-failure --no-tests=error"
        status: pass
  - id: "10-09-unmapped-addresses"
    description: "Unused CGB addresses read as $FF while the DMG fail-closed control remains"
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build/phase15_1_18 -R '^cgb_visibility_unmapped_cgb$' --output-on-failure --no-tests=error"
        status: pass
  - id: "10-09-register-boundaries"
    description: "Register visibility boundaries are checked on both sides in each profile"
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build/phase15_1_18 -R '^cgb_visibility_boundaries$' --output-on-failure --no-tests=error"
        status: pass
  - id: "10-09-deferred-access"
    description: "Deferred reads stop atomically and deferred writes report their stop address"
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build/phase15_1_18 -R '^cgb_visibility_deferred_stop$' --output-on-failure --no-tests=error"
        status: pass
  - id: "10-09-ie-gate"
    description: "IE visibility is profile-specific and the interrupt mask retains its negative control"
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build/phase15_1_18 -R '^cgb_visibility_ie_gate$' --output-on-failure --no-tests=error"
        status: pass
  - id: "10-09-current-ir-interrupt-continuation"
    description: "Implemented FF56 IR writes and interrupt-entry stack pushes continue to the vector"
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build/phase15_1_18 -R '^cgb_ir_interrupt_continuation$' --output-on-failure --no-tests=error"
        status: pass
  - id: "10-09-postboot-and-baseline"
    description: "Post-boot documentation mirror and frozen DMG baseline remain consistent"
    human_judgment: false
    verification:
      - kind: unit
        ref: "ctest --test-dir build/phase15_1_18 -R '^cgb_tables_postboot$' --output-on-failure --no-tests=error"
        status: pass
      - kind: other
        ref: "bash tests/scripts/verify-dmg-baseline.sh --build-dir build/phase15_1_18"
        status: pass
---

# Phase 10 Plan 09: CGB register visibility Summary

A const `io_visibility[0x80]` table (DMG, CGB and COMPAT cells per FF00-FF7F address) now drives the CGB-profile FF4C-FF7F decode and the CGB part of `read_supported`; a generalised `bus_unsupported` latch with address stops DEFERRED writes visibly; IE bits 5-7 are stored on CGB only; guests select VRAM and WRAM banks through VBK and SVBK.

## Accomplishments

- `io_visibility[]` with kinds EXISTING, DMG_STOP, CONST_FF, KEY1, VBK, SVBK, STORE, DEFERRED_RW, DEFERRED_W. Read and write hooks sit behind one range test plus `model_is_cgb`; the DMG chain is untouched (FF4C-FF7F reads still stop, writes are silent).
- D-10 cells implemented per column: KEY0, KEY1, VBK (bank only in CGB mode), FF51-FF54, FF55 (write deferred to 13), FF56, BCPS/OCPS (read stored | $40), FF69/6B/6C (deferred 11, compat ignored), SVBK (read $F8 | raw), FF72-FF75, FF76/FF77 (deferred 14), unused addresses read $FF.
- `serial_unsupported` replaced by `bus_unsupported` + `bus_unsupported_address`; serial sets both, behaviour unchanged. Failed read pre-flight records the address. Test seam `gbb_test_last_unsupported_address` (non-header).
- The latch is also reported after an interrupt-entry push, so a deferred write inside entry is not carried past the vector.
- IE gate: CGB stores and reads all 8 bits; DMG keeps `& $1F` and reads bits 5-7 as 1. Recorded as owner veto item 6 in 10-CONTEXT.md.
- Ten new post-boot fields (KEY1, VRAM bank, SVBK, WRAM bank, BCPS, OCPS, FF72-FF75) in `post_boot[]`, mirrored in docs/cgb-profile.md; `test_cgb_tables.c` field names extended. Compat BCPS $C8 / OCPS $D0 are HW_TEST (boot_hwio-C); CGB-mode $C0 is POLICY "[VERIFY] no hardware oracle for CGB-mode index".
- model-gates: GATE-21/37/39 resolved to CGB_ONLY; GATE-69..73 added; scanner passes.

## Verification

- Targeted `^(cgb_visibility_|cgb_tables_|cgb_postboot_|bus_|serial_|banking_|model_gates)`: 48/48 pass. Full suite before the final test-constant fix: 468/469 (the one failure was my miscounted constant, below); targeted rerun after the fix is green.
- `verify-dmg-baseline.sh`: `baseline status=pass`. `verify-model-gates.py`: pass.
- Acceptance greps: `io_visibility[` 5 hits, `serial_unsupported` 0, header seam 0, doc oracle string present.

## Deviations from Plan

**1. [Rule 1 - Test arithmetic] unmapped_cgb address count.** I first asserted 44 addresses; the independent range arithmetic (1+7+1+1+9+1+1+17+3+1+8) is 50, because FF57-FF67 spans 17 addresses. Corrected the constant to 50; the code under test was not changed.

**2. [Rule 2 - Missing critical] Latch checked after interrupt entry.** The plan only reports the latch after instruction retire. An entry push into a deferred register (SP = $FF57) would otherwise leave the latch set until the next instruction. Added a check after entry; covered by `deferred_latch_interrupt`.

**3. Process: one commit for three tasks.** The tracer slice, the full D-10 table and the latch were written together in one table-driven change (the tracer row is a subset of the table, and the test file is one TU); splitting would require artificial partial staging of the same hunks. One commit (47b4c27) holds all three.

**4. Scope note.** `tests/test_cgb_tables.c` and 10-CONTEXT.md (veto item 6) were touched; neither was in the plan's file list but both are required by it (field names for the two-way doc check; the veto record).

## Known Stubs

None. DEFERRED cells are intentional, stop visibly, and are owned by phases 11, 13 and 14.

## Threat Flags

None. T-10-14 (bank indices masked `& 7` / `& 1`, CGB mode only), T-10-15 (deferred reads/writes stop with address, latch survives interrupts) and T-10-16 (DMG chain unchanged, baseline pass) are mitigated.

## Self-Check: PASSED

- tests/test_cgb_visibility.c exists; commit 47b4c27 is an ancestor of HEAD; acceptance greps re-run.

## Fresh Coverage Verification (15.1-18)

At source `65e69ca2dc6f51515ebba002361b0966e3b45a17`, the fresh build passed the seven currently registered Phase 10-09 behavior and table checks plus `cgb_ir_interrupt_continuation` (8 current cases total). The original `cgb_visibility_deferred_latch_interrupt` selector is absent now: it existed at immutable Phase 10 commit `47b4c27` and was replaced in `24f07c7` after FF56 became implemented. The current replacement passes and checks that the implemented IR write and interrupt-entry push continue to the vector without an unsupported-bus stop. The old deferred-FF56 latch semantics remain historical evidence only; this plan does not claim a fresh pass for them. The frozen DMG baseline also passes with zero changed rows.
