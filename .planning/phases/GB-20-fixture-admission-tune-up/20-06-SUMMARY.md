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
  tasks: 3
  files: 5
actuals:
  tokens: 11757.75
  tasks: 3
  commits: 6
requirements-completed: []
requirements-pending: [RIGHTS-01]
commits: 6
plan_head_before: 802555ac42264561d6b3f6fbad233d9aac6db0a9
plan_head_after: 0d2a28d3
status: complete
completion_scope: Original Tasks 1 and 2 plus owner-authorized Task 3; original task evidence and historical actuals are preserved.
coverage:
  - id: PLATFORM-ARCHIVE-TRUST
    description: Trusted publisher verifies macOS and Windows downloaded products before draft validation; hostile archives, altered bytes, and unsafe paths reject.
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^workflow_policy_group_release_jobs$' (installed-product positives and archive policy negatives, including hidden metadata limits and cleanup/retry)"
        status: pass
      - kind: integration
        ref: "python3 -I .github/scripts/verify-workflow-policy.py --self-test --group release_jobs --root ."
        status: pass
  - id: PLATFORM-ARCHIVE-COVERAGE
    description: The independent workflow source snapshot and stable control registry cover the platform archive trust implementation and its mutations.
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^workflow_policy_coverage$' (exact reviewed checker and bounded-helper source/AST pins)"
        status: pass
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^workflow_policy_coverage_controls$' (82 negative controls, including independent resource/cleanup registry removal checks)"
        status: pass
  - id: BOUNDED-ARCHIVE-METADATA-CLEANUP
    description: Product archives are bounded before hidden metadata or payload consumption, and missing-checker/late-rejection failures leave a retryable clean destination.
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^workflow_policy_group_release_jobs$'"
        status: pass
      - kind: unit
        ref: "python3 -I .github/scripts/safe_extract_package.py --self-test"
        status: pass
---

# Phase GB-20 Plan 06: Trusted Platform Archive Summary

The release publisher now checks downloaded macOS and Windows product archives with a trusted local verifier before draft validation.

## Reopened for owner-authorized final-review security rescope

Final review reproduced a hidden PAX/GNU metadata bypass of the extractor's regular-file byte budget (CR-01) and a missing-trusted-checker path that leaves a stale destination (WR-01). The original accomplishments, completed-task metrics, three task commits and passing coverage remain historical evidence for Tasks 1 and 2; Task 3 adds the resource and cleanup guarantees.

The bounded follow-up in [20-06-PLAN.md](20-06-PLAN.md) adds total decompressed-stream and pre-payload metadata size/aggregate/count limits through the existing trusted production archive gate, synthetic controls for each limit, missing-checker cleanup and same-destination retry, and the reviewed source/AST/control-registry update. This stays inside Plan 20-06 and the nine-plan Phase 20 cap. No fixture or rights-policy change and no live publication are included. The executor acts next on Task 3; no new owner confirmation is required.

At the committed implementation/coverage head, reconfigure/build passed. The release-job grouped CTest, both workflow coverage CTests, safe-extractor self-test, plan-cap, planning-hygiene and live-summary CTests passed. Final Phase 20 full-suite, hosted platform and review/security/closure evidence remain separate required gates.

## Accomplishments

- Added bounded tar.gz extraction that rejects traversal, links, special entries, duplicate and case-folded paths, and archive size excesses.
- Validated downloaded macOS core, macOS player, and Windows core archives against the exact product inventory using the trusted checkout's checker and policy.
- Added workflow ordering and checker-authority mutations, Windows positive archive coverage, and hostile archive controls.
- Updated the independent workflow policy source snapshot, AST allowlist, and stable control registry under the owner's narrow authorization. Its source digest pins the complete reviewed checker; only the approved changed functions are exempted from historical AST equality.

## Task Commits

- `88b3ccc1`: Verify downloaded platform products in trusted publisher.
- `8dac3398`: Cover platform archive mutations and path aliases.
- `aea38114`: Pin workflow policy archive coverage and registry.
- `886000ef`: Bound product archive metadata streams and make cleanup/retry safe.
- `36ed25a2`: Pin the bounded helper source/AST and add resource/cleanup coverage negatives.
- `0d2a28d3`: Align the coverage CTest marker with the expanded negative-control count.

Six Plan 20-06 task commits are listed above. Interleaved Plan 20-09 commits are excluded from this plan's count.

## Verification

- `cmake --preset phase1` and `cmake --build --preset phase1 -j2` passed at the final implementation/coverage head.
- The release workflow grouped controls passed in CTest, including macOS and Windows archive positives, exact hidden-metadata limits, missing-checker retry, and partial-extraction cleanup.
- Both workflow coverage CTests passed; the independent coverage-control CTest reports 82 passing negative controls, including helper source mutation and each new registry-row removal.
- `python3 -I .github/scripts/safe_extract_package.py --self-test`, `plan_cap`, `planning_hygiene_controls`, and `summary_coverage_live` passed.

## Deviations from Plan

The independent coverage checker required its owner-authorized snapshot, AST allowlist, registry update, and an updated CTest completion marker to recognize the new trusted workflow checker and expanded negative-control count. The gate remained enforced and its negative controls passed.

## Self-Check: PASSED

- All six Plan 20-06 task commits are ancestors of the recorded final head; interleaved Plan 20-09 commits are excluded.
- No fixture was admitted, and RIGHTS-01 remains pending.
