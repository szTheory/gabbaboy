---
phase: GB-20-fixture-admission-tune-up
verified: 2026-11-01T03:07:06Z
status: gaps_found
score: 6/9
covered_files:
  - .github/scripts/release-evidence-lifecycle.sh
  - .github/scripts/verify-workflow-policy.py
  - .github/workflows/ci.yml
  - .github/workflows/fixture-repro.yml
  - .github/workflows/preview.yml
  - .github/workflows/release.yml
  - .planning/phases/GB-20-fixture-admission-tune-up/20-01-PLAN.md
  - .planning/phases/GB-20-fixture-admission-tune-up/20-01-SUMMARY.md
  - .planning/phases/GB-20-fixture-admission-tune-up/20-02-PLAN.md
  - .planning/phases/GB-20-fixture-admission-tune-up/20-02-SUMMARY.md
  - .planning/phases/GB-20-fixture-admission-tune-up/20-03-PLAN.md
  - .planning/phases/GB-20-fixture-admission-tune-up/20-03-SUMMARY.md
  - .planning/phases/GB-20-fixture-admission-tune-up/20-04-PLAN.md
  - .planning/phases/GB-20-fixture-admission-tune-up/20-04-SUMMARY.md
  - .planning/phases/GB-20-fixture-admission-tune-up/20-REVIEW-FIX.md
  - .planning/phases/GB-20-fixture-admission-tune-up/20-REVIEW.md
  - .planning/phases/GB-20-fixture-admission-tune-up/20-SECURITY.md
  - .planning/phases/GB-20-fixture-admission-tune-up/20-VALIDATION.md
  - CMakeLists.txt
  - THIRD_PARTY_NOTICES.md
  - build/Testing/Temporary/LastTest.log
  - build/Testing/Temporary/LastTestsFailed.log
  - cmake/FixtureAdmissionPolicy.json
  - cmake/PreviewPackageSmoke.cmake
  - cmake/VerifyInstalledPackage.cmake
  - docs/fixture-admission.md
  - tests/CMakeLists.txt
  - tests/data/workflow-policy-controls.json
  - tests/expected-tests.txt
  - tests/scripts/test_player_package_policy.py
  - tests/scripts/verify-fixture-admission.py
  - tests/scripts/verify-phase3-player.sh
  - tests/scripts/verify-release-candidate.sh
  - tests/scripts/verify-v02-source-archive.py
  - tests/scripts/verify-workflow-policy-coverage.py
covered_digest: "v4:sha256:94000c36b16480f0fa0e2bf1326fbaa2f873173160721117638e13f9debdf463"
behavior_unverified: 0
overrides_applied: 0
gaps:
  - truth: "Repository and public-CI admission cannot be redirected around the fixture gate."
    status: failed
    reason: "CR-09: the workflow policy matcher accepts command prefixes and extra assignments/options. A PATH override can select an untrusted Python, and a later --repo-root can redirect validation to a controlled tree."
    artifacts:
      - path: .github/scripts/verify-workflow-policy.py
        issue: "_fixture_call delegates to require_call with non-exact matching for the CI and fixture-reproduction admission commands (approximately lines 852-877 and 1760-1818)."
      - path: build/Testing/Temporary/LastTest.log
        issue: "workflow_policy_group_ci failed because its mutation subject lacked tests/scripts/verify-release-candidate.sh; the final review also found no negative control for the PATH and duplicate --repo-root redirects."
    missing:
      - "Require exact command words and assignments, including exactly one --repo-root ., and add both redirect mutations."
  - truth: "The product allowlist is independently pinned before it can authorize fixture bytes or destinations."
    status: failed
    reason: "CR-08: _product_rules reads the current FixtureAdmissionPolicy.json and validates its shape and baseline, but does not bind the product-policy bytes to an immutable reviewed identity. A policy edit can add a repository-only ROM and destination that the same policy then approves."
    artifacts:
      - path: tests/scripts/verify-fixture-admission.py
        issue: "The policy is loaded and used to populate allowed fixture sources and product destinations without checking its full-file digest (approximately lines 847-875, 922-983, and 1042-1074)."
      - path: cmake/FixtureAdmissionPolicy.json
        issue: "The mutable products map supplies the allowed source paths and destinations."
    missing:
      - "Pin the full policy bytes to an independently reviewed identity or read them from a trusted immutable checkout."
      - "Add a negative control that adds a forbidden baseline fixture and destination to a candidate policy."
  - truth: "Core and player release packages are rechecked by trusted release code on every platform before publication."
    status: failed
    reason: "CR-05: macOS and Windows jobs copy verifiers from the workflow commit before running tagged build code, then check products with files and policy from that tagged workspace. The trusted publisher rechecks the Linux archive but does not re-extract and validate the macOS and Windows product layouts before draft validation."
    artifacts:
      - path: .github/workflows/release.yml
        issue: "macOS and Windows package checks use a checker copied to RUNNER_TEMP and pass --repo-root . after tagged source build steps (reviewed ranges 728-737, 781-792, 850-861, 922-928, 968-979, and 1041-1051)."
      - path: .github/scripts/release-evidence-lifecycle.sh
        issue: "Trusted draft validation hashes and inventories platform assets but does not independently validate the downloaded macOS and Windows package contents (reviewed lines 224-293)."
    missing:
      - "Download and safely extract macOS and Windows candidate archives in the trusted publisher job, then check them with the trusted checkout's verifier and policy before draft validation."
  - truth: "The final Phase 20 full CTest validation is green."
    status: partial
    reason: "The final-head log records 20 failures out of 1,711 tests. Several failures are checkout or sandbox limitations, while others are repository/test-contract failures; the suite cannot be represented as passing."
    artifacts:
      - path: build/Testing/Temporary/LastTestsFailed.log
        issue: "Lists the 20 failing test names; build/Testing/Temporary/LastTest.log records each command and failure output."
    missing:
      - "Resolve the phase-relevant workflow_policy_group_ci failure and obtain an owner-authorized disposition for the other full-suite failures before closing the phase."
---

# Phase 20: Fixture Admission Tune-up Verification Report

**Phase Goal:** Maintainers can admit permitted evidence through one checked fixture and distribution boundary before new game or diagnostic bytes enter public automation.
**Verified:** 2026-11-01T03:07:06Z
**Status:** gaps_found
**Re-verification:** No

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | Complete fixture records and changed identities are checked before repository and public-CI use; historical approvals remain intact. | FAILED | The real CLI, repository, and identity controls pass, but CR-09 shows the workflow-policy checker accepts redirected CI/reproduction admission commands. The phase's `workflow_policy_group_ci` CTest also failed in its mutation harness. |
| 2 | Product paths map only to independently pinned fixture and notice bytes, with the source archive governed separately. | FAILED | The source archive remains a separate path, but CR-08 confirms the current product map is loaded from an unpinned mutable JSON file and can authorize a new fixture source and destination. |
| 3 | Tooling records identities and rights fields without presenting them as legal clearance; no new fixture is admitted by this tune-up. | VERIFIED | `docs/fixture-admission.md` states that automation cannot decide legal grant scope. The recorded `fixture_admission_repository` CTest passed with its required `admitted_changes=0` result. RIGHTS-01 remains pending. |
| 4 | Installed and release packages reject controlled ROM insertions while valid core/player packages retain fixture notices and GabbaBoy's MIT declaration. | FAILED | The local `preview_package_smoke` passed and the focused core/player mutation tests passed. However, CR-08 leaves the allowlist mutable, and CR-05 shows final macOS/Windows package checks use tagged-workspace code while the trusted publisher only rechecks Linux. |
| 5 | Direct manifest and repository fixture walks reject more than the fixed entry limit. | VERIFIED | The `fixture_admission_controls` and `fixture_admission_repository` CTests passed at the final code revision; the Plan 20-04 self-test includes content-caused directory-entry overflow controls. |
| 6 | Git fixture-tree enumeration limits bytes and records while streaming and terminates/reaps an over-limit child. | VERIFIED | The final `fixture_admission_controls` CTest passed. Plan 20-04's focused controls cover stdout and record limits plus fake-process cleanup; the full CTest log confirms this named test passed. |
| 7 | Stable rejection tokens distinguish filesystem entry overflow, Git entry overflow, and Git output-byte overflow. | VERIFIED | The source defines separate rejection tokens and the recorded `fixture_admission_controls` self-test passed with the content-caused overflow cases. |
| 8 | Existing fixture identities, package policy, notices, and admission decisions continue to pass their Phase 20 controls. | VERIFIED | At the exact `ee4fd369d5e318c9d416534f92aeee0d45ecd2e5` test revision, `fixture_admission_controls`, `fixture_admission_repository`, `fixture_product_core_controls`, `fixture_product_player_controls`, and `preview_package_smoke` passed. This does not override the separate product-policy and release-trust gaps above. |
| 9 | Git blob reads stop at the configured limit while consuming output and clean up the child on overflow or timeout. | VERIFIED | At current HEAD, `blob()` reads in chunks to `MAX_FILE_BYTES + 1`, rejects overflow, and terminates/reaps the child. `fixture_admission_controls` passed and includes a bounded-read and process-cleanup negative control. |

**Score:** 6/9 truths verified (0 present, behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `tests/scripts/verify-fixture-admission.py` | Admission, repository, and product-byte checker with negative controls | PARTIAL | Substantive and wired to CMake/workflows; product policy lacks an independent identity pin (CR-08). Current Git blob reads are bounded while consuming output. |
| `cmake/FixtureAdmissionPolicy.json` | Exact product source/destination policy | FAILED | Present and consumed, but CR-08 shows its `products` map can be changed without an independently pinned policy digest. |
| `docs/fixture-admission.md` | Admission contract, limits, and legal-scope boundary | VERIFIED | Documents structural checks and explicitly disclaims automated legal clearance. |
| `cmake/VerifyInstalledPackage.cmake` | Validate installed core bytes through shared policy | VERIFIED | Present and calls the shared checker for the actual installed prefix. |
| `cmake/PreviewPackageSmoke.cmake` | Check installed and extracted archive bytes before consumers | VERIFIED | Present and wired; final CTest `preview_package_smoke` passed, including its renamed CGB fixture rejection. |
| `tests/scripts/verify-v02-source-archive.py` | Keep source archives separate and check actual product archive entries | VERIFIED | Present and used by release-candidate verification; source archive policy remains distinct. |
| `.github/workflows/release.yml` | Enforce core/player product policy at producers and release consumers | PARTIAL | Wiring is present, but CR-05 finds macOS/Windows checks trust mutable tagged-workspace files; CR-08 finds the policy itself is not pinned. |
| `tests/scripts/verify-phase3-player.sh` | Check player stage/extract bytes and mutation controls before execution | PARTIAL | Present and wired; portable product controls passed. The validation record says full hosted macOS package qualification is still pending. |
| `.github/scripts/verify-workflow-policy.py` | Reject workflow changes that remove or redirect admission gates | FAILED | Present and wired, but CR-09 confirms fixture admission calls use permissive prefix/subset matching. |

No phase artifact is missing or a placeholder. The failures are trust-boundary gaps in substantive, connected implementations.

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `tests/scripts/verify-fixture-admission.py` | `cmake/FixtureAdmissionPolicy.json` | Reads baseline and product mappings | PARTIAL | The references are wired; product mappings are not independently pinned (CR-08). |
| `CMakeLists.txt` | `tests/scripts/verify-fixture-admission.py` | Configure gate before fixture consumers | WIRED | The configure gate calls the checker; the final repository-admission CTest passed. |
| `.github/workflows/fixture-repro.yml` | `tests/scripts/verify-fixture-admission.py` | Gate before fixture tools/downloads | PARTIAL | The call is present, but the workflow checker accepts redirected command forms (CR-09). |
| `cmake/VerifyInstalledPackage.cmake` | `tests/scripts/verify-fixture-admission.py` | Installed-prefix actual-byte check | WIRED | The checker is called with explicit product layout and root. |
| `cmake/PreviewPackageSmoke.cmake` | `cmake/VerifyInstalledPackage.cmake` | Installed and extracted package validation | WIRED | Both installed and extracted layouts are checked before consumer smoke. |
| `tests/scripts/verify-release-candidate.sh` | `tests/scripts/verify-v02-source-archive.py` | Existing release/archive verification dispatch | WIRED | The shared source/product archive policy is invoked. |
| `.github/workflows/release.yml` | trusted publisher product checks | Downloaded archive validation | PARTIAL | Linux is rechecked in the trusted publisher; macOS and Windows final package contents are not. |
| `tests/scripts/verify-phase3-player.sh` | `tests/scripts/verify-fixture-admission.py` | Validate staged/extracted player before execution | WIRED | The shared checker is called; final package qualification is still pending and the policy identity is weak. |
| `check_manifest()` | `current_fixture_files()` | Count fixture entries before inventory/traversal | WIRED | `verify.key-links` could not resolve function names as file paths; source inspection confirms the call path and the CTest controls pass. |
| `check_repository()` | `current_fixture_files()` and `tree_files()` | Apply filesystem and Git enumeration bounds | WIRED | Manually confirmed in the checker; the query's source-path restriction prevented automated link resolution. |
| `fixture_admission_controls` CTest | `--self-test` | Exercises direct-manifest and tree-limit controls | WIRED | Registered in `tests/CMakeLists.txt`; final CTest record is PASS. |

### Data-Flow Trace (Level 4)

Not applicable. The verified artifacts are command-line checkers, policy/configuration files, and build/package scripts; they do not render dynamic user-facing data.

### Behavioral Spot-Checks

These results come from the full CTest run at `ee4fd369d5e318c9d416534f92aeee0d45ecd2e5`. Afterward, five Git-worktree-dependent failures were rerun with `.git/worktrees` write access and passed; `acceptance_dense_input_controls` was rerun with the same access and still failed.

| Behavior | Recorded command/test | Result | Status |
|---|---|---|---|
| Admission, identity, and bounded-input negative controls | `fixture_admission_controls` | Passed, 22.54 s | PASS |
| Existing repository fixtures remain admitted without changes | `fixture_admission_repository` | Passed, 3.49 s | PASS |
| Core and player policy mutation controls | `fixture_product_core_controls`, `fixture_product_player_controls` | Both passed | PASS |
| Installed core archive, extraction, and external C/C++ consumer smoke | `preview_package_smoke` | Passed, 40.17 s; renamed CGB fixture was rejected | PASS |
| Release-job workflow controls | `workflow_policy_group_release_jobs` | Passed, 39.30 s | PASS |
| CI workflow policy mutation controls | `workflow_policy_group_ci` | Failed: temporary mutation subject lacked `tests/scripts/verify-release-candidate.sh` | FAIL |
| Workflow policy coverage and its mutation controls | `workflow_policy_coverage`, `workflow_policy_coverage_controls` | Both passed; controls reported 72 | PASS |
| Git-worktree-dependent controls | `v02_performance_controls`, `v02_delivery_controls`, `perf_advisory_pipeline`, `perf_advisory_controls`, `release_review_approval` | All five passed on a targeted rerun with Git metadata write access; the full-suite sandbox run had denied `.git/worktrees` creation | PASS (targeted rerun) |
| Dense-input mutant checkout | `acceptance_dense_input_controls` | Still failed on targeted rerun with Git metadata access: source-only checkout cannot resolve the pinned baseline object | FAIL |

### Full CTest Evidence

The captured full run at the exact code revision ran 1,711 tests and reported 20 failures. Later targeted reruns replaced CTest's live `LastTest.log`; the grouped full-run results are preserved here and in `20-VALIDATION.md`. The full run is not green. The failures group as follows:

| Failure group | Tests | Recorded cause |
|---|---|---|
| Existing adoption/disclosure/support checks | `v02_adoption_docs`, `v02_adoption_docs_controls`, `v02_support_ledger_controls`, `release_disclosure_generator`, `release_disclosure_controls`, `support_claims_controls` | `product-package-distinction-missing:THIRD_PARTY_NOTICES.md` |
| Git history/worktree restrictions | `v02_performance_controls`, `v02_delivery_controls`, `perf_advisory_pipeline`, `perf_advisory_controls`, `release_review_approval` | The full-suite sandbox denied worktree writes; all five passed when rerun with `.git/worktrees` write access. |
| Baseline object unavailable | `acceptance_dense_input_controls` | Still fails with Git metadata access: the source-only mutant checkout cannot resolve the pinned baseline object during configure. |
| Workflow policy test subject setup | `workflow_policy_group_ci`, `workflow_policy_group_release_support`, `workflow_policy_group_rehearsal`, `workflow_policy_group_ledger`, `workflow_policy_group_helpers` | The mutation subject lacked `tests/scripts/verify-release-candidate.sh`. |
| Existing install contract | `installed_runner_smoke` | The installed tree contained unlisted `lib/cmake/GabbaBoy/GabbaBoyTargets-debug.cmake`. |
| CTest budget contract | `test_budget` | `fixture_product_core_controls` and `fixture_product_player_controls` each have 120-second timeouts without allowlist rows. |
| Planning hygiene | `plan_cap` | Phases 22 and 23 have no `**Plan cap**: N` line. |

Some failures are sandbox/environment or existing-repository contract failures rather than direct Phase 20 product-check failures. They still prevent a clean full-suite sign-off. The failed `workflow_policy_group_ci` is directly relevant to the admission-gate test path.

### Probe Execution

No Phase 20 plan or summary declares a probe path. No probe under the prescribed `scripts/*/tests/probe-*.sh` location was found. The repository's `tests/scripts/probe-mooneye-candidate.sh` is not declared by this phase and was not run.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| RIGHTS-01 | 20-01 through 20-04 | Verify redistribution permission and per-component terms for an admitted fixture; exclude ROMs from product packages and retain root MIT. | BLOCKED / pending | The boundary checks structure and identity but cannot decide a grant's legal scope; no candidate was admitted. CR-05, CR-08, and CR-09 also leave the technical gate incomplete. The requirement remains pending; there are no orphaned Phase 20 requirement IDs. |

### Test Quality Audit

No disabled-test markers were found in the Phase 20-linked test files. The admission and package self-tests use synthetic repositories/trees and explicit negative assertions; the checker also binds baseline bytes to immutable Git blobs rather than generating expected values from the behavior under test. The Phase 20 CI workflow mutation group did not pass in the recorded full run because its temporary subject omitted a required script, so that group's controls are not accepted as complete evidence.

### Decision Coverage

All 3 trackable decisions in `20-CONTEXT.md` are honored by shipped artifacts. The decision-coverage check is non-blocking.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---:|---|---|---|
| — | — | No unreferenced `TBD`, `FIXME`, or `XXX` markers; no placeholder implementation found in Phase 20 key files. | — | — |

The grep-only `return []` matches are empty collection/error-result helpers, not user-visible stubs. The one empty-return source string in the workflow-coverage checker is a deliberate mutation used to prove checker rejection.

### Human Verification Required

None. Phase 20 explicitly has no manual UAT, and this report uses the existing automated evidence. RIGHTS-01 remains pending because legal grant scope is outside automated verification; the phase did not admit a candidate or claim clearance.

### Gaps Summary

The final review reports three blockers: CR-05 (untrusted tagged-workspace checks for macOS/Windows products), CR-08 (unpinned mutable product allowlist), and CR-09 (workflow command redirection accepted). `20-SECURITY.md` now confirms the authored threat registers are closed at current HEAD `ee4fd369`; T-20-04 is resolved by bounded streaming and timeout controls. The five Git-worktree failures were isolated to the sandbox and passed on targeted rerun, but the dense-input test and other full-suite contracts remain failing. The focused fixture/package controls pass, while the CI workflow policy group itself fails.

No later milestone phase clearly closes these gaps; they are not deferred. The single planned gap-closure plan and the second review-fix iteration are already consumed. The next step is an owner-authorized rescope before Phase 20 can close; Phase 21 must not start from this verification result.

---

_Verified: 2026-11-01T03:07:06Z_  
_Verifier: the agent (gsd-verifier)_
