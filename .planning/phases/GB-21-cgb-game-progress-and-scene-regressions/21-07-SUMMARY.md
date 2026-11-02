---
phase: GB-21-cgb-game-progress-and-scene-regressions
plan: "07"
subsystem: testing
tags: [CGB, native acceptance, candidate evidence, CTest]
requires:
  - phase: GB-21-cgb-game-progress-and-scene-regressions
    provides: Native CGB progress, ordered fixture-admission records, and scene-report contracts from Plans 21-01 through 21-06.
provides:
  - A source-bound composition checker and mutation controls for the two candidate outcomes, original harness result, and scene-workflow claims.
  - Current Phase 21 outcome documentation, qualification evidence, and an explicit phase-boundary handoff.
affects: [Phase 22 composition evidence, Phase 23 release evidence]
actuals:
  tokens: 31682
  tasks: 2
  commits: 21
tech-stack:
  added: []
  patterns:
    - Compose existing Python-standard-library checkers using one immutable full source revision.
    - Reject unsupported evidence claims with content-caused mutation controls.
key-files:
  created:
    - tests/scripts/verify-cgb-game-evidence.py
    - tests/cmake/game-evidence.cmake
  modified:
    - docs/game-acceptance.md
    - docs/cgb-profile.md
    - docs/support/unreleased.md
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - tests/data/state-forks.json
    - tests/scripts/verify-cgb-candidates.py
    - tests/scripts/verify-cgb-progress.py
    - tests/scripts/verify-fixture-admission.py
    - tests/scripts/verify-scene-report.py
    - .planning/context/LESSONS.md
    - .planning/phases/GB-21-cgb-game-progress-and-scene-regressions/21-VALIDATION.md
    - .planning/phases/GB-21-cgb-game-progress-and-scene-regressions/21-07-REVIEW.md
    - .planning/phases/GB-21-cgb-game-progress-and-scene-regressions/deferred-items.md
    - .planning/phases/GB-21-cgb-game-progress-and-scene-regressions/.continue-here.md
key-decisions:
  - "Both named candidates remain rights/source-scope no-go outcomes; no license prohibition is inferred."
  - "FIXT-01 remains pending because neither game's build, ROM bytes, cartridge header, or native mode was observed."
  - "The original project-authored CGB ROM is harness evidence only; its repeatable RGB555/PCM digests do not establish accuracy or real-game progress."
  - "Keep both descriptor-less plan prohibitions visible and unresolved as required by the plan."
patterns-established:
  - "A result receipt binds candidate facts, harness evidence, runner identity, and documentation to one full source revision."
  - "Claim mutations target each candidate/license statement independently so one valid claim cannot mask an unsupported one."
requirements-completed: [GAME-01, GAME-02, FEED-01]
coverage:
  - id: D1
    description: Source-bound CGB outcome composes current candidate facts and the original harness result, rejecting missing evidence and unsupported game, accuracy, or hardware claims.
    requirement: GAME-02
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase21_game_evidence(_controls)?$'"
        status: pass
      - kind: other
        ref: "verify-cgb-game-evidence.py --check at source 893ecac8f70b2b6484c17686548f5ad091b7733b; build/phase21-evidence/result.json"
        status: pass
    human_judgment: false
  - id: D2
    description: Ordered candidate records retain the bounded two-candidate no-go outcome and reject identity, rights-claim, and source-pin mutations.
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase21_fixture_admission(_contract|_controls)?$'"
        status: pass
    human_judgment: false
  - id: D3
    description: Scene-report documentation preserves independent regression expectations, owner agency, and private-media boundaries.
    requirement: FEED-01
    verification:
      - kind: integration
        ref: "ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase21_scene_report_.*$'"
        status: pass
    human_judgment: false
  - id: D4
    description: The final configured implementation passes the complete registered CTest suite and the fixed test-budget gate.
    requirement: GAME-01
    verification:
      - kind: integration
        ref: "cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error — source 893ecac8f70b2b6484c17686548f5ad091b7733b"
        status: pass
    human_judgment: false
duration: 293min
completed: 2026-11-02
commits: 21
plan_head_before: 9f7bda3787d69f726a7ef2e63fa4b2c65be7ad63
plan_head_after: 893ecac8f70b2b6484c17686548f5ad091b7733b
status: complete
---

# Phase GB-21 Plan 21-07: Source-Bound Outcome and Qualification Summary

**The final receipt records a harness-only CGB result and two bounded rights/source-scope no-go outcomes without implying game progress or license prohibition.**

## Performance

- **Duration:** 293 minutes
- **Started:** 2026-11-02T03:58:54Z
- **Completed:** 2026-11-02
- **Tasks:** 2
- **Files modified:** 17

## Accomplishments

- Added a source-bound outcome composer that reuses the progress, candidate, and scene-report checkers and rejects missing evidence, contradictory candidate claims, and overbroad accuracy, hardware, or game-progress language.
- Recorded the final no-go outcome with its evidence limits. Potion Panic's exact source/component grants and repository/public-CI scope were not established after the creator-linked repository fetch failed. µCity 1.3 source commit `d1880a2a112d7c26f16c0fc06a15b6c32fdc9137` was identified, but the required `source/engine/hardware.inc` has no identified grant or notice. These are unresolved rights/source-scope outcomes, not claims that either license prohibits use.
- Kept both game's build, ROM, digest, cartridge-header and execution facts `not_observed`; no third candidate or fallback fixture/case/input/predicate/notice row was created. `FIXT-01` therefore remains pending.
- Qualified the original authored CGB control at source `893ecac8f70b2b6484c17686548f5ad091b7733b`. It remains harness-only under model `CGB-CPU-E`, native CGB mode; digest repeatability does not establish game progress, rendering accuracy, physical hardware behavior, perceptual quality, mode-3 timing, or general compatibility.
- Preserved the existing DMG baseline and the scene workflow's independent expectation, owner-agency, and private-media boundaries. Both descriptor-less plan prohibitions remain explicitly unresolved.
- Configured and built the final implementation, then passed all 1,724 registered CTests in 1,256.12 seconds. The deterministic `test_budget` check passed. The fixture-admission contract and mutation controls took 3.44 and 18.48 seconds under their unchanged 60-second limits.
- Produced a source-qualified receipt at `build/phase21-evidence/result.json` and updated the independent review report. Exact-head hosted/platform and installed-consumer qualification is still pending on PR #140 at the time of this summary; stale earlier workflow results are not used as proof.

## Task Commits

Task 1 established the TDD contract and implementation: `cd339510` (test) and `a7e37b6e` (feature). Its isolated pre-GREEN test replay failed at the intended missing-outcome assertion; the recorded target/semantic check passed, and the implementation then passed the contract suite.

Task 2 and attributable follow-up fixes were committed individually:

1. `cd919d63` classify the integrated test correctly.
2. `d9fac798` bind state-fork cases to Phase 21 source.
3. `213c9081` reject contradictory CGB claims.
4. `8a784907` cover candidate rights-claim variants.
5. `1e328e66` reject candidate license overclaims.
6. `063cc849` write evidence under the canonical build path.
7. `2c49bb76` remove redundant per-mutation checker work.
8. `948d414a` allow the primary evidence run during a fallback identity control.
9. `15cb0c31`, `a0a82f99`, `72845e23`, `9a0ab07d`, and `a58c52dd` tighten license-claim negation, repeated-claim isolation, and contrastive claim handling.
10. `cbfda907` qualify evidence checks across platforms.
11. `6d14f9d1` verify the complete CTest inventory.
12. `d066a0fb` preserve spaced dump paths.
13. `3713b8e5` record local qualification evidence.
14. `b8f80f48` accept CRLF admission pins.
15. `893ecac8` reject bare-CR admission pins.

**Plan commit range:** 21 commits from `9f7bda3787d69f726a7ef2e63fa4b2c65be7ad63` through `893ecac8f70b2b6484c17686548f5ad091b7733b`, measured before the plan-metadata commit.

## Files Created/Modified

- `tests/scripts/verify-cgb-game-evidence.py` and `tests/cmake/game-evidence.cmake` — compose and register the immutable-source outcome receipt and negative controls.
- `tests/scripts/verify-cgb-candidates.py`, `verify-cgb-progress.py`, `verify-fixture-admission.py`, `verify-scene-report.py`, `tests/CMakeLists.txt`, `tests/expected-tests.txt`, and `tests/data/state-forks.json` — complete platform, source-pin, timing, and test-inventory coverage.
- `docs/game-acceptance.md`, `docs/cgb-profile.md`, and `docs/support/unreleased.md` — state the actual candidate/harness outcome and limits.
- `21-VALIDATION.md`, `21-07-REVIEW.md`, `deferred-items.md`, `.continue-here.md`, and `.planning/context/LESSONS.md` — record local evidence, review, budget resolution, causes, and handoff.

## Decisions Made

- Keep Potion Panic and µCity 1.3 as no-go outcomes because repository/public-CI source scope could not be established for the exact candidate inputs. Do not infer that a license prohibits use.
- Do not close `FIXT-01`: the required exact source/build, ROM identity, cartridge header, and CGB execution observations were not produced.
- Preserve the harness-only label and software-model boundary for the original control. Keep physical, perceptual, timing, and broad compatibility questions unqualified.
- Preserve both descriptor-less prohibitions as unresolved statements; the plan does not authorize turning them into automated passes or removing them.
- Resolve the test-budget failure by eliminating unnecessary repeated work in mutation controls. Retain the deterministic 60-second budget, without refreshing its baseline or repairing unrelated v0.3 debt.

## Deviations from Plan

### Auto-fixed Issues

1. **Rule 3 — fixture-admission controls exceeded the 60-second project budget.**
   - **Found during:** Task 2 final qualification.
   - **Issue:** The fixture-admission CTests originally declared 120 and 180 seconds while `test_budget` fixes the project cap at 60 seconds.
   - **Fix:** Removed redundant full-checker work per mutation and retained explicit 60-second limits. The final checks took 3.44 and 18.48 seconds; `test_budget` passed. No timeout or baseline increase.
   - **Files modified:** `tests/scripts/verify-cgb-candidates.py`, `tests/cmake/game-evidence.cmake`.
   - **Commits:** `2c49bb76`, `3713b8e5`.

2. **Rule 1 — fixture-admission test subjects needed immutable identity and platform-safe handling.**
   - **Found during:** Task 2 review and stale hosted-run diagnosis.
   - **Issue:** Phase 21 state-fork cases referenced the wrong source identity; the registered-test comparison was order-sensitive; Windows scene tests omitted Debug configuration; Windows dump parsing truncated paths with spaces; Windows checkout normalized fixture pins to CRLF; and a permissive parser accepted a bare CR.
   - **Fix:** Pinned the intended source, compared the complete test inventory, selected the Debug config, preserved quoted/unquoted spaced paths, accepted only absent/LF/CRLF pin endings, and added a bare-CR negative control. The focused checks and final full suite passed.
   - **Files modified:** `tests/data/state-forks.json`, `tests/CMakeLists.txt`, `tests/expected-tests.txt`, `tests/scripts/verify-cgb-progress.py`, `tests/scripts/verify-fixture-admission.py`, `tests/scripts/verify-scene-report.py`.
   - **Commits:** `d9fac798`, `cbfda907`, `6d14f9d1`, `d066a0fb`, `b8f80f48`, `893ecac8`.

3. **Rule 1 — claim controls needed to distinguish each license statement.**
   - **Found during:** Task 1 integrated mutation testing and review.
   - **Issue:** Generic negation and mixed/repeated candidate statements could obscure a positive overclaim or reject a correctly scoped unresolved statement.
   - **Fix:** Scoped negation and contrastive claim parsing to individual candidate/license statements; added controls for repeated, mixed, and contrastive claims. Independent review closed the resulting findings.
   - **Files modified:** `tests/scripts/verify-cgb-game-evidence.py`.
   - **Commits:** `213c9081`, `8a784907`, `1e328e66`, `15cb0c31`, `a0a82f99`, `72845e23`, `9a0ab07d`, `a58c52dd`.

4. **Rule 1 — source receipt and documentation checks needed canonical, cross-platform identities.**
   - **Found during:** Task 2 CMake-floor/ASan/hosted review.
   - **Issue:** The CMake-floor checker rejected a generated evidence path, integrated output was not canonical under the build tree, and CTest registration/suite results varied by platform.
   - **Fix:** Constrained output to the canonical build evidence directory and qualified registration and result checks across the supported CI runners. No third-party tool or dependency was added.
   - **Files modified:** `tests/scripts/verify-cgb-game-evidence.py`, `tests/cmake/game-evidence.cmake`, `tests/CMakeLists.txt`.
   - **Commits:** `063cc849`, `948d414a`, `cbfda907`, `6d14f9d1`.

5. **Rule 1 — the new lesson identifier collided with an existing ledger entry.**
   - **Found during:** First full CTest run.
   - **Issue:** `lessons_unique_ids` rejected duplicate `GB-CGB-001`.
   - **Fix:** Assigned the new lesson unique ID `GB-CGB-015`; its focused check and final full suite passed.
   - **Files modified:** `.planning/context/LESSONS.md`.
   - **Commit:** `3713b8e5`.

**Total deviations:** 5 directly attributable fixes. **Impact:** Kept the planned evidence scope and project limits; no baseline, timeout budget, dependency, third candidate, or unrelated release debt was added.

## Issues Encountered

- The TDD RED evidence record is a replay of the immutable test-only snapshot because the initial harness output was not retained. The recorded target failed specifically because the candidate-outcome function returned `None`; the semantic assessment ruled out discovery/setup failures. The GREEN implementation passed.
- The plan's example source argument `HEAD` did not always match the runner's build-stamped source after documentation commits. Final receipt uses the full immutable source hash explicitly.
- One earlier full-suite run found the lesson-ID collision; after its fix, the final source run passed completely.
- Earlier hosted workflow failures were investigated and fixed where attributable, but those runs are stale. They are not cited as proof for the current revision.

## Threat and Review Status

- Independent code review at `893ecac8` is clean with zero open findings; see `21-07-REVIEW.md`.
- Security review closed T-21-15 and T-21-SC. T-21-16 remains open until exact-head hosted and installed-consumer checks pass. T-21-17 is the shared verify-work/closure step.
- The new checker consumes existing CLIs and the Python standard library; it adds no network endpoint or third-party dependency.

## Next Phase Readiness

Plan 21-07 implementation and local qualification are complete. Exact-head hosted native/platform, acceptance, and installed-consumer checks on PR #140 are the remaining plan qualification gate; then the shared `/gsd-verify-work 21` closure completes Phase 21. Phase 22 remains **not started**. After Phase 21 is verified and closed, the owner-selected next phase command is `/gsd-discuss-phase 22` for **Phase 22 — Composition and Microtest Evidence**. Automatic advance remains disabled.

---
*Phase: GB-21-cgb-game-progress-and-scene-regressions*
*Plan: 07*
*Completed: 2026-11-02*

## Self-Check: PASSED

The summary, evidence checker, CMake registration, and source-bound receipt exist. All 21 task commits are ancestors of the recorded plan head. The six summary-coverage checks passed after the summary was written.
