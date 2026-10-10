---
phase: GB-06-qualified-dmg-release-and-consumer-handoff
plan: 02
subsystem: release
tags: [github-actions, cmake, windows, macos, c, cpp, sdl3, sha256]

# Dependency graph
requires:
  - phase: GB-06-qualified-dmg-release-and-consumer-handoff
    provides: Exact-tag Linux core draft candidate and source/build/download receipt pattern from Plan 06-01
provides:
  - Draft-only macOS arm64 and Windows x64 core archives with downloaded-byte relocation and consumer smoke routes
  - Downloaded macOS player package verification with legally pinned fixtures and scripted SDL devices
  - Fail-closed exact platform asset inventory and a digest manifest for all three core archives and the player archive
affects: [06-04, 06-06, release-automation, adopter-packages]

# Actuals (#2632); measured diff bytes/4 over the declared files.
actuals:
  tokens: 7231
  tasks: 2
  commits: 5
commits: 5
plan_head_before: 966a4d053887449b1bff0616515d15ea7ac03354
plan_head_after: 087bc4ba2558f9346804f43883b756b83828114c

# Tech tracking
tech-stack:
  added: []
  patterns: [trusted-tag builds, draft-only release attachments, downloaded-byte package smoke, exact asset-set validation]

key-files:
  created: []
  modified:
    - .github/workflows/release.yml
    - tests/scripts/verify-release-candidate.sh
    - tests/scripts/verify-phase3-player.sh

key-decisions:
  - "Keep the Windows release archive check on the existing native Windows runner and reuse the current C and C++ consumer projects."
  - "Force SDL dummy video and audio before player verification so the downloaded-package smoke proves software paths only."
  - "Keep all platform bytes attached to the existing unpublished draft and enforce the exact candidate asset set before writing the platform digest manifest."

patterns-established:
  - "Build core packages on the tested native runner, download the attached release bytes, verify their digest, safely extract, and run relocated consumers."
  - "A platform manifest is produced only after every platform smoke succeeds and records source identity, build provenance, archive digests, and explicit unsigned/unqualified claims."

requirements-completed: []
coverage:
  - id: D1
    description: "Linux, macOS, and Windows core release archives have exact-byte relocated C/C++ consumer qualification routes and a fail-closed asset manifest."
    requirement: SHIP-01
    verification:
      - kind: integration
        ref: "cmake --preset phase1; cmake --build --preset phase1; ctest --preset phase1 --output-on-failure --no-tests=error -R '^preview_package_smoke$'"
        status: pass
      - kind: integration
        ref: "tests/scripts/verify-release-candidate.sh --self-test (local macOS archive, receipt negatives, relocated C/C++ consumers)"
        status: pass
      - kind: other
        ref: "candidate-platform-manifest job on linux-x64/macos-arm64/windows-x64, to be observed after the Phase 6 tag in Plan 06-06"
        status: unknown
    human_judgment: true
    rationale: "The three hosted runner/download combinations do not exist until the exact release tag and draft are created in Plan 06-06."
  - id: D2
    description: "The pinned macOS player archive is downloaded and tested for legal demo input, visible-frame/audio smoke, battery save, exit, and fresh-process continuation."
    requirement: SHIP-02
    verification:
      - kind: integration
        ref: "bash tests/scripts/verify-phase3-player.sh (local pinned SDL 3.4.18 archive and extracted-package smoke)"
        status: pass
      - kind: other
        ref: "macOS draft asset download on the exact release tag, to be observed in Plan 06-06"
        status: unknown
    human_judgment: true
    rationale: "Hosted exact-tag release bytes are not available until Plan 06-06."
  - id: D3
    description: "Candidate receipt checks bind downloaded bytes to the draft, version, source, notices, build identity, and exact asset set."
    requirement: SHIP-03
    verification:
      - kind: integration
        ref: "preview_package_smoke plus extracted C/C++ consumer builds in verify-release-candidate.sh --self-test"
        status: pass
      - kind: other
        ref: "actionlint .github/workflows/release.yml .github/workflows/release-please.yml"
        status: pass
      - kind: other
        ref: "Exact-tag hosted release gate and downloaded platform manifest, to be observed in Plan 06-06"
        status: unknown
    human_judgment: true
    rationale: "Local verifier and workflow syntax checks cannot establish exact-tag GitHub release behavior."

# Metrics
duration: 5min
completed: 2026-10-08
status: complete
---

# Phase 6 Plan 2: Downloaded Platform and macOS Player Qualification Summary

**The draft candidate now has macOS arm64 and Windows x64 core archive routes, a downloaded macOS player smoke, and a fail-closed manifest covering the three core archives and player bytes.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-10-08T23:05:26Z
- **Completed:** 2026-10-08T23:13:26Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Added sequential macOS and Windows jobs that verify trusted tag identity, preserve draft status, build each core archive once, attach immutable-by-comparison bytes, download them, check archive digests, safely extract, and run relocated C/C++ consumers.
- Reused the existing Windows native C/C++ consumer projects and Visual Studio toolchain for the downloaded archive check; no new package or framework dependency was added.
- Guarded platform retries so a complete existing macOS or Windows candidate is reused and re-smoked; a partial asset set fails closed instead of rebuilding and replacing bytes.
- Wired the pinned SDL 3.4.18 player tarball into the same draft and made its verifier force SDL dummy audio/video before testing package notices, demo input/frame/PCM, battery save, exit, and fresh-process continuation.
- Added a final exact asset-set gate and `candidate-platform-manifest.json` with source SHA, archive digests, platform toolchain details, and explicit software-only trust limits.

## Task Commits

1. **06-02-01: Qualify three downloaded core archives** — `b429b4e` (`feat`)
2. **06-02-01: Include Linux provenance in platform manifest** — `c3b584f` (`fix`)
3. **06-02-02: Qualify the downloaded macOS player and legal continuation** — `619f7d1` (`fix`)
4. **06-02-01: Reuse qualified platform bytes on retry** — `087bc4b` (`fix`)

An earlier plan-summary bookkeeping commit, `257b25c`, was replaced by this final summary after the retry fix; the measured commit count includes it.

## Files Created/Modified

- `.github/workflows/release.yml` — native macOS and Windows build/download/smoke jobs plus exact candidate asset inventory and digest manifest.
- `tests/scripts/verify-release-candidate.sh` — self-test guards for the platform matrix, downloaded archives, player lifecycle, and scripted SDL backends.
- `tests/scripts/verify-phase3-player.sh` — explicitly forces SDL dummy audio and video for software-only package evidence.

## Decisions Made

- Kept the Windows validation on `windows-2022` and reused the current C and C++ consumer sources against the downloaded archive.
- Kept the final platform manifest draft-only. Every core and player archive must be attached once, its exact downloaded bytes must verify, and all platform jobs must pass before the manifest is attached.
- Treated SDL dummy devices as software-path evidence; no physical display/audio, hotplug, or perceptual qualification is claimed.

## Deviations from Plan

None. `cmake/PreviewPackageSmoke.cmake` and `.github/scripts/safe_extract_package.py` already provided relocated consumers and bounded contained extraction; the new workflow reuses those existing project mechanisms and the release-candidate extractor.

## Issues Encountered

- Retry builds would have changed the player tarball because package metadata records the Actions run ID. The workflow now reuses complete existing platform byte sets without rebuilding, revalidates the downloaded bytes, and rejects partial sets; `actionlint` and the candidate self-test passed.
- The first sandboxed player-verifier run could not create its synthetic lock file under the macOS per-user Application Support directory. The same required command passed after it was rerun with normal host filesystem access; no application data was left behind by the verifier.
- Live hosted tag, draft upload/download, and Windows runner evidence remain pending Plan 06-06, as designed. This local machine is macOS arm64 and does not establish Windows or Linux release qualification.

## Verification

- `actionlint .github/workflows/release.yml .github/workflows/release-please.yml` — passed after the retry-reuse changes.
- `bash -n tests/scripts/verify-release-candidate.sh tests/scripts/verify-phase3-player.sh` — passed.
- `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '^preview_package_smoke$'` — passed, 1/1 relocated package test.
- `bash tests/scripts/verify-release-candidate.sh --self-test` — passed: installed archive, relocated C/C++ consumer build/run, receipt and altered-byte rejection, and traversal rejection.
- `bash tests/scripts/verify-phase3-player.sh` — passed on macOS arm64: 50/50 player tests, SDL dummy backend smoke, extracted local package lifecycle, and fresh-process MBC1 continuation.
- `python3 .github/scripts/safe_extract_package.py --self-test` — passed bounded archive adversarial cases.
- `git diff --check` — passed.
- No live GitHub draft was created or published; final hosted tag/draft checks and downloaded cross-runner receipts are owned by Plan 06-06.

## Next Phase Readiness

Plan 06-02 is ready for integration with the support ledger and baseline work. The next dependency wave is Plan 06-04; final exact-tag hosted evidence and publication remain gated to Plan 06-06.

The phase-level SHIP-01, SHIP-02, and SHIP-03 checkboxes remain pending until their required exact-tag hosted evidence and final release gate are observed.

---
*Phase: GB-06-qualified-dmg-release-and-consumer-handoff*
*Completed: 2026-10-08*

## Self-Check: PASSED

- Summary file is present at the planned path.
- Task commits `b429b4e`, `c3b584f`, `619f7d1`, and `087bc4b` are ancestors of the current phase branch HEAD.
