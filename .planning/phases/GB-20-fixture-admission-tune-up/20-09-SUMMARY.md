---
phase: GB-20-fixture-admission-tune-up
plan: "09"
subsystem: dense-input-admission
tags: [fixture-admission, source-only-build, immutable-baseline]
requires:
  - phase: GB-20-fixture-admission-tune-up/20-05
    provides: Pinned fixture admission policy
provides:
  - Explicit trusted baseline object source for source-only admission checks
  - Source-only mutant identity remains unknown and unqualified
affects: [fixture-admission, acceptance-tests, RIGHTS-01]
tech-stack:
  added: []
  patterns: [Separate bare Git object store for immutable reads, subject-owned current bytes]
key-files:
  created: [.planning/phases/GB-20-fixture-admission-tune-up/20-09-SUMMARY.md]
  modified: [tests/scripts/verify-dense-input.py, tests/scripts/verify-fixture-admission.py, CMakeLists.txt, docs/fixture-admission.md]
key-decisions:
  - Keep build revision resolution scoped to the source-only subject; baseline evidence cannot qualify the build.
metrics:
  duration: 20 min
  completed: 2026-11-01
  tasks: 2
  files: 4
actuals:
  tokens: 3381.25
  tasks: 2
  commits: 2
requirements-completed: []
requirements-pending: [RIGHTS-01]
commits: 2
plan_head_before: 88b3ccc151d8d5abc65a85649f87d4dd05c3fa87
plan_head_after: fd0070db
status: complete
coverage:
  - id: SOURCE-ONLY-BASELINE
    description: A source-only mutant passes admission through a separately verified fixed baseline object store while its build remains unknown and unqualified.
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^acceptance_dense_input_controls$'"
        status: pass
  - id: SOURCE-ONLY-NEGATIVES
    description: Missing and empty baseline stores reject with baseline-object-unavailable; changed fixture bytes fail closed before consumer execution.
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^(acceptance_dense_input_controls|fixture_admission_controls|fixture_admission_repository)$'"
        status: pass
---

# Phase GB-20 Plan 09: Source-Only Baseline Summary

Source-only dense-input mutants now read immutable fixture baseline objects from a separate local store without inheriting a qualified build identity.

## Accomplishments

- Added an explicit optional baseline object root to the admission checker and the narrow CMake harness cache path; default remains the subject repository.
- Copied and verified the fixed full baseline commit in a disposable bare repository, with subject fixture bytes, manifests, notices, and policy still read from the subject.
- Preserved `unknown` and unqualified build definitions and the real altered-core `predicate-not-reached` semantic failure.
- Added missing-object, empty/wrong-object-store, and changed-fixture fail-closed controls.

## Task Commits

- `e637189a`: Preserve fixture admission for source-only mutants.
- `fd0070db`: Distinguish an unrelated baseline identity.

## Verification

- Reconfigured after the implementation commit.
- The post-commit dense-input, fixture-admission controls, and fixture-admission repository CTests passed (3/3).

## Deviations from Plan

None. The changed legacy fixture control rejects on its missing required admission-record fields before consumer execution; the test asserts that actual rejection reason.

## Self-Check: PASSED

- The task commit is an ancestor of the recorded plan head; the measured range contains one commit.
- Fixture rights and admission status remain unchanged; RIGHTS-01 remains pending.
