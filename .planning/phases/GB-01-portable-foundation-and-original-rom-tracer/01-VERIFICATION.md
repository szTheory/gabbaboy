---
phase: GB-01-portable-foundation-and-original-rom-tracer
verified: 2026-10-03T17:53:27Z
status: passed
score: 5/5 roadmap truths verified
revision: 8396096ad17500974b30657af91fd2ef9ad51237
covered_files:
  - .github/scripts/safe_extract_package.py
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
covered_digest: "v2:sha256:84d2e6263741ca6c1ba2b44949bd5e47a55b7baeb180a01253dfe9c8aaec9970"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 3/5
  gaps_closed:
    - ROM-only headers declaring more than 32 KiB are rejected before allocation, and a valid-checksum 64 KiB replacement regression proves the active 32 KiB machine remains usable.
    - Downloaded preview packages are validated and safely extracted with bounded paths, members, expansion, stream reads, and regular-file-only writes before consumer execution.
    - Required CI and fixture-reproduction workflows passed for the exact verified source SHA.
    - Linux and macOS preview artifacts passed installed-package smoke and exact source, package-digest, and retention verification for the exact verified source SHA.
  gaps_remaining: []
  regressions: []
deferred:
  - truth: "Hardware-qualified address-space behavior, including actual cartridge RAM availability, is implemented and validated."
    addressed_in: "Phase 2 — DMG CPU, Bus, and Time"
    evidence: "Phase 2 success criterion 3 requires memory mapping to match declared DMG evidence at observable access boundaries. The Phase 1 tracer uses an emulator-owned 0xA000 RAM window for its authored protocol; this is explicitly not hardware-conformance evidence."
---

# Phase 1: Portable Foundation and Original ROM Tracer Verification Report

**Phase Goal:** As a developer, I want to run an original ROM with an installable GB core via a bounded API, so that I can embed it.
**Verified:** 2026-10-03T17:53:27Z
**Status:** passed
**Revision:** `8396096ad17500974b30657af91fd2ef9ad51237`
**Re-verification:** Yes — after the code-review fixes and at the current checkout revision.

## User Flow Coverage

User story validator accepted the roadmap goal. The flow below checks observable outcomes against the current code and test output; plan summaries are not used as implementation evidence.

| Step | Expected | Evidence | Status |
|---|---|---|---|
| Configure and build | A prepared C17 toolchain configures and builds the headless core and runner with documented CMake presets. | macOS `cmake --preset phase1` and `cmake --build --preset phase1` passed; Linux CMake 3.25.3 floor lane also configured and built. | ✓ VERIFIED |
| Install and embed | A relocated install exposes `GabbaBoy::core` and the public header to independent C and C++ consumers. | macOS CTest and Linux CMake-floor relocated CTest each passed runner, C, and C++ consumer tests. | ✓ VERIFIED |
| Run the original ROM | The guest code executes through the decoder/bus subset and yields its guest-derived pass state and bounded trace. | `build/gabbaboy-runner fixtures/tracer/tracer.gb` returned `outcome=pass`, `half_dots=200000`, `trace_records=8337`; first trace is entry `0x0100` followed by `0x0150` at half-dot 32. | ✓ VERIFIED |
| Reject unsafe cartridge inputs | Unsupported or malformed replacement images return explicit errors without damaging a loaded instance. | Full test suite includes unsupported-size and non-destructive cases; 64 KiB valid-checksum regression expects `GBB_UNSUPPORTED_ROM_SIZE` and checks continued execution of prior ROM. | ✓ VERIFIED |
| Use the hosted PR and download a qualified preview | Required checks and downloadable package artifacts qualify the exact source revision. | `sh .github/scripts/verify-pr-evidence.sh` passed for local HEAD, PR #1 head, workflow runs, both downloaded package artifacts, sidecars, smoke results and API expiry metadata; all identify `8396096ad17500974b30657af91fd2ef9ad51237`. | ✓ VERIFIED |

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | Developers can configure, build, test, and install the C17 core/runner with documented CMake/Ninja/CTest commands after dependency preparation, without SDL or network in the ordinary path; installed C/C++ consumers run the tracer. | ✓ VERIFIED | macOS phase1 preset and full CTest passed; Linux official CMake 3.25.3 floor script passed configure/build/test/install/relocation/consumers. No RGBDS step is in default configure/build/test. |
| 2 | Opaque instances support documented creation, reset, run, destruction, independent state, and bounded ownership/error rules. | ✓ VERIFIED | Public header documents ownership, thread and model constraints; CTest lifecycle, independent-instance, run-budget and trace-capacity cases passed on macOS and Linux sanitizer build. |
| 3 | Malformed, excessive, unsupported, or invalid ROM loads return bounded explicit errors without mutating a usable loaded instance. | ✓ VERIFIED | Loader validates null/length, header checksum/type/size and exact length before allocation/mutation. The new 64 KiB declared-size regression passed in local CTest, ASan/UBSan CTest, and CMake-floor CTest. |
| 4 | The original authored ROM executes its declared subset through the decoder and bus, reports explicit unsupported/failure states, and produces bounded deterministic trace output with reproducible rights and recipe evidence. | ✓ VERIFIED | Runner output is guest-derived; 26-case CTest passed. RGBDS v1.0.1 Linux archive digest was checked; local regeneration byte-compared equal to the fixture and manifest SHA-256 `85d84babe64e852babc55fe355919f9d2f8013f90dc56550d58e972470321f77`. Manifest and MIT notice document applicability and exclusions. |
| 5 | Current-revision required CI proves mandatory cases and sanitizers ran, and a current-revision preview package is available with installed-consumer smoke and honest limits. | ✓ VERIFIED | Exact current-SHA CI run `37141965336`, fixture run `37141965338`, preview run `37141965332`; required contexts pass, both hosted installed-package smoke jobs pass, and the exact artifact verifier matched downloaded archives and sidecars to source SHA, digest, smoke and 14-day retention. |

**Score:** 5/5 roadmap truths verified; behavior-unverified: 0.

## Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `CMakeLists.txt`, `CMakePresets.json` | C17 core/runner, schema-6 presets, install/export | ✓ VERIFIED | Build, install, floor and relocated-package paths executed successfully. |
| `include/gabbaboy/gabbaboy.h` | Bounded opaque-instance public contract | ✓ VERIFIED | Explicit ownership, thread-use, model, size and error rules; functions are implemented by the core. |
| `src/core/gabbaboy.c` | Instance lifecycle, loader, declared CPU/bus subset, run bounds | ✓ VERIFIED | Substantive code. ROM-only size codes above 0 are rejected before declared-size calculation and allocation, preventing ROM bytes from shadowing the external-RAM window. |
| `src/runner/main.c` | Headless runner reports guest outcome and trace | ✓ VERIFIED | Reads a bounded file, calls public API, reads guest marker, and emits structured pass/failure/unsupported/timeout result. |
| `fixtures/tracer/{tracer.asm,tracer.gb,manifest.json,LICENSE.txt}` | Original fixture with rights, digest, recipe and protocol | ✓ VERIFIED | Pinned RGBDS v1.0.1 reproduction passed byte equality and digest. Claims exclude boot ROM, hardware conformance, general gameplay and CGB. |
| `tests/test_api.c`, `tests/test_loader.c`, `tests/test_tracer.c` | Lifecycle, bounds, loader, fixture positive/negative controls | ✓ VERIFIED | All registered applicable cases ran in local normal and sanitizer CTest. |
| `tests/consumers/{c,cpp}` | External consumers of installed `GabbaBoy::core` | ✓ VERIFIED | Both consumers built and executed against relocated install on macOS and in the Linux CMake-floor lane. |
| `.github/workflows/ci.yml`, `tests/expected-tests.txt`, inventory script | Native, sanitizer, CMake-floor jobs and fail-closed test inventory | ✓ VERIFIED | Local macOS inventory verified 26 installed cases; Linux ASan/UBSan verified 23 core/package cases; CMake-floor verified 23 base and 26 relocated cases. Exact-SHA hosted CI run `37141965336` passed required-native. |
| `.github/workflows/fixture-repro.yml` | Digest-pinned RGBDS reproduction | ✓ VERIFIED | Pinned v1.0.1 archive SHA and byte reproduction passed locally; exact-SHA GitHub fixture run `37141965338` passed. |
| `.github/workflows/preview.yml`, `cmake/PreviewPackageSmoke.cmake` | Exact archive is safely extracted, relocated and smoke-tested | ✓ VERIFIED | Local normal/sanitizer/floor preview smoke passed; exact-SHA hosted run `37141965332` passed Linux and macOS installed-package smoke jobs. |
| `.github/scripts/safe_extract_package.py` | Bounded regular-file-only safe archive extraction | ✓ VERIFIED | `--self-test` passed symlink, hardlink, special-file, traversal, absolute/out-of-prefix path, duplicate, file-parent conflict, member count, path depth, expanded-size and decompressed-stream checks. |
| `.github/scripts/verify-pr-evidence.sh` | Exact source/check/run/artifact chain verifier | ✓ VERIFIED | Passed at exact HEAD; verified required contexts, workflow runs, downloaded Linux/macOS artifacts, sidecars and API metadata. |
| `README.md` and `01-VALIDATION.md` | Accurate build, integration, evidence and limitation guidance | ✓ VERIFIED | Scope claims remain limited; exact current run evidence is recorded below and older run-scoped samples are distinguished. |

## Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `fixtures/tracer/tracer.asm` | `fixtures/tracer/tracer.gb` | RGBDS recipe | ✓ WIRED | Pinned RGBDS v1.0.1 rebuilt identical bytes and digest. |
| `fixtures/tracer/tracer.gb` | `src/core/gabbaboy.c` | CTest input to loader/decode/bus | ✓ WIRED | Fixture tests load bytes through public API and assert success/failure/unsupported outcomes. |
| `include/gabbaboy/gabbaboy.h` | `src/core/gabbaboy.c` | C API definitions | ✓ WIRED | Core implements the declared lifecycle/load/run/peek interface. |
| `src/core/gabbaboy.c` | `src/runner/main.c` | API result drives runner output | ✓ WIRED | Runner uses API stop reason and guest RAM marker, not a static success result. |
| CMake install export | `tests/consumers/c` and `tests/consumers/cpp` | `find_package` and `GabbaBoy::core` | ✓ WIRED | Both external projects compiled and ran using relocated install only. |
| `tests/expected-tests.txt` | CI inventory verifier | CTest JUnit inventory comparison | ✓ WIRED | Local normal/sanitizer/floor inventories passed with expected core-only or installed selection. |
| `ci.yml` | `preview.yml` | Matching successful workflow SHA | ✓ WIRED | Exact current-SHA CI and preview runs passed. |
| Preview archive | Safe extractor and artifact sidecar verifier | Validate-before-write then consumer smoke | ✓ WIRED | Extractor adversarial suite and local package tests pass; exact hosted Linux/macOS archives were downloaded and their metadata verified. |

## Data-Flow Trace

| Artifact | Data | Source and flow | Real data | Status |
|---|---|---|---|---|
| `src/runner/main.c` → `src/core/gabbaboy.c` | ROM, guest machine state, trace and outcome | Explicit fixture path → bounded file read → validated private ROM copy → opcode decoder and bus → guest marker → runner output | Yes; checked-in authored ROM, no mocked/static result. | ✓ FLOWING |

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| macOS build and full installed suite | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` | 26/26 passed, including package archive extraction and relocated runner/C/C++ consumers. | ✓ PASS |
| Executed case inventory | `bash .github/scripts/verify-test-inventory.sh /tmp/gabbaboy-phase1-tests.xml tests/expected-tests.txt --installed` | 26 cases verified; none skipped. | ✓ PASS |
| Linux ASan/UBSan build and suite | CMake 3.25.3, Ubuntu 22.04 x86_64 container; `phase1-asan` preset, verbose flags and CTest | Both `-fsanitize=address,undefined` flags present; 23/23 passed. | ✓ PASS |
| Official CMake floor and relocation | `bash .github/scripts/verify-cmake-floor.sh` under Ubuntu 22.04 x86_64 | Official archive digest/version passed; 23/23 floor tests and 26/26 relocated tests; both inventories, install, runner, C/C++ consumers passed. | ✓ PASS |
| Pinned fixture reproduction | RGBDS v1.0.1 archive SHA verification, assemble/link/fix, `cmp`, manifest SHA comparison | Exact byte match; SHA-256 `85d84babe64e852babc55fe355919f9d2f8013f90dc56550d58e972470321f77`. | ✓ PASS |
| Safe extraction adversarial cases | `python3 .github/scripts/safe_extract_package.py --self-test` | Passed all path/type/resource-bound rejection tests. | ✓ PASS |
| Current remote evidence chain | `sh .github/scripts/verify-pr-evidence.sh` | Passed for repository `szTheory/gabbaboy`, PR #1, exact HEAD `8396096ad17500974b30657af91fd2ef9ad51237`; CI `37141965336`, fixture `37141965338`, preview `37141965332`. | ✓ PASS |
| Goal-visible ROM result | `build/gabbaboy-runner fixtures/tracer/tracer.gb` | `outcome=pass`, `half_dots=200000`, `trace_records=8337`; deterministic guest pass marker. | ✓ PASS |

## Probe Execution

No `probe-*.sh` files are declared by the plans or present under `scripts/*/tests/`; there was no phase probe path to execute.

| Probe | Command | Result | Status |
|---|---|---|---|
| None declared/discovered | Probe-path scan | No probe script found. | N/A |

## Requirements Coverage

| Requirement | Source plan | Status | Evidence |
|---|---|---|---|
| BASE-01 | 01-01, 01-03 | ✓ SATISFIED | macOS normal build and CTest; Linux CMake 3.25.3 floor and install/relocation consumers passed. |
| BASE-02 | 01-01, 01-02 | ✓ SATISFIED | Public header contract and lifecycle/independent-instance tests passed. |
| BASE-03 | 01-02 | ✓ SATISFIED | Loader boundaries and non-destructive 64 KiB unsupported-size regression passed; safe bounded allocation order inspected. |
| BASE-04 | 01-01, 01-02 | ✓ SATISFIED | Real fixture execution, explicit stop results, runner pass, trace/budget/negative controls passed. This is not general gameplay or hardware conformance. |
| BASE-05 | 01-01, 01-04 | ✓ SATISFIED | License, manifest, source, digest and locally reproduced pinned RGBDS bytes. |
| BASE-06 | 01-03 | ✓ SATISFIED | Relocated C/C++ consumers passed macOS and CMake-floor Linux testing. |
| BASE-07 | 01-02, 01-04 | ✓ SATISFIED | Local ASan/UBSan passed 23/23; exact-SHA hosted CI run `37141965336` passed required-native and mandatory lanes. |
| BASE-08 | 01-05 | ✓ SATISFIED | Exact-SHA preview run and artifact/API verification passed for Linux x64 and macOS arm64; run-scoped expiry and limits are recorded below. |

All Phase 1 requirements are represented in the five plans; no Phase 1 requirement is orphaned. All eight Phase 1 requirements are satisfied at the verified revision.

## Exact Hosted Evidence

`sh .github/scripts/verify-pr-evidence.sh` passed. PR #1's head, local HEAD, successful pull-request workflow runs, sidecars and package source metadata all matched `8396096ad17500974b30657af91fd2ef9ad51237`. Required contexts `required-native`, `fixture-repro`, and `preview-package-smoke` passed. The exact fixture job reproduced the checked-in ROM; the preview run passed both installed-package smoke jobs. Each artifact was downloaded, safely extracted, and checked against the sidecar's package digest, source SHA, smoke result and configured 14-day retention.

| Evidence | Run | Result |
|---|---:|---|
| Native CI | `37141965336` | Success; `required-native` and its Linux/macOS/Windows, ASan/UBSan, and CMake floor lanes passed. |
| Fixture reproduction | `37141965338` | Success; pinned RGBDS fixture regeneration passed. |
| Preview package smoke | `37141965332` | Success; Linux x64 and macOS arm64 installed-package smoke jobs passed. |

| Artifact | GitHub artifact digest | Package SHA-256 | Created | API expires | Retention |
|---|---|---|---|---|---|
| `preview-linux-x64` | `sha256:b2e3d57aa5cc8527bd05c2ee11d8e006495dd30193b38a08e828e11e60bd092b` | `045c5c063c48f5e125452f7053f670a75474059fa2e26e84dd365f88994a2726` | `2026-10-03T17:51:15Z` | `2026-10-17T17:51:14Z` | 14 days |
| `preview-macos-arm64` | `sha256:d95990eab682cae084a5992777167a5fc6c71011eafa2326d8b74a5311499097` | `62462139dc88d4228b29cf2ea47d26176f3047dfc968a11f870d1a1f1143aef3` | `2026-10-03T17:51:19Z` | `2026-10-17T17:51:18Z` | 14 days |

Artifacts are run-scoped preview downloads, not durable releases. There is no Windows preview artifact.

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| — | — | No implementation debt markers, placeholders, empty code paths, or static guest-result stub found in the reviewed implementation. | — | — |

## Limitations and Deferred Scope

This deliverable is an installable headless C17 core and an authored bootless DMG-CPU-B tracer for one declared opcode subset. It does not establish full DMG CPU correctness, real cartridge RAM mapping, game compatibility, display/audio, CGB execution, boot-ROM behavior or hardware conformance. In particular, the tracer fixture declares ROM-only/no cartridge RAM yet uses an emulator-owned 0xA000 RAM window as its test protocol; Phase 2 owns hardware-qualified memory-map behavior. Preview artifacts are run-scoped and Linux/macOS-only; no Windows download or stable ABI is claimed.

## Gaps Summary

No blocking gaps remain. Local code, loader boundaries, package extraction, fixture provenance, installation/consumer behavior, Linux sanitizer and CMake floor evidence pass. Exact-revision hosted CI, fixture regeneration and Linux/macOS preview artifact evidence now pass for the same verified SHA. No manual UAT is required for these headless, automatically checked contracts. Hardware qualification and perceptual behavior are explicitly deferred/out of scope for this phase.

---

_Verified: 2026-10-03T17:53:27Z_
_Verifier: the agent (gsd-verifier)_
