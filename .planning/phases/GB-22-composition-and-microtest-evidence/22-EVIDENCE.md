# Phase 22 Final Evidence

**Scope:** Owner-approved D-141 synthetic-plus-metadata closeout plus the single D-143 C1 OSC correction/review cycle in existing Plan 22-12. DIAG-01, DIAG-02, and RIGHTS-01 retain their original definitions and remain Pending. All seven real-fixture gates remain unresolved; no license prohibition is inferred.

## Immutable Source and Metadata

The source-bound metadata assessment preserves historical source revision `559b5f7296f957a1a1fea278056a908f9a3d9339`. Local immutable checks at reviewed source `06d2cbc1e0ceaa100cc0ecc28826e39794a73f04` report 513 named metadata cases: 480 shared-macro, two inline, and 31 initial no-protocol exclusions. All seven required gates remain unresolved, admitted = 0, and executed = 0. Approval exits 2 with `scope-resolution-required` and the exact seven-gate list.

The historical generated snapshot at `06d2cbc1` had SHA-256 `2f059fe21aac5131c96d4547a9937428d64911502e4ba5b85ba124e9e126223b`. At the D-143 C1 source `93004a65143a4bc3199e1f028b003e2d3dd11ef6`, the checker regenerated `build/phase22/evidence.json` with SHA-256 `19e846ed8dea0f94061e446ac956cd0843483ac427326c4f309103dffc14a3fe`; both snapshots preserve the same 513-case metadata-only no-go, seven unresolved gates, admitted=0, and executed=0.

## D-143 C1 Sanitizer Evidence

The last reviewed source `f59ebd166a354537343dd9e87b870698cc686b2b` left the printable body of a valid UTF-8 C1 OSC sequence after generic control cleanup removed U+009D and U+009C. The amended existing `diagnostic_sanitization_control` adds distinct prefix/suffix sentinels, supplied native/Windows/home roots, the byte sequence `U+009D 0;synthetic-c1-title U+009C`, and long trailing padding. The regression requires full payload/delimiter/control/root removal, both sentinels retained, and output at most 700 characters while preserving existing ESC CSI/OSC assertions.

Before the correction, the direct control refused with `diagnostic-sanitization-control-failed`; `build/phase22/c1-fail-first.json` retains that result. At corrected source `93004a65143a4bc3199e1f028b003e2d3dd11ef6`, the direct control passes. An isolated in-memory mutation that disables only `C1_OSC_ESCAPE` returns the same specific refusal, then restoring the matcher passes; `build/phase22/c1-direct-and-mutation.json` retains those outcomes. The same augmented control runs inside the existing `phase22_evidence_controls` test identity; no new CTest or command was added.

## Phase 21 Squash-Reference Reconciliation

The fallback `ucity-1.3.json` points to the primary no-go record `tests/data/cgb-candidates/potion-panic.json`. Its historical reference used Phase 21 branch commit `1ab7180e9f35c70246e62c252d3dd4851fa77473`, which ceased to be an ancestor after PR #140 was squash-merged. The record is now pinned to the squash merge commit `bef2cfbdbdd0fc9b2d78631586827e29e0241b3b`; only the commit pointer changed. The referenced record's Git blob is `f3583f2933e48479b275e68beb275cfd1f356c01` at the squash commit and in the current source, and its SHA-256 is `9a23c0c13dba57f7806b19501756f09616c6cbbebe1e4bcef04eb099bf8ca352`. The verifier reads only that immutable path and digest, while separately binding the selected project source. Candidate controls reject a non-ancestor reference even when the blob is present and reject a mismatched record digest.

## Local Checks

| Check | Source | Result |
|---|---|---|
| `cmake --preset phase1` | `06d2cbc1` | Focused configure passed in 13.2 seconds at an earlier source; the exact-head configure/build/full-suite result below supersedes it for final qualification. |
| `cmake --build --preset phase1` | `24c4e191` | All 339 build targets passed during the focused check cycle; later changes only tightened the Python planning-label checker and its control floor. |
| `ctest --test-dir build --parallel 4 --output-on-failure --no-tests=error -R '^(planning_labels|planning_labels_controls|phase22_evidence_contract|phase22_evidence_controls)$'` | `06d2cbc1` | Passed 4/4; the explicit configured build inventory, 17 label-policy controls, immutable no-go contract, and evidence mutants passed. |
| Focused Phase 22/fixture/product/budget/Phase 21 selection | `24c4e191` | Passed 23/23 in 42.98 seconds; included exact Phase 21 game-reference and candidate controls, no-phase-path controls, cap, fixture admission, core/player product, and Phase 22 contracts. The final full suite below supersedes this focused result for completion. |
| `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --parallel 4 --output-on-failure --no-tests=error` | `042e7f34` | Passed 1,732/1,732 in 495.43 seconds; the final tracked-head run is captured in `build/phase22/remote-evidence.json`. |
| `verify-diagnostic-evidence.py --check --repo-root . --source-revision 06d2cbc1... --build-dir build --write-evidence build/phase22/evidence.json` | `06d2cbc1` | Passed: 513 cases, seven unresolved gates, admitted=0, executed=0. |
| `verify-diagnostic-admission.py --self-test-controls` | `06d2cbc1` | Passed all 12 mutation controls, including mutable Phase 20 checker and policy substitutions. |
| `verify-diagnostic-admission.py --require-approved` | `06d2cbc1` | Correctly refused with exit 2 and all seven unresolved gates. |
| `verify-planning-labels.py --build-dir build` | `06d2cbc1` | Passed with 1,732 configured CTests and 47 planning-labelled tests. |
| `verify-no-phase-paths.py --self-test` and `--check --report` | `06d2cbc1` | Passed 19 controls; scanned 594 tracked files with the pinned allowlist. |
| `verify-planning-hygiene.py --check plan-cap` | `06d2cbc1` | Passed: four phases and 28 plan files under the combined cap of 40. Phase 21 uses 8 of 10 slots, keeping two reserve slots; Phase caps are 9/10/12/9. |
| `verify-summary-coverage.py` for 22-01, 22-02, 22-10, and 22-11 | Current live summaries | Passed; Plan 22-02 D2 is automated with `human_judgment: false`. |
| Direct C1 fail-first control | Pre-correction working tree before commit `93004a65` | Failed with the required `diagnostic-sanitization-control-failed` refusal. |
| Direct C1 control and disabled-matcher mutation | `93004a65143a4bc3199e1f028b003e2d3dd11ef6` | Corrected control passed; in-memory disabling of only the C1 matcher produced the required refusal; restored control passed. |
| `phase22_evidence_controls` | `93004a65143a4bc3199e1f028b003e2d3dd11ef6` | Passed 1/1 in 14.00 seconds after configure; retained mutations and the C1 fail-first/mutation control run under the unchanged 60-second limit. |
| Retained ten-test Phase 21/22 selection | `93004a65143a4bc3199e1f028b003e2d3dd11ef6` | Configure and all 339 build targets passed; all 10 selected tests passed in 57.27 seconds. |
| Alternate `cmake-3.25.3` inventory selection | `93004a65143a4bc3199e1f028b003e2d3dd11ef6` | Configure passed in 14.0 seconds; all 4 selected tests passed in 16.25 seconds from the alternate build directory. |
| Task 2 Phase 22/21/budget selection | `93004a65143a4bc3199e1f028b003e2d3dd11ef6` | All 19 selected tests passed in 56.00 seconds, including all `phase22_*`, planning-label, CGB-progress, fixture-admission, game-evidence, and budget tests. |
| `verify-diagnostic-evidence.py --check --repo-root . --source-revision HEAD --build-dir build --write-evidence build/phase22/evidence.json` | `93004a65143a4bc3199e1f028b003e2d3dd11ef6` | Passed with assessment=blocked, cases=513, unresolved_gates=7, admitted=0, executed=0. |

The 1,732/1,732 suite on `042e7f34` is a historical pass before the C1 correction. The final configured suite at PR #142's exact head `9cb92b0f344b884d5f3e7179740ff5bc87eae379` passed 1,732/1,732 in 1,424.19 seconds after configure and build; the exact result is preserved in `build/phase22/remote-evidence.json`.

## Review and Security

The fresh independent C1 code and ASVS 1 reviews are clean at `93004a65143a4bc3199e1f028b003e2d3dd11ef6`, with zero findings and zero blocking threats; see `22-REVIEW.md` and `22-SECURITY.md`. The earlier ASVS result at `f59ebd16` omitted C1 and remains historical. The prior inventory-only exception still pins the exact checker, command shape, source revision, active build directory, and configured Python interpreter; its negative controls remain intact. T-22-32 closed when PR #142's exact-head local/remote evidence, artifacts, reviews, protection checks, and merge-tree comparison all passed; the merged tree is `ca2f0be6b38e7dd22e0eb3296b9a21cceed1a765`.

## Build and Feedback Cost

The D-143 configure took 14.0 seconds; the 339-target build passed. The ten-test selection passed in 57.27 seconds, the alternate four-test selection in 16.25 seconds, and the broader 19-test selection in 56.00 seconds. `phase22_evidence_controls` passed in 14.00–14.16 seconds under the unchanged 60-second limit. The authoritative final suite at PR #142's exact head passed 1,732/1,732; its identity and runtime are retained above and in the ignored remote evidence record. Those local D-143 measurements did not support a scheduling change at that time. The later post-merge Windows timeout and its bounded serial scheduling remedy are recorded in the cleanup addendum below.

## Exact-Head Qualification

The prior immutable boundary candidate is commit `4ac46e7406329efbd4fb6ac0dc39c86c14156691`; it predates D-143 and is historical only. The final Phase 22 boundary is PR #142 head `9cb92b0f344b884d5f3e7179740ff5bc87eae379`, merged as `ca2f0be6b38e7dd22e0eb3296b9a21cceed1a765` with matching tree `e768b7ec26d7c07542d6aa29aef53ae8fc826c5e`. It preserves all seven no-go gates, zero real admissions/executions, Pending requirements, both false automatic-advance flags, and the owner-controlled Phase 23 route.

`build/phase22/remote-evidence.json` records sanitized repository, PR, head, required run/job/check, package artifact, review, merge-tree, and duration identities. `.github/scripts/verify-pr-evidence.sh` is authoritative for exact-head equality, required checks, package sidecars/archives, and same-head CI, fixture, and preview jobs. Any missing, stale, skipped, inaccessible, failed, or mismatched evidence leaves Phase 22 unclosed.

**Phase 23 handoff:** Phase 23 — Qualified v0.4.0 Release — remains unstarted and owner-controlled through `/gsd-discuss-phase 23`. Both automatic-advance flags remain false.

## Post-Merge CI Recovery

After PR #142 merged as `ca2f0be6b38e7dd22e0eb3296b9a21cceed1a765`, main push run [41694766412](https://github.com/szTheory/gabbaboy/actions/runs/41694766412) failed only in the Windows native suite: `phase22_evidence_controls` reached its unchanged 60-second timeout at 60.01 seconds while CTest ran in parallel. PR #143 (`1346176fadb9926624bf318d128e61289504f0f2`) adds `RUN_SERIAL TRUE` and `COST 60` to that CTest declaration; its command, assertions, inventory, and `TIMEOUT 60` are unchanged.

On exact PR head `1346176f`, the first macOS suite attempt hit the unrelated existing `phase21_fixture_admission_controls` limit at 60.06 seconds. The identical-head push run passed it in 58.67 seconds, and the refreshed local control passed in 27.72 seconds. The single targeted retry passed all 1,732 tests; that Phase 21 control completed in 58.59 seconds. The exact-head CMake floor job also passed in 36 minutes 34 seconds, within its existing 40-minute limit. Windows passed the full 1,594-test inventory, including `phase22_evidence_controls` in 50.45 seconds. The retry and job identities are retained in `build/phase22/repository-cleanup-evidence.json`.

The first preview-package attempt failed at its exact-head CI wait because CI attempt 1 failed; its package and consumer steps were skipped. After CI attempt 2 passed, the Linux/macOS installed-package checks passed, but the player check could not find the exact-attempt artifact: only the native Mac job had been rerun, so the successful macOS player artifact still belonged to CI attempt 1. The macOS player-artifact producer was rerun as CI attempt 3, and the full preview workflow then passed on preview attempt 3: Linux and macOS installed-package builds/consumers passed, and the player package was downloaded and verified against the attempt-3 artifact. This preserves the existing source/run/attempt binding and required no workflow change. PR #143 merged as `4eee5b51`. Post-merge main push CI run [41715210158](https://github.com/szTheory/gabbaboy/actions/runs/41715210158) completed successfully at 21:13:38Z; native Linux/macOS/Windows, Linux sanitizer acceptance and tests, the minimum CMake 3.25.3 job, performance, and required-native aggregation all passed. Planning checks and the macOS player build were skipped by the change classifier. The same-head fixture-reproduction run [41715210637](https://github.com/szTheory/gabbaboy/actions/runs/41715210637) and release-please run [41715210175](https://github.com/szTheory/gabbaboy/actions/runs/41715210175) also passed. The final docs handoff and local-main reconciliation are recorded in the section below.

At the cleanup inventory check, PR #143 was the only open pull request and there were no open issues. The duplicate same-SHA push run completed green before the PR's exact required checks passed, so there was no safe cancellation window under the existing CI-efficiency policy. No workflow trigger or required coverage was changed.

## Final Repository Cleanup and Handoff

PR #144 (`dcca6afaccf93782a1a1935981cd007e4fc18849`) recorded the completed Phase 22 handoff and merged through branch protection as `d18db4c56d2a79e6138df37a9d16e3d346a86e13`. Its exact-head `required-native`, `fixture-repro`, and `preview-package-smoke` contexts passed. The post-merge planning CI run [41721377525](https://github.com/szTheory/gabbaboy/actions/runs/41721377525), fixture-reproduction run [41721377486](https://github.com/szTheory/gabbaboy/actions/runs/41721377486), and release-please run [41721377533](https://github.com/szTheory/gabbaboy/actions/runs/41721377533) passed. The planning classifier ran its planning check and skipped native/test lanes for the documentation-only merge. The duplicate full push CI run `41720420486` was canceled only after the exact-head required PR checks passed.

Local `main` was merged with `origin/main` at `d18db4c56d2a79e6138df37a9d16e3d346a86e13` without rewriting the original local v0.4 commits `ed2bd0c8`, `64bd50a6`, and `ddf157d4`. The local and remote trees matched at `79da9de4e44509da2caa90b46c379cf07c9c7b06`; the tracked worktree was clean, and the three pre-existing untracked research notes were preserved. No pull requests or issues remained open. Machine-readable cleanup details are retained in the ignored `build/phase22/repository-cleanup-evidence.json`.

Phase 22 is complete at the approved metadata-only scope. Phase 23 — Qualified v0.4.0 Release — remains unstarted and owner-controlled through `/gsd-discuss-phase 23`; automatic advance and auto-chain remain false.
