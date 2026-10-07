# DMG video evidence ledger

This ledger separates software-authored composition checks from source-derived timing expectations. It does not claim physical DMG observation.

## Source snapshot and applicability

The reference snapshot is the `gbdev/pandocs` repository at commit [`0191af06ac49661587dcde3d57a241a626b8df75`](https://github.com/gbdev/pandocs/commit/0191af06ac49661587dcde3d57a241a626b8df75), retrieved 2026-10-07. Relevant source sections are [Rendering](https://github.com/gbdev/pandocs/blob/0191af06ac49661587dcde3d57a241a626b8df75/src/Rendering.md), [Pixel FIFO](https://github.com/gbdev/pandocs/blob/0191af06ac49661587dcde3d57a241a626b8df75/src/pixel_fifo.md), [Tile Maps](https://github.com/gbdev/pandocs/blob/0191af06ac49661587dcde3d57a241a626b8df75/src/Tile_Maps.md), [Tile Data](https://github.com/gbdev/pandocs/blob/0191af06ac49661587dcde3d57a241a626b8df75/src/Tile_Data.md), [Graphics](https://github.com/gbdev/pandocs/blob/0191af06ac49661587dcde3d57a241a626b8df75/src/Graphics.md), [Accessing VRAM and OAM](https://github.com/gbdev/pandocs/blob/0191af06ac49661587dcde3d57a241a626b8df75/src/Accessing_VRAM_and_OAM.md), and [Interrupt Sources](https://github.com/gbdev/pandocs/blob/0191af06ac49661587dcde3d57a241a626b8df75/src/Interrupt_Sources.md). These are maintained technical documentation for Game Boy behavior, including DMG; they do not provide a CPU-B-specific hardware observation for every rule. Applicability below is therefore a documented DMG expectation applied to the bootless `GBB_PROFILE_DMG_CPU_B` model, not a physical CPU-B qualification.

## Image composition cases

| Case | Guest setup and independent expected result | Evidence class | Scope / caveat |
|---|---|---|---|
| `frame_composition_bg` signed/wrap | Guest selects map `$9C00`, signed tile data, `SCX=SCY=$FF`, palette `$93`; authored shade image checks tile 0 at `$9000`, map row/column wrap, and a contrasting unselected `$9800` map. | Owned software composition; original expected pixels in `tests/test_ppu.c`. | Tile-map, signed-address, wrap, and palette rules from Tile Maps / Tile Data / Palettes. CPU-B hardware not observed. |
| `frame_composition_bg` unsigned/map | Guest selects map `$9C00` and unsigned tile 0 at `$8000`; the `$9800` map points to a different tile. | Owned software composition; full independently filled shade image. | Same DMG documentation applicability as above. |
| `frame_composition_window` | `WY=1`, `WX=0`; window map at `$9C00`; expected pixels distinguish line before WY, clipped first window pixel, and next internal window row. | Owned software composition. | Tile Maps defines `(WX-7,WY)` and window-line increments only while visible. Mid-line register-write edge cases remain outside this case. |
| `frame_composition_sprites` | Authored OAM rows check 8×8, X/Y flip, OBP0/OBP1, 8×16 even-tile alignment and lower-tile fetch. | Owned software composition. | OAM/tile-data rules; no DMA or mid-line OAM mutation claim. |
| `frame_composition_priority` | Expected pixels check transparent color 0, BG-behind priority, smaller-X ordering, OAM-index tie break, and first-ten scanline selection. | Owned software composition. | DMG composition rules from Rendering / Graphics / OAM. Not a physical observation. |

## Timing expectation matrix

Timing cases use guest bus observations and the private test observer; each row records dots from the start of a visible scanline, where one dot is two core half-dots. CPU bus operations occur at their scheduled machine phases, so the test asserts the observed access timestamp and register value rather than treating a rendered image as a timing oracle.

| Case | Primary documented expectation | Applicability / unverified boundary |
|---|---|---|
| Modes | Mode 2 occupies dots 0–79; baseline Mode 3 starts at dot 80 and lasts 172 dots; HBlank fills the remaining 204 dots of a 456-dot line. | Generic DMG documentation; exact half-dot phase for readable mode transitions on CPU-B is not physically observed. |
| Fine scroll | Mode 3 adds `SCX & 7` dots; its leftmost background pixels are discarded. | Pan Docs Rendering; mid-scanline SCX write phase remains unclaimed. |
| Window | A visible window costs six dots while the BG fetcher is restarted; WX=0 with nonzero fine SCX has the documented one-dot shortening. | Pan Docs Pixel FIFO / Rendering. Window activation/restart write edges vary by hardware state and are not generalized here. |
| Objects | Each displayed intersecting object adds 6–11 dots under the documented fetch-wait rule; X=0 has the documented fixed 11-dot penalty. | Pan Docs Rendering. Exact ordering of the X=0 penalty relative to fetch wait is explicitly unconfirmed by Pixel FIFO and excluded from exact assertions. |
| VBlank | LY=144 enters Mode 1 and requests VBlank; frame has 154 lines, with LY 144–153 in VBlank before wrap. | Generic DMG reference. Initial post-boot mode and LCD disable/re-enable phase are emulator startup policy until independently qualified. |
| STAT | Enabled Mode 0/1/2 and LY=LYC sources feed one ORed interrupt line; IF is requested on its rising edge. | Pan Docs Interrupt Sources. DMG STAT-write transient and CPU-B-specific sub-dot coincidence timing are excluded pending qualified cases. |

No case in this plan substitutes agreement with another emulator for hardware evidence. Any unlisted revision-sensitive effect is outside the claim and remains an evidence gap.
