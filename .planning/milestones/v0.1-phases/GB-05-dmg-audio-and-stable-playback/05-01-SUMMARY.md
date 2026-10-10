---
phase: GB-05-dmg-audio-and-stable-playback
plan: "01"
subsystem: audio
tags: [C17, DMG, PCM, SDL3, SPSC]
requires:
  - phase: GB-03-visible-interactive-dmg
    provides: Optional SDL3 player event loop, host pacing, and packaged player smoke.
provides:
  - Public gbb_run_audio API with caller-owned 48 kHz signed-16 stereo frames and whole-instruction capacity preflight.
  - Per-instance pulse-one register path and a fixed-capacity SDL SPSC ring adapter.
  - Authored pulse guest smoke and named audio_tracer/audio_capacity regression cases.
affects: [GB-05-02, audio, player]
actuals:
  tokens: 8638
  tasks: 2
  commits: 3
tech-stack:
  added: []
  patterns: [caller-owned PCM, whole-instruction output preflight, C17 SPSC ring, SDL3 audio-stream callback]
key-files:
  created: [src/player/audio.c, tests/test_audio.c]
  modified: [include/gabbaboy/gabbaboy.h, src/core/gabbaboy.c, src/player/main.c, CMakeLists.txt, tests/CMakeLists.txt, tests/expected-tests.txt]
key-decisions:
  - "Expose gbb_run_audio with gbb_audio_frame and an explicit produced-frame count; legacy gbb_run and gbb_run_ex remain muted."
  - "Keep guest execution on the player loop and let the SDL stream callback copy only from the bounded SPSC ring."
patterns-established:
  - "Audio capacity is preflighted against the complete next instruction before CPU or device mutation."
  - "The player ring has a 3,214-frame logical ceiling and lock-free atomic indices/counters."
requirements-completed: []
coverage:
  - id: D1
    description: "The public audio run emits deterministic 48 kHz stereo frames and stops atomically when caller capacity is insufficient."
    verification:
      - kind: unit
        ref: "tests/test_audio.c#audio_capacity"
        status: pass
    human_judgment: false
  - id: D2
    description: "An authored pulse-register guest produces the expected frame count and duty waveform."
    verification:
      - kind: unit
        ref: "tests/test_audio.c#audio_tracer"
        status: pass
    human_judgment: false
  - id: D3
    description: "The player smoke submits the authored guest's nonzero PCM to the SDL adapter and reports application counters."
    verification:
      - kind: e2e
        ref: "tests/scripts/verify-phase3-player.sh#player_smoke"
        status: pass
    human_judgment: false
metrics:
  duration: 16min
  completed: 2026-10-08
  status: complete
  plan_head_before: dc58bf3da62ca9473ea70b9882cd7383e0f8f40c
  plan_head_after: 321fdb4ecd1319888a0a431c0b1b72dbb4a21ccc
  commits: 3
---

# Phase GB-05 Plan 01: DMG Pulse PCM Tracer Summary

**A bootless guest can program pulse one, produce bounded 48 kHz stereo PCM, and submit it through the SDL3 player ring.**

## Performance

- **Duration:** 16 min
- **Started:** 2026-10-08T12:48:24Z
- **Completed:** 2026-10-08T13:04:12Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- Added `gbb_run_audio`, which writes caller-owned `gbb_audio_frame` output and reserves the next instruction's maximum frame contribution before guest mutation. Legacy run calls remain muted.
- Added an initial per-instance pulse-one register oscillator, 48 kHz stereo sampling, and a bounded SDL3 SPSC audio-stream adapter. The player loop advances the guest; its stream callback only copies/zero-fills ring data and updates lock-free counters.
- Extended player smoke with an authored pulse-register guest and added named `audio_tracer` and `audio_capacity` cases. On the final packaged smoke, the guest produced 803 frames, 404 nonzero frames, and submitted 803 frames to SDL; application underflow was 1,024 frames and ring high-water was 1,606 frames.

## Task Commits

1. **Task 1: Carry one guest pulse tone into SDL** — `c13adb3` (`feat`)
2. **Task 2: Register the pulse and output-capacity regression** — `c2d49ed` (`test`)
3. **Rule 2 fix: Count ring backpressure** — `321fdb4` (`fix`)

The plan ledger records base `dc58bf3da62ca9473ea70b9882cd7383e0f8f40c`, plan head `321fdb4ecd1319888a0a431c0b1b72dbb4a21ccc`, and three commits before the plan metadata commit.

## Files Created/Modified

- `include/gabbaboy/gabbaboy.h` — Declares the fixed-format audio frame and audio-aware run API.
- `src/core/gabbaboy.c` — Adds per-instance pulse-one registers, oscillator sampling, reset behavior, and frame-capacity preflight.
- `src/player/audio.c` — Owns the bounded SPSC ring, lock-free counters, and SDL3 stream callback.
- `src/player/main.c` — Opens audio with an explicit unavailable fallback, feeds PCM from the event loop, and verifies an authored pulse guest in smoke mode.
- `CMakeLists.txt` — Adds the audio adapter to the optional player target.
- `tests/test_audio.c` — Checks exact elapsed-time frame count, pulse duty waveform, guard bytes, muted-run timing continuity, and output-full instruction atomicity.
- `tests/CMakeLists.txt`, `tests/expected-tests.txt` — Register the named audio regressions in CTest and its required inventory.

## Decisions Made

- The public entry point is `gbb_run_audio`; callers provide an array of signed-16 interleaved stereo frames and receive the exact frame count separately.
- Core output remains device-independent. SDL format conversion and host ring ownership stay inside the optional player.
- AUDIO-01/02/03 remain phase-level requirements with further planned work, so this plan summary marks none complete. This slice implements one pulse path; it does not deliver the full four-channel APU, divider sequencer, mixer controls, volume controls, or sustained-playback qualification.
- `requirements.ready-ids` reported 0/3 IDs eligible at this plan boundary; no requirement checkbox was changed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Count producer stalls at the ring ceiling**
- **Found during:** Overall review after Task 2
- **Issue:** Guest advancement stopped when the ring reached its logical ceiling, but the backpressure counter did not record that stop unless publication itself failed.
- **Fix:** Count ring-full producer stalls directly and use lock-free 64-bit lifetime counters for underflow/backpressure.
- **Files modified:** `src/player/audio.c`, `src/player/main.c`
- **Verification:** Rebuilt the player; the selected core/audio CTests and all 37 packaged-player tests passed.
- **Committed in:** `321fdb4`

**Total deviations:** 1 auto-fixed (Rule 2). The correction closes the planned application-side backpressure reporting requirement.

## TDD Gate Compliance

Task 05-01-02 was explicitly marked `tdd="true"`, but its tests follow Task 05-01-01, which already implements and commits the tested behavior. No semantically valid pre-implementation RED run or RED commit could be produced in this sequential task order. The first draft test run failed on an incorrect edge-count threshold; after correcting that expectation and a trace-buffer advancement mistake, both named tests passed against the already committed implementation. No failed or malformed run is presented as RED evidence, and Task 2 required no additional feature implementation.

The run path was also inspected for allocation calls: `gbb_run_audio` and its execution path do not allocate. This is source inspection, not runtime allocator instrumentation.

## Automated Results

- `cmake --preset phase1 -DGABBABOY_BUILD_PLAYER=OFF` — passed.
- `cmake --build --preset phase1` — passed.
- `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(instance_lifecycle$|run_output_capacity$|audio_(tracer|capacity))$'` — 4/4 passed.
- Player package verifier `tests/scripts/verify-phase3-player.sh` passed; packaged-player CTest inventory 37/37 passed, authored pulse PCM reached SDL, and downloaded-package smoke passed.
- The sandbox blocked SDL's normal macOS preferences path with `EPERM`; checks were rerun successfully with `CFFIXED_USER_HOME=/private/tmp/gabbaboy-home` and `SDL_AUDIODRIVER=dummy`. The script built its pinned SDL 3.4.18 dependency.

## Issues Encountered

- The first local player CMake configure inherited `GABBABOY_BUILD_PLAYER=ON` and found only system SDL 3.4.10. The project verification script builds pinned SDL 3.4.18, and the core preset was rerun with the player option explicitly disabled.
- Default SDL preferences were outside the writable sandbox. A temporary preferences home under `/private/tmp` enabled the player smoke without changing project configuration.

## User Setup Required

None.

## Next Plan Readiness

Plan 05-01 is complete and Plan 05-02 is runnable. It expands the one-channel tracer into both pulse channels and divider-sequencer behavior. This is still Phase GB-05; no phase or milestone is complete. The next phase-level executor command remains `$gsd-execute-phase 5`.

---
*Phase: GB-05-dmg-audio-and-stable-playback*
*Completed: 2026-10-08*

## Self-Check: PASSED

- Summary file exists at the required phase path.
- Task commits `c13adb3`, `c2d49ed`, and `321fdb4` are ancestors of the current plan branch HEAD.
