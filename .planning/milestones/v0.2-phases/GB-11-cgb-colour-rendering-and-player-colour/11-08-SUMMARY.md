---
phase: 11-cgb-colour-rendering-and-player-colour
plan: 08
subsystem: cgb-colour-fixtures
tags: [rgb555, fixture, rgbds, attributes, lcdc0, cram, compat-palette, lcd-off, d-23, d-11, d-17, d-02, mutant]
requires:
  - phase: 11-cgb-colour-rendering-and-player-colour
    provides: "11-07 fixture pipeline, manifest recipe shape, RGB555 digest helpers; 11-02 palette port and mutant anchor; 11-06 public RGB555 and compat palette API"
provides:
  - "fixtures/cgb-colour/ attr.asm, cram.asm, compat.asm, lcdoff.asm and five ROMs (colour-attr, colour-lcdc0, colour-cram, colour-compat, colour-lcdoff) as manifest rows with recipes and protocols"
  - "cgb_colour_attr, cgb_colour_lcdc0, cgb_colour_guest_cram, palette_compat_mapping, cgb_colour_lcd_off public CTests and cgb_rgb_store_lcdoff_fixture internal CTest"
  - "cgb_colour_guest_cram_mutant_blocked_no_increment with control"
affects: [11-09]
requirements-completed: []
actuals:
  tokens: 42000
  tasks: 2
  commits: 2
coverage:
  - id: C1
    description: "Every CGB BG attribute rule (palette, tile bank, X and Y flip, unused bit 4, BG priority) and OBJ bank and palette selection is shown on a guest-built frame through the public RGB555 call, with literal per-cell colours checked before the digest pin"
    human_judgment: false
    verification:
      - kind: integration
        ref: "cgb_colour_attr"
        status: pass
  - id: C2
    description: "With LCDC bit 0 clear the BG is still drawn and the BG-priority cell shows the object, on a guest-built frame"
    human_judgment: false
    verification:
      - kind: integration
        ref: "cgb_colour_lcdc0"
        status: pass
  - id: C3
    description: "A guest exercises palette RAM auto-increment, wrap, read-back, read without increment, the mode-3 blocked write that still increments, the blocked read and the LCD-off write, reporting through WRAM markers; a core whose blocked write does not increment fails the guest while its control still passes"
    human_judgment: false
    verification:
      - kind: integration
        ref: "cgb_colour_guest_cram"
        status: pass
      - kind: integration
        ref: "cgb_colour_guest_cram_mutant_blocked_no_increment"
        status: pass
      - kind: integration
        ref: "cgb_colour_guest_cram_mutant_blocked_no_increment_control"
        status: pass
  - id: C4
    description: "In compatibility mode BGP, OBP0 and OBP1 select shades that map through the default palette set of their own region, and after gbb_set_compat_palette the next completed frame uses the override for BG, OBJ0 and OBJ1 separately"
    human_judgment: false
    verification:
      - kind: integration
        ref: "palette_compat_mapping"
        status: pass
  - id: C5
    description: "While the guest keeps the LCD off the completed frame is retained and the generation is frozen, and the internal working RGB buffer is all 0x7FFF"
    human_judgment: false
    verification:
      - kind: integration
        ref: "cgb_colour_lcd_off"
        status: pass
      - kind: integration
        ref: "cgb_rgb_store_lcdoff_fixture"
        status: pass
  - id: C6
    description: "The five new committed ROMs match the sizes and SHA-256 digests in their manifest rows and rebuild byte for byte from their recipes with RGBDS 1.0.1 (six ROMs in total)"
    human_judgment: false
    verification:
      - kind: integration
        ref: "cgb_colour_fixture_digest"
        status: pass
      - kind: other
        ref: "bash tests/scripts/reproduce-cgb-colour.sh"
        status: pass
  - id: C7
    description: "DMG output stays byte-identical"
    human_judgment: false
    verification:
      - kind: other
        ref: "bash tests/scripts/verify-dmg-baseline.sh"
        status: pass
status: complete
commits: 2
plan_head_before: 96f9199ff895ccc017b2487978fefb30c69c6976
plan_head_after: 9ac8dbf959bde2a9085773f8c23b3b7ff885418f
duration: 45 min
completed: 2026-10-12
---

# Phase 11 Plan 08: Remaining original CGB colour fixtures Summary

Five original guest ROMs (attribute grid with and without LCDC.0, palette-RAM port cells reported through WRAM, DMG-mode compat bars with a host override, and LCD off) are rebuilt byte for byte from manifest recipes and checked through the public RGB555 call against literal expected colours before each digest is compared.

## Accomplishments

- `attr.asm` draws ten 16x16 cells, each 2x2 copies of an 8x8 tile of four 4x4 quadrants: BG palette 3, tile bank 1, X flip, Y flip, attribute bit 4 (equal to the attr-0 reference cell), BG-over-object priority bit, OBJ bank 1 with palette 5, and OBJ palette 2. Palette 1 and 2 and the unused OBJ palettes hold decoys so a wrong select cannot pass. `-D LCDC0_CLEAR` gives `colour-lcdc0.gb` (LCDC = $92): the BG is still drawn and the priority cell flips from the BG colour to the object colour.
- `cram.asm` runs seven D-11 cells and writes `$01`/`$00` per cell at `$C001..$C007` and the verdict at `$C000` ($A5/$EE). The driver reads them with `gbb_peek_ram`.
- `compat.asm` (no CGB flag) shows four BG bars and three OBJ0 plus three OBJ1 objects under BGP $E4, OBP0 $E4, OBP1 $1B. `palette_compat_mapping` checks the default palette per region, then a twelve-value override on the next completed frame, and that every pixel changed.
- `lcdoff.asm` shows a solid colour for four frames, switches the LCD off in VBlank and sets `$C000`. `cgb_colour_lcd_off` checks the retained frame and frozen generation over five more frames; `cgb_rgb_store_lcdoff_fixture` checks `rgb_working` is all 0x7FFF.
- All five frame digests were recomputed independently with `python3 -I` from the expected-colour tables (not from core output) and matched the observed values before being pinned.
- Mutant `cgb_colour_guest_cram_mutant_blocked_no_increment` reuses the plan 11-02 anchor; it exits 1 at `cell 5 byte C005 is 00` and its control (`cgb_colour_attr` on the mutated core) passes.
- `common.inc` gained OCPS/OCPD/VBK/BGP/OBP0/OBP1/OAM register names and two small macros (`CopyBytes`, `LoadCram`); `colour-hblank.gb` is byte-identical afterwards.

## Deviations from Plan

**1. [Interpretation] CRAM guest ends in a spin, not HALT.** The plan says the guest "then halts". `gbb_run` returns at every HALT (plan 11-07 deviation 2), so a final `jr` spin is used and the host runs 10 frames before reading markers. No core change. Files: `fixtures/cgb-colour/cram.asm`.

**2. [Interpretation] Reference cell added.** The plan's eight cells became ten (cell 8 = attr-0 reference for the bit-4 comparison, cell 9 blank), so "bit 4 equals the bit-4-clear reference" is a pixel-for-pixel check rather than a table equality only. Files: `attr.asm`, `tests/test_cgb_colour.c`.

**3. [Rule 3 - Blocking] Shared include extended.** The new sources need extra register names and copy macros, so `common.inc` was edited (its digest in `source_sha256` updated; no ROM byte changes in the existing fixture, confirmed by the reproduction script). Commit 2e75c50.

**4. [Toolchain] Pinned RGBDS obtained as the precedent prescribes.** The RGBDS v1.0.1 macOS archive was downloaded into a scratch directory outside the repo, its SHA-256 matched the recorded pin, and `rgbasm --version` printed `rgbasm v1.0.1` before any ROM was built. The Linux byte-identity proof runs in the fixture-repro CI job after push.

**Total deviations:** 4, none affecting scope or locked decisions.

## Verification

- `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error`: 657/657 passed.
- `bash tests/scripts/reproduce-cgb-colour.sh` with pinned tools: `result=byte-identical roms=6`.
- `bash tests/scripts/verify-dmg-baseline.sh`: `baseline status=pass`.
- Acceptance: manifest lists exactly the six expected ROMs; inventory counts 2 (task 1) and 6 (task 2) as required.
- `phase1-asan` is Linux-only; it runs in CI on the pushed branch.

## Known Stubs

None.

## Threat Flags

None. T-11-36 and T-11-37 mitigations are in place: rows carry sha256 and recipe, `cgb_colour_fixture_digest` and the reproduce script (roms=6) reject any byte change, expected values are typed from the fixture design and independently recomputed, the CRAM guest mutant fails, and the LCD-off internal case checks `rgb_working` separately.

## Self-Check: PASSED

Commits 2e75c50 and 9ac8dbf are ancestors of HEAD; attr.asm, cram.asm, compat.asm, lcdoff.asm and the five new .gb ROMs exist under fixtures/cgb-colour/.
