---
phase: GB-05-dmg-audio-and-stable-playback
plan: 04
subsystem: audio
tags: [C17, DMG, PCM, fixed-point, edge-resampler, high-pass]
requires:
  - phase: GB-05-dmg-audio-and-stable-playback
    provides: Four-channel DMG APU mixer and caller-owned 48 kHz PCM path from Plans 05-01 through 05-03.
provides:
  - Authored impulse, step, periodic, alias, partition, and HPF software-model checks.
  - Per-instance fixed-point eight-phase event-response ring and DMG-style high-pass state with reset semantics.
  - Overflow/overlap validation and public caller-owned PCM/backpressure contract.
affects: [GB-05-05, audio, player]
actuals:
  tokens: 8395
  tasks: 2
  commits: 4
tech-stack:
  added: []
  patterns: [Q15 polyphase event response, per-instance high-pass history, checked caller-buffer extents]
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
  - "Detect mixed-level changes at emulated half-dot resolution, map each event to one of eight output phases, and accumulate a fixed 16-frame Q15 step response per instance; retain the D-02 48 kHz HPF approximation."
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
plan_head_after: 1287ca131936a230617f0e37f159c3d825d4b3f6
---

# Phase GB-05 Plan 04: Fixed-Point Resampling, High-Pass and Bounded PCM Summary

**48 kHz caller-owned PCM uses a bounded eight-phase event-response ring, per-instance high-pass state, and checked whole-instruction backpressure.**

## Performance

- **Duration:** 62 min
- **Started:** 2026-10-08T13:51:30Z
- **Completed:** 2026-10-08T14:53:49Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments

- Added independently authored impulse, step, 1/8-duty periodic, and alternating Nyquist vectors with declared peak, settling, and alias limits before adding the fixed-tap kernel. The tests also check a 256-frame high-pass decay and APU reset behavior.
- Replaced the sample-domain FIR with mixed-level event detection at each emulated half-dot, an eight-phase/16-frame Q15 response table, bounded ring accumulation, and the D-02 charge-factor approximation. Event and HPF histories are per instance and clear on reset.
- Added a fractional-phase vector that injects the same level edge at phases 0, 3/8, and 7/8 and verifies distinct phase-dependent output; the guest partition test still compares exact PCM bytes/counts.
- Hardened `gbb_run_audio` against size multiplication overflow, pointer extent overflow, and overlapping output/count storage. Retry after output-full produces the same remaining PCM as one call with sufficient capacity.
- Documented the fixed 48 kHz interleaved s16 contract, muted legacy stepping, bounded storage, test limits, measurement identity, and the hardware/perceptual evidence boundary.

## Task Commits

1. **Task 1: Fix the original edge-resampler and high-pass contract** — `8da9392` (`feat`)
2. **Task 2: Harden public PCM capacity and explain the model** — `0ce27da` (`fix`)
3. **Correction: Replace sampled FIR with phase-aware edge response** — `1287ca1` (`fix`)

The measured plan range from `689a0fb53c06d022bcb684b5634515aa5b85dea0` to `1287ca131936a230617f0e37f159c3d825d4b3f6` contains 4 commits, including the summary commit from the original execution and this correction.

## Files Created/Modified

- `src/core/gabbaboy.c` — Per-instance fixed-point polyphase event processing, high-pass filtering, and checked PCM output extents.
- `include/gabbaboy/gabbaboy.h` — Caller-owned format, capacity, error, and lifetime contract.
- `tests/test_audio.c` — Signal, fractional-phase, filter, partition, retry, overlap, and overflow cases.
- `tests/CMakeLists.txt`, `tests/expected-tests.txt` — Named CTest registration and required inventory entries.
- `docs/audio-and-playback.md` — Numeric software-model limits, measurement method, PCM contract, and evidence limits.
- `.planning/phases/GB-05-dmg-audio-and-stable-playback/deferred-items.md` — Existing out-of-scope DMA test warning record.

## Decisions Made

- Preserved the original fixed-point/no-dependency choice. Each detected mixer edge deposits a bounded 16-tap Q15 correction selected from eight fixed phase rows; each stereo channel then uses Q15 high-pass coefficient 32648, nearest rounding with ties away from zero, and s16 saturation.
- Kept the filter approximation and authored mathematical signals separate from channel-model, perceptual, and physical hardware evidence.
- Rejected malformed frame extents and count/frame overlap before instruction execution; the count output is initialized to zero when provided.

## Deviations from Plan

None — the follow-up correction replaced the sample-domain FIR with the planned bounded fixed-point edge-event/polyphase path. Signal coverage remains limited to authored mathematical references and does not characterize every signal frequency or establish perceptual/hardware quality.

## TDD Execution

- Task 1 signal cases were authored before the initial kernel change. The fractional-phase correction adds a separate explicit edge-phase vector; signal, phase, and partition cases pass after the correction.
- Task 2's `audio_api_edges` target failed first on the overlapping-buffer assertion, then passed after the extent/overlap checks were added. The required atomic task commit contains both the test and implementation.
- The project config has `workflow.tdd_mode: false`; no format-based RED evidence record was required by the configured gate.

## Automated Results

- `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '^audio_(signal|partition|filter)$'` — passed, 3/3.
- `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '^(audio_|instance_lifecycle$|independent_instances$|run_output_capacity$)'` — passed, 10/10.
- `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` — passed, 169/169.
- `git diff --check` — passed.
- Signal reference digest: FNV-1a 64 `202a3e9f96f3cead`; guest partition PCM digest: FNV-1a 64 `b5bb127cdda6a035`.
- The former FIR timing sample is retired because its workload no longer represents this kernel. Structural bounded-work evidence is at most 16 ring updates per changed mix/channel and one ring-slot consumption per output frame; no isolated timing claim is made.
- The full preset rebuild also emitted an unchanged `-Wunsequenced` warning in `tests/test_dma.c:702`; it is recorded in `deferred-items.md` and was not changed.

## Evidence Limits

The signal vectors and CTests establish only analytical properties of this original software path and exact deterministic PCM behavior across tested partitions. They do not establish subjective sound quality, analog output behavior, SDL/device playback, or equivalence to physical DMG-CPU-B hardware. No physical or perceptual qualification was performed.

## Deferred Issues

- Characterize a broader set of passband/alias frequencies before making claims beyond the authored signal limits.
- Existing unrelated `tests/test_dma.c:702` unsequenced modification warning; no Phase 05-04 source change is warranted.

## Next Plan Readiness

Plan 05-04 is complete within **Phase GB-05 — DMG Audio and Stable Playback**. Continue this phase with **Plan 05-05 — SDL audio device stream and ring behavior** (title from the remaining phase plan). The exact continuation command is `$gsd-execute-phase 5`. Phase 5 is not complete; after its verification, the next phase is **Phase 6 — Qualified DMG Release and Consumer Handoff**. Auto-advance remains disabled.

---
*Phase: GB-05-dmg-audio-and-stable-playback*
*Completed: 2026-10-08*

## Self-Check: PASSED

- Summary file exists at the required phase path.
- Task commits `8da9392`, `0ce27da`, and correction `1287ca1` are ancestors of the recorded plan head.
- The plan ledger measures 4 commits from `689a0fb53c06d022bcb684b5634515aa5b85dea0` through `1287ca131936a230617f0e37f159c3d825d4b3f6`.
- `.planning/STATE.md` reflects the 10/10 audio/API inventory and updated event-kernel evidence.
