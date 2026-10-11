---
phase: 07
review: 07-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: deferred
    title: "Driver batch size equals the core's total event queue capacity, so valid dense scripts fail with an opaque `drive-error`"
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "Player script smoke sets `skip_final_save` only after fallible steps, so an early exit can still run the battery-save path"
  - id: WR-03
    severity: warning
    disposition: fixed
    title: "The script-smoke \"attack surface\" guard scans only `script_smoke.c/.h`, not the `run_script_smoke` code in `main.c`"
  - id: WR-04
    severity: warning
    disposition: fixed
    title: "`--mutate` (and `--raw-verdict`) are silently ignored for frame-digest cases"
  - id: WR-05
    severity: warning
    disposition: fixed
    title: "The \"title garbage\" half of the predicate truth-table test cannot discriminate"
  - id: IN-01
    severity: info
    disposition: fixed
    title: "`gbb_accept_write_ppm` can leave a truncated file on write or close failure"
  - id: IN-02
    severity: info
    disposition: fixed
    title: "NUL-byte test fixture writes 20 bytes from a 19-byte literal"
  - id: IN-03
    severity: info
    disposition: skipped
    title: "CI \"Record acceptance and Mooneye observations\" steps assert nothing"
  - id: IN-04
    severity: info
    disposition: fixed
    title: "`player_script_smoke_prepare` formats into `err` without a NULL check"
  - id: IN-05
    severity: info
    disposition: skipped
    title: "Install-tree scan does not descend into directory symlinks"
open: 0
total: 10
recorded: 2026-10-11T08:20:00.000Z
---

# Phase 07: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-01 | warning | deferred | 79c9876 names the failure (`reason=event-delivery-failed`, test `acceptance_dense_script_delivery_failed`); driver back-pressure is a design change. Recorded as a limitation in docs/game-acceptance.md. Only scripts denser than the core queue drains are affected. |
| WR-02 | warning | fixed | fe1fb68 (07-REVIEW-FIX.md) |
| WR-03 | warning | fixed | d146902 (07-REVIEW-FIX.md) |
| WR-04 | warning | fixed | 3609111 (07-REVIEW-FIX.md) |
| WR-05 | warning | fixed | 97d3225 (07-REVIEW-FIX.md) |
| IN-01 | info | fixed | 7aec1ed (07-REVIEW-FIX.md) |
| IN-02 | info | fixed | 8eebe9d (07-REVIEW-FIX.md) |
| IN-03 | info | skipped | Observation steps are evidence capture by design (07-11); turning them into assertions is a CI policy choice (07-REVIEW-FIX.md) |
| IN-04 | info | fixed | 7caac52 (07-REVIEW-FIX.md) |
| IN-05 | info | skipped | Changing the admission scan's symlink behaviour needs its own negative fixture; out of the review-fix scope (07-REVIEW-FIX.md) |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
