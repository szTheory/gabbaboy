---
phase: "12"
slug: "cgb-double-speed"
status: verified
threats_open: 0
threats_open_nonblocking: 1
asvs_level: 1
block_on: high
register_authored_at_plan_time: true
created: "2026-10-14"
---

# Phase 12 — Security Verification

The read-only security auditor checked all 19 authored threat registers at `fbfeb24306bde6b45e9f0e0c9037b8cd1486ff2a`. Repeated T-12-SC rows are consolidated: 33 unique threats, 32 closed, one medium open below the high blocking threshold. The timeout gap remains scheduled for a verified fix before phase completion.

## Trust Boundaries

- Untrusted guest ROMs and KEY1/STOP loops enter bounded core execution.
- Fixture manifests, source archives and build recipes enter reproduction and CI.
- Expected-failure dispositions select exact measured test outcomes.
- Install trees and public artifacts must exclude test ROMs and private identifiers.
- Workflow state controls phase advancement; both auto-advance flags remain false.

## Threat Register

| Threat ID | Category | Severity | Disposition | Mitigation evidence | Status |
|---|---|---|---|---|---|
| T-12-01 | Tampering | medium | mitigate | cmake/P12Mutants.cmake:179–187; build-tree mutant targets; cgb_speed_mutant_anchor_guard and zero-mask controls | closed |
| T-12-02 | Denial of Service | high | mitigate | src/core/gabbaboy.c:4043–4070,4184; cgb_speed_tracer_switch and cgb_speed_budget_semantics | closed |
| T-12-03 | Tampering | medium | mitigate | src/core/gabbaboy.c:1424–1431; per-field reset and M24/M25/M26 controls | closed |
| T-12-04 | Tampering / Repudiation | high | mitigate | tests/scripts/reproduce-age.sh:59–92,152; VerifyFixtureManifest; pinned MIT license digest; hosted fixture-repro 38502094682 | closed |
| T-12-05 | Tampering | medium | mitigate | tests/scripts/reproduce-age.sh:53–64,123–130,146–147; age_repro_selfcheck_tampered | closed |
| T-12-06 | Spoofing | high | mitigate | tests/scripts/reproduce-age.sh:100–115; .github/workflows/fixture-repro.yml:67–113; digest before extraction | closed |
| T-12-07 | Tampering | medium | mitigate | src/core/gabbaboy.c:1738,2781,2869–2891; remainder/M11/M15 controls and identity gates | closed |
| T-12-08 | Tampering | medium | mitigate | src/core/gabbaboy.c:3586,3629,3872,4133; STOP table, operand/M33 and FF04 negative controls | closed |
| T-12-09 | Tampering | high | mitigate | src/core/gabbaboy.c:3588,4192; cgb_speed_dmg_unarmed_unchanged and M8/M30 controls | closed |
| T-12-10 | Tampering | high | mitigate | src/core/gabbaboy.c:4143–4148; cgb_speed_headroom full-state check and M22 control | closed |
| T-12-11 | Denial of Service | high | mitigate | src/core/gabbaboy.c:4043–4070; cgb_speed_never_stopped and M9 control | closed |
| T-12-12 | Repudiation | medium | mitigate | tests/scripts/verify-model-gates.py:317–398; CMake exactly-once STOP tag; no-phase12 and doc negative controls | closed |
| T-12-13 | Repudiation | medium | mitigate | tests/scripts/derive-cgb-speed-expectations.py:23; no core reads/execution; regenerated table and factor3/tamper controls | closed |
| T-12-14 | Tampering | medium | mitigate | tests/scripts/reproduce-cgb-speed.sh:21–25,57–59,80–118,134–144; workflow digest/pin checks; missing-pin/tool-failure controls | closed |
| T-12-15 | Denial of Service | medium | mitigate | tests/CMakeLists.txt:2590–2598 scaler precedes partition registrations at 3474–3493; no later scaler; caps and snapshot controls present | open — non-blocking |
| T-12-16 | Repudiation | medium | mitigate | tests/player/test_limitations.c:10; tests/player/claims_agree.cmake:47–50; hosted player package and mutation controls | closed |
| T-12-17 | Tampering | medium | mitigate | Public-header tokens unchanged after stripping comments; cgb_consumer_symbol_coverage and missing-symbol control | closed |
| T-12-18 | Denial of Service | high | mitigate | tests/fuzz_core.c:15,495,509–527,608–612; eight seeds and inverted-oracle controls | closed |
| T-12-19 | Denial of Service | medium | mitigate | tests/test_age.c:154–164,209; manifest budgets and explicit per-ROM sanitizer-scaled limits | closed |
| T-12-20 | Information Disclosure / Tampering | high | mitigate | cmake/ScanForbiddenFixtures.cmake:44–57; age_not_installed and renamed payload.bin negative; digest/repro tamper controls | closed |
| T-12-21 | Repudiation / Tampering | high | mitigate | tests/scripts/verify-cgb-speed-dispositions.py:67–150; exact signatures/masks; missing-pin and reason-edited controls | closed |
| T-12-22 | Tampering | medium | mitigate | src/core/gabbaboy.c:26,216; tests/test_age.c:515–542; age_stall_window fail/pass/pass/fail boundaries | closed |
| T-12-23 | Repudiation | medium | mitigate | tests/check_no_stale_speed_claims.cmake:5–30; doc contracts/mutated copies; comment-only header diff | closed |
| T-12-24 | Information Disclosure | medium | mitigate | verify-closeout-contract.py:231–235 privacy scan; benchmark host class only; positive plus scratch mutations | closed |
| T-12-25 | Elevation of Privilege | medium | mitigate | verify-closeout-contract.py:220–229; both workflow flags false, no GB-13 directory, exact verification route | closed |
| T-12-26 | Tampering | medium | mitigate | src/core/gabbaboy.c:1427–1431; reset/M24–26 and instance isolation tests | closed |
| T-12-27 | Tampering | high | mitigate | All-entry AGE manifest/rebuild/digest guards; exact hosted receipt for all 13 ROMs in fixtures/age/SOURCES.md | closed |
| T-12-28 | Tampering | medium | mitigate | No noncomment leaked stall literals; macro-derived expectations; age_stall_window precedes derived fixture pins | closed |
| T-12-29 | Denial of Service | medium | mitigate | Bounded AGE driver; measured budgets; TIMEOUT 120/240 sanitizer scaled; timeout negative | closed |
| T-12-30 | Tampering | low | mitigate | tests/test_cgb_speed_fixture.c:19,289–292,355,386; in-memory selector at 0x0200; fixture digest/rebuild controls | closed |
| T-12-31 | Tampering | medium | mitigate | tests/test_cgb_partition.c:357–374,410–415,898–911; independent owned copies; snapshot fidelity/unsupported-pointer negative | closed |
| T-12-32 | Tampering | medium | mitigate | tests/CMakeLists.txt:3153–3184; four AGE sensitivity sweeps plus mutated M28-reference control | closed |
| T-12-SC | Tampering | high | mitigate | No new npm/pip/cargo install commands among changed executable/build/workflow files; digest-pinned RGBDS and unchanged SDL/compiler fuzz path | closed |

## Open Mitigation

T-12-15: the generic sanitizer timeout multiplier runs before the late Phase 12 tests are registered. Partition limits remain 60 seconds instead of the declared 180 seconds under sanitizers. Work caps and snapshot checks exist; hosted ASan passing does not prove this missing policy. All late registrations must be checked, including AGE limits already scaled separately, to prevent double scaling.

## Accepted Risks Log

No accepted risks or transferred threats. No new threat flags were reported in the summaries.

## Verification Evidence and Scope

The current root CTest run passed 897/897 in 36.36 seconds. The auditor inspected all 216 selected speed, partition, AGE, model-gate, consumer and documentation records in that run, plus the player log and exact hosted source receipts. The closeout contract positive case and 17 scratch mutations passed. Public-header tokens are unchanged, private paths/emails are absent from the audited artifacts, and Phase 13 has not started.

Standalone `reproduce-cgb-speed.sh` checks PATH tool versions and executes assemblers before its optional archive digest check. Hosted CI checks the digest before extraction. T-12-14's declared checks are present at ASVS L1; the ordering observation is retained for code-review assessment, without treating it as an accepted risk or fabricated blocker.

AGE outcomes are two passes and eleven pinned expected failures. Byte reproduction and software-model results do not establish hardware qualification. ASVS L1 establishes declared mitigation presence; it is not a new-vulnerability scan or full data-flow audit.

## Security Audit Trail

| Audit date | Revision | Unique threats | Closed | Blocking open | Non-blocking open |
|---|---|---|---|---|---|
| 2026-10-14 | fbfeb24 | 33 | 32 | 0 | 1 |

## Sign-Off

- [x] Every threat has a mitigation disposition and implementation evidence or an explicit gap.
- [x] No accepted risks were invented.
- [x] Severity-filtered `threats_open: 0` confirmed.
- [ ] T-12-15 policy fix verified before phase completion.
