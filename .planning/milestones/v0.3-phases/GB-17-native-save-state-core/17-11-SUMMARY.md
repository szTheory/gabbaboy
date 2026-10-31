---
phase: GB-17-native-save-state-core
plan: "11"
subsystem: testing
tags: [release-gates, owner-approval, nightly-replay, boundary, workflow-policy, RM-030]

requires:
  - phase: GB-17-native-save-state-core/17-10
    provides: "The trusted-revision release path, the exact-tree rehearsal selection, the workflow policy and the lifecycle replay that these gates are wired into"
  - phase: GB-16-tune-up-and-v0-2-debt-closure
    provides: "The deterministic Ir ratchet and exception receipt schema, the nightly receipt and the Phase 16 history this plan preserves"
provides:
  - "verify-release-gates.py: --digest, --review-approval and --nightly-gate with 8 owner-approval and 6 nightly named mutants plus 62 further controls"
  - "A widened Ir limit reaches the real ratchet only through a verified OWNER approval bound to the full measurement digest, cause, per-ROM band and approved limit; the unverified receipt bypass is gone"
  - "The publisher runs the exact-tree nightly ASan replay gate from the trusted revision after the final byte gate and before the one publication transition"
  - "verify-state-contract.py --boundary --rev SHA reads a phase boundary from one literal commit"
affects: [GB-17-verification, release-evidence, workflow-policy, GB-18, GB-19]

boundary_sha: d53ec9c34e42094e6b468f5ca725afe28cb4e819
final_source_head: d2d27eba14e50deaba88256e6465a6350448103e

actuals:
  tokens: 29969
  tasks: 3
  commits: 6

tech-stack:
  added: []
  patterns:
    - "An approval is credited only after it is bound to the exact subject digest and the receipt it produces is judged again by the downstream verifier"
    - "Evidence is chosen newest-first at an exact head, and a newer red or other-head run supersedes an older green one"
    - "A boundary check reads one literal commit through git and is unaffected by the working tree, a later commit or the current HEAD"

key-files:
  created:
    - tests/scripts/verify-release-gates.py
    - tests/scripts/state_boundary.py
  modified:
    - tests/scripts/verify-perf-gate.py
    - tests/scripts/verify-state-contract.py
    - tests/scripts/verify-release-lifecycle.py
    - tests/scripts/run-perf-gate.sh
    - tests/scripts/verify-no-phase-paths.py
    - .github/scripts/release-evidence-lifecycle.sh
    - .github/scripts/verify-workflow-policy.py
    - .github/workflows/release.yml
    - .github/workflows/ci.yml
    - .github/workflows/release-rehearsal.yml
    - docs/release.md
    - tests/CMakeLists.txt
    - tests/cmake/perf.cmake
    - tests/cmake/ci-lanes.cmake
    - tests/expected-tests.txt

key-decisions:
  - "boundary_sha is d53ec9c, the commit at which every Phase 17 plan, the ten completed summaries, the Phase 16 receipts and the six RM-027 rows exist. A commit cannot contain its own hash, so the boundary the CTest pins is a literal earlier commit; the code that was qualified is final_source_head."
  - "The approval wording is derived by the gate from the decision (digest, limit, cause, reference, per-ROM bands), so the owner approves everything the receipt will say and a later edit of any of them changes the expected text."
  - "The nightly head is the rehearsed head proved by the existing trusted tree selection, because the squash commit never has a nightly run of its own; the gate then judges the newest run at that head and a newer run at another head supersedes it."
  - "The boundary facts live in state_boundary.py, not in verify-state-contract.py, because the planning-label lint treats any script that names planning files as a planning reader and that checker is also run by build-tree tests."

patterns-established:
  - "Mutant controls that prove the checker itself: removing each named check from a copy made the matching control fail (11 gate and 7 boundary mutants run)"
  - "One scenario and one workspace serve all hostile lifecycle histories, so a control costs one mode run, not one clone"

requirements-completed: []

coverage:
  - id: RM-030-ir-owner-approval
    description: "A deterministic Ir exception is authorized only by a verified OWNER comment on the recorded review issue that is newer than the issue and carries the exact wording derived from the full canonical measurement digest, the accepted cause and its reference, the per-ROM ratio bands and the approved limit. The eight named mutants (non-owner, wrong issue, wrong digest, missing approval text, prefix-only digest, unrecorded issue, comment predating the issue, prefilled owner fields) are each refused for their own reason, further controls refuse an edited cause, limit, band, measurement, revision, association or reference, an unrelated edit still passes, and a refusal writes no file and edits no input."
    requirement: RM-030
    verification:
      - kind: unit
        ref: "d2d27eba14e50deaba88256e6465a6350448103e: python3 -I tests/scripts/verify-release-gates.py --self-test review-controls --rev d2d27eba14e50deaba88256e6465a6350448103e (controls=38 positives=4)"
        status: pass
      - kind: integration
        ref: "d2d27eba14e50deaba88256e6465a6350448103e: ctest release_review_controls (passed in 1.7 s inside the full -j8 run)"
        status: pass
    human_judgment: false
  - id: RM-030-ir-approval-reaches-ratchet
    description: "The evaluator writes the exact measurement the owner approves, the approved receipt is the only way the widened limit passes the real verify-perf-gate ratchet, the same widening without approval is refused, an approved run still fails on a wrong correctness digest and on a realtime miss, a receipt edited after approval is refused downstream, ordinary advisory timing passes with no approval and an approval offered for it is refused, and the triggered advisory pipeline succeeds without any decision."
    requirement: RM-030
    verification:
      - kind: integration
        ref: "d2d27eba14e50deaba88256e6465a6350448103e: python3 -I tests/scripts/verify-release-gates.py --self-test review-approval --rev d2d27eba14e50deaba88256e6465a6350448103e (controls=5 positives=10) and ctest release_review_approval"
        status: pass
      - kind: unit
        ref: "d2d27eba14e50deaba88256e6465a6350448103e: python3 -I tests/scripts/verify-perf-gate.py --self-test-exception-measurement (controls=2) and ctest perf_exception_measurement"
        status: pass
    human_judgment: false
  - id: RM-030-nightly-exact-head
    description: "The nightly gate selects the newest eligible nightly-asan run at the exact head and requires it completed with success and a successful asan-full-replay job. The six named mutants (failure, wrong head superseded by a newer run, skipped replay, run in progress, no run at the head, older green behind a newer red) and 32 further variants (failed, cancelled, missing or repeated replay job, other workflow, event or branch, another attempt, repeated run id, out-of-order or malformed timestamps, unresolvable head, boundary source of another tree) are each refused for their own reason, the receipt is written exclusively and only on success, and a head and a tagged commit that share a tree are accepted."
    requirement: RM-030
    verification:
      - kind: unit
        ref: "d2d27eba14e50deaba88256e6465a6350448103e: python3 -I tests/scripts/verify-release-gates.py --self-test nightly-controls --rev d2d27eba14e50deaba88256e6465a6350448103e (controls=38 positives=4) and --self-test nightly-gate (controls=2 positives=7)"
        status: pass
      - kind: integration
        ref: "d2d27eba14e50deaba88256e6465a6350448103e: ctest release_nightly_gate and release_nightly_controls"
        status: pass
    human_judgment: false
  - id: RM-030-immutable-boundary
    description: "The Phase 17 boundary check reads plans, summaries, requirement ids, route flags, the Phase 16 receipt blobs, nightly receipt timestamps and the six RM-027 rows from one literal commit. A short, named, upper-case, unresolvable or substituted revision, a missing plan or summary, an unreachable plan_head_after, a later phase, an auto flag, a regenerated historic receipt, a seventh or dropped release_bound row, a version past 0.2.1 with rows left and a receipt checked after its commit or before its run completed are each refused, while an uncommitted edit and a later commit do not change an earlier boundary."
    requirement: RM-030
    verification:
      - kind: unit
        ref: "d2d27eba14e50deaba88256e6465a6350448103e: python3 -I tests/scripts/verify-state-contract.py --boundary --self-test --rev d53ec9c34e42094e6b468f5ca725afe28cb4e819 (controls=31) and --boundary --rev d53ec9c34e42094e6b468f5ca725afe28cb4e819"
        status: pass
      - kind: integration
        ref: "d2d27eba14e50deaba88256e6465a6350448103e: ctest state_boundary_controls (planning label, 13.9 s inside the full -j8 run)"
        status: pass
    human_judgment: false
  - id: RM-030-production-wiring
    description: "The real release paths call the gates: the publisher runs the nightly-gate lifecycle mode from the trusted checkout after the final byte gate and before the publication transition with actions read only, run-perf-gate.sh hands the ratchet only a receipt that --review-approval wrote and no longer accepts a bare receipt, and ci.yml and the rehearsal run the gate controls beside the perf gate. The workflow policy refuses a removed, echoed, tagged-checkout, failure-swallowing, unbound, reordered or over-permissioned nightly call and each broken link of the approval path with 19 new negative controls, and the lifecycle replay runs the production nightly mode against recorded run shapes in both attempts and refuses twelve hostile run histories."
    requirement: RM-030
    verification:
      - kind: integration
        ref: "d2d27eba14e50deaba88256e6465a6350448103e: python3 -I .github/scripts/verify-workflow-policy.py --check and --self-test (negative_controls=366 positive_controls=4)"
        status: pass
      - kind: integration
        ref: "d2d27eba14e50deaba88256e6465a6350448103e: python3 -I tests/scripts/verify-release-lifecycle.py --rev d2d27eba14e50deaba88256e6465a6350448103e --replay (modes=8 publish_decisions=2 live_mutations=0) and --self-test (positives=4 controls=97)"
        status: pass
      - kind: integration
        ref: "d2d27eba14e50deaba88256e6465a6350448103e: bash .github/scripts/verify-release-gates.sh --self-test (exit 0)"
        status: pass
    human_judgment: false
  - id: RM-027-blocker-preserved
    description: "The six release_bound timeout rows stay a named Phase 19 entry blocker: the boundary check requires exactly those rows and the blocker wording at version 0.2.1 and refuses any row left once the version passes 0.2.1. docs/release.md records the approval and nightly contracts and the blocker, and the documentation adoption check passes."
    requirement: RM-030
    verification:
      - kind: other
        ref: "d2d27eba14e50deaba88256e6465a6350448103e: python3 -I tests/scripts/verify-state-contract.py --boundary --rev d2d27eba14e50deaba88256e6465a6350448103e (release_bound=6 version=0.2.1) and python3 -I tests/scripts/verify-v02-adoption.py --check docs"
        status: pass
    human_judgment: false
  - id: phase17-11-no-regression
    description: "The full suite passes at the final source head after a fresh configure, including dmg_baseline, the test inventory and budget, the planning labels and the summary coverage checks."
    verification:
      - kind: integration
        ref: "d2d27eba14e50deaba88256e6465a6350448103e: cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 -j8 --output-on-failure --no-tests=error (1494/1494 passed, 170.9 s)"
        status: pass
    human_judgment: false

duration: 3h
completed: 2026-10-28
status: complete
plan_head_before: 8e3990fad8e9a12b8e7bed31d0de9cf9f244794b
plan_head_after: d2d27eba14e50deaba88256e6465a6350448103e
---

# Phase GB-17 Plan 11: Release Gates Enforced in CTest and the Real Release Paths Summary

**A widened Ir limit now passes only with a verified OWNER approval that is bound to the exact measurement, and publication waits for a successful exact-tree nightly ASan replay; both gates run in CTest and in the release paths, and the Phase 17 boundary is read from one literal commit.**

## Performance

- **Duration:** roughly 3 hours of wall time including reading, design, three full-suite runs and the checker mutation runs (approximate; no per-task clock was kept).
- **Tasks:** 3/3 delivered. Hosted evidence is pending (below); nothing hosted is claimed.
- **Commit ledger:** 6 commits measured from the persisted plan base `8e3990f` to the final code head `d2d27eb`: three task commits and three follow-ups (one lifecycle-cost reduction, one fixture fix, one documentation commit).
- **Diff-size proxy:** 29,969 (119,875 changed characters of non-planning files divided by four; not measured model-token use, and not comparable to the raw plan projection of 65,000).
- **New tests (this host, alone / inside the full -j8 run):** `release_review_approval` 4.6 s / 9.6 s, `release_review_controls` 0.9 s / 1.7 s, `release_nightly_gate` 0.3 s / 0.7 s, `release_nightly_controls` 0.6 s / 1.2 s, `state_boundary_controls` 8.6 s / 13.9 s, `perf_exception_measurement` 0.3 s / 0.5 s. None exceeds 30 s alone. Changed existing tests: `release_lifecycle_controls` 31.8 s inside the full run against a 60 s TIMEOUT (28 s before this plan), `release_lifecycle_replay` 18.2 s, `workflow_policy_controls` 59.3 s inside the full run against 180 s.

## Accomplishments

- **Approval gate.** `verify-release-gates.py --review-approval` verifies one comment against the decision and the measurement, derives the exact expected wording, and only then writes the completed decision and the perf-gate exception receipt into new files. It also checks the measurement internally (closed schema, correctness identity equal to the workload pin, bands recomputed from the instruction counts), that it was taken at `--rev`, and that the limits base it names matches the bytes of that commit. The receipt is judged again by the same `verify_deterministic_exception` the ratchet uses, so a limit that is no widening or does not cover the band is refused with its own code.
- **Ratchet and production path.** `verify-perf-gate.py --evaluate` gained `--emit-exception-measurement`. `run-perf-gate.sh --gate` now emits the measurement, asks the gate for the receipt and hands only that receipt to the evaluator. The previous `GBB_PERF_EXCEPTION_RECEIPT` path, which let any self-attested receipt through, is removed (Deviation 2).
- **Nightly gate.** `--nightly-gate` implements the newest-at-exact-head selection with run id, attempt, event, workflow, branch, status and timestamp checks; the `nightly-gate` lifecycle mode feeds it saved `gh run list` and `gh run view` JSON for the rehearsed head and the publisher runs it before publication.
- **Boundary.** `verify-state-contract.py --boundary --rev SHA` (facts in `state_boundary.py`) with 31 controls in disposable repositories seeded from the boundary commit's own files.
- **Policy and replay.** 19 new workflow-policy mutants (366 negative controls now, from 347) and a nightly replay in the lifecycle lab with twelve hostile histories (97 controls now, from 85).

## Task Commits

1. **Task 1 (tracer)** `d53ec9c` (`feat`): approval gate, `--emit-exception-measurement`, `release_review_approval`, `release_review_controls`, `perf_exception_measurement`. The whole `verify-release-gates.py` was written in this commit, so the nightly code is present but unregistered until Task 2.
2. **Task 2** `687dfe4` (`feat`): nightly CTests, `--boundary`, `state_boundary_controls`.
3. **Task 3** `0033c2c` (`feat`): production wiring, policy and lifecycle replay. Follow-ups `3198fb0` and `1e0cd9a` (`test`) cut the lifecycle control cost and clear the receipt between cases; `d2d27eb` (`docs`) documents the contracts and raises the lifecycle floor.

## CLI Registry

- `verify-release-gates.py --digest --measurement FILE`; `--review-approval --comment-json FILE --decision FILE --measurement FILE --rev SHA [--output FILE] [--exception-receipt FILE]`; `--nightly-gate --runs-json FILE --run-json FILE --head SHA --output FILE [--rev SHA] [--branch NAME] [--checked-at TIMESTAMP]`; `--self-test [review-approval|review-controls|nightly-gate|nightly-controls] --rev SHA`.
- `verify-perf-gate.py --evaluate ... --emit-exception-measurement FILE`; `--self-test-exception-measurement`.
- `verify-state-contract.py --boundary --rev SHA [--repo DIR] [--self-test]`.
- `release-evidence-lifecycle.sh nightly-gate`.
- CTests: `release_review_approval`, `release_review_controls`, `release_nightly_gate`, `release_nightly_controls`, `state_boundary_controls`, `perf_exception_measurement`. Floors: `workflow_policy_controls` 300 to 360, `release_lifecycle_controls` 75 to 95.

## Verification

All at final source head `d2d27eba14e50deaba88256e6465a6350448103e` unless stated:

- `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 -j8 --output-on-failure --no-tests=error`: 1494/1494 passed in 170.9 s, `dmg_baseline` 8.0 s included.
- `python3 -I tests/scripts/verify-release-gates.py --self-test --rev d2d27eb...` (four suites pass); `verify-perf-gate.py --self-test-exception-measurement`; `verify-state-contract.py --boundary --self-test --rev d53ec9c...` and `--boundary --rev` at both `d53ec9c` and `d2d27eb`; `verify-release-lifecycle.py --replay` and `--self-test`; `verify-workflow-policy.py --check` and `--self-test` (366 negative, 4 positive); `bash .github/scripts/verify-release-gates.sh --self-test` (exit 0); `verify-planning-hygiene.py --check plan-cap --rev d2d27eb...` (phases=4 plans=18); `verify-no-phase-paths.py --check`; `verify-planning-labels.py --build-dir build` (tests=1494 planning=37); `verify-test-budget.py --build-dir build --base <HEAD at start>` (tests=1491 allowlisted=79 at the first commit; the later full run includes it as a CTest).
- **Discriminating power.** On copies of the checkers, removing the owner check, the issue check, the comment-time check, the prefilled-field check, the exact-text check, accepting a prefix digest, taking the oldest run, accepting a skipped replay, ignoring a superseding run, accepting an in-progress run and writing on refusal were each killed by the matching named control (11 of 11). Disabling the historic-receipt pin, the receipt-time check, the later-phase check, the ancestry check, the auto-flag check, the revision-format check and the six-row comparison was each killed by the boundary controls (7 of 7).

## Hosted evidence pending (not claimed)

No hosted run exists for these changes. The parent should push the branch and require, at the exact head that contains `d2d27eb` (the summary commit changes planning files only):

1. The required exact-head checks of PR 130: native Linux, macOS and Windows, the ASan/UBSan lane, fuzz, `perf-gate` (which now also runs the four release-gate suites), the package checks and `required-native`. The new CTests are cross-platform; they were run on this host only.
2. The hosted time of `release_lifecycle_controls` (POSIX only, 31.8 s here inside a loaded run against a 60 s TIMEOUT). If the hosted time approaches 60 s it is a pending failure under GB-CI-012; the remedy is fewer controls or an allowlisted ceiling with a cited run, not a silent bump.
3. The first real release run is the first execution of the `nightly-gate` step (GitHub-shaped `gh run list` and `gh run view --json` output with the field lists named in the lifecycle script). The replay serves recorded shapes of exactly those lists, not captured GitHub responses; the operator-run dry order is: dispatch `nightly-asan.yml` on `rehearsal/<tag>` at the rehearsed head, then release.

## Decisions Made

See `key-decisions`. In addition: the self-test for the owner approval runs the real perf-gate CLI over the canned fixtures with a widened limit in a disposable copy, so it exercises the actual ratchet, not a model of it; and `nightly_gate` never applies a freshness window, because a clock is not evidence (AGENTS.md), only ordering of the recorded timestamps.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] The planning-label lint forbids planning knowledge in `verify-state-contract.py`**
- **Found during:** Task 2. That checker is run by build-tree tests that cannot carry the planning label, and a script whose text names `.planning/` is treated as a planning reader.
- **Fix:** the boundary facts are in `tests/scripts/state_boundary.py`, loaded by `--boundary`; `state_boundary_controls` carries the planning label; `verify-no-phase-paths.py` has one count-pinned row for its single `PHASES_AT_REV` constant (the same point-in-time class as the plan-cap reader).
- **Files:** `tests/scripts/state_boundary.py`, `tests/scripts/verify-state-contract.py`, `tests/scripts/verify-no-phase-paths.py`. **Commit:** `687dfe4`.

**2. [Rule 2 - Missing critical security] An unverified exception receipt could reach the ratchet**
- **Found during:** Task 3. `run-perf-gate.sh` passed `GBB_PERF_EXCEPTION_RECEIPT` straight to the evaluator, whose `external_verification` is self-attested (a digest anyone can compute), so the OWNER gate (T-17-27) could be bypassed.
- **Fix:** removed; the only receipt that reaches the evaluator is the one `--review-approval` wrote, and the workflow policy refuses the variable's return (mutant G17-12). **Commit:** `0033c2c`.

**3. [Rule 3 - Blocking] Files outside the plan's list**
- The lifecycle script, `verify-release-lifecycle.py`, `run-perf-gate.sh`, `ci.yml`, `tests/cmake/perf.cmake` and `tests/cmake/ci-lanes.cmake` had to change for the gates to be called, replayed and counted. The plan's `.github/scripts/verify-release-gates.sh` and `release-rehearsal.yml` entries: the shell gate needed no change (the new mode does not need it) and the rehearsal gained only the control step.

**4. [Scope] Boundary pinned to an earlier literal commit**
- The CTest pins `d53ec9c` because a commit cannot contain its own hash and the boundary must not follow the moving HEAD. The final qualified head is recorded separately (`final_source_head`). If the owner wants a later boundary, change the one constant in `tests/CMakeLists.txt` and the `boundary_sha` here together.

### Auth gates

None. Only read-only `gh api` calls on this public repository were used (see the open item).

## Open items for verification

- **`release.yml:candidate-performance` citation (`--verify-cited` reports `FAIL ... job missing or not successful`).** Not in this plan's scope and not fixable honestly here. The job was renamed to `exact-tag-advisory-paired-performance-observation` after run 39406047351, and a read-only `gh api` of the published release run 40332345735 shows the job still under its older name `exact-tag-paired-performance-qualification` (success, 9 s, 2026-10-26). No run with the new name exists, so a real re-citation needs the next release run. Neither a `release_bound` row (a seventh RM-027 row needs plan authority) nor an invented run was added. The exact next step: after the first release run in which that job succeeds, update the row's `cited_run_id`, `cited_sha`, `p50_minutes` and `samples` from that run, or accept the rename as the recorded open item until then.
- IN-03 from 17-10 is closed by `fdce605`/`50fda9e` and is unaffected.
- RM-027 stays a Phase 19 entry blocker. `requirements-completed` is empty because the parent owns requirement state.

## Known Stubs

None. The `gh` in the lifecycle lab and the canned perf-gate fixtures are declared test stand-ins; `gh run list` and `gh run view` serve recorded JSON of exactly the field lists the production mode requests.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: privilege | .github/workflows/release.yml | `publish-qualified-release` now holds `actions: read` (read-only, used to list nightly runs), enforced as exactly `read` by the workflow policy |

## Next route

- **Completed stage:** Phase 17 execution (plans 17-01 through 17-11; no gap plan was used).
- **Next stage:** Phase 17 verification. Run `/gsd-verify-work 17`. Closure is written with `python3 -I tests/scripts/verify-uat-closure.py <phase-dir> --write <evidence>` and checked with `--self-test`; do not hand-write UAT.md.
- **Next phase:** 18, Player Save Slots and Host Contract, only after the owner chooses to continue. Auto-advance flags are unchanged (both false). No Phase 18 work was started.

## Self-Check: PASSED

All created and modified files exist, the six code commits (`d53ec9c`, `687dfe4`, `0033c2c`, `3198fb0`, `1e0cd9a`, `d2d27eb`) are ancestors of HEAD, and `.planning/config.json` is still the owner's uncommitted edit.
