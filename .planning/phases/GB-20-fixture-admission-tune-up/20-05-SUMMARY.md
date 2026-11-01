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
  tokens: 2411.75
  tasks: 2
  commits: 2
requirements-completed: []
requirements-pending: [RIGHTS-01]
commits: 2
plan_head_before: c37681b019aadc580b53265aaa2f61f3db9b2a92
plan_head_after: 462cc2898428dcaed6e93c115761516964854401
status: complete
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
---

# Phase GB-20 Plan 05: Product Policy Pin Summary

The trusted checker now pins complete product policy bytes and permits only one known configuration-specific core export.

## Accomplishments

- Added a checker-owned policy digest and controls for altered policy bytes and a coordinated forbidden-fixture policy rewrite.
- Matched exactly one Debug, Release, RelWithDebInfo, or MinSizeRel CMake export while rejecting arbitrary or simultaneous exports.
- Retained the product control budgets and added their missing allowlist references without changing global ceilings.
- Kept fixture bytes, rights records, notices, and admission status unchanged.

## Task Commits

- `d956bee4`: Pin exact product policy and configuration exports.
- `462cc289`: Track bounded product control runtimes.

## Verification

- Focused product, installed-runner, and preview package CTests passed.
- Budget allowlist controls passed, including stale and missing-row negatives.

## Deviations from Plan

None.

## Self-Check: PASSED

- Both task commits are ancestors of this summary's implementation head.
- The recorded plan range contains two commits. Rights clearance remains pending.
