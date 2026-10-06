---
phase: "GB-02"
slug: "dmg-cpu-bus-and-time"
status: blocked
threats_open: 2
asvs_level: 1
created: "2026-10-06"
---

# Phase 2 — Security

The read-only security auditor verified the 29 plan-authored entries at L1. Subsequent corrective testing closed general read preflight and wrap coverage gaps, and exposed an applicability gap in the fixture reporting path. Closed threat entries establish their bounded mitigation, not full CPU/timing conformance; CR-01..04 remain open correctness findings. No requirement or phase completion is implied. Source revision: `c583e33`.

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
| T-02-14 | Tampering | fixture bytes | high | mitigate | Pins and stored digests are recorded, but hosted DAA reproduction differs at byte 335; timer comparisons are not reached. Cross-host reproduction is not qualified. | open |
| T-02-15 | Repudiation | asset license/model claim | high | mitigate | Rights and pins recorded, but all required ROMs read unsupported LY before their advertised completion protocol. Runtime qualification contradicts phase applicability; source-qualified repair required. | open |
| T-02-SC (02-07) | Tampering | WLA-DX tool preparation | high | mitigate | Pinned immutable revision, isolated temp build and verified archive/source; no package-manager install or ordinary network tests. Evidence: matching focused tests and current source boundary. | closed |
| T-02-16 | Tampering | corpus denominator | high | mitigate | Required nonzero immutable IDs, exact executed set, negative skip controls. Evidence: matching focused tests and current source boundary. | closed |
| T-02-17 | Denial of service | runner inputs | high | mitigate | Size, count, path and tick bounds before allocation/execution. Evidence: matching focused tests and current source boundary. | closed |
| T-02-18 | Information disclosure | receipt | medium | mitigate | Relative identity allowlist and reproducibility/privacy tests. Evidence: matching focused tests and current source boundary. | closed |
| T-02-SC (02-08) | Tampering | package installs | low | accept | Plan-authored acceptance: no package-manager install in core tasks; ordinary test jobs use checked-in bytes. Explicit pinned fixture/tool preparation stays in separate reproduction workflow. | closed |
| T-02-19 | Tampering | installed consumer contract | medium | mitigate | Both relocated consumers assert capacity and deterministic input path. Evidence: matching focused tests and current source boundary. | closed |
| T-02-20 | Repudiation | CI inventory | high | mitigate | Exact nonzero inventory, skip/failure/error rejection; synthetic failed/error controls reject, passing control accepts; c583e33. | closed |
| T-02-SC (02-09) | Tampering | package installs | low | accept | Plan-authored acceptance: no package-manager install in core tasks; ordinary test jobs use checked-in bytes. Explicit pinned fixture/tool preparation stays in separate reproduction workflow. | closed |

## Accepted Risks Log

The seven low-severity package-install entries were accepted explicitly in their authored plans (02-02/03/04/05/06/08/09), within the owner-authorized routine decisions. They record that these core tasks introduce no package-manager installation; they do not waive source/tool pins in fixture preparation. No newly discovered correctness or qualification gap is accepted.

## Security Audit Trail

| Date | Total | Closed | Blocking open | Evidence |
|---|---|---|---|---|
| 2026-10-06 | 29 | 27 | 2 | Typed L1 auditor, corrective regressions, source-audited reporting path, local execution and failing hosted evidence |

## Remaining Gate

T-02-14 and T-02-15 remain high-severity OPEN. DAA stops at PC `6958` and the timer cases at PC `4BEB`, executing `F0 44` (LY read). The shared `quit` path probes PPU before its callback and result breakpoint. The fixed three-case corpus is retained, and four required CTests fail. Hosted reproduction also fails and its cause is unresolved. Source metadata and earlier local reproduction are not sufficient eligibility evidence. See `02-VALIDATION.md`, `02-HOSTED-EVIDENCE.md`, and `fixtures/mooneye/SOURCES.md`. Do not complete Phase 2 or advance Phase 3 until qualified.
