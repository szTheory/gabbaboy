---
phase: GB-20-fixture-admission-tune-up
verified: 2026-11-01T23:13:34Z
status: passed
score: 35/35 must-haves verified
source_head: 1b9aa6f79b8a78efa995fa689bb8f9762c3aa30c
verification_head: 20e34d9a09b63059b34188c8fb486b5df50c2999
covered_files: [
    ".github/scripts/release-evidence-lifecycle.sh",
    ".github/scripts/safe_extract_package.py",
    ".github/scripts/verify-workflow-policy.py",
    ".github/workflows/ci.yml",
    ".github/workflows/fixture-repro.yml",
    ".github/workflows/preview.yml",
    ".github/workflows/release.yml",
    ".planning/phases/GB-20-fixture-admission-tune-up/20-01-PLAN.md",
    ".planning/phases/GB-20-fixture-admission-tune-up/20-01-SUMMARY.md",
    ".planning/phases/GB-20-fixture-admission-tune-up/20-02-PLAN.md",
    ".planning/phases/GB-20-fixture-admission-tune-up/20-02-SUMMARY.md",
    ".planning/phases/GB-20-fixture-admission-tune-up/20-03-PLAN.md",
    ".planning/phases/GB-20-fixture-admission-tune-up/20-03-SUMMARY.md",
    ".planning/phases/GB-20-fixture-admission-tune-up/20-04-PLAN.md",
    ".planning/phases/GB-20-fixture-admission-tune-up/20-04-SUMMARY.md",
    ".planning/phases/GB-20-fixture-admission-tune-up/20-05-PLAN.md",
    ".planning/phases/GB-20-fixture-admission-tune-up/20-05-SUMMARY.md",
    ".planning/phases/GB-20-fixture-admission-tune-up/20-06-PLAN.md",
    ".planning/phases/GB-20-fixture-admission-tune-up/20-06-SUMMARY.md",
    ".planning/phases/GB-20-fixture-admission-tune-up/20-07-PLAN.md",
    ".planning/phases/GB-20-fixture-admission-tune-up/20-07-SUMMARY.md",
    ".planning/phases/GB-20-fixture-admission-tune-up/20-08-PLAN.md",
    ".planning/phases/GB-20-fixture-admission-tune-up/20-08-SUMMARY.md",
    ".planning/phases/GB-20-fixture-admission-tune-up/20-09-PLAN.md",
    ".planning/phases/GB-20-fixture-admission-tune-up/20-09-SUMMARY.md",
    ".planning/phases/GB-20-fixture-admission-tune-up/20-CLOSEOUT-REVIEW.md",
    ".planning/phases/GB-20-fixture-admission-tune-up/20-FINAL-ARCHIVE-CODE-REVIEW.md",
    ".planning/phases/GB-20-fixture-admission-tune-up/20-FINAL-CODE-REVIEW.md",
    ".planning/phases/GB-20-fixture-admission-tune-up/20-FINAL-PRODUCT-CODE-REVIEW.md",
    ".planning/phases/GB-20-fixture-admission-tune-up/20-FINAL-TAR-CODE-REVIEW.md",
    ".planning/phases/GB-20-fixture-admission-tune-up/20-REVIEW-DISPOSITION.md",
    ".planning/phases/GB-20-fixture-admission-tune-up/20-REVIEW-FIX.md",
    ".planning/phases/GB-20-fixture-admission-tune-up/20-REVIEW.md",
    ".planning/phases/GB-20-fixture-admission-tune-up/20-SECURITY.md",
    ".planning/phases/GB-20-fixture-admission-tune-up/20-UAT.md",
    ".planning/phases/GB-20-fixture-admission-tune-up/20-UI-REVIEW.md",
    ".planning/phases/GB-20-fixture-admission-tune-up/20-VALIDATION.md",
    "CMakeLists.txt",
    "THIRD_PARTY_NOTICES.md",
    "cmake/FixtureAdmissionPolicy.json",
    "cmake/PreviewPackageSmoke.cmake",
    "cmake/VerifyInstalledPackage.cmake",
    "docs/fixture-admission.md",
    "tests/CMakeLists.txt",
    "tests/ci/test-budget-allowlist",
    "tests/cmake/ci-lanes.cmake",
    "tests/data/workflow-policy-controls.json",
    "tests/expected-tests.txt",
    "tests/scripts/test_player_package_policy.py",
    "tests/scripts/verify-dense-input.py",
    "tests/scripts/verify-fixture-admission.py",
    "tests/scripts/verify-phase3-player.sh",
    "tests/scripts/verify-release-candidate.sh",
    "tests/scripts/verify-release-lifecycle.py",
    "tests/scripts/verify-v02-adoption.py",
    "tests/scripts/verify-v02-source-archive.py",
    "tests/scripts/verify-workflow-policy-coverage.py"
]
covered_digest: "v4:sha256:b1f365f798ccb3e09000b59a33bfff93b9e2b881e7dcaf409734a69b0e57770b"
behavior_unverified: 0
overrides_applied: 0
decision_coverage:
  honored: 3
  total: 3
  not_honored: []
---

# Phase 20: Fixture Admission Tune-up Verification Report

**Phase Goal:** Maintainers can admit permitted evidence through one checked fixture and distribution boundary before new game or diagnostic bytes enter public automation.

**Source head:** 1b9aa6f79b8a78efa995fa689bb8f9762c3aa30c

**Verified:** 2026-11-01T23:13:34Z

**Status:** passed
**Re-verification:** No. The prior report had no `gaps:` section, so this pass re-established must-haves from the roadmap and plans.

## Goal Achievement

Both roadmap success criteria are implemented: admission is checked against exact fixture/source/build identities and recorded component terms, and installed/release products reject controlled ROM insertions while validating notices and root MIT. The checkers inspect repository objects, staged and extracted product trees, and downloaded archives. They validate identity and package policy; they do not grant legal permission.

Plan 20-01’s flagged RIGHTS-01 assumption is represented by truth 6 below: this phase admits no candidate and automated checks do not adjudicate grant scope. The boundary is verified; RIGHTS-01 remains pending and is not cleared by this report.

### Owner-Reviewed Prohibitions

Plan 20-01 now marks both judgment-tier prohibitions resolved and records the owner's 2026-11-01 confirmation, grounded in D-01. The evidence supports both findings:

- **No automated legal-clearance claim:** `docs/fixture-admission.md` says a digest establishes byte identity, not redistribution permission. The checker validates required record fields, pinned snapshots, and hashes; it has no legal grant adjudication path. `verify-v02-adoption.py --check docs --root .` passed with 447 documentation contract checks.
- **Historical dispositions preserved:** `--check-repository` compared 236 baseline fixture files and returned `admitted_changes=0`. No fixture manifest, fixture notice, or root `LICENSE` differs from the immutable baseline. The only notice-file change is the narrowly scoped product-inventory paragraph; the adoption controls retain the historical digest-row checks. No fixture or new rights disposition was added.

These findings resolve the two prior owner-review items only. They do not approve a fixture or satisfy RIGHTS-01.

### Observable Truths

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | A fixture can enter repository/public CI only when exact bytes, source/build inputs, and component terms/notices are recorded; incomplete rights or changed identities reject. | ✓ VERIFIED | The admission CLI validates versioned records against immutable Git blobs and the notice index. Final-head admission controls pass, and the direct repository check reports zero admitted changes. |
| 2 | A controlled game-ROM insertion in an installed or product-release package is rejected, while a valid package retains component notices and the root MIT declaration. | ✓ VERIFIED | Core/player package policies check actual staged, extracted, and archived bytes; exact-head preview and CI jobs pass. |
| 3 | Complete synthetic admission reaches the real CLI through a versioned manifest, notice index, and independent Git pins; incomplete records and changed identities fail closed. | ✓ VERIFIED | The registered fixture-admission controls exercise the production CLI, positive admission, and semantic negatives; they passed in the final-head local runs. |
| 4 | New or changed evidence cannot enter configured repository tests or fixture reproduction without admission checks; existing approvals are retained without a rights re-audit. | ✓ VERIFIED | CMake runs the repository check before configuring fixture-consuming targets. CI and fixture-repro run the same check before their first fixture-consuming steps. The direct check reports admitted_changes=0. |
| 5 | Product policy maps exact fixture and notice paths to independently pinned source bytes while source-archive policy remains separate. | ✓ VERIFIED | The product-policy JSON is pinned independently; the source archive checker keeps its receipt and source-archive contract separate from binary products. |
| 6 | This phase admits no candidate, and automated structure or identity checks do not adjudicate grant scope. | ✓ VERIFIED | The repository check reports admitted_changes=0; REQUIREMENTS.md still marks RIGHTS-01 Pending; fixture-admission docs state that hashes establish identity rather than permission. |
| 7 | An installed prefix and extracted preview archive contain exactly permitted core fixture bytes and notices plus unchanged root MIT. | ✓ VERIFIED | Installed-prefix and extracted-archive checks call the shared actual-tree policy and compare against the produced stage inventory; preview-package smoke passed at the exact head. |
| 8 | Renamed, suffixless, or subtree ROM insertions are rejected at the core package boundary. | ✓ VERIFIED | Forbidden fixture digests are checked before path exceptions; product mutation controls assert the product-fixture-leak rejection. |
| 9 | Core release producers and downloaded/reused archive checks enforce policy on actual archive and sidecar bytes; source archive inclusion is separate. | ✓ VERIFIED | Release workflow stages and downloads use the trusted product checker; the source archive checker retains a separate source contract. Exact-head CI and release-policy controls pass. |
| 10 | Missing or altered fixture notices, root MIT, or the core gabbaboy-notices.txt sidecar cannot pass the core package check. | ✓ VERIFIED | Package mutation controls reject missing, altered, and misnamed notice assets at the real product boundary. |
| 11 | Source receipts and Linux/core product archive checks bound hidden PAX/GNU metadata before payload parsing, including stream, per-header, aggregate-byte, and count limits. | ✓ VERIFIED | The bounded streaming TAR parser checks metadata limits before its base parser consumes extension payloads. The exact named source-archive control passed alone in 45.57 seconds at this head. |
| 12 | The 128-header chain cap remains separate from a 32,768-header archive-wide cap; valid archives with more than 128 long-path members remain accepted. | ✓ VERIFIED | The parser has distinct chain and total counters. Its controls test interleaved over-limit headers, 256 long-path members, and independent counter lifetime. |
| 13 | The actual macOS player stage and extracted archive retain the exact fixture subset, root MIT, and fixture/SDL notices at established paths. | ✓ VERIFIED | The player verifier checks stage and extracted trees; exact-head macOS player-package CI passed. |
| 14 | Downloaded/reused player verification applies the same actual-byte policy before launch, including renamed or hidden fixture payloads. | ✓ VERIFIED | Release and preview callers check downloaded player bytes before execution; player mutation controls and exact-head preview qualification pass. |
| 15 | A clean player package passes, while insertion, identity, and missing/changed fixture, MIT, or SDL notice controls fail for their intended reasons. | ✓ VERIFIED | Production-wrapper player controls assert semantic rejection reasons and preserve the clean candidate inventory; exact-head package CI passed. |
| 16 | Direct manifest and repository validation reject fixture walks above the fixed file/directory-entry limit. | ✓ VERIFIED | Incremental filesystem traversal counts entries before processing; the registered fixture-admission controls passed in final-head runs. |
| 17 | Git fixture enumeration bounds stdout bytes and record count while consuming output, and terminates/reaps an over-limit child. | ✓ VERIFIED | The streaming reader applies both limits during consumption; fake-process controls assert termination, reaping, stream closure, and reader completion. |
| 18 | Stable rejection tokens distinguish filesystem-entry, Git-entry, and Git-output-byte overflow. | ✓ VERIFIED | Each bounded branch returns its dedicated token, and negative controls assert the exact token. |
| 19 | Existing fixture identities, product policy, notices, and admission decisions continue to pass after traversal hardening. | ✓ VERIFIED | The current repository check and final-head admission/product controls pass; no admitted fixture changes are present. |
| 20 | Product authority is independently pinned and the exact core inventory reconciles with that policy. | ✓ VERIFIED | The checker pins the policy digest and derives the expected product inventory from immutable source bytes; product controls pass. |
| 21 | Positive and content-caused negative controls exercise production boundaries and reject for the intended reasons. | ✓ VERIFIED | Admission, core/player product, workflow-policy, and notice controls assert exact acceptance/rejection results and reason tokens. |
| 22 | Every regular product file is checked for a forbidden fixture digest before allowed/generated/one_of path handling in both core and player layouts. | ✓ VERIFIED | Digest checks precede path exceptions; core and player controls cover required and one_of generated paths. |
| 23 | No fixture is admitted, prior rights dispositions remain unchanged, and RIGHTS-01 stays pending. | ✓ VERIFIED | The direct repository check reports admitted_changes=0; REQUIREMENTS.md remains Pending; the source and license state do not claim new permission. |
| 24 | The trusted publisher validates downloaded macOS and Windows products. | ✓ VERIFIED | Release workflow callers use checker and policy files from the trusted publisher checkout; exact-head release-policy controls and hosted platform CI passed. |
| 25 | Positive and content-caused negative controls exercise downloaded-product verification and reject for intended reasons. | ✓ VERIFIED | Release lifecycle controls cover downloaded bytes, altered content, and unsafe paths; release-policy controls passed at this head. |
| 26 | Hidden tar extension metadata and total decompressed bytes are bounded before an over-limit payload reaches parsing. | ✓ VERIFIED | The bounded reader and pre-payload TAR guards enforce stream and extension limits; exact-head source-archive controls passed. |
| 27 | A missing trusted checker rejects without leaving an extraction destination; restoring the checker permits retry at the same destination. | ✓ VERIFIED | Lifecycle controls exercise cleanup on missing-checker and late-rejection paths and same-destination retry; the registered final-head controls passed. |
| 28 | Drive-qualified and NTFS alternate-stream paths reject on every host, and directory/file targets are contained before filesystem creation. | ✓ VERIFIED | The reusable extractor self-test passed for drive/ADS syntax and injected directory/file escapes; exact-head Windows CI also passed. |
| 29 | Repository-admission commands are matched exactly in complete workflow mutation subjects. | ✓ VERIFIED | The trusted workflow checker parses exact command words and root assignments; complete-subject mutation controls pass. |
| 30 | Positive and content-caused negative controls exercise repository-admission workflow matching. | ✓ VERIFIED | CI and workflow-policy controls assert the intended command match and reject removal or redirection. |
| 31 | Notice-contract consumers preserve the exact source-versus-product distinction. | ✓ VERIFIED | The adoption checker verifies the reviewed distinction against THIRD_PARTY_NOTICES.md; its registered controls pass. |
| 32 | Positive and negative notice controls reject missing or contradictory claims for intended reasons. | ✓ VERIFIED | Adoption/documentation mutations assert the specific missing or contradictory notice outcomes; final-head test evidence passes. |
| 33 | Dense-input source-only mutant admission uses separate immutable evidence. | ✓ VERIFIED | The source-only harness reads baseline objects from a separate pinned object store while evaluating subject-owned source bytes. |
| 34 | An external baseline object store does not qualify a source-only build; missing trusted evidence fails closed. | ✓ VERIFIED | The source-only flow keeps build qualification tied to the subject revision; missing/wrong baseline and changed-fixture controls reject. |
| 35 | Positive and content-caused negative controls exercise dense-input admission and reject for intended reasons. | ✓ VERIFIED | The registered dense-input controls cover the separate baseline, unqualified-build, and changed-fixture cases and passed in the final-head evidence set. |

**Score:** 35/35 observable truths verified (0 present, behavior-unverified).

### Resolved Must-Not Prohibitions

Both Plan 20-01 prohibitions now declare `verification: judgment` and `status: resolved`. The owner review is recorded in the plan; the independent evidence above supports those resolutions. No unresolved prohibition remains.

## Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| tests/scripts/verify-fixture-admission.py | Admission, repository, and actual product-byte checker | ✓ VERIFIED | Exists, substantive validation paths and semantic controls, called by CMake and CI/release flows. |
| cmake/FixtureAdmissionPolicy.json | Independently pinned product paths and source identities | ✓ VERIFIED | Exists, consumed by the checker and package policies. |
| docs/fixture-admission.md | Manifest, limits, identity, and legal-scope contract | ✓ VERIFIED | Exists, substantive contract; aligned with checker and notice controls. |
| cmake/VerifyInstalledPackage.cmake | Installed-prefix policy validation | ✓ VERIFIED | Checks actual installed bytes through the shared checker. |
| cmake/PreviewPackageSmoke.cmake | Stage/extracted package and mutation checks | ✓ VERIFIED | Checks the produced prefix and extracted archive before consumers run. |
| tests/scripts/verify-v02-source-archive.py | Bounded source/archive and core product inspection | ✓ VERIFIED | Shared bounded TAR parser is used by receipt and product paths. |
| .github/workflows/release.yml | Trusted core/player downloaded-product enforcement | ✓ VERIFIED | Release jobs call trusted checker and lifecycle boundaries. |
| tests/scripts/verify-phase3-player.sh | Player stage/extract package policy | ✓ VERIFIED | Calls the shared checker before archive use and player execution. |
| tests/ci/test-budget-allowlist | Bounded test-control budgets | ✓ VERIFIED | Present and checked by registered test-budget controls. |
| .github/scripts/release-evidence-lifecycle.sh | Trusted release extraction and cleanup lifecycle | ✓ VERIFIED | Called from release workflow and checked by release lifecycle controls. |
| .github/scripts/verify-workflow-policy.py | Trusted workflow and downloaded archive policy | ✓ VERIFIED | Substantive policy; dynamically loads the sibling safe extractor. |
| tests/data/workflow-policy-controls.json | Stable workflow/source-control registry | ✓ VERIFIED | Present; independent coverage checks validate required entries. |
| .github/scripts/safe_extract_package.py | Bounded archive reader and safe extractor | ✓ VERIFIED | Present; rejects unsafe names and proves containment before writes. |
| tests/scripts/verify-workflow-policy-coverage.py | Immutable source and mutation coverage checker | ✓ VERIFIED | Present; pins the reviewed source and tests guard-removal mutants. |
| tests/cmake/ci-lanes.cmake | Enforced workflow-coverage completion | ✓ VERIFIED | Present and wired into registered CTest lanes. |
| tests/scripts/verify-v02-adoption.py | Shared source/product notice contract | ✓ VERIFIED | Present and called by registered adoption/documentation controls. |
| tests/scripts/verify-dense-input.py | Source-only mutant baseline enforcement | ✓ VERIFIED | Present and connected to the dense-input CTest path. |
| CMakeLists.txt | Configure-time fixture admission gate | ✓ VERIFIED | Gate runs before fixture-consuming targets and tests are configured. |

## Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| tests/scripts/verify-fixture-admission.py | cmake/FixtureAdmissionPolicy.json | Reads independent baseline and policy identities | WIRED | Target reference and current repository check verified. |
| CMakeLists.txt | tests/scripts/verify-fixture-admission.py | BUILD_TESTING configure gate | WIRED | CMake executes the checker before target/test setup. |
| .github/workflows/fixture-repro.yml | tests/scripts/verify-fixture-admission.py | Before fixture build/download | WIRED | Workflow invokes repository admission at entry. |
| cmake/VerifyInstalledPackage.cmake | tests/scripts/verify-fixture-admission.py | Actual installed-prefix tree | WIRED | Passes explicit checkout and policy roots. |
| cmake/PreviewPackageSmoke.cmake | cmake/VerifyInstalledPackage.cmake | Stage and extracted prefix | WIRED | Both actual trees are checked before use. |
| tests/scripts/verify-release-candidate.sh | tests/scripts/verify-v02-source-archive.py | Product receipt/verification dispatch | WIRED | Existing verification modes invoke the archive checker with a real sidecar. |
| tests/scripts/verify-v02-source-archive.py inspect_tar | build_receipt and check_product | inspect_archive dispatches to inspect_tar; both callers use inspect_archive | WIRED | The receipt and core product paths share the bounded TAR parser through the archive dispatcher. |
| .github/workflows/release.yml | tests/scripts/verify-fixture-admission.py | Core product stages and extracted downloads | WIRED | Trusted source checker validates actual trees before qualification. |
| tests/scripts/verify-phase3-player.sh | tests/scripts/verify-fixture-admission.py | Player stage and extracted package | WIRED | Production wrapper calls the shared policy before launch. |
| .github/workflows/ci.yml | tests/scripts/verify-phase3-player.sh | macos-player-package producer | WIRED | Exact package build lane calls the wrapper. |
| .github/workflows/release.yml | tests/scripts/verify-phase3-player.sh | Player build and downloaded verification | WIRED | Both package stages use the wrapper. |
| check_manifest | current_fixture_files | Bounded filesystem walk | WIRED | Manifest checker calls the incremental walker. |
| check_repository | current_fixture_files and tree_files | Current and immutable tree comparison | WIRED | Repository admission calls both bounded enumerators. |
| fixture_admission_controls CTest | verify-fixture-admission.py --self-test | Production semantic controls | WIRED | CTest registration invokes the script self-test. |
| tests/scripts/verify-fixture-admission.py | cmake/FixtureAdmissionPolicy.json | Product inventory and immutable authority | WIRED | Shared contract also covers the Plan 20-05 policy link. |
| .github/workflows/release.yml | .github/scripts/release-evidence-lifecycle.sh | Trusted release lifecycle | WIRED | Workflow invokes lifecycle operations from trusted checkout. |
| .github/scripts/verify-workflow-policy.py | .github/scripts/safe_extract_package.py | Dynamic sibling load | WIRED | Manual trace confirmed resolved sibling path, importlib load, and use of bounded archive APIs. |
| tests/scripts/verify-workflow-policy-coverage.py | tests/data/workflow-policy-controls.json | Stable controls and reviewed source | WIRED | Coverage checker reads and validates the registry. |
| .github/scripts/verify-workflow-policy.py | tests/data/workflow-policy-controls.json | Workflow mutation controls | WIRED | Registered release and CI controls invoke the production checker. |
| tests/scripts/verify-v02-adoption.py | THIRD_PARTY_NOTICES.md | Source/product notice claims | WIRED | Registered adoption controls read and validate the notice contract. |
| tests/scripts/verify-dense-input.py | tests/scripts/verify-fixture-admission.py | Independent baseline admission | WIRED | Dense-input controls use the fixture checker without inheriting build qualification. |

The GSD link query could not interpret function-name endpoints in Plans 20-02 and 20-04 and did not detect the dynamic helper load in Plan 20-06. Source inspection confirmed those links as wired; no link remains unresolved.

## Data-Flow Trace (Level 4)

| Artifact | Data variable | Source | Produces real data | Status |
|---|---|---|---|---|
| Fixture admission checker | Current fixture tree and manifest bytes | Working tree plus pinned Git blobs | Yes; direct repository check reads the actual checkout and immutable baseline | ✓ FLOWING |
| Core/player product checker | Product paths, sizes, and digests | Staged and extracted package files | Yes; policies enumerate and hash actual files, with synthetic trees used only as negatives | ✓ FLOWING |
| Trusted publisher | Downloaded archive and sidecar | CI artifact bytes, checked with trusted checkout code | Yes; checker runs before release qualification | ✓ FLOWING |
| Source archive checker | Members and metadata | Real TAR stream | Yes; bounded parser processes archive bytes and feeds receipt/product checks | ✓ FLOWING |
| Dense-input admission | Subject source and baseline objects | Source-only mutant plus separately pinned object store | Yes; baseline objects do not supply subject build identity | ✓ FLOWING |

## Final Implementation-Head Evidence

Implementation head: 1b9aa6f79b8a78efa995fa689bb8f9762c3aa30c.

| Check | Result | Evidence |
|---|---|---|
| Configure/build | PASS | Final implementation-head configure and build passed. The subsequent commit changes planning evidence only; code is unchanged. |
| First full local CTest run | 1706/1711 passed | Five Git worktree metadata writes were denied by the managed read-only .git. All five named controls passed with temporary Git metadata under /tmp. |
| Wrapper-based full local CTest run | 1710/1711 passed | Only v02_source_archive_controls reached its 90-second timeout during the full run, without a checker assertion. |
| Focused source-archive retest | PASS, 45.57 seconds | The exact test passed alone using the normal Git path. The load/scheduler cause of the full-run timeout was not established. |
| Combined local test evidence | 1711/1711 have passing evidence | Two partial full runs plus six focused retests cover all registered cases. No single full-suite invocation was all-green. |
| Planning/summary/hygiene checks | 3/3 passed | plan_cap, planning_hygiene_controls, and summary_coverage_live passed after the latest documentation refresh. |
| Shared UAT closure | Complete, 23/23 automated cases pass | `20-UAT.md` records zero issues or pending cases; the two Plan 20-01 judgment items were separately reviewed by the owner. |
| Exact-head pull-request CI | PASS | [Run 41347651035](https://github.com/szTheory/gabbaboy/actions/runs/41347651035), head SHA matches the implementation head. |
| Exact-head push CI | PASS | [Run 41347645660](https://github.com/szTheory/gabbaboy/actions/runs/41347645660), head SHA matches the implementation head. |
| Exact-head preview package | PASS | [Run 41347651030](https://github.com/szTheory/gabbaboy/actions/runs/41347651030), head SHA matches the implementation head. |
| Exact-head fixture-repro PR and push runs | PASS | [PR run 41347651034](https://github.com/szTheory/gabbaboy/actions/runs/41347651034) and [push run 41347645556](https://github.com/szTheory/gabbaboy/actions/runs/41347645556) both match the implementation head. |
| PR disposition | OPEN, unmerged | [PR #139](https://github.com/szTheory/gabbaboy/pull/139) remains open; no merge is claimed. |
| Security audit | 29/29 authored threat entries closed | 20-SECURITY.md records threats_open=0; rights clearance remains separate. |
| Final review | Clean | Current code review reports zero open findings; the disposition table marks all six reviewed findings fixed. |
| UI review | Not applicable | Phase 20 changes no interface or user flow. |

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Reusable extraction rejects drive/ADS paths and out-of-root writes before filesystem mutation | `python3 -I .github/scripts/safe_extract_package.py --self-test` | PASS; controls cover path aliases, containment, and bounded reads (0.2 s) | ✓ PASS |
| Repository admission rejects unrecorded fixture changes | `python3 -I tests/scripts/verify-fixture-admission.py --check-repository --repo-root .` | PASS; legacy_files=236, admitted_changes=0 (2.9 s) | ✓ PASS |
| Notice documentation preserves the distinction between byte identity and permission | `python3 -I tests/scripts/verify-v02-adoption.py --check docs --root .` | PASS; 447 checks, positive_success=true (0.2 s) | ✓ PASS |

The full fixture-admission self-test and core product self-test also passed in this refresh (2 positive cases plus 58 admission negatives; 42 core-product negatives). They are recorded as production control runs, not under-ten-second spot-checks. The exact-head final evidence above covers the remaining registered and hosted controls; the code has not changed since that implementation head.

## Probe Execution

| Probe | Command | Result | Status |
|---|---|---|---|
| No Phase 20 probe is declared in the plans or summaries | N/A | The repository Mooneye candidate probe is unrelated to this fixture/package-boundary phase | N/A |

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| RIGHTS-01 | Plans 20-01 through 20-09 | An admitted candidate has source-grounded repository/public-CI rights by component; game ROMs stay out of products and root MIT remains unchanged. | PENDING (explicitly retained) | No candidate was admitted. The technical boundary and product exclusions are verified; no candidate-specific grant was evaluated. `.planning/REQUIREMENTS.md` remains Pending as instructed. |

No other requirement is mapped to Phase 20. The phase goal is achieved without claiming candidate rights clearance; future admission still requires source-grounded maintainer review.

## Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
|---|---|---:|---:|---|---|---|
| tests/scripts/verify-fixture-admission.py | RIGHTS-01 boundary | Yes | 0 found | No | Behavioral/value: positive admission, exact rejection tokens, and immutable identity checks | Proves the evidence gate; does not prove legal grant scope. |
| tests/scripts/verify-v02-source-archive.py | RIGHTS-01 product boundary | Yes | 0 found | No | Behavioral/value: exact parser limits, product bytes, and rejection reasons | Pass; synthetic archives are inputs, expected outcomes are independent tokens. |
| tests/scripts/verify-workflow-policy-coverage.py | RIGHTS-01 trusted workflow boundary | Yes | 0 found | No | Value: pinned source digest, registry identity, and guard-removal mutants | Pass; controls are not derived from the system response. |
| tests/scripts/verify-v02-adoption.py | RIGHTS-01 notice contract | Yes | 0 found | No | Value: expected notice claims and semantic mutations | Pass; candidate-specific legal scope remains pending. |

**Disabled tests on requirements:** 0 found.

**Circular patterns detected:** 0; test scripts write synthetic inputs and mutants, not expected output generated from the implementation.
**Insufficient assertions:** 0 for the checked admission, archive, workflow-policy, and notice behaviors. Candidate-specific legal permission has no fixture to exercise and remains pending.

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---:|---|---|---|
| .planning/phases/GB-20-fixture-admission-tune-up/20-08-SUMMARY.md | 18 | Lists tests/data/notice-adoption-controls.json as modified, but the file is absent and has no Git history or references. | Info | Plan 20-08’s notice controls are in verify-v02-adoption.py; this summary key-file mismatch does not affect the declared must-haves. |

The implementation-file scan found no unreferenced TBD/FIXME/XXX markers, cleanup placeholders, empty implementations, hardcoded empty output data, or console-log-only handlers.

## Human Verification Required

None for the Phase 20 goal. The owner explicitly reviewed the two judgment-tier findings and the code/docs support them. RIGHTS-01 remains pending because there is no candidate-specific rights decision to verify; no fixture is approved or admitted by this report.

## Gaps Summary

No implementation truth, artifact, or key link failed; all 35 observable truths are verified. The two prior judgment findings are resolved by the owner and supported by current code and documentation. RIGHTS-01 remains Pending because no candidate was admitted and no source-grounded grant scope was evaluated. This is not a legal-clearance claim or an implementation gap in the Phase 20 boundary.

### Decision Coverage

All 3 trackable CONTEXT.md decisions are honored by shipped artifacts. This gate is non-blocking.

---

_Verified: 2026-11-01T23:13:34Z_
_Verifier: the agent (gsd-verifier)_
