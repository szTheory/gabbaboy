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
  - id: IN-01
    severity: info
    disposition: fixed
    title: "Unreachable optional-player branch left in the preview aggregate"
  - id: IN-02
    severity: info
    disposition: fixed
    title: "Exact-head lookup can fail on a stale failed run while a newer same-SHA run is in progress"
  - id: IN-03
    severity: info
    disposition: deferred
    title: "PASS path writes `run_attempt=None` when the job object lacks `run_attempt`"
  - id: IN-04
    severity: info
    disposition: deferred
    title: "`gh api` subprocess has no timeout, so the poll deadline cannot interrupt a hung call"
open: 0
total: 7
recorded: 2026-10-10T15:52:00Z
---

# Phase 01: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| CR-01 | critical | fixed | 01-REVIEW-FIX.md (not in the current review) |
| CR-02 | critical | fixed | 01-REVIEW-FIX.md (not in the current review) |
| WR-01 | warning | fixed | 01-REVIEW-FIX.md (not in the current review) |
| IN-01 | info | fixed | Fixed by Phase 06.1 PR #54, squash merge `ab76d09c2ee27ba09fc5f3c2510af016aebfdecb` (exact tested head `2a8fd1c`). `preview.yml` no longer has `PLAYER_REQUESTED` or the "optional" branch; the aggregate requires player `success` unconditionally (rechecked in the 2026-10-10 post-06.1 review, `preview.yml:179-182`). Hosted proof: preview run 38064419803 `preview-package-smoke` success. `.github/scripts/wait-exact-head-ci.py --self-test` (26 cases) passes. |
| IN-02 | info | fixed | Fixed by Phase 06.1 PR #54, squash merge `ab76d09c2ee27ba09fc5f3c2510af016aebfdecb`. `.github/scripts/wait-exact-head-ci.py` evaluates only the newest same-SHA run and waits while it is in progress; `--self-test` (26 cases) covers the stale-failed-run case. All three preview jobs call it. Hosted proof: preview run 38064419803 logged three `exact-head-ci: PASS run_id=38064419789 run_attempt=1` lines. |
| IN-03 | info | deferred | 2026-10-10 post-06.1 review. The PASS path does not type-check the job's `run_attempt` (`wait-exact-head-ci.py:103,141-147`). It still fails closed, because the artifact download by the `None` name fails, but only after the PASS line prints. Not fixed here because the 06.1 verification-refresh branch is docs-only (D-09). Revisit trigger: the next change to `.github/scripts/wait-exact-head-ci.py` or the next CI-workflow phase. Fix: return WAIT when `run_attempt` is not an int, plus a self-test row. |
| IN-04 | info | deferred | 2026-10-10 post-06.1 review. `gh_get` calls `subprocess.run` with no timeout (`wait-exact-head-ci.py:48`), so a hung `gh` call can outlive `--deadline-seconds`. The job-level `timeout-minutes` still bounds it, so it fails closed. Deferred for the same docs-only reason as IN-03 (D-09). Revisit trigger: same as IN-03. Fix: `timeout=60`, with `TimeoutExpired` mapped to `TransientError`. |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.

## Supplemental re-review history

The following warnings were found and resolved during the 2026-10-09 incremental review cycle; the reviewer reused `WR-01` and `WR-02` for the final recheck, so titles and review narrative are the disambiguators rather than IDs alone.

| Review finding | Disposition | Resolution evidence |
|----------------|-------------|---------------------|
| Earlier `WR-01`: double-reset run side effects were not asserted | fixed | `01-REVIEW.md` → Historical Supplemental Findings; reset-run outcome, budget, trace bounds, and RAM are asserted after each run. |
| Earlier `WR-02`: identical concurrent workloads could mask state interference | fixed | `01-REVIEW.md` → Historical Supplemental Findings; distinct guest immediates and RAM outcomes exercise per-instance independence. |
| Earlier `WR-03`: concurrent-instance test had no host watchdog | fixed | `01-REVIEW.md` → Historical Supplemental Findings; CTest applies a 30-second timeout to `concurrent_independent_instances`. |
| Final `WR-01`: partial Windows thread creation could destroy an in-use instance | fixed | `01-REVIEW.md` → Recheck Outcome; failure path releases, joins, and closes the created worker before destroying instances. |
| Final `WR-02`: help-output test did not check all invocation forms | fixed | `01-REVIEW.md` → Recheck Outcome; `verify_runner_help.cmake` checks ROM, manifest-case, and manifest-suite forms. |
