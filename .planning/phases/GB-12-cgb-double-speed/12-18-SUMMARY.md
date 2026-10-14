---
phase: 12-cgb-double-speed
plan: 18
subsystem: docs
tags: [CGB, KEY1, STOP, CMake, CTest, support-ledger]
requires:
  - phase: GB-12 plans 12-11 and 12-17
    provides: Existing CGB guide contracts, measured speed behavior, and pinned AGE dispositions
provides:
  - Host-facing master-time budget and modeled STOP-pause documentation
  - Updated release, preview, cartridge, and RTC evidence claims for CGB double speed
  - Stale-speed-claim scanner with a mutated-copy negative control
affects: [GB-12 plan 12-19, Phase 13 CGB HDMA, native integrators]
actuals:
  tokens: 2594.5
  tasks: 2
  commits: 3
commits: 3
plan_head_before: 7d057784d90ba04e2fe03e9f1148e983e08c5e1
plan_head_after: 081f45096f2b37ebc549fabd591bb80c305592a1
tech-stack:
  added: []
  patterns:
    - Stale public claims are scanned across newline-normalized documents and guarded by a mutated-copy control.
key-files:
  created:
    - tests/check_no_stale_speed_claims.cmake
  modified:
    - docs/native-integration.md
    - include/gabbaboy/gabbaboy.h
    - docs/support/unreleased.md
    - docs/preview.md
    - docs/cartridge-and-saves.md
    - docs/mbc3-rtc-evidence.md
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
key-decisions:
  - Keep the public ABI unchanged; guest-visible speed remains KEY1 bit 7 and there is no public speed getter.
  - Describe AGE results as software-model evidence: only the DIV and STOP-prefetch cases pass, while eleven named cases remain expected failures.
  - Scope M28 to transitions into double speed; mode-0 detects the corrected mutant while the DIV case does not.
patterns-established:
  - Public capability and limitation claims are checked against a maintained stale-phrase list.
requirements-completed: [CGB-06]
duration: 8 min
completed: 2026-10-13
status: complete
coverage:
  - id: CGB-06-HOST-SPEED-CONTRACT
    description: The native guide and public header comments describe KEY1 speed visibility, master-time budgets, frame duration, and modeled pause stop semantics without changing declarations.
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: integration
        ref: cgb_native_guide_contract
        status: pass
      - kind: integration
        ref: cgb_native_guide_contract_missing_selftest
        status: pass
      - kind: integration
        ref: cgb_consumer_symbol_coverage
        status: pass
      - kind: integration
        ref: cgb_consumer_symbol_coverage_selftest
        status: pass
  - id: CGB-06-PUBLIC-DOCS-STALE-CLAIMS
    description: Release, preview, cartridge, and RTC evidence docs state the implemented double-speed behavior and retain HDMA, mode-3, hardware, and corpus limitations.
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: other
        ref: cgb_speed_docs_no_stale_claims
        status: pass
      - kind: other
        ref: cgb_speed_docs_no_stale_claims_mutated
        status: pass
      - kind: integration
        ref: mbc3_rtc_evidence_ledger_names
        status: pass
      - kind: integration
        ref: mbc3_rtc_evidence_ledger_selftest
        status: pass
  - id: CGB-06-AGE-EVIDENCE-SCOPE
    description: The published AGE summary distinguishes its two passing cases from eleven expected failures and records the corrected M28 mode-0 versus DIV sensitivity without a hardware claim.
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: integration
        ref: cgb_speed_dispositions
        status: pass
      - kind: integration
        ref: cgb_speed_dispositions_mutated
        status: pass
      - kind: integration
        ref: cgb_speed_dispositions_pinned_by_missing
        status: pass
      - kind: integration
        ref: age_sensitivity_m28
        status: pass
      - kind: integration
        ref: age_sensitivity_m28_reference_mutated
        status: pass
  - id: CGB-06-FULL-INVENTORY
    description: The complete local CTest inventory, including both newly registered scanner tests, passes.
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build --output-on-failure --no-tests=error -j8 (897/897)"
        status: pass
      - kind: integration
        ref: summary_coverage
        status: pass
      - kind: integration
        ref: summary_coverage_selftest
        status: pass
---

# Phase 12 Plan 18: Host-Facing Speed Semantics and Stale-Claim Guard Summary

**Host and release docs now explain CGB KEY1 double speed, master-time budgets, the modeled switch pause, and evidence limits under a negative-controlled stale-claim guard.**

## Performance

- **Duration:** 8 minutes.
- **Started:** 2026-10-14T01:55:15Z.
- **Completed:** 2026-10-14T02:03:17Z.
- **Tasks:** 2.
- **Files modified:** 9.
- **Full-suite verification:** 897/897 CTests passed in 38.78 seconds.

## Accomplishments

- Updated the native guide and public-header comments to describe guest speed visibility through KEY1 bit 7, master half-dots at both speeds, 140448 half-dots per frame, progress returned during the modeled pause, and zero consumed half-dots for sub-quantum budgets.
- Reworded release, preview, cartridge, and RTC evidence docs so double speed is described as implemented while CGB HDMA, mode-3 timing, physical hardware, and broad compatibility remain bounded claims.
- Added a scanner for stale double-speed phrases across seven public-facing files, registered it in CTest, and added a mutated-preview control that proves an obsolete claim is rejected.
- Recorded RTC speed-independence evidence and the measured AGE scope accurately. Only `spsw-div-cgbBCE` and `spsw-stop-prefetch-cgbBCE` pass; eleven other cases retain named expected-failure dispositions. The corrected M28 mutant is double-speed-destination-only, detected by `spsw-mode0-cgbBCE` but not by the DIV case. These are software-model results, not hardware observations.

## Task Commits

1. **Task 1: Host guide, header comments, and native guide contract** — `1a16f3a` (`docs`).
2. **Task 1 correction: Keep the literal guide phrase contiguous** — `2bfc0d4` (`fix`).
3. **Task 2: Host docs and stale-claim scanner** — `081f450` (`docs`).

## Files Created/Modified

- `docs/native-integration.md` — CGB KEY1, master-time, budget, and pause-stop semantics.
- `include/gabbaboy/gabbaboy.h` — comment-only API contract update; declarations and ABI are unchanged.
- `docs/support/unreleased.md` — Phase 12 support scope, RTC evidence, AGE dispositions, and remaining limits.
- `docs/preview.md` — implemented speed-switch wording with HDMA and mode-3 limits retained.
- `docs/cartridge-and-saves.md` — physical-observation limitation wording.
- `docs/mbc3-rtc-evidence.md` — named software-profile RTC speed-independence tests.
- `tests/check_no_stale_speed_claims.cmake` — stale-phrase scanner.
- `tests/CMakeLists.txt` — guide phrase and scanner test registration, including the mutated-copy control.
- `tests/expected-tests.txt` — two new CTest inventory entries.

## Decisions Made

- Preserve the public API and ABI; the guest sees speed through KEY1 bit 7, with no host speed getter.
- Keep all AGE results scoped to the tested software model and the named pass/expected-failure rows.
- Describe M28 only as a double-speed-destination mutation; its mode-0 sensitivity does not imply DIV sensitivity.
- Keep HDMA and CGB mode-3 timing explicitly unimplemented.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Kept the required guide phrase on one line.**

- **Found during:** Task 1 acceptance checks.
- **Issue:** The contract normalized whitespace, but the plan’s literal `grep` acceptance could not match a phrase split by a line break.
- **Fix:** Kept `master half-dots at both speeds` contiguous in the guide.
- **Files modified:** `docs/native-integration.md`.
- **Verification:** Literal phrase and stale-phrase checks, guide contract, header comment-only check, and full Task 1 verification passed.
- **Committed in:** `2bfc0d4`.

**2. [Rule 1 - Bug] Registered plan tests before the inventory check.**

- **Found during:** Task 2 CMake configure.
- **Issue:** The first configure evaluated `gabbaboy_verify_registered_tests()` before the two new plan tests were added, so the expected and registered inventories differed.
- **Fix:** Moved the inventory check after the new test registrations.
- **Files modified:** `tests/CMakeLists.txt`.
- **Verification:** Configure/build, both scanner CTests, and the complete 897-test suite passed.
- **Committed in:** `081f450`.

**Total deviations:** 2 Rule 1 fixes. Both corrected acceptance or registration issues directly caused by this plan; no core behavior changed.

## Issues Encountered

The sandbox blocked writing the plan-head ledger inside `.git`. The exact initial HEAD was recorded in `/private/tmp/gabbaboy-plan-head-before-12-18-7d057784` and used to measure the three plan commits.

## User Setup Required

None.

## Next Phase Readiness

Plan 12-18 is complete. Phase GB-12 remains in progress with plan 12-19 next; resume through `/gsd-execute-phase 12`. After Phase 12 completes and is verified, the next phase is **Phase 13: CGB HDMA**. Phase 13 has not started. Keep both auto-advance flags false and stop after Phase 12.

---
*Phase: 12-cgb-double-speed*
*Completed: 2026-10-13*

## Self-Check: PASSED

- Summary file exists at the expected phase path.
- All three task commits are ancestors of the current plan head.
- Summary coverage validation passed (1/1), and its negative-control self-test passed (1/1).
