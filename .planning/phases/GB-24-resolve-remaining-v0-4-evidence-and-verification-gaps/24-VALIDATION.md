---
phase: "24"
slug: "resolve-remaining-v0-4-evidence-and-verification-gaps"
status: draft
nyquist_compliant: false
wave_0_complete: false
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
| **Quick run command** | `python3 -I tests/scripts/verify-planning-hygiene.py --self-test --rev "$PHASE24_CHECK_REV" --repo .` |
| **Focused CTest command** | `cmake --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '^(plan_cap|planning_hygiene_controls)$'` |
| **Full suite command** | Not authorized in Phase 24; D-103 remains a separate exact-final-head milestone gate. |
| **Estimated runtime** | Not measured; runtime is not an acceptance signal. |

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Contract | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|----------|------------|-----------------|-----------|-------------------|-------------|--------|
| 24-01-T1-map | 01 | 1 | Point-in-time requirement map | T-24-01, T-24-02 | Reads exact committed inputs and keeps source facts, tracker/audit status, historical report result, freshness, and remaining gates separate | integration | `python3 -I tests/scripts/verify-planning-hygiene.py --check v04-gap-assessment --rev "$PHASE24_CHECK_REV" --repo .` | Planned | ⬜ pending |
| 24-01-T2-controls | 01 | 1 | False completion/owner/milestone negatives | T-24-01 | Canonical evidence passes; causal mutations for Pending status, original owner, stale freshness, and open milestone are refused through the production checker | integration | `python3 -I tests/scripts/verify-planning-hygiene.py --self-test --rev "$PHASE24_CHECK_REV" --repo .` | Existing checker; new cases planned | ⬜ pending |
| 24-01-T3-boundary | 01 | 1 | Plan-cap and bounded regression gate | T-24-02 | Uses the committed full revision; runs only the two owner-selected focused CTests | integration | `cmake --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '^(plan_cap|planning_hygiene_controls)$'` | Existing CTests | ⬜ pending |
| 24-01-T4-closure | 01 | 1 | Summary and generated closure | — | Summary coverage uses the required GSD block schema and shared closure reports no human checkpoint or coverage gap | other | `python3 -I tests/scripts/verify-summary-coverage.py --file .planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-01-SUMMARY.md` | Existing checker | ⬜ pending |

Every runnable plan command must state a causal `<fails_when>` condition. The immutable report check must use full commit IDs for the assessment input and any historical comparison baseline; it must not read current source facts from a moving branch or dirty worktree.

---

## Sampling Rate

- **After each checker change:** Run cheap syntax and direct positive/negative controls before any CTest.
- **At the final committed candidate:** Reconfigure the existing `phase1` preset and run only `plan_cap` and `planning_hygiene_controls`.
- **Before phase closure:** Check summary coverage and the shared generated UAT closure. Record the assessed input revision and the containing evidence commit separately.
- **Stopped:** Do not run the broad suite, a lifecycle retry, release checks, fixture/source acquisition, or rights action.

---

## Wave 0 Requirements

The existing Python standard-library checker, immutable Git snapshot reader, CMake preset, two focused CTests, summary-coverage checker, and shared UAT-closure checker cover the approved scope. No package, framework, new CTest identity, emulator build, fixture, or external service is required.

---

## Manual-Only Verifications

None. Source-page access outcomes are recorded only when supported by existing first-party observations; they do not establish rights. Fixture admission, rights determinations, and all four original Pending requirements remain outside this phase's automated closure claim.

---

## Validation Sign-Off

- [ ] Every task has an automated pass and failure condition.
- [ ] The point-in-time evidence map rejects false completion, owner transfer, freshness promotion, and milestone closure.
- [ ] Historical Phase 20/21 reports and source identities remain unchanged.
- [ ] Only `plan_cap` and `planning_hygiene_controls` CTests run.
- [ ] All four requirements remain Pending under original owners and v0.4 remains open.
- [ ] Phase completion is not represented as requirement or milestone completion.
