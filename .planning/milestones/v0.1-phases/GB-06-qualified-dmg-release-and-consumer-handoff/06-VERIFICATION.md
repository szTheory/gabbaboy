---
phase: GB-06-qualified-dmg-release-and-consumer-handoff
verified: 2026-10-10T16:20:53Z
status: passed
score: 5/5 must-haves verified
covered_files:
  - .github/scripts/verify-published-release-assets.py
  - .github/scripts/verify-release-gates.sh
  - .github/scripts/verify-release-source-proof.py
  - .github/workflows/ci.yml
  - .github/workflows/release-please.yml
  - .github/workflows/release.yml
  - .planning/phases/GB-06-qualified-dmg-release-and-consumer-handoff/06-01-PLAN.md
  - .planning/phases/GB-06-qualified-dmg-release-and-consumer-handoff/06-01-SUMMARY.md
  - .planning/phases/GB-06-qualified-dmg-release-and-consumer-handoff/06-02-PLAN.md
  - .planning/phases/GB-06-qualified-dmg-release-and-consumer-handoff/06-02-SUMMARY.md
  - .planning/phases/GB-06-qualified-dmg-release-and-consumer-handoff/06-03-PLAN.md
  - .planning/phases/GB-06-qualified-dmg-release-and-consumer-handoff/06-03-SUMMARY.md
  - .planning/phases/GB-06-qualified-dmg-release-and-consumer-handoff/06-04-PLAN.md
  - .planning/phases/GB-06-qualified-dmg-release-and-consumer-handoff/06-04-SUMMARY.md
  - .planning/phases/GB-06-qualified-dmg-release-and-consumer-handoff/06-05-PLAN.md
  - .planning/phases/GB-06-qualified-dmg-release-and-consumer-handoff/06-05-SUMMARY.md
  - .planning/phases/GB-06-qualified-dmg-release-and-consumer-handoff/06-06-PLAN.md
  - .planning/phases/GB-06-qualified-dmg-release-and-consumer-handoff/06-06-SUMMARY.md
  - .planning/phases/GB-06-qualified-dmg-release-and-consumer-handoff/06-07-PLAN.md
  - .planning/phases/GB-06-qualified-dmg-release-and-consumer-handoff/06-07-SUMMARY.md
  - .release-please-manifest.json
  - CHANGELOG.md
  - CMakeLists.txt
  - README.md
  - THIRD_PARTY_NOTICES.md
  - cmake/PreviewPackageSmoke.cmake
  - cmake/VerifyReleaseReceipt.cmake
  - docs/cartridge-and-saves.md
  - docs/native-integration.md
  - docs/preview.md
  - docs/release.md
  - docs/support/v0.1.0.md
  - examples/relocated-c/CMakeLists.txt
  - examples/relocated-c/main.c
  - release-please-config.json
  - tests/CMakeLists.txt
  - tests/consumers/c/main.c
  - tests/consumers/cpp/main.cpp
  - tests/expected-tests.txt
  - tests/fuzz_core.c
  - tests/measure_core.c
  - tests/player/CMakeLists.txt
  - tests/player/expected-tests.txt
  - tests/scripts/measure-release-baseline.sh
  - tests/scripts/run-bounded-fuzz.sh
  - tests/scripts/test_verified_player_output_dir.py
  - tests/scripts/verified_player_output_dir.py
  - tests/scripts/verify-phase3-player.sh
  - tests/scripts/verify-release-candidate.sh
  - tests/scripts/verify-support-ledger.py
  - tests/test_battery_fuzz.c
  - tests/test_fuzz_core.c
  - tests/test_loader_fuzz.c
covered_digest: "v3:sha256:d418a8379396b55186f9a9cd24f7547bc701b7d100019e42a41bff066893692e"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 5/5
  gaps_closed: []
  gaps_remaining: []
  regressions: []
---

# Phase 6: Qualified DMG Release and Consumer Handoff Verification Report

**Phase Goal:** As a project adopter, I want to download a qualified limited-DMG release, reproduce native integration, and assess its actual compatibility, safety, and performance evidence, so that I can judge whether it fits my project and what its limits are.
**Verified:** 2026-10-10T16:20:53Z
**Status:** passed
**Re-verification:** Yes. Freshness refresh after Phase 06.1 (PR 54, squash-merged at `ab76d09c2ee27ba09fc5f3c2510af016aebfdecb`, PR head `2a8fd1c357262d4b69707b553c603fd441a0f3fa`), on branch `gsd/phase-06.1-verification-refresh` at HEAD `c4acd89`. HEAD differs from `ab76d09` only under `.planning/`. No prior gaps.

Stale cause: covered `.github/workflows/ci.yml`, `tests/scripts/test_verified_player_output_dir.py` and `tests/scripts/verify-phase3-player.sh` changed since the previous fingerprint. PR 54 also added `audio_api_smoke()` to `tests/consumers/c/main.c` and `tests/consumers/cpp/main.cpp`; both files are added to `covered_files` because the SHIP-01 audio-consumer claim now rests on them.

## Release workflow premise (D-06)

06.1 did not change release.yml. `git diff --exit-code 06c723b5574941ecff7ebefc4b40a9714b7aa495 HEAD -- .github/workflows/release.yml` exited 0 (no difference between the pre-phase base `06c723b` and HEAD).

There is pre-existing drift from v0.1.0. `release.yml` already differed from the v0.1.0 tag before Phase 06.1 began, through earlier post-release fixes. `git diff --stat v0.1.0 06c723b5574941ecff7ebefc4b40a9714b7aa495 -- .github/workflows/release.yml` output:

```
 .github/workflows/release.yml | 140 ++++++++++++++++++++++++++++--------------
 1 file changed, 93 insertions(+), 47 deletions(-)
```

Nothing is claimed here about the v0.1.0 evidence beyond the statement that 06.1 did not change release.yml. The v0.1.0 release evidence below is retained as frozen historical evidence and was not re-run.

## Refresh Evidence (this session)

Re-run by the verifier on branch `gsd/phase-06.1-verification-refresh` at `c4acd89` (macOS arm64). Local evidence only.

| Check | Result |
|---|---|
| `ctest --preset phase1 --output-on-failure --no-tests=error` | 184/184 passed |
| `ctest --preset phase1 --no-tests=error -R 'preview_package_smoke\|installed_consumer'` | 5/5 passed, including `installed_consumer_cpp` and `installed_consumer_phase2_cpp` |
| `bash tests/scripts/verify-release-candidate.sh --self-test` | rc=0; PASS: built archive, relocated external C/C++ consumers, receipt identity, digest tamper, and draft/proof negatives |
| `bash .github/scripts/verify-release-gates.sh --self-test` | rc=0; PASS: release configuration and exact-head required-check gate |
| `python3 tests/scripts/verify-support-ledger.py --self-test` | rc=0 |
| `python3 tests/scripts/test_verified_player_output_dir.py` | 21 tests, OK |
| `gh release view v0.1.0` | `isDraft=false`, 18 assets, target `e30d168f7fc61de8db0a3801e7b1736362912cb7` |
| `git status --short` | only untracked `.planning/milestone.lock` |

Gate results taken from the committed artifacts, not re-run in this session beyond what is listed above: validation `109d6d3` (0 gaps), security `47fc9c8` (18/18 closed), code review `fcbc47f` (clean), disposition `c4acd89` (audit audio-consumer gap recorded as fixed), regression 184/184.

## SHIP-01 audio coverage (Phase 06.1)

The installed C and C++ consumers now call `gbb_run_audio`. Checked in source: `tests/consumers/c/main.c` defines `audio_api_smoke()` (line 76), calls `gbb_run_audio` at lines 124-165 and invokes it from `main` at line 231; `tests/consumers/cpp/main.cpp` does the same (definition line 77, calls lines 126-167, invoked at line 233). Per D-03 the assertions are structural only.

Hosted runs, confirmed with `gh run view <id> --json conclusion,headSha,jobs`:

| Run | Workflow | headSha | Conclusion | Relevant jobs |
|---|---|---|---|---|
| 38064419789 (PR head) | ci | `2a8fd1c357262d4b69707b553c603fd441a0f3fa` | success | `native-linux-x64`, `native-macos-arm64`, `native-windows-x64`, `required-native` all success |
| 38064419803 (PR head) | preview-package-smoke | `2a8fd1c357262d4b69707b553c603fd441a0f3fa` | success | `installed-package-smoke-linux-x64`, `installed-package-smoke-macos-arm64`, `player-package-smoke-macos`, `preview-package-smoke` all success |
| 38064726000 (main push) | ci | `ab76d09c2ee27ba09fc5f3c2510af016aebfdecb` | success | `native-linux-x64`, `native-macos-arm64`, `native-windows-x64`, `required-native` success; `macos-player-package` skipped |

`06.1-DEBT-DISPOSITION.md` records the Windows job log for run 38064419789: installed_consumer_c/_cpp and installed_consumer_phase2_c/_cpp passed in a 184-test run, compiler GNU 14.2.0 (MinGW-w64 GCC, windows-2022, static core). The verifier did not re-download that job log; the job conclusion above is the confirmed fact.

ROADMAP criterion 2's "Windows preview lane" is met by the ci.yml `native-windows-x64` installed-consumer lane per D-02, not by a preview.yml Windows job. No MSVC, DLL, Windows archive-level, hardware or perceptual claim is made. Windows archive-level `preview_package_smoke` parity is re-deferred (`06.1-DEBT-DISPOSITION.md`).

## Historical evidence (frozen v0.1.0), carried forward and NOT re-run

Per-asset ID/size/SHA-256 reconciliation of the 18 published assets, hosted exact-tag Linux x64 / macOS arm64 / Windows x64 receipts, and the recorded performance and support runs concern the frozen v0.1.0 tag. This session re-confirmed only the asset count (18), draft state (false) and tag target. v0.1.0 is immutable and predates later script fixes: its tag retains the disclosed `rm -rf "$FINAL_ARTIFACT_DIR"` path in `verify-phase3-player.sh`, and the changelog self-comparison link in its release notes. Current source uses the output-directory helper. This is a tooling limitation of the frozen tag, not a gap in current source. Not hardware, perceptual, signed, or notarized evidence; no live Playstead Game Boy adapter is claimed.

## User Flow Coverage

User story validation: `valid=true` under the canonical validator (carried from the prior report; goal text unchanged).

| Step | Adopter action | Expected outcome | Evidence | Status |
|---|---|---|---|---|
| 1 | Download the published v0.1.0 package and evidence. | Packages, notes, notices and evidence match the release identity. | Release is not draft, 18 assets, target `e30d168f`. Earlier byte reconciliation is historical. | VERIFIED |
| 2 | Build and run the native consumer example. | C and C++ adopters use the relocated installed package without private or SDL dependencies; consumers exercise the PCM API. | Candidate self-test rc=0 with relocated C/C++ consumers; `installed_consumer*` ctest 5/5; hosted ci and preview runs above including `native-windows-x64`. | VERIFIED |
| 3 | Inspect compatibility, safety, and performance evidence. | Scope, corpus, workload, uncertainty, and boundaries are clear. | `docs/support/v0.1.0.md` and sidecar (support-ledger self-test rc=0); performance receipt and bounded fuzz inventory in the fixed CTest set. | VERIFIED |
| 4 | Check player and trust limitations. | Scripted software behavior is not presented as perceptual, physical, signed, or notarized qualification. | Docs and support ledger state unsigned, not notarized, no hardware qualification, no live Playstead GB adapter. | VERIFIED |

## Goal Achievement

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | Clean relocated packages build/run external C/C++ consumers across the claimed host/compiler matrix without private or SDL dependencies; adopters can follow current integration guidance. | VERIFIED | Candidate self-test and installed-consumer tests pass locally; hosted ci jobs `native-linux-x64`, `native-macos-arm64`, `native-windows-x64` succeeded at the PR head and on main push, and the consumers now call `gbb_run_audio`. `examples/relocated-c/` and docs present. |
| 2 | The packaged macOS player passes automated legal-fixture load/input/video/audio/save/exit/reopen smoke, with device/perceptual limits separately recorded. | VERIFIED | Hosted `macos-player-package` and `player-package-smoke-macos` succeeded at the PR head; exact-tag receipt is historical. Software behavior only. |
| 3 | Published bytes match source/version/digests, include notices and notes, make only verified trust claims, and use fail-closed release gates. | VERIFIED | Release state re-confirmed (not draft, 18 assets, target `e30d168f`); gate self-test rc=0; byte reconciliation historical. No new branch-protection assertion is made. |
| 4 | Adopters can inspect a scoped support ledger plus reproducible speed, memory, trace, build, CI, and uncertainty evidence without mistaking subset results for broad compatibility. | VERIFIED | Ledger/sidecar present; ledger self-test rc=0; performance receipt is historical frozen evidence. |
| 5 | Maintainers can reproduce bounded loader/battery/API fuzz and boundary regression results under applicable sanitizers. | VERIFIED | CTest 184/184 locally; hosted `linux-asan-ubsan` succeeded in runs 38064419789 and 38064726000. |

**Score:** 5/5 truths verified (0 present, behavior-unverified)

## Required Artifacts

| Artifact group | Status | Evidence |
|---|---|---|
| Release workflows and gate verifiers | VERIFIED | Gate and candidate self-tests rc=0 with negative controls. |
| Relocated package and consumers (`examples/relocated-c`, `tests/consumers/{c,cpp}`) | VERIFIED | Substantive and wired through CTest `installed_consumer*`; audio smoke present in both. |
| Player verification and output-dir helper | VERIFIED | `test_verified_player_output_dir.py` 21 tests OK. |
| Support and performance evidence | VERIFIED | Ledger self-test rc=0; receipts historical. |
| Release docs and notices | VERIFIED | Files present and unchanged in role. |

PLAN `must_haves.artifacts` use inline path lists, so the artifact query is not treated as a pass; direct file, content and wiring evidence is recorded instead.

## Key Link Verification

| From | To | Via | Status |
|---|---|---|---|
| Installed C/C++ consumers | `gbb_run_audio` public API | CTest `installed_consumer*`; ci `native-*` lanes | WIRED |
| Relocated example | Installed `GabbaBoy::core` | CMake prefix/public headers | WIRED |
| Release-Please outputs | Exact-tag candidate jobs | `release_created`, `tag_name`, `sha` | WIRED (historical; release.yml unchanged by 06.1) |
| Draft assets | Published release | Download gate then publish | WIRED (historical; gate self-test rc=0) |
| Ledger | Source-bound sidecar | Tag blob/source SHA verifier | WIRED (self-test rc=0) |
| Player smoke | Output-dir helper | `verify-phase3-player.sh` invokes helper | WIRED |

## Data-Flow Trace (Level 4)

| Evidence artifact | Data source | Status |
|---|---|---|
| Published release inventory | GitHub release API (count/draft/target re-checked; per-asset hashes historical) | FLOWING |
| Support sidecar and performance receipt | Tagged ledger, fixed legal workload (frozen v0.1.0) | FLOWING (historical) |
| Audio consumer smoke | `gbb_run_audio` called on a real machine instance with caller-owned buffers | FLOWING |

## Behavioral Spot-Checks

Listed in Refresh Evidence above: ctest 184/184, installed-consumer subset 5/5, candidate and gate self-tests rc=0, ledger self-test rc=0, helper tests 21 OK. Measurement and bounded-fuzz self-tests were not re-run in this session.

## Probe Execution

No Phase 6 plan declares a shell probe. Not applicable.

## Requirements Coverage

All eight IDs are declared in PLAN frontmatter (06-01 through 06-07) and in REQUIREMENTS.md (`[x]`, traceability rows mapped to Phase 6). None is orphaned.

| Requirement | Source plans | Status | Evidence |
|---|---|---|---|
| SHIP-01 | 06-01, 06-02, 06-03, 06-06 | SATISFIED | Relocated C/C++ consumers pass locally and in hosted ci on Linux x64, macOS arm64, Windows x64 (MinGW-w64 GCC), now including `gbb_run_audio`. |
| SHIP-02 | 06-01, 06-02, 06-06 | SATISFIED | Scripted macOS player smoke; hosted player package jobs succeeded; software-only limitation explicit. |
| SHIP-03 | 06-01, 06-02, 06-04, 06-06, 06-07 | SATISFIED | Tag/source identity, release state re-confirmed; byte reconciliation historical. Unsigned/not notarized stated. |
| SHIP-04 | 06-03, 06-06, 06-07 | SATISFIED | Docs and relocated example present; no live GB adapter claimed. |
| SHIP-05 | 06-04, 06-06 | SATISFIED | Ledger and sidecar; self-test rc=0. |
| SHIP-06 | 06-04, 06-06 | SATISFIED | Historical performance receipt with samples, digests, environment, uncertainty. |
| SHIP-07 | 06-05, 06-06 | SATISFIED | CTest 184/184; hosted ASan/UBSan lane success. |
| SHIP-08 | 06-01, 06-06, 06-07 | SATISFIED | Gate self-test rc=0; main-push ci run success. No live branch-protection claim. |

## Anti-Patterns and Historical Limitations

| File/revision | Finding | Severity | Assessment |
|---|---|---|---|
| Frozen `v0.1.0` release notes | Heading link compares `v0.1.0...v0.1.0` | Warning | Immutable navigation defect; current `CHANGELOG.md` fixes it. |
| Frozen `v0.1.0` `verify-phase3-player.sh` | Recursive `rm -rf "$FINAL_ARTIFACT_DIR"` | Warning | Fixed on current source via the helper; the tag retains it. Tooling only, not shipped in the player package. |
| Future v0.1.1 PR #41 | Open, untouched | Info | Future-version work; no claim made. |

Code review (`fcbc47f`) is recorded clean and security (`47fc9c8`) 18/18 closed. This session did not independently scan for debt markers beyond what those gate artifacts record.

## Human Verification Required

None. Physical DMG behavior, perceptual audio/video, signing/notarization, MSVC/DLL, Windows archive-level preview smoke, and live Playstead Game Boy integration remain explicitly unclaimed or deferred and are outside these acceptance criteria; no manual UAT is invented for them.

## Gaps Summary

No must-have gaps. Phase 06.1 strengthened SHIP-01 by adding PCM-API calls to the installed C and C++ consumers, with hosted success on three native lanes. Frozen v0.1.0 evidence remains historical and is not re-run here.

---

_Verified: 2026-10-10T16:20:53Z_

_Verifier: the agent (gsd-verifier)_
