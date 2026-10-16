# Phase 14 execution evidence

Execution remains active until all 13 plans and the phase goal gates pass. Physical CGB-E remains UNKNOWN/POLICY. Fixture-author expectations, actual execution and evaluator dispositions remain separate. Both auto-advance flags are false.

Runtime identity: installed `@opengsd/gsd-core` 1.16.0 through `$HOME/.codex/gsd-core/bin/gsd-tools.cjs`; unqualified `gsd_run` resolved another installation and is not used for workflow authority. The runtime selected sequential dispatch because `origin/HEAD` was unresolved.

## Wave 1

Native Debug source `ed41d6f`: `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --parallel 4 --output-on-failure --no-tests=error --output-junit phase14-wave1-final.xml` passed **1003/1003**, zero failures/errors/skips. JUnit SHA-256 `b63492c6f80428230bab0ef7ba164d635b55129fdb2aab3af6867b34395dc170`; local generated file `build/phase14-wave1-final.xml`. Evidence is revision-bound; this is not hosted CI or physical hardware proof.

The first serial gate was stopped after four stale Mooneye unsupported-stop failures (exit 130). The next complete gate failed 6/1,003 in 72.21 seconds: model-gate tags and independent PCM table expectations were stale. Corrections retained author pass expectations, recorded two exact guest xfails, preserved false-pass controls, added helper gate tags and independent three-model PCM policy mutations. These failed attempts are not passes. Future model-visible changes must include the runner/dispositions, model-gate scanner and independent table checks in focused verification.

Capability checks: schema drift did not block; codebase drift reported `no-structure-md`; UI safety reported no frontend files and did not block. Upcoming key links owned by the upcoming wave are intentionally deferred to that wave; no unmet prior-wave link is waived.

## Wave 2

Native Debug source `ffb2644`: `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --parallel 2 --output-on-failure --no-tests=error --output-junit phase14-wave2.xml` passed **1009/1009**, zero failures/errors/skips. JUnit SHA-256 `b8742366c983d4859915cc0985cd497b5b164cb20437c23fbe5783fc199a2bc9`; local generated file `build/phase14-wave2.xml`. Evidence is revision-bound; this is not hosted CI or physical hardware proof.

The initial configure failed before build because three CMake consumers assumed every admitted AGE fixture had row-oracle metadata. The correction added explicit versioned row/image classes, preserved the 13 prior row registrations, kept six image cases admitted/pending execution, and added an unknown-class rejection control. The failed configure is not counted as a pass. A later full run failed 3/1,007 in 123.31 seconds because external/speed disposition consumers assumed absent image bytes or all-AGE row membership. The follow-up enforces exact row/image identities, explicit admitted-not-executed image state and the unchanged speed-row set; intended image-state, extra-case and missing-pin controls pass. Manifest extensions must enumerate all registration and disposition consumers before focused verification. A later four-worker rerun was stopped after host-contention timeouts; read-only inspection measured load 65.63 on 18 logical CPUs. No timeout was increased. A bounded representative AGE case then passed in 0.94 seconds before the lower-concurrency retry. That stopped run is not a pass.

Capability checks: schema drift did not block; codebase drift reported `no-structure-md`; UI safety reported no frontend files and did not block. Upcoming key links owned by the upcoming wave are intentionally deferred to that wave; no unmet prior-wave link is waived.

## Wave 3

Native Debug source `1580533`: `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --parallel 2 --output-on-failure --no-tests=error --output-junit phase14-wave3.xml` passed **1018/1018**, zero failures/errors/skips. JUnit SHA-256 `e9acdd014db8f0ce9a27650d15b19a628b4269019cfd84800dac309a4f324e22`; local generated file `build/phase14-wave3.xml`. Evidence is revision-bound; this is not hosted CI or physical hardware proof.

The initial full gate failed 1/1,018 in 219.11 seconds because unexecuted DMG length-retention limitations were incorrectly tagged as expected failures. Source and documentation now use UNKNOWN/research classification, preserve the unresolved independent-DMG-fixture obligation and do not fabricate a corpus disposition. The focused correction passed 15/15 before this full rerun.

Capability checks: schema drift did not block; codebase drift reported `no-structure-md`; UI safety reported no frontend files and did not block. Upcoming key links owned by the upcoming wave are intentionally deferred to that wave; no unmet prior-wave link is waived.

## Wave 4

Native Debug source `d08b728`: `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --parallel 2 --output-on-failure --no-tests=error --output-junit phase14-wave4.xml` passed **1025/1025**, zero failures/errors/skips. JUnit SHA-256 `814e1ced92d866f89d176f1a7112f19a7936e71cd6624f8923eb0455c0b602f1`; local generated file `build/phase14-wave4.xml`. Evidence is revision-bound; this is not hosted CI or physical hardware proof.

Capability checks: schema drift did not block; codebase drift reported `no-structure-md`; UI safety reported no frontend files and did not block. Upcoming key links owned by the upcoming wave are intentionally deferred to that wave; no unmet prior-wave link is waived.

## Phase-boundary remote triage

The live GitHub query found zero open issues and one open release-please PR, [#70](https://github.com/szTheory/gabbaboy/pull/70), proposing v0.2.0. It remains pending Phase 15 acceptance/release gates and is outside this execution. The installed GitHub workflow skill has no `ci_monitor.cjs` at its documented path or in its installed skill/runtime tree; monitoring uses the available GitHub API fallback, with exact-head/event checks retained.

## Early hosted seam

Draft [PR #71](https://github.com/szTheory/gabbaboy/pull/71) was opened at `74bad9a53867584190e7be66c32d6c387b9f03b3` after the Wave 4 local gate. PR-event runs started: [CI](https://github.com/szTheory/gabbaboy/actions/runs/38798590344), [fixtures](https://github.com/szTheory/gabbaboy/actions/runs/38798590343), and [preview](https://github.com/szTheory/gabbaboy/actions/runs/38798592496). They were running when recorded; no success is inferred. Later code, review fixes and final metadata need their own eligible exact-head checks before merge. The release-please PR remains pending Phase 15.

The initial head `74bad9a53867584190e7be66c32d6c387b9f03b3` subsequently passed all 19 jobs across those three PR-event runs: fixture reproduction 7/7, CI 8/8 (including Linux ASan/UBSan, Windows/macOS native, CMake floor and player package), preview/installed/downloaded-byte smoke 4/4. Every job was completed/success; zero skipped jobs. This is historical evidence for work through Wave 4, not proof for later commits or merge authorization for a later head.

## Wave 5

Native Debug source `8b9bb46`: `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --parallel 2 --output-on-failure --no-tests=error --output-junit phase14-wave5.xml` passed **1032/1032**, zero failures/errors/skips. JUnit SHA-256 `870c404d66f3873cb48de05058c2ff46ca6dd68542d8e939aee72961f5bf9ce6`; local generated file `build/phase14-wave5.xml`. Evidence is revision-bound; this is not hosted CI or physical hardware proof.

Capability checks: schema drift did not block; codebase drift reported `no-structure-md`; UI safety reported no frontend files and did not block. Upcoming key links owned by the upcoming wave are intentionally deferred to that wave; no unmet prior-wave link is waived.

## Wave 6

Native Debug source `dbef238`: `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --parallel 2 --output-on-failure --no-tests=error --output-junit phase14-wave6.xml` passed **1107/1107**, zero failures/errors/skips. JUnit SHA-256 `7cd0560e6148d479de79973653ed12ac1aa70066fc1d99a3e526b4f78837bd8d`; local generated file `build/phase14-wave6.xml`. Evidence is revision-bound; this is not hosted CI or physical hardware proof.

The SameSuite APU run completed all 70 cases with 8 actual guest passes, 62 exact xfails and 4,784 assertions; all 70 author expectations remain pass. Existing four DMA outputs are retained. All 74 SameSuite outputs reproduce byte-identically; total corpus inventory is 109 admitted ROM outputs with zero pending output bytes and 107 required case identities. Six admitted AGE image cases still await execution in 14-09. CTest success is evaluation-contract success and does not convert those 62 guest failures to passes.

Capability checks: schema drift did not block; codebase drift reported `no-structure-md`; UI safety reported no frontend files and did not block. Upcoming key links owned by the upcoming wave are intentionally deferred to that wave; no unmet prior-wave link is waived.

## Wave 7

Native Debug source `8ae187324f101393b35153f1b180b769d4ecefc3`: `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --parallel 2 --output-on-failure --no-tests=error --output-junit phase14-wave7.xml` passed **1117/1117**, zero failures/errors/skips. JUnit SHA-256 `d88f6f4956981164cedcc76ae512b20117886bd1a421f711abc276722b0f9dfe`; local generated file `build/phase14-wave7.xml`. Evidence is revision-bound; this is not hosted CI or physical hardware proof.

Capability checks: schema drift did not block; codebase drift reported `no-structure-md`; UI safety reported no frontend files and did not block. Upcoming key links owned by the upcoming wave are intentionally deferred to that wave; no unmet prior-wave link is waived.

## Wave 8

Native Debug source `65bcbbc5872f17322ebae998c0653b4849490f74`: `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --parallel 2 --output-on-failure --no-tests=error --output-junit phase14-wave8.xml` passed **1123/1123**, zero failures/errors/skips. JUnit SHA-256 `eb89761460e73f90d39503fdd2b77c766ee3ef5c1a70b5c0c76044bfce577c40`; local generated file `build/phase14-wave8.xml`. Evidence is revision-bound; this is not hosted CI or physical hardware proof.

Capability checks: schema drift did not block; codebase drift reported `no-structure-md`; UI safety reported no frontend files and did not block. Upcoming key links owned by the upcoming wave are intentionally deferred to that wave; no unmet prior-wave link is waived.

## Wave 9

Native Debug source `de43a64`: `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --parallel 2 --output-on-failure --no-tests=error --output-junit phase14-wave9.xml` passed **1127/1127**, zero failures/errors/skips. JUnit SHA-256 `a4831b76da67bd3a7f05fdb14b86c833aa9303dcabf7cb8d92439b23595b2cd0`; local generated file `build/phase14-wave9.xml`. Evidence is revision-bound; this is not hosted CI or physical hardware proof.

A server restart interrupted plan 14-11 after its tracer commits and during saved Task 2 edits. Artifact reconciliation found no SUMMARY and preserved the committed tracer plus partial edits; a fresh executor continued Tasks 2–3 without repeating the completed tracer. The initial full gate then failed 1/1,127 in 134.99 seconds: the AGE live verifier assumed numeric assertion IDs while the new events exposed the already-frozen source labels. The direct consumer correction accepts exact validated source IDs and rejects altered observed values with the original drift diagnostic; focused tests passed 6/6 before this full rerun. That failed gate is not a pass. The bounded receipt independently reconciles 107/107 complete cases, 25 actual passes and 82 matched expected failures; 2,845/4,959 assertion rows pass and 18,208/138,240 image pixels mismatch. Reusing the bound CTest log produces the same counts without executing the corpus again.

Capability checks: schema drift did not block; codebase drift reported `no-structure-md`; UI safety reported no frontend files and did not block. Upcoming key links owned by the upcoming wave are intentionally deferred to that wave; no unmet prior-wave link is waived.

## Wave 10

Native Debug source `50b28b1490201615185ce3b50c2d77427043ea02`: `cmake --preset phase1 && cmake --build --preset phase1 && python3 -I tests/scripts/verify-cgb-corpus-report.py --begin-run --build-dir build --receipt build/cgb-corpus-receipt.json && ctest --test-dir build -T Test --no-compress-output --test-output-size-passed 16777216 --parallel 2 --output-on-failure --no-tests=error --output-junit cgb-corpus-ctest-cb5a72236fcd79608eea0c1de00332a2.xml && python3 -I tests/scripts/verify-cgb-corpus-report.py --from-ctest --build-dir build --receipt build/cgb-corpus-receipt.json` passed **1133/1133**, zero failures/errors/skips. JUnit SHA-256 `f847ca5b7b32aed89dd78fb67595acc719c70b6a9f8423824e0529cff853d41c`; local generated file `build/phase14-wave10.xml`. Evidence is revision-bound; this is not hosted CI or physical hardware proof.

Same-run required inventory, DMG JUnit inventory and allowlisted JSON artifact privacy checks passed. Complete 107-case receipt SHA-256 `223aaac0e29801b171197eacdfe555a4f9d1c3927af233fd2aacd738215bb410`; run ID `f25c733e82d6d5d64b334b83a618285c744f01e9599390ddd176c0eeaa83eb8b`; 25 actual passes, 82 matched expected failures, 2,845/4,959 passing assertion rows and 18,208/138,240 mismatching image pixels. Raw CTest XML stays local; public artifact selection is checked separately.

The first parent gate passed all 1,133 CTests in 139.39 seconds, then rejected stale dashboard XML. Combining the test preset and dashboard action located dashboard output at the source root rather than the build tree; the existing stale-run guard correctly left the receipt incomplete. This rerun uses the same explicit `--test-dir build -T Test` form as CI. Earlier plan-level parser, stale-runner and package/CI findings, their negative controls and the Task 3 TDD deviation are preserved in 14-12-SUMMARY.md. Five later-plan RED tracebacks were found to contain personal workspace prefixes; publication is held until evidence and unpublished history are sanitized.

Capability checks: schema drift did not block; codebase drift reported `no-structure-md`; UI safety reported no frontend files and did not block. Upcoming key links owned by the upcoming wave are intentionally deferred to that wave; no unmet prior-wave link is waived.

## Wave 11

Native Debug source `f826054`: `cmake --preset phase1 && cmake --build --preset phase1 && python3 -I tests/scripts/verify-cgb-corpus-report.py --begin-run --build-dir build --receipt build/cgb-corpus-receipt.json && ctest --test-dir build -T Test --no-compress-output --test-output-size-passed 16777216 --parallel 2 --output-on-failure --no-tests=error --output-junit cgb-corpus-ctest-82996a6a7c9cdd2d438af465fec592d1.xml && python3 -I tests/scripts/verify-cgb-corpus-report.py --from-ctest --build-dir build --receipt build/cgb-corpus-receipt.json` passed **1136/1136**, zero failures/errors/skips. JUnit SHA-256 `ab6b02a9b515499bcd406c9dd1311757c48143e24bf7dca7c16e5a8dbd5496b0`; local generated file `build/phase14-wave11.xml`. Evidence is revision-bound; this is not hosted CI or physical hardware proof.

Same-run required inventory, DMG JUnit inventory and allowlisted JSON artifact privacy checks passed. Complete 107-case receipt SHA-256 `2be80587e04fb7a1eb19568a4415a28e2df8d51fe49966c6aaa952d77d5f307a`; run ID `53a7b4be86a2bee9500a2ef55479bbef7a0794f17255663824451a01c16239ca`; 25 actual passes, 82 matched expected failures, 2,845/4,959 passing assertion rows and 18,208/138,240 mismatching image pixels. Raw CTest XML stays local; public artifact selection is checked separately.

Capability checks: schema drift did not block; codebase drift reported `no-structure-md`; UI safety reported no frontend files and did not block. Upcoming key links owned by the upcoming wave are intentionally deferred to that wave; no unmet prior-wave link is waived.

## All-wave implementation result

All 13 plans / 31 tasks completed across 11 verified waves. This is implementation completion; Nyquist validation, security, UI scope, code review, regression and goal verification still gate Phase 14 closure. CGB-08/CGB-10 remain pending that qualification. Phase 15 remains unstarted and both auto-advance flags remain false.

| Wave | Plans | Verified native tests |
| --- | --- | ---: |
| 1 | 14-01, 14-05 | 1,003 |
| 2 | 14-02, 14-08 | 1,009 |
| 3 | 14-03 | 1,018 |
| 4 | 14-04 | 1,025 |
| 5 | 14-06 | 1,032 |
| 6 | 14-07 | 1,107 |
| 7 | 14-09 | 1,117 |
| 8 | 14-10 | 1,123 |
| 9 | 14-11 | 1,127 |
| 10 | 14-12 | 1,133 |
| 11 | 14-13 | 1,136 |

Digital PCM, mode-specific IR/ports, CH3 fetch and transitions, lifecycle/partition/bounds, independently frozen membership, pinned admission, AGE pixels, exact inherited gates, one bounded receipt, recurring CI/package boundaries and semantic claims each have automated positive and negative checks. Final corpus completion is 107/107, with 25 actual passes and 82 matched expected failures; physical CGB-E remains UNKNOWN/POLICY. The 31-gate ledger preserves four tested resolutions and 27 owned limitations.

Original execution IDs are retained as recorded. Unpublished ancestry was sanitized before publication with a byte-identical final tree; see [14-HISTORY-REDACTION.md](14-HISTORY-REDACTION.md). Wave 11 is the fresh post-sanitization build/stream/receipt/claims proof. The private recovery refs are not published. No closed Phase 13 UAT was restarted.
