---
phase: 10-cgb-profile-banking-and-register-visibility
plan: 08
subsystem: core-memory
tags: [cgb, vram, wram, banking, dmg-identity]
requires: [10-07]
provides: [banked vram/wram storage, wram_byte helper, gbb_test_bank_state seam]
affects: [10-09]
key-files:
  created: [tests/test_banking_internal.c]
  modified: [src/core/gabbaboy.c, tests/test_rtc3test.c, tests/CMakeLists.txt, tests/expected-tests.txt]
requirements-completed: []
status: complete
commits: 1
plan_head_before: eec0283f020c9c3181d92437863280be35aadd0b
plan_head_after: a5544731e1a804f1d11c5a1078a4dd90b3a423dc
actuals:
  tokens: 9000
  tasks: 2
  commits: 1
duration: 15 min
completed: 2026-10-12
coverage:
  - deliverable: "DMG profile matches a flat 8 KiB WRAM + VRAM model over 200000 seeded steps; bank pins stay 0/1"
    verification:
      - {kind: ctest, ref: "banking_dmg_flat_reference", status: pass}
    human_judgment: false
  - deliverable: "Negative control: CGB with scrambled banks diverges from the flat model"
    verification:
      - {kind: ctest, ref: "banking_cgb_diverges_from_flat", status: pass}
    human_judgment: false
  - deliverable: "Bank pins survive reset and reload on DMG"
    verification:
      - {kind: ctest, ref: "banking_dmg_bank_pins_after_reset", status: pass}
    human_judgment: false
  - deliverable: "Tracer correctness digest unchanged (4c7a57ff3d50d228) and DMG baseline pass"
    verification:
      - {kind: ctest, ref: "banking_tracer_digest_unchanged", status: pass}
      - {kind: command, ref: "bash tests/scripts/verify-dmg-baseline.sh", status: pass}
    human_judgment: false
---

# Phase 10 Plan 08: Banked VRAM and WRAM storage Summary

VRAM is now `vram[2][8192]` and WRAM `wram[8][4096]` with `vram_bank`/`wram_bank`/`svbk`, reached through one `wram_byte` helper (C000-CFFF and echo -> bank 0, D000-DFFF and echo -> `wram[wram_bank]`) used by read8, write8, `gbb_peek_ram` and `dma_source_read`; the PPU reads `vram[0]` with a per-bank map bound. DMG is byte-identical: reset pins `vram_bank=0`, `wram_bank=1`, and no VBK/SVBK decode exists yet (Plan 10-09).

## Accomplishments

- Banked arrays, named size constants, reset pins on every profile and mode.
- CPU VRAM access uses `vram[vram_bank]`; `cpu_vram_access_allowed` is still the single mode-3 gate.
- `gbb_test_bank_state` is a non-header extern (0 hits in `include/gabbaboy/gabbaboy.h`).
- `test_banking_internal` (single TU, no core link): flat-reference metamorphic test, CGB divergence control, reset/reload pin test; plus `banking_tracer_digest_unchanged`.

## Verification

- Full suite: 462/462 pass. Targeted `^(banking_|bus_|dma_|ppu_|rtc3test|model_gates|cgb_)`: 86/86 pass.
- `verify-dmg-baseline.sh`: `baseline status=pass`. Tracer digest `4c7a57ff3d50d228`.
- Acceptance greps: `sizeof(m->(vram|wram))` = 2 (reset memsets only); `wram[GBB_WRAM_BANKS][GBB_WRAM_BANK_SIZE]` = 1; header seam hits = 0; expected-tests entries present (1 and 3).

## Deviations from Plan

None in behaviour. Process note: Tasks 1 and 2 share one commit (a554473) because the test file and its CTest wiring were authored together and the divergence/digest cases live in the same new file; splitting would have required staging an artificial partial file. The model-gates scanner and docs/model-gates.md needed no row change (new helpers use the existing GATE-00 row; the scanner passes).

## Known Stubs

None.

## Threat Flags

None. T-10-12/T-10-13 mitigated: banks set only by reset in this plan, arrays sized by constants, per-bank map bound, no whole-array sizeof outside reset memsets.

## Self-Check: PASSED

- tests/test_banking_internal.c exists; commit a554473 is an ancestor of HEAD; all acceptance criteria re-run and pass.
