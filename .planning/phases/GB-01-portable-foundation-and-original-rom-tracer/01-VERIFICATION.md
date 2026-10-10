---
phase: GB-01-portable-foundation-and-original-rom-tracer
verified: 2026-10-10T00:00:00Z
status: passed
score: 21/21 must-haves verified
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
covered_digest: "v3:sha256:e4a348907f6e91c59e122390e30e7b02097a97cc70c986ec629b1847cce8da9d"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 21/21
  gaps_closed: []
  gaps_remaining: []
  regressions: []
---

# Phase 1: Portable Foundation and Original ROM Tracer Verification Report

**Phase Goal:** As a developer, I want to run an original ROM with an installable GB core via a bounded API, so that I can embed it.
**Verified:** 2026-10-10T00:00:00Z
**Status:** passed
**Re-verification:** Yes — verification-freshness refresh of a `passed` 21/21 report (2026-10-09T17:48:35Z) that went stale after covered files changed; no previous `gaps:` section existed. Worktree: branch `gsd/phase-01-verification-refresh` at 9287994 on origin/main 93b53d5.

## User Flow Coverage

The roadmap phase is in MVP mode and its user story passed `user-story.validate` (`valid: true`). The flow is a developer-facing build, package, and headless execution path. Its automated checks provide observable evidence; no perceptual or physical hardware check is part of the goal.

| Step | Expected | Evidence | Status |
|---|---|---|---|
| Configure and build | Developer builds the C17 core and runner with documented CMake/Ninja/CTest commands after dependency preparation, without SDL or network access in the normal build path. | `CMakePresets.json`, `CMakeLists.txt`, `README.md`; recorded exact-revision CMake-floor and native CI evidence in `01-VALIDATION.md`. | ✓ VERIFIED |
| Install and embed | Installed package exposes public headers and `GabbaBoy::core` to external C and C++ consumers. | Current `preview_package_smoke` passed (test 179/179 in this refresh's full run); it archives, relocates, and exercises the installed package and external consumers. | ✓ VERIFIED |
| Run original ROM | Authored tracer ROM executes guest instructions and yields guest-derived pass and bounded trace. | Current runner invocation (`build/gabbaboy-runner fixtures/tracer/tracer.gb`) returned `outcome=pass`, `half_dots=199984`, `trace_records=8335`, starting at PC `0100`; `tracer_success`, `tracer_trace`, and `tracer_smoke` passed. | ✓ VERIFIED |
| Handle bounded errors | Bad ROM input and unsupported guest behavior return explicit bounded outcomes while preserving a valid instance. | Current named loader boundary/non-destructive tests and tracer failure/unsupported/timeout/capacity cases passed. | ✓ VERIFIED |
| Obtain qualified preview | Contributor can use configured PR checks and download only a revision-linked smoke-tested preview with explicit limits. | `01-VALIDATION.md` records exact PR #35 head, required contexts, artifact digests/sidecars/expiry, and extracted Linux/macOS package smoke. This prior hosted evidence is historical (tied to the old PR #35 head) and was not rerun; exact-head CI for this refresh is pending the PR, which is not yet opened. | ✓ VERIFIED |

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | Configure, build, test, and install the C17 core/runner offline after preparation; relocated C and C++ consumers use the installed public target and execute the tracer. | ✓ VERIFIED | Current `preview_package_smoke` passed; exact native and CMake-floor results are recorded in validation evidence. |
| 2 | Independent opaque instances support lifecycle, reset, bounded run, documented model/ownership/thread/error contracts, and non-destructive invalid ROM failures. | ✓ VERIFIED | Public header/core inspected; current lifecycle, reset, bounds, concurrency, and loader tests passed. |
| 3 | Original ROM executes through real CPU/bus code with bounded trace and explicit unsupported outcomes; fixture identity, rights, reproduction, applicability, protocol, and timeout are recorded. | ✓ VERIFIED | Direct runner output plus current tracer and digest tests; fixture source/manifest/license inspected; recorded RGBDS fixture-reproduction run passed. |
| 4 | Required CI verifies mandatory tests and sanitizers actually ran, and fails closed for missing/skipped/failed/timed-out evidence. | ✓ VERIFIED | Workflow, expected inventory, verifier and timeout wiring inspected; exact hosted `required-native` evidence and ASan/UBSan result are recorded. |
| 5 | Remote PR flow produces a source-linked preview package with install smoke and honest limits. | ✓ VERIFIED | Exact PR #35 checks and downloaded package evidence are recorded in `01-VALIDATION.md`; packages are explicitly run-scoped, Linux/macOS only, and not durable releases. |

**Plan must-haves:** All 16 plan-declared truths were also checked against current files and executable evidence.

| Plan | Must-have truth | Status | Evidence |
|---|---|---|---|
| 01-01 | Original tracer runs through public C API and CPU/bus path. | ✓ VERIFIED | Current runner invocation and tracer tests pass. |
| 01-01 | Guest checks RAM and exposes distinct success/failure states. | ✓ VERIFIED | Tracer positive and negative controls pass; trace shows guest writes/readback. |
| 01-01 | Bounded half-dot progress, structured stop, and retained trace are returned. | ✓ VERIFIED | Current output reports bounded budget and trace; run-bounds/trace-capacity tests pass. |
| 01-01 | Profile, fixture, opcode inventory, and limits are precise. | ✓ VERIFIED | Header, manifest, README, and fixture evidence specify bootless DMG-CPU-B scope and exclusions. |
| 01-02 | Opaque instance lifecycle and contract are documented and usable independently. | ✓ VERIFIED | Header/core inspected; lifecycle, reset, independence, and concurrency cases pass. |
| 01-02 | Invalid/truncated/oversized/unsupported ROMs fail without replacing valid state. | ✓ VERIFIED | Current loader cases include `loader_non_destructive`; all pass. |
| 01-02 | Underflow, unsupported opcode, trace exhaustion, guest failure, and timeout remain distinct bounded results. | ✓ VERIFIED | Current bounded API and tracer outcome cases pass. |
| 01-03 | Documented offline core/runner configure/build/test/install path works. | ✓ VERIFIED | Current package smoke passes; exact floor and native hosted runs are recorded. |
| 01-03 | Relocated external C/C++ consumers use only installed public package and run tracer. | ✓ VERIFIED | Current `preview_package_smoke` passed; hosted consumer evidence is recorded. |
| 01-04 | Explicit native Linux/macOS/Windows lanes include Linux sanitizers and installed consumers. | ✓ VERIFIED | Workflow inspection plus recorded exact-head native matrix and sanitizer run. |
| 01-04 | Missing/skipped/failed/timed-out required cases cannot pass CI. | ✓ VERIFIED | Inventory script, aggregate gate, and CTest timeouts inspected; exact hosted aggregate passed. |
| 01-04 | Pinned RGBDS fixture rebuild compares bytes; default path uses checked-in bytes. | ✓ VERIFIED | Fixture workflow/manifest inspected; recorded reproduction run and current `fixture_digest` pass. |
| 01-05 | Linux/macOS packages are made only after same-revision installed smoke and include executable package contents. | ✓ VERIFIED | Workflow and package smoke inspected; recorded extracted exact-run packages and installed consumer evidence. |
| 01-05 | Metadata binds revision/digest/smoke/limits/retention; no Windows package. | ✓ VERIFIED | Workflow sidecar checks and validation ledger reviewed; report names run-scoped retention and platform scope. |
| 01-05 | Remote PR required checks and exact-source package evidence exist. | ✓ VERIFIED | Recorded PR #35 exact head, required contexts, source SHA, package digests, and smoke evidence. |
| 01-05 | PR instructions reflect configured workflow and limitations. | ✓ VERIFIED | Current README documents required checks, run-scoped artifact retrieval, and support exclusions. |

**Score:** 21/21 declared truths verified (5 roadmap criteria plus 16 plan truths); behavior-unverified: 0.

### Required Artifacts

All plan-declared artifacts passed `query verify.artifacts`: 01-01 5/5, 01-02 3/3, 01-03 5/5, 01-04 4/4, and 01-05 6/6. The current code was inspected for substantive behavior; the current relocated package smoke exercised the package path.

| Artifact group | Status | Evidence |
|---|---|---|
| Build and public API: `CMakePresets.json`, `include/gabbaboy/gabbaboy.h`, `src/core/gabbaboy.c`, `src/runner/main.c`, `CMakeLists.txt` | ✓ VERIFIED | Substantive C17 API/core/runner and build/install targets; direct ROM run and focused tests pass. |
| Fixture: `fixtures/tracer/{manifest.json,tracer.asm,tracer.gb,LICENSE.txt}` | ✓ VERIFIED | Original source/notice, digest, pinned recipe, boot/model applicability, protocol, and timeout; digest and hosted reproduction evidence pass. |
| Tests: `tests/test_api.c`, `tests/test_instance_concurrency.c`, `tests/test_loader.c`, `tests/test_tracer.c`, consumer sources/CMake, inventory and test CMake | ✓ VERIFIED | 179 current checks pass (including the focused Phase 1 cases), including C/C++ relocation package smoke. |
| Package: `cmake/GabbaBoyConfig.cmake.in`, `cmake/VerifyInstalledPackage.cmake`, `cmake/PreviewPackageSmoke.cmake`, `cmake/RunInstalledConsumer.cmake`, `cmake/VerifyArtifactSidecar.cmake`, `cmake/VerifyFixture.cmake`, `cmake/ExpectedTests.cmake` | ✓ VERIFIED | CMake target/export and relocated package flow traced; current package smoke passes. |
| CI and preview: `.github/workflows/{ci,fixture-repro,preview}.yml`, `.github/scripts/{verify-cmake-floor.sh,verify-pr-evidence.sh,verify-test-inventory.sh,safe_extract_package.py}` | ✓ VERIFIED | Fail-closed workflow and package evidence wiring inspected; prior exact-revision hosted evidence is recorded. |
| Contributor/evidence: `README.md`, `01-VALIDATION.md`, `01-SECURITY.md`, `01-REVIEW.md`, `01-REVIEW-FIX.md`, `01-REVIEW-DISPOSITION.md`, `01-UI-REVIEW.md` | ✓ VERIFIED | Current scope and evidence inspected; security records zero open threats and review disposition is clean. |

### Key Link Verification

The generic key-link query reported lexical false negatives for most C/CMake/CI connections. Manual source tracing and executable smoke provide direct evidence for each declared link:

| From | To | Via | Status | Evidence |
|---|---|---|---|---|
| Fixture assembly | Core | ROM bytes decode through guest CPU/bus | ✓ WIRED | Tracer guest outcome and trace tests pass. |
| Core | Runner | API result and guest RAM interpreted by runner | ✓ WIRED | Runner links public core and direct invocation reports guest-derived pass. |
| Public header | Core | API declarations implemented in instance-owned core | ✓ WIRED | CMake compiles core; tests and runner call public functions. |
| Loader tests | Core | Invalid parsing leaves live state unchanged | ✓ WIRED | `loader_non_destructive` passes. |
| API tests | Header | Public lifecycle/bounds exercised through public contract | ✓ WIRED | Test sources use public header; current lifecycle/bounds tests pass. |
| Tracer tests | Fixture manifest | Protocol and expected guest states follow fixture identity | ✓ WIRED | Manifest/digest checks plus tracer positive/negative tests pass. |
| CMake package | Package config template | Exported `GabbaBoy::core` config | ✓ WIRED | Package generation includes config template; relocated package smoke passes. |
| C consumer | Installed prefix | Configure/build/run against relocated package | ✓ WIRED | Current package smoke builds and runs external consumer. |
| C++ consumer | Installed prefix | Configure/build/run against relocated package | ✓ WIRED | Current package smoke builds and runs external consumer. |
| Expected tests | CI | Executed inventory compared with required cases/jobs | ✓ WIRED | Workflow invokes verifier; exact hosted aggregate passed. |
| Fixture manifest | Fixture workflow | Pinned rebuild compared to admitted bytes | ✓ WIRED | Workflow comparison and recorded exact reproduction run passed. |
| CI | Preview workflow | Preview gated by same-revision required checks | ✓ WIRED | Workflow dependency and exact source SHA evidence inspected. |
| Preview workflow | Installed package archive | Smoke exact extracted archive before upload | ✓ WIRED | Current local package smoke and recorded hosted archive consumer tests pass. |

### Data-Flow Trace (Level 4)

| Artifact | Data | Source and flow | Real data | Status |
|---|---|---|---|---|
| ROM → runner → core → trace/result | ROM bytes, guest RAM, stop status, trace | Checked-in authored ROM → bounded read → public load/run → CPU/bus writes/readback → runner output | Yes; outcome follows guest marker and trace. | ✓ FLOWING |
| Installed package → C/C++ consumers | Public header/library/export | Install → archive/relocate → `find_package`/`GabbaBoy::core` → consumer calls | Yes; current package smoke passed. | ✓ FLOWING |
| Preview metadata | Source SHA, archive/package digest, smoke and retention | Exact hosted run metadata and extracted artifact sidecars | Yes; prior validation ledger records actual API/download checks. | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Full local inventory (loader, tracer, lifecycle, concurrency, fixture, runner, installed package) | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` (re-run by verifier; orchestrator also ran it) | 179/179 passed, 2.23 s ctest time; includes `preview_package_smoke` (1.38 s). | ✓ PASS |
| Original guest execution | `./build/gabbaboy-runner fixtures/tracer/tracer.gb` | `outcome=pass`, `half_dots=199984`, `trace_records=8335`; trace begins at PC `0100`. | ✓ PASS |
| Fixture digest | `shasum -a 256 fixtures/tracer/tracer.gb` vs `fixtures/tracer/manifest.json` | `ded6a499...ec8d` matches manifest `sha256`. | ✓ PASS |
| Required-CI gate logic | Inspect `.github/workflows/ci.yml` `required-native` aggregate | `PLAYER_REQUESTED` is true on `pull_request`; a non-success player result fails the gate; pushes accept skipped. `macos-player-package` is in `needs`. Consistent with removal of the label gate. | ✓ PASS (static inspection) |

### Probe Execution

No phase-declared or discovered `probe-*.sh` applies to this phase. Named tests and the original runner exercise the declared outcomes.

| Probe | Result | Status |
|---|---|---|
| None declared/discovered | Probe discovery found no applicable Phase 1 probe script. | N/A |

### Requirements Coverage

Every requirement ID declared across the five plans was checked against `.planning/REQUIREMENTS.md`. Their union is exactly BASE-01 through BASE-08, each mapped to Phase 1; there are no additional Phase 1 requirements orphaned from plans.

| Requirement | Source plans | Description | Status | Evidence |
|---|---|---|---|---|
| BASE-01 | 01-01, 01-03 | Offline documented CMake build/test/install | ✓ SATISFIED | README/build files, current package smoke, recorded CMake-floor/native CI. |
| BASE-02 | 01-01, 01-02 | Independent opaque instances and lifecycle/ownership rules | ✓ SATISFIED | Header/core and lifecycle/reset/concurrency tests. |
| BASE-03 | 01-02 | Bounded explicit non-destructive loader errors | ✓ SATISFIED | Core loader and current boundary/non-destructive tests. |
| BASE-04 | 01-01, 01-02 | Original ROM CPU/bus path, bounded trace, explicit unsupported outcomes | ✓ SATISFIED | Direct runner invocation and positive/negative tracer tests. |
| BASE-05 | 01-01, 01-04 | Reproducible rights-cleared fixture provenance | ✓ SATISFIED | Source, license, manifest, digest, recorded RGBDS fixture-reproduction result. |
| BASE-06 | 01-03 | Installed C/C++ consumer package | ✓ SATISFIED | Current relocated package smoke and exact hosted consumer evidence. |
| BASE-07 | 01-02, 01-04 | Required test inventory, sanitizer evidence, fail-closed timeouts | ✓ SATISFIED | Workflow/inventory/watchdog inspection and recorded exact-hosted required result. |
| BASE-08 | 01-05 | Revision-linked preview artifact and honest limits | ✓ SATISFIED | Exact PR #35 checks, artifact digests/sidecars, extracted consumer smoke, expiry record. |

### Test Quality Audit

| Test file or evidence | Linked requirement | Active/skipped | Circular | Assertion strength | Verdict |
|---|---|---|---|---|---|
| `tests/test_api.c`, `tests/test_instance_concurrency.c` | BASE-02 | Active focused cases | No | State, output, budget, and isolation values | PASS |
| `tests/test_loader.c` | BASE-03 | Active focused cases | No | Error values and retained-state assertions | PASS |
| `tests/test_tracer.c` | BASE-04 | Active focused cases | No | Guest-derived values/status/trace | PASS |
| Fixture reproduction and manifest | BASE-05 | Active current digest and recorded hosted rebuild | No | Byte/digest equality from authored source | PASS |
| Installed C/C++ package consumers | BASE-01, BASE-06, BASE-08 | Active current smoke and recorded hosted smoke | No | Compile, link, relocate, and execute | PASS |
| Inventory/sanitizer CI | BASE-07 | Active recorded exact-head jobs | No | Executed inventory equality and sanitizer run | PASS |

Disabled requirement tests: 0 found. Circular test patterns: 0 identified. Insufficient assertions: 0 identified. The optional local Clang libFuzzer runtime is not claimed as run; it is outside these Phase 1 success criteria.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---:|---|---|---|
| None in Phase 1 implementation/test artifacts | — | No unresolved debt markers, stubs, relevant disabled tests, or unlicensed fixture assets found. Ten plan prohibitions were checked against source, package, fixture, workflow, and validation evidence. | — | No blocker or warning. |

The Phase 1 context decision gate reports 11/11 trackable decisions honored. Review evidence records the final Windows thread-creation cleanup and runner-help fixes; security evidence reports zero open threats. Neither report substitutes for the current focused test run.

### Human Verification Required

None. This foundation phase has no user-facing UI or physical-device requirement. The phase verifies a bootless DMG-CPU-B software profile and does **not** qualify physical Game Boy hardware, broad compatibility, full CPU/gameplay, boot execution, or CGB support.

### Gaps Summary

No phase-goal or requirement gaps were found. The stale status was an evidence-fingerprint freshness issue caused by: `.github/workflows/ci.yml` and `preview.yml` (GB-03 PR #40 removed the `labeled` trigger and `run-macos-player` gate, so the macOS player lane is now required on every pull request; the aggregate gate, exact-head lookup, and job names were inspected and are consistent), `.gitignore` (`__pycache__/`), `README.md` (PR #35 evidence paragraph), and refreshed phase docs. None alter the Phase 1 core, API, fixture, or tests. This refresh re-ran the full local suite (179/179) and the direct original-ROM execution. The fresh code review recorded 0 critical / 0 warning / 2 info findings, both deferred in `01-REVIEW-DISPOSITION.md` with rationale. Prior exact-head hosted CI, fixture reproduction, and preview artifact evidence (PR #35) is historical, reused from the validation ledger, and not rerun; **exact-head hosted CI for this refresh revision is pending the PR, which has not been opened, and no remote result is claimed for it.** No physical Game Boy hardware qualification is claimed.

---

_Verified: 2026-10-10T00:00:00Z_
_Verifier: the agent (gsd-verifier)_
