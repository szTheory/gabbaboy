# Phase 15 Plan Overview

Planning only. Four requirements remain pending; no product implementation, PR approval/merge, tag or publication occurred in this planning run. Planning artifacts are versioned separately from implementation evidence.

Goal: Adopters get a qualified v0.2.0 release whose ledger, docs and consumers accurately state what DMG-CPU-B and CGB-CPU-E support has been proven.

## Roadmap success criteria (verbatim)
1. One rights-clear CGB game passes a game-level acceptance run in the GAME-02 style (scripted input, progress predicate, negative control, frame/PCM digests), or the ledger explicitly states that no CGB game-level evidence exists.
2. The v0.2 support ledger names DMG-CPU-B and CGB-CPU-E, the mapper matrix, evidence classes, corpus revisions, denominators, failures, exclusions and known issues, and contains no unqualified compatibility claim.
3. Installed C and C++ consumers exercise profile selection, ROM probe, RGB555 frames and RTC catch-up, and API, cartridge/save, integration and third-party-notice docs match the shipped behavior.
4. An exact-tag v0.2.0 release publishes with refreshed fuzzing and performance baselines, including a measured DMG performance comparison against v0.1.

## Dependency graph and ownership
| Plan | Wave | Needs | Creates / observable result |
|---|---|---|---|
| 15-01 | 1 | Existing Phase 14 source/research | Publish the explicit CGB game-evidence boundary |
| 15-02 | 2 | 15-01 | Bind a versioned support ledger to complete current corpus evidence |
| 15-03 | 2 | 15-01 | Prove relocated native consumers and API/save guidance |
| 15-04 | 3 | 15-02, 15-03 | Make adoption and limitation claims executable |
| 15-05 | 2 | 15-01 | Measure a provenance-bound v0.1.0/candidate DMG comparison |
| 15-06 | 2 | 15-01 | Require actual bounded Clang/libFuzzer exploration |
| 15-07 | 4 | 15-04 | Verify licensed source archives separately from product packages |
| 15-08 | 5 | 15-02, 15-05, 15-06, 15-07 | Bind release qualification and recovery to exact evidence |
| 15-09 | 6 | 15-08, 15-03, 15-04 | Wire strict qualification into the existing exact-tag release flow |
| 15-10 | 7 | 15-09 | Complete protected delivery and verify the published exact-tag release |

Wave 2's ledger, consumer, performance and fuzz owners modify disjoint paths. Shared docs/checker work waits in wave 3; archive waits for notices; aggregate gates wait for every producer; release glue waits for gates; remote delivery waits for implementation. No task is tests-only preparation: each first tracer connects an adopter/distribution/evidence contract to its real production entry point. Two tasks per plan, at most five modified files per task; plan 04 has six total files across two bounded documentation slices. Plan 10 is external delivery of the prior implementation, not another development subsystem.

All plans autonomous under existing authorization. No external tool/service setup is invented. Actual credential/permission failures during delivery are honest blockers, not requirement waivers. Publication is one-way, protected merge costly; D-20 and AGENTS already authorize the normal reviewed/tested route, so no confirmation-only template checkpoint applies.

## Discovery and evidence disposition
Existing LIGHT research and exact analogs in 15-PATTERNS.md are sufficient. No additional library/toolchain install, ecosystem survey or child research is needed. Private Rebound build at cc2966e1643d480d0780fb6cc5b9ef53d5ef6898 failed with 494 assembler errors on tested official RGBDS 1.0.1; installed 1.0.4 was also inspected/tested and asset rights remain unresolved. D-07 cutoff is met: use the explicit absence alternative. D-03–D-06 are addressed by this checked failed admission and conditional inapplicability, not silently dropped. No native-CGB runner adaptation/ROM admission/core rewrite is planned. Libbet remains unchanged.

Candidate/current/PR/squash/tag/bookkeeping identities remain separate. v0.2 tracked ledger uses manifest/covered-input identities; final source/tag SHA belongs in generated sidecars, preventing a self-referential future SHA. Final version changes must reconcile covered inputs. Exact-tag A/B, fuzz and corpus reruns are the default; any reuse needs independently proven complete input equality and preserves original producer labels. Historical 107/25/82 is current only after a fresh complete producer confirms it.

## Multi-source coverage audit
| Source | ID | Item | Plan | Status |
|---|---|---|---|---|
| GOAL | Phase 15 | Qualified accurate v0.2.0 adoption/release | 01–10 | COVERED |
| GOAL | SC1 | Game or explicit absence | 01/02/04/09 | COVERED |
| GOAL | SC2 | Scoped ledger, failures and denominators | 02/08/09 | COVERED |
| GOAL | SC3 | Installed consumers and current docs | 03/04/07/09/10 | COVERED |
| GOAL | SC4 | Exact-tag release, refreshed fuzz/performance | 05/06/08/09/10 | COVERED |
| REQ | CGB-11 | Exact absence alternative | 01/02/04/09/10 | COVERED |
| REQ | SHIP-09 | Model-qualified ledger and strict evidence | 02/04/08/09/10 | COVERED |
| REQ | SHIP-10 | Relocated/downloaded consumers, docs/notices/source | 03/04/07/08/09/10 | COVERED |
| REQ | SHIP-11 | Clean measured comparison, real fuzz, release | 05/06/07/08/09/10 | COVERED |
| RESEARCH | Q1 | Failed candidate/rights cutoff, absence, unchanged Libbet | 01 | COVERED |
| RESEARCH | Q2 | Schema dispatch, exact ledger, immutable sidecar | 02/08/09 | COVERED |
| RESEARCH | Q3 | Reused behavioral consumers, semantic docs, source archive | 03/04/07/09 | COVERED |
| RESEARCH | Q4-A | Matching clean baseline/candidate, digest, uncertainty/privacy | 05/09 | COVERED |
| RESEARCH | Q4-B | Actual Clang campaign, bounds, eligible lane, no unsupported pass | 06/09 | COVERED |
| RESEARCH | Q5 | Protected PR sequence, event approval, exact tag, retry | 08/09/10 | COVERED |
| RESEARCH | Validation/security | Negatives, inventories, source/receipt bounds, scoped token | 01–10 | COVERED |
| CONTEXT | D-01 | Reuse completed phases/current integration | 01–10 | COVERED |
| CONTEXT | D-02 | Small original helpers/no dependencies | 01–09 | COVERED |
| CONTEXT | D-03 | Bounded pinned candidate checked; failed cutoff | 01 | COVERED |
| CONTEXT | D-04 | Unresolved rights/no admitted ROM | 01/07 | COVERED |
| CONTEXT | D-05 | Game objective conditional disposed after failed admission | 01 | COVERED |
| CONTEXT | D-06 | Runner/capture conditional disposed; preserve Libbet | 01 | COVERED |
| CONTEXT | D-07 | Explicit absence and contrary-claim checks | 01/02/04/09 | COVERED |
| CONTEXT | D-08 | Current model-qualified ledger | 02/04 | COVERED |
| CONTEXT | D-09 | Independent membership/guest/assertion outcomes | 02 | COVERED |
| CONTEXT | D-10 | Separate schema dispatch/exact tag/sidecar | 02/08/09 | COVERED |
| CONTEXT | D-11 | Relocated/downloaded C and C++ behavior | 03/07/09/10 | COVERED |
| CONTEXT | D-12 | Synchronized docs/API/save/notices | 01/03/04 | COVERED |
| CONTEXT | D-13 | Explicit clean 3/30 paired v0.1.0 comparison | 05/09 | COVERED |
| CONTEXT | D-14 | Resources/uncertainty/+5% disposition/privacy | 05 | COVERED |
| CONTEXT | D-15 | Actual bounded Clang exploration | 06/09 | COVERED |
| CONTEXT | D-16 | Eligible hosted route/source identity freshness | 05/06/08/09 | COVERED |
| CONTEXT | D-17 | Phase PR then version PR then exact-tag flow | 08/09/10 | COVERED |
| CONTEXT | D-18 | Supported run approval/exact protected checks | 08/10 | COVERED |
| CONTEXT | D-19 | All identities/assets/readback bound | 07/08/09/10 | COVERED |
| CONTEXT | D-20 | Same unpublished retry/published immutability | 08/09/10 | COVERED |
| CONTEXT | D-21 | Licensed source archive versus fixture-free products | 04/07/09 | COVERED |
| CONTEXT | D-22 | Automated negatives/exact inventory/SUMMARY schema | 01–10 | COVERED |
| CONTEXT | D-23 | Reuse five resolved LIGHT research gates | 01–10 | COVERED |
| CONTEXT | D-24 | Discussion stop satisfied; planning/execution phase stops retained | 10 | COVERED |

Deferred/out-of-scope ideas remain excluded: additional silicon/peripherals, physical/perceptual qualification, broad core timing/APU work, save states, new frontend/Playstead integration, signing, dependency expansion and provisional v0.3.

## Spec-less fallback: six surfaced items, no silent drop
No Phase 15 SPEC exists. The runtime fallback is ON; six engine items were supplied.
| Requirement / edge | Disposition | Concrete contract and owner |
|---|---|---|
| SHIP-09 empty | resolved, explicit | Plan 02 truth/task controls reject null/empty/single-member narrowed/duplicate/incomplete required inventories. |
| SHIP-09 encoding | resolved, explicit | Plan 02 truth/task controls: strict UTF-8, duplicate JSON keys rejected, exact decoded string identity, raw-byte SHA256, no Unicode normalization. |
| SHIP-10 idempotency | resolved, explicit | Plan 03 repeat real same-prefix consumers; stable behavioral/package results, isolated per-run receipts. |
| SHIP-10 concurrency | resolved, explicit | Plan 03 real concurrent isolated runs and interruption/collision controls; partial output cannot become success. |
| CGB-11 unclassified | unresolved, flagged assumption | Absence contract semantics assumed to be exact positive statement plus rejection of contrary claims. Plan 01/02/04/09 checks resolve that concrete contract during execution; this row is not auto-passed or backstopped. |
| SHIP-11 unclassified | unresolved, flagged assumption | Qualification assumed to require real 60-second exploration and strict 3/30 paired baseline plus final-tag/protected/distributed-byte evidence. Plans 05/06/08/09/10 check this explicitly; no unsupported auto-pass/backstop. |

All six are authored: four explicit must-have truths, two flagged assumptions. No unclassified edge was silently resolved.
Prohibition recall precision: candidate values prohibitions (admitting uncertain ROMs, implying hardware/game proof, relabeling evidence, overwriting published bytes, bypassing phase pause, hiding data, inventing UAT) are already D-04/D-07/D-09/D-16/D-19/D-20/D-22/D-24 and AGENTS requirements; no new bespoke prohibition survives. Routine empty/idempotence/identity hygiene belongs to explicit edge contracts. Path/receipt input safety and token scope refer to existing security/STRIDE controls; no redundant canon prohibition or fake wired-check descriptor is authored.

## Remaining execution gates and handoff
Planning probes: actual OpenGSD frontmatter and structure validators accept all 10 plans; decision coverage passes 24/24; failing-direction probe passes 20/20. The built-in command-path probe reports not_applicable for these Python/Bash/CMake commands, so an additional SDK-frontmatter/tracked-path probe checks all 42 script targets against existing tracked files or earlier/same-plan declared producers, with zero missing targets and zero same-wave ownership conflicts. All four requirement IDs are present; 20 unique numbered threats and all 20 exact per-task validation command mappings reconcile. Estimate calibration factor 1, sample count 0, confidence low. Structure reports one expected one-way-door warning for publication; D-20/AGENTS authorization governs that normal release path.

Full-plan API detector reports a native-integration wording false positive; COVERAGE.md explicitly declares no new external API integration and maps existing GitHub delivery operations to their checks. Assumption-delta detector reports detected:false. No UI/frontend or ORM schema is introduced. These planning probes do not qualify product execution.

Strict negative controls and all actual execution evidence remain pending. Required external gates are the eligible Clang campaign, real same-host baseline pair, current corpus, installed/downloaded platform behavior, internally reviewed Phase 15 PR exact-head protected merge, refreshed/reviewed PR 70 exact-head protected merge, exact-tag draft/build/sidecars/source archive, final gate and publication/readback.

Completed stage: Phase 15 planning. Next stage: Phase 15 — CGB Acceptance, Support Ledger and v0.2.0 Release, execution.
Next command: `/gsd-execute-phase 15`.
Planning stops here. Execution later stops at its Phase 15 boundary with `/gsd-verify-work 15`; no next milestone is chosen or started. Parent owns STATE and continuation routing; both auto-advance flags stay false.

