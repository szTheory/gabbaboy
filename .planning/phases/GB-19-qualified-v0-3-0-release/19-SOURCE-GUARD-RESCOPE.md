# Approved bounded repair: freeze the complete reviewed policy harness

Status: owner-approved under D-128. The owner answered “yes i approve” to the bounded source-guard repair proposal. Source is frozen at local `790f79c99fa985d04d6aeb1fff7d3a9e662f17ff`. PR #135 remains remotely at `70d3e42225c14e636876aad6697672ec08d861b3`, main at `9895896922f51f48a225636f4b587e3ab1be7058`, and the exact v0.3.0 tag lookup returns 404. No new push, CI, merge or release window has started. Prior approvals and failures remain historical.

## Verified blocker and consequence

D-127 implemented six groups retaining 412 mutation cases and 499 POSIX / 467 Windows control IDs. Direct grouped execution, the retained full self-test, and native immutable coverage/budget checks pass. Consolidated review found four defects; its bounded correction fixed archive configuration, existing sanitizer scaling and effective CTest command validation. Focused regressions and archive core build pass.

Independent code re-review and a security addendum still reproduced a source-integrity hole: normalization accepts side effects in marker and selector arguments, and omits all four added runner function bodies. Replacing `run_policy_self_test` with `return` was also accepted. That does not mean a missing completion marker passes CTest; it means the claimed source-preservation proof accepts removal of control execution. The actual policy runner itself remains unchanged from the reviewed partition. This is a latent verification gap, not an observed production guard alteration. Reports are retained under ignored `build/phase19-window/policy-partition/`, including `final-code-rereview.md`. The security auditor withdrew its earlier clean re-audit after independently confirming these cases.

## Recommended exact scope

Authorize one additional bounded correction and focused independent re-review cycle in the same unmerged PR #135. Preserve all prior rounds; do not use reserved post-tag plan19-08.

1. In existing `tests/scripts/verify-workflow-policy-coverage.py`, require the entire candidate `.github/scripts/verify-workflow-policy.py` blob to equal the reviewed instrumented snapshot from immutable commit `2c4a66ad50b979bbfcf3bff6cf9f4e644a56d9b7`, SHA-256 `f6092a477be22336ffe585c25508f3e7da761e7b9da3f3716e3f0dbdc302405c`. That file is byte-identical at790f79c. Resolve the reference from Git, verify the literal digest, and fail closed on missing/mismatched source. The complete runner, added functions, marker arguments and selector calls are frozen.
2. Retain baseline `70d3e42225c14e636876aad6697672ec08d861b3`, its digest, independent stable-ID reconstruction, original assertion/production comparison and all existing controls. The exact pin supplements these checks; no self-derived expected value, broader normalization or silent pin refresh. Simplify only normalization machinery made unnecessary by the exact pin, preserving every proof obligation.
3. Add persistent negatives for the accepted marker/selector side effects, altered runner body (including removed or fabricated execution), changed/duplicated marker/selector expressions, and missing/wrong reviewed source identity; retain an exact-reference positive. Keep registration overrides, platform/coverage, archive and native/sanitizer-scaling controls. Adjust only necessary existing CMake success-marker/control wiring; all budgets stay unchanged.
4. Independently review the corrected immutable helper and replay the accepted mutations. Require final-head source/coverage/registration checks and fresh exact-head protected CI with actual Windows/Mac/Linux, unchanged performance receipts and source-bound Mac metadata inspection. Earlier failures/local candidates are not qualification.
5. Only after complete current-head qualification may the single D-125 guarded merge proceed, followed by actual regenerated component-PR discovery/inactive judgment and fresh Plan19-07 Task1. Preserve all old bases, one main-merge allowance, tag/draft immutability and every window precondition.

Ownership: existing coverage helper, narrowly necessary existing CMake control wiring, and related scope/decision/plan/STATE records. No change to the reviewed policy runner, baseline manifest, original assertions, production checker, core/API/dependencies, permissions, timeout/job/performance limits, minimum-OS policy, tag/draft or additional main merge. Future intentional runner edits require explicit reviewed rebaselining.

## Owner decision and route

The phase's original review-fix allowance was already exhausted. D-127 permitted the bounded partition and consolidated correction; an unresolved correctness finding remains after that correction. AGENTS.md requires unresolved correctness/security to force rescope, so another correction/review cycle is not assumed. Keeping the hold requires no acknowledgment.

Completed stage: Phase19 execution through19-06 and qualifiedD123/D124 hardening. Active stage: Phase19 — Qualified v0.3.0 Release, PR135 qualification held. Approved exact continuation: `/gsd-execute-phase 19`. Final execution boundary: `/gsd-verify-work 19`, not automatic. Both automatic-advance flags stay false.
