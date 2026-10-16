---
phase: "14"
slug: "cgb-e-model-qualification-and-corpus"
status: verified
threats_total: 27
threats_closed: 27
threats_open: 0
asvs_level: 1
block_on: high
register_authored_at_plan_time: true
created: "2026-10-15"
evidence_revision: "f8260549009f3150dc82de801373f40de3a02aa0"
---

# Phase 14 — Security

The independent security auditor verified every declared mitigation at ASVS L1: 27 closed, zero open, zero accepted or transferred risks. This verifies the authored threat register and its native offline boundaries. It does not claim exact-current-head hosted CI, physical hardware, analog/perceptual output, IR peers, game acceptance or Phase 15 release readiness.

## Trust Boundaries

| Boundary | Required protection |
| --- | --- |
| Guest/ROM/manifest to native harness | Explicit finite input, observation, execution and output bounds; exact model/mode and source identities |
| Source/fixture/tool to admitted corpus | Independent frozen membership, redistribution evidence, source/tool/archive/output pins and intended tamper rejection |
| Observation/CTest to qualification receipt | Independent expected values, terminal membership, actual outcome versus evaluator disposition, input stamp and fresh run identity |
| Receipt/docs/package to public claim | Semantic claims, fixture-byte exclusion and allowlisted privacy-safe artifacts |

## Threat Register

All rows have severity **high**, disposition **mitigate** and status **closed**. IDs and categories come from the 13 plan-time registers; T-14-SC is defined once in plan 14-05.

| Threat ID | Category | Actual mitigation evidence | Status |
| --- | --- | --- | --- |
| T-14-01 | Tampering | `src/core/gabbaboy.c:612,642,1380`; `tests/test_cgb_apu.c:110,340,356,374`: independent digital output, nibble packing, routing and write mutants | closed |
| T-14-02 | Denial of service | `tests/test_cgb_apu.c:184,623`; `src/runner/main.c:261`: bounded guest calls, output pressure and hostile seeds | closed |
| T-14-03 | Tampering | `src/core/gabbaboy.c:1348,1376`; `tests/test_cgb_visibility.c:614,706,729`: explicit IR/port mode cells and defect twins | closed |
| T-14-04 | Denial of service | `tests/test_cgb_visibility.c:653,676,683`: reset/load preservation, wrong-state controls and fixed observation buffers | closed |
| T-14-05 | Tampering | `src/core/gabbaboy.c:568,1701,3278`; `tests/test_cgb_apu.c:448,470,497,521`: CH3 latch/fetch and transition predicates | closed |
| T-14-06 | Denial of service | `tests/test_cgb_apu.c:623`: finite transition execution, output pressure and hostile-seed checks | closed |
| T-14-07 | Tampering | `tests/test_cgb_partition.c:754,881,942,995`: guest traces, private-state comparison, lost-remainder and duplicate-fetch controls | closed |
| T-14-08 | Denial of service | `tests/test_cgb_partition.c:766,803,1073,1131`: finite partition work, lifecycle preservation and corruption controls | closed |
| T-14-09 | Tampering | `tests/scripts/verify-cgb-corpus-inventory.py:24,108,118,130`: independent rosters, source pins and source/output/case digests | closed |
| T-14-10 | Denial of service | `tests/scripts/verify-cgb-corpus-inventory.py:95,108,136`: bounded input/path/roster parsing and oversized-input controls | closed |
| T-14-SC | Tampering | `tests/scripts/reproduce-age.sh:52,59,308`; `reproduce-mooneye-cgb.sh:123`; `reproduce-samesuite.sh:95`: source/tool/archive/asset pins; no new package install in reviewed build/workflow paths | closed |
| T-14-11 | Tampering | `src/runner/main.c:169,304,353`; `tests/scripts/reproduce-mooneye-cgb.sh:194`: pinned ROM identity and exact guest callback/register signatures | closed |
| T-14-12 | Denial of service | `src/runner/main.c:145,172,261,360`: manifest/ROM size, guest budgets and terminal bounds | closed |
| T-14-13 | Tampering | `tests/test_samesuite_apu.c:146,220,299,322`: exact 70-case roster, manifest/disposition/ROM hashes and failure signatures | closed |
| T-14-14 | Denial of service | `tests/test_samesuite_apu.c:10,15,119,238,263`: finite input/run calls/budget and mandatory terminal verdict | closed |
| T-14-15 | Tampering | `tests/scripts/reproduce-age.sh:229,262,337,343`: exact source, ROM, header and reference-image identity | closed |
| T-14-16 | Denial of service | `tests/scripts/verify-age-phase14-contract.py:155,181`; `verify-age-m3-pixels.py:80,106`: bounded paths, rows, budgets and image decoding | closed |
| T-14-17 | Tampering | `tests/test_age_m3.c:27,131`; `tests/scripts/verify-age-m3-pixels.py:332,354,367,385`: mode/header identity, terminal metadata and complete reference comparison | closed |
| T-14-18 | Denial of service | `tests/test_age_m3.c:13,59`; `tests/scripts/verify-age-m3-pixels.py:37,123,182,210`: ROM/frame/run/decompression bounds and early-frame rejection | closed |
| T-14-19 | Tampering | `tests/test_age.c:443,462,473`; `tests/scripts/verify-age-phase14-contract.py:194,216,297`: independent source row IDs/bytes, masks and exact signatures | closed |
| T-14-20 | Denial of service | `tests/test_age.c:29,133,164,547`; `tests/scripts/verify-age-phase14-contract.py:181,183,185`: finite row/address/budget and hostile-fixture controls | closed |
| T-14-21 | Tampering | `tests/scripts/verify-cgb-corpus-report.py:388,552,564,671,1251`: executable/input/build identity, nonce-bound streams and exact normalized membership | closed |
| T-14-22 | Denial of service | `tests/scripts/verify-cgb-corpus-report.py:25,603,1433,1577,1833`: finite XML/events/output, timeout termination, atomic receipts and stale-green invalidation | closed |
| T-14-23 | Tampering | `.github/workflows/ci.yml:51,55,58,64,93`: one nonce-bound stream shared by receipt, required inventory and DMG checks | closed |
| T-14-24 | Denial of service | `.github/workflows/ci.yml:55`; `cmake/ScanForbiddenFixtures.cmake:79,89,157`: finite capture and hash-based ROM/PNG exclusion with renamed-fixture controls | closed |
| T-14-25 | Tampering | `tests/scripts/verify-cgb-corpus-claims.py:141,183,250,297,407`: semantic mode matrix, independent expectations and receipt-derived counts | closed |
| T-14-26 | Denial of service | `tests/scripts/verify-cgb-corpus-artifacts.py:14,37,51,74`: finite public artifacts, privacy/path rejection and explicit upload allowlist | closed |

## Verification Evidence

The auditor ran 40 focused native/parser/receipt/claim/package positive and negative checks, all passing. Its `LastTest.log` contains 34 `Test Passed.` records and six `Test Pass Reason:` records, with zero failed records. The independently inspected Wave 11 JUnit has 1,136 passing cases, zero failures/errors/skips and SHA-256 `ab6b02a9b515499bcd406c9dd1311757c48143e24bf7dca7c16e5a8dbd5496b0`.

The complete receipt binds source `f8260549009f3150dc82de801373f40de3a02aa0`: 107/107 completed cases, 25 actual passes, 82 matched expected failures, 2,845/4,959 passing assertion rows and 18,208/138,240 mismatching image pixels. At that audit, subsequent qualification commits had changed metadata only; the unrelated CMake blank line was preserved. These are software-model observations, not hardware passes.

Original execution IDs and the privacy RED limitation are retained in [14-HISTORY-REDACTION.md](14-HISTORY-REDACTION.md). Task 14-12-3's absent pre-implementation RED is an explicit process deviation, not reconstructed evidence. Current positive/negative runtime mitigations remain independently verified.

## Accepted Risks Log

No accepted risks. No transfers. No additional unregistered threat flags were identified in the reviewed summary deviations.

## Sign-Off

- [x] All 27 plan-time threats retain their mitigation disposition and concrete implementation evidence.
- [x] Independent focused controls and the source-bound full stream were checked.
- [x] `threats_open: 0`; no risk acceptance inferred.
- [x] `status: verified`; no phase advancement or release claim follows from this document alone.

## Security Audit 2026-10-16

| Metric | Count |
|---|---|
| Threats found | 27 |
| Closed | 27 |
| Open | 0 |

## Post-review tooling changes

Independent code review subsequently found two Windows portability blockers in the existing report adapter. The native executable suffix fix and bounded Windows pipe reader retain the T-14-21 identity checks and T-14-22 finite output/deadline boundaries. Their eight positive/negative controls and all 13 report-contract tests passed; an independent recheck closed both findings without a new material issue. The final full regression at actual producer `0018d4a9b8bfa0e60890be7fb3386b73601e0eb2` passed 1,136/1,136 with no skips and rebuilt the complete 107-case receipt; see `14-CLOSURE.md` for source-bound hashes. The register remains 27 closed and zero open. Local Windows behavior was simulated; hosted native Windows execution is a separate exact-head check.

## Incremental security audit after hosted portability findings

The independent security auditor rechecked the adapter delta through `e373b3f2b32292035531ba0aad1d05e5a4a009d9`: **SECURED, 27/27 closed, zero open**, ASVS L1, block on high. No risk acceptance, transfer or new unregistered threat was introduced. Configured executable/CTest identity and the real-stamp mutation retain T-14-21; bounded Windows reads, a two-entry queue, deadlines and cleanup retain T-14-22. Portable bounded AGE identities and integer child deadlines retain T-14-19/T-14-20. Byte-preserving manifest copy/hash equality retains T-14-11, and narrow LF attributes with isolated autocrlf controls retain T-14-SC. APU roster, digest and bounds checks remain enforced; the other 19 registered threats are unchanged.

Fresh audit controls passed eight suffix/reader tests, two inherited AGE tests and the isolated Git LF/CRLF control. The auditor's initial nine-CTest selection passed seven and rejected two stale producer checks before configure/build (`event-identity-mismatch`, `build-input-stamp-mismatch`). This sequencing error remains recorded; a fresh parent configure/build/full stream must supersede that stale attempt. Neither that audit nor earlier simulated platform checks claim final hosted Windows, floor or sanitizer success.

After the final fixes, the parent refreshed configure/build and reran the affected identity, reader/configuration, LF/CRLF, AGE/path/deadline and manifest controls: **10/10 CTests passed**, including the two previously stale producer checks. All **13** corpus-report unit tests passed. This supersedes the audit's stale-build attempt with fresh evidence; the scheduled full stream remains the aggregate producer proof.
