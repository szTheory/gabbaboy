---
phase: GB-03-visible-interactive-dmg
plan: 13
subsystem: testing
tags: [dmg, joypad, dma, ppu, guest-tests, source-evidence]
requires:
  - phase: GB-03-visible-interactive-dmg
    provides: Existing public guest, DMA, PPU, frame, and validation infrastructure
provides:
  - Guest-visible JOYP selected falling-edge IF.4 behavior with ordered transition coverage
  - Confidence-qualified DMA/PPU scan, fetch, bus-access, boundary, and same-half-dot collision evidence
  - Refreshed Phase 3 verification, requirement traceability, and continuation route
affects: [phase-3-verification, phase-4-readiness]
tech-stack:
  added: []
  patterns: [original guest oracles, independently asserted pixels/bus/timing, confidence-qualified software model]
key-files:
  created: [.planning/phases/GB-03-visible-interactive-dmg/03-13-SUMMARY.md]
  modified: [src/core/gabbaboy.c, tests/test_joypad.c, tests/test_dma.c, tests/CMakeLists.txt, tests/expected-tests.txt, docs/dmg-video-evidence.md, .planning/phases/GB-03-visible-interactive-dmg/03-VALIDATION.md, .planning/phases/GB-03-visible-interactive-dmg/03-VERIFICATION.md, .planning/REQUIREMENTS.md, .planning/context/LESSONS.md, .planning/ROADMAP.md, .planning/STATE.md, .planning/.continue-here.md]
key-decisions:
  - "Apply D-025's confidence-qualified deterministic model to source-supported JOYP and DMA/PPU behavior while retaining exact CPU-B timing and revision uncertainty."
  - "Keep Phase 3 open for VIDEO-04's actual packaged-window and mapped-key observation on a display-equipped Mac."
patterns-established:
  - "Assert authored frame pixels, DMA destination bytes, CPU bus values, and event timestamps as separate guest outcomes."
  - "Preserve FF46 start/restart/readback exceptions and the previously sourced startup window while testing the normal active-DMA interval."
requirements-completed: [VIDEO-02, VIDEO-03]
coverage:
  - id: D1
    description: "The guest observes selected JOYP pin falling edges as IF.4, with negative controls, sticky IF, IE independence, event ordering, and partition invariance."
    requirement: VIDEO-03
    verification:
      - kind: unit
        ref: "tests/test_joypad.c#joypad_interrupt"
        status: pass
      - kind: unit
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^joypad_'"
        status: pass
    human_judgment: false
  - id: D2
    description: "The guest asserts the D-025 DMA/PPU scan/fetch model, active-DMA access matrix, word boundaries, and same-half-dot tie outcomes."
    requirement: VIDEO-02
    verification:
      - kind: unit
        ref: "tests/test_dma.c#dma_active_mode_matrix,dma_ppu_overlap,dma_ppu_word_boundaries,dma_ppu_cpu_collision"
        status: pass
      - kind: unit
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error"
        status: pass
    human_judgment: false
duration: 25min
completed: 2026-10-08
status: complete
commits: 3
plan_head_before: 0f481ae9051a73f08ced6b9bf3ca8d4152058349
plan_head_after: ddac31aefcbe316f4443a08ad668ee912365102f
---

# Phase GB-03 Plan 13: Close selected JOYP and DMA/PPU evidence gaps

**Guest-visible JOYP interrupt and DMA/PPU contention behavior now have independently asserted coverage under D-025's declared software model, with VIDEO-04 retained as the remaining live display check.**

## Performance

- **Duration:** 25 minutes based on the first and last plan commits
- **Started:** 2026-10-07T20:01:36-04:00
- **Completed:** 2026-10-08T00:26:01Z
- **Tasks:** 3
- **Files modified:** 13

## Accomplishments

- Added guest-visible IF.4 tests for selected pin falling edges across P10–P13, unselected input, held selector and repeated press, second pin, shared rows, release, sticky IF, IE=0, same-time event ordering, and run-partition equivalence.
- Added independently authored DMA/PPU guests for full/partial scan overlap, nonoverlap controls, active-DMA CPU VRAM/OAM access in PPU modes 0–3, before/after word-update pixels, exact same-half-dot DMA→PPU→CPU collision, and split-run equivalence.
- Refreshed evidence and requirement records: VIDEO-02/03 pass under their confidence-qualified contracts; VIDEO-04 remains open for the actual packaged window/demo/key observation.
- Preserved the 03-12 startup window and FF46 start/restart/readback exceptions. The active-DMA access matrix applies to the normal blocked interval only.
- Follow-up review fixed the omitted 40th OAM entry and reset-time scan cursor; new guest regressions cover both cases. A fresh review of the affected core and tests is clean.

## Task Commits

The persisted plan ledger measured 3 commits after `plan_head_before` (`0f481ae9051a73f08ced6b9bf3ca8d4152058349`). Earlier implementation commits are ancestors of that ledger base and are listed for complete task provenance.

1. **Task 1: JOYP guest oracle and implementation** — `5c0a700` (red guest), `00bfceb` (IF.4 implementation), `2a65b1e` (expanded edge matrix)
2. **Task 2: DMA/PPU oracle and model** — `5b44193` (red guest), `4435f45` (model), `0f481ae` (initial outcomes), `6901129` (complete matrix/tie coverage)
3. **Task 3: Evidence and Phase 3 route** — `ddac31a` (docs)

## Files Created/Modified

- `src/core/gabbaboy.c` - selected JOYP falling-edge IF.4 request and incremental DMA/PPU scan/fetch behavior.
- `tests/test_joypad.c` - guest IF edge matrix and boundary controls.
- `tests/test_dma.c` - active-DMA mode matrix, scan/fetch overlap, word-boundary, and three-way collision guests.
- `tests/CMakeLists.txt`, `tests/expected-tests.txt` - named focused test registration and fail-closed inventory.
- `docs/dmg-video-evidence.md` - pinned provenance, test matrix, and confidence boundaries.
- `.planning/phases/GB-03-visible-interactive-dmg/03-VALIDATION.md` - current focused and full-suite outcomes.
- `.planning/phases/GB-03-visible-interactive-dmg/03-VERIFICATION.md` - historical baseline plus current 4/5 goal-backward verdict.
- `.planning/REQUIREMENTS.md`, `.planning/context/LESSONS.md` - VIDEO-02/03 traceability and the D-025 execution lesson.
- `.planning/ROADMAP.md`, `.planning/STATE.md`, `.planning/.continue-here.md` - Phase 3 pause and exact verification route.

## Decisions Made

- Use the source-backed deterministic software model adopted by D-025 for testable JOYP and DMA/PPU behavior. Do not represent it as physical CPU-B qualification; exact pulse qualification, CPU sample phase, OAM byte lane, word-update/tie timing, and PPU-revision parity remain unmeasured.
- Retain VIDEO-04 as open until a display-equipped Mac visibly launches the packaged player, displays the fixture, and responds to one mapped key.

## Deviations from Plan

None. Task-level TDD evidence was committed before implementation, and the required guest matrix/collision cases were completed. The prior startup and FF46 exceptions remain intact.

## Issues Encountered

The local environment has no SDL display (`SDL_Init: The video driver did not add any displays`), so the actual packaged-window/key response could not be observed. This is the sole remaining Phase 3 truth; no hardware, live-window, or current-head hosted-CI claim is made.

## Validation

- `ctest --preset phase1 --output-on-failure --no-tests=error -R '^joypad_'` — 6/6 passed.
- `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(dma_ppu_overlap|dma_active_mode_matrix|dma_ppu_word_boundaries|dma_ppu_cpu_collision)$'` — 4/4 passed.
- `cmake --preset phase1 && cmake --build --preset phase1 --parallel 2 && ctest --preset phase1 --output-on-failure --no-tests=error` — 141/141 passed after the review fixes.
- Fresh code review at `eb31afd` — clean, 0 findings; focused JOYP/PPU/DMA regressions passed 17/17.
- `git diff --check` — passed.
- Fresh goal-backward audit: `human_needed`, 4/5 truths; VIDEO-01/02/03/05 pass under declared evidence classes; VIDEO-04 needs a display-equipped Mac observation. No exact-head hosted CI was run.

## Next Phase Readiness

Plan 03-13 is complete. Phase 3 is still executing, not complete, because VIDEO-04 remains open. The next exact command after the display observation is `$gsd-verify-work 3`. Phase 4 — MBC1 and Safe Battery Continuation — has not started; keep both auto-advance flags false.

## Self-Check: PASSED

- Summary and all 12 planned source/evidence artifacts exist.
- Task commits `5c0a700`, `00bfceb`, `2a65b1e`, `5b44193`, `4435f45`, `0f481ae`, `6901129`, and `ddac31a` are ancestors of the current branch head.
- The plan ledger measures 3 commits after `plan_head_before`.

---
*Phase: GB-03-visible-interactive-dmg*
*Completed: 2026-10-08*
