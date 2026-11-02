---
phase: GB-21-cgb-game-progress-and-scene-regressions
plan: "04"
subsystem: testing
tags: [cgb, candidate-evidence, fixture-admission, rights-no-go]
requires:
  - phase: GB-20-fixture-admission-tune-up
    provides:
      - Component-level fixture-rights and package-exclusion gate
  - phase: GB-21-cgb-game-progress-and-scene-regressions/21-02
    provides:
      - Native-CGB progress controls and bound RGB555/PCM observations
  - phase: GB-21-cgb-game-progress-and-scene-regressions/21-03
    provides:
      - Ordered candidate record and final no-go contract
provides:
  - Final Potion Panic primary rights no-go with the creator-linked source acquisition failure
  - Explicit not-observed source, build, ROM, mode, progress, observation, and receipt facts
affects: [GB-21-05, GB-21-07, FIXT-01]
actuals:
  tokens: 1622.75
  tasks: 3
  commits: 1
tech-stack:
  added: []
  patterns:
    - Creator-level license labels remain leads until exact component coverage and required repository/public-CI scope are established
    - A rights cutoff records later candidate facts as not observed and stops before acquisition or execution
key-files:
  created:
    - tests/data/cgb-candidates/potion-panic.json
  modified:
    - .planning/phases/GB-21-cgb-game-progress-and-scene-regressions/.continue-here.md
key-decisions:
  - "Stop at the rights gate because the exact creator-linked source tree and its per-component grants could not be inspected; do not infer permission from public availability or page-level labels."
  - "Keep µCity 1.3 as the only eligible fallback after the committed primary no-go; this plan does not start that attempt."
patterns-established:
  - "Candidate no-go records preserve the exact blocker and explicitly identify every downstream fact that was not observed."
requirements-completed: []
coverage:
  - id: D1
    description: The primary candidate has a final source-grounded rights no-go; exact source and all downstream candidate facts remain explicitly not observed.
    requirement: FIXT-01
    verification:
      - kind: other
        ref: "python3 -I tests/scripts/verify-cgb-candidates.py --check-record tests/data/cgb-candidates/potion-panic.json --require-final --repo-root . --source-revision 1ab7180e9f35c70246e62c252d3dd4851fa77473"
        status: pass
    human_judgment: false
  - id: D2
    description: The no-go branch adds no candidate fixture or acceptance input and preserves the Phase 20 repository/package boundary.
    requirement: FIXT-01
    verification:
      - kind: integration
        ref: "python3 -I tests/scripts/verify-fixture-admission.py --check-repository --repo-root . && ctest --preset phase1 --output-on-failure --no-tests=error -R '^(fixture_product_core_controls|fixture_product_player_controls|phase21_fixture_admission_(contract|controls))$'"
        status: pass
    human_judgment: false
metrics:
  duration: 4min
  completed: 2026-11-02
status: complete
commits: 1
plan_head_before: f4b693b8632b98495326643766d03269516c1c10
plan_head_after: 1ab7180e9f35c70246e62c252d3dd4851fa77473
---

# Phase GB-21 Plan 21-04: Potion Panic Primary Candidate Summary

**Potion Panic is closed as a rights no-go because exact component coverage and required repository/public-CI scope could not be established; no later candidate facts were observed.**

## Performance

- **Duration:** 4 minutes
- **Started:** 2026-11-02T03:33:09Z
- **Completed:** 2026-11-02T03:37:01Z
- **Tasks:** 3/3 (Task 2 and Task 3 completed through their specified no-go branch without fixture changes)
- **Files modified:** 2 (candidate record and continuation route)

## Accomplishments

- Verified the creator page lists MIT for code and CC BY-NC-SA 4.0 for assets and links to `https://codeberg.org/DevEd/potion-panic`. The indexed GitHub repository identifies itself as a fork and was not substituted for the creator-linked source.
- `git ls-remote` against the creator-linked Codeberg repository failed before returning a ref or commit (`SSL_ERROR_SYSCALL` to `codeberg.org:443`). Without the exact source tree, component inventory, grant authority, notice coverage, and explicit Phase 20 repository/public-CI scope could not be established. This is a rights no-go; it does not claim that CC BY-NC-SA categorically forbids this use.
- Recorded the final no-go in `tests/data/cgb-candidates/potion-panic.json`. Source/build identities, ROM bytes/header, runtime mode, game route/predicate, RGB555/PCM observations, and receipt are all explicitly `not_observed` at the rights cutoff.
- No candidate source was acquired, no upstream script/tool or game ROM was run or built, and no candidate bytes, fixture manifest, notice row, acceptance case, input, or predicate were added. The build-isolation gate was not reached; no sandbox capability is claimed.
- Updated the continuation note for the next eligible step, Plan 21-05, while preserving the existing `test_budget` finding for Plan 21-07.

## Checks Run

- `verify-cgb-candidates.py --check-record ... --require-final` passed against the immutable primary record.
- `verify-fixture-admission.py --check-repository` passed with zero admitted changes.
- The four planned fixture/package admission CTests passed, including both synthetic Phase 21 admission controls.
- Confirmed no `fixtures/potion-panic/` directory or Potion Panic acceptance case/input exists. JSON parsing and `git diff --check` passed.
- The separate `test_budget` check was not run by this plan; its existing two over-limit Phase 21 fixture test declarations remain open in `deferred-items.md` for Plan 21-07.

## Task Commits

1. **Task 1 — record primary rights no-go** — `1ab7180e` (`docs(GB-21-04): record Potion Panic rights no-go`)
2. **Task 2 — conditional provenance snapshot** — no commit; the no-go branch requires no fixture or notice changes.
3. **Task 3 — conditional admission/progress closure** — no commit; the no-go branch adds no admission, predicate, case, input, or ROM artifacts.

The measured plan commit count is one. The separate summary/state/roadmap metadata commit follows the task commit.

## Decisions Made

- The creator page's MIT and CC BY-NC-SA labels identify terms to investigate; they do not establish which exact source components each grant covers or the grantor's authority over every component.
- The official CC BY-NC-SA 4.0 terms limit licensed use to noncommercial purposes and require attribution; share-alike applies to adapted material. No conclusion was made that public CI is either permitted or forbidden. Phase 20 requires the exact project scope to be affirmatively established before admission.
- The only authoritative source link on the creator page was retained. No GitHub fork, ROM download, or inferred source revision was used.

## Deviations from Plan

The plan's Task 1 example uses `--stage assessed` and `--source-revision HEAD`, but the installed checker accepts named stages without `assessed` and requires a full lowercase commit ID. The final no-go was verified with the supported `--require-final` option and full immutable commit `1ab7180e9f35c70246e62c252d3dd4851fa77473`; no implementation change was needed. The first checker invocation with `HEAD` failed on the required full hash and was immediately replaced.

## Issues and Limitations

- The upstream Codeberg endpoint was inaccessible from this environment, so exact source identity and the component-level rights map remain unobserved. This attributable rights no-go determines fallback eligibility; Plan 21-05 may proceed only as the sole approved fallback.
- Candidate build isolation probes and the candidate runner were not invoked because the rights gate failed earlier. No upstream code was executed.
- The existing `test_budget` finding remains unchanged and assigned to Plan 21-07.
- The optional broken-windows append for the plan-command deviation could not run because the existing `.planning/WINDOWS.md` contains entry 19 with invalid status `resolved`. That pre-existing ledger issue was left untouched.
- GAME-02 remains complete based on the Phase 21 progress/negative controls. FIXT-01 remains pending until the permitted fallback disposition and final candidate-pair composition are recorded.

## Threat Flags

None. This plan adds a bounded evidence record and no new executable path or candidate bytes.

## Next Phase Readiness

Plan 21-04 is complete. Phase GB-21 remains in execution; Plan 21-05 is the next eligible stage, and Plan 21-07 still owns final candidate-pair composition and the open `test_budget` finding. Phase 22 — Composition and Microtest Evidence — remains the next phase after Phase 21 closes. Continue Phase 21 with `/gsd-execute-phase 21` only when the owner/orchestrator chooses to start the fallback.

---
*Phase: GB-21-cgb-game-progress-and-scene-regressions*
*Completed: 2026-11-02*

## Self-Check: PASSED

- Candidate outcome record and continuation note exist at the planned paths.
- Task commit `1ab7180e` is an ancestor of the current plan head.
- The immutable candidate checker and Phase 20 fixture boundary passed; summary coverage passed its CTest.
