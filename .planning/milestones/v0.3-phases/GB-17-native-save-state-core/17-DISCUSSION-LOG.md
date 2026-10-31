# Phase 17: Native Save State Core - Discussion Log

> Audit trail only. Do not use as input to planning, research or execution agents.
> Adopted decisions and canonical references belong in `17-CONTEXT.md`.

**Date:** 2026-10-26
**Phase:** 17 — Native Save State Core
**Areas discussed:** build compatibility and complete snapshots; caller errors and transactional safety; performance and inherited release tooling.
**Status:** Recommendations adopted after adversarial synthesis; implementation remains unstarted.

## Owner direction and discussion method

The initial prompt offered three areas for selection. The owner selected all via a broader instruction: fan out across relevant stakeholder roles, use reputable primary sources where useful, compare patterns/anti-patterns/tradeoffs, conduct an adversarial pass, stop at diminishing returns, and automatically follow the coherent recommendations. They added a preference for small flat dependencies and small copied helpers over unnecessary packages.

This explicitly delegates the recommendations and context write; it replaces the default four-question-per-area loop and final confirmation prompt. No empty-answer default was inferred. No implementation, next phase, release, external message or cap waiver is inferred from this discussion.

Three read-only `gsd-advisor-researcher` tasks ran independently: `state_compatibility`, `state_api_safety` and `release_perf_policy`. Model and effort were resolved from the installed OpenGSD runtime/project config (`gpt-6-luna`, `xhigh`) and supplied inline. A runtime warning said static agent frontmatter was stale; inline resolution avoided relying on it. Runtime identity: `@opengsd/gsd-core` 1.18.0. The completed release advisor was then assigned the bounded cross-area adversarial pass.

## Build compatibility and complete snapshots

| Option | Pros | Cons | Complexity | Selected |
|--------|------|------|------------|----------|
| Format-only, advisory behavior revision | Simple, accepts more old files | Can accept divergent continuation; conflicts with D-106 | Small parser, larger semantic uncertainty | No |
| Exact release plus format version | Clear released-build policy, portable | Development builds sharing a release version can differ | Version wiring and controls | Insufficient alone |
| Exact release, format and enforced behavior compatibility | Explicit patch refusal; detects declared layout/behavior incompatibility | Requires intentional bump discipline | Header/token checks and golden continuation evidence | Yes |
| Source/build fingerprint | Distinguishes arbitrary builds | Churn, platform-dependent identity, destabilized canonical pins | Build provenance embedded in format | No |

**Owner's choice:** follow the synthesized recommendation automatically. No cross-version converter or source-SHA compatibility promise. Keep source/build provenance in receipts, outside canonical bytes.

| ROM identity option | Pros | Cons | Complexity | Selected |
|---------------------|------|------|------------|----------|
| Title/header/size | Minimal work | Different body bytes compare equal | Small header checks | No |
| Full-ROM CRC-32 | Small accidental-error detector | Deliberate collisions are easy | Cached load-time digest | No for identity |
| Full-ROM SHA-256 | Strong full-byte identity; existing original helper | Private reuse/copy seam needed; load-time pass | No new dependency; 32-byte digest | Yes |

**Notes:** CRC remains suitable for state corruption detection, with hostile semantic validation still required. The core must not acquire a dependency on the acceptance library. Full-ROM hashing is paid only on successful ROM replacement. Header fit is a planning research gate.

| Palette option | Pros | Cons | Complexity | Selected |
|----------------|------|------|------------|----------|
| Preserve destination palette and require matching config | Keeps target host preference | Hidden precondition narrows the locked same-ROM/profile/mode promise | Extra caller coordination or mismatch check | No |
| Save and restore the 12 RGB555 values | Exact future frames across differently configured instances | State load replaces palette configuration | Small payload and bounds checks | Yes |

**Notes:** The advisors checked D-077/Phase 11: reset/ROM-load preservation does not specify future state-load behavior. The old research exclusion is superseded, not an adopted owner promise being reversed. Complete frame/audio/input/RTC state remains required. Host battery/rumble counters stay local and are tested as deltas.

## Caller errors and transactional safety

| Option | Pros | Cons | Complexity | Selected |
|--------|------|------|------------|----------|
| Fixed header/body, shared field list, validate then apply | Allocation-free; one list prevents codec drift | Pass symmetry and stable input are essential | Small direct C codec plus hostile-bound checks | Yes |
| Scratch instance on load | Obvious staged commit | Large allocation/OOM path; does not itself solve aliased input | Additional ownership/allocation paths | No |
| Tagged sections | Convenient external dump diagnostics | More parser surface without current migration consumer | Extra tags/length dispatch | No |

**Owner's choice:** follow the synthesized recommendation. Preserve exact size, output no-write/tail behavior, append typed errors and define refusal precedence. Wrong identity precedes body size when the fixed header can be safely read. Explicit stable/non-overlapping buffer and per-instance thread-ownership preconditions avoid a false arbitrary-alias promise.

**Counter contradiction found and resolved:** absolute `battery_generation`/`rumble_changes` cannot match the source in a fresh-instance fork while also remaining monotonic receiving-host observers. Compare battery bytes/rumble level, and independently test zero/one saturating counter increments. Frame generation remains snapshot metadata.

**Time contradiction found and resolved:** accepting a time at `2^62` while permitting runtime advancement beyond it violates the closure requirement. Require an all-path operational-horizon prototype and guard controls rather than narrow the property to convenient runs. Explicit timer sentinels are handled separately. This is not a claim that those guards exist today.

**Evidence balance:** inventory and no-writable-global checks precede codec work, but the first executable plan also calls the compiled public API. Fork category coverage, poisoned destinations, field-drop sensitivity, hostile sweeps, canonical pins and real hosted fuzzing complement one another; no single count or self-roundtrip proves completeness.

## Performance and inherited release tooling

| Option | Pros | Cons | Complexity | Selected |
|--------|------|------|------------|----------|
| Keep paired wall-clock review blocking | Captures end-to-end timings | Same-code +18.29%..+45.04% spread caused repeated review churn | Existing measurement/review path | No |
| Advisory paired percentage; blocking Ir and separate realtime floor | Keeps reproducible regression guard and gross speed floor | Ir misses cache/branch effects; timing uncertainty remains disclosed | Policy/receipt/workflow updates | Yes |
| Raise limits until green | Removes immediate failure | Hides cause and defeats the gate | Superficially small | No |

**Owner's choice:** automatically adopt RM-026/029 recommendation. Existing 1.10 Ir cap and separate 4.02 realtime floor remain blocking; accepted deterministic regressions need cause and measured band. The approval verifier remains mandatory for genuine explicit acceptance events, even when ordinary advisory wall-clock results no longer trigger approval.

| Rehearsal option | Pros | Cons | Complexity | Selected |
|------------------|------|------|------------|----------|
| More invented verifier-only fixtures | Cheap | Misses production/API mismatches found after v0.2.1 tagging | False confidence | No |
| Production paths replayed with sanitized captured API-shaped data | Deterministic, no production mutation; covers non-git workspace/check-run/retry defects | Cannot prove service permissions or publication | Bounded stub/fixtures using real scripts | Yes |
| Live isolated draft/repository lifecycle | Tests service transitions | Extra credentials/repository and cleanup, possible accidental writes | Separate service surface | Only for a material unresolved API gap |

**Mandatory scope:** all RM-030 WR-01..05 and IN-01..04 plus review-approval/nightly gates; RM-028 generator and version-window protection; RM-026/029 policy. Each fix needs its intended negative. RM-027 final citations remain a Phase 19 entry blocker. RM-024/025 stay parked. Four cohesive tooling batches were considered feasible, but are not fixed PLANs or permission to exceed the 12-plan cap; planning must prove the complete coverage fits or report a concrete rescope before execution.

## Cross-role synthesis and diminishing returns

| Relevant lens | Conflict examined | Result |
|---------------|-------------------|--------|
| Player/product and API consumers | Familiar save restoration versus preserving target palette | Snapshot restores palette, RAM and RTC; explicit docs |
| C/security and ownership | Atomic load versus allocation/aliasing complexity | Validate/apply one field list; explicit buffer ownership; hostile guards |
| Emulator timing/audio/rendering | Visible frames versus hidden phase/filter/FIFO state | Full boundary inventory, in-flight fork census and canonical output |
| QA and portability | Roundtrips versus omissions, false positives and host widths | Poisoned destination, field-drop controls, independent bounds and platform pins |
| DevOps/release trust | Green artifact names versus producer/source/event identity | Exact bindings and production-path gates/replay |
| Maintenance and delivery | More framework/coverage machinery versus phase convergence | Small helpers, existing lanes, hard cap, narrow research gates |

Existing sibling evidence and primary sources are listed in the canonical context. More unrelated ecosystems add no distinct contract, failure mode or acceptance discriminator. No UI work or framework selection is needed for this core phase. Reopen only a concrete contradiction or failed prototype/discriminator.

## Adversarial synthesis disposition

One bounded cross-area review returned three high-priority contract/enforcement gaps and two medium-priority specificity gaps. All were applied to the discussion contract; this disposition does not claim that any corresponding code is fixed.

| Finding | Severity | Resolution in the adopted contract |
|---------|----------|------------------------------------|
| Calling timing advisory leaves producers/consumers stuck at `pending-investigation` | High | D-18 requires successful advisory receipts and changes to the actual producer/verifier/reuse/aggregate/attach/release path. D-22 binds explicit Ir acceptance to deterministic cause/limit/measurement, preserving other blockers. |
| Limit and golden-pin policies have no immutable-base enforcing control | High | D-02/D-18 require ratchets and failing unapproved-change controls. Digests do not claim semantic inference. Phase 19 intentionally rebaselines exact-release-token state bytes for v0.3.0. |
| Roadmap/traceability omit inherited mandatory tooling | High | Phase 17 ROADMAP criteria 6–8 and REQUIREMENTS inherited-obligation rows explicitly cover RM-026/028/029/030. The milestone window/phase set is unchanged. D-24 reserves one of 12 slots for the gap round and requires rescope if work cannot fit. |
| Header offsets/ranges/checksum and signed mapping remain unspecified | Medium | D-04 makes a precise offset/width/range table, checksum/size/reserved/version-range rules and defined signed encoding a pre-codec planning research gate. No arbitrary header growth or native signed dump. |
| Field-drop tests can be vacuous for unexercised fields | Medium | D-14 requires per-field discriminating non-default exercise or an explicit invariant treatment; targeted fixtures fill the gaps. An unexercised mutant cannot count as killed. |

The reviewer found no contradiction in the explicit stable/non-overlapping buffer precondition, time-horizon path list, host-observer semantics or discussion-only stop. Additional review would repeat these same discriminators; remaining uncertainty is intentionally assigned to narrow planning prototypes, not another broad survey. The review was terminal before parent reconciliation.

## Discussion artifact verification

One-off local checks validate the context sections/decision sequence, six native requirement rows, every inherited finding/gate, adversarial corrections, consistent discussion/planning routes, disabled advance flags, unchanged unrelated roadmap sections, preserved owner config/runtime note and absence of PLAN/checkpoint leftovers. Mutated copies of the artifacts must fail for missing sections/trace/gates/ratchets, stale routes, wrong stage or phase name, enabled advancement, omitted roadmap coverage, missing adoption and broken navigation. Every local canonical reference resolves.

The existing CTests `plan_cap`, `lessons_unique_ids`, `state_size` and `planning_hygiene_controls` pass (4/4). Runtime `state.validate --strict` reports valid with no warnings; `roadmap.validate` reports no warnings; `git diff --check` passes. Final artifact verification is repeated after the last edit and against the committed discussion revision. No full emulator regression suite, hosted campaign, release consumer or save-state implementation result is claimed by this discussion evidence.

## Agent discretion

Private helper names/layout, portable inventory implementation, original fixture organization and economical test grouping are delegated. No invented owner/manual UAT checkpoints, dependency obligation or cap waiver.

## Deferred Ideas

Player slots/runner contract (Phase 18), RM-027 final citations and qualified release (Phase 19), RM-024/025 broad optional quality/CI changes, cross-version conversion/BESS/RTC footer interop, rewind UI/libretro/live Playstead and additional hardware/perceptual claims remain deferred.
