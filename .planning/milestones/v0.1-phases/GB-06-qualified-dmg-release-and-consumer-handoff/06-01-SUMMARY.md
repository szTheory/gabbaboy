---
phase: GB-06-qualified-dmg-release-and-consumer-handoff
plan: 01
subsystem: release
tags: [github-actions, release-please, cmake, provenance, sha256, c, cpp]

# Dependency graph
requires:
  - phase: GB-01-portable-foundation-and-original-rom-tracer
    provides: Relocatable GabbaBoy::core install/export and external C/C++ consumers
  - phase: GB-04-mbc1-and-safe-battery-continuation
    provides: Versioned legal fixture manifests and bounded installed package metadata
provides:
  - Pinned release-please manifest flow that maps CMake version to a matching v tag and one unpublished draft
  - Trusted same-workflow release candidate path with exact source, merged-PR checks, and existing-draft retry validation
  - Separate source, build, and downloaded-byte receipts bound by SHA-256
  - Linux core package builder with extracted relocated C/C++ consumer smoke and fail-closed candidate verifier
affects: [06-02, 06-06, release-automation, adopter-packages]

# Actuals (#2632); realized diff bytes/4, measured plan commits before metadata commit.
actuals:
  tokens: 14218
  tasks: 2
  commits: 2
commits: 2
plan_head_before: c1e4d5ee54b72e232565644b8c08eb4a15bbc67a
plan_head_after: 94cd5b6f6526272dbff0432aa7f67b1ca2f22313

# Tech tracking
tech-stack:
  added: [release-please-action v5.0.0, GitHub Actions reusable workflow]
  patterns: [Build once from exact trusted tag; separate source/build/download receipts; reuse qualified draft bytes on retry]

key-files:
  created:
    - .github/workflows/release.yml
    - .github/workflows/release-please.yml
    - .release-please-manifest.json
    - release-please-config.json
    - cmake/VerifyReleaseReceipt.cmake
    - tests/scripts/verify-release-candidate.sh
  modified:
    - CMakeLists.txt

key-decisions:
  - "CMake PROJECT_VERSION remains the product version source; release-please mirrors it and emits matching v<version> tags."
  - "Use GITHUB_TOKEN for the version PR and keep GitHub's normal approval requirement for its exact-head checks."
  - "A qualified candidate remains an unpublished draft until the final Phase 6 release gate."
  - "Record source identity, build provenance, and downloaded-byte smoke in separate receipts linked by digests."

patterns-established:
  - "Draft retries revalidate release ID, tag/source SHA, current PR proof, and receipt hashes before reusing already-qualified bytes."
  - "Archive extraction rejects traversal, links, special files, duplicate names, and excess uncompressed size before running relocated consumers."

requirements-completed: []

coverage:
  - id: D1
    description: "Release candidate receipt and extraction verifier builds a package, smokes relocated C/C++ consumers, and rejects altered or malformed candidate evidence."
    requirement: SHIP-03
    verification:
      - kind: integration
        ref: "tests/scripts/verify-release-candidate.sh --self-test (macOS arm64 local package; hosted Linux candidate remains pending)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Release-please manifest and same-workflow candidate route are statically checked for draft/tag settings, full-SHA action pinning, exact outputs, and guarded retries."
    requirement: SHIP-08
    verification:
      - kind: other
        ref: "actionlint .github/workflows/release.yml .github/workflows/release-please.yml"
        status: pass
      - kind: other
        ref: "tests/scripts/verify-release-candidate.sh --self-test"
        status: pass
    human_judgment: false

# Metrics
duration: 167min
completed: 2026-10-08
status: complete
---

# Phase 6 Plan 1: Release-Please Draft and Trusted Linux Core Candidate Summary

**A pinned release-please flow now connects the CMake version to one unpublished draft and an exact-tag Linux core candidate, with separate provenance receipts and downloaded-byte consumer verification.**

## Performance

- **Duration:** 167 min
- **Started:** 2026-10-08T19:55:56Z
- **Completed:** 2026-10-08T22:43:03Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- Added manifest-mode release-please configuration with the verified `googleapis/release-please-action` v5.0.0 full commit SHA, CMake version marker, draft releases, immediate matching `v` tags, and no component prefix.
- Added a trusted main-branch workflow route that consumes release-please `release_created`, `tag_name`, and `sha` in the same run, confirms the exact tag target and a merged main PR's exact-head required checks, and leaves publication to Plan 06-06.
- Added guarded retries for the same existing draft and exact tag/source/proof. Once a downloaded candidate has passed, retries smoke its existing bytes without rebuilding. Interrupted candidates only reuse matching draft attachments.
- Added separate source identity, build provenance, and downloaded-byte smoke receipts. The verifier binds them to the same release ID, version/tag, source SHA, notices, release notes, fixture manifests, and archive digest.
- Added bounded archive extraction and a local self-test that builds and installs the core, extracts the package, compiles/runs external C and C++ consumers, then exercises negative receipt and archive cases.

## Task Commits

Each task was committed atomically:

1. **Task 06-01-01: Qualify one Linux core archive through a draft release** — `5647ba0` (`feat`)
2. **Task 06-01-02: Bind version PR and trusted tag to the release path** — `94cd5b6` (`feat`)

## Files Created/Modified

- `.github/workflows/release.yml` — trusted reusable release candidate and guarded retry workflow.
- `.github/workflows/release-please.yml` — main push and explicit existing-draft retry entry points.
- `release-please-config.json`, `.release-please-manifest.json`, and `CMakeLists.txt` — version PR settings and product version linkage.
- `cmake/VerifyReleaseReceipt.cmake` — fail-closed source/build/download receipt and digest validation.
- `tests/scripts/verify-release-candidate.sh` — local build/consumer self-test, receipt verifier entry point, and safe extraction.

## Decisions Made

- Kept CMake `PROJECT_VERSION` as the product version source and configured release-please to update its version marker alongside the manifest.
- Used `GITHUB_TOKEN`; the generated version PR must receive its ordinary approval before its exact-head workflows run. No dispatch is treated as a substitute for those checks.
- Kept the Linux candidate draft-only. Publication, final multi-platform bytes, and live final gate evidence belong to Plan 06-06.
- Kept the release dependency limited to the pinned release-please action; the package and verification logic use existing project tooling and Python's standard library.

## Deviations from Plan

None. The verifier was extended to keep source, build, and downloaded-byte receipts as distinct attached files, as required by the plan's provenance contract.

## Issues Encountered

- The sandbox denied writes to `.git`, so the plan's base-commit measurement ledger was kept under `/private/tmp`; task commits required the approved Git mutation path. The measured count is two task commits.
- The local environment is macOS arm64, so the local self-test validates the package/receipt/relocation path on that host. It does not claim Linux x64 qualification. The repository currently has no GitHub releases or open PRs, so no hosted draft/tag/download evidence exists yet; the workflow intentionally defers the live protected merge and final release to Plan 06-06.
- Live branch protection was rechecked read-only: strict mode is enabled and requires `required-native`, `fixture-repro`, and `preview-package-smoke`.

## Verification

- `actionlint .github/workflows/release.yml .github/workflows/release-please.yml` — passed (actionlint 1.7.12).
- `bash -n tests/scripts/verify-release-candidate.sh` — passed.
- `git diff --check` — passed.
- `tests/scripts/verify-release-candidate.sh --self-test` — passed: Release build/install; archive extraction; external C and C++ configure/build/run; receipt/source/build digest binding; rejection of altered archive, published release, duplicate asset, stale proof, missing notes/source, wrong tag, changed source/build receipt, bad notice digest, and archive traversal.
- No hosted Linux release candidate, GitHub draft, tag, or publication was created in this plan.

## Next Phase Readiness

Plan 06-01 is complete. The workflow and local receipt verifier are ready for downstream asset and final-gate integration. The hosted exact-tag Linux lane remains unobserved until the release-please version PR is merged after its required exact-head checks; Plan 06-06 owns that final gated merge/tag/publication evidence. Plan 06-02 and 06-05 are the remaining Wave 1 plans.

---
*Phase: GB-06-qualified-dmg-release-and-consumer-handoff*
*Completed: 2026-10-08*

## Self-Check: PASSED

- Summary file exists at the planned phase path.
- Task commits `5647ba0` and `94cd5b6` are ancestors of the current phase branch HEAD.
