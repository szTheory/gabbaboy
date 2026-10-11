---
phase: 08-cartridge-seam-mbc5-and-mbc2
plan: 04
subsystem: player
tags: [player, battery, mbc2, mbc5, limitations]
requires: [08-03]
provides:
  - "player_save_identity.battery_unsupported for cartridge types $06, $1B, $1E"
  - "Fixed status string and stderr warning on startup and ROM replacement"
  - "Updated limitations clause and its byte-for-byte pin"
  - "Player CTest player_session_battery_unsupported"
affects: [08-09]
key-files:
  modified:
    - src/player/session.h
    - src/player/session.c
    - src/player/main.c
    - src/player/limitations.h
    - tests/player/test_limitations.c
    - tests/player/test_session.c
    - tests/player/expected-tests.txt
key-decisions:
  - "battery_backed expression unchanged; battery_unsupported is a separate flag so every existing save path early-returns for $06/$1B/$1E"
  - "PLAYER_SESSION_MAX_ROM_SIZE and its 2 MiB message untouched (D-15)"
requirements-completed: [CART-02, CART-03]
status: complete
duration: 20 min
completed: 2026-10-11
commits: 2
plan_head_before: e2ccf182a82f362179b19bdb36d1944e397ae585
plan_head_after: dd7bdd8
actuals:
  tokens: 14000
  tasks: 2
  commits: 2
coverage:
  - deliverable: "MBC2/MBC5 battery cartridges run in the player without touching the save directory"
    verification:
      - {kind: test, ref: "tests/player/test_session.c#player_session_battery_unsupported", status: pass}
    human_judgment: false
  - deliverable: "Status string, stderr warning and limitations text name the unsaved-progress gap"
    verification:
      - {kind: test, ref: "tests/player/test_limitations.c#player_limitations", status: pass}
      - {kind: command, ref: "grep -c of the status string in src/player/main.c is 4", status: pass}
    human_judgment: true
    rationale: "The visible status line is not asserted by an automated UI test; only the source branches and the limitations pin are checked."
---

# Phase 8 Plan 04: Player battery honesty Summary

Player identity now flags MBC2 $06 and MBC5 $1B/$1E as battery_unsupported (persistence stays off, no save file touched), and the player says "Battery saving is not supported for this cartridge type yet; progress is not kept" in its status and on stderr.

## Accomplishments

- `battery_unsupported` added to `player_save_identity`, set in `player_session_identify_rom`; `battery_backed` and `persistence_enabled` logic unchanged.
- `player_session_battery_unsupported` loads synthetic $06/$1B/$1E ROMs through `player_session_replace_rom`, runs load, save and lock, and requires an empty save directory; a $03 ROM still yields battery_backed true.
- main.c startup and replacement paths show the D-22 status and write `gabbaboy-player: warning: ...` to stderr.
- Limitations sentence replaced in `limitations.h` and the test pin; the v1 save envelope is unchanged.

## Evidence

- `verify-phase3-player.sh --build-package`: 57/57 player tests pass (inventory check `names=55` baseline ok, expected-tests.txt agrees); package smoke passed.
- phase1 full ctest: 287/287 pass.
- Acceptance greps: status string 4 occurrences in main.c; old MBC1-only sentence 0 in both files; no PLAYER_SESSION_MAX_ROM_SIZE diff; no `battery_backed =` diff.

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Threat Flags

None.

## Self-Check: PASSED

- FOUND commits 2076d26, dd7bdd8 on the branch
- Tracer `<verify>` and task 2 `<verify>` ran green (57/57)
