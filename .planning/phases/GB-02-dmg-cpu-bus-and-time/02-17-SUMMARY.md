---
phase: GB-02-dmg-cpu-bus-and-time
plan: 17
subsystem: testing
tags: [mooneye, fixtures, wla-dx, cross-host, cpu-05]
candidate_gate: admitted
phase17_head: 93647ac98b7f8437cc9640e3dec437bba4f11e9c

requires:
  - phase: GB-02-dmg-cpu-bus-and-time
    provides: pinned Mooneye source, local source-qualified result protocol, and baseline fixture inventory
provides:
  - deterministic WLA-DX candidate linker recipe using input section appearance order
  - exact Darwin/arm64 and hosted Linux/x86_64 candidate byte identity at retained source revision and workflow run
  - admitted source-qualified DAA and timer candidate ROMs with fixed denominator and immutable pre-admission baseline
  - staged promotion and baseline restoration guard with isolated rollback test
affects: [GB-02 Plan 02-16, CPU-05, Mooneye fixtures]

actuals:
  tokens: 35048
  tasks: 3
  commits: 6

tech-stack:
  added: []
  patterns:
    - candidate digest lock separated from the strict fixture manifest
    - retain exact hosted evidence before staging candidate promotion
    - restore raw Git blobs and verify denominator after failed promotion

key-files:
  created:
    - fixtures/mooneye/pre-admission-baseline.json
    - tests/scripts/verify-mooneye-hosted-candidate.sh
    - tests/scripts/verify-mooneye-unadmitted.sh
  modified:
    - tests/scripts/reproduce-mooneye.sh
    - .github/workflows/fixture-repro.yml
    - fixtures/mooneye/candidate-digests.json
    - fixtures/mooneye/manifest.json
    - fixtures/mooneye/ELIGIBILITY.md
    - fixtures/mooneye/SOURCES.md

key-decisions:
  - "Use `wlalink -nS -d -S` so tied sections follow source appearance order; no WLA-DX tool patch was needed."
  - "Admit derived candidate bytes only after all three local/hosted byte arrays, source/rights provenance, and positive/negative protocol probes pass."
  - "Keep the original manifest and ROM blobs separately captured and retain the one-CPU/two-timer denominator."

patterns-established:
  - "Bind hosted artifact evidence to the exact pushed source SHA, workflow path, run, and candidate digest lock."
  - "Build and validate a complete candidate fixture set in isolation before atomically promoting it."

requirements-completed: [CPU-05]

plan_head_before: bdf214bc978548baa3b501c90b2efc5c654c5279
plan_head_after: b088b3e145d61a72697fbdd04aaf8952058bdd6d
commits: 6
duration: 54min
completed: 2026-10-07
status: complete
---

# Phase GB-02 Plan 02-17: Deterministic Mooneye Candidate Qualification Summary

**Pinned `wlalink -nS -d -S` output for three source-qualified candidates matched exact hosted Linux bytes, passed protocol and provenance gates, and was admitted without changing the one-CPU/two-timer denominator.**

## Performance

- **Duration:** 54 min
- **Started:** 2026-10-07T01:44:10Z (plan commit timestamp; execution began after planning)
- **Completed:** 2026-10-07T02:37:49Z
- **Tasks:** 3
- **Files modified:** 12 plan implementation files, plus phase summary/state/roadmap/continuation records

## Accomplishments

- Captured the original manifest's raw SHA-256 (`76204bc792a5a767f3d7430edfe5542698953507fe268de6a0154b7cb02bcc3e`), original ROM Git-blob digests, source HEAD `bdf214bc978548baa3b501c90b2efc5c654c5279`, exact eligible IDs, and the unchanged one-CPU/two-timer denominator in `pre-admission-baseline.json`.
- Selected the documented `wlalink -nS -d -S` input-appearance ordering recipe. Two complete local builds were byte-identical for each 32,768-byte candidate; the pinned source/tool/font/harness identities and three acceptance-source digests remained unchanged.
- Qualified exact pushed commit `93647ac98b7f8437cc9640e3dec437bba4f11e9c` with completed hosted `fixture-repro.yml` push run [37561292904](https://github.com/szTheory/gabbaboy/actions/runs/37561292904). The retained Linux/x86_64 artifact matched the local Darwin/arm64 byte arrays exactly:

  | Candidate | Size | SHA-256 | Local/hosted |
  |---|---:|---|---|
  | DAA | 32,768 | `3a39eda77a09b817e4e38004a3d117990565fb797e8a4f470920f1b7608f0a08` | identical |
  | TIM00 | 32,768 | `476b2332de3f2d6604f8e1478daa8cbc7c59c89c50837fd47cc95e96e784d4f7` | identical |
  | TIM00 DIV trigger | 32,768 | `566da853858061c69866c47cc31b85b1fef003d4c088c8e8dbb26973da9944da` | identical |

- Positive and induced-negative probes reached their source callbacks and the original symbol-addressed `LD B,B` result breakpoint with zero PPU accesses. Source closure, MIT and replacement-font notices, bootless DMG-CPU-B profile, finite budgets, and pinned source/tool/patch identities passed review.
- Staged and promoted the three derived candidate ROMs and manifest. The final manifest SHA-256 is `98a1799b8be9c022ac13467a552890fb12bdd706017e42e12c944ec618d60527`; strict `cmake -DGBB_MOONEYE_DIR=fixtures/mooneye -P cmake/VerifyMooneye.cmake` reported `3 eligible Mooneye ROM(s): 1 CPU, 2 timer (complete)`.
- The rollback self-test passed before promotion. No live rollback was needed. The historical Plan 02-15 summary remains unchanged.

## Task Commits

1. **Task 1: Establish and locally prove a deterministic candidate linker recipe** — `0a69676` (`feat`)
2. **Task 2: Compare all three candidate byte streams on local and hosted Linux** — `e2bdaa5`, `10c9766`, `93647ac`, `c498abf` (`feat`, two blocking fixes, evidence docs)
3. **Task 3: Admit candidates only after every source, protocol and byte gate passes** — `b088b3e` (`feat`)

**Plan metadata:** committed separately with the summary and phase state records; the metadata commit is reported in the executor completion record.

## Decisions Made

- WLA-DX's documented `-nS` ordering solved cross-host candidate byte differences, so no tool source patch or dependency was added.
- Candidate admission changes current fixture bytes only after exact all-three cross-host byte identity and complete source, rights, protocol, model, and budget review. The original bytes, raw manifest, and denominator remain machine-readable rollback evidence.
- CPU-05 remains pending until Plan 02-16 verifies runner receipts, inventory behavior, and independent Phase 2 evidence.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking issue] Fetch baseline Git blobs for original-ROM diagnostics**
- **Found during:** Task 2
- **Issue:** The original-reproduction job used a shallow checkout that did not contain the captured source commit needed to read original ROM Git blobs.
- **Fix:** Set `fetch-depth: 0` for that diagnostic job so the baseline source commit is available.
- **Files modified:** `.github/workflows/fixture-repro.yml`
- **Verification:** The exact hosted fixture workflow completed successfully and retained its candidate evidence.
- **Committed in:** `10c9766`

**2. [Rule 3 - Blocking issue] Select only exact push/workflow-dispatch evidence**
- **Found during:** Task 2
- **Issue:** The verifier could select a matching `pull_request` merge-SHA run even when the required exact-head `push` run was available.
- **Fix:** Restrict candidate evidence selection and verify-only qualification to the allowed event types and exact pushed source SHA.
- **Files modified:** `tests/scripts/verify-mooneye-hosted-candidate.sh`
- **Verification:** Run `37561292904` matched the exact pushed task revision and workflow path; all three artifact byte comparisons and identity checks passed.
- **Committed in:** `93647ac`

**Total deviations:** 2 auto-fixed (2 blocking issues)
**Impact on plan:** Both fixes were required to bind original diagnostics and hosted candidate evidence correctly. Scope remained within the plan.

## Issues Encountered

- A second rollback-self-test invocation after promotion correctly refused to treat the promoted manifest as the pre-admission baseline. The required isolated rollback self-test had already passed before promotion; the post-promotion strict manifest verifier passed. No rollback was triggered.
- The candidate lock's local output path was refreshed by the final local verification run before staging; the promoted manifest binds the resulting lock digest.

## User Setup Required

None. The exact hosted run and retained artifact were available; no credential or manual UAT step was required.

## Next Phase Readiness

- Plan 02-17 is complete and the deterministic candidate gate is admitted.
- Plan 02-16, “verify runner protocol, inventory, and final exact-revision evidence,” is next in Phase GB-02. Run `$gsd-execute-phase 2 --gaps-only`.
- CPU-01 through CPU-05 and Phase 2 remain pending independent verification. Phase 3 — Visible Interactive DMG remains paused until Phase 2 gaps and required checks close and the owner chooses to continue.

## Self-Check: PASSED

---
*Phase: GB-02-dmg-cpu-bus-and-time*
*Completed: 2026-10-07*
