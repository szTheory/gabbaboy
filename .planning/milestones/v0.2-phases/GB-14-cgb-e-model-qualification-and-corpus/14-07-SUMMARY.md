---
phase: 14-cgb-e-model-qualification-and-corpus
plan: "07"
subsystem: testing
tags: [cgb-e, samesuite, apu, rgbds, corpus, ctest]
requires:
  - phase: 14-03
    provides:
      - timed CGB CH3 sample latching and guest-qualified APU transition contracts
  - phase: 14-05
    provides:
      - pinned external source closure, frozen CGB case membership, and rights/model evidence policy
  - phase: 14-06
    provides:
      - exact nine-case Mooneye CGB-CPU-E compatibility corpus and bound execution records
provides:
  - 70 pinned SameSuite APU ROM outputs with source, rights, digest, and reproduction evidence
  - 70 independent author pass expectations and bounded CGB-CPU-E observations
  - exact per-case CTest membership and eight fail-closed cohort controls
  - synchronized CGB corpus admission counts with six AGE image cases still pending execution
affects: [14-09, 14-11, 14-12, cgb-corpus]
actuals:
  tokens: 779865
  tasks: 3
  commits: 5
commits: 5
plan_head_before: e566a7fcd149ac7b6e801a61c0ed2ce15ca7044f
plan_head_after: cb54cc62c2985eaef63d4f6f2d820d21ddde1c09
tech-stack:
  added: []
  patterns:
    - One bounded full-corpus execution emits immutable per-case receipts; member CTests validate identity without rerunning ROMs
    - Author expectations remain independent from observed model dispositions and xfails bind to exact signatures
    - Manifest paths resolve relative to suite roots, including nested fixture directories
key-files:
  created:
    - tests/scripts/verify-cgb-apu-dispositions.py
    - tests/test_samesuite_apu_membership.py
  modified:
    - fixtures/samesuite/manifest.json
    - fixtures/samesuite/ELIGIBILITY.md
    - tests/external/cgb-apu-dispositions.json
    - tests/external/cgb-corpus-inventory.json
    - tests/scripts/reproduce-samesuite.sh
    - tests/scripts/verify-cgb-corpus-inventory.py
    - tests/test_samesuite_apu.c
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - docs/cgb-corpus.md
key-decisions:
  - "Every pinned APU source stays selected, including revision-suffixed names and cases whose software-model observations disagree with the author expectation."
  - "The source expectation remains pass for all 70 cases; 62 evaluator xfails record model observations and never count as guest passes."
  - "A single bounded suite run owns ROM execution; exact member CTests and sensitivity controls inspect the frozen receipts without adding another execution lane."
  - "The six AGE image outputs are admitted from pinned ROM, source, and PNG evidence while their image cases remain admitted-not-executed for Plan 14-09."
  - "Software-model evidence makes no physical CGB-E hardware claim."
requirements-completed: []
coverage:
  - id: D1
    description: All 70 pinned APU ROM outputs are admitted with source and output digests, rights records, and byte-identical reproduction.
    requirement: CGB-10
    human_judgment: false
    verification:
      - kind: integration
        ref: "bash tests/scripts/reproduce-samesuite.sh --self-check && bash tests/scripts/reproduce-samesuite.sh --self-test && GBB_RGBDS_ARCHIVE=/tmp/gabbaboy-rgbds-v1.0.1.zip bash tests/scripts/reproduce-samesuite.sh --compare-pinned"
        status: pass
  - id: D2
    description: The bounded CGB-CPU-E run records all 70 terminal case outcomes and 4,784 result assertions while preserving pass as each author's expectation.
    requirement: CGB-08
    human_judgment: false
    verification:
      - kind: e2e
        ref: "build/tests/test_samesuite_apu --suite fixtures/samesuite/manifest.json --dispositions tests/external/cgb-apu-dispositions.json"
        status: pass
  - id: D3
    description: Exact per-case membership, tracer contracts, and eight named negative controls reject cohort omissions, result-selected filtering, altered expectations, changed receipts, and unexpected passes.
    requirement: CGB-08
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build --output-on-failure --parallel 2 --no-tests=error -R '^(cgb_samesuite_apu_(membership|controls|tracer|tracer_controls|channel_.*|div_.*)|cgb_corpus_inventory_(selection|selftest)|cgb_external_dispositions.*|cgb_speed_dispositions.*)$'"
        status: pass
  - id: D4
    description: The frozen inventory reports 109 admitted outputs, no pending output bytes, and 107 required cases while retaining six admitted AGE image cases as not executed.
    requirement: CGB-10
    human_judgment: false
    verification:
      - kind: unit
        ref: "python3 -I tests/scripts/verify-cgb-corpus-inventory.py --selection-only && python3 -I tests/scripts/verify-cgb-corpus-inventory.py --self-test"
        status: pass
duration: 36min
completed: 2026-10-15
status: complete
---

# Phase 14 Plan 07: CGB-E Model Qualification and Corpus Summary

**All 70 pinned SameSuite APU outputs are admitted and receipt-bound, with source pass expectations kept separate from eight model passes and 62 exact xfails.**

## Performance

- **Duration:** 36 minutes
- **Started:** 2026-10-15T20:35:45Z
- **Completed:** 2026-10-15T21:11:36Z
- **Tasks:** 3
- **Files modified:** 90

## Accomplishments

- Admitted all 70 pinned APU ROMs with exact source paths, source and output digests, G7 rights records, RGBDS 1.0.1 provenance, and byte-identical pinned reproduction. All 70 source expectations remain pass, including `channel_4_freq_change` and `channel_1_sweep_restart_2`.
- Executed the frozen cohort once on the bounded CGB-CPU-E native, normal-speed software model. The terminal receipts record 8 observed guest passes, 62 exact expected failures, and 4,784 result assertions, with per-case mismatch masks and observation signatures. Xfails are not counted as guest passes.
- Registered all 70 exact case CTests plus membership and controls. The eight negative controls reject omitted and suffix-filtered sources, a bogus green exit, altered author expectations, changed signatures, an unexpected pass, an all-xfail cohort, and an empty required cohort.
- Synchronized the shared inventory and documentation to 109 admitted output records, zero pending output bytes, and 107 fixed cases. AGE's 13 row cases remain distinct from six admitted image outputs whose image cases are pending execution.

## Task Commits

1. **Task 1: Tracer RED control** — `ef3b0c7` (`test(14-07)`).
2. **Task 1: Admit and execute the first APU tracer** — `b46bfc9` (`feat(14-07)`).
3. **Task 2: Admit and qualify all 70 SameSuite APU cases** — `85f72fa` (`feat(14-07)`).
4. **Task 3: Membership RED test and evidence** — `ddad93a` (`test(14-07)`).
5. **Task 3: Enforce exact membership and cohort controls** — `048723c` (`feat(14-07)`).

## Files Created/Modified

- `fixtures/samesuite/manifest.json`, `fixtures/samesuite/ELIGIBILITY.md`, and `tests/scripts/reproduce-samesuite.sh` — 70 pinned output admissions, source expectations, rights, and deterministic reproduction.
- `tests/external/cgb-apu-dispositions.json` and `tests/external/cgb-corpus-inventory.json` — independent author expectations, exact model receipts, assertion rows, signatures, and synchronized corpus counts.
- `tests/test_samesuite_apu.c`, `tests/scripts/verify-cgb-apu-dispositions.py`, and `tests/test_samesuite_apu_membership.py` — bounded execution, receipt validation, membership checks, and negative controls.
- `tests/CMakeLists.txt`, `tests/expected-tests.txt`, and `tests/scripts/verify-cgb-corpus-inventory.py` — exact case registrations, expected inventory, path and digest validation, and complete-mode pending-case rejection.
- `docs/cgb-corpus.md` — current admitted, executed, and pending-image totals and model limitations.

## Decisions Made

The 70-case roster stays frozen from the pinned source tree. Revision suffixes and current emulator outcomes do not select membership. The source's CGB-E pass claim remains author evidence; each local model observation stays separately qualified by its receipt and signature. This plan does not claim physical CGB-E hardware behavior. AGE's six image cases retain the upstream author expectation and admitted bytes while remaining unexecuted until their planned image comparison.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Resolve admitted fixture paths relative to their pinned suite manifest.**
- **Found during:** Task 3
- **Issue:** The corpus verifier reduced fixture paths to basenames, so nested SameSuite APU paths could not match the manifest. The admitted APU output rows also lacked the manifest's `size_bytes` field.
- **Fix:** Resolve output paths relative to each suite's manifest root and record each admitted APU output size from the pinned manifest.
- **Files modified:** `tests/scripts/verify-cgb-corpus-inventory.py`, `tests/external/cgb-corpus-inventory.json`
- **Verification:** Inventory selection and self-tests passed; the focused 83-test CTest selection passed.
- **Committed in:** `048723c`

**2. [Rule 2 - Missing Critical Functionality] Reflect the existing AGE admissions in the shared output inventory.**
- **Found during:** Task 3 integration
- **Issue:** The six AGE mode-3 ROMs already had pinned ROM, ASM source, PNG, rights, and reproduction evidence in Plan 14-08, but the shared inventory still listed their output bytes as unadmitted.
- **Fix:** Record the manifest-relative paths, digests, sizes, and admission status for those six ROM outputs while leaving the six image cases not executed. Keep the AGE row-oracle set at 13 and the overall case set at 107.
- **Files modified:** `tests/external/cgb-corpus-inventory.json`, `tests/scripts/verify-cgb-corpus-inventory.py`, `docs/cgb-corpus.md`
- **Verification:** Inventory selection/self-tests and AGE external/speed disposition controls passed in the focused CTest selection.
- **Committed in:** `048723c`

**Total deviations:** 2 auto-fixed (Rule 1: 1; Rule 2: 1)
**Impact on plan:** Both corrections were required for manifest-backed inventory correctness; the fixed 107-case selection and APU execution receipts remain unchanged.

## Issues Encountered

The first negative-control run found two expected-diagnostic mismatches and an author-expectation mutation that did not touch a field checked by the validator. The controls were corrected to mutate the validated author result and to assert the validator's exact source-path diagnostics; all eight now pass with a clean twin.

## User Setup Required

None - no external service configuration is required.

## Next Phase Readiness

The APU cohort is ready for Plan 14-11 receipt aggregation. The six admitted AGE image cases remain ready for their planned image execution in Plan 14-09. Phase-level requirement traceability and full-wave integration remain with the phase orchestrator.

---
*Phase: 14-cgb-e-model-qualification-and-corpus*
*Completed: 2026-10-15*

## Self-Check: PASSED

The summary exists, all five task commits are ancestors of the recorded plan head, the commit window measures five commits, and the `summary_coverage` and `summary_coverage_selftest` CTests passed.

## Sanitized ancestry

The top-level commit windows use sanitized unpublished ancestry. Historical execution revision IDs and task IDs above remain as originally recorded; [14-HISTORY-REDACTION.md](14-HISTORY-REDACTION.md) maps them to the equivalent sanitized commits. Fresh final qualification is recorded separately after this rewrite.
