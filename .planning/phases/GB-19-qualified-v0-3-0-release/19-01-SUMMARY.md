---
phase: GB-19-qualified-v0-3-0-release
plan: "01"
subsystem: release-infra
tags: [release, ci, timeout-ledger, linkage, policy-controls]
requires:
  - phase: GB-18-player-save-slots-and-host-contract
    provides: "Player build and core-linkage checker used to close RM-031"
provides:
  - "Normal timeout rows with offline tree equality, main-anchor, disclosure and online cited-run verification"
  - "Release-head retention check for tree-equal citations, full-history rehearsal judge and VERSION 0.3.0 checkout controls"
  - "Correct player-core linkage and policy-pinned CI budget and read-only checkout controls"
affects: [19-02, 19-06, 19-07, docs/release.md]
actuals:
  tokens: 11014
  tasks: 4
  commits: 4
commits: 4
plan_head_before: 33b6c569edfad3d4960129b2b8a53591eb4aebfb
plan_head_after: 6b35be140b9c5823f0a1866601e8133cb012525b
tech-stack:
  added: []
  patterns:
    - "Release-only evidence retention reads tree-equal citation objects from the checked git object database; plain merged-PR citations remain independent of stale remote refs."
    - "Optimized package checks and debug-identity linkage checks use separate builds so package flags stay unchanged while the finished core member remains inspectable."
key-files:
  created: []
  modified:
    - .github/ci-timeouts.json
    - .github/scripts/verify-workflow-policy.py
    - .github/workflows/ci.yml
    - .github/workflows/libbet-repro.yml
    - .github/workflows/release-rehearsal.yml
    - tests/cmake/ci-lanes.cmake
    - tests/player/CMakeLists.txt
    - tests/scripts/verify-phase3-player.sh
key-decisions:
  - "Use git-object tree and ancestry checks for tree-equal ledger rows; only --release-head enforces cited-object retention."
  - "Keep the package build optimized and validate linkage in a separate Debug build because Release output lacks the debug identity records used by the linkage checker."
  - "REL-01 remains pending: this plan closes release-entry blockers but does not publish the exact v0.3.0 tag."
patterns-established:
  - "Policy mutations must refuse for their own policy code, with measured POSIX and Windows floors."
requirements-completed: []
coverage:
  - id: D1
    description: "The six former release_bound ledger rows are normal citations: four rehearsal jobs cite run 40257161612 by tree equality, candidate-fuzz and attach-v02-evidence cite run 40332345735, candidate-performance names its exact job, and report-red uses the successful main dry-run citation."
    requirement: REL-01
    human_judgment: false
    verification:
      - kind: integration
        ref: "python3 -I .github/scripts/verify-workflow-policy.py --check --verify-cited --root .: verify-cited rows=45 failures=0"
        status: pass
      - kind: integration
        ref: "cmake --preset phase1; ctest -R ^workflow_policy_(check|controls)$ (workflow_policy_controls=40.40 seconds on Task 2)"
        status: pass
  - id: D2
    description: "Release-head checks retain each tree-equal cited commit and matching tree in a heads-plus-tags object set, refuse a missing rehearsal object, keep plain cited rows unread, validate changed job-body disclosure, and enforce the ceil(2 x p50) boundary."
    requirement: REL-01
    human_judgment: false
    verification:
      - kind: integration
        ref: "python3 -I .github/scripts/verify-workflow-policy.py --check --release-head --root ."
        status: pass
      - kind: integration
        ref: "Task 3 scratch Git controls: VERSION 0.3.0 full heads-plus-tags checkout passes; main-only checkout rejects timeout-ledger-cited-object-missing; policy self-test negative_controls=415 positive_controls=4"
        status: pass
  - id: D3
    description: "The player linkage checker reports no wrong-core or duplicate-core targets, the player lane exercises linkage, and the budget base-copy and libbet-repro credential rules have refusing controls."
    requirement: REL-01
    human_judgment: false
    verification:
      - kind: integration
        ref: "Debug player build: ctest -R ^(player_|core_linkage_) excluding the two SDL menu tests passed 108/108; verify-core-linkage.py --check reported targets=66 mutant_targets=16 identity_normal=46 identity_mutant=16 no_core_linked=4"
        status: pass
      - kind: integration
        ref: "Phase1 six policy, budget and linkage CTests passed; policy controls negative_controls=418 positive_controls=4; test budget self-test controls=54; inventory self-test passed"
        status: pass
      - kind: other
        ref: "Release player tests excluding display-dependent shortcuts passed 106/106; verify-dmg-baseline.sh --inventory player passed with 55 expected names"
        status: pass
  - id: D4
    description: "The release-head and player tooling has automated positive and negative controls, including D-08 budget and read-only checkout mutants; the six original RM-031 linkage violations are eliminated."
    requirement: REL-01
    human_judgment: false
    verification:
      - kind: integration
        ref: "workflow_policy_controls Task 1=47.82 seconds, Task 2=40.40 seconds, Task 3=47.67 seconds, Task 4=49.60 seconds; existing 180 second timeout retained"
        status: pass
      - kind: other
        ref: "python3 -I tests/scripts/verify-test-budget.py --self-test: controls=54; bash .github/scripts/verify-test-inventory.sh --self-test"
        status: pass
duration: 35min
completed: 2026-10-29
status: complete
---

# Phase 19 Plan 01: Qualified Release Entry Blockers Summary

**Tree-verifiable timeout citations, retained release evidence, clean player-core linkage, and pinned CI trust checks for the v0.3.0 release sequence.**

## Performance

- **Duration:** 35 minutes
- **Started:** 2026-10-29T17:55:46Z
- **Completed:** 2026-10-29T18:31:02Z
- **Tasks:** 4 of 4
- **Files modified:** 8 source/configuration files
- **Measured task commits:** 4; `plan_head_before` and `plan_head_after` record the ledger interval.

## Accomplishments

- Replaced all six `release_bound` timeout-ledger rows with normal, verifiable citations. Four rehearsal rows use tree-equal evidence from run `40257161612` and the v0.2.1 tree; the two release workflow rows cite run `40332345735`. Candidate performance names `exact-tag-paired-performance-qualification`.
- Dispatched the authorized `nightly-asan.yml` report-red dry run. Run `40927061574` completed green at `f80bdf54c6c7d81e8e21f0275b43cda6edf6c8c4`, an ancestor of main; its 3-second sample gives `ceil(3 / 60 * 100) / 100 = 0.05` minutes and the ledger row is non-provisional.
- Added offline git-object verification, online cited-run tree/job checks, disclosure comparison, release-head retention and the full-history judge setup. The online check reported `verify-cited rows=45 failures=0`.
- Removed the six pre-change player-linkage violations and pinned the CI budget checker to the base revision; disabled persisted checkout credentials in libbet-repro.

## Citation Timing Evidence

P50 minutes use `ceil(seconds / 60 * 100) / 100` from the cited job duration. Every row remains within its existing timeout:

| Ledger row | Run / job evidence | Seconds | P50 calculation | Timeout |
| --- | --- | ---: | ---: | ---: |
| release-rehearsal.yml:performance | 40257161612 / rehearsal-paired-performance-qualification | 8 | 0.14 | 45 min |
| release-rehearsal.yml:judge | 40257161612 | 9 | 0.15 | 15 min |
| release-rehearsal.yml:corpus | 40257161612 | 731 | 12.19 | 60 min |
| release-rehearsal.yml:aggregate | 40257161612 | 1420 | 23.67 | 75 min |
| release.yml:candidate-fuzz | 40332345735 | 13 | 0.22 | 112 min |
| release.yml:attach-v02-evidence | 40332345735 | 24 | 0.40 | 15 min |
| release.yml:candidate-performance | 40332345735 / exact-tag-paired-performance-qualification | 9 | 0.15 | 45 min |
| nightly-asan.yml:report-red | 40927061574 / report_red_dry_run | 3 | 0.05 | 5 min |

The release-head scratch check passed against a fresh heads-plus-tags object set and rejected the main-only object set with `timeout-ledger-cited-object-missing`. A pruned tree-equal citation also refused; plain rows were verified not to trigger object reads. The disclosure scratch controls rejected an undisclosed changed job body and accepted the disclosed and unchanged cases. The boundary control rejects `ceil(2 x p50) - 1` and accepts `ceil(2 x p50)`.

## Player Linkage and CI Evidence

Before the linkage edits, `verify-core-linkage.py --check` reported four wrong-core targets (`dmg-path`, `ppu-follows-cpu`, `rb-swap`, `session ignores_flag`) and two duplicate-core targets (`test_player_colour`, `test_player_colour_mutant_rb_swap`). After the edits, the Debug player linkage build reported `targets=66 mutant_targets=16 identity_normal=46 identity_mutant=16 no_core_linked=4` with zero violations.

The optimized Release build lacks the debug identity records the checker uses. The package remains Release; the script builds a separate Debug linkage tree and runs `^(player_|core_linkage_)` there. Release CTest remains filtered to `^player_` so linkage rows do not contaminate the DMG JUnit inventory. On this host, the runnable Debug subset passed 108/108 and the Release player suite excluding two display-dependent menu shortcut tests passed 106/106; the 55-entry DMG inventory passed.

The Phase 1 build and six requested policy, budget and linkage CTests passed. Policy controls finished at 418 negative and 4 positive controls (POSIX floor 418; Windows floor 396); budget self-test reported 54 controls; the inventory self-test passed. `workflow_policy_controls` times were Task 1 47.82 s, Task 2 40.40 s, Task 3 47.67 s and Task 4 49.60 s, all below the existing 180-second timeout.

## Task Commits

1. **Task 1: Tree-equal citation tracer** — `124dff99` (`fix`)
2. **Task 2: Convert and recite timeout ledger rows** — `34c16530` (`fix`)
3. **Task 3: Release-head retention and full-history judge** — `865607cd` (`fix`)
4. **Task 4: Player linkage and CI trust pins** — `6b35be14` (`fix`)

## Files Modified

- `.github/ci-timeouts.json` — converted the release blockers to normal tree-equal or plain citations.
- `.github/scripts/verify-workflow-policy.py` — added schema, object, online citation, disclosure, retention, and CI mutant checks.
- `.github/workflows/release-rehearsal.yml` — configured the trusted judge with full history and its explicit git root.
- `.github/workflows/ci.yml` — executes the budget verifier from the pinned base copy and keeps its self-test separate.
- `.github/workflows/libbet-repro.yml` — disables persisted checkout credentials.
- `tests/player/CMakeLists.txt` — corrected mutant and colour target core linkage.
- `tests/scripts/verify-phase3-player.sh` — separates optimized package tests from Debug linkage validation.
- `tests/cmake/ci-lanes.cmake` — sets the measured control floors.

## Decisions Made

- Release-head object retention applies to tree-equal citations only; plain rows can cite merged PR heads no longer present in the checkout.
- Keep package settings unchanged and use a distinct Debug player build for linkage identity checks.
- WR-C04 and IN-08 are executed here as the planner's ownership deviation, because this plan owns the shared policy checker and CI floor.

## Deviations from Plan

### Implementation adjustment

The plan's direct linkage check on the optimized player build could not identify its finished core member because Release output omits the debug identity records. The script now runs the linkage suite in a separate Debug build while retaining Release settings for package tests and DMG inventory. This avoided changing package flags or introducing stripping/package machinery.

### Verification environment limitation

The two `player_slot_menu_shortcuts` CTests could not initialize SDL on this headless host (`The video driver did not add any displays`). Attempts with SDL `dummy` and `offscreen` drivers returned the same error. They are not represented as passing or as a visual/hardware validation; all other player tests and the DMG inventory passed. The planned verification ledger append could not write because the existing `WINDOWS.md` entry 20 has legacy status `resolved`, which the installed runtime rejects as an invalid status. The append was best-effort and no historical ledger entry was modified.

**Total deviations:** 1 implementation adjustment; 1 unrun display-dependent test pair and a best-effort ledger append failure recorded as a verification limitation.
**Impact on plan:** Release and linkage checks are automated and green. No player visual/perceptual claim is made for the two unavailable menu tests.

## Issues Encountered

- The release build lacked the symbol/debug records required by `verify-core-linkage.py`; a separate Debug linkage build resolved this without changing package behavior.
- The headless host could not initialize SDL for the menu shortcut tests, even with `dummy` and `offscreen` drivers.
- `gsd-tools windows append` refused the unrun-verification entry because existing `.planning/WINDOWS.md` row 20 uses the unsupported legacy status `resolved`; this did not affect implementation or test results.

## Known Stubs

None found in the files created or modified by this plan.

## Requirements and Release Readiness

`REL-01` remains pending. This plan has closed its ledger, player-linkage, budget-checker and checkout-credential entry work, but the exact v0.3.0 tag has not been published. Later Phase 19 plans own the preflight, PR sequence, tag, publication and readback evidence.

## Suggested Replacement for `docs/release.md` (19-06)

Replace the RM-027 paragraph near lines 255–258 with:

> The six former `release_bound` timeout rows have been replaced by verified normal citations. Four rehearsal rows use tree-equal citations whose commits and trees are checked from the release checkout; the two release workflow rows cite merged PR evidence and are not object-read. Before publishing v0.3.0, run the release-head policy check from a fresh heads-and-tags checkout and require zero provisional rows.

## Next Plan Readiness

Plan 19-01 is complete. The next serial Wave 1 plan is **19-02 — Review leftovers and state conversion**. REL-01 remains open until publication and exact-tag readback. Continue only when the owner chooses, using `/gsd-execute-phase 19`; both automatic advance flags remain false.

## Self-Check: PASSED

- SUMMARY file exists at the required path and its coverage classifier accepts all four deliverables for automated pass.
- All four task commits (`124dff99`, `34c16530`, `865607cd`, `6b35be14`) are ancestors of the recorded plan head.
- `commits: 4` matches the persisted plan ledger interval from `33b6c569edfad3d4960129b2b8a53591eb4aebfb` through `6b35be140b9c5823f0a1866601e8133cb012525b`.

---
*Phase: GB-19-qualified-v0-3-0-release*
*Completed: 2026-10-29*
