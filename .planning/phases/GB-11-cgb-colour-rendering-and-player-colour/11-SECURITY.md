---
phase: "11"
slug: "cgb-colour-rendering-and-player-colour"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-10-13"
---

# Phase 11 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Plan |
|----------|-------------|------|
| repository core text → configure-time mutant copies | Build-tree copies of the core are compiled into test executables | 11-01, 11-05 |
| generator script → committed test data | Script output is trusted as an oracle | 11-01 |
| guest writes FF68-FF6C → 64-byte host arrays | Guest-chosen indices address fixed host storage | 11-02 |
| guest VRAM/OAM/CRAM → per-dot index arithmetic | Guest bytes pick palette, bank, tile and colour indices | 11-03 |
| guest OAM/BGP/OBP → compat palette lookup | Guest bytes pick the palette set and shade | 11-04 |
| committed oracle data → test verdicts | The `.inc` rows are the trusted expectation | 11-05 |
| host caller → `gbb_copy_frame_rgb555` / `gbb_set/get_compat_palette` | Untrusted pointer, capacity, pitch, `struct_size` and colour values | 11-06 |
| downloaded RGBDS archive → committed ROM bytes; fixture ROM → core; manifest recipe → reproduce script | A network toolchain, guest code and manifest fields become tool arguments | 11-07, 11-08 |
| case files / runner flags → runner | Cases select ROMs, digests and output directories; `--model`/`--profile` pick the profile | 11-09 |
| GitHub release assets → repo fixtures; third-party ROM → core | Third-party binaries enter the repo and run as guests | 11-10 |
| upstream trees → disposition record; user acid2 ROM/PNG → local script | Third-party names and untrusted local files are hashed and parsed | 11-11 |
| command line → player; ROM file → probe | Untrusted argv and file bytes | 11-12 |
| repository text → users and release notes | Published capability statements | 11-13 |
| fuzz input → palette registers and compat API; bench receipts → repo | Arbitrary bytes and host measurements | 11-14 |
| local session facts → committed planning records | Run IDs, heads and lessons become public text | 11-15 |

---

## Threat Register

All dispositions are `mitigate`. Evidence was verified at 7881c88 (docs-only on top of d3d8752).

| Threat ID | Category | Component | Severity | Disposition | Evidence | Status |
|-----------|----------|-----------|----------|-------------|----------|--------|
| T-11-01 | Tampering | `gbb_colour_mutant` | medium | mitigate | tests/CMakeLists.txt `gbb_colour_mutant`: anchor must occur exactly once (forward and reverse), copies in the build tree only, linked only into test executables; no install rule | closed |
| T-11-02 | Repudiation | truth-table oracle independence | medium | mitigate | tests/scripts/gen-cgb-priority-truth.py is stdlib-only and reads no core source; `cgb_priority_truth_regen`, `_selftest`, `_regen_mutated` | closed |
| T-11-03 | Tampering | CRAM index from BCPS/OCPS | high | mitigate | src/core/gabbaboy.c `cram_data_write`/`cram_data_read` mask `& 0x3F` on every use; `palette_cram_*`, `palette_mutant_*`, `cgb_fuzz_palette_*`; hosted phase1-asan | closed |
| T-11-04 | Tampering | post-boot CRAM fill | medium | mitigate | fill bound `sizeof(bg_cram)/2`; `cgb_postboot_cram_white` | closed |
| T-11-05 | Information disclosure | DMG-profile visibility | low | mitigate | `cgb_visibility_matrix_dmg`, `dmg_baseline` | closed |
| T-11-06 | Tampering | palette/bank/colour indices from attributes | high | mitigate | `ppu_vram_read` bounds the address and masks the bank; `cram_colour` masks palette and index; `cgb_attr_*` with mutant pairs | closed |
| T-11-07 | Tampering | RGB buffer writes at `ly*160+slot` | high | mitigate | early return on `fetched_slot >= GBB_FRAME_WIDTH`; one shared `pixel_at`; buffers sized `GBB_FRAME_PIXELS` | closed |
| T-11-08 | Information disclosure | DMG frame regression | medium | mitigate | `cgb_dmg_identity_shade_pin`, `cgb_dmg_identity_mutant_shade_flip`, the `colour_writes_shade` mutant pair, `dmg_baseline` | closed |
| T-11-09 | Repudiation | a truth table that cannot fail | medium | mitigate | 12 priority/compat/OPRI/attribute mutants, each with a control; row count asserted at 6144 | closed |
| T-11-10 | Tampering | mutant builds leaking into release | low | mitigate | as T-11-01 | closed |
| T-11-11 | Tampering | `gbb_copy_frame_rgb555` destination arithmetic | high | mitigate | NULL, alignment, even-pitch, overflow-safe pitch bound, capacity, pointer-overflow and overlap checks all before the first copy; `cgb_rgb555_args`, `cgb_rgb555_mutant_skewed_validator` + control | closed |
| T-11-12 | Tampering | partial mutation on a rejected palette set | high | mitigate | `struct_size` check and full bit-15 validation before any store; `palette_compat_api_reject`, `palette_compat_mutant_mask_bit15` + control | closed |
| T-11-13 | Information disclosure | `gbb_get_compat_palette` writing past a small struct | high | mitigate | NULL and `struct_size < V1` rejected before any store; only V1 fields written; `palette_compat_api_get_reject`, `_larger` | closed |
| T-11-14 | Denial of service | misaligned `uint16_t` store | medium | mitigate | odd pointer and pitch rejected; rows copied with `memcpy` | closed |
| T-11-15 | Tampering | RGBDS archive and manifest tool arguments | high | mitigate | tests/scripts/reproduce-cgb-colour.sh: scratch `mktemp -d`, v1.0.1 version guard, `python3 -I`, regex-validated recipe fields as argv lists; fixture-repro.yml `sha256sum --check` on the pinned archive; hosted fixture-repro green | closed |
| T-11-16 | Tampering | committed fixture bytes | medium | mitigate | `cgb_colour_fixture_digest`; `.gitattributes` `fixtures/cgb-colour/*.gb -text` | closed |
| T-11-17 | Repudiation | fixture provenance and rights | medium | mitigate | fixtures/cgb-colour/LICENSE.txt (MIT); manifest licence, source identity, evidence class and scope limits, enforced by the reproduce script | closed |
| T-11-18 | Tampering | RGB555 digest of out-of-range values | low | mitigate | src/accept/digest.c `rgb555_valid` rejects `> 0x7FFF` before output; `acceptance_digest_rgb555_vectors` against the independent Python vector | closed |
| T-11-19 | Tampering | acid2 inputs | high | mitigate | tests/scripts/run-acid2-local.py checks size and SHA-256 pins before decode or run, exits 2 on refusal; `cgb_acid2_local_refuses_unpinned` | closed |
| T-11-20 | Denial of service | PNG decoder on hostile input | medium | mitigate | per-chunk cap, CRC, 160x144 non-interlaced only, colour type/depth allow-list, capped inflate, exact-size check; runs under `-I`, only after pins pass | closed |
| T-11-21 | Repudiation | rights gate G1 | high | mitigate | only tests/acid2/manifest.json and the script are tracked (no ROM or PNG); G1 recorded in the manifest; CTests use synthetic input only | closed |
| T-11-22 | Tampering | failure PPM path | low | mitigate | src/runner/acceptance.c `join_path` bound under `failure_dir` | closed |
| T-11-23 | Tampering | downloaded MagenTests ROM bytes | high | mitigate | all six ROMs re-hashed (size and SHA-256 match manifest, RESEARCH and SOURCES.md, `$143` C0/C0/80); `magentests_fixture_digest`; hosted `magentests-repro` green | closed |
| T-11-24 | Repudiation | MagenTests redistribution rights | high | mitigate | fixtures/magentests/LICENSE.txt (MIT), SOURCES.md and ELIGIBILITY.md rows per ROM; `magentests_not_installed` | closed |
| T-11-25 | Repudiation | overstated evidence | medium | mitigate | ELIGIBILITY.md applicability label per ROM (author-attested / CGB photo, revision E unattested / SameBoy differential) | closed |
| T-11-26 | Denial of service | guest never reaching a stable frame | low | mitigate | tests/test_magentests.c fixed 20-frame run; generation must advance and the last two frames must match | closed |
| T-11-27 | Tampering | player `--model` value | medium | mitigate | src/player/main.c exact match on auto/dmg/cgb, otherwise usage and exit 2; `player_cgb_cli` | closed |
| T-11-28 | Denial of service | probe of a large or hostile file | medium | mitigate | src/player/session.c `PLAYER_SESSION_MAX_ROM_SIZE`; the probe path frees on every exit and does not touch the running instance | closed |
| T-11-29 | Tampering | RGBA buffer sizes in `update_frame` | medium | mitigate | fixed 160x144 buffers, pitch 320 checked by the core; src/player/colour.c expands masked 5-bit channels only | closed |
| T-11-30 | Information disclosure | smoke output and HOME | low | mitigate | isolated `HOME`/`CFFIXED_USER_HOME` in tests/player/CMakeLists.txt; the colour smoke sets `skip_final_save` | closed |
| T-11-31 | Tampering | palette fuzz path | high | mitigate | tests/fuzz_core.c operation and half-dot limits, bit-15 and no-mutation-on-reject invariants; `cgb_fuzz_palette_regressions`, `cgb_fuzz_palette_mutant_no_mask` + control; hosted ASan fuzz leg | closed |
| T-11-32 | Information disclosure | 11-BENCH receipts | medium | mitigate | `ab-receipt-private-path` guard in tests/scripts/measure-release-baseline.sh; receipts carry no home paths or emails, hardware recorded as a class string | closed |
| T-11-33 | Repudiation | stale gate ownership | medium | mitigate | `model_gates_no_phase11_rows` and `_mutated_doc` | closed |
| T-11-34 | Tampering | compat set/shade indices | high | mitigate | `compat_rgb555[set % 3][shade & 3]`, set from OAM bit 4; `cgb_compat_internal_*` | closed |
| T-11-35 | Information disclosure | DMG regression through the compat branch | medium | mitigate | compat branch writes only `rgb_working`, DMG branch first; `cgb_rgb_store_shade_untouched`, shade pin, `dmg_baseline` | closed |
| T-11-36 | Tampering | five new committed ROMs and manifest rows | medium | mitigate | manifest rows carry SHA-256 and recipe; `cgb_colour_fixture_digest`; reproduce script checks every row; hosted fixture-repro green | closed |
| T-11-37 | Repudiation | fixture predicate that cannot fail | medium | mitigate | `cgb_colour_guest_cram_mutant_blocked_no_increment`, `cgb_colour_mutant_frame_resolve` (each with a control), `cgb_rgb_store_lcdoff_fixture` | closed |
| T-11-38 | Spoofing | CGB digest read as RGB888 or wrong profile label | medium | mitigate | `GBB-RGB555LE-v1` header; runner format from the `gbb_get_info` profile with `frame555`/`observed555` keys; profile/model conflict exits 2; `acceptance_cgb_colour_*`, `acceptance_digest_rgb555_vectors` | closed |
| T-11-39 | Repudiation | overstated AGE/Mealybug coverage | high | mitigate | tests/scripts/verify-external-dispositions.py checks reasons, the docs mirror and tracked fixtures; `cgb_external_dispositions`, `_mutated` | closed |
| T-11-40 | Repudiation | player capability claims drifting | medium | mitigate | `player_claims_agree`, `_mutated` (expects the specific `claims-disagree no colour correction` reason) | closed |
| T-11-41 | Information disclosure | DECISIONS/INDEX/LESSONS/STATE/continuation | medium | mitigate | phase diff adds no home paths or owner email (only grep patterns in plan text) | closed |
| T-11-42 | Repudiation | handoff advancing or naming the wrong step | medium | mitigate | STATE.md names Phase 11 execution and `/gsd-verify-work 11`; Phase 12 not started; `auto_advance` and `_auto_chain_active` false | closed |
| T-11-SC | Tampering | package installs (npm/pip/cargo) | high | mitigate | declared in all 15 plans; the phase adds no package manifests or install lines, Python is stdlib-only, RGBDS archives are digest-pinned | closed |

*Accounting:* T-11-01..T-11-42 plus T-11-SC = 43 distinct IDs. T-11-SC is the only ID declared in more than one plan. No SUMMARY raised an unregistered threat flag.

### Audit notes (closed, non-blocking)

- The 11-11 acid2 PNG decoder accepts more colour types than the plan named (types 0, 3 and 4 at depths 1-8), because the pinned reference images use them. It remains bounded, so T-11-20 holds.
- `phase1-asan` is Linux-only and does not configure on the macOS development host. The ASan/UBSan evidence for T-11-03, T-11-06, T-11-31 and T-11-34 is the hosted CI leg. It was green at 68cdb71 after the LeakSanitizer fix for deliberately failing mutants (361256d). The exact PR head must be green before merge.
- The player threats (T-11-27..T-11-30, T-11-40) were checked by code reading and test registration in this audit. The player suite itself passed 93/93 at d3d8752 in the execute-phase post-merge gate.
- The byte-identical rebuild of the three new MagenTests ROMs is proven by the hosted `magentests-repro` job, because the local RGBDS is not the pinned 0.6.1.

---

## Accepted Risks Log

None. Every threat is mitigated.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-13 | 43 | 43 | 0 | gsd-security-auditor (execute-phase verify:post) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-13
