---
phase: GB-03-visible-interactive-dmg
verified: 2026-10-08T00:38:55Z
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
  - .planning/phases/GB-03-visible-interactive-dmg/03-REVIEW.md
  - .planning/phases/GB-03-visible-interactive-dmg/03-VALIDATION.md
  - docs/dmg-video-evidence.md
  - src/core/gabbaboy.c
  - tests/CMakeLists.txt
  - tests/expected-tests.txt
  - tests/test_dma.c
  - tests/test_joypad.c
  - tests/test_ppu.c
covered_digest: "v3:sha256:7f3bf9d2b0a5dee5e485ace99c8cf44dce6c73119d6642007011026d9baff48a"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 2/5
  gaps_closed:
    - "VIDEO-02: source-backed deterministic software behavior for active-DMA CPU VRAM/OAM access, mode-2 overlap, mode-3 fetch words, same-half-dot DMA/PPU/CPU results, and partition invariance is covered under D-025."
    - "VIDEO-03: the selected falling-edge IF.4 software contract is covered for timestamped public input and wired SDL input events, including sticky IF, IE independence, selector changes, shared pins, ordering, and partition invariance."
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "Open the packaged player and demo on a display-equipped Mac, then press one mapped key."
    expected: "The demo is visibly rendered and responds to the mapped key."
    why_human: "SDL reports that this environment has no display; offscreen software-renderer and input-queue tests cannot prove a visible macOS window or live keyboard response."
decision_coverage:
  honored: 14
  total: 14
  not_honored: []
---

# Phase 3: Visible Interactive DMG Verification Report

> Historical audit details below are retained for traceability and are superseded by the latest goal-backward re-verification at the end of this file. Use the frontmatter and latest section for current status.

**Phase Goal:** As a Mac user, I want to play a legal GB ROM with timed input and video evidence, so that I can verify the DMG preview.
**Verified:** 2026-10-07T23:12:54Z
**Implementation revision:** 427313a613f38676358638557676b9f72a188bd2 plus the current working-tree test and planning changes; no current-head hosted CI claim.
**Historical status (superseded):** gaps found — this result predates Plan 03-13 and the current code-review fixes.
**Historical re-verification:** After Plan 03-12 DMA gap closure.

## User Flow Coverage

| Step | Expected | Evidence | Status |
|---|---|---|---|
| Open preview | The macOS player loads the original legal 32 KiB ROM-only demo and presents a frame. | Current-source player smoke and fixture digest tests passed, but the smoke test uses SDL's software renderer; no actual app window was observed. | ⚠ NEEDS HUMAN — confirm a packaged player window opens and displays the fixture. |
| Press a control | A timestamped keyboard input reaches the guest and affects selected-row reads. | player_input_events and joypad_selection passed; SDL queues timed public events and guest reads active-low state. | ⚠ Partial — JOYP IF behavior is absent; no live keyboard interaction was observed. |
| See the preview | Composition and dot-timed LCD/STAT/fetch behavior have separate evidence. | Four composition and five timing tests plus scripted gameplay passed. | ⚠ NEEDS HUMAN for actual macOS window visibility; automated content checks passed. |
| Verify the preview claim | DMG-CPU-B behavior includes qualified DMA/PPU contention and input interrupts. | VIDEO-02 collision applicability and VIDEO-03 interrupt behavior remain open. | ✗ BLOCKED |

## Goal Achievement

| # | Roadmap truth | Status | Evidence |
|---|---|---|---|
| 1 | Background/window/sprite composition, LCD/STAT transitions, and dot-sensitive fetch are shown by separate cases. (VIDEO-01) | ✓ VERIFIED | frame_composition_bg, frame_composition_window, frame_composition_sprites, frame_composition_priority, and five ppu_timing_* cases passed (9/9); expected shades and bus timestamps are asserted separately. Software profile only; no physical CPU-B claim. |
| 2 | Guests observe model-specific OAM DMA, VRAM/OAM restrictions, and CPU/PPU/DMA contention results. (VIDEO-02) | ? UNCERTAIN — WARNING | Eight current-source DMA/startup/restart/readback/source/lock tests passed. No test asserts simultaneous active PPU/DMA collision outcomes. |
| 3 | Timestamped joypad transitions produce deterministic selection/interrupt behavior through API and SDL. (VIDEO-03) | ✗ FAILED — BLOCKER | Polling and SDL event scheduling work, but the core has no JOYP interrupt request path and tests do not assert IF bit 4. |
| 4 | A macOS user can play the legal fixture, resize, pause, reset, quit, and receive actionable errors. (VIDEO-04) | ? UNCERTAIN — WARNING | Current-source SDL build passed five focused input/layout/session/smoke/limitations tests, but these do not establish that the packaged application opens a visible macOS window and responds to live keyboard input. |
| 5 | Automated evidence separates composition, timing, and gameplay; preview labels audio/persistence limits. (VIDEO-05) | ✓ VERIFIED | Separate PPU/gameplay/fixture checks passed; current player limitation assertion and installed C/C++ package smoke passed; docs/preview.md names the limitations. |

**Score:** 2/5 roadmap truths verified; two are uncertain and one failed.

### Re-verification

- Previous status/score: gaps_found, 3/5.
- Closed subcases: M=1 startup access/first byte, active FF46 restart, latest readback, and replacement completion boundaries.
- Remaining: exact CPU-B simultaneous PPU/DMA outcomes, D-08 JOYP IF behavior, and the visible packaged-window/key check.
- No regressions found in the prior composition, PPU timing, player, and evidence-separation checks.

## Current-Source Validation

Configured with SDL 3.4.18 from the existing digest-checked prefix and built all 46 targets:

~~~sh
VERIFY_BUILD_DIR=$(mktemp -d /private/tmp/gabbaboy-phase3-verify.XXXXXX)
cmake -S . -B "$VERIFY_BUILD_DIR" -G Ninja \
  -DCMAKE_PREFIX_PATH="$PWD/build/phase3-player/prefix" \
  -DGABBABOY_BUILD_PLAYER=ON -DBUILD_TESTING=ON
cmake --build "$VERIFY_BUILD_DIR" --parallel 2
~~~

Fresh validation used `cmake --preset phase1`, `cmake --build --preset phase1 --parallel 2`, and `ctest --preset phase1 --output-on-failure`; the full core/package inventory passed 134/134. The generated inventory contains 149 cases, including player checks not selected by the `phase1` preset. The earlier focused current-source selection also passed 29/29 across PPU composition/timing, DMA/locks, joypad/gameplay/fixture evidence, player input/layout/session/smoke/limitations, and installed package relocation/consumer checks.

dma_start checks the first M=1 OAM instruction (B=$01) and first copied byte ($D7); it does not reproduce the upstream full B/C/D/E tuple. dma_restart checks $FF at restart+1272 and $01 at +1288 half-dots. FF46 tests check pinned $9F, $42, $8F, and $3F values. D-024's $8000–$DFFF source policy remains in force.

### Hosted Evidence Boundary

The previously cited successful CI run 37686137977 and preview run 37686137834 report headSha=fd62c48d84b8339435fefd008147f0c06f696e0e via gh run view. They are not runs for this verification revision (427313a613f38676358638557676b9f72a188bd2) and are not current-head CI evidence. Current-source local SDL build/tests passed; no current-head remote CI or downloaded-package qualification is claimed.

## Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| src/core/gabbaboy.c | Timed PPU, DMA, joypad behavior | PARTIAL | DMA/access behavior is implemented; JOYP selection/input state exists, but JOYP IF generation does not. |
| tests/test_ppu.c | Independent composition/timing assertions | VERIFIED | Separate registered value/timestamp cases; all nine selected checks passed. |
| tests/test_dma.c | Guest-visible DMA/access and qualified collision cases | PARTIAL | Sourced startup/restart/readback/source/lock behavior is exercised. dma_contention checks isolation/reset with PPU disabled. |
| tests/test_joypad.c | Public selection, deterministic queue and qualified IF cases | PARTIAL | Polling/ordering/partition checks pass; no IF case exists. |
| Player source and tests | SDL fixture launch, input, presentation, geometry | VERIFIED | Current-source SDL player built and five focused cases passed. |
| Original demo and manifest | Legal interactive ROM and reproducible identity | VERIFIED | Fixture digest and gameplay tracer passed. |
| docs/dmg-video-evidence.md | Source-to-case matrix and exclusions | VERIFIED | Pinned sources, provenance limit, D-024 conflict, and unresolved collision/JOYP behavior are explicit. |

GSD artifact checks passed 29/29 structured entries in Plans 03-01–03-11. Plan 03-12 lists prose artifacts, so the verifier returned 0/0 there; these were checked manually against code, tests, inventory, and docs. Some automated key-link queries could not trace C/linker relationships; the connections below were manually traced. The Plan 03-04 link to JOYP IF assertions is genuinely not wired.

## Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| src/core/gabbaboy.c | tests/test_dma.c | FF46 gate/start state to guest-observed transfer | WIRED | FF46 is an active-DMA exception; restart/readback/start cases passed. dma_hram checks other blocked accesses remain restricted. |
| DMA tests | CMake and expected inventory | Named test registration | WIRED | Plan 03-12 names are registered; CMake inventory check succeeds. |
| Evidence matrix | Pinned Mooneye sources | Source assertions and provenance | WIRED | Exact startup/restart/readback paths are cited; suite evidence is distinguished from project hardware observation. |
| Public input API | Core joypad state | Timed events → button state → FF00 | WIRED | Guest polling tests passed. |
| Core JOYP | Joypad IF tests | Button/selection changes → IF bit 4 | NOT WIRED | No IF update in core and no FF0F assertion in tests. |
| SDL keyboard/player | Public API and SDL renderer | Timed event and completed frame | WIRED | Current-source input and smoke tests passed. |

## Fresh goal-backward audit — 2026-10-08

**Result:** 4/5 roadmap truths verified; `gaps_found`. Phase 3 remains in progress because VIDEO-04 requires an actual display observation.

| # | Roadmap truth | Status | Current evidence |
|---|---|---|---|
| 1 | VIDEO-01 composition and dot-sensitive PPU behavior | VERIFIED | Existing independent frame composition and PPU timing guest tests pass. |
| 2 | VIDEO-02 DMA, access restrictions, and CPU/PPU/DMA outcomes | VERIFIED for the declared D-025 software model | `dma_active_mode_matrix`, `dma_ppu_overlap`, `dma_ppu_word_boundaries`, and `dma_ppu_cpu_collision` pass. The matrix covers active DMA and PPU modes 0–3; controls and pixels verify scan suppression and aligned-word fetch; the exact guest tie asserts DMA byte, rendered pair, CPU `$FF`, and partition equivalence. CPU-B lane/timing and universal revision parity remain unmeasured. |
| 3 | VIDEO-03 timestamped joypad selection and interrupt behavior | VERIFIED for the documented selected falling-edge software contract | Six focused `joypad_*` cases pass, including FF0F/FF00 observations, sticky IF, IE=0, selected/unselected pins, held-selector, shared pins, equal-time ordering, and partition equivalence. CPU-B pulse qualification and sample phase remain unmeasured. |
| 4 | VIDEO-04 visible macOS packaged player and live input | NEEDS HUMAN | The available environment has no SDL display (`SDL_Init: The video driver did not add any displays`); a live window/key response was not observed. Earlier hosted package receipts are stale for this revision. |
| 5 | VIDEO-05 evidence separation and limitation labeling | VERIFIED | Source provenance, original guest results, and hardware/software evidence boundaries are recorded in `docs/dmg-video-evidence.md`; the full SDL-free core inventory passed 139/139. |

The source-backed behavior in VIDEO-02/03 follows the adopted D-025 confidence-qualified policy, not a claim of physical DMG-CPU-B qualification. Fresh local validation at implementation commit `6901129` ran the complete `phase1` CTest inventory: 139/139 passed; `git diff --check` passed. No current-head hosted CI or hardware observation is claimed. The only remaining phase truth is the actual packaged-window/demo/key observation on a display-equipped Mac.

## Data-Flow Trace

| Path | Source → output | Status |
|---|---|---|
| SDL input → guest FF00 | Scancode → timestamped event → instance button state → selected active-low rows | FLOWING for polling; disconnected from JOYP IF |
| Guest → player frame | CPU/PPU state → copied shade frame → SDL texture/render | FLOWING; PPU and player smoke checks passed |
| Demo source → ROM | Pinned build recipe → checked-in ROM bytes/digest | FLOWING; fixture digest/gameplay checks passed |

## Behavioral Spot-Checks

| Behavior | Current-source check | Result |
|---|---|---|
| Composition and PPU timing | Nine named frame_composition_* and ppu_timing_* tests | 9/9 passed |
| DMA startup/restart/readback, source, HRAM, PPU locks | Eight named dma_* tests | 8/8 passed; no simultaneous collision claim |
| Joypad, gameplay, fixture identity | Six named joypad/tracer/digest tests | 6/6 passed; no IF result asserted |
| SDL input, geometry, replacement, limitations, frame smoke | Five named player_* tests | 5/5 passed |
| Installed package relocation and C/C++ consumers | preview_package_smoke | 1/1 passed |

## Probe Execution

No probe path is declared in the Phase 3 plans/summaries. tests/scripts/probe-mooneye-candidate.sh targets Phase 2 CPU fixture candidates and was not substituted for Phase 3 evidence.

## Requirements Coverage

| Requirement | Plans | Status | Evidence |
|---|---|---|---|
| VIDEO-01 | 03-01, 03-02 | SATISFIED | Nine current-source composition/timing cases passed. |
| VIDEO-02 | 03-03, 03-10, 03-12 | OPEN | DMA subcases pass; exact simultaneous CPU-B PPU/DMA outcomes remain unqualified. |
| VIDEO-03 | 03-01, 03-04, 03-05, 03-10 | BLOCKED | Polling/input pass; no JOYP IF path or exact expected interrupt cases. |
| VIDEO-04 | 03-05–03-09 | NEEDS HUMAN | Automated player checks passed; the packaged macOS window and live keyboard path were not observed. |
| VIDEO-05 | 03-01, 03-02, 03-05, 03-06, 03-08, 03-09, 03-11 | SATISFIED | Separate named evidence and explicit limitations are present and tested. |

Every Phase 3 VIDEO requirement appears in a plan; none is orphaned. Decision coverage honored 14/14 trackable decisions. No later phase specifically closes the two evidence gaps; neither is deferred.

## Test Quality Audit

| Test files | Active/skipped | Circular | Assertion level | Verdict |
|---|---|---|---|---|
| tests/test_ppu.c, tests/test_dma.c | Active; 0 skipped | No | Expected values/timestamps | Sufficient for sourced cases; collision outcomes absent |
| tests/test_joypad.c | Active; 0 skipped | No | Guest-visible polling values | Insufficient for interrupt behavior; no IF assertion |
| tests/player/test_input.c | Active; 0 skipped | No | Exact event values/state | Sufficient for SDL mapping, not JOYP IF |
| Player presentation/session tests | Active; 0 skipped | No | Geometry/session behavior | Sufficient for automated paths |
| tests/test_tracer.c | Active; 0 skipped | No | Expected frame/gameplay values | Sufficient; no generated golden |

Disabled-test scan found none. No expected values are generated by the system under test. test_session.c writes temporary ROM inputs, not expected emulator output. No unreferenced TBD/FIXME/XXX markers or empty production implementations were found; return NULL matches are normal error paths and audio/persistence limitation text is intentional.

## Security and Human Limitations

### Plan 03-13 execution evidence (not a goal-backward verdict)

After the historical verification above, Plan 03-13 added a selected JOYP falling-edge IF.4 software model and an original guest for selected presses on P10–P13 plus an unselected-row control. It also added an original DMA/PPU overlap guest with baseline sprite pixels, a selected object whose modeled mode-3 fetch uses the aligned current DMA destination word, a later mode-2 entry suppressed during DMA, a next-line overlap, and separate DMA-byte/timestamp assertions. The pinned documentation and emulator-source provenance and exact model-policy boundaries are recorded in `docs/dmg-video-evidence.md` and `03-RESEARCH.md`.

Fresh local evidence at implementation commit `0f481ae` (with this documentation update pending) is: `joypad_` selection passed 6/6; `dma_ppu_overlap` passed 1/1; the selected PPU composition/timing and DMA/start/restart/lock set passed 16/16; the complete `phase1` inventory passed 136/136 with zero missing tests; and `git diff --check` passed. The JOYP test does not yet cover release, duplicate/shared-row/held-selector/second-edge IF behavior or JOYP run-partition equivalence. The DMA test does not yet cover all active-DMA PPU-mode access cells, every scan/fetch start/end boundary, word-update before/after, an exact DMA→PPU→CPU same-half-dot assertion, or partition splits at those events. Existing tests retain and pass the fresh-start M-cycle and FF46 read/restart exceptions. No dependency or third-party ROM was added.

The previous independent goal-backward result remains the historical baseline of `gaps_found`, 2/5 truths. It has not been updated from this execution record; a fresh goal-backward verification must inspect the current committed revision before changing roadmap truth or requirement status. VIDEO-04 still requires a packaged-window/key observation on a display-equipped Mac. No physical DMG-CPU-B measurement and no exact-head hosted CI result are claimed.

03-SECURITY.md still lists T-03-27 (“Preview limitations”) as an open medium issue below the high-severity blocking threshold. Current player_limitations passed, but this verification did not rerun downloaded-package metadata assertions or refresh that audit.

No physical DMG-CPU-B observation occurred. Mooneye documents DMG-family acceptance assertions and a CPU-B unit in its manually tested fleet, but retains no per-test/per-unit logs. The Nintendo manual and CPU-B reverse-engineered schematics do not establish exact JOYP sample phase. SDL smoke used a software renderer; no live macOS window was perceptually checked.

## Human Verification Required

Open the packaged player with its bundled legal demo ROM on macOS and confirm the preview is visibly drawn; press one mapped control and confirm the visible demo responds. This is the smallest useful human check for VIDEO-04 because the current automated smoke test exercises SDL's software renderer without establishing a visible OS window or live keyboard delivery. It does not close the CPU-B collision or JOYP interrupt gaps.

Follow-up attempt on 2026-10-07: the fresh current-source `gabbaboy-player` executable was launched from this environment, but SDL initialization returned `SDL_Init: The video driver did not add any displays`. No live window or key event could be observed here; the local display limitation is now confirmed. The earlier qualified package receipt is from `fd62c48d84b8339435fefd008147f0c06f696e0e` and remains stale for this source revision.

## Advisory (New Scope, Unevidenced)

Plan 03-13 supplies new source-backed software behavior and focused guest tests for VIDEO-02/03; those additional subcases must be included in the next goal-backward audit. The full mode/DMA access matrix, word-update/tie boundaries, three-way CPU/PPU/DMA guest outcome, and broader JOYP IF transition cases remain uncovered in the current plan execution evidence.

## Gaps Summary and Smallest Next Action

Plan 03-12 preserves the source-backed fresh DMA startup M-cycle and FF46 restart/readback exceptions. Plan 03-13 adds a source-selected JOYP IF.4 model and focused DMA/PPU scan/fetch guest evidence, but the planned full access matrix, exact update/tie boundaries, same-half-dot CPU/PPU/DMA guest outcome, and additional JOYP IF cases still need implementation or explicit narrowing. No exact CPU-B values are claimed.

For VIDEO-04, open the packaged app on a Mac with a display and confirm the demo is visible and responds to a mapped key. The next workflow action is a fresh goal-backward audit of the current committed Plan 03-13 evidence; it must retain the 2/5 baseline until it verifies a different result. Do not re-run gap planning before that audit. If it identifies executable software gaps, plan only those; if only true hardware/perceptual limits remain, keep them open without another churn loop.

Phase 3 remains in progress. Stop; do not advance to Phase 4.

---

_Verified: 2026-10-07T23:12:54Z_
_Verifier: gsd-verifier — current-source goal-backward audit_

## Current goal-backward verdict — 2026-10-08T00:26:01Z

This verdict supersedes every historical status, gap, and recommendation above. It was refreshed after Plan 03-13 implementation and the complete local CTest run.

| # | Requirement truth | Result | Evidence and boundary |
|---|---|---|---|
| 1 | VIDEO-01 composition and raster timing | PASS | Existing independent composition and PPU timing guests pass. |
| 2 | VIDEO-02 DMA, bus restrictions, and CPU/PPU/DMA behavior | PASS under D-025 software model | New original guests cover the active-DMA VRAM/OAM matrix in modes 0–3, scan overlap controls, DMA word-boundary pixels, one same-half-dot DMA/PPU/CPU outcome, and run-partition equivalence. Exact CPU-B byte lane/timing and PPU-revision parity remain unmeasured. |
| 3 | VIDEO-03 ordered JOYP selection/interrupt behavior | PASS under selected falling-edge software contract | Six JOYP cases assert FF00/FF0F outcomes, edge and no-edge cases, sticky IF, IE independence, equal-time ordering, and partition equivalence. CPU-B pulse-duration qualification and sample phase remain unmeasured. |
| 4 | VIDEO-04 visible packaged window and live key response | NEEDS HUMAN | SDL cannot add a display in this environment. The actual window/demo/key response remains unobserved. |
| 5 | VIDEO-05 independent evidence and limitations | PASS | Evidence classes and limitations are explicit; the SDL-free core suite is 139/139. |

**Fresh score:** 4/5. **Phase status:** incomplete; only VIDEO-04 remains open. The next exact workflow command is `$gsd-verify-work 3` after the display-based observation. No current-head hosted CI, physical CPU-B qualification, or live-window observation is claimed. The Phase 4 — MBC1 and Safe Battery Continuation — work has not started.

## Current goal-backward re-verification — 2026-10-08T00:38:55Z

This result supersedes the older evidence above. Verification targets current branch revision `eb31afd` (`fix(03-13): reset OAM scan cursor`) after the two review fixes. D-025 authorizes selecting and testing a deterministic source-backed software model for undocumented or revision-qualified behavior; it does not turn emulator agreement or documentation into a physical CPU-B measurement.

### User Flow Coverage

User story: “As a Mac user, I want to play a legal GB ROM with timed input and video evidence, so that I can verify the DMG preview.”

| Step | Expected | Evidence | Status |
|---|---|---|---|
| Open and play the fixture | The legal original demo loads and produces a frame. | Fixture digest/reproduction, gameplay tracer, player session and software-renderer smoke checks are registered and covered by the current suite. The packaged window cannot be displayed here. | NEEDS HUMAN for visible window |
| Press a control | Timestamped input reaches the guest and updates selected JOYP reads and IF.4 under the documented software contract. | `player_input_key` maps SDL scancodes to public queued events; original guests assert selected pin/IF behavior, while player input tests assert mapping and queue admission. | VERIFIED for software model; live key remains part of VIDEO-04 |
| Inspect video evidence | Composition, raster timing, and gameplay are separately asserted and limitations are visible. | Independent composition/timing/gameplay tests, fixture identity, and `docs/preview.md` limitation assertions are included in the phase inventory. | VERIFIED |
| Confirm the preview on a Mac | A visible packaged window shows the demo and responds to a mapped key. | No display is available; the attempted launch reports `SDL_Init: The video driver did not add any displays`. | NEEDS HUMAN |

**User-story outcome:** Not fully verified because the packaged preview could not be seen or operated on a display-equipped Mac.

### Roadmap Truths and Requirements Coverage

| # | Truth / requirement | Status | Evidence and boundary |
|---|---|---|---|
| 1 | VIDEO-01: composition, LCD/STAT transitions, dot-sensitive fetch | VERIFIED | Separate authored background/window/sprite/priority outputs and PPU timing guests assert expected pixels and timestamps. |
| 2 | VIDEO-02: model-specific DMA, access restrictions, CPU/PPU/DMA contention | VERIFIED under D-025 software model | `dma_active_mode_matrix`, `dma_ppu_overlap`, `dma_ppu_word_boundaries`, `dma_ppu_cpu_collision`, `dma_oam_entry39`, and `dma_oam_entry39_reset` assert access behavior, per-entry scan suppression, latched fetch words, selected same-dot ordering, and reset/partition behavior. The exact word/lane behavior on CPU-B and PPU-revision applicability remain unmeasured. |
| 3 | VIDEO-03: timestamped selection/interrupt behavior through public API and SDL keyboard path | VERIFIED under the selected falling-edge software contract | `joypad_interrupt` asserts FF00/FF0F outcomes for selected/unselected pins, selector changes, sticky IF, IE=0, duplicate/shared pins, event ordering, and partition equivalence. SDL mapping enqueues those same public input events; `player_input_events` covers mapping and admission. Manual low-duration guidance and CPU-B pulse/sample timing are not modeled or claimed. |
| 4 | VIDEO-04: packaged macOS user flow, sizing, controls, actionable errors | NEEDS HUMAN | Automated session, scaling, controls, error, and offscreen-renderer checks are present; actual visible window and live key response were unavailable because there is no SDL display. |
| 5 | VIDEO-05: distinct composition/timing/gameplay evidence and limitation labels | VERIFIED | Evidence matrix, original fixture identity, preview limitation text, and registered regression coverage are present. |

All five VIDEO requirements are claimed by plans; none is orphaned. Decision coverage reports all 14/14 trackable Phase 3 decisions honored. VIDEO-02/03 completion is bounded to the cited documented software model and repository event-order policy. There is no physical CPU-B qualification claim.

### Current Validation, Review, and Test Quality

- Full registered local CTest suite: **141/141 passed** at `eb31afd`; the code-review report records the same exact count. `git diff --check HEAD` passed for current tracked changes.
- Code review: **clean**, with 0 critical, 0 warning, 0 info findings across six reviewed implementation/test files; review confirms entry-39 scan and reset-cursor fixes and their named regressions.
- New focused model cases include `joypad_interrupt`, `dma_ppu_overlap`, `dma_ppu_word_boundaries`, `dma_ppu_cpu_collision`, `dma_active_mode_matrix`, `dma_oam_entry39`, and `dma_oam_entry39_reset`; all are registered in CMake and the fail-closed expected-test inventory.
- Test-quality scan: no disabled requirement tests, circular expected-value generation, or unreferenced `TBD`/`FIXME`/`XXX` markers found in reviewed phase changes. CPU/PPU/DMA pixels and bus values are authored expectations; emulator source is cross-check evidence, not the oracle.
- No Phase 3 probe is declared. The existing Mooneye candidate probe is Phase 2 and is not used as Phase 3 proof.
- Current-head hosted CI and downloaded-package qualification are not claimed. Earlier package receipts are for a different source revision.

### Human Verification Required

**Packaged preview visibility and live key response** — On a Mac with a display, launch the packaged player with its bundled legal demo, confirm the demo is visible, and press one mapped key. Expected: the visible demo responds. The current environment cannot perform this observation because SDL cannot add a display; no result is inferred from the offscreen renderer.

### Remaining Work

VIDEO-01/02/03/05 have current code and test evidence. VIDEO-02 and VIDEO-03 are complete only for D-025’s source-backed deterministic software rules, not measured DMG-CPU-B timing or universal hardware behavior. The only phase-level acceptance item still awaiting evidence is VIDEO-04’s visible packaged-window/key interaction. Keep Phase 3 open and do not advance to Phase 4 until that human check and final verification are done.

**Next command after the display check:** `$gsd-verify-work 3`.
