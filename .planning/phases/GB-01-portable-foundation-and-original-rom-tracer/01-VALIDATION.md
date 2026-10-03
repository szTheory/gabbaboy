---
phase: "01"
slug: "portable-foundation-and-original-rom-tracer"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-02"
---

# Phase 01 — Validation Strategy

> Phase validation contract with implementation evidence recorded below. The strategy remains unsigned until the phase-wide review resolves its remaining probe signals.

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
| BASE-01 | Offline configure/build/test/install after dependencies are prepared, including headless runner | integration | Schema-6 preset smoke and exact CMake 3.25.3 configure/build/test/install/relocation/consumer floor lane | ✅ | ✅ local and hosted; CMake floor passed in CI run `37131835427` |
| BASE-02 | Independent opaque instances, lifecycle, ownership, errors, and thread-use contract | unit/integration | 25-case CTest suite, including named lifecycle cases | ✅ | ✅ 25/25 local CTest and required native lanes |
| BASE-03 | Bounded parsing; malformed input leaves active state unchanged; unsupported cartridges fail explicitly | unit/security | Named loader boundary cases in the required CTest inventory | ✅ | ✅ local and required native lanes |
| BASE-04 | Guest RAM result protocol, bounded trace/time, unsupported execution, timeout and negative controls | integration | Named tracer cases in the required CTest inventory | ✅ | ✅ local and required native lanes |
| BASE-05 | Fixture source, rights, build recipe, applicability, protocol, timeout, digest, and regenerated-byte equality | reproducibility | Offline CMake `fixture_digest` plus pinned-RGBDS regeneration run | ✅ | ✅ fixture run `37131835525`, context `fixture-repro` |
| BASE-06 | Relocated installed package works from public headers in external C and C++ consumers | integration | Installed-runner and native C/C++ consumer smoke on Linux x64, macOS arm64, and Windows x64 | ✅ | ✅ required CI run `37131835427`; preview C/C++ consumers passed on Linux/macOS |
| BASE-07 | Explicit expected-test inventory, loader/lifecycle cases, and ASan/UBSan actually ran | CI contract | Exact-SHA `required-native` aggregate plus explicit test inventory | ✅ | ✅ run SHA `59b104e`, CI run `37131835427`, including Windows 25-case inventory and Linux ASan/UBSan |
| BASE-08 | Full install-tree package and smoke evidence identify tested source revision, digest, and retention limits | artifact smoke | Extracted Linux x64/macOS arm64 tar artifacts, installed runner/consumers, sidecar and API metadata | ✅ | ✅ preview run `37131835440`; exact artifact evidence below |

---

## Infrastructure Sequencing

- [x] Plan 01 Task 1 establishes the minimal portable C17 core/runner CMake targets and target-based tracer CTest before any later CMake build command.
- [x] `CMakePresets.json` uses schema version 6 with `phase1` and exact CMake 3.25.3 configure/build/test presets; the floor lane passed.
- [x] Plan 02 adds the public API and focused lifecycle, loader, and tracer test executables, reconfiguring after CMake input changes.
- [x] Original assembly, checked-in ROM bytes, rights notice, manifest, CMake-native offline `fixture_digest`, and isolated RGBDS regeneration comparison; no Node dependency.
- [x] Relocated external C and C++ consumer projects use only the installed public package.
- [x] Required native CI matrix, Linux ASan/UBSan lane, explicit expected-case inventory, and aggregate gate passed on the current evidence SHA.
- [x] Revision-linked Linux x64/macOS arm64 preview artifacts passed smoke and sidecar/API verification.

## Hosted Evidence (Run-Scoped Sample)

The public PR is [#1](https://github.com/szTheory/gabbaboy/pull/1). For this sample, the verifier recorded source SHA `59b104ef5ba95f7dd48e6dd3f4732f49f4cc77de` as equal to local `HEAD`, the PR `headRefOid`, and all three workflow run head SHAs. `gh pr checks --required` reported passing buckets for `required-native`, `fixture-repro`, and `preview-package-smoke`. The required branch-protection contexts were read back from GitHub and match those three names.

| Evidence | Run | Result |
|----------|-----|--------|
| Native CI | `37131835427` | Success: Linux x64, macOS arm64, Windows x64, Linux ASan/UBSan, CMake 3.25.3 floor, and `required-native` |
| Fixture reproduction | `37131835525` | Success: `fixture-repro` regenerated and matched the checked-in ROM |
| Preview packages | `37131835440` | Success: Linux x64 and macOS arm64 package smoke plus `preview-package-smoke` aggregate |

| Artifact | GitHub artifact digest | Package SHA-256 | API created at | API expires at | Sidecar retention |
|----------|------------------------|-----------------|----------------|----------------|-------------------|
| `preview-linux-x64` | `sha256:97b2b5f705d2e37601ab6a87ae43f057f6760363b7671e5bf08a84bed40dafad` | `23b65ad30aca49be9ab2b68976168ce03509a8c69bf42bb0ee0f28d4ef5a59a0` | `2026-10-03T15:03:47Z` | `2026-10-17T15:03:47Z` | 14 days |
| `preview-macos-arm64` | `sha256:ee0f0aa0c894b7f3d410c67eb7c1b2ecb9ecc300e93ea7c4297a9610132c9a98` | `b93c0c2601472ee6dae84b77920d27e790bde1a0f1235ef67c7b87ecf35efe0c` | `2026-10-03T15:03:55Z` | `2026-10-17T15:03:53Z` | 14 days |

The digest in GitHub's artifact API identifies the uploaded workflow artifact; the package SHA-256 identifies the `.tar.gz` inside it. The verifier downloaded and extracted both exact-run artifacts, ran the installed runner and external C/C++ consumers from the extracted package, and matched the package digest, source SHA, smoke marker, and configured retention against each sidecar. Artifacts are run-scoped, expire at the API timestamps above, and are not durable releases. There is no Windows preview download.

Remediation history is retained to make earlier hosted failures explicit. Run `37129638490` exposed a Windows `.exe` path assumption and missing sanitizer linker flags for extracted external consumers; the suffix forwarding and test-only sanitizer linker flags fixed those failures. Run `37131303838` still exposed one script-mode runner path using an unset CMake variable; it was changed to use the forwarded executable suffix. Run `37131494144` then passed Windows `preview_package_smoke` but found a CRLF mismatch in the expected test inventory; the verifier now normalizes CR at line endings. This sample supersedes those failed attempts; subsequent source revisions must be checked with the same verifier.

## Probe Disposition

Unresolved items remain `unresolved` and `flagged-unverified` until their named execution/test trigger produces evidence; task prose is not closure. The phase-level probe set retains BASE-01 concurrency, BASE-02 idempotency and concurrency, BASE-03/04/06/07 unclassified review signals, and BASE-08 concurrency. For BASE-05, the auto-probe's adjacency, empty-input and stable-order prompts describe collection semantics and do not apply to fixture provenance/digest; those three are explicitly dispositioned as not applicable, while BASE-05 retains one unclassified review signal until provenance and regeneration evidence exist. No signal is silently auto-dismissed.

---

## Manual-Only Verifications

No manual-only UAT is required. Authenticated remote access and hosted runners were available for the run-scoped evidence recorded above.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verification and meaningful adjacent `<fails_when>` behavior
- [ ] Sampling continuity: no 3 consecutive tasks without automated verification
- [ ] Plan 01 and Plan 02 sequencing covers initial and expanded test infrastructure
- [ ] No watch-mode flags
- [ ] Local CTest feedback latency under 30 seconds
- [ ] `nyquist_compliant: true` set only after implementation evidence exists

Nyquist compliance remains false and approval remains pending because several phase-level probe signals are still unclassified in the section above. Hosted BASE-07/BASE-08 evidence is complete for the recorded SHA; the phase-wide validation contract has not been signed off.

**Approval:** pending
