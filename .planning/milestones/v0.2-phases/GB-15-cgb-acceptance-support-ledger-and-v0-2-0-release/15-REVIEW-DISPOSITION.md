---
phase: 15
review: 15-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: open
    title: "Evidence jobs run tagged source (build, full CTest, fuzz binary) with a job-level `contents: write` token"
  - id: WR-02
    severity: warning
    disposition: open
    title: "`--check-receipt` accepts a source-archive receipt that was never bound to the Git tree"
  - id: WR-03
    severity: warning
    disposition: open
    title: "Fuzz receipt is self-attested, so the \"forged evidence\" checks are shape-only"
  - id: WR-04
    severity: warning
    disposition: open
    title: "Performance regression gate can never fail (standing pre-written \"review\")"
  - id: WR-05
    severity: warning
    disposition: open
    title: "Source-archive receipt depends on GitHub producing byte-identical tarballs across downloads"
  - id: WR-06
    severity: warning
    disposition: open
    title: "Trust-boundary overlay covers three files, but the gate delegates to many more tagged files"
  - id: WR-07
    severity: warning
    disposition: open
    title: "DMG KEY1 oracle fix leaves scenario 3 (held button) exposed to the same failure and the new DMG seeds are weak controls"
  - id: WR-08
    severity: warning
    disposition: open
    title: "Consumer receipt `source_sha` is self-reported by the package under test"
  - id: IN-01
    severity: info
    disposition: open
    title: "`--check-recovery` and `--decide` are not wired into any workflow"
  - id: IN-02
    severity: info
    disposition: open
    title: "Wiring validators rely on substring counts, which comments and echoes can satisfy"
  - id: IN-03
    severity: info
    disposition: open
    title: "`--evidence-only` skips build-artifact digest checks for any absent path"
  - id: IN-04
    severity: info
    disposition: open
    title: "`check_tree` does not compare file modes; unwrapped-symlink depth math is off by one"
  - id: IN-05
    severity: info
    disposition: open
    title: "`curl --max-filesize` does not bound chunked downloads"
  - id: IN-06
    severity: info
    disposition: open
    title: "`check_runs` binds workflow runs only to head SHA and success, not to a workflow"
  - id: IN-07
    severity: info
    disposition: open
    title: "Duplicate `Create the local-only rehearsal tag` and corpus scripts across rehearsal and release jobs"
  - id: IN-08
    severity: info
    disposition: open
    title: "`.gitattributes` forces `eol=lf` on whole globs and `gbb_add_v02_contract` embeds counts in regex"
open: 16
total: 16
recorded: 2026-10-20T11:20:41.654Z
---

# Phase 15: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-01 | warning | open | - |
| WR-02 | warning | open | - |
| WR-03 | warning | open | - |
| WR-04 | warning | open | - |
| WR-05 | warning | open | - |
| WR-06 | warning | open | - |
| WR-07 | warning | open | - |
| WR-08 | warning | open | - |
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |
| IN-04 | info | open | - |
| IN-05 | info | open | - |
| IN-06 | info | open | - |
| IN-07 | info | open | - |
| IN-08 | info | open | - |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
