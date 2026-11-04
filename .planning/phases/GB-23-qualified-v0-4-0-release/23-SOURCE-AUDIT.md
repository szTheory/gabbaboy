# Phase 23 source coverage and dependency audit

Planning date: 2026-11-03. Installed runtime identity observed: `@opengsd/gsd-core` 1.19.0. Planning only: no implementation change, build, test suite, hosted workflow, fixture operation, tag or publication was executed. Plan syntax/schema validation is separate from implementation verification.

Nine plans occupy nine waves after the owner-approved targeted visibility rescope; the nine-plan cap is fully allocated. Each production-code task touches at most five exact source files. Existing shared test registration and mutable release control-plane state force sequential waves; artificial concurrency would conflict on `tests/CMakeLists.txt`, inventory, generated copy or the same version PR. No external dependency, database schema or new release infrastructure is planned. Plan 23-07 executes between 04 and 05: planning inspection confirmed that existing state goldens still declare 0.3.0 and both support validation and compiled pin checks require the actual CMake release token. Its existing release-change disposition and documentation must therefore move with the generated 0.4.0 source, under the already adopted same-release-only policy. Plan 23-06 now owns seven modified files for downloaded-release reconciliation and automated release-evidence closure. Former 23-06-T3 milestone bookkeeping/lessons/continuation moves to Plan 23-08, which depends on 06, owns seven modified files and includes final all-summary closure regeneration. No plan exceeds ten modified files.

## Four-source coverage

| SOURCE | ID | Required outcome or constraint | Plans/tasks | Status |
|---|---|---|---|---|
| GOAL | Phase 23 | Qualified v0.4.0 with accurate established CGB/diagnostic evidence | 01–09; execution order 01 → 02 → 03 → 09 → 04 → 07 → 05 → 06 → 08 | COVERED |
| GOAL | Criterion 1 | Final implementation-head local/hosted qualification, reviewed exact-source rehearsal, consumers and controls; historical phase evidence retained | 04-T1/T2/T3, 05-T1/T3, 06-T1 | COVERED — deterministic real-report gate blocks missing/stale reviews and unresolved blocking findings before qualification |
| GOAL | Criterion 2 | Both named absence reasons or exact admitted progress; source/model distinctions and hardware/perceptual/timing/platform/compatibility limits | 01-T1/T2, 02-T1/T2, 05-T1, 06-T2 | COVERED — accepted source facts require absence, never fixture execution |
| GOAL | Criterion 3 | Published/downloaded source/digest reconciliation, actual-byte consumers, notices and real-product/game-ROM-insertion controls | 05-T3, 06-T1 | COVERED |
| GOAL | Cap/out-of-scope | At most nine plans; no default RM-032, libretro, Linux/Deck support, timing rewrite, license migration, libfuturo dependency or API/state freeze | Execution contract; 04-T3, 05-T1, 08-T1/T2 | COVERED |
| REQ | REL-01 | Qualified release and source/model-bound support documentation with explicit evidence limits | All nine `requirements` fields; 06-T2 release closure; 08-T2 final all-summary closure/handoff | COVERED |
| RESEARCH | Profile dispatch | Current v0.3-only claims need explicit v0.4 input/validation/rendering while preserving historical bytes | 01-T1/T2 | COVERED |
| RESEARCH | Claims/ledger controls | Strict bounded immutable Git reads, closed schema, exact generator output and causal promotion refusals | 01-T1/T2, 02-T1 | COVERED |
| RESEARCH | Concise notes | Reuse existing adoption/disclosure gate; share facts with ledger and reject omissions/contradictions | 02-T1/T2 | COVERED |
| RESEARCH | Content window | Add all v0.4 copy inputs; retain body/base/source/run invalidation and inactive development semantics | 03-T1, 05-T1 | COVERED |
| RESEARCH | Verified version dependency | Existing state goldens declare 0.3.0; actual 0.4.0 serialized release token needs compiled pins and exact immutable-base compatibility disposition | 07-T1/T2; 03-T1 managed-input binding; 05-T1 review/rehearsal | COVERED — no format/behavior/API change or guard weakening |
| RESEARCH | Resolved planning / exact-version gate | Actual release-please output remains unobserved; current source is 0.3.0 and observed history did not prove a minor bump | 03-T2, 07-T1, 05-T1 | COVERED — RESOLVED FOR PLANNING by the strict pre-freeze gate; wrong/missing output holds freeze/rehearsal/tag; a further concrete blocker requires another owner-approved rescope because 09 consumes the reserve |
| RESEARCH | H/R1/W/R2 | Actual reviewed H, R1, record-only W, R2/current checks/nightly before version merge | 05-T1/T3 | COVERED |
| RESEARCH | Two-stage qualification | Rehearsal is source-side only; later trusted draft-bound downloads/consumers/final publication remain required | 05-T1/T3, 06-T1 | COVERED |
| RESEARCH | Resolved planning / live access/checks | Observe actual auth/protection/check/source identity; future access/results remain unobserved and historical/local success cannot qualify remote head | 04-T3, 05-T1/T3 | COVERED — RESOLVED FOR PLANNING by existing fail-closed live gates; unavailable credentials/protection or missing/stale/non-successful current checks hold the transition; auth gate only when observed |
| RESEARCH | Privilege/source boundaries | Preserve trusted checkout, exact tag/source, scoped tokens, bounded archive policy, notices and fixture exclusion | 04-T2, 05-T3, 06-T1 | COVERED |
| RESEARCH | Retry/recovery hold | Same draft/tag/source/byte-identical assets only; historical v0.3 repair is not general authorization | 02-T2, 05-T3 | COVERED |
| RESEARCH | CI efficiency | Measure current job/step durations, queue/dependency waits and headroom; preserve all required lanes and accept justified no-change | 04-T3, 06-T1, 08-T1 | COVERED |
| RESEARCH | Independent review | Release/consumer, security and adversarial source review with bounded fixes, exact implementation SHA and no unresolved blocking findings | 04-T1 gate/causal controls, 04-T2 real reports/direct check, 04-T3 qualification-head repeat; generated-delta review 05-T1 | COVERED — independent reviewers provide substantive judgment; immutable schema/role/source/disposition gate enforces the separate mechanical facts |
| RESEARCH | Automated closure | Correct SUMMARY schema and shared closure checker; no invented gameplay/document UAT | Execution contract; 06-T2 release-evidence closure; 08-T2 exact nine-summary set and final shared regeneration/self-test | COVERED — 23-UAT-EVIDENCE.md remains the --write evidence input; 23-UAT.md is generated output |
| RESEARCH | Milestone handoff | Read-only sibling/Playstead XFER scan, measured lessons, rolling-roadmap refresh and precise owner-controlled audit route | 08-T1/T2, moved from former 06-T3 | COVERED — both automatic-advance flags remain false; no next milestone starts |
| RESEARCH | Package audit | No new dependency install; existing pinned CMake/Python/GitHub infrastructure | All plans' supply-chain row; execution contract | COVERED |
| CONTEXT | D-01 | Concise exact candidate/model/diagnostic/limit notes and versioned ledger link | 02-T1/T2, 05-T1 | COVERED |
| CONTEXT | D-02 | Generated self-sufficient concise v0.4 ledger; direct detail links; v0.3 unchanged | 01-T1/T2, 05-T1 | COVERED |
| CONTEXT | D-03 | Immutable managed input facts, exact rendering and no drift | 01, 02, 03; 05-T1 | COVERED |
| CONTEXT | D-04 | Exact Potion Panic and µCity reasons; neither built/run; no CGB game admitted; downstream unobserved; no license prohibition inferred | 01-T1, 02-T1, 05-T1, 06-T1/T2 | COVERED |
| CONTEXT | D-05 | CGB-CPU-E native harness-only RGB555/PCM reproducibility with all evidence limits | 01-T2, 02-T1/T2, 06-T1/T2 | COVERED |
| CONTEXT | D-06 | Synthetic composition and metadata-only assessment; 513 names, seven unresolved gates, zero admitted/executed; DIAG/RIGHTS Pending | 01-T2, 02-T1, 05-T1, 06-T1/T2 | COVERED |
| CONTEXT | D-07 | Existing version/rehearsal/source/tag/download/consumer/notice/fixture/final publish gates and unsigned platform limits | 02-T2, 03, 04, 05, 06-T1 | COVERED |
| CONTEXT | D-08 | Historical receipts preserved; current reviewed release source/download identity distinct | 01–08 | COVERED |

No required source item is missing. Deferred/out-of-scope research suggestions and unresolved fixture admission itself are excluded from implementation; their Pending disclosure is included. A new concrete correctness/security failure requires correction or rescope within the configured bounds, never silent deferral.

## Needs, creates and execution waves

| Plan / wave | Needs | Creates / user-visible result | Checkpoint / coupling |
|---|---|---|---|
| 23-01 / 1 | Accepted immutable Phase 21/22 records and existing generator | End-to-end generated candidate summary, complete v0.4 profile and causal CTests | None; owns generator/profile/test registration |
| 23-02 / 2 | 01 profile/render interfaces | Shared concise release preface, notes controls and accurate operator docs | None; shares generator/test files with 01 |
| 23-03 / 3 | All 01/02 managed inputs | Complete content-window binding and expected 0.4.0 refusal gate | None; shares test registration/inventory |
| 23-09 / 4 | Completed 03 and the three exact-source open visibility findings | Incomplete-HTML refusal and causal production-path controls in the existing notes/docs/changelog validators | No checkpoint; only the two existing validator scripts change; completed 01–03 remain intact |
| 23-04 / 5 | Completed implementation 01–03 and 09 visibility fix | Source-bound review-evidence gate/CTest inventory, three independent reports and exact-head local/hosted implementation merge | T1 owns verifier/CMake/inventory; T2 reviewers own distinct reports; T3 owns qualification evidence. Any source change returns to review; only six exact evidence paths may differ from IMPLEMENTATION_SHA |
| 23-07 / 6 | Reviewed merged implementation and actual generated 0.4.0 version PR | Compiled release-bound state pins/disposition/docs under existing same-release policy | No new approval of established policy; no freeze/rehearsal/tag |
| 23-05 / 7 | 07 actual exact 0.4.0 source and consistent native-state pins | Generated tracked ledger/notes, H/R1/W/R2, protected version merge and trusted published bytes | One-way decision immediately before tag/publication-triggering merge; one mutable release control plane |
| 23-06 / 8 | Actual successful release and qualified inventories | Reconciled downloaded release, automated release-evidence closure and Pending traceability | No checkpoint; final milestone bookkeeping/closure follows in 08 |
| 23-08 / 9 | Completed 06 release reconciliation/closure | Sanitized transfer/CI lessons, rolling-roadmap refresh, all-nine-summary shared closure and exact owner-controlled milestone-audit route | Stop at phase boundary; never start next milestone; shares UAT evidence/output with 06 in a later wave |

Each plan has 2–3 tasks. Plan 23-05 has a decision in addition to preparation and implementation because it must keep reversible reviewable work ahead of the one-way release action. The leading plan's frontmatter and first task are both marked tracer. Every task includes exact files where modified, read_first, action, automated checks, immediate observable fails_when, acceptance_criteria and done.

Revision 1 resolves both research questions for planning through explicit execution-time gate/hold dispositions without asserting unknown future output or credentials. The closeout split preserves all original responsibilities, locked decisions, probe flags, exact-version/state-pin ordering and the existing release path. The transfer and continuation checks are one-off local bookkeeping assertions; they do not add a reusable checker or dependency.

## Discovery, interface and path grounding

Discovery Level 0 is supported by the existing standard-library/CMake/release paths and the current source-grounded 23-RESEARCH/23-PATTERNS records. There is no library choice or new external integration requiring another discovery document. The installed runtime was identity-checked; configured planner skills are empty and project skill directories provide no additional skill. Graph context is unavailable because graphify is disabled/no graph is configured. Relevant prior implementation/source and digest-selected Phase 20/21/22 summary interfaces were consulted; historical qualification was not rerun.

Every existing source path targeted in plans and inherited pattern paths was checked using `git ls-files -- <path>`. New source paths are `tests/data/support-claims-v0.4.json` and `tests/scripts/verify-review-evidence.py`; the new generated output is `docs/support/v0.4.0.md`; new Phase 23 review/evidence artifacts are explicitly intended new files. Existing source authority comes from tracked scripts, never ignored install/runtime mirrors. No new production file is hidden behind a vague task file field. Existing Phase 21/22 evidence and both candidate/diagnostic records are read-only inputs, not targets. Plan 23-03 hashes their immutable contents so copy cannot drift.

New CLI interfaces are explicit scoped extensions of existing scripts: `--claims-version` for profile check/control and the concise preface renderer; `--render-release-notes-preface`; and `--expect-version` on the existing window checker. The new stdlib review-evidence checker supplies --check/--self-test with --rev/--repo, explicit --implementation-sha for direct real-report checks and --qualification-sha for the six-path evidence-only comparison. No alternate publisher is introduced. New positive/control CTests are registered with exact inventory membership and causal rejection semantics. The existing full command is inherited verbatim; relevant existing workflow-policy/lifecycle/fixture/closure commands retain their established behavior. No grep/count acceptance gate is used. New v0.4 CTest identities are absent at planning HEAD; their owning task creates/registers them before invocation. Plan 23-04-T1 creates the controls and registers the real-report contract; T2 invokes that positive contract only after committing its three real reports. No implementation test is represented as already run or passing.

Revision 2 closes the independent checker's review-evidence blocker without adding a plan. Plan 23-04 now has three tasks and eight modified files; no task touches more than three files. The direct gate consumes all three actual immutable reports and the explicit observed IMPLEMENTATION_SHA, with wrong/stale SHA, missing role/report and unresolved blocking/high finding controls. T3 distinguishes the later observed QUALIFICATION_SHA used by hosted protection from IMPLEMENTATION_SHA, preventing report-recording commits from creating a self-referential SHA requirement. Its explicit qualification comparison rejects changes beyond the six listed report/bookkeeping files. Permanent CTest validates historical review records without falsely claiming that a later generated version delta was reviewed; 23-05 remains responsible for that delta. All locked decisions and scope boundaries are retained; the owner-approved rescope below adds 09 before 04 and consumes the former reserve slot. Planning validation remains separate from execution evidence.

Estimates use `estimate-calibration`: factor 1, zero samples, confidence low. Raw projections equal emitted calibrated values; this is calibration metadata, not self-rated confidence or acceptance evidence.

## Owner-approved targeted visibility rescope — 2026-11-04

The owner selected one targeted addition, Plan 23-09, before Plan 23-04 qualification. The installed runtime was identity-checked as `@opengsd/gsd-core` 1.20.0 for this rescope. The three historical reports at evidence commit `4c833703329a256e87614bc91c2b5b974427d6d8` reviewed implementation `276f317d199cdd3246e9a90ce72a1f3a1235af1c`; the later handoff changes planning metadata only. RC-02, SEC-23-06 and ADV-09 remain open until the fixed implementation is independently re-reviewed. The real-report gate correctly rejects them; plan validation is not fix or qualification evidence.

| SOURCE | ID | Required outcome or constraint | Plans/tasks | Status |
|---|---|---|---|---|
| GOAL | Criteria 1/2 | Reader-visible release proof is required before reviewed implementation qualification | 09-T1/T2 → 04-T2/T3 | COVERED — exact-opener production controls precede all-three-report reissue/direct gate and unchanged final qualification |
| REQ | REL-01 | Hidden Markdown-looking disclosures/links cannot establish public release evidence | 09-T1/T2 | COVERED — existing notes/docs/changelog entrypoints; no new release mechanism |
| RESEARCH | Existing stdlib/CTest patterns; CommonMark evidence in the three reports | Incomplete script/pre/style starts, declarations and processing instructions must fail closed without weakening bounded source reads or code/comment masking | 09-T1/T2 | COVERED — each reproduced opener, both changelog placements, accepted visible/masked examples, precise refusal and isolated old-matcher causality |
| CONTEXT | D-01/D-02/D-03 | Concise generated notes and exact visible ledger links remain aligned to immutable facts | 09-T1/T2; completed 01–03 retained | COVERED — generated wording and historical ledger bytes remain unchanged |
| CONTEXT | D-04/D-05/D-06 | Exact candidate no-go/harness/metadata boundaries and Pending requirements remain intact | 09-T1/T2; original coverage above retained | COVERED — no fixture acquisition, execution or claims promotion |
| CONTEXT | D-07/D-08 | Existing qualification/release authority and historical/current evidence separation remain intact | 09-T2 → 04-T2/T3; existing 05/06 | COVERED — no local test substitutes for fresh source-bound reports or actual hosted/downloaded-byte gates |

Discovery remains Level 0: only existing production matchers and self-test functions are extended, with no dependency installation or external integration. All nine plans have REL-01 and non-overlapping sequential waves; 04 depends on both 03 and 09. The remaining chain is 07/6 → 05/7 → 06/8 → 08/9. Exact-summary closure now requires all nine summaries. Plan 23-09 estimates use the freshly observed calibration factor 1, sample_count 0 and confidence low. No source item is missing; no extra reserve slot, review-limit reset, manual UAT or next-phase authority is inferred. A new blocker after this addition requires explicit rescope rather than a tenth plan. The historical reserve wording in research/earlier plans is superseded by this allocation.

## Spec-less fallback: explicit flagged assumption

The exact REL-01 edge probe returned one `category: unclassified`, `status: unresolved`, `verification: null`, `resolution: null`, `reason: null`, `probe: unclassified — review manually` item. It remains an **unresolved flagged assumption**. The plan set covers all three concrete roadmap criteria but does not claim that these classify or resolve the probe. No automatic backstop dismissal or invented UAT is permitted. The verifier must surface the classification flag separately from concrete software evidence.

## Prohibition recall → precision → canon referral

Recall over REL-01 asked what this release could silently become that the owner would reject. Raw candidates were: false license bans; harness/metadata presented as real evidence; Pending requirement completion by prose; broader hardware/perception/timing/platform support; stale check reuse; wrong version/source; package byte changes; hidden disclosure contradictions; malformed-input/resource behavior; token/secret leakage.

Precision dropped stale-check/version/byte correctness and malformed-input/resource candidates as ordinary engineering concerns already covered by edges, review and explicit release gates. Hidden contradictory wording is a control for the retained transparency constraint rather than a separate intent prohibition. Token/secret leakage is canon security: covered by `/gsd-secure-phase` and existing workflow/security review, not minted as a bespoke prohibition. The remaining broader-claim cases form the two bespoke transparency items below, avoiding redundant routine/canon items.

| Kept statement | Source requirement | Category | Status | Verification | Plan projection |
|---|---|---|---|---|---|
| Source/rights no-go must not become a license ban; harness/synthetic/metadata observations must not become admitted-game/real-diagnostic evidence | REL-01 | transparency | unresolved | null | 23-01 must_haves.prohibitions |
| Recording absence must not complete admission requirements or grant hardware/perceptual/timing/general-game/Linux-player/Deck qualification | REL-01 | transparency | unresolved | null | 23-06 must_haves.prohibitions |

The installed `probe-core.cjs` `projectProhibitions` serializer was invoked for these two raw items. The plans carry its descriptor-less statement/status/reason projection, with no fabricated wired-check fields. Both remain flagged-unverified downstream. Counts reconcile: two kept, two projected, zero silently dropped or auto-dismissed. Concrete executable claim/refusal tests are still required by the plans; their results do not silently change fallback classification.

## Capability checks

The deterministic API detector ran over the Phase 23 roadmap section plus the generated PLAN bodies and returned a CI API surface signal. This refers to the existing hosted-check control plane; no external API integration is added. `COVERAGE.md` contains the reasoned no-integration declaration. No capabilities were fabricated.

The assumption-delta detector supplied by the orchestrator was negative. The roadmap/context/research and planned files have no Payload, Prisma, Drizzle, Supabase or TypeORM schema-relevant paths, so no schema-push task applies. Applicable STRIDE threats and specific mitigations appear in every plan; high unresolved findings block release. No web-application authentication/session controls are invented.
