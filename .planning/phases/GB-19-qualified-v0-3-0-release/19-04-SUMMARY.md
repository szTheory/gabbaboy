---
phase: GB-19-qualified-v0-3-0-release
plan: "04"
subsystem: release
tags: [github-actions, release, github-api, ctest, immutable-replay]
requires:
  - phase: GB-19-qualified-v0-3-0-release/19-01
    provides: release workflow policy and timeout controls
  - phase: GB-19-qualified-v0-3-0-release/19-03
    provides: tree-bound version-window checker and CTest infrastructure
provides:
  - exact-version-PR binding for nightly and candidate rehearsal runs
  - trusted pre-tag version PR gate and tree-only active window validation
  - immutable post-tag endpoint inventory and refreshed sanitized API captures
  - separate post-tag lifecycle control CTest
affects: [GB-19-qualified-v0-3-0-release/19-05]
actuals:
  tokens: 46540
  tasks: 4
  commits: 7
commits: 7
plan_head_before: f3ace2c244d4c05b893647433fb97db3cf31d33d
plan_head_after: 24a69f5c67aa348c4f8c1a933d48b38d3e85d485
tech-stack:
  added: []
  patterns:
    - Immutable source revisions are the input to endpoint and workflow trust checks.
    - Captured GitHub response schemas declare every consumed path and reject reshaped responses.
key-files:
  created:
    - .github/workflows/version-pr-gate.yml
  modified:
    - .github/scripts/release-evidence-lifecycle.sh
    - .github/scripts/verify-release-source-proof.py
    - .github/scripts/verify-release-gates.sh
    - .github/scripts/verify-workflow-policy.py
    - .github/scripts/verify-test-inventory.sh
    - .github/workflows/release.yml
    - .github/workflows/release-rehearsal.yml
    - tests/scripts/verify-version-window.py
    - tests/scripts/verify-release-lifecycle.py
    - tests/data/release-api/captured.json
    - tests/data/release-api/SOURCES.md
    - tests/cmake/ci-lanes.cmake
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - cmake/ExpectedTests.cmake
key-decisions:
  - "OQ-4: use a dedicated pull_request version-pr-gate with a trusted base-SHA checkout, rather than extending ci.yml."
  - "OQ-5: keep the pre-tag gate informational until the owner configures required checks; 19-07 documents merge discipline."
  - "D-21: every observed post-tag GitHub CLI form is replayed against a declared capture contract or tied to a named workflow-policy rule."
patterns-established:
  - "A rehearsal is selected once and refused on any head, merge-time, attempt, or tag-order mismatch; there is no fallback."
  - "The endpoint inventory parses immutable lifecycle, judge, and release workflow sources and checks route or policy coverage."
metrics:
  duration: 53min
  completed: 2026-10-29
  status: complete
requirements-completed: []
coverage:
  - id: D1
    description: Nightly and candidate release gates bind the selected rehearsal to the exact merged version PR head and merge time, and reject reused postdated attempts without fallback.
    requirement: REL-01
    human_judgment: false
    verification:
      - kind: integration
        ref: "At immutable source f0aef194ef0218a4bc08fee45207c008e5ac34c5, nightly replay and refusal controls passed; `release_lifecycle_replay` retained publish_decisions=2 and live_mutations=0."
        status: pass
      - kind: integration
        ref: "At immutable source 67eb73db0452d1a6d24db7d871362be08d6bfc76, release_lifecycle_replay, release_nightly_gate, and release_nightly_controls passed."
        status: pass
  - id: D2
    description: The version PR receives a trusted read-only pre-tag gate, and active version-window records must match the version in their own immutable tree.
    requirement: REL-01
    human_judgment: false
    verification:
      - kind: integration
        ref: "At immutable source 703800972c0cc249ea6310dec55f0cef7a31bceb, release_window_contract, release_window_controls, workflow_policy_check, and workflow_policy_controls passed; trigger, trusted checkout, permissions, step timeouts, and refusing policy mutants were checked."
        status: pass
      - kind: integration
        ref: "workflow_policy_controls measured 44.01s for Task 1, 44.41s for Task 2, and 53.58s for Task 3; the existing 180s timeout was retained."
        status: pass
  - id: D3
    description: A 22-form immutable endpoint inventory covers lifecycle, judge, and release workflow calls; the sanitized capture includes the exact-source v0.2.1 CI run and rejects missing response members.
    requirement: REL-01
    human_judgment: false
    verification:
      - kind: integration
        ref: "At immutable source 65c58159e1f9e82aa2bb6f1ec75414bae0ba2668, direct post-tag controls reported controls=80 and endpoints=22; the suite rejects unlisted lifecycle/workflow forms and missing REQUIRED_PATHS."
        status: pass
      - kind: other
        ref: "At immutable source 67eb73db0452d1a6d24db7d871362be08d6bfc76, the replay capture digest/schema/sanitization contract passed at 168019 bytes; ci_run is 40259198255, path .github/workflows/ci.yml, event push, head b93137f00d07b11dc74e40330e0ddf6029c0677d."
        status: pass
  - id: D4
    description: The lifecycle replay and post-tag controls are registered in CTest and correctly excluded on Windows while the inventory self-test retains platform checks.
    requirement: REL-01
    human_judgment: false
    verification:
      - kind: integration
        ref: "At immutable source 67eb73db0452d1a6d24db7d871362be08d6bfc76, replay passed in 14.46s, baseline controls in 30.70s, post-tag controls in 34.00s, nightly gate in 0.67s, and nightly controls in 1.18s; all were below 60s. At 24a69f5c67aa348c4f8c1a933d48b38d3e85d485, the corrected 80-control floor passed in 19.04s."
        status: pass
      - kind: other
        ref: "At final source 24a69f5c67aa348c4f8c1a933d48b38d3e85d485, bash .github/scripts/verify-test-inventory.sh --self-test passed platform exclusions, platform-independent retention, missing-test rejection, and the cleanup-trap control."
        status: pass
---

# Phase 19 Plan 04: Rehearsal Binding Summary

**The release path now binds rehearsals to the exact version PR, checks the version window from trusted code, and inventories every post-tag GitHub call.**

## Performance

- **Duration:** 53 min from the first Task 1 commit; executor start time was not persisted.
- **Started:** 2026-10-29T20:22:25Z (first task commit used as the timing baseline).
- **Completed:** 2026-10-29T21:15:15Z.
- **Tasks:** 4.
- **Files modified:** 15 implementation, evidence, and test files.
- **Plan commit count:** 7, measured from `f3ace2c244d4c05b893647433fb97db3cf31d33d` through `24a69f5c67aa348c4f8c1a933d48b38d3e85d485`.
- **Diff size for actuals:** 186161 characters, or 46540 tokens at the estimate's chars/4 scale.

## Accomplishments

- Bound nightly and candidate rehearsal selection to the merged version PR head and server-recorded `merged_at`; the selected attempt's completed job times must not exceed that merge time. A refusal never falls back to an older run. The judge also refuses a rehearsal after the release tag already exists.
- Added the trusted `version-pr-gate.yml` for release-please pull requests. It checks out the PR base SHA, treats the PR head and body as data, has read-only `contents` and `actions` permissions, and uses bounded step timeouts. The active window checker compares the record with the version in the same immutable tree.
- Added the D-21 inventory of 22 distinct GitHub CLI forms across lifecycle code, judge files, and release workflow run blocks. Each form has a replay route and response-path contract or a named workflow-policy rule. The refreshed sanitized capture is 168019 bytes (SHA-256 `f07daba99707dacadfc0a5823c83c3e5779dbbac452807c54cac8edef50351ec`) and includes the exact-source v0.2.1 CI push run `40259198255` for 19-05.
- Split post-tag coverage into `release_lifecycle_post_tag_controls`. It runs 80 negative controls across 22 endpoint forms; the original `release_lifecycle_controls` floor remains 95. Both controls CTests stayed below 60 seconds.
- Preserved the frozen performance limits, immutable base receipt binding, refreshed release-notes receipt, and the Wave 1 integration closure at `f3ace2c2` without policy changes.

## Task Commits

1. **Task 1: nightly rehearsal binding** — `9eac29eac316d61178f638a4cbe2e519b561169a`, `f0aef194ef0218a4bc08fee45207c008e5ac34c5`.
2. **Task 2: candidate rehearsal binding** — `ce46c9020e2f67eabea4c7b686ad6c62f08fba1c`.
3. **Task 3: trusted version PR gate and window rule** — `703800972c0cc249ea6310dec55f0cef7a31bceb`.
4. **Task 4: endpoint inventory and capture** — `67eb73db0452d1a6d24db7d871362be08d6bfc76`.
5. **Task 4 CTest floor calibration** — `65c58159e1f9e82aa2bb6f1ec75414bae0ba2668`, superseded by the measured-count correction `24a69f5c67aa348c4f8c1a933d48b38d3e85d485`.

## CTest and Policy Measurements

- `workflow_policy_controls` finished at 44.01s (Task 1), 44.41s (Task 2), and 53.58s (Task 3). The TIMEOUT remains 180s; measured policy floors are 433 POSIX and 411 Windows controls.
- Plan 19-01's earlier `workflow_policy_controls` times were 47.82s, 40.40s, 47.67s, and 49.60s for its four tasks.
- The final focused Task 4 CTest run passed 6/6: `test_budget` 0.17s, lifecycle replay 14.46s, baseline lifecycle controls 30.70s, post-tag controls 34.00s, nightly gate 0.67s, and nightly controls 1.18s. At the corrected final head, the post-tag controls CTest passed with its measured minimum of 80 in 19.04s; `test_budget` passed in 0.12s. The test-inventory self-test passed on both runs.
- The replay output contract continues to require at least seven uploads and exactly two publish decisions with zero live mutations. No lifecycle or policy timeout was raised.

## Files Created/Modified

- `.github/scripts/release-evidence-lifecycle.sh` — nightly PR/merge/attempt binding.
- `.github/scripts/verify-release-source-proof.py` — exact-head, postdate, and tag-exists refusal checks.
- `.github/scripts/verify-release-gates.sh` — calls the trusted version-window check in the candidate path.
- `.github/scripts/verify-workflow-policy.py` — exact-set pins and refusing controls for the new workflow and rehearsal bindings.
- `.github/workflows/release.yml`, `.github/workflows/release-rehearsal.yml`, `.github/workflows/version-pr-gate.yml` — candidate binding, tag guard, and pre-tag PR gate.
- `tests/scripts/verify-version-window.py` — immutable tree-version match and `--require-active` behavior.
- `tests/scripts/verify-release-lifecycle.py` — immutable endpoint inventory, route and schema checks, CI run capture route, and split controls.
- `tests/data/release-api/captured.json`, `tests/data/release-api/SOURCES.md` — refreshed sanitized v0.2.1 response shapes and endpoint provenance.
- `tests/cmake/ci-lanes.cmake`, `tests/CMakeLists.txt`, `tests/expected-tests.txt`, `cmake/ExpectedTests.cmake`, `.github/scripts/verify-test-inventory.sh` — measured control floor and platform-aware test registration.

## Decisions Made

- OQ-4 uses a dedicated `version-pr-gate.yml`, avoiding CI change classification and running trusted base-revision code.
- OQ-5 remains an owner-only branch setting. The new gate is not declared required; 19-07 carries the release merge discipline.
- D-21 uses immutable source scans and an explicit replay-or-policy coverage entry for each CLI form.

## Deviations from Plan

None. The extra Task 4 calibration commits set the CTest minimum to the measured control count of 80; they did not change runtime policy or release behavior.

## Issues Encountered

- The prescribed release-gates self-test initially hit the known sandbox worktree-creation restriction. The scoped escalated retry passed; the failed and passing evidence remain in their separate Task 1 logs.
- The passing CTest wrapper suppresses stdout, so the post-tag control count was read from a direct immutable-revision run (`/tmp/phase19-plan04-task4-posttag-detail.log`). This exposed an initial floor set from elapsed seconds rather than control count; the floor was corrected to 80 and rerun at the final head.

## User Setup Required

None.

## Next Phase Readiness

Plan 19-04 is complete. Continue within Phase 19 with **plan 19-05 — Perf-gate receipt and trusted reader, host smoke, and v0.3.0 readback** using `/gsd-execute-phase 19`. The phase is not complete: REL-01 remains pending until exact-tag publication and readback. D-09 owner acknowledgment remains pending for PR A review, and the two SDL menu-shortcut CTests remain display-limited on this host. Both automatic advance flags remain false.

## Self-Check: PASSED

- The seven plan commits are ancestors of the measured `plan_head_after`; the commit count is measured from the persisted 19-04 ledger.
- The captured response and SOURCES digest match; the capture contract and immutable endpoint controls passed.
- All four coverage entries have `human_judgment: false` and passing automated verification references.
- The source, test, and capture changes introduce no unmodeled runtime trust boundary or deliverable stub.
- Owner changes to `.planning/config.json` and `.planning/state.json` remain unstaged and untouched.

---
*Phase: GB-19-qualified-v0-3-0-release*
*Completed: 2026-10-29*
