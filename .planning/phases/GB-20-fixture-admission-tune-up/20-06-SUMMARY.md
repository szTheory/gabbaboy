---
phase: GB-20-fixture-admission-tune-up
plan: "06"
subsystem: release-products
tags: [release-workflow, archive-validation, fixture-admission]
requires:
  - phase: GB-20-fixture-admission-tune-up/20-05
    provides: Pinned policy and exact product inventory
  - phase: GB-20-fixture-admission-tune-up/20-07
    provides: Exact trusted workflow policy checks
provides:
  - Trusted bounded verification of downloaded macOS and Windows product archives
  - Coverage registry and independent AST/source review updated for the trusted checker
affects: [fixture-admission, CI, RIGHTS-01]
tech-stack:
  added: []
  patterns: [Bounded standard-library tar extraction, trusted checker source and policy authority]
key-files:
  created: [.planning/phases/GB-20-fixture-admission-tune-up/20-06-SUMMARY.md]
  modified: [.github/workflows/release.yml, .github/scripts/release-evidence-lifecycle.sh, .github/scripts/verify-workflow-policy.py, tests/scripts/verify-workflow-policy-coverage.py, tests/data/workflow-policy-controls.json]
key-decisions:
  - Validate downloaded platform bytes using only the trusted publisher checkout before draft validation.
  - Preserve source-only and fixture rights boundaries; archive checks do not establish legal permission.
metrics:
  duration: 30 min
  completed: 2026-11-01
  tasks: 2
  files: 5
actuals:
  tokens: 11757.75
  tasks: 2
  commits: 4
requirements-completed: []
requirements-pending: [RIGHTS-01]
commits: 4
plan_head_before: 802555ac42264561d6b3f6fbad233d9aac6db0a9
plan_head_after: aea38114
status: reopened
completion_scope: Original Tasks 1 and 2 only; their evidence and measured actuals are historical.
pending_follow_up: Task 3 — final-review tar metadata bounds and missing-checker cleanup/retry.
coverage:
  - id: PLATFORM-ARCHIVE-TRUST
    description: Trusted publisher verifies macOS and Windows downloaded products before draft validation; hostile archives, altered bytes, and unsafe paths reject.
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^workflow_policy_group_release_jobs$'"
        status: pass
      - kind: integration
        ref: "python3 -I .github/scripts/verify-workflow-policy.py --self-test --group release_jobs --root ."
        status: pass
  - id: PLATFORM-ARCHIVE-COVERAGE
    description: The independent workflow source snapshot and stable control registry cover the platform archive trust implementation and its mutations.
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^workflow_policy_coverage$'"
        status: pass
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^workflow_policy_coverage_controls$'"
        status: pass
---

# Phase GB-20 Plan 06: Trusted Platform Archive Summary

The release publisher now checks downloaded macOS and Windows product archives with a trusted local verifier before draft validation.

## Reopened for owner-authorized final-review security rescope

Plan 20-06 is incomplete until its appended Task 3 passes. Final review reproduced a hidden PAX/GNU metadata bypass of the extractor's regular-file byte budget (CR-01) and a missing-trusted-checker path that leaves a stale destination (WR-01). The original accomplishments, completed-task metrics, three task commits and passing coverage below remain historical evidence for Tasks 1 and 2; they do not establish the new resource/cleanup guarantees.

The bounded follow-up in [20-06-PLAN.md](20-06-PLAN.md) adds total decompressed-stream and pre-payload metadata size/aggregate/count limits through the existing trusted production archive gate, synthetic controls for each limit, missing-checker cleanup and same-destination retry, and the reviewed source/AST/control-registry update. This stays inside Plan 20-06 and the nine-plan Phase 20 cap. No fixture or rights-policy change and no live publication are included. The executor acts next on Task 3; no new owner confirmation is required.

After implementation, reconfigure/build at its committed head and pass the release-job grouped CTest, both workflow coverage CTests, the safe-extractor self-test, and the plan-cap/planning-hygiene/live-summary CTests named in Task 3. Append actual follow-up commits and fresh block-style coverage, then change status to complete. Final Phase 20 full-suite, hosted platform and review/security/closure evidence remain separate required gates.

## Accomplishments

- Added bounded tar.gz extraction that rejects traversal, links, special entries, duplicate and case-folded paths, and archive size excesses.
- Validated downloaded macOS core, macOS player, and Windows core archives against the exact product inventory using the trusted checkout's checker and policy.
- Added workflow ordering and checker-authority mutations, Windows positive archive coverage, and hostile archive controls.
- Updated the independent workflow policy source snapshot, AST allowlist, and stable control registry under the owner's narrow authorization. Its source digest pins the complete reviewed checker; only the approved changed functions are exempted from historical AST equality.

## Task Commits

- `88b3ccc1`: Verify downloaded platform products in trusted publisher.
- `8dac3398`: Cover platform archive mutations and path aliases.
- `aea38114`: Pin workflow policy archive coverage and registry.

The measured plan range includes the interleaved Plan 20-09 implementation commit, so its measured commit count is four while three commits above belong to Plan 20-06.

## Verification

- Release workflow grouped controls passed in CTest, including macOS and Windows archive positives and negative mutations.
- Both workflow coverage and coverage-control CTests passed after updating the reviewed source snapshot and reconfiguring at the candidate head.

## Deviations from Plan

The independent coverage checker required its owner-authorized snapshot, AST allowlist, and registry update to recognize the new trusted workflow checker. The gate remained enforced and its negative controls passed.

## Original Tasks 1–2 Self-Check: PASSED (historical)

- All three Plan 20-06 commits are ancestors of the recorded implementation head; the measured range contains four commits due to Plan 20-09 interleaving.
- No fixture was admitted, and RIGHTS-01 remains pending.
