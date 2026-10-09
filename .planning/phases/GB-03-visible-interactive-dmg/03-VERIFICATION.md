---
phase: GB-03-visible-interactive-dmg
verified: "2026-10-09T14:28:01Z"
status: passed
score: 5/5 roadmap truths verified
covered_files:
  - .github/workflows/ci.yml
  - .github/workflows/preview.yml
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
  - .planning/phases/GB-03-visible-interactive-dmg/03-SECURITY.md
  - .planning/phases/GB-03-visible-interactive-dmg/03-UAT.md
  - .planning/phases/GB-03-visible-interactive-dmg/03-VALIDATION.md
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
  - tests/scripts/verify-phase3-player.sh
  - tests/test_dma.c
  - tests/test_joypad.c
  - tests/test_ppu.c
  - tests/test_tracer.c
covered_digest: "v3:sha256:31033fdba6a3a3051ddbdd16f62280b8aefe944f060b1e5d0aa7dc2eeda814b4"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: human_needed
  previous_score: 4/5 roadmap truths verified
  gaps_closed:
    - "Current packaged preview visibility and live Z press/release response, recorded in completed UAT test 34."
  gaps_remaining: []
  regressions: []
decision_coverage:
  honored: 14
  total: 14
  not_honored: []
---

# Phase GB-03: Visible Interactive DMG Verification Report

**Phase Goal:** As a Mac user, I want to play a legal GB ROM with timed input and video evidence, so that I can verify the DMG preview.
**Verified:** 2026-10-09T14:28:01Z
**Status:** passed
**Re-verification:** Yes — current packaged-player UAT test 34 closes the prior report's sole human item.

## User Flow Coverage

User story: “As a Mac user, I want to play a legal GB ROM with timed input and video evidence, so that I can verify the DMG preview.” The canonical user-story validator accepts this roadmap goal.

| Step | Expected | Evidence | Status |
|---|---|---|---|
| Open and play the fixture | The legal, original GB demo loads and produces a visible frame. | `fixtures/visible-demo/manifest.json` binds source, rights, profile, protocol, and ROM digest; session and rendering paths are tested. UAT test 34 records the user's 2026-10-09 confirmation that the current packaged Mac player displays the demo. | VERIFIED |
| Press and release a control | Timed Z events reach the guest and change the target tile. | `tests/player/test_input.c`, guest JOYP assertions, and current-package UAT test 34: user confirmed the tile darkens while Z is held and restores on release. | VERIFIED |
| Verify video evidence | Composition, timing, contention, and gameplay have distinct evidence. | Registered independent `frame_composition_*`, `ppu_timing_*`, DMA/JOYP guests, and `docs/dmg-video-evidence.md` provenance/applicability matrix. | VERIFIED within declared software model |
| See preview limitations | The preview identifies missing audio and battery persistence. | `src/player/main.c`, `src/player/limitations.h`, `tests/player/test_limitations.c`, `docs/preview.md`, and downloaded-package metadata assertions. | VERIFIED |

**User-story outcome:** The current packaged app displays the owned demo and visibly responds to Z press/release, as recorded in completed UAT test 34. The report does not treat that observation as hardware qualification.

## Goal Achievement

| # | Roadmap truth | Status | Evidence |
|---|---|---|---|
| 1 | VIDEO-01: Background/window/sprite composition and dot-sensitive LCD/STAT/fetch behavior are separately demonstrated. | ✓ VERIFIED | Production `src/core/gabbaboy.c` feeds independent authored expected images and guest timestamp assertions in `tests/test_ppu.c`; cases are registered in CMake and `tests/expected-tests.txt`. Validation reports the refreshed combined CTest inventory passed 229/229. |
| 2 | VIDEO-02: Guests observe model-specific OAM DMA, VRAM/OAM restrictions, and CPU/PPU/DMA contention results. | ✓ VERIFIED (D-025 software model) | `tests/test_dma.c` contains active-DMA mode matrix, overlap controls, word-boundary, and same-half-dot guest cases with separate byte/pixel/CPU assertions. `docs/dmg-video-evidence.md` distinguishes documented behavior from repository policy. Exact CPU-B lane/timing and PPU-revision parity remain unmeasured and are not claimed. |
| 3 | VIDEO-03: Timestamped joypad transitions produce deterministic selection/interrupt behavior through the public API and SDL keyboard path. | ✓ VERIFIED (selected falling-edge software contract) | Public event API and SDL mapping paths are wired; `joypad_interrupt` exercises selected/unselected edges, sticky IF, ordering, and partition equivalence. Exact CPU-B pulse/sample phase remains unmeasured. |
| 4 | VIDEO-04: A Mac user can open/play a permissioned fixture, resize with aspect/integer scaling, pause, reset, quit, and receive actionable errors. | ✓ VERIFIED | Fixture and session loading, controls, error paths, and integer presentation are covered by player tests. Exact-head macOS package and downloaded-artifact consumer passed. UAT test 34 supplies current-package visible-window and live-Z confirmation; it does not claim a full physical-hardware test. |
| 5 | VIDEO-05: Automated evidence distinguishes composition, timing, and gameplay; preview labels incomplete audio and persistence. | ✓ VERIFIED | Evidence ledger maintains distinct classes; player limitation text and package metadata have focused assertions; current package consumer checks the downloaded artifact. |

**Score:** 5/5 roadmap truths verified (0 present-but-behavior-unverified).

### Plan Must-Have Audit

All thirteen phase plans were checked. Their artifact declarations resolve to existing substantive implementation/tests; plan 12/13 use shorthand artifact paths that the structured artifact query does not parse, so those were checked directly against the named source, guest tests, inventory, evidence ledger, and traceability. Key links were checked in code and test paths; a query parser miss on older links without explicit patterns was not treated as proof of a broken link.

| Plan | Must-have coverage | Status | Evidence |
|---|---|---|---|
| 03-01 | Original ROM → production core → bounded frame and timestamped input | VERIFIED | `tests/test_tracer.c`, fixture manifest/digest, public header and core path. |
| 03-02 | Independent BG/window/object images and guest-observed LCD/STAT/fetch timing | VERIFIED | `tests/test_ppu.c`; source and applicability records in evidence ledger. |
| 03-03 | Timed DMA progress, source mapping, HRAM and access/contention outcomes | VERIFIED | Registered guest cases in `tests/test_dma.c`; evidence boundaries documented. |
| 03-04 | Active-low JOYP selection, queue rules, only qualified interrupt behavior | VERIFIED | Public API, guest tests, and unresolved CPU-B limits documented. |
| 03-05 | Optional SDL player, timestamped key path, and frame presentation | VERIFIED | `src/player/main.c`, `input.c`, and player input/presentation tests. |
| 03-06 | Safe ROM replacement, session controls, actionable errors, integer-scaled presentation | VERIFIED | Session/presentation implementation and tests cover success/failure and bounds. |
| 03-07 | Bounded frame/event failure behavior and installed C/C++ consumers | VERIFIED | Core API tests and registered consumer paths. |
| 03-08 | Reproducible original fixture and exact-revision hosted receipt | VERIFIED | Fixture reproducer and fixture CI exact-head receipt (validation evidence). |
| 03-09 | Exact-head macOS package and extracted-byte consumer | VERIFIED | Final PR head `1a2a02434eb348cd9e107072760fbd49867f8e28`: CI run 37942861727 and preview run 37942861800 passed; summary records package/runtime/fixture identity checks. |
| 03-10 | Source-applicability constraints and explicit uncertainty for DMA/JOYP claims | VERIFIED as evidence-boundary truths | Source-to-case ledger retains unsupported CPU-B outcomes as unresolved; no hardware result is inferred from emulator or SDL behavior. |
| 03-11 | Audio/persistence limitations in help and downloaded metadata | VERIFIED | Focused limitation test and package metadata checks. |
| 03-12 | Source-supported FF46 startup/restart/readback while retaining open arbitration boundaries | VERIFIED | Registered DMA guest cases and model-limit documentation. |
| 03-13 | JOYP edge matrix, DMA/PPU overlap/access/collision model, and explicit applicability limits | VERIFIED | Guest assertions and registered inventory cover IF.4 state, PPU/DMA matrix, same-half-dot outcomes, and partition behavior. VIDEO-04's formerly open package check is now completed in UAT test 34. |

The two `verification: backstop` truths in Plan 03-10 are evidence-boundary claims, not requests to infer physical CPU-B behavior: the ledger maps each asserted outcome to its source/applicability class and explicitly leaves unsupported cases unqualified. They do not establish hardware accuracy. D-025 defines the accepted software-model scope.

## Required Artifacts

| Artifact group | Expected | Status | Details |
|---|---|---|---|
| Core/API and player | Timed DMG core, bounded frame/event API, optional SDL adapter | ✓ EXISTS + SUBSTANTIVE + WIRED | Core is consumed by the player and guest tests; SDL remains optional and outside the portable core dependency graph. |
| PPU/DMA/JOYP/tracer tests | Independent image/timing/contention/input/gameplay cases | ✓ EXISTS + SUBSTANTIVE + WIRED | CMake and fail-closed expected-test inventory register the cases; authored expected values and guest-observed state exercise the production core. |
| Original demo fixture | Legal reproducible interactive ROM | ✓ EXISTS + SUBSTANTIVE + WIRED | Source, license, manifest, digest, binary and reproducer connect fixture to tests and player default. |
| Evidence and preview docs | Provenance, model boundaries, and limitations | ✓ EXISTS + SUBSTANTIVE + WIRED | Evidence matrix distinguishes hardware observations, documentation, software model, and repository policy. Audio and battery persistence limitations are explicit. |
| Exact-head package workflows | Build and inspect actual downloaded package bytes | ✓ EXISTS + SUBSTANTIVE + WIRED | Required PR macOS package and downloaded consumer paths verify source/artifact/runtime/fixture identities and run player smoke against extracted bytes. |

## Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| Core PPU | Public frame API and authored image guests | Dot progression, completed-frame copy | ✓ WIRED | Tests assert independent pixels and bounded frame behavior from production code. |
| Core DMA/PPU | DMA guest cases | FF46, access gating, scan/fetch timeline | ✓ WIRED | Separate guest assertions cover DMA bytes, pixels, CPU bus reads, and partitioning. |
| Public input API | JOYP guest cases | Timestamped queue → selected pin state → IF.4 software contract | ✓ WIRED | Guest reads FF00/IF and asserts edge/no-edge, stickiness, ordering, and partitions. |
| SDL keyboard event | Player input → core API | Scancode mapping and timestamped event queue | ✓ WIRED | Automated input tests and UAT test 34 confirm mapped Z reaches visible demo behavior. |
| Core frame | SDL window | Frame copy → texture update → render/present | ✓ WIRED | Package smoke checks rendered shade; user UAT confirms the current window visibly presents it. |
| Fixture package | Extracted executable | Receipt-verified package-relative demo and SDL runtime | ✓ WIRED | Exact-head downloaded-package consumer passed and UAT exercised the current package. |
| Limitation source | Help and package metadata | Shared text plus metadata validation | ✓ WIRED | Focused player assertion and downloaded-package consumer reject false audio/persistence support claims. |

## Data-Flow Trace (Level 4)

| Artifact | Data variable | Source | Produces real data | Status |
|---|---|---|---|---|
| Player screen | shade frame / texture pixels | Production core completed frame → player buffer → SDL texture/window | Yes | ✓ FLOWING; current visible output confirmed by UAT 34. |
| Guest joypad | FF00 and IF.4 | Timestamped public/SDL events → per-instance button/select state | Yes | ✓ FLOWING under selected falling-edge software contract. |
| ROM fixture | Guest program bytes | Checked-in original ROM tied to manifest source and digest | Yes | ✓ FLOWING into guest tests and package-relative player load. |

## Behavioral Spot-Checks

| Behavior | Evidence | Result | Status |
|---|---|---|---|
| Core/test inventory | Validation receipt: combined CTest 229/229; closeout rerun of `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` passed 179/179 core tests on local commit `04877a3` | Passed | ✓ PASS |
| Optional player tests | Current validation receipt: pinned SDL 3.4.18 player suite 50/50 | Passed | ✓ PASS |
| macOS package build | Exact-head CI run 37942861727 for `1a2a02434eb348cd9e107072760fbd49867f8e28`; `macos-player-package` and `required-native` passed | Passed | ✓ PASS |
| Extracted package consumer | Preview run 37942861800 at the same exact head; `player-package-smoke-macos` and `preview-package-smoke` passed | Passed | ✓ PASS |
| Fixture reproduction | Exact-head fixture run 37942861652 at the same exact head | Passed | ✓ PASS |
| Current packaged live preview | Completed UAT test 34, 2026-10-09; user reported visible demo and shade darken/restore on Z press/release | Pass | ✓ PASS |

The package and fixture receipts are recorded in `03-VALIDATION.md` and `03-09-SUMMARY.md`; the latest local core CTest rerun passed 179/179 on the closeout tree. UAT test 34 is the single current packaged-window observation, and the future check is automated in the required PR package smoke.

## Probe Execution

No Phase 3 plan declares a probe and the phase success criteria do not require one. The Phase 2 Mooneye candidate probe is out of scope.

## Requirements Coverage

| Requirement | Source plans | Status | Evidence |
|---|---|---|---|
| VIDEO-01 | 03-01, 03-02, 03-07 | SATISFIED | Authored composition and raster-timing guest cases are distinct and registered. |
| VIDEO-02 | 03-03, 03-10, 03-12, 03-13 | SATISFIED within D-025 software model | DMA/access/PPU guest checks and source applicability ledger; exact CPU-B lane/timing and PPU-revision parity remain unmeasured. |
| VIDEO-03 | 03-01, 03-04, 03-05, 03-10, 03-13 | SATISFIED within selected falling-edge software contract | Public timestamped events and SDL path are tested; exact CPU-B pulse/sample phase remains unmeasured. |
| VIDEO-04 | 03-05–03-09 | SATISFIED | Controls, safe replacement, errors, geometry, package and current user-confirmed live preview evidence. |
| VIDEO-05 | 03-01, 03-02, 03-05, 03-06, 03-08, 03-09, 03-11 | SATISFIED | Separate evidence classes, original fixture provenance, and explicit audio/persistence limitations. |

All five plan requirement IDs are accounted for; no additional Phase 3 requirement mapping is orphaned. All 14 trackable phase decisions are honored. Physical DMG-CPU-B measurements are outside the stated acceptance evidence and are not represented as requirement failures.

## Test Quality Audit

| Test File | Linked requirement | Active/registered | Circular expected-value generation | Assertion strength | Verdict |
|---|---|---|---|---|---|
| `tests/test_ppu.c` | VIDEO-01/05 | Yes | None identified; expected images are authored independently | Value and guest-timestamp assertions | PASS |
| `tests/test_dma.c` | VIDEO-02/05 | Yes | None identified; byte/pixel/bus outcomes are asserted independently | Value and behavioral guest assertions | PASS within declared model |
| `tests/test_joypad.c` | VIDEO-03 | Yes | None identified; guest reads FF00/IF | Value and multi-step state assertions | PASS within declared contract |
| `tests/test_tracer.c` | VIDEO-01/03/05 | Yes | None identified; fixture and expected behavior are separately specified | Frame/gameplay assertions | PASS |
| `tests/player/test_input.c`, `test_presentation.c`, `test_session.c`, `test_limitations.c` | VIDEO-03/04/05 | Yes | No circular expected-value generation identified | Value, failure-boundary, and workflow assertions | PASS |

Disabled requirement tests: none found in the reviewed registered inventory. Circular expected-value patterns: none identified. Exact hardware behavior beyond the declared model is not tested or claimed.

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| None | — | No blocking debt markers or placeholder implementation identified in the phase implementation/review scope. | — | Returns and initial empty state inspected are normal error/state defaults, not user-visible stubs. |

`03-REVIEW.md` reports zero findings. `03-SECURITY.md` reports no high-threshold open threat; T-03-27 is a medium historical limitation-text/metadata coverage item that Plan 03-11 closes with focused assertions. The review and security documents predate parts of the current evidence refresh; exact-head CI and current UAT are independently recorded above.

## Human Verification Required

None. The user-facing current packaged preview and Z response are recorded as completed UAT test 34. No second observation is required. Physical CPU-B timing and lane behavior remain unmeasured hardware limitations, not unresolved software acceptance steps.

## Gaps Summary

**No phase-goal gaps found.** All roadmap truths and mapped requirements are satisfied within their declared software evidence scopes. The current packaged player’s visible demo and mapped Z response were directly confirmed on 2026-10-09; exact-head package CI and extracted-byte smoke passed. The report makes no physical CPU-B or universal PPU-revision claim: JOYP pulse/sample phase, DMA lane/word-tie timing, and revision parity remain unmeasured and are explicitly recorded in the evidence ledger.

---

_Verified: 2026-10-09T14:28:01Z_
_Verifier: the agent (gsd-verifier)_
