# Phase 16: Tune-up and v0.2 Debt Closure - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-24
**Phase:** 16-tune-up-and-v0-2-debt-closure

**Areas discussed:**
- Archive and phase-path lint
- Phase 8 verifiers
- Performance gate and attribution
- CI budget and planning-only lane
- v0.2.1 release path and planning hygiene
- Gap sweep

**Mode:** advisor fan-out with owner-delegated auto-follow (standing preference).
1. Five parallel researchers: archive/lint, perf gate, CI budget, release path, gap sweep.
2. Synthesis into a draft.
3. One adversarial review (3 blockers, 7 major, 8 minor findings, all applied).
4. Three owner questions for the choices that contradicted earlier decisions or needed owner authority.

---

## Performance debt (owner question)

| Option | Description | Selected |
|--------|-------------|----------|
| Accept, record, seed | The D-106 default. No `src/` change; the attribution receipt closes LIM-PERF-REVIEW; v0.2.1 notes disclose +8.3% against v0.2.0; the recovery items become seed RM-023 | ✓ |
| Fix 15.1 polling early-out | One extra `perf:` plan before the release | |
| Fix both hot spots | Also the Phase 7 mixer; needs audio-digest proof | |

**User's choice:** Accept, record, seed (CONTEXT D-13).

## v0.2.0 ledger drift (owner question; found by the adversarial review)

| Option | Description | Selected |
|--------|-------------|----------|
| Accept and pin both | Pin the tag blob `a542a5c…` and the working file `c47ff12…`; allow only the #93 appended block; record it as a disclosed exception to D-106 | ✓ |
| Revert to the tag bytes | Move the paragraph into the v0.2.1 ledger and change the adoption check | |

**User's choice:** Accept and pin both (CONTEXT D-29).

## TUNE-01 wording (owner question)

| Option | Description | Selected |
|--------|-------------|----------|
| Disclosed interpretation | REQUIREMENTS.md is unchanged; live reads go only through the allowlisted `GBB_LIVE_PHASES_DIR` | ✓ |
| Reword TUNE-01 | Edit REQUIREMENTS.md and annotate D-105 | |

**User's choice:** Disclosed interpretation (CONTEXT D-07).

---

## Auto-followed recommendations (owner-delegated)

### Ordering
Release-last (D-01) was chosen over release-first. Release-first would need two ledger regenerations and a split archive.

### Archive (D-05..D-10)
- Retarget frozen readers to `milestones/v0.2-phases` rather than freezing copies into `tests/data` or retiring them.
- Extract only the HDMA lane code.
- The lint covers all tracked text, with a count-pinned allowlist.

### Phase 8 verifiers (D-11, D-12)
- Six CTests, including wrong-boundary rejections.
- Tag the off-main boundary `96d5eec`.

### Performance gate (D-14..D-17)
- Proxy: cachegrind Ir. Rejected `perf stat` (unavailable on hosted runners) and an in-core counter (hot-path code without evidence).
- Baseline: v0.2.0 built in the same job, with a 1.10 Ir limit. Rejected D-22's 105% wall-clock style.
- Attribution is deterministic per commit.

### CI budget (D-18..D-23)
- A static `TIMEOUT` ratchet rather than wall-clock durations (D-102).
- A timeout ledger checked in `verify-workflow-policy.py`.
- A job-level classifier feeding the existing `required-native` aggregator. Rejected: workflow `paths-ignore` (it leaves checks Pending) and a branch-protection change.

### Release qualification (D-30)
- The adversarial review reversed the draft's "switch to the Ir gate" plan, because it would have weakened D-101.
- The existing receipt-bound reviewed-disposition path is used instead.

### Release window (D-31)
- Reordered after the review found that PR #75 has no checks and that `GITHUB_TOKEN` pushes start no workflows.
- The preface goes in the PR body, and version-bound commits are pushed under a user identity.

### Verification boundary (D-33)
The post-release disposition flip commit, so that success criterion 5 is point-in-time.

## Claude's Discretion
- Script names, CMake fragment layout and allowlist formats.
- The measured lint floor and the STATE bound.
- Further plan merging below 7.

## Deferred Ideas
- RM-023 perf recovery.
- A PPU-heavy perf workload.
- Planning-only classification for `fixture-repro`/`preview`.
- A single-aggregator branch protection (owner action).
- A `feat` title lint.
