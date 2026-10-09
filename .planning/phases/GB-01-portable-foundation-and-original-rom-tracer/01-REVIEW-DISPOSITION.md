---
phase: 01
review: 01-REVIEW.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: fixed
    title: "ROM-only sizes above 32 KiB are accepted but mapped incorrectly"
  - id: CR-02
    severity: critical
    disposition: fixed
    title: "Artifact path checks do not validate archive link targets"
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "RGBDS release archive is version-named but not digest-pinned"
open: 0
total: 3
recorded: 2026-10-03T17:31:34.594Z
---

# Phase 01: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| CR-01 | critical | fixed | 01-REVIEW-FIX.md (not in the current review) |
| CR-02 | critical | fixed | 01-REVIEW-FIX.md (not in the current review) |
| WR-01 | warning | fixed | 01-REVIEW-FIX.md (not in the current review) |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.

## Supplemental re-review history

The current review is clean. The following warnings were found and resolved during the 2026-10-09 incremental review cycle; the reviewer reused `WR-01` and `WR-02` for the final recheck, so titles and review narrative are the disambiguators rather than IDs alone.

| Review finding | Disposition | Resolution evidence |
|----------------|-------------|---------------------|
| Earlier `WR-01`: double-reset run side effects were not asserted | fixed | `01-REVIEW.md` → Historical Supplemental Findings; reset-run outcome, budget, trace bounds, and RAM are asserted after each run. |
| Earlier `WR-02`: identical concurrent workloads could mask state interference | fixed | `01-REVIEW.md` → Historical Supplemental Findings; distinct guest immediates and RAM outcomes exercise per-instance independence. |
| Earlier `WR-03`: concurrent-instance test had no host watchdog | fixed | `01-REVIEW.md` → Historical Supplemental Findings; CTest applies a 30-second timeout to `concurrent_independent_instances`. |
| Final `WR-01`: partial Windows thread creation could destroy an in-use instance | fixed | `01-REVIEW.md` → Recheck Outcome; failure path releases, joins, and closes the created worker before destroying instances. |
| Final `WR-02`: help-output test did not check all invocation forms | fixed | `01-REVIEW.md` → Recheck Outcome; `verify_runner_help.cmake` checks ROM, manifest-case, and manifest-suite forms. |
