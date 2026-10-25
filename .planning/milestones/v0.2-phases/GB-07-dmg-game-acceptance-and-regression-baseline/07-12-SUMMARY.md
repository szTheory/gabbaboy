---
phase: 07-dmg-game-acceptance-and-regression-baseline
plan: 12
subsystem: player
tags: [player, sdl3, acceptance, libbet, pcm-digest, package-scan, game-03]

requires:
  - phase: 07-11
    provides: exact-head PCM calibration, shared gbb_accept stepper, driver and predicate
  - phase: 07-10
    provides: libbet acceptance case and libbet-tutorial input script
provides:
  - D-36 scripted player smoke (src/player/script_smoke.{h,c}) over the shared gbb_accept driver
  - "gabbaboy-player --smoke-package <invalid-rom> --input-script <script> <rom>" with one smoke_report line
  - Package-script check that the player PCM digest equals the headless acceptance.libbet.pcm_sha256
  - Package ROM-absence scan (verify-libbet-admission.py --scan-dir) on the extracted package
affects: [07-13, 07-15, 07-16]

status: complete
actuals:
  tokens: 14000
  tasks: 2
  commits: 2
plan_head_before: 15020fbfd98c64e2229da9769140705431b0bba4
plan_head_after: f32b1cd2ac7cdd3166f71e81e3fabc2206c86f3d

tech-stack:
  added: []
  patterns:
    - "Scripted events become SDL key events whose timestamps invert to the exact script half-dot, so player_input_key schedules them where the headless runner queues them"
    - "PCM digest and window statistics are taken in the stepper sink before frames reach player_audio_submit; ring backpressure never alters the digest"

key-files:
  created:
    - src/player/script_smoke.h
    - src/player/script_smoke.c
  modified:
    - src/player/main.c
    - CMakeLists.txt
    - tests/player/CMakeLists.txt
    - tests/scripts/verify-phase3-player.sh

key-decisions:
  - "Ledger-free prepare/run split: script and ROM are parsed, hashed and bound to the pinned predicate before any guest or player state exists"
  - "The smoke never loads or saves battery state (skip_final_save, no lock) so it writes no files"
  - "Open Question 3 option (b): ROM and script are read from the checkout; the package does not ship them"

requirements-completed: [GAME-03]

duration: 40 min
completed: 2026-10-10
---

# Phase 7 Plan 12: Packaged player scripted Libbet smoke Summary

**The extracted, packaged SDL3 player replays the Libbet gbinput script through its keyboard path, clears the tutorial predicate and produces a PCM digest identical to the headless runner's; the package scan proves the ROM is not shipped.**

## Accomplishments

- `script_smoke.c` prepares (bounded 64 KiB script read, 8 MiB ROM read, SHA-256, predicate lookup by digest) before mutating anything, then runs `gbb_accept_drive` with budget 505612800, tail 8388608 and max_batch 56 and a deliver callback.
- `main.c` converts each press/release to the keyboard mapping (arrows, Z, X, Return, Right Shift), pushes it as an SDL key event timestamped at exactly `host_anchor + ns(at_half_dots)` (no skew; overflow checked) and pumps events so `handle_key` and `player_input_key` process it. Exit codes: 0 pass, 1 miss or silent PCM, 2 bad input.
- Observed locally (dummy SDL drivers): `smoke_report rom_sha256=3607...f1a9 half_dots=125841408 predicate=pass pcm_nonsilent=1 pcm_sha256=3d051cb0...aae5`, equal to headless `acceptance.libbet.pcm_sha256`. Negative checks: libbet-no-input gives predicate=fail exit 1; missing script and a non-Libbet ROM give exit 2.
- `verify-phase3-player.sh` computes the headless digest (building the runner alone if APP_BUILD lacks one), requires the pinned ROM digest and `predicate=pass pcm_nonsilent=1 pcm_sha256=<expected>` from the extracted player, and fails the macos-player-package job if the extracted package holds the Libbet ROM or a libbet-named path (`libbet absent from scanned tree files=14`).

## Task Commits

1. Task 1 (tracer): 08bdf56 feat(07-12) packaged player scripted smoke and PCM equality
2. Task 2: f32b1cd test(07-12) extracted-package ROM-absence scan

## Verification

- `bash tests/scripts/verify-phase3-player.sh --build-package` exit 0 (51/51 player ctests, existing demo and MBC1 smokes, scripted smoke with PCM equality, package scan). Tracer feedback gate: verify re-run end-to-end, passed.
- Acceptance greps: `--input-script` in main.c 3; `+ 8u` in script_smoke.c 0; `gbb_accept_drive` in script_smoke.c 3; `acceptance.libbet.pcm_sha256` in the package script 2; `--scan-dir` 1.
- Not run: the remote macos-player-package CI job on this head (local pass only; not treated as remote evidence).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] test_player_reset_transition includes main.c directly**
- **Found during:** Task 1
- **Issue:** main.c now includes script_smoke.h and gbb_accept.h, so the test target failed to compile and link.
- **Fix:** added script_smoke.c to that target and linked gabbaboy_accept.
- **Files modified:** tests/player/CMakeLists.txt
- **Commit:** 08bdf56

**Total deviations:** 1 auto-fixed (Rule 3). **Impact:** none on behavior.

Notes: the plan said "5-argument shape"; the invocation has argc 6 (program plus five arguments). The invalid-rom argument is accepted for shape parity with the existing package smoke and is not used by the scripted path.

## Known Stubs

None.

## Threat Flags

None. T-07-23, T-07-25 and T-07-43 mitigations are implemented as planned (bounded reads before mutation, checked half-dot to nanosecond conversion, package scan).

## Self-Check: PASSED

- src/player/script_smoke.c and src/player/script_smoke.h exist; commits 08bdf56 and f32b1cd are ancestors of HEAD; plan-level verification command passed.
