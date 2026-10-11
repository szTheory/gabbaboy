---
phase: 07-dmg-game-acceptance-and-regression-baseline
plan: 14
subsystem: player
tags: [player, script-smoke, negative-controls, attack-surface, exact-head-ci, game-03]

requires:
  - phase: 07-12
    provides: player --input-script smoke, script_smoke module, packaged scripted smoke
provides:
  - Session-level script controls player_session_script_no_input and player_session_script_invalid
  - Packaged no-input control in verify-phase3-player.sh (non-zero exit and predicate=fail)
  - tests/player/verify_script_smoke_surface.cmake plus player_script_smoke_surface and selftest CTests (D-38)
  - Exact-head macos-player-package evidence on PR #63
affects: [07-15, 07-16]

status: complete
actuals:
  tokens: 14000
  tasks: 3
  commits: 3
plan_head_before: 1f37628
plan_head_after: 238ff534f9aa171c4b367d4e92cbc8d5a02c341e

tech-stack:
  added: []
  patterns:
    - "cmake -P source scanner with a configure-time injected copy as its own negative control, run through tests/expect_exit.cmake"
    - "Optional extra argv for player_session_* tests (pinned ROM and script) with argc >= 5"

key-files:
  created:
    - tests/player/verify_script_smoke_surface.cmake
  modified:
    - tests/player/test_session.c
    - tests/player/CMakeLists.txt
    - tests/player/expected-tests.txt
    - tests/scripts/verify-phase3-player.sh

key-decisions:
  - "test_player_session now compiles audio.c, input.c and script_smoke.c directly (as test_reset_transition does) rather than linking the adapter, which would duplicate session.c"
  - "Surface check also forbids freopen, O_WRONLY, O_RDWR, O_CREAT, a non-literal fopen mode, and the player_session_* lock/replace_rom/save/load/remove names, beyond the plan's minimum list"

requirements-completed: []

coverage:
  - id: D1
    description: "No-input control fails the predicate at session level and through the packaged player"
    requirement: GAME-03
    verification:
      - kind: integration
        ref: "ctest player_session_script_no_input; CI log: packaged no-input control failed as expected (exit 1), predicate=fail"
        status: pass
    human_judgment: false
  - id: D2
    description: "Rejected script or ROM input leaves no state behind"
    requirement: GAME-03
    verification:
      - kind: integration
        ref: "ctest player_session_script_invalid (NUL byte, 65537-byte script, ROM without predicate)"
        status: pass
    human_judgment: false
  - id: D3
    description: "D-38 attack surface guarded by an inventoried test that can fail"
    requirement: GAME-03
    verification:
      - kind: integration
        ref: "ctest player_script_smoke_surface and player_script_smoke_surface_selftest"
        status: pass
    human_judgment: false
---

# Phase 07 Plan 14: Packaged player smoke controls and attack-surface guard Summary

The scripted Libbet player smoke now has a session-level and a packaged no-input control that must fail, a registered check that keeps the diagnostic free of environment, network, file-write and save-persistence use, and exact-head macos-player-package evidence on PR #63.

Requirement GAME-03 is not marked complete here: sibling plans in the phase still declare it.

## Accomplishments

- **Task 1 (tracer).** `player_session_script_no_input` drives `libbet-no-input.input` through the script_smoke prepare/run API and requires `GBB_ACCEPT_DRIVE_NOT_REACHED` with zero delivered events. `player_session_script_invalid` requires prepare to reject a NUL-byte script, a 65537-byte script and a ROM (the demo) with no pinned predicate, leaving rom, predicate, events and marks empty. The package script now runs the packaged no-input control and fails unless the exit is non-zero and the output has `predicate=fail`. `src/player/script_smoke.c` needed no change: prepare already mutates nothing on rejection.
- **Task 2 (D-38).** `verify_script_smoke_surface.cmake` scans `script_smoke.c` and `script_smoke.h` for environment, network, write-mode fopen, non-literal fopen mode and battery/save persistence tokens, and `main.c` for an environment read naming SCRIPT. The selftest copies `script_smoke.c` at configure time with an injected `getenv("GBB_SCRIPT_SELFTEST")` and must exit 1 with `script-smoke-surface: getenv`.
- **Task 3.** Pushed and read the exact-head run (below). No tracked file changed for it.

## TDD record

- RED for Task 2: `03027e0` registered both tests with the script absent; both failed ("Not a file"). GREEN `238ff53`.
- Task 1 controls passed on first run (the behaviour already existed). Mutation checks showed they can fail: running the no-input control with the tutorial script failed at `event_count == 0u` (rc 1); replacing the predicate rejection in `script_smoke.c` with `if (0)` made `player_session_script_invalid` fail at the demo-ROM case. Mutation reverted, not committed.
- Surface-check mutations run by hand against copies: write-mode `fopen("x","wb")` and `"r+"`, non-literal mode, `player_session_save_battery`, `SDL_OpenURL`, and `SDL_getenv("GBB_SCRIPT_X")` in main.c all failed with the named token. A first regex missed a quoted path argument; fixed before the GREEN commit.
- The packaged no-input control is proven able to fail by its own assertions (exit status and `predicate=fail`); it was not separately mutated.

## Exact-head CI evidence

- Run 38100653716, https://github.com/szTheory/gabbaboy/actions/runs/38100653716, head `238ff534f9aa171c4b367d4e92cbc8d5a02c341e`, event pull_request, attempt 1.
- `wait-exact-head-ci.py` (with `--require` for all eight jobs) printed `PASS run_id=38100653716 run_attempt=1`.
- Jobs, all `success`: native-windows-x64, native-macos-arm64, cmake-floor-3.25.3, native-linux-x64, player-gate, linux-asan-ubsan, macos-player-package, required-native.
- macos-player-package log: 55 of 55 player tests passed, including `player_session_script_no_input` (6.32 s), `player_session_script_invalid`, `player_script_smoke_surface` and `player_script_smoke_surface_selftest`; `libbet absent from scanned tree files=14`; `smoke_report rom_sha256=3607412031c8287cf878299ce96e581e85b852dde703806343b95576fa3ff1a9 half_dots=125841408 predicate=pass pcm_nonsilent=1 pcm_sha256=3d051cb0a0a4ced82706126c5cbcaddcd22dbe2cc2e61c92d0c5717f1e8aaae5` (the package script only continues past this line when the digest equals the headless runner's); `packaged no-input control failed as expected (exit 1)` with `predicate=fail pcm_nonsilent=0`.
- D-37: `git diff main -- .github/workflows/ci.yml` adds no job header; ci.yml is untouched by this plan. `check-player-result.sh --self-test` exits 0.
- First push was green; no fix cycles used.

## Deviations from Plan

None - plan executed exactly as written. (The surface-check token list is a superset of the plan's; see key-decisions.)

## Known Stubs

None.

## Threat Flags

None.

## Self-Check: PASSED

- tests/player/verify_script_smoke_surface.cmake exists; commits 08cd664, 03027e0, 238ff53 are ancestors of HEAD.
- Acceptance criteria re-run: 2 `player_session_script_` and 2 `player_script_smoke_surface` inventory lines, `libbet-no-input.input` referenced in the package script, 0 `getenv` in script_smoke.c, check-player-result self-test passes.
