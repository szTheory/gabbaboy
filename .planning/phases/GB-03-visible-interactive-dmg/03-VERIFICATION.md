---
phase: GB-03-visible-interactive-dmg
verified: "2026-10-10T16:04:13Z"
status: passed
score: 5/5 roadmap truths verified
covered_files:
  - .github/scripts/check-player-result.sh
  - .github/scripts/wait-exact-head-ci.py
  - .github/workflows/ci.yml
  - .github/workflows/preview.yml
  - .github/workflows/release.yml
  - .planning/config.json
  - .planning/phases/GB-03-visible-interactive-dmg/03-01-PLAN.md
  - .planning/phases/GB-03-visible-interactive-dmg/03-01-SUMMARY.md
  - .planning/phases/GB-03-visible-interactive-dmg/03-02-PLAN.md
  - .planning/phases/GB-03-visible-interactive-dmg/03-02-SUMMARY.md
  - .planning/phases/GB-03-visible-interactive-dmg/03-03-PLAN.md
  - .planning/phases/GB-03-visible-interactive-dmg/03-03-SUMMARY.md
  - .planning/phases/GB-03-visible-interactive-dmg/03-04-PLAN.md
  - .planning/phases/GB-03-visible-interactive-dmg/03-04-SUMMARY.md
  - .planning/phases/GB-03-visible-interactive-dmg/03-05-PLAN.md
  - .planning/phases/GB-03-visible-interactive-dmg/03-05-SUMMARY.md
  - .planning/phases/GB-03-visible-interactive-dmg/03-06-PLAN.md
  - .planning/phases/GB-03-visible-interactive-dmg/03-06-SUMMARY.md
  - .planning/phases/GB-03-visible-interactive-dmg/03-07-PLAN.md
  - .planning/phases/GB-03-visible-interactive-dmg/03-07-SUMMARY.md
  - .planning/phases/GB-03-visible-interactive-dmg/03-08-PLAN.md
  - .planning/phases/GB-03-visible-interactive-dmg/03-08-SUMMARY.md
  - .planning/phases/GB-03-visible-interactive-dmg/03-09-PLAN.md
  - .planning/phases/GB-03-visible-interactive-dmg/03-09-SUMMARY.md
  - .planning/phases/GB-03-visible-interactive-dmg/03-10-PLAN.md
  - .planning/phases/GB-03-visible-interactive-dmg/03-10-SUMMARY.md
  - .planning/phases/GB-03-visible-interactive-dmg/03-11-PLAN.md
  - .planning/phases/GB-03-visible-interactive-dmg/03-11-SUMMARY.md
  - .planning/phases/GB-03-visible-interactive-dmg/03-12-PLAN.md
  - .planning/phases/GB-03-visible-interactive-dmg/03-12-SUMMARY.md
  - .planning/phases/GB-03-visible-interactive-dmg/03-13-PLAN.md
  - .planning/phases/GB-03-visible-interactive-dmg/03-13-SUMMARY.md
  - docs/dmg-video-evidence.md
  - docs/preview.md
  - fixtures/visible-demo/demo.asm
  - fixtures/visible-demo/demo.gb
  - fixtures/visible-demo/manifest.json
  - include/gabbaboy/gabbaboy.h
  - src/core/gabbaboy.c
  - src/player/audio.c
  - src/player/audio.h
  - src/player/input.c
  - src/player/input.h
  - src/player/limitations.h
  - src/player/main.c
  - src/player/session.c
  - src/player/session.h
  - tests/CMakeLists.txt
  - tests/expected-tests.txt
  - tests/player/CMakeLists.txt
  - tests/player/expected-tests.txt
  - tests/player/test_input.c
  - tests/player/test_limitations.c
  - tests/player/test_presentation.c
  - tests/player/test_session.c
  - tests/scripts/test_verified_player_output_dir.py
  - tests/scripts/verified_player_output_dir.py
  - tests/scripts/verify-phase3-player.sh
  - tests/test_dma.c
  - tests/test_joypad.c
  - tests/test_ppu.c
  - tests/test_tracer.c
covered_digest: "v3:sha256:7149850e3cb41814804997a1d619db388bcb358cb99243ba2d9dd183531ffbd8"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 5/5
  gaps_closed: []
  gaps_remaining: []
  regressions: []
decision_coverage:
  honored: 14
  total: 14
  not_honored: []
---

# Phase GB-03: Visible Interactive DMG Verification Report

**Phase Goal:** As a Mac user, I want to play a legal GB ROM with timed input and video evidence, so that I can verify the DMG preview.
**Verified:** 2026-10-10T16:04:13Z against branch `gsd/phase-06.1-verification-refresh` (HEAD `21c11446db2404195c8c7d1a65b8309cb9be057d`; working tree clean apart from untracked `.planning/milestone.lock`).
**Status:** passed
**Re-verification:** Yes, freshness refresh. The prior report (verified 2026-10-10T01:55:17Z, status passed, 5/5, no `gaps:`) went stale because Phase 06.1 PR #54 (squash merge `ab76d09c2ee27ba09fc5f3c2510af016aebfdecb`, exact tested head `2a8fd1c357262d4b69707b553c603fd441a0f3fa`) changed covered files. No plans were re-executed. The commands below were re-run by this verifier.

## User Flow Coverage

| Step | Expected | Evidence | Status |
|---|---|---|---|
| Launch a legal fixture | The original ROM-only demo opens and shows its frame. | `fixtures/visible-demo/manifest.json` records original project-authored assembly, license, ROM digest. The extracted-byte smoke loaded the packaged demo. | VERIFIED |
| Press and release a mapped key | Timestamped input reaches the guest and changes the tile. | This run's smoke: "SDL Z-down rendered the darker demo tile and Z-up restored the lighter tile". Owner observation in `03-UAT.md` test 34 is reused as recorded, not repeated. | VERIFIED |
| Inspect video evidence | Composition, raster timing, DMA/input and gameplay have distinct evidence. | Separate `frame_composition_*`, `ppu_timing_*`, DMA and JOYP guest cases passed in 184/184. `docs/dmg-video-evidence.md` is the ledger. | VERIFIED (declared software model) |
| Basic player controls | Resize, pause, reset, open, quit. | 51/51 optional player CTests passed. The smoke covered replacement lock conflict, save retry, cancel and continue. | VERIFIED |
| Understand support limits | Help, docs and package state audio/save scope and limits. | `src/player/limitations.h` and `test_limitations` are in the passing player set. | VERIFIED |

## Goal Achievement

| # | Roadmap truth | Status | Evidence |
|---|---|---|---|
| 1 | VIDEO-01: BG/window/sprite composition and dot-sensitive LCD/STAT/fetch behavior are separately demonstrated. | VERIFIED | Registered `frame_composition_*` and `ppu_timing_*` cases in `tests/test_ppu.c` passed in 184/184. |
| 2 | VIDEO-02: Model-specific OAM DMA, VRAM/OAM restrictions and CPU/PPU/DMA contention results. | VERIFIED (D-025 software-model scope) | `tests/test_dma.c` cases passed. No physical DMG-CPU-B lane/timing or PPU-revision measurement is claimed. |
| 3 | VIDEO-03: Timestamped joypad transitions are deterministic through the public API and the SDL path. | VERIFIED (selected falling-edge software contract) | `tests/test_joypad.c` and JOYP guest cases passed. SDL Z-down/up smoke covers the keyboard path. CPU-B pulse qualification and sample phase remain unmeasured. |
| 4 | VIDEO-04: Open and play a permissioned fixture, resize with aspect/integer scaling, pause, reset, quit, actionable errors. | VERIFIED | Player CTests 51/51 and extracted-byte smoke passed. UAT test 34 reused. |
| 5 | VIDEO-05: Automated checks distinguish composition, timing and gameplay; the preview states its audio/persistence scope and limits. | VERIFIED | Separate suites passed. `test_limitations` and package metadata checks passed. Fresh-process MBC1 continuation passed. |

**Score:** 5/5 roadmap truths verified (0 present-but-behavior-unverified).

## What Changed Since The Prior Report, And Whether It Holds

| Change (PR #54) | Check | Result |
|---|---|---|
| `src/player/session.c` `read_rom_file`: adds `O_NOCTTY` to the open flags (line 107); size overrun and `close()` failure now reported in separate branches (lines 143-153). | Read the code directly. Session tests passed in the 51/51 player run. | Size-bound branch: test-guarded by the 2097153-byte assertion in `tests/player/test_session.c` (the 2097154-byte case asserts the earlier `fstat` "bounded regular file" rejection). `close()`-failure branch: **inspection only**. No fault-injection stage exists for ROM close, so it is not test-covered and is not claimed to be. |
| `tests/player/test_session.c` 2097153/2097154-byte assertions | Present; the player CTests passed. | Guards the size-bound message only. |
| `tests/scripts/test_verified_player_output_dir.py`: `_receipt_fields` helper and inner withdrawal-site test | `PYTHONDONTWRITEBYTECODE=1 python3 tests/scripts/test_verified_player_output_dir.py` | 21 tests OK (was 20). |
| `tests/scripts/verify-phase3-player.sh` (comment-only) | Run as the gate below. | No behavioral change; gate passes. |
| `.github/workflows/ci.yml`: single `player-gate` job feeding `macos-player-package` and `required-native` (via `.github/scripts/check-player-result.sh`) | Read workflow; `gh run view` on the hosted runs. | Wired (`ci.yml` lines 125-198). |
| `.github/workflows/preview.yml`: exact-head waits via `.github/scripts/wait-exact-head-ci.py` | Read workflow (lines 30, 77, 126). | Wired. |

`.github/scripts/wait-exact-head-ci.py` and `.github/scripts/check-player-result.sh` were added to the covered set because the Phase 3 player package lanes now depend on them.

## Required Artifacts

| Artifact group | Status | Details |
|---|---|---|
| Core/API and optional SDL player | VERIFIED | Built and linked in the phase1 preset. Player lane built with SDL 3.4.18. |
| PPU/DMA/JOYP/tracer tests and inventories | VERIFIED | `tests/expected-tests.txt` and `tests/player/expected-tests.txt` are fail-closed inventories and the run used `--no-tests=error`. |
| Original interactive fixture | VERIFIED | Manifest digest checked by CTest; packaged demo ran. |
| Evidence and support documentation | VERIFIED | The ledger separates documentation, software policy and physical observation. |
| Package and consumer workflows | VERIFIED | Run locally and confirmed on hosted CI for the PR head (below). |

## Key Link Verification

| From | To | Via | Status |
|---|---|---|---|
| PPU/core run | Public frame API and guest tests | Dot progress, completed frame copy, independent assertions | WIRED |
| DMA/PPU scheduling | DMA guest suite | FF46 state, DMA deadlines, access gating | WIRED |
| Public event API | JOYP guests | Timestamped queue to FF00/IF.4 reads | WIRED |
| SDL keyboard | Public event API | Scancode mapping, smoke Z-down/up | WIRED |
| Frame and fixture | SDL renderer | Copied shade frame to texture to renderer; smoke asserts shades | WIRED |
| `ci.yml` `player-gate` | `macos-player-package` and `required-native` | `needs`, `player_required` output, `check-player-result.sh` | WIRED |
| `preview.yml` package lanes | Exact-head CI | `wait-exact-head-ci.py` | WIRED |
| Limitation source | Help, docs, metadata | Shared capability statement, `test_limitations` | WIRED |

## Data-Flow Trace (Level 4)

| Artifact | Data | Source | Real data | Status |
|---|---|---|---|---|
| SDL display | Frame pixels | Guest ROM, PPU, completed frame, player copy, SDL texture | Yes | FLOWING (smoke asserts rendered shades) |
| Guest joypad | FF00 / IF.4 and tile | SDL/public timestamped input, JOYP state, guest polling, PPU frame | Yes | FLOWING |
| Fixture | Guest program bytes | Checked-in assembly, manifest digest, ROM-only loader | Yes | FLOWING |

## Behavioral Spot-Checks (run by this verifier, macOS)

| Behavior | Command | Result | Status |
|---|---|---|---|
| Core inventory | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` | 184/184 passed | PASS |
| Output-dir helper | `PYTHONDONTWRITEBYTECODE=1 python3 tests/scripts/test_verified_player_output_dir.py` | 21 tests OK | PASS |
| Player and package gate | `bash tests/scripts/verify-phase3-player.sh --build-package` | Player CTest 51/51. Extracted-byte smoke passed for SDL 3.4.18: Z-down/Z-up shade transition, dummy-audio recovery, guest audio, fresh-process MBC1 continuation. `source_revision=21c11446db2404195c8c7d1a65b8309cb9be057d`. | PASS |

The local package SHA-256 differs between builds and directories. It is not a release identity and no reproducible-build claim is made.

## Hosted CI Evidence (queried with `gh run view`)

| Run | Head | Result |
|---|---|---|
| ci 38064419789 (PR #54 head) | `2a8fd1c3` | success: native-linux-x64, native-macos-arm64, native-windows-x64, cmake-floor-3.25.3, linux-asan-ubsan, player-gate, macos-player-package, required-native |
| preview 38064419803 (PR #54 head) | `2a8fd1c3` | success: installed-package-smoke-macos-arm64, installed-package-smoke-linux-x64, player-package-smoke-macos, preview-package-smoke |
| ci 38064726000 (main push) | `ab76d09c` | success; `macos-player-package` skipped by design on push |

This hosted evidence is for the PR head and the squash merge, not for the later documentation-only commits on this branch.

## Probe Execution

No Phase 3 plan declares a probe.

## Requirements Coverage

Every requirement ID declared in the 13 PLAN frontmatters (VIDEO-01 to VIDEO-05) appears in REQUIREMENTS.md, with checked boxes (lines 32-36) and traceability rows (lines 108-112).

| Requirement | Status | Evidence |
|---|---|---|
| VIDEO-01 | SATISFIED | Separate composition and PPU timing cases passed. |
| VIDEO-02 | SATISFIED within the D-025 software model | DMA/PPU observables passed. Physical CPU-B timing, lane and PPU-revision parity unclaimed. |
| VIDEO-03 | SATISFIED under the selected falling-edge software contract | Public and SDL input paths and guest JOYP/IF cases passed. CPU-B pulse and sample phase unmeasured. |
| VIDEO-04 | SATISFIED | Extracted-byte smoke, player CTests, reused UAT 34. |
| VIDEO-05 | SATISFIED | Evidence classes are separate. Limitations are asserted. |

No orphaned Phase 3 requirements.

## Review, Security, Validation

- `03-REVIEW.md` (2026-10-10T16:02:18Z): clean, 0 critical / 0 warning / 0 info. `03-REVIEW-DISPOSITION.md`: 8 findings, 0 open. IN-01, IN-02 and IN-03 fixed by PR #54. WR-02 remains skipped by intent (a stale verified archive/receipt pair must not survive a failed run); I did not re-adjudicate it and it affects no VIDEO-xx truth.
- `03-SECURITY.md`: status verified, 0 open threats of 40.
- `03-VALIDATION.md`: status validated, nyquist_compliant true.

## Evidence-class statement (AGENTS.md)

- Software-model and regression evidence: 184/184 core and 51/51 player tests, with independent guest-visible expectations under D-025.
- User observation: UAT test 34 (owner saw the packaged window respond to Z press and release), reused as recorded. Perceptual window evidence rests on that recorded observation.
- Hardware-backed evidence: none claimed. No physical DMG-CPU-B timing or lane, JOYP pulse/sample phase, or PPU-revision measurement exists for Phase 3.
- Test-coverage limit: the `read_rom_file` `close()`-failure branch is verified by inspection only.

## Human Verification Required

None. The recorded UAT is reused and no new manual UAT is requested.

## Gaps Summary

No must-have gap. The PR #54 changes are consistent with the Phase 3 goal and covered by passing tests and hosted CI, apart from the inspection-only `close()` branch noted above. Residual limits are explicit: software-model scope for VIDEO-02/03 and no physical hardware qualification.

---

_Verified: 2026-10-10T16:04:13Z_
_Verifier: the agent (gsd-verifier)_
