---
phase: GB-07-dmg-game-acceptance-and-regression-baseline
verified: 2026-10-20T18:00:45Z
status: passed
score: 122/122 must-haves verified
covered_files:
  - ".gitattributes"
  - ".github/workflows/ci.yml"
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
  - "THIRD_PARTY_NOTICES.md"
  - "cmake/VerifyDmgBaseline.cmake"
  - "docs/game-acceptance.md"
  - "docs/support/v0.2.0.md"
  - "fixtures/libbet/LICENSE.txt"
  - "fixtures/libbet/SOURCES.md"
  - "fixtures/libbet/libbet.gb"
  - "fixtures/libbet/manifest.json"
  - "src/accept/digest.c"
  - "src/accept/gbb_accept.h"
  - "src/accept/input_script.c"
  - "src/accept/predicate.c"
  - "src/accept/sha256.c"
  - "src/accept/stepper.c"
  - "src/player/main.c"
  - "src/player/script_smoke.c"
  - "src/runner/acceptance.c"
  - "src/runner/cases.c"
  - "src/runner/main.c"
  - "tests/acceptance/CMakeLists.txt"
  - "tests/acceptance/cases.txt"
  - "tests/baseline/dmg-cpu-b-v1.txt"
  - "tests/scripts/verify-dmg-baseline.sh"
  - "tests/scripts/verify-libbet-admission.py"
  - "tests/scripts/verify-phase3-player.sh"
  - "tests/scripts/verify-stall-report.py"
  - "tests/test_acceptance_cases.c"
  - "tests/test_acceptance_digest.c"
  - "tests/test_acceptance_lib.c"
  - "tests/test_audio.c"
  - "tests/test_runner.c"
covered_digest: "v3:sha256:24dd15e7a537439b23311b8b6dac06d5102dfcac6ac4910d0ea1b71e6a5f7738"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 5/5
  gaps_closed: []
  gaps_remaining: []
  regressions: []
human_verification: []
---

# Phase 7: DMG Game Acceptance and Regression Baseline Verification Report

**Phase Goal:** A maintainer can show one rights-clear DMG game starting, responding to input and progressing on the existing DMG core and player, and every later v0.2 phase has a frozen DMG baseline to prove itself against.
**Verified:** 2026-10-20 at current HEAD `492b5f522387f02c08b062074c9dff5f2dbb2150`
**Status:** passed. All five roadmap criteria, all 117 plan-specific truths, and all five requirements are verified.
**Verification mode:** Fresh goal-backward verification. The previous report had no `gaps:` section and was stale because `docs/game-acceptance.md` changed; Phase 7 regression and negative-control evidence was rerun at current HEAD.

## Observable Truths

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | Libbet admission is pinned to a ROM digest and complete provenance/redistribution contract; malformed or incomplete admission fails closed. | VERIFIED | `python3 -I tests/scripts/verify-libbet-admission.py` passed (`closure_files=45`, `embedded_assets=45`); `--self-test` passed five mutation controls. `libbet_admission_*`, notice, package-scan and install-tree CTests passed in both focused and full suites. |
| 2 | Scripted, emulated-time input starts and progresses the admitted DMG game; the acceptance receipt has frame and non-silent PCM evidence, while negative controls fail. | VERIFIED | Current runner receipt passed at core revision `492b5f5…`, `t_hit_half_dots=125841408`, PCM SHA-256 `3d051cb0a0a4ced82706126c5cbcaddcd22dbe2cc2e61c92d0c5717f1e8aaae5`, peak-to-peak 20290 and 164822 sample changes. A fresh no-input raw verdict exited 1 with `reason=predicate-not-reached`. |
| 3 | Acceptance cases enforce model/revision applicability, deterministic RGB digest capture, input replay, and failure-only image output without adding runtime dependencies. | VERIFIED | The focused and full CTest runs passed parser, predicate, digest-vector, LD B,B, exclusion, target-revision, unsupported-model, strict-xfail, mutation, and failure-output controls. The CLI mutation control and SGB probe wiring were manually traced where runtime pattern matching was too narrow. |
| 4 | The extracted SDL3 package launches Libbet with scripted input and matches the headless PCM digest; invalid/no-input paths fail and the ROM is absent from the package. | VERIFIED | `bash tests/scripts/verify-phase3-player.sh --build-package` passed; its 98/98 player CTests passed. Packaged smoke reported `predicate=pass`, `pcm_nonsilent=1`, and matching PCM digest; no-input control failed as expected and the ROM was absent from the package. |
| 5 | A frozen DMG baseline has stable CTest inventory, Mooneye/acceptance observations and benchmark records, and detects byte or inventory drift. | VERIFIED | `bash tests/scripts/verify-dmg-baseline.sh` passed (`mooneye=15`, `acceptance=20`, `bench=2`, `changes=0`). Baseline positive and negative tests passed in the focused and full suites; full regression gate ran at current HEAD. |

**Score:** 122/122 must-haves verified: five roadmap criteria plus 117 plan-specific truth statements. No behavior-dependent truth remains untested.

## Plan-Specific Truths

Every plan’s declared `must_haves.truths` was checked against implementation, tests, current output, or historical boundary evidence. The groups below total 117/117; plan-level runtime queries found 42 artifacts and 31 key links. Three narrow pattern misses are reconciled in the artifact and link tables rather than treated as implementation failures.

| Plan | Truths | Verified contract and evidence |
|---|---:|---|
| 07-01 | 13/13 | Pinned ROM, rights and closure metadata, notices, strict manifest admission, mutation controls, and package/install exclusion; admission self-test and CTests pass. |
| 07-02 | 10/10 | Bounded all-or-nothing script parsing, emulated-time stepping, predicate anchors and transition behavior; parser, replay and predicate tests pass. |
| 07-03 | 5/5 | Mixer/headroom regression and bounded audio evidence; `audio_saturation` passes. D-027’s missing pre-fix RED demonstration remains explicit. |
| 07-04 | 6/6 | Reproduction recipe and scope are recorded; only local macOS reproduction is claimed, with no hosted/Linux run asserted (D-039). |
| 07-05 | 8/8 | Acceptance runner and replay are connected to cases, parser, predicate, digests and failure paths; focused CTests pass. |
| 07-06 | 3/3 | Invalid scripts and negative files reject with bounded errors; parser-negative CTests pass. |
| 07-07 | 9/9 | RGB/PCM evidence and failure-only image behavior; independent digest vectors and failure-path tests pass. |
| 07-08 | 5/5 | Model, target revision, expected-failure and exclusion rules; suite applicability controls pass. |
| 07-09 | 9/9 | LD B,B canonical frame result, control manifest and not-ready behavior; `acceptance_ldbb_*` controls pass. |
| 07-10 | 6/6 | Dropped-input and raw-verdict controls distinguish predicate failure and strict xfail; registered acceptance controls pass. |
| 07-11 | 5/5 | Fresh dropped-START stall report, bounded trace/I/O/histogram, deterministic artifacts and malformed-report rejection; actual integration check passes and self-test rejects 20 weakened cases. |
| 07-12 | 6/6 | Packaged player smoke uses the normal keyboard path, shared acceptance driver and matching headless PCM; package check passes. |
| 07-13 | 8/8 | Frozen baseline content and failure-on-drift behavior; baseline tests and shell validator pass. |
| 07-14 | 5/5 | Player-session no-input, invalid-script and smoke-surface guards; package run passed all 98 player CTests. |
| 07-15 | 7/7 | Inventory/baseline closure and controls remain byte-stable; baseline and full regression gates pass. |
| 07-16 | 7/7 | Historical exact-head CI, privacy/triage and handoff evidence are checked at Phase 7 boundary `175c9fce4a5c2cdfd62811462a2e8d9e3e2ac441`. The handoff there names `/gsd-verify-work 7` and the macOS limitation; later Phase 15 migration of the support-ledger entry and current continuation route are expected lifecycle updates. |
| 07-17 | 5/5 | Decision/lesson and scope refinements are recorded and traceable; underlying acceptance and documentation contracts remain present. |

## Regression and Negative Controls

Fresh checks at current HEAD:

| Command | Result |
|---|---|
| `cmake --build build --parallel 4` | Pass. |
| `ctest --test-dir build -R '^(libbet_|acceptance_|dmg_baseline)' --output-on-failure --no-tests=error` | 84/84 passed. |
| `bash tests/scripts/verify-phase3-player.sh --build-package` | Pass; packaged-player build and smoke succeeded; 98/98 player CTests passed. |
| `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` | Full regression gate passed, 1144/1144. This command was run once through the configured 600-second GSD timeout. |
| `python3 -I tests/scripts/verify-libbet-admission.py` and `--self-test` | Pass; five admission mutations rejected. |
| `bash tests/scripts/verify-dmg-baseline.sh` | Pass; inventory and baseline status pass, zero changes. |
| `python3 -I tests/scripts/verify-stall-report.py --self-test` | Pass; 19 malformed-report cases and one repeated-byte mismatch rejected. |
| `build/gabbaboy-runner --acceptance tests/acceptance/cases.txt --case libbet-no-input --raw-verdict` | Expected exit 1 with `reason=predicate-not-reached`. |

The fresh passing Libbet receipt was `status=pass`, `build_qualified=true`, `t_hit_half_dots=125841408`; its PCM digest matched the packaged-player smoke. The test runner’s optional matching Clang libFuzzer runtime was unavailable, but deterministic sanitizer/regression tests remained enabled in the passing suite.

## Required Artifacts

| Artifact group | Status | Details |
|---|---|---|
| 42 artifacts declared across plans 07-01 through 07-17 | VERIFIED | 39 passed the runtime pattern query. One query did not find `sgb_probe_frames` in `predicate.c`; the field is declared in `gbb_accept.h`, positionally initialized to `90u` in `predicate.c`, read by `runner/acceptance.c`, and covered by passing SGB-tolerance tests. |
| Two Plan 07-16 historical artifacts | VERIFIED | Runtime queries inspect current paths and therefore miss the old handoff/macOS marker. Both are present at the required Phase 7 boundary commit; the later Phase 15 versioned support ledger supersedes the unreleased entry. |
| `tests/scripts/verify-stall-report.py` | VERIFIED | New reconciliation checker exercises the real dropped-START run twice, validates report shape/counts/caps and deterministic report/PPM identity, and has 20 passing negative controls. |

## Key Link Verification

| Link group | Status | Details |
|---|---|---|
| 31 declared links across plans 07-01 through 07-17 | VERIFIED | 30 passed the runtime key-link query. The sole pattern miss was `--mutate drop:<BUTTON>` from `src/runner/acceptance.c` to the acceptance API: `src/runner/main.c` parses the CLI option, `src/runner/acceptance.c` filters events before the shared driver, and CTest covers dropped START and digest mutation. |

## Data-Flow Trace

| Flow | Source to result | Status |
|---|---|---|
| Admission | Pinned ROM and manifest → strict validator and closure scan → CTest/package exclusion | FLOWING; current admission, mutation, install and package checks pass. |
| Headless game acceptance | Case/script bytes → runner → shared stepper/predicate → receipt with frame and PCM digests | FLOWING; direct passing and no-input negative receipts observed at current HEAD. |
| Player smoke | Scripted SDL keyboard events → packaged player/session → acceptance predicate and PCM digest | FLOWING; package smoke matches headless PCM and ROM remains absent from the extracted archive. |
| Regression baseline | Versioned records and exact CTest inventory → baseline verifier and CI gate | FLOWING; current validator and full CTest gate pass. |

## Requirements Coverage

| Requirement | Status | Evidence |
|---|---|---|
| GAME-01 | SATISFIED | Current pinned manifest/closure admission passes; five mutation controls and install/package exclusion pass. |
| GAME-02 | SATISFIED | Current positive receipt proves input-driven predicate progress and stable frame/PCM digests; no-input and dropped-input controls fail correctly. |
| GAME-03 | SATISFIED (macOS packaged player) | Fresh package build and smoke pass; 98/98 player CTests pass. Linux/Windows packaged-player game smoke is not claimed. |
| EVID-01 | SATISFIED | Digest, input, applicability, model and revision controls pass; no runtime dependency was added. |
| EVID-02 | SATISFIED | Frozen DMG baseline, failure controls, and full 1144-test regression gate pass. |

No requirements are orphaned; REQUIREMENTS.md maps exactly GAME-01..03 and EVID-01..02 to Phase 7.

## Review, Security, and Validation Gates

- Code review: reused the Phase 7 review because no Phase 7 implementation source changed. `07-REVIEW-DISPOSITION.md` records 10 findings and 0 open. WR-01 remains a documented deferred driver-backpressure concern with explicit `event-delivery-failed` behavior and a passing negative test; IN-03/IN-05 remain skipped with reasons.
- Security: reused `07-SECURITY.md`, which records `threats_open: 0`; current code tests do not change the security surface.
- Validation: `07-VALIDATION.md` contains the 2026-10-20 retroactive reconciliation of the stall-report check. The actual report integration and its 20 negative controls were rerun successfully in this verification.
- UI review hook: no Phase 7 UI-SPEC exists. The phase claims automated launch/progress/audio smoke, not visual quality; no perceptual claim is made.

## Anti-Patterns Found

No blocking debt markers, TODO stubs, placeholder implementations, or disconnected behavior were found in the Phase 7 acceptance path. `NULL` returns in runner/parser code are guard/error paths; the `PLACEHOLDERS` set in admission validation rejects invalid manifest values and is not placeholder product content.

## Limitations (Recorded, Not Gaps)

- Evidence is one game on one bootless DMG-CPU-B software model. No physical DMG hardware, broad game compatibility, perceptual audio/video or physical CGB-E result is claimed.
- Packaged-player smoke is macOS-only; headless acceptance has historical Linux/macOS/Windows CI evidence. No Linux hosted Libbet reproduction run exists (D-039); local reproduction evidence is macOS-only.
- D-027’s strengthened `audio_saturation` test was not demonstrated failing against the pre-fix core. Its historical defect evidence is the recorded scratch probe, and the missing RED demonstration remains disclosed.
- Libbet asset rights retain the documented single-author-history inference and are not represented as per-asset upstream licence grants.
- Dense scripts that exceed the runner’s delivery batch still fail explicitly; driver backpressure is deferred under WR-01.
- The later Phase 15 `docs/game-acceptance.md` change adds CGB game-evidence scope and explicitly says no CGB game-level, physical or perceptual evidence exists. It does not weaken or replace Phase 7’s DMG claims.

## Human Verification Required

None. Hardware and perceptual observations are explicit scope limitations, not acceptance criteria for this phase. D-029 is already ratified; no owner decision is pending.

## Gaps Summary

No blocking gaps remain. The stale report was refreshed with current test evidence and a current fingerprint. Plan-query name-pattern misses were resolved by source, boundary-commit and test evidence. All five roadmap criteria, 117 plan-specific truths, 42 artifacts, 31 links, and five mapped requirements are verified.

---

_Verified: 2026-10-20T18:00:45Z_
_Verifier: the agent (gsd-verifier)_
