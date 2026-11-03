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
| `cmake --preset phase1` | `06d2cbc1` | Configure passed in 13.2 seconds; the exact final configure/build/full-suite run is still required after the evidence commit. |
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

The historical full local CTest suite passed 1,732/1,732 on `042e7f34`, before the C1 correction. It does not qualify the changed source. The final configured full-suite run, fresh Windows/remote jobs and artifacts, exact-head review/protection checks, and merge-tree comparison remain required; `build/phase22/remote-evidence.json` retains the earlier failed remote attempt and must record any new attempt without rewriting that history.

## Review and Security

The fresh independent C1 code and ASVS 1 reviews are clean at `93004a65143a4bc3199e1f028b003e2d3dd11ef6`, with zero findings and zero blocking threats; see `22-REVIEW.md` and `22-SECURITY.md`. The earlier ASVS result at `f59ebd16` omitted C1 and remains historical. The prior inventory-only exception still pins the exact checker, command shape, source revision, active build directory, and configured Python interpreter; its negative controls remain intact. T-22-32 remains open until the final full local suite, exact-head remote checks/artifacts, review dispositions, protection checks, and merge-tree equivalence pass.

## Build and Feedback Cost

The D-143 configure took 14.0 seconds; the 339-target build passed. The ten-test selection passed in 57.27 seconds, the alternate four-test selection in 16.25 seconds, and the broader 19-test selection in 56.00 seconds. `phase22_evidence_controls` passed in 14.00–14.16 seconds under the unchanged 60-second limit. The historical 1,732-test suite at `042e7f34` predates C1 and is not final evidence. No measured evidence supports raising limits, adding a cache, or changing CI scheduling; record the final full-suite and hosted durations while preserving current budgets.

## Exact-Head Qualification

The prior immutable boundary candidate is commit `4ac46e7406329efbd4fb6ac0dc39c86c14156691`; it predates D-143 and is not the final boundary for the corrected source. Task 3 must prepare and retain a new point-in-time candidate after all tracked evidence is ready, preserving Pending requirements, all seven no-go gates, both false automatic-advance flags, Phase 23 unstarted, and `/gsd-discuss-phase 23`. Final exact-head qualification remains outstanding.

`build/phase22/remote-evidence.json` records sanitized repository, PR, head, required run/job/check, package artifact, review, merge-tree, and duration identities. `.github/scripts/verify-pr-evidence.sh` is authoritative for exact-head equality, required checks, package sidecars/archives, and same-head CI, fixture, and preview jobs. Any missing, stale, skipped, inaccessible, failed, or mismatched evidence leaves Phase 22 unclosed.

**Phase 23 handoff:** Phase 23 — Qualified v0.4.0 Release — remains unstarted and owner-controlled through `/gsd-discuss-phase 23`. Both automatic-advance flags remain false.
