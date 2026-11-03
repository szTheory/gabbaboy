# Phase 21 automated verification evidence

## Local implementation boundary

The final implementation and rescope source is `e0845db5841a1d56d8a297cbfaa3e0811af6ad67`. Configure and build passed. The full serial Phase 1 CTest run completed 1,717 of 1,718 registered tests successfully; `v02_source_archive_controls` hit its existing 90-second timeout. Its isolated same-head retest passed in 77.17 seconds without changing test membership, timeout, or budget. Thus all 1,718 registered tests have passing evidence across the full run and that focused retest, but no single full-suite invocation was all-green. The full run took 1,910.62 seconds.

The 18 candidate compile-command unit tests passed. The focused `phase21_fixture_admission_controls` test passed in 34.59 seconds. Configure/build, Phase 21 game-evidence, game-evidence controls, scene controls, and scene contract checks passed at the same source. The final game-evidence record says `game=not-admitted`, model `CGB-CPU-E`, mode `cgb`. No candidate game source or ROM was executed.

Potion Panic remains a source and rights-scope no-go because exact component grants and repository/public-CI scope were not established. µCity 1.3 remains a no-go because required `source/engine/hardware.inc` has no identified grant or notice. These are evidence-scope decisions, not claims that either license prohibits use. `FIXT-01` remains pending further owner-selected source evidence.

## Review and security boundary

The final scoped source review and independent security audit both checked `e0845db5841a1d56d8a297cbfaa3e0811af6ad67`; neither found a remaining issue in the approved qualification-parser and diagnostic-escaping scope. The security audit reports zero open threats. See [21-REVIEW.md](21-REVIEW.md), [21-SECURITY.md](21-SECURITY.md), and [21-RESCOPE.md](21-RESCOPE.md).

## Hosted qualification boundary

PR #140's exact-head checks all passed at `e0845db5841a1d56d8a297cbfaa3e0811af6ad67`. Pull-request CI run [41554959166](https://github.com/szTheory/gabbaboy/actions/runs/41554959166) passed native Windows/Linux/macOS, CMake 3.25.3, the complete ASan/UBSan shards, fixture/native acceptance gates, and performance/player gates. Fixture reproduction [41554959121](https://github.com/szTheory/gabbaboy/actions/runs/41554959121) and the preview package run [41554959116](https://github.com/szTheory/gabbaboy/actions/runs/41554959116) passed, including both installed-package consumers and the macOS player-package smoke. The `planning-checks` lane was skipped for this product-code change; the version pre-tag gate was skipped because no tag was being prepared. Neither skip substituted for a required check.

The same-SHA push CI and fixture runs also passed ([41554953994](https://github.com/szTheory/gabbaboy/actions/runs/41554953994), [41554954013](https://github.com/szTheory/gabbaboy/actions/runs/41554954013)); they are diagnostic only and are not counted as PR qualification. The documentation closeout commit will change the PR head, so phase closure still requires a fresh successful check set for that final exact SHA.

The push and pull-request events each started overlapping CI and fixture-reproduction work for the same SHA. This duplicates hosted work without adding distinct coverage. Track a bounded CI-trigger efficiency follow-up; preserve required checks and verify GitHub event/token behavior before changing workflow triggers.

## Outcome limits

The original CGB result remains harness-only. RGB555/PCM digests establish repeatability, not accuracy, physical hardware behavior, perceptual behavior, or general compatibility. The scene workflow is synthetic-only; no live defect or real-game scene regression is claimed.
