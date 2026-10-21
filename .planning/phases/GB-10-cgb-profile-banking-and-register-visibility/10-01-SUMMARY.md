---
phase: 10-cgb-profile-banking-and-register-visibility
plan: 01
subsystem: testing
tags: [model-gates, cgb, dmg, scanner, ctest, python-stdlib]
requires: []
provides:
  - "tests/scripts/verify-model-gates.py: D-08 scanner (R1-R5, --release, --self-test)"
  - "docs/model-gates.md: gate table skeleton with machine-read markers and GATE-00 row"
  - "CTests model_gates_tracer_pass, model_gates_tracer_doc_mismatch, model_gates_selftest"
affects: [10-02]
tech-stack:
  added: []
  patterns: ["stdlib-only Python verifier run with -I, negative controls through expect_exit.cmake"]
key-files:
  created:
    - tests/scripts/verify-model-gates.py
    - docs/model-gates.md
  modified:
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
key-decisions:
  - "GATE-00 code tags are not compared against the doc resolution text (basis varies per function); only class BOTH and a basis= are enforced, plus the single doc row"
  - "Added tokens gate-unbalanced (unparseable source) and free prose after ' -- ' in a tag, beyond the plan's token list"
requirements-completed: [CGB-02]
duration: 25 min
completed: 2026-10-12
status: complete
commits: 1
plan_head_before: 5e2b32f16fa705043c5437fb63a08bd83a4d750b
plan_head_after: bdc623ee31131665375a74fdf9885be7a6d6df0f
actuals:
  tokens: 14000
  tasks: 2
  commits: 1
coverage:
  - id: D1
    description: "The D-08 scanner rejects malformed tags, declarations, and source with named findings."
    requirement: CGB-02
    verification:
      - kind: unit
        ref: "ctest --test-dir build/phase15_1_13 -R '^model_gates_selftest$' --output-on-failure"
        status: pass
    human_judgment: false
  - id: D2
    description: "Clean and mismatched-document scanner verdicts reach CTest through exact exit and diagnostic checks."
    requirement: CGB-02
    verification:
      - kind: integration
        ref: "ctest --test-dir build/phase15_1_13 -R '^(model_gates_tracer_pass|model_gates_tracer_doc_mismatch)$' --output-on-failure"
        status: pass
    human_judgment: false
---

# Phase 10 Plan 01: Model-gate scanner Summary

**Stdlib-only D-08 model-gate scanner with R1-R5, `--release`, and an 18-mutant self-test that cross-checks the real core's 126 functions against an independent brace counter.**

## Accomplishments

- `tests/scripts/verify-model-gates.py`: lexes C (comments, strings, char literals, preprocessor blanked, line numbers kept), finds top-level definitions including multi-line signatures and one-liners, and enforces R1-R5 with deterministic, source-line-ordered findings.
- `docs/model-gates.md`: tag grammar, five rules, GATE-00 policy and the marker-delimited table holding the single GATE-00 row.
- `--self-test`: 18 mutants (deleted tag, class/guard/resolution drift, UNKNOWN unresolved and under `--release`, guard 13 lines below with a 12-line positive boundary, missing GUARD, hazard under BOTH, doc order, empty block, missing marker, duplicate id, GATE-00 misuse, malformed id, unbalanced brace, untagged function appended to the real source). Scanner count on `src/core/gabbaboy.c` is 126, equal to the independent counter.
- CTest: `model_gates_tracer_pass`, `model_gates_tracer_doc_mismatch`, `model_gates_selftest`; inventory in `tests/expected-tests.txt` in sync.

## Deviations from Plan

**1. [Process] Both tasks in one commit.** The scanner was written with the self-test already in place, so Tasks 1 and 2 share files and landed as one commit (`bdc623e`) rather than two. Both tasks' acceptance criteria were checked separately and pass.

**2. [Rule 2 - Missing critical] Added `gate-unbalanced` token** for unterminated comments/literals and unbalanced braces, implementing the plan's prohibition that an unparseable file must fail rather than skip a function. Covered by a self-test mutant.

**Total deviations:** 2 (1 process, 1 Rule 2). **Impact:** none on scope.

## Verification

- `ctest -R '^model_gates'`: 3/3 pass. Full `ctest --preset phase1`: 414/414 pass.
- `git diff --quiet main -- src/core/gabbaboy.c tests/baseline` exits 0.

## Known Stubs

None.

## Threat Flags

None.

## Next

Ready for Plan 10-02 (tag the core against the scanner and fill the table).

## Self-Check: PASSED
