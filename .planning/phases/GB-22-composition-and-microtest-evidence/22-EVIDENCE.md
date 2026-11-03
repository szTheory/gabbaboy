# Phase 22 Final Evidence

**Scope:** Owner-approved D-141 synthetic-plus-metadata closeout. DIAG-01, DIAG-02, and RIGHTS-01 retain their original definitions and remain Pending. All seven real-fixture gates remain unresolved; no license prohibition is inferred.

## Immutable Source and Metadata

The source-bound metadata assessment preserves historical source revision `559b5f7296f957a1a1fea278056a908f9a3d9339`. Local immutable checks at reviewed source `06d2cbc1e0ceaa100cc0ecc28826e39794a73f04` report 513 named metadata cases: 480 shared-macro, two inline, and 31 initial no-protocol exclusions. All seven required gates remain unresolved, admitted = 0, and executed = 0. Approval exits 2 with `scope-resolution-required` and the exact seven-gate list.

The generated snapshot is `build/phase22/evidence.json`, SHA-256 `2f059fe21aac5131c96d4547a9937428d64911502e4ba5b85ba124e9e126223b`. It records the checker digest and immutable case/requirement/source-boundary results. DIAG-01/02 and RIGHTS-01 remain Pending; the underlying definitions and package boundary records are unchanged.

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

The full local CTest suite passed 1,732/1,732 on `042e7f34`; its authoritative final tracked-head result and the exact-head PR evidence are recorded in `build/phase22/remote-evidence.json`. A local pass does not substitute for the required remote evidence.

## Review and Security

The independent scoped code review and security review are clean at source `06d2cbc1e0ceaa100cc0ecc28826e39794a73f04`. The fixed inventory-only exception pins the exact checker, command shape, source revision, active build directory, and configured Python interpreter; its negative controls reject build executables, extra output flags, `python -c` pass-output substitution, and an absolute Python stub. T-22-32 remains open until exact-head remote checks, artifacts, reviews, and merge-tree equivalence pass.

## Build and Feedback Cost

The focused run configured in 13.2 seconds, built 339 targets, and passed 23 CTests in 42.98 seconds at four-way parallelism. The final local full suite passed 1,732/1,732 in 495.43 seconds. The separate planning/evidence selection passed 4/4 in 13.10 seconds; `phase22_evidence_controls` accounted for 13.09 seconds. No measured evidence supports increasing timeouts, adding a build cache, or changing CI scheduling. The final configured full-suite rerun and hosted durations will be recorded in the remote evidence file; preserve existing budgets and required coverage.

## Exact-Head Qualification

The immutable boundary candidate is commit `4ac46e7406329efbd4fb6ac0dc39c86c14156691`. The boundary check against that point-in-time commit passed, preserving Pending requirements, all seven no-go gates, both false automatic-advance flags, Phase 23 unstarted, and `/gsd-discuss-phase 23`. It is a candidate boundary until final exact-head qualification succeeds.

`build/phase22/remote-evidence.json` records sanitized repository, PR, head, required run/job/check, package artifact, review, merge-tree, and duration identities. `.github/scripts/verify-pr-evidence.sh` is authoritative for exact-head equality, required checks, package sidecars/archives, and same-head CI, fixture, and preview jobs. Any missing, stale, skipped, inaccessible, failed, or mismatched evidence leaves Phase 22 unclosed.

**Phase 23 handoff:** Phase 23 — Qualified v0.4.0 Release — remains unstarted and owner-controlled through `/gsd-discuss-phase 23`. Both automatic-advance flags remain false.
