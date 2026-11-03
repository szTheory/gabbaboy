# Phase 20 source coverage and planning assumptions

Planning scope is RIGHTS-01 only, with three plans. No build/test was run during planning. Existing local research and verified source patterns supply Level 0 discovery: CMake, Python standard library, Git object reads, CTest and current package scripts; there is no new library/integration choice. Runtime identity was confirmed as @opengsd/gsd-core 1.19.0. No configured planner skills or enabled graph are present. Estimate calibration has no samples, factor 1 and confidence low; projections are 36,000, 30,000 and 22,000 execution tokens, respectively.

## Multi-source coverage audit

| Source | ID | Required outcome or constraint | Plan / task | Status | Notes |
|--------|----|--------------------------------|-------------|--------|-------|
| GOAL | Phase 20 | Maintainers admit permitted evidence through a checked fixture/distribution boundary before new bytes enter public automation | 20-01 / 1–3; 20-02 / 1–3; 20-03 / 1–2 | COVERED | Contract and enforcement delivered here; no candidate admitted. |
| GOAL | Success 1 | Exact fixture/source/build identity and code/art/audio-driver/notices coverage; incomplete rights or changed identity rejected | 20-01 / 1–2 | COVERED | Versioned manifest, positive component evidence, explicit absence, both use scopes and independent pins. |
| GOAL | Success 2 | Actual install/product package rejects controlled game insertion and retains component notices/root MIT | 20-01 / 3; 20-02 / 1–3; 20-03 / 1–2 | COVERED | Clean and content-caused negative controls at actual producer/extraction boundaries. |
| REQ | RIGHTS-01 | Component rights, repository/public-CI permission, game exclusion from installed/product packages, unchanged root MIT | 20-01; 20-02; 20-03 | COVERED | Every plan lists RIGHTS-01. Future candidate decisions consume this boundary. Legal coverage remains the explicit assumption below. |
| CONTEXT | D-01 | Positive source-grounded terms for each component; distinguish build-only tools; no automated legal inference | 20-01 / 1–2 | COVERED | Evidence snapshots, mapped grant scope, reviewer rationale; unresolved/conflicting scope is no-go. |
| CONTEXT | D-01 | Retain existing fixture dispositions; no retroactive re-audit or blanket Libbet inference | 20-01 / 1–3 | COVERED | Current manifests are not modified. Baseline path/byte discovery is identity enforcement, not a new historical rights decision. |
| CONTEXT | D-02 | Versioned admission with existing per-fixture manifest; digest-bound human notice index; no registry/dependency | 20-01 / 1–3 | COVERED | Policy contains baseline and destinations only, with no rights metadata. |
| CONTEXT | D-02 | Independent immutable identity and coordinated fixture/manifest/notice rewrite negative | 20-01 / 1–2 | COVERED | Literal legacy baseline outside mutable records; adjacent admission.commit for later records; full-commit review/update rule. |
| CONTEXT | D-03 | Actual staged/extracted bytes and exact identities; only existing smoke fixtures and established notices | 20-01 / 3; 20-02 / 1–3; 20-03 / 1 | COVERED | Player keeps its current two-fixture subset; the core has all three. No new player tracer. |
| CONTEXT | D-03 | Clean positive; renamed/suffixless/in-subtree payloads; missing/changed notices and root MIT | 20-02 / 1–3; 20-03 / 1–2 | COVERED | Policy self-tests plus real-tree wrapper controls. |
| CONTEXT | D-03 | Source archives distinct; core sidecar and player central GabbaBoy/SDL licenses, no source-only binary notice | 20-01 / 3; 20-02 / 2–3; 20-03 / 1–2 | COVERED | Source check remains distinct from binary product entry/tree checks. |
| RESEARCH | Responsibility map | Grant-scope decision belongs to maintainer review; structure/identity belongs to build/CI; actual output policy belongs to packaging | All plans | COVERED | No emulator core/API change or legal-clearance claim. |
| RESEARCH | Strict input | Reject duplicate/non-object/malformed JSON, invalid hashes, missing fields, links/path escapes and bounded-work violations | 20-01 / 1–3; 20-02 / 2 | COVERED | Existing safe archive limits are preserved. |
| RESEARCH | Baseline A2 | Pin outside mutable record; fail closed on unavailable full commit/blob; do not resolve current HEAD as authority | 20-01 / 1–2 | COVERED | Legacy pin 7cc6495e64f3645caa120e7458f754585b788985; history supplied by callers, not fetched by checker. |
| RESEARCH | Inventory | Derive fixed identities from manifests plus baseline; store destination mapping only; equality on actual members | 20-01 / 3; 20-02 / 1–3; 20-03 / 1 | COVERED | Explicit generated paths, complete stage inventory and extracted equality; existing receipts bind generated binary identity. |
| RESEARCH | Package paths | Core MIT share/gabbaboy/LICENSE.txt and gabbaboy-notices.txt; player share/licenses/GabbaBoy and SDL3 | 20-01 / 1–3; 20-02 / 1,3; 20-03 / 1–2 | COVERED | Adding installed root MIT fills a concrete boundary gap without rewriting LICENSE. |
| RESEARCH | Archive distinction | Licensed source archives stay valid; source-as-product and product-as-source controls fail | 20-02 / 2–3 | COVERED | No third-party fixture removed from source archives. |
| RESEARCH | Documentation | Clarify binary smoke exception and legal-review limitation; retain historical digest/rights index | 20-01 / 1,3; 20-02 / 2 | COVERED | Parsed contract/doc positive and altered-doc negative. |
| RESEARCH | Validation A1 | Focused synthetic controls, CTest integration and real packages; target fast feedback, measure actual latency | 20-01 / 1,3; both package plans | COVERED | Timing is feedback evidence only, never correctness proof. |
| RESEARCH | Security | Strict validation, independent pins, safe archive paths, notices, no new dependency | All plans | COVERED | Unique phase threat IDs, ASVS-1 analogy only. |
| RESEARCH | Retained boundaries | No candidate search/admission, historical migration, root MIT change, v0.3 debt repair or RM-032 expansion | All plans | COVERED | These exclusions are preserved, not omitted implementation scope. |

No source item is missing. Phase 21 candidate assessment/game runner, Phase 22 diagnostics, Phase 23 actual release publication, and accepted v0.3 debts are outside this phase. CONTEXT.md has no deferred ideas.

## Dependency and file ownership map

| Plan | Needs | Creates | Wave | Checkpoints |
|------|-------|---------|------|-------------|
| 20-01 | Existing fixture/notice and Git/CMake/Python patterns | Shared admission CLI, fixed pin/destinations, configure/reproduction gates, CTest controls and docs | 1 | None |
| 20-02 | 20-01 shared policy/entry/tree API | Core install/preview/archive/release boundary enforcement | 2 | None |
| 20-03 | 20-01 shared policy/entry/tree API | Existing macOS player producer/verifier policy route and real-tree controls | 2 | None |

Plan 20-01 exclusively owns the shared checker/policy, tests/CMakeLists.txt, root CMakeLists.txt, release.yml and the parsed workflow-policy implementation/controls. It installs unchanged root MIT and wires the shared CI/release gates together so those gates are runnable within Wave 1. Plan 20-02 owns package-specific CMake modules/core scripts, preview.yml checkout history and THIRD_PARTY_NOTICES.md product wording. Plan 20-03 owns only verify-phase3-player.sh. All cross-plan file ownership is disjoint. Plan 20-01 has nine paths, reduced from ten: retaining release.yml with its policy owner avoids an intermediate failing workflow contract. Wave 2 has no modified-file overlap; it must not edit shared Wave 1 files. Both Wave 2 plans consume the same settled CLI and policy, not one another's implementation. Per-task modifications remain at five files or fewer.

## Spec-less edge assumption

The supplied engine result is retained unchanged: RIGHTS-01, category unclassified, status unresolved, verification null; applicable=1, unresolved=1, unclassified=1. It is explicitly flagged in 20-01 must_haves.truths. It was not reclassified, auto-dismissed or converted into a fabricated backstop.

Concrete consequence: Phase 20 can prove the admission boundary rejects incomplete records/changed identities. It admits no game or diagnostic candidate. A future admission still requires the maintainer to decide from positive source evidence whether the grant covers exact code, art, audio-driver, build material and repository/public-CI use. These plans do not schedule that future decision or manufacture manual UAT. A phase verifier must preserve this limit rather than claiming automated legal clearance.

## Prohibition recall — stage 1, adversarial

Question applied to the exact RIGHTS-01 text: What could this feature silently become that the author would not want, but the requirement does not forbid?

| Raw candidate | Precision disposition |
|---------------|-----------------------|
| Populated fields or matching hashes are marketed as automated legal clearance | KEEP: bespoke transparency constraint; no legal adjudication by code. |
| Historical acceptance is silently revoked or generalized into blanket permission for new fixtures | KEEP: bespoke owner-value constraint; preserve dispositions and evaluate new evidence explicitly. |
| Any public repository is treated as permission to redistribute | Merge into the first kept transparency constraint; D-01 already supplies the concrete evidence rule. |
| Fixture identities can be coherently rewritten along with mutable digest tables | DROP: normal correctness/tampering concern; threat T-20-01 and coordinated-mutation test own it. |
| An allowed directory permits hidden unknown payloads | DROP: ordinary package-policy correctness; threats T-20-02/T-20-05/T-20-09 own it. |
| Missing notice files are silently ignored | DROP: explicit requirement and ordinary correctness; threats T-20-03/T-20-06/T-20-10 own it. |
| Root MIT is replaced to simplify mixed license handling | DROP: already expressly forbidden by RIGHTS-01/D-03; byte-bound baseline controls enforce the explicit requirement. |
| Archive links/path traversal escape the tree | CANON REFERRAL: file-handling security belongs to the phase threat models and secure-phase; no duplicate prohibition minted. |
| Private personal ROM/save material is made public | CANON REFERRAL: privacy/disclosure belongs to secure-phase and the existing project prohibition; no duplicate minted. |
| Every fixture is retroactively migrated or extra game candidates searched | DROP: explicitly excluded phase scope in CONTEXT.md, carried directly into task boundaries. |
| A complete-but-ambiguous component grant becomes approved | Merge into the first kept transparency constraint; checker rejects ambiguous scope and the source reviewer owns interpretation. |
| A new framework/dependency is added merely to validate JSON | DROP: ordinary engineering preference already settled in D-02. |

## Prohibition recall — stage 2, precision result

Two bespoke prohibitions remain. The installed probe-core.projectProhibitions serializer was invoked on these unresolved items and its exact flat projection is carried in 20-01 must_haves.prohibitions. Both are descriptor-less flagged-unverified: no check_kind/check_target/check_rule/check_violation_fixture/check_clean_fixture is fabricated. Coverage is applicable=2, resolved=0, unresolved=2, byVerification test=0/judgment=0. The raw engineering/canon candidates above are precision exclusions, not silently dismissed retained items.

The absence of legal adjudication is a reported limitation, not a new manual acceptance checkpoint. There is no manual UAT in Phase 20.

## Verification and closure contract

The validation map records all eight tasks, actual commands and failure signals. Product fixture/notice identities come from immutable baseline blobs; generated binaries keep their existing source/build/archive receipt authority. Temporary full stage inventories cannot authorize unknown product members. Source archive consumers retain their distinct non-testing build behavior without a hidden Git dependency; repository fixture tests and product-policy checks fail closed without their required baseline objects.

Every SUMMARY coverage entry must have id, description, human_judgment and block-style verification items with an allowed kind, ref and status: pass. The phase orchestrator runs the full existing suite once at the final implementation head, performs required review/fixes within phase caps, and uses tests/scripts/verify-uat-closure.py to generate/check closure. Source/boundary claims use point-in-time commit facts. Nothing in this planning output repairs retained v0.3 debts or starts Phase 21.
