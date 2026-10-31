# Proposed bounded repair: discover the real component release PR

Status: approved by the owner on 2026-10-30, recorded as D-125. The owner selected “Approve bounded guard repair (Recommended)” for this exact linked proposal. The release remains held before H/W/tagging until the bounded repair is qualified and its real post-regeneration path is verified.

## Verified defect

Qualified corrective PR #134 merged as `9895896922f51f48a225636f4b587e3ab1be7058`. Release-please run 41095868403 successfully regenerated #131 at direct-child head `3c0bb13027c3eaa7fa9d49993ad27c37a093e19b`, with its exact three expected files and title; this was independently checked from PR/commit APIs.

However, its post-regeneration `version-window-gate` printed “No open version PR.” Discovery in `.github/workflows/release-please.yml` searches `release-please--branches--main`; the real configured component branch is `release-please--branches--main--components--GabbaBoy`. The separate pre-tag workflow uses the correct branch. The existing policy checker validates the surrounding trust wiring but does not pin this discovery query.

An independent security audit ran the exact discovery/judge bodies locally with controlled GitHub responses exposing the actual component PR. The current query sets `present=false`, both steps exit zero and a rejecting checker is never invoked. Changing only the branch query in memory sets `present=true` and propagates the sentinel checker rejection. No source, refs or external state changed. The current record is inactive, so no damaged active freeze or unsafe publication is established; the same false-negative discovery would skip an active component window too.

This is a verified fail-open implementation gap in an existing declared backstop (T-19-30, already open/high), not a new accepted risk. Workflow comments, the policy contract and research Pitfall 6 require active freezes to be judged fatally after regeneration. Operator main pins and the separate mandatory pre-tag gate reduce the overall risk but do not make this backstop work.

## Approved bounded scope

Authorize one additional pre-tag hardening PR and one consolidated fix/review cycle solely for this discovery path. D-123/D-124 are completed; no previous round or failure is reset. This explicitly amends the earlier main-push allowance again; preserve the original PR A and PR #134 squashes as historical facts.

1. Correct the discovery query to the configured component branch. The exact one-line candidate is prepared in ignored `build/phase19-window/window-guard-rescope/candidate.patch`.
2. Pin discovery in the existing workflow-policy checker, with a mutant restoring the legacy query and any directly necessary malformed/omitted discovery controls. Preserve data-only subject handling; do not execute arbitrary subject workflow code from the trusted judge.
3. Add deterministic controlled discovery-to-judge tests for absent PR, inactive record, valid active record and stale active record. Require the stale case's checker failure to propagate; prove the original legacy-query mutant skips that checker and is refused by the regression contract. Use existing self-test infrastructure where practical, stdlib/local shims only, no live PR mutation for these cases.
4. Independently review the complete small repair and require fresh exact-head protected CI, actual Windows/macOS and the unchanged performance gate. Merge only with `--match-head-commit`; capture the real post-regeneration job discovering the actual open component PR after the merge, not merely workflow success.
5. Record this new corrective squash separately as the current WINDOW_BASE, verify fresh release-please regeneration, then restart Plan 19-07 Task 1. Retire only the obsolete cancelled pre-tag rehearsal attempt under the existing exact-head/no-tag guards. Fresh version content/receipt/H/R1/W/R2/nightly/pre-tag gate and publication/readback remain required.

Runtime ownership is limited to `.github/workflows/release-please.yml`, `.github/scripts/verify-workflow-policy.py`, its existing CTest floor wiring in `tests/cmake/ci-lanes.cmake`, and a small routing-control helper under `tests/scripts/` only if existing self-test infrastructure cannot express the controlled cases. A new helper must read an immutable revision and be wired into CTest with negative controls. Related scope/decision/current-plan/STATE/security/lesson records may be reconciled. No emulator/API changes, unrelated discovery redesign, packages, permissions, trusted-checkout changes, timeouts/performance weakening, fixture thinning, tag/draft moves or gap-cap waiver.

The source and tests from PR #134 remain qualified historical evidence; they cannot qualify the new workflow revision. No further unchanged-source retry is proposed. Any unrelated correctness/security finding stops again for scope resolution. The reserved 19-08 post-tag slot remains untouched.

Completed stage: Phase 19 execution through 19-06 and the D-123/D-124 corrective hardening merge/regeneration. Active stage: Phase 19 — Qualified v0.3.0 Release, held before the fresh version window. Under the approved recovery, exact continuation command: `/gsd-execute-phase 19`. The final boundary remains `/gsd-verify-work 19`, not run automatically.

Approval is required because [the adopted prior scope](19-CI-PARTITION-RESCOPE.md) covers the two test harnesses in PR #134, which is already merged; it does not authorize another main workflow repair/merge. AGENTS.md also requires rescoping an unresolved correctness/security finding. Keeping the release held requires no confirmation.
