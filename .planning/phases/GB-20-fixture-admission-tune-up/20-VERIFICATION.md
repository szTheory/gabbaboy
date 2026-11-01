---
phase: GB-20-fixture-admission-tune-up
verified: 2026-11-01T14:12:14Z
status: pending_external_gate
score: 8/9
implementation_head: 7293eb47a6c799b6455dd854533aca932f4529ad
covered_files:
  - .github/scripts/release-evidence-lifecycle.sh
  - .github/scripts/safe_extract_package.py
  - .github/scripts/verify-workflow-policy.py
  - .github/workflows/ci.yml
  - .github/workflows/release.yml
  - cmake/FixtureAdmissionPolicy.json
  - tests/scripts/verify-fixture-admission.py
  - tests/scripts/verify-v02-source-archive.py
  - tests/scripts/verify-release-candidate.sh
  - tests/scripts/verify-workflow-policy-coverage.py
  - tests/scripts/verify-dense-input.py
---

# Phase 20 — Verification

## Result

Local verification is green at implementation head `7293eb47a6c799b6455dd854533aca932f4529ad`. Eight of nine outcomes are verified. The remaining gate is the hosted `macos-player-package` workflow on the final PR head. Phase 20 stays open until that exact revision passes.

## Goal-Backward Checks

| # | Outcome | Status | Evidence |
|---|---|---|---|
| 1 | Fixture admission uses full immutable identities, bounded input handling, pinned notice/product policy, exact path inventory, and meaningful negative controls. | VERIFIED | `fixture_admission_controls`, `fixture_admission_repository`, both core/player product-control groups, and their self-tests passed in the final full CTest run. |
| 2 | Installed, extracted, and released core packages enforce actual bytes, paths, inventory, root MIT, and named notice sidecar requirements. | VERIFIED | `preview_package_smoke`, `installed_runner_smoke`, source-archive controls, and final release-candidate replay passed. |
| 3 | Player package staging and extracted-byte policy reject fixture payloads and notice mutations before execution. | VERIFIED LOCALLY; HOSTED GATE PENDING | The production player policy and 21 isolated mutation controls pass locally. Exact-head `macos-player-package` CI remains required to qualify the complete Cocoa package path. |
| 4 | Filesystem/Git enumeration and Git blob reads remain bounded and clean up child processes on overflow or timeout. | VERIFIED | Fixture admission/repository controls and self-tests passed, including over-limit and stalled-child cleanup cases. |
| 5 | Source/core archive parsing bounds hidden metadata and extension counts before payload parsing, and the counter resets per inspection. | VERIFIED | `v02_source_archive_controls` and release-candidate replay passed; the 256-long-path positive is inspected twice under an exact observed-count cap at `7293eb47`. |
| 6 | Trusted release publisher validates downloaded macOS and Windows archives before draft validation and contains/cleans hostile extraction paths. | VERIFIED | `workflow_policy_group_release_jobs`, workflow source/AST coverage tests, and release lifecycle replay passed with archive substitution and cleanup negatives. |
| 7 | Repository-admission workflow gates cannot be removed or redirected without rejection. | VERIFIED | Exact-command workflow controls, independent source coverage, and coverage mutation controls passed in the final full suite. |
| 8 | The dense-input mutant path has separate immutable baseline evidence and preserves unqualified-build behavior. | VERIFIED | `acceptance_dense_input_controls` and related planning/build checks passed in the final full suite. |
| 9 | Every phase plan has an automated deliverable check, all plans fit the approved cap, and release/archive behavior has final regression evidence. | VERIFIED LOCALLY | `plan_cap`, planning hygiene, live-summary coverage, all 1,711 CTests, and `verify-release-candidate.sh --self-test` passed. The hosted platform lane remains separately pending. |

## Verification Evidence

- `cmake --preset phase1` and `cmake --build --preset phase1` passed at the implementation head.
- The final full CTest run passed 1,711/1,711 tests.
- `bash tests/scripts/verify-release-candidate.sh --self-test` passed, including archive/product acceptance and receipt identity, digest tamper, draft/proof, fixture-leak, source-archive, and substitution rejection controls.
- The final ASVS L1 audit reports 29/29 authored threat entries closed across nine plan registers, with no open high-or-higher authored threat.
- Review findings CR-05/08/09, the archive metadata/cleanup finding, the Windows path finding, and TAR warning WR-01 have closure evidence. The final archive/path review is clean.
- The generated `20-UAT.md` is checked by the shared closure helper; no manual UAT item is required.

## Requirement Coverage

| Requirement | Status | Evidence |
|---|---|---|
| RIGHTS-01 | PENDING | No fixture candidate was admitted. The repository now enforces the structural, identity, notice, and product-distribution boundary, but automated checks do not determine redistribution permission or legal grant scope. |

The pending rights decision is recorded without claiming that checksums or populated records constitute legal clearance. It does not change the separate hosted macOS release gate.

## Human Verification

None. Phase 20 has no manual UAT. The remaining qualification is an automated hosted CI check.
