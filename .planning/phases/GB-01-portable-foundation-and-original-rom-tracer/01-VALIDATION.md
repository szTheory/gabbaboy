---
phase: "01"
slug: "portable-foundation-and-original-rom-tracer"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-02"
---

# Phase 01 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution. This is a plan, not evidence that implementation or tests exist.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | CTest with small C test executables; no third-party runtime test framework |
| **Config file** | `CMakeLists.txt`, schema-6 `CMakePresets.json`, and target-based CTest registration created in Plan 01 Task 1; expanded in Plan 02 |
| **Quick run command** | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` |
| **Full suite command** | CTest plus installed C/C++ consumer, ASan/UBSan, fixture regeneration, and artifact-smoke jobs in required CI |
| **Estimated runtime** | Local CTest target: under 30 seconds; hosted multi-platform jobs are reported individually |

---

## Sampling Rate

- **After every task commit:** Reconfigure through `cmake --preset phase1` when CMake inputs change, then run the targeted CTest cases named by the task.
- **After every plan wave:** Run `ctest --test-dir build --output-on-failure` and the affected installed-consumer or fixture checks.
- **Before `$gsd-verify-work`:** Required CI must pass on the exact phase revision; skipped or missing mandatory jobs are not passes.
- **Max feedback latency:** 30 seconds for the local CTest set; CI lane timings are recorded separately.

---

## Per-Requirement Verification Map

| Requirement | Secure behavior / evidence | Test Type | Automated Command or Gate | File Exists | Status |
|-------------|----------------------------|-----------|---------------------------|-------------|--------|
| BASE-01 | Offline configure/build/test/install after dependencies are prepared, including headless runner | integration | Schema-6 preset smoke in Plan 01, then exact CMake 3.25.3 configure/build/test/install/relocation/consumer floor lane in Plan 04 | ❌ Plan 01 / Plan 04 | ⬜ pending |
| BASE-02 | Independent opaque instances, lifecycle, ownership, errors, and thread-use contract | unit/integration | `ctest --test-dir build --output-on-failure` with named lifecycle cases | ❌ Plan 02 | ⬜ pending |
| BASE-03 | Bounded parsing; malformed input leaves active state unchanged; unsupported cartridges fail explicitly | unit/security | `ctest --test-dir build --output-on-failure` with named loader boundary cases | ❌ Plan 02 | ⬜ pending |
| BASE-04 | Guest RAM result protocol, bounded trace/time, unsupported execution, timeout and negative controls | integration | `ctest --test-dir build --output-on-failure` with named tracer cases | ❌ Plan 01 / Plan 02 | ⬜ pending |
| BASE-05 | Fixture source, rights, build recipe, applicability, protocol, timeout, digest, and regenerated-byte equality | reproducibility | Offline CMake `fixture_digest` case plus isolated pinned-RGBDS regenerate-and-compare CI job | ❌ Plan 01 Task 2 | ⬜ pending |
| BASE-06 | Relocated installed package works from public headers in external C and C++ consumers | integration | Installed-runner and native C/C++ consumer smoke jobs on Linux x64, macOS arm64, and Windows x64 | ❌ Plan 03 | ⬜ pending |
| BASE-07 | Explicit expected-test inventory, loader/lifecycle cases, and ASan/UBSan actually ran | CI contract | Required aggregate CI job fails on missing cases, failed jobs, or timeouts | ❌ Plan 04 | ⬜ pending |
| BASE-08 | Full install-tree package and smoke evidence identify tested source revision, digest, and retention limits | artifact smoke | Extract the exact Linux x64/macOS arm64 tar artifact, run installed runner and consumers, and verify metadata | ❌ Plan 05 | ⬜ pending |

---

## Infrastructure Sequencing

- [ ] Plan 01 Task 1 establishes the minimal portable C17 core/runner CMake targets and target-based tracer CTest before any later CMake build command.
- [ ] `CMakePresets.json` uses schema version 6 with `phase1` and exact CMake 3.25.3 configure/build/test presets; support remains unclaimed until the Plan 04 floor lane passes.
- [ ] Plan 02 adds the public API and focused lifecycle, loader, and tracer test executables, reconfiguring after CMake input changes.
- [ ] Original assembly, checked-in ROM bytes, rights notice, manifest, CMake-native offline `fixture_digest`, and isolated RGBDS regeneration comparison; no Node dependency.
- [ ] Relocated external C and C++ consumer projects using only the installed public package.
- [ ] Required native CI matrix, Linux ASan/UBSan lane, explicit expected-case inventory, and aggregate gate.
- [ ] Revision-linked Linux x64/macOS arm64 preview artifacts with digest and installed-package smoke evidence.

## Probe Disposition

Unresolved items remain `unresolved` and `flagged-unverified` until their named execution/test trigger produces evidence; task prose is not closure. The phase-level probe set retains BASE-01 concurrency, BASE-02 idempotency and concurrency, BASE-03/04/06/07 unclassified review signals, and BASE-08 concurrency. For BASE-05, the auto-probe's adjacency, empty-input and stable-order prompts describe collection semantics and do not apply to fixture provenance/digest; those three are explicitly dispositioned as not applicable, while BASE-05 retains one unclassified review signal until provenance and regeneration evidence exist. No signal is silently auto-dismissed.

---

## Manual-Only Verifications

All Phase 1 behaviors have automated verification. No manual-only UAT is required. Missing remote, credentials, or hosted runner access must be recorded as a real evidence limitation; it cannot be converted into a passing CI result.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verification and meaningful adjacent `<fails_when>` behavior
- [ ] Sampling continuity: no 3 consecutive tasks without automated verification
- [ ] Plan 01 and Plan 02 sequencing covers initial and expanded test infrastructure
- [ ] No watch-mode flags
- [ ] Local CTest feedback latency under 30 seconds
- [ ] `nyquist_compliant: true` set only after implementation evidence exists

**Approval:** pending
