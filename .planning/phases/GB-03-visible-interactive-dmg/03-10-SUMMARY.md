---
phase: GB-03-visible-interactive-dmg
plan: 10
subsystem: video-input-evidence
tags: [dmg, dma, joypad, evidence, hardware-applicability]
requires:
  - phase: GB-03-visible-interactive-dmg
    provides: Existing DMA/PPU and timestamped JOYP behavior plus pinned source ledger
provides:
  - Source applicability ledger for unresolved simultaneous PPU/DMA outcomes
  - Corrected JOYP threshold and source-to-timestamp trace with explicit evidence limits
affects: [phase-03-verification]
actuals:
  tokens: 6336
  tasks: 3
  commits: 4
tech-stack:
  added: []
  patterns: [source-to-case applicability ledger]
key-files:
  created: []
  modified:
    - docs/dmg-video-evidence.md
    - .planning/phases/GB-03-visible-interactive-dmg/03-10-PLAN.md
    - .planning/phases/GB-03-visible-interactive-dmg/03-RESEARCH.md
    - .planning/context/LESSONS.md
key-decisions:
  - Do not assert CPU-B PPU/DMA collision outcomes when available sources are revision-dependent or omit the simultaneous-access tie-break.
  - Do not assert JOYP IF timing from the manual threshold or reconstructed schematic without a validated phase trace.
  - Record unavailable observation apparatus as an open evidence dependency; do not infer a hardware result.
patterns-established:
  - Separate primary documentation, reverse-engineered circuit inference, software tests, and physical hardware observations in the evidence ledger.
requirements-completed: []
coverage:
  - id: D1
    description: DMA collision evidence is limited to source-supported behavior, with unsupported CPU-B outcomes left open.
    requirement: VIDEO-02
    verification:
      - kind: unit
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^(dma_.*|ppu_timing_.*)$' (14/14)"
        status: pass
    human_judgment: true
    rationale: The tests protect existing behavior; deciding whether a source applies to CPU-B still requires evidence review.
  - id: D2
    description: JOYP threshold and circuit path are traceable while exact CPU-B interrupt timing remains unresolved.
    requirement: VIDEO-03
    verification:
      - kind: unit
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^(joypad_.*|event_(queue_order|queue_atomic|partition))$' (8/8)"
        status: pass
      - kind: unit
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^(dma_.*|joypad_.*)$' (14/14)"
        status: pass
    human_judgment: true
    rationale: Software tests do not measure the physical sampling phase or qualify CPU-B interrupt behavior.
duration: "11min+ minimum recorded"
completed: 2026-10-07
status: complete
---

# Phase GB-03 Plan 10: Source Applicability Audit Summary

**DMA collision and JOYP evidence now distinguish source-backed behavior from unresolved CPU-B timing.**

## Performance

- **Duration:** At least 11 minutes of recorded execution; the exact start time was not captured.
- **Started:** 2026-10-07T21:57:25Z (earliest task commit; execution began earlier).
- **Completed:** 2026-10-07T22:08:02Z.
- **Tasks:** 3.
- **Files modified:** 4, plus this summary.

## Accomplishments

- Added a source-applicability table for mode 2 DMA overlap, mode 3 object-fetch overlap, and simultaneous CPU/PPU/DMA access. No CPU-B collision expectation was invented.
- Corrected the manual threshold from the OCR-flattened “24” to 2^4 (16) source periods and pinned the referenced DMG-CPU-B schematics to a resolvable upstream commit.
- Recorded that no lawful, available observation setup or raw record was identified or supplied for this run. VIDEO-02 and VIDEO-03 remain open where the hardware applicability evidence is absent.

## Task Commits

1. **Task 1: Source-grounded DMA collision path and evidence boundary** — `eff0896` (`docs`).
2. **Task 2: Source-grounded JOYP sampling path under D-08** — `30187c9` (`docs`).
3. **Task 3: Record the unresolved CPU-B observation dependency** — `2c73591` (`docs`).

Plan metadata was committed with this summary.

## Files Created/Modified

- `docs/dmg-video-evidence.md` — source-to-case applicability and explicit unresolved hardware dependencies.
- `.planning/phases/GB-03-visible-interactive-dmg/03-10-PLAN.md` — corrected threshold wording.
- `.planning/phases/GB-03-visible-interactive-dmg/03-RESEARCH.md` — corrected source pin and transcription note.
- `.planning/context/LESSONS.md` — OCR and immutable-source verification lesson.

## Decisions Made

- Existing `dma_contention` coverage remains a reset/isolation check; it does not assert simultaneous collision results.
- JOYP matrix polling and deterministic event tests remain software checks and do not assert IF edges.
- The absent physical observation is recorded as an access dependency, not as a measured negative result.

## Deviations from Plan

No new DMA collision or JOYP interrupt case was added because the cited sources did not establish exact DMG-CPU-B expected values. This follows the plan's explicit evidence gate. The plan and research text were also corrected after visual inspection showed the manual's superscript had been flattened and upstream resolution showed the previous schematic SHA was invalid.

## Verification

- DMA/PPU focused filter: 14/14 passed.
- JOYP/event focused filter: 8/8 passed.
- Combined DMA/JOYP filter: 14/14 passed.
- `git diff --check`: passed.
- These software results do not establish physical CPU-B applicability.

## Open Requirements

VIDEO-02 simultaneous PPU/DMA applicability and VIDEO-03 / D-08 JOYP interrupt timing remain open pending source-applicable expected outcomes or a provenance-complete owner-run observation.

## Next Phase Readiness

Plan 03-11 is next. Phase 3 remains in progress and must be verified before Phase 4 starts.

## Self-Check: PASSED

- All three plan tasks have task-scoped commits.
- The focused commands were run and passed; no unsupported hardware assertion or fixture was added.
- The plan-level open requirement disposition is explicit.
