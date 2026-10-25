# Phase 14: CGB-E Model Qualification and Corpus - Discussion Log

> **Audit trail only.** Downstream research/planning/execution consumes `14-CONTEXT.md`, not this log.

**Date:** 2026-10-15
**Areas discussed:** Corpus breadth, inherited timing gaps, qualification reports; cross-cutting dependency, safety, evidence and automation policy.
**Owner instruction:** Consider every area, fan out through relevant perspectives, use reputable primary sources, run adversarial checks, synthesize coherent recommendations and automatically follow them. Prefer smaller/flatter dependencies and small local helpers. This replaces repeated interactive option selection; no numbered answers or approvals were fabricated.

## Corpus breadth

| Option | Tradeoff | Selected |
|---|---|---|
| Small representative sample | Cheap, but subjective curation can conceal hard or absent cases | No |
| Full pinned candidate inventory with finite predeclared required set | Explicit source/model/mode/rights/oracle reasons; select independently of results; execute required cases whether they pass or fail | Yes |
| Require every upstream test | Includes wrong models, unrelated behavior and unavailable assets; nominal breadth produces misleading denominators | No |

**Owner's choice:** Delegated research and automatic adoption of the coherent recommendation.
**Captured:** D-12–D-16. Preserve immutable pins and distinguish candidate source, admitted bytes and executable case variants. Require source-header applicability and a nonempty real pass cohort for required suites/behaviors. Retain rights and unsupported-model reasons independently.

## Inherited timing and APU/I/O priorities

| Option | Tradeoff | Selected |
|---|---|---|
| Narrow qualification with independent discriminators | Implements required PCM/IR/APU differences; qualifies existing masks; evaluates inherited AGE targets without promising complete hardware timing | Yes |
| Blanket expected-failure/defer policy | Avoids changes but abandons recorded Phase 14 ownership and can substitute green evaluator exits for implementation | No |
| Broad CPU/PPU/APU rewrite | Enlarges scope and obscures which observable defect was fixed | No |

**Owner's choice:** Delegated research and automatic adoption; exact researched failure fallback remains available for qualified limits.
**Captured:** D-01–D-11 and D-21. Separate silicon/mode/speed/boot/evidence axes. PCM is pre-mixer digital output, not host audio. FF72–FF75 already exist. Research native/compat access and a minimal wave-buffer model. Preserve the DMG baseline and bounded API. Treat inherited single-speed AGE native and compatibility m3 cases as pass targets; classify double-speed siblings separately.

## Qualification reports and CI

| Option | Tradeoff | Selected |
|---|---|---|
| Existing fragmented summaries only | No new adapter, but incompatible counters and evaluator success cannot provide one honest cross-suite receipt | No |
| Small original standard-library test-side adapter | Normalize existing observations into terminal and JSON output with exact membership/provenance, without duplicate full execution | Yes |
| Reporting framework, dashboard or service | More dependency/operational surface without solving project-specific model/xfail/rights semantics | No |

**Owner's choice:** Delegated research and automatic adoption.
**Captured:** D-17–D-23. Distinguish expected result, observed result and evaluator disposition. A matched xfail is completed execution and successful evaluation, never an actual pass. Missing required bytes, incomplete membership, timeout, truncation, stale identities, xpass and signature drift fail closed. Reuse existing CI/reproduction paths; no new production dependency, C API or GSD installation in CI. Every deliverable gets automation and an intended failing control; zero routine human UAT.

## Research and adversarial reconciliation

Three typed `gsd-advisor-researcher` investigations ran independently: hardware/timing, corpus rights/applicability, and reporting/DevOps/security. The installed OpenGSD resolver supplied the model/effort. Follow-ups challenged cross-mode behavior, timing ownership, denominator accounting and applicability inference. A final focused read of the synthesized context checked remaining blockers. No agent modified production code, fixtures or workflows.

- **Mooneye omission:** An initial five-case observation was a CGB-named misc subset, not the full eligible corpus. Common unsuffixed `div_write`, `tim00` and `daa` headers include CGB. The correction is captured in D-13: enumerate headers/model tokens instead of copying a suffix count. The source-only `vblank_stat_intr-C` candidate must receive an explicit disposition.
- **SameSuite suffix trap:** The three revision-suffixed APU sources are not automatically excluded. The pinned README author-reports E success; per-source semantics need mapping before a denominator claim. All 70 assembly paths are inventory candidates, not 70 executed/passing ROMs.
- **AGE mode trap:** `nocgb-ncmBCE` m3 sources attest CGB-E in compatibility mode. Four single-speed m3 targets cover native and compatibility execution; two double-speed siblings require separate attribution. CGB-C/D Mealybug images cannot replace them.
- **Existing implementation:** FF72–FF75 masks already have code/visibility provenance. Broad documentation wording must not erase the compatibility column without a contrary discriminator. PCM must remain independent of NR50/NR51 and host output processing.
- **Expectation independence:** SameSuite's author result and SameBoy's `channel_4_freq_change`/`channel_1_sweep_restart_2` disagreements remain separate. Exact named software-model failures cannot become source-author expectations or suite-wide waivers.
- **Stale admission prose:** The Magen eligibility tail still says HDMA is not vendored, contradicting its manifest, source record and later admission section. D-14/Q3 requires reconciliation against the admitted seventh ROM, without duplicate admission or dropped coverage.
- **Vacuous/partial green:** Existing runner xfails return successful evaluator exits. D-18–D-20 require observed pass counts, exact identities/membership, nonempty required pass cohorts, and negative controls for missing/duplicate/narrowed/partial/stale results.
- **Mixed-result ROMs:** The final context review found that case identity alone could hide a failing guest row or inflate counts by splitting one ROM into several successes. D-16/D-18/D-19 now require stable assertion IDs and per-assertion dispositions/signatures, exact membership at both levels, and separate case/assertion denominators. A Phase 14 SCX-row improvement cannot relabel unrelated LY failures as a passing ROM.
- **Scope conflict:** Prior phases assigned CGB mode-3/window work to Phase 14. Blanket deferral was rejected; targeted research remains mandatory, while a broad rewrite and full physical timing qualification are not imposed.

The coherent recommendation stops here: five concrete DEEP-research gates remain in D-24. No additional stakeholder lens introduced a new capability or owner decision after these corrections. Technical unknowns are assigned to research/prototypes, not routine human UAT.

## Handoff checks

The local artifact checks validate decision IDs, canonical paths, scope/rights/accounting safeguards and the exact current route, with weakened-record negative controls. This is discussion-artifact verification, not a new emulator test run. The installed runtime's session resync included the archived v0.1 progress row in the current-milestone completed count; the existing curated v0.2 execution count remains 7/9 (78%), with Phase 14 planning/execution unstarted. Its generic machine route also needs the project's specific command projection: STATE.md, state.json and the continuation note explicitly use the Phase 14 planning route. Preserve those curated values; do not regenerate historical verification or widen this phase to repair the runtime.

Fresh local contract result: **PASS**, 25 contiguous decision IDs, 54 existing canonical local files, and 9/9 weakened records rejected (missing decision/reference/section, stale continuation/machine route, enabled chain, omitted assertion identity/rights gate and wrong milestone count). The discussion-only artifact inventory, unchanged prior UAT and preserved owner configuration pass. Installed OpenGSD `state.validate --strict` returns `valid: true`, no warnings; `git diff --check` is clean. This session-specific check stays local; existing recurring CI is unchanged.

## Agent discretion

The owner delegated helper layout, fixture organization, report-schema details within the accounting contract, economical test/mutation grouping and plan sizing. Dependency choices remain constrained by D-096. A new dependency or scope change must have concrete evidence; unrelated UI/framework/distributed-system surveys add no requirement.

## Deferred ideas and route

Physical/perceptual qualification, additional silicon, real IR/link, snapshots, Playstead, public reporting services and broader rewrite remain deferred. Phase 15 owns CGB game acceptance and release.

**Completed stage:** Phase 14 discussion only. **Next:** Phase 14 planning with DEEP research, `/gsd-plan-phase 14`. Both automatic-advance flags remain false; Phase 15 is unstarted. Prior completed UAT stays closed unless covered behavior or evidence changes.
