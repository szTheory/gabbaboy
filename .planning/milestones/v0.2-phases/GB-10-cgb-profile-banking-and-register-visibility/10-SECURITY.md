---
phase: "10"
slug: "cgb-profile-banking-and-register-visibility"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-10-12"
---

# Phase 10 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| guest ROM / header → core | Untrusted cartridge header and guest code select profile, exec mode, bank indices and I/O accesses | header bytes, guest bus traffic (FF4C-FF7F, VBK/SVBK, KEY0/KEY1, OAM DMA) |
| host → public API | Embedders call `gbb_probe_rom`, `gbb_get_info` (`struct_size` handshake), `gbb_create` with a profile | caller-sized structs, ROM buffers |
| network → fixture rebuild | Reproduction scripts and CI fetch RGBDS, Mooneye and WLA-DX sources | toolchain archives, upstream sources (digest-pinned) |
| repository → packages | Install and preview trees must not carry third-party ROMs | fixture binaries |
| repository → public artifacts | Docs, manifests, benchmark receipts, PR body | text; must carry no personal paths or identifiers |

---

## Threat Register

Built from the 20 `10-NN-PLAN.md` `<threat_model>` blocks (register authored at plan time). Evidence was verified by gsd-security-auditor against the implementation and a local 538/538 CTest run; hosted evidence is PR #66 exact-head CI (10-20-SUMMARY.md).

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-10-01 | Tampering | verify-model-gates.py function detection | high | mitigate | Independent brace-depth function count vs scanner; real-file untagged/deleted-tag mutants; `-I` stdlib-only | closed |
| T-10-02 | Repudiation | docs/model-gates.md drift | medium | mitigate | Bijection, order and empty-table checks; `model_gates_real_doc_mismatch`, `model_gates_tracer_doc_mismatch` | closed |
| T-10-03 | Tampering | gabbaboy.c tagging pass | high | mitigate | Comment-only commit e426d0f; exactly-once anchor checks; DMG baseline | closed |
| T-10-04 | Repudiation | runner labels | medium | mitigate | Single profile mapping in `src/runner/acceptance.c`; CGB cases forbid `DMG-CPU-B`; unknown/conflict exit 2 | closed |
| T-10-05 | Tampering | reset_state refactor | high | mitigate | Pin test committed before refactor; `cgb_postboot_dmg_pin` + flipped controls; DMG baseline | closed |
| T-10-06 | Tampering | gbb_info struct_size handshake | high | mitigate | Reject sizes below `GBB_INFO_SIZE_V1`; field-by-field store; static assert; `cgb_info_struct_size`; hosted ASan/UBSan | closed |
| T-10-07 | Denial of service | gbb_probe_rom on huge rom_size | medium | mitigate | Ceiling check first in shared `validate_header`; probe allocates nothing; `cgb_probe_parity` | closed |
| T-10-08 | Tampering | exec_mode on failed load | medium | mitigate | Mode commits with the ROM swap after both allocations; `cgb_info_failed_load_unchanged` | closed |
| T-10-09 | Tampering | channel 1 post-boot state | medium | mitigate | Volume-0 policy; `cgb_postboot_ch1_silent` with audible controls | closed |
| T-10-10 | Repudiation | provenance labels | medium | mitigate | HW_TEST rejected outside COMPAT with mutant; Mooneye source named; CGB A-E applicability documented | closed |
| T-10-11 | Repudiation | post-boot doc/code drift | medium | mitigate | `cgb_tables_postboot`, selftest, mutated-doc control | closed |
| T-10-12 | Tampering | bank index into vram/wram | high | mitigate | Arrays sized by constants; banks set only by reset and masked writes; `banking_*` under hosted ASan | closed |
| T-10-13 | Tampering | whole-array sizeof bounds | high | mitigate | `sizeof` only in reset memsets; per-bank map bound | closed |
| T-10-14 | Tampering | SVBK/VBK writes to bank indices | high | mitigate | `& 1u` / `& 7u` (0→1), CGB exec mode only; fuzz `require_banks` | closed |
| T-10-15 | Repudiation | DEFERRED cells | high | mitigate | Deferred reads refused; writes latch stop + address; `cgb_visibility_deferred_*` | closed |
| T-10-16 | Tampering | DMG I/O path | high | mitigate | `model_is_cgb` guard leaves DMG chain unchanged; `cgb_visibility_matrix_dmg`, `banking_dmg_banks_frozen`, DMG baseline | closed |
| T-10-17 | Denial of service | STOP with KEY1 armed | medium | mitigate | Latch unsupported-bus at FF4D instead of sleeping; `cgb_stop_*` with controls | closed |
| T-10-18 | Tampering | dma_source_read CGB branch | high | mitigate | Bounded helpers per source page; `banking_dma_*`; wrong-bank mutant | closed |
| T-10-19 | Tampering | RGBDS toolchain | high | mitigate | Archive sha256 checked before extract; version pinned to v1.0.1; temp work dir; byte compare | closed |
| T-10-20 | Information disclosure | fixture and manifest text | low | mitigate | No personal paths in manifests; privacy grep clean | closed |
| T-10-21 | Tampering | fetched Mooneye/WLA-DX sources | high | mitigate | Pinned revisions, trees, patch, font and tool digests; `--fuzz=0`; out-of-repo work dir; byte compare; CI `mooneye-cgb-repro` | closed |
| T-10-22 | Information disclosure | third-party ROMs in packages | medium | mitigate | `cgb_mooneye_not_installed` + planted-ROM selftest over the install tree (see note 2) | closed |
| T-10-23 | Spoofing | manifest substitution | high | mitigate | Raw manifest SHA gate in runner; pc-table, expected-unsupported and unknown-manifest tamper controls | closed |
| T-10-24 | Information disclosure | 10-BENCH.json receipt | medium | mitigate | Generic hardware class only; receipt path guard; `cgb_bench_ab_*` | closed |
| T-10-25 | Denial of service | CGB fuzz path | medium | mitigate | Input 65536, run 2048, CGB op 64 limits enforced; `run-bounded-fuzz.sh --self-test` (see note 3) | closed |
| T-10-26 | Tampering | bank indices under random I/O | high | mitigate | `require_banks` after every fuzz step on both profiles; non-vacuity control; hosted ASan/UBSan | closed |
| T-10-27 | Repudiation | guide and ADR drift | medium | mitigate | `cgb_native_guide_contract`, `cgb_adr_half_dot_*` contracts, selftests and static-assert mutant | closed |
| T-10-28 | Repudiation | completion claim | high | mitigate | PR #66 open and unmerged; exact-head green required before merge (see note 1) | closed |
| T-10-29 | Information disclosure | changed files, PR body | medium | mitigate | Phase diff grep finds no home paths; only email is the upstream licence line | closed |
| T-10-30 | Elevation of privilege | branch protection | high | mitigate | No merge, no protection change | closed |
| T-10-31 | Repudiation | io section of cgb-profile.md vs io_visibility[] | medium | mitigate | `cgb_tables_io`, mutated-doc control, matrix flip/cross/sweep controls | closed |
| T-10-32 | Tampering | fixtures/mooneye-cgb/manifest.json | high | mitigate | Digest, inventory and tamper CTests; CI `mooneye-cgb-repro` | closed |
| T-10-SC | Tampering | npm/pip/cargo installs | high | mitigate | No package-manager installs in the phase diff; scanner stdlib-only | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

### Audit notes (closed, non-blocking)

1. **T-10-28 exact head.** Local commits after PR head `0902058` (Nyquist tests `58cbc6d`, validation and security docs) have no hosted run yet. Merge still requires exact-head green on the final pushed head.
2. **T-10-22 preview package.** `cmake/PreviewPackageSmoke.cmake` scans the extracted preview package with the mooneye-mbc manifest only; the CGB digest list covers the install tree. The fixture-directory allowlist and the "mooneye" path rule still apply to the preview tree. The CGB scan also prints the default "mooneye-mbc absent" label (message only). Follow-up candidate.
3. **T-10-25 self-test depth.** `run-bounded-fuzz.sh --self-test` checks the 65536 and 2048 limits but not `FUZZ_CGB_OPERATION_LIMIT 64u`; the limit is enforced in code and bounded by the other two. Low impact.

---

## Accepted Risks Log

No accepted risks.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-12 | 33 | 33 | 0 | gsd-security-auditor (execute-phase verify:post) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-12
