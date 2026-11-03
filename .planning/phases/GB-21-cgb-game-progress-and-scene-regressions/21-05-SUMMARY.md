---
phase: GB-21-cgb-game-progress-and-scene-regressions
plan: "05"
subsystem: testing
tags: [cgb, candidate-evidence, fixture-admission, rights-scope]
requires:
  - phase: GB-21-cgb-game-progress-and-scene-regressions/21-04
    provides:
      - Final primary candidate no-go enabling the sole µCity 1.3 fallback
provides:
  - Final µCity 1.3 preferred-artifact rights no-go with exact source identity
  - Component-scope finding for an uncovered required source input
affects: [GB-21-07, FIXT-01, GAME-02]
actuals:
  tokens: 19921.25
  tasks: 3
  commits: 1
tech-stack:
  added: []
  patterns:
    - Candidate no-go records bind exact source identity and leave downstream facts not observed at the cutoff.
key-files:
  created:
    - tests/data/cgb-candidates/ucity-1.3.json
  modified: []
key-decisions:
  - "The author-linked µCity v1.3 tag resolves to d1880a2a112d7c26f16c0fc06a15b6c32fdc9137; the required hardware include has no identified grant or notice, so repository/public-CI scope remains unestablished."
  - "Stop at the rights cutoff before tool acquisition, sandbox probes, or upstream execution; record the toolchain and all later game facts as not observed."
patterns-established:
  - "Record source and release identity independently from ROM/build observations, which remain not observed after an earlier gate stops the attempt."
requirements-completed: [GAME-02]
coverage:
  - id: D1
    description: The sole fallback is tied to the author-linked v1.3 source and has a concrete component-scope no-go with later facts explicitly not observed.
    requirement: FIXT-01
    verification:
      - kind: other
        ref: "python3 -I tests/scripts/verify-cgb-candidates.py --check-all --require-final --repo-root . --source-revision c0fa267be2f14c632ef2208354a4267ef2edd6e0"
        status: pass
    human_judgment: false
  - id: D2
    description: The no-go branch creates no fallback ROM, fixture, notice row, acceptance case, input, or predicate and leaves Phase 20 admission unchanged.
    requirement: FIXT-01
    verification:
      - kind: other
        ref: "Automated path assertions for fixtures/ucity-1.3, the ucity acceptance case/input, predicate registry, and THIRD_PARTY_NOTICES.md"
        status: pass
      - kind: integration
        ref: "python3 -I tests/scripts/verify-fixture-admission.py --check-repository --repo-root ."
        status: pass
    human_judgment: false
  - id: D3
    description: Existing native-CGB harness progress, input/predicate controls, mode refusal, and fixture/product boundary tests pass; the result remains harness evidence only.
    requirement: GAME-02
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^(fixture_product_core_controls|fixture_product_player_controls|acceptance_cgb_progress_.*|phase21_fixture_admission_(contract|controls))$'"
        status: pass
    human_judgment: false
metrics:
  duration: 15min
  completed: 2026-11-02
status: complete
commits: 1
plan_head_before: 514039755a58853442f9e122ac82626e3ffa60cd
plan_head_after: c0fa267be2f14c632ef2208354a4267ef2edd6e0
---

# Phase GB-21 Plan 21-05: µCity 1.3 Fallback Summary

**The author-linked µCity 1.3 source was pinned, but an uncovered required hardware include leaves the sole fallback at a rights no-go.**

## Performance

- **Duration:** 15 minutes
- **Started:** 2026-11-02T03:40:00Z
- **Completed:** 2026-11-02T03:55:23Z
- **Tasks:** 3/3 (Tasks 2 and 3 followed the no-go branch and produced no fixture or runner-consumption artifacts)
- **Files modified:** 1 plan-owned candidate record

## Accomplishments

- Validated the final Potion Panic no-go record at its immutable source commit and confirmed its rights cutoff does not claim a license restriction from the earlier Codeberg fetch failure.
- Resolved the author-linked Codeberg v1.3 tag to commit `d1880a2a112d7c26f16c0fc06a15b6c32fdc9137`, corroborated the same tag identity in the author GitHub release, and recorded a complete source inventory with no submodules. The release advertises preferred `ucity.gbc`; its bytes were not acquired.
- Mapped the v1.3 README terms for GPL-header code, BSD-2-Clause GBT Player files, and CC BY-SA 4.0 media. The required `source/engine/hardware.inc` has no identified grant or notice and says it is based on Jones' `hardware.inc`; repository/public-CI scope for the complete build therefore remains unestablished.
- Recorded a final rights no-go before tool acquisition or build. Build isolation, toolchain identity, ROM bytes/header, native mode, progress, observations, and receipt remain explicitly not observed. No upstream script/tool ran, and no fallback fixture, ROM, notice row, case, input, or predicate was created.
- Verified the ordered two-candidate outcome and Phase 20 repository boundary. The focused nine-test CTest selection passed after refreshing the stale build revision metadata.

## Checks Run

- `verify-cgb-candidates.py --check-record` passed for the immutable primary no-go.
- `verify-cgb-candidates.py --check-all --require-final` passed for the final ordered pair at `c0fa267be2f14c632ef2208354a4267ef2edd6e0`.
- `verify-fixture-admission.py --check-repository` passed with zero admitted fixture changes.
- The focused CTest selection passed all nine product, native-CGB harness, candidate-control, and admission tests. An initial run found three CGB cases using stale runner revision metadata; after `cmake --preset phase1` and `cmake --build --preset phase1`, those cases passed, and the full selection passed 9/9. The separate `test_budget` check was not run; its existing two over-limit CTests remain assigned to Plan 21-07.

## Task Commits

1. **Task 1 — assess and record the fallback no-go** — `c0fa267b` (`docs(GB-21-05): record µCity 1.3 component-scope no-go`)
2. **Task 2 — no-go provenance branch** — no fixture or notice files changed; the final candidate checker passed.
3. **Task 3 — no-go closure branch** — no predicate or runner-consumption files changed; ordered-pair, admission, and focused CTest verification passed.

## Decisions Made

- The exact fallback source and release were available and identified. The no-go is based on a required build input whose licensing and grant authority are not established, not on repository reachability.
- Tool acquisition and build-isolation probes were not reached after the rights gate. No ROM or game behavior was observed.
- `GAME-02` remains complete from the existing harness work. `FIXT-01` remains pending until Plan 21-07 composes the final candidate-pair outcome.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Refresh stale source revision metadata before CGB verification**
- **Found during:** Task 3
- **Issue:** Three CGB progress CTests initially reported `progress-field-mismatch:core_revision` because the runner build predated the new candidate-record commit.
- **Fix:** Reconfigured and rebuilt the existing `phase1` preset so the runner used the current source revision. No tracked source files changed.
- **Files modified:** None tracked; build outputs are ignored.
- **Verification:** The three affected CTests passed on retest, followed by a 9/9 pass for the complete focused selection.
- **Committed in:** No source commit; the only plan commit records the candidate no-go.

**2. [Rule 3 - Blocking] Use supported final-stage candidate-checker options**
- **Found during:** Task 1
- **Issue:** The plan verification examples use `--stage assessed` and `--stage provenance`, which the installed checker does not accept.
- **Fix:** Used the supported `--require-final` check for the assessed outcome and the final ordered-pair check for closure.
- **Files modified:** None beyond the planned candidate record.
- **Verification:** Both final record checks passed.
- **Committed in:** `c0fa267b`.

**Total deviations:** 2 auto-fixed (2 Rule 3). No candidate or product scope was added.
**Impact on plan:** Verification used the current checker interface and refreshed the runner build identity; the fallback remained a bounded rights no-go.

## Issues Encountered

- The sandbox denied writes to `.git/index.lock`; a narrow permission grant allowed staging and committing only the candidate record. The measured plan-head ledger was stored under `/tmp` because `.git` is read-only in this environment.
- The existing `test_budget` finding was left unchanged for Plan 21-07.

## User Setup Required

None - no external service configuration is required.

## Next Phase Readiness

- Plan 21-05 is complete with a concrete µCity rights-scope no-go. Phase 21 remains active; Plan 21-07 is the next incomplete plan and owns final composition plus the pre-existing `test_budget` finding. It was not started here.
- Phase 22 — Composition and Microtest Evidence — remains the next phase after Phase 21 closes. Both automatic-advance flags remain false.

---
*Phase: GB-21-cgb-game-progress-and-scene-regressions*
*Completed: 2026-11-02*

## Self-Check: PASSED

- Summary file exists at the planned phase path.
- Task commit `c0fa267be2f14c632ef2208354a4267ef2edd6e0` is an ancestor of the current HEAD.
