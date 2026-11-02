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
| **Quick run command** | `ctest --preset phase1 --output-on-failure --no-tests=error -R 'acceptance_cgb_progress|cgb_runner_profile_dmg_identity_acceptance'` after configure/build. |
| **Full suite command** | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error`. |
| **Feedback target** | Keep focused progress and contract checks under 30 seconds; measure and record actual full-suite runtime during execution. |

---

## Sampling Rate

- **After each task commit:** Run the smallest focused CTest or standard-library contract check for the changed behavior.
- **After each plan wave:** Run the combined acceptance and admission checks affected by that wave; avoid repeating the full suite when focused checks cover the changes.
- **Before `$gsd-verify-work`:** Run the configured full suite once at the final implementation head and retain exact-head evidence.
- **Feedback target:** Under 30 seconds for the focused CGB progress path; record actual duration rather than assuming it.

---

## Per-Task Verification Map

All task statuses are pending implementation. Commands below are the focused contract selectors; each PLAN carries its full configure/build prerequisites, additional checks and observable `fails_when` condition.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 21-01-01 | 21-01 | 1 | GAME-01, GAME-02 | T-21-01, T-21-02 | Native-CGB source-bound original input/predicate tracer; missing input fails. | integration | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^acceptance_cgb_progress_tracer$'` | New in task | pending |
| 21-01-02 | 21-01 | 1 | GAME-01, GAME-02 | T-21-01, T-21-02 | Actual compatibility-mode refusal and unchanged Libbet/DMG policy. | integration | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(acceptance_cgb_progress_tracer|acceptance_cgb_progress_compat_rejected|cgb_runner_profile_dmg_identity_acceptance|dmg_baseline)$'` | New controls plus existing baseline | pending |
| 21-02-01 | 21-02 | 2 | GAME-01, GAME-02 | T-21-03 | No-input/wrong-input/impossible-predicate raw failures and strict mapping. | integration | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(acceptance_cgb_progress_(tracer|compat_rejected|discrimination)|acceptance_predicate_(truth_table|anchors)|acceptance_cgb_colour_.*)$'` | Extended in task | pending |
| 21-02-02 | 21-02 | 2 | GAME-01, GAME-02 | T-21-04 | Bound native observations/dumps with independent original sequence and content mutations. | integration | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(acceptance_cgb_progress_.*|acceptance_digest_rgb555_vectors|cgb_runner_profile_dmg_identity_acceptance|dmg_baseline|test_budget(_controls)?)$'` | Extended in task | pending |
| 21-03-01 | 21-03 | 1 | FIXT-01 | T-21-05, T-21-06 | Actual candidate-record CLI rejects missing/early fallback and partial closure. | integration | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase21_fixture_admission_contract$'` | New in task | pending |
| 21-03-02 | 21-03 | 1 | FIXT-01, GAME-02 | T-21-06 | Existing admission CLI and exact game-progress binding reject coordinated rewrites; executed builds require confinement/probe evidence and permissive mutations fail. | integration | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase21_fixture_admission_(contract|controls)$'` | Extended in task | pending |
| 21-04-01 | 21-04 | 3 | FIXT-01 | T-21-07, T-21-08 | Actual primary source/build/rights facts plus credential-free offline confinement/probes before build, or attributable pre-execution no-go. | other | `python3 -I tests/scripts/verify-cgb-candidates.py --check-record tests/data/cgb-candidates/potion-panic.json --stage assessed --repo-root . --source-revision HEAD` | Record created in task | pending |
| 21-04-02 | 21-04 | 3 | FIXT-01 | T-21-09 | Only permitted source-built provenance is prepared; no-go has no fixture consumption path. | integration | `python3 -I tests/scripts/verify-cgb-candidates.py --check-record tests/data/cgb-candidates/potion-panic.json --stage provenance --repo-root . --source-revision HEAD` | Conditional fixture artifacts | pending |
| 21-04-03 | 21-04 | 3 | FIXT-01, GAME-02 | T-21-09 | Immutable admission and native input/predicate controls, or final genuine no-go. | integration | `python3 -I tests/scripts/verify-cgb-candidates.py --check-record tests/data/cgb-candidates/potion-panic.json --require-final --runner build/gabbaboy-runner --repo-root . --source-revision HEAD` | Conditional case/record | pending |
| 21-05-01 | 21-05 | 4 | FIXT-01 | T-21-10, T-21-11 | Primary disposition controls preferred µCity 1.3 eligibility; any build requires credential-free offline confinement/probes or a pre-execution no-go. | other | `python3 -I tests/scripts/verify-cgb-candidates.py --check-record tests/data/cgb-candidates/ucity-1.3.json --stage assessed --repo-root . --source-revision HEAD` | Record created in task | pending |
| 21-05-02 | 21-05 | 4 | FIXT-01 | T-21-12 | Complete mixed-component snapshot or no fallback consumption artifacts. | integration | `python3 -I tests/scripts/verify-cgb-candidates.py --check-record tests/data/cgb-candidates/ucity-1.3.json --stage provenance --repo-root . --source-revision HEAD` | Conditional fixture artifacts | pending |
| 21-05-03 | 21-05 | 4 | FIXT-01, GAME-02 | T-21-12 | Entire ordered pair final; native progress controlled and unresolved defects block. | integration | `python3 -I tests/scripts/verify-cgb-candidates.py --check-all --require-final --runner build/gabbaboy-runner --repo-root . --source-revision HEAD` | Conditional case/record | pending |
| 21-06-01 | 21-06 | 2 | FEED-01 | T-21-13 | Minimal text intake without implicit personal-media or owner-play requirements. | integration | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase21_scene_report_tracer$'` | New in task | pending |
| 21-06-02 | 21-06 | 2 | FEED-01 | T-21-13, T-21-14 | Independent permitted scene promotion, relevant negatives and privacy controls. | integration | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase21_scene_report_(tracer|controls|contract)$'` | Extended in task | pending |
| 21-07-01 | 21-07 | 5 | GAME-01, GAME-02, FIXT-01, FEED-01 | T-21-15, T-21-16 | Integrated actual outcome/docs reject false or unsupported claims. | integration | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase21_(game_evidence(_controls)?|fixture_admission|scene_report_.*)$'` | New composition checks | pending |
| 21-07-02 | 21-07 | 5 | GAME-01, GAME-02, FIXT-01, FEED-01 | T-21-16, T-21-17 | Final source/full-suite/hosted-consumer and traceable automated closure. | integration | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` | Existing full suite plus new tests | pending |

Every runnable command added to a plan must name an observable `fails_when` condition. Expected-failure controls must assert the raw predicate/mode reason so setup errors cannot masquerade as the intended negative.

---

## Wave 0 Requirements

- [ ] Generate the original native-CGB control from pinned project-authored source/build/digest in Plan 21-01; label it harness-only and use its result as the fallback harness evidence if neither named game is admitted.
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

The six spec-less edge assumptions and two descriptor-less values prohibitions remain visible in the plan set and source audit. They are not fabricated automated passes or new manual UAT tasks.

**Approval:** planning decomposition recorded; implementation, audit and final-source evidence remain pending.
