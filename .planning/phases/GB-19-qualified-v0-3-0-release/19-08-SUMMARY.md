---
phase: GB-19-qualified-v0-3-0-release
plan: "08"
subsystem: release
tags: [v0.3.0, post-tag-recovery, release-notes, readback]
requires:
  - phase: GB-19-qualified-v0-3-0-release/19-05
    provides: tag-bound release proof, asset receipts, and existing readback validator
  - phase: GB-19-qualified-v0-3-0-release/19-07
    provides: immutable tag S, same-draft identity, and the approved single D-27 recovery slot
provides:
  - regression coverage for the actual generated-notes failure and exact tagged-section repair
  - retry-aware readback that reports actual workflow G separately from product source S
  - one successful publication retry of the existing v0.3.0 release
affects: [GB-19-qualified-v0-3-0-release/19-07]
actuals:
  tasks: 3
  commits: 13
plan_head_before: a3f3390451f9a893aa47475f15a722ada86daaa6
plan_head_after: 97c20d56e76c0caf4cdc14f421f0cf64cb970b93
tech-stack:
  added: []
  patterns: [immutable-source repair regression, conditional G/S publication binding, exact same-draft API readback]
key-files:
  created:
    - tests/data/release-api/v030-notes-failure.json
    - tests/data/release-api/v030-draft-association-restoration.json
    - tests/data/release-api/SOURCES.md
    - .planning/phases/GB-19-qualified-v0-3-0-release/19-08-SUMMARY.md
  modified:
    - tests/scripts/verify-release-lifecycle.py
    - tests/scripts/verify-v03-dispositions.py
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - docs/release.md
key-decisions:
  - "Keep ordinary push readbacks strict at head S; allow G only for an explicitly captured workflow_dispatch retry whose products remain bound to S."
  - "Stop after the body-only update changed the draft tag association; perform no retry until the same release ID/tag association was restored and read back."
  - "Use the one pre-authorized live retry only after the corrective PR, exact-head qualification, and complete offline replay passed."
patterns-established:
  - "A release API success code does not establish that unrelated draft metadata stayed unchanged; verify the full identity after each mutation."
  - "Record failed run, workflow head, product source, raw receipt, and published assets as separate provenance facts."
requirements-completed: []
coverage:
  - id: D1
    description: The first release-notes failure is preserved as a real refusal, and the transformed tag-section bytes pass the unchanged production adoption checker.
    verification:
      - kind: integration
        ref: "`release_lifecycle_post_tag_recovery_controls` exercises the sanitized failing body, original tagged section, exact one-link repair, byte hashes, and adoption-negative/positive twins."
        status: pass
      - kind: integration
        ref: "The original live failure is retained as run 41148606886, candidate job 124379552103, refusal `release-notes-absence-missing`; no fixture replaces its failure evidence."
        status: pass
    human_judgment: false
  - id: D2
    description: Retry readback binds the actual dispatch/run/jobs to workflow head G and independently binds tag, assets, receipts, perf data, and inventory to source S.
    verification:
      - kind: integration
        ref: "`v03_readback` validates `.planning/phases/GB-19-qualified-v0-3-0-release/19-release-readback.json`; `v03_readback_controls` rejects fake S heads, wrong event/workflow, missing raw receipt IDs, digest drift, and incomplete inventory."
        status: pass
      - kind: other
        ref: "Actual run 41205021983 attempt 1: workflow head G d61a25ea, product/tag source S a3f33904, release 429606490, successful publication with 22 assets."
        status: pass
    human_judgment: false
  - id: D3
    description: The draft tag-association drift stopped retry dispatch; an explicit same-ID restoration preserved the repaired body before the single retry.
    verification:
      - kind: integration
        ref: "`release_lifecycle_post_tag_recovery_controls` models tag drift, incomplete API objects, marker reuse, competing release workflows, malformed release rows, and refusing second invocation after an ambiguous mutation."
        status: pass
      - kind: other
        ref: "Actual body PATCH evidence records the HTTP 200 body repair and changed tag association; The D-132-authorized restoration with D-133 UTF-8 fixes kept body bytes unchanged and restored CLI draft lookup before dispatch. Captures remain under `build/phase19-window/posttag-recovery/`."
        status: pass
    human_judgment: false
duration: not recorded across sessions
completed: 2026-10-31
status: complete
---

# Phase 19 Plan 08: Single Post-Tag Notes Recovery Summary

**The approved one-time recovery repaired the same v0.3.0 release, preserved the failed first run, and proved the main retry workflow at G still published product source S.**

## Performance

- **Duration:** Not recorded across sessions.
- **Started:** 2026-10-30.
- **Completed:** 2026-10-31.
- **Tasks:** 3 of 3.
- **Source diff basis:** The implementation branch from S to `97c20d56` contained 13 commits across the seven authorized implementation paths; corrective PR #136 squash G is recorded separately. A token delta was not recorded after the approved D130–D133 follow-ups extended recovery evidence and operator controls across the implementation and PR B branches.

## Accomplishments

- Added a sanitized fixture and provenance for the actual first live failure. The original generated notes remain a negative against `release-notes-absence-missing`; the tagged S changelog section and the exact single tag-pinned support-ledger URL replacement pass the unchanged adoption checker with exact UTF-8 hashes.
- Extended the existing lifecycle recovery controls, strict readback validator, test inventory, and release procedure. The recovery controls preserve source-S receipts and product evidence while recording the actual retry workflow head G. Normal push stays bound to S. The retry branch requires an explicit dispatch request, actual successful API run/jobs, raw receipt bytes, full asset identities, source performance receipt, pre-publish inventory, and the bounded allowlist.
- Corrective PR #136 was independently reviewed, qualified, and merged as G `d61a25ea`, a direct child of S `a3f33904` with the approved source change. Required CI, fixture, and preview checks passed; the version-PR gate was skipped because this was not the component release PR. The ordinary G release-please push was benign and produced no candidate. At G, the complete remaining-stage replay passed 50/50 without skips.
- The first body-only repair returned HTTP 200 and installed the repaired body, but also changed the existing draft's tag association. Dispatch remained stopped. After the D-132-authorized restoration using the D-133-corrected and independently reviewed operator, independent readback confirmed the same release ID/tag and unchanged body before the sole retry.
- Retry run `41205021983`, attempt 1, completed successfully on workflow head G with product/tag source S. Existing release `429606490` was published at `2026-10-31T13:47:13Z` with 22 assets. The actual raw receipt and pre-publication inventory passed the strict committed readback.
- At source `8a561c58`, the focused readback/recovery/disclosure/window/policy set passed 19/19 in 47.62 seconds. Recovery controls reported 93 refusal and 12 positive controls; the live readback test and readback controls passed. The exact runtimes are summarized in the 19-07 SUMMARY and retained in `build/phase19-window/posttag-recovery/checkout/build/prb-focused.log`.

## Task Commits

The recovery branch ran from S `a3f33904` to qualified branch head `97c20d56` in 13 commits. The non-releasable corrective PR #136 squash is G `d61a25ea`. Detailed task commits, review rounds, and intermediate failed test attempts are preserved in `build/phase19-window/posttag-recovery/implementation-report.md` and its referenced evidence directories.

## Decisions Made

- The failed first release run remains failed; the successful retry is a distinct dispatch with actual API-provided run and job identities.
- The body-only PATCH's tag-association drift was treated as a stop. D-132 authorized the one tag-only restoration; D-133 corrected the no-write entrypoint error. No retry was dispatched until the exact same-ID request and strict independent readback succeeded.
- No second retry, tag move, new release, or later gap round was authorized or performed.
- REL-01 stayed pending until 19-07 committed and validated the published readback.

## Deviations from Plan

The post-tag failure correctly consumed the single reserved D-27 gap plan. Owner-approved D-130 corrected the readback run-ID, allowlist and documentation contracts before source qualification. D-131 permitted diagnosis after the body-only response changed the draft association. D-132 then authorized one conditional tag-only restoration and the same unused retry. Its actual read-only preflight raised a str/bytes TypeError before any mutation. D-133 authorized exactly two UTF-8 call-site corrections, full actual-main entrypoint replay and fresh independent review. The fixed read-only preflight, one restoration and sole retry succeeded. These approvals changed neither the Git tag, product source, frozen policy authority, timeouts nor performance limits.

## Issues Encountered

The first draft-body update changed tag association despite the body-only request. The guard prevented retry dispatch, the exact drift was recorded, and the same draft was restored and independently read back before the one successful retry. This is retained as an important release-service behavior, not classified as a transient API error.

## Next Phase Readiness

The single post-tag recovery is complete and feeds the final 19-07 readback. It does not independently complete REL-01 or phase verification. Phase 19 has 8/8 plans executed; after the parent closes PR B's exact-head gates, the exact next command is `/gsd-verify-work 19`. No milestone audit or next phase was started.

---
*Phase: GB-19-qualified-v0-3-0-release*
*Completed: 2026-10-31*
