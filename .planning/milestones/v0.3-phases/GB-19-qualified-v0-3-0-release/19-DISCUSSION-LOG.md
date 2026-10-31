# Phase 19: Qualified v0.3.0 Release - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-29
**Phase:** 19-qualified-v0-3-0-release

**Areas discussed:**
- A. Entry blockers and review leftovers
- B. Version-PR, rehearsal, tag and post-tag choreography
- C. v0.3.0 support-ledger scoping
- D. Tag-bound receipts, perf gate and readback
- G. Gap sweep (cross-cutting, siblings, external practice)

**Method:** The owner re-pasted the standing fan-out instruction (see the [[discuss-fanout-auto-follow]] memory), which this log treats as confirmation. Five parallel advisor tracks ran read-only against `origin/main` `f80bdf54`. They covered these lenses:
- release engineering;
- CI and DevOps;
- supply-chain security;
- QA and negative controls;
- technical writing and product honesty;
- the embedder;
- perf;
- emulator ecosystem practice.

The tracks drew on these sources:
- GitHub immutable releases;
- release-please docs;
- savestate-compatibility practice from Dolphin, SameBoy and mGBA;
- sibling lessons from muhtari, cogmaster and nesturbator.

An independent adversarial review then checked the merged draft against the code. It found 2 blockers, 8 majors and 7 minors, and all were folded in. The recommendations were adopted without per-question prompts.

---

## A. Entry blockers

| Item | Options considered | Adopted |
|---|---|---|
| RM-027 | (a) tree-equality citation form; (b) raise the expiry to 0.3.0; (c) cite post-tag runs | (a), made general: `tree_equal_sha` on main plus `cited_tree`, the online check by API tree, and branch retention. (b) defeats the blocker. (c) is impossible because the judge needs the rows before the tag |
| candidate-performance | (a) leave the stale citation; (b) a new one-key `release_bound` expiring above 0.3.0 (the track A recommendation); (c) cite the predecessor job name | (c). The adversarial review showed that run 40332345735 has the predecessor job green. (b) amends D-110 and contradicts "refuses a seventh row" |
| Rehearsal `performance` row | Dispatch a rehearsal run on main | Rejected: corpus, package and judge fail on `--ref main`. Cite the predecessor job of 40257161612 instead |
| WR-C03 | (a) dispatch the dry run and re-cite; (b) add a CTest that parses REJECT lines and allows a pending set | (a). (b) rests on a false fact: the exit code is 1, not 0. The first Reject stops the run, so a pending-set filter hides later rules. A permanent CTest would outlaw development provisional rows |
| state_boundary | Edit it together with the row removal | Do not edit it. It pins the Phase 16 boundary commit `d53ec9c` point-in-time |
| RM-031 | (a) rename executables only; (b) rename the CTests too | (a). (b) churns the inventory and budget |

## A2. Review leftovers

| Item | Disposition |
|---|---|
| WR-C04 | Fix: the checker comes from the base commit, with no fallback (a fallback would be a bypass) |
| IN-05, IN-08, IN-07, IN-02 | Fold into 19-02 and the docs |
| WR-A05 + IN-01 | Include, with the range predicate moved into `state_validate`. The draft's `assert`-on-return was rejected because it does nothing in NDEBUG and leaves partial mutation. First item cut if the plan overruns |
| IN-03/04/06 | Defer to RM-024 |
| WR-C05 | Already on main (`f4082a65`; the draft cited phase-branch `f2ce8e7`) |

## B. Choreography

| Question | Options | Adopted |
|---|---|---|
| Ordering | (a) single main push then freeze; (b) fixes ride the version PR; (c) keep landing on main | (a) plus a synthetic 0.3.0 pre-flight. (b) is used only for content that needs the bump. (c) never |
| #131 | Reuse it, or close and regenerate | Reuse; untouched until PR A merges |
| Window record vs tree equality | (a) a one-path tree allowance in the judges; (b) a second rehearsal at W | (b). The trust-path judges keep exact tree equality. The record names R1 as the review-time run; R2 is release-binding; R2 red refuses the release |
| SC1 enforcement time | Post-tag only (draft) | Rejected by the adversarial review as blocker 2. A new pre-tag `pull_request` gate runs on the version PR, and the post-tag check is kept as defence in depth |
| "Postdates the tag" field | Run `updated_at`; tag committer date; draft `created_at`; job `completed_at` of the pinned attempt | `completed_at` of the pinned attempt vs `merged_at`. `updated_at` is not documented as immutable. Committer dates can be forged. The draft is created after the merge |
| Post-tag failures | Fix on main and retry; delete or recreate the tag; cut v0.3.1 | Fix on main and retry, find-all-then-fix-once in the single gap slot. A defective tagged tree goes to the owner. Deleting or recreating is forbidden |
| `bump-minor-pre-major` | Add it before the window | Deferred: it is a managed window input and #131 already computes 0.3.0 |
| Immutable releases | Enable before the tag (track B); leave off (tracks D and G) | Leave off for v0.3.0, because it is an unrehearsed change to the publish path. It is an owner option for v0.4 |

## C. Support ledger

| Question | Options | Adopted |
|---|---|---|
| Form | (A) hand prose with phrase checks; (B) a structured claims file rendered by the generator; (C) fully derived | (B) with C-style derived cross-checks. Hand prose already fails the fixed point |
| Renderer | Edit v2 in place; copy to v3 | Copy to v3, so the v0.2.x fixed points stay exact |
| Sidecar schema | Bump to 3; keep 2 | Keep 2 if possible, binding the claims through `ledger_blob`. Otherwise 19-05 owns the gate and replay changes (adversarial major 9) |
| Release notes | Ledger link only; required sentences | Required sentences plus forbidden patterns |

## D. Receipts

| Question | Options | Adopted |
|---|---|---|
| `v02-*` names | Keep with a note; rename; aliases | Keep with a note; rename in v0.4 |
| Perf-gate receipt | A new asset and job; fold into the `candidate-fuzz` trusted reader | Fold in. A new job would need an uncitable ledger row and be post-tag-only code (adversarial major 10) |
| Host smoke on shipped bytes | Release candidate only; rehearsal package plus candidate | Both. The rehearsal run makes it pre-tag |
| Readback | A new checker; extend the `verify-v03-dispositions.py` schema | Extend (adversarial minor 12) |
| Ir baseline | Keep v0.2.0; move to v0.2.1 | Keep. Moving it resets headroom and hides cumulative growth |

## G. Gap sweep findings adopted

- The active window record would judge future version PRs. It gets a tree-only rule (adversarial blocker 1 replaced a tag-reading rule) and is reset in PR B.
- The stale `## Unreleased` block in the CHANGELOG, plus a first-heading check.
- Release-notes content and the state-format warning.
- Stale v0.2 docs.
- The version-bump pre-flight, including the hand-authored `release-change` row.
- Host-contract smoke on shipped bytes.
- Non-releasable PR titles.
- Branch hygiene.
- Extending the privacy scan to readback JSON.
- A lifecycle replay delta audit (about 4.1k lines changed since v0.2.1).

## Deferred

See CONTEXT.md `<deferred>`.
