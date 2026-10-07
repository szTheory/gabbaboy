---
phase: GB-03-visible-interactive-dmg
verified: 2026-10-07T22:45:20Z
status: gaps_found
score: 3/5 roadmap truths verified
covered_files:
  - .planning/phases/GB-03-visible-interactive-dmg/03-CONTEXT.md
  - .planning/phases/GB-03-visible-interactive-dmg/03-RESEARCH.md
  - .planning/phases/GB-03-visible-interactive-dmg/03-VALIDATION.md
  - .planning/phases/GB-03-visible-interactive-dmg/03-PLAN-CHECK.md
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
  - .planning/phases/GB-03-visible-interactive-dmg/03-10-SUMMARY.md
  - .planning/phases/GB-03-visible-interactive-dmg/03-11-SUMMARY.md
  - .planning/phases/GB-03-visible-interactive-dmg/03-12-PLAN.md
  - .planning/phases/GB-03-visible-interactive-dmg/03-12-SUMMARY.md
  - .planning/phases/GB-03-visible-interactive-dmg/03-SECURITY.md
  - src/core/gabbaboy.c
  - src/player/main.c
  - tests/test_ppu.c
  - tests/test_dma.c
  - tests/test_joypad.c
  - tests/test_tracer.c
  - tests/player/test_input.c
  - tests/player/test_session.c
  - tests/player/test_presentation.c
  - tests/scripts/verify-phase3-player.sh
  - tests/scripts/reproduce-visible-demo.sh
  - .github/workflows/ci.yml
  - .github/workflows/preview.yml
  - .github/workflows/fixture-repro.yml
  - docs/dmg-video-evidence.md
  - docs/preview.md
  - .planning/REQUIREMENTS.md
  - .planning/ROADMAP.md
  - .planning/STATE.md
  - .planning/.continue-here.md
  - .planning/context/LESSONS.md
  - .planning/research/INDEX.md
covered_digest: "v3:sha256:fcd7cab8b71c8d3534b4410c7b71dfcc9531e4b42316941b1026246b80c05ff9"
behavior_unverified: 2
overrides_applied: 0
gaps_remaining:
  - "VIDEO-02: simultaneous CPU/PPU/DMA results are not qualified for the declared DMG-CPU-B model; startup/restart/readback are supported by pinned upstream assertions and owned software regressions."
  - "VIDEO-03 / D-08: JOYP interrupt edge/selection expectations lack a primary model-applicable source and focused qualified cases."
---

# Phase 3: Visible Interactive DMG Verification Report

**Phase Goal:** A macOS user can play a legal interactive ROM-only GB fixture with deterministic input and evidenced DMG video behavior.
**Verified:** 2026-10-07T22:45:20Z
**Implementation revision:** `a1a084a3e961276abb0e2495d35be40ae0b77679`
**Status:** gaps found — this report does not mark Phase 3 complete.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | Background, window, and sprites render with LCD/STAT transitions and dot-sensitive fetch behavior demonstrated separately. (VIDEO-01) | ✓ VERIFIED | The authored composition cases and focused PPU timing/mode tests are registered in the core inventory; the prior full offline CTest passed 132/132. This plan did not change PPU implementation. Claims remain limited to the declared bootless DMG-CPU-B software model. |
| 2 | Guests observe model-specific OAM DMA, VRAM/OAM restrictions, and CPU/PPU/DMA contention. (VIDEO-02) | GAP | DMA progress/restrictions and the source-backed fresh-start M=1 access, accepted restart/completion, and FF46 readback subcases now have registered guest regressions. The pinned Mooneye sources report DMG-family passes and document a fleet including CPU-B, but provide no per-test/per-unit raw logs. Simultaneous active PPU/DMA arbitration therefore remains unqualified. [dmg-video-evidence.md](../../../docs/dmg-video-evidence.md) records the provenance and boundary. |
| 3 | Timestamped joypad transitions produce deterministic selection/interrupt behavior through the public API and SDL keyboard path. (VIDEO-03) | GAP | Timestamped API and SDL events share the same bounded core boundary and pass their software tests. Exact JOYP interrupt edge/selection behavior remains blocked by D-08 because the available material does not establish a primary source for this model and focused expected result. |
| 4 | A macOS user can launch the optional player, load and play a supported ROM-only fixture, resize, pause, reset, quit, and receive actionable errors. (VIDEO-04) | ✓ VERIFIED | The opt-in arm64 package job built at the exact PR head, ran 14/14 player tests, and uploaded a complete package. The separate consumer downloaded, verified, extracted, and launched that exact package; the scripted SDL event path preserved failed ROM replacement, accepted success, and produced a completed frame. Live-window perception remains unobserved. |
| 5 | Automated evidence separates composition, raster timing, and scripted gameplay, and the preview states audio/persistence limits. (VIDEO-05) | ✓ VERIFIED | Separate CTest groups and fixture reproduction preserve the three evidence classes; `docs/preview.md` and packaged metadata state audio and battery persistence are absent. Exact-head CI and downloaded-artifact smoke passed. |

**Score:** 3/5 roadmap truths verified; behavior-unverified: 2.

## Exact-Revision Package Evidence

- CI run [37686137977](https://github.com/szTheory/gabbaboy/actions/runs/37686137977) passed `macos-player-package` and `required-native` at the exact head SHA above.
- Preview run [37686137834](https://github.com/szTheory/gabbaboy/actions/runs/37686137834) passed both installed-package consumers, `player-package-smoke-macos`, and `preview-package-smoke` at that same SHA.
- The final downloaded artifact receipt bound build run `37686137977/1` to consumer run `37686137834/1`. Its package SHA-256 was `cd0ce476c34a91ab9de2a6ee5e084a0ecff94b95f5015d1aa7b41bc9f88e175f`; its SDL license SHA-256 was `1c040b8271b37e5076359f8fd54240e371114112924d2df81ef87c7d6a1dfdfd`. Source, SDL archive, fixture ROM, project/demo/SDL notices, run identities, and unsigned/unnotarized/unqualified flags were checked.
- The artifact was downloaded, its receipt and digest were checked, it was safely extracted, and the actual downloaded executable passed the package smoke locally (`frame=1`).
- At the earlier Phase 3 verification revision, the ordinary core suite passed 132/132 and the optional player suite passed 14/14. For Plan 03-12, `cmake --preset phase1`, `cmake --build --preset phase1`, and the focused `dma_(start|restart|register_readback|hram|source_mapping)` CTest selection passed. The full core CTest suite then passed 134/134 at `a1a084a`.

## Requirement Coverage

| Requirement | Status | Evidence |
|---|---|---|
| VIDEO-01 | SATISFIED | Independent image composition and focused timing cases; full CTest passed. |
| VIDEO-02 | OPEN | Startup/restart/readback progress is evidenced by upstream acceptance assertions and owned software regressions. Simultaneous CPU/PPU/DMA collision outcomes remain model-unqualified. |
| VIDEO-03 | OPEN | D-08 lacks a primary model-applicable JOYP edge/selection source and qualifying focused cases. |
| VIDEO-04 | SATISFIED | Exact-head macOS arm64 package and downloaded-byte SDL guest/frame smoke passed. |
| VIDEO-05 | SATISFIED | Composition, timing, gameplay, fixture provenance, and preview limitations have distinct automated evidence. |

## Human and Hardware Limitations

No physical DMG-CPU-B observation occurred, and the live macOS window and status text were not perceptually checked because this environment has no desktop display. The Mooneye suite reports DMG-family outcomes and documents a CPU-B in its test fleet, but no retained per-unit test logs were available. These limits do not qualify simultaneous PPU/DMA arbitration or JOYP IF behavior.

## Security Verification

The Phase 3 threat audit closed 30 of 31 registered threats. T-03-27 remains open at medium severity because automated checks do not assert the audio/persistence limitation text and package metadata fields; it is below the configured high-severity blocking threshold (`threats_open: 0`). See [03-SECURITY.md](03-SECURITY.md). The audit kept this finding separate from the VIDEO-02/03 correctness evidence gaps.

## Gaps Summary and Route

Plan 03-12 closes only source-backed FF46 startup/restart/readback behavior and its active write-gate mismatch. Phase 3 remains **executing**. VIDEO-02 simultaneous PPU/DMA applicability and D-08/VIDEO-03 JOYP IF behavior remain open. This plan does not verify Phase 3 or authorize Phase 4.

---

_Verified: 2026-10-07T22:45:20Z_
_Verifier: inline goal-backward evidence audit; no live desktop or hardware behavior inferred._
