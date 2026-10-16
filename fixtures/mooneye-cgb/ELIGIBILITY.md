# Mooneye CGB-profile eligibility audit

## Inventory

Nine ROMs, all derived from Mooneye Test Suite commit `31510e12eea6286d36eea060a6adde755e1067aa` (MIT, `LICENSE.txt`). Identity, digests and build recipe are in `SOURCES.md` and `manifest.json`. All nine are compat-mode ROMs: none defines `CART_CGB`, and the reproduction script asserts bit 7 of the header byte `$143` is clear.

| ROM | Upstream source | `$143` | Author `expect` | Current CGB-CPU-E software observation | `target_revision` |
|---|---|---|---|---|
| `boot_regs-cgb.gb` | `misc/boot_regs-cgb.s` | `0x00` | pass | pass | CGB |
| `boot_div-cgbABCDE.gb` | `misc/boot_div-cgbABCDE.s` | `0x00` | pass | pass | CGB-A..E |
| `boot_hwio-C.gb` | `misc/boot_hwio-C.s` | `0x00` | pass | xfail: guest fail callback `0x01F5`, result `0x4067` | CGB |
| `unused_hwio-C.gb` | `misc/bits/unused_hwio-C.s` | `0x00` | pass | xfail: guest fail callback `0x1A31`, result `0x4070` | CGB |
| `daa.gb` | `acceptance/instr/daa.s` | `0x00` | pass | pass | CGB |
| `div_write.gb` | `acceptance/timer/div_write.s` | `0x00` | pass | pass | CGB |
| `tim00.gb` | `acceptance/timer/tim00.s` | `0x00` | pass | pass | CGB |
| `tim00_div_trigger.gb` | `acceptance/timer/tim00_div_trigger.s` | `0x00` | pass | pass | CGB |
| `vblank_stat_intr-C.gb` | `misc/ppu/vblank_stat_intr-C.s` | `0x00` | pass | xfail: assertion callback `0x4000`, result `0x4327` | CGB |

The two HWIO ROMs and `vblank_stat_intr-C` retain their upstream author assertion `expect=pass`. The CGB-CPU-E software model reaches each row's exact failure callback and `LD B,B` result with the declared failure registers. For `vblank_stat_intr-C`, this is the shared assertion callback at `0x4000` and result `0x4327`; the source asserts the measured round values `B=1,C=0,D=1,E=0`. The runner reports `status=xfail observed=fail`; none enters the guest-pass count. Each xfail matches only the compiled failure callback, result PC and all six failure registers, and the inventory/pc-table checks bind those values to the manifest. The vblank discrepancy is assigned to the CGB PPU/interrupt model; promote it only after this pinned guest passes and wrong-callback/signature controls still fail.

## Evidence class

The upstream results are author-attested Mooneye hardware results, stated in each source header:

- `boot_regs-cgb`: pass on CGB.
- `boot_div-cgbABCDE`: pass on CGB A, B, C, D and E (it fails on CGB 0).
- `boot_hwio-C` and `unused_hwio-C`: pass on CGB, AGB and AGS.

Here the derivative ROMs execute on the CGB-CPU-E software profile in compat mode through the unchanged `LD B,B` register protocol. GabbaBoy claims only the applicability each source states:

- `boot_div-cgbABCDE` supports a "CGB A-E" claim and **never a CGB-E-alone claim**; the manifest `target_revision` is `CGB-A..E`.
- No AGB or AGS claim is made, even though two headers list them.
- Never game compatibility, never hardware qualification of this emulator.

The derivatives are not untouched upstream ROMs: the parent headless-report patch removes PPU-only harness sections where applicable so the verdict does not depend on PPU behavior, and the font is replaced by a zero asset (`FONT-LICENSE.txt`). Assertions are unchanged. The manifest `original_sha256` records each unpatched build for provenance.

## Current HWIO observations

`boot_hwio-C` produced the raw guest verdict `fail` at callback `0x01F5` and result `0x4067` after 25,904 half-dots. `unused_hwio-C` produced `fail` at callback `0x1A31` and result `0x4070` after 34,504 half-dots. These are software-model observations, not changes to the author-attested hardware result. The separate `cgb_visibility_` sweeps remain the source for unmapped-register visibility claims.

## Not admitted

- `unused_hwio-GS`: the DMG variant would require a DMG behaviour change (DMG FF4C-FF7F reading `$FF`), excluded by D-09; candidate for Phase 14 qualification.
- `oam_dma/sources-GS`: DMG-only.
- `boot_*-cgb0` and `boot_*-A` ROMs: unsupported CGB steppings.
- AGE and SameSuite test ROMs: deferred to Phase 14.

## Per-ROM program-counter table

From `tests/scripts/reproduce-mooneye-cgb.sh --facts` on the byte-identical rebuild. Assert-style ROMs (`boot_regs-cgb`, `boot_div-cgbABCDE`, `tim00`, `tim00_div_trigger`, and `vblank_stat_intr-C`) end in a shared `check_asserts_cb` callback at `0x4000`; their `LD B,B` registers decide pass or fail. `boot_regs-cgb` also lists the `invalid_sp` inline quit site `0x01da`; `vblank_stat_intr-C` lists `fail_halt` at `0x0173`. The two HWIO ROMs quit through inline sites: the first is the pass site and the second the mismatch (fail) site. DAA uses pass site `0x0166`, fail site `0x01b3`, and result `0x409a`. `div_write` uses pass site `0x0175`, fail site `0x018d`, and result `0x4051`. The manifest and the runner's `cgb_cases[]` carry the same values; `cgb_mooneye_pc_table` fails if those two disagree. Each case has a finite half-dot budget.

| ROM alias | result_pc | pass callback | fail callbacks | budget (half-dots) |
|---|---|---|---|---:|
| `boot_regs-cgb` | `0x4327` | `0x4000` | `0x4000`, `0x01da` | 500000 |
| `boot_div-cgbABCDE` | `0x4327` | `0x4000` | `0x4000` | 500000 |
| `boot_hwio-C` | `0x4067` | `0x01ce` | `0x01f5` | 2000000 |
| `unused_hwio-C` | `0x4070` | `0x1a02` | `0x1a31` | 2000000 |
| `daa` | `0x409a` | `0x0166` | `0x01b3` | 2000000 |
| `div_write` | `0x4051` | `0x0175` | `0x018d` | 6000000 |
| `tim00` | `0x4327` | `0x4000` | `0x4000` | 200000 |
| `tim00_div_trigger` | `0x4327` | `0x4000` | `0x4000` | 200000 |
| `vblank_stat_intr-C` | `0x4327` | `0x4000` | `0x4000`, `0x0173` | 2000000 |
