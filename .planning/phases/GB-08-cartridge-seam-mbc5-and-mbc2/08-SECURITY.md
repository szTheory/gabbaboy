---
phase: "8"
slug: "cartridge-seam-mbc5-and-mbc2"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-10-11"
---

# Phase 8 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Host ROM bytes → `validate_header` | Untrusted header and length enter the loader; type-aware ceiling up to 8 MiB for MBC5 | ROM bytes; validated before allocation |
| Guest writes → mapper registers / RAM window | Guest-controlled bank, enable and rumble values index host memory | Bank numbers and RAM indices; masked before use |
| Caller battery image → `gbb_import_battery` (MBC2) | 512-byte image normalised to `0xF0 \| nibble` | Save bytes; size-checked first, single commit |
| Upstream Mooneye / WLA-DX → `fixtures/mooneye-mbc/` | 15 derivative ROMs admitted once | ROM bytes and notices; SHA-256 pinned, hosted rebuild matched |
| Repository → install tree and packages | Test-only ROMs must not ship | Fixture files; allowlist plus digest-and-name scan |
| Player → save directory | MBC2 and MBC5 battery types run without persistence in Phase 8 | No save files written |
| CI evidence → completion claims | Exact-head required checks | Run ids, job conclusions |

---

## Threat Register

Register authored at plan time across plans 08-01 to 08-10 (41 distinct threats; T-08-SC is repeated per plan and listed once). Verified 2026-10-11 at ASVS level 1 (grep and test level) against head `96d5eec`.

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-08-01 | Tampering | validate_header table lookup | high | mitigate | Row lookup only after size >= 0x150; rom_size_code > row max rejected before the 32768u << code shift; precedence identical (D-05); proven by 86,016-cell differential and loader_boundary_fuzz. Evidence: `validate_header` checks the ceiling, then the row, then `rom_size_code > row->max_rom_code` before `32768u << code` (gabbaboy.c:1838-1870); differential rerun at 96d5eec: 83,328 cells, 0 differences | closed |
| T-08-02 | Tampering | gbb_load_rom allocation order | high | mitigate | Validate, allocate, commit unchanged; cart_state committed only after allocation succeeds; loader_non_destructive and the differential's previous-ROM read check failed loads leave state intact. Evidence: `loader_non_destructive` green; differential checks the previous ROM after failed loads | closed |
| T-08-03 | Tampering | read8/write8 MBC1 bank and RAM index | high | mitigate | Moved helpers keep the rom_banks-1 / ram_banks-1 masks and the offset < rom_size guard; ASan preset and seeded write/read differential. Evidence: masks and `offset < rom_size` guard kept; linux-asan-ubsan green at exact head | closed |
| T-08-04 | Denial of service | read8 hot path | low | accept | switch on a stored byte replaces a range test; no indirect call (D-02); measure_core recorded as advisory and the frozen digest gated. Evidence: accepted: see Accepted Risks Log | closed |
| T-08-05 | Repudiation | no-observable-change claim | medium | mitigate | Claim rests on zero-difference differential, unchanged suites, frozen digest and exact-head CI; no expectation edits allowed (D-09, D-12). Evidence: zero-difference differential, `baseline status=pass`, frozen digest `4c7a57ff3d50d228`, exact-head CI 38158954335 | closed |
| T-08-06 | Tampering | MBC2 header admission | high | mitigate | RAM size from the row (512), $149 must be $00, ROM code <= $03 checked before the shift; mbc2_header_matrix. Evidence: `mbc2_header_matrix` green | closed |
| T-08-07 | Tampering | MBC2 RAM index and bank | high | mitigate | Index masked to address & 0x1FF; bank translated then masked by rom_banks-1 with the offset < rom_size guard; mbc2_ram_echo over 8192 addresses, ASan run. Evidence: `address & 0x1FFu` (gabbaboy.c:798, 938); `mbc2_ram_echo` green | closed |
| T-08-08 | Tampering | gbb_import_battery for MBC2 | high | mitigate | Exact 512-byte length checked first; normalise and compare before any write; single commit and one generation bump; input buffer never written; mbc2_battery_errors and mbc2_battery_idempotent. Evidence: `mbc2_battery_*` (5 tests) green | closed |
| T-08-09 | Tampering | battery_generation counter | low | mitigate | Saturating increment reused from the existing path. Evidence: saturating generation path reused | closed |
| T-08-10 | Denial of service | 8 MiB ceiling / allocation | high | mitigate | Type-aware early ceiling before header work; 8 MiB only for MBC5 rows; allocation only after validation; max 8 MiB + 128 KiB; mbc5_rom_bound and the differential prove non-MBC5 results unchanged. Evidence: per-row `early_ceiling_bytes`; only MBC5 rows ($19-$1E) carry `GBB_MAX_ROM_SIZE`; `mbc5_rom_bound`, `loader_oversized` and `loader_boundary_fuzz` green | closed |
| T-08-11 | Tampering | 32-bit size_t overflow in declared length / bank offset | high | mitigate | ROM code checked <= $08 before 32768u << code; bank masked by rom_banks-1; offset < rom_size guard kept; ASan run. Evidence: code check before the shift (gabbaboy.c:1845); ASan job green | closed |
| T-08-12 | Tampering | MBC5 RAM index with rumble bit | high | mitigate | RAM bank masked 0x0F / 0x07 then by ram_banks-1; bit 3 never reaches the RAM index on rumble rows; mbc5_ram_banking and mbc5_rumble_state. Evidence: `mbc5_ram_*` and `mbc5_rumble_state` green | closed |
| T-08-13 | Tampering | gbb_rumble_state outputs | medium | mitigate | NULL checks first; outputs written only on GBB_OK; mbc5_rumble_errors with sentinels. Evidence: `gbb_rumble_state` checks NULL first and writes outputs only on `GBB_OK` (gabbaboy.c:2014); `mbc5_rumble_errors` green | closed |
| T-08-14 | Tampering | rumble_changes counter | low | mitigate | Guarded saturating increment on both the write and gbb_reset paths; mbc5_rumble_saturation presets UINT64_MAX - 1 in a single-TU white-box test and asserts UINT64_MAX after each of three transitions. Evidence: `!= UINT64_MAX` guard on both paths (gabbaboy.c:901, 1915); `mbc5_rumble_saturation` green | closed |
| T-08-15 | Repudiation | silent progress loss for $06/$1B/$1E | medium | mitigate | battery_unsupported flag drives a fixed status string and stderr warning on startup and replacement. Evidence: status and stderr paths at src/player/main.c:517, 965 | closed |
| T-08-16 | Tampering | save directory writes for unsupported types | medium | mitigate | battery_backed stays false so every file path early-returns; player_session_battery_unsupported asserts an empty save directory. Evidence: `player_session_battery_unsupported` green (empty save directory) | closed |
| T-08-17 | Tampering | 2 MiB player read bound | low | mitigate | PLAYER_SESSION_MAX_ROM_SIZE and its message untouched (D-15), checked by acceptance grep and player_session_max_size. Evidence: `player_session_max_size` green; cap unchanged | closed |
| T-08-18 | Spoofing | fixture admission provenance | medium | mitigate | Pinned revision, tree and builder archive digests; per-ROM SHA-256 and size; parent patch/font referenced by digest; MIT and font notices copied in the same commit as the ROMs. Evidence: manifest pins and notices; `mooneye_mbc_fixture_digest` green | closed |
| T-08-19 | Tampering | Darwin vs Linux digest drift | medium | mitigate | Digests must equal D-25 before commit; claim deferred until the hosted Linux leg (Plan 08-07) matches. Evidence: hosted mooneye-mbc-repro matched 15/15 (fixture-repro run 38158954278) | closed |
| T-08-20 | Information disclosure | .sym/.lnk/.log with local paths | medium | mitigate | Builds in mktemp dirs; acceptance greps forbid those extensions and home paths in committed files. Evidence: no `.sym`, `.lnk` or `.log` in the branch diff; home-path grep clean outside `.planning` | closed |
| T-08-21 | Spoofing | unknown or edited manifest accepted | medium | mitigate | Suite selected by exact SHA-256; unknown digest exits 2 invalid-manifest (checked here by hand, pinned as mooneye_mbc_unknown_manifest in Plan 08-06). Evidence: `mooneye_mbc_unknown_manifest` green | closed |
| T-08-22 | Spoofing | false pass (wrong mapper or wrong PC) | high | mitigate | Unchanged oracle requires the pass callback then LD B,B at the exact result_pc with exact registers; mooneye_mbc_type_mutation; pc-table agreement plus tamper control; per-case receipts pin callback_pc and result_pc. Evidence: `mooneye_mbc_type_mutation`, `mooneye_mbc_pc_table` and `_tamper` green | closed |
| T-08-23 | Denial of service | 8 MiB ROM read into runner | low | mitigate | Buffer = size_bytes + 1 capped at GBB_CASES_MAX_ROM_BYTES; exact size check before digest. Evidence: buffer capped by `GBB_CASES_MAX_ROM_BYTES` with an exact-size check | closed |
| T-08-24 | Tampering | path traversal via manifest rom field | low | mitigate | Compiled table supplies names; verifier rejects slash, backslash and ... Evidence: cmake/VerifyMooneyeMbc.cmake:64, 102 reject slash, backslash and `..` | closed |
| T-08-25 | Information disclosure | sibling ROMs in install/package artifacts | high | mitigate | Install allowlist plus digest-and-name scan of install tree, extracted preview package and player package; planted, empty and dir-list self-tests prove the scan can fail. Evidence: `mooneye_mbc_not_installed` with planted-payload and empty-tree self-tests green; `preview_package_smoke` green | closed |
| T-08-26 | Tampering | stale install allowlist | high | mitigate | Exact share/gabbaboy/fixtures child list asserted in install tree and extracted package. Evidence: `mooneye_mbc_fixture_dirs_selftest` green | closed |
| T-08-27 | Tampering | mutant built from an unmutated core | medium | mitigate | Exactly-once anchor check with FATAL_ERROR; 32Mb pass plus 64Mb non-pass pair proves the mutation took effect. Evidence: mitigated in 08-08 after the D-062 amendment: configure FATAL_ERROR unless the `& 1u) << 8` anchor occurs exactly once (tests/CMakeLists.txt:75-82); `mbc5_ninth_bit_mutant_bank_1ff` (non-pass) and `_control_below_100` (pass) prove the mutation took effect | closed |
| T-08-28 | Repudiation | D-25 digest claim without hosted proof | medium | mitigate | Claim only after mooneye-mbc-repro succeeds at the exact head; mismatch stops the plan. Evidence: hosted mooneye-mbc-repro success at the exact head | closed |
| T-08-29 | Tampering | CI supply chain | medium | mitigate | No new actions; reuse pinned checkout and upload-artifact SHAs. Evidence: only the existing pinned checkout and upload-artifact SHAs appear in the diff | closed |
| T-08-30 | Tampering | RGBDS toolchain | medium | mitigate | Exact v1.0.1 version gate and archive SHA-256 from existing manifests; hosted rebuild compares bytes. Evidence: RGBDS 1.0.1 version gate and archive SHA-256; hosted rebuild byte-compares | closed |
| T-08-31 | Repudiation | fixture evidence class | low | mitigate | Manifest states harness-supplied marker and 'not hardware evidence'; scope_limits list no CGB, rumble or hardware claim. Evidence: fixture manifest scope_limits | closed |
| T-08-32 | Denial of service | 8 MiB in-memory inflation in tests | low | mitigate | Single calloc freed on every path; ASan run. Evidence: single calloc freed on every path; ASan job green | closed |
| T-08-33 | Repudiation | overclaiming cartridge, rumble or hardware scope | medium | mitigate | Evidence ledger states D-30 classes, MBC2A caveat, no CGB/physical rumble/game compatibility; support entry names model and revision. Evidence: docs/mbc2-mbc5-evidence.md states evidence classes and exclusions | closed |
| T-08-34 | Information disclosure | personal paths in docs | medium | mitigate | Repository-relative paths and run URLs only; home-path grep in acceptance and in Plan 08-10's privacy check. Evidence: home-path grep clean on the changed files outside `.planning` | closed |
| T-08-35 | Tampering | release-bound support ledger | low | mitigate | Only docs/support/unreleased.md changes; verify-support-ledger.py --self-test and v0.1.0 untouched check. Evidence: only docs/support/unreleased.md changed | closed |
| T-08-36 | Repudiation | completion claim | high | mitigate | Only exact-head required checks count; skipped, stale or local results are never green; PR left OPEN until verification passes. Evidence: exact-head run ids recorded; PR #64 OPEN | closed |
| T-08-37 | Information disclosure | changed files, PR body | medium | mitigate | Home-path and email privacy check across all Phase 8 files; no build products with local paths tracked. Evidence: privacy check clean; one email, inside the verbatim upstream Mooneye licence | closed |
| T-08-38 | Elevation of privilege | branch protection | high | mitigate | No merge and no protection change in this plan; the later pre-authorized squash merge requires exact-head green after verification. Evidence: no merge and no protection change during execution | closed |
| T-08-39 | Tampering | D-27 sibling patch variant | medium | mitigate | Created only if a pass path is corrupted; changes reporting code only, never an assertion; SHA-256 pinned in manifest and suite_def; reason and affected digests recorded. Evidence: no sibling patch variant was needed; parent patch referenced by digest | closed |
| T-08-40 | Repudiation | provenance or notice drift after admission | medium | mitigate | mooneye_mbc_fixture_digest requires SOURCES.md and ELIGIBILITY.md, checks parent_references digests and pins; notices row carries the final manifest SHA-256. Evidence: `mooneye_mbc_fixture_digest` checks SOURCES, ELIGIBILITY and parent references | closed |
| T-08-SC | Tampering | npm/pip/cargo installs | high | mitigate | No package-manager install in this plan. Evidence: no package-manager installs in any plan; toolchains are SHA-pinned archives | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-08-01 | T-08-04 | A `switch` on a stored byte replaces a range test in `read8`, with no indirect call (D-02). Speed is advisory only; the frozen correctness digest is gated. | Plan 08-01 threat model (low severity, below block threshold) | 2026-10-11 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-11 | 41 | 41 | 0 | secure-phase orchestrator (L1 short-circuit; register authored at plan time) |

Note: the 08-07 SUMMARY recorded T-08-27 as not mitigated because no mutant landed there. Plan 08-08 closed it after the D-062 amendment re-pointed the mutant to bank `$1FF`.

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-11
