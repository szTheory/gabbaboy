---
phase: GB-21-cgb-game-progress-and-scene-regressions
verified: 2026-11-03T01:29:42Z
status: passed
score: 5/5 roadmap success criteria verified
covered_files:
  - .planning/phases/GB-21-cgb-game-progress-and-scene-regressions/21-01-PLAN.md
  - .planning/phases/GB-21-cgb-game-progress-and-scene-regressions/21-01-SUMMARY.md
  - .planning/phases/GB-21-cgb-game-progress-and-scene-regressions/21-02-PLAN.md
  - .planning/phases/GB-21-cgb-game-progress-and-scene-regressions/21-02-SUMMARY.md
  - .planning/phases/GB-21-cgb-game-progress-and-scene-regressions/21-03-PLAN.md
  - .planning/phases/GB-21-cgb-game-progress-and-scene-regressions/21-03-SUMMARY.md
  - .planning/phases/GB-21-cgb-game-progress-and-scene-regressions/21-04-PLAN.md
  - .planning/phases/GB-21-cgb-game-progress-and-scene-regressions/21-04-SUMMARY.md
  - .planning/phases/GB-21-cgb-game-progress-and-scene-regressions/21-05-PLAN.md
  - .planning/phases/GB-21-cgb-game-progress-and-scene-regressions/21-05-SUMMARY.md
  - .planning/phases/GB-21-cgb-game-progress-and-scene-regressions/21-06-PLAN.md
  - .planning/phases/GB-21-cgb-game-progress-and-scene-regressions/21-06-SUMMARY.md
  - .planning/phases/GB-21-cgb-game-progress-and-scene-regressions/21-07-PLAN.md
  - .planning/phases/GB-21-cgb-game-progress-and-scene-regressions/21-07-SUMMARY.md
  - .planning/phases/GB-21-cgb-game-progress-and-scene-regressions/21-08-PLAN.md
  - .planning/phases/GB-21-cgb-game-progress-and-scene-regressions/21-08-SUMMARY.md
  - CMakeLists.txt
  - docs/cgb-game-candidates.md
  - docs/cgb-profile.md
  - docs/game-acceptance.md
  - docs/scene-feedback.md
  - docs/support/unreleased.md
  - src/accept/gbb_accept.h
  - src/accept/predicate.c
  - src/runner/acceptance.c
  - tests/CMakeLists.txt
  - tests/acceptance/CMakeLists.txt
  - tests/acceptance/cases-cgb-colour.txt
  - tests/ci/test-budget-allowlist
  - tests/cmake/game-evidence.cmake
  - tests/data/cgb-candidates/potion-panic.json
  - tests/data/cgb-candidates/ucity-1.3.json
  - tests/data/state-forks.json
  - tests/expected-tests.txt
  - tests/scripts/test_cgb_candidate_order.py
  - tests/scripts/verify-cgb-candidates.py
  - tests/scripts/verify-cgb-game-evidence.py
  - tests/scripts/verify-cgb-progress.py
  - tests/scripts/verify-fixture-admission.py
  - tests/scripts/verify-scene-report.py
  - tests/test_acceptance_lib.c
covered_digest: "v4:sha256:30ca52c3f9ec374cd4501beb91f09aee6044497bd31d4f46e0e19fd6642363fc"
behavior_unverified: 0
overrides_applied: 1
re_verification:
  previous_status: gaps_found
  previous_score: 4/5
  gaps_closed:
    - "Exact-head hosted qualification for implementation source e0845db5841a1d56d8a297cbfaa3e0811af6ad67 passed."
    - "FIXT-01's phase requirement gap was accepted as an intentional deferral by the project owner; the requirement itself remains Pending."
  gaps_remaining: []
  regressions: []
advisory: []
overrides:
  - must_have: "FIXT-01: each named candidate attempt verifies exact source/build, ROM digest, cartridge metadata, and native CGB mode, or records a bounded reasoned absence."
    reason: "The owner directs FIXT-01 to remain Pending: both candidates stopped at source/rights gates before build and ROM facts, and Phase 21 accepts the bounded no-go plus harness-only outcome. This applies only to this phase's incomplete requirement; it claims no license prohibition, grant, fixture admission, or completed requirement."
    accepted_by: "project owner"
    accepted_at: "2026-11-02T21:29:20-04:00"
---

# Phase 21: CGB Game Progress and Scene Regressions Verification Report

**Phase Goal:** Maintainers can obtain a reproducible CGB progress result from the shared runner, explain the bounded game-candidate outcome, and turn useful scene reports into controlled regressions.

**Verified:** 2026-11-03T01:29:42Z

**Status:** passed

**Re-verification:** Yes — after exact-head hosted qualification and owner override

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | Shared runner observes native CGB RGB555 output and guest progress on CGB-CPU-E while preserving DMG acceptance. | VERIFIED | Current `build/phase21-evidence/result.json` binds source `e0845db5841a1d56d8a297cbfaa3e0811af6ad67`, qualified runner digest, native `cgb`, `CGB-CPU-E`, authored ROM/input digests, predicate, RGB555 and PCM observations. `src/runner/acceptance.c` queries loaded mode and captures RGB555; DMG policy remains on the existing acceptance path. |
| 2 | Positive input reaches the guest predicate; no-input, wrong-input, impossible-predicate and compatibility-mode controls reject vacuous progress. | VERIFIED | Current receipt records positive pass, three `predicate-not-reached` controls and compatibility refusal. Local CTest evidence is at this source. The result class is `original-harness-only`, not game progress. |
| 3 | Search assesses Potion Panic first and only then µCity 1.3, records source/build and rights evidence reached at each gate, and performs no third search. | VERIFIED WITH LIMIT | Current-source candidate checker passed. Exactly two records exist in order. The primary could not be resolved from the creator-linked source; the fallback source is pinned and its required include lacks identified grant/notice. Records mark downstream build, ROM and mode facts unobserved at the rights cutoff. |
| 4 | If neither game is admitted, evidence names the actual blockers and delivers a concrete harness result without presenting it as admitted game evidence. | VERIFIED | Both rights/source-scope no-go outcomes and the current CGB-CPU-E original harness result are composed in the receipt and docs. No license prohibition, game progress, physical behavior, perceptual quality or general compatibility is claimed. FIXT-01 remains pending. |
| 5 | Text-only scene reports support agent-owned reproduction/classification and controlled promotion with privacy boundaries. | VERIFIED | `verify-scene-report.py`, `docs/scene-feedback.md`, test registration and receipt cover intake, synthetic promotion, independent expectation, causal negative control, optional owner play and personal-media exclusion. No live report/defect is claimed. |
| 6 | Current-source hosted/platform and installed-consumer qualification completes before phase closure. | VERIFIED WITH FOLLOW-UP GATE | `21-UAT-EVIDENCE.md` records PR #140 checks passing at exact implementation source `e0845db5841a1d56d8a297cbfaa3e0811af6ad67`, including native Windows/Linux/macOS, sanitizer, fixture reproduction, package consumers and player package smoke. The verification artifact changes the closeout revision; its final PR head must receive the required checks before merge. |

**Score:** 5/5 roadmap success criteria verified. The bounded no-go/harness-only result satisfies the roadmap's justified-absence outcome and does not claim game admission. FIXT-01 remains Pending in `REQUIREMENTS.md`; its phase-level gap is accepted by the owner as an intentional deferral using the override recorded above. The hosted qualification passed at `e0845db`; rerun it for the closeout artifact's final PR head before merge.

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `src/runner/acceptance.c` | Native mode gate, RGB555 progress observations, retained DMG behavior | VERIFIED | Substantive runner implementation; manual source trace and current receipt confirm connection. |
| `tests/scripts/verify-cgb-progress.py` | Source-bound CGB progress and negative controls | VERIFIED | Present, substantive, called by acceptance tests; current receipt binds its digest. |
| `tests/scripts/verify-cgb-candidates.py` | Fixed two-candidate ordering/admission/no-go validation | VERIFIED | Current exact-source pair checker passed. |
| `tests/scripts/verify-cgb-game-evidence.py` | Composed source-bound outcome and claim controls | VERIFIED | Present and registered; current receipt binds checker and source identities. |
| `tests/scripts/verify-scene-report.py` | Text intake and controlled promotion gate | VERIFIED | Present, substantive, connected to scene-report tests. |
| Two candidate JSON records | Ordered attempt dispositions | VERIFIED | Current candidate checker passes. Missing candidate manifests/cases are expected because neither rights gate passed. |
| Candidate ROMs/manifests/cases | Created only after rights/admission gates pass | NOT APPLICABLE | Neither candidate passed; no candidate ROM/source ran. |
| `21-UAT-EVIDENCE.md` | Current local qualification limits | VERIFIED | Explicitly separates local evidence from exact-head hosted status. |

The generic artifact checker flagged conditional candidate manifests/cases as absent and descriptive plan links as unresolved. Manual inspection confirms those candidate files are deliberately absent in the valid no-go branches. The generic key-link matcher also cannot resolve descriptive endpoints such as “original control source colours”; implementation and tests were inspected directly.

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `tests/acceptance/CMakeLists.txt` | `tests/scripts/verify-cgb-progress.py` | Real runner and immutable source | WIRED | CMake registers the checker against the runner. |
| `src/runner/acceptance.c` | loaded-ROM info and RGB555 capture API | Mode gate and bounded frame capture | WIRED | Manual source trace confirms loaded mode query and completed-frame capture. |
| `tests/scripts/verify-cgb-candidates.py` | `tests/scripts/verify-fixture-admission.py` | Phase 20 rights/admission validation | WIRED | Candidate admission delegates to the Phase 20 validator. |
| `tests/cmake/game-evidence.cmake` | `tests/scripts/verify-cgb-game-evidence.py` | Exact built runner and qualification receipt | WIRED | CMake supplies target path and source qualification. |
| `docs/scene-feedback.md` | Scene intake/promotion checker | Reproduction and promotion contract | WIRED | Documentation names the checker and evidence requirements. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|---|---|---|---|---|
| Harness receipt | ROM/progress/frame/PCM fields | Authored temporary ROM and actual runner callbacks | Yes, for harness only | FLOWING; not a game/accuracy oracle |
| Candidate result | Ordered attempts and blockers | Two source-bound candidate records | Yes, actual source/rights evidence | FLOWING; game build/ROM facts unobserved |
| Scene report | Intake/classification | User-supplied title/scene/symptom and later explicit evidence | No live report supplied | Contract-only; no live regression claimed |

### Behavioral Spot-Checks

| Behavior | Evidence | Result | Status |
|---|---|---|---|
| Full local suite | `21-UAT-EVIDENCE.md`, source `e0845db5841a1d56d8a297cbfaa3e0811af6ad67` | 1,717/1,718 passed in the full serial run; the single existing 90-second timeout `v02_source_archive_controls` passed isolated at 77.17 seconds. Every test has passing evidence across the full run plus that retry; no single full run was all-green. | PASS (combined evidence) |
| Candidate pair contract | `python3 -I tests/scripts/verify-cgb-candidates.py --check-all --require-final --repo-root . --source-revision e0845db5841a1d56d8a297cbfaa3e0811af6ad67` | Exit 0; two no-go records in order | PASS |
| Composed current receipt | `build/phase21-evidence/result.json` | Exact source and qualified runner; harness controls present | PASS (inspected) |
| Hosted exact-head checks | PR #140 | Required checks passed at exact implementation source `e0845db5841a1d56d8a297cbfaa3e0811af6ad67`; closeout artifact changes revision and must be requalified on its own PR head before merge. | PASS; final closeout SHA pending |

### Probe Execution

No phase-declared `probe-*.sh` files or explicit probe command was found. Existing CTest/checker evidence is cited above; no CTest was rerun.

### Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|---|---|---|---|---|
| GAME-01 | 21-01, 21-02, 21-07 | CGB RGB555/progress support on CGB-CPU-E and preserved DMG path | SATISFIED | Current source-qualified harness receipt, mode refusal, retained DMG policy and final local suite evidence. |
| GAME-02 | 21-01, 21-02, 21-03, 21-07, 21-08 | Bind ROM/profile/mode/input/predicate/observations and distinguish vacuous controls | SATISFIED for harness evidence | Receipt binds authored control inputs and observations; independent color expectations and negative controls are covered. Harness-only labeling is explicit. |
| FIXT-01 | 21-03, 21-04, 21-05, 21-07 | Bounded candidate search with exact source/build/ROM/header/native-mode evidence or reasoned absence | PASSED (override) | Owner accepted this phase-level deferral because both candidates stopped at source/rights gates. REQUIREMENTS.md remains Pending; no candidate build, ROM facts, rights grant, or admission is asserted. |
| FEED-01 | 21-06, 21-07 | Concise intake and controlled scene promotion with independent expectation, negative control and privacy boundaries | SATISFIED as workflow contract | Source-bound synthetic checks/documentation cover the contract; no real scene regression is asserted. |

No extra Phase 21 requirement mappings outside the plans were found.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---:|---|---|---|
| None in scanned implementation deliverables | — | No unreferenced TBD/FIXME/XXX markers or stub implementations found | INFO | No additional implementation blocker found. |

### Test Quality Audit

The source-bound receipt composes real runner execution with pinned checkers. Positive and negative harness routes are distinguished, observations bind to the same run, and changed/missing receipt facts have mutation controls. Scene promotion uses synthetic subjects and a causal negative control; tests do not claim real-game, hardware or accuracy evidence. Candidate records stop before execution at the rights gates.

### Human Verification Required

None. Exact-head hosted qualification passed at `e0845db`; the final closeout PR head still needs its required checks before merge. FIXT-01 remains Pending in `REQUIREMENTS.md` and requires further owner-selected source/rights evidence; this is not a manual UAT checkpoint.

### Gaps Summary

The phase delivers the native CGB harness, its controls, the bounded candidate outcome, and the automated scene-report workflow. The roadmap accepts reasoned absence when both candidates fail their gates; the no-go records plus harness-only result satisfy that outcome without implying game progress, admission or license permission. FIXT-01 is accepted as an intentional phase-level deferral, remains Pending in `REQUIREMENTS.md`, and has not been completed. Exact-head hosted/platform and installed-consumer checks passed at implementation source `e0845db5841a1d56d8a297cbfaa3e0811af6ad67`; the final closeout artifact revision needs its own exact-head qualification before merge.

---

_Verified: 2026-11-03T01:29:42Z_

_Verifier: the agent (gsd-verifier)_
