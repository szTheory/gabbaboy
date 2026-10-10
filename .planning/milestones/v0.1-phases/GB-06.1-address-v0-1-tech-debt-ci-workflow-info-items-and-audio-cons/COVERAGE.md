# Phase 06.1 API Coverage Matrix

**Authored:** 2026-10-10 (plan time)
**Scope:** the GitHub Actions REST surface that the new exact-head gate `.github/scripts/wait-exact-head-ci.py` (plans 06.1-03 and 06.1-04) uses to decide whether the exact pull-request head passed required CI. The gate is read-only. It uses `gh api` with the workflow `GITHUB_TOKEN`, and preview.yml grants `actions: read` and `contents: read` only.

GabbaBoy's own audio C API (`gbb_run_audio`, `gbb_reset`, and the rest of `include/gabbaboy/gabbaboy.h`), which plan 06.1-01 calls from the installed consumers, belongs to this project. It is not an external integration, so it is not listed below.

| # | Endpoint / capability | Disposition | Reason / usage |
|---|-----------------------|-------------|----------------|
| 1 | `GET /repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs` (list workflow runs for `ci.yml`, filters `head_sha`, `event=pull_request`, `per_page=100`) | INTEGRATE | Finds same-SHA candidate runs. The gate checks `total_count` against the number of entries listed, and a truncated list fails closed. The newest run is chosen by `run_number`. |
| 2 | `GET /repos/{owner}/{repo}/actions/runs/{run_id}` (get a workflow run) | INTEGRATE | Detail read for the newest run. Disagreement with the list on `run_attempt`, `head_sha`, `event`, `path` or `status` means WAIT. The terminal `status` and `conclusion` come from here. |
| 3 | `GET /repos/{owner}/{repo}/actions/runs/{run_id}/jobs?filter=latest&per_page=100` (list jobs for a run, latest attempt only) | INTEGRATE | Each required job (`required-native`, plus `macos-player-package` in the player job) must appear exactly once and have succeeded. The player job's `run_attempt` names the downloaded candidate artifact. |
| 4 | `GET .../actions/runs/{run_id}/jobs?filter=all` | OPT-OUT | Returns jobs from older attempts mixed with the latest one (live probe of run 37620710587), so the latest-only filter is used instead. |
| 5 | `GET .../actions/runs/{run_id}/attempts/{attempt_number}` (get a run attempt) | OPT-OUT | The gate only judges the latest attempt, which the list and detail endpoints already show. Older attempts never decide the result. |
| 6 | `POST .../actions/runs/{run_id}/rerun`, `/rerun-failed-jobs`, `/jobs/{job_id}/rerun` | OPT-OUT | The gate is read-only. Re-running is a maintainer action, out of scope. |
| 7 | `POST .../actions/runs/{run_id}/cancel`, `/force-cancel` | OPT-OUT | The gate is read-only. It never changes run state. |
| 8 | `POST .../actions/runs/{run_id}/approve` and `/pending_deployments` (approve or review) | OPT-OUT | The gate is read-only. Approving bot-PR runs, such as PR #41, is an owner action (D-11). |
| 9 | `GET/DELETE .../actions/runs/{run_id}/artifacts` and `/actions/artifacts/*` | OPT-OUT | The gate does not touch artifacts. The existing `gh run download` step in preview.yml downloads the candidate using the `run_id`/`run_attempt` outputs. |
| 10 | `GET .../actions/runs/{run_id}/logs` and `.../jobs/{job_id}/logs` | OPT-OUT | The gate decides from structured status and conclusion, never from log text. Plan 06.1-04 reads logs separately with `gh run view --log` as human-readable evidence. |
| 11 | `POST .../actions/workflows/{workflow_id}/dispatches` (workflow_dispatch) | OPT-OUT | The gate is read-only. Workflows run on `pull_request` and `push` only. |
| 12 | `DELETE .../actions/runs/{run_id}` and `/logs` | OPT-OUT | The gate is read-only. It never deletes evidence. |
| 13 | `GET .../commits/{ref}/check-runs` (Checks API) | OPT-OUT (gate) | The gate does not use it. Plan 06.1-04 and 06.1-07 executors use it, through `gh pr checks` and `verify-pr-evidence.sh`, to read required contexts back on the exact head. |
| 14 | `workflow_run` trigger / reusable workflows | OPT-OUT | Rejected in D-07: they would change how required checks are attributed. |
