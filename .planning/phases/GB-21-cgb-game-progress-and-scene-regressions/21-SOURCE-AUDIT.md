# Phase 21 — Source Coverage and Planning Decisions

Original planning covers seven plans and sixteen tasks in five waves. Plan 21-08 adds two tasks in Wave 6 as the single reserved gap round after final review. The resulting eight plans remain within the twelve-plan cap; the primary and fallback attempts each occupy exactly one plan. This planning artifact does not itself establish implementation, candidate admission, game progress or phase completion.

## Source Coverage

| Source | Item | Plans | Disposition |
|--------|------|-------|-------------|
| GOAL | Reproducible shared CGB progress, bounded game outcome and controlled scene-report workflow | 01–07 | Covered |
| REQ | GAME-01 — RGB555 progress and preserved DMG acceptance | 01, 02, 07 | Covered |
| REQ | GAME-02 — exact bindings and meaningful positive/input/predicate controls | 01–05, 07 | Covered |
| REQ | FIXT-01 — primary, sole eligible fallback, exact gates and justified absence | 03–05, 07 | Covered |
| REQ | FEED-01 — concise intake, agent-owned reproduction, independent regression and privacy | 06, 07 | Covered |
| CONTEXT | D-01 — Potion Panic first, µCity 1.3 only after primary no-go, no third game | 03–05, 07 | Covered |
| CONTEXT | D-02 — Phase 20 component terms, exact source/build/ROM/header/mode and notices | 03–05, 07 | Covered |
| CONTEXT | D-03 — shared runner/API seams, actual loaded mode, preserve DMG | 01, 02, 07 | Covered |
| CONTEXT | D-04 — shortest meaningful input-driven in-game state change and independent predicate | 01, 02, 04, 05 | Covered |
| CONTEXT | D-05 — independent original native-CGB harness proof and honest harness-only label | 01, 02, 07 | Covered |
| CONTEXT | D-06 — RGB555/PCM observations bound for repeatability, without accuracy promotion | 01, 02, 04, 05, 07 | Covered |
| CONTEXT | D-07 — static independent pixels or relevant bounded semantic/sequence expectation, targeted negative | 02, 06, 07 | Covered |
| CONTEXT | D-08 — title/scene/symptom starts agent metadata/reproduction, no recurring owner-play gate | 06, 07 | Covered |
| CONTEXT | D-09 — explicit provision before specific private-media reads, no tracked/hosted personal data | 06, 07 | Covered |
| CONTEXT | D-10 — existing C/CMake/CTest and stdlib, no new dependency by default | All | Covered |
| RESEARCH | Existing CGB progress callback refusal versus working separate RGB555 capture | 01, 02 | Covered |
| RESEARCH | Mode must come from sized loaded gbb_info, not selected profile/header | 01–05 | Covered |
| RESEARCH | Exact receipt/predicate/script/frame/PCM bindings and valid raw negatives | 01–05, 07 | Covered |
| RESEARCH | Potion Panic upstream/fork mismatch, recursive inputs and missing-tool caveats | 04 | Covered by actual bounded source/build gate; scouting facts do not predetermine no-go |
| RESEARCH | µCity preferred artifact, exact 1.3 identity, mixed terms and short predicate feasibility | 05 | Covered conditionally after checked primary no-go |
| RESEARCH | No current actionable GabbaBoy scene defect or independent live scene oracle | 06, 07 | Covered by tested intake/promotion contracts and honest no-live-report status |
| RESEARCH | ASVS L1 bounded native parsing, identity, false assurance and private-data risks | All threat registers | Covered |
| CODE DISCOVERY | Fixed Libbet predicate evaluator, semantic role diagnostics and shade/audible/SGB success gates | 01, 02 | Covered by appended internal evaluator/observation policy with unchanged legacy defaults |
| PROJECT | D-069 automated checks/negatives, shared UAT closure and SUMMARY coverage schema | All; final closure 07 | Covered |
| PROJECT | Deterministic performance, state continuation, exact-source consumer/CI and phase stop | 07 | Covered |

RIGHTS-01 retains Phase 20 ownership; it is reused as a mandatory admission boundary, not reassigned or marked satisfied by these plans. Phase 22 diagnostics and Phase 23 release, third-candidate search, supported Deck/Linux gameplay, Libretro, timing rewrites, root licence migration and new consumer/state freezes remain outside scope.

## Discretion Applied

- Generate the original native-CGB test ROM in a private temporary directory from documented project-authored SM83 bytes, following `host_fixture.py`. Pin its source/build/digest and compiled predicate. This proves the implementation independently before external candidates; if both fail, the final outcome cites this same result as harness-only. It does not add a fixture-directory exemption, vendor a ROM, or create game evidence.
- Use one readiness byte and one input-driven progress byte; RIGHT changes an authored uniform RGB555 screen from 0x001F to 0x03E0. This independently specified sequence also demonstrates why Libbet's shade/audible gates must remain case-specific. Its impossible predicate expects the unreachable value 0xFF.
- Keep source/tool acquisition in private temporary areas, verify immutable identities before execution, then run upstream build code only in a disposable low-privilege credential-free offline sandbox/container with read-only source/toolchain and one writable output mount. Trusted synthetic outside-root/network probes must establish the intended denial first; otherwise record build-isolation no-go without running scripts. A necessary pinned build-only tool may be acquired for the single documented recipe; unavailable/unpinnable required tooling records a concrete build no-go. No application runtime dependency or global installation is planned.
- Keep three established checkpoint names (`title`, `play_start`, `mid`) and `hit` for the shared path. Candidate budgets derive from the shortest meaningful source route; the original control has a fixed 120-frame budget including the existing tail.
- Implement scene intake and promotion contracts without inventing a current report. Synthetic checker subjects are explicitly controls. A real report remains unresolved unless permitted reproduction and an independent expectation support promotion.

## Dependency and Ownership Check

| Wave | Plans | Dependency/ownership |
|------|-------|----------------------|
| 1 | 01, 03 | Runner/acceptance files versus separate candidate checker and test-area include; no overlapping modified paths |
| 2 | 02, 06 | 02 expands 01; 06 consumes 01/03 and owns separate scene checker/docs/test-area file; no same-wave overlap |
| 3 | 04 | Primary candidate consumes complete harness and candidate contract |
| 4 | 05 | Sole fallback consumes primary final disposition; shared predicate/notices writes are sequential |
| 5 | 07 | Final composition/docs/qualification waits for controls, candidate pair and scene contract |

All tasks modify at most five named files; plans have two or three tasks. Existing paths were grounded through `git ls-files`; other paths are intentional new artifacts. `CMakePresets.json` declares phase1 binaryDir `${sourceDir}/build`, grounding local `build/gabbaboy-runner`; CTest registrations use `$<TARGET_FILE:gabbaboy-runner>` across platforms. Estimate calibration returned factor 1 with zero samples and `confidence: low`; all estimate blocks preserve that derived confidence.

## Spec-less Edge Coverage

The default-on probe emitted six unresolved rows. Every row is retained as a flagged assumption in plan frontmatter; none is dismissed or auto-resolved.

| Requirement | Probe category | Status | Plan |
|-------------|----------------|--------|------|
| GAME-01 | unclassified | unresolved; verification null | 01 |
| GAME-02 | unclassified | unresolved; verification null | 02 |
| FIXT-01 | adjacency | unresolved; verification null | 03 |
| FIXT-01 | empty | unresolved; verification null | 03 |
| FIXT-01 | ordering | unresolved; verification null | 03 |
| FEED-01 | unclassified | unresolved; verification null | 06 |

Surfaced edges 6 = authored flagged assumptions 6. The concrete tests do not claim to have resolved the generic probe classification.

## Prohibition Recall and Precision

The recall considered: cross-model/accuracy claim inflation; a new public ABI without need; RGB555 byte-order changes; a self-derived golden mistaken for progress; missing-input positives; unbound input identities; third-game expansion; using absence to hide a defect; licence labels mistaken for permission; recurring compulsory owner play; implicit private-media collection; and screenshot hashes mistaken for scene oracles.

Routine implementation/scope items (ABI, byte order, input binding, false positives, candidate count, defect lifecycle) are covered by task/edge/review contracts rather than minted as values prohibitions. Canon-referral breadcrumb: generic legal grant authority and personal-data access/disclosure are covered by the adopted fixture/privacy boundaries and their existing security/compliance controls; no new canon prohibition is minted.

Two bespoke values/transparency constraints survive precision: honest evidence-class claims and owner agency in the report workflow. They were projected through the installed `projectProhibitions` serializer into Plan 21-07 with `status: unresolved`, `verification: judgment`, explicit flagged-unverified reasons and no `check_*` descriptor. They restate locked D-05/D-06/D-08/D-09 and do not introduce a new decision. Surfaced prohibitions 2 = authored items 2. The final checker has concrete claim/privacy contract negatives, but planning does not fabricate a wired-check descriptor or silently mark a judgment resolved.

## Capability Decisions

- API-coverage detector examined the actual phase scope/plans and returned `detected: false`; exit 1 is its documented negative verdict, not a missing probe. No external API/SDK/service is integrated and no coverage matrix is needed.
- Assumption-delta detected `fallback` and `optional`. Plan 21-03 records `no-change`: exact candidate attempt remains the primary identity, D-01 already fixes the ordered conditional pair, and optional Deck exploration is outside the qualified path. No additional owner choice is required.
- No listed ORM/schema path exists in the phase scope, so schema-push guidance does not apply.
- Security enforcement is active at ASVS 1/high. All eight plans have threat registers; ordinary IDs T-21-01 through T-21-19 are unique and only reserved T-21-SC repeats.

## Planning Validation

The first independent review's five findings are addressed by scoped planning changes: all four research questions now have explicit planning resolutions while their factual execution evidence stays pending; Plans 21-04/05 justify their ten-file conditional footprint; both candidate build tasks require confinement/probes or a pre-execution no-go; and Plan 21-03 rejects missing/permissive isolation evidence through synthetic controls. The seven-plan/five-wave graph, one-plan-per-candidate bounds and all locked decisions remain intact.

The installed OpenGSD runtime validates all seven plan frontmatters and task structures; each task has read-first, acceptance criteria, automated verification and an observable fails_when condition. All files end in `</output>`. This validates executable planning shape only. No implementation tests or candidate builds are run by planning; independent plan-checker review remains the orchestrator's next gate.

## Final-Review Rescope Coverage — Plan 21-08

The final review at source `29ab44c7bbaaca8ba587c4dd19e169466df5d78e` found that a current replay could not satisfy both a historical executable hash and current embedded source revision, and that well-formed changed PCM values were accepted. Plan 21-08 consumes the phase's one gap round; it does not turn either issue into a deferred seed or use actual candidate absence as a substitute for repair.

| Source | Gap item | Plan | Disposition |
|--------|----------|------|-------------|
| GOAL | Reproducible current CGB replay after historical receipt creation | 08 Task 1 | Current CMake artifact qualification is independent of immutable historical source/hash facts. |
| REQ | GAME-02 exact source, executable and frame/PCM bindings | 08 Tasks 1–2 | Canonical current target/build receipt and exact stored aggregate observations, with causal rejection controls. |
| REQ | FIXT-01 bounded admitted/absence accounting | 08 Tasks 1–2 | Actual two-candidate no-go records stay unchanged; no third attempt or new rights authority. |
| RESEARCH | Source-qualified receipts must not be refreshed merely to agree with HEAD | 08 Task 1 | Historical blobs and current checker/build snapshot validation are distinct; CR-03 case/input equality is retained. |
| CONTEXT | D-02/D-04 exact admission and shared qualified runner | 08 Task 1 | Phase 20 admission precedes candidate execution; trusted CMake output supplies the current artifact. |
| CONTEXT | D-06 bound RGB555/PCM reproducibility observations | 08 Task 2 | Supported aggregate window values replace unsupported per-checkpoint PCM and compare exactly. |
| CONTEXT | D-10 existing helpers and standard library | 08 Tasks 1–2 | Reuse normal CMake/Python/CTest and original harness qualification, without another dependency. |

Other GOAL/REQ/RESEARCH/CONTEXT items retain the original coverage table. Deferred ideas, later phases, both retained descriptor-less prohibitions and the six unresolved generic edge assumptions keep their existing dispositions. The new plan adds T-21-18/T-21-19 and reserved T-21-SC; no existing threat ID is reused.
