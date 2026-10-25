---
phase: GB-08-cartridge-seam-mbc5-and-mbc2
verified: 2026-10-21T00:26:14Z
status: passed
score: 97/97 must-haves verified
covered_files:
  - ".gitattributes"
  - ".github/workflows/fixture-repro.yml"
  - ".github/workflows/preview.yml"
  - ".gitignore"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-01-PLAN.md"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-01-SUMMARY.md"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-02-PLAN.md"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-02-SUMMARY.md"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-03-PLAN.md"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-03-SUMMARY.md"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-04-PLAN.md"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-04-SUMMARY.md"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-05-PLAN.md"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-05-SUMMARY.md"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-06-PLAN.md"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-06-SUMMARY.md"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-07-PLAN.md"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-07-SUMMARY.md"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-08-PLAN.md"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-08-SUMMARY.md"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-09-PLAN.md"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-09-SUMMARY.md"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-10-PLAN.md"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-10-SUMMARY.md"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-PACKAGE-REFRESH-EVIDENCE.md"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-PACKAGE-REFRESH-GATES.md"
  - ".planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-UAT.md"
  - "README.md"
  - "THIRD_PARTY_NOTICES.md"
  - "cmake/PreviewPackageSmoke.cmake"
  - "cmake/ScanForbiddenFixtures.cmake"
  - "cmake/VerifyInstalledPackage.cmake"
  - "cmake/VerifyMooneyeMbc.cmake"
  - "docs/cartridge-and-saves.md"
  - "docs/mbc2-mbc5-evidence.md"
  - "docs/native-integration.md"
  - "docs/preview.md"
  - "docs/support/unreleased.md"
  - "fixtures/mbc5-banking/LICENSE.txt"
  - "fixtures/mbc5-banking/banking.asm"
  - "fixtures/mbc5-banking/banking.gb"
  - "fixtures/mbc5-banking/manifest.json"
  - "fixtures/mooneye-cgb/boot_regs-cgb.gb"
  - "fixtures/mooneye-cgb/manifest.json"
  - "fixtures/mooneye-mbc/ELIGIBILITY.md"
  - "fixtures/mooneye-mbc/FONT-LICENSE.txt"
  - "fixtures/mooneye-mbc/LICENSE.txt"
  - "fixtures/mooneye-mbc/SOURCES.md"
  - "fixtures/mooneye-mbc/manifest.json"
  - "fixtures/mooneye-mbc/mbc2_bits_ramg.gb"
  - "fixtures/mooneye-mbc/mbc2_bits_romb.gb"
  - "fixtures/mooneye-mbc/mbc2_bits_unused.gb"
  - "fixtures/mooneye-mbc/mbc2_ram.gb"
  - "fixtures/mooneye-mbc/mbc2_rom_1Mb.gb"
  - "fixtures/mooneye-mbc/mbc2_rom_2Mb.gb"
  - "fixtures/mooneye-mbc/mbc2_rom_512kb.gb"
  - "fixtures/mooneye-mbc/mbc5_rom_16Mb.gb"
  - "fixtures/mooneye-mbc/mbc5_rom_1Mb.gb"
  - "fixtures/mooneye-mbc/mbc5_rom_2Mb.gb"
  - "fixtures/mooneye-mbc/mbc5_rom_32Mb.gb"
  - "fixtures/mooneye-mbc/mbc5_rom_4Mb.gb"
  - "fixtures/mooneye-mbc/mbc5_rom_512kb.gb"
  - "fixtures/mooneye-mbc/mbc5_rom_64Mb.gb"
  - "fixtures/mooneye-mbc/mbc5_rom_8Mb.gb"
  - "include/gabbaboy/gabbaboy.h"
  - "src/core/gabbaboy.c"
  - "src/player/limitations.h"
  - "src/player/main.c"
  - "src/player/session.c"
  - "src/player/session.h"
  - "src/runner/main.c"
  - "tests/CMakeLists.txt"
  - "tests/consumers/c/main.c"
  - "tests/consumers/cpp/main.cpp"
  - "tests/expected-tests.txt"
  - "tests/player/expected-tests.txt"
  - "tests/player/test_limitations.c"
  - "tests/player/test_session.c"
  - "tests/scripts/reproduce-mbc5-banking.sh"
  - "tests/scripts/reproduce-mooneye-mbc.sh"
  - "tests/scripts/verify-dmg-baseline.sh"
  - "tests/scripts/verify-phase3-player.sh"
  - "tests/scripts/verify-phase8-closure-contract.py"
  - "tests/scripts/verify-phase8-player-contract.py"
  - "tests/scripts/verify-summary-coverage.py"
  - "tests/scripts/verify-uat-closure.py"
  - "tests/test_mbc2.c"
  - "tests/test_mbc5.c"
  - "tests/test_mbc5_internal.c"
  - "tests/test_runner.c"
covered_digest: "v3:sha256:3e748905f5571f742525a041102728af7143d1ee4d0e6ec8cda52f61cbc98aed"
behavior_unverified: 0
overrides_applied: 1
decision_coverage:
  honored: 34
  total: 34
  not_honored: []
overrides:
  - must_have: "D-29 ninth-bit mutant uses Mooneye rom_64Mb as discriminator and rom_32Mb as control"
    reason: "Accepted D-062 replaced the non-discriminating upstream ROM-size pair with the original mbc5_bank_1ff fixture and a below-$100 mutant control. The upstream rom_64Mb loop does not select a bank at or above $100; the replacement directly exercises bit 8."
    accepted_by: "Phase 8 adopted decision D-062"
    accepted_at: "2026-10-11"
---

# Phase 8: Cartridge Seam, MBC5 and MBC2 Verification Report

**Phase Goal:** Cartridge behavior lives behind one type-table mapper seam with no observable DMG change, and callers can run MBC5 and MBC2 cartridges.
**Verified:** 2026-10-21 at Phase 8 boundary `96d5eec977bee99a0629499b89c737415e24184c`, with the later package-scan input checked at Phase 10 commit `1ba23463cf1beec9930abd54d19e226ef5e33f7b` and fresh regression results from producer `a338f54abcb1956cd5e6c3c5faba716137d5a07e`.
**Status:** passed
**Verification refresh:** The prior passing report was stale on `cmake/PreviewPackageSmoke.cmake`. All 97 truths, 27 artifact declarations, 19 links and three requirements were rechecked; no implementation plan was replayed. The changed package exclusion now covers both MBC and CGB manifests, with a renamed-CGB-payload negative control.

## Goal Achievement

### Observable Truths

The four ROADMAP success criteria and all 93 `must_haves.truths` across Plans 08-01 through 08-10 were checked. Each truth ordinal in the table is individually VERIFIED, except 08-07/T4, which is PASSED under the recorded D-062 replacement. This yields 97/97 verified truths including the accepted override.

| Source | Truths | Status | Evidence used |
|---|---:|---|---|
| ROADMAP SC1 | 1 | VERIFIED | Historical Phase 8 mapper section and type table; exact-boundary loader/read/write/reset inspection; Plan 08-01 differential and current DMG baseline. |
| ROADMAP SC2 | 1 | VERIFIED | MBC5 type rows, 9-bit bank path, RAM/rumble paths, `mbc5_bank_1ff`, Mooneye cases, API tests and focused CTest run. |
| ROADMAP SC3 | 1 | VERIFIED | MBC2 type rows, address-bit-8 decode, canonical 512-byte RAM/battery paths, Mooneye cases and focused CTest run. |
| ROADMAP SC4 | 1 | VERIFIED | Original fixture, synthetic ninth-bit mutant/control, package/install exclusions and package smoke test. |
| 08-01/T1–T13 | 13 | VERIFIED | Boundary mapper/type-table inspection, MBC1 and DMG differential, digest/benchmark records, exact-head CI and unchanged baseline/inventory evidence. |
| 08-02/T1–T10 | 10 | VERIFIED | MBC2 synthetic header/decode/echo/battery/reset/two-instance tests and differential excluding only newly added `$05/$06` rows. |
| 08-03/T1–T13 | 13 | VERIFIED | MBC5 header/banking/RAM/rumble/battery/reset and saturation tests; oversized loader tests; differential excluding only new mapper types. |
| 08-04/T1–T5 | 5 | VERIFIED | Boundary player identity and startup/replacement warning wiring, no-save session tests, limitation-copy contract and unchanged 2 MiB player cap. T2 also passes the automated boundary contract checker and its negative controls. |
| 08-05/T1–T11 | 11 | VERIFIED | Pinned fixture inventory/manifests, runner receipt/protocol, reproduction claims, fixture attributes and decision records inspected against boundary source/docs. |
| 08-06/T1–T12 | 12 | VERIFIED | Manifest/digest/PC table checks and negative controls; exact Mooneye inventory and 15-case result; evidence class and license records. |
| 08-07/T1–T3, T5–T7 | 6 | VERIFIED | Forbidden-fixture scans and self-tests, extracted preview package smoke, hosted fixture reproduction and exact-head CI. The actual scanner contains the `mooneye-installed` diagnostic despite a query pattern false negative. |
| 08-07/T4 | 1 | PASSED (override) | Accepted D-062 replaces the non-discriminating `rom_64Mb` mutant criterion with the original `mbc5_bank_1ff` fixture and ninth-bit mutant/control. `rom_64Mb` remains a loader/install ceiling case. |
| 08-08/T1–T7 | 7 | VERIFIED | Original ROM fixture digest/rebuild, guest markers, both bank-write orders, rumble masking, synthetic 8 MiB `$1FF` test, fixture scope and unchanged inventory. |
| 08-09/T1–T9 | 9 | VERIFIED | Public docs and support ledger checked against source, fixtures, tests and dated decisions; the support-to-evidence Markdown link was resolved at the immutable Phase 8 boundary. |
| 08-10/T1–T6 | 6 | VERIFIED | Exact Phase 8 boundary commits establish privacy, CI, PR, route and phase-pause facts. These are recorded as point-in-time facts, not asserted from live routes or current ancestry. |

**Score:** 97/97 truths verified (0 present, behavior-unverified; 1 accepted override).

The Phase 8 mapper is one delimited section in `src/core/gabbaboy.c`, with fixed-width per-instance mapper state, a static type table, and switch dispatch. Loader validation precedes allocation and commit; read/write paths dispatch by stored mapper kind; reset clears registers without clearing cartridge RAM. MBC2 `$05/$06` and MBC5 `$19–$1E` have tested header limits, bank decode, RAM behavior and battery semantics. MBC5’s ninth bank bit is exercised with a real CPU/bus guest after inflating the in-memory ROM to 8 MiB. Historical DMG differential runs show zero differences for the old supported types.

### Plan matcher notes

The installed artifact query directly matched 21 of 27 declarations and the key-link query directly matched 11 of 19 at the live tree. The remaining results were manually traced against the source and time boundary each declaration describes; they were not silently counted as matcher passes:

- Six link patterns use a function or symbol in the `from` field where the matcher requires a relative file path: two in 08-01 and one each in 08-02, 08-03, 08-04 and 08-08. I traced each caller-to-target path in the actual core, test or fixture source. One 08-09 link is a relative Markdown link from `docs/support/unreleased.md`; at the Phase 8 boundary it resolves to `../mbc2-mbc5-evidence.md`. The current support files were edited later, so the 08-09 and 08-10 mutable-document links are both checked only at the immutable Phase 8 boundary, as their truths require.
- The six artifact query misses are localized: 08-04's historical `battery_unsupported` symbols were later superseded by Phase 9 persistence code; the boundary player contract checker verifies the original startup/replacement warning and save suppression. In 08-07 the scanner composes `mooneye-installed` from its default label and suffix, and the ninth-bit mutant library plus its two CTests are registered in `tests/CMakeLists.txt` rather than the declared `tests/acceptance/CMakeLists.txt`; the current CTest receipt contains both mutant tests. The two 08-10 handoff artifacts were verified at boundary `96d5eec...`, where STATE and continuation recorded `/gsd-verify-work 8`, named Phase 9 as not started and kept both auto-advance flags false. Later route, merge and persistence changes do not rewrite those historical facts.
- The 08-07 ninth-bit discriminator deviation is separately covered by the accepted D-062 override: the plan's Mooneye `rom_64Mb` mutant premise is false because the guest never selects bank `$100+`; the original `$1FF` guest and its mutant/control pair exercise the ninth bit through the CPU and bus.

| Plan | Artifact matcher | Key-link matcher | Manual resolution |
|---|---:|---:|---|
| 08-01 | 3/3 | 0/2 | Both `from` patterns name functions rather than paths; loader and mapper call sites were traced. |
| 08-02 | 2/2 | 1/2 | Remaining `from` pattern names the MBC2 decode function; test-to-code path was traced. |
| 08-03 | 4/4 | 1/2 | Remaining `from` pattern names the bank-composition expression; source and bank tests were traced. |
| 08-04 | 0/2 | 0/1 | Current-head patterns were affected by later player work; exact boundary source, tests and automated contract checker verified the promised behavior. |
| 08-05 | 3/3 | 2/2 | No residual mismatch. |
| 08-06 | 3/3 | 2/2 | No residual mismatch. |
| 08-07 | 1/3 | 2/2 | Scanner diagnostic is composed from the default label; ninth-bit mutant CTests are registered in `tests/CMakeLists.txt`, outside the declared path. Their actual registration and current test cases were checked. D-062 separately replaces the non-discriminating Mooneye premise. |
| 08-08 | 3/3 | 1/2 | Remaining `from` pattern names a test helper; guest-to-core path was traced. |
| 08-09 | 2/2 | 2/3 | The support-to-evidence Markdown link resolves at the immutable Phase 8 boundary; the live support files were edited later. |
| 08-10 | 0/2 | 0/1 | Mutable route/PR criteria were checked only at the exact historical boundary commit. |
| **Total** | **21/27** | **11/19** | **All non-matching results resolved against historical or current source evidence.** |

## Required Artifacts

| Artifact group | Status | Details |
|---|---|---|
| `src/core/gabbaboy.c`, public header, runner | VERIFIED | Substantive mapper/type table, load validation, mapper read/write/reset dispatch, battery calls and rumble API; runner selects the digest-pinned Mooneye suite. |
| `tests/test_mbc2.c`, `tests/test_mbc5.c`, `tests/test_mbc5_internal.c`, player tests | VERIFIED | Registered and exercised. The refreshed core CTest receipt passes 1,144/1,144 cases with zero skips; the separate rebuilt player receipt passes 98/98. Named MBC2/MBC5 and mutant tests are present in the core JUnit. |
| Mooneye MBC and original MBC5 fixtures | VERIFIED | Manifests, digests, licensing/source notes, compiled oracle table, reproduction and forbidden-install/package scans are connected to tests. |
| Player limitation copy and status warning | VERIFIED | Exact boundary startup and replacement paths set the status/title and emit the warning; unsupported battery types are blocked from save/lock/recovery paths. The checker enforces the pinned limitation copy and has five negative controls. |
| Preview-package extraction and fixture exclusion | VERIFIED | The current package smoke scans both MBC and CGB manifests, enforces the exact allowed fixture directories, rejects a renamed CGB ROM by digest, removes the planted file, then runs relocated consumers. The full regression receipt and `LastTest.log` show this path passed. |
| Plan-declared artifacts | 21/27 matcher passes; all manually resolved | The six path/pattern misses and their evidence are described above. No required behavior is missing. |

## Key Link Verification

| Link group | Status | Evidence |
|---|---|---|
| Type-table rows → loader classification and validation | WIRED | Each accepted type is looked up once; table limits and feature flags feed the loaded per-instance cart state. |
| Stored mapper kind → ROM/RAM reads and writes | WIRED | Core read/write paths dispatch through the same mapper kind; bank and RAM masks are exercised by unit tests and guests. |
| Mapper state → reset and battery API | WIRED | Reset helper clears mapper registers only; MBC2/MBC5 battery tests cover import/export normalization, errors, generation and instance isolation. |
| MBC5 rumble register → public host query | WIRED | `$4000–$5FFF` write path stores the line and counts transitions; tests cover masking, saturation, reset/load and absent-rumble results. |
| Mooneye manifest → runner suite and compiled case table | WIRED | Digest-selected suite, PC/size/digest/budget table comparison, mutation controls and pinned 15-case receipt. |
| Install/package artifacts → forbidden-fixture scanner | WIRED | Install tree scan, extracted preview smoke and macOS staged-package script all invoke the scanner; negative controls assert failure on planted content. |
| Extracted preview package → MBC/CGB manifests and renamed-payload control | WIRED | `cmake/PreviewPackageSmoke.cmake` passes both manifests to the scanner, copies a CGB ROM to `share/payload.bin`, requires the digest rejection, removes the file before consumer execution, and preserves the exact fixture-directory allowlist. |
| Player ROM classification → save suppression and status | WIRED | Boundary source routes `$06/$1B/$1E` through unsupported battery classification; session tests check no files, and the automated contract checks startup/replacement status and stderr wiring. |
| Plan-declared key links | WIRED | 19/19 traced. CLI directly matched 11; eight pattern-shape failures were manually traced as documented above. |

## Data-Flow Trace

| Value | Source and path | Produces real data | Status |
|---|---|---|---|
| MBC2/MBC5 guest RAM | Guest writes → mapper RAM → canonical battery image export/import | Yes; exact-length, normalization, no-op generation and error atomicity are tested. | FLOWING |
| MBC5 rumble state | Guest register writes → per-instance transition state → `gbb_rumble_state` outputs | Yes; public API and internal saturation behavior have focused tests. | FLOWING |
| Player unsupported-battery status | Loaded cartridge type → session classification → status/title and stderr warning | Yes; boundary source contract and session tests cover classification and wiring. No pixel-rendering claim is made. | FLOWING |
| Mooneye result | Manifest-selected fixture → runner callback/result-PC oracle → per-case receipt | Yes; all 15 eligible cases and PC-table controls pass. | FLOWING |
| Preview package fixture exclusion | Extracted package bytes → MBC/CGB manifest sizes and digests → clean-tree and renamed-CGB rejection | Yes; the fresh `preview_package_smoke` output records the renamed-payload rejection and package consumers pass. | FLOWING |

## Behavioral Spot-Checks

| Behavior | Command/evidence | Result | Status |
|---|---|---|---|
| Fresh configured core regression | `build/08-package-refresh-regression.xml` and `.log` | 1,144/1,144 test cases; zero failures, errors or skips. Includes all MBC2/MBC5 cases, both ninth-bit mutant controls, install scans and `preview_package_smoke`. | PASS |
| Rebuilt player regression | `build-player/08-package-refresh-player.xml` and `.log` | 98/98 test cases; zero failures or skips. | PASS |
| Separate installed-package consumers | `build/08-package-refresh-consumers.xml` | 5/5 installed consumer and runner cases; zero failures or skips. This is a separate stream, not part of the 1,144-case core run. | PASS |
| Changed CGB package exclusion | `build/Testing/Temporary/LastTest.log`, `preview_package_smoke` | The current test logs `Extracted package renamed CGB fixture rejected by digest`, then reports relocated C/C++ consumer smoke success. The extracted fixture tree contains only `mbc1-continuation`, `tracer` and `visible-demo`; the temporary `share/payload.bin` is removed. | PASS |
| MBC2/MBC5 oracle and ninth-bit controls | Core JUnit named cases | All seven `mooneye_mbc_case_mbc2_*` and eight `mooneye_mbc_case_mbc5_*` cases pass; `mbc5_bank_1ff`, `mbc5_ninth_bit_mutant_bank_1ff` and `mbc5_ninth_bit_mutant_control_below_100` pass. | PASS |
| Current frozen DMG baseline | `bash tests/scripts/verify-dmg-baseline.sh --build-dir build` | 313 inventory keys; 15 Mooneye, 20 acceptance and 2 bench rows; `baseline changes=ok rows=0`, `baseline status=pass`. | PASS |
| Frozen test-name inventories | `verify-dmg-baseline.sh --junit … --inventory core|player` | 258/258 core names and 55/55 player names match the frozen inventories. The combined core-and-consumers XML is used for identity checking only; test counts come from the separate stream receipts above. | PASS |
| Phase 8 automated closure and historical player contracts | `verify-phase8-closure-contract.py --self-test`; `verify-phase8-player-contract.py --self-test`; `verify-uat-closure.py … --self-test` | Historical boundary checker passes across 65 immutable files and rejects 157 controls; player contract rejects five controls; canonical UAT checker passes 34 automated deliverables with 19 rejected controls. | PASS |
| Ten SUMMARY coverage schemas | `verify-summary-coverage.py --self-test` and each of ten `--file` checks | 12 negative controls pass; all ten Phase 8 summaries pass, and their original bodies match committed versions byte-for-byte. | PASS |
| Historical Phase 7 → Phase 8 differential, Plan 08-01 receipt at boundary `96d5eec` | Immutable `08-01-SUMMARY.md` and evidence ledger; base `5673bed`; 86,016 loader cells plus seeded MBC1 reads/writes | 0 differences; old and new output SHA-256 both `d171c90db94218aa0378d457578657bd9e8bbdf94745f1a83f91f717307800b6`. This corrects the prior report's transcription ending `800b5`; the immutable receipt ends `800b6`. | PASS |
| Historical MBC2 exclusion differential, Plan 08-02 boundary `689a86e` | Same harness with `--exclude-types 05,06`; 85,344 cells | 0 differences; equal SHA-256 `b25b2024300bcb30d74369ad39dbc855cf7018d9fbd522573ffb00b9c696e6e8`. | PASS |
| Historical Phase 8 boundary differential `96d5eec` | Same harness excludes newly added `$05/$06,$19–$1E`; 83,328 cells | 0 differences; equal SHA-256 `15f93a2cc01db5406683ea8e786d44c540f9a7d3628935ee48d12af17e28b52b`. | PASS |
| Player warning and limitation contract | `python3 tests/scripts/verify-phase8-player-contract.py --self-test` | Boundary `96d5eec...` source contract passed; fail-first controls detected removed warning, changed pinned copy, removed replacement branch, removed status call and removed stderr call. | PASS |
| Exact-head required CI and fixture reproduction | Required CI run `38155767928` and fixture run `38155768038`, both at `a3f27f71...` | Eight required jobs and four fixture-reproduction jobs report success at the exact recorded head. | PASS |

The differential is intentionally evaluated at the historical phase boundaries and excludes only mapper types introduced by that boundary. It does not compare current Phase 9/10 behavior against the old core.

## Probe Execution

Not applicable: Phase 8 declares no `probe-*.sh` scripts. The core, player and installed-package CTest receipts above are the runnable behavioral evidence.

## Requirements Coverage

| Requirement | Source plans | Status | Evidence |
|---|---|---|---|
| CART-01 | 08-01, 08-09, 08-10 | SATISFIED | Type-table seam, unchanged legacy mapper behavior, boundary differential and DMG baseline pass. |
| CART-02 | 08-03 through 08-10 | SATISFIED | MBC5 header/banking/RAM/rumble tests, original `$1FF` guest and 8/8 Mooneye cases; install/package exclusions. |
| CART-03 | 08-02, 08-04 through 08-10 | SATISFIED | MBC2 address decode, RAM/battery tests and 7/7 Mooneye cases; player explicitly reports unsaved progress for unsupported battery types. |

No Phase 8 requirement is orphaned. CART-04 through CART-06 belong to Phase 9 and are outside this phase goal.

## Test Quality Audit

| Test set | Linked requirement | Active evidence | Provenance and assertion strength | Verdict |
|---|---|---|---|---|
| `tests/test_mbc2.c` and seven Mooneye MBC2 cases | CART-03 | Named MBC2 tests and all seven derivative cases appear in the zero-skip core JUnit. | Synthetic header/RAM/battery tests assert exact bank values, canonical bytes, unchanged generations and instance isolation; Mooneye fixtures and expected PCs come from the pinned upstream manifest. | PASS |
| `tests/test_mbc5.c`, `tests/test_mbc5_internal.c`, original guest and eight Mooneye MBC5 cases | CART-02 | Mapper, RAM, rumble, reset, boundary, `$1FF` guest and both mutant/control cases pass in the core JUnit. | Exact value/state assertions; the `$1FF` marker is explicitly harness-supplied, while the upstream MBC5 suite is an independent author-attested oracle. | PASS |
| Differential harness and frozen DMG baseline | CART-01 | Historical 86,016-cell old-core differential reports zero differences; current baseline reports zero changed rows. | The legacy source is pinned at `5673bed`; expected output is not generated from the new mapper. | PASS |
| Install and preview-package scans | CART-02 | Install, extracted-package, symlink and renamed-payload controls pass; the fresh preview smoke logs the CGB digest rejection. | Expected fixture identities come from pinned manifests; negative controls use actual fixture bytes under a renamed path. | PASS |

Disabled-test scan: no disabled or skipped tests were found in the requirement-linked MBC, fixture and package tests, and the three current JUnit receipts report zero skips. Circular-test scan: no expected output is generated by the mapper under test; fixture rebuild scripts compare against pinned upstream or committed source artifacts. Assertions are value-level or multi-step behavioral checks, not symbol-presence-only checks.

## Plan Prohibitions

The 15 legacy must-not statements across Plans 08-01 through 08-10 were checked against the Phase 8 source boundary, current tests, package scans, fixture/documentation records and exact-boundary handoff contract. The plans predate typed `verification` metadata for prohibitions, so these checks are recorded here rather than silently treating missing metadata as proof.

| Plan | Prohibition theme | Evidence checked | Status |
|---|---|---|---|
| 08-01 | No baseline or inventory edits to mask a difference; no performance or hardware overclaim | Frozen baseline output, historical differential and evidence ledger | VERIFIED |
| 08-02 | Preserve canonical MBC2 battery bytes; do not claim packed 256-byte save support | MBC2 normalization/idempotency tests and cartridge documentation | VERIFIED |
| 08-03 | Do not present rumble state as physical haptics; preserve old error classes for non-MBC5 types | Documentation, rumble API tests, differential and baseline | VERIFIED |
| 08-04 | Name unsupported persistence to users and never write unsupported cartridge saves | Immutable player-contract test and its five fail-first controls | VERIFIED |
| 08-05 | Do not claim game/CGB/hardware compatibility; do not commit build byproducts or unlicensed artwork | Evidence ledger, fixture source/license records, boundary tree | VERIFIED |
| 08-06 | Preserve installed-test naming and the expected-test inventory | Immutable boundary closure check and frozen inventory controls | VERIFIED |
| 08-07 | Keep the MBC fixture corpus out of install and package artifacts | Fresh install/package scans, renamed MBC/CGB controls and exact fixture allowlist | VERIFIED |
| 08-08 | Keep the original `$1FF` marker classified as a harness-supplied software oracle | Fixture manifest, evidence ledger and live CPU/bus tests | VERIFIED |
| 08-09 | Keep docs from claiming game, CGB, hardware or physical-rumble qualification | Phase-boundary documentation closure contract | VERIFIED |
| 08-10 | Do not merge before verification or advance phases/auto flags early | Exact Phase 8 boundary STATE/continuation contract | VERIFIED |

No prohibition violation or unresolved item was found.

## Decision Coverage

The non-blocking decision-coverage gate reports **34/34** trackable Phase 8 CONTEXT decisions honored by the plans, summaries, implementation, tests and documentation; no unhonored decision was reported.

## Review, Security and Validation Evidence

These artifacts were **reused under the project reuse policy**, not freshly rerun for this refresh. `08-REVIEW-DISPOSITION.md` records 0 open findings out of 5: WR-01 and IN-01 fixed, WR-02 deferred to Phase 9, and IN-02/IN-03 skipped. The original review status was `issues_found`, so this report relies on the disposition rather than treating that initial status as clean. `08-SECURITY.md` records 41/41 threats closed, 0 open at `96d5eec`. `08-VALIDATION.md` records V-01 through V-27 green at that boundary and the historical CI run. No UI-SPEC exists. The automated status contract checker addresses the former presentation-copy concern without inventing manual UAT.

## Anti-Patterns Found

| Scope | Result | Details |
|---|---|---|
| Phase 8 implementation files at boundary and refreshed package input | None found | The prior boundary scan covered 59 non-planning files; the changed `cmake/PreviewPackageSmoke.cmake` and `cmake/ScanForbiddenFixtures.cmake` were also scanned for debt markers, placeholder copy and empty implementations. No unresolved markers or stubs were found. Routine guard returns were not classified as stubs. |

## Human Verification Required

None. The status text and warning are deterministic source contracts and have a checker with negative controls, consistent with project decision D-069. This does not claim visual pixel validation, physical rumble/hardware behavior, CGB behavior, or commercial game compatibility.

## Recorded Limits (not gaps)

- The Mooneye fixtures carry upstream author-attested hardware evidence but run here on the bootless DMG-CPU-B profile. They do not establish model-specific, CGB, or game-compatibility claims; the MBC2A variant caveat remains documented.
- The original MBC5 `$1FF` test uses an in-memory inflated ROM and a harness-supplied marker. It is a software fixture plus synthetic oracle, not hardware evidence.
- The player supports reading MBC2/MBC5 battery-backed cartridges but does not persist their progress in this phase. Persistence was deliberately deferred to Phase 9.
- `rom_64Mb` verifies loader ceiling and package exclusion. It is not a ninth-bit bank-selection discriminator; D-062’s accepted replacement is tested.
- Reused review/security/validation conclusions reflect their recorded Phase 8 boundary and were not rerun during this verification refresh.

## Gaps Summary

No blocking or uncertain gaps remain. All roadmap criteria, plan truths, requirements, artifacts and links were checked against implementation and behavioral evidence. The sole plan-criterion deviation is the formally adopted D-062 replacement, which is covered by an override and direct ninth-bit mutant/control tests.

---

_Verified: 2026-10-21T00:26:14Z_
_Verifier: gsd-verifier_
