# Phase 17: Native Save State Core - Context

**Gathered:** 2026-10-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver STATE-01 through STATE-06: the three public state calls, complete DMG-CPU-B and CGB-CPU-E snapshots (native and compatibility modes), exact continuation, transactional bounded refusal, canonical portable bytes, installed C/C++ consumers and automated safety/completeness/continuation evidence. A destination instance must have the same ROM, profile and execution mode; different host compatibility palettes must not break the promise.

Also close the explicitly inherited Phase 17 release-tooling work: RM-026/029 performance policy, RM-028 generator/rehearsal/window protection, and all RM-030 review and release-gate obligations. These are not already fixed by this discussion. RM-027 remains a named Phase 19 entry blocker. Player slots and the host-process contract remain Phase 18; no release is published here.

The owner selected all discussion areas and authorized parallel research, adversarial synthesis and automatic adoption of coherent recommendations. Three independent advisors covered compatibility/product/identity, C/API/safety/verification, and DevOps/release/performance. Relevant primary sources and existing sibling research were used; unrelated language/framework/graphics lenses create no requirements. Prefer small direct original or appropriately licensed copied helpers over new dependencies.
</domain>

<decisions>
## Implementation Decisions

### Compatibility, identity and canonical state

- **D-01: Enforce same-version compatibility.** Require exact GabbaBoy release major/minor/patch, state-format version and behavior-compatibility revision. A patch mismatch refuses even if the schema is unchanged. Both format and behavior tokens are enforced; a behavior mismatch is not a warning-and-continue path. No converter before 1.0. Layout/meaning changes bump the format token; continuation changes without layout changes bump behavior compatibility. Before the first state release, layout may evolve, but golden changes still need explicit disposition. Never advertise arbitrary unreleased builds sharing a version as compatible.
- **D-02: Keep cross-platform bytes reproducible.** The same release and compatibility tokens produce the same canonical bytes on Linux, macOS and Windows. Do not encode OS, architecture, compiler, source commit, paths, machine identity or build metadata. Bind qualification receipts to the source separately. An immutable-base ratchet must reject a changed state-golden pin without its compatibility disposition and required release/format/behavior-token change (or documented pre-first-state-release evolution). A digest cannot infer semantic equivalence: the check enforces intentional disposition and the independent continuation evidence, not automatic detection of every behavior change. Phase 19 intentionally regenerates and requalifies pins when the release token becomes 0.3.0; Phase 17's current-version bytes cannot be relabeled as that release's evidence.
- **D-03: Strong full-ROM identity.** Cache SHA-256 of the complete successfully loaded ROM; compare it along with profile/mode and ROM-derived identity. Hash once during ROM replacement, never during save/load. Reuse or copy the existing original `src/accept/sha256.c` through a small private seam; do not make the standalone core depend on the acceptance library or a new package. Preserve failed-ROM-load transactionality. Add known vectors and same-title/same-size/different-body controls, preferably an original generated CRC-32 collision pair. CRC-32 may detect state corruption; it never authenticates hostile input or substitutes for semantic validation.
- **D-04: Fixed simple format.** Retain the adopted 64-byte header, explicit little-endian fixed-width fields, exact versioned body order and exact total length. One field description drives size, write, validate, apply and test recording. Default to an untagged body: migrations and a public inspection API are out of scope, so section dispatch adds no necessary behavior. Test recording can supply field/offset diagnostics without adding a public feature. Before codec implementation, planning research must pin an exact offset/width/range table, checksum coverage, total/body size ceiling, zero-reserved rules and rejection of unrepresentable CMake version components. Fit the SHA-256/tokens/checksum without unsafe truncation; do not silently change header size. Specify signed audio-history encoding mathematically (fixed-width unsigned modulo encoding and range-checked decoding), not via native signed representation or out-of-range casts.
- **D-05: Snapshot the compatibility palette.** Include all 12 RGB555 values and restore them on successful state load, validated before mutation. D-077/Phase 11 preserve palette configuration across reset and ROM replacement; they made no future state-load promise. State loading intentionally replaces the target palette, save RAM and RTC. This corrects the palette exclusion in the old research proposal and preserves the roadmap's exactness claim without a hidden matching-palette precondition.
- **D-06: Account for every field before codec work.** Inventory the instance and nested mapper/HDMA/APU structs, including conditional members: serialize, derive, reset, or exclude with a concrete reason and discriminator. Pointer/borrowed output/diagnostic/test plumbing and immutable ROM-derived identity are excluded or retained locally; queued accepted events, emulated rumble level, RTC, audio synthesis/filter history, CPU/device latches, and working/completed frame data and metadata are included. Derive duplicates only through shared rules with evidence. Mode-selected frame buffers may be omitted only if their reset treatment and lack of observable state are proven; the inventory must not merely call them transient. Test-only behavior overrides must not silently contaminate production bytes/tokens.

### Public API and transactional safety

- **D-07: Three additive calls.** Use `gbb_state_size(const gbb_instance *, size_t *)`, `gbb_save_state(const gbb_instance *, uint8_t *, size_t capacity_bytes)` and `gbb_load_state(gbb_instance *, const uint8_t *, size_t size_bytes)`, returning `gbb_error`. Size stays fixed per loaded ROM/profile/mode through reset, execution and palette changes. All stopped, halted, locked and in-flight states reachable at a public run boundary remain saveable.
- **D-08: Explicit error classes.** Append state-specific no-ROM, bad-format/magic, unsupported-version, identity-mismatch, exact-size-mismatch, corruption and invalid-content codes; preserve every existing numeric value. Reuse `GBB_INVALID_ARGUMENT` for null arguments and `GBB_BUFFER_TOO_SMALL` for insufficient save capacity. Freeze the names and numeric additions with API docs, string mappings, inventories and compiled C/C++ clients in the same change.
- **D-09: Deterministic refusal order.** For load: null arguments; shorter than a complete fixed header; magic; unsupported format/release/behavior version; no loaded ROM; profile/mode/ROM identity; exact supplied/header/expected size; checksum; reserved bits/canonical fields/bounds/cross-field rules. Identity precedes size once the complete header is available. Never read partial header fields before the minimum-length check. Size/save check valid arguments and loaded-ROM preconditions before capacity. Compound-invalid tests pin precedence; callers need not infer which error happened from a log message.
- **D-10: No-write failure and bounded buffers.** `gbb_state_size` leaves its output untouched on error; null is not a size-query convention. A refused save leaves the entire output unchanged; success writes exactly the required bytes and preserves the tail. Load requires exact size and leaves the entire instance and owned RAM unchanged on refusal, including counters and config. No pointers, raw structure padding, host-width integers or native-endian dumps enter the format.
- **D-11: Allocation-free two-pass load and save.** Use the shared field list to validate all bytes and cross-field invariants before an apply pass that cannot fail. No per-call allocation or ROM hashing; no large per-load scratch-instance API. All three calls inherit one-thread-at-a-time instance ownership. Caller buffers remain stable for the operation and must not overlap instance-owned storage; this is an explicit API precondition, not a promise to support arbitrary aliasing through casts to the opaque instance. Test documented refusal cases without invoking undefined alias behavior; use an apply-before-validation mutant to prove atomicity sensitivity. If symmetry cannot be made auditable, rescope rather than silently weaken transactionality.
- **D-12: Canonical acceptance and bounded work.** Validate canonical booleans, unused queue slots, queue order/capacity, indices, masks, signed audio-history arithmetic and derived relationships. Reject invalid RGB555 and MBC2 representations rather than silently normalize state bytes. `save(load(S)) == S` for accepted S. Safety/bounded-work acceptance need not prove a state is physically reachable; closure and sanitizer/fuzz evidence must nevertheless cover the accepted space.
- **D-13: A consistent time horizon.** Loads reject ordinary time values above `2^62`; explicit sentinels such as `timer_reloaded_at == UINT64_MAX` retain separately validated meaning. Do not weaken closure by testing only convenient runs. Research/prototype a matching operational horizon: no time-advancing public run path can cross `2^62`; use existing invalid-state/no-progress semantics as appropriate, with exact behavior documented. Bound queued timestamps and device additions consistently. Cover STOP, HALT, IRQ/instruction dispatch, OAM DMA/HDMA, speed-switch stalls and peripheral advancement. Test cap-1, cap and cap+1, legitimate sentinels and independent missing-guard mutants before claiming closure. This is a planning research gate, not implemented evidence.

### Exact continuation and host observers

- **D-14: Preserve complete machine continuation.** Fork the existing admitted corpus plus small original fixtures at seeded random public boundaries and explicitly observed OAM DMA, HDMA, speed-switch stall, HALT/EI, APU sequencer, RTC subsecond and partial-frame points. Include other inventoried boundary-live fields (timer reload, serial, queued wake/input, FIFO/window, lockup) where applicable. Load into a fresh whitebox-poisoned destination that retains valid ownership/identity. Compare each later frame, PCM sample, run result, battery bytes, rumble level and final canonical state bytes under identical remaining inputs and slices. Separate slice-invariance evidence from fork equivalence. The coverage gate must reject a missing required category; every declared field-drop mutant must be caught for its intended discrepancy. Field recording must show each serialized field exercised with a discriminating non-default value or an explicitly justified constant/derive/reset/exclusion treatment; add a targeted fixture when the corpus never distinguishes a field. A mutant not exercised by its fixture is a test failure, not a kill. No kill-rate quota or run count substitutes for this proof.
- **D-15: Host counters are local observers.** Do not serialize or rewind `battery_generation` or `rumble_changes`; preserve their receiving-instance history and saturation behavior. Load bumps battery generation once only when projected battery bytes (RAM plus RTC) differ, and records one rumble transition only when the line changes. Repeated/unchanged loads bump zero times. Fresh-instance continuation compares battery bytes and rumble level; counter deltas are checked separately, because absolute counters cannot both remain local and match an unrelated source instance. Serialized frame generation remains machine output metadata and is restored.
- **D-16: Restore RTC exactly, without host time.** Include live/latched registers, latch edge, subsecond phase and emulated-time anchor. A state load reads no wall clock, calls no catch-up and changes no battery-file format. Document host order: load ROM, optionally import battery/catch up, then load snapshot which replaces those machine values. Tests distinguish lazy-clock representations with equal projected battery bytes from actual battery changes, and preserve canonical raw state representation.
- **D-17: Shift evidence left using existing lanes.** Inventory and `nm` writable-global checks, each with its seeded negative, must exist and run before codec data lands. The first executable plan must also exercise the compiled public API path; sequence these within that plan rather than create a checker-only feature plan. Extend real relocated/installed C and C++ consumers and package lanes. Add refusal sweeps, CRC-recomputed hostile bounds, closure, allocator instrumentation, a semantic-reaching state-load fuzz target in the hosted campaign, and cross-platform pinned digests. Negative controls include added/unclassified fields, writable globals, output mutation/allocation, altered pins and premature apply. Reuse existing CTest, sanitizer, corpus and fixture-rights mechanisms; no duplicated full CI matrix or new runtime dependency.

| Requirement | Decisions guiding planning | Required discriminator |
|-------------|----------------------------|------------------------|
| STATE-01 | D-07..11, D-17 | Compiled installed C/C++ calls; fixed size; purity/allocation and poisoned buffer/tail controls |
| STATE-02 | D-05..06, D-14..15 | Poisoned-instance forks; actual in-flight census; omitted-category and field-drop failures |
| STATE-03 | D-09..13, D-17 | Unchanged refused loads; hostile semantic bounds; all-path horizon closure; hosted state fuzzing |
| STATE-04 | D-06, D-17 | Pre-codec struct treatment and writable-global checks reject their seeded defects |
| STATE-05 | D-01..04, D-12, D-17 | Canonical LE resave and Linux/macOS/Windows pins; altered pin and token controls |
| STATE-06 | D-05, D-15..16 | RAM/full RTC replacement, no catch-up, equal/changed projected battery and counter-delta controls |

### Performance and inherited release-tooling work

- **D-18: Adopt RM-026/029 through the actual release path.** The paired wall-clock slowdown percentage and its noisy repeated review trigger become advisory. A triggered valid measurement must produce a successful advisory receipt with its timing/investigation metadata, rather than leave `pending-investigation` as a release-blocking disposition. Change producer, schema/verifier, reuse selection, rehearsal aggregate, attach and release consumers together; use a triggered-but-valid fixture to prove they accept advisory evidence while malformed or unbound evidence still fails. Keep the deterministic cachegrind Ir gate blocking, including its existing `1.10` ratio limit against `v0.2.0`, digest/consumption and repeat checks. Keep the separate realtime sanity floor blocking (currently `4.02`); advisory paired timing does not remove this floor. Report the observed same-code +18.29% to +45.04% spread and uncertainty as runner-noise evidence, not several different core regressions. An immutable-base ratchet rejects a widened Ir limit without a durable accepted cause, measured per-ROM Ir band, approved new limit, source/workload/build identities and unchanged correctness evidence. A seeded unapproved widening must fail; no automatic threshold increase to obtain green CI.
- **D-19: RM-028 generator and release window.** Render the historical performance disclosure from validated generator inputs so `--write-current` does not require hand-inserted prose. Preserve historical tagged bytes. Use managed inputs/regeneration plus an explicit short freeze/revalidation rule for the eventual version-PR window; do not broadly exclude relevant release-note paths or disable required checks. No release/version-PR work is performed by discussion.
- **D-20: RM-028 pre-tag lifecycle rehearsal.** Exercise the production attach, manifest, final-gate/publish decision and retry paths against sanitized captured GitHub API-shaped data through a bounded local service/`gh` stub. Include a non-git workspace, real check-run `url`/`html_url` and `check_suite` shapes without an invented `repository` field, and reuse of already-attached identical bytes on retry. Reject altered attached data, stale identities, duplicates and partial sets. Fixtures must be traceable to documented/captured shapes and pass the same production code paths; no self-fulfilling alternate verifier. This proves deterministic logic, not live GitHub permissions or publication. Use a throwaway live draft only if a remaining material API gap justifies it and existing authorization/credentials permit it; no published production tag/assets are mutated as a test.
- **D-21: All RM-030 findings stay in scope.** Fix the following with a positive and an intended failing control each:
  - WR-01: bind reused performance artifacts to the producing workflow/run/event, successful conclusion and exact source SHA or explicitly verified equal-tree route; branch/artifact name alone is insufficient.
  - WR-02: assert `historical/phase-08-boundary` still peels to its recorded SHA, using immutable historical facts.
  - WR-03: reject duplicate/malformed names in `SHA256SUMS` before maps can collapse them.
  - WR-04: bound new test-budget allowlist rows, including rows reusing existing references; preserve the base-revision ratchet.
  - WR-05: count suffixed plan names and enforce both the per-phase plan cap and four-phase milestone limit.
  - IN-01: preserve an independent retry tamper check and correct its order relative to attached-byte reuse.
  - IN-02: bind required-check application identity consistently at PR and release time; no wildcard where a trusted app is required.
  - IN-03: add the `report-red` timeout with real ledger evidence and exact intended title/label deduplication.
  - IN-04: verify both performance repeats' digest and consumption, and make the HDMA skipped-lane control require its intended rejection.
- **D-22: Implement the gates deferred under D-112.** `--review-approval` checks OWNER association, exact stored issue URL, comment newer than issue, full-digest approval wording and owner fields derived only after verification (8 specified mutants). Its explicit acceptance event is an Ir exception/limit change: bind the approval to the deterministic measurement receipt, approved limit, cause and per-ROM/workload band. Ordinary advisory paired timing never requires approval. No approval makes wrong correctness digests or failed independent safety/realtime checks pass. `--nightly-gate` rejects non-success, in-progress, wrong-head, superseded and skipped/failed replay evidence (6 specified mutants), with timestamp and immutable boundary re-checks. Bind both into CTest and the actual relevant release path; offline functions alone do not close RM-030.
- **D-23: Respect RM-027's boundary.** Reusable tree-equality citation support may be added alongside the gate work, but the six timeout-ledger `release_bound` rows remain a named Phase 19 entry blocker until real citations are replaced and verified before VERSION exceeds 0.2.1. Do not fabricate runs, use live HEAD ancestry as a historical fact, or mark this blocker closed by discussion. RM-024 coverage/mutation expansion and RM-025 CI scheduling remain parked; feature-required field-drop/closure tests are already mandatory here.

### Convergence and discretion

- **D-24: Plan cap remains 12, not a target.** Group cohesive state and tooling work, parallelizing only independent ownership. Plan at most 11 primary plans, reserving one slot for the single gap round; retain at most two review-fix rounds. No added phase or cap waiver is inferred from delegated recommendations. Planning must map STATE-01..06 plus RM-026/028/029/030 to executable coverage within the cap and the reconciled roadmap success criteria. If mandatory work cannot fit, report a concrete rescope before execution; never seed unresolved correctness/security findings or silently omit inherited work. There are no PLANs in this discussion deliverable.
- **D-25: Stop at discussion.** Completed stage after final review is Phase 17 discussion only. Next stage is planning for **Phase 17 — Native Save State Core**, exact command `/gsd-plan-phase 17`. Keep `workflow.auto_advance` and `workflow._auto_chain_active` false. Do not execute the phase, reopen Phase 16 verification or start Phase 18 here.
- **Agent discretion:** private helper layout, field-list spelling, portable symbol-inventory tooling, original fixture organization and economical test grouping are delegated. A licensed small copy is preferable to adding a dependency; a new dependency needs a demonstrated benefit. Research only concrete gates above and contradictions found in implementation; do not repeat the completed ecosystem survey.
</decisions>

<canonical_refs>
## Canonical References

Downstream agents must read applicable sections before planning or implementation. This context resolves the specific conflicts in the older research; it does not claim implementation or qualification.

### Scope, adopted choices and inherited obligations
- `AGENTS.md` — core ownership, automated checks/negative controls, caps and phase stops.
- `.planning/STATE.md`, `.planning/PROJECT.md`, `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md` — active phase and STATE-01..06.
- `.planning/context/DECISIONS.md` — D-069, D-077, D-102..106, D-112 and the Phase 17 adoption entry.
- `.planning/context/FUTURE-MILESTONES.md` — RM-024..030 and Phase 18/19 boundaries.
- `.planning/context/LESSONS.md`, `.planning/research/INDEX.md` — evidence navigation and existing cause/remedy lessons.
- `.planning/research/SUMMARY.md`, `.planning/research/v0.3/SUMMARY.md` — initial and current milestone synthesis.
- `.planning/research/v0.3/SAVE-STATES.md` — inventory and prior codec/test recommendations; advisory behavior revision, CRC-only ROM identity, palette exclusion, section framing and old phase split are superseded here.
- `.planning/research/v0.3/SIBLING-NESTURBATOR-MUHTARI.md`, `.planning/research/v0.3/SIBLING-YOUNGER-CORES.md`, `.planning/research/v0.3/SIBLING-GLUEYNEO.md` — existing sibling evidence; not GabbaBoy qualification.
- `.planning/milestones/v0.2-phases/GB-11-cgb-colour-rendering-and-player-colour/11-CONTEXT.md` — compatibility palette/reset contract.
- `.planning/phases/GB-16-tune-up-and-v0-2-debt-closure/16-CONTEXT.md`, `.planning/phases/GB-16-tune-up-and-v0-2-debt-closure/16-REVIEW.md`, `.planning/phases/GB-16-tune-up-and-v0-2-debt-closure/16-REVIEW-DISPOSITION.md`, `.planning/phases/GB-16-tune-up-and-v0-2-debt-closure/16-SECURITY.md`, `.planning/phases/GB-16-tune-up-and-v0-2-debt-closure/16-07-SUMMARY.md` — exact inherited findings and D-112 exceptions; historical completion stays boundary-bound.

### Existing implementation and recurring evidence
- `include/gabbaboy/gabbaboy.h`, `src/core/gabbaboy.c` — public ownership/error/run/output contracts and complete instance state.
- `src/accept/sha256.c`, `CMakeLists.txt` — original hash implementation and release-version source.
- `tests/test_battery.c`, `tests/test_rtc_battery.c`, `tests/test_mbc3_rtc_internal.c`, `tests/fuzz_core.c` — existing transactional, lazy-RTC, whitebox and fuzz patterns.
- `tests/consumers/c/main.c`, `tests/consumers/cpp/main.cpp`, `tests/CMakeLists.txt`, `tests/expected-tests.txt` — compiled installed consumers and exact inventory.
- `tests/scripts/verify-summary-coverage.py`, `tests/scripts/verify-uat-closure.py` — block-schema SUMMARY coverage and automated closure.
- `tests/scripts/verify-perf-gate.py`, `tests/scripts/run-perf-gate.sh`, `tests/baseline/perf-gate-v1.txt` — deterministic Ir and independent realtime-floor policies.
- `tests/scripts/measure-release-baseline.sh`, `tests/scripts/verify-v02-performance.py` — advisory-trigger producer and receipt-consumer migration; existing pending investigation is not a successful advisory receipt.
- `tests/scripts/verify-support-ledger.py`, `tests/scripts/verify-planning-hygiene.py`, `.github/scripts/verify-workflow-policy.py`, `tests/cmake/ci-lanes.cmake` — generator, cap and budget seams.
- `.github/workflows/ci.yml`, `.github/workflows/release.yml`, `.github/workflows/release-rehearsal.yml`, `.github/workflows/nightly-asan.yml`, `.github/ci-timeouts.json` — actual execution/inherited release paths.
- `docs/native-integration.md`, `docs/audio-and-playback.md`, `docs/release.md`, `docs/support/v0.2.1.md`, `README.md` — update API, observers, palette, save replacement and scoped claims together during implementation.

### Primary-source background considered
- https://cmake.org/cmake/help/latest/variable/CMAKE_PROJECT_VERSION.html — project version source; exact equality is GabbaBoy policy.
- https://semver.org/ — version vocabulary; no upstream rule grants save-state compatibility.
- https://nvlpubs.nist.gov/nistpubs/fips/nist.fips.180-4.pdf — SHA-256 definition.
- https://www.rfc-editor.org/rfc/rfc3385.html#section-10 — CRC error detection versus deliberate changes.
- https://raw.githubusercontent.com/libretro/RetroArch/master/libretro-common/include/libretro.h — fixed loaded-game size precedent only; no libretro requirement.
- https://raw.githubusercontent.com/mgba-emu/mgba/master/src/gb/serialize.c — explicit LE/version/identity precedent; lenient compatibility is not adopted.
- https://raw.githubusercontent.com/LIJI32/SameBoy/master/Core/save_state.c — alternate section/sanitization pattern, not an atomicity specification for this core.
- https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf — C object representation and overlapping-copy hazards.
- https://docs.github.com/en/rest/actions/workflow-runs — actual run/event/SHA/conclusion shape.
- https://docs.github.com/en/rest/releases/releases and https://docs.github.com/en/rest/releases/assets — draft/assets/retry API shapes.
- https://github.com/googleapis/release-please/blob/main/docs/customizing.md — managed release inputs and regeneration policy.
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
The opaque core currently concentrates machine state in `struct gbb_instance` and nested device structs. Battery import already validates before applying; RTC export projects a local copy without mutation and import compares projected clock bytes before advancing generation. The original SHA-256 helper, whitebox device tests, installed C/C++ programs, existing mutant builds, CTest inventory and hosted sanitizer/fuzz lanes supply direct extension points.

### Established Patterns
Run calls return at safe CPU-operation boundaries while device state remains in flight. Host timing/filesystems/devices stay in adapters. Frame metadata is externally observable; synthesis history is necessary for exact PCM. Compatibility palette configuration survives reset/ROM replacement but affects future pixels. Public outputs and failed operations preserve caller-owned data.

### Integration Points
ROM replacement caches strong identity transactionally; the shared codec walks boundary-live state; the run/event preflights enforce the time horizon; the public header, error mappings, installed clients and docs change together. Existing release/performance scripts must execute the new checks in their real paths, with no separate untested success route. There are no codebase maps; the scout used direct header/core/battery/fuzz/consumer inspection.
</code_context>

<specifics>
## Specific Ideas

The owner explicitly requested breadth and depth across relevant roles, comparison of pros/cons/footguns, high-quality primary sources, an adversarial pass, and automatic adoption at diminishing returns. They prefer “another copy and paste” over another dependency. Apply that preference within license/provenance and ownership rules; it is not permission to copy unrelated frameworks or reopen settled hardware choices.

Concrete planning gates: token/header fit and intentional-bump tests; SHA reuse without acceptance-library coupling; state restore into a different palette; inventory before codec with a compiled API path in the same first plan; signed audio/cross-field bounds; all-path `2^62` horizon closure; host-counter delta semantics; actual API-shaped pre-tag replay; and mandatory tooling coverage within the phase cap. These gates are unresolved implementation work, not reasons to ask routine owner questions again.
</specifics>

<deferred>
## Deferred Ideas

- Phase 18 — player slots, runner files/signals/exit codes and declared battery format ids.
- Phase 19 — final RM-027 tree-bound timeout citations, exact-tag release rehearsal and v0.3.0 publication.
- RM-024/025 remain parked: broad coverage/mutation expansion and CI scheduling changes beyond mandatory state/tooling evidence.
- Cross-version conversion, BESS, RTC footer interop, rewind/runahead UI, libretro, live Playstead qualification and new hardware/perceptual claims remain out of scope.
- A public snapshot probe, tagged extensibility framework, compression dependency and per-load scratch-buffer API have no demonstrated consumer here.
</deferred>

---
*Phase: 17-Native Save State Core*
*Context gathered: 2026-10-26*
