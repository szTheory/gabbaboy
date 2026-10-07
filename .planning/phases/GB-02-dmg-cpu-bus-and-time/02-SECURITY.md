---
phase: "GB-02"
slug: "dmg-cpu-bus-and-time"
status: verified
threats_open: 0
asvs_level: 1
created: "2026-10-06"
audited: "2026-10-07"
---

# Phase 2 — Security

The read-only security auditor verified the original 29 plan-authored entries at L1. A second audit on 2026-10-07 verified the later Plan 02-13 through 02-17 threats against current code, retained fixture artifacts, local regressions, and fresh hosted checks for PR head `03a22919417303dc9df2906c4135bf5ff124e7aa`; those 41 scoped threats are closed with evidence below. Plan 02-18 adds three mitigation threats that remain open until its CPU-01 semantic tests and final checks pass; its low-severity package-install acceptance is recorded as closed. These fixture and runner mitigations do not establish full CPU/timing conformance or phase completion. Original upstream Mooneye reporting paths remain PPU/LY-dependent and ineligible; the admitted fixtures are documented derived headless variants.

## Trust Boundaries

Guest ROM/opcodes and caller timestamps cross into instance state; finite output buffers cross back to callers. Third-party source/tool bytes cross into checked-in fixtures. Exact CI outcomes and receipts cross into qualification claims. Host filesystem and network remain adapters/tool preparation.

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation evidence | Status |
|---|---|---|---|---|---|---|
| T-02-01 | Tampering | ROM-only bus | high | mitigate | General instruction/fetch/conditional stack read preflight; cross-family atomic rejection regression checks; corrected in 2af612c. | closed |
| T-02-02 | Denial of service | run/trace | high | mitigate | Checked budget and capacity preflight with canary tests. Evidence: matching focused tests and current source boundary. | closed |
| T-02-SC (02-01) | Tampering | tool preparation | high | mitigate | Reuse pinned digest and safe temporary extraction; no ordinary network test dependency. Evidence: matching focused tests and current source boundary. | closed |
| T-02-03 | Denial of service | opcode loop | high | mitigate | Exhaustive decode classification, bounded lockup and budget checks. Evidence: matching focused tests and current source boundary. | closed |
| T-02-04 | Tampering | stack/address math | medium | mitigate | Explicit wrapping stack/address guest regressions plus timed byte-order observations; 2af612c. | closed |
| T-02-SC (02-02) | Tampering | package installs | low | accept | Plan-authored acceptance: no package-manager install in core tasks; ordinary test jobs use checked-in bytes. Explicit pinned fixture/tool preparation stays in separate reproduction workflow. | closed |
| T-02-05 | Tampering | CB memory operation | medium | mitigate | Full-cost preflight and BIT read-only/RES write tests. Evidence: matching focused tests and current source boundary. | closed |
| T-02-06 | Denial of service | CB decoder | medium | mitigate | Full 256-byte inventory and finite per-instruction cost. Evidence: matching focused tests and current source boundary. | closed |
| T-02-SC (02-03) | Tampering | package installs | low | accept | Plan-authored acceptance: no package-manager install in core tasks; ordinary test jobs use checked-in bytes. Explicit pinned fixture/tool preparation stays in separate reproduction workflow. | closed |
| T-02-07 | Denial of service | HALT/STOP/lockup | high | mitigate | Bounded idle time and distinct stopped outcomes in named tests. Evidence: matching focused tests and current source boundary. | closed |
| T-02-08 | Tampering | interrupt stack | medium | mitigate | Full-entry bounds preflight and stack byte-order/vector regressions. The independent diagnostic chronology defect remains open as CR-04; this closure covers bounded stack mutation. | closed |
| T-02-SC (02-04) | Tampering | package installs | low | accept | Plan-authored acceptance: no package-manager install in core tasks; ordinary test jobs use checked-in bytes. Explicit pinned fixture/tool preparation stays in separate reproduction workflow. | closed |
| T-02-09 | Denial of service | timer deadline loop | high | mitigate | Monotonic checked time, finite work per tick, bounded call budget. Evidence: matching focused tests and current source boundary. | closed |
| T-02-10 | Tampering | timer reload collision | medium | mitigate | Exact boundary cases and explicit write/deadline order. Evidence: matching focused tests and current source boundary. | closed |
| T-02-11 | Denial of service | external serial pending | medium | mitigate | Pending state returns boundedly until explicit edge input. Evidence: matching focused tests and current source boundary. | closed |
| T-02-SC (02-05) | Tampering | package installs | low | accept | Plan-authored acceptance: no package-manager install in core tasks; ordinary test jobs use checked-in bytes. Explicit pinned fixture/tool preparation stays in separate reproduction workflow. | closed |
| T-02-12 | Tampering | event queue | high | mitigate | Atomic batch validation, fixed capacity and tie-order tests. Evidence: matching focused tests and current source boundary. | closed |
| T-02-13 | Denial of service | uint64 time/output | high | mitigate | Checked arithmetic, preflighted slots, canaries and finite progress tests. Evidence: matching focused tests and current source boundary. | closed |
| T-02-SC (02-06) | Tampering | package installs | low | accept | Plan-authored acceptance: no package-manager install in core tasks; ordinary test jobs use checked-in bytes. Explicit pinned fixture/tool preparation stays in separate reproduction workflow. | closed |
| T-02-14 | Tampering | fixture bytes | high | mitigate | Deterministic `wlalink -nS -d -S` recipe resolves the prior DAA byte-335 difference; retained run 37561292904 compares all three local Darwin/arm64 and hosted Linux/x86_64 byte arrays, sizes, and digests. Fresh exact-current-SHA fixture run 37620710600 also passed. | closed |
| T-02-15 | Repudiation | asset license/model claim | high | mitigate | Source/rights audit and derived reporting patch retain upstream assertions while removing the PPU-dependent pre-callback path. Prior positive probes and induced DAA failure reached callback then `LD B,B` with zero PPU accesses; current exact-SHA fixture run 37620710600 passed. Original upstream reporting paths remain ineligible. | closed (derived fixtures only) |
| T-02-24 | Tampering | WLA reproduction | high | mitigate | Immutable source/tool/font identities and deterministic linker option are checked; local/hosted comparisons cover every output byte and digest, and mismatch artifacts are retained. Exact candidate run 37561292904 and fresh PR-head fixture run 37574747612 passed. | closed |
| T-02-25 | Repudiation | Mooneye applicability | high | mitigate | Pinned source/include closure, rights notices, and derived patch are reviewed; positive and induced-negative probes verify callback/result order and zero PPU accesses. The strict admitted set uses only the documented derived variants. | closed (derived fixtures only) |
| T-02-26 | Tampering | final corpus bytes/denominator | high | mitigate | Strict manifest/lock checks enforce the fixed three-ROM set, one CPU and two timer IDs, per-ROM sizes/digests, and reject missing or changed bytes. `VerifyMooneye.cmake` and the complete runner inventory pass. | closed |
| T-02-27 | Repudiation | runner result claim | high | mitigate | Runner requires each fixture's real callback, exact symbol-addressed result PC, expected registers, and induced-failure rejection; receipts bind revision, digest, profile, denominator, and bounded diagnostics. Focused runner/Mooneye tests pass 17/17. | closed |
| T-02-28 | Repudiation | runner corpus claim | high | mitigate | Exact eligible/executed inventory and fixed denominator are enforced with negative controls and revision-linked bounded receipts. The exact-head hosted gate passed all explicit Phase 2 contexts and required jobs. | closed |
| T-02-29 | Tampering | WLA-DX recipe and candidate bytes | high | mitigate | Pinned upstream/tool inputs, deterministic linker option, candidate patch, and all three output digests are checked against full local/hosted byte arrays; retained run 37561292904 and fresh exact-head run 37574747612 passed. | closed |
| T-02-30 | Repudiation | fixture admission evidence | high | mitigate | Promotion now binds the mutable lock to the exact Git lock blob and retained artifact, head, run ID, three ROM byte arrays, source/rights/protocol records, and manifest gate. Tampered-lock and local-byte mismatch self-tests reject; exact-head hosted CI and fixture jobs passed. | closed |
| T-02-SC (02-07) | Tampering | WLA-DX tool preparation | high | mitigate | Pinned immutable revision, isolated temp build and verified archive/source; no package-manager install or ordinary network tests. Evidence: matching focused tests and current source boundary. | closed |
| T-02-16 | Tampering | corpus denominator | high | mitigate | Required nonzero immutable IDs, exact executed set, negative skip controls. Evidence: matching focused tests and current source boundary. | closed |
| T-02-17 | Denial of service | runner inputs | high | mitigate | Size, count, path and tick bounds before allocation/execution. Evidence: matching focused tests and current source boundary. | closed |
| T-02-18 | Information disclosure | receipt | medium | mitigate | Relative identity allowlist and reproducibility/privacy tests. Evidence: matching focused tests and current source boundary. | closed |
| T-02-SC (02-08) | Tampering | package installs | low | accept | Plan-authored acceptance: no package-manager install in core tasks; ordinary test jobs use checked-in bytes. Explicit pinned fixture/tool preparation stays in separate reproduction workflow. | closed |
| T-02-19 | Tampering | installed consumer contract | medium | mitigate | Both relocated consumers assert capacity and deterministic input path. Evidence: matching focused tests and current source boundary. | closed |
| T-02-20 | Repudiation | CI inventory | high | mitigate | Exact nonzero inventory, skip/failure/error rejection; synthetic failed/error controls reject, passing control accepts; c583e33. | closed |
| T-02-SC (02-09) | Tampering | package installs | low | accept | Plan-authored acceptance: no package-manager install in core tasks; ordinary test jobs use checked-in bytes. Explicit pinned fixture/tool preparation stays in separate reproduction workflow. | closed |
| T-02-SC (02-13) | Tampering | ordinary test fixture/tool supply | low | accept | Plan-authored acceptance: ordinary tests use digest-verified checked-in fixtures and existing pinned tools; source/tool reproduction stays separate, with no ordinary-test network dependency. | closed |
| T-02-SC (02-14) | Tampering | ordinary test fixture/tool supply | low | accept | Plan-authored acceptance: ordinary tests use digest-verified checked-in fixtures and existing pinned tools; source/tool reproduction stays separate, with no ordinary-test network dependency. | closed |
| T-02-SC (02-15) | Tampering | ordinary test fixture/tool supply | low | accept | Plan-authored acceptance: ordinary tests use digest-verified checked-in fixtures and existing pinned tools; source/tool reproduction stays separate, with no ordinary-test network dependency. | closed |
| T-02-SC (02-16) | Tampering | ordinary test fixture/tool supply | low | accept | Plan-authored acceptance: ordinary tests use digest-verified checked-in fixtures and existing pinned tools; source/tool reproduction stays separate, with no ordinary-test network dependency. | closed |
| T-02-SC (02-17) | Tampering | fixture/tool supply chain | high | mitigate | Pinned WLA-DX source/archive, Mooneye MIT notice, replacement-font rights, and reviewed candidate patch identity are retained; hosted reproduction verifies all candidate bytes. No unpinned install or fixture source is admitted. | closed |
| T-02-31 | Tampering | base opcode expected vectors | high | mitigate | `tests/test_cpu.c` uses an independently authored state model and fixed per-opcode architectural assertions; arithmetic/address/branch expected values do not come from core output. The clean 02-18 review confirmed the oracle is independent. | closed |
| T-02-32 | Denial of service | legal opcode test matrix | medium | mitigate | Base matrix uses finite ROMs, fixed trace/event arrays, bounded loops, and explicit finite `gbb_run` budgets. Branch and address vectors also use fixed buffers and budgets. | closed |
| T-02-33 | Repudiation | CPU-01 qualification evidence | high | mitigate | At implementation SHA `cf28e90270be24d9528bfa8a1e4055a2b8485989`, local inventory passed 104/104, installed consumers/inventory passed 109/109, exact PR CI run 37620710587 passed after a transient pre-configuration HTTP 500 rerun, and fixture reproduction run 37620710600 passed. The security auditor confirmed the workspace head matches the qualified SHA. | closed |
| T-02-SC (02-18) | Tampering | package installs | low | accept | Plan-authored acceptance: no package-manager install is part of this test-only plan; ordinary tests remain offline and use owned vectors. | closed |

## Accepted Risks Log

The twelve low-severity package-install entries were accepted explicitly in their authored plans (02-02/03/04/05/06/08/09 and 02-13/14/15/16/18), within the owner-authorized routine decisions. They record that ordinary tests introduce no package-manager installation or network dependency; they do not waive source/tool pins in fixture preparation. No newly discovered correctness or qualification gap is accepted.

## Security Audit Trail

| Date | Total | Closed | Blocking open | Evidence |
|---|---|---|---|---|
| 2026-10-06 | 29 | 27 | 2 | Typed L1 auditor, corrective regressions, source-audited reporting path, local execution and failing hosted evidence |
| 2026-10-07 (Plan 02-18 intake; not an audit) | 45 | 42 | 3 | Plan 02-18 threat model added; T-02-31 through T-02-33 await implementation and security audit; T-02-SC (02-18) accepted |

## Remaining Gate

The 2026-10-06 audit remains as historical evidence of the earlier unsupported-LY and cross-host-byte failures. Plans 02-13 through 02-17 resolved those fixture gates for the derived headless variants, and the 2026-10-07 audits closed the mapped threats on current code and exact-head hosted evidence. The original upstream ROM reporting paths remain ineligible, and no physical DMG hardware run is claimed. Phase requirements remain for the independent phase verifier; this security record does not imply requirement completion.

## Security Audit 2026-10-07

| Metric | Count |
|---|---|
| Threats found | 41 |
| Closed | 41 |
| Open | 0 |

## Security Audit 2026-10-07

| Metric | Count |
|---|---|
| Threats found | 45 |
| Closed | 45 |
| Open | 0 |
