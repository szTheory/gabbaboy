---
phase: GB-05-dmg-audio-and-stable-playback
plan: "05"
subsystem: audio
tags: [C17, SDL3, SPSC, PCM, playback]
requires:
  - phase: GB-05-dmg-audio-and-stable-playback
    provides: Caller-owned 48 kHz PCM and the bounded DMG edge-event audio model.
provides:
  - Fixed-capacity lock-free SPSC transport with exact variable-byte callback service.
  - Distinct PCM underflow, producer backpressure, high-water, sink failure, and unavailable-sink discard counters.
  - Host gain controls and paced queue-capacity integration in the macOS player.
affects: [GB-05-06, audio, playback]
actuals:
  tokens: 6966
  tasks: 2
  commits: 2
tech-stack:
  added: []
  patterns: [fixed-chunk SDL callback, acquire-release SPSC publication, callback-owned partial-frame carry]
key-files:
  created: [src/player/audio.h, tests/player/test_audio.c]
  modified: [src/player/audio.c, src/player/main.c, tests/player/CMakeLists.txt, tests/player/expected-tests.txt]
key-decisions:
  - "Service SDL byte requests exactly and carry partial s16-stereo frame bytes across callbacks, avoiding over-queueing for irregular requests."
  - "Use bracket keys for host-only gain from 0% to 200%; never write guest APU volume registers."
  - "On unavailable sink, discard and count PCM immediately while continuing host-paced guest execution."
patterns-established:
  - "SDL callback work uses 1024-byte stack chunks and never runs guest code, allocates, logs, or locks."
  - "All callback-visible atomics are checked for lock-free support before opening a sink."
requirements-completed: [AUDIO-03, AUDIO-02]
coverage:
  - id: D1
    description: "The callback preserves ordered PCM across wrap and concurrent producer/consumer traffic, honors partial and large byte requests, and zero-fills shortage."
    requirement: AUDIO-03
    verification:
      - kind: unit
        ref: "player_audio_ring, player_audio_concurrent"
        status: pass
      - kind: integration
        ref: "bash tests/scripts/verify-phase3-player.sh (42/42 player tests; extracted package smoke)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Paced PCM publication, bounded host gain, SDL dummy-device open/close, and counted no-queue sink policy are covered."
    requirement: AUDIO-03
    verification:
      - kind: unit
        ref: "player_audio_pacing, player_audio_gain, player_audio_unavailable"
        status: pass
      - kind: integration
        ref: "bash tests/scripts/verify-phase3-player.sh (42/42 player tests; extracted package smoke)"
        status: pass
    human_judgment: false
duration: 12min
completed: 2026-10-08
status: complete
plan_head_before: 35430e571e38bc02781723b4032d243670131381
plan_head_after: a07a4b27a3047f8bd5b3bc2b71c60a3b44f6643e
---

# Phase 5 Plan 05 Summary: SDL Audio Transport and Stable Playback

**SDL playback now consumes exact requested bytes from a bounded SPSC ring, applies host gain, and counts PCM discarded when no device is available.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-10-08T15:10:03Z
- **Completed:** 2026-10-08T15:21:48Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Added the narrow player audio adapter interface and a 4096-frame SPSC storage ring with a 3214-frame software limit, approximately four video frames at 48 kHz.
- The SDL callback copies only acquire-published frames, transfers through fixed 1024-byte chunks, retains partially consumed four-byte stereo frames across callback requests, zero-fills shortages, and does not allocate, lock, log, or execute guest work.
- Added lock-free checks for callback-visible atomic widths and quiescent callback teardown before stream destruction.
- Kept queue high-water, whole-frame application underflow, producer backpressure, SDL sink write failures, no-device discarded frames, and queued input bytes distinct.
- Connected producer capacity to `gbb_run_audio`, so guest work stops at ring backpressure. A missing device discards PCM immediately and counts it while guest time remains host-paced.
- Added 100% default host gain with bracket-key controls from 0% through 200%; gain does not touch APU registers. Help and the window title identify the controls and sink status.
- Added registered coverage for `player_audio_ring`, `player_audio_concurrent`, `player_audio_pacing`, `player_audio_gain`, and `player_audio_unavailable`. The concurrency case transfers 100,000 ordered frames, and the available-device case opens SDL's dummy sink.

## Evidence and Limits

- `player_audio_ring`, `player_audio_concurrent`, `player_audio_pacing`, `player_audio_gain`, and `player_audio_unavailable` — 5/5 passed.
- The packaged-player verifier — passed twice, 42/42 player tests each time, including player smoke, packaged continuation, and extracted-package smoke for the pinned SDL 3.4.18 build.
- Final verifier candidate archive SHA-256: `3069b52d3193b30bb825658c6bafd846a3085e0d7d6d2194d3ed7c980340dc5f`. This was a local candidate built while the working tree contained the Plan 05-05 integration change; it is not an exact-head release receipt.
- The callback test requests the positive `int` boundary and verifies that a rejected sink write stops further chunk processing. No physical DMG output or perceptual listening check was performed; no sound-quality or hardware-equivalence claim is made.

## Task Commits

1. **05-05-01: Prove bounded SPSC publication and callback shortage** — `e2ce036` (`feat`)
2. **05-05-02: Enforce paced publication, gain and unavailable-sink policy** — `a07a4b2` (`feat`)

## Files Created/Modified

- `src/player/audio.h` — Narrow player adapter API for capacity, publication, gain, and separate sink counters.
- `src/player/audio.c` — Fixed-chunk callback, bounded SPSC ring, partial-byte carry, saturating counters, gain, dummy-device support, and quiescent teardown.
- `src/player/main.c` — Ring-capacity pacing, discoverable gain keys, accurate unavailable-sink status, and audio smoke metrics.
- `tests/player/test_audio.c` — Irregular and boundary requests, wrap, underflow, concurrent sequence stress, backpressure, gain, no-device discard, and SDL dummy open/close.
- `tests/player/CMakeLists.txt`, `tests/player/expected-tests.txt` — Five required named player audio cases.

## Decisions Made

- The callback writes exactly SDL's requested byte count. Callback-owned partial-frame bytes carry to the next request, so repeated non-frame-aligned requests cannot accumulate extra queued input.
- Unavailable hardware is a supported sink state. The producer still requests bounded PCM, then discards and counts it without retaining stale frames or changing the host pacing source.
- SDL queued bytes are reported only as queued input bytes; they are not conflated with ring occupancy or device output latency.

## Deviations from Plan

### Auto-fixed Test Issues

**1. [Rule 1 - Test fixture] Corrected audio test helper and byte-count expectations.**
- **Found during:** Tasks 1 and 2.
- **Issue:** The first compile exposed a helper name colliding with `player_audio_gain`; early callback assertions also treated irregular requests as whole-frame requests, and the wrap comparison included uninitialized frames.
- **Fix:** Renamed the test helper, asserted exact byte carry/zero-fill behavior, and limited the wrap comparison to initialized frames.
- **Files modified:** `tests/player/test_audio.c`.
- **Verification:** All five named cases and both packaged-player verifier runs passed.
- **Committed in:** `e2ce036`.

**TDD execution note:** The project config had `workflow.tdd_mode: false`. The named tests were written before the adapter implementation, but the initial failed build was a helper-name compilation error rather than a behavior assertion; no classifier-backed RED evidence was captured. This procedural gap is recorded explicitly; all final test and package inventories passed.

**Total deviations:** 1 test-fixture correction and the noted RED-evidence gap. **Impact:** No product scope change; final behavior is covered by deterministic player tests.

## Issues Encountered

The first verifier invocation inside the workspace sandbox could not create the smoke test's temporary battery lock under the user's normal application-data directory. Rerunning the same required command with the necessary external test-file access passed; no source change was needed.

## Evidence Limits

These checks establish the SDL adapter's deterministic software behavior and the pinned SDL dummy-device lifecycle. They do not establish physical DMG audio output, subjective quality, analog filtering, or device-specific latency.

## Next Plan Readiness

Plan 05-05 is complete within **Phase GB-05 — DMG Audio and Stable Playback**. Continue with **Plan 05-06 — input ownership and lifecycle recovery**, whose transition matrix covers focus/controller events, pause/reset/replacement, and audio-device loss. The exact continuation command is `$gsd-execute-phase 5`. After Phase 5 verification, the next phase is **Phase 6 — Qualified DMG Release and Consumer Handoff**. Auto-advance remains disabled.

---
*Phase: GB-05-dmg-audio-and-stable-playback*
*Completed: 2026-10-08*

## Self-Check: PASSED

- Summary file exists at the required phase path.
- Task commits `e2ce036` and `a07a4b2` are ancestors of the plan head.
- The persisted plan-base record was unavailable because `.git` is read-only in this runtime; the measured base is the execution-start HEAD `35430e571e38bc02781723b4032d243670131381`, and its range contains two commits.
