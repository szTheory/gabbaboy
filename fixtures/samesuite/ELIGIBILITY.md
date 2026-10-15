# SameSuite CGB DMA and APU fixture eligibility

## Pinned admission

This directory contains four DMA and one APU fixture from SameSuite revision
`f15645fb049a47ea235f6d2c9a033e72d8087901`:

| Case | Source | Intended observation |
|---|---|---|
| `gbc_dma_cont` | `dma/gbc_dma_cont.asm` | Two consecutive one-block GDMA starts copy contiguous expected bytes into VRAM. |
| `gdma_addr_mask` | `dma/gdma_addr_mask.asm` | Low address nibbles written to HDMA1-4 are ignored and one block copies expected WRAM bytes. |
| `hdma_lcd_off` | `dma/hdma_lcd_off.asm` | The author-encoded result expects one block on an LCD-off HBlank-DMA start, then records the remaining and cancellation status sequence. |
| `hdma_mode0` | `dma/hdma_mode0.asm` | After waiting for visible Mode 0, the author-encoded result expects one block and records the remaining and cancellation status sequence. |

The selected APU corpus contains all 70 pinned `apu/*.asm` sources. The first
admitted tracer is `apu/channel_3/channel_3_first_sample.asm`; its manifest row
records the exact source and ROM SHA-256, RGBDS build recipe, output filename,
and source-encoded result bytes `00 00 00 00 00 0e 0e 0e`. Each admitted APU
output retains the same source-level CGB-E pass expectation, including revision
suffix variants. The README's aggregate claim is not independent physical
hardware evidence.

The manifest pins each source and include closure, source and ROM sizes and
SHA-256 values, the upstream output filename, RGBDS 1.0.1 archive digests,
build options, and the bootless `CGB-CPU-E selected software model` applicability.
The reproducer validates this exact set and byte-compares fresh builds without
overwriting committed ROMs.

## Rights

The pinned SameSuite repository X11 license is retained in `LICENSE.txt`.
G7 accepts that repository license for `include/hexdigits.2bpp`. The included
`include/hardware.inc` carries its own CC0-1.0 waiver and SPDX notice; the
corresponding notice excerpt is also retained in `LICENSE.txt`. These are the
actual source notices and adopted rights bases, not a new permission request.

## Evidence limits and retained contradiction

These are author test ROMs: their encoded expected sequences and successful
RGBDS reproduction establish fixture provenance and bytes. Reproduction does
not run an emulator, establish a core pass, or supply independent physical
CGB-E evidence. The target label is the selected software model, not a hardware
measurement.

D-06 retains the SameSuite `hdma_lcd_off` and `hdma_mode0` expectations: write
`$83`, observe the author-expected `$02`, cancel with `$00`, then observe `$80`.
Pan Docs instead describes retained remaining-length readback and warns against
starting in Mode 0. This contradiction remains visible here; the upstream
expected results are unchanged, and this fixture admission does not resolve
physical CGB-E behavior.

The DMA admission is limited to the four rows above. Mealybug
`hdma_timing-C` and `hdma_during_halt-C` are not included: they target CGB-C,
and their unresolved font closure remains gated by G1. Any future CGB-C result
is informational and outside the CGB-E evidence set.
