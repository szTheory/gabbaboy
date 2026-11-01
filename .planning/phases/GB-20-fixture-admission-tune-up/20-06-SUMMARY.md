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
  modified: [.github/workflows/release.yml, .github/workflows/ci.yml, .github/scripts/release-evidence-lifecycle.sh, .github/scripts/verify-workflow-policy.py, .github/scripts/safe_extract_package.py, tests/scripts/verify-workflow-policy-coverage.py, tests/data/workflow-policy-controls.json, tests/cmake/ci-lanes.cmake]
key-decisions:
  - Validate downloaded platform bytes using only the trusted publisher checkout before draft validation.
  - Preserve source-only and fixture rights boundaries; archive checks do not establish legal permission.
metrics:
  duration: 30 min
  completed: 2026-11-01
  tasks: 4
  files: 8
actuals:
  tokens: 26404.25
  tasks: 4
  commits: 10
requirements-completed: []
requirements-pending: [RIGHTS-01]
commits: 10
plan_head_before: 802555ac42264561d6b3f6fbad233d9aac6db0a9
plan_head_after: 1b9aa6f79b8a78efa995fa689bb8f9762c3aa30c
status: complete
completion_scope: Tasks 1–4; original task evidence is preserved and the final plan record covers all ten Plan 20-06 implementation and coverage commits.
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
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^workflow_policy_coverage_controls$' (94 negative controls, including independent resource/cleanup/path registry removal checks)"
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
  - id: WINDOWS-ARCHIVE-PATH-CONTAINMENT
    description: Windows drive and alternate-stream archive names reject, and directory/file targets are proven inside the extraction root before any creation.
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^workflow_policy_group_release_jobs$' (drive, ADS, injected directory/file escape controls, unchanged outside sentinels, zero outside write attempts)"
        status: pass
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^workflow_policy_(coverage|coverage_controls)$' (exact source pin and independent removal checks for all four path controls)"
        status: pass
---

# Phase GB-20 Plan 06: Trusted Platform Archive Summary

The release publisher now checks downloaded macOS and Windows product archives with a trusted local verifier before draft validation.

## Task 4 Windows target-containment rescope (completed)

The independent review reproduced a Windows drive-qualified directory escape and regular-parent creation before containment checks; production validation also accepted NTFS alternate-stream names. Task 4 now rejects colon syntax in every path component and validates each target and its existing ancestry before archive-controlled creation. Production controls prove drive/ADS rejection, zero outside write attempts, unchanged sentinels and destination cleanup.

The task retained Task 3's bounded stream and cleanup behavior, refreshed the immutable source/AST snapshot and four stable path controls, and passed the required final-head build and focused checks. The nine-plan cap is unchanged. No fixture/rights change or live publication is included; final Phase 20 integration and hosted gates are recorded below.

## Task 3 bounded metadata and cleanup rescope (completed)

Final review reproduced a hidden PAX/GNU metadata bypass of the extractor's regular-file byte budget (CR-01) and a missing-trusted-checker path that leaves a stale destination (WR-01). The original accomplishments, completed-task metrics, three task commits and passing coverage remain historical evidence for Tasks 1 and 2; Task 3 adds the resource and cleanup guarantees.

The bounded follow-up in [20-06-PLAN.md](20-06-PLAN.md) adds total decompressed-stream and pre-payload metadata size/aggregate/count limits through the existing trusted production archive gate, synthetic controls for each limit, missing-checker cleanup and same-destination retry, and the reviewed source/AST/control-registry update. This stays inside Plan 20-06 and the nine-plan Phase 20 cap. No fixture or rights-policy change and no live publication are included. Task 3 completed before Task 4; its implementation and coverage commits are listed below.

At the committed implementation/coverage head, reconfigure/build passed. The release-job grouped CTest, both workflow coverage CTests, safe-extractor self-test, plan-cap, planning-hygiene and live-summary CTests passed. Final Phase 20 full-suite, hosted platform, review, security and closure evidence is recorded in the phase-level artifacts.

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
- `a5bf5cc8`: Reject Windows drive/ADS names and validate extraction targets before creation.
- `b4cdba4e`: Pin the original Task 4 source/AST and require independent path-control removal negatives.
- `37de7e8a`: Extend Task 4 containment to the reusable package extractor and connect its path controls to release policy.
- `1b9aa6f7`: Pin the reviewed helper and policy sources and require independent removal controls.

All ten Plan 20-06 implementation and coverage commits are listed above. Interleaved Plan 20-09 commits are excluded from this plan's count.

## Verification

- `cmake --preset phase1` and `cmake --build --preset phase1 -j2` passed at the final implementation/coverage head.
- The release workflow grouped controls passed in CTest, including macOS and Windows archive positives, exact hidden-metadata limits, missing-checker retry, and partial-extraction cleanup.
- Both workflow coverage CTests passed; the independent coverage-control CTest reports 94 passing negative controls, including source mutation and removal of each resource, cleanup and path registry row.

## Final lifecycle replay integration follow-up

Commit `7163002d` extended the existing release-lifecycle replay to carry the trusted downloaded-byte product gate through its successful publication path and reject each required macOS-core, macOS-player, and Windows-core archive when omitted or altered. It also pins the evolving adoption checker separately from the historical v0.3 source. The final `bash tests/scripts/verify-release-candidate.sh --self-test` passed at source head `7293eb47a6c799b6455dd854533aca932f4529ad`, including receipt identity, digest tampering, draft/proof, fixture-leak, source-archive, and substitution negatives. This phase-orchestration follow-up does not change rights policy or publish a release.

## Windows native checkout exact-byte follow-up

The first hosted PR run found that the Windows runner's default `core.autocrlf=true` converted fixture manifests before CMake ran, causing the exact-byte admission check to treat unchanged legacy manifests as mutations. This was reproduced in a temporary clone with the precise `record-field-missing: manifest` rejection. The `native-windows` CI job now sets `core.autocrlf=false` and `core.eol=lf` before `actions/checkout`; a temporary clone with that setup passes the same repository-admission check, while the unconfigured clone fails. Exact-head Windows CI passed in both the PR and push matrices.
- Drive-qualified, drive-relative, nested mixed-case drive, ADS filename/component, directory escape injection and regular-parent escape injection controls all reject with `product-archive-path`; spies observed zero outside writes and sentinels stayed unchanged.
- `python3 -I .github/scripts/safe_extract_package.py --self-test`, `plan_cap`, `planning_hygiene_controls`, and `summary_coverage_live` passed.

## Deviations from Plan

The independent coverage checker required its owner-authorized snapshots, precise AST inventories, registry updates and dynamic CTest completion markers for the Task 3 and Task 4 controls. The gate remained enforced and all negative controls passed.

## Self-Check: PASSED

- All ten Plan 20-06 implementation and coverage commits are ancestors of the recorded implementation head; interleaved Plan 20-09 commits are excluded.
- No fixture was admitted, and RIGHTS-01 remains pending.

## Exact-head hosted qualification

The earlier implementation head `39eb048e7770652b84a3fc5da7aaa3890adbd70c` passed both exact-head CI events: pull-request run 41334163805 and push run 41334157283. The final implementation head `1b9aa6f79b8a78efa995fa689bb8f9762c3aa30c` passed PR CI run 41347651035 and push CI run 41347645660; its macOS player package, Windows native, sanitizer, and required-native checks passed. The PR-only version gate was skipped as expected.

Preview run 41347651030 and fixture-repro runs 41347651034 (PR) and 41347645556 (push) also passed. Preview covered Linux/macOS installed-package smoke, downloaded macOS player receipt verification, and the aggregate gate. RIGHTS-01 remains pending because no fixture was admitted.


## Reusable safe-extractor containment follow-up

The final standard review found that the reusable `.github/scripts/safe_extract_package.py` helper still accepted a later drive-qualified component. The same Task 4 rescope now covers both that helper and the trusted product extractor. It rejects colon syntax in every component and proves each resolved native target remains inside the extraction root before parent creation or file open. The helper's self-test covers nested drive/ADS names, Windows cross-drive joining, and injected outside directory/file targets with zero outside write attempts and unchanged sentinels.

Implementation and independent coverage updates are commits `37de7e8a9afee6b2b8a263e543279704cbfc1d56` and `1b9aa6f79b8a78efa995fa689bb8f9762c3aa30c`. At source head `1b9aa6f79b8a78efa995fa689bb8f9762c3aa30c`, configure/build, direct extractor self-test, the release-job policy group, workflow-policy coverage and negative controls, plan cap, planning hygiene, and live summary coverage passed. The first full CTest run passed 1,706/1,711 because five Git-worktree controls could not write metadata under this managed checkout's read-only `.git`; all five passed in focused reruns with a temporary Git metadata clone under `/tmp`. A second wrapper-based full run passed 1,710/1,711; `v02_source_archive_controls` timed out at 90 seconds without checker output, then passed alone in 45.57 seconds with the normal Git path. Thus all 1,711 tests have passing evidence across two full runs and six focused reruns; no single full-suite invocation is claimed all-green.

No fixture was admitted, no rights decision changed, and `RIGHTS-01` remains pending. Hosted checks for this implementation head are recorded with the final Phase 20 qualification evidence.

The fresh phase verifier confirmed 35/35 implementation truths but returned `human_needed` because two spec-less Plan 20-01 prohibitions remain unresolved and descriptor-less by project instruction. The owner must source-ground those assumptions before verification can pass. This is not a request for manual UAT and does not decide fixture rights; Phase 21 remains unstarted.
