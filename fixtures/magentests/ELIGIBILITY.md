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

`ppu_disabled_state` reads STAT mode 0 right after the guest turns the LCD off at vblank. A
second case clears `$143` (recomputing `$14D`) so the same ROM runs in compatibility mode, where
the guest's CRAM writes are ignored and the frame must be one uniform default BG value.

None of these ROMs is CGB-E hardware evidence. `key0_lock_after_boot` and `hblank_vram_dma` are
not vendored.

AGE has no CGB colour, attribute or priority ROM at 1f5bc10e (only m3-bg-lcdc and m3-bg-scx,
which are expected-unsupported for mode-3 pixel timing, D-09). Roadmap success criterion 1 is
met by these MagenTests ROMs, the original fixtures/cgb-colour ROMs and the exhaustive priority
truth table, not by AGE. (D-20; the AGE expected-unsupported records are plan 11-11.)

## Distribution

Repository test fixtures only. Not installed and not packaged.
