---
phase: 16
review: 16-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: deferred
    title: "Release reuses a performance receipt from an unauthenticated rehearsal-branch artifact"
  - id: WR-02
    severity: warning
    disposition: deferred
    title: "Phase 8 boundary pinned by a mutable tag with no expected-SHA assertion"
  - id: WR-03
    severity: warning
    disposition: deferred
    title: "`check_final_receipt` silently collapses duplicate `SHA256SUMS` entries"
  - id: WR-04
    severity: warning
    disposition: deferred
    title: "Test-budget ratchet does not bound new allowlist rows"
  - id: WR-05
    severity: warning
    disposition: deferred
    title: "Plan-cap check can be bypassed by plan file names and does not enforce the 4-phase limit"
  - id: IN-01
    severity: info
    disposition: deferred
    title: "Retry replaces regenerated evidence with the attached bytes before the recovery judge reads them"
  - id: IN-02
    severity: info
    disposition: deferred
    title: "Required-check app identity is a wildcard at PR time but hard-coded at release time"
  - id: IN-03
    severity: info
    disposition: deferred
    title: "`report-red` has no job timeout, and its dedupe search matches on a title phrase"
  - id: IN-04
    severity: info
    disposition: deferred
    title: "Weak or incomplete controls in the perf-gate runner and the HDMA lane self-test"
open: 0
total: 9
recorded: 2026-10-26T15:17:26.232Z
---

# Phase 16: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-01 | warning | deferred | RM-030: Phase 17 entry item (Phase 16 closed to code; fix rounds spent) |
| WR-02 | warning | deferred | RM-030: Phase 17 entry item (Phase 16 closed to code; fix rounds spent) |
| WR-03 | warning | deferred | RM-030: Phase 17 entry item (Phase 16 closed to code; fix rounds spent) |
| WR-04 | warning | deferred | RM-030: Phase 17 entry item (Phase 16 closed to code; fix rounds spent) |
| WR-05 | warning | deferred | RM-030: Phase 17 entry item (Phase 16 closed to code; fix rounds spent) |
| IN-01 | info | deferred | RM-030: Phase 17 entry item (Phase 16 closed to code; fix rounds spent) |
| IN-02 | info | deferred | RM-030: Phase 17 entry item (Phase 16 closed to code; fix rounds spent) |
| IN-03 | info | deferred | RM-030: Phase 17 entry item (Phase 16 closed to code; fix rounds spent) |
| IN-04 | info | deferred | RM-030: Phase 17 entry item (Phase 16 closed to code; fix rounds spent) |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
