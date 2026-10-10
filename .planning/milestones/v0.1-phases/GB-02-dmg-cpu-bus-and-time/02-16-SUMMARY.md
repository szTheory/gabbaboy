---
phase: GB-02-dmg-cpu-bus-and-time
plan: 16
subsystem: testing
tags: [mooneye, runner, cpu, timer, exact-revision, hosted-ci]

requires:
  - phase: GB-02-dmg-cpu-bus-and-time
    provides: admitted source-qualified candidate fixtures and fixed denominator from Plan 02-17
provides:
  - strict runner results bound to source-qualified callbacks followed by the exact LD B,B result PC
  - regressions for wrong-PC signatures and a real induced guest assertion failure
  - exact-PR-SHA hosted evidence gate and accurate derived-corpus limitations
affects: [CPU-01, CPU-02, CPU-03, CPU-04, CPU-05, Phase GB-02 verification]

actuals:
  tokens: 7845
  tasks: 2
  commits: 4

tech-stack:
  added: []
  patterns:
    - source-qualified callback plus exact result-PC protocol before classifying a guest result
    - explicit expected GitHub contexts when the stacked phase base exposes no branch-protection-required contexts

key-files:
  created:
    - tests/scripts/verify-phase2-hosted.sh
  modified:
    - src/runner/main.c
    - tests/test_runner.c
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - README.md

key-decisions:
  - "A Mooneye pass or fail requires the matching source callback and the exact symbol-addressed LD B,B result PC with its expected register vector."
  - "Receipts identify the derived headless reporting closure and unchanged upstream assertions; they do not claim original-ROM PPU applicability or hardware qualification."
  - "Keep CPU-01 through CPU-05 and Phase 2 pending until independent phase verification assesses this evidence."

patterns-established:
  - "Require nonempty passing Phase 2 contexts and completed pull_request workflow runs tied to the exact open-PR head SHA."
  - "Keep bounded diagnostics in receipts while emitting only the most recent eight records."

requirements-completed: [CPU-02, CPU-05]

plan_head_before: 5097703f46ce0caac75a6488657342977c52911c
plan_head_after: 8481d603b780af7889832ea3a8d3ad84d2439ba5
commits: 4
duration: 24min
completed: 2026-10-07
status: complete
---

# Phase GB-02 Plan 02-16: Runner Protocol and Exact-Revision Qualification Summary

**The runner now classifies the admitted CPU/timer candidates only after their real callback and exact LD B,B result protocol; all final hosted lanes passed at PR head `8481d603`.**

## Performance

- **Duration:** 24 min
- **Started:** 2026-10-07T02:37:49Z
- **Completed:** 2026-10-07T03:01:50Z
- **Tasks:** 2
- **Files modified:** 6 plan implementation files, plus the summary and phase closeout records

## Accomplishments

- Matched the runner allowlist and fixed nonzero denominator to the admitted manifest: one CPU fixture and two timer fixtures. Results now require the fixture-specific pass or fail callback, followed by the exact symbol-addressed `LD B,B` result PC and expected register vector.
- Added a wrong-result-PC regression and an induced DAA guest assertion failure. The failure reached the same callback/result protocol and was reported as `fail`; earlier or unrelated breakpoints cannot produce a pass. Existing timeout, unsupported, missing-fixture, bad-digest, and invalid-manifest reasons remain distinct.
- Expanded receipts with source, tool, patch, original/derived ROM and manifest identities; core/runner revision and build qualification; model, protocol stage, callback/result PCs, elapsed ticks, budget, fixed eligible/executed counts, stop reason, and bounded diagnostic count. Only the latest eight of up to 128 recent diagnostics are printed.
- Updated README evidence and limitation notes to distinguish the derived headless reporting closure from the original upstream-built ROMs. The upstream CPU/timer assertions are unchanged; the original ROM reporting paths remain PPU/LY-limited, and no hardware result is claimed.
- Added a fail-closed hosted gate that binds the open PR to local HEAD, checks all reported PR statuses and the explicit Phase 2 context set, and requires successful completed `pull_request` CI and fixture-reproduction runs at that exact SHA.

## Verification Evidence

- The focused runner and Mooneye selection passed **17/17**. The full offline core inventory passed **100/100** with no skips. The relocated installed inventory passed **105/105**, including installed C/C++ consumers; its fresh core-only inventory passed **100/100**.
- The exact PR SHA `8481d603b780af7889832ea3a8d3ad84d2439ba5` passed CI run [37564610248](https://github.com/szTheory/gabbaboy/actions/runs/37564610248) and fixture-reproduction run [37564610420](https://github.com/szTheory/gabbaboy/actions/runs/37564610420). CI jobs `native-linux-x64`, `native-macos-arm64`, `native-windows-x64`, `linux-asan-ubsan`, `cmake-floor-3.25.3`, and `required-native` passed. Fixture jobs `fixture-repro`, `mooneye-original-repro`, and `mooneye-candidate-repro` passed. `bash tests/scripts/verify-phase2-hosted.sh` independently confirmed the exact PR head and all reported contexts pass.
- GitHub reports no configured required-check contexts for PR #2's stacked Phase 1 base (`gh pr checks --required` is empty). The hosted verifier therefore requires every reported PR status plus its explicit expected Phase 2 context list; it does not treat missing branch protection as evidence that checks passed.
- The runner emitted `pass` for all three fixtures at the unchanged denominator `eligible=3 executed=3`: DAA reached callback `0166`, result PC `409a`, at 1,805,896/2,000,000 half-dots; TIM00 reached `4000` then `4327` at 37,056/200,000; TIM00 DIV trigger reached `4000` then `4327` at 34,928/200,000. The manifest digest was `98a1799b8be9c022ac13467a552890fb12bdd706017e42e12c944ec618d60527`.
- The task's RED evidence is `build/02-16-red-evidence.json`; `gsd_run check tdd-red-evidence ... --raw` returned `RED_EVIDENCE_OK`. The target `runner_wrong_breakpoint` failed on its planned assertion because a matching register signature at a non-result PC was previously accepted. GREEN passed the focused selection. No refactor was needed.
- The host is Darwin, so local Linux sanitizer execution was not available; the final-SHA hosted Linux ASan/UBSan inventory passed. No manual UAT or hardware action was required for this plan.

## Task Commits

1. **Task 1 RED: reject a signature at the wrong PC** — `1d0309b` (`test`)
2. **Task 1 GREEN: qualify admitted Mooneye runner results** — `0e38a7a` (`feat`)
3. **Task 2: document derived evidence and hosted gate** — `ba28aa0` (`docs`)
4. **Task 2 gate correction: validate phase-required PR contexts** — `8481d60` (`fix`)

**Plan metadata:** committed separately with the summary and phase state records.

## Files Created/Modified

- `src/runner/main.c` — strict result protocol, admitted fixture identity, provenance-rich bounded receipts.
- `tests/test_runner.c` — wrong-PC and guest-induced assertion-failure regressions.
- `tests/CMakeLists.txt`, `tests/expected-tests.txt` — registered cases and exact inventory.
- `tests/scripts/verify-phase2-hosted.sh` — exact-PR-SHA and named-context gate.
- `README.md` — scoped corpus evidence and limitations.

## Decisions Made

- A result is credible only after the source-qualified callback and the fixture's exact result breakpoint both execute with the expected registers.
- Candidate fixtures remain accurately labeled as derived reporting closures. Their upstream acceptance logic is unchanged, while original PPU/LY behavior and physical hardware remain unqualified.
- Hosted evidence is required at the exact final PR SHA; successful local inventories do not substitute for remote evidence.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking issue] Verify Phase 2 contexts when GitHub reports no branch-protection-required contexts**
- **Found during:** Task 2
- **Issue:** PR #2 is stacked on a phase branch without configured branch protection, so `gh pr checks --required` returned no required contexts and could not satisfy the plan's fail-closed gate by itself.
- **Fix:** Require every reported PR check to pass and separately require the explicit Phase 2 context names, plus completed successful exact-SHA runs and required job names in both workflows.
- **Files modified:** `tests/scripts/verify-phase2-hosted.sh`
- **Verification:** The gate passed at PR head `8481d603b780af7889832ea3a8d3ad84d2439ba5`; no remote branch-protection setting was changed.
- **Committed in:** `8481d60`

**Total deviations:** 1 auto-fixed (Rule 3)
**Impact on plan:** The verifier now fails closed despite the repository's branch-protection configuration; implementation and fixture scope remained unchanged.

## Known Limitations

- CPU-01 through CPU-05 remain pending independent Phase 2 verification. Plan completion and green hosted checks are evidence for that verifier, not a phase-completion claim.
- The fixed three-case result applies to the admitted derived headless fixtures. The original upstream ROMs still depend on PPU/LY reporting and were not changed to fabricate PPU behavior. No physical DMG hardware run occurred.
- The final hosted verifier found no configured GitHub required-context policy on the stacked base branch; the explicit project context list passed for the observed final revision.

## User Setup Required

None. Credentials were available to inspect the open PR and hosted run evidence; no manual verification step was required.

## Next Phase Readiness

Plan 02-16 is complete. Phase GB-02 remains **executing** until independent verification assesses all seven gaps and requirement traceability. CPU-01 through CPU-05 remain pending; do not merge, release, or enter Phase 3 from this closeout. The next implementation phase is **Phase 3 — Visible Interactive DMG**, paused until Phase 2 is independently verified and the owner chooses to continue.

Next stage: run `$gsd-execute-phase 2 --gaps-only` to resume Phase GB-02 independent gap verification.

---
*Phase: GB-02-dmg-cpu-bus-and-time*
*Completed: 2026-10-07*

## Self-Check: PASSED

Summary file exists; all four measured plan task commits are ancestors of `8481d603b780af7889832ea3a8d3ad84d2439ba5`; the ledger count is 4.
