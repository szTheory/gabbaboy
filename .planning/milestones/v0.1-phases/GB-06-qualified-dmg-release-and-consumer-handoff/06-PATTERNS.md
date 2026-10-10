# Phase GB-06: Qualified DMG Release and Consumer Handoff - Pattern Map

**Mapped:** 2026-10-08  
**Files analyzed:** 20 anticipated additions/modifications (some locations are planner choices)  
**Analogs found:** 19 / 20

## File Classification

| New/Modified File | Role | Data Flow | Closest Tracked Analog | Match Quality |
|---|---|---|---|---|
| `.github/workflows/release-please.yml` (suggested) | config/workflow | event-driven | `.github/workflows/ci.yml` | role-match |
| `.github/workflows/release.yml` (suggested) | config/workflow | event-driven, artifact I/O | `.github/workflows/preview.yml` | role-match |
| `cmake/VerifyReleaseReceipt.cmake` or script equivalent (suggested) | utility | file-I/O/transform | `cmake/VerifyArtifactSidecar.cmake` | exact |
| `cmake/PreviewPackageSmoke.cmake` / installed-package tests | utility/test | file-I/O, request-response | `cmake/PreviewPackageSmoke.cmake` | exact |
| `tests/consumers/c/main.c` (extended) | test / consumer example | request-response, file-I/O | `tests/consumers/c/main.c` | exact |
| `tests/consumers/cpp/main.cpp` (possible extension) | test | request-response, file-I/O | `tests/consumers/cpp/main.cpp` | exact |
| `tests/CMakeLists.txt` | config/test | batch | `tests/CMakeLists.txt` | exact |
| `tests/expected-tests.txt` | config | batch | `tests/expected-tests.txt` | exact |
| `tests/scripts/verify-phase3-player.sh` | utility / package smoke | file-I/O, event-driven process smoke | `tests/scripts/verify-phase3-player.sh` | exact |
| `tests/scripts/measure-core-workload.sh` (suggested) | utility | batch / transform | `tests/scripts/measure-audio-playback.sh` | role-match |
| `tests/test_loader_fuzz.c` or libFuzzer target | test | transform / batch | `tests/test_loader.c` | exact |
| `tests/test_battery_fuzz.c` or new libFuzzer target | test | stateful request-response | `tests/test_battery_fuzz.c` | exact |
| `tests/test_loader.c`, boundary cases | test | request-response | `tests/test_loader.c` | exact |
| `docs/support-ledger-v0.1.0.md` + validator (suggested) | documentation / utility | transform | `docs/preview.md`, `cmake/VerifyArtifactSidecar.cmake` | role-match |
| `examples/consumer-c/` or installed C example (suggested) | example | request-response, file-I/O | `tests/consumers/c/main.c` | role-match |
| `README.md` | documentation | — | `README.md` | exact |
| `docs/preview.md` | documentation | — | `docs/preview.md` | exact |
| `docs/cartridge-and-saves.md` | documentation | — | `docs/cartridge-and-saves.md` | exact |
| new upgrade/troubleshooting/Playstead handoff doc (location open) | documentation | — | `docs/preview.md`, `docs/cartridge-and-saves.md` | role-match |
| release notes, SHA manifest and support sidecar (generated/release assets) | documentation / config | file-I/O | `tests/scripts/verify-phase3-player.sh` receipt generation | role-match |

The phase artifacts do not lock every new filename. Keep the proposed paths above adaptable; additions should extend current CMake, `tests/`, `.github/workflows/`, and `docs/` conventions. Existing analogs listed here were checked with `git ls-files`; no ignored runtime mirror paths are used.

## Pattern Assignments

### Release workflow and release-please workflow

**Analog:** `.github/workflows/ci.yml` and `.github/workflows/preview.yml`

The CI workflow uses minimal top-level permissions, explicit runner labels/timeouts, and full commit SHA action references. Its native jobs install the package and verify the actual CTest inventory (`.github/workflows/ci.yml:8-30,52-82`). The preview workflow first queries a completed CI run for the exact PR head and checks the required job result before checking out that exact SHA (`.github/workflows/preview.yml:21-50`). Reuse this exact-SHA/run-event/job-result gate for any release PR status gate; a workflow dispatch is not evidence for a PR context.

**One-build/package evidence pattern** (`.github/workflows/preview.yml:51-79`):

```yaml
- name: Configure, build, and install
  run: |
    cmake --preset phase1
    cmake --build --preset phase1 --verbose
    cmake --install build --prefix build/preview-stage
- name: Smoke extracted archive and external consumers
  run: ctest --test-dir build --output-on-failure --no-tests=error -R '^preview_package_smoke$'
- name: Write package evidence sidecar
  run: |
    archive=build/preview-package-smoke/installed-prefix.tar.gz
    digest=$(cmake -E sha256sum "$archive" | cut -d ' ' -f 1)
```

Release publishing is new; do not treat the preview workflow as a release implementation. Preserve the phase decision to build once from a clean trusted tag, draft and attach those bytes, verify downloads, and publish only after all current required checks pass. Keep release job permissions least-privilege, pin actions to reviewed full SHAs, do not execute untrusted PR code in a privileged event, and fail closed on missing/skipped/stale/failing evidence. The existing workflow analog does not supply a release-please manifest or immutable publication gate.

### Release receipt, exact-byte verifier, SHA manifest and trust state

**Analog:** `cmake/VerifyArtifactSidecar.cmake` and `tests/scripts/verify-phase3-player.sh`

The sidecar verifier requires its input paths, validates a full source revision, checks a 64-character package digest against actual bytes, requires a passing smoke, and checks retention and nonempty capability limits (`cmake/VerifyArtifactSidecar.cmake:1-64`). Adapt that fail-closed structure for version/tag/source/build-toolchain/fixture-corpus identity, per-asset hashes, downloaded smoke receipts, and explicit signed/notarized status.

**Concrete digest checks** (`cmake/VerifyArtifactSidecar.cmake:30-49`):

```cmake
string(JSON sidecar_package_sha ERROR_VARIABLE package_error GET "${sidecar_json}" package_sha256)
if(NOT package_error STREQUAL "NOTFOUND")
  message(FATAL_ERROR "Artifact sidecar has no valid package_sha256: ${package_error}")
endif()
file(SHA256 "${GBB_PACKAGE_FILE}" actual_package_sha)
if(NOT sidecar_package_sha STREQUAL actual_package_sha)
  message(FATAL_ERROR "Artifact package digest mismatch: sidecar ${sidecar_package_sha}, archive ${actual_package_sha}")
endif()
```

The macOS script checks the exact checkout SHA and clean tracked source state, receipt schema/result, archive hash, and then extracts and smoke-tests the candidate (`tests/scripts/verify-phase3-player.sh:28-54,56-98`). Its final receipt binds build and consumer run IDs/attempts, source revision, package digest, fixture digests, and explicit false trust/hardware claims (`tests/scripts/verify-phase3-player.sh:250-334`). Use that evidence chain for release assets, while ensuring the verifier reads the downloaded release bytes and no post-qualification rebuild occurs.

### Relocated CMake consumers and Windows package lane

**Analog:** `cmake/PreviewPackageSmoke.cmake`, `cmake/VerifyInstalledPackage.cmake`, `cmake/RunInstalledConsumer.cmake`, and `tests/consumers/{c,cpp}`

The strongest analog stages and archives an install, extracts it elsewhere, verifies the installed contents/metadata, configures external C and C++ projects against the extracted prefix, builds them, and executes each with the installed fixture (`cmake/PreviewPackageSmoke.cmake:63-111`). The consumer configuration supplies only `CMAKE_PREFIX_PATH` and the installed fixture path (`:76-82`). `VerifyInstalledPackage.cmake` checks required package/fixture files and fixture digests, rejects source/build paths embedded in package metadata, and runs the installed runner from an unrelated working directory (`cmake/VerifyInstalledPackage.cmake:19-72,76-89`).

**External consumer pattern** (`cmake/PreviewPackageSmoke.cmake:76-110`):

```cmake
foreach(language IN ITEMS c cpp)
  set(consumer_configure_command
    "${GBB_CMAKE_COMMAND}" -S "${source_dir}/tests/consumers/${language}"
    -B "${smoke_root}/consumer-${language}" -G "${GBB_GENERATOR}"
    "-DCMAKE_PREFIX_PATH=${extracted_prefix}"
    "-DGBB_TRACER_ROM=${extracted_prefix}/share/gabbaboy/fixtures/tracer/tracer.gb")
  execute_process(COMMAND ${consumer_configure_command} RESULT_VARIABLE configure_result)
  # Fail on configure/build errors, then execute the consumer with installed bytes.
endforeach()
```

`tests/consumers/c/main.c:57-113` is the closest example/API analog: it reads a ROM supplied on argv, creates and loads a profile instance, queues timestamped inputs, runs with bounded time and fixed caller-owned trace/diagnostic/frame buffers, checks output bounds, destroys the instance, and has a separate battery API smoke. Add audio and host-owned save import/export to this example using the public header. Keep filesystem ownership in the example host. `tests/consumers/cpp/main.cpp:58-113` mirrors the public API smoke in C++.

Current CI already has Windows native package install and installed C/C++ inventory; don't duplicate that lane. The remaining addition should qualify downloaded Windows release bytes only if a Windows core archive is published. The native workflow pattern is `.github/workflows/ci.yml:52-82`; installed consumer registrations are in `tests/CMakeLists.txt:273-302`.

### Player package smoke

**Analog:** `tests/scripts/verify-phase3-player.sh`

Extend this script rather than introducing an installer framework. It pins SDL version/archive SHA (`:4-17`), gates expected revision and relevant dirty source (`:28-54`), validates receipt and package digest before extraction (`:56-98`), checks packaged legal notices/fixture metadata and runtime linkage (`:99-145`), and later emits a verification receipt with source/package/fixture identity and trust limits (`:250-334`). The script already sets SDL audio to dummy and restricts the package test to macOS arm64 (`:350-359`). Follow its process-level, extracted-package smoke and fail-on-missing assertions for input, completed frame, PCM, save, exit, and fresh-process reopen. Preserve the explicit boundary that dummy SDL tests do not qualify physical devices or perception.

### Support/measurement ledger and reproducible workload receipt

**Analog:** `docs/preview.md`, `docs/cartridge-and-saves.md`, `tests/scripts/measure-audio-playback.sh`, and `cmake/VerifyArtifactSidecar.cmake`

The docs lead with exact model and limitations, enumerate supported cartridge/API behavior, and distinguish software policy from hardware claims (`docs/cartridge-and-saves.md:1-6,8-26,44-65`; `docs/preview.md:1-20,61-71`). A versioned support ledger should copy that claim style, but bind entries to release SHA and fixture/corpus revisions, list the three-case eligible denominator, excluded cases, failures, and known issues; do not convert it into a compatibility percentage.

The measurement script verifies source revision, relevant dirty state, release build mode, and legal fixture size/digest before running a fixed workload (`tests/scripts/measure-audio-playback.sh:60-91`). It parses a single structured metric record, rejects duplicate/missing fields, validates fixed model/workload/sink/format and exact sample counts (`:93-145`), compares partition digests/counts, and writes a JSON receipt with provenance (`:173-220`). Reuse the verification and receipt style for the core speed/memory/allocation and trace/no-trace workload. Add raw samples, warm-up policy, build/compiler/runner identity, uncertainty, and output-digest equivalence; keep budgets advisory until variance is measured. `tests/test_audio_no_alloc.c:38-97` is the narrow allocation assertion analog.

### Loader/stateful battery fuzz and boundary regressions

**Analog:** `tests/test_battery_fuzz.c`, `tests/test_loader.c`, `tests/CMakeLists.txt`, `tests/expected-tests.txt`, `.github/scripts/verify-test-inventory.sh`

`test_battery_fuzz.c` is a deterministic bounded stateful regression: fixed PRNG seed and iteration count, explicit ROM/input caps, generation checks, canary-protected output, failed-import/load atomicity, and bounded guest run budget (`tests/test_battery_fuzz.c:6-15,41-48,55-99,110-147`). Keep this as fast deterministic regression even when a separate libFuzzer entry point exists. `tests/test_loader.c:118-172` already checks truncated, oversized, malformed, declared-size mismatch, unsupported cartridge, and non-destructive failed load cases; extend it for the named boundary gaps instead of duplicating cases.

Register new deterministic cases in `tests/CMakeLists.txt` and `tests/expected-tests.txt`. The CMake test file uses explicit executable/link/language registration and named cases (`tests/CMakeLists.txt:31-35,127-132`); the expected inventory verifier rejects missing reports, failures, skipped cases, and inventory drift (`.github/scripts/verify-test-inventory.sh:9-23,37-44`). Keep longer libFuzzer exploration separate from exact deterministic CTest inventory, cap input/work/resources, and replay every minimized finding as a named regression. No analog exists for the new libFuzzer entry-point/runner configuration itself; use the compiler-integrated runtime described in RESEARCH.md.

### Adopter docs and Playstead handoff

**Analog:** `README.md`, `docs/preview.md`, `docs/audio-and-playback.md`, `docs/cartridge-and-saves.md`

README currently gives build/install commands and an embedding contract with ownership, half-dot bounds, event behavior, and explicit API/ABI limitations (`README.md:22-65,73-104`). `docs/cartridge-and-saves.md` is the best save/recovery source: caller-owned battery buffers and failure atomicity (`:44-65`), versioned player envelope and identity (`:67-96`), failure/retry and filesystem replacement behavior (`:98-123`), and recovery (`:125-130`). Keep these claims synchronized with generated release/support metadata and add the native consumer example and honest Playstead current-state distinction. Research says the sibling's current adapter is GBA/mGBA only; this phase should document a future C seam and not create a sibling integration.

## Shared Patterns

### Exact source and artifact identity

**Sources:** `tests/scripts/verify-phase3-player.sh:28-54,56-98,250-334`; `cmake/VerifyArtifactSidecar.cmake:13-49`  
**Apply to:** release workflow, release receipts, player package, support ledger, measurement output.

Require full source SHA, expected version/tag, clean source state where release build requires it, exact fixture/corpus identities, and archive SHA computed from the bytes being consumed. Missing, malformed, mismatched, skipped, or non-passing evidence is fatal. Keep signing/notarization booleans tied to verification of the final distributed bytes.

### Bounded external inputs and failure atomicity

**Sources:** `tests/test_battery_fuzz.c:6-15,55-99,110-147`; `tests/test_loader.c:137-170`; `tests/consumers/c/main.c:18-54`  
**Apply to:** consumer example, fuzz targets, loader/save regressions.

Cap buffers and guest work before use; exercise truncated/oversized lengths and canaries; assert rejected operations preserve live state and generations. Keep host file I/O explicit in the example, outside core ownership.

### Fail-closed inventory and claims

**Sources:** `tests/CMakeLists.txt:31-35,258-302`; `tests/expected-tests.txt:1-20`; `.github/scripts/verify-test-inventory.sh:12-42`; `cmake/VerifyArtifactSidecar.cmake:21-64`  
**Apply to:** test registration, CI gates, release/support/measurement validators.

Reject empty or missing evidence, skipped/failing tests, unexpected inventory changes, missing metadata, digest mismatch, and claims without a supporting receipt. Runner labels are evidence for those observed combinations only; do not describe them as minimum OS or full-platform compatibility promises.

## No Analog Found

| File / capability | Role | Data Flow | Reason |
|---|---|---|---|
| New libFuzzer target and bounded long-run workflow | test/config | transform, batch | Existing `tests/test_battery_fuzz.c` is a deterministic seeded CTest regression, not a compiler-integrated coverage-guided fuzz target. Use RESEARCH.md's Clang libFuzzer guidance; preserve current CTest fallback. |

## Metadata

**Analog search scope:** `.github/workflows/`, `.github/scripts/`, `cmake/`, `tests/`, `tests/consumers/`, `tests/scripts/`, `docs/`, root `README.md`.  
**Files scanned:** 20 anticipated additions/modifications classified; 18 tracked analog files were read as analogs in targeted ranges.  
**Pattern extraction date:** 2026-10-08
