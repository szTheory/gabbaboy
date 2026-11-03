---
phase: GB-20-fixture-admission-tune-up
plan: "05"
subsystem: fixture-products
tags: [fixture-admission, product-policy, ctest]
requires:
  - phase: GB-20-fixture-admission-tune-up/20-04
    provides: Bounded fixture admission and product checker
provides:
  - Product policy bytes checked against an independent trusted digest
  - Exact configuration-specific core CMake exports
  - Bounded product-control CTest budgets in the allowlist
affects: [fixture-admission, RIGHTS-01]
tech-stack:
  added: []
  patterns: [Independent SHA-256 policy pin, exact-one generated export group]
key-files:
  created: [.planning/phases/GB-20-fixture-admission-tune-up/20-05-SUMMARY.md]
  modified: [tests/scripts/verify-fixture-admission.py, cmake/FixtureAdmissionPolicy.json, docs/fixture-admission.md, tests/ci/test-budget-allowlist]
key-decisions:
  - Keep RIGHTS-01 pending; byte identity checks do not establish grant scope.
metrics:
  duration: 12 min
  completed: 2026-11-01
  tasks: 2
  files: 4
actuals:
  tokens: 3395
  tasks: 3
  commits: 26
requirements-completed: []
requirements-pending: [RIGHTS-01]
commits: 26
plan_head_before: c37681b019aadc580b53265aaa2f61f3db9b2a92
plan_head_after: 7b73b46ef0c5b71e35239ec0a7444f1747709804
status: complete
completion_scope: Original Tasks 1 and 2 historical evidence plus final security-rescope Task 3; no fixture, rights-policy, or legal-scope change.
pending_follow_up: None for this plan; phase-level review, full verification, and hosted macOS qualification remain with Phase 20 orchestration.
coverage:
  - id: PRODUCT-POLICY-PIN
    description: Product validation rejects a modified complete policy and coordinated forbidden inventory mutation, and accepts only one supported configuration export.
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^(fixture_product_(core|player)_controls|installed_runner_smoke|preview_package_smoke)$'"
        status: pass
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^test_budget(_controls)?$'"
        status: pass
  - id: FORBIDDEN-GENERATED-BYTES
    description: Forbidden fixture bytes are rejected at required and one_of generated product paths for both layouts while clean products and exact pinned file identities remain accepted.
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^(fixture_product_core_controls|fixture_product_player_controls)$'"
        status: pass
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^(fixture_product_(core|player)_controls|installed_runner_smoke|preview_package_smoke)$'"
        status: pass
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^v02_source_archive_controls$'"
        status: pass
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^(plan_cap|planning_hygiene_controls|summary_coverage_live)$'"
        status: pass
---

# Phase GB-20 Plan 05: Product Policy Pin Summary

The trusted checker now pins complete product policy bytes and permits only one known configuration-specific core export.

## Final security-audit forbidden-digest follow-up completed

The latest research addendum confirmed known forbidden fixture bytes could bypass digest checks at allowed generated paths, including `one_of` alternatives. Task 3 now checks those digests before generated path exemptions while preserving exact pinned identities of already-approved files whose shared license text also appears in the forbidden source set.

The production validator now rejects forbidden digests before generated and `one_of` path handling. A collision existed between shared fixture license text and bytes in other forbidden fixture trees; the narrow exception permits that digest only at its pinned file path with exact pinned size and digest, after which the normal identity check still applies. The core `one_of` and a self-test-only player `one_of` group both exercise the production validator; the pinned policy remains unchanged. Required and `one_of` generated leaks reject as `product-fixture-leak` in both layouts. Focused product, installed/preview, source-archive, and planning controls pass. RIGHTS-01 remains pending and final Phase 20 security closure is separate.

## Accomplishments

- Added a checker-owned policy digest and controls for altered policy bytes and a coordinated forbidden-fixture policy rewrite.
- Matched exactly one Debug, Release, RelWithDebInfo, or MinSizeRel CMake export while rejecting arbitrary or simultaneous exports.
- Retained the product control budgets and added their missing allowlist references without changing global ceilings.
- Kept fixture bytes, rights records, notices, and admission status unchanged.

## Task Commits

- `d956bee4`: Pin exact product policy and configuration exports.
- `462cc289`: Track bounded product control runtimes.
- `7b73b46e`: Reject known forbidden digests at generated paths before path exemptions.

## Verification

- Focused product, installed-runner, and preview package CTests passed.
- Budget allowlist controls passed, including stale and missing-row negatives.
- RED: before the production check moved, both core and player controls accepted a forbidden digest at a required generated path.
- GREEN: core and player package controls passed, including required and `one_of` generated leak negatives with exact `product-fixture-leak` reasons and valid pinned product positives.
- `cmake --preset phase1 && cmake --build --preset phase1 -j2` passed after the implementation commit.
- `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(fixture_product_core_controls|fixture_product_player_controls)$'` passed.
- `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(fixture_product_(core|player)_controls|installed_runner_smoke|preview_package_smoke)$'` passed.
- `ctest --preset phase1 --output-on-failure --no-tests=error -R '^v02_source_archive_controls$'` passed.
- `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(plan_cap|planning_hygiene_controls|summary_coverage_live)$'` passed.

## Deviations from Plan

### Security-rescope semantic adjustment

The full forbidden digest set contains shared license text that is also an exact pinned allowed product file. An unconditional digest-first rejection made clean core and player product positives fail. Per the phase owner’s decision, a forbidden digest is exempt only when the entry path, size, and digest exactly match a pinned `kind: file` expectation; the normal identity check still follows. Generated and `one_of` entries have no pinned file digest and reject the bytes. The player `one_of` test uses a self-test-only group because the reviewed pinned player policy currently has none; the policy itself remains unchanged.

## Original Tasks 1–2 Self-Check: PASSED (historical)

- Both task commits are ancestors of this summary's implementation head.
- The recorded plan range contains two commits. Rights clearance remains pending.

## Task 3 Self-Check: PASSED

- Implementation commit `7b73b46e` is the recorded task head.
- Reconfigured and built successfully at the committed implementation head.
- All four plan verification commands passed; both product layouts retained clean positives and rejected required/`one_of` generated forbidden bytes semantically.
