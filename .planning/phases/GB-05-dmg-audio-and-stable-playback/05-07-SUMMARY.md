---
phase: GB-05-dmg-audio-and-stable-playback
plan: 07
subsystem: playback
tags: [SDL3, C, PCM, DMG-CPU-B, sustained-measurement, audio-evidence]
requires:
  - phase: GB-05-dmg-audio-and-stable-playback
    provides: Bounded PCM core, SDL ring/gain/sink adapter, and lifecycle recovery from Plans 05-04 through 05-06.
provides:
  - Revision-bound 300-frame authored playback receipt with two partition checks and explicitly labeled software counters.
  - Consumer documentation, player help, and package capability metadata for the scoped DMG audio contract.
affects: [GB-06, audio-consumers, preview-packages]
actuals:
  tokens: 13411
  tasks: 2
  commits: 2
commits: 2
plan_head_before: 4fce83ae39a6b13745535b4c5b1508a1f77c4b3d
plan_head_after: 5dd62c18d83cd8392fd8ef4a8504925362a5e773
tech-stack:
  added: []
  patterns: [bounded revision-linked PCM receipt, application-counter evidence labels, package capability assertions]
key-files:
  created:
    - tests/scripts/measure-audio-playback.sh
  modified:
    - src/player/main.c
    - src/player/audio.c
    - src/player/audio.h
    - src/player/limitations.h
    - tests/scripts/verify-phase3-player.sh
    - tests/player/test_limitations.c
    - docs/audio-and-playback.md
    - docs/preview.md
    - README.md
    - .github/workflows/preview.yml
    - .planning/WINDOWS.md
key-decisions:
  - "Bind the sustained result to the committed source revision, Release build, scoped DMG model, original licensed fixture, and PCM digest."
  - "Keep SDL queued-input bytes and application PCM underflow explicitly separate from playback latency and hardware starvation."
  - "Report dummy backend and default-device availability as software/device-presence evidence only; do not claim physical hotplug or perceptual qualification."
patterns-established:
  - "The measurement route writes PCM to stdout and a bounded, machine-readable counter record to stderr."
  - "Consumer help and package metadata assert the same format, gain range, model scope, and evidence limits as the docs."
requirements-completed: [AUDIO-01, AUDIO-02, AUDIO-03, HOST-01, HOST-02]
coverage:
  - id: D1
    description: "A repeatable 300-frame authored pulse workload produces identical PCM across frame and 792-half-dot partitions with revision, digest, queue bounds, and precisely named application counters."
    requirement: AUDIO-03
    verification:
      - kind: integration
        ref: "bash tests/scripts/measure-audio-playback.sh at 5dd62c18d83cd8392fd8ef4a8504925362a5e773"
        status: pass
      - kind: unit
        ref: "CTest phase1 core inventory (169/169)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Player help, preview package metadata, and consumer docs describe the scoped DMG model, 48 kHz s16 stereo format, host gain, lifecycle rules, and evidence limits."
    requirement: AUDIO-02
    verification:
      - kind: integration
        ref: "bash tests/scripts/verify-phase3-player.sh at 5dd62c18d83cd8392fd8ef4a8504925362a5e773 (48/48; package help, metadata, dummy smoke, extracted-package smoke)"
        status: pass
    human_judgment: false
duration: 32min
completed: 2026-10-08
status: complete
---

# Phase GB-05 Plan 07: Sustained Playback Evidence and Consumer Contract Summary

**A committed-revision playback receipt and aligned player/package documentation now describe the bounded DMG audio path and its evidence limits.**

## Performance

- **Duration:** approximately 32 minutes; the exact plan start timestamp was not retained through continuation.
- **Completed:** 2026-10-08T16:32:10Z
- **Tasks:** 2
- **Files changed:** 12

## Accomplishments

- Added a bounded, fixed-duration measurement route using the original pulse-control workload and MIT-licensed visible demo fixture. It records revision, Release build, model, workload and fixture digests, PCM digest/count, ring bounds/high-water, application underflow, producer backpressure, intentional host discards, and SDL queued-input bytes.
- Added player `--help` and F1 help text for the PCM format, host gain, unavailable-sink behavior, recovery rules, and the DMG model's limits. Updated README, preview/audio contracts, player limitations, package assertions, and Linux/macOS preview capability metadata.
- Kept the software APU and player claims scoped to the deterministic DMG-CPU-B model. CGB/VIN, revision equivalence, physical-device hotplug/output, and listening quality remain unqualified.

## Evidence and Limits

- At committed source revision `5dd62c18d83cd8392fd8ef4a8504925362a5e773`, the full core inventory passed **169/169** and the packaged-player verifier passed **48/48**. The player package SHA-256 was `e649db2e42a9cb2db0d9c6bb75dfe8f4376c06fab19c04c7375716565a7cd8e2`; built and extracted-package smoke passed, including dummy SDL open/stream/close/recovery.
- The sustained Release `macos-arm64` run passed for frame and 792-half-dot partitions. Both produced 241,095 signed 16-bit little-endian interleaved stereo frames with PCM SHA-256 `15cd3f831bcc2c6df652ab1da2228ff06c107b7b026cb111e63156d01895a47a`. The MIT fixture digest was `38afb54b40f4b6612906c7a68e367199d8bff135508a39d7acdc996bf3d86530`.
- Each partition ran 300 video frames (42,134,400 target half-dots; 42,134,424 elapsed, within the declared 40-half-dot bound). Ring target/ceiling/high-water were 1,606/3,214/3,214 frames. Both reported 1,024 application PCM underflow frames in one callback event, 2,503 intentionally discarded host frames, and zero SDL queued-input bytes; producer backpressure was 3,576 events for frame partitioning and 3,504 for 792-half-dot partitioning. The default audio device was unavailable.
- The receipt reports a clean source state for its measured code, test, documentation, README, and workflow paths. Pre-existing unrelated `.planning` scratch was preserved and excluded from the task commits.
- Dummy and software counters do not measure playback latency or prove hardware starvation. This run does not establish physical hotplug, analog output, hardware/revision equivalence, or perceptual quality.

## Task Commits

1. **05-07-01: Record bounded sustained playback evidence** — `bfbb3da` (`feat`)
2. **05-07-02: Publish consumer and lifecycle limits** — `5dd62c1` (`feat`)

The plan commit ledger measured two task commits between `plan_head_before` and `plan_head_after`; the state/summary metadata commit is separate.

## Files Created/Modified

- `tests/scripts/measure-audio-playback.sh` — bounded dummy-backend workload, receipt validation, and partition digest comparison.
- `src/player/main.c`, `src/player/audio.c`, `src/player/audio.h` — measurement route, status/help, and precise ring/underflow counters.
- `src/player/limitations.h`, `tests/player/test_limitations.c` — aligned player capability statement and assertion.
- `tests/scripts/verify-phase3-player.sh` — player/package help and capability metadata checks.
- `docs/audio-and-playback.md`, `docs/preview.md`, `README.md` — consumer format, controls, lifecycle, and scope contract.
- `.github/workflows/preview.yml` — package capability limits match the built Linux core and optional macOS player.
- `.planning/WINDOWS.md` — recorded the documentation/metadata scope correction.

## Decisions Made

- Preserve exact application-level labels: SDL queued-input bytes are not latency, and application PCM underflow is not hardware starvation.
- Keep device availability separate from the forced dummy-backend acceptance result and from physical/perceptual evidence.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical measurement interface] Added adapter counters required by the receipt.**
- **Found during:** Task 1
- **Issue:** The plan's file list omitted `audio.c` and `audio.h`, which own the ring target/ceiling and callback underflow event state needed for accurately labeled receipt fields.
- **Fix:** Added bounded getters/counter reporting in the existing player adapter and included the files in the task commit.
- **Files modified:** `src/player/audio.c`, `src/player/audio.h`
- **Verification:** Full core/player verifier and sustained measurement passed at the committed revision.
- **Committed in:** `bfbb3da`

**2. [Rule 2 - Stale consumer capability claims] Updated package and player limitations omitted from the plan file list.**
- **Found during:** Task 2
- **Issue:** The preview workflow and player limitations helper still described audio as absent, which would contradict the new player and consumer contract.
- **Fix:** Updated Linux/macOS capability sidecars, the shared limitations text and its test, and recorded the scope adjustment in the broken-windows ledger.
- **Files modified:** `.github/workflows/preview.yml`, `src/player/limitations.h`, `tests/player/test_limitations.c`, `.planning/WINDOWS.md`
- **Verification:** Full core/player verifier passed 169/169 and 48/48 at the committed revision; package metadata and help assertions passed.
- **Committed in:** `5dd62c1`

**Total deviations:** 2 auto-fixed Rule 2 adjustments. Both preserve receipt correctness and consumer claim accuracy.

## Issues Encountered

- The sandboxed macOS preference directory initially prevented the player verifier from acquiring its battery-session lock. Re-running with an isolated temporary `HOME` and `CFFIXED_USER_HOME` succeeded; no product change was needed.
- One earlier root-pin guard invocation had a typo in the failure-only diagnostic string. Its success-path root equality check passed; the issue was caught, reported to the orchestrator, and all remaining writes and commits used the supplied guard verbatim. No operation was performed from another checkout.

## User Setup Required

None.

## Next Phase Readiness

Plan 05-07 execution is complete within **Phase 5 of 6**. Phase 5 remains active pending goal verification; the next command is `$gsd-verify-work 5`. Only after Phase 5 verification should work move to **Phase 6 — Qualified DMG Release and Consumer Handoff**. No Phase 6 work was started.

---
*Phase: GB-05-dmg-audio-and-stable-playback*
*Completed: 2026-10-08*

## Self-Check: PASSED

- `05-07-SUMMARY.md` exists at the plan output path.
- Task commits `bfbb3da` and `5dd62c1` are ancestors of the current HEAD.
- The persisted plan ledger measured exactly two task commits from `4fce83ae39a6b13745535b4c5b1508a1f77c4b3d` through `5dd62c18d83cd8392fd8ef4a8504925362a5e773`.
