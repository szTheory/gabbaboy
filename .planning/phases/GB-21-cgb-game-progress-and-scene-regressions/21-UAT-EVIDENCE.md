# Phase 21 automated verification evidence

## Local boundary

Local code and test results refer to source `ca17216b22d0d9f2fb742c8baed3e1543bc307e1`. This record does not assert a hosted status for a future PR head.

All eight plan summaries (21-01 through 21-08) classify deliverables as automated and cite passing verification. There are no mandatory human UAT checkpoints.

Configure and build passed. The focused `phase21_fixture_admission_(contract|controls)` selection passed 2/2 (39.02s and 3.75s). The first full serial CTest run registered 1,718 tests: 1,712 passed and six timed out at existing per-test limits. Every Phase 21 progress, admission, game-evidence, and scene-report test passed in that run. After the separate test run in another checkout cleared, all six timed-out controls passed in one serial focused retry (84.77s, 11.83s, 12.88s, 17.57s, 21.45s, 26.90s). A second final-head configure/build/full serial CTest run passed all 1,718 tests in 1,665.95s. The cause of the initial timeouts remains unestablished. The suite's 27.8-minute wall time used a 3,600-second outer workflow cap; CTest limits, budgets, and membership were unchanged. After closure generation, the helper self-test and normal check passed for all 20 automated deliverables, and focused evidence checks passed 11/11 in 10.46s.

The independent source-bound game-evidence check records `game=not-admitted`, model `CGB-CPU-E`, and mode `cgb`. No candidate game source or ROM was executed. Potion Panic remains a source and rights-scope no-go because exact component grants and repository/public-CI scope were not established. µCity 1.3 remains a no-go because required `source/engine/hardware.inc` has no identified grant or notice. These are evidence-scope decisions, not claims that either license prohibits use. `FIXT-01` remains pending further owner-selected source evidence.

## Hosted qualification boundary

Current-head hosted CI, fixture-reproduction, and installed-package consumer status must be read from [PR #140](https://github.com/szTheory/gabbaboy/pull/140) after the final evidence commit is pushed. This local record does not treat older run results or push-event checks as proof for that later head.

## Outcome limits

The original CGB result remains harness-only. RGB555/PCM digests establish repeatability, not accuracy, physical hardware behavior, perceptual behavior, or general compatibility.
