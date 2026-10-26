---
phase: 16-tune-up-and-v0-2-debt-closure
plan: "07"
subsystem: release-publication
tags: [v0.2.1, release-window, rehearsal, source-proof, attach-evidence, pr-closure, dispositions, tune-06]
requires:
  - phase: 16-06
    provides: the ledger freeze, the review path, the rehearsal dispatch inputs and the pending-release disposition record this plan closes
provides:
  - v0.2.1 published from PR #75 (tag commit b93137f, tree b02c14b equal to the rehearsed tree) with 22 assets and a reconciled readback
  - docs/support/v0.2.1.md and the README, preview and release links to it
  - the owner-approved performance review for the exact v0.2.1 measurement (issue #122)
  - 16-DISPOSITIONS.json with the four release-linked rows and PR-78-92-SUPERSEDED closed against tag-bound receipts
  - PRs #78-#92 closed as superseded by #93
  - the post-tag recovery fixes #123, #124 and #125 and the gate fixes #118 and #120
affects: [phase-16-verification, phase-17, phase-19]
actuals:
  tokens: 14539
  tasks: 3
  commits: 6
commits: 6
plan_head_before: c26e3b67b626d9774daab69944c1c4ce84eaee48
plan_head_after: 113b98c03e88f20ea5f90d9b56a22d9999ab2666
tech-stack:
  added: []
  patterns:
    - A gate that reads GitHub objects is tested against the real object shape; an invented fixture hid a missing repository member until publication.
    - A retry reuses the bytes already attached to a draft and lets the downstream owner validators judge them, instead of regenerating per-run evidence that the never-overwrite guard must refuse.
    - A pre-merge rehearsal verifies a source-bound fuzz receipt; only the release verifies the hosted ci.yml-on-main binding.
key-files:
  created:
    - docs/support/v0.2.1.md
    - .planning/phases/GB-16-tune-up-and-v0-2-debt-closure/16-release-readback.json
    - .planning/phases/GB-16-tune-up-and-v0-2-debt-closure/16-pr-closures.json
    - .planning/phases/GB-16-tune-up-and-v0-2-debt-closure/16-nightly-asan-gate.json
    - .planning/phases/GB-16-tune-up-and-v0-2-debt-closure/16-perf-review-decision.json
    - .planning/phases/GB-16-tune-up-and-v0-2-debt-closure/continue.md
  modified:
    - .planning/phases/GB-16-tune-up-and-v0-2-debt-closure/16-DISPOSITIONS.json
    - .planning/context/DECISIONS.md
    - .planning/context/FUTURE-MILESTONES.md
    - tests/scripts/verify-support-ledger.py
    - tests/scripts/verify-v02-delivery.py
    - tests/scripts/verify-v02-fuzz.py
    - .github/scripts/verify-release-gates.sh
    - .github/scripts/verify-release-source-proof.py
    - .github/scripts/verify-workflow-policy.py
    - .github/scripts/produce-release-evidence.sh
    - .github/workflows/release-rehearsal.yml
    - .github/workflows/release.yml
key-decisions:
  - "D-112: the amendments, the owner-waived gap rounds (#116, #118, #120), the rehearsal-scope narrowing, the post-tag recovery round (#123, #124, #125), the window mechanics and the review history."
requirements-completed: ["TUNE-06"]
coverage:
  - id: R1
    description: "v0.2.1 is published from PR #75: the tag commit b93137f is the squash of the rehearsed head c6dc575 and has the same tree b02c14b."
    requirement: "TUNE-06"
    human_judgment: false
    verification:
      - kind: other
        ref: "16-release-readback.json: tag v0.2.1, tag_sha b93137f00d07b11dc74e40330e0ddf6029c0677d, tag_tree b02c14bbdc9be80b7aa6b6145cb8b89331388cca, is_draft false, published 2026-10-26T13:52:06Z; git rev-parse b93137f^{tree} equals c6dc575^{tree}"
        status: pass
  - id: R2
    description: "The published asset inventory reconciles: 22 assets whose ids, names and digests match the qualified inventory."
    requirement: "TUNE-06"
    human_judgment: false
    verification:
      - kind: other
        ref: "verify-published-release-assets.py read back the release assets: PASS published release asset IDs, names, and digests match the qualified inventory (16-release-readback.json reconciliation)"
        status: pass
  - id: R3
    description: "The exact-head rehearsal is green with the trusted judge, and the operator-dispatched nightly-asan run is green on the same head and tree."
    requirement: "TUNE-06"
    human_judgment: false
    verification:
      - kind: e2e
        ref: "release-rehearsal run 40257161612 (all 7 jobs success, judge job 121367397151) and nightly-asan run 40245698754 (asan-full-replay success), both at c6dc575 with tree b02c14b; 16-nightly-asan-gate.json"
        status: pass
  - id: R4
    description: "The performance review is the owner's receipt-bound decision for the exact measurement digest, copied from the owner comment by jq."
    requirement: "TUNE-06"
    human_judgment: false
    verification:
      - kind: other
        ref: "issue #122 comment 6406576530 (OWNER, body equal to the approval line for digest fb254880...a0cd); verify-v02-performance.py --apply-decision and --verify passed on 16-perf-review-decision.json"
        status: pass
  - id: R5
    description: "PRs #78-#92 are closed as superseded by #93 with one comment each; none changes src/ or include/."
    requirement: "TUNE-06"
    human_judgment: false
    verification:
      - kind: other
        ref: "16-pr-closures.json lists 15 CLOSED PRs with closed_at, comment_url and changed_paths; verify-v03-dispositions.py pr-closures rules"
        status: pass
  - id: R6
    description: "The dispositions record closes the four release-linked rows and PR-78-92-SUPERSEDED against tag-bound receipts read at a commit."
    requirement: "TUNE-06"
    human_judgment: false
    verification:
      - kind: unit
        ref: "python3 -I tests/scripts/verify-v03-dispositions.py --check .planning/phases/GB-16-tune-up-and-v0-2-debt-closure/16-DISPOSITIONS.json (rows=26 pending=0 closed=6 owner_accepted=7)"
        status: pass
      - kind: integration
        ref: "ctest -R '^(v03_dispositions|v03_dispositions_controls)$'"
        status: pass
  - id: R7
    description: "The gate fixes carry negative controls: attached retained-build sidecar (6 controls), source-bound rehearsal fuzz receipt (4 plus 3 delivery plus 4 policy controls), GH_REPO recovery from a non-git directory (3 cases), real-shaped check-run repository (9 controls) and retry reuse of attached evidence (3 policy controls)."
    requirement: "TUNE-06"
    human_judgment: false
    verification:
      - kind: unit
        ref: "python3 -I tests/scripts/verify-support-ledger.py --self-test; verify-v02-fuzz.py --self-test; verify-v02-delivery.py --self-test; verify-release-source-proof.py --self-test; verify-workflow-policy.py --self-test (266 negative controls); verify-release-gates.sh --self-test"
        status: pass
  - id: R8
    description: "The D-07 reading of TUNE-01 holds: completed-milestone records are never read from the live phases directory, and current-milestone live reads go only through GBB_LIVE_PHASES_DIR (see 16-01-SUMMARY.md)."
    requirement: "TUNE-01"
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest -R '^no_phase_paths$' (passed in every exact-head required-native run of the window PRs)"
        status: pass
  - id: R9
    description: "git diff --quiet v0.2.0 v0.2.1 -- include holds and the v0.2.0..v0.2.1 src delta is exactly the five planned files."
    requirement: "TUNE-06"
    human_judgment: false
    verification:
      - kind: other
        ref: "git diff --quiet ab301aa69b1f085050fd66bf7b1378863a0821f2 v0.2.1 -- include; git diff --name-only ab301aa v0.2.1 -- src lists gbb_accept.h, stepper.c, gabbaboy.c, gbb_accept_input.h and acceptance.c only"
        status: pass
duration: about two days wall clock, dominated by three owner review rounds and five hosted release runs
completed: 2026-10-26
status: complete
---

# Phase 16 Plan 07: Publish v0.2.1 and close the v0.2 release debt Summary

**v0.2.1 is published from PR #75 with an owner-approved performance review, a green exact-head rehearsal and nightly run, a reconciled 22-asset readback and PRs #78-#92 closed, after five gate defects found only by running the release path were fixed under owner waivers.**

Stage completed: Phase 16 execution (plans 16-01..16-07). Next stage: Phase 16 verification. Next command: `/gsd-verify-work 16`. Nothing auto-advances; both auto flags stay false. The boundary SHA is the squash commit of the boundary pull request that carries this file; the orchestrator records it as `boundary_sha` after the merge (a commit cannot contain its own SHA), then re-runs `verify-v03-dispositions.py --check ... --rev <that sha>`.

## Delivery state

- **Release:** tag `v0.2.1` at b93137f00d07b11dc74e40330e0ddf6029c0677d (squash of PR #75, head c6dc575b6a84cf51a56688948fce9241ba323400, tree b02c14bbdc9be80b7aa6b6145cb8b89331388cca), release id 423802899, published 2026-10-26T13:52:06Z by release-please run 40332345735 (a retry for the existing draft). The release notes carry the version token, the v0.2.1 ledger link, "No CGB game-level evidence exists.", "unsigned and not notarized", `+8.3%` and `tests/baseline/perf-attribution-v1.json`.
- **Evidence runs:** rehearsal 40257161612 (success, judge job 121367397151), nightly-asan 40245698754 (success), measurement run 40247741964 (median 118.29 percent, SD 1.77 percent, margin 0.63 percent), the attach job of the publishing run took 24 s (a recorded fact, D-112).
- **Review:** issue #122 approved (comment 6406576530); #117, #119 and #121 were superseded.
- **Closures:** #78-#92 closed with one comment each.
- **Main:** 113b98c; merged window PRs: #118, #120, #75, #123, #124, #125.

## Deviations from Plan

**1. [Rule 4 - owner amendments] No release-gates checker, receipts adapted.** The orchestrator amendments (D-112) replaced `verify-release-gates.py` and its CTests with `gh api`/jq checks and a recorded nightly run, kept the readback receipt, produced `16-pr-closures.json` because the merged checker needs it, and moved the ceiling and ledger re-citations to recorded facts.

**2. [Rule 1 - bugs on the release head, owner-waived gap rounds #118, #120, #116 before the window]**
- `verify-workflow-policy.py` replaced the literal `VERSION 0.2.0` in a control that no longer existed at 0.2.1, and the sidecar self-test mutants pinned version 0.2.0 (both on #75).
- The aggregate and delivery gate rejected every retained-build sidecar (#118) and demanded a hosted main run for a rehearsed branch commit, while the judge compared the receipt with the default branch HEAD (#120). Rehearsal-scope narrowing recorded as owner-accepted.

**3. [Rule 1 - post-tag defects, owner-approved recovery round]** #123 (attach job `gh repo view` in a non-git workspace), #124 (source-proof verifier required a check-run `repository` member GitHub does not return; it would also have blocked v0.2.0) and #125 (a retry's per-run corpus evidence was refused by the never-overwrite guard; the retry now reuses the evidence already attached). Four release-please runs were needed: 40259198302, 40263572284, 40267392726, 40332345735. The tag, the draft and its assets were never moved, deleted or replaced.

**4. [Rule 3] release-please regenerated #75 twice** after main pushes; the window edits were reapplied with merge commits and the rehearsal branch was fast-forwarded; no force-push anywhere.

**5. [Observation] Hand-inserted ledger block.** `docs/support/v0.2.1.md` needed the disclosed historical performance block that the adoption check requires; the generator does not render it (FUTURE-MILESTONES RM-028).

**6. [Observation] Wall-clock variance.** The same code measured +18.29 to +45.04 percent on hosted runners across runs; the owner approved the lowest-SD reading (RM-026, RM-029).

**Total deviations:** 6 (all recorded in D-112; owner waivers for the gap rounds and the recovery).

## Known Stubs

None.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: release-write | .github/workflows/release.yml | The attacher now reads evidence already on the draft on a retry; the block holds no write and the owner validators still judge those bytes (D-112, #125). |

## Self-Check: PASSED

- Receipts present: 16-release-readback.json, 16-pr-closures.json, 16-nightly-asan-gate.json, 16-perf-review-decision.json.
- Commits b93137f, 75d627c, 77ed0e6, c896855, 2ce7fee and 113b98c are ancestors of origin/main.
- `git rev-parse b93137f^{tree}` equals `git rev-parse c6dc575^{tree}`; the tag and draft were never edited.
- `.planning/config.json` and `.planning/milestone.lock` were never staged.

---
*Phase: 16-tune-up-and-v0-2-debt-closure*
*Completed: 2026-10-26*
