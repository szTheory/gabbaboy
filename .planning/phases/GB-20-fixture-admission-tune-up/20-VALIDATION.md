---
phase: "20"
slug: "fixture-admission-tune-up"
status: validated
nyquist_compliant: false
wave_0_complete: true
created: "2026-10-31"
---

# Phase 20 — Validation Strategy

> Feedback contract for the fixture admission and distribution boundary. All fixture/package decisions use exact bytes and pinned identities; hashes establish identity, not redistribution permission.

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
| 20-01-02 | 20-01 | 1 | RIGHTS-01 | T-20-01, T-20-03, T-20-04 | Existing approvals pass; incomplete component/use records, new unregistered evidence including additions in legacy subtrees, bad input and changed identity fail before consumption. | integration | `python3 -I tests/scripts/verify-fixture-admission.py --self-test && python3 -I tests/scripts/verify-fixture-admission.py --check-repository --repo-root . && python3 -I .github/scripts/verify-workflow-policy.py --self-test --group ci && python3 -I .github/scripts/verify-workflow-policy.py --self-test --group release_jobs` | New, Task 1 dependency | ✓ pass |
| 20-01-03 | 20-01 | 1 | RIGHTS-01 | T-20-02, T-20-03, T-20-04 | Both exact product policies accept clean synthetic trees and reject insertion, identity, notice/MIT/SDL/sidecar and documentation mutations. | unit | `python3 -I tests/scripts/verify-fixture-admission.py --self-test && python3 -I tests/scripts/verify-fixture-admission.py --self-test-packages --layout core && python3 -I tests/scripts/verify-fixture-admission.py --self-test-packages --layout player` | New, Task 1 dependency | ✓ pass |
| 20-02-01 | 20-02 | 2 | RIGHTS-01 | T-20-05, T-20-06, T-20-07 | Real install/archive/extraction and consumers pass exact policy; a renamed planted ROM fails before execution. | integration | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '^preview_package_smoke$'` | Existing target, extended | ✓ pass |
| 20-02-02 | 20-02 | 2 | RIGHTS-01 | T-20-05, T-20-06, T-20-07, T-20-08 | Every approved core subtree, renamed/suffixless insertion and missing/changed notice/MIT control fails in actual trees and parsed archives; source contract remains distinct. | integration | `python3 -I tests/scripts/verify-v02-source-archive.py --self-test && ctest --preset phase1 --output-on-failure --no-tests=error -R '^preview_package_smoke$'` | Existing, extended | ✓ pass |
| 20-02-03 | 20-02 | 2 | RIGHTS-01 | T-20-06, T-20-07, T-20-08 | Core new/reused/downloaded production paths apply actual-byte policy; missing/changed gabbaboy-notices.txt fails; separate source evidence retained. | integration | `bash tests/scripts/verify-release-candidate.sh --self-test && python3 -I tests/scripts/verify-v02-source-archive.py --self-test && python3 -I .github/scripts/verify-workflow-policy.py --self-test --group release_jobs` | Existing, extended | ✓ pass |
| 20-03-01 | 20-03 | 2 | RIGHTS-01 | T-20-09, T-20-10, T-20-11 | Real macOS stage/extracted player inventory and lifecycle pass; planted renamed payload fails before execution. | integration | `bash tests/scripts/verify-phase3-player.sh --build-package` | Existing, extended | ⚠ hosted macOS lane pending |
| 20-03-02 | 20-03 | 2 | RIGHTS-01 | T-20-09, T-20-10, T-20-11 | Real valid player prefix passes shell wrapper; suffixless/renamed/subtree and every missing/changed fixture/GabbaBoy/SDL notice case fail with intended reasons, without altering positive bytes. | integration | `python3 -I tests/scripts/verify-fixture-admission.py --self-test-packages --layout player && bash tests/scripts/verify-phase3-player.sh --self-test-package-policy build/phase3-player/package-stage/installed-prefix` | New mode; Task 1 produces prefix | ✓ pass |

Each PLAN task carries its concrete `<fails_when>` signal. All eight task behaviors have automated checks and negative controls; the only outstanding execution result is the existing hosted macOS player-package lane for 20-03-01. The local run produced the package stage and passed the policy/leak controls, but two pre-existing Cocoa menu tests could not initialize without a display service. Run the existing `macos-player-package` CI job at the exact final Phase 20 head before closing the phase. This is an automated environment limitation, not a human-verification item. The first tracer created its own synthetic verification path. No separate Wave 0 plan was added: missing scaffolds are part of Plan 20-01, before the two dependent package plans.

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

## Validation Sign-Off

- [x] Every plan task has an automated verify command or an explicit Wave 0 dependency.
- [x] Each package boundary has a clean positive control and meaningful mutation controls.
- [x] Wave 0 covers the missing admission and exact-inventory checks.
- [x] No watch-mode flags.
- [x] Focused self-test feedback latency is under 30 seconds (about 15 seconds in Plan 20-01).
- [ ] `nyquist_compliant: true` set in frontmatter after validation; awaiting the existing hosted macOS package lane.

**Approval:** partial; one automated package execution result remains pending.

## Execution Evidence

- **Coverage:** 8/8 plan tasks have automated checks; each package boundary has a clean positive and content-caused negative controls.
- **Passed execution evidence:** Plans 20-01 and 20-02 all task checks; Plan 20-03's policy wrapper, portable controls, and 21 real-tree mutation cases.
- **Pending execution evidence:** `20-03-01` full `--build-package` qualification in the existing `macos-player-package` CI lane. Local run stopped at `player_slot_menu_shortcuts` and its negative control because the host lacks a Cocoa display service; 106/108 local CTests passed. The stage policy and seeded ROM rejection were separately verified locally. This remains an automated-result gap until the existing lane passes at the exact final head; it is not a manual test.
- **Human judgment:** none for this phase. RIGHTS-01 remains pending because no fixture was admitted and automation does not determine legal grant scope.

The supplied spec-less edge remains explicitly unresolved/unclassified (RIGHTS-01; verification null) in Plan 20-01 must_haves. The two precision-filtered prohibition assumptions remain descriptor-less flagged-unverified. They do not invent manual UAT or legal clearance; see `20-SOURCE-AUDIT.md`.

## Validation Audit 2026-11-01

| Metric | Count |
|---|---|
| Gaps found | 1 |
| Resolved | 0 |
| Escalated | 1 |
