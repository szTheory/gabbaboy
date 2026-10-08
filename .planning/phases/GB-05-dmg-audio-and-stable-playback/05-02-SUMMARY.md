---
phase: GB-05-dmg-audio-and-stable-playback
plan: "02"
subsystem: audio
tags: [C17, DMG, APU, pulse, divider, PCM]
requires:
  - phase: GB-05-dmg-audio-and-stable-playback
    provides: Caller-owned 48 kHz stereo PCM and the initial pulse-one path from Plan 05-01.
provides:
  - Per-instance pulse-two registers and oscillator alongside pulse one.
  - NR10-14 and NR21-24 pulse controls, DAC enable, sweep, envelope, and length state.
  - NR50/NR51 stereo routing and NR52 power/channel status behavior.
  - Divider-falling-edge APU sequencer clocks, including DIV-write edges.
  - Authored pulse, mixer, sequencer, run-partition, HALT, STOP, and reset regressions.
affects: [audio, GB-05, playback]
actuals:
  tokens: 6588
  tasks: 2
  commits: 3
tech-stack:
  added: []
  patterns: [per-instance pulse channels, divider-edge sequencer, authored guest register programs]
key-files:
  created: [tests/test_apu.c, .planning/phases/GB-05-dmg-audio-and-stable-playback/05-02-01-red-evidence.json]
  modified: [src/core/gabbaboy.c, tests/CMakeLists.txt, tests/expected-tests.txt]
key-decisions:
  - "Keep pulse, mixer, and divider-sequencer behavior in the existing per-instance core and half-dot timeline; this is a documented software model, not hardware qualification."
  - "Keep AUDIO-01 pending because the remaining wave/noise channels and phase-level evidence are not complete."
patterns-established:
  - "Guest APU registers are exercised through original register-writing programs and caller-owned PCM output."
  - "Run partition checks compare exact output at the same consumed emulated time."
requirements-completed: []
coverage:
  - id: D1
    description: "Both DMG pulse channels expose scoped register, DAC, sweep, envelope, length, and stereo mixer behavior."
    requirement: AUDIO-01
    verification:
      - kind: unit
        ref: "ctest -R '^(apu_(pulse|mixer)|audio_tracer)$'"
        status: pass
    human_judgment: false
  - id: D2
    description: "DIV falling edges and DIV writes clock the APU sequencer deterministically across run partition, HALT, STOP, and reset cases."
    requirement: AUDIO-01
    verification:
      - kind: unit
        ref: "ctest -R '^(apu_(sequencer|timeline)|timer_|halt_|stop_)'"
        status: pass
    human_judgment: false
metrics:
  duration: 17min
  completed: 2026-10-08
  status: complete
  plan_head_before: 3f3aafa80ff8ce5d225362156fd9c3bc496f2133
  plan_head_after: d444076f57293c858f2ed2e03e8e46fac7445b52
  commits: 3
---

# Phase 5 Plan 02: Both Pulse Channels and Divider Sequencer Summary

**Pulse one and two now feed independently routed stereo output, with register and sequencer state advanced on the emulated divider timeline.**

## Performance

- **Duration:** 17 min
- **Started:** 2026-10-08T13:05:30Z (approximate; start timestamp was not captured at executor initialization)
- **Completed:** 2026-10-08T13:22:30Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Added pulse-two state and guest register access, and expanded pulse one to cover sweep, envelope, length, trigger, DAC disable, and NR52 status behavior.
- Routed digital pulse output independently through NR50/NR51 left and right controls while retaining the existing pulse-one waveform regression.
- Clocked length, sweep, and envelope sequencing from divider bit 12 falling edges, including a falling edge caused by a DIV write. Added run-partition, HALT, STOP, reset, and DIV-write checks.

## Evidence and Limits

The authored guest programs and named CTests establish the implemented deterministic software model. They are not differential hardware observations and do not establish electrical or revision-specific DMG equivalence. No physical DMG or subjective listening evidence was collected. AUDIO-01 remains pending because the wave and noise channels and the full phase requirement remain outside this plan.

## Task Commits

1. **Task 1 RED: add pulse-two register regression** — `b14529c` (`test`)
2. **Task 1 GREEN: implement both pulse channels and routing** — `319e3ca` (`feat`)
3. **Task 2: cover divider and audio timeline boundaries** — `d444076` (`test`)

The measured plan ledger base is `3f3aafa80ff8ce5d225362156fd9c3bc496f2133`; three commits follow it through `d444076`.

## Files Created/Modified

- `src/core/gabbaboy.c` — Per-instance pulse register/channel state, status and mixer reads/writes, stereo digital routing, and divider-sequencer clocking.
- `tests/test_apu.c` — Original guest programs check pulse-two register/DAC behavior, stereo routing, divider-write length clock, output partition equality, HALT/STOP, and reset.
- `tests/CMakeLists.txt`, `tests/expected-tests.txt` — Register the four required `apu_*` cases.
- `.planning/phases/GB-05-dmg-audio-and-stable-playback/05-02-01-red-evidence.json` — Captured TAP RED result for the pulse-two NR22 readback case; `gsd_run check tdd-red-evidence` returned `RED_EVIDENCE_OK`.

## Decisions Made

- Kept the sequencer in the core instance and tied it to the existing divider transition path; host time and polling do not drive APU ticks.
- Kept physical hardware and perceptual claims explicitly outside this software test evidence.
- Did not mark AUDIO-01 complete because this plan covers the pulse channels and sequencer only; phase scope still includes the wave and noise channels.

## Deviations from Plan

The divider-sequencer implementation was added in Task 1's implementation commit because pulse length and envelope behavior depend on sequencer clocks. Task 2 then added boundary and timeline regressions against that implementation rather than adding duplicate clock code.

## TDD Gate Compliance

- **Task 05-02-01:** Valid RED evidence captured before implementation. The target `apu_pulse` assertion failed because pulse-two NR22 was unmapped; the evidence classifier returned `RED_EVIDENCE_OK`. The implementation commit followed, and the pulse, mixer, and prior audio tracer tests passed.
- **Task 05-02-02:** No valid pre-implementation RED was produced. Sequencer behavior had already landed with Task 1 to support pulse envelope/length handling. The new sequencer/timeline tests were added and passed afterward, so this task does not have a canonical RED-then-GREEN commit pair.

## Automated Results

- `cmake --preset phase1` — passed.
- `cmake --build --preset phase1` — passed.
- `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(apu_(pulse|mixer)|audio_tracer)$'` — 3/3 passed.
- `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(apu_(sequencer|timeline)|timer_|halt_|stop_)'` — 13/13 passed.

## Deviations / Deferred Issues

None beyond the task implementation overlap and TDD ordering noted above. No package installs, hardware runs, or external services were required.

## Next Plan Readiness

Plan 05-02 is complete. Continue Phase GB-05 with Plan 05-03, which expands the scoped APU model beyond the two pulse channels. This is not phase completion; AUDIO-01 remains pending.

---
*Phase: GB-05-dmg-audio-and-stable-playback*
*Completed: 2026-10-08*

## Self-Check: PASSED

- Summary file exists at the required phase path.
- Task commits `b14529c`, `319e3ca`, and `d444076` are ancestors of the plan head recorded above.
- The persisted plan ledger measures three task commits from the recorded base.
