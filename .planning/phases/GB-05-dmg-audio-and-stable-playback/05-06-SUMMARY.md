---
phase: GB-05-dmg-audio-and-stable-playback
plan: "06"
subsystem: host-input-audio
tags: [C17, SDL3, gamepad, focus, PCM, lifecycle]
requires:
  - phase: GB-03-visible-interactive-dmg
    provides: SDL event loop and queued focus-release policy.
  - phase: GB-04-mbc1-and-safe-battery-continuation
    provides: Transactional battery save and ROM replacement ordering.
  - phase: GB-05-dmg-audio-and-stable-playback
    provides: Bounded PCM adapter and guest-side APU output.
provides:
  - Fixed-capacity, source-owned keyboard/gamepad button contributions with neutral reconnect and deferred release retry.
  - Quiescent host PCM clearing across pause, focus, reset, successful replacement, and audio-device transitions.
  - A pinned SDL3 dummy-backend package lane that verifies software open/stream/close/recovery.
affects: [GB-05-07, GB-06, input, playback, session-lifecycle]
actuals:
  tokens: 14303
  tasks: 3
  commits: 6
commits: 6
plan_head_before: 714d2137aac0464a55ad4bbbe3a10882825ad596
plan_head_after: af438212384028307c7de3d3b3868258dae7c81a
tech-stack:
  added: []
  patterns: [bounded source-owned input, commit-after-queue-admission, callback-quiescent audio flush, SDL default-device recovery]
key-files:
  created:
    - .planning/phases/GB-05-dmg-audio-and-stable-playback/05-06-01-red-evidence.json
    - .planning/phases/GB-05-dmg-audio-and-stable-playback/05-06-02-red-evidence.json
    - .planning/phases/GB-05-dmg-audio-and-stable-playback/05-06-03-red-evidence.json
  modified:
    - src/player/input.h
    - src/player/input.c
    - src/player/audio.h
    - src/player/audio.c
    - src/player/main.c
    - tests/player/test_input.c
    - tests/player/test_audio.c
    - tests/player/CMakeLists.txt
    - tests/player/expected-tests.txt
    - tests/scripts/verify-phase3-player.sh
    - .planning/WINDOWS.md
key-decisions:
  - "Keep per-controller state keyed by SDL_JoystickID in a fixed four-source table; aggregate contributions before timestamped guest queue admission."
  - "Clear callback-owned and SDL-queued host PCM only after callback quiescence, preserving guest APU history on pause and ordering reset/replacement after battery transitions."
  - "Treat dummy-backend and injected SDL events as software-path evidence only; no physical hotplug or audible-quality result is claimed."
patterns-established:
  - "Host source state changes only after guest queue admission succeeds; failed releases remain pending for bounded retry."
  - "SDL stream callbacks are paused/locked before ring, partial-frame, and stream queue state is counted and cleared."
requirements-completed: [HOST-01, HOST-02, AUDIO-03]
coverage:
  - id: D1
    description: "Keyboard and multiple gamepads contribute independently; disconnect and focus release preserve shared holds, retry full queues, and reconnect neutral."
    requirement: HOST-01
    verification:
      - kind: unit
        ref: "player_input_sources, player_input_reconnect, player_input_focus_audio"
        status: pass
      - kind: integration
        ref: "bash tests/scripts/verify-phase3-player.sh (48/48 player tests at af438212)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Pause, focus, reset, successful replacement, and device recovery clear stale host PCM while retaining save ordering and guest clock behavior."
    requirement: HOST-02
    verification:
      - kind: unit
        ref: "player_audio_lifecycle, player_audio_device, player_audio_replacement"
        status: pass
      - kind: integration
        ref: "bash tests/scripts/verify-phase3-player.sh (48/48 player tests; dummy backend receipt; extracted package smoke)"
        status: pass
    human_judgment: false
duration: 25min
completed: 2026-10-08
status: complete
---

# Phase 5 Plan 06 Summary: Input Ownership and Lifecycle Recovery

**Per-source input ownership and callback-quiescent audio clearing now keep host state clean across focus, controller, session, and device transitions.**

## Performance

- **Duration:** 25 min
- **Started:** 2026-10-08T15:35:11Z
- **Completed:** 2026-10-08T16:00:39Z
- **Tasks:** 3
- **Files changed:** 14 (10 source/test files, three RED evidence records, and the broken-windows ledger)

## Accomplishments

- Added bounded source-owned keyboard and gamepad button contributions keyed by stable SDL joystick IDs. Disconnect releases only that controller's contribution, overlapping holds remain active, and a reused ID begins neutral.
- Preserved focus-release retry when the guest event queue is full and kept intentional pause separate from focus pause. Focus regain re-anchors host pacing without changing guest timing.
- Added a lifecycle transition table and quiescent audio clear that counts and discards ring frames, partial callback bytes, and SDL stream bytes. Reset and replacement keep the existing battery transaction order; failed transitions leave the active session's PCM intact.
- Added deterministic input/audio transition cases and made the pinned macOS player verifier force SDL's dummy backend before initialization. The built-player smoke confirms software open, stream, close, and recovery.

## Evidence and Limits

- Task 1 `player_input_sources` RED evidence was captured and accepted; its named case passed after implementation. The prior input/focus inventory passed 3/3.
- Task 2 `player_input_reconnect` and `player_input_focus_audio` RED evidence was accepted; the input inventory passed 6/6. The reconnect fixture exercises ID reuse, equal-timestamp ordering, and full-queue release retry against a loaded demo ROM.
- Task 3 `player_audio_lifecycle`, `player_audio_device`, and `player_audio_replacement` RED evidence was accepted; the audio inventory passed 8/8.
- Each task's required `bash tests/scripts/verify-phase3-player.sh` verifier passed: 42/42 after Task 1, 45/45 after Task 2, and 48/48 after Task 3. The final committed-revision run reported `source_revision=af438212384028307c7de3d3b3868258dae7c81a`, package SHA-256 `92f9e19a908f0f6603e0ac74da4d1112dead37ec7153d48d0e119e515e79969b`, and `audio dummy smoke passed: driver=dummy open/stream/close/recovery`.
- Injected SDL device events and the dummy backend establish deterministic software behavior. They do not establish physical device hotplug, hardware output, or audible quality.

## Task Commits

1. **05-06-01: Track keyboard and controller button ownership** — `fa7c4bd` (RED test/evidence), `703afd3` (SDL event wiring)
2. **05-06-02: Prove source-owned input recovery** — `c4da7e7` (RED test/evidence), `b6ea7d7` (focus and retry behavior)
3. **05-06-03: Enforce clean audio and battery transition ordering** — `c68014a` (RED test/evidence), `af43821` (audio transitions and dummy verifier)

The final summary/state/roadmap/requirements metadata commit is separate and is reported by the executor completion record.

## Files Created/Modified

- `src/player/input.h`, `src/player/input.c` — bounded source contributions, neutral reconnect, focus release retry, and aggregate guest input.
- `src/player/audio.h`, `src/player/audio.c` — transition flush/count API, SDL stream recovery, and callback-quiescent ring/stream clearing.
- `src/player/main.c` — gamepad event wiring, lifecycle ordering, audio event recovery, and dummy-backend smoke route.
- `tests/player/test_input.c`, `tests/player/test_audio.c` — input ownership, reconnect, focus, PCM lifecycle, device, and replacement cases.
- `tests/player/CMakeLists.txt`, `tests/player/expected-tests.txt` — fixed inventory registration for six input and eight audio cases.
- `tests/scripts/verify-phase3-player.sh` — force the SDL dummy backend and fail unless its smoke receipt is present.
- Three `05-06-0N-red-evidence.json` files — classifier-backed RED records for each TDD task.
- `.planning/WINDOWS.md` — records the three documented deviations in the cross-phase ledger.

## Decisions Made

- Keyboard and gamepad ownership is represented as a small fixed source table; guest state is the union of live source contributions.
- SDL default-device migration is preferred; if the stream is no longer active, the adapter closes and reopens it while keeping guest execution on its existing host-paced timeline.
- The dummy backend is a required software-path check, with physical hotplug and subjective listening kept as explicit evidence gaps.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test fixture] Loaded the demo ROM in the reconnect queue-full case.**
- **Found during:** Task 2.
- **Issue:** The initial empty-machine fixture did not advance a guest timeline, so it could not exercise deferred release retry as intended.
- **Fix:** Load the authored demo ROM before filling and draining the input queue.
- **Files modified:** `tests/player/test_input.c`.
- **Verification:** `player_input_reconnect`, the 6/6 input inventory, and the 48/48 final player inventory passed.
- **Committed in:** `c4da7e7` / `b6ea7d7`.

**2. [Rule 2 - Required interface] Added audio adapter declarations.**
- **Found during:** Task 3.
- **Issue:** The plan's task file list omitted the adapter header needed by the new clear-count and SDL device-event behavior consumed by both `main.c` and tests.
- **Fix:** Declared the transition functions and test-only device-drop hook in the existing internal adapter header.
- **Files modified:** `src/player/audio.h`.
- **Verification:** Audio inventory passed 8/8 and the final package verifier passed 48/48.
- **Committed in:** `c68014a` / `af43821`.

### Execution Deviations

- Task 1's input behavior assertion failed before implementation and the RED evidence classifier accepted the result, but `src/player/input.c` was staged in the same commit as the RED test. `main.c` event wiring followed in the next commit; the product changes and later tests passed.
- The prescribed `.git` plan-head ledger could not be written because this runtime exposes `.git` read-only. The execution-start HEAD was captured as `714d2137aac0464a55ad4bbbe3a10882825ad596`; `git rev-list --count` measured six task commits through `af438212384028307c7de3d3b3868258dae7c81a`.

**Total deviations:** 2 auto-fixed issues and 2 execution/plan-file deviations. **Impact:** No guest clock or battery contract changed; the additional header is the existing internal interface required to use the new adapter functions.

## Issues Encountered

- The first sandboxed full player verifier could not create its synthetic battery lock in the SDL app-data location. The same required verifier passed with approved filesystem access; a post-commit rerun also passed and bound its package receipt to `af438212`.
- The full rebuild emitted the pre-existing `-Wunsequenced` warning in `tests/test_dma.c:702`; that unrelated warning is already recorded in the phase deferred-items list and was not changed here.

## User Setup Required

None - no external service or credential configuration is required.

## Next Plan Readiness

Plan 05-06 is complete within **Phase GB-05 — DMG Audio and Stable Playback**. Phase 5 remains active; continue with **Plan 05-07 — sustained queue evidence and consumer documentation** using `$gsd-execute-phase 5`. After Phase 5 verification, the next phase is **Phase 6 — Qualified DMG Release and Consumer Handoff**. Auto-advance remains disabled.

---
*Phase: GB-05-dmg-audio-and-stable-playback*
*Completed: 2026-10-08*

## Self-Check: PASSED

- Summary file exists at the required phase path.
- All six measured task commits are ancestors of the recorded plan head.
- The self-check verified task commits `fa7c4bd`, `703afd3`, `c4da7e7`, `b6ea7d7`, `c68014a`, and `af43821`.
