---
phase: GB-20-fixture-admission-tune-up
plan: "07"
subsystem: workflow-policy
tags: [workflow-checks, fixture-admission, negative-controls]
requires:
  - phase: GB-20-fixture-admission-tune-up/20-05
    provides: Pinned product policy boundary
provides:
  - Exact fixture-admission command matching in CI workflow subjects
  - Complete temporary workflow subject preflight
affects: [fixture-admission, CI]
tech-stack:
  added: []
  patterns: [Parsed shell words and assignments, preflight before subject materialization]
key-files:
  created: [.planning/phases/GB-20-fixture-admission-tune-up/20-07-SUMMARY.md]
  modified: [.github/scripts/verify-workflow-policy.py, tests/data/workflow-policy-controls.json]
key-decisions:
  - Require exactly one trusted repository-root assignment and reject command prefixes or duplicate roots.
metrics:
  duration: 10 min
  completed: 2026-11-01
  tasks: 2
  files: 2
actuals:
  tokens: 2810.5
  tasks: 2
  commits: 2
requirements-completed: []
requirements-pending: [RIGHTS-01]
commits: 2
plan_head_before: 462cc2898428dcaed6e93c115761516964854401
plan_head_after: 9d69d015f0be2a6c7d743039672b9e4a92d73768
status: complete
coverage:
  - id: EXACT-WORKFLOW-GATE
    description: Fixture admission workflow calls must match exact parsed command words and repository root, while missing subject inputs fail before copying.
    human_judgment: false
    verification:
      - kind: integration
        ref: "python3 -I .github/scripts/verify-workflow-policy.py --self-test --group ci --root ."
        status: pass
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^workflow_policy_group_ci$'"
        status: pass
---

# Phase GB-20 Plan 07: Exact Workflow Admission Summary

Workflow policy now matches fixture admission gates as exact commands and rejects incomplete temporary subjects before copying.

## Accomplishments

- Added exact parsed command matching for the fixture-reproduction and macOS package gates, including one `--repo-root .` and no untrusted prefix.
- Preflighted all required subject inputs, including the release-candidate checker, before materializing a test subject.
- Added path-prefix, duplicate-root, moved/removed gate, and incomplete-subject negative controls.
- Kept source fixture material and rights dispositions unchanged.

## Task Commits

- `e8f97927`: Require exact fixture admission commands.
- `9d69d015`: Prove incomplete workflow subjects fail closed.

## Verification

- Workflow CI group CTest passed, including grouped negative controls.
- A missing required checker source rejected before target creation, with source tree unchanged.

## Deviations from Plan

The grouped control fixture was made self-contained after its initial run failed because it lacked `verify-release-candidate.sh`; that required input is now explicit and preflighted.

## Self-Check: PASSED

- Both task commits exist at the recorded plan head; the measured plan range contains two commits.
- RIGHTS-01 remains pending.
