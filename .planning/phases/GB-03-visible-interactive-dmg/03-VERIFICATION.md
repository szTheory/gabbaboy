---
phase: GB-03-visible-interactive-dmg
verified: "2026-10-10T01:55:17Z"
status: passed
score: 5/5 roadmap truths verified
covered_files:
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
covered_digest: "v3:sha256:da98944bc45fc9ef2272a5727c13c0c41a5c2968f6c0a59aee6ae73d69de5b4b"
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
**Verified:** 2026-10-10T01:55:17Z against committed clean HEAD `9832ba441d620b37b3e1e9ad87bed0e6f1129a5d` (branch `gsd/phase-03-verification-refresh`).
**Status:** passed
**Re-verification:** Yes, freshness refresh. The prior report (status passed, 5/5, at 0403b71) had no `gaps:`. It went stale because the verified-player output helper and `verify-phase3-player.sh` changed (eb96902, all-or-nothing archive+receipt publication). The branch then merged origin/main (O_NONBLOCK FIFO ROM-open hardening in `src/player/session.c`, #43). `.github/workflows/release.yml` joined the covered set. No plans were re-executed. The re-run commands below were run by this verifier and not taken from SUMMARY or orchestrator claims.

## User Flow Coverage

| Step | Expected | Evidence | Status |
|---|---|---|---|
| Launch a legal fixture | The original ROM-only demo opens and shows its frame. | `fixtures/visible-demo/manifest.json` records original project-authored assembly, MIT license, ROM digest, bootless DMG profile. The extracted-byte smoke this run loaded the packaged demo. | VERIFIED |
| Press and release a mapped key | Timestamped input reaches the guest and changes the tile. | This run's smoke printed "SDL Z-down rendered the darker demo tile and Z-up restored the lighter tile". The recorded owner observation in 03-UAT.md test 34 (holding Z darkens the tile, release restores it) is reused, not repeated. | VERIFIED |
| Inspect video evidence | Composition, raster timing, DMA/input, and gameplay have distinct evidence. | Separate registered `frame_composition_*`, `ppu_timing_*`, DMA and JOYP guest cases passed in 179/179. `docs/dmg-video-evidence.md` is the ledger. | VERIFIED (declared software model) |
| Basic player controls | Resize, pause, reset, open, quit. | 51/51 optional player CTests passed, including session, presentation, input and reset_transition. The smoke also covered replacement lock conflict, save retry, cancel and continue. | VERIFIED |
| Understand support limits | Help, docs and package state the supported audio and save scope and the limits. | `src/player/limitations.h` and `test_limitations` are in the passing player set; the smoke rejects false hardware claims. | VERIFIED |

## Goal Achievement

| # | Roadmap truth | Status | Evidence |
|---|---|---|---|
| 1 | VIDEO-01: BG/window/sprite composition and dot-sensitive LCD/STAT/fetch behavior are separately demonstrated. | VERIFIED | Registered `frame_composition_*` and `ppu_timing_*` cases in `tests/test_ppu.c` passed in this run's 179/179 CTest. |
| 2 | VIDEO-02: Model-specific OAM DMA, VRAM/OAM restrictions and CPU/PPU/DMA contention results. | VERIFIED (D-025 software-model scope) | `tests/test_dma.c` cases passed. The ledger scopes outcomes to the confidence-qualified D-025 model. No physical DMG-CPU-B lane/timing or PPU-revision measurement is claimed. |
| 3 | VIDEO-03: Timestamped joypad transitions are deterministic through the public API and the SDL path. | VERIFIED (selected falling-edge software contract) | `tests/test_joypad.c` and the JOYP guest cases passed. The SDL Z-down/up smoke covers the keyboard path. Exact CPU-B pulse qualification and sample phase remain unmeasured. |
| 4 | VIDEO-04: Open and play a permissioned fixture, resize with aspect/integer scaling, pause, reset, quit, actionable errors. | VERIFIED | Player CTests 51/51 and extracted-byte smoke passed. UAT test 34 is reused. |
| 5 | VIDEO-05: Automated checks distinguish composition, timing and gameplay; the preview states its audio/persistence scope and limits. | VERIFIED | Separate suites passed. `test_limitations` and the package metadata checks passed. Audio and MBC1 battery-save scope is stated and a fresh-process MBC1 continuation passed. |

**Score:** 5/5 roadmap truths verified (0 present-but-behavior-unverified).

## What Changed Since The Prior Report, And Whether It Holds

| Change | Check | Result |
|---|---|---|
| All-or-nothing archive+receipt publication in the verified-player helper | `python3 tests/scripts/test_verified_player_output_dir.py` | 20/20 pass (was 8/8). This covers equal, ancestor and descendant paths, symlinks, roots, name collisions, publication failure and withdrawal reporting. |
| Review fixes 91d11d4 and 8151a75 (release output dir, withdrawal failures not swallowed, no masking of the original error) | `.github/workflows/release.yml:620` sets `GBB_VERIFIED_OUTPUT_DIR="$RUNNER_TEMP/release-player-downloaded"`. `preview.yml:216` uses `${{ runner.temp }}/...`. `test_workflows_place_verified_output_outside_the_checkout` enforces this across all workflows. It passed in the 20/20. | Wired and test-guarded |
| O_NONBLOCK FIFO-safe ROM open, merged from #43 | `src/player/session.c:104` and `:315` use `O_RDONLY\|O_CLOEXEC\|O_NOFOLLOW\|O_NONBLOCK`. The session tests passed in 51/51. | Present and exercised by the test set |

## Required Artifacts

| Artifact group | Status | Details |
|---|---|---|
| Core/API and optional SDL player | VERIFIED | Built and linked in the phase1 preset. The player lane built with SDL 3.4.18. |
| PPU/DMA/JOYP/tracer tests and inventories | VERIFIED | `tests/expected-tests.txt` and `tests/player/expected-tests.txt` are fail-closed inventories. The player helper test `player_verified_output_directory` is registered (test 230 passed). |
| Original interactive fixture | VERIFIED | The manifest digest is checked by CTest, and the packaged demo ran. |
| Evidence and support documentation | VERIFIED | The ledger separates documentation, software policy and physical observation. |
| Package and consumer workflow | VERIFIED as wired and locally run | See Behavioral Spot-Checks. No hosted-CI result exists for this revision and none is claimed. |

## Key Link Verification

| From | To | Via | Status |
|---|---|---|---|
| PPU/core run | Public frame API and guest tests | Dot progress, completed frame copy, independent pixel and timestamp assertions | WIRED |
| DMA/PPU scheduling | DMA guest suite | FF46 state, DMA deadlines, access gating | WIRED |
| Public event API | JOYP guests | Timestamped queue to FF00/IF.4 reads | WIRED |
| SDL keyboard | Public event API | Scancode mapping, smoke Z-down/up | WIRED |
| Frame and fixture | SDL renderer | Copied shade frame to texture to renderer; smoke asserts shades | WIRED |
| Package workflows (preview.yml, release.yml) | `verify-phase3-player.sh` and helper | `GBB_VERIFIED_OUTPUT_DIR` under runner temp, guarded by test | WIRED |
| Limitation source | Help, docs, metadata | Shared capability statement, `test_limitations` | WIRED |

## Data-Flow Trace (Level 4)

| Artifact | Data | Source | Real data | Status |
|---|---|---|---|---|
| SDL display | Frame pixels | Guest ROM, PPU, completed frame, player copy, SDL texture | Yes | FLOWING (smoke asserts rendered shades) |
| Guest joypad | FF00 / IF.4 and tile | SDL/public timestamped input, instance JOYP state, guest polling, PPU frame | Yes | FLOWING |
| Fixture | Guest program bytes | Checked-in assembly, manifest digest, ROM-only loader | Yes | FLOWING |

## Behavioral Spot-Checks (run by this verifier at HEAD 9832ba4, macOS)

| Behavior | Command | Result | Status |
|---|---|---|---|
| Core inventory | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` | 179/179 passed, including `preview_package_smoke` | PASS |
| Output-dir helper | `PYTHONDONTWRITEBYTECODE=1 python3 tests/scripts/test_verified_player_output_dir.py` | 20 tests OK | PASS |
| Player and package gate | `GBB_VERIFIED_OUTPUT_DIR=<scratch> bash tests/scripts/verify-phase3-player.sh --build-package` | 51/51 optional player CTests passed. Extracted-byte smoke passed for SDL 3.4.18: Z-down/Z-up shade transition, dummy-audio recovery, guest audio, fresh-process MBC1 continuation. `source_revision=9832ba441d620b37b3e1e9ad87bed0e6f1129a5d`. Package SHA-256 `8521d5d3cce9b686de23dc38df9cd5c080f94019c425506d7b4d3097dc9d37cd`. | PASS |

Package hash note: this run's SHA-256 differs from the orchestrator-observed `2ce29970...`. Both come from independent local builds in different directories at the same source revision. The packaged bytes are not asserted to be bit-reproducible across builds, so neither hash is a release identity. The extracted-byte smoke verifies each build's own bytes. A reproducible-build claim, if wanted, needs a separate check.

The working tree stayed clean apart from a transient `tests/scripts/__pycache__/`, which was removed.

## Probe Execution

No Phase 3 plan declares a probe. `tests/scripts/probe-mooneye-candidate.sh` belongs to Phase 2.

## Requirements Coverage

Every requirement ID declared in the PLAN frontmatters appears in REQUIREMENTS.md. The traceability rows (lines 108-112) and the checked boxes (lines 32-36) match.

| Requirement | Source plans | Status | Evidence |
|---|---|---|---|
| VIDEO-01 | 01, 02, 07 | SATISFIED | Separate composition and PPU timing cases passed. |
| VIDEO-02 | 03, 10, 12, 13 | SATISFIED within the D-025 software model | DMA/PPU observables passed. Physical CPU-B timing and lane and PPU-revision parity are unclaimed. |
| VIDEO-03 | 01, 04, 05, 07, 10, 13 | SATISFIED under the selected falling-edge software contract | Public and SDL input paths and the guest JOYP/IF cases passed. CPU-B pulse and sample phase are unmeasured. |
| VIDEO-04 | 05, 06, 09, 13 | SATISFIED | Extracted-byte smoke and reused UAT 34. |
| VIDEO-05 | 01, 02, 03, 05, 06, 07, 08, 09, 11 | SATISFIED | Evidence classes are separate. Limitations are asserted. |

No orphaned Phase 3 requirements. VIDEO-01 through VIDEO-05 are all claimed by at least one plan.

## Review, Security, Test Quality

- 03-REVIEW.md reports 0 critical, 0 warning and 3 deferred info. 03-REVIEW-DISPOSITION.md lists 8 findings with 0 open: CR-01, WR-01, WR-01-followon and IN-04 fixed, WR-02 skipped, IN-01/02/03 deferred. The deferred items are non-blocking: IN-01 is a misleading close() message and a missing O_NOCTTY in `read_rom_file`, IN-02 a duplicated test fixture, IN-03 narrow test coverage of withdrawal reporting.
- WR-02 ("prepare clears the previous verified set before republishing") is recorded as skipped. I did not re-adjudicate it. It concerns publication ordering and does not affect any VIDEO-xx truth.
- 03-SECURITY.md records 40/40 threats closed (carried forward; the changed files are the helper, script, workflow and the session.c open flags, all covered by the passing tests above).
- No disabled or skipped requirement-linked tests were observed in the run. Expected images and guest observations are independently authored.

## Evidence-class statement (AGENTS.md)

- Software-model and regression evidence: 179/179 core tests and 51/51 player tests, including independent guest-visible expectations under D-025.
- User observation: UAT test 34 (owner saw the packaged window respond to Z press and release), reused as recorded.
- Hardware-backed evidence: none claimed. No physical DMG-CPU-B timing or lane, JOYP pulse/sample phase, or PPU-revision measurement exists for Phase 3.
- Hosted CI: none exists for this revision. The workflow wiring is verified statically and by the local scripts only. Required checks must be satisfied on the PR before merge.

## Human Verification Required

None. The recorded UAT is reused, and no new manual UAT is requested.

## Gaps Summary

No must-have gap. The refreshed output-directory publication, the release workflow contract and the FIFO-safe ROM open changes are consistent with the Phase 3 goal and are covered by passing tests. Residual limits are explicit: software-model scope for VIDEO-02/03, no physical hardware qualification, and no hosted-CI proof for this revision.

---

_Verified: 2026-10-10T01:55:17Z_
_Verifier: the agent (gsd-verifier)_
