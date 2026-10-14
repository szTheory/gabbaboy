---
phase: 12-cgb-double-speed
plan: 19
subsystem: testing
tags: [CGB, AGE, CTest, hosted-CI, benchmarking, handoff]
requires:
  - phase: GB-12 plans 12-12 and 12-18
    provides: Public CGB claims, model limits, prior summary coverage contracts, and selected AGE dispositions
provides:
  - Adopted Phase 12 decisions, concrete lessons, and evidence navigation
  - Advisory CGB timing measurements and exact-head CI, fixture, and package receipts
  - Automated closeout and negative-control checks with a verification-first handoff
affects: [Phase 12 verification, Phase 13 CGB HDMA, native integrators]
actuals:
  tokens: 17040.50
  tasks: 3
  commits: 4
commits: 4
plan_head_before: f8c7a7df2dad4d2aec995916ee2caf5b7121a963
plan_head_after: d1254a82e8c2904d4a6e6897eeb9b35d8b879ecb
tech-stack:
  added: []
  patterns:
    - Every durable closeout claim is checked by a contract validator with scratch-mutated negative controls.
    - Source-provenance pins are kept distinct from plan and hosted-verification revisions.
key-files:
  created:
    - .planning/phases/GB-12-cgb-double-speed/COVERAGE.md
    - .planning/phases/GB-12-cgb-double-speed/verify-closeout-contract.py
    - .planning/phases/GB-12-cgb-double-speed/12-19-SUMMARY.md
  modified:
    - .planning/context/DECISIONS.md
    - .planning/context/LESSONS.md
    - .planning/research/INDEX.md
    - .planning/phases/GB-12-cgb-double-speed/12-BENCH.md
    - .planning/STATE.md
    - .planning/.continue-here.md
    - fixtures/age/SOURCES.md
    - .github/scripts/verify-test-inventory.sh
    - .github/workflows/ci.yml
key-decisions:
  - Record D-084 through D-095 for adopted Phase 12 decisions D-37 through D-42 and owner-veto outcomes, with evidence and revisit triggers.
  - Keep the 0x20004 T stall at the measured AGE window [0x20004, 0x20007], with low bits explicitly unresolved; scope AGE to two passing cases and eleven named expected failures.
  - Preserve fixture-source identity, pre-change identity pins, plan execution start, and hosted verification head as distinct revisions.
  - Keep the PR draft and Phase 12 in progress until the owner completes /gsd-verify-work 12 and the tail reviews.
patterns-established:
  - Cross-phase memory and handoff metadata receive positive and scratch-mutation checks.
  - Historical CI wall-time comparisons include inventory and runner caveats and do not imply performance attribution.
requirements-completed: [CGB-06]
coverage:
  - id: CGB-06-MEMORY
    description: Adopted decisions D-084 through D-095, lessons GB-CGB-008 through 010, and the Phase 12 evidence index are complete with resolving links and bounded evidence claims.
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: integration
        ref: "python3 -I .planning/phases/GB-12-cgb-double-speed/verify-closeout-contract.py --self-test"
        status: pass
  - id: CGB-06-BENCHMARK
    description: The advisory CGB measurement, DMG digest, AGE and partition timings, mutant build costs, Phase 12 ASan test-duration sum, and qualified GB-CI-004 comparison are recorded from preserved samples and exact hosted logs.
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: integration
        ref: "python3 -I .planning/phases/GB-12-cgb-double-speed/verify-closeout-contract.py --self-test"
        status: pass
      - kind: integration
        ref: "CI run 38502094649 at 301f1b05577e6d35a4c3a756ded1ec15a4082c8d: required-native and all required PR jobs passed"
        status: pass
  - id: CGB-06-FIXTURE-RECEIPTS
    description: The pinned Linux rebuild is byte-identical for all 13 AGE ROMs and both CGB-speed ROMs; tampered AGE reproduction controls pass, and no hardware behavior is inferred.
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: integration
        ref: "CI fixture-reproduction run 38502094682, job 115651190879"
        status: pass
      - kind: integration
        ref: age_repro_compare_tampered
        status: pass
      - kind: integration
        ref: age_repro_selfcheck_tampered
        status: pass
  - id: CGB-06-WINDOWS-INVENTORY
    description: The Windows required-test filter excludes only the 12 known WIN32 Bash-only tests; it preserves unrelated tests and still rejects a missing required test.
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: integration
        ref: "bash .github/scripts/verify-test-inventory.sh --self-test"
        status: pass
      - kind: integration
        ref: "CI run 38502094649: native-windows-x64 and required-native passed"
        status: pass
  - id: CGB-06-COVERAGE-AND-HANDOFF
    description: API coverage is explicitly declared, all plan summaries pass the machine-readable coverage schema, and state points to Phase 12 verification before any Phase 13 entry.
    requirement: CGB-06
    human_judgment: false
    verification:
      - kind: integration
        ref: "gsd_run check api-coverage.verify-pre .planning/phases/GB-12-cgb-double-speed"
        status: pass
      - kind: integration
        ref: summary_coverage
        status: pass
      - kind: integration
        ref: summary_coverage_selftest
        status: pass
      - kind: integration
        ref: "python3 -I .planning/phases/GB-12-cgb-double-speed/verify-closeout-contract.py --self-test"
        status: pass
metrics:
  duration: 50m 37s
  completed: 2026-10-14
status: complete
---

# Phase 12 Plan 19: CGB Double-Speed Close-out Summary

**Phase 12 close-out records model-scoped CGB timing evidence, exact-head fixture and CI receipts, and an automated handoff to verification.**

## Performance

- **Duration:** 50 minutes 37 seconds.
- **Started:** 2026-10-14T02:13:01Z.
- **Completed:** 2026-10-14T03:03:38Z.
- **Tasks:** 3.
- **Files modified:** 12.
- **Local verification:** 897/897 CTests passed in 40.06 seconds. The DMG baseline check passed with inventory 313, Mooneye 15, acceptance 20, benchmark 2, and zero changed rows.

## Accomplishments

- Added D-084 through D-095, lessons GB-CGB-008 through 010, and a Phase 12 research-index entry. The records preserve the stall window `[0x20004, 0x20007]`, low-bit uncertainty, the limited AGE verdicts, corrected M28 scope, TIMA contingency, and the different source and execution revisions used by the pre-change identity pins.
- Recorded the advisory Release measurement with host class, compiler, workload, ROM digest, three warm-ups, 30 samples, output digest, spread and uncertainty. The DMG digest remains `4c7a57ff3d50d228`; the five planned mutant build sites and measured local configure/build costs are recorded.
- Captured exact H2 hosted evidence at `301f1b05577e6d35a4c3a756ded1ec15a4082c8d`. CI, fixture-reproduction and package-smoke PR runs `38502094649`, `38502094682`, and `38502094771` passed. The ASan/UBSan job ran 892/892 tests without skips in 579.99 seconds; the 206 Phase 12 additions account for 325.28 seconds as a sum of individual test durations, not wall time.
- Recorded that the exact Linux RGBDS 1.0.1 job rebuilt all 13 AGE ROMs and both CGB-speed ROMs byte-identically. Tampered AGE compare and self-check controls passed. This is byte-reproduction evidence, not hardware evidence.
- Added a scratch-mutated closeout contract with 17 negative controls and fixed a Windows inventory filter mismatch found by H1 CI. H1's test inventory failure remains documented; the exact H2 PR checks pass after the narrow correction.
- Wrote the one-line API coverage declaration and handed off to `/gsd-verify-work 12`; Phase 13 remains unstarted and auto-advance stays disabled.

## Task Commits

1. **Task 1: adopted decisions, lessons, and research index** — `b03e6a6` (`docs`).
2. **Task 2 CI correction: align WIN32 test inventory and add platform-filter self-test** — `301f1b0` (`fix`).
3. **Task 2: benchmark and fixture receipts** — `df142f4` (`docs`).
4. **Task 3: coverage contract and Phase 12 handoff** — `d1254a8` (`docs`).

**Plan metadata:** recorded in the final documentation commit after self-check.

## Files Created/Modified

- `.planning/context/DECISIONS.md` — adopted D-084 through D-095.
- `.planning/context/LESSONS.md` — evidence-based CGB lessons GB-CGB-008 through 010.
- `.planning/research/INDEX.md` — Phase 12 evidence navigation and model-scoped caveats.
- `.planning/phases/GB-12-cgb-double-speed/12-BENCH.md` — local measurements, hosted receipts, test duration and CI caveats.
- `.planning/phases/GB-12-cgb-double-speed/COVERAGE.md` — API coverage-gate declaration.
- `.planning/phases/GB-12-cgb-double-speed/verify-closeout-contract.py` — positive closeout check and scratch-mutation controls.
- `.planning/phases/GB-12-cgb-double-speed/12-19-SUMMARY.md` — this plan summary and its coverage matrix.
- `.planning/STATE.md` and `.planning/.continue-here.md` — exact handoff and route to verification.
- `fixtures/age/SOURCES.md` — exact Linux fixture-byte reproduction receipt.
- `.github/scripts/verify-test-inventory.sh` and `.github/workflows/ci.yml` — exact WIN32 exclusions and a registered filter self-test.

## Decisions Made

- The model-selected stall is `0x20004` T inside the AGE pass window `[0x20004, 0x20007]`; that fixture does not discriminate the low bits.
- Only `spsw-div-cgbBCE` and `spsw-stop-prefetch-cgbBCE` pass. Eleven admitted AGE cases remain named expected failures. Corrected double-only M28 detects the mode-0 signature but not the DIV signature; the `spsw-tima-cgbBC` contingency removes the B/C TIMA claim.
- GB-CI-004's 826–915-second interval is observed ASan CTest wall time at `--parallel 4`. The current 579.99-second wall time is compared descriptively across different revisions, inventories, and runners; no speedup or Phase 12 attribution is claimed. The separate 325.28-second total is the elapsed-time sum for the 206 Phase 12-added tests.
- The `fb45111` baseline and `aac4772` plan execution start remain distinct provenance pins; their relevant core and public-header files agree. No identity pins were re-recorded.

## Deviations from Plan

### Sequencing adjustment

A truthful `12-BENCH.md` scaffold was added with Task 1 so the unchanged tracer gate's all-links contract would pass. Task 2 later filled it with measured results and hosted receipts; no absent-target exception was added.

### Auto-fixed issues

**1. [Rule 3 - Blocking issue] Corrected the Windows required-test inventory.**

- **Found during:** Task 2 exact-head PR CI, H1 at `b03e6a6`.
- **Issue:** All 885 native Windows CTests passed, but the inventory verifier required five bash-only AGE/CGB reproduction tests that CMake correctly excludes on WIN32.
- **Fix:** Added only the exact WIN32 filter exclusions and registered a platform-filter self-test. Its positive control preserves platform-independent required tests, while its negative control rejects a genuinely missing required test. No broad CGB prefix removal was used.
- **Files modified:** `.github/scripts/verify-test-inventory.sh`, `.github/workflows/ci.yml`.
- **Verification:** H2 exact PR Linux self-test, native Windows inventory, `required-native`, full local 897/897 suite, and closeout contract with 17 scratch mutations passed.
- **Committed in:** `301f1b0`.

**2. [Rule 2 - Missing critical check] Added a closeout contract for durable metadata.**

- **Found during:** Task 3 D-069 review.
- **Issue:** The handoff, benchmark metadata, fixture receipt, privacy scan, and negative-control expectations otherwise relied on prose checks spread across the plan.
- **Fix:** Added a standard-library validator that checks these artifacts together and rejects 17 scratch mutations, including missing decisions, broken links, changed digests, incomplete fixture receipts, changed benchmark statistics, stale routes, enabled auto-advance, and a started Phase 13 directory.
- **Files modified:** `.planning/phases/GB-12-cgb-double-speed/verify-closeout-contract.py`.
- **Verification:** `python3 -I .planning/phases/GB-12-cgb-double-speed/verify-closeout-contract.py --self-test` passed.
- **Committed in:** `d1254a8`.

**Total deviations:** 3 (one sequencing adjustment and two automated fixes).
**Impact on plan:** The new checks close the Windows gate and D-069 artifact-validation gap without changing emulator behavior or broadening hardware claims.

## Issues Encountered

- H1's exact PR CI exposed the Windows inventory mismatch described above. The H2 correction passed all exact PR checks. The earlier failure remains part of the record.
- `gh run watch` could not read the Checks API with the available token. The authorized `gh pr checks`, `gh run view`, and Actions job-log endpoints provided exact revision-bound evidence, so hosted verification was not blocked.
- Phase 12 has no physical hardware measurement. All AGE and CGB fixture outcomes remain limited to named software cases and generated ROM bytes.
- Issue/PR boundary triage found no open issues and one open PR: draft PR #68. It remains unmerged pending tail review and Phase 12 verification.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 12-19 is complete. Phase 12 remains in progress until `/gsd-verify-work 12` and the execute-phase tail reviews are complete. PR #68 is open, draft, and unmerged. Phase 13: CGB HDMA has not started; after verification and merge, the owner can enter it with `/gsd-discuss-phase 13`. Both workflow auto-advance flags remain false.

## Self-Check: PASSED

- Confirmed the summary, benchmark, coverage declaration, memory files, fixture receipt, validator, and handoff files exist.
- Confirmed all four task commits are ancestors of the current branch and measured four plan commits from the persisted start ledger.
- Confirmed `summary_coverage`, `summary_coverage_selftest`, the closeout contract positive case and its 17 mutated negatives pass after this SUMMARY is written.
- Confirmed the API coverage gate, exact H2 PR CI, fixture-reproduction and package-smoke receipts, and the current state route; Phase 13 does not exist.

---
*Phase: 12-cgb-double-speed*
*Plan: 19*
*Completed: 2026-10-14*
