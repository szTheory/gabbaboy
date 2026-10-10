---
phase: GB-03-visible-interactive-dmg
slug: visible-interactive-dmg
status: verified
threats_open: 0
asvs_level: 1
created: "2026-10-07"
---

# Phase 3 — Security

> Phase threat audit against all executed Phase 3 plan registers. The configured blocking threshold is high; all 40 declared threat IDs are now closed.

## Trust Boundaries

| Boundary | Description | Data Crossing |
|-----------|-------------|---------------|
| Guest ROM and fixture → core | Untrusted guest bytes and guest-controlled addresses enter bounded core state. | ROM bytes, bus addresses, opcodes, timestamps |
| Public core API → caller memory | Caller-owned buffers and event batches cross the opaque instance boundary. | Frame buffers, event arrays, capacities, timestamps |
| SDL player → core | Host input, file selection, and timing are translated by the optional adapter. | Key events, ROM paths/bytes, host counter values |
| CI/source/artifact supply chain → package | Source, tool archives, packages, and workflow actions are pinned and verified before use. | Checkout SHA, SDL/RGBDS archives, package bytes, licenses, run receipts |

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation / evidence | Status |
|-----------|----------|-----------|----------|-------------|-----------------------|--------|
| T-03-01 | Tampering | Frame copy API | high | mitigate | Checked capacity, pitch, and extents; canary tests (`src/core/gabbaboy.c:962-982`, `tests/test_ppu.c:657-697`). | closed |
| T-03-02 | Denial of service | Renderer and input queue | high | mitigate | Fixed per-instance arrays and budget-bounded guest runs (`src/core/gabbaboy.c:6-90,1378-1383`); allocation limited to create/load (`:1016,1037`). | closed |
| T-03-03 | Tampering | Owned fixture | high | mitigate | Original source, rights, fixed digest, and separate reproduction checks (`fixtures/visible-demo/manifest.json:1-18`, `fixtures/visible-demo/LICENSE.txt:1-6`, `tests/scripts/reproduce-visible-demo.sh:55-100`). | closed |
| T-03-04 | Repudiation | Evidence classes | medium | mitigate | Evidence ledger separates composition, timing, and gameplay and states applicability (`docs/dmg-video-evidence.md:1-7,41-49`); test groups remain distinct (`tests/test_ppu.c`, `tests/test_tracer.c`). | closed |
| T-03-05 | Tampering | Tile/FIFO/object indexing | high | mitigate | Explicit coordinates, object counts, and fixed-array bounds (`src/core/gabbaboy.c:581-629`); composition cases and sanitizer CI (`tests/test_ppu.c:253-400`, `.github/workflows/ci.yml:84-105`). | closed |
| T-03-06 | Denial of service | LCD/fetch transitions | high | mitigate | Bounded FIFO pushes, finite object scan, fixed per-dot work, and budget-bounded runs (`src/core/gabbaboy.c:626-635,715-730,776-820,1383`). | closed |
| T-03-07 | Repudiation | Model evidence | medium | mitigate | Source applicability and evidence limits are recorded; missing claims remain gaps, and the configured ship workflow requires passed verification (`docs/dmg-video-evidence.md:3-39`, `03-VERIFICATION.md:72-76`). | closed |
| T-03-08 | Tampering | DMA addressing and OAM writes | high | mitigate | Bounded DMA source mapping and exactly 160 destination bytes (`src/core/gabbaboy.c:863-893`); boundary and finite-progress tests (`tests/test_dma.c:268-315`). | closed |
| T-03-09 | Elevation of privilege | Memory arbitration | high | mitigate | Initiator-specific CPU VRAM/OAM and DMA/HRAM checks (`src/core/gabbaboy.c:335-377,422-430,863-893`) with lockout tests (`tests/test_dma.c:320-335,529-574`). | closed |
| T-03-10 | Denial of service | DMA restart/contention | medium | mitigate | Fixed transfer state and bounded byte-per-deadline progression (`src/core/gabbaboy.c:873-895`); partition tests (`tests/test_dma.c:403-429`). | closed |
| T-03-12 | Tampering | Package installation | high | mitigate | No npm/pip/cargo manifest or ordinary-core SDL dependency; SDL is exact-version optional CMake configuration (`CMakeLists.txt:17,63-83`), with archive digest controls under T-03-23/T-03-34. | closed |
| T-03-13 | Tampering | Fixture/package admission | high | mitigate | Fixture reproducer verifies project-owned source, rights, ROM hash, and bytes (`tests/scripts/reproduce-visible-demo.sh:55-105`); ledger records no upstream fixture admission (`docs/dmg-video-evidence.md:23`). | closed |
| T-03-14 | Tampering | Input event admission | high | mitigate | Whole-batch validation precedes mutation (`src/core/gabbaboy.c:934-959`); atomic rejection tests (`tests/test_joypad.c:118-172`). | closed |
| T-03-15 | Repudiation | JOYP interrupt claim | high | mitigate | JOYP interrupt result is not asserted; unsupported behavior remains an explicit phase gap (`src/core/gabbaboy.c:430,552-569`, `docs/dmg-video-evidence.md:27-39`, `03-VERIFICATION.md:74,94-104`). The configured ship gate rejects non-passed verification. | closed |
| T-03-16 | Denial of service | Queue ordering | medium | mitigate | Fixed 64-event queue and bounded atomic admission (`src/core/gabbaboy.c:6,68,934-959`); full/invalid batch cases (`tests/test_events.c:118-180`). | closed |
| T-03-21 | Tampering | Host-to-core timestamp mapping | high | mitigate | Checked quotient/remainder conversion and overflow guards (`src/player/input.c:7-35,60-73`); boundary tests (`tests/player/test_input.c:34-66`). | closed |
| T-03-22 | Denial of service | Focus-loss release | high | mitigate | Eight queue slots reserved for releases and resume blocked on unexpected failure (`src/player/input.h:12-25`, `src/player/input.c:164-203`); capacity recovery tests (`tests/player/test_input.c:148-212`). | closed |
| T-03-23 | Tampering | SDL acquisition | high | mitigate | SDL version/digest pinned and checked before extraction (`tests/scripts/verify-phase3-player.sh:5-7,301-314`); CMake dependency remains optional (`CMakeLists.txt:17,63-83`). | closed |
| T-03-24 | Repudiation | Host input claims | medium | mitigate | SDL events are pushed and checked through guest outcomes (`src/player/main.c:629-639,780-799`); core input tests are separate (`tests/test_joypad.c:74-227`). | closed |
| T-03-25 | Tampering | ROM replacement | high | mitigate | Bounded path/file reads and validation before replacement; `read_rom_file` opens with `O_NOCTTY`, rejects non-regular or oversized files, and reports a read-bound overrun and a `close()` failure in separate branches (`src/player/session.c:80-216`, `src/core/gabbaboy.c:997-1045`); failed replacement preserves session, including the 2097153-byte read-bound and 2097154-byte cases (`tests/player/test_session.c:94-163`). | closed |
| T-03-26 | Denial of service | Presentation arithmetic | medium | mitigate | Integer-scale geometry and checked dimensions (`src/player/presentation.c:5-23`); extreme and undersized cases (`tests/player/test_presentation.c:38-55`). | closed |
| T-03-27 | Repudiation | Preview limitations | medium | mitigate | Player limitation text and package metadata are asserted in the player test inventory and downloaded-package consumer (`tests/player/test_limitations.c`, `tests/scripts/verify-phase3-player.sh:64-91`; 03-11 SUMMARY verification). | closed |
| T-03-28 | Tampering | Frame output buffer | high | mitigate | Checked extent, pointer overflow, and overlap rejection (`src/core/gabbaboy.c:962-980`); canary, overlap, padding, and reset cases (`tests/test_ppu.c:657-772`). | closed |
| T-03-29 | Tampering | Event batches | high | mitigate | Entire batch validates before final copy (`src/core/gabbaboy.c:934-959`); unchanged-state rejection tests (`tests/test_events.c:118-180`). | closed |
| T-03-30 | Denial of service | Core output/queue | medium | mitigate | Fixed frame/FIFO/DMA/queue storage, bounded runs, and allocation limited to create/load (`src/core/gabbaboy.c:6-90,1016,1037,1378-1384`). | closed |
| T-03-31 | Tampering | Installed package API | medium | mitigate | Relocated C/C++ consumers run against installed headers/library (`tests/scripts/verify-phase2-installed.sh:24-39`, `tests/consumers/c/main.c:16-52`, `tests/consumers/cpp/main.cpp:16-52`). | closed |
| T-03-32 | Tampering | RGBDS release archive | high | mitigate | Official archive digest and version checked before extraction/use (`.github/workflows/fixture-repro.yml:19-73`, `tests/scripts/reproduce-visible-demo.sh:66-75`). | closed |
| T-03-33 | Repudiation | Fixture identity receipt | medium | mitigate | Run-scoped receipt binds checkout, tool, and ROM digests (`tests/scripts/reproduce-visible-demo.sh:123-171`); workflow provides exact revision and run identities (`.github/workflows/fixture-repro.yml:74-90`). | closed |
| T-03-34 | Tampering | SDL release archive | high | mitigate | Pinned SDL digest is checked before extraction (`tests/scripts/verify-phase3-player.sh:350-359`). | closed |
| T-03-35 | Tampering | Downloaded preview package | high | mitigate | Receipt/source/package checks precede safe extraction; metadata, licenses, fixtures, and extracted executable are checked (`tests/scripts/verify-phase3-player.sh:54-184,397-419`, `.github/scripts/safe_extract_package.py:15-27,95-220`, `.github/workflows/preview.yml:110-156`). The verified archive and receipt are published as one all-or-nothing set through the boundary helper; a failure withdraws only the inodes it published (`tests/scripts/verified_player_output_dir.py:127-320`, `tests/scripts/test_verified_player_output_dir.py:180-360`, `tests/scripts/verify-phase3-player.sh:296-303`). | closed |
| T-03-36 | Elevation of privilege | GitHub Actions | high | mitigate | Read-only permissions and immutable actions; PR code runs in unprivileged `pull_request` workflows (`.github/workflows/ci.yml:3-10,125-164`, `.github/workflows/preview.yml:3-10,110-156`). | closed |

| T-03-37 | Tampering | Evidence ledger and test expectations | medium | mitigate | The ledger records source applicability and evidence classes; focused test inventory is fail-closed (`docs/dmg-video-evidence.md:1-7,39-49`, `03-VERIFICATION.md:72-76`). | closed |
| T-03-38 | Repudiation | Hardware observation claims | medium | mitigate | Ledger and verification distinguish source/software evidence from hardware; VIDEO-04 remains explicitly open pending live observation (`docs/dmg-video-evidence.md:1-7`, `03-VERIFICATION.md:74,94-104`). | closed |
| T-03-39 | Repudiation | Player limitation text and package metadata | medium | mitigate | Registered limitation assertion and extracted-package checks require both unsupported-feature fields to be literal false (`tests/player/test_limitations.c`, `tests/player/expected-tests.txt:1-70`, `tests/scripts/verify-phase3-player.sh:64-91`; 03-11 SUMMARY negative controls). | closed |
| T-03-41 | Tampering | Active-DMA FF46 write gate | high | mitigate | Bus write path admits the FF46 exception while DMA blocks other non-HRAM CPU accesses; guest regression coverage is recorded in 03-12 SUMMARY (`src/core/gabbaboy.c:335-377,422-430`, `tests/test_dma.c:529-574`). | closed |
| T-03-42 | Repudiation | DMA applicability/evidence claims | medium | mitigate | Immutable source assertions, evidence classes, and hardware/per-unit limitations are recorded (`docs/dmg-video-evidence.md:1-7,13-20,41-49`, `03-VERIFICATION.md:74,94-104`). | closed |
| T-03-43 | Tampering | JOYP IF state | medium | mitigate | Ordered selected-pin transitions OR only IF.4; tests cover sticky IF, IE independence and transition behavior (`src/core/gabbaboy.c:430,552-569`, `tests/test_joypad.c:118-227`). | closed |
| T-03-44 | Tampering | DMA/PPU scan, fetch, and CPU access | medium | mitigate | Bounded 40-entry/10-object scan, aligned OAM word fetch and DMA arbitration are exercised by overlap, mode-matrix, boundary and collision controls (`src/core/gabbaboy.c:581-629,863-893`, `tests/test_dma.c:839-1005,1086-1150`). | closed |
| T-03-45 | Repudiation | VIDEO-02/03 evidence claims | medium | mitigate | Ledger retains pinned sources, commands, confidence class and unmeasured CPU-B limitations (`docs/dmg-video-evidence.md:1-7,41-49`; 03-13 SUMMARY). | closed |
| T-03-SC | Tampering | Package installation | high | mitigate | Ordinary core remains SDL-free and the repository has no npm/pip/cargo dependency installation path; phase summaries preserve the offline-core/package legitimacy gate (`CMakeLists.txt:17,63-83`, 03-02/03-10/03-11/03-12/03-13 SUMMARY). | closed |

## Accepted Risks Log

No accepted risks. All declared threats use the mitigate disposition.

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-07 | 31 | 30 | 1 non-blocking | OpenGSD `gsd-security-auditor` |
| 2026-10-10 (freshness after Phase 06.1) | 40 | 40 | 0 | Orchestrator ASVS L1 short-circuit (plan-time register, no open threats) |

The audit found no unregistered threat flags. The summaries contain no `## Threat Flags` sections. VIDEO-02 and VIDEO-03 remain unqualified correctness/evidence gaps and are not represented as verified behavior; those gaps do not create an unmitigated security threat because the evidence and ship gates prevent unsupported claims.

## Sign-Off

- [x] All threats have a disposition.
- [x] Accepted risks documented in Accepted Risks Log (none).
- [x] `threats_open: 0` confirmed at the configured high-severity threshold.
- [x] `status: verified` set in frontmatter.

**Approval:** verified 2026-10-09

## Security Audit 2026-10-09 (refreshed)

Rechecked all 40 threat IDs from plans 03-01 through 03-13. T-03-27's later implementation and T-03-39 close the limitation assertion gap. The downloaded-package verifier now prepares its output directory through a dedicated boundary helper: it rejects overlap with the untrusted candidate, filesystem/repository roots, and directory collisions, and removes only the two expected artifact paths. Regressions cover preserving unrelated output files, symlink targets, root/candidate aliases and directory collisions (`tests/scripts/verified_player_output_dir.py:14-47`, `tests/scripts/test_verified_player_output_dir.py:23-120`, `tests/scripts/verify-phase3-player.sh:294-297`).

| Metric | Count |
|---|---|
| Threats found | 40 |
| Closed | 40 |
| Open | 0 |

## Security Audit 2026-10-10 (publication-rollback refresh)

Rechecked the register after the shared verified-output helper moved to all-or-nothing publication (`eb96902`). The register still holds 40 threat IDs, all closed, so `threats_open: 0` is unchanged. Under ASVS level 1 with a plan-time register, the workflow short-circuits without an auditor pass. The helper keeps every earlier output-directory rejection: filesystem and repository roots, repository descendants, candidate overlap and aliases, and directory collisions. It publishes the archive and the receipt bound to it through directory-descriptor-relative operations. On any failure after a name is linked, it withdraws only the inodes it published, so concurrent replacements survive and the original error is not masked. The focused helper suite passed 17/17 and the optional player suite passed 51/51 at `0403b71`. Stale line references for T-03-34 and T-03-35 were updated. No new threat was introduced. The frozen v0.1.0 tag keeps its disclosed historical deletion path; its published bytes are unchanged.

## Security Audit 2026-10-10

| Metric | Count |
|---|---|
| Threats found | 40 |
| Closed | 40 |
| Open | 0 |

## Security Audit 2026-10-10 (freshness after Phase 06.1)

Rechecked the register after Phase 06.1 PR #54 (merge `ab76d09c2ee27ba09fc5f3c2510af016aebfdecb`). The register still holds 40 threat IDs, all closed, so `threats_open: 0` is unchanged; under ASVS level 1 with a plan-time register the workflow short-circuits without an auditor pass. Covered changes and their threat bearing:

- `src/player/session.c` (T-03-25): `read_rom_file` now opens with `O_NOCTTY` and separates the size-bound and `close()` failure branches. Both still fail closed and free the buffer before replacement, so a failed read cannot replace the session. `player_session_replacement_failure` asserts the read-bound message and the unchanged session (player suite 51/51 at `4bcd27e`). The `close()` failure branch is verified by inspection only; no fault-injection stage exists for it.
- `tests/scripts/test_verified_player_output_dir.py` (T-03-35): shared receipt helper plus an inner withdrawal-site test; 21 tests OK. The helper itself (`verified_player_output_dir.py`) is unchanged.
- `tests/scripts/verify-phase3-player.sh`: comment-only change.
- `.github/workflows/ci.yml` and `.github/workflows/preview.yml` (T-03-35, T-03-36): one `player-gate` job feeds `macos-player-package` and `required-native`; the preview player job resolves the exact-head ci run through `.github/scripts/wait-exact-head-ci.py` before downloading. Triggers stay `pull_request`/`push`, permissions stay read-only, actions stay SHA-pinned, and no `pull_request_target` is used. Line references for T-03-25, T-03-35 and T-03-36 were updated.

No new threat was introduced.

## Security Audit 2026-10-10

| Metric | Count |
|---|---|
| Threats found | 40 |
| Closed | 40 |
| Open | 0 |
