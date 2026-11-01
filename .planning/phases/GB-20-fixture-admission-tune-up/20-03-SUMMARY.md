---
phase: GB-20-fixture-admission-tune-up
plan: "03"
subsystem: fixtures
tags: [player-packaging, product-policy, macos, fixture-admission]
requires:
  - phase: GB-20-fixture-admission-tune-up
    provides: Shared exact player product policy, immutable fixture identities, and inventory checker from Plan 20-01
provides:
  - Player package stage and extracted bytes route through the shared exact policy before archive consumption or player execution
  - Isolated real-tree player controls reject hidden ROM payloads, changed fixture identities, and every bundled notice mutation
affects: [macos-player-qualification, player-packaging, fixture-policy]
actuals:
  tokens: 2917
  tasks: 2
  commits: 7
tech-stack:
  added: []
  patterns:
    - Production shell wrapper delegates player tree validation to the shared Python policy with the repository as its trusted root
    - Per-mutation private package copies are checked for an exact rejection reason and path, while before/after inventories protect the candidate
key-files:
  created:
    - tests/scripts/test_player_package_policy.py
    - .planning/phases/GB-20-fixture-admission-tune-up/20-03-SUMMARY.md
  modified:
    - tests/scripts/verify-phase3-player.sh
key-decisions:
  - Keep product byte identity checks separate from legal rights determinations; RIGHTS-01 remains pending.
  - Run full hosted macOS package qualification once at the exact Phase 20 final head, as directed by phase orchestration.
patterns-established:
  - Validate staged and extracted player files against the same layout policy before any packaged executable runs.
  - Prove rejection controls through the production shell entry point and verify they leave the candidate inventory unchanged.
requirements-completed: []
requirements-pending: [RIGHTS-01]
coverage:
  - id: D1
    description: The real player stage passes the production policy wrapper, and an isolated seeded ROM is rejected before player execution.
    verification:
      - kind: integration
        ref: "bash tests/scripts/verify-phase3-player.sh --check-package-policy build/phase3-player/package-stage/installed-prefix; seeded Mooneye ROM rejected as product-fixture-leak"
        status: pass
    human_judgment: false
  - id: D2
    description: Real-tree controls reject renamed and suffixless fixture bytes, unknown subtree members, changed fixture identities, and missing or changed fixture, GabbaBoy, and SDL notices.
    verification:
      - kind: integration
        ref: "bash tests/scripts/verify-phase3-player.sh --self-test-package-policy build/phase3-player/package-stage/installed-prefix; all 21 isolated mutation cases rejected and candidate inventory preserved"
        status: pass
    human_judgment: false
  - id: D3
    description: The shared portable product checker continues to exercise the player layout policy independently of the macOS build lane.
    verification:
      - kind: integration
        ref: "python3 -I tests/scripts/verify-fixture-admission.py --self-test-packages --layout player"
        status: pass
    human_judgment: false
duration: 31min
completed: 2026-10-31
status: complete
commits: 7
plan_head_before: 5825b1b409a7ff1007c9edb5cea1f27b385a07a6
plan_head_after: eac465d5aee3dbeff52faea60d4bf8cdf5c52c41
---

# Phase GB-20 Plan 03: Fixture Admission Tune-up Summary

**Player package verification now routes actual staged and extracted bytes through the shared fixture and notice policy before execution.**

## Performance

- **Duration:** 31 min
- **Started:** 2026-10-31T20:50:48-04:00 (first recorded RED commit)
- **Completed:** 2026-10-31T21:22:13-04:00
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Added early `--check-package-policy PREFIX` and `--self-test-package-policy PREFIX` modes to the existing player verifier.
- Validated the existing staged player package and rejected a controlled Mooneye ROM insertion through the production wrapper.
- Added 21 isolated real-tree controls covering renamed and suffixless payloads, unauthorized members, fixture identities, and all fixture, GabbaBoy, and SDL notice copies. The candidate inventory was unchanged after the controls.
- Wired stage inventory creation and stage-to-extraction comparison into package construction, and policy validation before player execution in build and downloaded-package verification paths.

## Task Commits

1. **Task 1: Carry one real player package through stage, extraction and exact policy** - `947cffa3` (RED test), `06b83fea` (implementation)
2. **Task 2: Exercise every player leak and notice mutation through the production wrapper** - `eac465d5` (controls)

The measured commit count is 7 because four Plan 20-02 commits landed while this plan's tracer verification was paused. The three Plan 20-03 commits are listed above.

## Files Created/Modified

- `tests/scripts/verify-phase3-player.sh` - Shared player policy calls, stage inventory comparison, and isolated mutation controls.
- `tests/scripts/test_player_package_policy.py` - RED test for the clean production policy CLI.

## Decisions Made

- Used the shared player layout policy with the repository as its trusted source; package metadata does not set policy identities.
- Kept rights review separate from byte and notice identity checks. This plan does not determine legal permission, so `RIGHTS-01` remains pending.

## Deviations from Plan

None in implementation scope. The required local `--build-package` attempt reached the existing player CTest suite, where 106 of 108 tests passed. The two Cocoa menu checks could not initialize because this host has no display service; unsetting `SDL_VIDEO_DRIVER` produced the same environment failure. The hosted exact-head macOS package qualification has not run and remains phase-orchestration work. No hosted result is claimed here.

## Issues Encountered

- Full local `bash tests/scripts/verify-phase3-player.sh --build-package` did not reach archive creation or lifecycle verification because the host has no Cocoa display service for `player_slot_menu_shortcuts` and its negative control.
- Phase orchestration will run the qualified macOS package lane at the exact Phase 20 final head. This plan's existing-stage policy and mutation-control evidence is local and does not substitute for that package qualification.

## User Setup Required

None.

## Next Phase Readiness

Plan 20-03's player policy integration and local mutation controls are complete. Exact-head hosted macOS package qualification remains for Phase 20 orchestration. `RIGHTS-01` remains pending because tooling verifies identities and notices but cannot decide redistribution permission. Do not advance to Phase 21 from this plan.

## Self-Check: PASSED

- Summary file exists at the required phase path.
- Task commits `947cffa3`, `06b83fea`, and `eac465d5` are ancestors of the current plan head.
- The local full-build limitation and unrun hosted qualification are explicitly recorded.

---
*Phase: GB-20-fixture-admission-tune-up*
*Completed: 2026-10-31*
