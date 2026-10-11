---
phase: 07-dmg-game-acceptance-and-regression-baseline
plan: 16
subsystem: docs
tags: [documentation, decisions, support-ledger, exact-head-ci, handoff, privacy-check]

requires:
  - phase: 07-15
    provides: frozen DMG-CPU-B baseline ledger and exact-head CI evidence
  - phase: 07-04
    provides: Libbet reproduction script and dispatch-only workflow
provides:
  - docs/game-acceptance.md with Libbet scope, controls, evidence classes, limits and baseline usage
  - docs/support/unreleased.md D-37 support-ledger entry, not release-bound
  - DECISIONS D-030..D-048 and LESSONS GB-GAME-004..009 for every planning refinement
  - Phase boundary handoff naming /gsd-verify-work 7
affects: [phase 7 verification, phase 8, phase 15]

status: complete
actuals:
  tokens: 15500
  tasks: 3
  commits: 2
plan_head_before: 564b5a5d22c006e7d393cc7a58de23e689271e8b
plan_head_after: 23c0ffd7c1ab3149be1b96c8ba384acf5c655c48

tech-stack:
  added: []
  patterns:
    - "Pending support-ledger entries live in a non-version-named file that verify-support-ledger.py ignores"

key-files:
  created:
    - docs/game-acceptance.md
    - docs/support/unreleased.md
  modified:
    - docs/preview.md
    - .planning/context/DECISIONS.md
    - .planning/context/LESSONS.md
    - .planning/STATE.md
    - .planning/.continue-here.md

key-decisions:
  - "D-040: the macOS-only player smoke limitation lives in docs/support/unreleased.md, not in the release-bound v0.1.0 ledger"
  - "D-029 (shade-count relaxation of locked D-25) is flagged as pending owner confirmation in the decision row and in docs/game-acceptance.md"

requirements-completed: [GAME-01, GAME-02, GAME-03, EVID-01, EVID-02]

coverage:
  - id: D1
    description: "Acceptance scope, evidence classes, controls and limitations documented without overclaiming"
    requirement: GAME-02
    verification:
      - kind: other
        ref: "plan Task 1 verify command and eight acceptance greps (all pass); verify-support-ledger.py --self-test passes and still resolves docs/support/v0.1.0.md"
        status: pass
    human_judgment: false
  - id: D2
    description: "D-37 limitation recorded as a pending support-ledger entry; released v0.1.0 ledger untouched"
    requirement: GAME-03
    verification:
      - kind: other
        ref: "git diff --quiet main...HEAD -- docs/support/v0.1.0.md"
        status: pass
    human_judgment: false
  - id: D3
    description: "Every planning refinement recorded as a dated DECISIONS row; lessons recorded"
    requirement: EVID-01
    verification:
      - kind: other
        ref: "grep counts on DECISIONS.md and LESSONS.md (Phase 7 rows 3 to 22, owner rows 0 to 2, HALTED_IDLE present)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Exact-head required checks green at the evidence head; phase PR ready for review, not merged"
    requirement: EVID-02
    verification:
      - kind: ci
        ref: "run 38106136572 at 23c0ffd, eight required jobs success"
        status: pass
    human_judgment: false

duration: 100min
completed: 2026-10-11
---

# Phase 7 Plan 16: Phase 7 close-out documentation and handoff Summary

**Honest acceptance documentation, a non-release-bound support-ledger entry, 19 dated decision rows and 6 lessons, with all eight required jobs green at evidence head 23c0ffd and the route to `/gsd-verify-work 7` persisted.**

## Performance

- **Duration:** about 100 min, of which about 25 min was waiting for the exact-head CI run (estimate; not measured to the second)
- **Completed:** 2026-10-11
- **Tasks:** 3
- **Files modified:** 7 (2 created)

## Accomplishments

- `docs/game-acceptance.md` states the scope (one game, DMG-CPU-B software profile, not compatibility, not hardware), asset rights as an inference, the predicate and its conditions, the calibrated PCM thresholds (2048 peak-to-peak, 4800 changes; observed 20290 and 164822, no-input control 0 and 0), the controls with the D-14 split between the raw exit 1 `reason=predicate-not-reached` assertion and the D-22 `status=xfail` mapping, the evidence classes, the packaged-player smoke, limitations and baseline usage. `docs/preview.md` links to it.
- Honest-documentation items reflected as written, each checked against the repository and earlier summaries:
  - D-029 relaxed locked D-25 (at least 2 shades for `title` and `play_start`, at least 3 for `mid` and `hit`); the DECISIONS row and the doc flag it as pending owner confirmation. It remains an open owner item.
  - The 07-03 `audio_saturation` assertion was not shown to fail against the pre-fix core (stated in the doc, D-043 and GB-GAME-009).
  - The Mooneye `daa` LD B,B frame is all shade 0; recorded as an observation (D-042), and `mooneye.daa.frame` guards "still blank" only.
  - The Libbet reproduction script was byte-identical on macOS arm64 only. `gh run list --workflow libbet-repro.yml` returns HTTP 404 (workflow not on the default branch), so no hosted run exists and the Linux path and the workflow are unverified (D-039).
  - No CTest covers `frame-digest@t`; `grep -rn 'frame-digest@t' tests` has no match.
- `docs/support/unreleased.md` carries the D-37 player-platform limitation and Libbet scope. `verify-support-ledger.py --self-test` passes and the working-tree ledger still resolves to `docs/support/v0.1.0.md`; the released ledger has no diff against `main`.
- DECISIONS D-030..D-048 cover each refinement named in the plan, with D-031 and D-032 as `Adopted (owner, 2026-10-10)`. LESSONS GB-GAME-004..009 cover the ExpectedTests directory scope, continuable stop reasons, master-timeline frame boundaries, the P6 size versus the 64 KiB cap, declared exclusion counts and stating unshown-to-fail evidence.

## Task Commits

1. **Task 1: acceptance doc, support-ledger entry, preview link** - `20bf999` (docs)
2. **Task 2: decision and lesson records** - `23c0ffd` (docs)
3. **Task 3: privacy check, CI read, triage, handoff** - no tracked code change; handoff files are in the plan metadata commits below.

**Plan metadata:** `4d7c06a` (summary), `baa0958` (handoff: STATE, ROADMAP, REQUIREMENTS, .continue-here).

## Privacy check

Over `git diff --name-only --diff-filter=d main...HEAD` excluding planning `*-PLAN.md` (97 files): zero matches for `/(Users|home)/<name>/` and zero non-noreply email addresses. No exception was needed.

## Exact-head CI evidence

- **Evidence head** `23c0ffd7c1ab3149be1b96c8ba384acf5c655c48`, run 38106136572 (https://github.com/szTheory/gabbaboy/actions/runs/38106136572), pull_request, attempt 1. `wait-exact-head-ci.py` with all eight `--require` options printed `PASS run_id=38106136572 run_attempt=1`. Per-job conclusions: native-linux-x64 success, native-macos-arm64 success, native-windows-x64 success, linux-asan-ubsan success, cmake-floor-3.25.3 success, player-gate success, macos-player-package success, required-native success.
- Log lines at that head: `baseline status=pass` and `baseline junit=ok inventory=core names=258` in the three native jobs; `baseline junit=ok inventory=player names=55` in macos-player-package.
- Local before push: full CTest 258/258 passed; `bash tests/scripts/verify-dmg-baseline.sh` printed `baseline status=pass`.
- Fix cycles used: 0 of 3.
- The handoff commits that follow are docs-only (planning files). Their heads are checked separately; see Handoff heads.

## Phase-boundary triage

`gh issue list --state open`: no open issues (no access failure). `gh pr list --state open`: one, #63 "Phase 7: DMG game acceptance and regression baseline" (this phase's draft PR). Dispositions: no issues, no action; PR #63 is marked ready for review and left unmerged for the orchestrator after phase verification. Open owner items to carry: D-029 confirmation; the first hosted `libbet-repro` dispatch after the workflow reaches the default branch; `linux-asan-ubsan` headroom (20 min 6 s of 30 on the 07-11 runs, see 07-11 summary).

## Deviations from Plan

**1. [Rule 3 - Format] Handoff commit scope**
- The plan asks that the handoff commit list only `.planning/STATE.md` and `.planning/.continue-here.md`. The executor close-out order (SUMMARY commit, then STATE and ROADMAP) adds this SUMMARY and `ROADMAP.md` to the docs-only post-evidence commits. All commits after the evidence head touch only `.planning/` files; verified with `git diff --name-only 23c0ffd..HEAD`.

**2. [Rule 3 - Sequencing] Handoff head recorded by an addendum commit**
- A commit cannot name its own SHA, so the handoff head's exact-head result is appended to this SUMMARY in a final docs-only commit, whose own head is read in turn and reported in the completion message.

**3. Task 3 wait command:** the plan's verify command omits the mandatory `--require` options of `wait-exact-head-ci.py`; all eight were supplied.

**Total deviations:** 3 (all procedural). **Impact:** none on content.

## Issues Encountered

None.

## Known Stubs

None.

## Threat Flags

None. No new network, auth, file-access or schema surface; documentation and planning records only (T-07-31 privacy check clean; T-07-32 only exact-head results counted; T-07-33 limits stated).

## Handoff heads

- **Handoff head** `baa09585275a665f90d27346b8acc7279cb7283f` (STATE.md, .continue-here.md, ROADMAP.md, REQUIREMENTS.md, state.json and this SUMMARY; planning files only), run 38107525049 (https://github.com/szTheory/gabbaboy/actions/runs/38107525049), attempt 1, `wait-exact-head-ci.py` PASS. Per-job conclusions: native-linux-x64 success, native-macos-arm64 success, native-windows-x64 success, linux-asan-ubsan success, cmake-floor-3.25.3 success, player-gate success, macos-player-package success, required-native success.
- The commit that adds this addendum is a further docs-only head; its run is reported in the completion message and the PR body, not here, to avoid another head.
- Requirements GAME-01..03 and EVID-01..02 were marked complete in REQUIREMENTS.md by the close-out command; Phase 7 verification (`/gsd-verify-work 7`) has not run and remains the gate.

## Self-Check: PASSED

- Files exist: docs/game-acceptance.md, docs/support/unreleased.md, docs/preview.md link, DECISIONS and LESSONS rows.
- Commits 20bf999 and 23c0ffd are ancestors of HEAD.
- Plan acceptance greps and the Task 1 verify command pass; `git diff --quiet main...HEAD -- docs/support/v0.1.0.md` exits 0.
