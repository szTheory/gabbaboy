---
phase: GB-06-qualified-dmg-release-and-consumer-handoff
verified: 2026-10-09T02:34:07Z
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
  - .planning/phases/GB-06-qualified-dmg-release-and-consumer-handoff/06-REVIEW-DISPOSITION.md
  - .planning/phases/GB-06-qualified-dmg-release-and-consumer-handoff/06-REVIEW.md
  - .planning/phases/GB-06-qualified-dmg-release-and-consumer-handoff/06-SECURITY.md
  - .planning/phases/GB-06-qualified-dmg-release-and-consumer-handoff/06-VALIDATION.md
  - .planning/phases/GB-06-qualified-dmg-release-and-consumer-handoff/COVERAGE.md
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
  - tests/scripts/measure-release-baseline.sh
  - tests/scripts/run-bounded-fuzz.sh
  - tests/scripts/verify-phase3-player.sh
  - tests/scripts/verify-release-candidate.sh
  - tests/scripts/verify-support-ledger.py
  - tests/test_battery_fuzz.c
  - tests/test_fuzz_core.c
  - tests/test_loader_fuzz.c
covered_digest: "v3:sha256:9cdde104d282992c228461bf7d54075e3ed291d5cf010767b37367b66850bcc0"
behavior_unverified: 0
overrides_applied: 0
---

# Phase 6: Qualified DMG Release and Consumer Handoff Verification Report

**Phase Goal:** As a project adopter, I want to download a qualified limited-DMG release, reproduce native integration, and assess its actual compatibility, safety, and performance evidence, so that I can judge whether it fits my project and what its limits are.
**Verified:** 2026-10-09T02:34:07Z
**Status:** passed
**Re-verification:** No — initial verification

## User Flow Coverage

User story: “As a project adopter, I want to download a qualified limited-DMG release, reproduce native integration, and assess its actual compatibility, safety, and performance evidence, so that I can judge whether it fits my project and what its limits are.”

| Step | Adopter action | Expected outcome | Evidence in codebase and release | Status |
|---|---|---|---|---|
| 1 | Open the v0.1.0 release and download the core archive for a tested platform. | A published release presents versioned platform packages, notices, release notes, and evidence attachments. | Live GitHub release API: `v0.1.0`, published, tag target `e30d168f7fc61de8db0a3801e7b1736362912cb7`, 18 assets. All 18 downloaded assets matched current API asset IDs, sizes, and SHA-256 digests. `docs/release.md` explains checksums and extraction. The immutable published notes' heading links to a self-comparison (`v0.1.0...v0.1.0`); the current working-tree changelog fixes the link, but the published body remains unchanged. | ✓ VERIFIED |
| 2 | Follow the relocated native C/C++ example against the package. | External consumers build against `GabbaBoy::core` using public headers and no source/build-tree or SDL dependency. | `examples/relocated-c/`, `docs/native-integration.md`, hosted Linux/macOS/Windows downloaded-package receipts, and the passing release-candidate self-test (relocated C and C++ consumers). Local `preview_package_smoke` also passed. | ✓ VERIFIED |
| 3 | Review support, performance, and safety evidence before deciding whether to adopt. | The adopter can see the tested model, corpus denominator, exclusions, fixed-workload measurements, and bounded safety evidence without mistaking them for broad game compatibility. | Tracked ledger and source-bound sidecar identify bootless DMG-CPU-B, standard MBC1/ROM-only limits, 3/3 eligible derived cases, no physical observations, and exclusions. Performance receipt is source-bound and includes ten samples per mode, two warmups, equal trace-pair digest, environment, RSS, build and exact-source hosted-check data, and uncertainty. Fuzz and boundary regressions are in CTest/CI. | ✓ VERIFIED |
| 4 | Check trust and known limitations. | Signing, notarization, hardware, and perceptual claims match the exact evidence available. | Published release receipt records `signed: false`, `notarized: false`, and `hardware_qualified: false`; release guide and ledger state no physical DMG or perceptual audio/video qualification and no live Playstead GB adapter. | ✓ VERIFIED |

The adopter outcome is observable: the published package and its evidence can be downloaded, the native integration path is reproducible, and the release states the scope and limits needed to judge fit.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | Clean relocated packages build and run external C/C++ consumers on the claimed Linux x64, macOS arm64, and Windows x64 runner/compiler combinations without private or SDL dependencies; current adopter docs and the Playstead-oriented example state the actual integration boundary. | ✓ VERIFIED | Hosted exact-tag package receipts and downloaded consumer smokes cover all three core platforms. `tests/scripts/verify-release-candidate.sh --self-test` rebuilt and installed the package, relocated the prefix, and compiled external C/C++ consumers. The example/docs show bounded half-dot work, timestamped input, caller-owned output buffers, host battery ownership, and the current GBA/mGBA-only Playstead boundary. No OS-floor or live GB integration claim is made. |
| 2 | The packaged macOS player passes legal-fixture load/input/video/audio/save/exit/reopen automation, while device and perceptual limits are separated. | ✓ VERIFIED | Exact-tag release candidate evidence records the macOS player archive download and scripted SDL dummy audio/video smoke; the workflow's macOS downloaded-candidate job completed its player smoke. `docs/release.md` limits this to software-path evidence. No physical device, hotplug, or perceptual result is claimed. |
| 3 | Published bytes match the qualified source/version/digests, include release notes/notices, and carry only verified trust claims; publication gates use current exact-head evidence and fail closed. | ✓ VERIFIED | Live release API says published `v0.1.0` targets source `e30d168f7fc61de8db0a3801e7b1736362912cb7`. Freshly downloaded 18/18 asset bytes matched API IDs, sizes, and SHA-256. `release-receipt.json` binds release ID `407367131`, tag, source, and asset inventory; its `draft: true` is the recorded pre-publication qualification snapshot, generated before the separate publish step, not the current release state. The API confirms `draft=false`. PR #31 fixed post-publish JSON readback; current verifier and self-tests cover direct JSON parsing. PR #33 adds a negative ordering regression. Branch protection currently requires strict `required-native`, `fixture-repro`, and `preview-package-smoke` contexts. Source PR #13 merged at exact head `e30d168f7fc61de8db0a3801e7b1736362912cb7` with `required-native` successful; the actual release run's candidate jobs and final asset gate completed before the publish transition. That run failed only on its post-publish readback step; the subsequent PR #31 repair and fresh read-only download reconciliation succeeded. Release notes and legal notices are present. The frozen release body still has a self-comparison heading link with an empty range; this does not affect the notes' presence or artifact/source qualification. |
| 4 | An adopter can inspect a truthful versioned support ledger and reproducible speed, memory, trace, build, CI, and uncertainty evidence without subset results being presented as all-game compatibility. | ✓ VERIFIED | `docs/support/v0.1.0.md` names model, boot profile, mapper scope, corpus revision, 3 eligible/3 executed cases, exclusions, failures, evidence classes, and known issues. Downloaded sidecar binds the source SHA and tagged ledger. Published performance receipt is source-bound, reports a fixed legal workload, ten raw samples per mode, warmups, equal trace-pair digest, RSS/memory, build environment, CI durations, uncertainty, and limits. It explicitly keeps allocation evidence to the separate `audio_no_alloc` scope and sets no premature budget. Claims explicitly exclude broad compatibility. |
| 5 | Maintainers can reproduce bounded loader/battery/API boundary regressions under applicable sanitizers, promote minimized findings into fast coverage, and run longer fuzzing separately with caps. | ✓ VERIFIED | Current CTest inventory passed 176/176, including the deterministic loader/battery/API regressions and fixed test inventory. `tests/scripts/run-bounded-fuzz.sh` documents bounded fast and longer modes; CI has a Linux ASan/UBSan lane. Downloaded release source and the published receipt identify the qualified source. The documented compiler/runtime-unavailable fallback retains deterministic sanitizer tests and does not claim a fuzz pass for an unavailable runtime. |

**Score:** 5/5 truths verified (0 present, behavior-unverified)

### Required Artifacts

| Artifact group | Expected | Status | Details |
|---|---|---|---|
| Release workflow and gate verifiers | Trusted exact-head source/tag flow, one guarded publish transition, downloaded-byte validation, post-publish readback | ✓ VERIFIED | `.github/workflows/release-please.yml`, `.github/workflows/release.yml`, `verify-release-gates.sh`, source-proof and published-asset verifiers are substantive and connected. Negative tests reject stale, skipped, failed, wrong-app, wrong-tag, changed-byte, published-before-gate, and malformed-readback cases. |
| Core packages and relocated consumers | Three platform archives, public CMake export, C/C++ example and current adoption docs | ✓ VERIFIED | Current published release assets reconcile to API; hosted downloaded package smokes and local release-candidate self-test exercise relocation and external consumer builds. No SDL dependency is required by the core export. |
| macOS player package | Legal fixture smoke over load, input, frame/audio, save, exit, and fresh-process reopen | ✓ VERIFIED | Candidate workflow and receipt record the exact downloaded player smoke with scripted SDL backends; limitations are documented. |
| Support, performance, and safety evidence | Tracked ledger, tagged source-bound sidecar, measured receipt, bounded fuzz and boundary regressions | ✓ VERIFIED | Public release has support/performance receipts; local support verifier self-test passed. CTest and hosted sanitizer evidence cover deterministic regressions. |
| Release notes and third-party notices | Versioned notes, fixture/runtime rights and digests, trust and recovery guidance | ✓ VERIFIED | `CHANGELOG.md`, `THIRD_PARTY_NOTICES.md`, and `docs/release.md` are present and linked to the release/sidecar. The standard-depth review warning is closed in `06-REVIEW-DISPOSITION.md`. |

The installed runtime artifact query returned zero enumerable entries for these plans' inline path-list format, so artifact status above comes from direct file, content, wiring, build, release, and test inspection rather than treating that empty query result as a pass.

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| Protected version PR | Trusted release tag and source SHA | Release Please outputs and exact-head checks | ✓ WIRED | PR #13 merged through protection at the exact final source SHA. Strict main rules require `required-native`, `fixture-repro`, and `preview-package-smoke`; required source checks have current exact-head evidence. |
| Trusted tag | Candidate platform assets | Same-workflow release outputs and candidate jobs | ✓ WIRED | Candidate receipts and platform manifest identify `v0.1.0` and the same full source SHA; downloaded Linux/macOS/Windows core and macOS player smokes are recorded. |
| Qualified draft bytes | Published release | Final downloaded-byte gate, pre-transition API check, single publish, post-publish inventory verifier | ✓ WIRED | Workflow ordering and negative self-tests verify the gate precedes publication. Current published API inventory and a fresh download reconcile all 18 assets. Post-publish readback was repaired by PR #31 and the current verifier's self-test passes. |
| Relocated package | C/C++ example and public `GabbaBoy::core` target | CMake prefix and public headers | ✓ WIRED | Example is configured outside the prefix/source tree and built by the candidate self-test and hosted package smokes. |
| Tagged source and manifests | Support sidecar and measurement receipt | Ledger verifier and measurement workflow | ✓ WIRED | Sidecar carries tag/source/ledger blob and fixture/corpus identity; performance receipt carries the same source SHA and workload digest evidence. |
| Public input APIs | Boundary tests and fuzz processors | CTest fixed inventory, ASan/UBSan, bounded fuzz script | ✓ WIRED | Regression tests are in the fixed inventory; compiler-integrated harnesses call bounded public loader/battery/API paths. |

### Data-Flow Trace (Level 4)

No dynamic UI or page rendering is part of this release phase. The adoption evidence is produced by release workflow jobs and static, source-bound artifacts. The live release API asset inventory flows to freshly downloaded files; each downloaded byte stream was hashed and matched against API asset ID, size, and digest (18/18). The source SHA flows into candidate and support/performance receipts and matches the published tag target.

| Artifact | Data variable | Source | Produces real evidence | Status |
|---|---|---|---|---|
| Published asset inventory | asset ID/name/size/SHA-256 | Current GitHub Release API plus fresh asset downloads | Yes; all 18 assets reconciled | ✓ FLOWING |
| Support sidecar | tag/source SHA/ledger blob/manifest identities | Tagged source ledger and fixture/corpus manifests | Yes; source-bound sidecar published | ✓ FLOWING |
| Performance receipt | workload samples/digests/environment/CI durations | Exact-tag measurement and hosted check records | Yes; 10 samples per mode and matching output digest | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Full local core and package inventory | `ctest --test-dir build --output-on-failure` | `100% tests passed, 0 tests failed out of 176`; `preview_package_smoke` passed | ✓ PASS |
| Relocated package C/C++ consumers and candidate-gate negatives | `bash tests/scripts/verify-release-candidate.sh --self-test` | Built/installed package, relocated prefix, built external C and C++ consumers; tampered archive, published draft, duplicate asset, stale proof, wrong tag, notice/build receipt mutations, and extraction escape rejected | ✓ PASS |
| Release gate and exact-head negative controls | `bash .github/scripts/verify-release-gates.sh --self-test` | Stale, failed, omitted, mixed, wrong-app, wrong-tag/source/digest, sidecar, and release-order controls rejected; gate configuration passed | ✓ PASS |
| Published asset readback verifier | `python3 .github/scripts/verify-published-release-assets.py --self-test` | Direct JSON API parsing and changed/malformed inventory rejection passed | ✓ PASS |
| Tagged support ledger and sidecar checks | `python3 tests/scripts/verify-support-ledger.py --self-test` | Tag/blob binding, scope, corpus order, digests, malformed input, denominator and claim controls passed | ✓ PASS |
| Current published release bytes | `gh release download v0.1.0 --repo szTheory/gabbaboy` plus API ID/size/SHA-256 reconciliation | 18 assets downloaded; 18/18 matched live API metadata | ✓ PASS |

### Probe Execution

No Phase 6 plan declares a shell probe. The conventional project search found no Phase 6-specific probe; the unrelated Mooneye candidate probe is not part of this release phase's requirements. Phase 6 fuzz/boundary claims were checked through the fixed CTest inventory, hosted sanitizer evidence, and the dedicated verifier scripts.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| SHIP-01 | 06-01, 06-02, 06-03, 06-06 | Relocated release packages and external C/C++ consumers across the claimed host/compiler combinations without private/SDL core dependencies | ✓ SATISFIED | Current 18-asset release reconciliation; exact-tag platform receipts/smokes; local relocated C/C++ candidate self-test. |
| SHIP-02 | 06-02, 06-06 | Packaged macOS player legal-fixture load/input/video/audio/save/exit/reopen smoke with limits stated | ✓ SATISFIED | Exact downloaded macOS player smoke in candidate workflow/receipt; software-only and perceptual/device limits explicit. |
| SHIP-03 | 06-01, 06-02, 06-04, 06-06, 06-07 | Exact-byte source-bound release, notices, notes, and verified trust state | ✓ SATISFIED | Published tag/source SHA and 18 current assets reconciled; release notes and notices are present, and unsigned/notarized fields are truthful. The frozen release notes have a non-blocking self-comparison link defect noted above. |
| SHIP-04 | 06-03, 06-06, 06-07 | Current integration, ownership, time/input/output, save recovery and troubleshooting docs, reproducible Playstead-oriented example, honest status | ✓ SATISFIED | `docs/native-integration.md`, `docs/release.md`, README, save docs, relocated C example, and explicit Playstead GBA/mGBA-only boundary. |
| SHIP-05 | 06-04, 06-06 | Versioned support ledger with model, mapper, corpus denominator, exclusions, and known issues | ✓ SATISFIED | Tracked v0.1.0 ledger plus downloaded sidecar; scoped 3/3 software corpus and no broad compatibility claim. |
| SHIP-06 | 06-04, 06-06 | Reproducible performance/build/CI baseline with digest, samples, environment, uncertainty and variance-based budgets | ✓ SATISFIED | Published performance receipt includes fixed workload, exact source/build environment, ten samples/mode, digest pair, RSS, build/check timing, uncertainty and advisory-only limits. No unsupported budget or allocation claim. |
| SHIP-07 | 06-05, 06-06 | Bounded loader/battery/API fuzz and sanitizer boundary regression, with minimized cases in fast coverage | ✓ SATISFIED | 176/176 local tests; deterministic fuzz regression inventory; hosted Linux ASan/UBSan; bounded optional longer fuzz runner. |
| SHIP-08 | 06-01, 06-06, 06-07 | Bot CI, exact-head merge eligibility, release trigger/cache/failure gates, and no unsafe publication path | ✓ SATISFIED | Live strict branch rules and exact PR evidence, release workflow review, release-gate negative tests, actual release run and repair PRs #31/#33; current API/download reconciliation. |

All eight requirement IDs declared by the phase map are claimed by the plan set and verified above. Current `REQUIREMENTS.md` marks SHIP-01 through SHIP-08 Complete with evidence notes; those statuses agree with the implementation and live release evidence described here.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---:|---|---|---|
| `git show v0.1.0:CHANGELOG.md` / published release body | — | Self-comparison release link | Warning | The frozen notes link `v0.1.0...v0.1.0`, so the heading does not open a commit-range comparison. The current working-tree changelog links to the release page, but that correction postdates the immutable release. This is a navigation defect; notes, notices, package qualification, and trust claims remain present and accurate. |

No unreferenced TBD/FIXME/XXX markers or user-visible stub patterns were found in the inspected Phase 6 implementation files. The optional empty hosted-row helper return guards the no-input path; the published exact-tag receipt contains hosted rows. `git diff --check` passed. The review disposition closes the source-tree changelog warning; the published release-body link defect remains as the non-blocking note above.

### Human Verification Required

None. This verification is based on reproducible package, workflow, release, and evidence outputs. Physical DMG behavior, perceptual audio/video, Developer ID signing/notarization, and a live Playstead GB adapter are explicitly unclaimed and are not Phase 6 acceptance claims requiring invented manual UAT.

### Gaps Summary

No must-have gaps remain. The published `v0.1.0` release and its current downloadable bytes reconcile to the qualified source and exact asset inventory. Consumer integration, support scope, safety, and performance evidence are present and wired. The release workflow's original run failed after publication during readback; the direct-JSON verifier fix was merged via PR #31, the publish-order negative test was added via PR #33, and the present published API and fresh bytes reconcile. The receipt's `draft: true` records its pre-publication qualification snapshot, while current live API state is published (`draft=false`). One non-blocking limitation remains in the immutable release notes: their comparison link has identical start and end tags, so it cannot show the commit range; the current changelog source has a release-page link.

---

_Verified: 2026-10-09T02:34:07Z_
_Verifier: the agent (gsd-verifier)_
