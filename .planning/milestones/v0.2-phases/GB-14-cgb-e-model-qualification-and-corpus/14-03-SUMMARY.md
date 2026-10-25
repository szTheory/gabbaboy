---
phase: 14-cgb-e-model-qualification-and-corpus
plan: "03"
subsystem: testing
tags: [cgb, apu, pcm, model-gates, guest-tests]
requires:
  - phase: "14-01"
    provides: Guest-visible PCM12/PCM34 per-mode reads and independent table contracts
  - phase: "14-02"
    provides: FF56 and FF72–FF75 visibility policies with guest and lifecycle checks
provides:
  - Timed CGB CH3 sample-buffer behavior shared by PCM output and host mixing
  - Guest-qualified APU power, off-state writes, wave access, length, sweep, and DIV transitions
  - Updated model-gate and audio limitation claims with exact DMG boundary
affects: [14-09, phase-14-integration, cgb-apu]
actuals:
  tokens: 10484
  tasks: 2
  commits: 4
commits: 4
plan_head_before: 72dd987ab214a888c5605d7a2e015ff8f7d82c3c
plan_head_after: e6e89a8f1730c004df9c90829b583c4853d07003
tech-stack:
  added: []
  patterns:
    - Guest-observed hardware transitions with independent expected-value assertions
    - Explicit mutant and omitted-transition controls for model sensitivity
key-files:
  created: []
  modified:
    - src/core/gabbaboy.c
    - tests/test_cgb_apu.c
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - docs/audio-and-playback.md
    - docs/model-gates.md
key-decisions:
  - CGB CH3 reads a sample latched on timed wave fetches; PCM and host mixing share that value while DMG keeps its frozen direct-RAM path.
  - CGB length-enable and trigger ordering follows the qualified odd-step clock behavior without changing the DMG baseline.
  - Model-gate claims remain scoped to tested software behavior; unresolved DMG length-retention evidence stays explicitly unknown.
patterns-established:
  - CGB APU transitions are exercised through bounded guest programs with exact terminal observations.
  - Every key transition includes a negative control that omits or mutates the relevant behavior.
requirements-completed: []
coverage:
  - id: D1
    description: CGB CH3 retains the previous sample through trigger until a timed fetch, and PCM and host mix use the same latched sample.
    requirement: CGB-08
    human_judgment: false
    verification:
      - kind: unit
        ref: ctest --test-dir build -R '^(cgb_apu_wave_latch|cgb_apu_wave_fetch|cgb_apu_wave_direct_ram_control)$' --output-on-failure --no-tests=error
        status: pass
      - kind: other
        ref: Direct-RAM mutant diagnostic expected=07 actual=0A before fetch; guest observes new sample after fetch.
        status: pass
  - id: D2
    description: CGB APU power, off-state writes, active wave access, length and sweep ordering, and normal/double-speed DIV transitions have guest assertions and controls.
    requirement: CGB-08
    human_judgment: false
    verification:
      - kind: integration
        ref: ctest --test-dir build -R '^(cgb_apu_power|cgb_apu_off_writes|cgb_apu_wave_access|cgb_apu_trigger_length_sweep|cgb_apu_div_stop|cgb_apu_transition_controls|model_gates)$' --output-on-failure --no-tests=error
        status: pass
      - kind: other
        ref: ctest related CGB APU, PCM, DMG APU, table, speed, runner, and disposition cohorts with -j2; 54/54 passed, including omitted-DIV and CH4-frequency controls.
        status: pass
  - id: D3
    description: Audio and model-gate claims track the implemented CGB behavior while preserving the frozen DMG baseline and precise unresolved DMG limitations.
    requirement: CGB-08
    human_judgment: false
    verification:
      - kind: other
        ref: bash tests/scripts/verify-dmg-baseline.sh
        status: pass
      - kind: other
        ref: python3 -I tests/scripts/verify-model-gates.py; model-gates pass functions=186 gates=100 unknown=34
        status: pass
      - kind: integration
        ref: ctest --test-dir build -R '^(model_gates|summary_coverage|cgb_speed_dispositions(_.*)?|cgb_apu_(power|off_writes|wave_access|trigger_length_sweep|div_stop|transition_controls|wave_latch|wave_fetch|wave_direct_ram_control))$' --output-on-failure --no-tests=error -j2; 15/15 passed
        status: pass
      - kind: integration
        ref: cmake --preset phase1 && cmake --build --preset phase1
        status: pass
duration: 16min
completed: 2026-10-15
status: complete
---

# Phase 14 Plan 03: CGB-E Model Qualification and Corpus Summary

**Timed CGB CH3 sample latching now drives both PCM and host mixing, with guest-qualified power, wave-RAM, length, sweep, and DIV transitions.**

## Performance

- **Duration:** 16 minutes from the first task commit through final verification; executor start time was not persisted.
- **Started:** 2026-10-15T15:02:38-04:00 (first task commit)
- **Completed:** 2026-10-15T15:18:40-04:00
- **Tasks:** 2 completed
- **Files modified:** 6

## Accomplishments

- Added a CGB CH3 sample buffer filled at timed wave fetches. Trigger resets position without replacing the current sample, and the same latched nibble feeds PCM and host mixing. A real guest distinguishes the retained sample from the next fetched sample.
- Added guest coverage for APU off/on clearing, ignored off-state writes, Wave RAM retention and active alias access, length-enable/trigger ordering, sweep restart, CH4 frequency changes, and DIV edge timing at normal and double speed.
- Updated the audio limitation and six model-gate dispositions to describe the tested software model, its controls, model/mode scope, owners, and promotion requirements. GATE-15 and GATE-34 retain the explicit DMG length-retention unknown; no physical-hardware result is claimed.

## Task Commits

1. **Task 1 RED: add failing CGB wave sample latch assertion** — `5440944` (`test`)
2. **Task 1 GREEN: latch CGB CH3 samples at timed wave fetches** — `b3b52dd` (`feat`)
3. **Task 2 RED: add failing CGB trigger length guest case** — `5c65c0e` (`test`)
4. **Task 2 GREEN: qualify CGB APU transition sequencing** — `e6e89a8` (`feat`)

## Files Created/Modified

- `src/core/gabbaboy.c` — Adds CGB CH3 timed sample latching and CGB odd-step length ordering while preserving the DMG path.
- `tests/test_cgb_apu.c` — Adds guest transition checks, direct-RAM mutant, and omitted-transition/frequency controls.
- `tests/CMakeLists.txt` — Registers the new private CGB APU tests and controls.
- `tests/expected-tests.txt` — Expands the required test inventory.
- `docs/audio-and-playback.md` — Documents the model-qualified CH3 behavior and its limitations.
- `docs/model-gates.md` — Records tested gate dispositions and exact unresolved evidence.

## Decisions Made

- Keep the sample buffer CGB-specific and update it only when the channel actually fetches a Wave RAM byte; this preserves the existing DMG output contract.
- Apply the additional CGB length clock at the modeled odd non-length sequencer step for both length-enable and zero-length trigger ordering; do not alter the frozen DMG baseline.
- Retain model-gate unknowns where evidence does not justify a broader claim, especially DMG length-counter retention.

## TDD Gate Compliance

- Task 1 RED evidence: `build/tdd-red-14-03-task-1.json`; the guest failed the intended retained-sample assertion (`expected 0x07, actual 0x0a`) and the RED evidence checker returned `RED_EVIDENCE_OK`. The direct-RAM mutant retains that mismatch as a named negative control.
- Task 2 RED evidence: `build/tdd-red-14-03-task-2.json`; the trigger/length guest failed on the expected odd-step status and reached its terminal observation; the RED evidence checker returned `RED_EVIDENCE_OK`.
- Both GREEN commits passed the named task test sets. The direct-RAM mutant, CH4 frequency contrast, and omitted-DIV controls produced their intended diagnostics.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Apply the CGB odd-step length clock when length is enabled during an active channel**
- **Found during:** Task 2
- **Issue:** The RED guest showed that enabling length at the odd non-length sequencer step left a length-one channel active when the independent contract expected it to stop immediately.
- **Fix:** Added the CGB-only extra length clock for the enable edge and applied the same ordering after a zero-length trigger reload.
- **Files modified:** `src/core/gabbaboy.c`, `tests/test_cgb_apu.c`
- **Verification:** The trigger/length guest and transition cohort pass; the frozen DMG baseline remains byte-identical.
- **Committed in:** `e6e89a8`

**2. [Rule 1 - Bug] Keep unexecuted DMG length-retention evidence unresolved**
- **Found during:** Wave 3 integration gate after plan execution
- **Issue:** GATE-15 and GATE-34 used an expected-failure marker for DMG length retention even though no DMG case had executed. The speed-disposition checker correctly required each such marker to map to an executed disposition row.
- **Fix:** Changed both source and table classifications to `UNKNOWN` with `research:14`; documented that no DMG case ran and retained the independent-fixture and baseline-revision promotion rule. No xfail or expectation was fabricated.
- **Files modified:** `src/core/gabbaboy.c`, `docs/model-gates.md`
- **Verification:** `model_gates`, all four `cgb_speed_dispositions` positives/negative controls, the nine affected APU guests, `summary_coverage`, and the frozen DMG baseline passed.
- **Committed in:** Wave 3 correction commit recorded in the execution report.

**Total deviations:** 2 auto-fixed bugs (Rule 1).
**Impact on plan:** The first correction is within planned CGB length behavior. The second reconciles an unresolved DMG classification with the executed evidence; it adds no test expectation or xfail, changes no runtime behavior, and preserves the frozen baseline.

## Issues Encountered

The full preset build passed; the focused transition set passed 7/7; the related APU, PCM, DMG, table, speed, runner, and disposition cohort passed 54/54 with no more than two CTest workers. The Wave 3 gate initially passed 1017/1018 tests; its sole failure was `cgb_speed_dispositions` reporting `disposition-mismatch expected-failure-model-gates ['dmg-length-retention']`. The marker described an unexecuted DMG case, so it was reclassified as unresolved research and the focused correction suite passed 15/15. The DMG baseline verifier passed all 313 inventory keys, 15 Mooneye keys, 20 acceptance keys, and 2 benchmark keys with zero changed rows. Model-gate verification passed with 186 functions, 100 gates, and 34 intentionally unknown gates.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

The CGB APU contracts and model dispositions are ready for downstream Phase 14 corpus work. Image-reference execution remains assigned to plan 14-09. The result qualifies this software model only; no hardware or commercial-game claim is made.

## Self-Check: PASSED

- Summary file exists at the expected phase path.
- All four task commits are ancestors of the current phase branch head.
- The Wave 3 classification correction and all four task commits are represented in the committed working history.
- After the summary update, `summary_coverage` and the targeted correction suite passed.

---
*Phase: 14-cgb-e-model-qualification-and-corpus*
*Completed: 2026-10-15*
