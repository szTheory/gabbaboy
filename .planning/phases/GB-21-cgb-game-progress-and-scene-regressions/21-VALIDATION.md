---
phase: "21"
slug: "cgb-game-progress-and-scene-regressions"
status: local-qualified
nyquist_compliant: true
wave_0_complete: true
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

Plan 21-07 implementation and local qualification are complete. The table records passing automated contracts; exact-head hosted qualification must be checked after the final plan metadata commit. Commands below are focused selectors; each PLAN carries its full configure/build prerequisites, additional checks and observable `fails_when` condition.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 21-01-01 | 21-01 | 1 | GAME-01, GAME-02 | T-21-01, T-21-02 | Native-CGB source-bound original input/predicate tracer; missing input fails. | integration | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^acceptance_cgb_progress_tracer$'` | New in task | pass |
| 21-01-02 | 21-01 | 1 | GAME-01, GAME-02 | T-21-01, T-21-02 | Actual compatibility-mode refusal and unchanged Libbet/DMG policy. | integration | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(acceptance_cgb_progress_tracer|acceptance_cgb_progress_compat_rejected|cgb_runner_profile_dmg_identity_acceptance|dmg_baseline)$'` | New controls plus existing baseline | pass |
| 21-02-01 | 21-02 | 2 | GAME-01, GAME-02 | T-21-03 | No-input/wrong-input/impossible-predicate raw failures and strict mapping. | integration | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(acceptance_cgb_progress_(tracer|compat_rejected|discrimination)|acceptance_predicate_(truth_table|anchors)|acceptance_cgb_colour_.*)$'` | Extended in task | pass |
| 21-02-02 | 21-02 | 2 | GAME-01, GAME-02 | T-21-04 | Bound native observations/dumps with independent original sequence and content mutations. | integration | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(acceptance_cgb_progress_.*|acceptance_digest_rgb555_vectors|cgb_runner_profile_dmg_identity_acceptance|dmg_baseline|test_budget(_controls)?)$'` | Extended in task | pass |
| 21-03-01 | 21-03 | 1 | FIXT-01 | T-21-05, T-21-06 | Actual candidate-record CLI rejects missing/early fallback and partial closure. | integration | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase21_fixture_admission_contract$'` | New in task | pass |
| 21-03-02 | 21-03 | 1 | FIXT-01, GAME-02 | T-21-06 | Existing admission CLI and exact game-progress binding reject coordinated rewrites; executed builds require confinement/probe evidence and permissive mutations fail. | integration | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase21_fixture_admission_(contract|controls)$'` | Extended in task | pass |
| 21-04-01 | 21-04 | 3 | FIXT-01 | T-21-07, T-21-08 | Actual primary source/build/rights facts plus credential-free offline confinement/probes before build, or attributable pre-execution no-go. | other | `python3 -I tests/scripts/verify-cgb-candidates.py --check-record tests/data/cgb-candidates/potion-panic.json --stage assessed --repo-root . --source-revision HEAD` | Record created in task | pass |
| 21-04-02 | 21-04 | 3 | FIXT-01 | T-21-09 | Only permitted source-built provenance is prepared; no-go has no fixture consumption path. | integration | `python3 -I tests/scripts/verify-cgb-candidates.py --check-record tests/data/cgb-candidates/potion-panic.json --stage provenance --repo-root . --source-revision HEAD` | Conditional fixture artifacts | pass |
| 21-04-03 | 21-04 | 3 | FIXT-01, GAME-02 | T-21-09 | Immutable admission and native input/predicate controls, or final genuine no-go. | integration | `python3 -I tests/scripts/verify-cgb-candidates.py --check-record tests/data/cgb-candidates/potion-panic.json --require-final --runner build/gabbaboy-runner --repo-root . --source-revision HEAD` | Conditional case/record | pass |
| 21-05-01 | 21-05 | 4 | FIXT-01 | T-21-10, T-21-11 | Primary disposition controls preferred µCity 1.3 eligibility; any build requires credential-free offline confinement/probes or a pre-execution no-go. | other | `python3 -I tests/scripts/verify-cgb-candidates.py --check-record tests/data/cgb-candidates/ucity-1.3.json --stage assessed --repo-root . --source-revision HEAD` | Record created in task | pass |
| 21-05-02 | 21-05 | 4 | FIXT-01 | T-21-12 | Complete mixed-component snapshot or no fallback consumption artifacts. | integration | `python3 -I tests/scripts/verify-cgb-candidates.py --check-record tests/data/cgb-candidates/ucity-1.3.json --stage provenance --repo-root . --source-revision HEAD` | Conditional fixture artifacts | pass |
| 21-05-03 | 21-05 | 4 | FIXT-01, GAME-02 | T-21-12 | Entire ordered pair final; native progress controlled and unresolved defects block. | integration | `python3 -I tests/scripts/verify-cgb-candidates.py --check-all --require-final --runner build/gabbaboy-runner --repo-root . --source-revision HEAD` | Conditional case/record | pass |
| 21-06-01 | 21-06 | 2 | FEED-01 | T-21-13 | Minimal text intake without implicit personal-media or owner-play requirements. | integration | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase21_scene_report_tracer$'` | New in task | pass |
| 21-06-02 | 21-06 | 2 | FEED-01 | T-21-13, T-21-14 | Independent permitted scene promotion, relevant negatives and privacy controls. | integration | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase21_scene_report_(tracer|controls|contract)$'` | Extended in task | pass |
| 21-07-01 | 21-07 | 5 | GAME-01, GAME-02, FIXT-01, FEED-01 | T-21-15, T-21-16 | Integrated actual outcome/docs reject false or unsupported claims. | integration | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase21_(game_evidence(_controls)?|fixture_admission|scene_report_.*)$'` | New composition checks | pass |
| 21-07-02 | 21-07 | 5 | GAME-01, GAME-02, FIXT-01, FEED-01 | T-21-16, T-21-17 | Final source/full-suite/hosted-consumer and traceable automated closure. | integration | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` | Existing full suite plus new tests | local pass; check live exact-head PR status |

Every runnable command added to a plan must name an observable `fails_when` condition. Expected-failure controls must assert the raw predicate/mode reason so setup errors cannot masquerade as the intended negative.

---

## Wave 0 Requirements

- [x] Generate the original native-CGB control from pinned project-authored source/build/digest in Plan 21-01; label it harness-only and use its result as the fallback harness evidence if neither named game is admitted.
- [x] Add CGB progress positive and fault-specific input, predicate, and execution-mode negative controls in the existing CMake/CTest acceptance path.
- [x] Add or extend an immutable-source fixture-admission checker for the two candidate records and malformed-record controls.
- [x] Add a report-intake or scene-promotion contract check without inventing a scene report.

---

## Manual-Only Verifications

There is no mandatory manual UAT. Candidate redistribution decisions must remain grounded in per-component source evidence; if evidence is unresolved, record a no-go and do not claim clearance. The phase's software-model observations do not establish physical hardware or perceptual behavior.

---

## Validation Sign-Off

- [x] Every plan task has an automated verify command or an explicit Wave 0 dependency.
- [x] Sampling continuity has no three consecutive tasks without automated verification.
- [x] Wave 0 covers the missing harness, admission, and report-contract checks.
- [x] No watch-mode flags.
- [x] The CGB evidence tracer and composition check meet the focused feedback target; the broad fixture-admission mutation suite is measured separately at 43.06 seconds and remains within the deterministic 60-second CTest budget.
- [x] `nyquist_compliant: true` set in frontmatter after local validation.

The six spec-less edge assumptions and two descriptor-less values prohibitions remain visible in the plan set and source audit. They are not fabricated automated passes or new manual UAT tasks.

## Final Local Evidence

Final code-change source and runner identity: `66ee663ba8f7a505d67871fab7163b57306d0dd2`.

- Configure: `cmake -S . -B build` — passed.
- Build: `cmake --build build` — passed (638 Ninja build steps).
- Full CTest: `ctest --test-dir build --output-on-failure --timeout 60 --parallel 1` — passed 1724/1724 in 1,204.93 seconds. The project budget and baseline remain unchanged. Sandbox-restricted attempts could not create temporary Git worktrees under `.git/worktrees`; the complete final run passed with repository-write permission.
- Fixture-admission budget: `phase21_fixture_admission_contract` took 3.61 seconds and `phase21_fixture_admission_controls` took 12.48 seconds; both retain explicit 60-second CTest limits. The full run's `test_budget` check passed. Earlier 120/180-second declarations were brought within the fixed 60-second budget by removing redundant full-checker work per mutation; neither the budget nor its baseline was raised or refreshed, and no unrelated v0.3 debt was changed.
- Source-bound receipt: `python3 -I tests/scripts/verify-cgb-game-evidence.py --check --runner build/gabbaboy-runner --repo-root . --source-revision 66ee663ba8f7a505d67871fab7163b57306d0dd2 --write-evidence build/phase21-evidence/result.json` — passed at the implementation source and runner identity. Outcome is `game=not-admitted`, model `CGB-CPU-E`, mode `cgb`.
- Final focused evidence: `ctest --test-dir build --output-on-failure --timeout 60 --parallel 1 -R '^(phase21_.*|summary_coverage.*|lessons_unique_ids|state_size|test_budget)$'` passed 16/16 in 26.56 seconds after the summary/lesson updates. It covers summary schema, unique lesson IDs, state size, the fixed budget, and every Phase 21 contract.
- Candidate result: Potion Panic is no-go because exact source/component grants and repository/public-CI rights scope could not be established after its author-linked source fetch failed. µCity 1.3 is no-go because required `source/engine/hardware.inc` has no identified grant or notice, leaving complete build-source scope unestablished. These are rights/source-scope no-go decisions, not claims that either license prohibits use.
- Neither game source was run. Fallback toolchain/build/run facts remain `not_observed`; no fallback fixture, acceptance case, input, predicate, or notice row exists. Original ROM progress remains harness-only. RGB555/PCM digests show repeatability only; no accuracy, physical-hardware, perceptual, mode-3 timing, or general-compatibility claim is made.
- Independent code review at `893ecac8`: clean, 0 findings. Executor follow-up through `66ee663b` found that the new path normalization adds no security surface. See `21-07-REVIEW.md`. Security review closed implementation mitigations for T-21-15 and T-21-SC. Exact-head hosted/platform/installed-consumer checks remain open for T-21-16; shared verify-work closure remains for T-21-17.

## CI/CD Efficiency

The full local serial run measured 1,204.93 seconds. `workflow_policy_group_release_jobs` took 60.91 seconds and passed; fixture-admission contract and mutation controls took 3.61 and 12.48 seconds under their unchanged declared 60-second caps, and `test_budget` passed. CI uses four workers. Exact-source push run `41430769014` on `6d552502` passed Linux native/sanitizer, macOS native, CMake-floor, and acceptance jobs; Windows failed only `phase21_scene_report_controls`, whose mixed path separators are fixed at `66ee663b`. Fixture-reproduction run `41430769108` passed. The push event skipped PR-only planning and macOS package checks, so these diagnostics are not hosted qualification. Measurements do not justify changing concurrency, caching, timeouts, or test membership.

## Hosted Qualification

PR #140 is the required source for exact-head native/platform and installed-consumer qualification. After the final metadata commit is pushed, accept only successful pull-request runs whose `headSha` equals the current PR head; push-event and local results are not substitutes. The previous exact-source push diagnostic failed on the path comparison that `66ee663b` fixes. Read the current hosted result live from PR #140; once exact-head checks pass, use the shared `/gsd-verify-work 21` closure.

**Status:** local implementation and automated validation are recorded; PR #140 carries the live hosted status, and shared phase closure remains a separate step.
