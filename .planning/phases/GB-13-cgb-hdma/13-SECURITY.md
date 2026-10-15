---
phase: "13"
slug: "cgb-hdma"
status: verified
threats_open: 0
threats_total: 25
threats_closed: 25
asvs_level: 1
block_on: high
created: "2026-10-15"
---

# Phase 13 — Security

## Trust boundaries

Guest registers, ROM bytes and public run budgets cross into the portable core. Fixture/source/tool bytes and local claim/evidence records cross into test, reproduction, package and workflow validation. There is no new web/authentication surface.

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation evidence | Status |
|---|---|---|---|---|---|---|
| T-13-01 | Tampering | src/core/gabbaboy.c | high | mitigate | src/core/gabbaboy.c:4220,4453; tests/test_cgb_hdma_internal.c:262,1508,1614 | closed |
| T-13-02 | Denial of service | src/core/gabbaboy.c | high | mitigate | src/core/gabbaboy.c:4480; bounded maximum/tiny-budget controls | closed |
| T-13-SC | Tampering | dependency installs | high | accept | Existing production dependency declarations unchanged; pinned archive digests checked before extraction/use; acceptance recorded below | closed |
| T-13-03 | Tampering | src/core/gabbaboy.c | high | mitigate | src/core/gabbaboy.c:1701,1712,1732,1755; address and overflow controls | closed |
| T-13-04 | Denial of service | src/core/gabbaboy.c | high | mitigate | tests/CMakeLists.txt:461,467; whole-block admission controls | closed |
| T-13-05 | Tampering | src/core/gabbaboy.c | high | mitigate | src/core/gabbaboy.c:1681,4380,4490; public HALT and competing-stall controls | closed |
| T-13-06 | Denial of service | src/core/gabbaboy.c | high | mitigate | tests/test_cgb_hdma_internal.c:1071,1118; independent stall controls | closed |
| T-13-07 | Tampering | tests/test_cgb_hdma_partition.c | high | mitigate | tests/test_cgb_partition.c:357,402; src/core/gabbaboy.c:3502; failed-load continuation | closed |
| T-13-08 | Denial of service | tests/test_cgb_hdma_internal.c | high | mitigate | tests/test_cgb_hdma_internal.c:1361,1781; lifecycle/hostile/partition controls | closed |
| T-13-09 | Tampering | src/core/gabbaboy.c | high | mitigate | cmake/P13Mutants.cmake:33,74; tests/expect_exit.cmake:43; anchor controls | closed |
| T-13-10 | Denial of service | src/core/gabbaboy.c | high | mitigate | cmake/P13Mutants.cmake:49; exact diagnostic/exit and finite timeout controls | closed |
| T-13-11 | Tampering | fixtures/samesuite/manifest.json | high | mitigate | tests/scripts/reproduce-samesuite.sh:200,344,459; rights/source/tool/digest controls | closed |
| T-13-12 | Denial of service | fixtures/samesuite/gdma_addr_mask.gb | high | mitigate | tests/test_samesuite_hdma.c:16,209,248; bounded runner and exact provenance | closed |
| T-13-13 | Tampering | fixtures/magentests/hblank_vram_dma.gbc | high | mitigate | tests/scripts/reproduce-magentests.sh:273; tests/test_magentests.c:389,488 | closed |
| T-13-14 | Denial of service | tests/test_magentests.c | high | mitigate | tests/test_magentests.c:414,554; typed bank/HALT/no-transfer controls | closed |
| T-13-15 | Tampering | fixtures/cgb-hdma/hblank.asm | high | mitigate | tests/scripts/reproduce-cgb-hdma.sh:87; tests/test_cgb_hdma.c:408,473 | closed |
| T-13-16 | Denial of service | tests/player/cgb_smoke.cmake | high | mitigate | tests/test_cgb_hdma.c:417; tests/player/cgb_smoke.cmake:151,171,205 | closed |
| T-13-17 | Tampering | tests/test_samesuite_hdma.c | high | mitigate | tests/scripts/verify-cgb-hdma-dispositions.py:236,246; rights/denominator mutations | closed |
| T-13-18 | Denial of service | tests/test_samesuite_hdma.c | high | mitigate | tests/test_samesuite_hdma.c:244; complete dispositions 5/5 with CGB-C excluded | closed |
| T-13-19 | Tampering | tests/consumers/c/main.c | high | mitigate | cmake/ScanForbiddenFixtures.cmake:68,145,155; cmake/RunInstalledConsumer.cmake:15 | closed |
| T-13-20 | Denial of service | cmake/PreviewPackageSmoke.cmake | high | mitigate | tests/consumers/c/main.c:287,401,670; equivalent C++ and renamed-ROM controls | closed |
| T-13-21 | Tampering | docs/native-integration.md | high | mitigate | tests/scripts/verify-cgb-hdma-claims.py:84,140,248; seven claim mutations | closed |
| T-13-22 | Denial of service | src/player/limitations.h | high | mitigate | tests/scripts/verify-cgb-hdma-claims.py:302; tests/scripts/cgb-hdma-prohibition.test.cjs:12 | closed |
| T-13-23 | Tampering | .github/workflows/preview.yml | high | mitigate | verify-hdma-closure.py:659-694; all Git states checked with exact metadata allowlist; 26/26 controls | closed |
| T-13-24 | Denial of service | .planning/STATE.md | high | mitigate | same corrected revision gate as T-13-23; staged/restored, rename, deletion and untracked controls | closed |

## Resolved finding — tested-source comparison omitted behavioral inputs

**Threats:** T-13-23 and T-13-24; one high-severity workflow-integrity finding, now fixed. The original isolated probe accepted an untested core-only change. Test-only commit `03292b1` reproduced that defect before fix `5459b7c` replaced the narrow comparison with independent committed, staged, unstaged and non-ignored untracked comparisons. Only explicitly named closeout metadata is allowed.

The independent focused re-audit executed 26/26 controls successfully, including core, fixtures, harnesses, workflows, unknown paths, deletion, rename into metadata, unusual filenames and permitted metadata positive controls. The live validator correctly rejects the old BENCH binding after the checker changes. Retesting/rebinding is required before closure; source `690c081` measurements remain historical. Exact final PR-head checks remain mandatory.

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---|---|---|---|---|
| AR-13-SC | T-13-SC | No new production dependency/install; existing upstream archive/tool trust remains bounded by pinned source, rights and digest checks before use. Root production CMake/preset/CI declarations are unchanged from Phase 12. | Authored Phase 13 PLAN accept dispositions; retained during audit | 2026-10-14 |

## Fresh verification

Security auditor executed 96/96 native boundary/control tests and 4/4 player HDMA/claim tests successfully. Magen and original-HDMA reproduction self-tests, complete disposition verification and eight-surface claim mutations passed. The initial isolated stale-core probe demonstrated the defect; the focused post-fix re-audit passed all 26 revision controls and found no residual issue. No implementation or test files were changed by the auditor.

## Non-findings and scope

Whole-block bounds, output/time headroom, lifecycle ownership, finite run loops, fixture provenance and package exclusion controls are implemented and tested. No new production dependency was introduced. Physical CGB-E remains UNKNOWN/POLICY; optional CGB-C is rights-gated and outside the five-case software denominator. No hardware measurement or host-fuzzer campaign is claimed.

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|---|---|---|---|---|
| 2026-10-15 | 25 | 23 | 2 | Initial audit; revision gate defect reproduced |
| 2026-10-15 | 25 | 25 | 0 | Independent focused re-audit at `5459b7c`; existing accepted risk retained |

## Sign-off

- [x] All threats have authored dispositions.
- [x] Existing accepted supply-chain risk recorded.
- [x] Revision-gate mitigation fixed and independently re-audited.
- [x] `threats_open: 0` confirmed.

Approval: secured, 25/25 threats closed. This security verdict does not substitute for fresh execution or exact-head hosted checks.
