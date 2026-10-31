# Phase 19 bounded schema-validation repair proposal

Status: approved under D-134. The owner answered “yes approve” to this concrete tested proposal. The bounded implementation and qualification below are authorized; no new live release action or general review/gap reset is granted.

## Concrete problem and consequence

The final standard-depth review found two validator defects. Otherwise valid pre-publish inventories with JSON `true` or `1.0` as schema version1 are accepted, and a policy registry with `true` is accepted. These values violate the integer schema contract. A non-object registry root such as `[]` raises an uncaught AttributeError rather than the normal controlled rejection. That second path still fails closed.

The actual retained release inventory uses integer1. The successful published v0.3.0 release, immutable tag/product S, actual workflow G and22-asset readback remain reconciled. No malformed actual release evidence, corrupted package or need for another release action was found. The unresolved validator correctness prevents final Phase19 PR B closure.

The review's initially cited embedded performance-receipt site already requires the exact integer type and is excluded from the correction. The corrected review and reproductions are retained in the execution checkout's19-REVIEW.md and build/prb-review-reproduction.json.

## Proposed bounded change

Permit one consolidated exact-type and controlled-error correction in these existing validators:

- `.github/scripts/verify-published-release-assets.py`
- `tests/scripts/verify-v03-dispositions.py`
- `tests/scripts/verify-workflow-policy-coverage.py`
- `tests/scripts/verify-release-lifecycle.py`
- `tests/scripts/verify-support-ledger.py`

Require the exact JSON integer type before accepting a supported schema version at the affected unchecked boundaries. Preserve already strict sites. Reject non-object workflow-policy registry roots through the existing controlled rejection path. Extend their existing self-tests with boolean/float/malformed-root refusal controls and valid-integer positive twins. Preserve all existing assertions, independent coverage, immutable source binding and timeouts. `tests/CMakeLists.txt` and `tests/cmake/ci-lanes.cmake` may change only to raise an existing measured control minimum or exact-count success marker when the added controls require it. The existing policy-coverage registration lives in ci-lanes.cmake and its62-control marker must reflect the measured72-control set; no timeout, label or command is relaxed. No new checker or test target is proposed.

Apply only the reviewed patch to the same `gsd/phase-19-post-release` closure branch after approval. Planning summaries, validation/security/review dispositions and lessons may record the actual correction and evidence. Do not rewrite the frozen19-06 summary or past failed runs.

## Prototype and evidence

The isolated shared clone is `build/phase19-window/posttag-recovery/schema-rescope-prototype`, based on535cdf79. It does not replace the active implementation. Its immutable head is `900eabfdd19290d98bf41854407f56990f4d7ef2`. The exact seven-path patch is `build/phase19-window/posttag-recovery/schema-rescope-prep/schema-version-rescope.patch`, SHA-256 `33c3646e59618a4f68f99fed16674f5240744d4493a534f79fb53ae7d5b4325b`. Detailed source/command results are in `schema-rescope-report.md` beside that patch. All seven affected existing CTests pass with no skips; the initial stale62-control marker failure is retained separately and the corrected measured marker is72. The same immutable prototype requires the raised existing control floors51/120/99. Existing target timeouts and baseline controls remain unchanged. The recovery self-test additionally verifies the published-asset helper matches the immutable revision before invoking its own schema tests, so that validator boundary is exercised through an existing CTest. No new target is added. Parent re-verification accepted the actual correct integer-schema inventory and valid registry, rejected boolean/float/string/null/array schema values and non-object roots through normal errors, verified the pinned patch digest and passed `git apply --check` against the actual closure checkout. The prototype worktree is clean and diff hygiene passes. Actual live release bytes and the task branch runtime remain untouched by prototype preparation. Independent code/security rechecks, full local qualification and exact-head hosted CI are still required after approval; the prototype is not final phase qualification.

## Required qualification after approval

1. Apply the bounded patch and commit with explicit paths. Reconfigure revision-bound checks and run every affected existing self-test/CTest, proving baseline malformed inputs accepted versus fixed inputs rejected and valid integer schemas accepted. No skipped, crashed, stale or timeout result counts as a pass.
2. Obtain fresh independent code and security rechecks of the exact correction and its interfaces. Reclose the reopened T-19-22 and validation gap only from actual evidence. Keep prior review rounds and failures; this is one bounded correction/recheck allowance, not a general reset. Any new unrelated correctness/security gap holds for another scope decision.
3. Complete the final local full suite and player/installed-consumer qualification at the settled source. Complete the one final phase-goal verification with stable summaries and CLI fingerprinting. No summary edit after fingerprinting.
4. Open the existing planned PR B, qualify every currently required check instance at its exact head, account for concrete covered skips and use the production guarded merge check immediately before the same single guarded PR B squash. No protection bypass or extra corrective release merge.
5. Verify immutable actual main-boundary facts against the pending base negative, preserve outer-workspace owner files and local evidence, record boundary SHA only in local continuation, then stop at `/gsd-verify-work 19`. Do not run verification, a milestone audit or another phase automatically.

## Limits retained

No new tag/release, body or association edit, workflow dispatch/rerun, attachment or publication is proposed. The sole release retry is already consumed successfully. No workflow/policy authority, package contents, emulator/API/state behavior, dependencies, permissions, limits or timeout changes. The publisher flow stays unchanged; its existing inventory validator becomes stricter. The historical G/S allowlist and product provenance remain proved against their immutable commits rather than current B. The phase stays within eight plans and its single used gap slot; no new gap is granted. Retain authority and cited rehearsal branches.

## Why an owner decision is required

AGENTS.md requires: “At most 2 review-fix rounds and 1 gap round per phase. An unresolved correctness or security finding forces a rescope, never a seed.” The existing allowance is exhausted, and the newly reproduced malformed-evidence acceptance is correctness despite its review warning label. Routine execution authority therefore does not authorize silently adding this repair to PR B or deferring the finding.

Recommended decision: approve this bounded schema repair and its fresh rechecks, then continue the remaining Phase19 closure gates. The alternative is to keep phase closure stopped with the already published release unchanged. No risk acceptance or further live release action is requested.

Evidence hashes:

- `schema-rescope-report.md`: `c841bac8287edb01ac6f2b52ee1a777118c7a2648cdefa76937f2ffe77a951ca`.
- `final-focused-ctest.log`: `fa31ea6c33c0c942fb04a695f96b97f13c318343aabdcb6940a944283cd27035`.
- `initial-ctest-marker-mismatch.md`: `c52b32ba1da60dac9f1261ce6fdb5adceb43c69dcf85fa2dedb1fcd0d4a902ef`.
