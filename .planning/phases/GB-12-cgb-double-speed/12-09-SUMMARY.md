---
phase: 12-cgb-double-speed
plan: 09
subsystem: cgb-speed-verification
tags: [cgb, age, stall-window, ctest, sha256]
requires:
  - phase: 12-cgb-double-speed
    provides: "Committed CGB STOP/stall core, pinned AGE corpus, and provisional stall derivation from plans 12-01 through 12-08"
provides:
  - "Bounded AGE verdict driver and a measured spsw-div-cgbBCE budget"
  - "Public mutant library with a committed-core M31 stall-window gate"
  - "Measured stall window, committed constant, and configure-time numeric documentation contract"
affects: [12-cgb-double-speed/12-10, cgb-speed-verification]
actuals:
  tokens: 7201
  tasks: 3
  commits: 3
commits: 3
plan_head_before: 11be544c8e1e114b23aa6ef106a3e54906de829f
plan_head_after: 87caa6868883898016501db310ad7b84a1508f0f
tech-stack:
  added: []
  patterns: [bounded AGE verdicts with distinct timeout, public-API mutant core, configure-time numeric documentation contract]
key-files:
  created: [tests/test_age.c]
  modified: [fixtures/age/manifest.json, tests/CMakeLists.txt, tests/expected-tests.txt, docs/cgb-profile.md, src/core/gabbaboy.c]
key-decisions:
  - "Keep GBB_SPEED_SWITCH_STALL_T at 0x20004 T: committed-core AGE window [0x20004, 0x20007] contains this M-aligned value, so D-37 requires no re-pin."
  - "Treat AGE measurements as pinned author-attested software-corpus evidence; make no physical-hardware claim."
patterns-established:
  - "AGE verdict drivers stop at a named executed instruction and distinguish timeout from an incorrect verdict."
  - "Stall-window boundary controls exercise a build-tree public mutant core against the committed production core."
requirements-completed: [CGB-06]
coverage:
  - id: GB-12-09-AGE
    description: "The bounded AGE driver validates all five spsw-div rows, emits a stable verdict signature, and uses a measured budget with a distinct timeout result."
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: integration
        ref: age_spsw_div_cgbBCE
        status: pass
      - kind: integration
        ref: age_spsw_div_cgbBCE_timeout
        status: pass
  - id: GB-12-09-WINDOW
    description: "The committed-core stall window is re-measured through the public M31 offset seam, including failing controls just outside both passing edges."
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: integration
        ref: age_stall_window
        status: pass
      - kind: integration
        ref: ctest --test-dir build -R '^(age_stall_window|age_spsw_div_cgbBCE|cgb_speed_)' --output-on-failure --no-tests=error
        status: pass
  - id: GB-12-09-DOCS
    description: "The CGB profile records the measured window and source revision, while numeric phrases derive from the core constant and a missing-phrase control still fails."
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: integration
        ref: cgb_speed_profile_contract
        status: pass
      - kind: integration
        ref: cgb_speed_profile_contract_missing_selftest
        status: pass
      - kind: integration
        ref: cgb_adr_half_dot_contract
        status: pass
  - id: GB-12-09-REGRESSION
    description: "The complete configured test inventory passes after the AGE driver, mutant gate, and measured-window contract are committed."
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: integration
        ref: ctest --test-dir build --output-on-failure --no-tests=error -j8
        status: pass
duration: "not captured; task commits span 4m 08s"
completed: 2026-10-13
status: complete
---

# Phase 12 Plan 09: AGE Driver and Committed-Core Stall Window Summary

**A bounded AGE driver now passes the pinned spsw-div corpus under a measured budget, and the committed core confirms stall window [0x20004, 0x20007] T with GBB_SPEED_SWITCH_STALL_T still at 0x20004 T.**

## Performance

- **Duration:** Total plan start time was not captured; the three task commits span 4m 08s.
- **Started:** Not captured.
- **Completed:** 2026-10-13.
- **Tasks:** 3.
- **Files modified:** 6 plan deliverable files.
- **AGE measurement:** 22,702,928 half-dots to verdict; manifest budget 46,000,000 half-dots (twice the measurement, rounded up to the next million).
- **Committed-core window:** inclusive `[0x20004, 0x20007]` T at source revision `2e78a48`; tested `0x20003` fail, `0x20004` pass, `0x20007` pass, and `0x20008` fail. No re-pin was needed.

## Accomplishments

- Added a bounded AGE driver that stops at the first executed `LD B,B` at or after `$0150`, checks the six CPU registers and five WRAM result rows, hashes the rows with the little-endian pass mask, and returns a distinct exit code for timeout. The committed core reports `rows_ok=5/5`, mask `001F`, and signature `9f58a8218c17c35769403cf0d5e0ab0de6024db93cd48fe6b19ffcc040aacc8f`.
- Added `gabbaboy_core_p12_mutants` and a CTest that runs the spsw-div ROM at the four measured-window boundaries through the M31 stall-offset seam. The boundary verdicts are fail/pass/pass/fail; the mutant library is built only in the test build tree.
- Recorded the committed-core measurement and half-dot conversions in `docs/cgb-profile.md`; the CMake documentation contract derives the numeric phrases from the source constant and retains its missing-phrase negative control.
- Re-ran the complete CTest inventory after these changes: 820/820 passed. The AGE results are software evidence from the pinned author-attested corpus, not a physical-hardware measurement.

## Task Commits

1. **Task 1: AGE verdict driver and measured pass budget** — `2e78a48` (`feat`).
2. **Task 2: Public mutant library and committed-core AGE stall-window gate** — `4bd9319` (`feat`).
3. **Task 3: Measured stall-window documentation and numeric contract** — `87caa68` (`docs`).

## Files Created/Modified

- `tests/test_age.c` — bounded AGE verdict, signature, timeout, mutant, stall-window, and scan modes.
- `fixtures/age/manifest.json` — measured spsw-div budget.
- `tests/CMakeLists.txt` and `tests/expected-tests.txt` — AGE targets, mutant library, pass/negative controls, and inventory entries.
- `docs/cgb-profile.md` — measured window, source revision, boundary verdicts, and half-dot conversions.
- `src/core/gabbaboy.c` — refreshed the now-stale provisional-window source comment; the constant remained unchanged.

## Decisions Made

- Kept the provisional `0x20004` T constant after committed-core measurement confirmed it is the M-aligned value inside the pass window. The plan's exact D-37 no-re-pin branch applied.
- Recorded the measured source revision as `2e78a48`, the committed production core used by the AGE window test. Later fixture expectations remain for plan 12-10 and beyond.
- Preserved the source corpus's author-attested provenance and explicitly limited the evidence claim to software measurements.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated the stale provisional-window source comment after measurement.**
- **Found during:** Task 3.
- **Issue:** The source comment still described the confirmed stall window as provisional after the committed-core AGE measurement.
- **Fix:** Updated the comment to match the measured result without changing `GBB_SPEED_SWITCH_STALL_T` or any identity pin.
- **Files modified:** `src/core/gabbaboy.c`.
- **Verification:** `cgb_speed_profile_contract` and `age_stall_window` passed; the profile contract derives numeric values from the unchanged source constant.
- **Committed in:** `87caa68`.

**Total deviations:** 1 auto-fixed (Rule 1 - stale source documentation).
**Impact on plan:** No behavior or pin changed; the docs now agree with the measured window.

## Issues Encountered

- A 10,000,000-half-dot exploratory run ended with the expected `age-timeout`; the measurement run used a larger temporary cap, then stored the required measured-times-two rounded budget of 46,000,000 half-dots.
- The first profile-contract run exposed that its scope marker ended before the numeric paragraph. The measured paragraph was kept contiguous with the scope marker, and the contract plus its missing-phrase negative control passed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Phase GB-12 plan 12-09 execution is complete; Phase 12 remains in progress. The next plan is **12-10 — original CGB speed probe fixture and independently derived expectations**, which can consume the now-confirmed `0x20004` T constant. The next phase after the remaining Phase 12 plans is **Phase 13 — CGB HDMA**; it is not started by this handoff. Continue only with `/gsd-execute-phase 12`. Auto-advance and auto-chain remain disabled.

---
*Phase: 12-cgb-double-speed*
*Completed: 2026-10-13*

## Self-Check: PASSED

- Summary file exists and its recorded `plan_head_after` matches task commit `87caa6868883898016501db310ad7b84a1508f0f`.
- Task commits `2e78a48`, `4bd9319`, and `87caa68` are ancestors of the current plan head.
- `summary_coverage` passed after the summary was written.
