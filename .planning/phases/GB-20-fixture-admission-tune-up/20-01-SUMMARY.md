---
phase: GB-20-fixture-admission-tune-up
plan: "01"
subsystem: fixtures
tags: [admission, product-policy, cmake, ctest, git-blobs]
requires: []
provides:
  - Strict fixture admission against immutable Git source, evidence, fixture, and notice bytes
  - Repository and CI checks that reject new or changed fixture evidence before consumption
  - Exact core/player product path policy and stage-to-extraction inventory comparison
affects: [20-02, 20-03, fixture-consumers, release-packaging]
actuals:
  tokens: 34413
  tasks: 3
  commits: 6
tech-stack:
  added: []
  patterns:
    - Standard-library Python checker with bounded JSON, Git object, and product-tree reads
    - Exact package path allowlists with immutable protected-byte digests and complete inventories
key-files:
  created:
    - cmake/FixtureAdmissionPolicy.json
    - docs/fixture-admission.md
    - tests/scripts/verify-fixture-admission.py
  modified:
    - CMakeLists.txt
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - .github/workflows/ci.yml
    - .github/workflows/fixture-repro.yml
    - .github/workflows/release.yml
    - .github/scripts/verify-workflow-policy.py
    - tests/scripts/verify-workflow-policy-coverage.py
    - tests/data/workflow-policy-controls.json
key-decisions:
  - Preserve all historical fixture bytes and dispositions; admit no candidate fixture in this plan.
  - Keep root MIT, tracer, visible-demo, MBC1, SDL notice, and generated product paths separately pinned by producer layout.
  - Treat identities and populated rights fields as byte evidence only; legal grant scope remains unresolved.
patterns-established:
  - New evidence must carry a complete manifest and independent immutable admission commit before repository or public-CI use.
  - Product stage inventories bind exact regular-file paths, sizes, hashes, layout, and policy digest before extracted bytes are consumed.
requirements-completed: []
requirements-pending: [RIGHTS-01]
coverage:
  - id: D1
    description: Fixture admission rejects coordinated rewrites, missing pins, unregistered repository changes, and changed root license bytes.
    verification:
      - kind: integration
        ref: "python3 -I tests/scripts/verify-fixture-admission.py --self-test"
        status: pass
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^fixture_(admission|product_).*'"
        status: pass
    human_judgment: false
  - id: D2
    description: CI and release workflow policy requires admission before fixture consumption and compares actual core bytes before reuse or consumer execution.
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^workflow_policy_(group_(ci|release_jobs)|coverage(_controls)?|check)$'"
        status: pass
      - kind: other
        ref: "python3 -I .github/scripts/verify-workflow-policy.py --check --root ."
        status: pass
    human_judgment: false
  - id: D3
    description: Core and player product trees use distinct exact path maps, protected byte identities, optional MIT sidecar verification, and complete stage inventories.
    verification:
      - kind: integration
        ref: "python3 -I tests/scripts/verify-fixture-admission.py --self-test-packages --layout core"
        status: pass
      - kind: integration
        ref: "python3 -I tests/scripts/verify-fixture-admission.py --self-test-packages --layout player"
        status: pass
      - kind: integration
        ref: "Actual non-testing core install and existing player package stage accepted; extracted core tree matched the written inventory."
        status: pass
    human_judgment: false
duration: 34 min
completed: 2026-10-31
status: complete
commits: 6
plan_head_before: aea002d9278b43b7aa382bf4530e17ceb6107a23
plan_head_after: 749da8f94af9098959559d0fe88ce25633d3a75f
---

# Phase GB-20 Plan 01: Fixture Admission Tune-up Summary

**Fixture admission now rejects unpinned evidence and checks core/player package bytes against immutable fixture and notice identities.**

## Performance

- **Duration:** 34 min
- **Started:** 2026-10-31T19:52:00-04:00 (first recorded RED commit)
- **Completed:** 2026-10-31T20:26:13-04:00
- **Tasks:** 3
- **Files modified:** 12

## Accomplishments

- Added a strict version 1 admission contract, independent commit/blob pins, baseline repository gate, and early CMake/reproduction checks.
- Added immutable-history checks and content-caused CI/release controls for admission, staged core packages, reused packages, and extracted consumer bytes.
- Added separate exact core/player path policies, protected source and notice digests, bounded tree inspection, documentation contract checks, and complete stage inventory comparison.
- Kept the existing fixture tree, manifests, root license bytes, and historical dispositions unchanged. No fixture was admitted and no legal grant scope was adjudicated.

## Task Commits

1. **Task 1: Prove manifest admission through the real CLI** — `6946af68` (RED), `40dc9c70` (GREEN), `83203ed9` (admission boundary and configure gate).
2. **Task 2: Gate repository, CI, and release fixture use** — `f5954e4c` (workflow admission and product checks), `99ab8763` (reviewed workflow control inventory and baseline guard).
3. **Task 3: Pin core and player product layouts** — `749da8f9`.

## Files Created/Modified

- `tests/scripts/verify-fixture-admission.py` — strict admission, repository change, product tree, sidecar, and inventory APIs plus synthetic positive and negative controls.
- `cmake/FixtureAdmissionPolicy.json` — fixed legacy baseline and exact source-to-product mappings, digests, generated files, and SDL notice pin.
- `docs/fixture-admission.md` — record schema, product path contracts, command examples, and legal-scope boundary.
- `CMakeLists.txt`, `tests/CMakeLists.txt`, `tests/expected-tests.txt` — early configure gate and named admission/product CTests.
- `.github/workflows/ci.yml`, `.github/workflows/fixture-repro.yml`, `.github/workflows/release.yml` — immutable history and pre-consumption product gates.
- `.github/scripts/verify-workflow-policy.py`, `tests/scripts/verify-workflow-policy-coverage.py`, `tests/data/workflow-policy-controls.json` — parsed workflow checks, reviewed mutation controls, and source identity binding.

## Decisions Made

- Existing fixtures remain under their historical checks; new or changed payloads require the new versioned admission record and independent pin.
- Core and player layouts have separate exact path contracts. Only explicit producer variants are allowed; a validated stage inventory must match extracted bytes exactly.
- The SDL notice uses the plan’s existing pinned digest. `gabbaboy-notices.txt` remains a separate root MIT copy, and source archives keep their own policy.
- `RIGHTS-01` remains pending because this plan admits no candidate and tooling cannot decide whether any grant legally covers its components.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical integrity binding] Extended the frozen workflow-policy control registry and source audit.**
- **Found during:** Task 2
- **Issue:** The workflow checker’s mutation controls are pinned by a separate coverage audit; new CI/release predicates would otherwise be outside the executable frozen control inventory.
- **Fix:** Added explicit Plan 20 mutation identities, groups, and reviewed source normalization for the new helper functions, globals, and call site.
- **Files modified:** `.github/scripts/verify-workflow-policy.py`, `tests/scripts/verify-workflow-policy-coverage.py`, `tests/data/workflow-policy-controls.json`
- **Verification:** Workflow CI/release mutation CTests and the exact-candidate coverage CTest passed.
- **Committed in:** `f5954e4c`, `99ab8763`

**2. [Rule 3 - Blocking] Raised the existing admission self-test timeout and added bounded package-control timeouts.**
- **Found during:** Task 3
- **Issue:** The full CLI self-test takes about 15 seconds locally; a 30-second limit left little room for slower CI hosts and the new product controls.
- **Fix:** Set admission self-test timeout to 90 seconds and each package-layout control timeout to 120 seconds.
- **Files modified:** `tests/CMakeLists.txt`
- **Verification:** All four focused fixture admission/product CTests passed at final HEAD.
- **Committed in:** `749da8f9`

## Issues Encountered

- Workflow coverage must run against the exact commit captured by CMake configuration. Reconfiguring after the Task 2 and final Task 3 commits made those point-in-time checks pass.
- Task 3’s production self-test controls were added with the product implementation rather than as a separate RED commit. The core/player clean-layout positives and all registered negative controls pass; no planned verification was skipped.
- No candidate game or diagnostic evidence was admitted. Legal grant scope remains unresolved by design.

## User Setup Required

None.

## Next Plan Readiness

Plan 20-02 can consume `check_product_entries`, the tree CLI, and inventory format without changing this plan’s owned policy files. `RIGHTS-01` is not legally cleared by these checks, and the phase owner must preserve that boundary through the remaining plans.

---
*Phase: GB-20-fixture-admission-tune-up*
*Completed: 2026-10-31*

## Self-Check: PASSED

- Summary file exists.
- All six task commits are ancestors of the final plan task commit.
- Final focused CTest run passed all nine fixture and workflow-policy tests.
