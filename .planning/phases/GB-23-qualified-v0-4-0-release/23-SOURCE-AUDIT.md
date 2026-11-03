# Phase 23 source coverage and dependency audit

Planning date: 2026-11-03. Installed runtime identity observed: `@opengsd/gsd-core` 1.19.0. Planning only: no implementation change, build, test suite, hosted workflow, fixture operation, tag or publication was executed. Plan syntax/schema validation is separate from implementation verification.

Seven plans occupy seven waves, leaving two of the nine allowed slots unused. Each production-code task touches at most five exact source files. Existing shared test registration and mutable release control-plane state force sequential waves; artificial concurrency would conflict on `tests/CMakeLists.txt`, inventory, generated copy or the same version PR. No external dependency, database schema or new release infrastructure is planned. Plan 23-07 executes between 04 and 05: planning inspection confirmed that existing state goldens still declare 0.3.0 and both support validation and compiled pin checks require the actual CMake release token. Its existing release-change disposition and documentation must therefore move with the generated 0.4.0 source, under the already adopted same-release-only policy.

## Four-source coverage

| SOURCE | ID | Required outcome or constraint | Plans/tasks | Status |
|---|---|---|---|---|
| GOAL | Phase 23 | Qualified v0.4.0 with accurate established CGB/diagnostic evidence | 01–06 | COVERED |
| GOAL | Criterion 1 | Final implementation-head local/hosted qualification, reviewed exact-source rehearsal, consumers and controls; historical phase evidence retained | 04-T1/T2, 05-T1/T3, 06-T1 | COVERED |
| GOAL | Criterion 2 | Both named absence reasons or exact admitted progress; source/model distinctions and hardware/perceptual/timing/platform/compatibility limits | 01-T1/T2, 02-T1/T2, 05-T1, 06-T2 | COVERED — accepted source facts require absence, never fixture execution |
| GOAL | Criterion 3 | Published/downloaded source/digest reconciliation, actual-byte consumers, notices and real-product/game-ROM-insertion controls | 05-T3, 06-T1 | COVERED |
| GOAL | Cap/out-of-scope | At most nine plans; no default RM-032, libretro, Linux/Deck support, timing rewrite, license migration, libfuturo dependency or API/state freeze | Execution contract; 04-T2, 05-T1, 06-T3 | COVERED |
| REQ | REL-01 | Qualified release and source/model-bound support documentation with explicit evidence limits | All seven `requirements` fields; 06-T2 closure | COVERED |
| RESEARCH | Profile dispatch | Current v0.3-only claims need explicit v0.4 input/validation/rendering while preserving historical bytes | 01-T1/T2 | COVERED |
| RESEARCH | Claims/ledger controls | Strict bounded immutable Git reads, closed schema, exact generator output and causal promotion refusals | 01-T1/T2, 02-T1 | COVERED |
| RESEARCH | Concise notes | Reuse existing adoption/disclosure gate; share facts with ledger and reject omissions/contradictions | 02-T1/T2 | COVERED |
| RESEARCH | Content window | Add all v0.4 copy inputs; retain body/base/source/run invalidation and inactive development semantics | 03-T1, 05-T1 | COVERED |
| RESEARCH | Verified version dependency | Existing state goldens declare 0.3.0; actual 0.4.0 serialized release token needs compiled pins and exact immutable-base compatibility disposition | 07-T1/T2; 03-T1 managed-input binding; 05-T1 review/rehearsal | COVERED — no format/behavior/API change or guard weakening |
| RESEARCH | Open exact-version gate | Actual release-please output remains unobserved; current source is 0.3.0 and observed history did not prove a minor bump | 03-T2, 05-T1 | COVERED — wrong/missing output holds freeze/rehearsal/tag; concrete blocker can use reviewed reserve plan |
| RESEARCH | H/R1/W/R2 | Actual reviewed H, R1, record-only W, R2/current checks/nightly before version merge | 05-T1/T3 | COVERED |
| RESEARCH | Two-stage qualification | Rehearsal is source-side only; later trusted draft-bound downloads/consumers/final publication remain required | 05-T1/T3, 06-T1 | COVERED |
| RESEARCH | Live access/checks | Observe actual auth/protection/check/source identity; historical/local success cannot qualify remote head | 04-T2, 05-T1/T3 | COVERED — auth gate only when observed |
| RESEARCH | Privilege/source boundaries | Preserve trusted checkout, exact tag/source, scoped tokens, bounded archive policy, notices and fixture exclusion | 04-T1, 05-T3, 06-T1 | COVERED |
| RESEARCH | Retry/recovery hold | Same draft/tag/source/byte-identical assets only; historical v0.3 repair is not general authorization | 02-T2, 05-T3 | COVERED |
| RESEARCH | CI efficiency | Measure current job/step durations, queue/dependency waits and headroom; preserve all required lanes and accept justified no-change | 04-T2, 06-T1/T3 | COVERED |
| RESEARCH | Independent review | Release, security, consumer and adversarial review with bounded fixes | 04-T1; generated-delta review 05-T1 | COVERED |
| RESEARCH | Automated closure | Correct SUMMARY schema and shared closure checker; no invented gameplay/document UAT | Execution contract; 06-T2/T3 | COVERED |
| RESEARCH | Package audit | No new dependency install; existing pinned CMake/Python/GitHub infrastructure | All plans' supply-chain row; execution contract | COVERED |
| CONTEXT | D-01 | Concise exact candidate/model/diagnostic/limit notes and versioned ledger link | 02-T1/T2, 05-T1 | COVERED |
| CONTEXT | D-02 | Generated self-sufficient concise v0.4 ledger; direct detail links; v0.3 unchanged | 01-T1/T2, 05-T1 | COVERED |
| CONTEXT | D-03 | Immutable managed input facts, exact rendering and no drift | 01, 02, 03; 05-T1 | COVERED |
| CONTEXT | D-04 | Exact Potion Panic and µCity reasons; neither built/run; no CGB game admitted; downstream unobserved; no license prohibition inferred | 01-T1, 02-T1, 05-T1, 06-T1/T2 | COVERED |
| CONTEXT | D-05 | CGB-CPU-E native harness-only RGB555/PCM reproducibility with all evidence limits | 01-T2, 02-T1/T2, 06-T1/T2 | COVERED |
| CONTEXT | D-06 | Synthetic composition and metadata-only assessment; 513 names, seven unresolved gates, zero admitted/executed; DIAG/RIGHTS Pending | 01-T2, 02-T1, 05-T1, 06-T1/T2 | COVERED |
| CONTEXT | D-07 | Existing version/rehearsal/source/tag/download/consumer/notice/fixture/final publish gates and unsigned platform limits | 02-T2, 03, 04, 05, 06-T1 | COVERED |
| CONTEXT | D-08 | Historical receipts preserved; current reviewed release source/download identity distinct | 01–06 | COVERED |

No required source item is missing. Deferred/out-of-scope research suggestions and unresolved fixture admission itself are excluded from implementation; their Pending disclosure is included. A new concrete correctness/security failure requires correction or rescope within the configured bounds, never silent deferral.

## Needs, creates and execution waves

| Plan / wave | Needs | Creates / user-visible result | Checkpoint / coupling |
|---|---|---|---|
| 23-01 / 1 | Accepted immutable Phase 21/22 records and existing generator | End-to-end generated candidate summary, complete v0.4 profile and causal CTests | None; owns generator/profile/test registration |
| 23-02 / 2 | 01 profile/render interfaces | Shared concise release preface, notes controls and accurate operator docs | None; shares generator/test files with 01 |
| 23-03 / 3 | All 01/02 managed inputs | Complete content-window binding and expected 0.4.0 refusal gate | None; shares test registration/inventory |
| 23-04 / 4 | Completed implementation 01–03 | Independent/adversarial reviews and exact-head local/hosted implementation merge | Independent review roles may run in parallel with distinct reports; findings return to owning task |
| 23-07 / 5 | Reviewed merged implementation and actual generated 0.4.0 version PR | Compiled release-bound state pins/disposition/docs under existing same-release policy | No new approval of established policy; no freeze/rehearsal/tag |
| 23-05 / 6 | 07 actual exact 0.4.0 source and consistent native-state pins | Generated tracked ledger/notes, H/R1/W/R2, protected version merge and trusted published bytes | One-way decision immediately before tag/publication-triggering merge; one mutable release control plane |
| 23-06 / 7 | Actual successful release and qualified inventories | Reconciled release, automated closure, Pending traceability and owner-controlled milestone-audit route | Stop at phase boundary; never start next milestone |

Each plan has 2–3 tasks. Plan 23-05 has a decision in addition to preparation and implementation because it must keep reversible reviewable work ahead of the one-way release action. The leading plan's frontmatter and first task are both marked tracer. Every task includes exact files where modified, read_first, action, automated checks, immediate observable fails_when, acceptance_criteria and done.

## Discovery, interface and path grounding

Discovery Level 0 is supported by the existing standard-library/CMake/release paths and the current source-grounded 23-RESEARCH/23-PATTERNS records. There is no library choice or new external integration requiring another discovery document. The installed runtime was identity-checked; configured planner skills are empty and project skill directories provide no additional skill. Graph context is unavailable because graphify is disabled/no graph is configured. Relevant prior implementation/source and digest-selected Phase 20/21/22 summary interfaces were consulted; historical qualification was not rerun.

Every existing source path targeted in plans and inherited pattern paths was checked using `git ls-files -- <path>`. The new source path is `tests/data/support-claims-v0.4.json`; the new generated output is `docs/support/v0.4.0.md`; new Phase 23 review/evidence artifacts are explicitly intended new files. Existing source authority comes from tracked scripts, never ignored install/runtime mirrors. No new production file is hidden behind a vague task file field. Existing Phase 21/22 evidence and both candidate/diagnostic records are read-only inputs, not targets. Plan 23-03 hashes their immutable contents so copy cannot drift.

New CLI interfaces are explicit scoped extensions of existing scripts: `--claims-version` for profile check/control and the concise preface renderer; `--render-release-notes-preface`; and `--expect-version` on the existing window checker. No alternate publisher is introduced. New positive/control CTests are registered with exact inventory membership and causal rejection semantics. The existing full command is inherited verbatim; relevant existing workflow-policy/lifecycle/fixture/closure commands retain their established behavior. No grep/count acceptance gate is used. New v0.4 CTest identities are absent at planning HEAD and are created in the same tasks that first invoke them; they are not represented as tests already run or passing.

Estimates use `estimate-calibration`: factor 1, zero samples, confidence low. Raw projections equal emitted calibrated values; this is calibration metadata, not self-rated confidence or acceptance evidence.

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
