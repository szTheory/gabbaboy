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
