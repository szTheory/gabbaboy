---
phase: 01-portable-foundation-and-original-rom-tracer
plan: 05
subsystem: infra
tags: [github-actions, cmake, package-smoke, artifact-evidence, privacy]
requires:
  - phase: GB-01 Plans 01-04
    provides: "Portable tracer, bounded API and loader, installed consumers, fixture reproduction, and required native CI"
provides:
  - "Revision-bound Linux x64 and macOS arm64 preview packages, each smoke-tested after extraction with the installed runner and external C/C++ consumers"
  - "An exact-PR-SHA verifier for required contexts, successful workflow runs, artifact API metadata, downloaded archive digests, sidecars, and installed-package behavior"
  - "A public contributor PR/check/artifact path with run-scoped retention and capability limits documented from hosted evidence"
affects: [phase-01-verification, phase-02-cpu-bus-time, contributor-workflow, preview-artifacts]
actuals:
  tokens: 21423
  tasks: 3
  commits: 6
commits: 6
plan_head_before: 93cab51708a11c168e1afffb27a78aa66ad858e9
plan_head_after: 59b104ef5ba95f7dd48e6dd3f4732f49f4cc77de
tech-stack:
  added: []
  patterns:
    - "Qualify uploaded package bytes only after testing the extracted archive and both external consumer languages against the same installed prefix"
    - "Bind every required check, workflow run, sidecar, downloaded package, and artifact API expiry to one exact PR head SHA"
    - "Use run-scoped artifact language and distinguish GitHub artifact digests from package SHA-256 values and configured retention"
key-files:
  created:
    - .github/scripts/verify-pr-evidence.sh
    - .github/workflows/preview.yml
    - cmake/PreviewPackageSmoke.cmake
    - cmake/VerifyArtifactSidecar.cmake
  modified:
    - CMakeLists.txt
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - cmake/RunInstalledConsumer.cmake
    - cmake/VerifyInstalledPackage.cmake
    - .github/scripts/verify-test-inventory.sh
    - README.md
    - .planning/phases/GB-01-portable-foundation-and-original-rom-tracer/01-VALIDATION.md
    - .planning/phases/GB-01-portable-foundation-and-original-rom-tracer/continue.md
key-decisions:
  - "Build preview archives only for Linux x64 and macOS arm64; do not publish a Windows preview package or infer product OS minimums from CI runner labels."
  - "Use exact PR source revisions and verified run-scoped artifact API expiry as evidence; temporary Actions artifacts are not durable releases."
  - "Keep sanitizer linker propagation confined to extracted-consumer test configuration so the normal exported package contract stays unchanged."
patterns-established:
  - "Forward the executable suffix explicitly into CMake script mode and nested smoke projects so Windows paths resolve correctly."
  - "Normalize CRLF in Windows CTest inventory output before comparing it with the checked-in required case list."
  - "Create and inspect actual gzip tar archives for the portable preview package transport."
requirements-completed: [BASE-08]
coverage:
  - id: D1
    description: "Linux x64 and macOS arm64 archives preserve the full installed tree and pass relocated runner plus external C/C++ consumer smoke."
    requirement: BASE-08
    verification:
      - kind: integration
        ref: "Local preview_package_smoke at Plan 05 Task 1 and exact hosted preview run 37131835440; both downloaded packages passed runner, C consumer, and C++ consumer checks."
        status: pass
    human_judgment: false
  - id: D2
    description: "The public PR workflow, required checks, and artifact evidence are verified against one exact source revision."
    requirement: BASE-08
    verification:
      - kind: integration
        ref: "sh .github/scripts/verify-pr-evidence.sh; exact sample SHA 59b104ef5ba95f7dd48e6dd3f4732f49f4cc77de, CI run 37131835427, fixture run 37131835525, preview run 37131835440."
        status: pass
    human_judgment: false
  - id: D3
    description: "Contributor documentation distinguishes temporary artifacts, actual API expiry, package hashes, capability limits, and hosted evidence."
    requirement: BASE-08
    verification:
      - kind: other
        ref: "README.md and 01-VALIDATION.md record PR #1 and the observed exact-SHA run-scoped sample; the new planning metadata SHA must receive a fresh exact-SHA verifier run before phase sign-off."
        status: pass
    human_judgment: false
duration: 84min
completed: 2026-10-03
status: complete
---

# Phase 1 Plan 5: Revision-linked Foundation Preview Packages Summary

**Linux and macOS preview archives now carry an extracted-package smoke result, exact source revision, package digest, consumer evidence, and GitHub-reported run expiry.**

## Performance

- **Duration:** 84 min, measured from the first Plan 05 task commit through documentation preparation.
- **Started:** 2026-10-03T13:59:31Z (first Plan 05 task commit).
- **Completed:** 2026-10-03T15:23:44Z.
- **Tasks:** 3.
- **Files modified:** 17 across the plan commit range and current documentation changes.

## Accomplishments

- Added `preview_package_smoke`, which installs the project, creates a real gzip tar archive, extracts it into a relocated prefix, and runs the extracted runner and external C/C++ consumers. The executable suffix is forwarded explicitly through CMake script mode, and sanitizer linker flags are passed only to the test consumer configuration.
- Added Linux x64 and macOS arm64 preview workflows gated by required native CI and installed-package smoke. The workflow preserves the exact tested archive bytes and records source SHA, package SHA-256, smoke result, capability limits, and configured 14-day retention. No Windows package is published.
- Created `.github/scripts/verify-pr-evidence.sh` and the sidecar verifier to check the exact local/PR/run/artifact chain, including required status contexts, fixture regeneration, both platform smoke jobs, archive digests, and actual API `created_at`/`expires_at` values.
- Created public repository `https://github.com/szTheory/gabbaboy`, opened PR #1, and read back the required contexts `required-native`, `fixture-repro`, and `preview-package-smoke`.
- Updated README and the Phase 1 validation ledger with a clearly labeled run-scoped hosted sample and explicit product-support limits. The latest fully verified code sample was SHA `59b104ef5ba95f7dd48e6dd3f4732f49f4cc77de`; the planning metadata commit creates a new SHA that must pass the exact-SHA verifier before phase-level sign-off.

## Task Commits

1. **Task 1: Publish only smoke-qualified Linux and macOS preview artifacts** — `8d536a6` (`feat`).
2. **Task 2: Provide the repository endpoint or report hosting unavailability** — resolved by the owner checkpoint response and authorized public repository creation; checkpoint record `4aa923e` and privacy-reference normalization `6f43b91`.
3. **Task 3: Configure and exercise the remote PR and required-check path** — `e753da2`, `2071ef3`, and `59b104e` (`fix`).

The six measured Plan 05 commits are `8d536a6`, `4aa923e`, `6f43b91`, `e753da2`, `2071ef3`, and `59b104e`; count measured from `93cab51708a11c168e1afffb27a78aa66ad858e9` through `59b104ef5ba95f7dd48e6dd3f4732f49f4cc77de`. The GSD plan-closeout metadata commit is separate.

## Files Created/Modified

- `.github/workflows/preview.yml` — exact-SHA Linux/macOS package production and smoke workflow, with a bounded wait that fits its job timeout.
- `.github/scripts/verify-pr-evidence.sh` — POSIX-shell verification of required contexts, exact workflow runs, artifacts, API expiry, downloaded packages, and sidecars.
- `cmake/PreviewPackageSmoke.cmake` and `cmake/VerifyArtifactSidecar.cmake` — archive creation/extraction, external consumer smoke, and built-in JSON sidecar validation.
- `CMakeLists.txt`, `tests/CMakeLists.txt`, and package smoke helpers — executable suffix forwarding, test-only sanitizer consumer flags, and Windows CRLF inventory normalization.
- `README.md` and `01-VALIDATION.md` — public PR/check/artifact instructions, exact hosted evidence, and bounded capability statements.
- `continue.md` and `STATE.md` — phase status, completed Plan 05 result, and conditional Phase 2 route.

## Decisions Made

- Publish only the two packages that passed installed-runner and external consumer smoke; Windows remains a native CI lane without a downloadable preview.
- Treat GitHub artifact API digests and package archive SHA-256 as separate identifiers. Record actual `expires_at` per run and do not present run artifacts as releases.
- Keep native support claims scoped to tested runner jobs; CI image labels do not establish minimum supported operating-system versions.
- Preserve the normal exported package flags and use sanitizer link flags only when configuring the test-only extracted external consumers.

## Verification Evidence

- Local configure/build/CTest passed 25/25 at the fixed code revision; `preview_package_smoke` passed after extraction, guest success, and both external consumers. A synthetic CRLF CTest inventory passed for both 25-case installed and 22-case core-only inventories.
- Exact hosted sample source SHA `59b104ef5ba95f7dd48e6dd3f4732f49f4cc77de` matched local HEAD, PR #1 `headRefOid`, and the CI, fixture, and preview workflow heads.
- Required `gh pr checks --required` contexts passed: `required-native`, `fixture-repro`, and `preview-package-smoke`; branch protection was read back with the same three required contexts.
- CI run `37131835427` passed Linux x64, macOS arm64, Windows x64, Linux ASan/UBSan, CMake 3.25.3 floor, and the `required-native` aggregate. Windows passed the 25-case inventory.
- Fixture run `37131835525` passed pinned RGBDS regeneration and the `fixture-repro` context.
- Preview run `37131835440` passed Linux x64 and macOS arm64 installed package smoke plus `preview-package-smoke`. The exact run's artifacts were downloaded, extracted, digest-checked, sidecar-checked, and executed with the installed runner and C/C++ consumers.
- Run-scoped sample artifact API data: Linux artifact digest `sha256:97b2b5f705d2e37601ab6a87ae43f057f6760363b7671e5bf08a84bed40dafad`, package SHA-256 `23b65ad30aca49be9ab2b68976168ce03509a8c69bf42bb0ee0f28d4ef5a59a0`, created `2026-10-03T15:03:47Z`, expires `2026-10-17T15:03:47Z`; macOS artifact digest `sha256:ee0f0aa0c894b7f3d410c67eb7c1b2ecb9ecc300e93ea7c4297a9610132c9a98`, package SHA-256 `b93c0c2601472ee6dae84b77920d27e790bde1a0f1235ef67c7b87ecf35efe0c`, created `2026-10-03T15:03:55Z`, expires `2026-10-17T15:03:53Z`. Both reported 14-day sidecar retention. These timestamps identify the 59b sample only; expiry must be queried again for the new metadata SHA.
- `actionlint`, `sh -n`, `bash -n`, and `git diff --check` passed on the implementation revisions. Gitleaks and author/history privacy gates passed before the latest push; they will be rerun immediately before pushing the planning metadata commit.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Forwarded the executable suffix into Windows CMake script-mode smoke helpers**
- **Found during:** Task 3 hosted CI.
- **Issue:** Script-mode CMake did not define the project executable suffix, so installed runner/consumer paths and inventory comparison failed on Windows.
- **Fix:** Pass `CMAKE_EXECUTABLE_SUFFIX` explicitly as `GBB_EXECUTABLE_SUFFIX` into script-mode helpers and normalize carriage returns in CTest inventory output.
- **Files modified:** `tests/CMakeLists.txt`, `cmake/PreviewPackageSmoke.cmake`, `.github/scripts/verify-test-inventory.sh`.
- **Verification:** Hosted Windows `preview_package_smoke` and all 25 expected CTest cases passed on run `37131835427`; synthetic CRLF inventory checks passed for installed and core-only inventories.
- **Committed in:** `2071ef3`, `59b104e`.

**2. [Rule 1 - Bug] Added test-only sanitizer link flags for extracted external consumers**
- **Found during:** Task 3 hosted CI.
- **Issue:** The Linux sanitizer lane failed when external consumers linked the installed static library because sanitizer runtime flags were not part of the normal exported package contract.
- **Fix:** Pass sanitizer executable linker flags into the nested smoke configuration only when sanitizers are enabled.
- **Files modified:** `tests/CMakeLists.txt`, `cmake/PreviewPackageSmoke.cmake`.
- **Verification:** Linux ASan/UBSan and both final hosted package consumer smokes passed on run `37131835427` / `37131835440`.
- **Committed in:** `e753da2`.

**3. [Rule 1 - Bug] Made the package archive a real gzip tar and hardened exact-run verification**
- **Found during:** Task 3 verifier review.
- **Issue:** The archive name claimed gzip compression while CMake created an uncompressed tar; verifier cleanup and artifact API failures also needed fail-closed handling.
- **Fix:** Use gzip tar creation/extraction, POSIX `trap 0` cleanup with signal exit traps, and actionable failures for artifact API queries. Trigger preview validation on pull requests and bound the polling deadline to the 30-minute job window.
- **Files modified:** `cmake/PreviewPackageSmoke.cmake`, `.github/workflows/preview.yml`, `.github/scripts/verify-pr-evidence.sh`.
- **Verification:** `actionlint`, shell syntax checks, local extracted-package smoke, and exact hosted artifact download/verification passed.
- **Committed in:** `e753da2`.

**4. [Rule 1 - Bug] Corrected exact-SHA evidence after successive hosted failures**
- **Found during:** Task 3 hosted workflow runs.
- **Issue:** Initial PR runs surfaced the Windows executable-path assumption, missing test-only sanitizer linker flags, and a CRLF mismatch in the Windows expected-test inventory.
- **Fix:** Applied the changes above, retained failed run IDs and diagnosis in the validation ledger, and reran all required workflows on the final sample revision.
- **Files modified:** `tests/CMakeLists.txt`, `cmake/PreviewPackageSmoke.cmake`, `.github/scripts/verify-test-inventory.sh`, `.github/workflows/preview.yml`, `.github/scripts/verify-pr-evidence.sh`, `README.md`, `01-VALIDATION.md`.
- **Verification:** Exact sample runs `37131835427`, `37131835525`, and `37131835440` all passed; required contexts and artifacts were checked against SHA `59b104e`.
- **Committed in:** `e753da2`, `2071ef3`, `59b104e`.

**Total deviations:** 4 auto-fixed (Rule 1: 4). **Impact on plan:** The fixes closed hosted Windows/sanitizer/archive-verification failures and preserved the planned public package contract and evidence boundaries.

## Issues Encountered

- Initial native PR run `37129638490` failed in Windows package smoke and Linux sanitizer consumers; later preview runs exposed script-mode suffix handling (`37131303838`) and Windows CRLF inventory mismatch (`37131494144`). All were fixed, and the exact 59b sample revision's required CI, fixture, and preview runs passed.
- An email-pattern privacy scan matched the generic GitHub SSH URL syntax `git@github.com`; this was a host URL false positive. Gitleaks remained clean, every commit used the generic project author, and the personal path/email/secret scan had no actual findings after excluding only that exact syntax.
- The final planning metadata commit changes the source SHA after the recorded sample. Its exact-SHA workflow and artifact API expiry must be independently verified after push before the phase verifier signs off. No expiry from SHA 59b is represented as current for that new run.

## User Setup Required

None beyond the owner-authorized public repository creation and authenticated `gh` session already available. No secrets or personal identity data were added to the repository.

## Next Phase Readiness

- Plan 05 execution is complete and all five Phase 1 plan summaries now exist. Phase-wide verification is still pending; the next phase must not start before it passes.
- `BASE-08` has an exact hosted sample; `BASE-07` also has hosted native/fixture evidence on the same sample revision. The final planning metadata SHA requires a fresh exact-SHA run before phase sign-off.
- Once Phase 1 verification passes and the owner chooses to continue, Phase 2 is **DMG CPU, Bus, and Time**. The specific next command is `$gsd-discuss-phase 2`.
- `workflow.auto_advance` and `workflow._auto_chain_active` remain `false`; do not merge PR #1 or begin Phase 2 as part of this plan closeout.

---
*Phase: 01-portable-foundation-and-original-rom-tracer*
*Completed: 2026-10-03*

## Self-Check: PASSED

- Plan summary file created at the required `01-05-SUMMARY.md` path.
- Six measured plan commits exist from `93cab51708a11c168e1afffb27a78aa66ad858e9` through `59b104ef5ba95f7dd48e6dd3f4732f49f4cc77de`.
- No stub-pattern matches were found in Plan 05 source, workflow, or documentation files.
- No new trust boundary outside the plan threat model was introduced.
