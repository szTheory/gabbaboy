---
phase: GB-19-qualified-v0-3-0-release
plan: "03"
subsystem: release-qualification
tags: [support-claims, release-notes, interop, performance-receipt]
requires:
  - phase: "17 — Native Save State Core"
    provides: [state API, continuation and canonical pin evidence]
  - phase: "18 — Player Save Slots and Host Contract"
    provides: [host and player evidence for the scoped claims]
  - phase: "19-01"
    provides: [release qualification workflow and CTest guardrails]
  - phase: "19-02"
    provides: [state and planning controls carried by the claims]
provides:
  - Managed D-13 support claims with immutable validation, v0.3 rendering, and sidecar binding
  - D-14 drift, evidence, and public-claim rejection controls
  - D-15 release-note requirements bound to the hosted Ir receipt and full source commit
  - Interop scanning for mGBA, SameBoy, BGB, and BESS, including an optional v0.3 ledger
affects: [19-04, 19-06, 19-07, Phase 19 release qualification]
actuals:
  tokens: 24155
  tasks: 3
  commits: 7
plan_head_before: bd67a6d2c9eeff663505205d92c1ab21870b981b
plan_head_after: 42cbba5cae31a9995e590d62f5fa42a7e8cab41c
tech-stack:
  added: []
  patterns:
    - Managed claim data with exact-key validation and derived-value drift controls
    - Release evidence bound to full immutable commit ids
key-files:
  created:
    - tests/data/support-claims-v0.3.json
  modified:
    - tests/scripts/verify-support-ledger.py
    - tests/scripts/verify-version-window.py
    - tests/scripts/verify-v02-adoption.py
    - tests/scripts/verify-perf-gate.py
    - tests/scripts/verify-no-interop-claims.py
    - tests/cmake/host-contract.cmake
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - tests/baseline/perf-attribution-v1.json
    - .github/workflows/release.yml
key-decisions: []
patterns-established:
  - Read release documents and ledgers from immutable full commit ids in CTest contracts
  - Require a tagged-source performance receipt when an attribution run predates the release commit
requirements-completed: []
coverage:
  - id: D1
    description: Nine scoped v0.3 claims and ten non-claims render through the validated v0.3 ledger path, with schema-2 sidecar binding and v0.2 fixed points retained.
    requirement: REL-01
    human_judgment: false
    verification:
      - kind: integration
        ref: "At source 94c79880cf96e7b2bd92e556a1153681deebe24a, CTest support_claims and support_claims_controls passed; controls reported positives=20 controls=16."
        status: pass
  - id: D2
    description: Claim scope, corpus, evidence, platform, pin, required non-claim, and managed-input drift are rejected by automated controls.
    requirement: REL-01
    human_judgment: false
    verification:
      - kind: integration
        ref: "At source 94c79880cf96e7b2bd92e556a1153681deebe24a, release_window_contract and release_window_controls passed; controls reported positives=8 controls=30."
        status: pass
  - id: D3
    description: Release notes require exact same-release state loading, POSIX-only host mode, the regenerated Ir figure and receipt head, and the pre-PR attribution limitation; README, preview, and notes reject unscoped claims.
    requirement: REL-01
    human_judgment: false
    verification:
      - kind: integration
        ref: "At immutable source 42cbba5cae31a9995e590d62f5fa42a7e8cab41c, adoption_claim_boundaries_controls passed with positives=36 controls=24; v02_adoption_docs and v02_adoption_docs_controls also passed."
        status: pass
  - id: D4
    description: The interop contract rejects claims naming mGBA, SameBoy, BGB, and BESS, while accepting scoped disclaimers and checking docs/support/v0.3.0.md when present.
    requirement: REL-01
    human_judgment: false
    verification:
      - kind: integration
        ref: "At immutable source 42cbba5cae31a9995e590d62f5fa42a7e8cab41c, doc_no_interop_claims and contract_rev_wiring passed; interop output files=6 controls=10, including a scratch-commit optional-ledger rejection."
        status: pass
  - id: D5
    description: The notes attribution receipt is regenerated from hosted run 40936934189 attempt 1 and its measured source head is carried into the notes contract.
    requirement: REL-01
    human_judgment: false
    verification:
      - kind: integration
        ref: "At immutable source 42cbba5cae31a9995e590d62f5fa42a7e8cab41c, perf_attribution and perf_attribution_merges passed for receipt head f80bdf54c6c7d81e8e21f0275b43cda6edf6c8c4; measured maximum instruction-count change is +9.6%."
        status: pass
  - id: D6
    description: The expanded CTest inventory retains the new contract test and still rejects missing or incorrectly excluded tests.
    requirement: REL-01
    human_judgment: false
    verification:
      - kind: other
        ref: "bash .github/scripts/verify-test-inventory.sh --self-test; platform exclusions, platform-independent retention, missing-test rejection, and cleanup-trap control passed."
        status: pass
  - id: D7
    description: The realtime floor remains bound to its immutable performance-policy receipt while the regenerated release-notes receipt remains independently verifiable.
    requirement: REL-01
    human_judgment: false
    verification:
      - kind: integration
        ref: "At immutable source 3d6e0a6debb7c3a2b31b8acb7b268cacfd96dd5a, perf_gate_controls passed 34 controls and all ten targeted performance CTests passed; the changed notes receipt is rejected as the policy receipt while the immutable base receipt preserves the 4.02 floor."
        status: pass
metrics:
  duration: 20min
completed: 2026-10-29
status: complete
---

# Phase 19 Plan 03: Scoped Claims and Release Evidence Summary

**The v0.3 support ledger is data-validated, and release claims now bind to hosted performance evidence and immutable source revisions.**

## Performance

- **Duration:** 20 min from the first task commit; executor start time was not persisted.
- **Started:** 2026-10-29T19:15:17Z (first task commit used as the timing baseline).
- **Completed:** 2026-10-29T19:35:38Z.
- **Tasks:** 3.
- **Files modified:** 10 implementation and test files.

## Accomplishments

- Added nine D-13-scoped claims and ten non-claims as managed input. The v0.3 renderer preserves v0.2.x fixed points and binds claim bytes through the schema-2 sidecar.
- Added D-14 controls for missing scope, stale derived values, missing evidence, unexercised platforms, required host/player evidence, managed-input drift, and unscoped public claims.
- Regenerated the Ir attribution receipt through hosted run `40936934189` attempt 1. The receipt is measured at `f80bdf54c6c7d81e8e21f0275b43cda6edf6c8c4`; the measured maximum instruction-count change is `+9.6%`.
- Added release-note checks for same-release state loading, POSIX-only host mode, the receipt figure and head, and the required pre-PR attribution limitation sentence.
- Expanded the interop checker to SameBoy, BGB, and BESS and verified that a v0.3 support ledger is scanned when present at the checked commit.
- Updated the release workflow to pass its full `GITHUB_SHA` into the notes checker.

## Task Commits

1. **Task 1: validated v0.3 claims and renderer**
   - `291195aa` — add scoped v0.3.0 support claims.
   - `79031acc` — correct support claims CTest arguments.
   - `d3ea10bc` — use portable support claims output matcher.
   - `8f98e69a` — compare synthetic ledger bytes correctly.
2. **Task 2: claim drift controls and managed-input freeze**
   - `94c79880` — validate claims drift and freeze managed input.
3. **Task 3: release notes, receipt, and interop controls**
   - `75ba3987` — bind release notes and interop claims.
   - `42cbba5c` — resolve immutable test snapshot roots.

## Files Created/Modified

- `tests/data/support-claims-v0.3.json` — managed claim scope and non-claim statements.
- `tests/scripts/verify-support-ledger.py` — validation, v0.3 rendering, drift checks, and controls.
- `tests/scripts/verify-version-window.py` — claims file included in the managed-input digest.
- `tests/scripts/verify-v02-adoption.py` — release-note and public-claim checks from the receipt and full source revision.
- `tests/scripts/verify-no-interop-claims.py` — immutable interop checks and optional v0.3 ledger scan.
- `tests/cmake/host-contract.cmake`, `tests/CMakeLists.txt`, `tests/expected-tests.txt` — CTest wiring and inventory.
- `tests/baseline/perf-attribution-v1.json` — hosted Ir receipt, SHA-256 `25ad51f963a68c19000b6d6d1cfccc580b0ad066f6aa280d6ed29c305e3030e3`.
- `.github/workflows/release.yml` — pass the source event's full commit id to the release-note checker.

## Decisions Made

No new project decisions. The plan follows D-11 through D-15 and the OQ-3 hosted-measurement resolution.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Pin release-note checks to the release event commit**
- **Found during:** Task 3.
- **Issue:** The release workflow invoked the notes checker without a source revision, so it could not compare the receipt head with the release source commit.
- **Fix:** Pass the full `GITHUB_SHA` as `--rev`; validate it as a 40-character commit id before checking the conditional limitation sentence.
- **Files modified:** `.github/workflows/release.yml`, `tests/scripts/verify-v02-adoption.py`.
- **Verification:** `adoption_claim_boundaries_controls` passed from immutable source `42cbba5cae31a9995e590d62f5fa42a7e8cab41c`.
- **Committed in:** `75ba3987`.

**2. [Rule 1 - Bug] Canonicalize the temporary snapshot root on macOS**
- **Found during:** Task 3.
- **Issue:** `TemporaryDirectory` returned a `/var` path while resolved files used `/private/var`, causing the immutable receipt test's containment check to reject its own fixture.
- **Fix:** Resolve the temporary root before writing the pinned snapshot.
- **Files modified:** `tests/scripts/verify-v02-adoption.py`.
- **Verification:** The immutable adoption control passed with 36 positives and 24 rejected controls.
- **Committed in:** `42cbba5c`.

### Plan-Recorded Deviation

**19-03-D1.** The plan authorized OQ-3's `perf-attribution.yml` dispatch on main before PR A, though the D-01 exception had previously named only D-05 and D-06. Run `40936934189` completed successfully at main `f80bdf54c6c7d81e8e21f0275b43cda6edf6c8c4`; its receipt is committed for PR A.

**Total deviations:** 2 auto-fixed issues and 1 plan-recorded deviation.
**Impact on plan:** The release workflow now supplies the evidence required by the immutable checker, and the temporary fixture works on macOS. No release scope changed.

## Issues Encountered

The first post-commit CTest run was configured with the default symbolic `HEAD`, which the new interop checker correctly rejected. Reconfigured with `GBB_SAVE_FORMATS_REV=42cbba5cae31a9995e590d62f5fa42a7e8cab41c`; the focused CTest run then passed 9/9.

## Wave 1 Integration Follow-up

- **Commit:** `3d6e0a6debb7c3a2b31b8acb7b268cacfd96dd5a` binds the realtime-floor check to the receipt at immutable `LIMITS_BASE_REV` (`947d6a9d177af6c04a5f9ea6abcc2c470ab9be57`), with a pinned receipt SHA-256 and head. The regenerated notes receipt remains independently checked and cannot raise the D-24 performance threshold. The limits file and its 4.02 floor were unchanged.
- **CTest:** At that source, 15 of 16 focused tests passed: all ten targeted performance CTests, `test_budget` and its controls, `release_review_controls`, `contract_rev_wiring`, and `adoption_claim_boundaries_controls`. `verify-test-inventory.sh --self-test` passed.
- **Environment-limited:** `release_review_approval` did not reach its approval assertion because this sandbox denied `git worktree add` from writing `.git/worktrees`. The scoped escalated retry remains with the phase orchestrator. Results were saved separately in `build/phase19-wave1-perf-fix-3d6e0a6d.xml`; the original Wave 1 log and JUnit were left untouched.

## User Setup Required

The orchestrator resolved the Wave 1 sandbox limitation at `cb1bb07440f8df5cf1c845eb8c638b86c673bdb4`: a scoped rerun passed 3/3 (`v02_performance_controls`, `v02_delivery_controls`, `release_review_approval`). Evidence: `build/phase19-wave1-sandbox-rerun.xml`. The earlier failed and blocked runs remain recorded above.

None.

## Next Phase Readiness

Plan 19-04 can proceed in Phase 19. REL-01 remains pending until exact-tag publication and readback. Owner acknowledgment of D-09 remains pending for PR A review, and the two SDL menu-shortcut tests remain display-limited on this host. The next command is `/gsd-execute-phase 19`.

## Self-Check: PASSED

- The summary exists, its coverage contract passes, and all seven task commits are ancestors of `42cbba5cae31a9995e590d62f5fa42a7e8cab41c`.
- The measured plan commit count is 7 from `bd67a6d2c9eeff663505205d92c1ab21870b981b` through `42cbba5cae31a9995e590d62f5fa42a7e8cab41c`.
- The later integration repair is recorded separately in the Wave 1 follow-up; it does not change the measured task-commit count above.
- The stub scan found only deliberate empty-input negative controls and an existing workflow initialization; no deliverable stubs were introduced.
- The threat-surface scan found no new service endpoint, authentication path, or runtime trust-boundary access.
- Owner edits to `.planning/config.json` and `.planning/state.json` remain unstaged and untouched.

---
*Phase: GB-19-qualified-v0-3-0-release*
*Completed: 2026-10-29*
