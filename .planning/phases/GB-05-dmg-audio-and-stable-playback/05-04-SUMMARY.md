---
phase: GB-05-dmg-audio-and-stable-playback
plan: 04
subsystem: audio
tags: [C17, DMG, PCM, fixed-point, FIR, high-pass]
requires:
  - phase: GB-05-dmg-audio-and-stable-playback
    provides: Four-channel DMG APU mixer and caller-owned 48 kHz PCM path from Plans 05-01 through 05-03.
provides:
  - Authored impulse, step, periodic, alias, partition, and HPF software-model checks.
  - Per-instance fixed-point FIR and DMG-style high-pass state with reset semantics.
  - Overflow/overlap validation and public caller-owned PCM/backpressure contract.
affects: [GB-05-05, audio, player]
actuals:
  tokens: 4957
  tasks: 2
  commits: 2
tech-stack:
  added: []
  patterns: [Q15 FIR filtering, per-instance high-pass history, checked caller-buffer extents]
key-files:
  created:
    - docs/audio-and-playback.md
    - .planning/phases/GB-05-dmg-audio-and-stable-playback/deferred-items.md
  modified:
    - src/core/gabbaboy.c
    - include/gabbaboy/gabbaboy.h
    - tests/test_audio.c
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
key-decisions:
  - "Use the original Q15 fixed-tap FIR and a Q15 high-pass coefficient derived from the D-02 48 kHz charge-factor approximation; preserve histories per instance and clear them on reset."
  - "Reject overflowing PCM extents and count/frame overlap before guest execution; initialize the count output to zero."
patterns-established:
  - "Signal fixtures state explicit numeric limits and remain separate from perceptual and hardware evidence."
  - "Run partition tests compare exact PCM bytes and counts across whole, half, and instruction-aligned repeated budgets."
requirements-completed: [AUDIO-01, AUDIO-02]
coverage:
  - id: D1
    description: "Authored software signal references and run partitions meet declared deterministic PCM bounds."
    requirement: AUDIO-02
    verification:
      - kind: unit
        ref: "ctest --preset phase1 -R '^audio_(signal|partition|filter)$'"
        status: pass
    human_judgment: false
  - id: D2
    description: "Malformed PCM storage extents and count/frame overlap are rejected; retry preserves PCM and guest progress."
    requirement: AUDIO-02
    verification:
      - kind: unit
        ref: "ctest --preset phase1 -R '^(audio_|instance_lifecycle$|independent_instances$|run_output_capacity$)'"
        status: pass
    human_judgment: false
duration: 62 min
completed: 2026-10-08
status: complete
plan_head_before: 689a0fb53c06d022bcb684b5634515aa5b85dea0
plan_head_after: 0ce27da03f33085a48e9a570c83cc4dcb9ecb4c7
---

# Phase GB-05 Plan 04: Fixed-Point Resampling, High-Pass and Bounded PCM Summary

**48 kHz caller-owned PCM now uses per-instance Q15 FIR/high-pass state, documented signal bounds, and checked whole-instruction backpressure.**

## Performance

- **Duration:** 62 min
- **Started:** 2026-10-08T13:51:30Z
- **Completed:** 2026-10-08T14:53:49Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- Added independently authored impulse, step, 1/8-duty periodic, and alternating Nyquist vectors with declared peak, settling, and alias limits before adding the fixed-tap kernel. The tests also check a 256-frame high-pass decay and APU reset behavior.
- Added per-instance 8-tap Q15 filtering and the D-02 charge-factor approximation, with symmetric stereo output, signed rounding, s16 saturation, and history retained across calls and cleared by reset.
- Hardened `gbb_run_audio` against size multiplication overflow, pointer extent overflow, and overlapping output/count storage. Retry after output-full produces the same remaining PCM as one call with sufficient capacity.
- Documented the fixed 48 kHz interleaved s16 contract, muted legacy stepping, bounded storage, test limits, measurement identity, and the hardware/perceptual evidence boundary.

## Task Commits

1. **Task 1: Fix the original edge-resampler and high-pass contract** — `8da9392` (`feat`)
2. **Task 2: Harden public PCM capacity and explain the model** — `0ce27da` (`fix`)

The measured plan range from `689a0fb53c06d022bcb684b5634515aa5b85dea0` to `0ce27da03f33085a48e9a570c83cc4dcb9ecb4c7` contains 2 commits.

## Files Created/Modified

- `src/core/gabbaboy.c` — Per-instance fixed-point FIR/high-pass processing and checked PCM output extents.
- `include/gabbaboy/gabbaboy.h` — Caller-owned format, capacity, error, and lifetime contract.
- `tests/test_audio.c` — Signal, filter, partition, retry, overlap, and overflow cases.
- `tests/CMakeLists.txt`, `tests/expected-tests.txt` — Named CTest registration and required inventory entries.
- `docs/audio-and-playback.md` — Numeric software-model limits, measurement method, PCM contract, and evidence limits.
- `.planning/phases/GB-05-dmg-audio-and-stable-playback/deferred-items.md` — Existing out-of-scope DMA test warning record.

## Decisions Made

- Preserved the original fixed-point/no-dependency choice. The kernel uses an 8-tap Q15 FIR with coefficients `[682,2731,5461,7510,7510,5461,2731,682]`; each stereo channel then uses Q15 high-pass coefficient 32648, nearest rounding with ties away from zero, and s16 saturation.
- Kept the filter approximation and authored mathematical signals separate from channel-model, perceptual, and physical hardware evidence.
- Rejected malformed frame extents and count/frame overlap before instruction execution; the count output is initialized to zero when provided.

## Deviations from Plan

### Implemented a fixed-phase sample-domain FIR rather than a fractional-phase edge-event table

- **Found during:** Task 1 implementation.
- **Issue:** The current 48 kHz output path samples the mixed APU level at frame deadlines. The added 8-tap FIR filters this sampled stream; it does not retain sub-frame edge timestamps or generate a multi-phase edge-event table as the plan's action described.
- **Reason:** This implementation retained the existing fixed output-phase core path and introduced bounded per-frame work without a dependency. The authored periodic and Nyquist vectors pass the predeclared limits.
- **Impact:** Exact partition determinism, declared signal thresholds, and API bounds are verified. Aliasing for channel transitions occurring between output deadlines is not fully characterized; this result is not hardware or perceptual qualification. Revisit the event-time kernel if the phase's broader evidence or later measurements show this analytical floor is insufficient.
- **Files:** `src/core/gabbaboy.c`, `tests/test_audio.c`, `docs/audio-and-playback.md`.

**Total deviations:** 1 kernel-shape deviation. **Impact:** No dependency or public API change; the remaining DSP limitation is explicit and bounded by the authored test set.

## TDD Execution

- Task 1 signal cases were authored before changing the kernel and then passed after implementation; the task-level commit includes the tests and implementation together.
- Task 2's `audio_api_edges` target failed first on the overlapping-buffer assertion, then passed after the extent/overlap checks were added. The required atomic task commit contains both the test and implementation.
- The project config has `workflow.tdd_mode: false`; no format-based RED evidence record was required by the configured gate.

## Automated Results

- `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '^audio_(signal|partition|filter)$'` — passed, 3/3.
- `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '^(audio_|instance_lifecycle$|independent_instances$|run_output_capacity$)'` — passed, 9/9.
- `git diff --check` — passed.
- Signal reference digest: FNV-1a 64 `18b8e1d6fb25b7a1`; guest partition PCM digest: FNV-1a 64 `1ac7eb1fffeb7349`.
- Throughput diagnostic: `phase1` Debug build, Apple clang 21.0.0 on Darwin arm64, `audio_signal` workload (4,144 stereo frames / 66,304 fixed-tap multiply-accumulates), 3 warmups and 30 monotonic wall-time samples; median 2.268 ms, MAD 0.209 ms, range 1.861–3.333 ms. This includes process startup and fixture setup and is not an isolated kernel speed claim.
- The full preset rebuild also emitted an unchanged `-Wunsequenced` warning in `tests/test_dma.c:702`; it is recorded in `deferred-items.md` and was not changed.

## Evidence Limits

The signal vectors and CTests establish only analytical properties of this original software path and exact deterministic PCM behavior across tested partitions. They do not establish subjective sound quality, analog output behavior, SDL/device playback, or equivalence to physical DMG-CPU-B hardware. No physical or perceptual qualification was performed.

## Deferred Issues

- Replace or further characterize the sample-domain FIR if future signal evidence requires fractional sub-frame event timing.
- Existing unrelated `tests/test_dma.c:702` unsequenced modification warning; no Phase 05-04 source change is warranted.

## Next Plan Readiness

Plan 05-04 is complete within **Phase GB-05 — DMG Audio and Stable Playback**. Continue this phase with **Plan 05-05 — SDL audio device stream and ring behavior** (title from the remaining phase plan). The exact continuation command is `$gsd-execute-phase 5`. Phase 5 is not complete; after its verification, the next phase is **Phase 6 — Qualified DMG Release and Consumer Handoff**. Auto-advance remains disabled.

---
*Phase: GB-05-dmg-audio-and-stable-playback*
*Completed: 2026-10-08*

## Self-Check: PASSED

- Summary file exists at the required phase path.
- Task commits `8da9392` and `0ce27da` are ancestors of the recorded plan head.
- The plan ledger records base `689a0fb53c06d022bcb684b5634515aa5b85dea0`; the measured task range contains 2 commits and ends at `0ce27da03f33085a48e9a570c83cc4dcb9ecb4c7`.
