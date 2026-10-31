---
phase: "20"
slug: "fixture-admission-tune-up"
status: draft
nyquist_compliant: false
wave_0_complete: false
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
| 20-01-01 | 20-01 | 1 | RIGHTS-01 | T-20-01 | A complete synthetic admission record passes; missing/ambiguous component terms, unresolved scope, stale identities, malformed/duplicate keys, and coordinated fixture+manifest+notice replacement against the unchanged immutable baseline fail. This validates record structure and identity, not legal coverage. | unit | `python3 -I tests/scripts/verify-fixture-admission.py --self-test` | ❌ Wave 0 | ⬜ pending |
| 20-02-01 | 20-02 | 2 | RIGHTS-01 | T-20-02, T-20-03 | The actual staged install and extracted core product match the exact path/digest inventory and retain package-specific fixture notices, the core notice sidecar, and root MIT bytes. Renamed, suffixless, and in-directory controlled payloads plus missing/changed notices or MIT bytes fail. | integration | `ctest --preset phase1 --output-on-failure -R '^preview_package_smoke$'` | ⚠️ Existing target; coverage partial | ⬜ pending |
| 20-02-02 | 20-02 | 2 | RIGHTS-01 | T-20-02, T-20-03 | The actual core release archive matches the exact product inventory; source archives retain their separate fixture policy. | integration | `python3 -I tests/scripts/verify-v02-source-archive.py --check-product-archive build/gabbaboy-core-linux-x64.tar.gz --repo-root .` (release-rehearsal artifact) | ⚠️ Existing checker; exact inventory partial | ⬜ pending |
| 20-03-01 | 20-03 | 2 | RIGHTS-01 | T-20-04 | The actual macOS player package contains only the approved smoke-fixture identities and required GabbaBoy/SDL notices; renamed, suffixless, or in-subtree controlled payloads and missing/changed notices fail. | integration | `bash tests/scripts/verify-phase3-player.sh --build-package` | ⚠️ Existing check; exact inventory partial | ⬜ pending |

---

## Wave 0 Requirements

- [ ] Add a focused Python standard-library admission validator/self-test under `tests/scripts/` and register it in CTest.
- [ ] Pin approved fixture identities independently from the mutable manifest/notice values and prove a coordinated mutation is rejected.
- [ ] Extend existing package checks to compare actual staged and extracted bytes against exact path/digest inventories, with positive and negative controls.
- [ ] Keep source archive policy separate from installed/core release/player binary products.
- [ ] Provide one package-path policy from Wave 1 for the core and player checks in Wave 2, without duplicating fixture rights metadata.

---

## Manual-Only Verifications

There is no manual UAT for Phase 20. A future candidate's rights scope still requires a source-grounded maintainer decision before it is marked admitted; Phase 20 does not select or admit a candidate, and automated checks must not represent hashes or populated fields as legal clearance.

---

## Validation Sign-Off

- [ ] Every plan task has an automated verify command or an explicit Wave 0 dependency.
- [ ] Each package boundary has a clean positive control and meaningful mutation controls.
- [ ] Wave 0 covers the missing admission and exact-inventory checks.
- [ ] No watch-mode flags.
- [ ] Focused self-test feedback latency is under 30 seconds.
- [ ] `nyquist_compliant: true` set in frontmatter after validation.

**Approval:** pending
