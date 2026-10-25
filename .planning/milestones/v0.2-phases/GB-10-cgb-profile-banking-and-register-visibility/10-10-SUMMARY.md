---
phase: 10-cgb-profile-banking-and-register-visibility
plan: 10
subsystem: tests-docs
tags: [cgb, io-registers, visibility-matrix, doc-contract]
requires: [10-09]
provides: [per-cell visibility matrix, published io_visibility doc mirror, two-way code-vs-doc check]
affects: [10-11]
key-files:
  created: []
  modified: [tests/test_cgb_visibility.c, tests/test_cgb_tables.c, docs/cgb-profile.md, tests/CMakeLists.txt, tests/expected-tests.txt]
requirements-completed: []
status: complete
commits: 3
plan_head_before: 054e5a18301d851eb158d7fd26f8ed2e73fe367c
plan_head_after: 48dc25ea4c4d34344d297965dec12a8329b1e92f
actuals:
  tokens: 28000
  tasks: 3
  commits: 3
duration: 35 min
completed: 2026-10-12
coverage:
  - id: "10-10-compat-matrix"
    description: "Compatibility register matrix runs through the public API with a flip control"
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build/phase15_1_18 -R '^(cgb_visibility_matrix_compat|cgb_visibility_flip_control)$' --output-on-failure --no-tests=error"
        status: pass
  - id: "10-10-cgb-dmg-matrices"
    description: "CGB and DMG visibility matrices preserve profile-specific behavior"
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build/phase15_1_18 -R '^(cgb_visibility_matrix_cgb|cgb_visibility_matrix_dmg)$' --output-on-failure --no-tests=error"
        status: pass
  - id: "10-10-matrix-negative-controls"
    description: "Cross-column and address-sweep controls reject mismatched visibility rows"
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build/phase15_1_18 -R '^(cgb_visibility_cross_column_control|cgb_visibility_sweep_control)$' --output-on-failure --no-tests=error"
        status: pass
  - id: "10-10-published-matrix"
    description: "Published register matrix matches the implementation and rejects a mutated document"
    human_judgment: false
    verification:
      - kind: unit
        ref: "ctest --test-dir build/phase15_1_18 -R '^(cgb_tables_io|cgb_tables_io_mutated_doc|cgb_tables_postboot_selftest)$' --output-on-failure --no-tests=error"
        status: pass
---

# Phase 10 Plan 10: Register visibility matrix Summary

Every non-pre-CGB cell of FF00-FF7F (71 addresses x DMG, CGB and compat = 213 cells) is now run through the public API from an independent D-10 table, with flip, cross-column and sweep controls, and the same matrix is published in `docs/cgb-profile.md` and diffed against `io_visibility[]` in both directions.

## Accomplishments

- `run_cell` runs `read0, w1, read1, w2, read2` as up to three guest programs (one per read, so a stopping read cannot hide later ones). It asserts bytes via HRAM, atomic read stops via `reject_atomically` plus the `gbb_test_last_unsupported_address` seam, write stops after retire with the seam address, and (outside CGB mode) that neither bank moved.
- The expected values were written from the D-10 table (not from `io_visibility[]`) and passed on the first run in all three columns; no expectation was adjusted to match code.
- Controls: `flip_control` (flipped read byte, a read expected to stop, a write expected to stop: all detected); `cross_column_control` (each expectation that differs between two columns must fail in the other column, all six ordered pairs non-empty); `sweep_control` (deleting any one row, duplicating a row or hiding an existing-address range is reported at the right address; FF4C-FF7F has all three columns).
- `docs/cgb-profile.md`: `cgb-io-visibility` marker block (213 rows: address, column, read, write, status, src), deferred-access asymmetry, IE bits 5-7, FEA0-FEFF fail-closed, D-09 DMG statement.
- `test_cgb_tables`: case `io` (two-way diff, hole detection, EXISTING rows must have no doc row, `emit_io` for the maintainer) and three io mutants (code row removed, zeroed hole, doc row dropped) in the postboot self-test (now `mutants=6`). A configure-time mutated doc (compat FF4F read changed to `$FF`) must fail.

## Verification

- Full suite: 477/477 pass. `verify-dmg-baseline.sh`: `baseline status=pass`, rows=0 changes.
- Targeted `^(cgb_visibility_|cgb_tables_|bus_)` green.

## Deviations from Plan

**1. [Rule 1 - Test harness bug] Refused read could pass for a write stop.** The first cross-column run showed DMG passing a DEF_RW expectation: after a "write stop" the harness re-ran, and a read stuck on the same atomic stop satisfied the next expected stop. Fixed in the harness (a write stop must have consumed time, a refused read consumes none); the code under test was unchanged. The control then passed for the right reason.

**2. Scope: doc rows omit pre-CGB (EXISTING) addresses.** The plan said "one row per address and column"; the 57 addresses owned by pre-CGB code behave identically on every profile, so the block lists only the 71 non-existing addresses (213 rows) and `cgb_tables_io` requires that EXISTING addresses have no doc row. The test sweep carries the same existing ranges.

**3. Sweep against io_visibility[] is by doc, not direct.** `test_cgb_visibility` links the public core and cannot see the static table, so the sweep over `io_visibility[]` is done in `test_cgb_tables` (every cell classified, no zero hole) and the test-table sweep in `test_cgb_visibility`; the doc ties them together.

## Known Stubs

None. DEFERRED cells are intentional and owned by phases 11, 13 and 14.

## Threat Flags

None. T-10-31 mitigated (two-way diff, mutated-doc control, independent oracle, flip/cross/sweep controls).

## Notes

CGB-02 is not marked complete in REQUIREMENTS.md: plans 10-11, 10-14, 10-15, 10-16, 10-18, 10-19 and 10-20 still declare it.

## Self-Check: PASSED

- tests/test_cgb_visibility.c, tests/test_cgb_tables.c, docs/cgb-profile.md exist; commits 266a33e, c9f3de3, 48dc25e are ancestors of HEAD; all eight new CTest names are in tests/expected-tests.txt.

## Fresh Coverage Verification (15.1-18)

At source `65e69ca2dc6f51515ebba002361b0966e3b45a17`, the plan-specific Debug build `build/phase15_1_18` freshly passed all nine mapped CTests: the three visibility matrices and their controls, the published matrix comparison, mutated-document rejection, and post-boot provenance self-test. No live Phase 10 producer claim was rewritten.
