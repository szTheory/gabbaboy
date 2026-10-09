---
phase: GB-03-visible-interactive-dmg
verified: "2026-10-09T13:17:53Z"
status: human_needed
score: 4/5 roadmap truths verified
covered_files:
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
  - src/player/main.c
  - src/player/session.c
  - src/player/session.h
  - tests/CMakeLists.txt
  - tests/expected-tests.txt
  - tests/player/CMakeLists.txt
  - tests/player/test_input.c
  - tests/player/test_presentation.c
  - tests/player/test_session.c
  - tests/test_dma.c
  - tests/test_joypad.c
  - tests/test_ppu.c
  - tests/test_tracer.c
covered_digest: "v3:sha256:2ee4daeee3bc578ce1cb8e7b7ea5c7de469773132f2ff484e5f6dc76eeb17189"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 5/5
  gaps_closed: []
  gaps_remaining: []
  regressions:
    - "VIDEO-04 packaged visibility and keyboard response need confirmation against the current player revision after later player/input changes."
decision_coverage:
  honored: 14
  total: 14
  not_honored: []
human_verification:
  - test: "On a display-equipped Mac, launch the current packaged player with the bundled legal demo, confirm the demo is visible, then hold and release Z."
    expected: "The packaged window displays the demo; holding Z darkens the target tile and releasing Z restores its lighter shade."
    why_human: "The 2026-10-08 user observation verifies the package tested then, but Phase 5 changed keyboard aggregation and the app event path since that observation. Current automated input and offscreen-renderer tests cannot establish visible window presentation or live keyboard delivery for the current package."
---

# Phase 3: Visible Interactive DMG Verification Report

**Phase Goal:** As a Mac user, I want to play a legal GB ROM with timed input and video evidence, so that I can verify the DMG preview.
**Verified:** 2026-10-09T13:17:53Z
**Status:** human_needed
**Re-verification:** Yes — after later player changes

## User Flow Coverage

User story: “As a Mac user, I want to play a legal GB ROM with timed input and video evidence, so that I can verify the DMG preview.”

| Step | Expected | Evidence | Status |
|---|---|---|---|
| Open and play the fixture | The original, legal ROM loads and produces video. | `fixtures/visible-demo/manifest.json`, fixture digest/gameplay tests, current player session and rendering paths. The 2026-10-08 UAT directly observed the packaged demo, but that observation predates later player changes. | PRESENT; current package visibility needs human confirmation |
| Press and release a control | Timestamped Z events reach the guest and change the visible tile. | `player_input_key` maps Z to A, event handling routes SDL key events, tests cover input mapping and queue admission; `joypad_interrupt` covers the public API software contract. | PRESENT; current live input needs human confirmation |
| Verify video evidence | Composition, timing and gameplay are separately evidenced. | Independent `frame_composition_*`, `ppu_timing_*`, DMA/PPU and gameplay guest tests; evidence matrix separates claims. | VERIFIED |
| Confirm the preview outcome | The current packaged Mac window is visible and responds to a mapped key. | Prior user observation: holding Z darkened the tile and release restored it. Phase 5 subsequently modified `src/player/input.c` keyboard aggregation and `src/player/main.c` event integration. Current phase1 suite passed 179/179, but automated tests do not exercise a visible packaged window. | NEEDS HUMAN |

**User-story outcome:** Not fully verified against the current player revision; the current packaged window and live key response need one Mac observation.

## Goal Achievement

| # | Roadmap truth / requirement | Status | Evidence |
|---|---|---|---|
| 1 | VIDEO-01: Background/window/sprite composition and dot-sensitive LCD/STAT/fetch behavior are separately demonstrated. | VERIFIED | `tests/test_ppu.c` has independent authored frame composition and guest timestamp cases; registered test inventory and supplied fresh 179/179 phase1 result support current core coverage. `docs/dmg-video-evidence.md` labels software model scope. |
| 2 | VIDEO-02: DMA, access restrictions and CPU/PPU/DMA contention produce expected model-specific outcomes. | VERIFIED (D-025 model) | Named `dma_active_mode_matrix`, `dma_ppu_overlap`, `dma_ppu_word_boundaries`, and `dma_ppu_cpu_collision` guests assert CPU/PPU/DMA observations and partition behavior. No physical CPU-B lane/timing or universal PPU-revision claim is made. |
| 3 | VIDEO-03: Timestamped joypad selection/interrupt behavior is deterministic through API and SDL keyboard path. | VERIFIED (selected falling-edge software contract) | `tests/test_joypad.c#joypad_interrupt` asserts FF00/IF outcomes, selected/unselected edges, sticky IF, selector/shared-row controls, ordering and partition equivalence. SDL Z mapping and queueing are covered in `tests/player/test_input.c`; live current-package response remains part of truth 4. Exact CPU-B pulse qualification/sample phase remains unmeasured. |
| 4 | VIDEO-04: A Mac user can open/play a fixture, resize, pause, reset, quit and receive actionable errors. | NEEDS HUMAN | Player code includes fixture/session loading, event handling, layout/presentation and controls. UAT 33/33 and user observation are valid for the package tested on 2026-10-08. Later changes to keyboard aggregation and event integration mean current packaged visibility/input cannot be inferred from that observation; no current display capture is available. |
| 5 | VIDEO-05: Composition, timing and gameplay evidence are distinct and incomplete audio/persistence support is labeled. | VERIFIED | `docs/dmg-video-evidence.md`, `docs/preview.md`, fixture manifest, limitation tests and separately named guest cases cover provenance, model bounds and preview limitations. |

**Score:** 4/5 roadmap truths verified; 1 requires current-revision human observation.

## Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `src/core/gabbaboy.c`, public API header | Timed PPU, DMA, input and bounded frame operations | VERIFIED | Per-instance implementation is consumed by player and guest tests; supplied current full CTest run passed 179/179. |
| `tests/test_ppu.c`, `tests/test_dma.c`, `tests/test_joypad.c`, `tests/test_tracer.c` | Independent composition/timing/contention/input/gameplay expectations | VERIFIED | Tests are registered in CMake and expected inventory; current suite receipt is 179/179. |
| `src/player/main.c`, `src/player/input.c`, session/presentation tests | SDL window, frame presentation, timed controls and session actions | PRESENT, behavior needs human | Code and automated controls exist; current visible package and live key are not observed. |
| `fixtures/visible-demo/*` | Legal, reproducible original interactive ROM | VERIFIED | Source, rights, manifest, digest and checked-in ROM connect to fixture tests and player default. |
| `docs/dmg-video-evidence.md`, `docs/preview.md` | Evidence boundaries and limitation labels | VERIFIED | Explicitly distinguish software-model and physical hardware evidence and label preview limitations. |

## Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| Guest/API core | PPU and frame assertions | Timed guest execution and caller-owned copied frames | WIRED | Composition and PPU timing tests use the production implementation. |
| Core DMA/PPU | DMA guest tests | FF46 transfer, access gating, per-dot arbitration | WIRED | D-025 cases assert destination bytes, pixels and CPU reads under the adopted model. |
| Public input API | JOYP guest tests | Queued timestamps → button state → FF00/IF.4 | WIRED | Guest reads and IF observations are asserted by named cases. |
| SDL keyboard event | `player_input_key` → core input API | Scancode mapping and timestamped event queue | WIRED; live behavior pending | Source path is connected and automated mapping tests exist; packaged interaction needs human observation after player changes. |
| Core frame | SDL texture/window | copied shade frame → texture update → renderer presentation | WIRED; visible output pending | Current player invokes the render/present path; offscreen checks cannot prove an OS-visible window. |
| Owned fixture | player and tracer | bundled/default path, digest and gameplay protocol | WIRED | Manifest, binary, tracer and packaged player reference the same owned demo. |

## Data-Flow Trace (Level 4)

| Artifact | Data variable | Source | Produces real data | Status |
|---|---|---|---|---|
| Player screen | shade frame / texture pixels | Core PPU completed frame copied into player buffer, uploaded to SDL texture, presented | Yes | FLOWING; perceptual visibility not observed at current revision |
| Guest joypad | FF00 and IF.4 state | Timestamped API/SDL events update per-instance button/select state and selected falling edges | Yes | FLOWING under software contract |
| ROM fixture | Guest program bytes | Checked-in original binary tied to source/build digest | Yes | FLOWING |

## Behavioral Spot-Checks

| Behavior | Evidence | Result | Status |
|---|---|---|---|
| Full current source build and registered phase1 suite | Fresh current-branch receipt supplied for `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --no-tests=error` | 179/179 passed | PASS |
| Composition, PPU timing, DMA/PPU and JOYP model cases | Named cases in current CTest inventory and prior current-source verification | Passed; exact CPU-B applicability remains bounded | PASS within declared model |
| SDL input mapping and offscreen presentation | Player input/presentation tests and player smoke evidence | Automated paths pass; no live window observation | HUMAN for visible package |

## Probe Execution

No Phase 3 plan declares a probe. The Mooneye candidate probe belongs to Phase 2 and is not evidence for this phase.

## Requirements Coverage

| Requirement | Source plans | Status | Evidence |
|---|---|---|---|
| VIDEO-01 | 03-01, 03-02 | SATISFIED | Independent composition and raster-timing guest cases. |
| VIDEO-02 | 03-03, 03-10, 03-12, 03-13 | SATISFIED under D-025 software model | Active-DMA matrix, overlap, word boundaries and same-half-dot outcomes; physical CPU-B behavior remains unmeasured. |
| VIDEO-03 | 03-01, 03-04, 03-05, 03-10, 03-13 | SATISFIED under selected falling-edge contract | Core guest assertions plus SDL mapping/queue path; CPU-B sampling remains unmeasured. |
| VIDEO-04 | 03-05–03-09 | NEEDS HUMAN | Earlier packaged observation is real evidence for the package then tested; later player/input changes require one current package observation. |
| VIDEO-05 | 03-01, 03-02, 03-05, 03-06, 03-08, 03-09, 03-11 | SATISFIED | Separate evidence classes and visible audio/persistence limitations are present. |

All five Phase 3 VIDEO requirements are represented in plans; none is orphaned. The 14/14 decision-coverage result is carried forward from the current Phase 3 decision audit. No later milestone phase is scheduled to perform the missing current-revision visible-window observation, so it is not deferred.

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| None | — | No blocking debt markers, placeholder implementation or empty production path identified in the phase implementation review. | — | Existing returns/null initialization inspected are normal error or state defaults. |

The current code review is reported clean. Security review reports zero blocking threats; one medium preview-limitations entry remains below the blocking threshold. UI review scored 16/24 and could not capture a live window; that reinforces the human check and is not evidence of a code failure.

## Human Verification Required

### Current packaged preview and key response

**Test:** On a display-equipped Mac, launch the current packaged player with its bundled legal demo. Confirm the preview is visible, hold Z, then release it.
**Expected:** The target tile darkens while Z is held and returns to its lighter shade on release.
**Why human:** UAT's 2026-10-08 user observation confirms this behavior on the package tested then. Since that observation, Phase 5 changed keyboard aggregation and the player event path. Automated input mapping and software-renderer checks do not show that the current packaged app opens visibly or delivers the live key to the guest.

No physical DMG-CPU-B behavior is claimed: VIDEO-02/03 are software-model evidence under D-025, with exact CPU-B timing/lane and revision parity limitations retained.

## Gaps Summary

No implementation gap is established. The code, data paths and automated tests are present, and the current supplied build/test evidence passes. The one open acceptance item is whether the current packaged macOS window visibly presents and responds to live Z input after later player changes. Keep Phase 3 pending until that observation is recorded; then refresh this verification. The previous direct UAT observation is preserved as evidence for the earlier tested package, not discarded or generalized to the changed current player.

---

_Verified: 2026-10-09T13:17:53Z_
_Verifier: the agent (gsd-verifier)_
