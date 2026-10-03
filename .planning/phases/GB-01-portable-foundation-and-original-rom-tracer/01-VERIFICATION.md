---
phase: "GB-01-portable-foundation-and-original-rom-tracer"
verified: "2026-10-03T16:11:44Z"
status: passed
score: "8/8 must-haves verified"
covered_files:
  - .github/scripts/verify-cmake-floor.sh
  - .github/scripts/verify-pr-evidence.sh
  - .github/scripts/verify-test-inventory.sh
  - .github/workflows/ci.yml
  - .github/workflows/fixture-repro.yml
  - .github/workflows/preview.yml
  - .gitignore
  - .planning/phases/GB-01-portable-foundation-and-original-rom-tracer/01-01-PLAN.md
  - .planning/phases/GB-01-portable-foundation-and-original-rom-tracer/01-01-SUMMARY.md
  - .planning/phases/GB-01-portable-foundation-and-original-rom-tracer/01-02-PLAN.md
  - .planning/phases/GB-01-portable-foundation-and-original-rom-tracer/01-02-SUMMARY.md
  - .planning/phases/GB-01-portable-foundation-and-original-rom-tracer/01-03-PLAN.md
  - .planning/phases/GB-01-portable-foundation-and-original-rom-tracer/01-03-SUMMARY.md
  - .planning/phases/GB-01-portable-foundation-and-original-rom-tracer/01-04-PLAN.md
  - .planning/phases/GB-01-portable-foundation-and-original-rom-tracer/01-04-SUMMARY.md
  - .planning/phases/GB-01-portable-foundation-and-original-rom-tracer/01-05-PLAN.md
  - .planning/phases/GB-01-portable-foundation-and-original-rom-tracer/01-05-SUMMARY.md
  - .planning/phases/GB-01-portable-foundation-and-original-rom-tracer/GB-01-01-SUMMARY.md
  - .planning/phases/GB-01-portable-foundation-and-original-rom-tracer/GB-01-02-SUMMARY.md
  - CMakeLists.txt
  - CMakePresets.json
  - README.md
  - cmake/ExpectedTests.cmake
  - cmake/GabbaBoyConfig.cmake.in
  - cmake/PreviewPackageSmoke.cmake
  - cmake/RunInstalledConsumer.cmake
  - cmake/VerifyArtifactSidecar.cmake
  - cmake/VerifyFixture.cmake
  - cmake/VerifyInstalledPackage.cmake
  - fixtures/tracer/LICENSE.txt
  - fixtures/tracer/manifest.json
  - fixtures/tracer/tracer.asm
  - fixtures/tracer/tracer.gb
  - include/gabbaboy/gabbaboy.h
  - src/core/gabbaboy.c
  - src/runner/main.c
  - tests/CMakeLists.txt
  - tests/consumers/c/CMakeLists.txt
  - tests/consumers/c/main.c
  - tests/consumers/cpp/CMakeLists.txt
  - tests/consumers/cpp/main.cpp
  - tests/expected-tests.txt
  - tests/test_api.c
  - tests/test_loader.c
  - tests/test_tracer.c
covered_digest: "v2:sha256:bc7d8d646cd4a718bdaf5e04493ae4c92df0869b77931d296ccb73ef4474ad97"
behavior_unverified: 0
overrides_applied: 0
decision_coverage:
  honored: 11
  total: 11
  not_honored: []
human_verification: []
deferred:
  - truth: "Hardware-qualified address-space behavior, including cartridge RAM availability, is outside the fixture-only tracer model."
    addressed_in: "Phase 2 — DMG CPU, Bus, and Time"
    evidence: "Phase 2 roadmap success criteria require memory mapping to match declared DMG evidence at observable access boundaries."
---

# Phase 1: Portable Foundation and Original ROM Tracer Verification Report

**Phase Goal:** As a developer, I want to run an original ROM with an installable GB core via a bounded API, so that I can embed it.
**Verified:** 2026-10-03T16:11:44Z
**Status:** passed
**Revision:** 97d73a7cfadb8b90edea2e406566ff0a254c4865
**Re-verification:** No — initial verification

## User Flow Coverage

User story: “As a developer, I want to run an original ROM with an installable GB core via a bounded API, so that I can embed it.” The runtime story validator returned valid: true.

| Step | Expected | Evidence | Status |
|---|---|---|---|
| Prepare and configure | Developer prepares CMake, Ninja, and a C17 compiler, then configures the headless core. | README prerequisites and cmake --preset phase1; schema-6 preset has a CMake 3.25 floor. | ✓ |
| Build and install | Build produces an installable core and runner without SDL or a network fetch in the ordinary flow. | CMake uses C17 and GabbaBoy::core; exact-revision Linux, macOS, Windows, and CMake 3.25.3 jobs passed build/install steps. | ✓ |
| Embed | External C and C++ projects use the installed public header and GabbaBoy::core. | Relocated consumers use find_package; exact-revision installed-package smoke passed for both extracted Linux/macOS packages and native consumers across three CI platforms. | ✓ |
| Run the original ROM | Guest reaches its declared success state and produces bounded trace output. | Local runner reported outcome=pass, half_dots=200000, trace_records=8337; two invocations produced identical output. Exact-revision package smoke passed. | ✓ |
| Reach the outcome | Developer can embed and inspect real guest execution through the API. | C and C++ consumers call create/load/run/peek/destroy and assert the guest marker and trace count; both ran against extracted packages. | ✓ |

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | Developers can configure, build, test, and install the dependency-prepared C17 core/runner using documented CMake/Ninja/CTest commands without SDL or network access in the ordinary flow. | ✓ VERIFIED | [README.md](../../../README.md) documents prerequisites and commands. [CMakePresets.json](../../../CMakePresets.json) defines schema-6 presets; [CMakeLists.txt](../../../CMakeLists.txt) declares C17 targets and installs the namespaced export. Exact-SHA floor and native jobs passed. |
| 2 | External C and C++ consumers can link relocated installed GabbaBoy::core using only the public include and execute the tracer. | ✓ VERIFIED | Consumer projects include the installed public header, use find_package and link GabbaBoy::core. Exact-SHA preview smoke extracted the archive and ran both consumers; native CI consumer steps passed on three platforms. |
| 3 | Opaque instances can be created, reset, run, and destroyed independently under documented ownership, lifetime, model, thread, and error rules. | ✓ VERIFIED | [gabbaboy.h](../../../include/gabbaboy/gabbaboy.h) documents the contract; [gabbaboy.c](../../../src/core/gabbaboy.c) stores mutable state per instance with no shared mutable globals. Named instance_lifecycle and independent_instances checks exited 0. |
| 4 | Malformed, excessive, or unsupported ROM inputs return bounded errors, and a failed replacement leaves the prior machine state usable. | ✓ VERIFIED | Header parsing checks null, length, 8 MiB cap, cartridge/RAM type, size code, exact declared length, and checksum before allocation or mutation. Named loader_non_destructive exited 0; exact-SHA required inventory passed. |
| 5 | The original fixture executes its declared opcode subset through the implemented decoder and bus path, exposes distinct success/failure states, and returns bounded time/trace results with unsupported execution explicit. | ✓ VERIFIED | decode/execute and read8/write8 in [gabbaboy.c](../../../src/core/gabbaboy.c) drive guest bytes; [main.c](../../../src/runner/main.c) consumes the structured result and marker. Runner returned the pass trace; tracer_success, run_bounds, trace_capacity, and exact-SHA negative-control cases passed. |
| 6 | The admitted fixture has reproducible source, build recipe, digest, rights, applicability, protocol, and timeout evidence. | ✓ VERIFIED | [manifest.json](../../../fixtures/tracer/manifest.json), [tracer.asm](../../../fixtures/tracer/tracer.asm), and [LICENSE.txt](../../../fixtures/tracer/LICENSE.txt) provide those fields. Local fixture_digest is registered; exact-SHA fixture-repro run 37134846450 regenerated and byte-compared the ROM. |
| 7 | Required CI fails closed when jobs, fixtures, cases, or sanitizer evidence are missing, skipped, failed, or timed out. | ✓ VERIFIED | [ci.yml](../../../.github/workflows/ci.yml), [verify-test-inventory.sh](../../../.github/scripts/verify-test-inventory.sh), [ExpectedTests.cmake](../../../cmake/ExpectedTests.cmake), and [expected-tests.txt](../../../tests/expected-tests.txt) wire an exact inventory and required aggregate. Exact-SHA run 37134846449 passed Linux, macOS, Windows, ASan/UBSan, CMake 3.25.3, and required-native; inventory and sanitizer steps were successful. |
| 8 | The PR flow produces a revision-linked, installed-smoke-qualified preview with verifiable metadata and expiry. | ✓ VERIFIED | PR #1 head, local HEAD, workflow head SHAs, and artifact sidecars matched 97d73a7cfadb8b90edea2e406566ff0a254c4865. Strict main protection requires required-native, fixture-repro, and preview-package-smoke. Exact-evidence script passed on downloaded/extracted packages and artifact API metadata. |

**Score:** 8/8 truths verified; behavior-unverified: 0.

### Deferred Items

| Item | Addressed In | Evidence |
|---|---|---|
| Hardware-qualified address-space behavior, including cartridge RAM availability, remains outside this fixture-only tracer contract. The current fixture declares ROM-only/no cartridge RAM but uses an emulator-owned 8 KiB backing window at 0xA000; its pass marker is not hardware-conformance evidence. | Phase 2 — DMG CPU, Bus, and Time | Phase 2 roadmap criterion requires memory mapping to match declared DMG evidence. [Pan Docs memory map](https://gbdev.io/pandocs/Memory_Map.html) identifies 0xA000–0xBFFF as cartridge external RAM when present; [Pan Docs No MBC](https://gbdev.io/pandocs/nombc.html) describes the ROM-only mapping and optional discrete RAM. The manifest excludes hardware conformance. |

This limitation does not invalidate Phase 1’s narrower architectural proof: the authored ROM bytes execute through the core’s decoder and bus functions, and package/API boundaries work. Do not describe this as a playable emulator or a hardware-backed result.

### Required Artifacts

The runtime artifact query reported 23/23 plan artifacts present and substantive. I also inspected their implementations and traced the consumers.

| Artifact | Expected | Status | Details |
|---|---|---|---|
| CMakePresets.json | Schema-6 build/test and sanitizer presets | ✓ VERIFIED | CMake 3.25 minimum, Ninja presets, installed and sanitizer flows. |
| include/gabbaboy/gabbaboy.h | Public bounded opaque-instance API | ✓ VERIFIED | Public types, ownership, thread, time, trace, and error contract. |
| src/core/gabbaboy.c | Profile, ROM loader, state, decoder, bus, execution | ✓ VERIFIED | Substantive per-instance implementation; not a full CPU or hardware map. |
| src/runner/main.c | Bounded headless fixture runner | ✓ VERIFIED | Reads bounded input, calls public API, reports guest outcome and trace. |
| fixtures/tracer/manifest.json | Provenance and reproducibility contract | ✓ VERIFIED | License, RGBDS recipe, digest, profile, protocol, timeout, exclusions. |
| tests/test_api.c | Lifecycle, independence, budget, trace-capacity checks | ✓ VERIFIED | Named assertions use only the public API. |
| tests/test_loader.c | ROM boundary and transactional-loader checks | ✓ VERIFIED | Exact error enums and retained-state assertions. |
| tests/test_tracer.c | Success/failure/unsupported/timeout/trace controls | ✓ VERIFIED | Authored fixture and explicit outcome assertions. |
| cmake/GabbaBoyConfig.cmake.in | Installed package config | ✓ VERIFIED | Loads exported GabbaBoy targets. |
| cmake/VerifyInstalledPackage.cmake | Relocation/content/runner check | ✓ VERIFIED | Checks installed files and rejects private-path leakage. |
| tests/consumers/c/main.c | Installed external C consumer | ✓ VERIFIED | Public-header calls linked by imported package target. |
| tests/consumers/cpp/main.cpp | Installed external C++ consumer | ✓ VERIFIED | C ABI exercised from C++17. |
| README.md | Build, embedding, remote artifact, scope instructions | ✓ VERIFIED | Commands and limitations match implementation. |
| .github/workflows/ci.yml | Native/sanitizer/floor required jobs | ✓ VERIFIED | Read-only PR jobs and fail-closed aggregate. |
| .github/scripts/verify-cmake-floor.sh | Pinned CMake floor validation | ✓ VERIFIED | Checks archive checksum, build, test, install, relocation, consumers. |
| .github/workflows/fixture-repro.yml | Isolated fixture regeneration | ✓ VERIFIED | Pins RGBDS 1.0.1 and compares bytes/digest. |
| tests/expected-tests.txt | Mandatory named-test inventory | ✓ VERIFIED | Matches 25 locally registered tests; sanitizer deliberately omits three install-only cases. |
| .github/workflows/preview.yml | Revision-linked Linux/macOS preview | ✓ VERIFIED | Waits on same-SHA CI, smoke-tests extracted install tree, uploads 14-day artifacts. |
| 01-VALIDATION.md | Local/hosted evidence ledger | ✓ VERIFIED WITH NOTE | Contains an older labelled run-scoped sample. This report records current-SHA expiry evidence. The ledger remains draft/Nyquist false with generic probe metadata unresolved. |
| .github/scripts/verify-pr-evidence.sh | Exact-PR evidence verifier | ✓ VERIFIED | Passed at exact local/PR SHA and inspected both downloaded artifacts and API metadata. |
| cmake/VerifyArtifactSidecar.cmake | Fail-closed sidecar validation | ✓ VERIFIED | Checks source SHA, package digest, smoke, capability limits, and retention. |
| cmake/PreviewPackageSmoke.cmake | Extracted install-tree smoke | ✓ VERIFIED | Reinstalls, archives, extracts, then runs runner and C/C++ consumers against extracted prefix. |
| cmake/RunInstalledConsumer.cmake | Relocated consumer build/run | ✓ VERIFIED | Uses only the supplied installed prefix and fixture. |

### Key Link Verification

The automatic key-link heuristic reported literal-text false negatives for build/runtime relations. I traced each link through CMake, includes, tests, and the hosted smoke workflows.

| From | To | Via | Status | Evidence |
|---|---|---|---|---|
| fixtures/tracer/tracer.asm | src/core/gabbaboy.c | Rebuilt ROM executes through decode and bus | ✓ WIRED | Fixture-repro rebuilds and byte-compares; CTest then supplies the checked ROM to tracer tests calling the core. |
| src/core/gabbaboy.c | src/runner/main.c | API results drive runner outcomes | ✓ WIRED | CMake links the core; runner calls create/load/run/peek functions. |
| include/gabbaboy/gabbaboy.h | src/core/gabbaboy.c | Public API maps to instance state | ✓ WIRED | Core includes the public header and defines its functions. |
| tests/test_loader.c | src/core/gabbaboy.c | Failed replacement preserves state | ✓ WIRED | Test links core and exercises loader/run via public API. |
| tests/test_api.c | include/gabbaboy/gabbaboy.h | Lifecycle/bounds use public contract | ✓ WIRED | Test includes header and links core. |
| tests/test_tracer.c | fixtures/tracer/manifest.json | Fixture protocol matches admitted bytes | ✓ WIRED | CTest passes checked fixture; fixture_digest verifies its manifest SHA. |
| CMakeLists.txt | cmake/GabbaBoyConfig.cmake.in | Installed namespaced export | ✓ WIRED | CMake configures package config and installs exported GabbaBoy::core target. |
| tests/consumers/c/CMakeLists.txt | Installed prefix | Consumer resolves relocated package | ✓ WIRED | find_package/imported target; CTest supplies relocated prefix. |
| tests/consumers/cpp/CMakeLists.txt | Installed prefix | Consumer resolves relocated package | ✓ WIRED | Same package-only path from C++17 consumer. |
| tests/expected-tests.txt | .github/workflows/ci.yml | Executed inventory is checked | ✓ WIRED | CI runs CTest with JUnit and inventory verifier; configure compares registered names. |
| fixtures/tracer/manifest.json | .github/workflows/fixture-repro.yml | Rebuilt bytes/digest are checked | ✓ WIRED | Workflow rebuilds pinned RGBDS output and compares bytes and SHA. |
| .github/workflows/ci.yml | .github/workflows/preview.yml | Preview waits on matching required CI | ✓ WIRED | Preview polls for successful pull-request CI with the same head SHA. |
| .github/workflows/preview.yml | Installed package archive | Exact extracted package is smoke-tested | ✓ WIRED | Archive is extracted, runner/C/C++ consumers run against it, then those archive bytes are uploaded. |

### Data-Flow Trace

| Artifact | Data | Source and flow | Real data | Status |
|---|---|---|---|---|
| src/runner/main.c + src/core/gabbaboy.c | ROM, machine state, trace, outcome | Fixture path → fread → validated private copy → decoder/bus execution → run result/guest marker → runner trace output | Yes; checked-in authored ROM, no mock/static result. | ✓ FLOWING |

### Behavioral Spot-Checks

Named checks below were run directly from the existing local build and each exited 0. The deterministic check compared two full runner outputs.

| Behavior | Command | Result | Status |
|---|---|---|---|
| Instance lifecycle/reset | build/tests/test_api instance_lifecycle fixtures/tracer/tracer.gb | Exit 0 | ✓ PASS |
| Independent instances | build/tests/test_api independent_instances fixtures/tracer/tracer.gb | Exit 0 | ✓ PASS |
| Budget no-overshoot | build/tests/test_api run_bounds fixtures/tracer/tracer.gb | Exit 0 | ✓ PASS |
| Trace capacity/no overwrite | build/tests/test_api trace_capacity fixtures/tracer/tracer.gb | Exit 0 | ✓ PASS |
| Failed load is non-destructive | build/tests/test_loader non_destructive fixtures/tracer/tracer.gb | Exit 0 | ✓ PASS |
| Guest success control | build/tests/test_tracer success fixtures/tracer/tracer.gb | Exit 0 | ✓ PASS |
| Runner | build/gabbaboy-runner fixtures/tracer/tracer.gb | outcome=pass, 200000 half-dots, 8337 records | ✓ PASS |
| Determinism | Two runner invocations compared byte-for-byte in shell variables | Identical 13-line output | ✓ PASS |

Exact-revision Actions API metadata showed all required jobs and steps successful, including the native test-inventory steps and sanitizer inventory step. Fetching detailed job log bodies with `gh run view --log` was blocked by the sandbox's user-cache restriction. Required statuses, step conclusions, and exact artifact evidence remained readable; no per-case CI log counts are asserted here.

### Probe Execution

No probe-*.sh paths were declared in phase plans/summaries, and no scripts/*/tests/probe-*.sh files were present. There was no executable phase probe path to run. The phase-level assumption metadata is separate from this probe-path contract.

| Probe | Command | Result | Status |
|---|---|---|---|
| None declared or discovered | Probe path scan | No probe script paths found | N/A |

### Requirements Coverage

| Requirement | Source plan | Description | Status | Evidence |
|---|---|---|---|---|
| BASE-01 | 01-01, 01-03 | Offline C17 configure/build/test/install and headless runner | ✓ SATISFIED | README, CMake presets, floor job, exact native CI. |
| BASE-02 | 01-01, 01-02 | Opaque lifecycle, ownership, model, thread, and error rules | ✓ SATISFIED | Public header, per-instance state, lifecycle/independence checks. |
| BASE-03 | 01-02 | Bounded loader and explicit non-destructive errors | ✓ SATISFIED | Header parser and direct transaction check; exact CI inventory. |
| BASE-04 | 01-01, 01-02 | Original ROM through declared CPU/bus subset; bounded trace and explicit unsupported execution | ✓ SATISFIED | Runner and positive/negative tracer cases; hardware conformance excluded. |
| BASE-05 | 01-01, 01-04 | Fixture provenance, rights, digest, reproducibility | ✓ SATISFIED | Authored source/license/manifest, digest test, exact RGBDS run. |
| BASE-06 | 01-03 | Installed C and C++ consumers | ✓ SATISFIED | Relocated consumers passed package smoke and native CI. |
| BASE-07 | 01-02, 01-04 | Mandatory test inventory and sanitizer evidence | ✓ SATISFIED | Exact-SHA native, sanitizer, and required aggregate steps passed. |
| BASE-08 | 01-05 | Remote PR and revision-linked preview | ✓ SATISFIED | Strict required checks and exact artifact/API evidence. |

All eight BASE requirements map to a phase plan. No Phase 1 requirement is orphaned.

### Exact Hosted Evidence

PR #1 at https://github.com/szTheory/gabbaboy/pull/1, local HEAD, workflow head SHAs, and downloaded sidecars all matched 97d73a7cfadb8b90edea2e406566ff0a254c4865.

| Workflow | Run | Exact-SHA result |
|---|---:|---|
| ci | 37134846449 | Success: Linux x64, macOS arm64, Windows x64, ASan/UBSan, CMake 3.25.3 floor, required-native. |
| fixture-repro | 37134846450 | Success: RGBDS output matched checked-in bytes and digest. |
| preview-package-smoke | 37134846475 | Success: Linux x64 and macOS arm64 package smoke and aggregate. |

Readback of main branch protection showed strict contexts required-native, fixture-repro, and preview-package-smoke. The exact-revision evidence script passed after downloading/extracting both artifacts and checking archive safety, installed files, source SHA, package digest, smoke metadata, capabilities, retention, and GitHub API expiry.

| Artifact | GitHub artifact digest | Package SHA-256 | Created | API expiry | Retention |
|---|---|---|---|---|---|
| preview-linux-x64 | sha256:d29c9e326121b920e8e906da5e39ff6af70128be5b395bbd9ce612da26957f31 | c4bf89cb36c153b75ff6148950545f1dfd16927f93f5633f17ac36e0e75f3ed7 | 2026-10-03T15:54:29Z | 2026-10-17T15:54:28Z | 14 days |
| preview-macos-arm64 | sha256:260d0c6c531b68840f3e13ed2dd32c7be83a711898bf3f7f77250f462afeee4f | 6be1bb688a70237022a4313d3dd66db67fa3f1ce7b44532a9f03c5777f24f806 | 2026-10-03T15:54:37Z | 2026-10-17T15:54:36Z | 14 days |

These are temporary workflow artifacts, not releases; no Windows package is published. They qualify only the install tree, runner, consumers, and limited DMG-CPU-B tracer.

### Decision Coverage

The runtime decision-coverage check reported all 11 trackable context decisions honored, with none missing. The check is non-blocking.

### Test Quality Audit

| Test file | Requirement | Active cases | Skipped | Circular | Assertion strength | Verdict |
|---|---|---:|---:|---:|---|---|
| tests/test_api.c | BASE-02 | 4 | 0 | 0 | Value/state-transition assertions | ✓ PASS |
| tests/test_loader.c | BASE-03 | 10 | 0 | 0 | Exact errors and retained-state assertions | ✓ PASS |
| tests/test_tracer.c | BASE-04 | 5 | 0 | 0 | Guest values and structured stop reasons | ✓ PASS |
| tests/consumers/c/main.c and tests/consumers/cpp/main.cpp | BASE-06 | 2 consumer builds | 0 | 0 | Installed API execution and guest marker | ✓ PASS |
| tests/expected-tests.txt and CI inventory verifier | BASE-07 | 25 installed / 22 core-only | 0 allowed | 0 | Exact JUnit inventory; missing/skipped cases fail | ✓ PASS |

Disabled-test and test-output-generator scans found no skipped cases or scripts that generate expected fixture output. Fixture expectations originate from the authored ROM/manifest and are checked by digest/regeneration; they are not generated from emulator output. This is regression evidence, not hardware or differential-oracle evidence.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---:|---|---|---|
| — | — | No stub, empty implementation, unresolved debt marker, or TODO/HACK/PLACEHOLDER found in phase implementation files. | — | No blocking anti-pattern. |

The text scan’s only XXX substring was XXXXXX in a mktemp filename template in verify-cmake-floor.sh, not a debt-marker comment.

## Human Verification Required

N/A — this is an infrastructure/foundation phase with no visual or perceptual user interface. Acceptance criteria are covered by named checks and exact-revision package/CI evidence; manual UAT is not required.

## Validation Ledger Note

01-VALIDATION.md still records status draft, nyquist_compliant false, and approval pending; its probe disposition retains generic concurrency/idempotency signals as unresolved. Concrete phase acceptance evidence is recorded above, but this verifier did not rewrite that validation strategy metadata. The generic assumptions are not additional roadmap success criteria; keep the validation ledger state distinct from this goal-backward phase verdict.

## Gaps Summary

No Phase 1 must-have failed or remained behavior-unverified. The phase delivers an installable, embeddable bounded API and a runnable authored tracer under its explicitly limited profile. Hardware-correct address-space behavior is deferred to Phase 2; artifacts make no gameplay, full-CPU, CGB, boot-ROM, or hardware-conformance claim.

---

_Verified: 2026-10-03T16:11:44Z_  
_Verifier: the agent (gsd-verifier)_
