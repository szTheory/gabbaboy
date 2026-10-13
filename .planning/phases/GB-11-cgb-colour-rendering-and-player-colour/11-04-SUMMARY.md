---
phase: 11-cgb-colour-rendering-and-player-colour
plan: 04
subsystem: cgb-compat-renderer
tags: [rgb555, compat-palette, d-17, d-18, d-39, d-08, d-25, gate-82]
requires:
  - phase: 11-cgb-colour-rendering-and-player-colour
    provides: "11-03 RGB stores and per-dot dispatch with the compat branch on the shade statement"
provides:
  - "compat_default_rgb555 ramp and gbb_instance.compat_rgb555, seeded in gbb_create only"
  - "ppu_compat_resolve and ppu_pixel_compat with DMG semantics"
  - "Compat dispatch branch writing rgb_working only (GATE-82)"
affects: [11-05, 11-06]
requirements-completed: []
actuals:
  tokens: 40000
  tasks: 2
  commits: 1
coverage:
  - id: C1
    description: "The default compat palette is the documented ramp for BG, OBJ0 and OBJ1 and survives reset and ROM load, including a host change"
    human_judgment: false
    verification:
      - kind: unit
        ref: "cgb_compat_internal_default"
        status: pass
  - id: C2
    description: "A compat BG pixel is resolved per dot through the compat palette and compat mode never writes the shade store"
    human_judgment: false
    verification:
      - kind: unit
        ref: "cgb_compat_internal_bg"
        status: pass
      - kind: unit
        ref: "cgb_rgb_store_shade_untouched"
        status: pass
  - id: C3
    description: "Objects pick set 1 or 2 by OAM bit 4 through OBP0 or OBP1 and OAM bits 0-3 have no effect"
    human_judgment: false
    verification:
      - kind: unit
        ref: "cgb_compat_internal_obj_sets"
        status: pass
  - id: C4
    description: "CGB attributes in vram bank 1, VBK and OPRI do not change the compat frame"
    human_judgment: false
    verification:
      - kind: unit
        ref: "cgb_compat_internal_attr_ignored"
        status: pass
  - id: C5
    description: "LCDC bit 0 clear renders BG index 0 through BGP while objects still draw, and objects order by smaller X then lower OAM index"
    human_judgment: false
    verification:
      - kind: unit
        ref: "cgb_compat_internal_lcdc0"
        status: pass
      - kind: unit
        ref: "cgb_compat_internal_x_order"
        status: pass
  - id: C6
    description: "A mid-frame compat palette change affects later pixels and never alters the completed frame until the next completion"
    human_judgment: false
    verification:
      - kind: unit
        ref: "cgb_compat_internal_live_config"
        status: pass
  - id: C7
    description: "DMG output is byte-identical and every new function and branch carries a MODEL tag with a docs row"
    human_judgment: false
    verification:
      - kind: unit
        ref: "cgb_dmg_identity_shade_pin"
        status: pass
      - kind: other
        ref: "bash tests/scripts/verify-dmg-baseline.sh"
        status: pass
      - kind: unit
        ref: "model_gates"
        status: pass
status: complete
commits: 1
plan_head_before: 11be45e877933d673157bce6fd18889d5305b081
plan_head_after: a537528f70f252823081583c98e5add05fb26faf
duration: 25 min
completed: 2026-10-12
---

# Phase 11 Plan 04: Compat renderer Summary

DMG software on the CGB profile now renders per dot through an instance compat palette (documented default ramp, DMG semantics, no vram[1] read); the DMG shade path is byte-identical.

## Accomplishments

- `compat_default_rgb555` (ramp `$639F, $4275, $254B, $0421`, rule and G4 provenance in its comment) copied into `compat_rgb555` in `gbb_create`, never in `reset_state`.
- `ppu_compat_resolve` masks set (`% 3`) and shade (`& 3`); `ppu_pixel_compat` mirrors `ppu_pixel_shade` and reuses `ppu_object_color` for X order.
- Compat dispatch branch writes `rgb_working` only; new gate GATE-82 (CGB_ONLY).
- Seven `cgb_compat_internal_*` cases plus the compat extension of `cgb_rgb_store_shade_untouched`.

## Deviations from Plan

**1. [Interpretation] One commit for both tasks.** The tracer and the five task-2 cases share the same code and test helpers, as in plan 11-03; the work is a single commit (a537528). Both tasks' verify commands pass at it. `commits: 1` is the measured count.

**2. [Interpretation] Acceptance grep text.** The plan greps `rgb_working[at] = ...`; the dispatch variable is `pixel_at`, so the line reads `m->rgb_working[pixel_at] = ppu_pixel_compat(m, fetched_slot);` (exactly one occurrence).

**3. [Rule 3 - Blocking] Compat branch is `else if (model_is_cgb(m))`.** The model-gates verifier requires the guard text within 12 lines of a `CGB_ONLY` tag, so the final branch names `model_is_cgb` explicitly. It is unreachable for the DMG profile (first branch) so behaviour is unchanged.

**Total deviations:** 3, none affecting scope.

## Verification

- `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error`: 598/598 passed.
- `bash tests/scripts/verify-dmg-baseline.sh`: baseline status=pass. `cgb_dmg_identity_shade_pin` passes.
- `phase1-asan` is Linux-only (CMake refuses sanitizers on this macOS host); it runs in CI.

## Known Stubs

None. The compat palette has no public API yet; that lands in plan 11-06.

## Threat Flags

None.

## Self-Check: PASSED

Modified files exist and commit a537528 is an ancestor of HEAD.
