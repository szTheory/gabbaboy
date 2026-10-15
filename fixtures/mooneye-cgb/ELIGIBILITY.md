# Mooneye CGB-profile eligibility audit

## Inventory

Four ROMs, all derived from Mooneye Test Suite commit `31510e12eea6286d36eea060a6adde755e1067aa` (MIT, `LICENSE.txt`). Identity, digests and build recipe are in `SOURCES.md` and `manifest.json`. All four are compat-mode ROMs: none defines `CART_CGB`, and the reproduction script asserts bit 7 of the header byte `$143` is clear.

| ROM | Upstream source | `$143` | Author `expect` | Current CGB-CPU-E software observation | `target_revision` |
|---|---|---|---|---|
| `boot_regs-cgb.gb` | `misc/boot_regs-cgb.s` | `0x00` | pass | pass | CGB |
| `boot_div-cgbABCDE.gb` | `misc/boot_div-cgbABCDE.s` | `0x00` | pass | pass | CGB-A..E |
| `boot_hwio-C.gb` | `misc/boot_hwio-C.s` | `0x00` | pass | xfail: guest fail callback `0x01F5`, result `0x4067` | CGB |
| `unused_hwio-C.gb` | `misc/bits/unused_hwio-C.s` | `0x00` | pass | xfail: guest fail callback `0x1A31`, result `0x4070` | CGB |

The two HWIO ROMs retain their upstream author assertion `expect=pass`. The CGB-CPU-E software model currently reaches each ROM's exact fail callback and `LD B,B` failure result with the declared failure registers. The runner reports `status=xfail observed=fail`; neither row enters the guest-pass count. The xfail matches only the compiled failure callback, result PC and all six failure registers, and the inventory/pc-table checks bind those values to the manifest.

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

## Current HWIO observations

`boot_hwio-C` produced the raw guest verdict `fail` at callback `0x01F5` and result `0x4067` after 25,904 half-dots. `unused_hwio-C` produced `fail` at callback `0x1A31` and result `0x4070` after 34,504 half-dots. These are software-model observations, not changes to the author-attested hardware result. The separate `cgb_visibility_` sweeps remain the source for unmapped-register visibility claims.

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
