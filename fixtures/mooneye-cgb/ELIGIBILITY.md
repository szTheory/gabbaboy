# Mooneye CGB-profile eligibility audit

## Inventory

Four ROMs, all derived from Mooneye Test Suite commit `31510e12eea6286d36eea060a6adde755e1067aa` (MIT, `LICENSE.txt`). Identity, digests and build recipe are in `SOURCES.md` and `manifest.json`. All four are compat-mode ROMs: none defines `CART_CGB`, and the reproduction script asserts bit 7 of the header byte `$143` is clear.

| ROM | Upstream source | `$143` | Manifest `expect` | `target_revision` |
|---|---|---|---|---|
| `boot_regs-cgb.gb` | `misc/boot_regs-cgb.s` | `0x00` | pass | CGB |
| `boot_div-cgbABCDE.gb` | `misc/boot_div-cgbABCDE.s` | `0x00` | pass | CGB-A..E |
| `boot_hwio-C.gb` | `misc/boot_hwio-C.s` | `0x00` | expected-unsupported, stop `unsupported-bus` at `0xFF76` | CGB |
| `unused_hwio-C.gb` | `misc/bits/unused_hwio-C.s` | `0x00` | expected-unsupported, stop `unsupported-bus` at `0xFF76` | CGB |

`boot_hwio-C` and `unused_hwio-C` are admitted only as expected-unsupported: they stop on the unbuilt FF76/FF77 PCM registers, so neither is counted as a pass. They flip to pass in Phase 14 when those registers are built. No ROM is admitted as a pass when it stops on unbuilt hardware.

## Evidence class

The upstream results are author-attested Mooneye hardware results, stated in each source header:

- `boot_regs-cgb`: pass on CGB.
- `boot_div-cgbABCDE`: pass on CGB A, B, C, D and E (it fails on CGB 0).
- `boot_hwio-C` and `unused_hwio-C`: pass on CGB, AGB and AGS.

Here the derivative ROMs execute on the CGB-CPU-E software profile in compat mode through the unchanged `LD B,B` register protocol. GabbaBoy claims only the applicability each source states:

- `boot_div-cgbABCDE` supports a "CGB A-E" claim and **never a CGB-E-alone claim**; the manifest `target_revision` is `CGB-A..E`.
- No AGB or AGS claim is made, even though two headers list them.
- Never game compatibility, never hardware qualification of this emulator.

The derivatives are not untouched upstream ROMs: the parent headless-report patch removes PPU-only harness sections so the verdict does not depend on PPU behavior, and the font is replaced by a zero asset (`FONT-LICENSE.txt`). Assertions are unchanged. The manifest `original_sha256` records the unpatched build for provenance.

## What reaching FF76 proves (C3)

"Reaching FF76 proves FF00-FF75 passed" holds for boot_hwio-C only (`boot_hwio-C`): it compares every address from FF00 sequentially and reports the first mismatch, so a stop at FF76 means every checked row before it matched. It does not hold for `unused_hwio-C`: that ROM's unmapped rows (`$FF03`, `$FF08`-`$FF0E`, `$FF15`, `$FF1F`, `$FF27`-`$FF29`, `$FF4C`-`$FF4E`, `$FF50`-`$FF67`, `$FF69`, `$FF6B`-`$FF71`, `$FF74`, `$FF78`-`$FF7F`) come after its FF76/FF77 rows, so a stop at FF76 says nothing about them. Claims about unmapped-register visibility rest on the `cgb_visibility_` sweeps, not on this Mooneye stop.

## Not admitted

- `unused_hwio-GS`: the DMG variant would require a DMG behaviour change (DMG FF4C-FF7F reading `$FF`), excluded by D-09; candidate for Phase 14 qualification.
- `oam_dma/sources-GS`: DMG-only.
- `boot_*-cgb0` and `boot_*-A` ROMs: unsupported CGB steppings.
- AGE and SameSuite test ROMs: deferred to Phase 14.

## Per-ROM program-counter table

From `tests/scripts/reproduce-mooneye-cgb.sh --facts` on the byte-identical rebuild (the four built ROMs equal the committed ROMs). Assert-style ROMs (`boot_regs-cgb`, `boot_div-cgbABCDE`) end in one shared `check_asserts_cb` callback at `0x4000`, so their pass and fail callback program counters are the same and the `LD B,B` registers decide, as for `tim00`. `boot_regs-cgb` also lists the `invalid_sp` inline quit site `0x01da` as a fail callback. The two hwio ROMs quit through inline sites: the first is the pass site and the second the mismatch (fail) site. The manifest and the runner's `cgb_cases[]` carry the same values; `cgb_mooneye_pc_table` fails if those two disagree. Budgets are generous multiples of the measured cost (about 34.7k half-dots for the two assert ROMs, a stop at 16.6k and 15.9k half-dots for the two staged ROMs).

| ROM alias | result_pc | pass callback | fail callbacks | budget (half-dots) |
|---|---|---|---|---:|
| `boot_regs-cgb` | `0x4327` | `0x4000` | `0x4000`, `0x01da` | 500000 |
| `boot_div-cgbABCDE` | `0x4327` | `0x4000` | `0x4000` | 500000 |
| `boot_hwio-C` | `0x4067` | `0x01ce` | `0x01f5` | 2000000 |
| `unused_hwio-C` | `0x4070` | `0x1a02` | `0x1a31` | 2000000 |
