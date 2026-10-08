---
phase: GB-05-dmg-audio-and-stable-playback
plan: "03"
subsystem: audio
tags: [C17, DMG, APU, wave, noise, PCM]
requires:
  - phase: GB-05-dmg-audio-and-stable-playback
    provides: Caller-owned 48 kHz PCM, two pulse channels, and divider-driven sequencing.
provides:
  - Per-instance wave channel, wave RAM, trigger, length, level, and mixer behavior.
  - Per-instance noise LFSR, width mode, polynomial timer, DAC, envelope, and length behavior.
  - Four-channel NR52 status and power-off/on behavior, including reset and channel-mask coverage.
affects: [audio, APU, playback, GB-05]
actuals:
  tokens: 6997.25
  tasks: 2
  commits: 6
tech-stack:
  added: []
  patterns: [authored guest register programs, per-instance channel state, emulated half-dot channel clocks]
key-files:
  created:
    - .planning/phases/GB-05-dmg-audio-and-stable-playback/05-03-01-red-evidence.json
    - .planning/phases/GB-05-dmg-audio-and-stable-playback/05-03-02-red-noise-evidence.json
    - .planning/phases/GB-05-dmg-audio-and-stable-playback/05-03-02-red-power-evidence.json
  modified: [src/core/gabbaboy.c, tests/test_apu.c, tests/CMakeLists.txt, tests/expected-tests.txt, .planning/WINDOWS.md]
key-decisions:
  - "Active wave-RAM accesses alias the current wave byte in the scoped deterministic model; CPU-B revision variation remains unqualified."
  - "Keep authored digital channel and power tests separate from physical hardware and perceptual audio evidence."
patterns-established:
  - "Exercise APU channel behavior through original register-writing guest programs and caller-owned PCM."
  - "Check channel status for all 16 NR52 enable combinations and explicit power/reset transitions."
requirements-completed: [AUDIO-01]
coverage:
  - id: D1
    description: "Wave RAM/register controls and channel-three nibble output join the routed stereo mix."
    requirement: AUDIO-01
    verification:
      - kind: unit
        ref: "ctest -R '^(apu_wave|apu_(pulse|mixer)|audio_tracer)$'"
        status: pass
    human_judgment: false
  - id: D2
    description: "Noise polynomial/LFSR, envelope, length, width mode, four-channel status, power transitions, and reset state are exercised."
    requirement: AUDIO-01
    verification:
      - kind: unit
        ref: "ctest -R '^(apu_noise|apu_power)$'"
        status: pass
      - kind: unit
        ref: "ctest -R '^(apu_|audio_tracer$)'"
        status: pass
    human_judgment: false
metrics:
  duration: 21min
  completed: 2026-10-08
  status: complete
  plan_head_before: 40909fad63998504eb9ddc12e2d876f4eb8307d2
  plan_head_after: 8aeae9d8a38ca3509c6c08c400e43106e4e15a59
  commits: 6
---

# Phase 5 Plan 03: Wave, Noise, and Four-Channel Power Summary

**All four scoped DMG channels now clock and mix deterministic digital output, with authored wave/noise registers and complete NR52 channel-status coverage.**

## Performance

- **Duration:** 21 min
- **Started:** 2026-10-08T13:26:34Z
- **Completed:** 2026-10-08T13:47:12Z
- **Tasks:** 2
- **Files modified:** 8 plan files, plus this summary and required tracking artifacts

## Accomplishments

- Added channel-three register state and wave RAM with DAC gating, trigger/frequency, length, level shifting, packed high/low nibble playback, active wave-RAM alias behavior, and left/right routing.
- Added channel-four register state and a bounded timer-driven 15-bit LFSR, including narrow-width mode, divisor/shift periods, DAC/envelope, length, trigger, and stereo routing.
- Extended the shared divider sequencer and NR52 status/power handling to wave/noise. Authored guest programs check all 16 channel-enable masks, all-channel power-off/on, ignored writes while powered off, wave-RAM retention across NR52-off, and clean core-reset state.

## Evidence and Limits

The authored tests establish the deterministic DMG software model and its digital register/PCM behavior. Active wave-RAM access is modeled as aliasing the current wave byte; revision-specific CPU-B behavior is not hardware-qualified. No physical DMG run or perceptual listening check was performed, and no analog filter/output equivalence is claimed.

## Task Commits

1. **Task 1 RED: add wave RAM/register/output regression** — `d40a2eb` (`test`)
2. **Task 1 GREEN: implement wave channel and wave RAM** — `96dfd9f` (`feat`)
3. **Task 2 RED: add noise and four-channel power cases** — `ea45cfa` (`test`)
4. **Task 2 GREEN: implement noise channel and APU power matrix** — `2fcadb3` (`feat`)
5. **Task 2 test correction: complete reset wave-RAM readback** — `8aeae9d` (`test`)

The initial plan metadata closeout `42233a2` preceded the final reset-test correction. The measured plan base was `40909fad63998504eb9ddc12e2d876f4eb8307d2`; six commits follow it through `8aeae9d8a38ca3509c6c08c400e43106e4e15a59` (five task commits and that earlier metadata commit).

## Files Created/Modified

- `src/core/gabbaboy.c` — Per-instance wave/noise state, register and wave-RAM bus access, divider-timeline channel clocks, frame-sequencer length/envelopes, NR52 status, and stereo mixing.
- `tests/test_apu.c` — Authored wave/noise programs, routed PCM checks, the four-channel status matrix, power transitions, wave-RAM retention, and reset checks.
- `tests/CMakeLists.txt`, `tests/expected-tests.txt` — Register `apu_wave`, `apu_noise`, and `apu_power` in the test inventory.
- Three plan-local RED evidence records — TAP reports accepted by `gsd_run check tdd-red-evidence` before each task's implementation commit.
- `.planning/WINDOWS.md` — Records the two corrected authored-test fixture issues as deviations.

## Decisions Made

- Active wave-RAM accesses alias the current byte in this scoped software model. That revision-sensitive behavior is recorded as an assumption and is not a universal hardware claim.
- Keep digital APU tests distinct from hardware and perceptual evidence; the latter remains uncollected.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test bug] Corrected the wave guest program's DAC register address.**
- **Found during:** Task 1
- **Issue:** The first GREEN attempt wrote `0x80` to `FF30` rather than `NR30` at `FF1A`, replacing the authored `0xF0` wave pattern and leaving the PCM assertion silent.
- **Fix:** Corrected the guest register address and used `NR34=0xC7` to enable length while triggering.
- **Files modified:** `tests/test_apu.c`
- **Verification:** Wave case and full selected APU/tracer inventory passed.
- **Committed in:** `96dfd9f`

**2. [Rule 1 - Test fixture] Moved the channel-mask guest program past the ROM header checksum byte.**
- **Found during:** Task 2
- **Issue:** The generated program crossed ROM offset `0x14D`, which the fixture helper overwrites with the header checksum.
- **Fix:** Loaded the generated test at `0x150` through the existing delayed-program helper.
- **Files modified:** `tests/test_apu.c`
- **Verification:** All 16 channel masks and both power transitions passed in `apu_power`.
- **Committed in:** `2fcadb3`

**3. [Rule 1 - Test fixture] Extended the reset run through the wave-RAM readback.**
- **Found during:** Final verification
- **Issue:** The reset run budget ended after starting the wave-RAM read, so the assertion could observe cleared work RAM without completing its guest store.
- **Fix:** Extended the run budget to include the read and store instructions before checking the value.
- **Files modified:** `tests/test_apu.c`
- **Verification:** The complete APU/tracer inventory passed 8/8.
- **Committed in:** `8aeae9d`

**Total deviations:** 3 test-fixture corrections. **Impact:** No scope change; corrections made the authored expectations execute as intended.

## TDD Gate Compliance

- **Task 05-03-01:** The target `apu_wave` failed because wave RAM/register support was absent; the classifier returned `RED_EVIDENCE_OK`. The wave implementation then passed the target and existing pulse/mixer/tracer regressions.
- **Task 05-03-02:** Both `apu_noise` and `apu_power` failed before implementation for missing noise registers and four-channel status. Both reports returned `RED_EVIDENCE_OK`; the implementation commit followed, and both targets passed.
- A final test-only correction extended the reset run to complete wave-RAM readback; it followed the Task 2 GREEN commit and did not change core behavior.

## Automated Results

- `cmake --preset phase1` — passed.
- `cmake --build --preset phase1` — passed.
- `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(apu_wave|apu_(pulse|mixer)|audio_tracer)$'` — 4/4 passed.
- `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(apu_noise|apu_power)$'` — 2/2 passed.
- `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(apu_|audio_tracer$)'` — 8/8 passed.
- `git diff --check` for the plan's source and test files — passed.

## Next Plan Readiness

Plan 05-03 is complete. Continue within Phase GB-05 with Plan 05-04, which specifies and validates the core audio resampler. This plan completes AUDIO-01's scoped digital-channel coverage; no physical or perceptual qualification is implied.

---
*Phase: GB-05-dmg-audio-and-stable-playback*
*Completed: 2026-10-08*

## Self-Check: PASSED

- Summary file exists at the required phase path.
- Task commits `d40a2eb`, `96dfd9f`, `ea45cfa`, and `2fcadb3` are ancestors of the recorded plan head.
- Task commits `d40a2eb`, `96dfd9f`, `ea45cfa`, `2fcadb3`, and `8aeae9d` are ancestors of the recorded plan head.
- The measured base range contains six commits, including the earlier metadata closeout.
