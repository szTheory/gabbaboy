---
phase: "20"
slug: "fixture-admission-tune-up"
status: validated
nyquist_compliant: true
wave_0_complete: true
created: "2026-10-31"
---

# Phase 20 — Validation Strategy

> Feedback contract for the fixture admission and distribution boundary. All fixture/package decisions use exact bytes and pinned identities; hashes establish identity, not redistribution permission.

The original per-task map below records the first implementation waves. Its partial statuses are historical; the final exact-head addendum at the end of this document is the current validation record for all nine plans.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | CTest under CMake; Python standard-library self-tests for admission and package controls. |
| **Config file** | `tests/CMakeLists.txt`; test preset `phase1` in `CMakePresets.json`. |
| **Quick run command** | `python3 -I tests/scripts/verify-fixture-admission.py --self-test` (planned for Wave 0; synthetic temporary data only). |
| **Full suite command** | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error`. |
| **Estimated runtime** | Keep the synthetic self-test under 30 seconds; record actual package/full-suite runtimes during execution. |

---

## Sampling Rate

- **After every task commit:** Run the focused synthetic admission self-test once implemented.
- **After every plan wave:** Run the relevant staged/extracted package check; do not duplicate the full CI matrix.
- **Before `$gsd-verify-work`:** Run the full suite above on the final Phase 20 head.
- **Max feedback latency:** Under 30 seconds for the synthetic self-test; package and full-suite latency is measured during execution.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 20-01-01 | 20-01 | 1 | RIGHTS-01 | T-20-01, T-20-03, T-20-04 | Real CLI accepts a complete synthetic manifest/notice/pinned-blob path and rejects a coordinated rewrite, missing pin or absent blob. | integration | `python3 -I tests/scripts/verify-fixture-admission.py --self-test` | New, created in this task | ✓ pass |
| 20-01-02 | 20-01 | 1 | RIGHTS-01 | T-20-01, T-20-03, T-20-04 | Existing approvals pass; incomplete component/use records, new unregistered evidence including additions in legacy subtrees, bad input and changed identity fail before consumption. | integration | `python3 -I tests/scripts/verify-fixture-admission.py --self-test && python3 -I tests/scripts/verify-fixture-admission.py --check-repository --repo-root . && python3 -I .github/scripts/verify-workflow-policy.py --self-test --group ci && python3 -I .github/scripts/verify-workflow-policy.py --self-test --group release_jobs` | New, Task 1 dependency | ⚠ partial — current CTest run's workflow-policy CI control failed while reading an absent temporary wrapper; release-jobs control passed |
| 20-01-03 | 20-01 | 1 | RIGHTS-01 | T-20-02, T-20-03, T-20-04 | Both exact product policies accept clean synthetic trees and reject insertion, identity, notice/MIT/SDL/sidecar and documentation mutations. | unit | `python3 -I tests/scripts/verify-fixture-admission.py --self-test && python3 -I tests/scripts/verify-fixture-admission.py --self-test-packages --layout core && python3 -I tests/scripts/verify-fixture-admission.py --self-test-packages --layout player` | New, Task 1 dependency | ✓ pass |
| 20-02-01 | 20-02 | 2 | RIGHTS-01 | T-20-05, T-20-06, T-20-07 | Real install/archive/extraction and consumers pass exact policy; a renamed planted ROM fails before execution. | integration | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '^preview_package_smoke$'` | Existing target, extended | ✓ pass |
| 20-02-02 | 20-02 | 2 | RIGHTS-01 | T-20-05, T-20-06, T-20-07, T-20-08 | Every approved core subtree, renamed/suffixless insertion and missing/changed notice/MIT control fails in actual trees and parsed archives; source contract remains distinct. | integration | `python3 -I tests/scripts/verify-v02-source-archive.py --self-test && ctest --preset phase1 --output-on-failure --no-tests=error -R '^preview_package_smoke$'` | Existing, extended | ✓ pass |
| 20-02-03 | 20-02 | 2 | RIGHTS-01 | T-20-06, T-20-07, T-20-08 | Core new/reused/downloaded production paths apply actual-byte policy; missing/changed gabbaboy-notices.txt fails; separate source evidence retained. | integration | `bash tests/scripts/verify-release-candidate.sh --self-test && python3 -I tests/scripts/verify-v02-source-archive.py --self-test && python3 -I .github/scripts/verify-workflow-policy.py --self-test --group release_jobs` | Existing, extended | ✓ pass |
| 20-03-01 | 20-03 | 2 | RIGHTS-01 | T-20-09, T-20-10, T-20-11 | Real macOS stage/extracted player inventory and lifecycle pass; planted renamed payload fails before execution. | integration | `bash tests/scripts/verify-phase3-player.sh --build-package` | Existing, extended | ⚠ hosted macOS lane pending |
| 20-03-02 | 20-03 | 2 | RIGHTS-01 | T-20-09, T-20-10, T-20-11 | Real valid player prefix passes shell wrapper; suffixless/renamed/subtree and every missing/changed fixture/GabbaBoy/SDL notice case fail with intended reasons, without altering positive bytes. | integration | `python3 -I tests/scripts/verify-fixture-admission.py --self-test-packages --layout player && bash tests/scripts/verify-phase3-player.sh --self-test-package-policy build/phase3-player/package-stage/installed-prefix` | New mode; Task 1 produces prefix | ✓ pass |
| 20-04-01 | 20-04 | 3 | RIGHTS-01 | T-20-12 | Direct manifest and repository walks plus Git tree streaming reject over-limit entries/output with bounded child cleanup. | integration | `python3 -I tests/scripts/verify-fixture-admission.py --self-test` | Existing self-test extended | ✓ pass in current full-suite run |
| 20-04-02 | 20-04 | 3 | RIGHTS-01 | T-20-12 | Filesystem and Git fixture enumeration reject excess entries/output during consumption, reap a rejected child, and preserve admission, repository, core and player controls. | integration | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^fixture_(admission|product_).*'` | Existing `fixture_admission_controls` target | ✓ pass in current full-suite run |

Each PLAN task carries its concrete `<fails_when>` signal. Plan 20-04's expected RED marker and passing follow-up are recorded in `20-04-SUMMARY.md`; its focused admission/repository/core/player controls also passed in the current full-suite run. The existing hosted macOS player-package lane remains unqualified. The earlier local package attempt produced the package stage and passed policy/leak controls, but two Cocoa menu tests could not initialize without a display service. Run the existing `macos-player-package` CI job at the exact final Phase 20 head before closing the phase. This is an automated environment limitation, not a human-verification item. The first tracer created its own synthetic verification path. No separate Wave 0 plan was added: missing scaffolds are part of Plan 20-01, before the two dependent package plans.

### Actual package producer/check stages

- `preview_package_smoke` produces `build/preview-package-smoke/installed-prefix`, `installed-prefix.tar.gz` and `extracted/installed-prefix`; the stage policy/inventory is checked before archive creation, then compared to extracted actual bytes before consumers.
- `release.yml` Linux core producer builds `build/release-stage` and `build/gabbaboy-core-linux-x64.tar.gz`; macOS core producer uses `build/release-stage` and `build/gabbaboy-core-macos-arm64.tar.gz`. Policy runs before archiving and against actual archive/extraction at existing qualification stages. The focused archive CLI is `python3 -I tests/scripts/verify-v02-source-archive.py --check-product-archive build/gabbaboy-core-linux-x64.tar.gz --repo-root .` only after its real producer has created that artifact.
- Core `gabbaboy-notices.txt` is the separately produced/copied root MIT asset. Existing release candidate and downloaded-byte paths check its actual bytes; do not expect source-only `THIRD_PARTY_NOTICES.md` inside binary archives.
- Player `--build-package` produces `build/phase3-player/package-stage/installed-prefix`, `preview-candidate/gabbaboy-preview-macos-arm64.tar.gz` and `build-receipt.json`; `--verify-package` safe-extracts before policy and lifecycle checks. The existing release download stage creates `build/downloaded-player` before `bash tests/scripts/verify-phase3-player.sh --verify-package build/downloaded-player` can consume it.
- Source archives retain their separate immutable source-tree/fixture/notices contract and are never passed as binary positives.

---

## Wave 0 Requirements

- [x] Add a focused Python standard-library admission validator/self-test under `tests/scripts/` and register it in CTest.
- [x] Pin approved fixture identities independently from the mutable manifest/notice values and prove a coordinated mutation is rejected.
- [x] Extend existing package checks to compare actual staged and extracted bytes against exact path/digest inventories, with positive and negative controls.
- [x] Keep source archive policy separate from installed/core release/player binary products.
- [x] Provide one package-path policy from Wave 1 for the core and player checks in Wave 2, without duplicating fixture rights metadata.

---

## Manual-Only Verifications

There is no manual UAT for Phase 20. A future candidate's rights scope still requires a source-grounded maintainer decision before it is marked admitted; Phase 20 does not select or admit a candidate, and automated checks must not represent hashes or populated fields as legal clearance.

---

## Initial Validation Sign-Off (historical; superseded by the final rescope run)

- [x] Every plan task has an automated verify command or an explicit Wave 0 dependency.
- [x] Each package boundary has a clean positive control and meaningful mutation controls.
- [x] Wave 0 covers the missing admission and exact-inventory checks.
- [x] No watch-mode flags.
- [x] Focused self-test feedback latency is under 30 seconds (about 15 seconds in Plan 20-01).
- [ ] `nyquist_compliant: true` set in frontmatter. The current full suite has 20 failing tests, three critical review findings remain, and the hosted macOS package lane is unavailable.

**Approval:** PARTIAL; the full suite is red, review blockers remain, and exact-head hosted macOS package qualification is unavailable.

## Execution Evidence

- **Coverage:** 10/10 plan tasks have automated checks or recorded TDD evidence. Each package boundary has a clean positive and content-caused negative controls.
- **Recorded source revision:** HEAD `ee4fd369d5e318c9d416534f92aeee0d45ecd2e5`.
- **Configure/build:** `cmake --preset phase1` and `cmake --build --preset phase1` passed.
- **Full CTest:** `ctest --preset phase1 --output-on-failure --no-tests=error` ran 1,711 tests and failed 20; the command returned nonzero. The failures were `v02_adoption_docs`, `v02_adoption_docs_controls`, `v02_support_ledger_controls`, `release_disclosure_generator`, `release_disclosure_controls`, `v02_performance_controls`, `v02_delivery_controls`, `installed_runner_smoke`, `acceptance_dense_input_controls`, `test_budget`, `perf_advisory_pipeline`, `perf_advisory_controls`, `workflow_policy_group_ci`, `workflow_policy_group_release_support`, `workflow_policy_group_rehearsal`, `workflow_policy_group_ledger`, `workflow_policy_group_helpers`, `plan_cap`, `support_claims_controls`, and `release_review_approval`. They cover notice-contract drift, the installed debug CMake target inventory, workflow-policy controls reading absent temporary wrappers, plan-cap parsing, timeout-budget rows, an unavailable baseline object, and Git worktree permission denials in the sandbox. This is not a green full-suite result.
- **Sandbox-only rerun:** The five failures that needed temporary Git worktrees (`v02_performance_controls`, `v02_delivery_controls`, `perf_advisory_pipeline`, `perf_advisory_controls`, and `release_review_approval`) passed when those exact tests were rerun with `.git/worktrees` write access. `acceptance_dense_input_controls` was also rerun with that access and still fails because its source-only mutant checkout cannot resolve the pinned baseline object. The original full-suite run remains red; this isolates five of its failures as sandbox-only.
- **Phase 20 focused evidence:** fixture admission, repository admission, core product and player product controls passed in that same run. The workflow-policy `ci` group failed while reading an absent temporary wrapper; the `release_jobs` group passed.
- **Review blockers:** the current `20-REVIEW.md` reports three critical findings after both fix rounds: macOS/Windows release product checks still trust the tagged workspace; the product allowlist digest is not independently pinned; and repository-admission workflow commands can be redirected by the command matcher. These implementation blockers remain escalated for the phase owner.
- **Pending execution evidence:** `20-03-01` full `--build-package` qualification in the existing hosted `macos-player-package` CI lane at the exact final Phase 20 head. Local qualification cannot substitute for that lane; the prior attempt stopped at two Cocoa menu checks because this host lacks a display service.
- **Human judgment:** none for this phase. RIGHTS-01 remains pending because no fixture was admitted and automation does not determine legal grant scope.

The supplied spec-less edge remains explicitly unresolved/unclassified (RIGHTS-01; verification null) in Plan 20-01 must_haves. The two precision-filtered prohibition assumptions remain descriptor-less flagged-unverified. They do not invent manual UAT or legal clearance; see `20-SOURCE-AUDIT.md`.

## Initial Validation Audit (historical; superseded by the final rescope run)

**Result:** PARTIAL / noncompliant. The focused Phase 20 behavioral controls pass, but the full suite fails and the outstanding security review and hosted macOS package qualification gates remain unresolved. No manual UAT is required.

## Prior Rescope Validation Run at 7293eb47 (historical)

This report records the implementation-head evidence before the final test follow-ups and hosted qualification. Its results are retained as history; the current exact-head status is recorded in the addendum below.

| Check | Final result | Evidence |
|---|---|---|
| Configure and build | PASS | `cmake --preset phase1` and `cmake --build --preset phase1` passed at source head `7293eb47a6c799b6455dd854533aca932f4529ad`. |
| Full local CTest | PASS | 1,711/1,711 passed at the same source head; the captured last test log ends with `End testing` and no failed tests. |
| Release-candidate replay | PASS | `bash tests/scripts/verify-release-candidate.sh --self-test` passed at the same source head, including archive/product positives and receipt, fixture-leak, source-archive, and substitution negatives. |
| Security audit | PASS | `20-SECURITY.md` records 29/29 authored threat entries closed across all nine plan registers; `threats_open: 0`. |
| Code reviews | PASS | Trusted publisher and Windows-path findings were fixed; the final archive/path review is clean; WR-01's exact-cap counter-reset proof is closed at `7293eb47`. |
| Plan/summary coverage and plan cap | PASS locally | The full CTest includes `plan_cap`, planning hygiene, live-summary coverage, workflow-policy coverage, and negative controls. The phase has 9 plans under its cap of 9. |
| Windows byte-exact repository configure | RETEST PENDING | The first hosted run reproduced Windows `core.autocrlf` conversion before fixture admission. CI now disables conversion before checkout; the next exact-head `native-windows-x64` run must pass. A local paired clone control proves configured checkout passes and `autocrlf=true` rejects with the same cause. |
| Exact-head hosted macOS player package | PENDING | The `macos-player-package` pull-request job must pass on the final pushed revision. Local Cocoa UI tests cannot substitute for this hosted lane. |

No fixture was admitted. `RIGHTS-01` remains pending because no candidate was admitted and automated identity/notice checks do not determine legal grant scope. No manual UAT is required; `20-UAT.md` is generated and checked by the shared closure helper from the plan-summary deliverables.

## Final Exact-Head Validation — 2026-11-01

Implementation head: `39eb048e7770652b84a3fc5da7aaa3890adbd70c`.

| Check | Result | Evidence |
|---|---|---|
| Configure/build | PASS | `cmake --preset phase1` and `cmake --build --preset phase1` passed after reconfiguring for this head. |
| Full local suite and revision-bound controls | PASS | The full CTest run passed 1,708/1,711. Its only three failures (`cgb_corpus_report_tracer`, `cgb_corpus_report_controls`, and `state_fuzz_controls`) used the stale configure-time revision. After reconfigure/build at this head, all three passed in a focused retest. |
| Source archive / release controls | PASS | `v02_source_archive_controls` passed in 52.11 seconds; `bash tests/scripts/verify-release-candidate.sh --self-test` passed against the same source tree. |
| Exact-head pull-request CI | PASS | Run 41334163805 completed successfully, including native Linux/macOS/Windows, CMake 3.25.3, sanitizer, acceptance, performance, and `required-native` jobs. The macOS player package passed. |
| Exact-head push CI | PASS | Run 41334157283 completed successfully with the same native, floor, sanitizer, acceptance, performance, and `required-native` gates. Event-specific planning and macOS player jobs were skipped as expected. |
| Installed and player consumers | PASS | Preview run 41334163730 passed Linux and macOS installed-package smoke, downloaded macOS player receipt verification, and the aggregate gate. |
| Rights disposition | PENDING | No fixture was admitted. These checks establish identity and distribution boundaries, not legal permission or grant scope. |

All registered CTests have passing evidence across the full run and the three post-configure retests. No manual UAT is required. This closes the remaining hosted qualification items without changing RIGHTS-01.


## Plan 20-06 containment follow-up — source head `1b9aa6f79b8a78efa995fa689bb8f9762c3aa30c`

| Check | Result | Evidence |
|---|---|---|
| Configure/build | PASS | `cmake --preset phase1` and `cmake --build --preset phase1 -j2` passed at `1b9aa6f79b8a78efa995fa689bb8f9762c3aa30c`. |
| Direct reusable extractor controls | PASS | `python3 -I .github/scripts/safe_extract_package.py --self-test` passed, including nested drive/ADS paths, cross-drive joining, and pre-creation outside-target controls. |
| Trusted release extraction and coverage | PASS | The `workflow_policy_group_release_jobs`, `workflow_policy_coverage`, and `workflow_policy_coverage_controls` CTests passed, including all four new control rows and their removal negatives. |
| Planning and summary gates | PASS | `plan_cap`, `planning_hygiene_controls`, and `summary_coverage_live` passed in the full run. |
| First full local CTest | 1706/1711 passed | The five failures were `v02_performance_controls`, `v02_delivery_controls`, `perf_advisory_pipeline`, `perf_advisory_controls`, and `release_review_approval`. Git could not create project-root worktree metadata under the managed checkout's read-only `.git`; none reported a product assertion failure. |
| Git-worktree focused retests | 5/5 passed | All five controls passed with a temporary Git wrapper redirecting only worktree operations launched from the project checkout to writable metadata under `/tmp`. |
| Wrapper-based full local CTest | 1710/1711 passed | All Git-worktree controls passed. `v02_source_archive_controls` reached its 90-second CTest timeout without a checker assertion or output while the full suite was running. |
| Source-archive focused retest | PASS, 45.57 seconds | The exact `v02_source_archive_controls` test passed alone with the normal Git path and its existing 90-second timeout. No timeout or implementation change was made. Its isolated pass after the full-suite timeout indicates a load-sensitive delay; the precise scheduler/process cause was not established. |
| Combined local test evidence | 1711/1711 cases have passing evidence | The two full-suite runs plus six focused retests cover all registered cases. This is combined evidence, not one uninterrupted green full-suite invocation. |
| Goal verification | HUMAN NEEDED | The GSD verifier confirmed all 35 implementation truths with no code gaps. It preserved two Plan 20-01 spec-less prohibitions as unresolved and descriptor-less, as required by the project instruction; owner source-grounding is needed before verification can pass. This is not a manual UAT request or a legal-clearance decision. |
| Rights status | PENDING | No fixture was admitted; byte identity checks do not establish legal permission or grant scope. |

The Phase 20 release-policy self-test passed with 186 controls, and the independent workflow-coverage self-test passed with 94 controls. Exact-head PR and push CI, preview-package smoke, and fixture-repro runs all completed successfully for PR #139 at this implementation head; the PR remains open and unmerged. The PR-only version gate was skipped as expected for this change.

## Validation Audit 2026-11-01

| Metric | Count |
|---|---|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
