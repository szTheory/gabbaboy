---
phase: 11-cgb-colour-rendering-and-player-colour
plan: 03
subsystem: cgb-mode-pixel-path
tags: [rgb555, cgb-attributes, obj-order, priority, d-01, d-02, d-05, d-06, d-07, d-08, d-09, d-25, mutant-controls]
requires:
  - phase: 11-cgb-colour-rendering-and-player-colour
    provides: "11-02 palette RAM, OPRI and white post-boot CRAM"
provides:
  - "rgb_working and rgb_completed RGB555 frame stores with the D-02 lifecycle"
  - "Per-dot dispatch: DMG profile shade path, CGB mode RGB path, compat branch left on the shade path"
  - "CGB-mode BG and window attribute fetch, OBJ bank and palette, OAM-index order, pure ppu_compose_cgb"
  - "GATE-43/45/46 resolved, GATE-28 split, GATE-78 to GATE-81 added"
affects: [11-04, 11-05, 11-06]
requirements-completed: [CGB-04]
actuals:
  tokens: 70000
  tasks: 2
  commits: 1
coverage:
  - id: C1
    description: "A CGB-mode BG pixel is resolved from live CRAM per dot into the RGB store, with bit 15 of the guest word masked"
    human_judgment: false
    verification:
      - kind: unit
        ref: "cgb_rgb_store_bg_palette"
        status: pass
      - kind: unit
        ref: "cgb_rgb_store_bit15_masked"
        status: pass
  - id: C2
    description: "The shade buffers stay zero on the CGB profile and the RGB buffers stay zero on the DMG profile"
    human_judgment: false
    verification:
      - kind: unit
        ref: "cgb_rgb_store_shade_untouched"
        status: pass
      - kind: unit
        ref: "cgb_rgb_store_dmg_untouched"
        status: pass
  - id: C3
    description: "LCD off fills the RGB working frame with white and keeps the completed frame, and reset zero-fills both RGB buffers"
    human_judgment: false
    verification:
      - kind: unit
        ref: "cgb_rgb_store_lcd_off"
        status: pass
      - kind: unit
        ref: "cgb_rgb_store_reset"
        status: pass
  - id: C4
    description: "BG attribute bits select palette, tile bank, X flip and Y flip, bit 4 is ignored and rendering never reads VBK or OPRI"
    human_judgment: false
    verification:
      - kind: unit
        ref: "cgb_attr_palette"
        status: pass
      - kind: unit
        ref: "cgb_attr_bank"
        status: pass
      - kind: unit
        ref: "cgb_attr_xflip"
        status: pass
      - kind: unit
        ref: "cgb_attr_yflip"
        status: pass
      - kind: unit
        ref: "cgb_attr_bit4_ignored"
        status: pass
      - kind: unit
        ref: "cgb_attr_vbk_not_read"
        status: pass
  - id: C5
    description: "LCDC bit 0 only removes priority in CGB mode, BG and window are still drawn, and the window is gated by LCDC bit 5 alone with the same attribute fetch"
    human_judgment: false
    verification:
      - kind: unit
        ref: "cgb_attr_bg_priority"
        status: pass
      - kind: unit
        ref: "cgb_attr_lcdc0_bg_drawn"
        status: pass
      - kind: unit
        ref: "cgb_attr_window_same_fetch"
        status: pass
      - kind: unit
        ref: "cgb_attr_window_lcdc0_clear"
        status: pass
  - id: C6
    description: "Objects take the tile bank from OAM bit 3 and palette from bits 0-2 and order by OAM index, with a transparent winner pixel letting the next object show"
    human_judgment: false
    verification:
      - kind: unit
        ref: "cgb_attr_obj_bank_palette"
        status: pass
      - kind: unit
        ref: "cgb_attr_obj_oam_order"
        status: pass
  - id: C7
    description: "A colour path that also writes the shade store is caught while a control case still passes, and the DMG shade output is unchanged"
    human_judgment: false
    verification:
      - kind: unit
        ref: "cgb_dmg_identity_mutant_colour_writes_shade"
        status: pass
      - kind: unit
        ref: "cgb_dmg_identity_mutant_colour_writes_shade_control"
        status: pass
      - kind: unit
        ref: "cgb_dmg_identity_shade_pin"
        status: pass
      - kind: other
        ref: "bash tests/scripts/verify-dmg-baseline.sh"
        status: pass
  - id: C8
    description: "Every new function and model-differing branch carries a MODEL tag with a docs row"
    human_judgment: false
    verification:
      - kind: unit
        ref: "model_gates"
        status: pass
status: complete
commits: 1
plan_head_before: 55d2faeaba5491c573f27942b0b87df602f43ba2
plan_head_after: 516e39abd0272c17d99e1c105ddf3f74df06bdf1
duration: 40 min
completed: 2026-10-12
---

# Phase 11 Plan 03: CGB-mode pixel path Summary

CGB mode now renders RGB555 per dot against live CRAM into a separate `rgb_working`/`rgb_completed` store, with full BG/window/OBJ attribute handling and a pure priority composer; the DMG shade path is byte-identical.

## Accomplishments

- Core: `rgb_working`/`rgb_completed` on the instance (zeroed on reset, white-filled on LCD off, copied on frame completion beside the shade copy). Per-dot dispatch is DMG profile, then CGB mode, then the compat branch which still uses the shade statement (plan 11-04 routes it).
- New siblings: `ppu_vram_read`, `cram_colour` (masks bit 15), `ppu_cgb_tile_color`, `ppu_cgb_window_visible_at` (LCDC.5 alone), `ppu_cgb_background`, `ppu_cgb_object` (OAM-index order, OAM bit 3 bank), `ppu_compose_cgb`, `ppu_pixel_cgb`. None reads `vram_bank` or `opri`.
- `ppu_window_should_start` enables on LCDC.5 alone in CGB mode (GATE-81, mode-3 timing not claimed).
- Gates: GATE-43/45/46 now BOTH with a DMG-semantics basis, GATE-28 re-tagged `research:14`, GATE-78 to GATE-81 CGB_ONLY.
- Tests: 6 `cgb_rgb_store_*`, 12 `cgb_attr_*`, and the `colour_writes_shade` mutant with control.

## Deviations from Plan

**1. [Interpretation] One commit for both tasks.** The tracer (Task 1) and the full CGB mode (Task 2) were written in one pass because `ppu_pixel_cgb` and the shared test scene helpers are the same code; the work is a single commit (516e39a) rather than two. All acceptance greps and both tasks' verify commands pass at that commit.

**2. [Interpretation] DMG-untouched case uses the demo fixture through the CTest argument.** `cgb_rgb_store_dmg_untouched` reads `fixtures/visible-demo/demo.gb` via the fixtures root argument, as the plan names the demo ROM.

**3. [Interpretation] Gate classes for GATE-43/45/46.** They are class BOTH with a `basis=` stating DMG semantics (no `model_is_dmg` guard appears in those bodies, so a DMG_ONLY class would fail R4).

**Total deviations:** 3 interpretations, no bugs. **Impact:** none on scope.

## Verification

- `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error`: 591/591 passed.
- `bash tests/scripts/verify-dmg-baseline.sh`: baseline status=pass. `cgb_dmg_identity_shade_pin` passes.
- `python3 -I tests/scripts/verify-model-gates.py`: pass, functions=158 gates=82.
- `phase1-asan` is Linux-only (CMake refuses sanitizers on this macOS host); it runs in CI. All indices are masked (bank & 1, palette & 7, colour & 3) and `ppu_vram_read` bounds the address.

## Known Stubs

None. The compat branch intentionally keeps the existing shade statement until plan 11-04; nothing is public until plan 11-06.

## Threat Flags

None.

## Self-Check: PASSED

Modified files exist and commit 516e39a is an ancestor of HEAD.
