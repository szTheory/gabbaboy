---
phase: GB-04-mbc1-and-safe-battery-continuation
plan: 04
subsystem: player-save-lifecycle
tags: [MBC1, battery-save, advisory-lock, autosave, SDL3]
requires:
  - phase: GB-04
    provides: identity-bound atomic battery persistence and dirty-generation API
provides:
  - Full-session nonblocking per-save writer lock and transactional ROM replacement
  - Host-time autosave cadence and explicit final-save retry/cancel/continue behavior
  - Player controls and limitations documentation for persistence behavior
affects: [GB-04-05, GB-04-06, GB-04-07, preview]
actuals:
  tokens: 13434
  tasks: 2
  commits: 3
tech-stack:
  added: []
  patterns: [stable advisory lock file, monotonic dirty-save cadence, staged session replacement]
key-files:
  created: []
  modified:
    - src/player/session.h
    - src/player/session.c
    - src/player/main.c
    - src/player/limitations.h
    - tests/player/test_session.c
    - tests/player/test_limitations.c
    - tests/player/expected-tests.txt
    - docs/preview.md
key-decisions:
  - "Hold a nonblocking exclusive advisory lock for each battery-backed session; serialize only cooperating GabbaBoy processes."
  - "Use SDL monotonic host time for 2-second quiet and 10-second maximum-age saves; guest time remains independent."
  - "A failed final save blocks reset, replacement, and quit until retry, explicit continue-without-saving, or cancel."
requirements-completed: [SAVE-03]
coverage:
  - id: D1
    description: Battery sessions have a stable single-writer lock; a busy candidate ROM cannot replace the active session.
    requirement: SAVE-03
    verification:
      - kind: integration
        ref: "bash tests/scripts/verify-phase3-player.sh (player_session_lock_lifecycle, player_smoke)"
        status: pass
    human_judgment: false
  - id: D2
    description: Changed battery RAM uses bounded autosave cadence and final transitions preserve progress or require an explicit user choice.
    requirement: SAVE-03
    verification:
      - kind: unit
        ref: "player_session_save_cadence; player_session_transition_choices"
        status: pass
      - kind: e2e
        ref: "player_smoke: save failure, retry, cancel, continue-without-saving, fresh-process outcomes"
        status: pass
    human_judgment: false
  - id: D3
    description: Player help and preview documentation describe save timing, recovery, lock scope, and limitations.
    verification:
      - kind: unit
        ref: "player_limitations"
        status: pass
      - kind: integration
        ref: "bash tests/scripts/verify-phase3-player.sh"
        status: pass
    human_judgment: false
duration: 11min
completed: 2026-10-08
status: complete
---

# Phase 4 Plan 04: Battery Session Lifecycle Summary

**The SDL player now serializes battery writers, autosaves changed RAM on a bounded host-time cadence, and makes failed final saves an explicit choice.**

## Performance

- **Duration:** 11 min
- **Started:** 2026-10-08T03:42:00Z
- **Completed:** 2026-10-08T03:52:35Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- Battery-backed sessions acquire a nonblocking exclusive advisory lock on a stable per-save `.lock` file and hold it until after the machine closes. Lock conflicts and lock errors are distinct; no-battery cartridges create neither save nor lock files.
- ROM replacement now builds a candidate machine, acquires its lock, validates its save, and only then swaps sessions. A lock conflict keeps the current ROM and guest state active.
- Dirty RAM saves after two seconds without a change or at ten seconds of dirty age, measured with SDL's monotonic host clock. Reset, replacement, and quit flush first.
- A failed transition pauses and visibly offers R to retry, C to continue without saving, or Escape to cancel. Failure remains in the title/F1 status until a successful save or explicit choice; the status distinguishes RAM held only in memory from data saved to disk.
- Preview instructions and limitation text now state the supported MBC1 battery scope, recovery behavior, autosave cadence, advisory-lock scope, and software-evidence limit.

## Task Commits

1. **Task 1: Keep one writable battery session and release it cleanly** — `9b8f6fd` (`feat(04-04): add battery session lock and save lifecycle policy`)
2. **Task 2: Autosave changed RAM and make final-flush failures actionable** — `2e48885` (`feat(04-04): gate player transitions on durable battery saves`)
3. **Task 2 integration smoke follow-up** — `398542d` (`test(04-04): exercise battery transition recovery choices`)

## Files Created/Modified

- `src/player/session.h` and `src/player/session.c` — lock ownership, deterministic save cadence, and explicit transition-resolution policy.
- `src/player/main.c` — candidate-session replacement, autosave, durable-save status, and retry/cancel/continue handling.
- `tests/player/test_session.c` and `tests/player/expected-tests.txt` — process-level lock, cadence, transition-policy, and named inventory coverage.
- `src/player/limitations.h`, `tests/player/test_limitations.c`, and `docs/preview.md` — accurate player persistence contract and limitations.

## Decisions Made

- Advisory locking applies to cooperating GabbaBoy processes. Other software that ignores the lock is outside its protection.
- Save cadence uses host monotonic time and the core's battery dirty generation; it does not alter guest timing.
- A candidate ROM must pass lock admission and save validation before replacing the active machine. A rejected save that was safely preserved may start with fresh RAM and an explicit warning; an unpreservable save disables persistence.

## Deviations from Plan

None. The named transition policy test and player smoke assertions implement the plan's requested transition and visible-failure coverage.

## Issues Encountered

- The first sandboxed player run could not create the synthetic battery lock in SDL's per-user preferences directory. The same required verifier passed after running with authorized filesystem access; it wrote only synthetic test data. No production or user save data was used.
- The final committed-revision verification passed 33/33 optional player CTests and the extracted package smoke. Candidate package SHA-256: `28eb872d801810d2d3741fa555f7c35d9f564622b6c0de3fa8a05f88b78fa7e1`; source revision: `398542d0c573c4bca8811b3ece1855afc5b7e813`; SDL 3.4.18 license digest matched the pinned receipt. This is local software/package evidence, not hosted CI or physical hardware evidence.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

Plan 04-04 is verified and committed. Plan 04-05, the original reproducible MBC1 battery-continuation fixture, is next; execution should continue with `$gsd-execute-phase 4` and stop at the Phase 4 boundary.

---
*Phase: GB-04-mbc1-and-safe-battery-continuation*
*Completed: 2026-10-08*

## Self-Check: PASSED

- [x] All task behaviors are implemented and exercised by named tests and player smoke assertions.
- [x] `bash tests/scripts/verify-phase3-player.sh` passed against source revision `398542d0c573c4bca8811b3ece1855afc5b7e813` (33/33 player tests and extracted-package smoke).
- [x] `git diff --check 8a47552cbf633c36248230b2c9993703d1fd7a23..HEAD` passed before writing this summary.
- [x] The phase evaluation-scope check resolved all three plan commits.
