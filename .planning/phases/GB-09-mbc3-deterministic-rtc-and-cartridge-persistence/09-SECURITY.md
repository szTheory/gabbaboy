---
phase: "9"
slug: "mbc3-deterministic-rtc-and-cartridge-persistence"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-10-11"
---

# Phase 9 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Host ROM bytes → `validate_header` | Untrusted header and length; MBC3 ceiling, MBC30 variant rejection, 8 MiB global bound | ROM bytes; validated before allocation |
| Guest writes → MBC3 registers / RAM window / RTC | Guest-controlled bank, RAM/RTC select, latch and clock register values | Bank numbers, RTC fields; masked before use, unmapped selections read `$FF` |
| Caller battery image → `gbb_import_battery` | RAM followed by the 21-byte RTC block | Save bytes; exact length, parse into locals, single commit |
| Host wall clock → `gbb_rtc_catch_up` | Elapsed seconds from the host (signed `int64_t`) | Negative rejected; only explicit calls advance the clock |
| Player save file → envelope v1/v2 decode | Untrusted file on disk, including `saved_at` | Lengths allow-listed before addition, exact size, CRC-32 (accident detection only) |
| `--clock-unix` argument → player | Test-only clock injection | Accepted only with battery smoke modes; `[-]digits` int64 |
| Upstream MagenTests / rtc3test / RGBDS → fixtures and CI | Third-party ROMs and toolchains | SHA-256 pinned; hosted byte-identical rebuild |
| Repository → install tree and packages | Test-only ROMs must not ship | Name-and-digest scan with self-test |
| CI evidence → completion claims | Exact-head required checks | Run ids, job conclusions |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-09-01 | Tampering | MBC3 ROM/RAM index | high | mitigate | ROM bank masked at write; RAM index masked only for `$00-$03`; `mbc3_rom_banking`, `mbc3_ram_banking`, `mbc3_unmapped_select` | closed |
| T-09-02 | DoS | `validate_header` 4 MiB ceiling | medium | mitigate | Row ceiling and ROM code checked before shift; `mbc3_header_matrix` | closed |
| T-09-03 | Tampering | MagenTests admission | high | mitigate | `VerifyFixtureManifest` size and SHA-256; MIT licence; `magentests_fixture_digest` | closed |
| T-09-04 | Info disclosure | install tree / packages | medium | mitigate | `magentests_not_installed` with self-test | closed |
| T-09-05 | DoS | fuzz harness memory | medium | mitigate | One static 8 MiB + 1 buffer (`tests/fuzz_core.c`) | closed |
| T-09-06 | Tampering | `gbb_load_rom` over-bound lengths | high | mitigate | `GBB_ROM_TOO_LARGE` before malloc; loader fuzz `MAX+1`/`SIZE_MAX`; ASan/UBSan leg | closed |
| T-09-07 | Repudiation | v0.1 corpus provenance | medium | mitigate | Manifests pin tag, commit, toolchain, digests; `--check` offline | closed |
| T-09-08 | Info disclosure | generator script / manifest | low | mitigate | Repository-relative paths; privacy grep clean | closed |
| T-09-09 | Tampering | `rtc_sync` / `rtc_add_seconds` overflow | high | mitigate | Split arithmetic, uint64 closed form; `rtc_time_near_max`, `rtc_closed_form_differential` | closed |
| T-09-10 | Tampering | out-of-range register values | medium | mitigate | Read/write masks; `rtc_out_of_range_rollover` | closed |
| T-09-11 | Repudiation | determinism claim | medium | mitigate | `no_host_clock` source + object layers; three negative controls; empty listing fails (8896725) | closed |
| T-09-12 | DoS | hot path | low | accept | RTC work only at RTC accesses | closed |
| T-09-13 | Tampering | rtc3test admission | high | mitigate | Manifest SHA-256; `rtc3test_fixture_digest` | closed |
| T-09-14 | Tampering | CI toolchain fetch | high | mitigate | RGBDS 0.6.1 archive `sha256sum --check` before `tar`; 0.4.2 from exact commit; upstream by exact SHA | closed |
| T-09-15 | Repudiation | reproduction claim | medium | mitigate | Hosted exact-head `result=byte-identical` only | closed |
| T-09-16 | Tampering | RTC block import | high | mitigate | Exact length, parse into locals, single commit; `rtc_block_corruption_matrix` | closed |
| T-09-17 | Tampering | `gbb_rtc_catch_up` arithmetic | high | mitigate | Negative rejected before cast; `rtc_catch_up_negative`, `rtc_catch_up_int64_max` | closed |
| T-09-18 | Tampering | policy delta overflow | medium | mitigate | Signed compare before unsigned diff, clamp; `catch_up_policy_table` | closed |
| T-09-19 | Spoofing | import as catch-up vector | medium | mitigate | Import re-anchors only; `rtc_import_never_advances` | closed |
| T-09-20/41/43 | Tampering | continuation toolchain archive | high | mitigate | `GBB_RGBDS_ARCHIVE_SHA256` verified before extraction; CI pin-consistency check | closed |
| T-09-21/42/44 | Repudiation | continuation guest provenance | low | mitigate | Source and ROM SHA-256 in manifests; hosted byte-identical rebuild | closed |
| T-09-22 | Repudiation | rtc3test pass claim | high | mitigate | `rtc3test_basic/range/subsecond` exact transcript; `rtc3test_negative_control` | closed |
| T-09-23 | DoS | runaway suite | low | mitigate | 60 emulated-second budget; `TIMEOUT 300` | closed |
| T-09-24 | DoS | v2 envelope lengths | high | mitigate | Allow-lists before addition, uint64 total, exact size; `player_session_v2_max_size` | closed |
| T-09-25 | Tampering | `saved_at` injection | medium | mitigate | CRC-32 over header (accident detection, documented); bounded catch-up | closed |
| T-09-26 | Tampering | partial write / crash | high | mitigate | Same-directory temp, fsync, rename; v2 fault tests | closed |
| T-09-27 | Tampering | classification drift | medium | mitigate | `player_session_classification_drift` | closed |
| T-09-28 | Tampering | loader partial mutation | high | mitigate | Guard instance after every rejection; ASan/UBSan leg | closed |
| T-09-29 | DoS | matrix memory | low | mitigate | One reused 8 MiB + 1 buffer | closed |
| T-09-30 | Repudiation | test strength | medium | mitigate | Five configure-time mutants with exactly-once anchors and paired controls | closed |
| T-09-31 | Spoofing | `--clock-unix` in normal play | medium | mitigate | Battery smoke modes only; `[-]digits` parse (19deb6b); `player_session_clock_flag_scope` | closed |
| T-09-32 | Tampering | rollback / future timestamps | medium | mitigate | `CLOCK_EARLIER` no action; rollback and no-clock continuation tests | closed |
| T-09-33 | Tampering | repeated catch-up | medium | mitigate | `catch_up_done` per open; re-stamp on save | closed |
| T-09-34 | Repudiation | evidence overclaim | medium | mitigate | `mbc3_rtc_evidence_ledger_names` (101 names) and `_selftest` (9bc23db) | closed |
| T-09-35 | Tampering | host misuse of catch-up on import | medium | mitigate | Contract in header; installed consumers | closed |
| T-09-36 | Repudiation | completion claim | high | mitigate | Exact-head required checks only; PR #65 open, unmerged | closed |
| T-09-37 | Info disclosure | changed files, PR body | medium | mitigate | Home-path and email scan clean | closed |
| T-09-38 | EoP | branch protection | high | mitigate | No merge, no protection change | closed |
| T-09-39 | Tampering | RGBDS 0.6.1 archive pin | medium | mitigate | Digest in `fixtures/magentests/SOURCES.md`; CI re-verifies | closed |
| T-09-40 | Repudiation | MagenTests pass claim | high | mitigate | `magentests_oob_sram_*` plus negative control | closed |
| T-09-45 | Tampering | installed RTC API surface | medium | mitigate | Installed consumers; `rtc_catch_up_errors`, `rtc_catch_up_negative` | closed |
| T-09-SC | Tampering | package-manager installs | high | mitigate | No npm/pip/cargo install added | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-09-01 | T-09-12 | No per-half-dot RTC work; clock cost only at RTC accesses; frozen tracer digest unchanged | plan 09-11 register | 2026-10-11 |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-11 (gsd-security-auditor, ASVS L1 grep-depth plus cited code; T-09-34 closed by 9bc23db)
