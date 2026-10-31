---
phase: 16-tune-up-and-v0-2-debt-closure
plan: "04"
subsystem: ci-budget
tags: [planning-only-lane, classifier, required-native, timeout-ledger, planning-labels, tune-04, workflow-policy]
requires:
  - phase: 16-02
    provides: the perf-gate job, the perf-attribution and rehearsal perf-gate wiring and the policy script
  - phase: 16-03
    provides: the per-test TIMEOUT ratchet (tests/ci/test-budget-allowlist), nightly-asan.yml, the post-shard main ci run
provides:
  - classify-changes.py, a fail-closed planning-only classifier whose copy at the base commit decides
  - check-required-native.py, the aggregator verdict behind the unchanged required-native context
  - ci.yml changes and planning-checks jobs and the kind == 'full' condition on every heavy job
  - .github/ci-timeouts.json (44 rows) with check_timeout_ledger(), 17 data mutations, boundary controls, --release-head and an advisory --verify-cited
  - verify-planning-labels.py and the planning label on every planning-reading test, so ctest -L planning runs on an unbuilt tree
affects: [16-06, 16-07]
actuals:
  tokens: 27200
  tasks: 3
  commits: 4
commits: 4
plan_head_before: 2bd618db0a48587bddedc535bad5722fcbf479aa
plan_head_after: cf1d09e9d6c6eb06a450d7a9f9f15569a0dda8e5
tech-stack:
  added: []
  patterns:
    - A change is planning-only only when every path is provably under .planning/ or is AGENTS.md; every doubt classifies as full, and the base commit's classifier decides.
    - The aggregator reads one classification plus every job result, and any value other than kind=planning is treated as full.
    - Each timeout cites the run whose duration it doubles; jobs that cannot have a green run yet carry a key-pinned, VERSION-expiring release_bound row.
    - A planning-labelled test reads the configured tree only, so it runs with the build directory as its working directory instead of naming it.
key-files:
  created:
    - .github/scripts/classify-changes.py
    - .github/scripts/check-required-native.py
    - .github/ci-timeouts.json
    - tests/scripts/verify-planning-labels.py
    - tests/cmake/ci-lanes.cmake
    - tests/data/classify-changes/
    - tests/data/repaired-summary-coverage.md
  modified:
    - .github/workflows/ci.yml
    - .github/workflows/release-rehearsal.yml
    - .github/scripts/verify-workflow-policy.py
    - tests/CMakeLists.txt
    - tests/cmake/areas.cmake
    - tests/expected-tests.txt
    - tests/ci/test-budget-allowlist
    - .gitattributes
    - .planning/context/DECISIONS.md
key-decisions:
  - "D-110 (D-20 release-bound ledger row, Phase 16): three release_bound keys, each at most once, expiring when VERSION passes 0.2.1."
  - "changes and planning-checks run on ubuntu-22.04 and the heavy-job needs/if lines follow timeout-minutes, so the fuzz receipt self-test anchors on the sanitizer job header still hold."
  - "The planning-label lint matches .planning/ or AGENTS.md in referenced scripts, not the bare word, which false-positived on an exclusion list and on needs.planning-checks."
requirements-completed: ["TUNE-04"]
coverage:
  - id: D1
    description: "A planning-only change runs one cheap job behind required-native while any src/, include/ or tests/ change still runs the full matrix; the classifier rejects renames out of src/, dot-dot segments, case variants, symlinks, submodules, empty and oversized diffs, a missing or zero base and tags."
    requirement: "TUNE-04"
    human_judgment: false
    verification:
      - kind: unit
        ref: "python3 -I .github/scripts/classify-changes.py --self-test"
        status: pass
      - kind: integration
        ref: "ctest --test-dir build -R '^classify_changes_src_rejected$'"
        status: pass
      - kind: e2e
        ref: "stacked probe PR 108 run 40166565258: planning-checks and required-native success, every heavy job skipped"
        status: pass
      - kind: e2e
        ref: "PR 107 exact-head runs 40168063465 and 40168065851: every heavy job ran and required-native success"
        status: pass
  - id: D2
    description: "required-native stays the single always() aggregator: kind=full needs every heavy job success and planning-checks skipped, kind=planning needs planning-checks success and every heavy job skipped, any other kind is full, and the three required contexts are unchanged."
    requirement: "TUNE-04"
    human_judgment: false
    verification:
      - kind: unit
        ref: "python3 -I .github/scripts/check-required-native.py --self-test"
        status: pass
      - kind: integration
        ref: "python3 -I .github/scripts/verify-workflow-policy.py --self-test"
        status: pass
  - id: D3
    description: "The timeout ledger has one row per job with timeout-minutes in every workflow, each citing a real run, and the policy rejects an edited timeout, a missing row, a p50 above half the timeout, a stale value, a new job without a row, a duplicate key, a provisional row at the release head, a gating p50 of 30.1, release_bound under any other key or after the VERSION expiry, and a normal row without samples."
    requirement: "TUNE-04"
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build -R '^workflow_policy_(check|controls)$'"
        status: pass
      - kind: unit
        ref: "python3 -I .github/scripts/verify-workflow-policy.py --check"
        status: pass
  - id: D4
    description: "Every test that reads .planning/ or AGENTS.md carries the planning label, no planning-labelled test names the build tree, and ctest -L planning passes on a configured but unbuilt tree."
    requirement: "TUNE-04"
    human_judgment: false
    verification:
      - kind: unit
        ref: "python3 -I tests/scripts/verify-planning-labels.py --self-test"
        status: pass
      - kind: integration
        ref: "ctest --test-dir build/phase16_04_unbuilt -L planning --no-tests=error (20 of 20 on a fresh unbuilt configure)"
        status: pass
  - id: D5
    description: "The full suite passes with the new lane, ledger and lint, and git diff of src and include against the plan base is empty."
    requirement: "TUNE-04"
    human_judgment: false
    verification:
      - kind: integration
        ref: "cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error (1209 of 1209)"
        status: pass
      - kind: other
        ref: "git diff --quiet 2bd618db0a48587bddedc535bad5722fcbf479aa HEAD -- src include"
        status: pass
duration: about 2h 30m including hosted CI waits
completed: 2026-10-25
status: complete
---

# Phase 16 Plan 04: Planning-only lane, timeout ledger and planning-label lint Summary

**A fail-closed planning-only CI lane behind the unchanged required-native context, a 44-row timeout ledger that cites real runs and is enforced from CTest, and a planning-label lint that lets `ctest -L planning` run on an unbuilt tree.**

## Performance

- **Duration:** about 2h 30m wall clock, mostly hosted CI waits (start time was not captured at dispatch)
- **Completed:** 2026-10-25
- **Tasks:** 3 (all in PR A, 4 commits)
- **Files modified:** 21 in PR A (1610 insertions, 31 deletions)

## Delivery state (correct as of PR A's merge)

- **PR A:** https://github.com/szTheory/gabbaboy/pull/107, final head `cf1d09e9d6c6eb06a450d7a9f9f15569a0dda8e5`, squash-merged by the orchestrator after exact-head checks.
- **Exact-head runs on cf1d09e:** ci pull_request 40168065851 and ci push 40168063465, fixture-repro pull_request 40168065838 and push 40168063437, preview-package-smoke pull_request 40168065879. All concluded success. `gh pr view 107` reported mergeStateStatus CLEAN with no failing check.
- **Stacked planning-checks probe:** PR https://github.com/szTheory/gabbaboy/pull/108, closed unmerged, branch deleted. Its pull_request run **40166565258** classified kind=planning against PR A's branch: planning-checks success (21 s), every heavy job skipped, required-native success (6 s).
- **Rehearsal probe:** `rehearsal/ledger-probe-16-04` pushed at 2bd618d (ancestor of origin/main, `git merge-base --is-ancestor` exit status 0), run **40166530630**. Only `rehearse-perf-gate` is cited (success, 0.90 min). `rehearse-paired-performance-qualification` and `rehearse-corpus-and-support-sidecar` failed, so `rehearse-trusted-judge` was skipped. The branch was deleted after citation.
- **PR B and the scheduled planning-only main run:** this SUMMARY is the only file of PR B. Its main push run (kind=planning, planning-checks success, every heavy job skipped) is found later with `gh run list --workflow ci.yml --branch main`; 16-06 re-cites planning-checks from it.
- **Branch-protection read** (`gh api repos/szTheory/gabbaboy/branches/main/protection`, 2026-10-25): required contexts exactly `required-native`, `fixture-repro`, `preview-package-smoke`, strict true. Nothing was changed.
- Also relied on: 16-03's post-shard main ci run **40163270595** on 2bd618d (success) and nightly-asan dispatch **40163271239** (success, asan-full-replay 5.79 min, report-red skipped).

## Accomplishments

- `classify-changes.py` prints `kind=planning` only when every path of `git diff --raw --no-renames -z` is under `.planning/` or is exactly `AGENTS.md`; 49 self-test controls cover every fail-closed case, a shuffled-order property and a real throwaway repository (rename out of `src/`, symlink entry, zero, unresolvable and tag cases).
- `ci.yml` gained `changes` (runs the base commit's copy; a base without the file, an unresolvable base or an all-zero push parent is kind=full) and `planning-checks` (configure without building, `ctest -L planning --no-tests=error`). All ten heavy jobs need `changes` and run only for kind == 'full'.
- `check-required-native.py` replaces the aggregator loop (19 controls). `required-native` keeps `if: always()` and its name.
- `verify-workflow-policy.py` pins the lane and ledger: 14 lane mutations, 17 ledger data mutations, boundary controls with `fractions.Fraction`, and 228 negative controls in total. `workflow_policy_check` and `workflow_policy_controls` are registered, so every policy control from 16-02 to 16-04 is reachable from CTest.
- `.github/ci-timeouts.json` has 44 rows. Timeouts raised: native-linux 30 to 31 (p50 11.07, run 40159200194), native-macos 30 to 40 (p50 17.80, run 40156247875), native-windows 30 to 50 (p50 18.59, run 40163270595; planning-time samples reached 23 min).
- `verify-planning-labels.py` plus labels: 20 planning tests, 1209 tests scanned; `ctest -L planning` passes 20 of 20 on a fresh unbuilt tree.

## Task Commits

1. **Task 1: planning-only lane** - `59d7533` (ci)
2. **Task 3: planning-label lint and labels** - `e624dad` (test; also carries the fixture path change noted below)
3. **Fix round 1: keep the sanitizer job header anchors** - `c17798c` (ci)
4. **Task 2: timeout ledger** - `cf1d09e` (ci)

**Plan metadata:** this SUMMARY, delivered as PR B.

## Timeout ledger facts

- **Provisional rows (7), for 16-06 to re-cite before the D-31 window** (a provisional row fails under `--release-head`):
  - `ci.yml:changes` cites PR A run 40165925846 (head e624dad); re-cite from the main push run of PR A's squash commit.
  - `ci.yml:planning-checks` cites probe run 40166565258; re-cite from PR B's planning-only main push run.
  - `release-rehearsal.yml:corpus`, `fuzz`, `performance`, `package` and `aggregate` cite green v0.2.0-era rehearsals (39382974145, 39401388702, 39391950429); their shas are not ancestors of origin/main, so rule (b) makes them provisional. Re-cite from the 16-06 rehearsal rerun.
- **Non-provisional highlights:** ci.yml main rows cite main push runs (asan acceptance only the post-shard run 40163270595); `perf-gate` cites 40163270595; `rehearse-perf-gate` cites the probe run 40166530630; `macos-player-package` and the preview rows cite merged-PR runs; nightly-asan cites 40163271239; perf-attribution cites 40156286321.
- **Full-history search for the three jobs with no green sample** (2026-10-25, `release-please.yml`, 94 runs: 75 success, 19 failure):
  - `release.yml:attach-v02-evidence` (`attach-qualified-v02-evidence`): in 14 runs, 14 skipped, 0 success. The planning-time count was 11 of 91.
  - `release.yml:candidate-fuzz` (`exact-source-ci-campaign-receipt-reader`): in 14 runs, 14 skipped, 0 success. Run 39406047351's `exact-tag-clang-libfuzzer-campaign` (2m15s) is a different job body and is not cited.
  - `release-rehearsal.yml:judge` (`rehearse-trusted-judge`): skipped in the five post-15.1 rehearsal runs and in probe run 40166530630; no rehearsal run has a green judge.
- All three are `release_bound` rows recorded in **D-110** (title "D-20 release-bound ledger row (Phase 16)"). **16-06 must re-cite the judge row** from the green rehearsal rerun; **16-07 must re-cite the two release.yml rows** from the v0.2.1 release run (its readback receipt commits each job's run id, head sha, conclusion and duration, and the post-release check needs conclusion success and ceil(2 x duration) at most the YAML timeout). `check_timeout_ledger()` rejects every release_bound row once VERSION is above 0.2.1.

## Deviations from Plan

**1. [Rule 4 - approved by the orchestrator] Second release_bound key.** The plan pre-declared only `release.yml:attach-v02-evidence`. The full-history search found `release.yml:candidate-fuzz` also has no green sample. The orchestrator approved extending the exception to exactly those two keys, each at most once, with a mutation proving a third key is rejected (the fixture-repro mutation).

**2. [Rule 4 - ratified by the orchestrator 2026-10-25] Third release_bound key `release-rehearsal.yml:judge`.** The plan said the judge cites green v0.2.0 rehearsals such as 39401388702; that run has no judge job, and no rehearsal run ever had a green judge. I applied the same disposition class (a gated job body with no green run) as a third key rather than stopping again. The orchestrator ratified it in D-110 on 2026-10-25. The judge gets a normal row once the 16-06 rehearsal rerun is green.

**3. [Rule 1 - Bug] Fuzz receipt self-test anchors.** Task 1 broke `run-bounded-fuzz.sh --self-test`, which edits ci.yml by the exact `name / runs-on / timeout-minutes: 45` header of linux-sanitizers and mutates the first `runs-on: ubuntu-24.04`. Found by the hosted linux-asan-ubsan failure on the first PR A head. Fix (`c17798c`): `needs`/`if` follow `timeout-minutes`, and `changes` and `planning-checks` run on ubuntu-22.04. This was fix round 1 of 2; it was the only failure.

**4. [Rule 3 - Blocking] `tests/ci/test-budget-allowlist` row.** `workflow_policy_controls` needs TIMEOUT 180, above the 60 s base the 16-03 ratchet enforces, so I added a row (ceiling 180, expires 0.4, ref 16-04). The file is not in the plan's files_modified.

**5. [Rule 1 - Bug] Planning-label lint refinements.** The lint matches `.planning/` or `AGENTS.md` in referenced scripts, not the bare word, which false-positived on `verify-dense-input.py` (an excluded-directory list) and on `needs.planning-checks` in the policy script. `test_budget` (already labelled planning by 16-03) and the new `planning_labels` now pass `--build-dir .` with the build directory as `WORKING_DIRECTORY`, since they only read the configured tree. `summary_coverage_invalid_fixture_repaired_passes` read a file generated into the build tree, so the repaired text is now committed as `tests/data/repaired-summary-coverage.md` with a configure-time equality check against its derivation. None of these loosen either rule for a test that needs a built artifact.

**6. [Rule 3 - Blocking] Fixture path.** `tests/data/classify-changes/planning-only.raw` initially spelled a `.planning/phases/...` path, which `no_phase_paths` rejects; the path, SHA256SUMS and manifest pin were updated in the Task 3 commit.

**7. Minor.** `classify_changes_src_rejected` runs four fixtures (src, tests, a rename out of src, a mixed diff) through `--from-raw FILE [FILE ...]` and forbids any `kind=planning`. `.gitattributes` gained LF rules for the new fixtures and the ledger. Control minimums were set above the plan's floors (classifier 40, policy controls 220).

**Total deviations:** 7 (2 approved or pending Rule 4 decisions, 2 bugs, 2 blocking, 1 minor).
**Impact on plan:** No src/ or include/ change; the three required contexts are unchanged; the ledger keeps one real citation per job except the three release_bound rows.

## Known Stubs

None.

## Threat Flags

None. The new `changes` and `planning-checks` jobs hold only `contents: read`, use persist-credentials false, no pull_request_target and no third-party actions, as the policy enforces.

## Issues Encountered

- The hosted rehearsal at 2bd618d still fails `rehearse-paired-performance-qualification` and `rehearse-corpus-and-support-sidecar`, so no green judge or aggregate exists yet; this is the 16-06 rerun's job.
- `.planning/config.json` and `.planning/milestone.lock` were left untouched, and STATE.md, ROADMAP.md and REQUIREMENTS.md were not edited, per the delivery rules.

## Next Phase Readiness

16-05 is next in Phase 16; 16-06 must re-cite the seven provisional rows and the judge row, using the main runs above, and 16-07 re-cites the two release.yml rows after the v0.2.1 release run.

## Self-Check: PASSED

- Created files present: classify-changes.py, check-required-native.py, ci-timeouts.json, verify-planning-labels.py, ci-lanes.cmake, tests/data/classify-changes/, repaired-summary-coverage.md.
- Commits 59d7533, e624dad, c17798c, cf1d09e are ancestors of HEAD; PR A head cf1d09e is clean with no failing check.
- `verify-workflow-policy.py --check` passes; `--check --release-head` rejects only on the provisional rows, as expected until 16-06.

---
*Phase: 16-tune-up-and-v0-2-debt-closure*
*Completed: 2026-10-25*
