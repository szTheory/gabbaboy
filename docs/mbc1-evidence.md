# MBC1 and battery-continuation evidence

This ledger maps Phase 4's SAVE requirements to the implementation, required
test names, reproducible fixture, and evidence class. It describes the
bootless DMG-CPU-B software profile; it does not claim physical hardware
qualification or general Game Boy compatibility.

## Requirement traceability

| Requirement | Implementation and executable evidence | Evidence class and limit |
|---|---|---|
| SAVE-01 — declared MBC1 support | `cartridge_bank_matrix`, `cartridge_ram_banks`, `cartridge_no_ram_reads`, `loader_mbc1_matrix`, `loader_mbc1m_variant`, and `loader_unsupported_cartridge` in the required core inventory. | Synthetic ROMs exercise the documented software model and strict header matrix. The MBC1M check recognizes a conservative candidate class and does not identify all multicarts. |
| SAVE-02 — bounded battery API | `battery_roundtrip8`, `battery_roundtrip32`, `battery_errors`, `battery_no_battery`, `battery_lifecycle`, `battery_instances`, `battery_api_fuzz`, plus relocated `installed_consumer_c` and `installed_consumer_cpp`. | Caller-owned API and public installed-package behavior. The seeded corpus is bounded regression fuzzing, not an unbounded campaign. Linux ASan/UBSan is a separate hosted gate. |
| SAVE-03 — safe player persistence | `player_session_identity`, `player_session_reject_matrix`, `player_session_max_size`, special-file and symlink cases, write/sync/rename/recovery fault cases, interruption cases, `player_session_lock_lifecycle`, `player_session_save_cadence`, and `player_session_transition_choices`. | macOS adapter tests inject file failures and process interruption. Before-rename failure preserves the old complete target; after-rename interruption can leave the new complete target. No power-loss behavior is claimed. Advisory locks coordinate cooperating GabbaBoy processes only. |
| SAVE-04 — meaningful fresh-process resume | `mbc1_continuation_fixture_digest`, `player_continuation_resume`, `player_continuation_missing_save`, `player_continuation_wrong_rom`, `player_continuation_mutated_payload`, and the extracted player-package continuation smoke. | Original project-authored guest plus separate-process file-backed software continuation. It is not a physical MBC1 observation or an emulator-differential claim. |

The exact names are listed in [`tests/expected-tests.txt`](../tests/expected-tests.txt)
and [`tests/player/expected-tests.txt`](../tests/player/expected-tests.txt).
The local macOS player inventory has 37 cases. The package verifier also checks
that the downloaded archive, source revision, fixture digests, notices, and
metadata agree before running its smoke.

## Fixture provenance

`fixtures/mbc1-continuation/continuation.asm` and its 32 KiB ROM are original
project-authored material covered by the repository's MIT license. The manifest
records the source SHA-256
`ad82e0cd51eeb6d536421d20c4a5b88ee0c019a4e699c2c75de077a20c82ba94`, ROM
SHA-256 `f89bf3884ff10a702aa117f2963e6fe9ea8aeac3a9bc003f52b6c5ca6abfbbd2`,
type `$03`, 8 KiB battery RAM, guest protocol, time bound, build recipe, and
bootless applicability. The pinned RGBDS 1.0.1 macOS archive used locally had
SHA-256 `2f6f13c6ec984313656c07b08d97dfcd3a471c7d3901d3ff486e5814bb503645`;
the reproduction script rebuilt byte-identical ROM data. Its Linux CI archive
pin is recorded in the same manifest and consumed by the `fixture-repro`
workflow.

## Executed local results

The Plan 04-06 implementation commits are `94bbf32` and `054adf0`. The local
Plan 04-07 validation and package run used source revision
`918ec265d1ab2a94292fe12c52a16563de8926b1`:

- The core CTest inventory passed **155/155**, including the bounded battery
  API fuzz case and offline fixture digest check.
- The relocated installed verifier passed **160/160** CTests, including the
  external C and C++ consumers, then passed a fresh core-only inventory
  **155/155**. Neither inventory skipped a case.
- The optional macOS player verifier passed **37/37** cases and reopened the
  packaged MBC1 fixture in a fresh process. The candidate package SHA-256 was
  `dc2b8ebdeee56fb73a5d14bbfa5c2872ab2cfcbebd2180cd3740814fedded9d2`.
- The pinned macOS RGBDS archive rebuilt the fixture byte-for-byte with the
  manifest's source and ROM digests.
- The local macOS host did not run Linux ASan/UBSan. No sanitizer result is
  inferred from the ordinary CTest pass.

## Issue and PR triage

At Phase 4 closeout on 2026-10-08, authenticated GitHub queries found no
unrelated open issues or pull requests. PR #8 is the Phase 4 review vehicle;
its final closeout revision must pass the exact-head checks before merge.

Earlier plan summaries record the focused matrix and API selections, recovery
and atomic-write fault cases, lock/cadence behavior, and initial separate-
process controls: [`04-01-SUMMARY.md`](../.planning/milestones/v0.1-phases/GB-04-mbc1-and-safe-battery-continuation/04-01-SUMMARY.md),
[`04-02-SUMMARY.md`](../.planning/milestones/v0.1-phases/GB-04-mbc1-and-safe-battery-continuation/04-02-SUMMARY.md),
[`04-03-SUMMARY.md`](../.planning/milestones/v0.1-phases/GB-04-mbc1-and-safe-battery-continuation/04-03-SUMMARY.md),
[`04-04-SUMMARY.md`](../.planning/milestones/v0.1-phases/GB-04-mbc1-and-safe-battery-continuation/04-04-SUMMARY.md),
[`04-05-SUMMARY.md`](../.planning/milestones/v0.1-phases/GB-04-mbc1-and-safe-battery-continuation/04-05-SUMMARY.md),
and [`04-06-SUMMARY.md`](../.planning/milestones/v0.1-phases/GB-04-mbc1-and-safe-battery-continuation/04-06-SUMMARY.md).

## Evidence classification

| Class | Admitted evidence | What it does not establish |
|---|---|---|
| Documented | [Pan Docs: MBC1](https://gbdev.io/pandocs/MBC1.html), [Pan Docs: cartridge header](https://gbdev.io/pandocs/The_Cartridge_Header.html), and Gekkio's [Game Boy: Complete Technical Reference](https://gekkio.fi/files/gb-docs/gbctr.pdf). | Documentation describes intended or known circuitry; it is not a measurement of the supported physical unit. |
| Software model | Owned synthetic bank, RAM gate, loader, API, and player-session regressions run against the declared profile. | It does not prove every revision, board, special wiring, startup condition, or game. |
| Original fixture | Digest-pinned source and ROM; bounded guest assertion; fresh process reloads the saved tuple and reaches a distinct marker. | It does not make the guest a general compatibility test or hardware oracle. |
| Emulator differential | None admitted as a Phase 4 pass criterion. Emulator source was used only as a cross-check in research; no differential result is claimed here. | Source agreement is not independent physical evidence. |
| Physical hardware | No identified DMG-CPU-B/MBC1 device, board revision, capture, or observation was used. | No physical MBC1, DMG, CGB, or power-on RAM claim is made. |

Process interruption tests stop a child before or after rename and inspect the
complete target. They do not remove power or test storage-controller behavior.
Directory-sync failure after rename is reported as uncertain durability; a
complete new target may already be visible. CRC-32 detects accidental damage
and is not authentication.

## Hosted exact-head evidence

On 2026-10-08, PR #8's exact source-and-fixture head was
`79f83f627ffb3631811b2f39b23081117ebaab8f`. All three pull-request workflow
runs below passed on that SHA. The detailed job IDs, downloaded receipt
contents, and package re-hash results are recorded in the
[Phase 4 validation record](../.planning/milestones/v0.1-phases/GB-04-mbc1-and-safe-battery-continuation/04-VALIDATION.md).

- CI run **37728192665** passed `required-native`, `native-linux-x64`,
  `native-macos-arm64`, `native-windows-x64`, `linux-asan-ubsan`,
  `cmake-floor-3.25.3`, and `macos-player-package`.
- Fixture run **37728192634** passed `fixture-repro`,
  `mooneye-original-repro`, and `mooneye-candidate-repro`, including
  byte-for-byte reproduction of the MBC1 continuation fixture.
- Preview package run **37728192674** passed the aggregate, installed Linux
  and macOS consumers, and downloaded macOS player smoke. Each receipt named
  source SHA `79f83f627ffb3631811b2f39b23081117ebaab8f`.

The downloaded package bytes were locally re-hashed against their receipts:

| Package | Source SHA | Package SHA-256 | Smoke result |
|---|---|---|---|
| Linux core preview | `79f83f627ffb3631811b2f39b23081117ebaab8f` | `74e893cdadd453dd13c981b7324448f824d53baad5388fa2217ed54743491ca2` | passed |
| macOS core preview | `79f83f627ffb3631811b2f39b23081117ebaab8f` | `5c5284633295504167ac689a5207fa3debba52e81f7231d18e01e64330efebf2` | passed |
| macOS player preview | `79f83f627ffb3631811b2f39b23081117ebaab8f` | `44fbac8b86eee0a1dc1565848a3febee2692e85edc117545a7d8d6d386a26d17` | passed; fresh-process continuation |

The player receipt reports `hardware_qualified: false`, `signed: false`, and
`notarized: false`. The documented result applies to the exact source head
above. The final closeout documentation revision is a separate PR head and
must pass its own required exact-head checks before merge. Skipped, stale,
canceled, unavailable, or manual-dispatch-only results do not satisfy that
final-head gate.

## Scope exclusions

There is no boot-ROM execution, CGB, RTC, MBC1M support, other mapper support,
raw `.sav` interchange, full-machine snapshots, unlicensed fixture, private
save data, mandatory telemetry, physical-hardware validation, or guarantee
against power loss. A successful exact-head CI run establishes the named
software/package checks only.
