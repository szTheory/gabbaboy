---
phase: "01"
slug: "portable-foundation-and-original-rom-tracer"
status: validated
nyquist_compliant: true
wave_0_complete: false
created: "2026-10-02"
---

# Phase 01 — Validation Strategy

> Phase validation contract with implementation evidence recorded below. The 2026-10-09 audit classified the remaining probes, added reset/concurrency checks and runner usage recovery, and refreshed exact-head hosted evidence on PR #35.

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
| BASE-01 | Offline configure/build/test/install after dependencies are prepared, including headless runner; independent instances do not interfere when used on separate threads | integration | Schema-6 preset smoke, exact CMake 3.25.3 configure/build/test/install/relocation/consumer floor lane, and `concurrent_independent_instances` | ✅ | ✅ local test passed; exact-head PR #35 required-native run `37928170860` included the updated inventory |
| BASE-02 | Independent opaque instances, lifecycle, ownership, errors, thread-use contract, and repeatable reset behavior | unit/integration | Named lifecycle cases, including `reset_idempotency` and `concurrent_independent_instances` | ✅ | ✅ both added behavioral cases passed locally and in exact-head PR #35 native CI run `37928170860` |
| BASE-03 | Bounded parsing; malformed input leaves active state unchanged; unsupported cartridges fail explicitly | unit/security | Named loader boundary cases in the required CTest inventory | ✅ | ✅ local and required native lanes, including the 64 KiB declared-size rejection regression |
| BASE-04 | Guest RAM result protocol, bounded trace/time, unsupported execution, timeout and negative controls | integration | Named tracer cases in the required CTest inventory | ✅ | ✅ local and required native lanes |
| BASE-05 | Fixture source, rights, build recipe, applicability, protocol, timeout, digest, and regenerated-byte equality | reproducibility | Offline CMake `fixture_digest` plus pinned-RGBDS regeneration run | ✅ | ✅ fixture run `37141965338`, context `fixture-repro` |
| BASE-06 | Relocated installed package works from public headers in external C and C++ consumers | integration | Installed-runner and native C/C++ consumer smoke on Linux x64, macOS arm64, and Windows x64 | ✅ | ✅ required CI run `37141965336`; preview C/C++ consumers passed on Linux/macOS |
| BASE-07 | Explicit expected-test inventory, loader/lifecycle cases, and ASan/UBSan actually ran | CI contract | Exact-SHA `required-native` aggregate plus explicit test inventory, including the new reset, concurrency, and runner-help cases | ✅ | ✅ PR #35 exact-head run `37928170860`: Linux, macOS, Windows, ASan/UBSan, CMake floor, and `required-native` passed |
| BASE-08 | Full install-tree package and smoke evidence identify tested source revision, digest, and retention limits | artifact smoke | Extracted Linux x64/macOS arm64 tar artifacts, installed runner/consumers, sidecar and API metadata | ✅ | ✅ PR #35 exact-head preview run `37928170973`; both package smokes, API metadata, downloaded bytes, sidecars, and safe extraction passed |

---

## Infrastructure Sequencing

- [x] Plan 01 Task 1 establishes the minimal portable C17 core/runner CMake targets and target-based tracer CTest before any later CMake build command.
- [x] `CMakePresets.json` uses schema version 6 with `phase1` and exact CMake 3.25.3 configure/build/test presets; the floor lane passed.
- [x] Plan 02 adds the public API and focused lifecycle, loader, and tracer test executables, reconfiguring after CMake input changes.
- [x] Original assembly, checked-in ROM bytes, rights notice, manifest, CMake-native offline `fixture_digest`, and isolated RGBDS regeneration comparison; no Node dependency.
- [x] Relocated external C and C++ consumer projects use only the installed public package.
- [x] Required native CI matrix, Linux ASan/UBSan lane, explicit expected-case inventory, and aggregate gate passed on exact PR #35 head `d1e5fdb3b23256f06694cd8d91613638612bccb8`.
- [x] Revision-linked Linux x64/macOS arm64 preview artifacts passed smoke and sidecar/API verification on that same SHA.

## Hosted Evidence (Run-Scoped Sample)

The public PR is [#1](https://github.com/szTheory/gabbaboy/pull/1). For this implementation sample, the verifier recorded source SHA `8396096ad17500974b30657af91fd2ef9ad51237` as equal to local `HEAD`, the PR `headRefOid`, and all three workflow run head SHAs. `gh pr checks --required` reported passing buckets for `required-native`, `fixture-repro`, and `preview-package-smoke`. The required branch-protection contexts were read back from GitHub and match those three names.

| Evidence | Run | Result |
|----------|-----|--------|
| Native CI | `37141965336` | Success: Linux x64, macOS arm64, Windows x64, Linux ASan/UBSan, CMake 3.25.3 floor, and `required-native` |
| Fixture reproduction | `37141965338` | Success: `fixture-repro` regenerated and matched the checked-in ROM |
| Preview packages | `37141965332` | Success: Linux x64 and macOS arm64 package smoke plus `preview-package-smoke` aggregate |

| Artifact | GitHub artifact digest | Package SHA-256 | API created at | API expires at | Sidecar retention |
|----------|------------------------|-----------------|----------------|----------------|-------------------|
| `preview-linux-x64` | `sha256:b2e3d57aa5cc8527bd05c2ee11d8e006495dd30193b38a08e828e11e60bd092b` | `045c5c063c48f5e125452f7053f670a75474059fa2e26e84dd365f88994a2726` | `2026-10-03T17:51:15Z` | `2026-10-17T17:51:14Z` | 14 days |
| `preview-macos-arm64` | `sha256:d95990eab682cae084a5992777167a5fc6c71011eafa2326d8b74a5311499097` | `62462139dc88d4228b29cf2ea47d26176f3047dfc968a11f870d1a1f1143aef3` | `2026-10-03T17:51:19Z` | `2026-10-17T17:51:18Z` | 14 days |

The digest in GitHub's artifact API identifies the uploaded workflow artifact; the package SHA-256 identifies the `.tar.gz` inside it. The verifier downloaded and extracted both exact-run artifacts, ran the installed runner and external C/C++ consumers from the extracted package, and matched the package digest, source SHA, smoke marker, and configured retention against each sidecar. Artifacts are run-scoped, expire at the API timestamps above, and are not durable releases. There is no Windows preview download.

### Phase 1 validation refresh — PR #35

PR #35's exact head `d1e5fdb3b23256f06694cd8d91613638612bccb8` passed the three required branch-protection contexts: `required-native`, `fixture-repro`, and `preview-package-smoke`. The native CI run passed Linux x64, macOS arm64, Windows x64, Linux ASan/UBSan, the CMake 3.25.3 floor, and the required aggregate. Fixture reproduction passed both its original and candidate checks. Both installed-package smoke jobs and the preview aggregate passed. PR #35 was squash-merged as `96f76dec9a675ede45da8d75bd72a5141c7419e4`; the evidence below remains tied to the tested PR head, not the later merge commit.

| Evidence | Exact PR-head run | Result |
|----------|-------------------|--------|
| Native CI | [37928170860](https://github.com/szTheory/gabbaboy/actions/runs/37928170860) | Success: Linux, macOS, Windows, ASan/UBSan, CMake floor, and `required-native` |
| Fixture reproduction | [37928170722](https://github.com/szTheory/gabbaboy/actions/runs/37928170722) | Success: original fixture reproduction and candidate byte checks |
| Preview packages | [37928170973](https://github.com/szTheory/gabbaboy/actions/runs/37928170973) | Success: Linux x64 and macOS arm64 installed-package smoke plus `preview-package-smoke` |

| Artifact | GitHub artifact digest | Package SHA-256 | API created at | API expires at | Retention |
|----------|------------------------|-----------------|----------------|----------------|-----------|
| `preview-linux-x64` | `sha256:3bd03898f2914ed8e63c984a6f51aed3e16eee3ceba298499ecf5f01bec38a1e` | `954c54826088b230ca3d8c359b47f843eb229e64ca2d74b3ce2be6897a94b533` | `2026-10-09T12:10:42Z` | `2026-10-23T12:10:41Z` | 14 days |
| `preview-macos-arm64` | `sha256:1a6e7de83eeeb3198adf47fe370fb80e7186ff15c9e97df38f2c369803280546` | `05c92c7e2ff33672222a87c04099321ec1745803ca4fd2b5fcead7586c1f6d3c` | `2026-10-09T12:10:36Z` | `2026-10-23T12:10:35Z` | 14 days |

The recorded run head SHA and every downloaded sidecar source SHA matched PR #35's tested head. `VerifyArtifactSidecar.cmake` verified each archive digest, passed smoke marker, and 14-day configured retention; `safe_extract_package.py` passed its adversarial self-test and safely extracted both archives. The open-PR-only wrapper was not rerun after PR #35 merged; these same exact-run checks were executed directly against its recorded run IDs after merge.

Remediation history is retained to make earlier hosted failures explicit. Run `37129638490` exposed a Windows `.exe` path assumption and missing sanitizer linker flags for extracted external consumers; the suffix forwarding and test-only sanitizer linker flags fixed those failures. Run `37131303838` still exposed one script-mode runner path using an unset CMake variable; it was changed to use the forwarded executable suffix. Run `37131494144` then passed Windows `preview_package_smoke` but found a CRLF mismatch in the expected test inventory; the verifier now normalizes CR at line endings. This sample supersedes those failed attempts; subsequent source revisions must be checked with the same verifier.

## Probe Disposition

The 2026-10-09 Nyquist audit resolved the phase-level probe set. `concurrent_independent_instances` exercises two independently loaded core instances from separate threads with distinct guest results; `reset_idempotency` checks repeated reset and deterministic post-reset output. `runner_help` checks recovery guidance for CLI users. The three added cases passed, and the full local suite passed 179/179.

- BASE-03 and BASE-04's generic prompts map to existing loader boundary/non-destructive tests and tracer success/failure/unsupported/timeout/trace controls; targeted selection passed 24/24.
- BASE-05's provenance/regeneration evidence is fixture-level, so adjacency, empty-input, and stable-order collection prompts do not apply to fixture identity.
- BASE-06 is installed-package behavior; the existing `preview_package_smoke` passed 1/1.
- BASE-07 and BASE-08 are automated hosted inventory, sanitizer, and package-evidence gates rather than additional guest behavior tests. Their exact PR #35 head results and artifact records are listed above; these gates are automated, not manual-only checks.

All phase task behaviors map to automated checks. BASE-07 and BASE-08 now have exact tested-PR-SHA hosted evidence; neither depends on manual UAT.

---

## Manual-Only Verifications

No manual-only UAT is required. Authenticated remote access and hosted runners were available for the run-scoped evidence recorded above.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verification and meaningful adjacent `<fails_when>` behavior
- [x] Sampling continuity: no 3 consecutive tasks without automated verification
- [x] Plan 01 and Plan 02 sequencing covers initial and expanded test infrastructure
- [x] No watch-mode flags
- [x] Local CTest feedback latency under 30 seconds
- [x] `nyquist_compliant: true` set only after implementation evidence exists

Nyquist compliance is validated based on the automated coverage map, passing local suite, and exact PR #35 hosted evidence above. Goal-backward verification remains the final phase gate.

**Approval:** validated by automated evidence

## Validation Audit 2026-10-09

| Metric | Count |
|---|---|
| Gaps found | 8 |
| Resolved | 8 |
| Escalated | 0 |

## Validation Audit 2026-10-09

| Metric | Count |
|---|---|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
