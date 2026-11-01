---
phase: GB-20-fixture-admission-tune-up
plan: "02"
subsystem: fixtures
tags: [core-packaging, product-policy, archive, notices, cmake, python]
requires:
  - phase: GB-20-fixture-admission-tune-up
    provides: Shared core product policy, immutable fixture identities, and product checker API from Plan 20-01
provides:
  - Actual installed and extracted core products are checked against shared policy and stage inventory
  - Core archive and release checks validate actual archive members and MIT sidecar bytes
  - Exact approved product-policy paragraph exception is covered while other notice bytes remain pinned
affects: [phase-20-release-qualification, core-packaging, fixture-policy]
actuals:
  tokens: 14023
  tasks: 3
  commits: 8
tech-stack:
  added: []
  patterns:
    - Bounded archive members route through the shared exact product-entry policy
    - Release sidecars are validated from their actual bytes and established asset name
key-files:
  created:
    - .planning/phases/GB-20-fixture-admission-tune-up/20-02-SUMMARY.md
  modified:
    - cmake/VerifyInstalledPackage.cmake
    - cmake/PreviewPackageSmoke.cmake
    - .github/workflows/preview.yml
    - tests/scripts/verify-v02-source-archive.py
    - tests/scripts/verify-fixture-admission.py
    - tests/scripts/verify-release-candidate.sh
    - THIRD_PARTY_NOTICES.md
    - .planning/phases/GB-20-fixture-admission-tune-up/20-02-PLAN.md
key-decisions:
  - Keep source archive rights evidence separate from binary product policy.
  - Permit only the exact owner-approved product-policy paragraph replacement while pinning all other notice bytes, including historical digest rows.
patterns-established:
  - Validate actual installed, extracted, and release archive bytes using the same shared policy.
requirements-completed: []
requirements-pending: [RIGHTS-01]
coverage:
  - id: D1
    description: Real installed and extracted core products are checked against shared policy and accepted stage inventory before consumers start.
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^preview_package_smoke$'"
        status: pass
    human_judgment: false
  - id: D2
    description: Core archive and extracted-tree controls reject hidden payloads, fixture mutations, and notice changes while preserving source-archive policy.
    verification:
      - kind: integration
        ref: "python3 -I tests/scripts/verify-v02-source-archive.py --self-test"
        status: pass
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^preview_package_smoke$'"
        status: pass
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^fixture_(admission|product_).*'"
        status: pass
    human_judgment: false
  - id: D3
    description: Release checks validate actual core archive and gabbaboy-notices.txt bytes and reject missing, altered, or misnamed sidecars.
    verification:
      - kind: integration
        ref: "bash tests/scripts/verify-release-candidate.sh --self-test"
        status: pass
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^v02_source_archive_controls$'"
        status: pass
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^workflow_policy_group_release_jobs$'"
        status: pass
      - kind: integration
        ref: "python3 -I .github/scripts/verify-workflow-policy.py --self-test --group release_jobs"
        status: pass
    human_judgment: false
duration: 46min
completed: 2026-10-31
status: reopened
completion_scope: Original Tasks 1–3 only; their six task commits, interleaving disclosure, metrics and evidence remain historical.
pending_follow_up: Task 4 — bounded pre-payload metadata and decompressed-stream parsing on source/Linux-core release paths.
plan_head_before: 6075bb2aecc687b287d830bb0f05ed8fcc414d42
plan_head_after: 75f4e835a8192e8e8f94eac075824c29a5c756e1
---

# Phase GB-20 Plan 02: Fixture Admission Tune-up Summary

**Installed, extracted, and released core products now enforce the shared fixture policy against actual archive and notice bytes.**

## Reopened for the final security-audit archive follow-up

Plan 20-02 is incomplete until its appended Task 4 passes. The latest research addendum records hidden PAX metadata bypassing inspect_tar's visible-member payload budget on the source-receipt and Linux/core product paths. The prior metrics, six task commits and passing coverage below remain evidence for Tasks 1–3; they do not establish the new pre-payload per-header/aggregate/count or decompressed-stream guarantees.

The executor acts next on Task 4 in [20-02-PLAN.md](20-02-PLAN.md) under the already authorized in-place security rescope. Add the bounds and direct/CLI production controls, preserve valid source commit comments and trusted checker relocation, and pass v02_source_archive_controls, the release-candidate self-test and planning checks at the committed implementation head. Keep status reopened until then; append actual follow-up commits and fresh block-style coverage after success. No new owner confirmation, plan, dependency, fixture/rights change or live publication is included. Final Phase 20 integration/security closure remains separate.

## Performance

- **Duration:** 46 min
- **Started:** 2026-10-31T20:30:29-04:00 (first task RED commit)
- **Completed:** 2026-10-31T21:16:19-04:00
- **Tasks:** 3
- **Files modified:** 8

## Accomplishments

- Validated actual core install and preview extraction bytes against the shared checker and full accepted stage inventory before runner and C/C++ consumers start.
- Expanded archive and private extracted-tree controls across the approved fixture subtrees, renamed and suffixless payloads, fixture notices, root MIT, and product substitutions. The source archive remains governed by its separate policy.
- Bound release candidate qualification to the actual archive and named `gabbaboy-notices.txt` bytes. Missing, altered, and misnamed sidecars are negative controls.
- Clarified the binary product notice paragraph while preserving every historical digest row and every other byte from the baseline notice file.

## Task Commits

1. **Task 1: Validate one real install through archive extraction and consumer startup** — `bc73db95` (RED), `96a5f92e` (GREEN).
2. **Task 2: Close the real core subtree and archive mutation gaps** — `5825b1b4` (RED), `845a74a4` (GREEN).
3. **Task 3: Enforce actual core release and sidecar bytes at producer and download boundaries** — `7c203c23` (RED), `75f4e835` (GREEN).

The required plan commit ledger measured 8 commits from `plan_head_before` through `plan_head_after`; it includes two interleaved Plan 20-03 commits on the shared branch. The six task commits listed above are the Plan 20-02 commits. No Plan 20-03 files were staged or changed by this plan.

## Files Created/Modified

- `cmake/VerifyInstalledPackage.cmake` — checks actual installed core bytes through the shared policy.
- `cmake/PreviewPackageSmoke.cmake` — validates the installed and extracted package inventories and exercises private mutation controls.
- `.github/workflows/preview.yml` — fetches full history for independent baseline blob checks.
- `tests/scripts/verify-v02-source-archive.py` — routes bounded archive entries and optional sidecar bytes through product policy.
- `tests/scripts/verify-fixture-admission.py` — accepts only the exact approved product paragraph replacement and tests surrounding-text, removal, changed-claim, and digest-row negatives.
- `tests/scripts/verify-release-candidate.sh` — supplies actual named sidecar bytes to archive policy and tests sidecar failures.
- `THIRD_PARTY_NOTICES.md` — clarifies the exact binary product fixture policy without changing historical digest rows or root MIT terms.
- `20-02-PLAN.md` — records the owner-approved narrow shared-checker exception.

## Decisions Made

- Preserve the source archive’s separate rights and fixture contract; product checks do not imply legal grant clearance.
- Apply the owner-approved exception only to the exact product-policy paragraph bytes. The unchanged baseline also passes; arbitrary paragraph edits, removal, altered claims, and historical digest-row changes fail.
- Keep the already established release sidecar name and validate its supplied bytes. No new receipt type or release asset family was added.

## Deviations from Plan

### Approved scope amendment

The owner approved a narrow shared-checker exception for the exact product-policy paragraph in `THIRD_PARTY_NOTICES.md`. The Plan 20-01 checker accepts either the unchanged baseline or that exact paragraph replacement and pins every other byte. Positive and negative checker controls cover the approved replacement, unrelated prose, paragraph removal, changed claim, and historical digest rows. This records package scope only and makes no legal grant judgment.

### Execution adjustment

The initial preview mutation approach started a separate CMake checker process per mutation and exceeded the focused CTest time budget. The exhaustive private-tree matrix was moved into the existing Python self-test path, retaining a production-boundary preview control. The final `preview_package_smoke` CTest passed in 38.61 seconds, with the self-test covering 26 private-tree negatives.

## Issues Encountered

- The local full `--build-package` command remained blocked by two existing Cocoa menu tests that need an unavailable display service. The phase owner deferred hosted macOS qualification until a coherent final Phase 20 branch head. Plan 20-02’s focused checks passed; final-head and hosted qualification remain with phase orchestration.
- The shared branch contained two already committed Plan 20-03 changes during this plan. They were left untouched and are disclosed in the measured commit count above.

## User Setup Required

None.

## Next Phase Readiness

Original Tasks 1–3 are complete; Plan 20-02 is reopened for Task 4 above. Phase orchestration still owns the remaining Phase 20 work and final-head qualification. No fixture was admitted; `RIGHTS-01` remains pending.

---
*Phase: GB-20-fixture-admission-tune-up*
*Completed: 2026-10-31*

## Original Tasks 1–3 Self-Check: PASSED (historical)

- Summary file exists.
- All six Plan 20-02 task commits are ancestors of the plan task head.
- GSD coverage classifier reports all three deliverables as automatically covered.
- Required focused package, archive, release-sidecar, fixture-product, and release-workflow controls passed.
