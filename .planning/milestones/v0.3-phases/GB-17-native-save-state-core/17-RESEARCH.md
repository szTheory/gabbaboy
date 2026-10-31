# Phase 17: Native Save State Core — Research

**Researched:** 2026-10-26  
**Domain:** Portable C save-state codec, deterministic emulator continuation, release evidence tooling  
**Confidence:** MEDIUM

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

CTX_7b3e91a6_START
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
CTX_7b3e91a6_END

### Agent discretion

CTX_8f1c42d9_START
- **Agent discretion:** private helper layout, field-list spelling, portable symbol-inventory tooling, original fixture organization and economical test grouping are delegated. A licensed small copy is preferable to adding a dependency; a new dependency needs a demonstrated benefit. Research only concrete gates above and contradictions found in implementation; do not repeat the completed ecosystem survey.
CTX_8f1c42d9_END

### Deferred Ideas (OUT OF SCOPE)

CTX_a9147c2e_START
## Deferred Ideas

- Phase 18 — player slots, runner files/signals/exit codes and declared battery format ids.
- Phase 19 — final RM-027 tree-bound timeout citations, exact-tag release rehearsal and v0.3.0 publication.
- RM-024/025 remain parked: broad coverage/mutation expansion and CI scheduling changes beyond mandatory state/tooling evidence.
- Cross-version conversion, BESS, RTC footer interop, rewind/runahead UI, libretro, live Playstead qualification and new hardware/perceptual claims remain out of scope.
- A public snapshot probe, tagged extensibility framework, compression dependency and per-load scratch-buffer API have no demonstrated consumer here.
CTX_a9147c2e_END
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Requirement | Research support |
|---|---|---|
| STATE-01 | Public size/save/load API, fixed size, typed errors, no allocation or save mutation, installed C/C++ consumers. | Existing opaque instance, error enum, installed clients, and per-instance ownership contract are identified below. |
| STATE-02 | Exact continuation across seeded/in-flight states, fresh poisoned target, output comparisons and field-drop mutants. | Core field census seams and fork comparisons are mapped; local observer counters need separate comparisons. |
| STATE-03 | Transactional bounded load, hostile-field rejection, closure and hosted state-load fuzzing. | Header order, two-pass codec, canonical bounds and 2^62 horizon are specified. |
| STATE-04 | Machine-checked member inventory and writable-global check, each with a negative control. | Instance declaration and CTest/nm integration seams are identified. |
| STATE-05 | Canonical LE bytes, resave identity, Linux/macOS/Windows pins. | Header/body rules and existing platform/package lanes are mapped. |
| STATE-06 | Full RAM/RTC replacement, no wall-clock catch-up, battery generation only for changed battery bytes. | Existing lazy RTC and transactional battery patterns support projected comparison before apply. |
</phase_requirements>

## Summary

The core snapshot work belongs in the existing C instance and public API. Machine state is concentrated in struct gbb_instance and nested mapper, HDMA, APU, frame, timer, input and audio fields. Battery import already validates before applying and projects RTC through a local copy. Public run wrappers converge on gbb_run_internal, which is the main operational horizon seam. [VERIFIED: src/core/gabbaboy.c:369-503, 3903-4025, 4624-5039]

A complete 64-byte header fits full SHA-256, release/format/behavior identity, profile/mode, lengths, reserved bits and checksum. The table below is a concrete recommendation, not an already-adopted wire format. A disposable prototype with proposed 2^62 preflights passed focused instruction, HALT, STOP, IRQ, OAM DMA, HDMA, speed-switch and event timestamp cases. Its first pass exposed the existing HDMA one-tick guard as a missing seam. This proves a route is feasible, not that repository code has implemented the route. [VERIFIED: /tmp/gb17_horizon_probe.c and its command output]

The phase also has substantial release tooling work: advisory timing receipts, blocking Ir/realtime gates, generated support disclosure and version-window checks, API-shaped attach/retry rehearsal, WR-01..05 / IN-01..04, and review/nightly approval gates with 8+6 specified mutants. Existing scripts and workflows supply production-path seams; no new package is recommended.

**Primary recommendation:** Make the first executable plan include the field inventory, seeded completeness/global checks and compiled public API path. Then use a single field manifest for size/write/validate/apply and fit all required tooling within 11 primary plans plus one gap slot.

## Architectural Responsibility Map

| Capability | Primary tier | Secondary tier | Rationale |
|---|---|---|---|
| Wire codec and machine state | Portable C core | Public API/tests | Opaque instance owns state; host files and devices stay outside the core. |
| Transactional load and observer deltas | Portable C core | Test adapters | Validate all bytes before changing RAM, palette, RTC or counters. |
| Operational time horizon | Portable C core | Public run wrappers | All public run modes converge on a shared scheduler. |
| Golden pins, closure and fuzz | CTest / CI | Release evidence | Existing native, package, sanitizer and fuzz lanes are the validation surfaces. |
| Release evidence | Scripts/workflows | CTest | Production attach, manifest, retry and publish decision must run the same checkers. |

## Project Constraints (from AGENTS.md)

- Target Game Boy and Game Boy Color; background NES/Neo Geo examples are not requirements.
- Preserve the phase stop and auto-advance flags false; this assignment ends after Phase 17 research.
- Every deliverable has an automated check and a negative control. No quotas, clocks, run counts or kill rates as evidence.
- Maximum 12 plans: 11 primary plus one gap round. Rescope if mandatory work cannot fit.
- Keep the core portable, explicit about ownership/errors, bounded, and free of host filesystem/clock/device dependencies.
- Never serialize C structs, padding, native widths or native endianness. Protect against overflow, excess allocation/work and partial mutation.
- Document evidence classes and fixture rights. Do not add prohibited ROMs, unlicensed homebrew, private data, telemetry, personal paths or machine identifiers.
- No mandatory human UAT for deterministic checks. Handoff must state completed stage, next phase and exact GSD command.

## Standard Stack

| Component | Status | Use |
|---|---|---|
| C17 | Existing core | Public API and codec; no new language runtime. |
| CMake / CTest | Existing build | Unit/integration checks, package clients, global/inventory controls. |
| Python 3 | Existing scripts | Policy checkers, release fixture orchestration and ledger generation. |
| In-tree SHA-256 | src/accept/sha256.c | Cache complete ROM digest on successful replacement through a private seam. |

No project package is proposed. The OpenGSD runtime identity was verified as @opengsd/gsd-core 1.18.0 for workflow tooling only. No package install is needed.

## Architecture Patterns

### State flow

~~~mermaid
flowchart LR
  ROM[Successful ROM replacement] --> SHA[Cache full ROM SHA-256]
  SAVE[Save API] --> SIZE[Validate instance and exact size]
  SIZE --> WRITE[Write fixed LE header and ordered body]
  LOAD[Load API] --> HEADER[Check complete 64-byte header and identity]
  HEADER --> VALIDATE[Check checksum, fields, bounds and relationships]
  VALIDATE -->|valid| APPLY[Allocation-free apply pass]
  VALIDATE -->|refused| RETURN[Typed error; instance unchanged]
  APPLY --> OBS[Apply palette, RAM, RTC and observer deltas]
  OBS --> RUN[Shared run loop and peripherals]
~~~

### Existing source map

| Capability | Source seam | Planning direction |
|---|---|---|
| Public enum/error/API | include/gabbaboy/gabbaboy.h:11-55 | Append state errors without renumbering; update docs, error strings and installed clients. |
| Full mutable state | src/core/gabbaboy.c:50-87, 118-140, 350-362, 369-503 | Inventory every member/nested field before codec. |
| RTC/battery pattern | src/core/gabbaboy.c:3903-4025 | Reuse parse-before-apply and local projected RTC comparison. |
| Run horizon | src/core/gabbaboy.c:3264-3362, 4624-4911, 4913-5039 | Bound every advancement and event/span admission path. |
| Consumer integration | tests/consumers/c/main.c, tests/consumers/cpp/main.cpp, tests/CMakeLists.txt, tests/expected-tests.txt | Compile installed C and C++ API clients. |
| Release integration | .github/scripts/verify-release-gates.sh, tests/scripts/verify-v02-performance.py, tests/scripts/measure-release-baseline.sh, tests/scripts/verify-support-ledger.py, .github/scripts/verify-workflow-policy.py, .github/workflows/release.yml, .github/workflows/nightly-asan.yml | Keep checker self-tests tied to actual workflow commands and trusted source. |

### Recommended fixed header

All multi-byte values are little-endian. The design is a recommendation to settle in planning. Proposed values not already locked by context are marked [ASSUMED].

| Offset | Width | Field | Range / meaning |
|---:|---:|---|---|
| 0 | 4 | Magic | bytes GBBS |
| 4 | 2 | Format | u16, initial value 1, exact match |
| 6 | 2 | Header length | u16, exactly 64 |
| 8 | 2 | Release major | CMake project major, 0..65535 |
| 10 | 2 | Release minor | CMake project minor, 0..65535 |
| 12 | 2 | Release patch | CMake project patch, 0..65535 |
| 14 | 2 | Behavior revision | u16, initial value 1, exact match |
| 16 | 1 | Profile | Existing profile enum; exact destination match |
| 17 | 1 | Mode | Existing execution-mode enum; exact destination match |
| 18 | 2 | Reserved flags | Exactly zero |
| 20 | 32 | ROM identity | Full SHA-256, all loaded ROM bytes |
| 52 | 4 | Body length | u32, 0..524288 |
| 56 | 4 | Total length | u32, exactly 64 + body; maximum 524352 |
| 60 | 4 | Checksum | Recommended CRC-32/ISO-HDLC over bytes 0..59 then body; checksum bytes excluded |

The present release source is CMake VERSION 0.2.1. [VERIFIED: CMakeLists.txt:1-2]

SRC_6a31c90d_START
~~~cmake
project(GabbaBoy VERSION 0.2.1 LANGUAGES C) # x-release-please-version
~~~
SRC_6a31c90d_END

Check each release component against UINT16_MAX at configure time and compile time. Never truncate. After checking body <= 524288, checked-compute 64 + body and compare with header total, supplied size and instance-derived expected size. CRC is corruption detection only, not authentication. Pin algorithm initialization/finalization and a standard known vector. Body cap, initial token values and CRC flavor are proposals [ASSUMED].

Header enum source values are quoted verbatim:

SRC_f01d88bc_START
~~~c
typedef enum {
    GBB_PROFILE_DMG_CPU_B = 1,
    GBB_PROFILE_CGB_CPU_E = 2
} gbb_profile;

typedef enum {
    GBB_MODE_NONE = 0,
    GBB_MODE_DMG = 1,
    GBB_MODE_CGB = 2,
    GBB_MODE_CGB_DMG_COMPAT = 3
} gbb_exec_mode;
~~~
SRC_f01d88bc_END
[VERIFIED: include/gabbaboy/gabbaboy.h:13-16, 316-320]

### Ordered body and field inventory

Use one source-local field manifest for size, write, validate, apply and test recording. Avoid tags/sections and a generic schema library. Recommended order:

1. Cartridge RAM bytes, exact size derived from loaded ROM.
2. Mutable mapper latches, current rumble line, full RTC live/latched fields and emulated-time anchor.
3. WRAM, HRAM, VRAM, OAM, CGB CRAM, bank/register state.
4. Both shade frame buffers, both RGB555 frame buffers, all 12 compatibility-palette entries and frame metadata.
5. OAM DMA and full HDMA transfer/register state.
6. CPU, interrupt, timer, divider, serial, HALT/STOP/lockup and master time.
7. Input queue count and all fixed slots; unused slots canonical zero.
8. APU channel/register/sequencer state, sample phase, signed event ring, mix and high-pass history.

Serialize both mode-specific frame buffer pairs unless inventory proves an omission safe. Core comments indicate an inactive pair is zero in some modes, but D-06 requires proof of reset and observability before omission. [VERIFIED: src/core/gabbaboy.c:395-405, 3071-3080, 3105-3111]

Exclude ROM bytes, pointers, allocation sizes, borrowed span/test/diagnostic/output buffers, diagnostic counters, audio run plumbing, and test-only APU behavior overrides. Header binds the ROM/profile/mode. Keep battery_generation and rumble_changes local. Include rumble_on, queued accepted events, and frame_generation. Every excluded member needs a reason in the inventory. [VERIFIED: src/core/gabbaboy.c:369-503]

Canonical bounds to encode in the manifest:

- Booleans must be exactly 0 or 1; reject instead of normalize.
- time_half_dots <= 2^62. timer_reloaded_at is UINT64_MAX sentinel or <= time. frame_completion_half_dots and rtc_synced_at <= time.
- Input count <= fixed capacity 64; active events valid, ordered and >= saved time; each timestamp <= 2^62; all unused slots zero. [VERIFIED: src/core/gabbaboy.c:28, 3365-3384; include/gabbaboy/gabbaboy.h:231-246]
- Shade pixels in [0,3]; RGB555 values have bit 15 clear. Palette setter validates all 12 before mutation and rejects bit 15. [VERIFIED: src/core/gabbaboy.c:3506-3516, 3543-3573; include/gabbaboy/gabbaboy.h:400-410]
- MBC2 battery RAM is 512 canonical bytes 0xF0 | nibble. Reject state bytes with a noncanonical upper nibble, even though battery import normalizes. [VERIFIED: include/gabbaboy/gabbaboy.h:178-183; src/core/gabbaboy.c:3992-4001]
- RTC subsecond < 2^23, seconds/minutes <= 0x3f, hours <= 0x1f, DH reserved bits zero, latch edge boolean; mirror existing parser bounds. [VERIFIED: src/core/gabbaboy.c:3903-3942]
- Bound PPU FIFO/cursors, OAM/HDMA phase/index/cursors, mapper banks/masks, CPU flags/delays and APU phase/timers from the functions that consume them, not just C storage width. [VERIFIED: src/core/gabbaboy.c:350-362, 1809-1965, 3060-3135, 3177-3190]
- apu_sample_phase < audio clock period; audio_event_head < tap count; audio_mix_level matches recomputation; HPF input/output are saturated s16 values. Arbitrary audio_event_ring int64 values are unsafe because sample mixing adds then rounds/negates them. Derive a conservative accepted bound from valid APU register/timer limits and the 16-tap ring lifetime. [VERIFIED: src/core/gabbaboy.c:518-557, 577-610, 3340-3353]

Signed int64 encoding recommendation: encode x as its modulo-2^64 unsigned residue; decode using safe branches. Avoid out-of-range unsigned-to-signed casts: WG14 specifies such signed conversions as implementation-defined or signal-raising. [CITED: https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf]

~~~c
static int64_t decode_i64(uint64_t u) {
    if (u <= (uint64_t)INT64_MAX) return (int64_t)u;
    return -1 - (int64_t)(UINT64_MAX - u);
}
~~~

The proposed provisional audio-ring bound ±2^50 is only a hypothesis. Plan must prove the maximum edge count and resulting arithmetic margin or choose a stricter bound; do not accept arbitrary int64 values. [ASSUMED]

### Allocation-free transaction pattern

- Validate nulls/loaded identity, complete header and exact lengths before body reads.
- Check checksum, canonical field ranges and all cross-field rules in a cursor-only first pass; no allocation, ROM hash, output mutation or instance writes.
- Apply the same manifest only after all validation succeeds. The apply pass must have no failure path.
- Compare projected pre-load destination and incoming saved RAM+RTC battery bytes before mutation. After successful apply, bump receiving battery_generation exactly once iff projected bytes differ, with saturation. Leave it untouched if unchanged.
- Keep rumble_changes local; update once iff rumble_on changes, with saturation. Compare output level and counter delta separately.
- Restore full raw RTC including anchor and subsecond data; never read wall clock or call catch-up. Host order remains ROM -> optional battery import/catch-up -> state load. Existing RTC projection uses a local copy; use it to avoid false battery changes when raw lazy-clock representations project to equal bytes. [VERIFIED: src/core/gabbaboy.c:285-305, 3960-4025]
- Successful load replaces compatibility palette even into a target with a different palette. Refused loads retain all instance memory and palette. [VERIFIED: src/core/gabbaboy.c:3557-3573]
- Buffer must remain stable and not overlap instance storage. Save must check state and capacity before first write; on error output is unchanged; on success write exact total and preserve tail. Load refusal preserves complete instance and owned RAM.

## Operational Horizon: feasibility and remaining proof

Current source guards against UINT64_MAX overflow, not the adopted 2^62 horizon. Distinct run paths are STOP elapsed wait, CPU stall, per-tick HDMA, IRQ, HALT, speed-switch reservation and instruction preflight. Public run/run_ex/audio wrappers share gbb_run_internal; ordinary event queue and borrowed acceptance span have separate admission checks. [VERIFIED: src/core/gabbaboy.c:4624-4860, 4913-5039, 3365-3384, 3397-3427]

A disposable /tmp copy inserted a common safe-add predicate, run-entry cap rejection and ordinary event bound, then compiled and passed instruction, HALT, STOP, IRQ, OAM DMA, HDMA, speed-switch stall/whole-switch reservation and event timestamp cases. It exercised cap-1, cap and cap+1. The first probe exposed the existing HDMA 1-tick UINT64_MAX-only guard as a missing seam; after substituting that guard, the focused probe passed. [VERIFIED: /tmp/gb17_horizon_probe.c and command output]

This is feasibility only. Permanent proof must also cover gbb_run_ex and gbb_run_audio via shared loop; acceptance diagnostic/audio wrappers plus span validation; event cap-1/cap/cap+1; and each independent STOP, stall, HDMA, IRQ, HALT, instruction/speed-switch and event missing-guard mutant. Run-boundary inputs must never overflow now+amount; test exact cap sentinel handling. No current project source was changed.

## Inherited release tooling and source seams

- RM-026/029: producer is tests/scripts/measure-release-baseline.sh; receipt verification/reuse/review decision is tests/scripts/verify-v02-performance.py; blocking Ir/realtime gate is tests/scripts/verify-perf-gate.py and run-perf-gate.sh; release calls are in .github/workflows/release.yml. Triggered valid advisory timing must produce a successful bound receipt throughout producer, verifier, reuse, rehearsal, attach and release consumers. Keep adopted 1.10 Ir and 4.02 realtime floor blocking; reject unapproved immutable-base limit widening. [VERIFIED: tests/scripts/measure-release-baseline.sh:700-779, tests/scripts/verify-v02-performance.py:1206-1259, .github/workflows/release.yml:1178-1189]
- RM-028: tests/scripts/verify-support-ledger.py --write-current is the generator seam; preserve prior tagged bytes. Generate the historical perf disclosure from managed input and protect the short version-PR freeze/revalidation window. [VERIFIED: tests/scripts/verify-support-ledger.py:2610-2704]
- API-shaped rehearsal must traverse existing release gate/attach/manifest/retry/publish paths using sanitized captured data and bounded local GH/gh stubs. Include non-git workspace, check-run url/html_url/check_suite shape without invented repository field, and identical attached-byte retry plus tamper/stale/duplicate/partial controls. .github/scripts/verify-release-source-proof.py contains fixture shape precedent; workflow call sites in .github/workflows/release.yml. No live publish is required. [VERIFIED: .github/scripts/verify-release-gates.sh:6-16, 181-259; .github/scripts/verify-release-source-proof.py:90-95; .github/workflows/release.yml:1504-1529][CITED: https://docs.github.com/en/rest/actions/workflow-runs?apiVersion=2026-03-10, https://docs.github.com/en/rest/checks/runs]
- WR-01..05: bind artifact to workflow/run/event/success/source SHA or verified equal tree; historical Phase 8 ref to recorded SHA; reject duplicate/malformed SHA256SUMS names; immutable-base test budget row bound including reused refs; count suffixed plans and enforce per-phase/four-phase caps.
- IN-01..04: retry tamper check remains independent and correctly ordered; exact required GitHub App identity at PR/release; bounded report-red timeout with real ledger evidence and exact title/label deduplication; digest and consumption for both performance repeats plus skipped-HDMA rejection.
- --review-approval requires OWNER association, exact issue URL, comment newer than issue, full digest approval wording, and owner fields unset until verification. Its 8 negatives: non-owner, wrong issue, wrong digest, missing approval text, prefix-only digest, unrecorded issue, comment predates issue, owner fields prefilled.
- --nightly-gate rejects failure/non-success, wrong head, skipped replay, in-progress run, no run at head, and older green behind newer red; includes timestamps and immutable boundary re-check. Wire both into CTest and actual release path, with all 8+6 mutants independent.
- RM-027 six release_bound timeout rows remain Phase 19 entry blocker; do not close here. RM-024/025 remain parked. [VERIFIED: .planning/REQUIREMENTS.md inherited obligations; .planning/context/FUTURE-MILESTONES.md]

## Feasible Decomposition

Cohesive grouping fits 11 primary plans plus the one reserved gap slot; this is feasibility, not a quota.

| # | Slice | Main automated discriminator |
|---:|---|---|
| 1 | Pre-codec field inventory/global check plus appended API/errors and compiled installed C/C++ path. | Unclassified-member/writable-global negatives; real linked calls. |
| 2 | Cached ROM SHA, exact header/body manifest, size/save writer. | Known SHA, same-title/body identity control, header/token and tail controls. |
| 3 | Two-pass transactional load, bounds, RTC/palette/counter application. | Refusal precedence, CRC-recomputed hostile fields, byte-identical refusal, allocation control. |
| 4 | All-path horizon and input/span admission. | Cap matrix and independent guard mutants. |
| 5 | Seeded fork census and field-drop mutants. | In-flight coverage gate and frame/PCM/run/battery/rumble/final bytes. |
| 6 | Cross-platform pins and semantic state fuzz/closure. | Linux/macOS/Windows digest equality, altered-pin negative, hosted fuzz target. |
| 7 | Advisory paired timing receipts through consumers; preserve Ir/realtime blockers and immutable ratchet. | Valid triggered advisory plus malformed/unbound and widened-limit negatives. |
| 8 | Historical disclosure generator and version-window freeze/revalidation policy. | Regeneration and tamper/omission controls, historic bytes preserved. |
| 9 | Production-path API-shaped attach/manifest/final-gate/retry rehearsal. | Non-git fixture and tamper/stale/duplicate/partial/retry controls. |
| 10 | WR-01..05 and IN-01..04 fixes through workflow-policy and release call sites. | Each finding has intended positive and negative control. |
| 11 | Review approval/nightly gate, 8+6 mutants, CTest and actual workflow wiring. | Each specified mutant independently rejects; immutable boundary controls. |
| 12 reserved | Single gap round if evidence finds a real gap. | No unresolved correctness/security item may be seeded. |

Keep plan ownership/dependencies explicit because release/tooling files overlap. Respect at most two review-fix rounds and one gap round. If the work cannot fit without weakening acceptance, rescope before implementation.

## Validation Architecture

| Requirement | Automated validation | Negative control |
|---|---|---|
| STATE-01 | API size/save purity, no-allocation instrumentation and installed C/C++ consumers. | Null/short buffer, partial output, tail overwrite, allocator and missing-consumer mutants. |
| STATE-02 | Seeded fresh-instance forks for all required in-flight categories; compare frame, PCM, run result, battery bytes, rumble level and final state. | Missing category and each field-drop mutant. |
| STATE-03 | Refusal precedence, hostile bounds with recomputed CRC, whole-instance equality, accepted-state closure and fuzz. | Bad size/token/identity/checksum/reserved/range/cross-field plus apply-before-validation mutant. |
| STATE-04 | Struct inventory parser and nm writable-global check in CTest. | New unclassified member and injected writable global. |
| STATE-05 | LE round-trip and immutable-base pin ratchet across native platform jobs. | Changed pin without compatibility disposition/token. |
| STATE-06 | RAM/full RTC replacement, no catchup, projected-battery counter semantics. | Equal projected bytes causing bump; actual changed bytes missing exactly one bump. |
| RM-026/029 | Valid triggered-advisory receipt through actual producer/consumer path; deterministic Ir and realtime floors. | Unbound receipt, missing repeat digest/consumption, unauthorized Ir widening. |
| RM-028/030 | Generated disclosure, window check, release replay, WR/IN, approval/nightly gates. | Required WR/IN, 8 review and 6 nightly mutants. |

Existing lane seams include tests/CMakeLists.txt, tests/expected-tests.txt, tests/fuzz_core.c, tests/test_battery.c, tests/test_rtc_battery.c, tests/test_mbc3_rtc_internal.c, consumers C/C++, .github/workflows/ci.yml and nightly-asan.yml. Reuse CTest/sanitizer/hosted fuzz/package lanes; do not duplicate the whole matrix. No project suite was run; only the disposable horizon prototype was compiled/run. For deterministic contracts no human UAT is required.

Suggested focused command after test names are defined: ctest --test-dir build -R '^(state_|release_gate_)' --output-on-failure --no-tests=error. Planner should replace this placeholder with actual CTest names. Validation is enabled in .planning/config.json; security enforcement is enabled.

## Security Domain

State files are untrusted input. Check bounds and exact lengths before reading; no per-load allocation; validate all enum/range/cross-field values before apply. ROM SHA-256 binds destination identity; CRC is not authentication. Exclude pointers, host paths/build metadata and wall clock.

| ASVS area | Applies | Control |
|---|---|---|
| V2 Authentication | No | No user authentication surface. |
| V3 Session | No | No network session. |
| V4 Access control | No | No new permission boundary. |
| V5 Input validation | Yes | Exact size, checked arithmetic, canonical fields, two-pass mutation, fuzz/negative controls. |
| V6 Cryptography | Narrowly | Reuse in-tree SHA-256; no new crypto package; CRC only detects corruption. |

## Assumptions Log and execution proof obligations

| # | Claim | Risk / required proof |
|---|---|---|
| A1 | Initial format and behavior tokens are 1. | Freeze with token-mismatch tests. |
| A2 | 512 KiB body cap is enough. | Prove generated field-size sum below cap; host sizeof is not the wire format. |
| A3 | CRC-32/ISO-HDLC over header bytes 0..59 and body. | Pin exact init/xorout/known vector before codec. |
| A4 | ±2^50 signed ring bound is conservative. | Derive max edge count from validated APU ranges and ring lifetime; otherwise replace. |
| A5 | Work fits 11 primary plans. | Planner must map each requirement/obligation and rescope if not. |

Open execution proof obligations:

1. Extend temporary horizon evidence to public diagnostic/audio and borrowed event-span paths, including cap-admission tests; the current probe exercised gbb_run and focused route branches only.
2. Prove accepted-space audio ring arithmetic bounds and all remaining field-specific ranges from consuming code.
3. Add compile-time/CTest checker for exact field inventory, descriptor size <= chosen cap, global scan, each with a seeded negative.
4. Keep checksum/token/cap recommendation explicit until selected in planning.

## Environment Availability

| Dependency | Available | Version |
|---|---:|---|
| C compiler | Yes | Apple clang 21.0.0 |
| CMake | Yes | 4.4.3 |
| Python | Yes | 3.14.4 |
| GitHub CLI | Yes | 2.101.0 |

No package install or live publish credential is required for the bounded API-shaped replay.

## Sources

### Project sources
- AGENTS.md; .planning/STATE.md; .planning/PROJECT.md; .planning/research/SUMMARY.md
- .planning/REQUIREMENTS.md; .planning/ROADMAP.md; phase 17 CONTEXT and DISCUSSION-LOG
- .planning/context/DECISIONS.md D-112/D-113; .planning/context/FUTURE-MILESTONES.md
- .planning/research/v0.3/SUMMARY.md and SAVE-STATES.md (older CRC-only identity/palette exclusion/section framing superseded)
- Phase 16 REVIEW-DISPOSITION.md, 16-07-PLAN.md and SECURITY.md
- Current core, public header, CMake/CTest, release scripts and workflows cited above

### Official external docs
- WG14 N1570 §6.3.1.3: https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf
- GitHub workflow runs: https://docs.github.com/en/rest/actions/workflow-runs?apiVersion=2026-03-10
- GitHub check runs: https://docs.github.com/en/rest/checks/runs
- GitHub artifacts: https://docs.github.com/en/rest/actions/artifacts
- GitHub releases/assets: https://docs.github.com/en/rest/releases/releases and https://docs.github.com/en/rest/releases/assets?apiVersion=2026-03-10

**Confidence by area:** core/source seams HIGH; header recommendation MEDIUM; horizon route MEDIUM; audio bound LOW until proof.  
**Research date:** 2026-10-26  
**Valid until:** 2026-11-25 unless core, release tooling or phase requirements change.

