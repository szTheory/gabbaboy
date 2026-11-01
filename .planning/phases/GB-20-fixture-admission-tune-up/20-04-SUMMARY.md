---
phase: GB-20-fixture-admission-tune-up
plan: "04"
subsystem: fixtures
tags: [fixture-admission, resource-limits, security, python]
requires:
  - phase: GB-20-fixture-admission-tune-up/20-01
    provides: Shared fixture admission checker and focused CTest controls
  - phase: GB-20-fixture-admission-tune-up/20-02
    provides: Core and player package policy checked by the retained controls
  - phase: GB-20-fixture-admission-tune-up/20-03
    provides: Bounded-input audit finding addressed by this gap closure
provides:
  - Fixture filesystem walks capped at 16,384 descendant entries
  - Git fixture-tree reads capped at 32 MiB and 16,384 records while streaming
  - Child termination, reaping, pipe closure, and reader completion on rejection
affects: [fixture-admission, RIGHTS-01]
tech-stack:
  added: []
  patterns:
    - Incremental os.scandir traversal with a shared descendant-entry cap
    - Concurrent bounded stdout and stderr readers for Git tree enumeration
key-files:
  created:
    - .planning/phases/GB-20-fixture-admission-tune-up/20-04-SUMMARY.md
  modified:
    - tests/scripts/verify-fixture-admission.py
    - docs/fixture-admission.md
key-decisions:
  - Keep the 4,096 manifest-file-list limit and apply separate fixed filesystem and Git tree bounds.
  - Keep RIGHTS-01 pending; these checks establish bounded byte processing, not legal grant scope.
metrics:
  duration: 7 min
  completed: 2026-10-31
  tasks: 2
  files: 2
actuals:
  tokens: 5724
  tasks: 2
  commits: 2
requirements-completed: []
requirements-pending: [RIGHTS-01]
commits: 2
plan_head_before: 2740d68123ede8a85b3ee63e59d2f7b1a8cbeacc
plan_head_after: f2296ebc8dd2b33791fbda4608860819fd07448d
status: complete
coverage:
  - id: BOUNDED-INPUT
    description: Direct manifest and repository walks reject excess directory entries, while Git output byte and record overflows are rejected during streaming with child cleanup.
    human_judgment: false
    verification:
      - kind: integration
        ref: "python3 -I tests/scripts/verify-fixture-admission.py --self-test"
        status: pass
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^fixture_(admission|product_).*'"
        status: pass
  - id: BOUNDED-DOCS
    description: Documentation states all enforced filesystem, Git stdout, Git record, manifest-file, and retained-stderr limits and rejection tokens.
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^fixture_(admission|product_).*'"
        status: pass
---

# Phase GB-20 Plan 04: Fixture Admission Resource Bounds Summary

**Fixture admission now bounds directory walks and streams Git tree output under fixed entry and byte limits.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-10-31T21:41:05-04:00
- **Completed:** 2026-10-31T21:48:15-04:00
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Counted every descendant directory and file, link, or special entry while scanning fixtures. Direct manifest validation now applies the same cap to its own fixture subtree.
- Replaced whole-output `git ls-tree` capture with concurrent readers that limit stdout to 32 MiB and 16,384 records, drain stderr while retaining at most 4 KiB, and terminate, reap, close, and join on errors or limit violations.
- Added four content-caused over-limit controls plus a portable fake-process lifecycle proof to the existing self-test and CTest path.
- Documented the 16,384 filesystem-entry cap, 16,384 Git-record cap, 32 MiB Git stdout cap, 4 KiB stderr retention, and stable rejection tokens. Kept `MAX_FILES` at 4,096 for manifest file lists.
- Preserved fixture bytes, manifests, notices, product policy, and admission decisions. No fixture was admitted and RIGHTS-01 remains pending.

## Task Commits

1. **Task 1: Add traversal-limit controls and record the expected red result** — `e46497b5`.
2. **Task 2: Bound filesystem and Git enumeration, document limits, and pass controls** — `f2296ebc`.

## TDD Evidence

- **RED:** `python3 -I tests/.tdd-fixture-admission-red.py`, exit code 1; target `test_over_limit_fixture_tree_is_rejected`. The expected behavior was for the admission self-test to return 0 after rejecting excess entries. It failed because the self-test emitted `REJECT self-test-fixture-entry-count-bypass`, proving direct `check_manifest()` accepted the added nested empty directories. `gsd_run check tdd-red-evidence` returned `RED_EVIDENCE_OK`; the recorded semantic assessment found the named assertion failed for the intended behavior, with setup completed and no unrelated failure.
- **GREEN:** `python3 -I tests/scripts/verify-fixture-admission.py --self-test` passed with all positive and negative controls. The focused CTest group passed admission, repository, core product, and player product checks.
- **REFACTOR:** No separate refactor was needed.

## Deviations from Plan

None. The existing `fixture_admission_controls` CTest registration was reused; no CMake changes were needed.

## Self-Check: PASSED

- Summary and both owned implementation files exist.
- Both task commits are ancestors of the current HEAD.
- The measured plan range contains exactly two task commits.
- `verify-summary-coverage.py` accepted both coverage entries.
