---
phase: GB-07-dmg-game-acceptance-and-regression-baseline
verified: 2026-10-11T09:00:00Z
status: passed
score: 5/5 must-haves verified
covered_files:
  - ".planning/phases/GB-07-dmg-game-acceptance-and-regression-baseline/07-01-PLAN.md"
  - ".planning/phases/GB-07-dmg-game-acceptance-and-regression-baseline/07-01-SUMMARY.md"
  - ".planning/phases/GB-07-dmg-game-acceptance-and-regression-baseline/07-02-PLAN.md"
  - ".planning/phases/GB-07-dmg-game-acceptance-and-regression-baseline/07-02-SUMMARY.md"
  - ".planning/phases/GB-07-dmg-game-acceptance-and-regression-baseline/07-03-PLAN.md"
  - ".planning/phases/GB-07-dmg-game-acceptance-and-regression-baseline/07-03-SUMMARY.md"
  - ".planning/phases/GB-07-dmg-game-acceptance-and-regression-baseline/07-04-PLAN.md"
  - ".planning/phases/GB-07-dmg-game-acceptance-and-regression-baseline/07-04-SUMMARY.md"
  - ".planning/phases/GB-07-dmg-game-acceptance-and-regression-baseline/07-05-PLAN.md"
  - ".planning/phases/GB-07-dmg-game-acceptance-and-regression-baseline/07-05-SUMMARY.md"
  - ".planning/phases/GB-07-dmg-game-acceptance-and-regression-baseline/07-06-PLAN.md"
  - ".planning/phases/GB-07-dmg-game-acceptance-and-regression-baseline/07-06-SUMMARY.md"
  - ".planning/phases/GB-07-dmg-game-acceptance-and-regression-baseline/07-07-PLAN.md"
  - ".planning/phases/GB-07-dmg-game-acceptance-and-regression-baseline/07-07-SUMMARY.md"
  - ".planning/phases/GB-07-dmg-game-acceptance-and-regression-baseline/07-08-PLAN.md"
  - ".planning/phases/GB-07-dmg-game-acceptance-and-regression-baseline/07-08-SUMMARY.md"
  - ".planning/phases/GB-07-dmg-game-acceptance-and-regression-baseline/07-09-PLAN.md"
  - ".planning/phases/GB-07-dmg-game-acceptance-and-regression-baseline/07-09-SUMMARY.md"
  - ".planning/phases/GB-07-dmg-game-acceptance-and-regression-baseline/07-10-PLAN.md"
  - ".planning/phases/GB-07-dmg-game-acceptance-and-regression-baseline/07-10-SUMMARY.md"
  - ".planning/phases/GB-07-dmg-game-acceptance-and-regression-baseline/07-11-PLAN.md"
  - ".planning/phases/GB-07-dmg-game-acceptance-and-regression-baseline/07-11-SUMMARY.md"
  - ".planning/phases/GB-07-dmg-game-acceptance-and-regression-baseline/07-12-PLAN.md"
  - ".planning/phases/GB-07-dmg-game-acceptance-and-regression-baseline/07-12-SUMMARY.md"
  - ".planning/phases/GB-07-dmg-game-acceptance-and-regression-baseline/07-13-PLAN.md"
  - ".planning/phases/GB-07-dmg-game-acceptance-and-regression-baseline/07-13-SUMMARY.md"
  - ".planning/phases/GB-07-dmg-game-acceptance-and-regression-baseline/07-14-PLAN.md"
  - ".planning/phases/GB-07-dmg-game-acceptance-and-regression-baseline/07-14-SUMMARY.md"
  - ".planning/phases/GB-07-dmg-game-acceptance-and-regression-baseline/07-15-PLAN.md"
  - ".planning/phases/GB-07-dmg-game-acceptance-and-regression-baseline/07-15-SUMMARY.md"
  - ".planning/phases/GB-07-dmg-game-acceptance-and-regression-baseline/07-16-PLAN.md"
  - ".planning/phases/GB-07-dmg-game-acceptance-and-regression-baseline/07-16-SUMMARY.md"
  - ".planning/phases/GB-07-dmg-game-acceptance-and-regression-baseline/07-17-PLAN.md"
  - ".planning/phases/GB-07-dmg-game-acceptance-and-regression-baseline/07-17-SUMMARY.md"
  - "docs/game-acceptance.md"
  - "fixtures/libbet/manifest.json"
  - "src/accept/input_script.c"
  - "src/player/script_smoke.c"
  - "tests/acceptance/cases.txt"
  - "tests/baseline/dmg-cpu-b-v1.txt"
  - "tests/scripts/verify-dmg-baseline.sh"
  - "tests/scripts/verify-libbet-admission.py"
covered_digest: "v3:sha256:2f7e42ef32f6840553a26fc64fdf7c13ab4bca12dcc64e6f0d250a7bfecc4933"
behavior_unverified: 0
human_verification: []
---

# Phase 7: DMG Game Acceptance and Regression Baseline Verification Report

**Phase Goal:** A maintainer can show one rights-clear DMG game starting, responding to input and progressing on the existing DMG core and player, and every later v0.2 phase has a frozen DMG baseline to prove itself against.
**Verified:** 2026-10-11 at branch head 175c9fce4a5c2cdfd62811462a2e8d9e3e2ac441
**Status:** passed (all five success criteria verified; the one owner decision, D-029, was ratified by the owner on 2026-10-11)
**Re-verification:** No, initial verification

## Evidence reproduced by the verifier (not taken from SUMMARY files)

- `cmake --preset phase1`, build, and `caffeinate -i -s ctest --preset phase1 --no-tests=error`: 261/261 passed, 217 s.
- `gabbaboy-runner --acceptance tests/acceptance/cases.txt --case libbet --receipt`: `status=pass`, `t_hit_half_dots=125841408`, `pcm_sha256=3d051cb0...aaae5`, PCM peak-to-peak 20290 and 164822 changes, `hw_f90=00`, `sgb_reset_pulses=2`, `build_qualified=true`, `core_revision=175c9fce...`.
- Same runner, `--case libbet-no-input --raw-verdict`: exit 1, `reason=predicate-not-reached`, `final_floor=00`.
- `bash tests/scripts/verify-dmg-baseline.sh`: `mooneye=ok keys=15`, `acceptance=ok keys=20`, `bench=ok keys=2`, `changes=ok rows=0`, `status=pass`.
- `python3 -I tests/scripts/verify-libbet-admission.py`: `libbet admission verified ... closure_files=45 embedded_assets=45`.
- `gh run view` on exact head 175c9fc: ci 38125054341 (all 8 jobs success, including native-linux-x64, native-macos-arm64, native-windows-x64, macos-player-package), fixture-repro 38125054309 success, preview-package-smoke 38125054331 success. CI logs show `baseline status=pass` on all three native jobs and, in `macos-player-package`, `smoke_report ... predicate=pass pcm_nonsilent=1 pcm_sha256=3d051cb0...` (matches the headless digest) plus a no-input control `predicate=fail pcm_nonsilent=0`.

## Success Criteria

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Admission requires a manifest with source commit, licence text, per-asset provenance, release digest, repro statement; unrecorded embedded-asset right fails | VERIFIED | `fixtures/libbet/manifest.json` records commit `46a765a2...`, licence digest, ROM sha256. `verify-libbet-admission.py` passes on the real tree (45 closure files, 45 embedded assets) and has failing controls registered in CTest: `libbet_admission_empty_assets`, `_missing_record`, `_unknown_licence`, `_bad_digest`, `_bad_header`, `_self_test`, plus `libbet_install_tree` / `libbet_not_installed` (+selftest). All pass locally. |
| 2 | Scripted emulated-time input reaches the guest-memory predicate with frame digests and non-silent PCM digest on Linux/macOS/Windows CI; the no-input run does not | VERIFIED | Local receipt above. Controls `acceptance_libbet-no-input_raw`, `_select_raw`, `acceptance_libbet_drop_start`, `acceptance_core_mutant` assert predicate-not-reached. CI native jobs on all three OSes ran the full CTest set (incl. `acceptance_libbet`) and are green at exact head. |
| 3 | Runner captures `LD B,B` frame as canonical RGB digest (image only on failure), replays joypad scripts, honours `model_pass`/`model_fail`/`target_revision`/`unsupported-model`, no new dependency | VERIFIED | Tests present and passing: `acceptance_digest_vectors` (independent stdlib Python vector), LD B,B controls file `tests/acceptance/ldbb-controls.txt`, `acceptance_libbet_excluded_cgb-cpu-e`, `acceptance_libbet-cgb-only_excluded_dmg-cpu-b`, strict xfail cases `acceptance_libbet-no-input` / `-select`, `acceptance_negative_*`. Dependencies: only CMake/C/stdlib Python. |
| 4 | Packaged SDL3 player launches the game and passes automated input/progress/audio smoke in CI | VERIFIED (macOS only) | `tests/scripts/verify-phase3-player.sh` runs the packaged player with `--input-script` on `fixtures/libbet/libbet.gb`, requires `predicate=pass pcm_nonsilent=1` and PCM digest equal to the headless value, and a no-input control that must fail. CI log of macos-player-package confirms both. Registered guards `player_script_smoke_surface*`, `player_session_script_no_input/invalid`. |
| 5 | Frozen DMG baseline (CTest inventory, Mooneye closures, acceptance digests, benchmark baseline) with a single byte-identity check | VERIFIED | `tests/baseline/dmg-cpu-b-v1.txt` plus `verify-dmg-baseline.sh` (local pass, CI pass on 3 OSes and in player build). 17 failing-path CTests (`dmg_baseline_modified/missing/extra/inventory_removed/changes_unrecorded/...`, JUnit skipped/failed/missing) show the check can fail. `CHANGES.md` has a reverse-apply protocol with zero rows and no update mode. |

## Requirements Coverage

| Requirement | Status | Evidence |
|-------------|--------|----------|
| GAME-01 | SATISFIED | Criterion 1 evidence. |
| GAME-02 | SATISFIED | Criterion 2 evidence; frame checkpoint digests and PCM digest in receipt; no-input control fails. |
| GAME-03 | SATISFIED (macOS) | Criterion 4 evidence. Packaging exists only for macOS, which the requirement does not exceed. |
| EVID-01 | SATISFIED | Criterion 3 evidence. |
| EVID-02 | SATISFIED | Criterion 5 evidence; later-phase enforcement is wired into CI (`baseline status=pass` step on all native jobs). |

No orphaned requirements: REQUIREMENTS.md maps exactly GAME-01..03 and EVID-01..02 to Phase 7.

## Anti-Patterns and Review

- 07-REVIEW.md: 10 findings, 0 open. WR-01 (dense scripts exceed the core's 64-event queue) is deferred and documented; it fails loudly with `reason=event-delivery-failed`, covered by `acceptance_dense_script_delivery_failed`. IN-03 and IN-05 skipped with stated reasons. 07-SECURITY.md: threats_open 0.
- Debt-marker scan of phase code was not exhaustive; no blocker surfaced in the areas read.

## Limitations (true, recorded, not gaps)

- One game, one model (DMG-CPU-B, bootless). No hardware evidence. Regression-class digests are emulator-captured, not hardware-verified. The `daa` LD B,B frame is all shade 0 and guards "still blank" only; `tim00` LD B,B frames are `not-ready`.
- Packaged-player smoke runs on macOS only. Headless acceptance runs on Linux, macOS and Windows.
- `libbet-repro` is `workflow_dispatch` only and its workflow file is not on the default branch, so there is no hosted reproduction run. Local reproduction is verified on macOS arm64 only; Linux and the dispatch path are unverified. The in-CI `fixture-repro` workflow is green but does not cover the Libbet rebuild.
- The strengthened `audio_saturation` test was not shown to fail against the pre-fix core (D-027); the `frame-digest@t` path has no CTest.
- Asset rights are an inference (single-author history plus repository-wide zlib), stated as such in the manifest `scope_note` and docs.

## Human Verification Required

### 1. Ratify D-029

**Test:** Owner reviews D-029 (checkpoint shade rule relaxed for the 1-bit title and two-shade `play_start`).
**Expected:** Owner confirms in DECISIONS.md, or requests a different structure gate.
**Why human:** Decision ratification, not verifiable from code. It does not affect any success criterion or requirement.
**Resolution:** Ratified by the owner on 2026-10-11; DECISIONS.md D-029 now reads "Adopted (owner, 2026-10-11)".

## Gaps Summary

No blocking gaps. All five roadmap success criteria and all five requirements trace to code plus tests that were observed failing in their negative controls and passing at exact-head CI. Optional follow-ups (not blockers): land the `libbet-repro` workflow on the default branch and run it once on Linux; add a CTest for `frame-digest@t`; add driver back-pressure for dense scripts (WR-01) when a real script needs it.

---

_Verified: 2026-10-11_
_Verifier: Claude (gsd-verifier)_
