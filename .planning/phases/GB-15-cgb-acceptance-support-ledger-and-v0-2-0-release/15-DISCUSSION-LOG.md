# Phase 15: CGB Acceptance, Support Ledger and v0.2.0 Release - Discussion Log

> **Audit trail only.** Downstream research/planning/execution consumes `15-CONTEXT.md`, not this log.

**Date:** 2026-10-16
**Areas discussed:** CGB game admission/absence; support ledger and consumer proof; fresh performance/fuzzing; exact-tag release and recovery; automation/dependencies and phase stop.
**Owner instruction:** Consider all relevant areas and stakeholder perspectives, use primary sources, challenge recommendations adversarially, synthesize and automatically follow coherent choices. Prefer smaller/flatter dependencies and small local helpers. This explicitly delegates recommendation selection; no user answers or approval were fabricated.

## CGB game route

| Option | Description | Selected |
|---|---|---|
| One gated Rebound attempt, then explicit absence | Audit exact source/assets/build; require meaningful native-CGB progress and controls; stop if gates cannot close | Yes |
| Immediate absence | Honest and permitted, but skips a bounded opportunity for actual game evidence | No |
| Hunt across all candidates or rewrite subsystems until a game passes | Greater possible breadth, uncertain rights/tools and unbounded phase scope | No |

**Selection:** Delegated recommendation. D-03–D-07. Rebound's source exposes plausible state, not an acceptance result. Candidate pin and old digest remain separate until rebuilt. Rex Runner, GBHack and Aevilia were considered through their primary source/build/asset and oracle complexity; none is admitted here. The no-input and wrong-input controls must reject the same objective at the same budget, and native-CGB capture needs a narrow runner adaptation.

## Ledger and installed consumers

| Option | Description | Selected |
|---|---|---|
| Versioned v0.2 ledger plus separate source-bound receipts | Preserve v0.1 validation and use complete corpus, existing consumers and current release facts | Yes |
| Append unreleased paragraphs or relax schema 1 | Cheap edit, but stale chronology and fixed DMG assumptions can misstate CGB support | No |
| New central evidence registry/renderer | Could serve future channels, but duplicates current producers and adds schema/maintenance cost | No |

**Selection:** Delegated recommendation. D-08–D-12. Both C/C++ examples already cover the requested public APIs and negative cases. Fresh relocated/downloaded proof and identified gaps matter more than another equivalent consumer. The exact v0.2.0 ledger must be required because current version selection otherwise permits v0.1 fallback. Physical UNKNOWN/POLICY, actual guest passes, matched xfails, assertions and game evidence remain separate.

## Performance and fuzzing

| Option | Description | Selected |
|---|---|---|
| Fresh v0.1.0/current paired comparison and actual bounded Clang campaign | Exact source/build/workload/digest and uncertainty; actual campaign result, not runtime availability | Yes |
| Reuse Phase 10 percentage and successful `--fast` exit | Lower effort, but loaded-host history and unsupported fuzz success do not satisfy SHIP-11 | No |
| New benchmark framework or unbounded fuzz/optimization project | Broader capability with unnecessary dependencies/runtime/scope | No |

**Selection:** Delegated recommendation. D-13–D-16. `v0.1.0` is explicit; source inspection found its matching one-million-half-dot workload. Execution still must validate both binaries. Three warmups/thirty interleaved pairs reuse current A/B defaults. Local runtime absence routes to an eligible hosted Clang campaign; no actual campaign means the requirement remains open.

## Release delivery and recovery

| Option | Description | Selected |
|---|---|---|
| Existing release-please, exact-tag draft, downloaded-byte gate and one publish | Reuse mature mechanisms; add the missing v0.2 ledger/comparison/campaign contracts | Yes |
| Provision an App token immediately | Could remove approval pauses, but no credential is evidenced or needed for discussion | No; conditional future option |
| Promote today's PR preview artifacts | Avoids builds, but source identity and artifact retention do not meet exact-tag proof | No |

**Selection:** Delegated recommendation. D-17–D-21. Current PR #70 is a dated action-required snapshot, not green evidence. An authorized agent can attempt run approval during execution; only a real access/credential limitation requires owner action. Keep PR-head/merge/tag/assets distinct and preserve protected checks. Retain licensed fixtures in automatic source archives, keep product packages fixture-free, and document the distinction. Same-draft byte-identical reuse is allowed; public assets/tags are not overwritten after publication.

## Automation, dependency and scope defaults

| Option | Description | Selected |
|---|---|---|
| D-069 checks/negative controls in existing lanes, small original helpers, explicit stage stop | Zero routine human UAT and bounded recurring cost | Yes |
| Manual reading/gameplay approval or a duplicate matrix | Adds toil without deciding the contract more reliably | No |

**Selection:** Owner's explicit durable preference. D-01/D-02/D-22–D-24. One-off discussion contracts stay local; recurring behavioral/release contracts belong in existing CI. No new dependency, product feature or service is added by discussion. Planning and execution remain unstarted.

## Independent research and adversarial reconciliation

Three typed `gsd-advisor-researcher` agents independently owned the game, evidence/consumer and delivery topic notes under `.planning/research/`. Each received freshly resolved OpenGSD model/effort (`gpt-6-luna`, `xhigh`) through supported inline fields; the static-agent staleness warning did not require changing the owner's configuration. All three reached terminal results. Focused follow-ups challenged the predicate, rights/absence fallback, exact ledger binding, actual fuzz execution and source/tag provenance.

Parent source inspection and reconciliation found these concrete failure modes:

- **CGB progress capture:** the existing Libbet path refuses a CGB frame profile; an existing RGB555 oracle elsewhere does not prove this route works.
- **False gameplay progress:** coordinates/time/attract motion could pass without meaningful input. Bind a source-defined objective and equal-budget failing controls.
- **v0.1 ledger schema:** the validator fixes one model, three case IDs, four manifests and zero failures. A general weakening would lose historical guarantees; use separate strict dispatch.
- **Silent ledger fallback:** a v0.2 tag can select the old ledger if the new versioned file is missing. Require the exact new ledger.
- **Existing consumer duplication:** all four requested API families already have C and C++ behavioral tests. Refresh installed/downloaded evidence and add only actual gaps.
- **Unsupported fuzz success:** Linux does not pin Clang and `--fast` can return successfully without a fuzzer. A real bounded campaign receipt is required; deterministic regressions alone cannot close SHIP-11.
- **Overstated delivery readiness:** the current pipeline produces generic support and trace/performance receipts; it does not yet supply v0.2 schema evidence or the required v0.1 A/B comparison. The delivery topic note was corrected before synthesis.
- **Revision drift:** Phase 14's tested PR head, its squash SHA, current version PR and future release tag are different identities. Historical receipts keep their producer; public artifacts require their actual downloaded bytes.
- **Unnecessary churn:** completed UAT, fixture pins and source expectations remain closed absent changed behavior/evidence. No further role/source pass changed the adopted scope or acceptance discriminators.

Five focused planning research gates remain in D-23. They are technical work for planning/prototypes, not routine owner questions. No emulator tests, benchmarks, fuzz campaign, game acceptance, version PR merge or publication was performed in discussion.

## Discussion artifact verification

The local discussion contract passed: 24 contiguous decisions, 48 existing canonical files and all three primary-source topic notes. Fifteen weakened records were rejected, covering missing decisions/sections/refs, asset-rights shortcuts, unequal game controls, omitted absence cutoff, old-ledger fallback, unsupported fuzz success, unspecified baseline, stale continuation/PROJECT/machine routes, premature phase completion, inflated milestone count and enabled auto-chain. Live STATE/continuation/PROJECT/INDEX/machine routes agree on `/gsd-plan-phase 15`; all four requirements remain pending. Owner configuration and timestamp edits and prior Phase 13/14 UAT artifacts are preserved. This is artifact verification, not a new emulator regression run.

The registered runtime session resync again counted the archived v0.1 progress row as a completed v0.2 phase. Its monotonic progress preservation cannot lower that accidental count, so the existing curated **8/9 (89%)** count was restored under the runtime's state lock and platform writer. No runtime installation or roadmap repair is introduced. The machine route uses the runtime contract publisher with the project's specific planning action. Both auto flags remain false; these one-off handoff checks stay local.

## Agent discretion

Helper layout/names, bounded schema details, economical test grouping, measurement storage and plan sizing are delegated. Necessary narrow technical amendments can proceed with evidence. No unrelated framework/language/3D/distributed-system survey is required.

## Deferred ideas and route

Broader game search, full timing/APU fidelity, new hardware/peripherals, physical/perceptual qualification, signing, report platforms and provisional v0.3 states/Playstead remain deferred.

**Completed stage:** Phase 15 discussion only. **Next:** Phase 15 — CGB Acceptance, Support Ledger and v0.2.0 Release, planning, `/gsd-plan-phase 15`. Both auto flags remain false; planning/execution and all four requirements remain pending. The discussion contract is checked locally with negative controls before committing; no recurring CI lane is added.
