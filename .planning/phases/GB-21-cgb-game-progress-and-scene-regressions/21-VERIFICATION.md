---
phase: GB-21-cgb-game-progress-and-scene-regressions
verified: 2026-11-02T21:00:00Z
status: gaps_found
score: 4/5 roadmap success criteria verified
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
covered_digest: "v4:sha256:058f170c0cfe59a893eb1a76fb2514cbe802a3765a447fb025332519ce0b2286"
behavior_unverified: 0
overrides_applied: 0
gaps:
  - truth: "Final source has current acceptance, DMG baseline, state-continuation, fixture/product boundary and required hosted evidence before phase closure."
    status: failed
    reason: "Local qualification is present at ca17216b22d0d9f2fb742c8baed3e1543bc307e1, but PR #140 still points to an older SHA; required exact-head hosted/platform and installed-consumer checks are not established for this source."
    artifacts:
      - path: ".planning/phases/GB-21-cgb-game-progress-and-scene-regressions/21-UAT-EVIDENCE.md"
        issue: "Defers hosted qualification to PR #140 and does not claim current-head hosted results."
    missing:
      - "Push the final source/evidence commit, update PR #140 to that SHA, and verify required hosted/platform, fixture-reproduction, and installed-consumer checks for that exact head."
  - truth: "FIXT-01: each named candidate attempt verifies exact source/build, ROM digest, cartridge metadata, and native CGB mode, or records a bounded reasoned absence."
    status: partial
    reason: "The bounded pair and rights/source-scope no-go reasons are source-bound and no third search occurred. Both records stop before build and ROM acquisition, leaving build, ROM digest, cartridge header, and native mode not observed. REQUIREMENTS.md correctly leaves FIXT-01 pending."
    artifacts:
      - path: "tests/data/cgb-candidates/potion-panic.json"
        issue: "Creator-linked source could not be resolved; downstream build/ROM/mode facts are unobserved."
      - path: "tests/data/cgb-candidates/ucity-1.3.json"
        issue: "Source is pinned and a required hardware include lacks identified grant/notice; downstream build/ROM/mode facts are unobserved."
    missing:
      - "Further owner-selected source/rights evidence permitting exact candidate build and ROM identity/mode checks, or an explicit requirement disposition. Do not infer license prohibition from these no-go records."
---

# Phase 21: CGB Game Progress and Scene Regressions Verification Report

**Phase Goal:** Maintainers can obtain a reproducible CGB progress result from the shared runner, explain the bounded game-candidate outcome, and turn useful scene reports into controlled regressions.
**Verified:** 2026-11-02T21:00:00Z  
**Status:** gaps_found  
**Re-verification:** No

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | Shared runner observes native CGB RGB555 output and guest progress on CGB-CPU-E while preserving DMG acceptance. | VERIFIED | Current `build/phase21-evidence/result.json` binds source `ca17216b22d0d9f2fb742c8baed3e1543bc307e1`, qualified runner digest, native `cgb`, `CGB-CPU-E`, authored ROM/input digests, predicate, RGB555 and PCM observations. `src/runner/acceptance.c` queries loaded mode and captures RGB555; DMG policy remains on the existing acceptance path. |
| 2 | Positive input reaches the guest predicate; no-input, wrong-input, impossible-predicate and compatibility-mode controls reject vacuous progress. | VERIFIED | Current receipt records positive pass, three `predicate-not-reached` controls and compatibility refusal. `21-UAT-EVIDENCE.md` records the final local full CTest pass at this source. Result class is `original-harness-only`, not game progress. |
| 3 | Candidate search is ordered and bounded, with source-grounded actual outcomes and rights decisions. | VERIFIED WITH LIMIT | Current-source `verify-cgb-candidates.py --check-all --require-final` passed. Exactly Potion Panic then µCity 1.3 are recorded; the primary fetch failure and fallback's pinned source/include gap are explicit. No license prohibition is claimed and downstream facts are marked unobserved after rights cutoffs. The roadmap permits reasoned absence if neither clears its gate; this is not game admission, and FIXT-01 remains pending. |
| 4 | Text-only scene reports support agent-owned reproduction/classification and controlled promotion with privacy boundaries. | VERIFIED | `verify-scene-report.py`, `docs/scene-feedback.md`, CTest registration and composed receipt cover intake, synthetic promotion, independent expectation, causal negative control, optional owner play and personal-media exclusion. No live report or defect is claimed. |
| 5 | Current-source hosted/platform and installed-consumer qualification completes before phase closure. | FAILED | PR #140 still points to an older SHA, so hosted checks for this exact final source are not established. |

**Score:** 4/5 roadmap success criteria verified. The bounded no-go/harness-only result is acceptable for the roadmap's justified-absence outcome; it does not mark FIXT-01 complete.

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
| Full local suite | `21-UAT-EVIDENCE.md`, source `ca17216b22d0d9f2fb742c8baed3e1543bc307e1` | 1,718/1,718 passed serially; not rerun here | PASS (existing evidence) |
| Candidate pair contract | `python3 -I tests/scripts/verify-cgb-candidates.py --check-all --require-final --repo-root . --source-revision ca17216b22d0d9f2fb742c8baed3e1543bc307e1` | Exit 0; two no-go records in order | PASS |
| Composed current receipt | `build/phase21-evidence/result.json` | Exact source and qualified runner; harness controls present | PASS (inspected) |
| Hosted exact-head checks | PR #140 | PR SHA is older than source under verification | BLOCKED |

### Probe Execution

No phase-declared `probe-*.sh` files or explicit probe command was found. Existing CTest/checker evidence is cited above; no CTest was rerun.

### Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|---|---|---|---|---|
| GAME-01 | 21-01, 21-02, 21-07 | CGB RGB555/progress support on CGB-CPU-E and preserved DMG path | SATISFIED | Current source-qualified harness receipt, mode refusal, retained DMG policy and final local suite evidence. |
| GAME-02 | 21-01, 21-02, 21-03, 21-07, 21-08 | Bind ROM/profile/mode/input/predicate/observations and distinguish vacuous controls | SATISFIED for harness evidence | Receipt binds authored control inputs and observations; independent color expectations and negative controls are covered. Harness-only labeling is explicit. |
| FIXT-01 | 21-03, 21-04, 21-05, 21-07 | Bounded candidate search with exact source/build/ROM/header/native-mode evidence or reasoned absence | PARTIAL / PENDING | Ordered pair and actual rights blockers are verified, but neither build nor ROM/header/mode was observed. REQUIREMENTS.md leaves it unchecked. |
| FEED-01 | 21-06, 21-07 | Concise intake and controlled scene promotion with independent expectation, negative control and privacy boundaries | SATISFIED as workflow contract | Source-bound synthetic checks/documentation cover the contract; no real scene regression is asserted. |

No extra Phase 21 requirement mappings outside the plans were found.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---:|---|---|---|
| None in scanned implementation deliverables | — | No unreferenced TBD/FIXME/XXX markers or stub implementations found | INFO | No additional implementation blocker found. |

### Test Quality Audit

The source-bound receipt composes real runner execution with pinned checkers. Positive and negative harness routes are distinguished, observations bind to the same run, and changed/missing receipt facts have mutation controls. Scene promotion uses synthetic subjects and a causal negative control; tests do not claim real-game, hardware or accuracy evidence. Candidate records stop before execution at the rights gates.

### Human Verification Required

None. Remaining work is exact-head hosted qualification and further source/rights evidence for FIXT-01, not a perceptual or manual UAT checkpoint.

### Gaps Summary

The phase delivers the native CGB harness, its controls, the bounded candidate outcome, and the automated scene-report workflow. The roadmap accepts reasoned absence when both candidates fail their gates; the no-go records plus harness-only result satisfy that outcome without implying game progress or license prohibition. FIXT-01 remains pending because candidate build/ROM facts were not observed. Phase closure is blocked until hosted/platform and installed-consumer checks are green for the exact current PR head; PR #140 currently references an older SHA.

---

_Verified: 2026-11-02T21:00:00Z_  
_Verifier: the agent (gsd-verifier)_
