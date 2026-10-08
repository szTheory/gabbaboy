---
phase: GB-04-mbc1-and-safe-battery-continuation
verified: 2026-10-08T04:53:26Z
status: passed
score: 7/7 truths verified
covered_files:
  - .gitattributes
  - .github/workflows/fixture-repro.yml
  - .github/workflows/preview.yml
  - .planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-01-PLAN.md
  - .planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-01-SUMMARY.md
  - .planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-02-PLAN.md
  - .planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-02-SUMMARY.md
  - .planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-03-PLAN.md
  - .planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-03-SUMMARY.md
  - .planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-04-PLAN.md
  - .planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-04-SUMMARY.md
  - .planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-05-PLAN.md
  - .planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-05-SUMMARY.md
  - .planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-06-PLAN.md
  - .planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-06-SUMMARY.md
  - .planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-07-PLAN.md
  - .planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-07-SUMMARY.md
  - .planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-REVIEW.md
  - .planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-SECURITY.md
  - .planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-UI-REVIEW.md
  - .planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-VALIDATION.md
  - CMakeLists.txt
  - README.md
  - cmake/PreviewPackageSmoke.cmake
  - cmake/VerifyInstalledPackage.cmake
  - docs/cartridge-and-saves.md
  - docs/mbc1-evidence.md
  - docs/preview.md
  - fixtures/mbc1-continuation/LICENSE.txt
  - fixtures/mbc1-continuation/continuation.asm
  - fixtures/mbc1-continuation/continuation.gb
  - fixtures/mbc1-continuation/manifest.json
  - include/gabbaboy/gabbaboy.h
  - src/core/gabbaboy.c
  - src/player/limitations.h
  - src/player/main.c
  - src/player/session.c
  - src/player/session.h
  - tests/CMakeLists.txt
  - tests/consumers/c/main.c
  - tests/consumers/cpp/main.cpp
  - tests/expected-tests.txt
  - tests/player/CMakeLists.txt
  - tests/player/expected-tests.txt
  - tests/player/test_continuation.c
  - tests/player/test_limitations.c
  - tests/player/test_session.c
  - tests/scripts/reproduce-mbc1-continuation.sh
  - tests/scripts/verify-phase2-installed.sh
  - tests/scripts/verify-phase3-player.sh
  - tests/test_battery.c
  - tests/test_battery_fuzz.c
  - tests/test_cartridge.c
  - tests/test_loader.c
covered_digest: "v3:sha256:304bee7d050ee8a1a17d44801e9a2c9007fa2c6b094196abf9a17d49ef6a2411"
behavior_unverified: 0
overrides_applied: 0
decision_coverage:
  honored: 16
  total: 16
  not_honored: []
re_verification:
  previous_status: gaps_found
  previous_score: 6/7 truths verified
  gaps_closed:
    - The public evidence ledger now identifies the exact tested source head, passing CI/fixture/package run IDs, receipt hashes, and links to the validation record.
  gaps_remaining: []
  regressions: []
---

# Phase 4: MBC1 and Safe Battery Continuation Verification

**Phase Goal:** As a player, I want to resume supported MBC1 games from battery saves, so that failures preserve my last good progress.
**Verified:** 2026-10-08T04:53:26Z
**Status:** passed
**Re-verification:** Yes — after the evidence-ledger gap was closed.

## User Flow Coverage

| Step | Expected | Evidence in codebase | Status |
|---|---|---|---|
| Load a declared MBC1 cartridge | Supported type/ROM/RAM combinations load and bank correctly; excluded headers fail explicitly without replacing active state. | `src/core/gabbaboy.c` validates the MBC1 matrix before replacing the active machine and maps ROM/RAM registers on bus access. `loader_mbc1_matrix`, `loader_mbc1m_variant`, `loader_non_destructive`, `cartridge_bank_matrix`, and `cartridge_ram_banks` pass. | VERIFIED |
| Save and restore bounded battery bytes | Callers can export/import exact supported RAM sizes; invalid buffers and malformed save envelopes do not mutate live state. | Public contract in `include/gabbaboy/gabbaboy.h`; core battery tests cover 8/32 KiB, canaries, errors, no-battery cartridges, lifecycle, instance isolation, and bounded fuzz. Player envelope validation checks identity, type, length, and CRC before import. | VERIFIED |
| Preserve the last good save across failure | Writes use a same-directory temporary, synchronization, and atomic replacement; failures are surfaced and transition choices remain explicit. | `src/player/session.c` atomic-save/recovery/lock paths and `src/player/main.c` status/transition paths; fault, interruption, lock, cadence, and transition-choice tests pass. Directory-sync failure after rename is reported as durability uncertainty. | VERIFIED |
| Reopen meaningful progress in a fresh process | The original guest resumes from saved bytes and reaches a progress-dependent marker; missing, wrong-identity, and altered-save controls remain distinct. | `tests/player/test_continuation.c` launches a child process, reopens the save in a fresh instance, and checks guest markers. Fixture digest test and pinned RGBDS reproduction pass; exact-head player-package smoke also resumes in a fresh process. | VERIFIED |

The centralized MVP guard returned valid=true for the normalized user story and confirmed mode=mvp. These are automated software acceptance results. No physical MBC1/DMG observation or power-loss qualification is claimed. The ledger now distinguishes the tested source-and-fixture SHA from the separate closeout-document revision, which still requires exact-head checks before merge.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---:|---|---|---|
| 1 | Declared standard MBC1 ROM/RAM/battery configurations exhibit expected banking and enable behavior; excluded variants and other mappers return explicit errors. | VERIFIED | Core descriptor/header validation, mapper access paths, and named loader/cartridge matrix tests passed; the selected local run passed all 15 focused mapper, loader, and battery tests. |
| 2 | A frontend can import/export bounded battery data under documented identity/size rules, and malformed imports leave live state unchanged. | VERIFIED | Public header contract, core error/canary tests, seeded fuzz case, installed C/C++ consumers, and player reject matrix. Exact hosted native and installed inventories passed. |
| 3 | The player follows documented atomic replacement, recovery, and concurrent-writer rules; failed writes preserve the last good save and visibly report failure. | VERIFIED | Session implementation is wired to player transitions. Fault injection covers write/sync/rename and interruption boundaries; transition tests cover retry/continue/cancel and persistent failure status. Hosted macOS player/package job passed. No storage power-loss inference is made. |
| 4 | An original GB fixture saves, exits, reopens in a fresh instance/process, and resumes behavior dependent on prior bytes; empty/wrong-save controls demonstrate a meaningful continuation oracle. | VERIFIED | Authored fixture source/ROM and manifest are digest-pinned; fixture reproduction and fresh-process positive plus missing-save, wrong-ROM, and altered-payload controls pass. Exact-head fixture and player package runs passed. |
| 5 | The integrator guide explains MBC1 support, API ownership, save identity/format/recovery/concurrency, and evidence limits. | VERIFIED | `docs/cartridge-and-saves.md` is substantive and matches implementation; evidence classes and explicit exclusions are also present in the MBC1 ledger. |
| 6 | Phase closeout cites current executed cases, package/consumer results, and exact hosted revision without a physical-hardware claim. | VERIFIED | `04-VALIDATION.md` records source SHA, current PR head, all three exact pull-request run IDs, job conclusions, package hashes/receipts, and the hardware/power-loss limits. Live GitHub run metadata was checked against the same head. |
| 7 | The public evidence ledger presents the current exact-head hosted evidence consistently with the validated closeout. | VERIFIED | `docs/mbc1-evidence.md` now names exact source SHA `79f83f627ffb3631811b2f39b23081117ebaab8f`, successful runs `37728192665`, `37728192634`, and `37728192674`, package receipt hashes, and links to `04-VALIDATION.md`. It explicitly says its separate final closeout revision still requires exact-head checks before merge. Live PR and run metadata were rechecked. |

**Score:** 7/7 truths verified; the four roadmap success criteria are 4/4 verified.

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `src/core/gabbaboy.c` | Validated MBC1 matrix, bus banking, bounded non-destructive load/import | VERIFIED | Substantive implementation; loader and bus paths are used by production API and tested. |
| `include/gabbaboy/gabbaboy.h` | Public battery ownership, bounds, and error contract | VERIFIED | Documents caller-owned buffers, exact sizes, and failure behavior consumed by installed C/C++ tests. |
| `src/player/session.c`, `src/player/main.c` | Safe save lifecycle, recovery, visible error, and final-transition decisions | VERIFIED | Session status and persistence paths are connected to player actions; fault and transition tests exercise them. |
| `tests/player/test_continuation.c`, fixture files and manifest | Independent fresh-process continuation oracle with negative controls and reproducible bytes | VERIFIED | Tests consume the authored fixture; pinned reproduction rebuilds and compares checked-in bytes. |
| `docs/cartridge-and-saves.md` | Public contract aligned with implemented support | VERIFIED | Present, substantive, and source-reviewed. |
| `docs/mbc1-evidence.md` | Current SAVE traceability, exact revision, and honest evidence limits | VERIFIED | Now records the exact tested source head, all three successful run IDs, package hashes, a link to validation, and the separate pending gate for the final documentation revision. |
| `.planning/phases/GB-04-mbc1-and-safe-battery-continuation/04-VALIDATION.md` | Executed local and exact hosted evidence, receipts, and limits | VERIFIED | Exact final head and results are recorded; package digests and qualifications are explicit. |

The OpenGSD `verify.artifacts` and `verify.key-links` queries returned total=0 for each plan because their frontmatter uses plain scalar lists where the query expects structured artifact/link mappings. I therefore checked artifact existence, substance, and wiring manually; the ledger content issue remains a real failure rather than being hidden by the empty query result.

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| ROM header | MBC1 descriptor and bank state | Validation before machine replacement; mapper registers consumed by bus reads/writes | WIRED | Core loader and bus paths implement matrix validation, bank selection, and RAM gating; focused tests pass. |
| Guest RAM writes | Battery export/import API | Instance RAM buffer and generation tracking | WIRED | Guest writes update RAM; public battery operations copy bounded bytes and preserve state on errors. |
| Save file | Active cartridge RAM | Bounded envelope parse, identity/CRC validation, then core import | WIRED | Session rejects invalid envelopes before import; tests verify rejected files and live RAM preservation. |
| Dirty battery state | Durable save target | Temp file, full write, sync, close, validation, atomic rename | WIRED | Player persistence is invoked on cadence and final transitions; injected failure cases assert old-or-complete-new outcomes. |
| Fresh process | Continuation guest assertion | Reopen exact fixture identity and bytes before guest execution | WIRED | Child-process positive and negative controls assert distinct guest markers. |
| Phase evidence | Public MBC1 ledger | Current run/revision record | WIRED | The ledger links to validation and identifies the exact tested SHA, run IDs, and package hashes while qualifying the unchecked final documentation head. |

### Data-Flow Trace

| Artifact | Data | Source | Produces real data | Status |
|---|---|---|---|---|
| MBC1 core | Selected ROM/RAM bank bytes | Loaded cartridge bytes and guest mapper-register writes | Yes | FLOWING |
| Battery export/import | Battery RAM payload | Live per-instance cartridge RAM and caller/file bytes | Yes | FLOWING |
| Save envelope | Persisted battery bytes | Core export, identity metadata, bounded checksum envelope | Yes | FLOWING |
| Player status | Save success/failure and dirty state | Session result and save-generation state | Yes | FLOWING; surfaced through window title/help/error choices, with visibility concerns noted in advisory UI review |

### Behavioral Spot-Checks

| Behavior | Command/evidence | Result | Status |
|---|---|---|---|
| Focused MBC1, loader, and battery behavior | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(cartridge_tracer|cartridge_bank_matrix|cartridge_ram_banks|cartridge_no_ram_reads|loader_mbc1_matrix|loader_mbc1m_variant|loader_non_destructive|battery_roundtrip8|battery_roundtrip32|battery_errors|battery_no_battery|battery_lifecycle|battery_instances|battery_api_fuzz|mbc1_continuation_fixture_digest)$'` | Re-run during re-verification: 15/15 passed, 0.11 seconds | PASS |
| Final exact-head required and native CI | PR pull-request run 37728192665 at 79f83f627ffb3631811b2f39b23081117ebaab8f | Rechecked live: all seven required/native/sanitizer/player jobs passed, no job skipped | PASS |
| Fixture reproducibility | PR pull-request run 37728192634 at the same SHA | Rechecked live: fixture reproduction and original/candidate Mooneye reproduction jobs passed, including byte-identical MBC1 fixture reproduction with pinned RGBDS 1.0.1 | PASS |
| Downloaded installed/player consumers | PR pull-request run 37728192674 at the same SHA | Rechecked live: aggregate, Linux installed consumer, macOS installed consumer, and downloaded macOS player consumer passed; receipts name the same source SHA | PASS |

The exact GitHub run metadata was checked independently and agrees with the validation record. Local validation also records 155/155 core, 160/160 relocated installed, 155/155 installed core-only, and 37/37 macOS player/package cases. No CI log download is claimed. The final source tree is unchanged from the clean review target: `git diff 95c076d 79f83f627ffb3631811b2f39b23081117ebaab8f` is empty.

### Probe Execution

Not applicable: this is a cartridge/player feature phase, not a migration or tooling phase, and its plans do not declare probe scripts or probe-based success criteria.

### Requirements Coverage

| Requirement | Source plans | Description | Status | Evidence |
|---|---|---|---|---|
| SAVE-01 | 04-01, 04-02, 04-07 | Supported MBC1 matrix and explicit excluded-cartridge errors | SATISFIED | Loader/cartridge implementation, synthetic matrix tests, exact hosted required CI. |
| SAVE-02 | 04-01, 04-02, 04-06, 04-07 | Bounded battery API and non-mutating malformed operations | SATISFIED | Core API/error/fuzz tests and relocated C/C++ consumer inventories. |
| SAVE-03 | 04-01, 04-03, 04-04, 04-05, 04-06, 04-07 | Safe player save identity, atomic replacement, recovery, writer coordination, and failure reporting | SATISFIED | Session/fault/lock/cadence/transition tests, exact macOS package smoke, security review. |
| SAVE-04 | 04-05, 04-06, 04-07 | Original fixture with fresh-process continuation and meaningful controls | SATISFIED | Fixture digest/reproduction, continuation tests, exact hosted fixture and package runs. |

All four requirements are assigned by plans and mapped in REQUIREMENTS.md. There are no orphaned Phase 4 requirements. The ledger discrepancy found in the first verification was a closeout-document gap and did not negate the current implementation or named execution evidence; the ledger is now corrected.

### Decision Coverage

OpenGSD context decision coverage reports 16/16 honored, with no unhonored decisions. The implementation/docs preserve the declared mapper boundary, ownership, identity, recovery, concurrency, fixture, and evidence-class decisions.

### Advisory (New Scope, Unevidenced)

None. Re-verification found no new-scope concerns lacking deterministic evidence.

### Anti-Patterns Found

None. The prior stale hosted-evidence instructions were removed and replaced with exact run/receipt records and an explicit final-documentation-head check. The original source review remains clean.

The source review at the final source tree reported 0 critical, warning, and informational findings across 26 files. No actionable TODO/FIXME/TBD/XXX/placeholder markers or stub implementations were found in the reviewed implementation and test files. The security review reports 22/22 threats closed and none open. The code-only UI review is advisory (13/24); it notes transient/title-only save status and keyboard-only final-save choices. It did not test a visual screenshot, and no perceptual or hardware claim is inferred from it.

### Human Verification Required

None for the automated software acceptance scope. Physical MBC1/DMG behavior and storage power-loss durability remain expressly unqualified; they are not represented as passed evidence or added as invented manual UAT. The existing UI audit remains advisory.

### Gaps Summary

The player and core satisfy all four roadmap success criteria, and SAVE-01 through SAVE-04 have implementation and execution evidence. The prior ledger gap is resolved: the public ledger now identifies the exact tested source head, all three passing workflow runs and package hashes, and links to detailed validation. Directly rechecked GitHub metadata confirms those runs remain successful on the exact PR source head; the focused MBC1/loader/battery selection passed 15/15. The ledger clearly states that a separate final documentation revision still requires its own exact-head checks before merge, so no unchecked documentation revision is claimed green. No verification gaps remain.

---

_Verified: 2026-10-08T04:53:26Z_
_Verifier: the agent (gsd-verifier)_
