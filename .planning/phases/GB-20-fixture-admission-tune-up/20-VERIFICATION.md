---
phase: GB-20-fixture-admission-tune-up
verified: 2026-11-01T18:53:11Z
status: passed
score: 35/35 must-haves verified
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
covered_digest: "v4:sha256:51eabf66b973fd39c1420855bf79acfdf5a47471176bf25b54dd674c7f0440b7"
behavior_unverified: 0
overrides_applied: 0
decision_coverage:
  honored: 3
  total: 3
  not_honored: []
human_verification: []
---

# Phase 20: Fixture Admission Tune-up Verification Report

**Phase Goal:** Maintainers can admit permitted evidence through one checked fixture and distribution boundary before new game or diagnostic bytes enter public automation.

**Source head:** 39eb048e7770652b84a3fc5da7aaa3890adbd70c
**Verified:** 2026-11-01T18:53:11Z
**Status:** passed
**Re-verification:** No. The prior report had no gaps section, so initial-mode verification applies.

## Goal Achievement

The outcome is a working admission and distribution boundary. It does not admit a fixture or decide the legal scope of any grant. Source and product bytes, their declared identities, required notices, and release paths are checked by executable controls.

### Observable Truths

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | A fixture enters repository/public CI only with exact bytes, source/build inputs and component terms/notices recorded; incomplete rights or changed identities reject. | ✓ VERIFIED | Actual CLI validates the versioned manifest, notice index and independent Git pins. Its synthetic positive and coordinated rewrite/missing-evidence controls pass. |
| 2 | A controlled game-ROM insertion in an installed or product-release package is rejected, while a valid package retains required notices and the root MIT declaration. | ✓ VERIFIED | Core/player stage, archive, extraction and downloaded-package controls inspect actual bytes; exact-head package CI and preview jobs pass. |
| 3 | A complete synthetic fixture admission reaches the real CLI through versioned manifest, notice index and independently pinned Git blobs; incomplete records and changed identities fail closed. | ✓ VERIFIED | tests/scripts/verify-fixture-admission.py self-test; exact admission decision, source pin and blob checks in check_manifest(). |
| 4 | New or changed evidence cannot enter configured repository tests or fixture reproduction without the admission gate; existing approvals are retained without a rights re-audit. | ✓ VERIFIED | CMake BUILD_TESTING gate precedes fixture-consuming tests; ci.yml and fixture-repro.yml gate use. Direct repository check reports 236 legacy files and 0 admitted changes; no fixture or LICENSE diff from the pinned baseline. |
| 5 | Product policy maps exact smoke-fixture and notice paths to independently pinned source bytes, while source-archive policy stays separate. | ✓ VERIFIED | cmake/FixtureAdmissionPolicy.json and verify-fixture-admission.py bind product inventory to baseline blobs; verify-v02-source-archive.py keeps source receipt parsing separate. |
| 6 | This phase admits no candidate, and automated structure/identity checks do not decide grant scope. | ✓ VERIFIED | No fixture changed or was added. docs/fixture-admission.md states a digest establishes identity, not permission; RIGHTS-01 remains PENDING. |
| 7 | An installed prefix and its extracted preview archive contain exactly permitted core fixture bytes/notices and unchanged root MIT. | ✓ VERIFIED | VerifyInstalledPackage.cmake and PreviewPackageSmoke.cmake call the shared actual-tree policy for stage and extracted archive; preview smoke passed locally/hosted. |
| 8 | Renamed, suffixless, or subtree ROM insertions are rejected at the core package boundary. | ✓ VERIFIED | Product checker compares forbidden fixture digests before path/allowlist handling; positive/negative core package controls pass. |
| 9 | Core release producers and downloaded/reused archive checks enforce policy on actual archive and sidecar bytes; source archive inclusion is separate. | ✓ VERIFIED | release.yml, verify-release-candidate.sh and verify-v02-source-archive.py trace staged/downloaded product bytes and the sidecar through the checker; release controls pass. |
| 10 | Missing or altered fixture notices, root MIT or core gabbaboy-notices.txt cannot pass the core package check. | ✓ VERIFIED | Exact notice and sidecar mutation controls reject at the core boundary; verify-v02-adoption controls pass. |
| 11 | Source receipts and Linux/core product archives reject excessive hidden PAX/GNU metadata before payload parsing with stream, per-header, aggregate-byte and header-count bounds. | ✓ VERIFIED | Bounded streaming parser checks counts/bytes before payload parsing; v02_source_archive_controls passed. |
| 12 | Per-member extension chains retain a 128-header cap while a separate archive-wide cap of 32,768 never resets; valid long-path archives with over 128 members remain accepted. | ✓ VERIFIED | Parser has independent chain and total counters; positive 256-long-path-member control passes with the total limit enforced. |
| 13 | The actual macOS player stage and extracted package carry only the exact original fixture subset, root MIT and fixture/SDL notices at their established paths. | ✓ VERIFIED | verify-phase3-player.sh validates stage and extracted archive inventories; exact-head hosted macOS player package lane passes. |
| 14 | Downloaded/reused player verification applies the same actual-byte policy before launch, including renamed or hidden fixture payloads. | ✓ VERIFIED | release/preview callers invoke the player policy before execution; player mutation controls reject before launch. |
| 15 | A clean player package passes, while insertion, identity and missing/altered fixture, MIT or SDL notices fail for their expected reasons. | ✓ VERIFIED | Actual package positive/negative controls pass; PR macos-player-package and preview player receipt jobs pass. |
| 16 | Direct manifest and repository validation reject fixture walks over the fixed file/directory-entry limit. | ✓ VERIFIED | Incremental filesystem walker enforces MAX_FIXTURE_ENTRIES; fixture_admission_controls exercises overflow and passes. |
| 17 | Git fixture-tree enumeration bounds stdout bytes and record count while consuming output, and terminates/reaps an over-limit child. | ✓ VERIFIED | Streaming tree_files() checks both bounds and cleans up the subprocess; self-test covers overflow/cleanup and passes. |
| 18 | Stable rejection tokens distinguish filesystem-entry, Git-entry and Git-output-byte overflow. | ✓ VERIFIED | Dedicated stable tokens are returned by the three checked branches; negative controls assert the intended token. |
| 19 | Existing fixture identities, product policy, notices and admission decisions continue to pass after traversal hardening. | ✓ VERIFIED | Current repository admission check and focused admission/core/player controls pass on this head. |
| 20 | Product authority is independently pinned and the exact core inventory reconciles with that policy. | ✓ VERIFIED | Product-policy SHA is pinned independently; core inventory is checked against exact paths, bytes and baseline identities. |
| 21 | Positive and content-caused negative controls exercise the real production boundary and reject for intended reasons. | ✓ VERIFIED | Core/player policy self-tests and workflow controls assert exact stable rejection reasons; all related CTests pass in the final evidence set. |
| 22 | Every regular product file is checked for a known forbidden fixture digest before allowed/generated/one_of path handling, for both layouts. | ✓ VERIFIED | _validate_product_entries() checks forbidden digests before exceptions; core/player insertion controls exercise all layouts. |
| 23 | No fixture is admitted, prior rights dispositions remain unchanged, and RIGHTS-01 stays pending. | ✓ VERIFIED | Repository check reports admitted_changes=0; fixture and root LICENSE are unchanged from the immutable baseline; REQUIREMENTS.md marks RIGHTS-01 Pending. |
| 24 | The trusted publisher validates downloaded macOS and Windows products. | ✓ VERIFIED | release.yml downloads and invokes the trusted shared checker for both platform products before qualification; exact-head native and release-policy jobs pass. |
| 25 | Positive and content-caused negative controls exercise the downloaded-product boundary and reject for intended reasons. | ✓ VERIFIED | release lifecycle and workflow-policy controls inspect the real downloaded-product path and assert stable reasons; current tests pass. |
| 26 | Hidden tar extension metadata and total decompressed bytes are bounded before an over-limit payload reaches the parser. | ✓ VERIFIED | Trusted bounded reader and safe extractor enforce stream and extension limits before member processing; security controls pass. |
| 27 | A missing trusted checker fails without leaving an extraction destination; restoring the checker permits retry at the same destination. | ✓ VERIFIED | Lifecycle controls verify cleanup and same-destination retry; these state transitions pass in the final CTest evidence. |
| 28 | Drive-qualified and NTFS alternate-stream names reject on every host, and target paths/parents are contained before filesystem creation. | ✓ VERIFIED | safe_extract_package.py and verify-workflow-policy.py validate path components and containment before writes; path mutation controls pass. |
| 29 | Admission workflow commands are matched exactly in complete mutation subjects. | ✓ VERIFIED | Workflow checker operates on isolated complete workflow subjects and rejects command redirection; workflow-policy controls pass. |
| 30 | Positive and content-caused negative controls exercise repository-admission workflow matching and reject for intended reasons. | ✓ VERIFIED | CI/release workflow mutation controls assert exact matcher outcomes; release/workflow policy groups pass. |
| 31 | Notice-contract consumers preserve the exact source-versus-product distinction. | ✓ VERIFIED | verify-v02-adoption.py checks the reviewed notice claims and explicit product contract; CTest adoption controls pass. |
| 32 | Positive and content-caused negative notice controls reject missing or contradictory claims for intended reasons. | ✓ VERIFIED | Notice mutation controls cover missing/altered source and product notices; adoption controls pass. |
| 33 | Dense-input source-only mutant admission uses separate immutable evidence. | ✓ VERIFIED | verify-dense-input.py creates a distinct baseline object store and source-only mutant; tests exercise it independently from the build tree. |
| 34 | An external baseline object store does not qualify the source-only build; missing trusted evidence fails closed. | ✓ VERIFIED | Baseline object identity is not treated as build evidence; missing/wrong baseline and changed fixture controls reject. |
| 35 | Positive and content-caused negative controls exercise dense-input admission and reject for intended reasons. | ✓ VERIFIED | acceptance_dense_input_controls and source-only mutant tests pass in the current exact-head evidence. |

**Score:** 35/35 truths verified (0 present, behavior-unverified).

The two must-not constraints in Plan 20-01 were also checked: the tooling/docs do not present hashes or populated fields as legal clearance, and the baseline comparison/gates preserve prior approvals without granting blanket permission to new evidence. Both are verified; this is not a decision on any fixture's legal scope.

### Required Artifacts

All 28 plan artifact declarations pass the GSD artifact check. Unique artifact paths are listed below; each exists, is substantive, and is wired into its caller or test boundary.

| Artifact | Expected | Status | Details |
|---|---|---|---|
| tests/scripts/verify-fixture-admission.py | Admission CLI and product checker | ✓ VERIFIED | 20-01/04/05/09; tested by CTest and direct repository check. |
| cmake/FixtureAdmissionPolicy.json | Independent baseline and destination policy | ✓ VERIFIED | 20-01/05; consumed by shared checker. |
| docs/fixture-admission.md | Manifest contract and legal-scope limitation | ✓ VERIFIED | 20-01/04/05/09; contract matches implementation. |
| cmake/VerifyInstalledPackage.cmake | Installed core policy check | ✓ VERIFIED | 20-02; invokes trusted shared policy. |
| cmake/PreviewPackageSmoke.cmake | Actual stage/extracted package smoke and mutations | ✓ VERIFIED | 20-02; drives installed and archive controls. |
| tests/scripts/verify-v02-source-archive.py | Bounded source/product archive verification | ✓ VERIFIED | 20-02; used by release candidate and CTest. |
| .github/workflows/release.yml | Core/player producer and downloaded product checks | ✓ VERIFIED | 20-02/06; validates actual bytes before release qualification. |
| tests/scripts/verify-phase3-player.sh | Player stage/archive validation | ✓ VERIFIED | 20-03; called by package/release jobs. |
| tests/ci/test-budget-allowlist | Test-budget and policy accounting | ✓ VERIFIED | 20-05; consumed by the matching CI lane. |
| .github/scripts/release-evidence-lifecycle.sh | Release evidence lifecycle helpers | ✓ VERIFIED | 20-06; sourced by the trusted release checker. |
| .github/scripts/verify-workflow-policy.py | Trusted workflow and downloaded archive verifier | ✓ VERIFIED | 20-06/07; wired to CI/release checks and tests. |
| tests/data/workflow-policy-controls.json | Stable workflow mutation-control registry | ✓ VERIFIED | 20-06/07; consumed by workflow policy tests. |
| .github/scripts/safe_extract_package.py | Bounded safe archive extraction helper | ✓ VERIFIED | 20-06; dynamically loaded from trusted sibling path. |
| tests/scripts/verify-workflow-policy-coverage.py | Control registry and workflow mutation tests | ✓ VERIFIED | 20-06; registered in CTest. |
| tests/cmake/ci-lanes.cmake | CI lane test wiring | ✓ VERIFIED | 20-06; wires safety checks into CTest. |
| tests/scripts/verify-v02-adoption.py | Notice and product-claim contract controls | ✓ VERIFIED | 20-08; registered and passing in CTest. |
| tests/scripts/verify-dense-input.py | Source-only mutant with independent evidence | ✓ VERIFIED | 20-09; invoked by dense-input acceptance controls. |
| CMakeLists.txt | Configure-time repository admission gate | ✓ VERIFIED | 20-09; runs before fixture-consuming targets when BUILD_TESTING is enabled. |

### Key Link Verification

| Plan | Automated result | Manual source trace | Status |
|---|---:|---|---|
| 20-01 | 3/3 | Manifest/policy, configure gate and fixture-repro call are direct references. | ✓ WIRED |
| 20-02 | 4/5 | The fifth link starts at inspect_tar(), a function within the target file, so the path-based checker cannot resolve it; receipt and product paths use the same bounded parser. | ✓ WIRED |
| 20-03 | 3/3 | Player stage/extraction calls and CI/release callers directly reference the shared policy. | ✓ WIRED |
| 20-04 | 0/3 | All three sources are function/test names rather than file paths; check_manifest(), check_repository(), current_fixture_files(), tree_files() and the registered CTest are connected in code. | ✓ WIRED |
| 20-05 | 1/1 | The production checker consumes the pinned policy; controls exercise it. | ✓ WIRED |
| 20-06 | 2/3 | The third link is a dynamic import from the trusted sibling script directory; the policy checker calls it before extraction. | ✓ WIRED |
| 20-07 | 1/1 | Mutation control registry is consumed by the workflow policy test. | ✓ WIRED |
| 20-08 | 1/1 | Notice checker reads the source/product notice contract. | ✓ WIRED |
| 20-09 | 1/1 | Dense-input checker invokes the admission checker with isolated immutable evidence. | ✓ WIRED |

The automated checker reports 16/21 direct links. I traced the remaining five in code; they are path-checker limitations on function-level and dynamic-import links, not disconnected artifacts. All 21 links are wired.

### Data-Flow Trace (Level 4)

| Artifact | Data variable | Source | Produces real data | Status |
|---|---|---|---|---|
| verify-fixture-admission.py | Manifest, notice index and file digests | Repository files plus pinned Git blobs | Yes; verifies actual bytes against immutable identities | ✓ FLOWING |
| Installed/package policy callers | Product entries and sidecar | Staged, extracted or downloaded filesystem/archive bytes | Yes; checker hashes actual regular files and compares exact inventory | ✓ FLOWING |
| verify-v02-source-archive.py | Tar members and receipts | Bounded decompressed archive stream | Yes; checks parsed payload, metadata and receipt against real archive bytes | ✓ FLOWING |
| safe_extract_package.py / workflow policy | Archive inventory and destinations | Downloaded release archive and trusted local checker | Yes; validates paths and actual content before/while extracting | ✓ FLOWING |

This is an infrastructure phase with no rendered user data; the byte/archive traces above are the relevant data flows.

### Behavioral Spot-Checks

| Behavior | Command/evidence | Result | Status |
|---|---|---|---|
| Current repository admission | python3 -I tests/scripts/verify-fixture-admission.py --check-repository --repo-root . | PASS: 236 legacy files, admitted_changes=0, baseline 7cc6495e64f3645caa120e7458f754585b788985 | ✓ PASS |
| Full local CTest evidence | Final exact-head full run plus focused retests after cmake --preset phase1 && cmake --build --preset phase1 | Full run passed 1708/1711; only cgb_corpus_report_tracer, cgb_corpus_report_controls and state_fuzz_controls failed on stale configure-time revision; all three passed in focused retest. This is combined evidence, not one 1711/1711 run. | ✓ PASS |
| Source archive controls | v02_source_archive_controls | Passed in 52.11 seconds. | ✓ PASS |
| Release candidate controls | bash tests/scripts/verify-release-candidate.sh --self-test | Passed against the same source tree. | ✓ PASS |
| Exact-head PR qualification | GitHub run 41334163805 at source head 39eb048e7770652b84a3fc5da7aaa3890adbd70c | Native Linux/macOS/Windows, CMake 3.25.3, sanitizer, acceptance, performance, required-native and macos-player-package passed. | ✓ PASS |
| Exact-head push qualification | GitHub run 41334157283 at the same head | Native, floor, sanitizer, acceptance, performance and required-native passed; trigger-specific macOS player/planning jobs skipped. | ✓ PASS |
| Installed/player consumer smoke | Preview run 41334163730 at the same head | Linux/macOS installed package smoke, downloaded macOS player receipt and aggregate passed. | ✓ PASS |

No single all-green local CTest run is claimed; all 1,711 tests have passing evidence across the full run and the three post-configure focused retests.

### Probe Execution

No Phase 20 plan or summary declares a probe, and no matching scripts/*/tests/probe-*.sh probe exists. The repository has a separate tests/scripts/probe-mooneye-candidate.sh, but Phase 20 does not reference it and it concerns the earlier candidate-protocol work, so it is not a Phase 20 probe.

### Requirements Coverage

| Requirement | Source plan | Description | Status | Evidence |
|---|---|---|---|---|
| RIGHTS-01 | 20-01 through 20-09 | Record exact rights/source/build/notices and exclude game ROMs from product packages while retaining root MIT. | PENDING | No fixture was admitted; current work proves byte identity and package boundaries, not legal permission or grant scope. REQUIREMENTS.md remains PENDING as directed. |

No additional Phase 20 requirement is orphaned from the plans.

### Test Quality Audit

| Test file | Linked requirement/behavior | Active | Skipped | Circular | Assertion level | Verdict |
|---|---|---:|---:|---:|---|---|
| tests/scripts/verify-fixture-admission.py | RIGHTS-01 admission and repository boundary | Yes | 0 | No | Behavioral/value: exact accept/reject decisions, digests and tokens | ✓ PASS |
| tests/scripts/verify-v02-source-archive.py | RIGHTS-01 source/product archive separation and metadata bounds | Yes | 0 | No | Behavioral/value: archive acceptance/rejection and exact reasons | ✓ PASS |
| tests/scripts/verify-phase3-player.sh | RIGHTS-01 actual player package policy | Yes | 0 | No | Behavioral: clean package plus staged/extracted mutation checks | ✓ PASS |
| .github/scripts/safe_extract_package.py and tests/scripts/verify-release-lifecycle.py | Downloaded product extraction, cleanup and retry | Yes | 0 | No | Behavioral: preflight, cleanup and same-destination retry | ✓ PASS |
| .github/scripts/verify-workflow-policy.py and tests/scripts/verify-workflow-policy-coverage.py | Trusted checker, workflow command wiring and path controls | Yes | 0 | No | Behavioral/value: isolated workflow mutations and expected outcomes | ✓ PASS |
| tests/scripts/verify-dense-input.py | Source-only mutant evidence boundary | Yes | 0 | No | Behavioral/value: independent evidence acceptance and fail-closed controls | ✓ PASS |
| tests/scripts/verify-v02-adoption.py | Source/product notice claims | Yes | 0 | No | Value: required and contradictory notice text controls | ✓ PASS |

Disabled-test scan found no skipped/pending tests in the linked files. Temporary files written by the controls are test subjects/receipts; expected decisions are independently specified or pinned, not generated by running the assertion target. No circular expected-value generation or insufficient assertion was found.

**Disabled tests on requirements:** 0
**Circular patterns detected:** 0
**Insufficient assertions:** 0

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---:|---|---|---|
| — | — | None | — | No unresolved TBD/FIXME/XXX, placeholder or empty implementation was found in changed implementation files. The small number of empty-list returns are explicit error/catch results; empty collection initializers are collectors populated along the checked paths, not product data stubs. |

### Decision Coverage

All 3 trackable decisions in 20-CONTEXT.md are honored by shipped artifacts.

### Human Verification Required

N/A — infrastructure/foundation phase with no user-facing elements. All acceptance criteria and state/cleanup invariants have automated evidence. RIGHTS-01 remains pending until a real candidate and source-grounded legal decision exist; no candidate is part of this phase.

### Gaps Summary

No phase-goal gaps found. Admission, actual-byte product checks, safe extraction, archive limits, workflow wiring, and their negative controls are present and exercised. RIGHTS-01 is deliberately still PENDING: no fixture was admitted, and this verification does not infer legal permission from hashes, populated fields or public availability.

---

_Verified: 2026-11-01T18:53:11Z_
_Verifier: the agent (gsd-verifier)_
