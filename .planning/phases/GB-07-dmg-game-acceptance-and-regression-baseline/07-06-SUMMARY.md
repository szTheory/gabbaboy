---
phase: 07-dmg-game-acceptance-and-regression-baseline
plan: 06
subsystem: testing
tags: [runner, acceptance, case-file, negative-tests, boundary-matrix, ctest]

requires:
  - phase: 07-dmg-game-acceptance-and-regression-baseline
    provides: "Plan 07-05 case-file parser, path validator and --acceptance runner entry point"
provides:
  - "Seven acceptance_negative_* CTests: each D-28 runner-level negative exits exactly 2 with its own reason and no pass/fail/unsupported status line"
  - "test_acceptance_cases with acceptance_parse_cases_bounds, acceptance_parse_cases_errors, acceptance_parse_paths"
  - "GBB_FORBID_REGEX option in tests/expect_exit.cmake"
affects: [07-07 applicability, GB-07 baseline]

actuals:
  tokens: 14000
  tasks: 2
  commits: 2

plan_head_before: 0fac1f847598f3318038e2c1dfb8d36357662b65
plan_head_after: 1c73be9f061fea505b087321d72ee3b11cadd6c5

tech-stack:
  added: []
  patterns: ["negative CTests assert exact exit code, reason regex, and absence of a status line (proves rejection before guest work)", "oversize input generated into the build tree at configure time rather than committed"]

key-files:
  created:
    - tests/acceptance/negative/flipped-digest.txt
    - tests/acceptance/negative/bad-script.txt
    - tests/acceptance/negative/bad-script.input
    - tests/acceptance/negative/duplicate-id.txt
    - tests/acceptance/negative/unknown-key.txt
    - tests/acceptance/negative/path-traversal.txt
    - tests/acceptance/negative/altered-input.txt
    - tests/test_acceptance_cases.c
  modified:
    - tests/acceptance/CMakeLists.txt
    - tests/expected-tests.txt
    - tests/expect_exit.cmake

key-decisions:
  - "Forbid pattern is status=(pass|fail|unsupported), not any status=, because invalid-input diagnostics legitimately print status=invalid"
  - "No src/runner change: the 07-05 parser and run ordering already satisfied every negative and boundary case"

requirements-completed: [EVID-01]

coverage:
  - id: D1
    description: "Every D-28 runner-level negative case file is rejected with exact exit 2 and its own reason before any guest instance exists"
    requirement: EVID-01
    verification:
      - kind: integration
        ref: "ctest --test-dir build -R '^acceptance_negative_' (7/7 pass)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Case-file parser and path validator boundary matrix pinned on both sides of 64 KiB, 1024 chars, 128 cases, 255-byte paths and every D-21 malformation"
    requirement: EVID-01
    verification:
      - kind: unit
        ref: "tests/test_acceptance_cases.c#acceptance_parse_cases_bounds,acceptance_parse_cases_errors,acceptance_parse_paths"
        status: pass
    human_judgment: false

duration: 25min
completed: 2026-10-10
status: complete
---

# Phase 7 Plan 06: Case-file rejection hardening Summary

**Seven exact-exit-2 negative case-file CTests (including a configure-generated 65537-byte file) plus a three-test boundary matrix pinning the case-file parser and relative-path validator.**

## Performance

- **Duration:** 25 min
- **Tasks:** 2
- **Files modified:** 11 (8 created, 3 modified)

## Accomplishments
- Negative files for flipped ROM digest, unknown script verb (line 3), duplicate id, unknown key, `../` path and altered input digest, plus a build-tree oversize file. Each runs `gabbaboy-runner --acceptance` from the repo root and must exit 2 with its own reason and no `status=pass|fail|unsupported` line.
- `expect_exit.cmake` gained `GBB_FORBID_REGEX`.
- Boundary matrix: 1024/1025-char lines (and CRLF), 128/129 cases (129th reported on line 129), 65536/65537 bytes (line 0), 255/256-byte paths, 8 MiB / 8 MiB+1 rom_size, every listed D-21 malformation with the exact `invalid-cases: <reason> line=<n>`, all-or-nothing (no cases retained), and the full path rule table.

## Task Commits

1. **Task 1: runner-level negatives (tracer)** - `a461edb` (test)
2. **Task 2: boundary matrix** - `1c73be9` (test)

## TDD Gate Compliance

Task 2 is `tdd="true"` but produced a single `test(07-06)` commit with no `feat` commit. RED was not obtainable: the 07-05 parser already satisfied every case, so the new tests passed on first run (unexpected-green investigation: the behaviour exists; the tests are new pins, not new behaviour). To confirm the tests are not vacuous, a mutation (`line_length > MAX` changed to `>=` in `src/runner/cases.c`) was applied; `acceptance_parse_cases_bounds` failed, and the mutation was reverted via `git checkout` before commit. No `feat`/`refactor` commits exist for this plan.

## Decisions Made
- Forbid regex limited to `status=(pass|fail|unsupported)` because input rejections print `status=invalid` by design.
- Left `src/runner/acceptance.c` and `cases.c` unchanged: all input validation already precedes `gbb_create`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] expect_exit.cmake lacked a forbidden-output check**
- **Found during:** Task 1
- **Issue:** The plan requires the tests to fail if output contains a status line; the helper only supported a positive regex.
- **Fix:** Added optional `GBB_FORBID_REGEX`.
- **Files modified:** tests/expect_exit.cmake
- **Verification:** 7/7 negatives pass; full suite green.
- **Committed in:** a461edb

**2. TDD RED not obtainable** - documented above under TDD Gate Compliance (behaviour pre-existed).

---

**Total deviations:** 1 auto-fixed (Rule 3), 1 TDD note
**Impact on plan:** No scope creep; `src/runner/*` untouched.

## Verification run
- `ctest --test-dir build -R '^acceptance_negative_'`: 7/7 passed.
- `ctest --test-dir build -R '^acceptance_(parse_cases_|parse_paths|negative_|libbet$)'`: 11/11 passed.
- `ctest --test-dir build --output-on-failure --no-tests=error`: 211/211 passed.
- `.github/scripts/verify-test-inventory.sh <junit> tests/expected-tests.txt --installed`: "Verified 211 executed CTest cases; none skipped." (The default `--core-only` mode differs only by local `installed_*` tests, unrelated to this plan.)
- `git check-attr eol` reports `lf` for path-traversal.txt and bad-script.input.

## Issues Encountered
None.

## Known Stubs
None.

## Next Phase Readiness
Case-file rejection surface is fixed by tests; Plan 07-07 can build applicability on the parser.

## Self-Check: PASSED
- Created files exist; commits a461edb and 1c73be9 are ancestors of HEAD.
