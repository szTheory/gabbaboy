# Phase13 plan source audit

Status: planning coverage only; no HDMA implementation or test pass is claimed.

## Plan and wave ownership

| Plan | Wave | Needs | User-facing capability |
|---|---|---|---|
| 13-01 | 1 | none | Real-transfer boundary gate and guest register visibility |
| 13-02 | 2 | 13-01 | Complete bounded transfer, restart and address policies |
| 13-03 | 3 | 13-02 | Real HALT wake and independent competing stalls |
| 13-04 | 4 | 13-03 | Partition, lifecycle and hostile-resource invariants |
| 13-05 | 5 | 13-04 | Bounded runtime mutation sensitivity and inherited anchors |
| 13-06 | 2 | 13-01 | Pinned four-case SameSuite admission and reproduction |
| 13-07 | 6 | 13-05 | Magen HDMA admission and structural differential oracle |
| 13-08 | 4 | 13-03 | Original visible DMA guest and existing player smoke |
| 13-09 | 7 | 13-05, 13-06, 13-07, 13-08 | Executed SameSuite dispositions and optional CGB-C boundary |
| 13-10 | 8 | 13-05, 13-09 | Installed C/C++ DMA consumers and closed package contents |
| 13-11 | 9 | 13-09, 13-10 | Atomic consumer claims and executable documentation contracts |
| 13-12 | 10 | 13-11, 13-08 | Current-revision lane cost, evidence closure and phase pause |

All shared core, CMake/inventory, profile, fixture-repro and test-harness edits are ordered. Same-wave plans have zero file overlap. Fixture admission branches start only after the first real-transfer gate. Plan07 waits for the shared runtime mutant core; no one creates a second mutant framework.

## Multi-source coverage audit

| Source | ID | Feature / requirement | Plan | Status |
|---|---|---|---|---|
| GOAL | Phase13 | CGB software uses general/HBlank DMA with hardware-shaped stall/cancel/readback, bounded per run | 01–12 | COVERED |
| GOAL | SC1 | Current VRAM bank; GDMA steal; visible-line HBlank; exact selected SameSuite plus original guests | 01,02,03,06,08,09 | COVERED |
| GOAL | SC2 | FF55/cancel/HALT/LCD/source stated qualified transitions | 02,03,04 | COVERED |
| GOAL | SC3 | Maximum128 blocks, partition equivalence, Magen pass and optional Mealybug outside denominator | 04,07,09 | COVERED |
| REQ | CGB-07 | General-purpose/HBlank VRAM DMA, CPU stall, cancel, HDMA5 readback, HALT and bounded runs | 01–12 | COVERED |
| RESEARCH | R01 | D09 real transfer versus arithmetic | 01 | COVERED |
| RESEARCH | R02 | Nominal64/cadence/sample/overhead POLICY | 01,02,05 | COVERED |
| RESEARCH | R03 | Explicit active writes/cancel/restart/continuation | 02 | COVERED |
| RESEARCH | R04 | LCD initial/armed toggle transitions | 02 | COVERED |
| RESEARCH | R05 | Source map/disabled RAM/invalid classes/prefix | 02 | COVERED |
| RESEARCH | R06 | Destination overflow and widened cursor | 02 | COVERED |
| RESEARCH | R07 | Per-block VBK and same-half-dot ordering | 01,02,03 | COVERED |
| RESEARCH | R08 | HALT/STOP/concurrent speed/OAM | 03 | COVERED |
| RESEARCH | R09 | Lifecycle/output/headroom/max128 | 04 | COVERED |
| RESEARCH | R10 | Hidden-state critical cuts/both speeds | 04 | COVERED |
| RESEARCH | R11 | Original guest/oracle/mutant specificity | 03,05,08 | COVERED |
| RESEARCH | R12 | Pinned four SameSuite/Magen reproduction | 06,07,09 | COVERED |
| RESEARCH | R13 | G1 rights/CGB-C denominator | 09 | COVERED |
| RESEARCH | R14 | Installed package/player/claims and full activation after workflow edit | 08,10,11,12 | COVERED |
| RESEARCH | R15 | Recurring CI and ASan/mutation cost | 05,12 | COVERED |
| CONTEXT | D-01 | Machine contract and unchanged ABI | 01,04,10 | COVERED |
| CONTEXT | D-02 | Flat dependency default | 01,06 | COVERED |
| CONTEXT | D-03 | Whole instructions and preflight | 01 | COVERED |
| CONTEXT | D-04 | Write-only registers and cursors | 01,02 | COVERED |
| CONTEXT | D-05 | Bounded register state/table | 02 | COVERED |
| CONTEXT | D-06 | Exact83/02/00/80 adopted cases | 02,09 | COVERED |
| CONTEXT | D-07 | Initial kick versus visible HBlank | 02 | COVERED |
| CONTEXT | D-08 | 64-half-dot data/cadence sensitivity | 01,02,05 | COVERED |
| CONTEXT | D-09 | In-flight seam real-transfer gate | 01 | COVERED |
| CONTEXT | D-10 | Independent stall endings | 03,04 | COVERED |
| CONTEXT | D-11 | Narrow source/VBK/order path | 01,02,03 | COVERED |
| CONTEXT | D-12 | Invalid source fail-closed prefix | 02 | COVERED |
| CONTEXT | D-13 | 9FF0 overflow state | 02 | COVERED |
| CONTEXT | D-14 | HALT/STOP/speed/OAM | 03 | COVERED |
| CONTEXT | D-15 | Lifecycle/resource/headroom bounds | 04 | COVERED |
| CONTEXT | D-16 | Four SameSuite admissions | 06,09 | COVERED |
| CONTEXT | D-17 | Magen new admission/oracle | 07,09 | COVERED |
| CONTEXT | D-18 | Optional Mealybug G1/CGB-C exclusion | 09 | COVERED |
| CONTEXT | D-19 | Original public guest/steal discriminator | 01,03,08,10 | COVERED |
| CONTEXT | D-20 | Partition/hostile/mutation controls | 04,05 | COVERED |
| CONTEXT | D-21 | Recurring CI/inventories/cost | 05,06,07,08,10,12 | COVERED |
| CONTEXT | D-22 | Automation/SUMMARY schema/no routine UAT | 01–12 | COVERED |
| CONTEXT | D-23 | Installed consumers/player smoke | 08,10 | COVERED |
| CONTEXT | D-24 | Claims/anchors/disposition mirrors | 01,02,03,05,09,11,12 | COVERED |
| CONTEXT | D-25 | Stage-specific stop and durable route | 12; planning parent handoff | COVERED |

Deferred/excluded: Phase14 mode3/window/APU/corpus expansion, Phase15 game/release qualification, public DMA APIs, generalized bus/event engine, save-state serialization and mandatory emulator dependency. None is implemented by this set. Four selected SameSuite names narrow the roadmap's dma shorthand per locked D-16.

## Selected-model policy targets

These are deterministic software choices, not new silicon facts. The complete actionable tables are in13-01..03.

| Unknown cell | Selected target | Provenance and discriminator |
|---|---|---|
| In-flight edge | Latch eligible edge; finish late accesses; service before next opcode/IRQ at safe instruction boundary | Real research collision, candidate arithmetic only; real-transfer gate in01 proves conservation/order/output/partition |
| Nominal data/cadence/overhead | 64 master half-dots;16 bytes at4,8,...64; startup/teardown0 |64 derived from Pan Docs nominal; cadence/sample/extra cost POLICY.02/05 report sensitivity ±1,2,4,8 and blind windows |
| VBK/source/order | VBK sampled per block; storage sampled on byte commit; OAM before HDMA before PPU, preserving prior relative order | SameBoy per-block differential plus deterministic POLICY; bank/order faults reject |
| Active FF55/cancel/restart | HDMA cancel reads80|writtenLow7; bit7 rewrite replaces remaining count without new kick; active GDMA/FF51–54 writes ignored | Exact00 cancel is adopted D-06; other cells POLICY; source-derived state matrix |
| LCD toggles armed | Clear unadmitted edge on disable, retain armed request, no disable/enable kick; wait next visible3→0 | POLICY/UNKNOWN, distinct from initial-start kick |
| Invalid source | Prevalidate16 addresses; preserve valid prefix, abort rejected block unchanged, inactive remaining count, existing unsupported-bus reason | Fail-closed POLICY; no accidental CPU I/O reads |
| Destination9FF0 | Legal last block; widened cursorA000; further block aborts without wrap, remaining count retained | Pan Docs premature stop, register state UNKNOWN; explicit policy/status/data test |
| HALT/STOP/speed/OAM | HALT no new ordinary admissions; started block finishes. STOP freezes/preserves. Speed and DMA advance concurrently with independent residuals; OAM concurrent existing order | Primary HALT plus existing STOP contract; collision/speed policy remains UNKNOWN |

## Probe and capability evidence

SPEC-less fallback is ON (default); no SPEC Edge Coverage or Prohibitions section supplied.
The deterministic edge report retained exactly one CGB-07 unclassified/unresolved row:
applicable1, resolved0, unresolved1. It remains a flagged assumption, never auto-resolved,
dismissed or backstop. Specific researched tests compensate; they do not rewrite the engine verdict.

Adversarial prohibition recall candidates: out-of-bounds access, unbounded work, lost split remainder,
partial failed load, extra public API, fabricated hardware qualification, unlicensed fixture import,
telemetry, broadened game claims, and stale remote green. Precision drops correctness items into
the edge/source/security tasks; existing AGENTS rights/privacy/no-telemetry and branch/check canon
are referred to their existing executable project contracts rather than duplicated imaginary UAT.
One bespoke transparency item is kept: author/differential/CGB-C evidence must not silently become
physical CGB-E qualification. OpenGSD projectProhibitions projected it into13-01 must_haves.prohibitions
with status unresolved and no check descriptor. It stays flagged-unverified during planning.13-11 creates one all-surface claim predicate with --subject and generated clean/known-bad text snapshots;13-12 Task1 creates the builtin node:test adapter and proves real bad RED, clean GREEN and live non-vacuous GREEN through installed OpenGSD check prohibition-enforcement. Only after proof it serializes projectProhibitions resolved/test output into the existing13-01 item with flat check_kind, check_target, check_violation_fixture and check_clean_fixture, reruns the saved projection and requires emitted status green/flagged false/located true/tier test plus real failFirst evidence. Closure/--handoff regenerates subjects and fails on unresolved/flagged/stale evidence. This resolves the claim-language safeguard, never physical UNKNOWN or the generic edge assumption.

Active capability contributions were read verbatim from the parent-provided planner contribution file.
API detector examined the actual Phase13 section plus complete plan bodies and returned detected:false,
not skipped; no external-API matrix exists because none is integrated.
Assumption-delta scan returned detected:false, not skipped. Schema scan found no Payload/Prisma/Drizzle/
Supabase/TypeORM paths; no schema push applies. No one-way API/schema/dependency change is planned.
OpenGSD runtime identity: @opengsd/gsd-core1.16.0. Graph context disabled. Estimate calibration
factor1, sample_count0, confidence low; raw projections remain unscaled. Each plan has2 tasks;
most tasks modify at most5 files.13-02/09 Task2 each add one tightly scoped durable-memory path (six files), colocating actual evidence with its record. The13-01 tracer owns nine inseparable behavior/mirror paths; its atomic scope rationale is documented in that plan.

## Artifact creation and command grounding

All pre-existing task paths were checked against git ls-files. New files are explicitly marked in
the creating plan and inherited only through dependencies. phase1 uses build and phase1-asan uses
build-asan from CMakePresets.json. Player plan creates build-player explicitly. test_cgb_hdma's
runtime location is explicitly assigned to build/tests/test_cgb_hdma in13-03. Installed tests are
conditional in existing CMake;13-10 installs current bytes then configures GBB_TEST_INSTALL_PREFIX
before asserting those target names. Every CTest verification enumerates JSON and requires explicit
new case names before selecting a group; existing cmake/ExpectedTests.cmake checks full set equality.
Prior proven configure/build, CTest and frozen-DMG commands are retained where applicable.

New target creation owners:
01 private tracer/visibility and immediate P12 FF55 mirror migration;02 matrix/address/timing;03 public/lowpower/OAM;04 partition/lifecycle/fuzz;
05 shared runtime mutants;06 reproduction script;07 Magen;08 original reproduction/player;
09 SameSuite/dispositions/original guest registration;10 package scans;11 direct native/player claim checker and selftest;
12 full/native+player/selftest Python claim registration plus CI-safe cgb_hdma_lane_contract (--lane) / cgb_hdma_lane_contract_selftest (--lane-self-test), and local closure/handoff checker. Recurring selectors check structural inventories/workflows without Node/OpenGSD or local stage/prohibition receipts and never mutate the checkout. Mandatory automatic local --prohibitions / --prohibitions-self-test execute the real producer proof outside CTest/inventories; missing runtime fails local closure rather than skipping proof.13-12 owns tests/scripts/cgb-hdma-prohibition.test.cjs and the post-proof13-01 projection edit; generated subjects/request/receipt live in ignored build/phase13-prohibition and regenerate before verify-work.13-11 owns preview workflow wording before full activation. Later tests cannot run before these dependencies.

## Stage pause

This artifact completes Phase13 planning only. Parent owns plan validation/commit and STATE/
continuation updates. Next is Phase13 CGB HDMA execution: `/gsd-execute-phase 13`.
Do not execute now. Phase14 CGB-E Model Qualification and Corpus remains unstarted.
After eventual Phase13 execution, verification is `/gsd-verify-work 13`; after verified/reviewed
exact-head merge the owner may choose `/gsd-discuss-phase 14`. Both auto flags remain false.


## Revision1 issue dispositions

| Finding | Disposition and concrete evidence |
|---|---|
| Research Q1–Q4 unmarked | All four now map to explicit selected policies, named plan/test discriminators or the blocking real-transfer execution gate; physical UNKNOWN remains a claim limit, zero owner UAT. |
| 13-11 ten-file warning | Reduced to eight by moving CTest/inventory registration to13-12. Five-path document/checker tracer plus three-path player expansion keep direct positive/mutated checks; no surface dropped. |
| 13-12 ten-file warning | Reduced to eight by moving DECISIONS policy recording to13-02 Task2 and INDEX admission/disposition navigation to13-09 Task2, each with stage/provenance and deletion-control contracts. PROJECT/STATE/continuation stay at final closure. |
| Premature full claims activation |13-11 verifies explicit selectors directly.13-11 Task2 updates preview text and proves default all-surface mode;13-12 then atomically registers full/native+player/selftest names and checks all three. |
| First tracer changed existing mirrors |13-01 Task1 owns source/model/profile/visibility and P12 FF55 positive/FF54 negative plus disposition migration; existing exact-name guards and selected tests pass before expansion. Atomic nine-path exception avoids a required failing intermediate revision. |

Revision2 connects the machine-checkable prohibition to actual downstream enforcement.13-11/12 each own nine paths after moving preview wording into13-11 and adding13-12's adapter/projection edit. The final six-path atomic task owns the enforcement source, metadata, registration and receipt together; no scope or test count is removed. Physical UNKNOWN remains unchanged, with zero owner checkpoints.

Plans remain twelve, tasks twenty-four and waves unchanged; added memory paths do not overlap another plan in the same wave. Estimates remain low-confidence with zero calibration samples;13-11/12 retain bounded28k/30k projections within the100k execution budget. These are planning checks, not execution receipts.


## Revision2 installed-producer pattern proof

Executed locally against identity-checked @opengsd/gsd-core1.16.0, using temporary original text subjects only. This proves the adapter/projection/producer mechanism; it is not execution evidence for the future Python claims checker, emulator behavior or physical hardware.

Reproduce after resolving GSD_TOOLS with the standard runtime resolver: create a temporary node:test file with one descriptive test named qualified claim text rejects physical qualification conflation. Its callback reads GSD_PROHIB_SUBJECT, falling back to a clean text file, and asserts text equality to CGB-C informational; physical CGB-E UNKNOWN with diagnostic hardware-qualification diagnostic. The clean subject contains that exact line; the bad subject contains CGB-C proves physical CGB-E qualification. Use projectProhibitions on a resolved/test item with node-test target and flat violation/clean fixture paths, then descriptorFromProjection on that result to create request.json containing prohibition, check and mode autonomous. Run `node "$GSD_TOOLS" check prohibition-enforcement /tmp/claim-proof/request.json` from the checkout (temporary directory names are arbitrary; no personal path is needed).

Observed emitted root producer JSON: status green, flagged false, tier test, located true, kind node-test, evidence containing passed true, failFirst true and failFirstProof violation-fixture. Reusing the bad file as check_clean_fixture instead of the clean file produced status unverified, flagged true, evidence empty. Thus the installed producer independently rejects a false clean control. Execution13-12 must repeat the proof using the real Python predicate, generated complete claim snapshots, actual live checkout and saved13-01 projection; the temporary equality predicate is never shipped or counted as claim coverage.


## Revision3 CI dependency boundary

The existing ci.yml full native/ASan inventory remains independent of Node and OpenGSD installation.13-12 owns the CI-safe Python lane selectors and recurring claim registrations; the builtin node:test adapter and actual producer fail-first/clean/live/saved-projection proof run automatically in local GSD closure before handoff. Both task commands explicitly execute --prohibitions and --prohibitions-self-test; --handoff reruns enforcement and verifies green/unflagged. Only explicit local proof may update13-01; isolated negative controls never mutate the live projection. No CTest target is required for local proof, no conditional skip or new hosted dependency is introduced, and physical UNKNOWN remains unchanged. Twelve plans, twenty-four tasks and ten waves are preserved.
