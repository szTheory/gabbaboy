---
phase: 14-cgb-e-model-qualification-and-corpus
plan: "06"
subsystem: testing
tags: [cgb, mooneye, corpus, ctest, qualification]
requires:
  - phase: "14-02"
    provides: Exact Mooneye failure-signature dispositions for the HWIO cases.
  - phase: "14-05"
    provides: Frozen nine-case Mooneye source and output membership.
  - phase: "14-04"
    provides: CGB model behavior used to qualify the selected guest results.
provides:
  - Five reproducible Mooneye CGB ROM outputs admitted with pinned source, builder, rights, and byte identity.
  - Exact nine-case CGB-CPU-E compatibility-mode execution records, including three signature-bound software xfails.
  - CTest bindings and negative controls for the complete nine-case corpus.
affects: [CGB corpus follow-up, Phase 14 verification, CGB model qualification]
actuals:
  tokens: 72038
  tasks: 3
  commits: 4
commits: 4
plan_head_before: 74bad9a53867584190e7be66c32d6c387b9f03b3
plan_head_after: 4c927c4bf87dbabc41042c6757340d4e04f757ea
tech-stack:
  added: []
  patterns:
    - Source expectations remain distinct from exact software-model failure dispositions.
    - The selected case set, raw manifest digest, CTest names, and callback/result signatures are independently bound.
key-files:
  created:
    - fixtures/mooneye-cgb/daa.gb
    - fixtures/mooneye-cgb/div_write.gb
    - fixtures/mooneye-cgb/tim00.gb
    - fixtures/mooneye-cgb/tim00_div_trigger.gb
    - fixtures/mooneye-cgb/vblank_stat_intr-C.gb
  modified:
    - fixtures/mooneye-cgb/manifest.json
    - fixtures/mooneye-cgb/SOURCES.md
    - fixtures/mooneye-cgb/ELIGIBILITY.md
    - src/runner/main.c
    - cmake/VerifyMooneyeCgb.cmake
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - tests/test_runner.c
    - tests/scripts/reproduce-mooneye-cgb.sh
    - tests/scripts/verify-cgb-corpus-inventory.py
    - tests/external/cgb-corpus-inventory.json
    - docs/cgb-corpus.md
    - docs/model-gates.md
    - docs/support/unreleased.md
key-decisions:
  - Keep all nine upstream author expectations at pass; report only the three pinned current guest failures as xfail.
  - Keep the frozen nine-case denominator and require complete case identities, nonempty assertion records, and exact CTest bindings.
  - Promote the VBlank xfail only after the same pinned guest passes and wrong-callback/signature controls continue to fail.
patterns-established:
  - Expected-failure dispositions succeed only for the compiled callback, result PC, and failure-register signature.
  - Corpus selection and terminal execution are verified separately from broader Phase 14 inventory completion.
requirements-completed: []
coverage:
  - id: D1
    description: The five added Mooneye CGB outputs reproduce byte-identically from the pinned source and toolchain recipe, and all nine selected guests execute to a terminal protocol result.
    human_judgment: false
    verification:
      - kind: e2e
        ref: "bash tests/scripts/reproduce-mooneye-cgb.sh --compare fixtures/mooneye-cgb"
        status: pass
      - kind: integration
        ref: "ctest --test-dir build -j2 -R '^(cgb_corpus_mooneye_boot_regs_cgb|cgb_corpus_mooneye_boot_div_cgbABCDE|cgb_corpus_mooneye_boot_hwio_C|cgb_corpus_mooneye_unused_hwio_C|cgb_corpus_mooneye_daa|cgb_corpus_mooneye_div_write|cgb_corpus_mooneye_tim00|cgb_corpus_mooneye_tim00_div_trigger|cgb_corpus_mooneye_vblank_stat_intr_C)$' --output-on-failure --no-tests=error"
        status: pass
  - id: D2
    description: The exact Mooneye identities, model, compatibility mode, header byte, ROM hashes, manifest digest, assertion signatures, and CTest bindings are checked independently.
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build -j2 -R '^(cgb_mooneye_fixture_digest|cgb_mooneye_inventory|cgb_mooneye_digest_tamper|cgb_mooneye_inventory_tamper|cgb_mooneye_pc_table|cgb_mooneye_pc_table_tamper|cgb_corpus_inventory_selection|cgb_corpus_inventory_selftest)$' --output-on-failure --no-tests=error"
        status: pass
      - kind: other
        ref: "ctest --test-dir build --show-only=json-v1 plus the required-name check: missing-required-tests: []"
        status: pass
  - id: D3
    description: Six guests count as passes and three author-pass guests remain exact xfails; missing bytes, wrong model or mode, altered callback/register signatures, and false xfail promotion are rejected.
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build -j2 -R '^(cgb_corpus_mooneye_controls|cgb_mooneye_required_suite)$' --output-on-failure --no-tests=error"
        status: pass
      - kind: other
        ref: "Runner receipt: eligible=9 executed=9; guest pass=6; exact xfail=3; expected-failure=3/3; nine assertion rows, one per case."
        status: pass
duration: 16min
completed: 2026-10-15
status: complete
---

# Phase 14 Plan 06: CGB-E Mooneye Model Qualification Summary

**Five pinned Mooneye outputs now complete the nine-case CGB-CPU-E compatibility corpus, with six guest passes and three exact software-model xfails kept separate from the author pass assertions.**

## Performance

- **Duration:** 16 minutes, measured from the earliest task commit because the original plan-start timestamp was not retained in this continuation.
- **Started:** 2026-10-15T20:07:29Z (earliest task commit)
- **Completed:** 2026-10-15T20:23:02Z
- **Tasks:** 3
- **Files modified:** 19, including five new ROM outputs.

The actual token estimate uses 124,312 characters from the text diff plus 163,840 bytes from the five new ROMs, divided by four. The measured plan ledger spans four task commits from `plan_head_before` through `plan_head_after`.

## Accomplishments

- Added the DAA, DIV-write, TIM00, TIM00-DIV-trigger, and VBlank ROM derivatives with their original and derivative hashes, pinned rights and builder ancestry, source symbols, and finite execution budgets.
- Executed all nine selected Mooneye guests on the CGB-CPU-E software profile in compatibility mode. Six guests pass; `boot_hwio-C`, `unused_hwio-C`, and `vblank_stat_intr-C` produce exact signature-bound xfails and remain excluded from the pass count.
- Bound the nine cases to exact CTest names and strengthened manifest, model, mode, header, source, assertion, and inventory checks. The external inventory now records 33 admitted outputs and 76 pending outputs across the larger 107-case corpus.

## Task Commits

1. **Task 1: Tracer: admit and execute the pinned DAA guest** — `401b6e0` (`feat`)
2. **Task 2: Expand the remaining four additions with explicit dispositions** — `fb1b4d4` (`feat`)
3. **Task 3 RED: Bind exact nine-case execution and controls to CTest** — `52cd2ec` (`test`)
4. **Task 3 GREEN: Bind exact nine-case execution and controls to CTest** — `b022402` (`feat`)

The summary is committed separately after its self-check.

## Files Created/Modified

- `fixtures/mooneye-cgb/{daa,div_write,tim00,tim00_div_trigger,vblank_stat_intr-C}.gb` — pinned reproducible test outputs.
- `fixtures/mooneye-cgb/manifest.json`, `SOURCES.md`, and `ELIGIBILITY.md` — nine-case membership, source/build lineage, exact assertions, rights, and execution dispositions.
- `src/runner/main.c` — trusted nine-case table, manifest digest, CGB category totals, and resumable halted-idle handling.
- `cmake/VerifyMooneyeCgb.cmake`, `tests/CMakeLists.txt`, and `tests/expected-tests.txt` — nine-row digest, metadata, table, registration, and mutation checks.
- `tests/test_runner.c` — exact expected-failure controls for the third VBlank xfail, including changed callback and register signatures.
- `tests/scripts/reproduce-mooneye-cgb.sh` — pinned finite output roster and reproduction data.
- `tests/scripts/verify-cgb-corpus-inventory.py` and `tests/external/cgb-corpus-inventory.json` — admitted output records, terminal per-case receipts, assertion rows, and exact test bindings.
- `docs/cgb-corpus.md`, `docs/model-gates.md`, and `docs/support/unreleased.md` — current admission counts, software xfail boundaries, and accurate status claims.

## Decisions Made

- The upstream author expectation remains `pass` for every selected case. Current software-model observations are stored separately and only the three exact guest failures qualify as xfails.
- The nine selected Mooneye identities remain fixed even though other Phase 14 suites are still pending.
- The VBlank discrepancy belongs to the CGB PPU/interrupt model. Promotion requires this same pinned guest to pass while the wrong-callback and wrong-register controls continue to fail.

## TDD Evidence

- **RED:** The newly registered `cgb_corpus_mooneye_controls` target ran the old verifier against the nine-row manifest and failed its intended admission assertion: the verifier required exactly four fixtures but found nine. The target executed and failed on the stale case-count contract, not during discovery or setup. The unchanged JUnit report and project-local evidence record were accepted by the explicit OpenGSD 1.16.0 classifier as `RED_EVIDENCE_OK`; semantic inspection confirmed the expected target assertion. Commit: `52cd2ec`.
- **GREEN:** The verifier now requires the exact nine identities and metadata. Nine exact runner CTests, inventory selection and self-tests, and a controls mode for missing bytes, wrong model/mode, tampered xfail disposition, changed callback, and changed failure registers all pass. Commit: `b022402`.
- **REFACTOR:** No separate refactor was needed; the verifier and control flow remain small and task-local.

## Verification

- `cmake --preset phase1` and `cmake --build --preset phase1` passed.
- The focused CGB Mooneye and corpus set passed **23/23**, including all nine exact CTest bindings, missing-ROM, wrong-model, wrong-mode, digest, duplicate-ID, PC-table, and exact-failure controls.
- The required test-name inventory check reported `missing-required-tests: []`.
- `verify-cgb-corpus-inventory.py --selection-only` reported **181 source candidates, 109 outputs, 33 admitted, 76 pending, and 107 required cases**. Its self-test passed all named controls, including altered model/mode, callback, and xfail-as-pass mutations.
- Model-gate and CGB table checks passed **19/19**.
- The direct runner receipt reported **9 eligible, 9 executed, 6 guest passes, 3 exact xfails, and 3/3 expected failures**. It recorded one nonempty `ld-b-b-result` assertion row for each of the nine Mooneye cases. Other corpus assertion totals remain pending.
- The plan’s exact CGB fixture reproduction and reproducer guard checks passed during Task 2. The full Phase 14 suite is parent-owned and will be run by the orchestrator after this plan; this summary does not claim a full-suite pass.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Keep resumable halted-idle execution eligible**

- **Found during:** Task 2.
- **Issue:** The runner classified `GBB_STOP_HALTED_IDLE` as an unsupported terminal stop, so a guest that continued after an eligible idle interval could not reach its later assertion.
- **Fix:** Removed halted-idle from the unsupported-stop classification, matching the public run-result contract and allowing the VBlank guest to continue to its exact assertion result.
- **Files modified:** `src/runner/main.c`.
- **Verification:** The nine-case suite reached all terminal callbacks; `vblank_stat_intr-C` now reports its exact xfail signature instead of an early stop.
- **Committed in:** `fb1b4d4`.

**2. [Rule 2 - Missing Critical Test] Add negative controls for the VBlank xfail signature**

- **Found during:** Task 3.
- **Issue:** The plan’s new VBlank expected-failure row needed controls proving that an altered callback or failure-register tuple could not be accepted as the declared xfail.
- **Fix:** Extended the existing test-runner disposition control with the VBlank raw failure, exact xfail, wrong-callback, and changed-register cases; bound these through the aggregate controls CTest.
- **Files modified:** `tests/test_runner.c`, `tests/CMakeLists.txt`, `cmake/VerifyMooneyeCgb.cmake`.
- **Verification:** `cgb_corpus_mooneye_controls` passed with named wrong-callback and wrong-register rejection diagnostics.
- **Committed in:** `b022402`.

**3. [Rule 2 - Missing Critical Documentation] Refresh current corpus and gate status**

- **Found during:** Task 3.
- **Issue:** The corpus and support notes still described 28 admitted outputs, 81 pending outputs, four Mooneye cases, and an unqualified status for the newly completed cases. GATE-21 also presented the `unused_hwio-C` observation without the new exact xfail boundary.
- **Fix:** Updated the current 33/76 global output counts, nine-case Mooneye outcomes, and GATE-21 evidence description while preserving broader pending corpus counts.
- **Files modified:** `docs/cgb-corpus.md`, `docs/model-gates.md`, `docs/support/unreleased.md`.
- **Verification:** Corpus inventory selection and self-test passed; model-gate and CGB table checks passed 19/19.
- **Committed in:** `b022402`.

**Total deviations:** 3 Rule 1/Rule 2 corrections. All were required for the planned guest execution, negative-control coverage, or truthful evidence documentation.

## Issues Encountered

- The first controls run revealed the runner’s actual missing-ROM diagnostic is `reason=missing-fixture`, not `missing-file`; the verifier and test predicate were corrected to assert the real diagnostic.
- The changed-mode inventory self-test is rejected earlier by the frozen case fingerprint than the field-level mode check; the self-test now expects that exact fail-closed diagnostic.
- The normal commit initially could not create `.git/index.lock` under the read-only Git metadata sandbox. The already-authorized commit succeeded after automatic sandbox review granted the required write access; hooks ran normally.

## User Setup Required

None. Reproduction is an explicit script invocation; required CTests consume only the checked-in, digest-pinned ROM outputs.

## Next Phase Readiness

Plan 14-06 is complete. Phase-level verification, STATE.md and continuation routing remain with the orchestrator, which will pause at the end of Phase 14 per the project workflow contract.

---
*Phase: 14-cgb-e-model-qualification-and-corpus*
*Completed: 2026-10-15*

## Self-Check: PASSED

All five new fixture files and this summary exist. Task commits `401b6e0`, `fb1b4d4`, `52cd2ec`, and `b022402` are ancestors of HEAD.

## Sanitized ancestry

The top-level commit windows use sanitized unpublished ancestry. Historical execution revision IDs and task IDs above remain as originally recorded; [14-HISTORY-REDACTION.md](14-HISTORY-REDACTION.md) maps them to the equivalent sanitized commits. Fresh final qualification is recorded separately after this rewrite.
