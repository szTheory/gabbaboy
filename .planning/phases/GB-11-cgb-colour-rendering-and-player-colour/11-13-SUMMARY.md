---
phase: 11-cgb-colour-rendering-and-player-colour
plan: 13
subsystem: player-claims
tags: [player, claims, cgb, d-44, d-19, d-29, docs, preview]
status: complete
requires:
  - phase: 11-cgb-colour-rendering-and-player-colour
    provides: "11-12 player --model, colour presentation and player_cgb_smoke"
provides:
  - "GBB_PLAYER_LIMITATIONS_TEXT, --help, F1 help, README, docs/preview.md and both preview.yml capability_limits strings state the same Phase 11 capabilities and limits"
  - "player_claims_agree: fixed phrase lists enforced across limitations.h, README and both preview strings"
  - "player_claims_agree_mutated: README copy without a phrase must exit 1 with claims-disagree"
affects: [11-14]
requirements-completed: []
plan_head_before: 68cdb7149f5b9d97e5cab84f753cdb3b9205d37c
plan_head_after: cff5c1241f786aff592c05a017d778553df4173f
actuals:
  tokens: 9000
  tasks: 2
  commits: 2
coverage:
  - id: C1
    description: "The pinned player limitations text states the D-44 claims verbatim: DMG and CGB software with --model auto|dmg|cgb (default dmg), the fixed compatibility palette with no palette flag, no colour correction, the DMG APU model on the CGB profile, and CGB mode-3 timing, double speed and HDMA not claimed"
    requirement: CGB-09
    human_judgment: false
    verification:
      - kind: unit
        ref: "player_limitations"
        status: pass
  - id: C2
    description: "Every phrase of one list appears in limitations.h, README.md and the macOS capability_limits string, and the Linux string (which keeps saying it has no SDL player) carries the shorter list"
    requirement: CGB-09
    human_judgment: false
    verification:
      - kind: unit
        ref: "player_claims_agree"
        status: pass
  - id: C3
    description: "A README copy with a phrase removed is rejected with exit 1 and claims-disagree naming that phrase"
    requirement: CGB-09
    human_judgment: false
    verification:
      - kind: unit
        ref: "player_claims_agree_mutated"
        status: pass
  - id: C4
    description: "The remaining player tests, the packaged player smoke and the full phase1 suite are unchanged by the text edits"
    requirement: CGB-09
    human_judgment: false
    verification:
      - kind: integration
        ref: "bash tests/scripts/verify-phase3-player.sh --build-package"
        status: pass
---

# Phase 11 Plan 13: Player claims follow evidence Summary

Every player-facing claim surface now says the same evidence-backed Phase 11 capabilities and limits, and `player_claims_agree` (with a mutated-README negative control) catches a surface that drifts.

## Accomplishments
- Task 1 (tracer): `tests/player/claims_agree.cmake` plus `player_claims_agree` and `player_claims_agree_mutated`, proven first on one phrase, "no colour correction".
- Task 2: full D-44 statements in `limitations.h` and its verbatim pin, `print_player_help`, the F1 `show_help` text (message buffer raised from 2048 to 4096 bytes because the limitations text grew), README, `docs/preview.md` and both `preview.yml` strings.
- Claims, matching 11-12 evidence: default `--model dmg`; `auto`/`cgb` opt-in; DMG software on the CGB profile uses the core's fixed compatibility palette and the player has no palette flag; no colour correction (`(c << 3) | (c >> 2)`); CGB-profile audio is the DMG APU model; CGB mode-3 timing, double speed and HDMA are not claimed or implemented; no CGB-E hardware qualification. The Linux string still says it has no SDL player.
- `docs/preview.md` replaced the blanket "does not implement CGB" with the specific unimplemented items and keeps "CGB double-speed clock behavior". README no longer says the project does not support CGB (now false for colour), keeping the VIN and boot ROM limits.

## Deviations from Plan
- [Rule 1 - Bug] The first mutated control passed for the wrong reason (the real check was failing on a capability_limits count, because the strings contain semicolons that split a CMake list). Fixed by protecting semicolons, and tightened the mutated control's regex to `claims-disagree no colour correction`.
- [Rule 3 - Blocking] Nested `;`-lists cannot pass through `expect_exit.cmake`, so the phrase lists are written to configure-time files (one phrase per line, since phrases contain `|`) and read with `file(STRINGS)`. The plan's `PHRASES`/`LINUX_PHRASES` inputs became `PHRASES_FILE`/`LINUX_PHRASES_FILE`.
- Extra manual negative check: a preview.yml copy missing "CGB mode-3 timing" in the Linux string makes the script exit 1 with claims-disagree.

## Verification
- `ctest --test-dir build/phase3-player/gabbaboy -R '^player_'`: 93 of 93 passed.
- `ctest --preset phase1`: 677 of 677 passed.
- `bash tests/scripts/verify-phase3-player.sh --build-package`: passed (SDL 3.4.18 package smoke).
- `phase1-asan` is Linux-only and is left to CI.

## Known Stubs
None.

## Threat Flags
None.

## Self-Check: PASSED
