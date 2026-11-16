---
phase: "24"
slug: "resolve-remaining-v0-4-evidence-and-verification-gaps"
status: validated
nyquist_compliant: true
wave_0_complete: true
created: "2026-11-16"
---

# Phase 24 — Validation Strategy

> Validate the additive, point-in-time requirement and verification evidence map. Passing controls do not refresh Phase 20/21 verification, satisfy Pending requirements, or close v0.4.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Existing Python standard-library checker and CMake/CTest |
| **Config file** | `tests/cmake/hygiene.cmake`; existing `phase1` CMake preset |
| **Quick run command** | `python3 -I tests/scripts/verify-planning-hygiene.py --self-test --rev "$PHASE24_CHECK_REV" --repo .` — fails when canonical fixtures fail or semantic mutants pass/refuse for an unrelated cause. |
| **Focused CTest command** | `cmake --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '^(plan_cap|planning_hygiene_controls)$'` — fails when configure cannot pin the candidate, the real cap/control contract fails, no tests match, or the existing timeout is exceeded. |
| **Full suite command** | Not authorized in Phase 24; D-103 remains a separate exact-final-head milestone gate. |
| **Estimated runtime** | Not measured; runtime is not an acceptance signal. |

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Contract | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|----------|------------|-----------------|-----------|-------------------|-------------|--------|
| 24-01-T1-map | 01 | 1 | Eight-row point-in-time map and exact D-205 cap | T-24-01, T-24-02, T-24-04 | Reads committed inputs; keeps criteria/owner, tracker, audit, history, freshness, boundaries and gates separate; preserves at most 40 actual plans | integration | `python3 -I tests/scripts/verify-planning-hygiene.py --check v04-gap-assessment --stage report --rev "$PHASE24_CHECK_REV" --baseline-rev "$PHASE24_BASELINE_REV" --repo .` | Report stage passed at `883fdbba160b0afcd2b35d8c0363b2cba598c016`; the plan-cap controls also accept the exact 40-plan D-205 fixture | ✅ pass |
| 24-01-T2-controls | 01 | 1 | Causal report/handoff/cap negatives | T-24-01, T-24-02, T-24-03, T-24-04, T-24-05 | Canonical committed positives pass; false completion, owner drift, freshness promotion, closure, source substitution and extra plan capacity refuse for intended reasons | integration | `python3 -I tests/scripts/verify-planning-hygiene.py --self-test --rev "$PHASE24_CHECK_REV" --repo .` | Post-review-fix self-test passed with 628 controls at candidate `a1e8067500016158347e92522934b9af45d78386` | ✅ pass |
| 24-01-T3-closure | 01 | 1 | Bounded regression, block-style summary and shared generated closure | T-24-02, T-24-03, T-24-04, T-24-05 | Runs only the two approved CTests, records their actual checked commit, then generates and checks automated UAT without requirement/milestone completion | integration / other | Focused CTest command above, then shared summary/UAT commands below and committed handoff stage | Existing CTests and shared scripts | ✅ pass |

Every runnable plan command must state a causal `<fails_when>` condition. The immutable report check must use full commit IDs for the assessment input and any historical comparison baseline; it must not read current source facts from a moving branch or dirty worktree.

### Observed Direct Outcomes

- The committed report candidate passed the immutable report stage against input `f511baa8c0330f5cd90d56da55d79dbc873b0559` and baseline `f6fe166a7c2a3668f5a412a82b648dd062329d3c`.
- The post-review-fix direct self-test passed all 628 controls at candidate `a1e8067500016158347e92522934b9af45d78386`. This validates the semantic mutation families and immutable fixture behavior; it is not a result from either CTest.
- At `a1e8067500016158347e92522934b9af45d78386`, the direct immutable report and handoff stages passed against input `f511baa8c0330f5cd90d56da55d79dbc873b0559` and baseline `f6fe166a7c2a3668f5a412a82b648dd062329d3c`; the plan-cap CLI passed with six phases and 40 plans.
- Configure-only generation selected exactly the existing `plan_cap` and `planning_hygiene_controls` identities. Both wrapped commands used full revision `a1e8067500016158347e92522934b9af45d78386`; both retained `TIMEOUT=30`; `planning_hygiene_controls` retained `GBB_EXPECT_MIN_VALUE=125`.
- The focused CTest filter passed `2/2` at `a1e8067500016158347e92522934b9af45d78386`: `plan_cap` in 0.46 seconds and `planning_hygiene_controls` in 22.04 seconds. No emulator build was run.
- The actual SUMMARY passed the supported block-style coverage schema with 6 entries; `verify-summary-coverage.py --self-test` passed with 12 mutation controls.
- The shared generator wrote `24-UAT.md` with 6 automated items and 0 human checkpoints. The generated closure passed with 6/6 items and 0 gaps; its self-test passed with 21 mutation controls. These checks close only the Phase 24 assessment deliverables.
- The direct immutable report and handoff stages passed at post-fix candidate `a1e8067500016158347e92522934b9af45d78386`, distinct from the original task completion candidate. The final documentation handoff commit and its direct stage checks remain pending.

### Causal Failure Conditions

| Task | Pass contract | Fails when |
|---|---|---|
| 24-01-T1-map | Exact report CLI passes and immutable plan-cap CLI passes | Any original criterion/owner/status or source identity differs, Phase 20/21 history changes, freshness is promoted, the audit closes, the D-205 approval differs, or a 41st actual plan is allowed. |
| 24-01-T2-controls | Production CLI positives and semantic mutants have their intended outcomes | A positive fails, a mutant passes/refuses for the wrong reason, a dirty tree alters immutable results, or a previous Phase 22/D-193 control regresses. |
| 24-01-T3-closure | Only two focused CTests pass; actual summary/UAT and committed pending-verification handoff pass | A CTest fails/times out, configured source identity/filter differs, summary schema is invalid, closure has a gap/human checkpoint, or the current handoff promotes a requirement/milestone. |

### Shared Summary and UAT Closure

These are direct shared contract checks inside task 24-01-T3-closure, not additional CTest identities. Preserve the observed-check candidate separately from the later documentation-containing PHASE24_HANDOFF_REV; do not claim tests at that later head.

| Command | Causal failure condition |
|---|---|
| `python3 -I tests/scripts/verify-summary-coverage.py --file .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-01-SUMMARY.md` | Coverage is not the supported block schema or cites missing/nonpassing evidence. |
| `python3 -I tests/scripts/verify-summary-coverage.py --self-test` | Canonical coverage fails or malformed coverage is accepted. |
| `python3 -I tests/scripts/verify-uat-closure.py .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps --write .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/.continue-here.md` | Actual summary coverage cannot generate gap-free automated closure. |
| `python3 -I tests/scripts/verify-uat-closure.py .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps` | Generated closure contradicts summary, lacks evidence, or has an unresolved phase-deliverable gap. |
| `python3 -I tests/scripts/verify-uat-closure.py .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps --self-test` | The shared checker accepts weakened closure copies. |
| `python3 -I tests/scripts/verify-planning-hygiene.py --check v04-gap-assessment --stage handoff --rev "$PHASE24_HANDOFF_REV" --baseline-rev "$PHASE24_BASELINE_REV" --repo .` | Current handoff/SUMMARY loses Pending owners, stops, evidence links or the bounded verification route, or implies requirement/milestone completion. |

---

## Sampling Rate

- **After each checker change:** Run cheap syntax and direct positive/negative controls before any CTest.
- **At the final committed candidate:** Reconfigure the existing `phase1` preset and run only `plan_cap` and `planning_hygiene_controls`.
- **After the focused checks:** Record only observed results, then check summary coverage and the shared generated UAT closure. Commit the documentation and check its report/handoff stages without misattributing earlier focused results to that new commit.
- **Stopped:** Do not run the broad suite, a lifecycle retry, release checks, fixture/source acquisition, or rights action.

---

## Wave 0 Requirements

The existing Python standard-library checker, immutable Git snapshot reader, CMake preset, two focused CTests, summary-coverage checker, and shared UAT-closure checker cover the approved scope. No package, framework, new CTest identity, emulator build, fixture, or external service is required.

---

## Manual-Only Verifications

None. Source-page access outcomes are recorded only when supported by existing first-party observations; they do not establish rights. Fixture admission, rights determinations, and all four original Pending requirements remain outside this phase's automated closure claim.

---

## Validation Sign-Off

- [x] Every task has an automated pass and failure condition.
- [x] The point-in-time evidence map rejects false completion, owner transfer, freshness promotion, and milestone closure.
- [x] Historical Phase 20/21 reports and source identities remain unchanged.
- [x] Only `plan_cap` and `planning_hygiene_controls` CTests run.
- [x] All four requirements remain Pending under original owners and v0.4 remains open.
- [x] Phase completion is not represented as requirement or milestone completion.

Plan 24-01 execution checks are recorded above. The fresh independent code review, configured regression hook, phase verifier, and owner-controlled milestone audit remain separate gates. All three task IDs match 24-01-PLAN.md; shared closure belongs to T3 rather than a fourth task.

## Validation Audit 2026-11-16

| Metric | Count |
|---|---|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
