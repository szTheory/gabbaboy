---
phase: GB-06-qualified-dmg-release-and-consumer-handoff
plan: 04
subsystem: release-evidence
tags: [support-ledger, provenance, benchmark, CMake, GitHub-Actions]
requires:
  - phase: GB-06
    provides: trusted release draft/tag routing and exact downloaded candidate lanes from Plans 06-01/02
provides:
  - Versioned support ledger and tagged-source sidecar generator/verifier
  - Bounded trace-paired core workload harness and release performance receipt workflow
affects: [GB-06-03, GB-06-06, release-support, performance-evidence]
actuals:
  tokens: 12981
  tasks: 2
  commits: 4
tech-stack:
  added: []
  patterns:
    - Stable tracked scope facts bind to tagged source through an external sidecar, avoiding self-hash cycles.
    - Fixed workload measurements preserve raw samples, peak RSS scope, uncertainty, and equal trace/no-trace guest digests.
key-files:
  created:
    - docs/support/v0.1.0.md
    - tests/scripts/verify-support-ledger.py
    - tests/measure_core.c
    - tests/scripts/measure-release-baseline.sh
  modified:
    - CMakeLists.txt
    - .github/workflows/release.yml
decisions:
  - "Keep the checked-in ledger independent of the future release tag and full source SHA; generate a separate tag-bound sidecar from tagged blobs."
  - "Treat speed and RSS results as advisory until repeated variance supports a defensible budget; do not claim allocation behavior from RSS."
  - "Reuse standard-library Python and platform resource APIs; add no package dependency."
requirements-completed: [SHIP-05, SHIP-06, SHIP-03]
coverage:
  - id: D1
    description: Versioned support ledger matches the pinned three-case corpus, fixture manifest digests, exclusions, and known evidence limits.
    requirement: SHIP-05
    verification:
      - kind: other
        ref: python3 tests/scripts/verify-support-ledger.py --self-test
        status: pass
    human_judgment: false
  - id: D2
    description: Release automation generates and verifies a separate source-SHA and tagged-ledger-blob-bound support sidecar.
    requirement: SHIP-03
    verification:
      - kind: other
        ref: python3 tests/scripts/verify-support-ledger.py --self-test (temporary tagged repository and sidecar mismatch controls)
        status: pass
    human_judgment: false
  - id: D3
    description: Fixed DMG core workload records repeated speed and peak-RSS samples, warm-up, uncertainty, trace overhead, and independent digest equality.
    requirement: SHIP-06
    verification:
      - kind: integration
        ref: bash tests/scripts/measure-release-baseline.sh --self-test
        status: pass
    human_judgment: false
duration: 8min
completed: 2026-10-08
status: complete
commits: 4
plan_head_before: be63a0c36e71c68b54927cf36ce119a1fab6f3d7
plan_head_after: 5c9332202530240cfac7c038dacf66a09ae29ad0
---

# Phase GB-06 Plan 04: Support Ledger and Reproducible Performance Evidence Summary

**A stable DMG-CPU-B support ledger, exact-tag release sidecar, and bounded trace-paired performance receipt with raw samples and explicit uncertainty.**

## Performance

- **Duration:** 8 minutes
- **Started:** 2026-10-08T23:14:54Z
- **Completed:** 2026-10-08T23:23:08Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Documented the bootless DMG-CPU-B model, ROM-only/standard MBC1 scope, fixed eligible CPU/timer corpus, outcomes, fixture classes, exclusions, evidence types, known issues, and absence of physical/perceptual observations.
- Added a standard-library validator for strict UTF-8 and duplicate keys, stable corpus order/revision, nonempty limitation/evidence data, manifest SHA-256s, and broad compatibility claims. It emits or verifies a separate post-tag sidecar containing the exact commit SHA, tagged ledger blob identity, and manifest identities.
- Added a bounded legal-fixture core benchmark with warm-up and repeated trace-on/off runs, independent WRAM/HRAM correctness digest, monotonic clock and precision reporting, in-process peak RSS, no-allocation regression status, median/spread/uncertainty, explicit advisory trace deltas, build durations, and exact-source hosted check-run durations.
- Wired the trusted candidate workflow to generate or reuse evidence on the exact tag, upload it only to the unpublished draft, and hash the support sidecar and performance receipt with all candidate assets in the final manifest. No tag was created or release published by this plan.

## Task Commits

1. **Task 1: Keep a tracked ledger and generate its post-tag support sidecar** — `abbe52c` (feature), `1caeb4a` (validator self-test fix), `5c93322` (temporary tagged-repository sidecar test)
2. **Task 2: Record reproducible speed, memory and trace baselines** — `1011cd7` (feature)

## Files Created/Modified

- `docs/support/v0.1.0.md` — stable human-readable scope and machine-validated corpus ledger.
- `tests/scripts/verify-support-ledger.py` — tagged blob sidecar generator, verifier, and mutation self-test.
- `tests/measure_core.c` — bounded 1,000,000-half-dot traced/untraced workload.
- `tests/scripts/measure-release-baseline.sh` — bounded build, repeated samples, digest pairing, host receipt, and exact-tag receipt path.
- `CMakeLists.txt` — optional test-build measurement executable.
- `.github/workflows/release.yml` — exact-tag draft evidence generation and complete candidate asset digesting.

## Decisions Made

- The tracked ledger contains no future release SHA; the separate sidecar binds tagged source and ledger blob so it can be hashed by the later asset manifest without a cyclic hash.
- Process peak RSS includes executable, loader, fixture, and optional trace storage. It is not core heap-only usage, and RSS does not establish allocation behavior. The existing `audio_no_alloc` regression is recorded with its narrower `gbb_run_audio` scope.
- Five local samples per mode were sufficient to exercise the receipt format, not to set a performance budget. Timings remain advisory and sensitive to host scheduling.
- No additional package dependency was introduced.

## Deviations from Plan

None. The release-bound tagged sidecar and exact-head hosted duration receipt are wired but cannot be generated in this local plan execution before the final release gate creates the trusted tag and provides hosted run data.

## Issues Encountered

- macOS `/usr/bin/time -l` attempted a restricted `sysctl` call, so peak RSS collection was moved into the benchmark executable using `getrusage` on Unix and the native process API on Windows. The measurement self-test then passed.

## Verification

- `python3 tests/scripts/verify-support-ledger.py --self-test` — passed, including a temporary tagged repository that exercises exact commit, ledger blob, fixture manifest binding, and sidecar mismatch rejection; it does not create a project release tag.
- `GBB_RELEASE_MEASURE_SAMPLES=5 GBB_RELEASE_MEASURE_WARMUPS=2 bash tests/scripts/measure-release-baseline.sh --self-test` — passed; trace-on and trace-off output digests matched, and `audio_no_alloc` passed.
- Local sample medians were 11.578 ms traced and 11.555 ms untraced on this run; their difference is noisy and is not a budget. Median process peak RSS was 2,654,208 bytes traced and 1,622,016 bytes untraced, including harness and trace storage.
- `actionlint -oneline .github/workflows/release.yml`, `python3 -m py_compile tests/scripts/verify-support-ledger.py`, `bash -n tests/scripts/measure-release-baseline.sh`, and `git diff --check` — passed.
- No Phase 6 tag, hosted release receipt, or published asset was created. The actual exact-tag sidecar and hosted timing evidence remain for Plan 06-06.

## Deferred Issues

- The local performance receipt is not a release qualification: it records a dirty working tree and no exact-tag or hosted CI durations. Plan 06-06 must generate and validate the release-bound receipt from the trusted tag and current exact-head hosted checks before publication.
- Physical DMG behavior, broad game compatibility, perceptual audio/video, and hardware memory use remain unqualified and are explicitly excluded from the ledger.

## Self-Check: PASSED

- All six declared source files exist and the four task commits are ancestors of `HEAD`.
- Plan commit count was measured from the persisted `gsd-plan-head-before-GB-06-04` ledger: 4.
- Owner scratch remains unstaged and unmodified by this plan: `.planning/HANDOFF.json`, `.planning/config.json`, `.planning/context/DECISIONS.md`, Phase 3 context/research files, `.planning/state.json`, and `.planning/milestone.lock`.

## Next Phase Readiness

Plan 06-04 is complete; Phase 6 remains executing. Wave 4 Plan 06-03 is next, followed by 06-07 and the final release gate 06-06. Continue with `$gsd-execute-phase 6` and stop at the Phase 6 boundary. Release publication stays gated to Plan 06-06.

---
*Phase: GB-06-qualified-dmg-release-and-consumer-handoff*
*Completed: 2026-10-08*
