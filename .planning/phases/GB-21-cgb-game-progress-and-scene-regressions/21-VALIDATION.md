---
phase: "21"
slug: "cgb-game-progress-and-scene-regressions"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-11-01"
---

# Phase 21 — Validation Strategy

> Feedback contract for CGB progress, fixture admission, and scene triage. RGB555/PCM digests establish repeatability, not accuracy; identity checks do not establish redistribution permission.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | CMake/CTest; Python standard-library checker tests where a source-bound fixture or report contract needs a dedicated validator. |
| **Config file** | `CMakePresets.json` (`phase1`); acceptance registrations in `tests/acceptance/CMakeLists.txt`. |
| **Quick run command** | `ctest --preset phase1 --output-on-failure -R 'acceptance_cgb_progress|cgb_runner_profile_dmg_identity_acceptance'` after configure/build. |
| **Full suite command** | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error`. |
| **Feedback target** | Keep focused progress and contract checks under 30 seconds; measure and record actual full-suite runtime during execution. |

---

## Sampling Rate

- **After each task commit:** Run the smallest focused CTest or standard-library contract check for the changed behavior.
- **After each plan wave:** Run the combined acceptance and admission checks affected by that wave; avoid repeating the full suite when focused checks cover the changes.
- **Before `$gsd-verify-work`:** Run the configured full suite once at the final implementation head and retain exact-head evidence.
- **Feedback target:** Under 30 seconds for the focused CGB progress path; record actual duration rather than assuming it.

---

## Per-Requirement Verification Map

The planner will assign exact plan/task IDs and waves after decomposition; the following contract map is the validation target.

| Requirement | Behavior | Threat Ref | Secure Behavior | Test Type | Automated Command | Existing Coverage |
|-------------|----------|------------|-----------------|-----------|-------------------|-------------------|
| GAME-01 | CGB progress copies RGB555 observations and preserves the existing DMG receipt/output behavior. | Plan threat register | Keep profile-aware frame dispatch bounded; preserve the DMG path and identity assertion. | integration | `ctest --preset phase1 --output-on-failure -R 'acceptance_cgb_progress|acceptance_cgb_colour|cgb_runner_profile_dmg_identity_acceptance'` | CGB digest and DMG identity patterns exist; CGB progress integration is new. |
| GAME-02 | Positive scripted input reaches an independently specified guest predicate; no/wrong input, broken predicate, and wrong-mode controls fail for their intended reasons; receipt binds ROM, input, predicate, profile, mode, and observations. | Plan threat register | Reject malformed or mismatched inputs before guest creation; distinguish expected predicate failure from setup failure. | integration | `ctest --preset phase1 --output-on-failure -R 'acceptance_cgb_progress'` | DMG predicate controls exist; CGB progress controls are new. |
| FIXT-01 | Only the ordered Potion Panic attempt and, after its recorded no-go, µCity 1.3 fallback run; each has exact source/build/ROM/header/mode and rights evidence or a concrete no-go. | Plan threat register | Fail closed on incomplete identity, component terms, or notices; keep candidate ROMs out of installed/release products. | unit/integration | `ctest --preset phase1 --output-on-failure -R 'phase21_fixture_admission'` | Phase 20 fixture manifest and product-policy patterns exist; Phase 21 candidate records/checks are new. |
| FEED-01 | A title/scene/symptom report starts agent-owned reproduction and classification; any promoted regression has an independent expectation and targeted negative; private media stays outside repository and CI. | Plan threat register | Use only original or rights-admitted fixtures; preserve report data without copying personal ROMs, saves, states, or captures. | unit/automated | `ctest --preset phase1 --output-on-failure -R 'phase21_scene_report'` | No current actionable GabbaBoy scene report was found; retain triage when no independent regression can be justified. |

Every runnable command added to a plan must name an observable `fails_when` condition. Expected-failure controls must assert the raw predicate/mode reason so setup errors cannot masquerade as the intended negative.

---

## Wave 0 Requirements

- [ ] Add an original native-CGB control ROM with fixed provenance/build/digest if neither named game is admitted; label it harness-only.
- [ ] Add CGB progress positive and fault-specific input, predicate, and execution-mode negative controls in the existing CMake/CTest acceptance path.
- [ ] Add or extend an immutable-source fixture-admission checker for the two candidate records and malformed-record controls.
- [ ] Add a report-intake or scene-promotion contract check if no real symptom can be promoted; do not invent a scene report.

---

## Manual-Only Verifications

There is no mandatory manual UAT. Candidate redistribution decisions must remain grounded in per-component source evidence; if evidence is unresolved, record a no-go and do not claim clearance. The phase's software-model observations do not establish physical hardware or perceptual behavior.

---

## Validation Sign-Off

- [ ] Every plan task has an automated verify command or an explicit Wave 0 dependency.
- [ ] Sampling continuity has no three consecutive tasks without automated verification.
- [ ] Wave 0 covers the missing harness, admission, and report-contract checks.
- [ ] No watch-mode flags.
- [ ] Focused feedback target is under 30 seconds; actual timings will be recorded during execution.
- [ ] `nyquist_compliant: true` set in frontmatter after validation.

**Approval:** pending planning decomposition and execution evidence.
