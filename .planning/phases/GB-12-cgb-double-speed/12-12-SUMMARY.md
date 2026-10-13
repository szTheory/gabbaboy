---
phase: 12-cgb-double-speed
plan: 12
subsystem: testing
tags: [cgb, double-speed, player, cmake, installed-consumers]
requires:
  - phase: GB-12
    provides: CGB KEY1/STOP speed switching, the original speed.gb guest, and pinned frame/audio observations
provides:
  - CGB player speed smoke with wrong-digest and PPU-follows-CPU controls
  - D-41 double-speed capability claims enforced across player documentation and help surfaces
  - Installed C and C++ partitioned speed guests with unarmed-twin negative controls and no ABI expansion
affects: [GB-12-13, CGB-06, player, installed-consumers]
actuals:
  tokens: 8518
  tasks: 3
  commits: 3
plan_head_before: 6f2590f28f3e02928a1c162b2237961248272841
plan_head_after: 4ed085b14b84249f00c06f1823b073eec8a4230d
tech-stack:
  added: []
  patterns:
    - Public player smoke pins the RGB output and title token while generated mutants exercise sensitivity.
    - Installed consumers build bounded inline ROM guests and use only the shipped public API.
key-files:
  created: []
  modified:
    - tests/player/cgb_smoke.cmake
    - tests/player/CMakeLists.txt
    - tests/player/expected-tests.txt
    - src/player/limitations.h
    - tests/player/test_limitations.c
    - README.md
    - .github/workflows/preview.yml
    - src/player/main.c
    - tests/consumers/c/main.c
    - tests/consumers/cpp/main.cpp
key-decisions:
  - Use gbb_frame_info.generation from gbb_copy_frame_rgb555 because gbb_info has no frame-generation field; preserve the public ABI.
  - Continue bounded public runs after HALTED_IDLE until the first completed frame, still stopping within two frame durations.
  - Treat the installed-consumer task as test-only coverage for existing behavior; do not manufacture a TDD RED failure while global TDD mode is disabled.
requirements-completed: [CGB-06]
coverage:
  - id: GB-12-12-PLAYER-SPEED
    description: The real CGB player renders speed.gb to the pinned RGBA digest and title token, while wrong-digest and PPU-follows-CPU controls are detected.
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: e2e
        ref: player_cgb_speed_smoke
        status: pass
      - kind: integration
        ref: player_cgb_speed_smoke_wrong_sha
        status: pass
      - kind: integration
        ref: player_cgb_speed_smoke_mutant_ppu_follows_cpu
        status: pass
  - id: GB-12-12-CLAIMS
    description: Player limitations, README, preview package metadata, help, and their expected text consistently state that CGB double speed is implemented while mode-3 timing and HDMA remain unclaimed.
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: unit
        ref: player_limitations
        status: pass
      - kind: integration
        ref: player_claims_agree
        status: pass
      - kind: integration
        ref: player_claims_agree_mutated
        status: pass
  - id: GB-12-12-INSTALLED-CONSUMERS
    description: Relocated installed C and C++ consumers exercise an armed switch in bounded gbb_run partitions, reject unarmed twins, and preserve the existing public symbol set.
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: integration
        ref: installed_consumer_c
        status: pass
      - kind: integration
        ref: installed_consumer_cpp
        status: pass
      - kind: integration
        ref: cgb_consumer_symbol_coverage
        status: pass
---

# Phase GB-12 Plan 12: CGB Speed Player and Consumers Summary

**The player, public claims, and relocated C/C++ consumers now demonstrate CGB double-speed behavior without changing the core or public ABI.**

## Performance

- **Duration:** 14 min
- **Started:** 2026-10-13T23:28:27Z
- **Completed:** 2026-10-13T23:42:32Z
- **Tasks:** 3
- **Files modified:** 10

## Accomplishments

- Added a real-player `--model cgb --smoke-colour` check for `fixtures/cgb-speed/speed.gb`, pinning RGBA SHA-256 `b53366fee4959a4220b6380816c20b1f2f74ba4ed0608adda0e3afc34c4a13e7` and the `CGB` title token. The speed check ignores colour-attribute diversity. A wrong SHA and a generated M1 PPU-follows-CPU core both fail their smoke controls.
- Updated the five D-41 capability surfaces so they claim double speed and retain the mode-3 timing and HDMA limitations. The claims agreement check now requires the implemented-speed phrase, and its mutated negative control remains effective.
- Added C and C++ installed-consumer guests with 17 program bytes at `$0150`. The positive guest verifies partitioned budget runs during the switch, sums reported consumption, reads KEY1 back through WRAM, observes frame generation through `gbb_frame_info`, and stays under two frame durations. Both consumers print `cgb_speed_partition_smoke unarmed twin rejected` only after their unarmed twin reports `STOPPED` with bit 7 clear.
- Kept the public header, symbol set, fixture bytes, source runtime, and package allow-list unchanged. `speed.gb` still hashes to `3c6e88de1e28d47566f7486dd13813c8fb1baf48ee336509e3902bd9ff8e2f3f`.

## Task Commits

1. **Task 1: Player speed smoke and M1 control** — `3ca58af` (`feat`).
2. **Task 2: D-41 capability claim update** — `025aedd` (`docs`).
3. **Task 3: Installed C/C++ speed partition guests** — `4ed085b` (`test`).

The final documentation and tracking commit is recorded in the executor completion report.

## Files Created/Modified

- `tests/player/cgb_smoke.cmake`, `tests/player/CMakeLists.txt`, and `tests/player/expected-tests.txt` — speed digest branch, wrong-digest and PPU-follows-CPU controls, and inventory.
- `src/player/limitations.h`, `tests/player/test_limitations.c`, `README.md`, `.github/workflows/preview.yml`, `src/player/main.c`, and `tests/player/CMakeLists.txt` — aligned capability wording and enforcing claim checks.
- `tests/consumers/c/main.c` and `tests/consumers/cpp/main.cpp` — installed public-API guests and unarmed-twin checks.

## Decisions Made

- Frame generation is read from `gbb_frame_info` returned by `gbb_copy_frame_rgb555`; `gbb_get_info` has no generation field. This preserves the unchanged ABI and still observes a completed frame through the installed API.
- `HALTED_IDLE` leaves the CPU halted but permits later public runs to advance the display. The guest reaches HALT before frame one, so consumers continue in bounded slices until the first frame is ready, with the same two-frame cap.
- No hardware or perceptual evidence is claimed. These checks use the software model and generated build controls.

## Deviations from Plan

**1. Read frame generation through the existing frame API.** The task text names `gbb_get_info` for frame generation, but `gbb_info` does not expose that value. The consumer instead checks `gbb_frame_info.generation` returned by the public RGB555 copy call. No public field or symbol was added.

**2. Continue after the first `HALTED_IDLE` result.** The installed guest reaches `HALTED_IDLE` after 131,244 half-dots, before the first completed frame. Because the plan also requires frame generation to advance, the consumers continue bounded calls while the CPU remains halted until frame generation is available or the two-frame cap is reached. The pre-HALT switch partitions still return `GBB_STOP_BUDGET`.

**3. TDD annotation and task classification.** Task 3 is test-only regression coverage for already implemented public behavior. The phase TDD mode is false, and the pre-task Phase 12 baseline had 833/833 CTests passing; the new consumer assertion did not exist for a meaningful product-code RED run. No failure was manufactured. The planned unarmed twin is the sensitivity control in each installed consumer.

## Issues Encountered

The first installed-consumer run used a pre-existing relocated prefix from October 12, which caused the new guest to encounter the old library's unsupported KEY1 path. The phase-1 build had compiled the current library but did not refresh the relocated prefix. Installing the freshly built target to `build/package-prefix` and rerunning the planned checks passed all four installed consumers and both symbol-coverage checks.

## User Setup Required

None.

## Next Phase Readiness

Plan 12-12 is complete; Phase GB-12 remains in progress. The next plan is **12-13 — reproducible CGB speed fixture and offline workflow controls**, via **`/gsd-execute-phase 12`**. After Phase 12 is complete, the next phase is **Phase 13 — CGB HDMA**. Stop at the Phase 12 boundary; auto-advance remains disabled.

---
*Phase: 12-cgb-double-speed*
*Completed: 2026-10-13*

## Self-Check: PASSED

- Summary file exists and `summary_coverage` passed 1/1.
- Task commits `3ca58af`, `025aedd`, and `4ed085b` are ancestors of HEAD; the plan ledger measures three task commits.
