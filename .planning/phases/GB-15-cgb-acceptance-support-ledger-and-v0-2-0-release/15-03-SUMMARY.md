---
phase: 15-cgb-acceptance-support-ledger-and-v0-2-0-release
plan: '03'
subsystem: testing
tags: [native-consumers, package, cgb, rtc, release-evidence]
requires:
  - phase: 15-01
    provides: Public CGB acceptance checker and release-scope foundation
provides:
  - Relocated C and C++ consumers verify the installed package and selected CGB and RTC calls
  - Repeat, concurrency, collision, and interrupted-run controls protect isolated success receipts
  - Native API and save documentation describe software-profile and host-owned persistence limits
affects: [phase-15-release-qualification, native-integration, save-contracts]
actuals:
  tokens: 9322
  tasks: 2
  commits: 4
commits: 4
plan_head_before: f81a3508ad83dc4177bc63949421ab77832bd639
plan_head_after: a03b0c2d11ef60a4f960436aaea4266018deb77e
tech-stack:
  added: []
  patterns:
    - Reuse installed-package CMake consumers and the existing runner without changing consumer sources
    - Reserve output paths and publish success receipts atomically after both language runs pass
key-files:
  created:
    - tests/scripts/verify-v02-consumers.py
  modified:
    - docs/native-integration.md
    - docs/cartridge-and-saves.md
    - include/gabbaboy/gabbaboy.h
key-decisions:
  - Keep profile and API evidence tied to the installed package bytes and the source revision reported by its runner.
  - Publish no successful receipt until both relocated language consumers complete all selected behaviors.
  - Describe CGB profiles as software behavior and preserve host ownership of files and wall-clock inputs.
patterns-established:
  - Interrupted-run controls stop after staged package bytes exist, verify no partial receipt, and retry successfully.
  - Repeated runs compare stable package and behavior identities while distinct concurrent runs use separate roots.
requirements-completed: [SHIP-10]
coverage:
  - id: D1
    description: The consumer verifier runs relocated C and C++ clients and publishes source, package, compiler, behavior, and isolation evidence only after success.
    requirement: SHIP-10
    human_judgment: false
    verification:
      - kind: integration
        ref: 'cmake --preset phase1 && cmake --build --preset phase1 && python3 -I tests/scripts/verify-v02-consumers.py --run --output build/v02-consumers-plan15-03.json'
        status: pass
      - kind: integration
        ref: 'python3 -I tests/scripts/verify-v02-consumers.py --self-test (9 tests, 6 negative controls, 5 positive successes)'
        status: pass
  - id: D2
    description: Native integration guidance describes the relocated package path, receipt contents, CGB API calls, and evidence limits.
    requirement: SHIP-10
    human_judgment: false
    verification:
      - kind: integration
        ref: 'python3 -I tests/scripts/verify-v02-consumers.py --run --output build/v02-consumers-plan15-03.json'
        status: pass
      - kind: integration
        ref: 'python3 -I tests/scripts/verify-v02-consumers.py --self-test (profile, probe/info, RGB555, RTC, and rejection controls)'
        status: pass
  - id: D3
    description: Cartridge and save guidance preserves the 21-byte RTC block, host-owned clock, and existing save contract.
    requirement: SHIP-10
    human_judgment: false
    verification:
      - kind: integration
        ref: 'python3 -I tests/scripts/verify-v02-consumers.py --self-test (RTC catch-up behavior and failure controls)'
        status: pass
  - id: D4
    description: The public header documents the software-profile boundary without changing public declarations or runtime behavior.
    requirement: SHIP-10
    human_judgment: false
    verification:
      - kind: integration
        ref: 'cmake --preset phase1 && cmake --build --preset phase1 && python3 -I tests/scripts/verify-v02-consumers.py --self-test'
        status: pass
duration: 16min
started: '2026-10-16T15:36:07Z'
completed: '2026-10-16T15:51:52Z'
status: complete
---

# Phase 15 Plan 03: CGB Acceptance Support Ledger and v0.2.0 Release Summary

**Relocated C and C++ consumers verify installed package bytes, source and compiler identity, and CGB and RTC behavior with retry-safe receipts.**

## Performance

- **Duration:** 16 minutes, measured from the first recorded task commit through final verification.
- **Started:** 2026-10-16 15:36:07 UTC.
- **Completed:** 2026-10-16 15:51:52 UTC.
- **Tasks:** 2 completed.
- **Files modified:** 4 plan deliverables.

## Accomplishments

- Added a bounded verifier that installs the configured package, relocates it outside the checkout and build tree, then configures and runs the unchanged C and C++ consumers against `GabbaBoy::core`.
- Receipts bind the installed package tree, source revision, compiler identities, isolated consumer builds, and observed profile, probe/info, RGB555, and RTC behavior. Atomic output reservation and publication prevent concurrent or interrupted runs from claiming partial success.
- Expanded the self-test to cover repeated identity, separate concurrent roots, output-lock collision, interrupted installation and clean retry, missing package inputs, and failing C and C++ clients.
- Updated native integration and cartridge/save guidance, and clarified in the public header that profile names describe software behavior rather than hardware equivalence or game compatibility.

## Task Commits

1. **Task 1 RED:** `6af1099` — add relocated consumer receipt contract.
2. **Task 1 implementation:** `a706e8e` — verify relocated native consumers.
3. **Task 2 RED:** `067f823` — exercise repeat and interruption controls.
4. **Task 2 implementation:** `a03b0c2` — harden consumer run interruption and guidance.

The four measured task commits are separate from this summary commit.

## Files Created/Modified

- `tests/scripts/verify-v02-consumers.py` — relocated consumer verifier, receipt generation, and positive/negative lifecycle controls.
- `docs/native-integration.md` — installed-consumer qualification instructions and evidence limits.
- `docs/cartridge-and-saves.md` — cross-link to CGB APIs and clarification of host-owned RTC time.
- `include/gabbaboy/gabbaboy.h` — software-profile boundary in the `gbb_create` API documentation.

## Decisions Made

- Kept the existing C and C++ consumer sources and CMake installed-consumer helper unchanged; they already exercised the required API behaviors.
- Bound success receipts to installed package and source identities, and published them only after both consumer processes completed successfully.
- Kept game compatibility and physical silicon claims outside the software-profile evidence.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Interrupted the run only after staged package bytes existed.**
- **Found during:** Task 2 interruption-control verification.
- **Issue:** The first test pause occurred before package installation, so it could not prove that termination after staged output left no partial success receipt.
- **Fix:** Moved the private test pause after `cmake --install` and recorded the staged file count. The control now terminates an actual staged install, confirms no final receipt, and retries successfully.
- **Files modified:** `tests/scripts/verify-v02-consumers.py`.
- **Verification:** `--self-test` passed 9 tests, including interrupted-run retry and six negative controls.
- **Committed in:** `a03b0c2`.

**Total deviations:** 1 auto-fixed (Rule 1 - Bug). The adjustment strengthens the planned interrupted-run evidence without changing public consumer sources or the API.

## Issues Encountered

The first final receipt invocation reused an existing output path and was correctly rejected as `receipt-exists`. A fresh output path then passed the full relocated C and C++ run.

## User Setup Required

None. No external service or credentials are required.

## Next Phase Readiness

Plan 15-03 is complete. The consumer verifier and native guidance are available to the remaining Phase 15 release-qualification plan. Stop here without advancing the phase.

---
*Phase: 15-cgb-acceptance-support-ledger-and-v0-2-0-release*
*Plan: 03*
*Completed: 2026-10-16*

## TDD Gate Compliance

- **Task 1 RED:** `test_relocated_prefix_runs_both_consumers` was recorded as invalid evidence initially then accepted as `RED_EVIDENCE_OK` by the runtime semantic and format checks.
- **Task 2 RED:** `test_interrupted_run_retries_without_partial_receipt` was recorded as valid RED evidence; the first green iteration exposed that the pause preceded staged bytes and the implementation moved it after installation.
- **Green:** Final self-test passed all 9 contract tests, and the installed relocation run passed for both C and C++.

## Self-Check: PASSED

The summary exists, all four measured task commits are ancestors of `plan_head_after`, and the required coverage classifier accepts every deliverable as automatically verifiable.

