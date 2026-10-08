---
phase: GB-04-mbc1-and-safe-battery-continuation
plan: 01
subsystem: core-player
tags: [c17, mbc1, battery-ram, sdl3, sha256, persistence]

# Dependency graph
requires:
  - phase: GB-03-visible-interactive-dmg
    provides: deterministic CPU/bus, bounded core API, SDL3 player and package smoke
provides:
  - Type $03 32 KiB MBC1 cartridges with 8 KiB battery RAM in the core
  - Caller-buffer battery APIs and changed-byte generation tracking
  - Versioned ROM-identity-bound player save and fresh-process continuation smoke
  - Independent cartridge guest/API regression
affects: [04-02, battery-api, mbc1, player-session]

# Actuals
actuals:
  tokens: 16775
  tasks: 2
  commits: 2

# Tech tracking
tech-stack:
  added: []
  patterns: [bounded instance-owned cartridge RAM, explicit little-endian save envelope, same-directory atomic replacement]

key-files:
  created:
    - tests/test_cartridge.c
  modified:
    - include/gabbaboy/gabbaboy.h
    - src/core/gabbaboy.c
    - src/player/session.c
    - src/player/main.c
    - tests/scripts/verify-phase3-player.sh

key-decisions:
  - "Use an exact 51-byte versioned envelope with ROM SHA-256 identity and IEEE CRC-32; no native structure dumps or core filesystem code."
  - "Initialize new cartridge RAM to FF as deterministic emulator policy, without claiming hardware power-on behavior."
  - "Preserve the existing save on invalid input and disable persistence for that session; recovery is completed in Plan 04-03."

patterns-established:
  - "Battery data crosses the core boundary only through caller-owned buffers and explicit size/generation queries."
  - "The end-to-end continuation oracle runs the guest in two bounded, separate player processes."

requirements-completed: [SAVE-01, SAVE-02, SAVE-03]

coverage:
  - id: D1
    description: "Supported type $03 32 KiB MBC1 guest writes honor RAM enable and persist one changed byte through the core battery API."
    requirement: SAVE-01
    verification:
      - kind: unit
        ref: "cartridge_tracer; cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '^cartridge_tracer$'"
        status: pass
    human_judgment: false
  - id: D2
    description: "Player persistence reloads the guest byte in a fresh process while the existing ROM-only player smoke remains green."
    requirement: SAVE-03
    verification:
      - kind: integration
        ref: "bash tests/scripts/verify-phase3-player.sh (15/15 player tests and packaged two-process smoke)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Loader, bus, lifecycle and independent ROM-only/cartridge paths pass their named regressions."
    requirement: SAVE-02
    verification:
      - kind: unit
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^(loader_|bus_|instance_lifecycle$)' (20/20)"
        status: pass
    human_judgment: false

# Metrics
duration: 13min
completed: 2026-10-07
status: complete
---

# Phase 4 Plan 01 Summary

A guest byte now travels from an MBC1 RAM write through the public core API and player save envelope, then controls a guest success path in a separate fresh process.

## Performance

- **Duration:** 13 minutes
- **Started:** 2026-10-07T23:05:26-04:00
- **Completed:** 2026-10-07T23:18:25-04:00
- **Tasks:** 2
- **Files modified:** 12

## Accomplishments

- Added bounded instance-owned type $03 MBC1 8 KiB RAM, enable gating, reset retention, and caller-owned battery size/copy/import/generation operations.
- Added exact-ROM SHA-256 save identity, a fixed-endian 51-byte versioned envelope with CRC-32, bounded validation, and same-directory write/sync/rename.
- Extended player smoke to store a byte in one process and prove a fresh guest takes its persisted-byte success branch; kept the ROM-only and failed-replacement smoke paths.
- Added an independent `cartridge_tracer` covering disabled reads/writes, changed-byte generation, import/export, and ROM-only execution.

## Task Commits

1. **Task 1: Carry one 8 KiB battery RAM byte from guest write to fresh player process** - `ec9adee` (feat)
2. **Task 2: Register an independent first-path cartridge regression** - `1f280b9` (test)

**Plan metadata:** this summary commit.

## Files Created/Modified

- `include/gabbaboy/gabbaboy.h`, `src/core/gabbaboy.c` - cartridge RAM ownership, MBC1 RAM access and battery APIs.
- `src/player/session.h`, `src/player/session.c` - bounded ROM/save files, identity, validation and atomic persistence.
- `src/player/main.c` - load/flush integration and bounded two-process guest smoke.
- `tests/test_cartridge.c`, `tests/CMakeLists.txt`, `tests/expected-tests.txt` - independently authored guest regression and required inventory registration.
- `src/player/limitations.h`, `tests/player/test_limitations.c` - state the now-supported save profile while retaining the audio limitation.
- `tests/player/test_session.c`, `tests/scripts/verify-phase3-player.sh` - update session API use and package metadata expectation.

## Decisions Made

- New battery RAM starts at `$FF` by explicit deterministic software policy; this is not a hardware startup claim.
- Invalid saves remain untouched and disable persistence for the current session. Preservation/recovery behavior is owned by Plan 04-03.
- Core RAM state remains independent of host file and crypto APIs; the player owns hashing and persistence.

## Deviations from Plan

1. The existing package verifier still required metadata to say battery persistence was unavailable. Updated that expectation and the player limitation assertion because the planned feature made both stale; the full package verifier passed.
2. The test task is marked `tdd="true"` but follows the tracer task that already implements the behavior. The regression was therefore run against the completed production slice; no code was undone to manufacture a red run. The project-wide TDD mode is disabled.

**Total deviations:** 2, both scope-aligned. No dependencies were added.

## Issues Encountered

- SDL's per-user save location is outside the workspace sandbox. The exact player verifier was run with the approved scoped filesystem escalation; it created and removed only its unique synthetic save.
- The build reports a pre-existing unsequenced access warning in `tests/test_dma.c:702`; this phase did not modify that fixture.

## User Setup Required

None.

## Next Phase Readiness

Plan 04-02 can now expand the support matrix and test the full battery API boundary. The current loader accepts only ROM-only and type $03 32 KiB/8 KiB MBC1; full bank mapping, type/size matrix, MBC1M rejection, 32 KiB battery RAM, and API failure canaries remain for that plan.

---
*Phase: GB-04-mbc1-and-safe-battery-continuation*
*Completed: 2026-10-07*
