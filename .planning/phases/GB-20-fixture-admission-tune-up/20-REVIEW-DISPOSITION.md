---
phase: 20
review: 20-REVIEW.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: fixed
    title: "Drive-qualified archive components could escape extraction on Windows"
  - id: CR-05
    severity: critical
    disposition: fixed
    title: "Release verification can still load a checker selected by tagged build code"
  - id: CR-06
    severity: critical
    disposition: fixed
    title: "A fenced code example satisfies the notice digest table check"
  - id: CR-07
    severity: critical
    disposition: fixed
    title: "Workflow policy accepts an untrusted Python executable through a PATH assignment"
  - id: WR-04
    severity: warning
    disposition: fixed
    title: "Workflow coverage self-test is pinned to the pre-fix policy source"
  - id: WR-05
    severity: warning
    disposition: fixed
    title: "Git blob stream reads have no deadline"
open: 0
total: 6
recorded: 2026-11-01T21:01:30.092Z
---

# Phase 20: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| CR-01 | critical | fixed | 20-REVIEW.md; resolved by 37de7e8a; confirmed by final clean review |
| CR-05 | critical | fixed | 20-REVIEW-FIX.md (not in the current review) |
| CR-06 | critical | fixed | 20-REVIEW-FIX.md (not in the current review) |
| CR-07 | critical | fixed | 20-REVIEW-FIX.md (not in the current review) |
| WR-04 | warning | fixed | 20-REVIEW-FIX.md (not in the current review) |
| WR-05 | warning | fixed | 20-REVIEW-FIX.md (not in the current review) |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
