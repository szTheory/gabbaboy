---
phase: GB-01-portable-foundation-and-original-rom-tracer
verified: 2026-10-09T12:17:36Z
status: passed
score: 5/5 must-haves verified
behavior_unverified: 0
overrides_applied: 0
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
  - .planning/phases/GB-01-portable-foundation-and-original-rom-tracer/01-02-PLAN.md
  - .planning/phases/GB-01-portable-foundation-and-original-rom-tracer/01-03-PLAN.md
  - .planning/phases/GB-01-portable-foundation-and-original-rom-tracer/01-03-SUMMARY.md
  - .planning/phases/GB-01-portable-foundation-and-original-rom-tracer/01-04-PLAN.md
  - .planning/phases/GB-01-portable-foundation-and-original-rom-tracer/01-04-SUMMARY.md
  - .planning/phases/GB-01-portable-foundation-and-original-rom-tracer/01-05-PLAN.md
  - .planning/phases/GB-01-portable-foundation-and-original-rom-tracer/01-05-SUMMARY.md
  - .planning/phases/GB-01-portable-foundation-and-original-rom-tracer/01-REVIEW.md
  - .planning/phases/GB-01-portable-foundation-and-original-rom-tracer/01-SECURITY.md
  - .planning/phases/GB-01-portable-foundation-and-original-rom-tracer/01-VALIDATION.md
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
  - tests/test_instance_concurrency.c
  - tests/test_loader.c
  - tests/test_tracer.c
  - tests/verify_runner_help.cmake
covered_digest: "v3:sha256:f7b70e3647b55fa9892da3c411acb15442100083c3e24e5d75b900fc5564067e"
---

# Phase 1: Portable Foundation and Original ROM Tracer Verification Report

**Phase Goal:** As a developer, I want to run an original ROM with an installable GB core via a bounded API, so that I can embed it.
**Verified:** 2026-10-09T12:17:36Z
**Status:** passed
**Re-verification:** No previous verification report had an unresolved `gaps:` section; all five roadmap truths and all eight plan-linked requirements were checked afresh.

## User Flow Coverage

The roadmap's MVP user story validated successfully (`user-story.validate`: `valid: true`). The flow is headless and fully automatable; no visual or perceptual user check is part of this phase.

| Step | Expected | Evidence | Status |
|---|---|---|---|
| Configure and build | A prepared developer environment can build the C17 core and runner using documented CMake presets without SDL or a network fetch in the normal path. | `CMakePresets.json`, `CMakeLists.txt`, and `README.md`; exact PR-head native CI includes Linux, macOS, Windows, and CMake 3.25.3 floor lanes. | ✓ VERIFIED |
| Install and embed | A developer can consume the installed package through public headers and `GabbaBoy::core` from C and C++ projects. | Relocated installed C/C++ consumer runs on exact PR-head native and preview lanes; current local `preview_package_smoke` passed 1/1. | ✓ VERIFIED |
| Run an original ROM | The original authored tracer runs through the bounded API and real CPU/bus path and returns a guest-derived pass and trace. | Current `./build/gabbaboy-runner fixtures/tracer/tracer.gb` returned `outcome=pass`, `half_dots=199984`, and 8335 trace records, beginning at PC `0100`; current `tracer_success` and `tracer_smoke` passed. | ✓ VERIFIED |
| Embed with bounded errors | Invalid ROMs and unsupported guest behavior produce explicit, bounded outcomes while preserving a valid loaded instance. | Current 26-test targeted Phase 1 CTest selection passed, including loader boundary/non-destructive cases and tracer failure, unsupported, timeout, and trace-capacity cases. | ✓ VERIFIED |
| Obtain a qualified preview | A contributor can use the documented PR workflow and download a revision-linked package with installed smoke and explicit limits. | PR #35 exact head `d1e5fdb3b23256f06694cd8d91613638612bccb8` passed all required contexts; both package artifacts were downloaded and checked against source SHA, digest, sidecar, expiry, and safe extraction. | ✓ VERIFIED |

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | A developer can configure, build, test, and install the C17 core/runner using documented CMake/Ninja/CTest commands without SDL or network access after explicit preparation; external C and C++ consumers link installed `GabbaBoy::core` and execute the tracer. | ✓ VERIFIED | `README.md` documents the offline build/install path; the exact PR-head `required-native` run passed Linux x64, macOS arm64, Windows x64 and the CMake 3.25.3 floor lane. Exact installed C/C++ package smoke passed in native and preview runs; current local `preview_package_smoke` passed. |
| 2 | Callers can create, reset, run, and destroy independent opaque instances under explicit model, ownership, lifetime, thread, and error rules; malformed, excessive, and unsupported ROMs fail with bounded non-destructive errors. | ✓ VERIFIED | Public contract in `include/gabbaboy/gabbaboy.h`; implementation in `src/core/gabbaboy.c`; current `instance_lifecycle`, `reset_idempotency`, `independent_instances`, `concurrent_independent_instances`, `run_bounds`, and 11 loader boundary/non-destructive tests passed. |
| 3 | The original ROM executes its declared opcode subset through the real CPU/bus path with a deterministic bounded trace and explicit unsupported outcomes; its fixture has reproducible provenance, rights, digest, applicability, protocol, and timeout evidence. | ✓ VERIFIED | Current runner invocation and `tracer_success`, `tracer_failure`, `tracer_unsupported`, `tracer_timeout`, `tracer_trace`, `tracer_smoke`, and `fixture_digest` passed. `fixtures/tracer/manifest.json`, `tracer.asm`, and `LICENSE.txt` bind original source, MIT terms, RGBDS 1.0.1 recipe/digest, ROM digest, boot/model scope, protocol, and budget. Exact fixture-repro run `37928170722` passed. |
| 4 | Required CI proves required tests and ASan/UBSan ran, and missing mandatory tests, failures, or timeouts cannot pass the aggregate gate. | ✓ VERIFIED | `.github/workflows/ci.yml`, `tests/expected-tests.txt`, `.github/scripts/verify-test-inventory.sh`, and CTest `TIMEOUT 30` enforce inventory and watchdog behavior. Exact required-native run `37928170860` passed Linux/macOS/Windows, ASan/UBSan, and the CMake floor lanes. The current full local CTest inventory is recorded as 179/179 in `01-VALIDATION.md`; this verifier independently reran the 26 Phase 1-relevant named cases, all passed. |
| 5 | Contributors can use the configured PR workflow and obtain a source-revision-linked foundation preview whose installation smoke passes and whose limitations are explicit. | ✓ VERIFIED | Exact PR #35 required contexts `required-native`, `fixture-repro`, and `preview-package-smoke` passed at the tested head; PR was squash-merged as `96f76dec9a675ede45da8d75bd72a5141c7419e4`. Exact preview run `37928170973` produced Linux x64 and macOS arm64 artifacts. Both archive digests, package digests, source SHA sidecars, 14-day retention, installed smoke, and safe extraction are recorded in `01-VALIDATION.md`. The open-PR-only wrapper was not rerun after merge; equivalent exact-run/API/download/sidecar/extraction checks were run directly, as documented. |

**Score:** 5/5 truths verified; behavior-unverified: 0.

### Required Artifacts

All plan-declared artifacts passed `query verify.artifacts`: Plan 01 5/5, Plan 02 3/3, Plan 03 5/5, Plan 04 4/4, Plan 05 6/6. Manual substance checks confirmed the public header documents ownership, threading, model and bounds; the core contains the real bounded CPU/bus path; the runner derives result from guest state; the fixture manifest has complete source/rights/build/protocol data; package consumers use the installed public target; and CI/package scripts enforce their stated gates.

| Artifact group | Expected | Status | Details |
|---|---|---|---|
| `CMakeLists.txt`, `CMakePresets.json`, `cmake/*` | C17 build, install/export, relocation and package smoke | ✓ VERIFIED | Build and CMake floor/relocated consumer lanes passed; current `preview_package_smoke` passed. |
| `include/gabbaboy/gabbaboy.h`, `src/core/gabbaboy.c` | Bounded opaque-instance public API and real guest execution | ✓ VERIFIED | API contract maps to instance-owned core state and bounded calls; lifecycle, loader, guest and concurrency checks passed. |
| `src/runner/main.c` | Bounded runner with explicit results, trace, and recovery guidance | ✓ VERIFIED | Reads bounded input and uses API result/guest state; current ROM run and `runner_help` passed. |
| `fixtures/tracer/*` | Original, redistributable fixture with reproducible build and applicability | ✓ VERIFIED | Manifest and license checked; exact fixture-repro run passed. |
| `tests/*` and `tests/expected-tests.txt` | Lifecycle, loader, tracer, inventory, and installed consumer checks | ✓ VERIFIED | Targeted Phase 1 CTest 26/26 passed. Inventory includes the current reset, threaded-isolation, and runner-help cases. |
| `.github/workflows/{ci,fixture-repro,preview}.yml`, `.github/scripts/*` | Exact-revision CI, fixture reproduction, and source-bound package evidence | ✓ VERIFIED | Required exact PR-head runs and both downloaded packages passed; wrapper post-merge limitation is documented. |
| `README.md`, `01-VALIDATION.md`, `01-SECURITY.md`, `01-REVIEW.md` | Honest usage, validation, security, and review evidence | ✓ VERIFIED | Current exact-hosted evidence is recorded; security register reports 21/21 closed and zero open; final source recheck is clean. |

### Key Link Verification

The generic `verify.key-links` lexical heuristic returned false negatives for several C, CMake, and workflow relationships because targets are connected through compilation, API calls, package configuration, CTest, or CI job dependencies rather than literal target-path strings. Each connection below was manually traced and behaviorally checked where applicable.

| From | To | Via | Status | Evidence |
|---|---|---|---|---|
| `fixtures/tracer/tracer.asm` | `src/core/gabbaboy.c` | ROM opcodes decode through guest CPU/bus | ✓ WIRED | Current tracer positive/negative tests and runner smoke execute checked-in ROM bytes. |
| `include/gabbaboy/gabbaboy.h` | `src/core/gabbaboy.c` | Public API declarations to definitions | ✓ WIRED | CMake core target compiles implementation; tests and runner call declared API. |
| `src/core/gabbaboy.c` | `src/runner/main.c` | Run result and guest RAM drive runner output | ✓ WIRED | Runner links `GabbaBoy::core`; current direct execution reports guest-derived pass/trace. |
| `CMakeLists.txt` | `cmake/GabbaBoyConfig.cmake.in` | Exported `GabbaBoy::core` package config | ✓ WIRED | Config is included in package generation and relocated consumers find the installed target. |
| `tests/consumers/{c,cpp}` | relocated installed prefix | `find_package` and public target | ✓ WIRED | Exact hosted package consumers and current local package smoke passed. |
| `tests/expected-tests.txt` | CI inventory verifier | Executed CTest XML compared to required list | ✓ WIRED | CI calls inventory script; exact required-native lane passed; current named cases passed. |
| `fixtures/tracer/manifest.json` | fixture reproduction workflow | Pinned assembler rebuild and digest comparison | ✓ WIRED | Exact `fixture-repro` run passed; local `fixture_digest` passed. |
| `ci.yml` | `preview.yml` | Package jobs gated on required revision evidence | ✓ WIRED | Same exact tested SHA was used by successful required-native and preview runs. |
| preview archive | sidecar verifier and safe extractor | Validate and smoke exact uploaded bytes | ✓ WIRED | Direct exact-run artifact, sidecar, digest, retention, and extraction checks passed on both packages. |

### Data-Flow Trace (Level 4)

| Artifact | Data variable | Source and flow | Real data | Status |
|---|---|---|---|---|
| ROM → runner → core → output | ROM bytes, guest RAM, stop result, trace records | Checked-in authored `tracer.gb` → bounded file read → public load/run → decoder and bus writes/readback → guest marker and trace → runner result | Yes; no synthetic pass result or mock is used. | ✓ FLOWING |
| Installed package → consumer result | Header/library/package path | Relocated package install → `find_package(GabbaBoy)` → `GabbaBoy::core` → external C/C++ calls | Yes; exact hosted installed-consumer smoke and current local preview smoke passed. | ✓ FLOWING |
| Package evidence | archive bytes, source SHA, package SHA, smoke marker, retention | Exact PR-head Actions artifacts → API metadata/download → sidecar check → safe extraction and execution | Yes; both Linux and macOS package bytes were checked against run metadata and executed. | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Phase 1 contract and regression cases | `ctest --test-dir build --output-on-failure --no-tests=error -R '^(instance_lifecycle|independent_instances|reset_idempotency|run_bounds|trace_capacity|concurrent_independent_instances|loader_...|tracer_...|tracer_smoke|fixture_digest|runner_help|preview_package_smoke)$'` | 26/26 passed in 1.51 seconds. | ✓ PASS |
| Actual guest path | `./build/gabbaboy-runner fixtures/tracer/tracer.gb` | `outcome=pass`, half-dot budget reached without exceeding it, 8335 bounded instruction traces starting at entry PC `0100`. | ✓ PASS |
| CLI recovery | `./build/gabbaboy-runner --help` | Shows ROM, manifest-case, and manifest-suite forms; `runner_help` passed. | ✓ PASS |
| Full local inventory | Recorded validation command in `01-VALIDATION.md` | 179/179 local CTest cases passed; this pass was recorded by the phase execution, not rerun as part of this focused verifier pass. | ✓ PASS (recorded evidence) |

### Probe Execution

No plan-declared or discovered `probe-*.sh` path applies to this phase. The declared phase probes were mapped to named automated CTest cases; those relevant cases were executed above.

| Probe | Command | Result | Status |
|---|---|---|---|
| None declared/discovered | Probe scan | No probe script path to execute. | N/A |

### Requirements Coverage

All requirement IDs from the five plan `requirements` lists were cross-referenced to `.planning/REQUIREMENTS.md`. The union is exactly BASE-01 through BASE-08, each mapped to Phase 1; no additional Phase 1 requirement is orphaned.

| Requirement | Source plan(s) | Description | Status | Evidence |
|---|---|---|---|---|
| BASE-01 | 01-01, 01-03 | Offline documented CMake build/test/install | ✓ SATISFIED | README, CMake configuration, exact native/floor CI and installed smoke. |
| BASE-02 | 01-01, 01-02 | Independent opaque instances and documented lifecycle/ownership rules | ✓ SATISFIED | Public header, implementation, reset/lifecycle/concurrency tests. |
| BASE-03 | 01-02 | Bounded explicit and non-destructive loader failures | ✓ SATISFIED | Loader code and 11 current boundary/non-destructive tests. |
| BASE-04 | 01-01, 01-02 | Original ROM via real CPU/bus with bounded trace and explicit unsupported behavior | ✓ SATISFIED | Runner direct run and tracer positive/negative tests. |
| BASE-05 | 01-01, 01-04 | Reproducible, rights-cleared fixture provenance | ✓ SATISFIED | Source, MIT notice, manifest, digest, and exact fixture-repro run. |
| BASE-06 | 01-03 | Installed C/C++ consumers using public package | ✓ SATISFIED | Exact native/preview consumer evidence and current local package smoke. |
| BASE-07 | 01-02, 01-04 | Required CI inventory plus sanitizer evidence and fail-closed timeouts | ✓ SATISFIED | Exact required-native run, inventory workflow, watchdog, and recorded 179/179 local inventory. |
| BASE-08 | 01-05 | Revision-linked preview artifacts with installation evidence and honest limits | ✓ SATISFIED | Exact PR #35 required contexts, artifact API metadata, sidecars, package hashes, and extracted package smoke. |

### Test Quality Audit

| Test File | Linked requirement | Active/skipped | Circular | Assertion level | Verdict |
|---|---|---:|---|---|---|
| `tests/test_api.c`, `tests/test_instance_concurrency.c` | BASE-02 | Active; no disabled cases found | No | Behavioral state, budget, trace and isolation assertions | PASS |
| `tests/test_loader.c` | BASE-03 | Active; no disabled cases found | No | Value/status and retained-state assertions | PASS |
| `tests/test_tracer.c` | BASE-04 | Active; no disabled cases found | No | Guest-derived value/status/trace assertions | PASS |
| Fixture reproduction plus `fixtures/tracer/manifest.json` | BASE-05 | Active | No; expected bytes are generated from independent authored assembly using pinned RGBDS, then compared against checked-in ROM | Byte-for-byte and digest equality | PASS |
| Installed C/C++ consumers and package smoke | BASE-01, BASE-06, BASE-08 | Active exact-hosted and local package smoke | No | Compile, link and execute against relocated package | PASS |
| Inventory/sanitizer CI | BASE-07 | Active exact-head jobs | No | Inventory equality, job success, sanitizer execution | PASS |

**Disabled tests on requirements:** 0. **Circular patterns:** 0. **Insufficient assertions:** 0 identified. The optional Clang libFuzzer runtime is unavailable in this local environment; it is not reported as having run. Deterministic sanitizer regressions and hosted ASan/UBSan remain enabled and passed.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---:|---|---|---|
| None in Phase 1 implementation/test artifacts | — | No unresolved debt markers, stubs, or relevant disabled tests found | — | No blocker or warning. |

### Decision Coverage

The GSD decision-coverage query reports 11/11 trackable Phase 1 context decisions honored, with no unhonored decisions.

### Security and Code Review

- `01-SECURITY.md` records 21 threats closed, 0 open, and five low-severity accepted risks that were explicitly dispositioned in the plans.
- `01-REVIEW.md` records a clean final review recheck of the incremental runner/test changes and confirms prior findings were fixed. Its current status is `clean`, with zero critical, warning, or informational findings.

### Hosted Evidence Scope

The tested PR head is `d1e5fdb3b23256f06694cd8d91613638612bccb8`, merged by squash as `96f76dec9a675ede45da8d75bd72a5141c7419e4`. Required checks `required-native` (`37928170860`), `fixture-repro` (`37928170722`), and `preview-package-smoke` (`37928170973`) passed at that exact tested head. The preview run's Linux and macOS artifacts are recorded with API digest/expiry and package SHA in `01-VALIDATION.md`. The open-PR-only wrapper script was not run after merge; equivalent exact-run checks were executed directly against the recorded run IDs, as clearly stated in the validation ledger. No hosted result is claimed for the later merge commit itself.

### Gaps Summary

No phase-goal gaps were found. The bounded tracer/profile is deliberately not hardware-conformance evidence and the project documentation limits that claim; later phases own broader CPU, bus, display, and hardware-qualified behavior. This scope boundary does not block Phase 1's installable original-ROM embedding goal.

---

_Verified: 2026-10-09T12:17:36Z_
_Verifier: the agent (gsd-verifier)_
