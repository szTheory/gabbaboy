---
phase: 10-cgb-profile-banking-and-register-visibility
plan: 07
subsystem: docs-and-tests
tags: [cgb, post-boot, provenance, doc-drift]
requires: [10-06]
provides: [docs/cgb-profile.md post-boot mirror, test_cgb_tables]
affects: [10-10]
key-files:
  created: [docs/cgb-profile.md, tests/test_cgb_tables.c]
  modified: [tests/CMakeLists.txt, tests/expected-tests.txt]
requirements-completed: [CGB-01]
status: complete
commits: 1
plan_head_before: 6d982feb4aa5797ff7704d0b9bc16fa119ce4edf
plan_head_after: 623d7f9e60bd63667b7edcbe2c594caeca88468e
actuals:
  tokens: 14000
  tasks: 2
  commits: 1
duration: 12 min
completed: 2026-10-12
coverage:
  - id: "10-07-postboot-mirror"
    description: "Published post-boot table mirrors the implementation"
    human_judgment: false
    verification:
      - kind: unit
        ref: "ctest --test-dir build/phase15_1_18 -R '^cgb_tables_postboot$' --output-on-failure --no-tests=error"
        status: pass
  - id: "10-07-mutated-document"
    description: "A changed post-boot document value is rejected"
    human_judgment: false
    verification:
      - kind: unit
        ref: "ctest --test-dir build/phase15_1_18 -R '^cgb_tables_postboot_mutated_doc$' --output-on-failure --no-tests=error"
        status: pass
  - id: "10-07-provenance-mutants"
    description: "Post-boot provenance rules reject mutated table copies"
    human_judgment: false
    verification:
      - kind: unit
        ref: "ctest --test-dir build/phase15_1_18 -R '^cgb_tables_postboot_selftest$' --output-on-failure --no-tests=error"
        status: pass
---

# Phase 10 Plan 07: Post-boot doc mirror and provenance check Summary

`docs/cgb-profile.md` now mirrors all 43 post_boot[] fields across DMG, CGB and COMPAT (129 rows, numbered source list), and `test_cgb_tables` fails on any code/doc difference, an empty POLICY reason, or HW_TEST outside the COMPAT column.

## Accomplishments

- Doc: evidence-class table, marker-delimited pipe table, eight numbered sources (Pan Docs, D-025, header, Mooneye boot_regs-cgb / boot_hwio-C / boot_div-cgbABCDE at 31510e12, SameBoy memory.c at c71f110e, phase-10 policy). The DIV cells say CGB A-E; SameBoy and Pan Docs are stated not to be hardware evidence.
- `test_cgb_tables` (white-box, includes the core): two-way diff keyed on field and column (missing, duplicate, extra rows and any value/prov/src/reason difference), plus the two provenance rules. An `emit` mode prints rows in the doc format for refreshing the mirror.
- Negative controls: configure-time mutated doc copy (compat A `$11` to `$12`, anchor must occur exactly once or configure fails) exits 1 with `cgb-tables mismatch`; selftest runs three in-memory mutants (DMG value changed, POLICY reason cleared, CGB cell relabelled HW_TEST), each required to return its specific result code, plus an unmutated pass.

## Test results

`ctest -R ^cgb_tables_`: 3/3. Full suite: 458/458. `verify-dmg-baseline.sh`: pass.

## Deviations from Plan

- Tasks 1 and 2 landed in one commit (623d7f9): the comparator was written taking row arrays from the start, so the selftest was inseparable from the tracer code without deliberately writing throwaway code.
- Header-derived cell (F, DMG) is written as its base value `$80` with the rule in the reason, rather than as a rule name, because the comparator checks numeric values for every cell. Minor; the doc states this convention.
- Rows in the doc were generated from the code by the test's `emit` mode; the independent check is the test's diff, and the provenance text was reviewed against the plan's source list.

**Total deviations:** 3 minor, no behavioural impact.

## Known Stubs

None.

## Self-Check: PASSED

docs/cgb-profile.md, tests/test_cgb_tables.c present; commit 623d7f9 is an ancestor of HEAD.

## Fresh Coverage Verification (15.1-18)

At source `65e69ca2dc6f51515ebba002361b0966e3b45a17`, the plan-specific Debug build `build/phase15_1_18` freshly passed the post-boot mirror comparison, mutated-document rejection, and all 14 provenance self-test mutants. This current run supplements the original Phase 10 evidence and does not change its producer claims.
