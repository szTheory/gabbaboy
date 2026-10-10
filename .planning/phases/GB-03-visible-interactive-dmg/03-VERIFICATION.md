---
phase: GB-03-visible-interactive-dmg
verified: "2026-10-09T22:37:25Z"
status: passed
score: 5/5 roadmap truths verified
covered_files:
  - .github/workflows/ci.yml
  - .github/workflows/preview.yml
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
  - tests/scripts/verify-phase3-player.sh
  - tests/scripts/verified_player_output_dir.py
  - tests/test_dma.c
  - tests/test_joypad.c
  - tests/test_ppu.c
  - tests/test_tracer.c
covered_digest: "v3:sha256:832ac6e22c4915733ffa76be28f581abf9bd751ba56a4c396e630bf8826aeee1"
behavior_unverified: 0
overrides_applied: 0
decision_coverage:
  honored: 14
  total: 14
  not_honored: []
---

# Phase GB-03: Visible Interactive DMG Verification Report

**Phase Goal:** As a Mac user, I want to play a legal GB ROM with timed input and video evidence, so that I can verify the DMG preview.
**Verified:** 2026-10-09T22:37:25Z against worktree HEAD `bb8fd654d03969e3d207fcdc92c345cc60be3298` plus its current dirty overlay.
**Status:** passed
**Verification mode:** Initial goal-backward pass. The previous report had no top-level `gaps:` section. This refresh checks the complete roadmap contract and fingerprints the current implementation inputs, including `.planning/config.json`, which selects the CMake regression command.

## User Flow Coverage

User story: “As a Mac user, I want to play a legal GB ROM with timed input and video evidence, so that I can verify the DMG preview.” The runtime user-story validator returned `true`.

| Step | Expected | Evidence in codebase | Status |
|---|---|---|---|
| Launch a legal fixture | A Mac user can open the original interactive ROM-only demo and see its frame. | `fixtures/visible-demo/manifest.json` identifies original project-authored assembly, MIT license, 32 KiB ROM digest, bootless DMG profile, and limitations. Current packaged-window observation is recorded in UAT test 34 (2026-10-09). | VERIFIED |
| Press and release a mapped key | Timestamped input reaches the guest and changes the rendered tile. | Public event queue → SDL scancode mapping → core joypad state → guest polling → copied frame → SDL render path is covered by player smoke. UAT test 34 records the owner's direct confirmation that holding Z darkened the tile and release restored it. | VERIFIED |
| Inspect video evidence | Composition, raster timing, DMA/input behavior, and gameplay have distinct evidence. | Separate registered `frame_composition_*`, `ppu_timing_*`, DMA/JOYP guest cases and `docs/dmg-video-evidence.md`; no screenshot substitutes for guest timing assertions. | VERIFIED within the declared software model |
| Use basic player controls | Resize, pause, reset, open, and quit are connected to the optional SDL player. | Player event/session/presentation tests and current extracted-package SDL smoke; bounded failed replacement preserves the active guest. | VERIFIED |
| Understand support limits | Help/package/documentation describe the current supported audio/save subsets and remaining limits accurately. | `src/player/limitations.h`, `docs/preview.md`, and package metadata identify scoped DMG-CPU-B software audio, standard MBC1 battery-save scope, and missing physical/revision/CGB/perceptual qualification. Phase 4/5 have since implemented some capabilities that Phase 3 originally planned to label absent. | VERIFIED |

## Goal Achievement

| # | Roadmap truth | Status | Evidence |
|---|---|---|---|
| 1 | VIDEO-01: Background/window/sprite composition and dot-sensitive LCD/STAT/fetch behavior are separately demonstrated. | ✓ VERIFIED | Production PPU and public frame path are exercised by registered guest tests. `tests/test_ppu.c` has independent expected shade images and separate timestamped mode/STAT/fetch cases; all `frame_composition_*` and `ppu_timing_*` inventory entries passed in the current 179-test CTest run. |
| 2 | VIDEO-02: Guests observe model-specific OAM DMA, VRAM/OAM restrictions, and CPU/PPU/DMA contention results. | ✓ VERIFIED (D-025 software-model scope) | `tests/test_dma.c` and CTest inventory assert DMA startup/restart/readback, bounded source/destination behavior, access restrictions, mode-2 scan/fetch overlap, word boundaries, and same-half-dot outcomes. Evidence ledger scopes collision/tie order to the deterministic D-025 software model. It does not claim exact CPU-B lane/timing or PPU-revision parity. |
| 3 | VIDEO-03: Timestamped joypad transitions produce deterministic selection/interrupt behavior through the public API and SDL keyboard path. | ✓ VERIFIED (selected falling-edge software contract) | `joypad_interrupt` and related guest cases assert active-low selection, selected pin falling edges, negative controls, sticky IF, IE independence, equal-time ordering, and partition equivalence. SDL Z-down/up maps to the public event API and is observed in the packaged player. Exact CPU-B pulse qualification and sample phase remain unmeasured. |
| 4 | VIDEO-04: A Mac user can open/play a permissioned fixture, resize with aspect/integer scaling, pause, reset, quit, and receive actionable errors. | ✓ VERIFIED | Original fixture manifest establishes rights and exact image identity. Player/session/presentation tests cover bounded replacement, errors, and geometry; the current package script's extracted-byte SDL smoke passed. UAT test 34 contains current Mac user's visible-window and Z response confirmation. |
| 5 | VIDEO-05: Automated evidence distinguishes composition, timing, and gameplay; preview accurately states supported audio/persistence scope and remaining limits. | ✓ VERIFIED | Separate evidence suites are registered and pass. Audio and battery saves have since been implemented within declared subsets; current help/docs/package metadata state the supported formats, mapper/save scope, and remaining hardware/revision limits. The old Phase 3 exact phrase “not implemented” and old Plan 03-11 metadata predicate are superseded by Phases 4/5; current assertions correctly require the implemented paths. |

**Score:** 5/5 roadmap truths verified (0 present-but-behavior-unverified).

### Plan Coverage

All 13 plans and all 13 summaries exist. The structured artifact query passed every artifact it could parse. Plans 03-12/03-13 use shorthand artifact declarations that the query does not parse; their implementation, tests, inventory registration, and evidence documents were checked directly. Several older key-link queries returned `Target not referenced` for cross-file behavior or non-file endpoints; these were manually traced below rather than treating parser output as a wiring failure. The Plan 03-11 literal check for “Audio and battery-save persistence are not implemented” is superseded by implemented Phase 4/5 support and a current exact limitation assertion.

| Plan | Requirement(s) | Coverage result |
|---|---|---|
| 03-01 | VIDEO-01/03/05 | Original ROM enters production core; bounded copied frame and timestamped guest input are tested. |
| 03-02 | VIDEO-01/05 | Independent BG/window/object images and guest-visible LCD/STAT/fetch timing are registered and passed. |
| 03-03 | VIDEO-02/05 | DMA progress, source mapping, HRAM/access restrictions and contention guests are registered and passed. |
| 03-04 | VIDEO-03 | Public event queue and active-low JOYP matrix/guest behavior are wired; hardware IF sampling remains outside the claim. |
| 03-05 | VIDEO-03/04/05 | Optional SDL keyboard mapping and frame presentation use the public API; current rendered Z behavior is tested and recorded in UAT. |
| 03-06 | VIDEO-04/05 | Transactional ROM replacement, actionable errors, pause/reset, integer scaling, and current limitation copy have focused tests. |
| 03-07 | VIDEO-01/03 | Bounded output/event contracts and installed consumers are present; public-only consumers exercise timestamped input/frame copy. |
| 03-08 | VIDEO-05 | Original fixture source, rights, digest, reproduction command, and exact-revision workflow are connected. Historical hosted receipt is not represented as a current-HEAD hosted run. |
| 03-09 | VIDEO-04/05 | Exact-revision package workflow and extracted-byte consumer are wired; current local package smoke is separately recorded below. |
| 03-10 | VIDEO-02/03 | Evidence ledger distinguishes source, software model, and physical observation; unsupported CPU-B behavior remains explicitly unqualified. Prohibitions on unlicensed fixtures, emulator-derived hardware claims, and host services in the portable core were checked against manifest, evidence labels, imports, and core/API. |
| 03-11 | VIDEO-05 | Current limitation text is exactly asserted and metadata identifies implemented audio/save scope. The plan's obsolete “both absent” predicate was intentionally superseded by Phases 4/5. |
| 03-12 | VIDEO-02 | FF46 startup/restart/readback guest cases and source boundaries are registered and passed. |
| 03-13 | VIDEO-02/03 | JOYP edge matrix and D-025 DMA/PPU scan/fetch/access/collision cases are registered and passed; test 34 closes the then-open visible-package check. |

## Required Artifacts

| Artifact group | Expected | Status | Details |
|---|---|---|---|
| Core/API and optional player | Timed PPU, DMA, JOYP, bounded frame/event API, and SDL adapter | ✓ VERIFIED | Core paths are consumed by public API tests, original guest tests, and optional player; SDL remains outside the portable core. |
| PPU/DMA/JOYP/tracer tests | Independent composition, timing, contention, input, and gameplay cases | ✓ VERIFIED | CMake and fail-closed expected-test inventory register cases; current core suite passed 179/179. |
| Original interactive fixture | Legal reproducible ROM-only GB image | ✓ VERIFIED | Source, license, manifest, size/digest, reproduction path, guest tests, and default package path are connected. |
| Evidence/support documentation | Provenance, applicability, limitations | ✓ VERIFIED | Evidence ledger separates documentation, software policy, and physical observation. CPU-B and revision limits are explicit; preview docs/help describe current audio/save scope. |
| Package and consumer workflow | Exact-head macOS package plus downloaded-byte smoke | ✓ VERIFIED as wired | PR workflow invokes the pinned build and downloaded consumer and gates its aggregate. Older hosted receipts are historical and are not claimed for current dirty HEAD. Current local extracted-byte package smoke passed. |

## Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| PPU/core run | Public frame API and authored PPU guests | Dot progress → completed frame copy → independent pixel and timestamp assertions | ✓ WIRED | Core PPU state drives public copied pixels and guest-visible register timing. |
| DMA/PPU scheduling | DMA guest suite | FF46 state, DMA deadlines, access gating, per-object scan/fetch | ✓ WIRED | DMA bytes, PPU output, CPU bus result and partitions are asserted separately. |
| Public event API | JOYP guests | Timestamped queue → per-instance button/select state → FF00/IF.4 reads | ✓ WIRED | Selected falling-edge software contract has positive and negative guest assertions. |
| SDL keyboard | Public event API | Scancode mapping and timestamped SDL events | ✓ WIRED | Player input tests plus current package Z-down/up smoke cover the same path. |
| Core frame and demo fixture | SDL renderer/window | Copied shade frame → texture → renderer; manifest-bound ROM loads into session | ✓ WIRED | Extracted-byte smoke asserts rendered shades; UAT 34 supplies current visible-window confirmation. |
| Package workflow | Extracted consumer | Receipt/digest verification → extraction → SDL guest/frame smoke | ✓ WIRED | Workflow dependencies and local script paths verified. Current local package SHA differs from older hosted receipt and is recorded below. |
| Limitation source | Help, docs, and metadata | Shared capability statement and package fields | ✓ WIRED | Current limitation test asserts supported audio/save scopes; package smoke rejects false hardware claims. |

## Data-Flow Trace (Level 4)

| Artifact | Data | Source | Produces real data | Status |
|---|---|---|---|---|
| SDL display | Frame pixels | Guest ROM → PPU → completed core frame → player copy → SDL texture | Yes | ✓ FLOWING; current packaged window confirmed in UAT 34. |
| Guest joypad | FF00 / IF.4 and ROM-visible tile | SDL/public timestamped input → instance JOYP state → guest polling/interrupt model → PPU frame | Yes | ✓ FLOWING under the selected falling-edge software contract. |
| Fixture | Guest program bytes | Checked-in original assembly/build manifest and digest → ROM-only loader | Yes | ✓ FLOWING into guest tests and packaged demo. |

## Behavioral Spot-Checks

| Behavior | Command/evidence | Result | Status |
|---|---|---|---|
| Core and registered test inventory | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` | 179/179 passed; includes current fixture digest and preview package smoke | ✓ PASS |
| Current optional player/package gate (dirty overlay on `bb8fd654d03969e3d207fcdc92c345cc60be3298`) | `bash tests/scripts/verify-phase3-player.sh --build-package` in the isolated macOS package run | 51/51 player CTests passed; extracted-package Z-down/Z-up rendered-shade checks, dummy-audio recovery, guest audio, and fresh-process MBC1 continuation passed; package SHA-256 `0016796835439b1fdba8fe15365137e85e8b6973cd28795966afa655a7f62fcc` | ✓ PASS |
| Caller-selected output-directory safety | `PYTHONDONTWRITEBYTECODE=1 python3 tests/scripts/test_verified_player_output_dir.py -v`; package verification with a caller-selected output directory | 8/8 direct helper regressions passed; package consumer preserved unrelated output while producing the expected archive and receipt. Resolved equal/ancestor/descendant paths, symlinks, roots, and artifact-name collisions are covered. | ✓ PASS |
| Current packaged live preview | Existing UAT test 34 (2026-10-09) | Owner reported demo visible; holding Z darkened the square and release restored lighter green | ✓ PASS |

Additional checks: `bash -n tests/scripts/verify-phase3-player.sh` and `git diff --check` passed. The added output-directory helper is registered in optional player CTest and `tests/player/expected-tests.txt`, so omission fails the package lane's expected-test inventory.

The full core CTest run was performed in the project worktree. The optional player/package result above came from a disposable macOS clone with current dirty worktree files copied over shared HEAD `bb8fd654d03969e3d207fcdc92c345cc60be3298`; it is not a clean-checkout or hosted-CI claim. The packaged-window observation is reused from the existing accepted UAT test 34; no repeat manual test is requested or implied. Previous exact-head hosted package/fixture receipts support workflow wiring only and do not prove hosted checks for this current dirty worktree.

## Probe Execution

No Phase 3 plan declares a probe and no roadmap criterion requires one. The discovered `tests/scripts/probe-mooneye-candidate.sh` is a Phase 2 probe and is outside this phase.

## Requirements Coverage

| Requirement | Source plans | Status | Evidence |
|---|---|---|---|
| VIDEO-01 | 01, 02, 07 | ✓ SATISFIED | Separate registered composition and PPU timing guest cases passed. |
| VIDEO-02 | 03, 10, 12, 13 | ✓ SATISFIED within declared software model | DMA/PPU observable cases passed under D-025; exact CPU-B lane/timing and PPU revision parity remain unclaimed. |
| VIDEO-03 | 01, 04, 05, 07, 10, 13 | ✓ SATISFIED under selected software contract | Public and SDL input paths plus guest JOYP/IF checks passed; exact CPU-B sample/pulse phase remains unmeasured. |
| VIDEO-04 | 05, 06, 09, 13 | ✓ SATISFIED | Local extracted-byte smoke and existing current-package UAT test 34. |
| VIDEO-05 | 01, 02, 03, 05, 06, 07, 08, 09, 11 | ✓ SATISFIED with current capability scope | Separate evidence suites pass; current help/docs/package accurately describe implemented scoped audio/save support and residual limits. |

All five Phase 3 requirements map to a plan and the roadmap; no orphaned Phase 3 requirement was found. VIDEO-05 describes accurate reporting of current supported audio/persistence scope and remaining limitations, consistent with the capabilities added in Phases 4 and 5.

## Review, Security, and Test Quality

- Focused Phase 3 review is `clean` (0 critical, 0 warning, 0 info) and examined current player rendering/input smoke and both workflows.
- Security report closes all 40/40 declared threat IDs (`threats_open: 0`); fixture, input, frame bounds, DMA, and package boundaries have identified mitigations. The evidence ledger prevents software-model outcomes from being represented as physical CPU-B observations.
- Nyquist validation marks `GB03-OUTPUT-DIR-OVERLAP` resolved with 8/8 focused helper regressions. The focused review is clean (0 critical, 0 warning, 0 info). The configured core regression command ran the full SDL-free CTest inventory (179/179).
- Requirement-linked tests have no disabled/skipped tests. Expected images and guest observations are independently authored; no test derives its expected result by running the implementation under test.
- Anti-pattern scan found no debt markers, placeholder implementation, empty user-visible result, or console-only path in covered implementation/tests. `.XXXXXX` matches are mktemp template strings, not `XXX` debt comments.
- Decision-coverage gate: 14/14 trackable CONTEXT decisions honored (non-blocking gate).

## Human Verification Required

None. The current packaged-window interaction is already documented as owner-observed in UAT test 34. No physical hardware measurement is needed for the declared software-model acceptance, and no physical CPU-B/PPU-revision claim is made.

## Gaps Summary

No must-have gap remains for the Phase 3 goal. The implementation delivers legal-fixture gameplay, timed input, separate video evidence, and the optional Mac player. The accepted scope is the declared DMG software model: exact CPU-B DMA lane/timing, JOYP pulse/sample phase, and PPU revision parity remain unmeasured. Scoped audio and standard-MBC1 battery persistence now exist from later phases; current limitations identify where support and physical qualification remain incomplete.

---

_Verified: 2026-10-09T22:37:25Z_
_Verifier: the agent (gsd-verifier)_
