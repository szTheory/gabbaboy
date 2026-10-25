---
phase: 12-cgb-double-speed
plan: 16
subsystem: testing
tags: [age, cgb, fixtures, ctest, reproducible-build]
requires:
  - phase: GB-12 plans 12-09 and 12-15
    provides: Committed-core AGE driver and CGB speed-switch implementation pinned at the measured stall window
provides:
  - Thirteen AGE ROMs pinned to committed-core signatures and row masks with measurement-derived budgets
  - Configure-time generated AGE disposition tests and fixture digest, rebuild, and install guards
affects: [GB-12 plan 12-17, CGB-06, AGE fixtures]
actuals:
  tokens: 6897.5
  tasks: 3
  commits: 4
commits: 4
plan_head_before: db1dd7b9635752c96f99f76fd9f2594ad80af5d1
plan_head_after: c0c9a5c0eb8a341368db7d678d800e0e60310f35
tech-stack:
  added: []
  patterns:
    - Disposition JSON drives one exact-behavior CTest per vendored AGE ROM, joined to its manifest layout and budget.
    - Fixture redistribution scans match both path labels and content digests, with renamed-copy negative controls.
key-files:
  created:
    - tests/external/cgb-speed-dispositions.json
  modified:
    - fixtures/age/manifest.json
    - fixtures/age/SOURCES.md
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - cmake/ExpectedTests.cmake
key-decisions:
  - Pin pass or expected-failure only from measurements on the committed core; apply the D-19 Tima contingency because spsw-tima-cgbE fails.
  - Keep the Linux fixture-reproduction note provisional because no hosted fixture-repro run exists for this branch.
patterns-established:
  - Measured per-ROM half-dot budgets are twice the observed verdict distance rounded upward to the next million.
  - Expected-failure signatures and row masks flip the test red if bytes of behavior change or the ROM begins to pass.
requirements-completed: [CGB-06]
coverage:
  - id: CGB-06-AGE-VERDICTS
    description: Each admitted AGE ROM is pinned to its measured committed-core outcome, with expected failures carrying exact signatures, row masks, flip rules, and bounded budgets.
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: integration
        ref: age_spsw_div_cgbBCE
        status: pass
      - kind: integration
        ref: age_spsw_tima_cgbE
        status: pass
      - kind: integration
        ref: age_spsw_tima_cgbBC
        status: pass
      - kind: integration
        ref: age_spsw_stop_prefetch_cgbBCE
        status: pass
      - kind: integration
        ref: age_spsw_interrupts_cgbE
        status: pass
      - kind: integration
        ref: age_spsw_mode0_cgbBCE
        status: pass
      - kind: integration
        ref: age_spsw_ch2_lc_delay_cgbBCE
        status: pass
      - kind: integration
        ref: age_stat_mode_ds_cgbBCE
        status: pass
      - kind: integration
        ref: age_stat_mode_cgbE
        status: pass
      - kind: integration
        ref: age_stat_mode_sprites_ds_cgbBCE
        status: pass
      - kind: integration
        ref: age_stat_mode_sprites_dmgC_cgbBCE
        status: pass
      - kind: integration
        ref: age_stat_mode_window_ds_cgbBCE
        status: pass
      - kind: integration
        ref: age_stat_mode_window_cgbBCE
        status: pass
  - id: CGB-06-AGE-DIGEST
    description: The AGE fixture manifest verifies all vendored digests and rejects a deliberately changed digest pin.
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: integration
        ref: age_fixture_digest
        status: pass
      - kind: integration
        ref: age_fixture_digest_tampered
        status: pass
  - id: CGB-06-AGE-REPRODUCTION
    description: Offline rebuild self-check and tampered-manifest and tampered-ROM negative controls detect changed fixture provenance or bytes.
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: other
        ref: age_repro_selfcheck
        status: pass
      - kind: other
        ref: age_repro_selfcheck_tampered
        status: pass
      - kind: other
        ref: age_repro_compare_tampered
        status: pass
  - id: CGB-06-AGE-NOT-INSTALLED
    description: AGE ROM bytes are absent from the install tree, and the renamed-copy control proves the scan detects them by digest.
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: integration
        ref: age_not_installed
        status: pass
      - kind: integration
        ref: age_not_installed_selftest
        status: pass
metrics:
  duration: 16min
  completed: 2026-10-13
status: complete
---

# Phase 12 Plan 16: AGE Verdicts and Fixture Guards Summary

**All thirteen AGE ROMs now have measurement-pinned CTest verdicts, bounded budgets, digest checks, offline tamper controls, and an install-tree scan.**

## Performance

- **Duration:** About 16 minutes; start time is estimated from the preceding plan handoff.
- **Started:** 2026-10-13T21:05:00-04:00
- **Completed:** 2026-10-13T21:21:09-04:00
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments

- Generated one `age_<case>` CTest per admitted ROM from the dispositions JSON. On core revision `db1dd7b9635752c96f99f76fd9f2594ad80af5d1`, `spsw-div-cgbBCE` and `spsw-stop-prefetch-cgbBCE` pass; the other eleven are pinned expected failures with their measured signatures and row masks.
- Recorded measured half-dots and local wall times for all thirteen ROMs in `fixtures/age/SOURCES.md`. Manifest budgets are twice each measured half-dot count, rounded up to the next million.
- Added digest verification and its tampered-manifest control, offline self-check and both tampered reproduction controls, and install-tree scan plus renamed-copy negative control. The Linux reproduction note remains provisional pending a hosted run.

## Task Commits

1. **Task 1: Generate AGE CTests from the two initial measured dispositions** — `8467e02` (feat)
2. **Task 2: Pin the remaining measured AGE verdicts and timings** — `71ef849` (feat)
3. **Task 3: Guard AGE digest, reproduction, and install behavior** — `15901e0` (test)
4. **Task 2 follow-up: Clarify passing-row counts in the source table** — `c0c9a5c` (docs)

## Files Created/Modified

- `tests/external/cgb-speed-dispositions.json` — thirteen measurement-derived dispositions, signatures, row masks, reasons, owners, and flip rules.
- `fixtures/age/manifest.json` — measured, rounded-up per-ROM run budgets.
- `fixtures/age/SOURCES.md` — committed-core verdict measurements and local wall times; hardware receipt language remains excluded.
- `tests/CMakeLists.txt` — JSON-driven AGE tests, digest controls, offline reproducibility controls, and install scan.
- `tests/expected-tests.txt`, `cmake/ExpectedTests.cmake` — CTest inventory and Windows exclusion of the three bash-only tests.

## Decisions Made

- The CGB-E Tima ROM fails on the committed core, so D-19 requires pinning both Tima ROMs as expected failures and dropping the B/C claim instead of marking the B/C case unsupported-model.
- STAT fallback reasons follow row analysis and the single-speed sibling rule; no core changes were made to force any AGE row to pass.
- No hosted fixture-repro run exists for this branch, so the Linux digest note stays provisional and no CI receipt is claimed.

## Deviations from Plan

**1. The plan's broad AGE inventory selector includes a pre-existing timeout negative control.**

- **Found during:** Task 2 verification.
- **Issue:** `ctest --test-dir build -R '^age_(spsw|stat)_' -N` lists 14 tests because the earlier `age_spsw_div_cgbBCE_timeout` control also matches the selector, while the plan's acceptance line expects 13.
- **Fix:** Kept the existing timeout control intact and separately verified the 13 generated ROM disposition tests. The broad selector passed 14/14.
- **Files modified:** `tests/expected-tests.txt` (the legacy control remains registered).
- **Verification:** All 13 generated disposition tests and the timeout negative control passed.
- **Ledger:** Recorded in `.planning/WINDOWS.md` as deviation 14.

**Total deviations:** 1 plan acceptance-count mismatch; no additional implementation scope.
**Impact on plan:** All planned deliverables are implemented and pass. The inherited timeout control remains unchanged.

## Validation Evidence

- `cmake --preset phase1 && cmake --build --preset phase1` — passed.
- `ctest --test-dir build -R '^age_(spsw|stat)_' --output-on-failure --no-tests=error` — 14/14 passed: 13 generated ROM verdicts plus the pre-existing timeout control.
- `ctest --test-dir build -R '^(age_fixture_digest|age_repro_|age_not_installed)' --output-on-failure --no-tests=error` — 8/8 passed, including both tampering controls and the install-scan negative control.
- `ctest --test-dir build -j8 --output-on-failure` — 875/875 passed.
- `git diff --check` — passed before task commits.

## Issues Encountered

No hosted Linux fixture-reproduction run was available. The source note correctly remains provisional, and no hardware evidence or reproducible hardware receipt is claimed.

## User Setup Required

None.

## Next Phase Readiness

Plan 12-16 is complete; Phase 12 remains in progress. Next is **GB-12 plan 12-17 — disposition pins, named failures, and stall sensitivity**. Continue with **`/gsd-execute-phase 12`**. After all Phase 12 work and its gates, stop for the owner; Phase 13 — CGB HDMA has not started.

---
*Phase: 12-cgb-double-speed*
*Completed: 2026-10-13*

## Self-Check: PASSED

- The four plan commits are ancestors of `c0c9a5c` and match the measured plan ledger.
- All six plan artifacts exist and are included in task commits.
- The full CTest run passed 875/875; `summary_coverage` passed with this summary's structured coverage block.
