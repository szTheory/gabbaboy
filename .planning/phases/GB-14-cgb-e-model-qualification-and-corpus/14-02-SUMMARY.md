---
phase: 14-cgb-e-model-qualification-and-corpus
plan: "02"
subsystem: model-qualification
tags: [cgb, ff56, io-visibility, model-gates, guest-tests, reset-lifecycle]
requires:
  - phase: 14-01
    provides: Independent CGB PCM12/PCM34 visibility and table contracts
provides:
  - Native CGB FF56 disconnected-receiver read and write policy with reset-state provenance
  - Guest and lifecycle checks for FF56 across creation, reset, successful load, failed-load preservation, and independent instances
  - Independent FF72-FF75 visibility contracts while retaining the PCM table oracle
affects: [CGB-08 evidence, CGB register profile, model-gate review]
actuals:
  tokens: 8681
  tasks: 2
  commits: 4
commits: 4
plan_head_before: 6c5b7040a40a25ca1f21aae11f97a8268d05c80b
plan_head_after: 01e1797a4720926a7ef843935fabb562360a4913
tech-stack:
  added: []
  patterns:
    - Guest bus assertions keep CGB register expectations independent of the implementation table.
    - Private test seams expose lifecycle state without changing the public API.
    - Independent table oracles pair positive cells with named mask and decode mutants.
key-files:
  created: []
  modified:
    - src/core/gabbaboy.c
    - tests/test_cgb_visibility.c
    - tests/test_cgb_tables.c
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - docs/cgb-profile.md
    - docs/model-gates.md
key-decisions:
  - Native CGB FF56 stores bits 7-6 and 0; the disconnected receiver and reserved-bit policy produce (stored & $C1) | $3E.
  - Keep FF56 compatibility and DMG behavior unchanged, and record the initial latch as policy rather than a hardware power-up measurement.
  - Preserve FF72/73 compatibility storage, absent compatibility FF74, FF75 $70 storage, and the existing PCM12/PCM34 contract.
patterns-established:
  - Model-visible claims are checked through real guest reads and writes plus independent mode-column expectations.
  - Failed-load preservation can be tested through a private read-only seam without extending the published API.
requirements-completed: []
coverage:
  - id: D1
    description: Native CGB FF56 reads and writes follow the disconnected-receiver policy, with compatibility and DMG access unchanged.
    human_judgment: false
    verification:
      - kind: e2e
        ref: "ctest --test-dir build -R '^(cgb_ir_tracer|cgb_ir_controls|cgb_ir_modes)$' --output-on-failure --no-tests=error"
        status: pass
      - kind: other
        ref: "Negative guest predicates report mask expected=$3E actual=$1E and compatibility expected=$FF actual=$BE."
        status: pass
  - id: D2
    description: FF56 creation, successful-load, reset, failed-load preservation, and instance isolation are checked alongside FF72-FF75 mode cells and PCM12/PCM34.
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build -R '^(cgb_ir_controls|cgb_ir_modes|cgb_visibility_matrix_dmg|cgb_visibility_matrix_compat|cgb_visibility_matrix_cgb|cgb_visibility_cross_column_control)$' --output-on-failure --no-tests=error"
        status: pass
      - kind: integration
        ref: "ctest --test-dir build -R '^(cgb_tables_io|cgb_tables_io_mutated_doc|cgb_tables_postboot|cgb_tables_postboot_selftest)$' --output-on-failure --no-tests=error"
        status: pass
      - kind: other
        ref: "Negative controls report FF56 reset expected=$00 actual=$01, failed-load expected=$C1 actual=$00, and table mutants reject FF75 mask and compatibility FF74 decode changes; postboot self-test passes mutants=14."
        status: pass
  - id: D3
    description: Model-gate claims, exact Mooneye observations, and the frozen DMG baseline remain aligned with the implementation.
    human_judgment: false
    verification:
      - kind: integration
        ref: "Focused model-gate, CGB Mooneye disposition, CGB speed reset, and HDMA lifecycle selections pass 29/29 tests."
        status: pass
      - kind: other
        ref: "Mooneye boot_hwio-C and unused_hwio-C retain author_expect=pass, observed=fail, exact callback/result signatures, and status=xfail; the disposition controls pass."
        status: pass
      - kind: other
        ref: "bash tests/scripts/verify-dmg-baseline.sh reports inventory=313, Mooneye=15, acceptance=20, benchmark=2, changed rows=0, status=pass."
        status: pass
duration: 14m
completed: 2026-10-15
status: complete
---

# Phase 14 Plan 02: FF56 Lifecycle and Undocumented-Port Qualification Summary

**Native CGB FF56 now has explicit disconnected-receiver semantics and lifecycle evidence, while FF72-FF75 and the existing PCM ports have independent table checks.**

## Performance

- **Duration:** 14m, measured from the first persisted plan test run.
- **Started:** 2026-10-15T17:47:51Z
- **Completed:** 2026-10-15T18:02:12Z
- **Tasks:** 2
- **Files modified:** 7

The implementation diff is 34,723 characters, or 8,681 estimate-scale tokens (characters divided by four), excluding this summary. The measured task-commit ledger covers four commits from `plan_head_before` through `plan_head_after`; the summary metadata commit is separate.

## Accomplishments

- Native CGB FF56 stores LED and receiver-enable bits 7-6 and bit 0, then reads `(stored & $C1) | $3E`. Compatibility mode remains `$FF` with ignored writes; DMG retains its existing fail-closed behavior. No host, peer, network, or physical IR path was added.
- The post-boot table now records a zero FF56 latch for creation, reset, and successful ROM load, with policy provenance separated from the bus read mask. Guest tests also cover failed-load preservation and independent CGB instances.
- Independent table checks preserve compatibility storage at FF72/73, absent compatibility FF74, FF75 `$70` write masking and `$8F` read-high bits, and the existing PCM12/PCM34 policy. Named controls reject an FF75 mask change and a compatibility FF74 decode change.
- Updated the register profile and model-gate descriptions alongside code and tests. The claims remain software-model qualifications; no physical CGB-E observation is asserted.

## Task Commits

1. **Task 1 RED:** `8f30749` — FF56 guest-read and mode contracts.
2. **Task 1 GREEN:** `24f07c7` — disconnected FF56 implementation and profile claims.
3. **Task 2 RED:** `5b9a004` — explicit FF56 reset-table requirement.
4. **Task 2 GREEN:** `01e1797` — lifecycle, port contracts, table mutants, and model-gate updates.

The plan metadata commit records this summary separately.

## Files Created/Modified

- `src/core/gabbaboy.c` — per-instance FF56 post-boot state and a private read-only lifecycle test seam.
- `tests/test_cgb_visibility.c` — guest FF56 checks and lifecycle, reset, failed-load, and instance controls.
- `tests/test_cgb_tables.c` — FF56 post-boot presence requirement and independent FF72-FF75/PCM table contracts.
- `tests/CMakeLists.txt` — updated the table self-test mutant count.
- `tests/expected-tests.txt` — exact IR guest test inventory from Task 1.
- `docs/cgb-profile.md` — FF56 latch provenance and mode-specific behavior.
- `docs/model-gates.md` — FF56 read/write behavior within the CGB I/O gate descriptions.

## Decisions Made

- Treat the FF56 LED and receiver-enable meanings as source-backed register behavior, while labeling reserved read bits and the initial latch value as project policy.
- Preserve the compatibility distinctions for FF72-FF75 already adopted from D-04/D-10, despite broader source wording, and keep existing PCM visibility checks in the same table oracle.
- Use `gbb_test_ir_latch` only as a private read-only test seam for lifecycle assertions; direct register behavior remains checked through guest bus instructions, with no public API change.

## TDD Evidence

- **Task 1 RED:** `cgb_ir_tracer` ran and failed its guest assertion with expected `$3E`, actual STOP at `$FF56`; the fresh JUnit evidence classifier returned `RED_EVIDENCE_OK`. An earlier direct attempt used an unregistered test case and was not counted as RED; the registered test was then run and captured correctly.
- **Task 1 GREEN:** `24f07c7` implemented the CGB policy. The exact three IR CTests passed, the expanded visibility/table/model-gate selection passed, and the tracer feedback rerun passed before Task 2 expansion.
- **Task 2 RED:** `cgb_tables_postboot` ran and failed specifically because `ff56 DMG` was missing from the post-boot mirror. The complete JUnit report was accepted by the evidence classifier as `RED_EVIDENCE_OK` before implementation.
- **Task 2 GREEN:** `01e1797` added the reset row and lifecycle and port contracts. The exact seven Task 2 CTests were present and passed; post-boot/table self-tests now reject the named mutants and report `mutants=14`.

## Verification

- `cmake --preset phase1 && cmake --build --preset phase1` passed.
- Task 1's exact required IR CTests passed 3/3. Task 2's exact seven required CTests were all present; its focused table/lifecycle selection passed 9/9.
- The broader affected selection covering all three visibility columns, IR contracts, post-boot/I/O mirrors, model-gate controls, CGB Mooneye dispositions, speed-reset seams, and HDMA lifecycle/timing seams passed 29/29. The final visibility/table selection passed 13/13.
- `cgb_tables_postboot_selftest` reports 14 rejected mutants, including FF75 mask and compatibility FF74 decode mutations; the documentation mutation tests also pass.
- The two Mooneye hardware-I/O guests still have exact observed failure signatures: `boot_hwio-C` callback/result PCs `$01F5/$4067`, `unused_hwio-C` `$1A31/$4070`. Their author expectation remains `pass`, evaluator status remains `xfail`, and the xfail tamper controls pass.
- `bash tests/scripts/verify-dmg-baseline.sh` passed with 313 inventory keys, 15 Mooneye keys, 20 acceptance keys, 2 benchmark keys, and zero changed rows.
- Input identity for this summary's measured implementation range: `6c5b7040a40a25ca1f21aae11f97a8268d05c80b` through `01e1797a4720926a7ef843935fabb562360a4913`. Runtime identity: `@opengsd/gsd-core` 1.16.0; build preset: `phase1`.

## Deviations from Plan

None in scope. The failed-load and independent-instance checks use one private read-only seam so they can inspect the instance-owned latch directly without widening the public API. Existing CGB runner dispositions were left unchanged because the two current hardware-I/O observations already matched their exact xfail signatures; the runner contract and its negative controls were rerun.

## Issues Encountered

- The first Task 2 RED record contained only the console assertion and was correctly rejected as unsupported evidence. Replacing it with the unchanged, complete JUnit report produced `RED_EVIDENCE_OK`; no implementation work began before that gate passed.
- A required Mooneye cohort still records two guest failures against author expectations of `pass`. Both are deliberately retained as exact xfails; neither was converted into a pass or broadened disposition.

## User Setup Required

None.

## Next Phase Readiness

Plan 14-02 is complete. The parent executor owns shared phase state and will run the full wave gate before the Phase 14 handoff; no Phase 15 work is started here.

## Self-Check: PASSED

The summary, all seven modified source/test/document files, and all four task commits exist; each task commit is an ancestor of the current plan head.

---
*Phase: 14-cgb-e-model-qualification-and-corpus*
*Completed: 2026-10-15*
