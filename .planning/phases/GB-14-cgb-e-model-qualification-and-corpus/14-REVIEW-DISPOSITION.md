---
phase: 14
review: 14-REVIEW.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: fixed
    title: "Build stamp looks up extensionless executable names on Windows"
  - id: CR-02
    severity: critical
    disposition: fixed
    title: "Bounded subprocess reader cannot register Windows pipes"
  - id: CR-03
    severity: critical
    disposition: fixed
    title: "Configured builds fall back to the default build directory"
  - id: CR-04
    severity: critical
    disposition: fixed
    title: "Windows checkout rewrites raw-digested source bytes"
  - id: CR-05
    severity: critical
    disposition: fixed
    title: "AGE row identity uses a slash-only basename"
  - id: CR-06
    severity: critical
    disposition: fixed
    title: "Missing-ROM control rewrites the pinned manifest"
  - id: CR-07
    severity: critical
    disposition: fixed
    title: "Build stamp fingerprints a different CTest than its consumers"
  - id: CR-08
    severity: critical
    disposition: fixed
    title: "AGE child deadline ignores sanitizer slowdown"
open: 0
total: 8
recorded: 2026-10-16T03:11:51.570Z
---

# Phase 14: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| CR-01 | critical | fixed | 14-REVIEW-FIX.md |
| CR-02 | critical | fixed | 14-REVIEW-FIX.md |
| CR-03 | critical | fixed | 14-REVIEW-FIX.iter2.md |
| CR-04 | critical | fixed | 14-REVIEW-FIX.iter2.md |
| CR-05 | critical | fixed | 14-REVIEW-FIX.iter2.md |
| CR-06 | critical | fixed | 14-REVIEW-FIX.iter2.md |
| CR-07 | critical | fixed | 14-REVIEW-FIX.iter3.md |
| CR-08 | critical | fixed | 14-REVIEW-FIX.iter4.md |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
