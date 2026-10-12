# rtc3test eligibility

## Evidence class

Hardware-derived, author-attested test ROM (rtc3test, aaaaaa123456789,
Unlicense). The author attests the expected MBC3 real-time-clock behaviour
against real hardware; this repository has not independently reproduced that on
hardware.

## Oracle

Screen only, menu-driven. Results are drawn as background-map tiles at $9C00: a
pass glyph is tile index `glyph | 0x40`, a fail glyph is `glyph | 0x80`. Pixel
shades are unreliable on DMG, so the oracle reads the BG map, not shades.
Suites: Basic, Range, Sub-second. The expected millisecond figures come from the
verbatim `tests.md`.

## Observation (gate G7, low risk)

The ROM bundles its own font. Glyph tile indices, not rendered pixels, are what
the oracle reads, so the font affects neither verdicts nor the digest check. This
is recorded for gate G7 and carries low risk.

## Expected failures

None. All three suites (Basic, Range, Sub-second) must pass.

## Distribution

Repository test fixture only. Not installed and not packaged.
