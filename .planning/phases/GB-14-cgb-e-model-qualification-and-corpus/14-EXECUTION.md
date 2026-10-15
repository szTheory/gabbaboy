# Phase 14 execution evidence

Execution remains active until all 13 plans and the phase goal gates pass. Physical CGB-E remains UNKNOWN/POLICY. Fixture-author expectations, actual execution and evaluator dispositions remain separate. Both auto-advance flags are false.

Runtime identity: installed `@opengsd/gsd-core` 1.16.0 through `$HOME/.codex/gsd-core/bin/gsd-tools.cjs`; unqualified `gsd_run` resolved another installation and is not used for workflow authority. The runtime selected sequential dispatch because `origin/HEAD` was unresolved.

## Wave 1

Native Debug source `ed41d6f`: `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --parallel 4 --output-on-failure --no-tests=error --output-junit phase14-wave1-final.xml` passed **1003/1003**, zero failures/errors/skips. JUnit SHA-256 `b63492c6f80428230bab0ef7ba164d635b55129fdb2aab3af6867b34395dc170`; local generated file `build/phase14-wave1-final.xml`. Evidence is revision-bound; this is not hosted CI or physical hardware proof.

The first serial gate was stopped after four stale Mooneye unsupported-stop failures (exit 130). The next complete gate failed 6/1,003 in 72.21 seconds: model-gate tags and independent PCM table expectations were stale. Corrections retained author pass expectations, recorded two exact guest xfails, preserved false-pass controls, added helper gate tags and independent three-model PCM policy mutations. These failed attempts are not passes. Future model-visible changes must include the runner/dispositions, model-gate scanner and independent table checks in focused verification.

Capability checks: schema drift did not block; codebase drift reported `no-structure-md`; UI safety reported no frontend files and did not block. Upcoming key links owned by the upcoming wave are intentionally deferred to that wave; no unmet prior-wave link is waived.
