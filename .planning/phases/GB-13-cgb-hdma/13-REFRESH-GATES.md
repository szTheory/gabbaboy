# Phase 13 — Verification Refresh Gates

**Refreshed:** 2026-10-20T23:20:59Z  
**Refresh target:** `a5f0d5962acb5eefa0143f7cde5942725ad2ac79`  
**Result:** No new blocker proven in this bounded refresh. The historical duplicate-library build warning remains deferred.

This supplement preserves the historical review, security, Nyquist and UI reports. It checks their present applicability without replaying the completed twelve implementation plans or treating old hosted receipts as current-head proof.

## Scope and runtime

The installed runtime identifies as `@opengsd/gsd-core` 1.18.0. Its `check evaluation-scope --phase 13 --raw` returns **resolved**, source `task-commits`, 71 commits and 64 non-planning paths, with no missing, outside-union or unreachable paths. The range base is `8091fb591de7fb68e666be01d344f5f26ebedc5c`. Unlike the preceding Phase 12 refresh, Phase 13's resolver is not degraded. This supplement is nevertheless a bounded applicability review, not a new standard-depth review of every one of those 64 files.

Active `verify:post` hooks are Nyquist, security and UI; active `execute:post` includes code review. Existing reports are retained. The current checks concentrate on historical findings, HDMA block admission/address/copy/cancellation and run-loop preflight, claim/disposition/reproduction boundaries, and the structural lane contract. No source file was changed. No project-local `.agents/skills` or `.codex/skills` directory exists; the reviewer skills-only query returned no additional skill block.

## Historical findings and retained debt

| Finding | Current disposition and evidence |
|---|---|
| CR-01 [BLOCKER], remote evidence accepted incomplete/conflicting/wrong-event checks | Remains fixed. `python3 -I tests/scripts/test_hdma_remote_evidence.py` passes one positive and 16 negative controls across the three fixed required contexts, including duplicate results, event, workflow, head and malformed receipt checks. These synthetic controls do not establish actual GitHub merge readiness. |
| WR-01 [WARNING], dense player help claims | Remains fixed. `src/player/main.c:401-410` separates Models, Video, Audio, Speed, Transfers and Limits. The eight-surface native/player claim check passes, retaining timing, physical-hardware and compatibility limits. |
| CR-UAT-01 [BLOCKER], hidden manual content escaped closure parsing | Strict numbered-heading/field handling remains in `verify-uat-contract.py`. Canonical closure is owned by the parent refresh using the shared checker; its historical final-record receipt must be distinguished from the implementation-fix commit. |
| WR-UAT-01 [WARNING], conflicting/compound handoff stages accepted stale routes | Exact standalone stage and command checks remain in `verify-hdma-closure.py:handoff_values`; historical stage-transition mutation tests remain in `tests/scripts/phase13-handoff-continuity.test.cjs`. Boundary-only facts require the completed immutable boundary below. |
| Deferred duplicate-library [WARNING] in `deferred-items.md` | **Still present structurally; not silently closed.** `CMakeLists.txt:40` exports `GabbaBoy::core` through `gabbaboy_accept` PUBLIC, while `tests/CMakeLists.txt:3733,3740,4198` also links core explicitly for AGE/speed targets. The current generated Ninja link records for `test_age` and `test_cgb_speed_fixture` contain `libgabbaboy_core.a libgabbaboy_accept.a libgabbaboy_core.a`. No fresh link was forced by this reviewer. Existing build-warning debt remains with the build targets; removing redundant direct links requires its own reviewed build verification. |

The four fixed findings in `13-REVIEW-DISPOSITION.md` do not include the separate deferred build warning. Their zero-open count must not be interpreted as absence of all phase debt.

## Security and Nyquist applicability

The historical security report closes 25 threats, including its accepted pinned-tool supply-chain risk and the source-revision defect fixed in `5459b7c`. Present inspection retains whole-block source/destination validation before admission, bank sampling per block, finite byte counters, output/time preflight before transfer progress, and independent speed-switch/HDMA ownership. No new concrete software-contract defect was proven in these inspected paths. This is not a fresh exhaustive audit of all 25 threats.

Fresh focused commands and results:

- `python3 -I .planning/phases/GB-13-cgb-hdma/verify-hdma-source-revision.py`: **27/27** isolated controls pass, including committed, staged, unstaged, renamed, deleted and non-ignored untracked behavioral inputs and allowed-metadata positives. Its scratch Git histories do not qualify live HEAD against an old benchmark revision.
- `python3 -I .planning/phases/GB-13-cgb-hdma/verify-hdma-closure.py --lane` and `--lane-self-test`: pass; six Python targets, 92 core HDMA cases, two player cases, parallelism four and timeout 45 remain structurally accounted for; **four** lane controls pass.
- `python3 -I tests/scripts/verify-cgb-hdma-claims.py --native-player` and `--self-test`: eight surfaces pass; **seven** claim mutations and **three** subject rejections pass.
- `python3 -I tests/scripts/verify-cgb-hdma-dispositions.py --complete` and `--self-test`: software CGB-E **5/5**, optional CGB-C `not-run:rights-gate-G1`; **16** controls pass. These are disposition-contract checks, not fresh executions of the five ROMs.
- `python3 -I tests/scripts/test_reproduce_magentests.py`: one test passes, executing the clean-copy/provenance-mutation self-test. `bash tests/scripts/reproduce-cgb-hdma.sh --self-test` passes source/ROM digest, source-pattern, RGBDS-pin and no-transfer-signature controls. `bash -n` passes independently for the original HDMA, Magen and SameSuite reproduction scripts.

The historical Nyquist record maps all **24 tasks** across twelve plans to automation and named negative controls. Current canonical SUMMARY/UAT closure, full behavioral regression and package/consumer execution are parent-owned evidence; the structural lane check alone cannot establish those passes. No local RGBDS rebuild, sanitizer run, fuzz campaign or fresh benchmark was performed here.

## Historical boundary limitations

Historical final closure belongs to immutable `e7ba52c81446096a9f6b5bf660d7721ea561eaa4`, not live STATE or current ancestry. The parent reports that the archived full closeout self-test cannot complete under OpenGSD 1.18.0: its old runtime-identity shape check rejects the current identity. Preserve that compatibility limitation rather than weakening the old checker or calling it a pass. The independent source-gate controls above still execute successfully.

An initial archive probe at implementation-review commit `0f1bb34340d8aa4a1c71cb5f913170dd9d3fa9da` was not completed-boundary evidence: that commit has no committed `13-UAT.md`, and the actual-state Node test rejects its pre-final stage; two synthetic stage-transition cases passed. The missing-record and stage rejections are reported as unavailable final-boundary setup, not retroactively presented as three passing continuity checks. Final-boundary pure-function checks and canonical UAT receipts are recorded separately by the parent.

## UI applicability

The installed runtime's `bin/lib/ui-safety-gate.cjs` API applied to the actual Phase 13 roadmap section returns `hasUI:false`, no tokens and no matched line. The old top-level `ui-safety-gate` CLI verb is unavailable in 1.18.0; the supported module API was used directly. The phase changes native help/limitations claims and core behavior; it adds no browser design contract. Historical visual/layout/interaction pillars remain N/A. The copywriting warning is closed by the labeled help and current claim controls. No screenshot, human-perceptual result or physical CGB-E qualification is claimed.

## Evidence limits

The parent reports a fresh SDL player selection **98/98** passing in **19.87 seconds**, zero skips, all twelve bounded plan windows reconciled, canonical shared UAT **45/45** with **19** rejected controls, and zero changed frozen DMG rows. Full core regression and final current handoff evidence remain parent-owned. Historical release, sanitizer, hosted and consumer receipts keep their own source revisions. This supplement authorizes no new release, merge, phase advance or debt acceptance.

## Parent producer and boundary checks

The original wrapper's exact OpenGSD 1.16.0 version pin also prevents its live `--prohibitions` mode on 1.18.0. Without changing that wrapper or its plan, the parent verified the installed runtime identity, prepared clean/bad subjects, parsed/projected the saved descriptor, and called the actual 1.18.0 `check prohibition-enforcement` producer through the existing helper functions. The result passed green/unflagged/located/test/node-test with actual fail-first violation-fixture, clean and live-checkout evidence. This qualifies the saved claim prohibition, not the old wrapper's compatibility.

At an archive of completed boundary `e7ba52c`, the original pure `handoff_values` check accepts that boundary's own STATE, continuation and config. Four mutations reject stale STATE route, stale continuation route, auto-advance and active auto-chain. No live route or current-HEAD ancestry substitutes for those immutable facts. All twelve recorded before/after task windows reconcile by their own commit counts and ancestor relationship.

## Final local regression receipt

At unchanged source `a5f0d5962acb5eefa0143f7cde5942725ad2ac79`, fresh configure/build and complete core regression pass **1,144/1,144** in **438.76 seconds**, zero skips. Rebuilt native SDL player selection passes **98/98** in **19.87 seconds**, zero skips. The duplicate-core-library warning was emitted during this build and remains deferred. The frozen DMG baseline has zero changed rows. No new hosted, sanitizer runtime, fixture rebuild, performance or hardware qualification.
