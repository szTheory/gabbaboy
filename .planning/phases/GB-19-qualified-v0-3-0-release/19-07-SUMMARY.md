---
phase: GB-19-qualified-v0-3-0-release
plan: "07"
subsystem: release
tags: [v0.3.0, exact-tag, publication, readback, phase-boundary]
requires:
  - phase: GB-19-qualified-v0-3-0-release/19-05
    provides: tag-bound release gates, consumer receipts, and v0.3 readback validator
  - phase: GB-19-qualified-v0-3-0-release/19-06
    provides: reviewed release content, notes preface, and operational preflight
provides:
  - v0.3.0 publication from its exact tag with a source-bound 22-asset readback
  - inactive version-window state and frozen v0.3.0 disclosure ledger
  - Phase 19 execution handoff after the one approved post-tag recovery
affects: [GB-19-qualified-v0-3-0-release verification]
actuals:
  tasks: 4
  commits: 6
plan_head_segments:
  version_pr_pin_commit: 53b7c2e041e80b67174df12cd9b44949560b7c53
  version_pr_head_h: 5948b0c32c0887323777d143b867b13d4feb0716
  version_pr_window_w: c4c0258bcdd65cf026e1497dd2585b634d807bd5
  tagged_source_s: a3f3390451f9a893aa47475f15a722ada86daaa6
  corrective_source_g: d61a25ea54364e0e26ef89bb7467c72089361d49
  prb_source_head: 8a561c58f2973fff7d1cf8e37bfcd75a31ef880c
tech-stack:
  added: []
  patterns: [production exact-head qualification, byte-bound published readback, truthful G/S recovery attribution]
key-files:
  created:
    - .planning/phases/GB-19-qualified-v0-3-0-release/19-release-readback.json
    - .planning/phases/GB-19-qualified-v0-3-0-release/19-07-SUMMARY.md
  modified:
    - .planning/phases/GB-19-qualified-v0-3-0-release/19-07-PLAN.md
    - .planning/REQUIREMENTS.md
    - .planning/ROADMAP.md
    - .planning/context/LESSONS.md
    - tests/data/version-window.json
    - tests/scripts/verify-v03-dispositions.py
    - tests/scripts/verify-support-ledger.py
key-decisions:
  - "Preserve the original failed S release run and the separate one-time G/S retry as distinct evidence."
  - "Close REL-01 only after the published tag, exact-source receipts, complete asset inventory, and committed readback reconcile."
  - "Keep the repair branch that anchors immutable policy authority objects until a reviewed authority rebaseline."
patterns-established:
  - "Use production --check-pr to qualify every required duplicate check instance; a literal count of three is not sufficient."
  - "Parse actual timestamped workflow verdict output so echoed shell patterns cannot be mistaken for results."
requirements-completed: [REL-01]
coverage:
  - id: D1
    description: v0.3.0 is published from tag S with every product receipt and all 22 API assets reconciled in the committed readback.
    requirement: REL-01
    verification:
      - kind: integration
        ref: "`v03_readback` and `verify-v03-dispositions.py --check-readback .planning/phases/GB-19-qualified-v0-3-0-release/19-release-readback.json --rev 8a561c58f2973fff7d1cf8e37bfcd75a31ef880c --tag v0.3.0`; actual retry run 41205021983 published release 429606490 from source S."
        status: pass
      - kind: integration
        ref: "`v03_readback_controls` rejects wrong tag/source, fake S workflow heads, missing or changed assets, receipt drift, and incomplete pre-publication inventory."
        status: pass
    human_judgment: false
  - id: D2
    description: The release version window is inactive after publication and the published v0.3.0 ledger is frozen to its tag bytes.
    requirement: REL-01
    verification:
      - kind: integration
        ref: "`release_window_contract` and `release_window_controls` pass with the final inactive record and refuse active/stale window mutants."
        status: pass
      - kind: integration
        ref: "`release_disclosure_generator` reports tagged=2; `release_disclosure_controls` refuses a one-byte v0.3.0 ledger mutation."
        status: pass
    human_judgment: false
  - id: D3
    description: The single post-tag notes recovery preserves the failed first run, exact tagged-section bytes, and truthful retry workflow/source identity.
    requirement: REL-01
    verification:
      - kind: integration
        ref: "`release_lifecycle_post_tag_recovery_controls` (93 refusal controls and 12 positive controls) plus `v03_readback_controls`; original release-notes-absence-missing remains in failed run 41148606886, separate from successful retry 41205021983."
        status: pass
      - kind: other
        ref: "Captured release API/readback projection: actual workflow G d61a25ea, product/tag source S a3f33904, same release ID 429606490."
        status: pass
    human_judgment: false
  - id: D4
    description: The version-window observer accepts only the actual timestamped active verdict and exact R2/W binding, and rejects echoed-pattern false evidence.
    requirement: REL-01
    verification:
      - kind: integration
        ref: "`workflow_policy_check` and `workflow_policy_coverage_controls`; actual W gate 41143678963 emitted active at W and bound rehearsal R2 41140523418. The wrong-run and inactive-output probes refuse."
        status: pass
    human_judgment: false
  - id: D5
    description: The partitioned workflow-policy coverage retains all six semantic groups and complete omission/duplication controls within unchanged budgets.
    requirement: REL-01
    verification:
      - kind: integration
        ref: "At source 8a561c58, `workflow_policy_group_ci`, `workflow_policy_group_release_jobs`, `workflow_policy_group_release_support`, `workflow_policy_group_rehearsal`, `workflow_policy_group_ledger`, `workflow_policy_group_helpers`, `workflow_policy_coverage`, and `workflow_policy_coverage_controls` passed; group TIMEOUT remains 180 seconds."
        status: pass
    human_judgment: false
  - id: D6
    description: The shipped macOS package metadata is documented with its actual architecture and deployment target without claiming hardware qualification or older macOS support.
    requirement: REL-01
    verification:
      - kind: other
        ref: "`build/phase19-window/release-S/published-41205021983/macos-binary-inspection/inspection-report.md`: API/receipt/SHA256SUMS asset digests match; runner, core object, player, and SDL are arm64 Mach-O with macOS minOS 15.0 / SDK 15.5. No binary was executed."
        status: pass
    human_judgment: false
duration: not recorded across sessions
completed: 2026-10-31
status: complete
---

# Phase 19 Plan 07: Exact-Tag Window, Publication and Readback Summary

**The v0.3.0 tag published successfully after one approved D-27 recovery, and its 22-asset release readback binds the actual main retry workflow to product source S.**

## Performance

- **Duration:** Not recorded across sessions.
- **Started:** 2026-10-30.
- **Completed:** 2026-10-31.
- **Tasks:** 4 of 4.
- **Plan commits:** Six persisted boundary commits are recorded in `plan_head_segments`; execution crossed the version-PR branch, main, the corrective PR, and the PR B branch, so there is no single linear `plan_head_before..plan_head_after` interval. Token delta was not recorded because the task output spans those overlapping histories.

## Accomplishments

- Closed the operational prerequisites while preserving the frozen 19-06 pre-merge SUMMARY. PR #133's actual squash was `cb3055c9`; D-123/D-124 PR #134 and D-125..D-129 PR #135 produced the qualified window base `9c405b01`. The authority branch retains the reviewed workflow-policy objects.
- Qualified version-PR head H `5948b0c3` with R1 `41135937384`, then W `c4c0258b` with R2 `41140523418`, nightly run `41140524840`, required CI, and version gate `41143678963`. Production `verify-release-gates.sh --check-pr` passed on the actual H and W heads, including duplicate required-check instances. The earlier `(length == 3)` predicates are not counted as evidence.
- Squash-merged PR #131 at S `a3f33904` on 2026-10-31; S is tree-equal to W and tag `v0.3.0` resolves to S. The original release run `41148606886` failed before build/publication because generated notes lacked the required preface. The approved one-gap recovery is recorded in 19-08; its actual successful retry run `41205021983` executed at G `d61a25ea` and published the same release ID `429606490` from product source S.
- Committed the strict 22-asset readback, reset the version window to inactive, froze the published v0.3.0 support ledger, and marked REL-01 complete. D-28's older `verify-v03-dispositions.py` pending rows were already closed at f80bdf54 (Drift 3); this plan did not rewrite that record.
- At source `8a561c58`, the focused immutable-source set passed 19/19. The six policy groups measured CI 15.71 s, release jobs 28.85 s, release support 6.80 s, rehearsal 17.24 s, ledger 5.08 s, helpers 5.84 s; policy coverage was 0.95 s and its controls 1.95 s. The f80bdf54 aggregate `workflow_policy_controls` time of 49.9 s is historical and superseded; all per-group 180-second budgets are unchanged. Total focused CTest wall time was 47.62 s.
- Inspected the actual published macOS core and preview archives. All four Mach-O targets were arm64 with macOS minOS 15.0 / SDK 15.5. The packages are unsigned, not notarized, and not hardware-qualified; no older OS or physical-hardware compatibility is claimed. The report and asset hashes are in `build/phase19-window/release-S/published-41205021983/macos-binary-inspection/`.

## Window and Recovery Boundaries

The version-PR lineage is H1 `53b7c2e0` → H `5948b0c3` → W `c4c0258b`; the merge created S `a3f33904`. The qualified corrective main head after the post-tag recovery is G `d61a25ea`. PR B source head `8a561c58` contains the committed readback and focused controls. These are distinct branch/merge points, not one first-parent plan interval.

The release-boundary triage captured no open issues and only PR #131, as expected, in `build/phase19-window/task3-go-no-go/`. The fresh pre-PR-B boundary triage captured no open issues or PRs in `build/phase19-window/prb-boundary-triage/`. No access failure was recorded.

The run observer now filters the timestamped verdict line and exact R2/W output. The old raw grep also matched an echoed shell case pattern; `gate-w-verdict-proof.json` retains the active verdict, exact R2 binding, and wrong-run/inactive-output refusal probes.

## Task Commits

The task boundary commits are H1 `53b7c2e0`, H `5948b0c3`, W `c4c0258b`, tag squash S `a3f33904`, corrective source G `d61a25ea`, and PR B source head `8a561c58`. H1/H/W are on the version-PR branch; S and G are main squashes; 8a561c58 is the local PR B source head. The successful recovery run and source distinction are detailed in [19-08-SUMMARY.md](19-08-SUMMARY.md).

## Decisions Made

- Preserved the first failed release run and used only the single D-27 gap slot.
- Treated the draft tag-association change after the body repair as a stop condition; the same release ID was restored and verified before the one retry.
- Kept REL-01 pending until the exact-tag publication and readback reconciled; the gap plan alone did not close the requirement.
- Kept signing, notarization, hardware qualification, and older macOS support outside the claims.

## Deviations from Plan

The original Task 3 success predicate did not pass: release run `41148606886` failed with `release-notes-absence-missing`. The already reserved D-27 gap plan 19-08 repaired the same draft and completed one retry at G while retaining product source S. This outcome is recorded rather than rewriting the original failure as a pass.

The operator verification template was corrected to use the production all-duplicates `--check-pr` gate and timestamped verdict lines. This removes two false assumptions from the plan evidence: a fixed count of three check runs and a raw log grep that matched echoed shell text.

## Issues Encountered

The first body-only API update returned HTTP 200 with the repaired body but also changed the draft tag association. No retry was dispatched until the same release association was restored and independently read back. Exact captures remain in the ignored `build/phase19-window/posttag-recovery/` evidence directories.

## Next Phase Readiness

Phase 19 execution has all eight plans complete, with the one planned gap slot used. The summary records the focused 19/19 run at `8a561c58`; PR B exact-head hosted qualification/merge and the final phase verification are not claimed here. After the parent closes those gates, the exact next command is `/gsd-verify-work 19`. No milestone audit or later phase was started.

---
*Phase: GB-19-qualified-v0-3-0-release*
*Completed: 2026-10-31*


## Final PR B review checkpoint

After the factual release/readback summary was authored, the final standard-depth code review reproduced malformed schema-version acceptance and a registry-root diagnostic gap. The actual published inventory uses integer version1 and the release still reconciles, but unresolved validator correctness prevents final PR B closure. T-19-22 and validation are reopened. Under the exhausted review-fix limit, an isolated bounded prototype is preparation for an owner scope decision only; no implementation fix has entered PR B. Full final-head local qualification, goal verification and exact-head hosted PR B/merge remain pending. This summary is halted at Task4 rather than claiming a completed phase boundary. Continue the same Phase19 with `/gsd-execute-phase 19` after the bounded scope decision; eventual owner handoff remains `/gsd-verify-work 19`.


## D-134 final schema repair and rechecks

The owner approved the concrete seven-path schema repair after the final code-review checkpoint. Committed d2c0dc95 exactly matches the isolated900eabfd prototype: five existing validators enforce their declared exact integer schemas and controlled registry-root errors; two existing registrations raise the measured floors/markers. No new target, timeout, policy authority, dependency, permission, product or live release action was added. Eight affected current-source CTests pass, including the actual22-asset readback and positive/negative schema controls. New measured control guards are51/120/99/72; earlier93-control and19-test results above remain historical source-specific facts.

Fresh independent code recheck closes WR-01/WR-02. The adjacent legacy numeric-version observation was withdrawn after contract/probe adjudication; no invalid source/measurement or unsupported version was accepted by that path, and it establishes no new exact-token policy. Fresh independent security recheck reclosed T-19-22 and confirmed all41 threats closed with existing AR-19-01 unchanged. Validation has automated gap closure. Final local full/player/consumer qualification, final phase-goal report, exact-head protected CI and the planned guarded PR B squash remain separate qualification gates; their final facts go to local continuation, not a summary edit after fingerprinting. No further scope decision is pending.
