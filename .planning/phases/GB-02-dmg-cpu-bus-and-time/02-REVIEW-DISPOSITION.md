---
phase: 02
review: 02-REVIEW.md
titles: json
findings:
  - id: IN-01
    severity: info
    disposition: deferred
    title: "Player-gating condition duplicated in two places"
  - id: CR-01
    severity: critical
    disposition: fixed
    title: "BLOCKER — Promotion trusts mutable candidate digests as hosted evidence"
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "Protocol probe accepts callback records after the result breakpoint"
  - id: CR-02
    severity: critical
    disposition: fixed
    title: "BLOCKER — Unconditional RET and RETI read the stack one machine cycle late"
  - id: CR-03
    severity: critical
    disposition: fixed
    title: "BLOCKER — Repeated EI postpones IME for an extra instruction"
  - id: CR-04
    severity: critical
    disposition: fixed
    title: "BLOCKER — Interrupt diagnostics can violate chronological order"
  - id: CR-05
    severity: critical
    disposition: fixed
    title: "BLOCKER — The required Mooneye corpus cannot reach its declared result protocol"
open: 0
total: 7
recorded: 2026-10-10T12:51:28.698Z
---

# Phase 02: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| IN-01 | info | deferred | Info-only maintainability note; both `pull_request` conditions agree today and drift would fail closed or be caught by required checks. Deferred because `ci.yml` is a covered input of the Phase 1, 2, 3 and 6 VERIFICATION reports — editing it in a docs-only freshness refresh would re-stale four reports. Revisit with the next intentional CI change. |
| CR-01 | critical | fixed | `verify-mooneye-unadmitted.sh:54-118` binds committed Git lock, retained hosted lock/report, local ROMs, exact run ID and all three hosted ROM bytes; its self-test rejects mutable-lock and local-byte tampering. (not in the current review) |
| WR-01 | warning | fixed | `probe-mooneye-candidate.sh:25-76` stops trace processing at the result breakpoint and rejects callback-after-result; `--self-test-order` proves both orders. (not in the current review) |
| CR-02 | critical | fixed | Retained `cpu_return_phases` regression; full Phase 1 CTest suite passed 100/100. (not in the current review) |
| CR-03 | critical | fixed | Retained `interrupt_ei_chain` regression; full Phase 1 CTest suite passed 100/100. (not in the current review) |
| CR-04 | critical | fixed | Retained `interrupt_diagnostic_order` regression; full Phase 1 CTest suite passed 100/100. (not in the current review) |
| CR-05 | critical | fixed | Exact hosted candidate run 37561292904 plus full Phase 2 runner suite; all 100 Phase 1 CTest cases passed. (not in the current review) |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
