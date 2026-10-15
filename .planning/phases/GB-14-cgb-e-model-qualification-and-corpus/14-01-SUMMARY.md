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
  commits: 4
commits: 4
plan_head_before: e463512aae7ce03e2b429973b4baf2b40d67297d
plan_head_after: 789ddc81c17bdc56380cd8393bff9dbd3f7fcb2f
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
    - tests/test_cgb_visibility.c
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - docs/cgb-profile.md
    - docs/audio-and-playback.md
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

The 8,400-token actual is 33,602 characters divided by four across the seven implementation, test, and documentation files at task HEAD; it excludes this summary. Commits are measured from the persisted plan ledger and exclude the separate summary commit.

## Accomplishments

- Added CGB-mode FF76/FF77 readback for digital channel outputs, packed CH2:CH1 and CH4:CH3, while preserving ignored writes, compatibility `$FF`, and the DMG fail-closed behavior.
- Added a guest tracer that copies FF76 into WRAM and confirms CH1=`0x0f` at half-dot 248; tests cover channel phase, channel/power/DAC gates, read-only behavior, and independent CH3/CH4 nibbles.
- Verified PCM observations remain the same across NR50/NR51 changes, muted `gbb_run`, full audio buffers, and one-frame drained output; documented the evidence boundary and pending CH3 fetch latch.

## Task Commits

1. **Task 1 RED:** `77748af` — failing timed CGB guest read tracer and visibility matrix correction.
2. **Task 1 GREEN:** `dfe02e5` — timestamped CGB PCM register reads and profile evidence.
3. **Task 2 RED:** `b12eddb` — four-channel, gating, read-only, host-invariance, and mutant-control tests.
4. **Task 2 GREEN:** `789ddc8` — compile-time mutation controls and audio-model evidence limits.

## Files Created/Modified

- `src/core/gabbaboy.c` — digital APU channel taps and CGB PCM register decoding; test mutations compile only into isolated mutant cores.
- `tests/test_cgb_apu.c` — timed guest reads, all-channel and phase checks, power/DAC/read-only tests, host-invariance tests, and negative controls.
- `tests/test_cgb_visibility.c` — updated only stale PCM matrix rows and deferred-access expectations; non-PCM assertions remain intact.
- `tests/CMakeLists.txt`, `tests/expected-tests.txt` — registered exact PCM contracts and compile-time mutant targets.
- `docs/cgb-profile.md` — CGB/compatibility/DMG register policy and Pan Docs evidence separated from hardware qualification.
- `docs/audio-and-playback.md` — digital readback contract, host-path independence, and CH3 fetch-boundary limitation.

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

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical Coverage] Updated superseded CGB PCM visibility expectations**

- **Found during:** Task 1 verification.
- **Issue:** `tests/test_cgb_visibility.c` still expected FF76/FF77 to remain deferred in native CGB and compatibility modes after this plan implemented their researched visibility policy.
- **Fix:** Updated only the PCM rows and deferred-access cases; kept all non-PCM matrix assertions unchanged.
- **Files modified:** `tests/test_cgb_visibility.c`.
- **Verification:** `cgb_visibility_matrix_dmg`, `cgb_visibility_matrix_compat`, `cgb_visibility_matrix_cgb`, `cgb_visibility_boundaries`, and `cgb_visibility_deferred_stop` passed.
- **Committed in:** `77748af` (Task 1 RED test commit; scope addition authorized by the orchestrator).

**Total deviations:** 1 Rule 2 coverage correction.
**Impact on plan:** Necessary to keep the visibility matrix aligned with the shipped register behavior; no unrelated rows or requirements were changed.

## Issues Encountered

One initial implementation patch used an outdated enum comment and applied no source changes. The current source context was reread and the patch was reapplied in smaller verified hunks.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 14-01 is complete. Phase 14 and requirement CGB-08 remain under the parent workflow’s tracking; this plan does not mark the phase requirement complete. The CH3 trigger-to-first-fetch latch boundary remains unqualified.

## Self-Check: PASSED

- Summary file exists at the planned path.
- All four task commits are ancestors of the current phase branch head.
- No task commit deleted tracked files.

---
*Phase: 14-cgb-e-model-qualification-and-corpus*
*Completed: 2026-10-15*
