# MagenTests eligibility

## Evidence class

Hardware-derived, author-attested test ROMs (MagenTests, alloncm, MIT). The
author attests the expected behaviour against real hardware; this repository
has not independently reproduced that on hardware.

## Oracle

Screen only. The ROM paints a uniform background: shade 0 means pass, shade 3
means fail. Frames 1 to 3 are white regardless of outcome, so the oracle must
read the screen after the test has finished, not early frames. A paired negative
control (Plan 09-07) uses RAM code $03 variants that must show shade 3, proving
the oracle can fail.

## Scope

- Subject: out-of-bounds external RAM access for MBC1 ($02), MBC3 ($12) and
  MBC5 ($1A) cartridges.
- All three cartridge types are volatile (no battery), so no battery or save
  path is exercised.
- The ROMs are CGB-flagged; CGB register writes are ignored by the DMG profile.
- Applies to the accepted mapper behaviour only; it says nothing about RTC.

## CGB PPU ROMs (Phase 11)

Three further MagenTests 0.5.0 ROMs exercise the CGB PPU. They run on `GBB_PROFILE_CGB_CPU_E`
through `gbb_copy_frame_rgb555` for a fixed 20 frames; the last two completed frames must be
byte-identical and come from distinct LCD-on completions. A literal RGB555 structural predicate
typed from the pinned upstream source must hold before any frame digest is accepted. The
`mbc_oob_sram` ROMs above stay on the DMG profile and are unchanged.

| ROM | Applicability label | Predicate |
|---|---|---|
| `ppu_disabled_state.gbc` | author-attested | all 23040 pixels `0x03E0`; the failure colour is red `0x001F` |
| `bg_oam_priority.gbc` | CGB hardware photo, revision E unattested | eight 8x8 cells at x 32-39, y 16k to 16k+7: cells 0, 2, 3 rows 0-3 `0x03E0` and rows 4-7 `0x7C00`; cells 1, 4, 5, 6, 7 all `0x03E0`; no `0x001F`; all else `0x7FFF` |
| `oam_internal_priority.gbc` | SameBoy differential, not hardware | 84 opaque pixels inside two 12x6 boxes (see the mask derivation), green `0x03E0` or red `0x001F`; all else `0x7FFF` |

## HBlank VRAM DMA ROM (Phase 13)

`hblank_vram_dma.gbc` is admitted from MagenTests 0.5.0 at the pinned source
commit. Its license and complete build/include closure are recorded in
`SOURCES.md`, `manifest.json`, and `LICENSE.txt`. It is a bootless
`GBB_PROFILE_CGB_CPU_E` selected-model case with **SameBoy-assisted
differential** evidence; the author screenshot and source are not physical
CGB-E qualification.

The source-derived guest contract is:

- Tile 0 is colour index 1 and palette colour 1 is red `0x001F`, the initial
  failure display. Tile 1 is colour index 2 and palette colour 2 is green
  `0x03E0`. Tile 2 is colour index 3 and palette colour 3 is blue `0x7C00`.
- `NewTileMap` contains `$400` bytes of tile index 1. It links at ROM `$022C`,
  and FF52 ignores the low nibble, so the first aligned HBlank-DMA source is
  `$0220`. The first 12 transferred bytes are `$FF` from the preceding tile-2
  data; the remaining 1012 bytes are tile index 1. The guest sets SCX to 96
  pixels (12 tile columns) and SCY to 112 pixels (14 rows), so those first 12
  entries are outside the display. The source-derived map must have exactly
  that byte sequence, and visible rows 14-31 / columns 12-31 must be tile 1.
  The first transfer targets `$9800`, uses 64 blocks, and the guest polls FF55
  until the busy bit clears; the visible screen must be uniformly green.
- The guest then arms a second 64-block transfer from `NewBadTileMap`, whose
  bytes are tile index 2, and enters a HALT loop. That transfer must remain
  pending: the guest is halted, FF55 retains the active/busy count, and the map
  stays tile 1. The wrong-HALT control must turn the map blue; wrong-bank and
  no-transfer controls must fail their named map/transfer assertions.
- The structural display predicate is all 23040 RGB555 pixels equal to
  `0x03E0`, with two distinct increasing LCD-on frame generations and equal
  final frames. Guest data, FF55 status/read evidence, HALT state, and the
  source-derived green predicate gate any digest comparison.

These expectations establish software-model behavior only. They make no
physical console timing claim, and there is no mandatory external emulator or
hardware setup.

`ppu_disabled_state` reads STAT mode 0 right after the guest turns the LCD off at vblank. A
second case clears `$143` (recomputing `$14D`) so the same ROM runs in compatibility mode, where
the guest's CRAM writes are ignored. The guest paints colour index 1 and its verdict is BGP (0x00
pass, 0x0C fail), so the frame must be the default BG shade 0 everywhere; the failure maps to
shade 3. The `magentests_lcd_off_no_mode0_compat` mutant proves the case fails when STAT mode 0 is skipped.

`bg_oam_priority` outcome: it passed its predicate on the core without any expected-unsupported
record (the per-band LCDC writes from STAT/LYC interrupts land before x = 32), so its digest is
pinned and the LCDC.0 mutant applies.

### oam_internal_priority mask derivation

Sources at MagenTests 3f9c090f: `src/oam_internal_priority/graphics_data.asm` (TileData: tile 0 all
colour 1; tile 1 rows 1-6 hold colour 1 in columns `7-r` to 6; tile 2 the same with colour 2; rows 0
and 7 transparent; OAMData: `db 40,46,2,0` / `db 40,40,1,0` / `db 60,40,1,0` / `db 60,46,2,0`) and
`src/oam_internal_priority/main.asm` (BG palette 1 colour 1 white, object palette 0 colour 1 green,
colour 2 red, LCDC `ON|BG8000|OBJON|BGON`). `src/common.asm` gives `GREEN = $03E0`, `RED = $001F`.

- Object screen position is (X-8, Y-16): Y 40 gives y 24-31, Y 60 gives y 44-51; X 40 gives x
  32-39, X 46 gives x 38-45. Opaque rows are tile rows 1-6, so y 25-30 and 45-50.
- Row r (1-6) holds r opaque pixels in tile columns `7-r`..6. Green (tile 1, X 40): x `39-r`..38.
  Red (tile 2, X 46): x `45-r`..44. The green object covers at most x 38 and the red object starts
  at x 39, so the two never share an opaque pixel.
- Per box that is 21 green plus 21 red pixels, 42; two boxes give 84 opaque pixels, equal to the
  RESEARCH simulation, so there is no disagreement to record. The other 60 box pixels and every
  pixel outside the boxes are the white BG `0x7FFF`.
- Box rows (x 33-44, `G` green, `R` red, `.` white): `.....G.....R`, `....GG....RR`,
  `...GGG...RRR`, `..GGGG..RRRR`, `.GGGGG.RRRRR`, `GGGGGGRRRRRR`.

None of these ROMs is CGB-E hardware evidence. `key0_lock_after_boot` remains
source-only and is not vendored. The existing `hblank_vram_dma.gbc` output is
admitted as the seventh fixture in `manifest.json` and remains a selected
native CGB case.

AGE has no CGB colour, attribute or priority ROM at 1f5bc10e (only m3-bg-lcdc and m3-bg-scx,
which are expected-unsupported for mode-3 pixel timing, D-09). Roadmap success criterion 1 is
met by these MagenTests ROMs, the original fixtures/cgb-colour ROMs and the exhaustive priority
truth table, not by AGE. (D-20; the AGE expected-unsupported records are plan 11-11.)

## Distribution

Repository test fixtures only. Not installed and not packaged.
