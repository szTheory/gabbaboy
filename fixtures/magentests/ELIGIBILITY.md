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

## Distribution

Repository test fixtures only. Not installed and not packaged.
