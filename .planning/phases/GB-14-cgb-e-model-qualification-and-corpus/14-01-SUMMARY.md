---
phase: 14-cgb-e-model-qualification-and-corpus
plan: "01"
subsystem: audio
tags: [cgb, apu, digital-pcm, qualification, guest-tests]
requires: []
provides:
  - Native CGB guest reads of read-only PCM12 and PCM34 digital channel outputs.
  - Automated evidence for all channel nibbles, visibility columns, host-output invariance, and negative controls.
affects: [CGB APU follow-up, audio-model evidence]
actuals:
  tokens: 8400
  tasks: 2
  commits: 12
commits: 12
plan_head_before: e463512aae7ce03e2b429973b4baf2b40d67297d
plan_head_after: 1ddacb60962d32e23133ef72de4bc4d105037d60
tech-stack:
  added: []
  patterns:
    - Guest-program tests read PCM registers through the timed bus path and store observations in WRAM.
    - Compile-time-only mutant cores prove test sensitivity without production runtime selectors.
key-files:
  created:
    - tests/test_cgb_apu.c
  modified:
    - src/core/gabbaboy.c
    - src/runner/main.c
    - tests/test_cgb_visibility.c
    - tests/test_runner.c
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - cmake/VerifyMooneyeCgb.cmake
    - fixtures/mooneye-cgb/manifest.json
    - fixtures/mooneye-cgb/ELIGIBILITY.md
    - docs/cgb-profile.md
    - docs/model-gates.md
    - docs/audio-and-playback.md
    - docs/support/unreleased.md
    - tests/test_cgb_tables.c
key-decisions:
  - Native CGB PCM reads expose digital DAC inputs before NR50/NR51 routing and host sample generation.
  - Keep the claim at the software-model boundary; no physical CGB-E waveform or timing claim is made.
  - Test the current fetched CH3 sample while leaving the trigger-to-first-fetch latch boundary unqualified.
patterns-established:
  - Guest-visible model claims are tested through a ROM program with independent expected values and named bus timestamps.
  - Mutation controls are isolated in test-only core builds and emit the observed mismatch.
requirements-completed: []
coverage:
  - id: D1
    description: Native CGB guests read PCM12 and PCM34 as CH2:CH1 and CH4:CH3 digital nibbles, including channel phase advancement.
    human_judgment: false
    verification:
      - kind: e2e
        ref: "ctest --test-dir build -R '^(cgb_pcm_tracer|cgb_pcm_channels)$' --output-on-failure --no-tests=error"
        status: pass
      - kind: integration
        ref: "tests/test_cgb_apu.c#cgb_pcm_channels expects PCM12=0xef, PCM34=0xfa, and pulse phase 0x0f then 0x00"
        status: pass
  - id: D2
    description: PCM reads obey the native CGB, compatibility, and DMG visibility policies, and the frozen DMG baseline remains byte-identical.
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build -R '^(cgb_visibility_matrix_dmg|cgb_visibility_matrix_compat|cgb_visibility_matrix_cgb|cgb_visibility_boundaries|cgb_visibility_deferred_stop)$' --output-on-failure --no-tests=error"
        status: pass
      - kind: other
        ref: "bash tests/scripts/verify-dmg-baseline.sh"
        status: pass
  - id: D3
    description: PCM output is read-only and independent of host routing, volume, and sample-buffer availability or draining; named controls detect incorrect implementations.
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build -R '^(cgb_pcm_power_dac|cgb_pcm_readonly|cgb_pcm_host_invariance|cgb_pcm_controls)$' --output-on-failure --no-tests=error"
        status: pass
      - kind: other
        ref: "Negative controls: swapped-nibble observed expected=0x0f actual=0xf0; routing-coupled observed expected-muted=0x0f actual=0x00; writable PCM observed expected-readonly=0x0f actual=0xa5."
        status: pass
  - id: D4
    description: Existing CGB Mooneye author pass assertions remain separate from exact current software-model failure observations; failing guests are never counted as passes.
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build -R '^cgb_mooneye_' --output-on-failure --no-tests=error"
        status: pass
      - kind: other
        ref: "Raw protocol verdicts: boot_hwio-C fail callback 0x01F5/result 0x4067; unused_hwio-C fail callback 0x1A31/result 0x4070. Tampered pass disposition, stale unsupported stop, changed fail callback, and false xfail on a passing ROM all remain nonzero controls."
        status: pass
  - id: D5
    description: PCM helper model tags and independent visibility-table checks agree with the native CGB, compatibility, and DMG policies for FF76/FF77.
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build -R '^(model_gates.*|cgb_tables_.*)$' --output-on-failure --no-tests=error"
        status: pass
      - kind: other
        ref: "Negative controls: model_gates_real_deleted_tag, model_gates_real_untagged_function, model_gates_real_doc_mismatch; cgb_tables self-test rejected six PCM profile-disposition mutations plus three existing visibility mutations (pass mutants=12 overall)."
        status: pass
duration: 12min
completed: 2026-10-15
status: complete
---

# Phase 14 Plan 01: Timestamped CGB Digital PCM Summary

**Native CGB guest reads now expose timestamped PCM12/PCM34 digital channel values, with all four channel nibbles, model visibility, host invariance, and mutation sensitivity checked automatically.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-10-15T16:48:58Z
- **Completed:** 2026-10-15T17:01:20Z
- **Tasks:** 2
- **Files modified:** 7

The 8,400-token actual is 33,602 characters divided by four across the seven implementation, test, and documentation files at the original task HEAD; it excludes this summary. Those metrics preserve the original two-task completion snapshot. The measured commit ledger now contains 12 commits from `plan_head_before` through `plan_head_after`, including four interleaved Phase 14-05 commits on the shared phase branch; the task-specific commits remain listed below.

## Accomplishments

- Added CGB-mode FF76/FF77 readback for digital channel outputs, packed CH2:CH1 and CH4:CH3, while preserving ignored writes, compatibility `$FF`, and the DMG fail-closed behavior.
- Added a guest tracer that copies FF76 into WRAM and confirms CH1=`0x0f` at half-dot 248; tests cover channel phase, channel/power/DAC gates, read-only behavior, and independent CH3/CH4 nibbles.
- Verified PCM observations remain the same across NR50/NR51 changes, muted `gbb_run`, full audio buffers, and one-frame drained output; documented the evidence boundary and pending CH3 fetch latch.

## Task Commits

1. **Task 1 RED:** `77748af` — failing timed CGB guest read tracer and visibility matrix correction.
2. **Task 1 GREEN:** `dfe02e5` — timestamped CGB PCM register reads and profile evidence.
3. **Task 2 RED:** `b12eddb` — four-channel, gating, read-only, host-invariance, and mutant-control tests.
4. **Task 2 GREEN:** `789ddc8` — compile-time mutation controls and audio-model evidence limits.
5. **Rule 2 integration correction:** `074695e` — replaced stale CGB Mooneye unsupported dispositions with exact observed-failure xfails while preserving author pass assertions.
6. **Rule 2 integration correction:** `1ddacb6` — tagged PCM helpers and added an independent three-model register-table oracle with six PCM mutants.

## Files Created/Modified

- `src/core/gabbaboy.c` — digital APU channel taps and CGB PCM register decoding; test mutations compile only into isolated mutant cores.
- `tests/test_cgb_apu.c` — timed guest reads, all-channel and phase checks, power/DAC/read-only tests, host-invariance tests, and negative controls.
- `tests/test_cgb_visibility.c` — updated only stale PCM matrix rows and deferred-access expectations; non-PCM assertions remain intact.
- `tests/CMakeLists.txt`, `tests/expected-tests.txt` — registered exact PCM contracts and compile-time mutant targets.
- `tests/test_cgb_tables.c` — independently pins FF76/FF77 visibility by model and compares the PCM register rows with the profile documentation.
- `docs/cgb-profile.md` — CGB/compatibility/DMG register policy and Pan Docs evidence separated from hardware qualification.
- `docs/model-gates.md` — documents the model-neutral PCM helpers' caller-gate basis.
- `docs/audio-and-playback.md` — digital readback contract, host-path independence, and CH3 fetch-boundary limitation.
- Integration follow-up also changed `src/runner/main.c`, `tests/test_runner.c`, `tests/CMakeLists.txt`, `tests/expected-tests.txt`, `cmake/VerifyMooneyeCgb.cmake`, `fixtures/mooneye-cgb/manifest.json`, `fixtures/mooneye-cgb/ELIGIBILITY.md`, and `docs/support/unreleased.md`.

## Decisions Made

- Digital PCM is sampled from per-instance channel generator state before host mixing, routing, or gain; no public API or host PCM format changed.
- Pan Docs establishes the documented register mapping, while the tests qualify this implementation’s software model only.
- CH3 tests observe the sample already fetched by this model; trigger-to-first-fetch latch timing remains future qualification work.

## TDD Evidence

- **Task 1 RED:** `build/tests/test_cgb_apu cgb_pcm_tracer` failed the named guest assertion before implementation: expected `0x0f`, actual `0x00`, `UNSUPPORTED_BUS`, zero FF76 reads, and no timestamp. `gsd_run check tdd-red-evidence` returned `RED_EVIDENCE_OK` for the recorded TAP result. After GREEN, the guest read `0x0f` at half-dot 248.
- **Task 2 RED:** `build/tests/test_cgb_apu_routing_mutant cgb_pcm_controls` failed the named mutant-sensitivity predicate before the mutation hook existed: route-enabled and muted values both remained `0x0f`. The target executed and failed its intended assertion; the evidence classifier returned `RED_EVIDENCE_OK` (`target_test_failed`).
- **Task 2 GREEN:** the routing-coupled control now reports `expected-muted=0x0f actual=0x00`; the writable control reports `expected-readonly=0x0f actual=0xa5`. The independent swapped-nibble control reports `expected=0x0f actual=0xf0`. Each control CTest passes only after observing its intended mutation.

## Verification

- Task 1 exact required CTest membership: all five names present; five required tests passed. Tracer feedback reran after the Task 1 commit and passed again.
- Task 2 exact required CTest membership: all five names present; five required tests passed. The complete PCM set (tracer, all-channel, gating, read-only, host invariance, baseline controls, and three mutation controls) passed.
- Nearby APU, visibility, CGB speed, and CGB HDMA regression selection passed **266/266** tests.
- `bash tests/scripts/verify-dmg-baseline.sh`: inventory 313 keys, Mooneye 15 keys, acceptance 20 keys, benchmark 2 keys; zero baseline changes; status pass.
- `cmake --preset phase1` and `cmake --build --preset phase1` passed. Expected-test membership had no missing required names.
- After the integration correction, the CGB Mooneye selection passed 18/18 tests including its fixture prerequisite; the CGB visibility matrices passed 3/3; `verify-cgb-corpus-inventory.py --selection-only` reported 181 sources, 109 outputs, 28 admitted, 81 pending and 107 cases. `summary_coverage` passed 1/1 after this summary update.
- After the PCM model-gate/table correction, the focused model-gate and `cgb_tables_*` selection passed 19/19; PCM, visibility, Mooneye, inventory, and DMG identity contracts passed 43/43. Corpus selection reported 181 sources, 109 outputs, 28 admitted, 81 pending and 107 cases. The DMG baseline remains unchanged: 313 inventory keys, 15 Mooneye keys, 20 acceptance keys, 2 benchmark keys, zero changed rows.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical Coverage] Updated superseded CGB PCM visibility expectations**

- **Found during:** Task 1 verification.
- **Issue:** `tests/test_cgb_visibility.c` still expected FF76/FF77 to remain deferred in native CGB and compatibility modes after this plan implemented their researched visibility policy.
- **Fix:** Updated only the PCM rows and deferred-access cases; kept all non-PCM matrix assertions unchanged.
- **Files modified:** `tests/test_cgb_visibility.c`.
- **Verification:** `cgb_visibility_matrix_dmg`, `cgb_visibility_matrix_compat`, `cgb_visibility_matrix_cgb`, `cgb_visibility_boundaries`, and `cgb_visibility_deferred_stop` passed.
- **Committed in:** `77748af` (Task 1 RED test commit; scope addition authorized by the orchestrator).

**Original plan deviation:** One Rule 2 visibility coverage correction, necessary to keep the matrix aligned with the shipped register behavior; no unrelated rows or requirements were changed.

**2. [Rule 2 - Missing Critical Functionality] Replace stale unsupported-bus expectations with exact observed-failure dispositions**
- **Found during:** Phase 14 Wave 1 integration after the PCM visibility change.
- **Issue:** `boot_hwio-C` and `unused_hwio-C` no longer stop at unsupported bus address `$FF76`; both reach their Mooneye protocol result with a failing guest verdict. The old manifest, runner rows, CTest predicates and unsupported-stop control produced four integration failures.
- **Fix:** Kept each manifest author assertion at `expect=pass`, added a separate `observed_disposition=expected-failure`, and accepted only the compiled failure callback, result PC and all six failure registers as an xfail. Updated suite/category counts, the manifest SHA admission pin, fail-closed inventory/pc-table checks, tamper controls and support notes. A failing guest remains `observed=fail` and is excluded from guest-pass totals.
- **Actual verdicts:** `boot_hwio-C` reports `callback_result=fail callback_pc=01f5 result_pc=4067` after 25,904 half-dots; `unused_hwio-C` reports `callback_result=fail callback_pc=1a31 result_pc=4070` after 34,504 half-dots. The local profile-runner receipts mark these observations `build_qualified=false`.
- **Negative-control diagnostics:** Tampered-to-pass `status=fail observed=fail code=1`; stale unsupported disposition `status=fail reason=no-unsupported-bus-stop code=1`; wrong callback `status=unexpected-failure reason=callback-not-reached code=1`; passing guest mislabeled as expected failure `status=unexpected-pass code=1`.
- **Files modified:** `src/runner/main.c`, `tests/test_runner.c`, `tests/CMakeLists.txt`, `tests/expected-tests.txt`, `cmake/VerifyMooneyeCgb.cmake`, `fixtures/mooneye-cgb/manifest.json`, `fixtures/mooneye-cgb/ELIGIBILITY.md`, `docs/support/unreleased.md`.
- **Verification:** CGB Mooneye CTest selection passed 18/18 (including its fixture prerequisite); CGB visibility matrices passed 3/3; CGB corpus inventory selection-only reported 181 sources, 109 outputs, 28 admitted, 81 pending and 107 cases; DMG baseline reported zero changes; `summary_coverage` passed 1/1 after this summary update.
- **Commit:** `074695e`.
- **Full-suite status:** The parent stopped the Phase 14 full CTest run after its integration failures. That run is not a pass; the parent will rerun the full suite after this correction.

**3. [Rule 2 - Missing Critical Coverage] Pin PCM model-gate tags and profile table semantics**
- **Found during:** Phase 14 Wave 1 recheck; the full suite reported 997/1003 passing and six failures, so the run was not a pass.
- **Issue:** Both PCM helpers were untagged, masking the expected diagnostics in four model-gate checks. The independent CGB register table could not render PCM cells and did not independently reject the superseded deferred/compatibility/DMG dispositions for both registers.
- **Fix:** Tagged both model-neutral helpers with the caller-branch basis and documented that basis. Added PCM12/PCM34 table rendering and an independent FF76/FF77 oracle for native CGB PCM reads, compatibility `$FF`, and DMG fail-closed reads. Six PCM profile mutants (two addresses across three model columns) are now rejected alongside the three existing register-table controls. No Phase 14-02 IR/FF74 cells were changed.
- **Negative-control evidence:** The model-gate deleted-tag, appended-untagged-function, and code/document mismatch tests passed with their expected diagnostics. The table self-test emitted `cgb-tables mismatch: a DMG`, `policy-without-reason: divider_counter DMG`, `hw-test-outside-compat: a CGB`, and register-row mismatches at `$FF4C CGB`, `$FF55 DMG`, and `$FF0A CGB`; it then reported `cgb-tables self-test pass mutants=12`, including the six PCM policy mutants.
- **Files modified:** `src/core/gabbaboy.c`, `docs/model-gates.md`, `tests/test_cgb_tables.c`, `tests/CMakeLists.txt`.
- **Verification:** Model-gate and CGB table contracts passed 19/19; the focused PCM, visibility, Mooneye, inventory, and DMG identity selection passed 43/43; CGB corpus selection reported 181 sources, 109 outputs, 28 admitted, 81 pending and 107 cases; the frozen DMG baseline reported zero changes.
- **Commit:** `1ddacb6`.
- **Full-suite status:** The failed 997/1003 Wave 1 recheck remains a failure. The parent owns the next full-suite rerun; no full-suite pass is claimed here.

**Total deviations:** 3 Rule 2 corrections.
**Impact on plan:** Both corrections align existing verification with the implemented CGB PCM behavior and actual guest protocol results; corpus membership and author assertions were preserved.

## Issues Encountered

One initial implementation patch used an outdated enum comment and applied no source changes. The current source context was reread and the patch was reapplied in smaller verified hunks.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 14-01 is complete. Phase 14 and requirement CGB-08 remain under the parent workflow’s tracking; this plan does not mark the phase requirement complete. The CH3 trigger-to-first-fetch latch boundary remains unqualified.

## Self-Check: PASSED

- Summary file exists at the planned path.
- The four original task commits and both Rule 2 correction commits are ancestors of the current phase branch head.
- Summary coverage passed 1/1; measured plan-ledger count is 12 commits through `1ddacb6`.
- No task commit deleted tracked files.

---
*Phase: 14-cgb-e-model-qualification-and-corpus*
*Completed: 2026-10-15*
