---
phase: GB-21-cgb-game-progress-and-scene-regressions
plan: "06"
subsystem: testing
tags: [scene-feedback, synthetic-controls, privacy, ctest, python]
requires:
  - phase: GB-21-cgb-game-progress-and-scene-regressions
    provides:
      - CGB progress and source-bound observation checks from Plans 21-01 and 21-02
      - Synthetic-only evidence and fixture admission patterns from Plan 21-03
provides:
  - Bounded text-only title/scene/symptom triage report intake
  - Agent-owned reproduction and classification procedure with private-media limits
  - Source-bound promotion gate requiring independent expectations and causal negative controls
affects: [GB-21-07, FEED-01, scene regression workflow]
actuals:
  tokens: 17520.5
  tasks: 2
  commits: 4
commits: 4
plan_head_before: 9f8aa2e29268dc29c843c783ca06ca547b21315d
plan_head_after: ba0dfa85433aa7f0b5ad648e9540b0fea8f63e5a
tech-stack:
  added: [Python standard library, CMake, CTest]
  patterns:
    - Strict bounded local text intake with no implicit filesystem or media discovery
    - Synthetic promotion controls bound to one immutable source revision
key-files:
  created:
    - tests/scripts/verify-scene-report.py
    - docs/scene-feedback.md
  modified:
    - tests/cmake/game-evidence.cmake
    - .planning/phases/GB-21-cgb-game-progress-and-scene-regressions/deferred-items.md
key-decisions:
  - "A title, scene and symptom create unresolved triage; unknown identity or reproduction evidence remains explicit and never claims a live defect."
  - "A scene regression requires a permitted minimized fixture, independent expected behavior, immutable source identity, bounded relevant evidence and a causal negative control."
  - "Personal ROMs, saves, states and captures remain outside repository and hosted regression evidence; owner play is optional."
  - "Carry the existing test_budget timeout finding into Plan 21-07 without changing unrelated test declarations or adding an exception."
requirements-completed: [FEED-01]
coverage:
  - id: D1
    description: Minimal text intake creates bounded unresolved triage and rejects malformed, oversized and unsafe inputs.
    requirement: FEED-01
    verification:
      - kind: integration
        ref: ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase21_scene_report_tracer$'
        status: pass
    human_judgment: false
  - id: D2
    description: Synthetic promotion evidence rejects missing, self-derived, unpermitted or irrelevant evidence and requires the causal negative control.
    requirement: FEED-01
    verification:
      - kind: integration
        ref: ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase21_scene_report_controls$'
        status: pass
    human_judgment: false
  - id: D3
    description: The committed agent procedure documents recovery, reproduction boundaries, classification, privacy, and promotion obligations.
    requirement: FEED-01
    verification:
      - kind: integration
        ref: ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase21_scene_report_contract$'
        status: pass
    human_judgment: false
duration: 17min
completed: 2026-11-02
status: complete
---

# Phase GB-21 Plan 21-06: Scene Feedback Intake and Promotion Summary

**Text-only scene reports now start agent-owned triage, while a source-bound gate requires independent, permitted and causally tested evidence before promotion.**

## Performance

- **Duration:** 17 minutes
- **Started:** 2026-11-02T03:11:55Z
- **Completed:** 2026-11-02T03:29:14Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Implemented `verify-scene-report.py` for bounded title/scene/symptom intake, strict local validation and evidence-gated promotion. A new report is explicitly unresolved triage with a concrete recovery action, not a reproduction claim.
- Documented the agent-owned route to recover public metadata, inspect behavior and source, reproduce at the core/conversion/host boundary, classify the result or blocker, and ask the owner only for a detail that changes the next step.
- Added three source-bound CTests. Synthetic positive subjects and mutation controls cover promotion requirements without using a real game or private media. Local output defaults below ignored `build/scene-reports/`.
- Updated `deferred-items.md` to carry the known `test_budget` issue into Plan 21-07.

## TDD Gate Compliance

- **Task 1 RED:** The registered tracer failed on the missing minimal-intake contract; `gsd_run check tdd-red-evidence` returned `RED_EVIDENCE_OK`.
- **Task 1 GREEN:** The real-CLI tracer passed after implementation. Configure and build also passed.
- **Task 2 RED:** Promotion controls and the committed procedure contract failed on the intended incomplete-contract assertions; both were classified `RED_EVIDENCE_OK`.
- **Task 2 GREEN:** Synthetic promotion and mutation controls passed after the gate and procedure were implemented. Final focused CTest verification passed all three registered checks.

## Task Commits

1. **Task 1 RED — minimal scene intake assertion** — `3d35d10b`
2. **Task 1 GREEN — text-only triage intake** — `a0704c14`
3. **Task 2 RED — promotion failure controls** — `f02c3659`
4. **Task 2 GREEN — evidence-gated promotion** — `ba0dfa85`

## Files Created/Modified

- `tests/scripts/verify-scene-report.py` — bounded intake, strict report validation, immutable source checks and synthetic promotion controls.
- `tests/cmake/game-evidence.cmake` — registers tracer, promotion controls and documentation-contract CTests with 60-second timeouts.
- `docs/scene-feedback.md` — agent-owned triage/reproduction/classification and privacy/promotion procedure.
- `deferred-items.md` — assigns the existing timeout-budget finding to Plan 21-07 integration.

## Decisions Made

- Unresolved and unknown triage is a valid outcome; no current GabbaBoy scene defect was reported or invented.
- Promotion requires rights-eligible, minimized deterministic input, independent expected behavior, immutable source identity and a negative control that targets the stated scene expectation. A progress no-input check is insufficient.
- Moving, timing or audio symptoms need a bounded sequence or semantic/event invariant at the relevant boundary; only a genuinely static scene may use independently derived pixels.
- No private ROM, save, state or capture was read or added. Synthetic subjects exist only in disposable control repositories.

## Deviations from Plan

None in implementation scope. The existing test-budget finding was carried into the deferred-items ledger for Plan 21-07 as directed by the orchestrator handoff.

## Issues Encountered

- `test_budget` remains failing on the two existing fixture-admission tests owned outside this plan. The new scene-report tests satisfy the 60-second limit. Plan 21-07 must resolve or explicitly disposition the finding before final integration.
- The owner supplied no live scene report. The checker, tests and documentation establish a workflow contract only; they provide no game compatibility or scene-correctness evidence.
- The sandbox denied ordinary writes to Git metadata. The required four task commits were made after approved escalation, with only task-owned paths staged. Owner config/state changes and inbound research files remain unstaged.

## User Setup Required

None. A report can be started with three text fields; no owner play session or media is required.

## Next Phase Readiness

Plan 21-06 is complete. Phase 21 remains active. The scene feedback workflow is available to Plan 21-07 for final composition, and the known `test_budget` issue remains open for that plan. No real game defect, candidate outcome or private-media evidence is claimed.

---
*Phase: GB-21-cgb-game-progress-and-scene-regressions*
*Completed: 2026-11-02*

## Self-Check: PASSED

- Summary file exists at the expected phase path.
- All four measured task commits are ancestors of the plan head.
- Plan commit count and head boundaries match the persisted ledger.
