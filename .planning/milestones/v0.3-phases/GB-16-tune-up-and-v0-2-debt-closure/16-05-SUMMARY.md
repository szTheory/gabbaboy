---
phase: 16-tune-up-and-v0-2-debt-closure
plan: "05"
subsystem: planning-hygiene
tags: [phase8-boundary-tag, phase8-verifiers, plan-cap, lessons-ids, state-size, playstead-docs, tune-02, tune-05]
requires:
  - phase: 16-04
    provides: the planning label and planning-only lane, so every test added here is planning-labelled and runs on an unbuilt tree
provides:
  - the annotated tag historical/phase-08-boundary on origin, peeling to 96d5eec977bee99a0629499b89c737415e24184c
  - --boundary REV (default historical/phase-08-boundary) on both Phase 8 verifiers, resolved once and failing closed
  - tests/cmake/hygiene.cmake with six Phase 8 CTests and five hygiene CTests
  - verify-planning-hygiene.py with plan-cap, lessons-ids, state-size and playstead-docs checks and a 43-control self-test
  - .planning/milestones/v0.2-STATE-ARCHIVE.md and a STATE.md trimmed from 649 to 90 lines
affects: [16-06, 16-07]
actuals:
  tokens: 52000
  tasks: 3
  commits: 3
commits: 3
plan_head_before: 6e99a953ca9a773b8c501df940a1195661db7b1a
plan_head_after: 1ed7dda74f65aea6a895e2bba78d26e7e82a9449
tech-stack:
  added: []
  patterns:
    - A verifier whose input is a past commit resolves a named revision once to a commit id and never falls back to a literal SHA; an unreadable revision and a wrong-but-readable one print different messages, and each CTest forbids the other class.
    - Hygiene checks are pure functions returning (summary, errors) with stable error-code prefixes, so a control pins the failure class and size bounds are exercised on generated fixtures, never on the live file.
key-files:
  created:
    - tests/scripts/verify-planning-hygiene.py
    - tests/cmake/hygiene.cmake
    - tests/data/planning-hygiene/roadmap-over-cap.md
    - tests/data/planning-hygiene/lessons-duplicates.md
    - .planning/milestones/v0.2-STATE-ARCHIVE.md
  modified:
    - tests/scripts/verify-phase8-closure-contract.py
    - tests/scripts/verify-phase8-player-contract.py
    - tests/cmake/areas.cmake
    - tests/expected-tests.txt
    - .planning/context/LESSONS.md
    - .planning/STATE.md
    - .planning/research/PRECEDENT.md
    - .planning/research/v0.3/SIBLING-YOUNGER-CORES.md
    - README.md
    - docs/native-integration.md
key-decisions:
  - "STATE_MAX_BYTES 40960 and STATE_MAX_LINES 250, the plan's ceilings, sized from the measured Phase 15 and 15.1 growth."
  - "The closure self-test minimum is 160 rather than 157, because the two new unreadable-boundary controls raise the count to 160."
requirements-completed: ["TUNE-02", "TUNE-05"]
coverage:
  - id: D1
    description: "The annotated tag historical/phase-08-boundary is on origin and peels to 96d5eec977bee99a0629499b89c737415e24184c before any CI run of the Phase 8 CTests."
    requirement: "TUNE-02"
    human_judgment: false
    verification:
      - kind: other
        ref: "git ls-remote origin refs/tags/historical/phase-08-boundary and its peeled ref: tag object b4a189e45f9bdffbdc3f2cd07f74679f17068dad peeling to 96d5eec977bee99a0629499b89c737415e24184c"
        status: pass
  - id: D2
    description: "Both Phase 8 verifiers take --boundary, resolve it once with rev-parse, fail closed with a distinct message on an empty, option-shaped or missing revision with no SHA fallback, and report a wrong-but-readable boundary (v0.2.0) as a clause miss."
    requirement: "TUNE-02"
    human_judgment: false
    verification:
      - kind: unit
        ref: "python3 -I tests/scripts/verify-phase8-closure-contract.py --self-test"
        status: pass
      - kind: unit
        ref: "python3 -I tests/scripts/verify-phase8-player-contract.py --self-test"
        status: pass
      - kind: integration
        ref: "ctest --test-dir build -R '^phase8_(closure|player)_contract' (6 of 6)"
        status: pass
  - id: D3
    description: "The six Phase 8 CTests run through expect_exit.cmake with the planning label, the self-test enforces rejected_controls of at least 160, and the wrong-boundary tests forbid the unreadable-boundary message."
    requirement: "TUNE-02"
    human_judgment: false
    verification:
      - kind: e2e
        ref: "PR 112 head 1ed7dda: ci pull_request run 40209514947 and ci push run 40209512854 concluded success on every full job"
        status: pass
      - kind: unit
        ref: "python3 -I tests/scripts/verify-no-phase-paths.py --check"
        status: pass
  - id: D4
    description: "Plan-cap, LESSONS-id and STATE-size checks reject an over-cap phase directory, a missing cap line, cap 13, a cap sum of 41, duplicate and vacuous LESSONS ids and an oversized STATE fixture, and accept the boundary values; the live files pass."
    requirement: "TUNE-05"
    human_judgment: false
    verification:
      - kind: unit
        ref: "python3 -I tests/scripts/verify-planning-hygiene.py --self-test"
        status: pass
      - kind: integration
        ref: "ctest --test-dir build -R '^(plan_cap|lessons_unique_ids|state_size|planning_hygiene_controls)$'"
        status: pass
  - id: D5
    description: "LESSONS.md has each of GB-FIXTURE-003, GB-FIXTURE-004 and GB-TEST-007 once, STATE.md keeps its frontmatter and every kept heading with the historical blocks verbatim in v0.2-STATE-ARCHIVE.md."
    requirement: "TUNE-05"
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build -R '^(lessons_unique_ids|state_size)$'"
        status: pass
      - kind: other
        ref: "heading survival loop over STATE.md and the archive from the task 2 verify command"
        status: pass
  - id: D6
    description: "README, docs/native-integration.md and PRECEDENT.md state GB, GBC and GBA through mGBA 0.10.5 on Playstead main 234bd45b21 as process adapters, keep both required adoption sentences, and the docs check rejects the stale pin, GBA/mGBA and the current-tense 1de3e95 sentences."
    requirement: "TUNE-05"
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build -R '^(playstead_docs|v02_adoption_docs|v02_adoption_docs_controls)$'"
        status: pass
  - id: D7
    description: "The full suite passes with the new tests and src and include are unchanged against the plan base."
    requirement: "TUNE-05"
    human_judgment: false
    verification:
      - kind: integration
        ref: "cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error (1227 of 1227)"
        status: pass
      - kind: other
        ref: "git diff --quiet 6e99a953ca9a773b8c501df940a1195661db7b1a HEAD -- src include"
        status: pass
      - kind: unit
        ref: "python3 .github/scripts/verify-workflow-policy.py --check"
        status: pass
duration: about 1h 45m including hosted CI waits
completed: 2026-10-25
status: complete
---

# Phase 16 Plan 05: Phase 8 verifiers in CTest and planning hygiene Summary

**The Phase 8 contract verifiers now run in CTest against a durable annotated boundary tag with fail-closed `--boundary`, and plan caps, LESSONS ids, STATE.md size and the Playstead statements are machine-checked, with the renumbered ids, the archived STATE blocks and the corrected docs in place.**

## Delivery state

- **PR A:** https://github.com/szTheory/gabbaboy/pull/112, final head `1ed7dda74f65aea6a895e2bba78d26e7e82a9449`, branch `gsd/phase-16-05-boundary-tag-and-planning-hygiene`. `gh pr view` reported mergeStateStatus CLEAN; every check passed and none failed. Squash-merge is the orchestrator's step.
- **Exact-head runs on 1ed7dda:** ci pull_request 40209514947, ci push 40209512854, fixture-repro pull_request 40209514926, fixture-repro push 40209512727, preview-package-smoke pull_request 40209514930. All concluded success. The only skipped jobs are `planning-checks` (both ci runs, kind=full) and `macos-player-package` (ci push, by design); the ci pull_request run has 12 successes and the one skipped `planning-checks`.
- **Tag push (D-12):** `git ls-remote origin refs/tags/historical/phase-08-boundary refs/tags/historical/phase-08-boundary^{}` printed `b4a189e45f9bdffbdc3f2cd07f74679f17068dad refs/tags/historical/phase-08-boundary` and `96d5eec977bee99a0629499b89c737415e24184c refs/tags/historical/phase-08-boundary^{}`. The tag push triggered ci run 40208774436 and fixture-repro run 40208774447 at the old commit 96d5eec (ci success). They are not evidence for this plan.
- **Fix rounds:** none used (0 of 2).
- **Branch name deviation:** see deviation 1.

## Accomplishments

- `--boundary REV` on both verifiers resolves `REV^{commit}` once with `git rev-parse --verify`, rejects empty and dash-leading values, and prints `phase8-closure-contract FAIL: boundary unreadable: REV` or `phase8-player-contract: FAIL: boundary unreadable: REV` with no SHA fallback. The closure verifier's OLD (`5673bed`) reads and PHASE constant are untouched, so `verify-no-phase-paths.py --check` passes unchanged (`files=492 allowlisted=6` locally).
- **Wrong-boundary outputs observed** with `--boundary v0.2.0`: the closure verifier prints `phase8-closure-contract FAIL docs/cartridge-and-saves.md: missing historical clause 'Player battery persistence applies only to MBC1 type ...'` and further clause misses, exit 1; the player verifier prints `phase8-player-contract: FAIL: startup status branch does not set the pinned warning copy`, exit 1. Unreadable runs (`''`, `refs/tags/nope`) print the `boundary unreadable` line. The closure CTest forbids `boundary unreadable|cannot read` and the player CTest forbids `boundary unreadable`.
- A path absent at a readable boundary now reads as empty so the failure is a clause miss; `old:` reads still fail with `cannot read`.
- Closure self-test: `rejected_controls=160` (157 plus three unreadable-boundary controls). Player self-test gained an unreadable-boundary control.
- `tests/cmake/hygiene.cmake` registers `phase8_closure_contract`, `phase8_closure_contract_selftest`, `phase8_closure_contract_wrong_boundary`, `phase8_player_contract`, `phase8_player_contract_selftest`, `phase8_player_contract_wrong_boundary`, `plan_cap`, `lessons_unique_ids`, `state_size`, `planning_hygiene_controls` and `playstead_docs`, all LABELS planning, running from the source directory.
- `verify-planning-hygiene.py`: 43 self-test controls. Plan-cap parses `### Phase N:` under `## Phase Details`, counts `NN-NN-PLAN.md` in `GB-N-*`, handles decimal phases against their parent, and rejects exceeded, missing, too-large, summed-above-40, orphan-directory, duplicate-cap, vacuous and missing-directory cases (live: `plan-cap pass phases=4 plans=7`). LESSONS ids compare exact tokens, name every duplicate line and keep the earliest (live: `lessons-ids pass ids=96`). State size counts raw bytes and newline characters.
- Renumbered ids: line 225 to GB-FIXTURE-003, line 846 to GB-FIXTURE-004, line 234 to GB-TEST-007, the line-294 inbound reference to GB-TEST-007, with "renumbered in Phase 16" notes at XFER-016 and in `SIBLING-YOUNGER-CORES.md`.

## STATE.md trim and measured growth

| Point | Bytes | Lines |
|-------|-------|-------|
| end of Phase 14 (c771b1b) | 60,812 | 536 |
| end of Phase 15 (04fe3c6) | 65,092 | 569 |
| end of Phase 15.1 (5356d38) | 90,052 | 675 |
| before this plan (6e99a95) | 78,399 | 649 |
| after the trim | 4,944 | 90 |

Phases 15 and 15.1 together added 29,240 bytes and 139 lines (about 14.6 KB and 70 lines per phase; 15.1 alone was +24,960 and +106). The bounds are `STATE_MAX_BYTES = 40960` and `STATE_MAX_LINES = 250`, the plan's ceilings: about 35 KB and 160 lines of room, one milestone at the Phase 15 rate and a trip wire two phases in at the Phase 15.1 rate. The archive holds the five Historical Phase subsections, Prior stage receipts, the whole Performance Metrics section, the Decisions body and the Blockers/Concerns bullets verbatim, with a header naming source commit 458fc71 (the branch head before the trim, descended from origin/main 6e99a95). The live frontmatter and Current Position (lines 1 to 43) are byte-identical to before.

## Task Commits

1. **Task 1: Phase 8 boundary tag, --boundary, six CTests** - `458fc71` (test)
2. **Task 2: plan-cap, LESSONS-id and STATE-size checks, renumber, trim** - `13241c0` (test)
3. **Task 3: Playstead statements and docs check** - `1ed7dda` (docs)

**Plan metadata:** this SUMMARY, delivered as PR B.

## Deviations from Plan

**1. [Rule 3 - Blocking] PR branch name.** The remote `gsd/phase-16-tune-up-and-v0-2-debt-closure` still held the pre-squash commit 4cedecc of the merged 16-04 PR B, so a push needed a force push, which the permission system denied. I pushed the same commits to `gsd/phase-16-05-boundary-tag-and-planning-hygiene` instead and opened PR 112 from it. The local branch still tracks no remote; the stale remote branch was not touched.

**2. [Rule 2 - Missing critical] Closure minimum 160, not 157.** The new unreadable-boundary controls raise the count to 160, and a minimum of 157 would let three dropped controls pass. `phase8_closure_contract_selftest` pins 160. Needs no ratification.

**3. [Rule 2 - Missing critical] Wrong-boundary CTests forbid the other failure class.** Both wrong-boundary tests add `GBB_FORBID_REGEX` so an unreadable boundary cannot pass for a clause miss (the player regex `phase8-player-contract: FAIL` alone matches both). Also, the closure verifier now treats a path absent at a readable boundary as empty (a clause miss) rather than a read error, as the plan allowed.

**4. [Rule 2 - Missing critical] Extra stale phrases.** `playstead-docs` also rejects `current continuation capability refusal` and `No current in-game continuation pass` (the other current-tense 1de3e95 statements in the PRECEDENT table row) and requires `mGBA 0.10.5` in all three files, beyond the plan's three rejects and the pin.

**5. [Rule 3 - Blocking] Files outside files_modified.** `.planning/research/v0.3/SIBLING-YOUNGER-CORES.md` gained its "renumbered in Phase 16" note, which the plan's action requires but the file list omits. Phase 16 rows in Performance Metrics and the [Phase 16] Decisions bullets that the runtime had appended to STATE.md were archived with the rest of those sections as the plan specifies; the runtime recreates `## Performance Metrics` or skips it when it records the next plan, and the plan's verify requires the heading be absent from the live file.

**6. [Minor] Self-test fixtures.** Only two fixture files are committed (`roadmap-over-cap.md`, `lessons-duplicates.md`); the phase directories, near-collision, zero-id, bound-edge and Playstead fixtures are generated inside the self-test in temporary directories so they cannot drift.

**Total deviations:** 6 (1 blocking, 3 missing-critical, 1 blocking file-list, 1 minor). **Impact on plan:** none on scope; no src/ or include/ change; `.planning/config.json` and `.planning/milestone.lock` were never staged.

## Known Stubs

None.

## Threat Flags

None. The new tests only read tracked files and `git show` output; no network, auth or write path was added. The tag is annotated, verified with `git ls-remote` and pinned by peel in the SUMMARY (T-16-14), and the STATE blocks are verbatim in the archive (T-16-16).

## Issues Encountered

- The remote tag push and the PR branch push are the only remote git actions; the Phase 8 branch and every other branch were left alone (T-16-15). The denied force push changed nothing.
- `.planning/config.json` carries an uncommitted owner edit and was left untouched; STATE.md was edited only for the plan-specified trim and ROADMAP.md and REQUIREMENTS.md were not edited.

## Facts for 16-06 and 16-07

- `ci-timeouts.json` rows for `changes` and `planning-checks` are still provisional (16-04). This PR's runs are full runs (it touches tests/), so they re-cite neither job; the planning-only PR B main push run is the citation for `planning-checks`.
- The four CI shards ran in parallel: native-linux-x64 6 to 11 min, native-macos-arm64 7 to 9 min, native-windows-x64 about 12 min, linux-asan-ubsan-acceptance about 18.5 min, cmake-floor 14 to 19 min. The whole check set finished in about 20 minutes.
- `historical/phase-08-boundary` must survive 16-07's PR and branch cleanup: delete neither the tag nor `gsd/phase-08-cartridge-seam-mbc5-and-mbc2`.
- CI checkouts use fetch-depth 0, which fetches the tag and the off-main commit 96d5eec; the Phase 8 tests passed on all three OS legs and both sanitizer legs.
- The phases-dir argument for `plan_cap` is `${GBB_LIVE_PHASES_DIR}`; Phase 16 holds 7 plans against its cap of 8, so 16-06 and 16-07 add none. A gap plan would take the eighth slot.
- STATE.md now has no `## Performance Metrics` heading; if `state.record-metric` fails or recreates it, the section is still within the size bound.

## Self-Check: PASSED

- Created files present: verify-planning-hygiene.py, hygiene.cmake, tests/data/planning-hygiene/, v0.2-STATE-ARCHIVE.md.
- Commits 458fc71, 13241c0 and 1ed7dda are ancestors of HEAD; PR 112 head 1ed7dda was clean with all checks passing.
- The remote tag peels to 96d5eec977bee99a0629499b89c737415e24184c.

---
*Phase: 16-tune-up-and-v0-2-debt-closure*
*Completed: 2026-10-25*
