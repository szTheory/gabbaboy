---
phase: GB-17-native-save-state-core
plan: "10"
subsystem: testing
tags: [release-evidence, workflow-policy, test-budget, plan-cap, nightly-report, hdma-lane, RM-030]

requires:
  - phase: GB-17-native-save-state-core/17-09
    provides: "The lifecycle script, the lifecycle replay and the strict SHA256SUMS parse that this plan rechecks and extends"
  - phase: GB-16-tune-up-and-v0-2-debt-closure
    provides: "The nine deferred review findings (WR-01..05, IN-01..04) recorded as RM-030"
provides:
  - "Release reuses a rehearsal run's performance receipt only when the newest successful run is a push or dispatch of the rehearsal workflow on this tag's branch in this repository and its head is the tagged commit or has exactly the tagged tree, proved from git objects, with the artifact bound to that run and attempt"
  - "Platform manifest entries are parsed strictly before any name-keyed map exists, and the PR-time required-check gate holds every recorded context to the one trusted GitHub App identity"
  - "Both Phase 8 checkers refuse a retargeted boundary tag and the CTests read the literal boundary commit"
  - "New test-budget allowlist rows are bounded against the immutable base, and plan-cap counts suffixed names, reserves the gap slot, rejects a fifth phase and reads a full commit id"
  - "The nightly red report has its own timeout, an exact title-and-label dedupe, a dispatch-only dry run and a replay of its production body; the HDMA skipped-lane control and every remote-evidence control require their intended refusal"
affects: [GB-17, release-evidence, workflow-policy, GB-17-11, GB-19]

actuals:
  tokens: 26846
  tasks: 3
  commits: 5

tech-stack:
  added: []
  patterns:
    - "A refusal control is credited only when the refusal names its own reason, and a mutant of the production code is credited only when it behaves differently from the real code"
    - "A mutable name is judged by the commit it must peel to, and the clauses are read from a literal commit"
    - "A token-holding step may run only listed read-only API calls, and the judge it runs is the trusted revision's copy"

key-files:
  created: []
  modified:
    - .github/scripts/verify-release-gates.sh
    - .github/scripts/verify-release-source-proof.py
    - .github/scripts/verify-workflow-policy.py
    - .github/workflows/release.yml
    - .github/workflows/nightly-asan.yml
    - docs/release.md
    - tests/scripts/verify-phase8-closure-contract.py
    - tests/scripts/verify-phase8-player-contract.py
    - tests/scripts/verify-test-budget.py
    - tests/scripts/verify-planning-hygiene.py
    - tests/scripts/verify-hdma-lane.py
    - tests/scripts/test_hdma_remote_evidence.py
    - tests/scripts/verify-no-phase-paths.py
    - tests/cmake/hygiene.cmake
    - tests/cmake/ci-lanes.cmake
    - tests/CMakeLists.txt

key-decisions:
  - "The PR-time gate holds the evidence, not only the branch rule, to the trusted App (id 15368, slug github-actions). The live branch protection leaves preview-package-smoke at app_id null, so rejecting a null rule would break --check-pr until the owner edits protection; the run identity check gives the same guarantee without that dependency."
  - "Only the newest successful rehearsal run is a reuse candidate. A stale or ineligible newest run means a fresh measurement, never an older run behind it."
  - "A new allowlist row is bounded by 3 x 60 s (the figure the checker already names as the budget that fits the hosted sanitizer limit) and may not cite a reference that already backs a base row. No new quota constant was invented."
  - "The 12th slot of every plan cap is reserved for plans that declare gap_closure: true in frontmatter."
  - "The job-level timeout of report-red and its ledger row are NOT added: no report-red job has ever executed, and a hosted dry run needs a pushed head. The reporting step carries a 5 minute timeout meanwhile."

patterns-established:
  - "Plain Phase 8 CTests pass the literal boundary commit and each selftest resolves the tag, so a retarget fails one place with its own message"
  - "Commit-scoped checker input is a full 40-hex id read with git; a name, a short id or an upper-case id is refused"

requirements-completed: []

coverage:
  - id: RM-030-WR-01-reuse-selection
    description: "Release reuses a rehearsal performance receipt only from the newest successful run that is a push or dispatch of release-rehearsal.yml on rehearsal/<tag> in this repository, whose head is the tagged commit or has the tagged tree proved from git objects, and only through the one artifact that exact run and attempt uploaded. Another workflow, event, conclusion, branch, repository or fork, an unprovable or different tree, a stale newest run behind an older valid run, a repeated or malformed run id, an expired, empty, oversized, renamed, duplicated or foreign-run artifact and a truncated artifact list are each refused with the intended diagnostic after the real captured run and artifact shapes pass. The judge is the trusted revision's copy and the workflow policy pins the selection, the trusted judge, the exact download and refuses write or unlisted API calls in the token step."
    requirement: RM-030
    verification:
      - kind: integration
        ref: "12e8dbb8e45c7d93b90d14eadd78b042b668b1dc: python3 -I .github/scripts/verify-release-source-proof.py --self-test (54 rehearsal reuse defects rejected on a hand-built shape and again on the captured GitHub run and artifact objects; the CLI proves an equal tree from git objects in a disposable repository)"
        status: pass
      - kind: integration
        ref: "12e8dbb8e45c7d93b90d14eadd78b042b668b1dc: python3 -I .github/scripts/verify-workflow-policy.py --check and --self-test (346 negative controls, 4 positive controls including 10 release.yml selection mutants)"
        status: pass
    human_judgment: false
  - id: RM-030-WR-03-manifest-parse
    description: "The platform manifest is parsed strictly before a name-keyed map is built, so a repeated name, a path-like name, a wrong-length or upper-case digest, a missing key and a non-list asset field are each refused with a named diagnostic. SHA256SUMS wrong-length, upper-case, blank, CRLF and extra-space lines are regression controls beside the earlier duplicate, malformed, path-like and unterminated cases."
    requirement: RM-030
    verification:
      - kind: integration
        ref: "12e8dbb8e45c7d93b90d14eadd78b042b668b1dc: bash .github/scripts/verify-release-gates.sh --self-test (exit 0; 6 manifest defects and 9 SHA256SUMS defects refused with the intended reason)"
        status: pass
    human_judgment: false
  - id: RM-030-IN-02-app-identity
    description: "Every recorded required context must come from GitHub App id 15368 with slug github-actions at PR time as at release time. A wildcard branch rule still gets the identity check on the run, and a rule that trusts another App or names the id as a string is refused."
    requirement: RM-030
    verification:
      - kind: integration
        ref: "12e8dbb8e45c7d93b90d14eadd78b042b668b1dc: bash .github/scripts/verify-release-gates.sh --self-test (4 wildcard-rule run identity defects and 2 branch-rule defects refused; fail-first at 33d157d accepted the wildcard case)"
        status: pass
    human_judgment: false
  - id: RM-030-IN-01-retry-recheck
    description: "The retry order of 17-09 holds: attached evidence is judged before any regenerated copy is replaced, and the release lifecycle replay still passes with the changed gates and workflow."
    requirement: RM-030
    verification:
      - kind: integration
        ref: "12e8dbb8e45c7d93b90d14eadd78b042b668b1dc: python3 -I tests/scripts/verify-release-lifecycle.py --self-test (positives=4 controls=85) and the release_lifecycle_replay CTest"
        status: pass
    human_judgment: false
  - id: RM-030-WR-02-historical-identity
    description: "Both Phase 8 checkers require historical/phase-08-boundary to peel to 96d5eec977bee99a0629499b89c737415e24184c and stop with a retargeted-tag message before any clause is judged. Disposable annotated and lightweight tags retargeted to another commit are refused, a deleted tag is unreadable, an explicit override revision is judged by its clauses alone, and the plain CTests read the literal commit."
    requirement: RM-030
    verification:
      - kind: unit
        ref: "12e8dbb8e45c7d93b90d14eadd78b042b668b1dc: python3 -I tests/scripts/verify-phase8-closure-contract.py --self-test (rejected_controls=168) and python3 -I tests/scripts/verify-phase8-player-contract.py --self-test (retargeted-tag-x8)"
        status: pass
      - kind: integration
        ref: "12e8dbb8e45c7d93b90d14eadd78b042b668b1dc: ctest --preset phase1 -j8 (phase8_closure_contract, phase8_closure_contract_selftest, phase8_closure_contract_wrong_boundary, phase8_player_contract, phase8_player_contract_selftest, phase8_player_contract_wrong_boundary all passed)"
        status: pass
    human_judgment: false
  - id: RM-030-WR-04-budget-new-rows
    description: "Against an immutable base commit, a test-budget allowlist row that is new is refused above 180 s and refused when it cites a reference that already backs a base row, so copying an existing reference cannot grant an unbounded timeout. Existing rows at larger ceilings, a first seeding, two new rows sharing one fresh reference and the shipped allowlist judged against itself stay valid. The base must be a full commit id and is pinned once."
    requirement: RM-030
    verification:
      - kind: unit
        ref: "12e8dbb8e45c7d93b90d14eadd78b042b668b1dc: python3 -I tests/scripts/verify-test-budget.py --self-test (controls=54) and --build-dir build --base main (pass tests=1488 allowlisted=79)"
        status: pass
    human_judgment: false
  - id: RM-030-WR-05-plan-cap
    description: "Plan-cap counts canonical and suffixed plan names toward each phase cap, never counts a no-id file such as NN-PLAN-CHECK.md, limits plans that are not gap_closure to the cap minus one reserved slot, rejects a fifth active milestone phase and, with --rev, reads the ROADMAP and plan names from one full commit id with git so a working-tree edit, a later commit and a symbolic name cannot change the verdict."
    requirement: RM-030
    verification:
      - kind: unit
        ref: "12e8dbb8e45c7d93b90d14eadd78b042b668b1dc: python3 -I tests/scripts/verify-planning-hygiene.py --self-test (controls=77) and --check plan-cap --rev 12e8dbb8e45c7d93b90d14eadd78b042b668b1dc (pass phases=4 plans=18)"
        status: pass
      - kind: integration
        ref: "12e8dbb8e45c7d93b90d14eadd78b042b668b1dc: ctest --preset phase1 -j8 (plan_cap, planning_hygiene_controls and no_phase_paths passed)"
        status: pass
    human_judgment: false
  - id: RM-030-IN-03-report-red-body
    description: "The nightly red report step has its own 5 minute timeout, reuses an open issue only for the exact title carrying the nightly-red label, creates the label when it is missing, and a dispatch-only dry run skips the replay and records every issue and label write instead of sending it. The production body is executed against a recording gh stand-in over 11 scenarios (an unrelated or prefix title, the exact title under another or no label and a lowest-numbered match among several) and 8 body mutants. This entry does NOT cover the job-level timeout and its ledger row, which wait for a completed report-red run."
    requirement: RM-030
    verification:
      - kind: integration
        ref: "12e8dbb8e45c7d93b90d14eadd78b042b668b1dc: python3 -I .github/scripts/verify-workflow-policy.py --self-test (19 static nightly mutants plus the 11 scenario and 8 mutant replay)"
        status: pass
    human_judgment: false
  - id: RM-030-IN-04-lane-controls
    description: "The HDMA skipped-lane control must be refused for the missing CTest registration of the lane test (and separately of its selftest), a missing inventory case must be refused by name, an unrelated edit still passes, and every remote-evidence control including skipped and reused-run receipts must be refused for its own reason. The perf-gate second repeat digest and consumption controls of 17-07 still pass."
    requirement: RM-030
    verification:
      - kind: unit
        ref: "12e8dbb8e45c7d93b90d14eadd78b042b668b1dc: python3 -I tests/scripts/verify-hdma-lane.py --lane-self-test (controls=5) and python3 -I tests/scripts/test_hdma_remote_evidence.py (negative=18)"
        status: pass
      - kind: unit
        ref: "12e8dbb8e45c7d93b90d14eadd78b042b668b1dc: python3 -I tests/scripts/verify-perf-gate.py --self-test (controls=33)"
        status: pass
    human_judgment: false
  - id: phase17-10-no-regression
    description: "The changed checkers, workflow and CTest wiring leave every existing test green, including the test inventory, test budget and summary coverage checks."
    verification:
      - kind: integration
        ref: "12e8dbb8e45c7d93b90d14eadd78b042b668b1dc: cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 -j8 --output-on-failure --no-tests=error (1488/1488 passed, 150.5 s)"
        status: pass
    human_judgment: false

duration: 2h
completed: 2026-10-28
status: complete
plan_head_before: b9cc82e6e0b146430b690fc7d5d999799a65e42c
plan_head_after: 12e8dbb8e45c7d93b90d14eadd78b042b668b1dc
---

# Phase GB-17 Plan 10: Phase 16 Review Findings Closed in Production Gates Summary

**Eight of the nine deferred Phase 16 findings are now enforced by production gates with refusals that name their own reason; the ninth, IN-03, is enforced except for the job-level timeout citation, which needs a completed report-red run that does not exist yet.**

## Performance

- **Duration:** roughly 2 hours of wall time including reading, design and three full-suite runs (approximate; no per-task clock was kept).
- **Tasks:** 3/3 delivered, one of them with an open evidence precondition (below).
- **Commit ledger:** 5 commits measured from the persisted plan base to the final code head (one fail-first, three feature commits, one lint follow-up).
- **Diff-size proxy:** 26,846 (107,382 changed characters divided by four; not measured model-token use, and not comparable to the raw plan projection of 76,000).
- **New tests:** none registered. Wall times alone on this host: `workflow_policy_controls` about 30 s (it was about 28 s before the red-report replay was added; 52 s inside the full `-j8` run against a 180 s TIMEOUT, so the margin is 3.5x), `release_lifecycle_controls` 28 s inside the full run (60 s TIMEOUT, unchanged), `planning_hygiene_controls` 1.2 s, `phase8_closure_contract_selftest` 2.0 s, `phase8_player_contract_selftest` 0.5 s, `test_budget_controls` 0.5 s. `verify-release-gates.sh --self-test` (run by the CI workflow, not CTest) takes about 50 s. Nothing new exceeds 30 s except the already existing policy controls at about 30 s.

## Accomplishments

- **WR-01.** `verify-release-source-proof.py` gained `select_performance_run` and `select_performance_artifact` with a CLI the release job runs from the trusted revision's copy. The run must be a push or dispatch of `release-rehearsal.yml` on `rehearsal/<tag>` in this repository, completed with success, and its head must be the tagged commit or have exactly the tagged tree, proved with `git rev-parse` (an object that cannot be proved refuses). The artifact must be the one named for that run and attempt, unexpired, bounded, and produced by the same run, head, branch and non-fork repository. The previous `|| true` that hid a download error is gone: a refusal logs its reason and the job measures afresh.
- **WR-03.** The platform manifest consumer was the remaining name-keyed collapse. It now validates every entry (exact keys, safe name, 64 lowercase hex) and refuses a repeated name before the map is built. The other `SHA256SUMS` consumers were rechecked: the strict parse from 17-09 stands, the delivery readback and the published-asset verifier already refuse repeated names, and the CMake `SHA256SUMS` in `tests/data/classify-changes` is unrelated immutable test data.
- **IN-02.** `check_required_checks` holds every recorded context to id 15368 and slug `github-actions` like the release-time proof, whatever the branch rule says.
- **IN-01.** Rechecked, not re-marked: the lifecycle self-test (85 controls) and replay pass unchanged at the final head.
- **WR-02.** Both Phase 8 checkers pin the boundary commit, with disposable-tag controls (annotated and lightweight retargets, a deleted tag, an override) and a command-line control from inside a disposable repository.
- **WR-04.** New-row bound and unique citation against the immutable base; the base must be a full commit id.
- **WR-05.** Suffixed names, gap reserve, four-phase limit and `--rev` (see coverage). The live repository passes: four phases, 18 plans, Phase 17 at 11 primary plans of a 12 cap.
- **IN-03 (part).** See Deviations 3 and the pending item below.
- **IN-04.** The skipped-lane control is anchored on the whole `add_test` line and requires the registration message; an unrelated edit must still pass; the remote-evidence controls each name their refusal, and two new receipts (skipped conclusion, reused run id) were added.

## Task Commits

1. **Task 1 fail-first** — `33d157d` (`test`). The gate self-test accepted a wildcard-rule check from another App.
2. **Task 1 implementation** — `37f4ca7` (`feat`): WR-01, WR-03, IN-02, workflow policy and `docs/release.md`.
3. **Task 2** — `6c69a93` (`feat`): WR-02, WR-04, WR-05 and their CTest wiring.
4. **Task 3** — `8c36f2d` (`feat`): IN-03 body, dry run, replay and IN-04 controls.
5. **Follow-up** — `12e8dbb` (`fix`): the commit-scoped phases path is one constant with a count-pinned allowlist row in the phase-path lint.

## CLI Registry

- `verify-release-source-proof.py --select-performance-run RUNS_JSON --tag TAG --source-sha SHA --repo OWNER/NAME --selected-run FILE` prints the run id; `--select-performance-artifact ARTIFACTS_JSON --selected-run FILE` prints the artifact name; a refusal prints `REJECT: reason` on stderr and exits 1.
- `verify-planning-hygiene.py --check plan-cap --rev COMMIT [--repo DIR]` (a full 40-hex commit id) beside the existing `--roadmap`/`--phases-dir` form.
- `verify-test-budget.py --base` now requires a full commit id.
- `nightly-asan.yml` `workflow_dispatch` input `report_red_dry_run` (boolean, default false).
- No CTest was added; floors rose: `test_budget_controls` 10 to 50, `planning_hygiene_controls` 12 to 70, `phase8_closure_contract_selftest` 160 to 165, `workflow_policy_controls` 220 to 300.

## Verification

All at `12e8dbb8e45c7d93b90d14eadd78b042b668b1dc`:

- `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 -j8 --output-on-failure --no-tests=error`: 1488/1488 passed in 150.5 s. (An earlier run at `8c36f2d` failed `no_phase_paths` on the new plan-cap reader; that is Deviation 5.)
- `bash .github/scripts/verify-release-gates.sh --self-test` exit 0; `python3 -I .github/scripts/verify-release-source-proof.py --self-test`; `python3 -I .github/scripts/check-required-native.py --self-test` (19 controls); `python3 -I .github/scripts/verify-workflow-policy.py --check` and `--self-test` (346 negative, 4 positive); `python3 -I tests/scripts/verify-release-lifecycle.py --self-test` (85 controls); `verify-hdma-lane.py --lane-self-test`; `test_hdma_remote_evidence.py`; `verify-perf-gate.py --self-test`; `verify-test-budget.py --build-dir build --base <main>` (tests=1488 allowlisted=79); `verify-planning-hygiene.py --check plan-cap --rev <head>`; `verify-no-phase-paths.py --check` (files=522 allowlisted=7).
- **Discriminating power.** 11 mutants of the reuse selection (tree compare, tree proof, older-run fallback, event, path, fork, branch, artifact run, conclusion, expiry, attempt name), 4 of the Phase 8 identity, 5 of planning hygiene (names, phase count, gap reserve, gap counting, symbolic rev), 4 of the budget, 3 of the HDMA lane, 1 of the remote evidence and a manifest-parse mutant were each refused by a control. `check-required-native.py` needed no change: it judges job results and has no app-identity surface.
- **Pending hosted evidence:** no hosted run of the changed gates, workflow or checkers is claimed. Hosted Linux, macOS and Windows runs are pending the parent's exact-head CI. The red-report replay is POSIX only (bash and jq) and prints a skip on Windows; the static report-red rules still apply there.

## Decisions Made

See `key-decisions`. In addition: the replay executes the workflow's own step text rather than a copy, so a drift between the workflow and the control is impossible; and the plain Phase 8 CTests passing a literal commit leaves the tag identity to the selftests, so a retarget is reported once with its own message.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical documentation] `docs/release.md` was not in the file list**
- **Issue:** the reuse rule is part of the release contract, and AGENTS.md requires docs, source and tests to change together.
- **Fix:** one paragraph in `docs/release.md` describing the newest-run, tree, artifact and fresh-measurement rules; `verify-v02-adoption.py --check docs` passes.
- **Commit:** `37f4ca7`.

**2. [Rule 3 - Blocking] CTest floors and wiring outside the listed files**
- **Issue:** the new controls need their pinned minima raised so a vanished control cannot pass, and `plan_cap` needed a configure-time revision. CMake regular expressions have no `{40}` quantifier, so the first attempt silently produced `unknown`, which failed closed and was caught by the run.
- **Fix:** `tests/CMakeLists.txt` and `tests/cmake/ci-lanes.cmake` floors; `hygiene.cmake` captures `git rev-parse HEAD` with a length check.
- **Commits:** `6c69a93`, `8c36f2d`.

**3. [Unmet evidence precondition, not closed] IN-03 job-level timeout and its ledger row**
- **Found during:** Task 3. All 8 `nightly-asan.yml` runs on record succeeded and `report-red` was skipped in every one (read-only `gh api` on the jobs of runs 40626546191 and 40163271239 and the run list), so no completed report-red job exists to cite. The plan's fallback is a hosted dry run, which needs the changed workflow on a pushed head; pushing and dispatching are the parent's. A normal ledger row needs a cited completed run, a `release_bound` row would be a seventh RM-027 row, and a provisional row would still need invented numbers. None was fabricated.
- **Done instead:** the reporting step carries a 5 minute `timeout-minutes` that the policy requires, the dry-run mode exists, and `.planning/WINDOWS.md` carries an open `unrun-verify` entry so the ship gate sees it.
- **Required next step (exact):** after the parent pushes the branch, `gh workflow run nightly-asan.yml --ref gsd/phase-17-native-save-state-core -f report_red_dry_run=true`, read the run id, head SHA and the `report-red` job duration with `gh api repos/{owner}/{repo}/actions/runs/RUN_ID/jobs`, add `timeout-minutes: 5` to the `report-red` job and a `nightly-asan.yml:report-red` row to `.github/ci-timeouts.json` (timeout 5, that run id and sha, the measured p50 rounded up to 0.01 min, samples 1, `provisional` true until the head is on main), then run `verify-workflow-policy.py --check`. IN-03 is not closed until then.

**4. [Design] The wildcard branch rule for `preview-package-smoke` is tolerated at the rule and refused at the evidence**
- Live branch protection (read-only `gh api`) has `app_id: null` for that context. Requiring a non-null rule would make `--check-pr` fail until the owner edits protection. The gate instead refuses any run not from the trusted App, which is the guarantee that matters. Pinning the rule is optional owner hardening.

**5. [Rule 3 - Blocking] `verify-no-phase-paths.py` allowlist row**
- The plan-cap `--rev` reader names the phases path once, inside a commit. The lint counts that spelling, so the path is one constant (`PHASES_AT_REV`) and `verify-no-phase-paths.py` carries a count-pinned row of 1, the same point-in-time class as the Phase 8 reader. Commit `12e8dbb`.

**6. [Scope] `check-required-native.py` unchanged**
- It is listed in the plan but has nothing to bind: it judges job results from the classifier, not check-run Apps.

### Auth gates

None. Only read-only `gh` calls on this public repository were used.

## Known Stubs

None. The red-report replay's `gh` is a declared test stand-in, and the dry-run recording is a production mode.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: privilege | .github/workflows/nightly-asan.yml | `report-red` can now also create the `nightly-red` label (still inside its `issues: write` grant, no checkout, no repository code) and `workflow_dispatch` takes one boolean input that can skip the replay |

## Deferred Verification and Limits

- IN-03 job-level timeout and ledger row (Deviation 3) block RM-030 from being marked complete; `requirements-completed` is empty for that reason.
- The reuse selection, the label creation and the dry run have not run on GitHub. `gh` and the label API were exercised only for read-only shape and `env` support in the `--jq` filter (verified locally against this repository's labels and issues).
- The CI budget step still runs the checker and allowlist from the head tree, as the Phase 16 review noted; running them from the base commit is a `ci.yml` change outside this plan.
- RM-027's six `release_bound` rows are unchanged and remain Phase 19 entry blockers. No version PR, tag, release, push or PR edit was made.

## Self-Check: PASSED

All 15 created or modified files exist and all 5 task commits are ancestors of HEAD (checked after the summary was written). The one open item is IN-03 (Deviation 3), recorded openly above and in `.planning/WINDOWS.md`; it is a pending evidence precondition, not a failed check.
