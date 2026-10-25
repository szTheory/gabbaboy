---
phase: 15-cgb-acceptance-support-ledger-and-v0-2-0-release
plan: '05'
subsystem: performance
tags: [release-performance, paired-benchmark, provenance, receipt]
requires:
  - phase: 15-01
    provides: Release scope and source-bound CGB evidence boundary
provides:
  - Clean v0.1.0 and candidate DMG builds with a provenance-bound paired performance receipt
  - Privacy, uncertainty, regression-disposition, and resource-observation receipt validation
affects: [phase-15-release-qualification, performance-evidence]
actuals:
  tokens: 13493
  tasks: 2
  commits: 4
commits: 4
plan_head_before: f44b7e9f7c5ec70838f4558b5e708d6058f8c8e1
plan_head_after: 86659914e2a3ba829a347ad0326a6be43e592afb
tech-stack:
  added: []
  patterns:
    - Build exact Git revisions in clean detached worktrees with matching Release compiler and flags
    - Bind timing and resource observations to source trees, compiler, build, binary, and workload hashes
    - Publish receipts atomically and reject output collisions, stale inputs, privacy leaks, and pending review
key-files:
  created:
    - tests/scripts/verify-v02-performance.py
  modified:
    - tests/scripts/measure-release-baseline.sh
key-decisions:
  - The +5% review trigger fired; accept only with the measured DMG slowdown disclosed because the project has no performance budget that defines a release-blocking threshold.
  - Label the CGB-CPU-E resource run as compatibility mode because the pinned tracer ROM has a DMG-only header; it is not native-CGB evidence.
patterns-established:
  - A performance receipt records actual Git, compiler, CMake, flags, binary, workload, sample-order, digest, and uncertainty identities instead of caller-provided source labels.
  - A triggered regression remains pending until a source and measurement review is recorded; raw timing alone is not a test pass/fail threshold.
requirements-completed: [SHIP-11]
coverage:
  - id: D1
    description: Clean v0.1.0 and candidate Release builds produce a validated 3-warmup, 30-pair interleaved DMG receipt with immutable source, build, binary, and workload identities.
    requirement: SHIP-11
    human_judgment: false
    verification:
      - kind: e2e
        ref: 'bash tests/scripts/measure-release-baseline.sh --qualify-v02 --output build/v02-performance-receipt.json --review-regression <source-backed disposition>'
        status: pass
      - kind: integration
        ref: 'python3 -I tests/scripts/verify-v02-performance.py --verify build/v02-performance-receipt.json'
        status: pass
  - id: D2
    description: The verifier rejects forged or stale identities, altered digests or uncertainty, invalid sample order, privacy leaks, missing review and resource evidence, and receipt collisions.
    requirement: SHIP-11
    human_judgment: false
    verification:
      - kind: unit
        ref: 'python3 -I tests/scripts/verify-v02-performance.py --self-test (19 tests, 18 negative controls, 1 positive success)'
        status: pass
  - id: D3
    description: Receipt includes digest-bound DMG trace/no-trace timing and peak-RSS samples plus candidate CGB-CPU-E compatibility-mode resource samples.
    requirement: SHIP-11
    human_judgment: false
    verification:
      - kind: integration
        ref: 'build/v02-performance-receipt.json resource_observations verified by tests/scripts/verify-v02-performance.py'
        status: pass
duration: 20min
started: '2026-10-16T15:59:28Z'
completed: '2026-10-16'
status: complete
---

# Phase 15 Plan 05: CGB Acceptance Support Ledger and v0.2.0 Release Summary

**A provenance-bound v0.1.0 comparison and resource receipt confirms a disclosed 23.96% median DMG slowdown while preserving the deterministic workload digest.**

## Performance

- **Duration:** 20 minutes from the plan start.
- **Started:** 2026-10-16 15:59:28 UTC.
- **Completed:** 2026-10-16.
- **Tasks:** 2 completed.
- **Files modified:** 2 plan deliverables.

## Accomplishments

- Added `--qualify-v02 --output PATH`, which builds the exact `v0.1.0` baseline (`e30d168f7fc61de8db0a3801e7b1736362912cb7`) and candidate source `a9a86206fa98f4bdb8771ae0cbb7b87f000c389d` in clean detached worktrees. Both used AppleClang 21.0.0.21000101, CMake 4.4.3, Unix Makefiles, Release configuration, and `-O3 -DNDEBUG`; compiler and binary hashes are bound in the receipt.
- Ran three warmups and thirty interleaved DMG pairs for `original-wram-tracer-1m-half-dots-v1`. All runs preserved digest `4c7a57ff3d50d228`. Candidate median time was 123.96% of baseline, with 9.93% sample standard deviation and a 3.55% approximate 95% mean margin. The +5% trigger fired.
- Investigated the result against the source delta. The candidate adds CGB speed-switch, HDMA arbitration, unsupported-bus, and output-boundary checks in the shared run loop, which the v0.1 baseline lacks. The receipt records the slowdown as accepted with explicit disclosure; it makes no equivalent-speed claim.
- Recorded ten raw timing and peak-RSS samples per build for DMG trace and no-trace modes, plus candidate CGB-CPU-E compatibility-mode observations. The ROM header identifies the tracer as DMG-only, so the CGB-profile measurement is not represented as native-CGB evidence. DMG resource digests match the workload digest; the CGB-profile digest is recorded and verified.
- Added a stdlib verifier and production-entry self-tests for source/build/binary/workload identity, digest, paired order, uncertainty, privacy, regression review, resource observations, and atomic collision refusal. The final self-test passed 19 tests with 18 negative controls and one positive success.

## Task Commits

1. **Task 1 RED:** `ae82afe` — add performance receipt acceptance contract.
2. **Task 1 implementation:** `e7ddc4a` — qualify v0.1 DMG performance comparison.
3. **Task 2 RED:** `a9a8620` — add privacy and disposition receipt controls.
4. **Task 2 implementation:** `8665991` — record regression disposition and resource evidence.

The measured four plan commits exclude this summary commit.

## Files Created/Modified

- `tests/scripts/measure-release-baseline.sh` — clean baseline/candidate Release builds, interleaved timing, refreshed trace/resource observations, privacy-safe atomic receipt production, and explicit review disposition.
- `tests/scripts/verify-v02-performance.py` — provenance, workload, uncertainty, privacy, review, resource, and negative-control validation.
- `build/v02-performance-receipt.json` — local generated campaign evidence; ignored build output, not a committed fixture.

## Decisions Made

- Recorded the measured slowdown rather than suppressing the review trigger. No repository performance budget defines a blocking threshold, so the candidate is retained only with the regression stated and no equivalent-speed claim.
- Identified the candidate CGB-CPU-E resource run as compatibility mode from the DMG-only ROM header. No native-CGB or physical-hardware performance claim follows from it.
- Kept the receipt as candidate-source evidence. The eventual exact-tag workflow must regenerate evidence after final source, version, and build inputs are fixed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking issue] Enabled the test CMake configuration for the clean measurement builds.**
- **Found during:** Task 1 clean baseline build.
- **Issue:** With `BUILD_TESTING=OFF`, CMake did not declare the existing `measure_core` target.
- **Fix:** Configured both clean worktrees with `BUILD_TESTING=ON`, then built only `measure_core` for the comparison.
- **Files modified:** `tests/scripts/measure-release-baseline.sh`.
- **Verification:** The exact baseline and candidate targets built and completed the full 3/30 campaign.
- **Committed in:** `e7ddc4a`.

**Total deviations:** 1 auto-fixed (Rule 3). The change enables the planned existing target without adding dependencies or expanding the build target set.

## Issues Encountered

- The first campaign exceeded the +5% review trigger and correctly remained pending without review notes. Source comparison and repeated, digest-matched measurements confirmed a material slowdown; the final receipt records the review and release disposition.
- CMake does not expose compiler ID/version through the cache entries used by the first implementation. The producer now reads CMake’s generated compiler metadata file and verifies the compiler binary hash.

## User Setup Required

None. No external service or credentials are required.

## Next Phase Readiness

Plan 15-05 is complete. The performance receipt is tied to candidate source `a9a86206fa98f4bdb8771ae0cbb7b87f000c389d`, not an exact release tag; final tag qualification must produce fresh evidence. Phase 15 remains active, and this executor stops here for the parent’s routing decision.

## TDD Gate Compliance

- **Task 1 RED:** `test_valid_receipt_is_accepted` failed through the production `--verify` CLI while it returned `verify-not-implemented`; the evidence classifier accepted the result as `RED_EVIDENCE_OK`.
- **Task 1 GREEN:** The clean baseline/candidate 3/30 campaign and receipt verification passed, and the self-test accepted one positive fixture while rejecting seven Task 1 mutations.
- **Task 2 RED:** The production verifier accepted receipts missing privacy, regression-disposition, and resource checks; four intended tests failed and the evidence classifier returned `RED_EVIDENCE_OK`.
- **Task 2 GREEN:** The final self-test passed 19 tests with 18 negative controls and one positive success. The clean campaign receipt passed production verification.

---
*Phase: 15-cgb-acceptance-support-ledger-and-v0-2-0-release*
*Plan: 05*
*Completed: 2026-10-16*

## Self-Check: PASSED

The summary exists, all four measured Task 15-05 commits are ancestors of `plan_head_after`, and the plan ledger reports four commits. The coverage verifier accepted all three deliverables for automated verification.
