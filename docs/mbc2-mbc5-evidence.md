# MBC2 and MBC5 cartridge evidence

This ledger maps Phase 8's cartridge requirements (CART-01 through CART-03) to
the implementation, required test names, fixtures and evidence class. It
describes the bootless DMG-CPU-B software profile. Mooneye pass counts, the
original banking fixture and the rumble query are **not game compatibility**
evidence, not CGB support, not physical rumble evidence and not hardware
qualification. The user-facing contract is in
[cartridge-and-saves.md](cartridge-and-saves.md); the earlier MBC1 and
battery-continuation ledger is [mbc1-evidence.md](mbc1-evidence.md).

## Requirement traceability

| Requirement | Executable evidence | Evidence class and limit |
|---|---|---|
| CART-01 — cartridge mapper seam, no observable DMG change | Differential harness (old core at `5673bed` versus the seam), run before and after each mapper plan: `cells=86016 differences=0` for the seam alone (old and new output SHA-256 both `d171c90d...800b6`); `--exclude-types 05,06` rerun `cells=85344 differences=0`; `--exclude-types 05,06,19,1A,1B,1C,1D,1E` rerun `cells=83328 differences=0`. The unchanged MBC1, battery and loader suites (`cartridge_*`, `battery_*`, `loader_*`, `mbc1_continuation_*`), `dmg_baseline` and the frozen `measure_core` digest `4c7a57ff3d50d228` all still pass. | Differential oracle against the project's own previous core plus regression fixtures. The harness lives under the phase planning directory and is not a CTest. The `measure_core` timing was advisory only, and the 32 KiB tracer it runs exercises the ROM-only kind, so it makes no MBC performance claim. |
| CART-02 — MBC5 | `mbc5_tracer`, `mbc5_header_matrix`, `mbc5_rom_banking`, `mbc5_ram_enable`, `mbc5_ram_banking`, `mbc5_no_ram_window`, `mbc5_battery`, `mbc5_rom_bound`, `mbc5_cgb_flag_ignored`, `mbc5_cross_mapper_control`, `mbc5_rumble_state`, `mbc5_rumble_errors`, `mbc5_rumble_reset_load`, `mbc5_reset_preserves_ram`, `mbc5_rumble_saturation`; Mooneye `mooneye_mbc_case_mbc5_rom_512kb` through `_64Mb` (8 of 8); the original-fixture cases `mbc5_banking_guest`, `mbc5_banking_guest_1b` and `mbc5_bank_1ff`; the ninth-bit mutant cases `mbc5_ninth_bit_mutant_bank_1ff` and `mbc5_ninth_bit_mutant_control_below_100`; the installed C and C++ consumers' `gbb_rumble_state` calls. | Synthetic ROMs (unit tests), author-attested upstream hardware results (Mooneye), and an original software fixture with a synthetic oracle. None is a physical observation by this project. |
| CART-03 — MBC2 | `mbc2_tracer`, `mbc2_header_matrix`, `mbc2_register_decode`, `mbc2_ram_echo`, `mbc2_reset`, `mbc2_battery_image`, `mbc2_battery_import`, `mbc2_battery_idempotent`, `mbc2_battery_errors`, `mbc2_battery_no_battery`, `mbc2_two_instance_roundtrip`; Mooneye `mooneye_mbc_case_mbc2_bits_ramg`, `_bits_romb`, `_bits_unused`, `_ram`, `_rom_512kb`, `_rom_1Mb`, `_rom_2Mb` (7 of 7). | Synthetic ROMs plus author-attested upstream results; see the MBC2A caveat below. |

The full inventory is [`tests/expected-tests.txt`](../tests/expected-tests.txt)
(319 names at this revision, additions only for Phase 8). The player check for
the unsupported-save status is `player_session_battery_unsupported` in
[`tests/player/expected-tests.txt`](../tests/player/expected-tests.txt).

## Mooneye emulator-only mbc2 and mbc5 derivatives

Fifteen ROMs live in [`fixtures/mooneye-mbc`](../fixtures/mooneye-mbc) as a
sibling of the earlier `fixtures/mooneye` set; the parent set, its manifest and
its CTests are unchanged. The pins, provenance, per-ROM program-counter table,
budgets and eligibility reasoning are in
[SOURCES.md](../fixtures/mooneye-mbc/SOURCES.md) and
[ELIGIBILITY.md](../fixtures/mooneye-mbc/ELIGIBILITY.md).

- **Source:** Mooneye test suite revision
  `31510e12eea6286d36eea060a6adde755e1067aa`, built with the pinned WLA-DX
  revision and the parent set's headless-report patch and zero-font
  replacement (referenced by relative path and SHA-256, not copied).
- **Result:** `suite eligible=15 executed=15 status=pass`, categories
  `mbc2=7/7 mbc5=8/8`, on the bootless DMG-CPU-B profile, through the same
  `LD B,B` oracle as the parent set.
- **Reproduction:** the local Darwin/arm64 rebuild matched every pinned digest.
  The hosted Linux `mooneye-mbc-repro` leg
  ([run 38151282870](https://github.com/szTheory/gabbaboy/actions/runs/38151282870),
  ubuntu-22.04, `wla-gb` 10.7, `wlalink` 5.22) printed 15 of 15 `match` lines
  against the same digests, so the digests are not specific to one host.
- **Evidence class (D-30):** the upstream suite's results are author-attested
  hardware results from a flash cart with a genuine MBC5 or MBC2A chip. Here
  they are executed on this project's software profile. They support the
  mapper behavior that the tests exercise and nothing broader.
- **MBC2A caveat:** the upstream `ram` test's expected upper-nibble behavior
  was observed on an MBC2A variant. The project adopts that behavior; other MBC2
  board revisions are not claimed.
- **Not covered:** the `mbc5` ROMs do not exercise RAM or the rumble line, and
  they are not CGB tests.
- **The ninth bank bit:** no Mooneye mbc5 ROM, `rom_64Mb` included, selects a
  bank at or above 256. The shared upstream harness loop ends at bank `$FF`
  (measured in Plan 08-07), so `rom_64Mb` is admitted as the 8 MiB loader and
  install-policy case only. See the next section for the ninth-bit proof.

## Original MBC5 banking fixture and ninth-bit mutant

[`fixtures/mbc5-banking`](../fixtures/mbc5-banking) holds an original,
MIT-licensed 64 KiB guest (`banking.asm` and `banking.gb`, type `$1E`) built
with RGBDS 1.0.1. The ROM SHA-256 is
`0b852837522f45fc3486d69d6b406f956d7dcc0f08a0f0ee6e2a2c288cddffef`;
[`tests/scripts/reproduce-mbc5-banking.sh`](../tests/scripts/reproduce-mbc5-banking.sh)
rebuilds it byte-identically, and the hosted `fixture-repro` workflow carries a
reproduce step for it. The guest checks bank 0 in the upper window, both
bank-write orders, RAM banking, and rumble bit 3 masked out of RAM banking, all
through the real CPU and bus. `mbc5_banking_guest_1b` reruns it as a non-rumble
`$1B` image.

The bank `$1FF` case `mbc5_bank_1ff` inflates the image in memory to exactly
8 MiB and has the test harness place a marker byte in bank `$1FF`; the guest
reads it through the mapper. The marker is supplied by the harness, not stored
in the committed ROM. This is **an original software fixture plus a synthetic
oracle, not hardware evidence**.

The ninth-bit mutant is generated at configure time from
`src/core/gabbaboy.c` by replacing the single anchor `& 1u) << 8` with
`& 0u) << 8` (configure fails unless the anchor occurs exactly once). The
mutant library is never installed. Measured outcomes:

- `mbc5_ninth_bit_mutant_bank_1ff` runs the `bank_1ff` case against the mutant
  and requires failure: it exits 1 at the `$1FF` check (guest result C005),
  while the checks before it still pass.
- `mbc5_ninth_bit_mutant_control_below_100` runs the plain banking guest
  against the same mutant and requires success, so the mutant is shown to
  break only banks at or above 256.
- The unmutated `mbc5_bank_1ff` passes.

The MBC5 unit tests `mbc5_rom_banking` and `mbc5_rom_bound` also cover the
ninth bit on synthetic images.

## Negative controls

- `mooneye_mbc_type_mutation`: the admitted image passes; the same image with
  its type byte changed to MBC1 (header checksum recomputed) must not.
- `mooneye_mbc_pc_table_tamper`, `mooneye_mbc_unknown_manifest`: a changed
  manifest program counter or an unknown manifest digest fails closed.
- `mbc5_cross_mapper_control`: the same write sequence selects different banks
  on MBC1, MBC5 and MBC2 images.

## Redistribution and packaging

The 15 Mooneye ROMs (MIT, with a separate font notice) and the banking fixture
are repository test fixtures only; each has a documented license and digest.
They are not installed and not packaged.

- `mooneye_mbc_not_installed` scans the real install tree by file name and by
  size plus SHA-256 against all 15 ROMs. File symbolic links are followed and
  their targets scanned. Controls: a planted copy, a ROM behind an innocuously
  named link, an empty tree and an exact fixture-directory list
  (`tracer`, `visible-demo`, `mbc1-continuation`).
- The extracted preview package and the staged macOS player package are scanned
  the same way (`preview_package_smoke`, `verify-phase3-player.sh
  --build-package`).
- GitHub's automatically generated source archives are outside that control and
  include the `fixtures/mooneye-mbc` directory (about 17 MiB of test ROMs, small
  once compressed). Phase 8 adds no `export-ignore`; this is revisited at the
  release boundary.

## Known limits

- No physical MBC2/MBC5 observation, CGB behavior, RTC, MBC3, MBC6/7, camera
  or other mapper claim.
- The rumble line is a software query; no physical motor behavior and no host
  haptics are claimed or implemented.
- Test-ROM pass counts are not a statement about any game's behavior.
- The player's on-screen status for unsupported battery cartridges has no
  automated UI test; the source branches and the pinned limitations text are
  checked, and the visible line itself was not observed by a test.
- The ASan/UBSan preset is Linux-only; it was proven on hosted CI, not on the
  local macOS host.
