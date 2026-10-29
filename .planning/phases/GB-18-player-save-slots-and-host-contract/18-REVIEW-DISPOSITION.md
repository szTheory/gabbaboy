---
phase: 18
review: 18-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: open
    title: "Rollback and post-load clock results are ignored, so \"nothing changed\" can be false"
  - id: WR-02
    severity: warning
    disposition: open
    title: "Slot, undo and preload temp files are never swept after a crash"
  - id: WR-03
    severity: warning
    disposition: open
    title: "The battery preload backup is clobbered by the first load of every new session"
  - id: WR-04
    severity: warning
    disposition: open
    title: "The save-format and contract checkers read the configure-time HEAD, so they can pass against a stale revision"
  - id: WR-05
    severity: warning
    disposition: open
    title: "The writer replaces an existing `.sav` with mode 0600, silently dropping its permissions"
  - id: WR-06
    severity: warning
    disposition: open
    title: "The no-interop-claims scan is easy to evade and can be satisfied vacuously for a rewritten claim"
  - id: IN-01
    severity: info
    disposition: open
    title: "`host_save_io_sweep` unlinks while iterating `readdir`"
  - id: IN-02
    severity: info
    disposition: open
    title: "The replace name cap does not guarantee the temp name fits NAME_MAX"
  - id: IN-03
    severity: info
    disposition: open
    title: "`player_input_rebase` early return leaves the mirror empty and a press unreleased"
  - id: IN-04
    severity: info
    disposition: open
    title: "A non-canonical MBC2 save is rewritten even when the guest never writes, and import failures are mislabelled"
  - id: IN-05
    severity: info
    disposition: open
    title: "Slot selection text follows neither the loader's symlink rule nor its regular-file rule"
  - id: IN-06
    severity: info
    disposition: open
    title: "A failed monotonic clock silently turns paced mode into a full-speed loop"
  - id: IN-07
    severity: info
    disposition: open
    title: "The `term` signal row uses a wall-clock ceiling as evidence, against project policy"
  - id: IN-08
    severity: info
    disposition: open
    title: "Hard-coded counts in PASS_REGULAR_EXPRESSION fight the append-only table"
  - id: IN-09
    severity: info
    disposition: open
    title: "Stale and duplicated comment, and directory fsync asymmetry on macOS"
open: 15
total: 15
recorded: 2026-10-29T06:29:14.266Z
---

# Phase 18: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-01 | warning | open | - |
| WR-02 | warning | open | - |
| WR-03 | warning | open | - |
| WR-04 | warning | open | - |
| WR-05 | warning | open | - |
| WR-06 | warning | open | - |
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |
| IN-04 | info | open | - |
| IN-05 | info | open | - |
| IN-06 | info | open | - |
| IN-07 | info | open | - |
| IN-08 | info | open | - |
| IN-09 | info | open | - |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
