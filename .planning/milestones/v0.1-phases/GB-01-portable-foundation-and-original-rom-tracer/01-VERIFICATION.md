---
phase: GB-01-portable-foundation-and-original-rom-tracer
verified: 2026-10-10T15:53:54Z
status: passed
score: 21/21 must-haves verified
covered_files:
  - .github/scripts/check-player-result.sh
  - .github/scripts/safe_extract_package.py
  - .github/scripts/verify-cmake-floor.sh
  - .github/scripts/verify-pr-evidence.sh
  - .github/scripts/verify-test-inventory.sh
  - .github/scripts/wait-exact-head-ci.py
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
covered_digest: "v3:sha256:902857ab2b97a41ec07f8b5980976a73313137b9cc6184083a166a22789e6aa5"
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
**Verified:** 2026-10-10T15:53:54Z
**Status:** passed
**Re-verification:** Yes. Freshness refresh of a `passed` 21/21 report that went stale after PR #54 (Phase 06.1) changed covered files. No previous `gaps:` section existed. Verified on branch `gsd/phase-06.1-verification-refresh`, cut from the PR #54 squash merge `ab76d09` (origin/main).

## User Flow Coverage

The roadmap phase is MVP mode; the user story is a developer-facing build, package, and headless execution path. Automated evidence only; no perceptual or hardware check is part of the goal.

| Step | Expected | Evidence | Status |
|---|---|---|---|
| Configure and build | Documented CMake/Ninja/CTest path builds the C17 core and runner without SDL or network. | `cmake --preset phase1` and `cmake --build --preset phase1` re-run by this verifier and succeeded; `CMakePresets.json`, `CMakeLists.txt`, `README.md`. | VERIFIED |
| Install and embed | Installed package exposes headers and `GabbaBoy::core` to relocated C and C++ consumers. | Full `ctest --preset phase1` re-run passed 184/184, including `preview_package_smoke` and installed consumer tests (C and C++ consumer `main` files, which now also run `audio_api_smoke()`). | VERIFIED |
| Run original ROM | Authored tracer executes guest instructions and yields a guest-derived pass plus bounded trace. | `./build/gabbaboy-runner fixtures/tracer/tracer.gb` returned `outcome=pass stop=budget half_dots=199984 trace_records=8335`, first trace record at PC `0100`. | VERIFIED |
| Handle bounded errors | Bad ROM input and unsupported guest behavior yield explicit bounded outcomes; valid instance preserved. | Loader boundary/non-destructive and tracer failure/unsupported/timeout/capacity cases within the 184/184 pass. | VERIFIED |
| Obtain qualified preview | PR checks gate a revision-linked, smoke-tested preview with explicit limits. | Exact-head hosted evidence for PR #54 head `2a8fd1c`, confirmed read-only with `gh run view` (see Hosted Evidence). | VERIFIED |

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | Configure, build, test, install the C17 core/runner offline after preparation; relocated C and C++ consumers use the installed public target and execute the tracer. | VERIFIED | 184/184 local CTest including `preview_package_smoke`; hosted ci run 38064419789 success. |
| 2 | Independent opaque instances support lifecycle, reset, bounded run, documented contracts, and non-destructive invalid-ROM failures. | VERIFIED | Header/core inspected; lifecycle, reset, bounds, concurrency, loader tests pass in the full run. |
| 3 | Original ROM executes through real CPU/bus with bounded trace and explicit unsupported outcomes; fixture identity, rights, reproduction, applicability, protocol and timeout are recorded. | VERIFIED | Direct runner output; `shasum -a 256 fixtures/tracer/tracer.gb` = `ded6a499...ec8d` equals manifest `sha256`; hosted fixture-repro run 38064419841 success at the PR head. |
| 4 | Required CI verifies mandatory tests and sanitizers ran, and fails closed for missing/skipped/failed/timed-out evidence. | VERIFIED | `ci.yml` `required-native` needs all native, sanitizer, CMake-floor, `player-gate` and `macos-player-package` jobs; any non-success of the first six fails; `check-player-result.sh` fails closed (self-test 14 cases PASS); inventory verifier wiring unchanged. |
| 5 | Remote PR flow produces a source-linked preview package with install smoke and honest limits. | VERIFIED | `preview.yml` three jobs call `wait-exact-head-ci.py`; hosted preview run 38064419803 success. |

**Plan must-haves:** All 16 plan-declared truths (01-01 through 01-05) were rechecked against current files and the executable evidence above; all VERIFIED. Behavioral dependence: none of these truths is a cancellation/state-transition invariant lacking a test; the lifecycle, non-destructive loader, and bounds invariants have named passing tests.

**Score:** 21/21 truths verified (5 roadmap criteria plus 16 plan truths); behavior-unverified: 0.

### Required Artifacts

| Artifact group | Status | Details |
|---|---|---|
| Build/API: `CMakePresets.json`, `CMakeLists.txt`, `include/gabbaboy/gabbaboy.h`, `src/core/gabbaboy.c`, `src/runner/main.c` | VERIFIED | Substantive; build succeeded; runner and tests exercise them. |
| Fixture: `fixtures/tracer/*` | VERIFIED | Digest matches manifest; original source and license present. |
| Tests and consumers: `tests/*`, `tests/consumers/{c,cpp}/*` | VERIFIED | 184/184 pass; consumers exercise the installed package. |
| Package: `cmake/*` | VERIFIED | Relocated package smoke passes. |
| CI/preview: `.github/workflows/{ci,fixture-repro,preview}.yml`, `.github/scripts/*` | VERIFIED | Self-tests pass; hosted runs success (below). |

### Key Link Verification

| From | To | Via | Status |
|---|---|---|---|
| Fixture assembly | Core | ROM bytes decoded by guest CPU/bus | WIRED (tracer tests, runner output) |
| Core | Runner | API result and guest RAM interpreted by runner | WIRED (direct invocation) |
| Public header | Core | Declarations implemented, used by tests and runner | WIRED |
| Loader tests | Core | Invalid parse leaves state unchanged | WIRED (`loader_non_destructive` in suite) |
| CMake package | Config template | Exported `GabbaBoy::core` | WIRED (package smoke) |
| C and C++ consumers | Installed prefix | Relocated configure/build/run | WIRED (`audio_api_smoke()` called at `main.c:231` and `main.cpp:233`) |
| Expected tests | CI | Inventory verifier compares executed vs required | WIRED |
| Fixture manifest | Fixture workflow | Pinned rebuild vs admitted bytes | WIRED (run 38064419841) |
| ci.yml `required-native` | `check-player-result.sh` | Called with gate result, required flag, player result (`ci.yml:198`) | WIRED |
| CI | Preview workflow | Each preview job runs `wait-exact-head-ci.py --require required-native` (macOS player job also requires `macos-player-package`) | WIRED |
| Preview aggregate | Player result | `preview.yml:179` rejects any non-success player result unconditionally | WIRED |

### Data-Flow Trace (Level 4)

| Artifact | Source and flow | Status |
|---|---|---|
| ROM to runner to core to trace/result | Checked-in authored ROM, bounded read, public load/run, CPU/bus writes and readback, runner output | FLOWING |
| Installed package to C/C++ consumers | Install, relocate, `find_package`, `GabbaBoy::core`, consumer calls | FLOWING |
| Preview metadata | Exact-head run IDs and source SHA flow from `wait-exact-head-ci.py` into preview jobs | FLOWING (hosted run 38064419803 logs show three `exact-head-ci: PASS run_id=38064419789` lines) |

### Hosted Evidence (read-only `gh run view`, authenticated)

| Run | Workflow | Head SHA | Conclusion |
|---|---|---|---|
| 38064419789 | ci | `2a8fd1c357262d4b69707b553c603fd441a0f3fa` (PR #54 head) | success |
| 38064419841 | fixture-repro | `2a8fd1c...` | success |
| 38064419803 | preview-package-smoke | `2a8fd1c...` | success; 3 log lines `exact-head-ci: PASS run_id=38064419789` |
| 38064726000 | ci (main push) | `ab76d09c2ee27ba09fc5f3c2510af016aebfdecb` | success |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Full local inventory | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` | 184/184 passed, 2.74 s | PASS |
| Original guest execution | `./build/gabbaboy-runner fixtures/tracer/tracer.gb` | `outcome=pass`, `half_dots=199984`, `trace_records=8335` | PASS |
| Fixture digest | `shasum -a 256 fixtures/tracer/tracer.gb` vs manifest | match | PASS |
| Exact-head gate logic | `python3 .github/scripts/wait-exact-head-ci.py --self-test` | PASS (26 cases) | PASS |
| Player result gate | `bash .github/scripts/check-player-result.sh --self-test` | PASS (14 cases) | PASS |

### Probe Execution

No probe script is declared or applies to this phase. N/A.

### Requirements Coverage

Union of `requirements:` across plans 01-01..01-05 is exactly BASE-01..BASE-08; REQUIREMENTS.md maps all eight to Phase 1 and marks them complete. None orphaned.

| Requirement | Source plans | Status | Evidence |
|---|---|---|---|
| BASE-01 | 01-01, 01-03 | SATISFIED | Local configure/build/ctest/install smoke; CMake-floor hosted job success. |
| BASE-02 | 01-01, 01-02 | SATISFIED | Header/core plus lifecycle/reset/concurrency tests. |
| BASE-03 | 01-02 | SATISFIED | Loader boundary and `loader_non_destructive` tests. |
| BASE-04 | 01-01, 01-02 | SATISFIED | Runner output; tracer positive/negative tests. |
| BASE-05 | 01-01, 01-04 | SATISFIED | Manifest, license, digest match, fixture-repro run success. |
| BASE-06 | 01-03 | SATISFIED | Relocated C/C++ installed consumers pass. |
| BASE-07 | 01-02, 01-04 | SATISFIED | `required-native` aggregate and `check-player-result.sh` fail-closed logic; inventory and sanitizer jobs success in run 38064419789. |
| BASE-08 | 01-05 | SATISFIED | `wait-exact-head-ci.py` exact-head gate; preview run 38064419803 success on PR head with three exact-head PASS lines. |

### Anti-Patterns Found

Grep for `TBD|FIXME|XXX` over `.github/scripts/wait-exact-head-ci.py`, `.github/scripts/check-player-result.sh`, `.github/workflows`, and `tests/consumers` found none. Code review disposition (`01-REVIEW-DISPOSITION.md`): prior IN-01/IN-02 fixed; new IN-03/IN-04 (info, `wait-exact-head-ci.py`) deferred with reason and trigger; open: 0. No blocker or warning.

### Human Verification Required

None. No physical Game Boy hardware qualification, broad compatibility, boot execution, or CGB support is claimed; the phase verifies a bootless DMG-CPU-B software profile.

### Gaps Summary

No phase-goal or requirement gaps. The staleness came from PR #54 changes to `ci.yml`, `preview.yml`, and the consumer mains, plus the new gate scripts; all were inspected, re-tested locally (184/184, both script self-tests), and confirmed against exact-head hosted runs. Covered set: previous set plus `.github/scripts/wait-exact-head-ci.py` and `.github/scripts/check-player-result.sh` (both added).

---

_Verified: 2026-10-10T15:53:54Z_
_Verifier: the agent (gsd-verifier)_
