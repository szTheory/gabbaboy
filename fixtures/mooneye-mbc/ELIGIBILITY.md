# Mooneye mbc2/mbc5 eligibility audit

## Inventory

Categories: `mbc2` 7 and `mbc5` 8. Eligible = executed = 15. The suite receipt is:

```
suite eligible=15 executed=15 status=pass
suite categories mbc2=7/7 mbc5=8/8
```

The sources are the `emulator-only/mbc2` and `emulator-only/mbc5` tests of Mooneye Test Suite commit `31510e12eea6286d36eea060a6adde755e1067aa` (MIT, `LICENSE.txt`). Their identity, closure and digests are in `SOURCES.md` and `manifest.json`.

## Evidence class (D-30)

The upstream pass results are author-attested hardware results: the Mooneye author records them from a flash cartridge with a genuine MBC5 chip or a genuine MBC2A chip. Here the derivative ROMs execute on the bootless DMG-CPU-B software profile through the unchanged `LD B,B` register protocol. That is the whole claim:

- no model-specific claim beyond that profile, and **no CGB claim**;
- **never game compatibility**, never hardware qualification of this emulator, and not a statement about any commercial cartridge;
- the MBC2A variant caveat: the upstream MBC2 results come from an MBC2A part. Other MBC2 revisions may differ in behavior these tests do not exercise, and nothing here speaks for them;
- none of the 15 exercises MBC5 RAM or rumble. Those behaviors rest on `tests/test_mbc5.c` and `fixtures/mbc5-banking`, not on this suite.

The derivatives are not untouched upstream ROMs: the parent headless-report patch removes PPU-only harness sections so the verdict does not depend on PPU behavior; assertions are unchanged. The ROM digests were captured from a local rebuild and then matched 15 of 15 by the hosted Linux `mooneye-mbc-repro` leg (run 38151282870).

## Per-ROM program-counter table

The result breakpoint is the `LD B,B` after the pass or fail callback. The manifest values are compared with the compiled `mbc_cases[]` rows in `src/runner/main.c` by `mooneye_mbc_pc_table`.

| ROM alias | result_pc | pass callback | fail callbacks | budget (half-dots) |
|---|---|---|---|---:|
| `mbc2_bits_ramg` | 0x407e | 0x01d7 | 0x0218, 0x0255, 0x029c, 0x02c1 | 97200000 |
| `mbc2_bits_romb` | 0x407e | 0x01c0 | 0x0174, 0x01f8 | 49600000 |
| `mbc2_bits_unused` | 0x407e | 0x018d | 0x01cc | 46200000 |
| `mbc2_ram` | 0x4071 | 0x029c | 0x06f8, 0x0719, 0x073a, 0x075b, 0x077c, 0x079d | 5300000 |
| `mbc2_rom_512kb` | 0x4071 | 0x0207 | 0x0175 | 100000 |
| `mbc2_rom_1Mb` | 0x4071 | 0x0207 | 0x0175 | 100000 |
| `mbc2_rom_2Mb` | 0x4071 | 0x0207 | 0x0175 | 100000 |
| `mbc5_rom_512kb` | 0x4072 | 0x0216 | 0x0175 | 900000 |
| `mbc5_rom_1Mb` | 0x4072 | 0x0216 | 0x0175 | 900000 |
| `mbc5_rom_2Mb` | 0x4072 | 0x0216 | 0x0175 | 900000 |
| `mbc5_rom_4Mb` | 0x4072 | 0x0216 | 0x0175 | 900000 |
| `mbc5_rom_8Mb` | 0x4072 | 0x0216 | 0x0175 | 900000 |
| `mbc5_rom_16Mb` | 0x4072 | 0x0216 | 0x0175 | 900000 |
| `mbc5_rom_32Mb` | 0x4072 | 0x0216 | 0x0175 | 900000 |
| `mbc5_rom_64Mb` | 0x4072 | 0x0216 | 0x0175 | 900000 |

The PCs come from the linker symbol file (`quit@serial_dump` for the result, the single `quit_ok` site's enclosing label for the pass callback, all other `quit_inline` sites for the fail callbacks) via `tests/scripts/reproduce-mooneye-mbc.sh --facts`. The three result PCs (0x407e, 0x4071, 0x4072) are the linked address of each ROM's `quit@serial_dump` label; they are per-ROM layout facts, not a shared constant, so they are pinned individually.

## Budgets (Open Question 2)

Method: the runner counts half-dots until the chunked `LD B,B` detection. Budget = ceil(2 x measured / 100000) x 100000. Measured on Darwin 26.6.2 arm64, Debug build (preset `phase1`), Plan 08-05; wall time was at most 1.9 s per ROM, so the default 30 s CTest timeout applies to every case.

| ROM | measured half-dots | final budget |
|---|---:|---:|
| `mbc2_bits_ramg` | 48558168 | 97200000 |
| `mbc2_bits_romb` | 24779552 | 49600000 |
| `mbc2_bits_unused` | 23073192 | 46200000 |
| `mbc2_ram` | 2646176 | 5300000 |
| `mbc2_rom_512kb`, `mbc2_rom_1Mb`, `mbc2_rom_2Mb` | 31792 each | 100000 |
| `mbc5_rom_512kb` through `mbc5_rom_64Mb` (8 ROMs) | 421568 each | 900000 |

Half-dot counts are emulated time, not host time, and are deterministic for a fixed core revision; a core timing change that moves them is a reason to re-measure, not to widen a budget silently.

## Negative controls pinned by CTest

- `mooneye_mbc_pc_table_tamper`: a copied manifest with a changed `result_pc` must fail `pc-table-mismatch` with exit code 1.
- `mooneye_mbc_unknown_manifest`: a manifest differing by one byte must be refused by the runner with `invalid-manifest` and exactly exit code 2.
- `mooneye_mbc_type_mutation`: `mbc5_rom_512kb` with header byte `$147` changed to `$01` (MBC1) and the header checksum recomputed must not pass.
