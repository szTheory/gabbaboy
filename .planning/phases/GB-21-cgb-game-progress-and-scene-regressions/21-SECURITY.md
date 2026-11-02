---
phase: "21"
slug: "cgb-game-progress-and-scene-regressions"
status: verified
threats_open: 0
asvs_level: 1
block_on: high
created: "2026-11-02"
---

# Phase 21 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Local acceptance runner | Guest ROM, scripted input and predicate enter the emulator runner and produce receipts/observations. | Project-authored or admitted ROM bytes, bounded input, predicate identity, RGB555/PCM observations |
| Candidate source admission | Candidate source, build outputs and notices must be tied to immutable source/build identities and checked before runner use. | Candidate metadata, source files, ROM, build result and rights evidence |
| Upstream build isolation | Any upstream build execution is permitted only after a disposable restricted environment and denial probes are established. | Pinned source/toolchain, scrubbed environment, bounded writable output |
| Scene-report intake and promotion | Local owner-provided text may be read from ignored storage; only independently reproduced behavior can become a tracked regression expectation. | Bounded report text, source-bound reproduction, independent expectation and private-media exclusion |
| Hosted qualification | CI and installed-consumer results qualify the exact reviewed source head; they do not confer game-source rights or hardware accuracy. | Commit identity, test results, installed package behavior |

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-21-01 | Spoofing | CGB progress runner | high | mitigate | Bind input, ROM, mode, profile, predicate and source identity into the runner receipt (`src/runner/acceptance.c:1069,1098,1176`; `verify-cgb-progress.py:277`). | closed |
| T-21-02 | Tampering | Predicate and mode selection | high | mitigate | Bind predicates to ROM digests and anchors; preserve existing Libbet gates (`src/accept/predicate.c:76,123,131`; `src/runner/acceptance.c:1105,1268`). | closed |
| T-21-03 | Tampering | Negative progress controls | high | mitigate | Require raw predicate-not-reached failures, expected final state and empty stderr; separately validate xfail behavior (`verify-cgb-progress.py:765,827,840`). | closed |
| T-21-04 | Spoofing | Observation and dump evidence | high | mitigate | Validate source-derived PPM pixels, receipt/observation identity, digests, timing and failure dumps (`verify-cgb-progress.py:256,277,382,860`). | closed |
| T-21-05 | Spoofing | Candidate record order and closure | high | mitigate | Fix candidate identities/order and permitted final states; reject extra records and missing attempts (`verify-cgb-candidates.py:36,287,1141,1157`). | closed |
| T-21-06 | Tampering | Candidate build and admission | high | mitigate | Require confined-build probes and bind manifest, ROM, source, build and progress before admission (`verify-cgb-candidates.py:329,811,887,1043,1116`). | closed |
| T-21-07 | Spoofing | Potion Panic rights/source evidence | high | mitigate | Record the author-linked source and rights cutoff before upstream execution; reject downstream fact inflation (`potion-panic.json:120`; `verify-cgb-game-evidence.py:251`). | closed |
| T-21-08 | Elevation of privilege | Upstream build execution | high | mitigate | Stop before upstream execution unless scrubbed environment, privilege, mounts and both denial probes are established (`potion-panic.json:130`; `verify-cgb-candidates.py:329,585`). | closed |
| T-21-09 | Tampering | Fixture admission boundary | high | mitigate | Delegate to Phase 20 immutable admission before runner use; enforce full commit syntax, ancestry, manifest, blobs and notices (`verify-cgb-candidates.py:887,1127`; `verify-fixture-admission.py:759`). | closed |
| T-21-10 | Spoofing | µCity fallback eligibility | high | mitigate | Validate immutable primary references and require the primary no-go before fallback disposition; fix fallback identity (`verify-cgb-candidates.py:917,937,1008`; `ucity-1.3.json:2015`). | closed |
| T-21-11 | Elevation of privilege | µCity build execution | high | mitigate | Keep fallback at pre-execution no-go unless the same credential-free isolation and denial probes pass (`ucity-1.3.json:2013`; `verify-cgb-candidates.py:329,585,1723`). | closed |
| T-21-12 | Tampering | Fallback evidence composition | high | mitigate | Bind source/build/ROM/progress to the Phase 20 manifest and preserve unobserved facts after fallback no-go (`verify-cgb-candidates.py:811,1116`; `verify-cgb-game-evidence.py:265`). | closed |
| T-21-13 | Information disclosure | Scene-report intake | high | mitigate | Confine reports to ignored local storage, use safe permissions, bound reads and reject private-media promotion (`verify-scene-report.py:230,296,325,474,627`). | closed |
| T-21-14 | Tampering | Scene-report promotion | high | mitigate | Require source-bound reproduction, an independent committed expectation and a causal negative (`verify-scene-report.py:619,662,703,1037`). | closed |
| T-21-15 | Spoofing | Game-evidence claims | high | mitigate | Check actual no-go causes and unobserved facts; reject unsupported game, accuracy, hardware and license-prohibition claims (`verify-cgb-game-evidence.py:236,399,408,514+`). | closed |
| T-21-16 | Tampering | Source-bound game result | high | mitigate | Compare source files to immutable blobs and bind runner, receipt and observations; exact PR head `a05a0b12e9b1e4bf4b1901b7c81b6160df3688b4` passed hosted CI, fixture and installed-consumer checks (`verify-cgb-game-evidence.py:136,696`; runs `41474032142`, `41474032137`, `41474032193`). | closed |
| T-21-17 | Repudiation | Phase evidence and closure | medium | mitigate | Preserve all 18 exact summary coverage rows in generated UAT; shared checker validates evidence mapping and rejects weakened closures (`21-UAT.md`; `verify-uat-closure.py:131,174`). Keep FIXT-01 pending and unresolved prohibitions visible. | closed |
| T-21-SC | Tampering | Source pin and helper dependencies | high | mitigate | Use existing standard-library helpers, do not execute upstream tools, and require full immutable commit/blob pin checks (`verify-fixture-admission.py:134,767`). | closed |

*Status: open · closed · open — below high threshold (non-blocking)*

## Accepted Risks Log

No accepted risks.

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-11-02 | 18 unique (24 plan entries; T-21-SC repeats) | 18 | 0 | gsd-security-auditor, ASVS L1 |

The exact-head qualification boundary is `a05a0b12e9b1e4bf4b1901b7c81b6160df3688b4`. The report does not assert later PR ancestry. Neither candidate game was admitted or run; no rights clearance or hardware/compatibility qualification is claimed. There are no unregistered threat flags.

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-11-02
