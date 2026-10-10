---
phase: GB-06-qualified-dmg-release-and-consumer-handoff
verified: 2026-10-10T12:00:00Z
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
covered_digest: "v3:sha256:ec31ebd166721863008100737e1fabda2fd2aaee8afb8e944f844ab9fe014abf"
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
**Verified:** 2026-10-10T12:00:00Z
**Status:** passed
**Re-verification:** Yes — freshness refresh at HEAD `70a44c4` (clean tree, branch `gsd/phase-06-verification-refresh`); no prior gaps. Covered inputs changed since the previous report: `.github/workflows/release.yml` (downloaded-player `GBB_VERIFIED_OUTPUT_DIR` now `$RUNNER_TEMP/release-player-downloaded`; job-level build/release-player-verified env dropped), `tests/scripts/verified_player_output_dir.py` and its tests (withdrawal failures reported without masking the publication error; 20 tests), and `tests/scripts/verify-release-candidate.sh` (static contract that every `GBB_VERIFIED_OUTPUT_DIR` in `release.yml` is rooted at runner temp, with mutation and positive self-checks).

## Refresh Evidence (this session vs historical)

Current-session, re-run by the verifier on the clean tree at `70a44c4` (macOS arm64). This is local evidence only; no hosted CI has run for this revision.

| Check | Result |
|---|---|
| `ctest --preset phase1` | 179/179 passed |
| `bash tests/scripts/verify-phase3-player.sh` (SDL 3.4.18) | 51 player tests listed and run, extracted-byte smoke passed (package SHA-256 `2c9c2d96...be4fb`). Local mode does not invoke `--publish`; publication is covered by the unit suite only. |
| `python3 -B -m unittest test_verified_player_output_dir` (from `tests/scripts`) | 20/20 OK |
| `bash tests/scripts/verify-release-candidate.sh --self-test` | rc=0; PASS: built archive, relocated external C/C++ consumers, receipt identity, digest tamper, draft/proof negatives, runner-temp output-dir contract |
| `verify-release-gates.sh --self-test`; `verify-support-ledger.py --self-test`; `run-bounded-fuzz.sh --self-test` | all exit 0 (fuzz libfuzzer fallback is not counted as a fuzz pass) |
| `git diff --check`; `git status` | clean |
| `release.yml` static check | Every `GBB_VERIFIED_OUTPUT_DIR` assignment (line 620) is `"$RUNNER_TEMP/release-player-downloaded"`; no checkout-relative `build/release-player-verified` remains |
| Live release | `gh release view v0.1.0`: `isDraft=false`, 18 assets, target `e30d168f7fc61de8db0a3801e7b1736362912cb7` (matches `git rev-parse v0.1.0^{commit}`) |
| Phase gates | `06-VALIDATION.md` refreshed (c55e65e); `06-SECURITY.md` 18/18 threats closed (164b037); code review clean with WR-01 fixed (daaaa18, 320fcc5, 70a44c4) |

Historical, carried forward and NOT re-run this session: per-asset ID/size/SHA-256 reconciliation of the 18 published assets, hosted exact-tag Linux x64/macOS arm64/Windows x64 receipts, and the recorded performance/support runs. They concern the frozen v0.1.0 tag and unchanged release machinery. This session only re-confirmed the count, draft state, and tag target.

Open items: PR #41 (release 0.1.1) remains open with no checks reported; it is future-version work and does not affect the v0.1.0 evidence. The previous report's mention of uncommitted `src/player/session.c` changes is obsolete: that change merged via PR #43 and belongs to Phases 4/5, outside this phase's covered inputs. The working tree is clean.

Frozen-tag note: v0.1.0 is immutable and predates later script fixes. Its tag retains the disclosed `rm -rf "$FINAL_ARTIFACT_DIR"` path in `verify-phase3-player.sh`, a checkout-relative verified-output directory in `release.yml`, and the pre-withdrawal-reporting helper. Current source uses the helper (root rejection, unlink of only expected artifact names, rollback of partial publication, non-masking withdrawal errors) and runner-temp output. This is a tooling limitation of the frozen tag, not a gap in current source, and published player bytes are unchanged. Not hardware, perceptual, signed, or notarized evidence; no live Playstead Game Boy adapter is claimed.

## User Flow Coverage

User story validation: `valid=true` under the canonical user-story validator.

| Step | Adopter action | Expected outcome | Evidence | Status |
|---|---|---|---|---|
| 1 | Download the published v0.1.0 package and evidence. | Published packages, notes, notices, and evidence match the qualified release identity. | Live release is `draft=false`, tag target `e30d168f7fc61de8db0a3801e7b1736362912cb7`. Earlier read-only download/hash reconciliation (historical, not re-run this session) matched all 18 assets to current API asset IDs, sizes, and SHA-256 metadata. Release notes and notices are present. | ✓ VERIFIED |
| 2 | Build and run the native consumer example. | C and C++ adopters can use the relocated installed package without private build-tree or SDL dependencies. | Clean-clone `bash tests/scripts/verify-release-candidate.sh --self-test` passed on current main `e4edf315909cb4d1068defe24e832b9f669d4be3`, including relocated C/C++ consumers and negative controls. Hosted exact-tag receipts cover Linux x64, macOS arm64, and Windows x64. | ✓ VERIFIED |
| 3 | Inspect compatibility, safety, and performance evidence. | Scope, corpus, workload, uncertainty, and boundaries are clear enough to judge fit. | Versioned ledger and source-bound sidecar identify bootless DMG-CPU-B, ROM-only/standard MBC1, 3/3 eligible derived cases, exclusions, and no physical observation. Performance receipt records fixed workload, build/environment, ten samples per mode, warmups, trace-pair digest, memory/RSS, and uncertainty. Bounded fuzz and boundary regressions are in the fixed inventory. | ✓ VERIFIED |
| 4 | Check player and trust limitations. | Scripted software behavior is not presented as perceptual, physical, signed, or notarized qualification. | Exact-tag macOS player smoke covers fixture load, input, frame/audio output, save, exit, and fresh-process reopen with scripted SDL backends. Published receipt says unsigned, not notarized, and not hardware-qualified; docs also state no live Playstead Game Boy adapter. | ✓ VERIFIED |

## Goal Achievement

The five roadmap success criteria are the contract. Plan-level truths were merged into these outcomes where they restated the same requirement; their added identity, failure-case, data-flow, and documentation specifics are checked in the evidence below.

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | Clean relocated packages build/run external C/C++ consumers across the claimed host/compiler matrix without private or SDL dependencies; adopters can follow current integration, ownership, time/input/output, save recovery, support, upgrade, troubleshooting, and Playstead-oriented example guidance. | ✓ VERIFIED | The current-main clean-clone candidate self-test built and ran relocated C and C++ consumers; exact-tag receipts and hosted package smokes cover all three named platform combinations. `examples/relocated-c/` and native-integration/release/save docs describe bounded half-dot work, timestamped input, caller-owned outputs, host battery ownership/recovery, and the GBA/mGBA-only Playstead boundary. No OS-floor or live GB integration claim is made. |
| 2 | The packaged macOS player passes automated legal-fixture load/input/video/audio/save/exit/reopen smoke, with device/perceptual limits separately recorded. | ✓ VERIFIED | Exact-tag macOS downloaded-candidate receipt and scripted SDL smoke cover the lifecycle. The release guide and support ledger explicitly limit evidence to software behavior; no physical device or perceptual claim is made. |
| 3 | Published bytes match source/version/digests, include notices and notes, make only verified trust claims, and use fail-closed release gates for current exact-head evidence and publication ordering. | ✓ VERIFIED | Current release API reports `draft=false` and tag source `e30d168f7fc61de8db0a3801e7b1736362912cb7`; an earlier read-only reconciliation (historical) matched all 18 downloaded assets; this session re-confirmed 18 assets, not draft, and the tag target to API IDs, sizes, and SHA-256. The source receipt, sidecar, manifest, notes, and notices are present. Stored exact-head evidence covers the release PR; PR #46's relevant current-main checks passed at its exact head and it was merged. Release-gate self-test passed. GitHub branch-rule access returned 403, so this report makes no new live branch-protection assertion. |
| 4 | Adopters can inspect a scoped support ledger plus reproducible speed, memory, trace, build, CI, and uncertainty evidence without mistaking subset results for broad compatibility. | ✓ VERIFIED | `docs/support/v0.1.0.md`, its source-bound sidecar, and the performance receipt disclose model, mapper/corpus scope, eligible denominator/exclusions, fixed workload, ten raw samples per mode, warmups, matching trace-pair digest, environment, memory/RSS, CI/build measurements, and uncertainty. No all-game compatibility claim or premature budget is made. |
| 5 | Maintainers can reproduce bounded loader/battery/API fuzz and boundary regression results under applicable sanitizers, with minimized findings in fast coverage and longer exploration separately capped. | ✓ VERIFIED | Integrated CTest passed 179/179, including the four player output-directory safety regressions (4/4). Bounded-fuzz self-test passed; plans, CMake inventory, runner, and CI wire deterministic loader/battery/API cases and applicable sanitizer coverage. Runtime-unavailable fuzz fallback is explicitly not counted as a fuzz pass. |

**Score:** 5/5 truths verified (0 present, behavior-unverified)

## Required Artifacts

| Artifact group | Expected | Status | Evidence |
|---|---|---|---|
| Release workflows and gate verifiers | Trusted source/tag routing, fail-closed checks, download validation, guarded publication/readback | ✓ VERIFIED | Workflows and `.github/scripts` verifiers are substantive and connected; release-gate and candidate self-tests passed, including negative controls. |
| Relocated package and consumer | Public CMake target and reproducible C/C++ example | ✓ VERIFIED | Example, package smoke, public headers, and hosted package receipts are wired; clean-clone self-test passed both consumer languages. |
| macOS player verification | Exact package lifecycle smoke using legal fixture | ✓ VERIFIED | Exact-tag downloaded-player receipt and scripted lifecycle smoke; no perceptual/device inference. |
| Support and performance evidence | Versioned ledger, exact-source sidecar, measured receipt | ✓ VERIFIED | Live release evidence carries the source-bound sidecar and performance receipt; support-ledger and performance self-tests passed. |
| Boundary regressions and bounded fuzz | Fixed deterministic inventory plus capped optional fuzzer | ✓ VERIFIED | CTest 179/179; output-dir safety tests 4/4; bounded-fuzz self-test passed. The new helper/test are wired by `verify-phase3-player.sh` in current main. |
| Release docs and third-party notices | Versioned notes, rights, recovery and trust guidance | ✓ VERIFIED | `CHANGELOG.md`, `THIRD_PARTY_NOTICES.md`, and `docs/release.md` are substantive. Current changelog points to the release page; frozen release notes retain the self-comparison issue listed below. |

PLAN `must_haves.artifacts` use inline path lists, so the installed artifact-query returned no enumerable entries; this is not treated as a pass. The table records direct file/content/wiring/release evidence instead.

## Key Link Verification

| From | To | Via | Status | Evidence |
|---|---|---|---|---|
| Relocated C/C++ example | Installed `GabbaBoy::core` | CMake prefix/public headers | ✓ WIRED | Candidate self-test and hosted package smokes configure/build/run external consumers after relocation. |
| Release-Please outputs | Exact-tag candidate jobs | Same-workflow `release_created`, `tag_name`, `sha` | ✓ WIRED | Workflow inspection and exact-source candidate receipts connect tag/source identity to package jobs; self-test rejects incorrect identity and negative controls. |
| Qualified draft assets | Published release | Downloaded-byte gate then one publish transition and readback | ✓ WIRED | Gate self-test passed; published API state is public and all 18 downloads matched the API inventory in the earlier reconciliation; count and state re-confirmed this session. |
| Tagged ledger/manifests | Support sidecar | Tag blob/source SHA verifier | ✓ WIRED | Published sidecar binds source and ledger digest; ledger self-test passed. |
| Measurement workload | Performance receipt | Trace-on/off digest comparison and release identity | ✓ WIRED | Source-bound receipt includes equal output digest and samples; performance self-test passed. |
| Public loader/battery/API | Deterministic tests and fuzz harnesses | CTest inventory, ASan/UBSan CI, bounded fuzz runner | ✓ WIRED | Fixed inventory passed 179/179; fuzz self-test passed; sanitizer and caps are present in CI/runner. |
| Player smoke output path | Safe directory helper | Python helper invoked before artifact copy/write | ✓ WIRED | `verify-phase3-player.sh` invokes `verified_player_output_dir.py`; four regressions cover unrelated file preservation, symlink target preservation, root rejection, and directory collision. |

## Data-Flow Trace (Level 4)

| Evidence artifact | Data source | Trace result | Status |
|---|---|---|---|
| Published release inventory | Live GitHub release API and downloaded asset bytes | All 18 current assets reconciled by ID, size, and SHA-256 | ✓ FLOWING |
| Support sidecar | Tagged source ledger blob and fixture/corpus manifests | Sidecar binds source SHA, blob digest, and identities | ✓ FLOWING |
| Performance receipt | Fixed legal workload and exact-source build/CI records | Samples, environment, output digest, memory, and uncertainty recorded | ✓ FLOWING |
| Release/package smoke | Downloaded exact-tag package | External consumers and scripted player smoke results tied to candidate identity | ✓ FLOWING |

## Behavioral Spot-Checks

| Behavior | Command/evidence | Result | Status |
|---|---|---|---|
| Integrated CTest and boundary regressions | `ctest --preset phase1` (orchestrator) | 179/179 pass; helper unittest suite 20/20 (both re-run this session) | ✓ PASS |
| Clean-clone candidate, relocated consumers, and negative controls | `bash tests/scripts/verify-release-candidate.sh --self-test` | rc=0 on the clean tree at `70a44c4` this session (relocated C/C++ consumers, negative controls, runner-temp output contract); earlier clean-clone pass at main `e4edf315` is historical. | ✓ PASS |
| Release gate, support ledger, performance receipt, bounded-fuzz self-tests | `verify-release-gates.sh --self-test`; `verify-support-ledger.py --self-test`; `measure-release-baseline.sh --self-test`; `run-bounded-fuzz.sh --self-test` | All exit 0, re-run this session (measurement self-test not re-run; carried from validation) | ✓ PASS |
| Published bytes | `gh release view v0.1.0` inventory (count, draft, target); per-asset hashes from earlier reconciliation | 18 assets, not draft, target e30d168; byte reconciliation historical | ✓ PASS |
| Diff whitespace check | `git diff --check` | Passed | ✓ PASS |

## Probe Execution

No Phase 6 plan declares a shell probe, and no Phase 6 conventional probe was found. Not applicable.

## Requirements Coverage

| Requirement | Source plans | Status | Evidence |
|---|---|---|---|
| SHIP-01 | 06-01, 06-02, 06-03, 06-06 | ✓ SATISFIED | Hosted package matrix receipts plus current-main clean-clone relocated C/C++ consumer run. |
| SHIP-02 | 06-02, 06-06 | ✓ SATISFIED | Exact-tag downloaded macOS player lifecycle smoke; software-only limitation explicit. |
| SHIP-03 | 06-01, 06-02, 06-04, 06-06, 06-07 | ✓ SATISFIED | Tag/source identity, 18/18 downloaded asset reconciliation, notices, notes, and truthful unsigned/notarized state. Frozen note link limitation is informational. |
| SHIP-04 | 06-03, 06-06, 06-07 | ✓ SATISFIED | Native and release documentation, relocated example, save recovery guidance, honest Playstead boundary. |
| SHIP-05 | 06-04, 06-06 | ✓ SATISFIED | Versioned support ledger and exact-source sidecar with scoped corpus denominator/exclusions. |
| SHIP-06 | 06-04, 06-06 | ✓ SATISFIED | Fixed-workload source-bound performance evidence with samples, digests, environment, memory, and uncertainty. |
| SHIP-07 | 06-05, 06-06 | ✓ SATISFIED | Deterministic boundary inventory, applicable sanitizer coverage, and capped fuzz runner; CTest 179/179. |
| SHIP-08 | 06-01, 06-06, 06-07 | ✓ SATISFIED | Release workflow/gate tests and exact-head merge evidence. No new current branch-protection claim is made because the live rules endpoint was inaccessible (403). |

No requirement mapped to Phase 6 in `REQUIREMENTS.md` is orphaned. PR #41 for a future v0.1.1 is currently recorded as `action_required` for its workflows; it is an operational condition for that future version PR and does not change the published v0.1.0 evidence. No action was taken on it.

## Anti-Patterns and Historical Limitations

| File/revision | Finding | Severity | Assessment |
|---|---|---|---|
| Frozen `v0.1.0` release notes | Heading link compares `v0.1.0...v0.1.0` | Warning | It is a navigation defect. The notes are present; current `CHANGELOG.md` fixes the link, but the published body is immutable and still contains the old link. |
| Frozen `v0.1.0` `tests/scripts/verify-phase3-player.sh` | Calls `rm -rf "$FINAL_ARTIFACT_DIR"` | Warning | The tag's verification script has a recursive output-directory removal path. Current main replaces it with `verified_player_output_dir.py`, which rejects root destinations and unlinks only the two expected artifact paths; its four safety regressions pass. This helper is release/verification tooling, not part of the published player package. The v0.1.0 tag does not contain the fix; users reproducing verification directly from that tag should use the current main version of the script/helper. This historical source limitation does not invalidate the already-built package bytes or the adopter's core consumer path. |
| Future v0.1.1 PR #41 | Required workflows `action_required` at exact head `7e953ca552551a151c5837fd88add8ca879b69bc` | Info | Does not block v0.1.0 qualification; no merge/release claim is made for that future PR. |

The refreshed standard-depth code review found zero current findings on the helper, regression tests, and wired script. Security report confirms the current helper path and retains the unsigned/notarized/hardware limitations. No unreferenced `TBD`, `FIXME`, or `XXX` debt marker was identified in the current reviewed helper path. `06-UI-REVIEW.md` correctly records UI review as not applicable; this phase packages the existing player rather than changing its visual interface.

## Human Verification Required

None. Automated release/package evidence covers the phase criteria. Physical DMG behavior, perceptual audio/video, signing/notarization, and live Playstead Game Boy integration remain explicitly unclaimed and are outside these acceptance criteria; no manual UAT is invented for them.

## Gaps Summary

No must-have gaps remain. The published limited-DMG package and its evidence are downloadable and match the tagged source and current asset digests; native consumer reproduction and bounded safety/performance evidence are present and wired. The immutable v0.1.0 tag retains two historical source issues: a self-comparison changelog link and the recursive output-directory deletion in its verification script. Both are disclosed above; the latter is fixed and tested on current main but is not present in the frozen tag. Neither issue changes the shipped player bytes or the outcome of the five roadmap success criteria. Current branch-protection rules were not freshly inspected because the GitHub rules endpoint returned 403; stored exact-head release evidence and current-main PR #46 check evidence are distinguished from that unavailable live setting.

---

_Verified: 2026-10-10T12:00:00Z_

_Verifier: the agent (gsd-verifier)_
