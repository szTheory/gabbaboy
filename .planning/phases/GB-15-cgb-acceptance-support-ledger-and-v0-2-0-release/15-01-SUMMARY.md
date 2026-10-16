---
phase: 15-cgb-acceptance-support-ledger-and-v0-2-0-release
plan: "01"
subsystem: testing
tags:
  - cgb
  - adoption
  - claims
  - evidence
requires:
  - phase: "Phase 07"
    provides:
      - "Libbet DMG game acceptance and its separate regression observations"
  - phase: "Phase 14"
    provides:
      - "CGB-CPU-E software corpus evidence and its limits"
provides:
  - "An explicit public statement that no CGB game-level evidence exists"
  - "A bounded CLI contract for public CGB game-evidence claims"
affects:
  - "Phase 15 support ledger and v0.2.0 release documentation"
actuals:
  tokens: 3031
  tasks: 2
  commits: 4
plan_head_before: 380cae907d524095930d12d9b958889cc4ac7b24
plan_head_after: e2c002e1cfdb6c5f51fc9c43df036ce7dcd6fc65
tech-stack:
  added: []
  patterns:
    - "Bounded standard-library document checks with isolated CLI mutation controls"
key-files:
  created:
    - tests/scripts/verify-v02-adoption.py
  modified:
    - docs/game-acceptance.md
    - README.md
key-decisions:
  - "Use the explicit CGB game-evidence absence route after Rebound failed the bounded build and rights gates."
  - "Keep Libbet as DMG-only game acceptance and keep test-ROM corpus results separate from game evidence."
patterns-established:
  - "Public evidence claims are checked through their real CLI entry point with named missing-claim and contrary-claim controls."
  - "Markdown whitespace is normalized for semantic checks while the required absence statement remains exact."
requirements-completed:
  - CGB-11
coverage:
  - id: D1
    description: "The game-acceptance guide states that no CGB game-level evidence exists and records the bounded Rebound outcome while retaining Libbet's DMG acceptance."
    requirement: CGB-11
    human_judgment: false
    verification:
      - kind: integration
        ref: "python3 -I tests/scripts/verify-v02-adoption.py --check game && python3 -I tests/scripts/verify-v02-adoption.py --self-test game"
        status: pass
  - id: D2
    description: "README states the CGB game-evidence boundary, distinguishes software corpus evidence, and links to the scoped corpus and game-acceptance records."
    requirement: CGB-11
    human_judgment: false
    verification:
      - kind: integration
        ref: "python3 -I tests/scripts/verify-v02-adoption.py --check docs && python3 -I tests/scripts/verify-v02-adoption.py --self-test docs"
        status: pass
  - id: D3
    description: "The adoption checker emits positive JSON summaries and rejects missing or contrary CGB game claims through isolated real-CLI controls."
    requirement: CGB-11
    human_judgment: false
    verification:
      - kind: unit
        ref: "python3 -I tests/scripts/verify-v02-adoption.py --self-test game && python3 -I tests/scripts/verify-v02-adoption.py --self-test docs"
        status: pass
duration: 7min
started: "2026-10-16T14:34:32Z"
completed: "2026-10-16T14:41:31Z"
status: complete
---

# Phase 15 Plan 01: CGB Game-Evidence Boundary Summary

**A bounded standard-library checker and synchronized public claims state that no CGB game-level evidence exists while preserving Libbet's DMG-only acceptance.**

## Performance

- **Duration:** 7 minutes
- **Started:** 2026-10-16T14:34:32Z
- **Completed:** 2026-10-16T14:41:31Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Added `tests/scripts/verify-v02-adoption.py` with `--check game`, `--self-test game`, `--check docs`, `--self-test docs`, and `--root PATH`. It bounds document reads, checks the exact absence statement and evidence limits, and reports check and rejection counts as JSON.
- Updated the game-acceptance guide with the Rebound source and RGBDS build evidence, missing output ROM/digest, unresolved asset rights, the unverified historical digest, and the explicit CGB evidence boundary. Libbet remains identified as DMG game acceptance; corpus and emulator output digests remain separate evidence classes.
- Updated README with the same CGB boundary, physical and perceptual limits, the distinction between corpus evidence and game acceptance, and links to the game guide and corpus contract.
- The final game-mode run passed 14 checks and rejected both intended controls. The combined documentation run passed 21 checks and rejected all seven intended controls.

## Task Commits

1. **Task 1 RED: adoption claim checker** - `504ac68` (`test`)
2. **Task 1 GREEN: game-acceptance guide** - `8d97c87` (`docs`)
3. **Task 2 RED: README contract controls** - `e08170e` (`test`)
4. **Task 2 GREEN: README evidence boundary** - `e2c002e` (`feat`)

## Files Created/Modified

- `tests/scripts/verify-v02-adoption.py` - bounded public-claim checker with real-CLI mutation tests.
- `docs/game-acceptance.md` - explicit CGB absence and bounded Rebound evidence, retaining DMG Libbet acceptance.
- `README.md` - adopter-facing CGB evidence boundary and scoped links.

## Decisions Made

- Selected the explicit absence route after the bounded Rebound build and rights checks did not produce admissible game bytes.
- Kept test-ROM corpus evidence, Libbet game progress, and RGB555/PCM regression observations distinct.
- Left `src/runner/acceptance.c` and all fixture/ROM paths unchanged.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Normalize Markdown whitespace before checking README claims**
- **Found during:** Task 2
- **Issue:** A Markdown line break split the `Physical CGB-E remains UNKNOWN/POLICY` sentence in source and caused a false checker failure.
- **Fix:** Normalize whitespace before evaluating README contract phrases.
- **Files modified:** `tests/scripts/verify-v02-adoption.py`
- **Verification:** `--check docs` and `--self-test docs` passed; all seven negative controls were rejected for their expected reasons.
- **Committed in:** `e2c002e`

**Total deviations:** 1 auto-fixed (Rule 1). The fix corrected a semantic-check bug without changing scope.

## TDD Gate Compliance

- **Task 1 RED:** `python3 -I tests/scripts/verify-v02-adoption.py --check game` exited 1 with `absence-statement-missing:docs/game-acceptance.md`. The script loaded the guide and rejected the intended missing public claim; there was no parser or setup failure. The guide update made the positive check pass, and the self-test rejected both missing-statement and contrary-claim mutations.
- **Task 2 RED:** `python3 -I tests/scripts/verify-v02-adoption.py --check docs` exited 1 with `absence-statement-missing:README.md`. The expanded checker loaded both surfaces and rejected the intended missing README claim. The README update made the combined check pass, and the self-test rejected all seven missing-claim, contrary-claim, and evidence-link mutations.
- `workflow.tdd_mode` was false and this is an execute plan; the task-level RED/GREEN cycles were recorded in the four task commits above.

## Issues Encountered

The workspace grants read-only access to `.git`, so commit operations required sandbox escalation. The escalation review approved the required commits; no unrelated planning changes were staged.

## User Setup Required

None.

## Next Phase Readiness

Plan 15-01 is complete. Its exact absence statement and contract checks are ready for the versioned support ledger and release documentation. The phase-level CGB-11 requirement remains pending until the ledger producer carries this boundary; Phase 15 remains in progress.

## Self-Check: PASSED

All three deliverables exist, the four task commits are ancestors of the current plan head, the plan evaluation-scope check resolves four commits, and the final positive and negative CLI checks pass. No fixture or runner files changed, no tracked files were deleted, and the required stub-pattern scan found no matches.

---
*Phase: 15-cgb-acceptance-support-ledger-and-v0-2-0-release*
*Plan: 01*
*Completed: 2026-10-16*
