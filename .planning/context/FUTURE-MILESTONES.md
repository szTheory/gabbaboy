# Rolling product roadmap

Reviewed: 2026-11-14 · Direction revision: 8 · Last completed milestone: **v0.3 Save States & Host Contract** (Phases 16–19); v0.4 release is qualified; milestone audit remains owner-controlled.

This is revisable direction, not authorization to advance. [ROADMAP.md](../ROADMAP.md) is the execution contract and has detailed phases for the active milestone only. Planning milestone numbers are not package versions. The kickoff evidence is [research/v0.3/SUMMARY.md](../research/v0.3/SUMMARY.md); the boundary refresh is [MILESTONE-BOUNDARY-LESSONS.md](../research/v0.3/MILESTONE-BOUNDARY-LESSONS.md). v0.3.0 is published and v0.3 archived with owner-approved overrides and nonblocking deferrals. v0.4 Evidence Floor has delivered its scoped qualified release and explicit no-go evidence; its milestone audit is next, and no subsequent phase or milestone is authorized.


## Phase 23 — qualified v0.4.0 direction boundary

The observed v0.4.0 outcome is the qualified publication at permanent source 3de1b0e427f37a202be4469dd818266f359c8b20, judged by actual trusted control fbea1e2cc70f7c2ab9ea5820fa92ca18ddf997e8 and successful publisher 43526085579 attempt 1. [23-EVIDENCE.md](../phases/GB-23-qualified-v0-4-0-release/23-EVIDENCE.md) records fresh public 22 readback, unchanged original 20 tuples/notes, exact source/receipt checks and actual consumers. This is delivered software evidence, not a milestone audit or new scheduling authority. The next owner-controlled command is /gsd-audit-milestone.

FIXT-01, RIGHTS-01, DIAG-01 and DIAG-02 remain Pending. Potion Panic and µCity retain their exact source/component-rights no-go reasons; no license prohibition is inferred. Diagnostics remain 513 named cases, seven unresolved gates, zero newly admitted/executed real fixtures. RM-005's admitted-oracle prerequisite is still unmet: publication alone does not qualify PPU timing. Hardware, perception, general games, Linux player, Steam Deck and live Playstead remain unqualified; unsigned/not-notarized status and existing software-model scope stay explicit.

The source-bound six-core/Playstead XFER scan in [LESSONS.md](LESSONS.md) corroborates current artifact/source/attempt and draft-ID safety. Playstead's separate archive/executable hashes and app-level wiring tests are a conditional future RM-020 input, not proof of GabbaBoy integration; RM-020 stays parked. No source was copied and no sibling test was run.

Measured G5 Windows CTest 66.20 minutes and product-S corpus 42.65 minutes identify remaining critical waits. The already-qualified deterministic reductions remove duplicate version-window positives and irrelevant routing-baseline scans while preserving assertions and limits. Current CI pushes only main, so the old all-branch-push description in RM-025 is historical evidence, not a remedy to repeat. RM-025 remains parked with its existing trigger/disposition, and RM-032 remains proposed/opt-in; neither is reopened or promoted here. Batch restoration of known immutable refs and platform-appropriate public-byte checks are now recorded as a local readback/process lesson. No new cache, concurrency, dependency, publisher, phase or milestone is introduced.

## Horizons and planning depth

| Horizon | Planning depth | Milestones |
|---|---|---|
| Immediate | Qualified v0.4.0 and Phase 23 closure; owner-controlled milestone audit next | delivered v0.4 scope; audit pending |
| Near | Outcome, scope direction, acceptance direction, triggers | v0.4–v0.5 |
| Mid | Outcome and promotion trigger | v0.6–v0.8 |
| Long | Outcome and the evidence that would schedule it | v1.0 and later |

**Statuses:**

| Status | Meaning |
|---|---|
| `shipped` | Released |
| `committed` | In the active ROADMAP.md |
| `delivered` | Implemented with linked evidence; not a separate milestone acceptance |
| `proposed` | Intended direction, not yet scheduled |
| `parked` | Must name a return trigger |
| `retired` | Must name a reason |

Ids `RM-NNN` are stable and never reused.

**Sizing rules (D-102):**
- At most 4 phases and about 40 plans per milestone, and at most 12 plans per phase.
- A 50% plan overrun triggers a rescope.
- At most two substantive tracks per milestone.
- Every milestone ends in a qualified release, and its first phase is a capped tune-up: CI headroom, the weakest quality dimension, doc freshness, and carry-over dispositions.

## Shipped

| ID | Milestone | Outcome |
|---|---|---|
| RM-001 | v0.1 Limited DMG Preview (2026-10-10) | Installable core, timed DMG, SDL3 player, MBC1 battery, scoped audio, `v0.1.0` |
| RM-002 | v0.2 Color & Cartridge Breadth (2026-10-24) | Libbet game-level DMG acceptance, MBC2/3/5 + RTC, CGB-CPU-E colour/double speed/HDMA, `v0.2.0` |

## Immediate

| ID | Status | Milestone | Outcome | Promotion / exit trigger |
|---|---|---|---|---|
| RM-003 | shipped | **v0.3 Save States & Host Contract** | <ul><li>Players and embedders can save and restore exact machine state.</li><li>The runner is safe for a host process: raw `.sav`, SIGTERM save-and-exit, exit codes.</li><li>The v0.2 debt is paid, and v0.2.1 ships.</li></ul> | Exit: `v0.3.0` qualified, with a fork-matrix equivalence receipt and a cumulative perf gate green |

**RM-003 delivery:** `v0.3.0` published on 2026-10-31 with 22 source-bound assets; exact state continuation, slots and the POSIX host contract are delivered. The milestone audit owns final-head qualification and records remaining nonblocking debt. This release does not qualify a live Playstead adapter.

**RM-003 detail.**
- **Sources:** research/v0.3.
- **Acceptance direction:**
  - continuation equivalence at seeded and targeted save points with a coverage gate;
  - refused loads leave the instance byte-identical;
  - real-signal SIGTERM tests on POSIX.
- **Excludes:** INT-01b (RM-020), RTC footer interop (RM-021), libretro (RM-009), BESS.
- **Would change priority:** Playstead schedules a second emulator adapter (promote RM-020), or the perf attribution shows one merge owning more than half of the regression (insert a fix).

## Near

| ID | Status | Milestone | Outcome | Promotion trigger | Alternative considered |
|---|---|---|---|---|---|
| RM-004 | delivered | **v0.4 Evidence Floor — scoped outcome, audit pending** | <ul><li>CGB RGB555 progress/scene contracts delivered.</li><li>Both named game candidates have source/rights no-go records.</li><li>Diagnostics remain metadata-only: seven unresolved gates, zero new real admissions/executions.</li><li>Qualified v0.4.0 exposes these limits; four fixture/rights/diagnostic requirements remain Pending.</li></ul> | Owner-controlled milestone audit reconciles the approved scope; no new phase starts | PPU timing still requires admitted oracles; the unmet admission trigger is not made true by publication |
| RM-032 | proposed | v0.4 | **Release-tooling candidates deferred by Phase 19:**<ul><li>GitHub immutable releases with `gh release verify` (enable only before a window opens).</li><li>An optional ruleset protecting `v*` tags.</li><li>SLSA build provenance (needs a new action; weigh it against copy-over-dependency).</li><li>Rename the `v02-*` evidence names to version-agnostic names (D-16).</li><li>`bump-minor-pre-major` in release-please-config.json (D-03).</li><li>Move the paired-timing baseline off v0.1.0.</li></ul> | v0.4 kickoff, before its release window | Doing them in v0.3.0 was rejected: each is an unrehearsed change to the publish path or to the evidence names (19-CONTEXT Deferred Ideas) |
| RM-005 | proposed | **v0.5 DMG PPU Timing** | DMG raster effects render correctly within a declared corpus: pixel FIFO and fetcher, mode-3 length, Mealybug DMG, Mooneye `ppu/` | RM-004 oracles admitted. Perf stays within the RM-003 budget | Landing behind a profile flag, with the old renderer kept as a reference, is the fallback if over budget |
| RM-009 | proposed | **Near-term libretro core candidate; milestone slot undecided** | A libretro adapter with globals confined to the adapter and states via STATE-01, followed by a real Steam Deck/RetroArch path check | The owner has concrete Steam Deck interest. Keep it out of v0.4; if the owner later schedules it earlier, explicitly trade away acid2/gbmicrotest admission and delay PPU-timing readiness. The v0.4 default is optional direct SSH/native exploration with no support claim | A desktop build or another emulator on the Deck does not qualify GabbaBoy there |

**RM-004 detail.**
- **Candidate games:**
  - [Potion Panic (GB Compo 2025 demo)](https://github.com/gbcompo25/potion-panic) first, only if the exact source/build/ROM and all notices are verified and the creator's [CC BY-NC-SA 4.0 asset terms](https://deved.itch.io/potion-panic) cover repository and public-CI use. The creator lists MIT code separately from those assets.
  - [µCity 1.3](https://github.com/AntonioND/ucity)'s preferred `ucity.gbc` as the sole fallback, only after pinning the exact release/source/ROM, CGB-only header, save configuration, GPLv3+ code and per-file exceptions, and CC BY-SA 4.0 media notices.
  - No third candidate; if neither passes its bounded admission gate, preserve the failure reason and report justified absence. Private observations from the owner's own collection do not become redistributable fixtures.
- **The time-box** is one bounded admission/build/predicate attempt per candidate, in that order. A failed rights or feasibility gate is not an emulation failure.
- **CGB acceptance:** extend the shared runner's existing RGB555 observation path rather than adding a second harness. Use the CGB-CPU-E software profile, verify the admitted ROM actually selects CGB mode, and require a meaningful guest-progress predicate plus no-input/wrong-input or deliberately broken-predicate controls. Frame and PCM digests are reproducibility evidence, not independent visual/audio correctness or hardware evidence.
- **Acid2:** derivatives replace glyph tiles and mask the text region. Label the substitution, retain source/build/provenance checks, and claim controlled composition only—not mode-3 timing. Admit gbmicrotest separately with its own rights and model applicability.
- **Feedback:** short scene reports guide agent-owned reproduction, classification, and minimal automated regressions with independent expectations and fault controls. Human play is optional and not a release gate. Personal ROMs, saves, and captures remain private.
- **Steam Deck:** the owner has already used SSH to transfer personal ROMs and test Nesturbator on the Deck. A direct GabbaBoy Linux/SDL attempt may be used for exploratory feedback if practical, but the current player is not a qualified Linux/Deck product path. Full libretro is deferred from v0.4 and reconsidered as RM-009.
- **Licensing:** retain GabbaBoy's root MIT license. Fixture rights stay separate and exact; no broad license rewrite or fixture relabeling.

**libfuturo coordination:** the owner reports its initial direction as a core/host specification, a small SDK, and conformance against real consumers. Treat this as architecture context only. Keep GabbaBoy independently usable; add or change an adapter only for a concrete consumer gap. Do not add a dependency, wait on libfuturo, or freeze GabbaBoy's API/state format early.

## Mid

| ID | Status | Milestone | Outcome | Promotion trigger |
|---|---|---|---|---|
| RM-006 | proposed | **v0.6 CGB Timing & Colour** | <ul><li>Expected failures cut to an owner-chosen target, each one reason-coded.</li><li>A second CGB game.</li><li>An optional user-supplied boot ROM.</li></ul> | RM-005 shipped. A CGB-D profile spike is adopted only if its delta list is small and source-backed |
| RM-007 | proposed | **v0.7 Audio Qualification** | APU edge behaviour; SameSuite APU denominators; PCM digests. No perceptual claim | RM-006 shipped. Swap with RM-006 if game evidence shows audio defects first |
| RM-008 | proposed | **v0.8 Reach (Wasm)** | An Emscripten/Wasm CI leg with a realtime receipt | RM-007 shipped |

## Long

| ID | Status | Milestone | Outcome | Evidence that would schedule it |
|---|---|---|---|---|
| RM-010 | proposed | **v1.0 Stable Embeddable Core** | <ul><li>A SemVer API/ABI freeze and a guaranteed v1 state format.</li><li>A support matrix for each model, mapper and suite.</li><li>At least two DMG and two CGB games with game-level evidence.</li><li>At least one independent embedder (Playstead, libretro or Wasm), or an owner waiver.</li><li>The perf budget met.</li></ul> | RM-004 to RM-008 shipped. This is a stability promise, not a compatibility promise |
| RM-011 | parked | SGB borders and palettes; MGB/AGB profiles | Further hardware family | Fixtures with rights, and demand |
| RM-012 | parked | Two-instance link cable | Local link play | An adopter request, plus a deterministic two-instance oracle |
| RM-013 | parked | Rewind and runahead in the player | Built on STATE-01 | A measured save/load cost within the frame budget |
| RM-014 | parked | Exotic mappers (MBC1M, MBC7, HuC1/3, camera, TAMA5) | Broader cartridges | Rights-clear fixtures plus an adopter request |
| RM-015 | parked | Further hosts (mobile, SIMD paths) | Lower cost on more hosts | Measured bottlenecks and adopter demand |

## Parked integration items

| ID | Status | Item | Return trigger |
|---|---|---|---|
| RM-020 | parked | **INT-01b:** a candidate Playstead AdapterPin plus the qualify / initial-run / continue continuation protocol over the headless runner | Playstead schedules CLNT-01 / multi-pin on its main branch. Re-read the live pin and continuation script first |
| RM-021 | parked | mGBA/VBA-M 48-byte and BGB 44-byte RTC footer import/export as a host adapter | A user or consumer asks to import saves from other emulators |
| RM-022 | parked | BESS export block (then import, as best effort only) | An interchange request. Never part of the equivalence tests |
| RM-023 | parked | **Perf recovery (D-13):**<ul><li>An empty-queue input early-out in `apply_input_events_now` (about 8% of v0.2.0, the +8.3% disclosed in the v0.2.1 notes).</li><li>The Phase 7 mixer cost (about 17% of v0.1.0, two thirds of the v0.2.0 increase is exactly 32 Ir per half-dot in `advance_devices_to`).</li></ul> | Before v0.5 PPU/FIFO work, or any milestone touching the hot path |
| RM-026 | delivered | **Make the paired wall-clock gate advisory and keep the cachegrind Ir gate blocking; bind accepted regressions to cause plus Ir band.** Hosted wall-clock readings of the same v0.2.1 code ranged from +18.29% to +45.04% (SD 1.1% to 4.6%) across runs, so the paired gate decides nothing the deterministic Ir gate does not, and it cost four owner review rounds in 16-07. | The next phase that plans release tooling (Phase 17) |
| RM-027 | delivered | **Phase 19 entry blocker (named): timeout-ledger release_bound rows expire when VERSION > 0.2.1; replace with tree-equality citations.** Rows still `release_bound`: `release.yml:attach-v02-evidence`, `release.yml:candidate-fuzz`, `release-rehearsal.yml:judge`, `:corpus`, `:performance`, `:aggregate`. Green evidence exists for the rehearsal rows (run 40257161612 at c6dc575, tree equal to the tag tree) and the release rows (run 40332345735); cite them by tree equality, not by ancestry, before the version moves. | Entry to Phase 19; it is a blocker, not a seed |
| RM-028 | delivered | **Phase 17 release-tooling items from 16-07:**<ul><li>The support-ledger generator does not render the disclosed historical performance block that `verify-v02-adoption.py --check docs` requires; `docs/support/v0.2.1.md` carries a hand-inserted copy.</li><li>The release attach, manifest and publish jobs are never exercised before a tag: three post-tag defects (#123, #124, #125) were found only by running them. Add a rehearsal that drives these jobs against a throwaway draft or fixture-shaped real data, and test gates against the real API shapes, not invented fixtures.</li><li>release-please regenerates the version PR after any main push that touches non-excluded paths, wiping window edits; consider a freeze rule or excluding more paths.</li></ul> | Phase 17 planning |
| RM-030 | delivered | **Phase 16 code review (16-REVIEW.md), deferred unfixed:**<ul><li>WR-01 (security): release.yml reuses the newest successful `rehearsal/$TAG` performance artifact without checking the run's headSha, workflow and event; bind them.</li><li>WR-02: assert `historical/phase-08-boundary` still resolves to its recorded SHA.</li><li>WR-03: reject duplicate names in `SHA256SUMS`.</li><li>WR-04: bound new test-budget allowlist rows that reuse an existing ref.</li><li>WR-05: count suffixed plan names toward the 12-plan cap and enforce the 4-phase limit.</li><li>IN-01..IN-04: retry tamper check order, app-id wildcard at PR time, `report-red` timeout and title dedupe, perf-gate second-repeat digest and HDMA skipped-lane control.</li><li>Release-gate code the 16-07 plan promised but D-112 replaced with one-time checks (16-SECURITY.md AR-16-01/02, T-16-22/T-16-25): `--review-approval` (OWNER association, exact `issue_url`, comment newer than the issue, full-digest approval text, owner fields not prefilled; 8 mutants) and `--nightly-gate` (non-success, in-progress, head-mismatched, superseded or skipped-replay runs are refused; 6 mutants; boundary timestamp re-check), wired into CTest. Must be done before the next release.</li></ul>Each fix needs a negative control. AGENTS.md: an unresolved correctness or security finding is rescoped, not seeded, so Phase 17 planning must take WR-01 in scope. | Phase 17 planning |
| RM-031 | delivered | **Player-build linkage debt (found at Phase 18 verification, 2026-10-29):** in a `GBB_BUILD_PLAYER` tree, `core_linkage_links` and `core_linkage_controls` fail. Pre-Phase-18 player targets `gabbaboy-player-mutant-rb-swap`, `-dmg-path` and `test_player_session_mutant_ignores_flag` mutate player source but carry `mutant` in their names, so `verify-core-linkage.py` expects a mutant core. `test_player_colour` and `test_player_colour_mutant_rb_swap` link `libgabbaboy_core.a` twice (`GabbaBoy::core` plus `gabbaboy_accept`). CI runs only `^player_` tests on that build, so no lane sees it. Remedy: rename the player-source variants (as 18-04 did with `-hostvariant-`), drop the duplicate core link, and run the linkage check on the player build in CI or the player verify script. Each fix needs a negative control. | Before v0.3.0 tag (Phase 19 entry) |
| RM-029 | delivered | **Hosted wall-clock noise:** record the spread (+18% to +45% on the same code, SD up to 4.6%) in the next performance note and prefer cachegrind Ir deltas for any regression claim. | With RM-026 |
| RM-024 | parked | **Test-quality pass (owner request, 2026-10-25):**<ul><li>llvm-cov line and branch coverage of `src/core/` first.</li><li>Then a sampled mutation run over the core: a small copied Python mutator in `tests/scripts/` (no Mull dependency), with off-by-one comparison, constant ±1, `&&`/`\|\|`, mask and statement-deletion operators, run locally or nightly and never per PR.</li><li>Triage the top surviving mutants into focused boundary and error tests, and drop clearly redundant tests.</li><li>No kill-rate quota (D-102–D-105).</li></ul> | The next phase plan after Phase 16 has room. Time-box: one coverage plan plus one mutation plan. Phase 17 review IN-03 (IN-A03), IN-04 (IN-B01) and IN-06 (IN-B03) deferred here by Phase 19 D-10: test-quality items with no open defect. WR-C05 was already fixed in f4082a65. |
| RM-025 | parked | **CI load (Phase 16 measurement):**<ul><li>`ci.yml` runs on `push` for every branch as well as `pull_request`, so each PR update runs the full matrix twice. The push-run ASan shards took about 22 minutes against 13 on the PR run in PR #111.</li><li>The `preview-package-smoke` jobs, one of them on macOS, poll for exact-head CI and hold runners for the whole run.</li><li>Restricting `push` to main needs the per-test budget base and the D-20 ledger push-run citations re-pointed first.</li></ul> | CI wall time or runner queueing becomes the bottleneck again, or the ledger re-citations in 16-06 make the change cheap |

Phase 21 repeated this same-SHA duplication at PR #140 head `e0845db5`: push run `41554953994` and PR run `41554959166` both ran `ci.yml`, while fixture reproduction also ran for both events. Completed duplicate CI jobs took 21:13/21:49 (PR/push native Linux), 18:11/21:13 (PR/push native macOS), 20:52/33:58 (PR/push CMake 3.25.3), and 38:41/26:00 (PR/push sanitizer test shard). In PR preview run `41554959116`, the installed Linux and macOS consumers took 40:00 and 40:18, and the player package smoke took 40:34; each started with the workflow and waited for the matching required CI run before package work. This confirms runners are held across that wait. This is fresh evidence for RM-025; Phase 21 did not alter workflow triggers or reduce required coverage.

### v0.3 boundary reconciliation

The descriptions above retain the original obligations. RM-026/028/029/030 were delivered through Phase 17 and the Phase 19 trusted release/ledger checks; RM-027's six release-bound citations and RM-031's player linkage debt were closed in Phase 19. Their original entry triggers are historical, not current blockers. See [integration audit](../milestones/v0.3-INTEGRATION-AUDIT.md) and [milestone audit](../milestones/v0.3-MILESTONE-AUDIT.md). Do not reopen completed phases merely because their source fingerprints differ from a later milestone head (D-103).

RM-024 remains parked: parity/canonical-value sweep, installed-tracer hash rechecks and measured fuzz-control totals are test-quality work without an open correctness defect. Historical GR2-IN-01 is the same control-total item, not a second debt. GR-IN-03 retains the documented published-state safety branch; an optional production published-state verifier requires owner demand. Existing D-106 accepted-later limitations remain explicit in the milestone audit.

RM-025 remains a measured follow-up. The completed main run at the Phase 19 boundary spent 2,071 seconds in the sanitizer test stream, 868 seconds in native Linux CTest, and 1,388 seconds in the CMake-floor original/relocated checks. The separate Linux support-ledger self-test took 20 seconds and is repeated by CTest; at the next authorized CI change, prove equivalent environment/assertions/lane membership before consolidating it. Preserve both CMake install configurations and all sanitizer/platform coverage. No pipeline rewrite is part of this audit.

RM-032 remains a set of proposed release-tooling candidates, not automatic v0.4 scope. The owner selected the v0.4 Evidence Floor and its conditional two-candidate fixture gate; exact artifact admission remains contingent on its source, model, build, digest, and rights checks. The live Playstead process/state work reinforces the need to re-read the current pin/protocol when RM-020 is triggered; no live adapter acceptance is inferred here.

## Cross-project learning (every milestone)

At each `/gsd-new-milestone` and `/gsd-complete-milestone`:
- Scan the sibling emulator cores (glueyneo, nesturbator, genewhip, schwaystation, muhtari, cogmaster) and the Playstead consumer.
- Import the transferable lessons into [LESSONS.md](LESSONS.md) with their provenance.
- Refresh this file.
- At close, snapshot it to `milestones/vX.Y-PRODUCT-ROADMAP.md`.

Sibling observations stay evidence about other projects until a GabbaBoy check reproduces them.

## Release progression and replanning discipline

- Ship clearly named artifacts as capabilities arrive, and state the actual capability level in the release notes.
- At each phase completion, record what evidence changed the next step, the weakest quality dimension, open regressions and integration constraints. Fix consequential gaps before expanding scope, record the next-step command, and stop.
- Do not prewrite speculative implementation plans for future milestones. No calendar estimates or universal compatibility promises are attached to these horizons.

## Review log

| Date | Revision | Change | Why |
|---|---|---|---|
| 2026-10-10 | 1 | v0.1 shipped; v0.2 started; v0.2/v0.3 split | Breadth too large for one milestone |
| 2026-10-24 | 2 | v0.2 shipped and archived | Milestone close |
| 2026-10-24 | 3 | <ul><li>Restructured into horizons with RM ids.</li><li>v0.3 became Save States & Host Contract; INT-01b and RTC footer interop were parked.</li><li>Added the Evidence Floor (v0.4) before PPU timing.</li><li>Adopted sizing caps.</li></ul> | Seven-lens fan-out plus adversarial review ([research/v0.3](../research/v0.3/SUMMARY.md)) |

| 2026-10-31 | 4 | v0.3.0 published; RM-026..031 reconciled to implementation evidence; RM-024/025/032 retained; sibling/Playstead boundary scan refreshed | Milestone audit, with acceptance and the next milestone still owner-selected |
| 2026-10-31 | 6 | Reconciled v0.4 with the CGB acceptance-harness gap, conditional Potion Panic/µCity rights gate, scene-first feedback loop, direct SSH exploration, a near-term libretro candidate, retained MIT, and independent libfuturo coordination | Owner-approved recommendations and read-only technical/rights reviews |

## Deferred-item ledger (where each deferred item went)

The phase-level deferrals below are revisable direction, not authorization. Promote them into an RM row when they are scheduled.

## Deferred from Phase 8 (revisable direction, not authorization)

- **Mooneye emulator-only/mbc1 backfill:** 13 further ROMs in a sibling-manifest category `mbc1`; `multicart_rom_8Mb` is an excluded candidate (MBC1M wiring is unsupported). Reuse the Phase 8 sibling-set recipe, verifier and runner `suite_def` table.
- **`src/core/cartridge.c` split:** worthwhile only with a named reason. Six build sites must change together: `CMakeLists.txt` core source list and dirty list, the allocation probe, `fuzz_core`, `probe-mooneye-candidate.sh`, the JOYP and ninth-bit mutants (their anchors move files), and the `test_runner.c` include.
- **`read8` region-decode refactor:** only with A/B evidence (identical output digests plus a controlled timing comparison); not justified by the Phase 8 advisory timing.
- **Generalised suite verifier:** when a third Mooneye-style suite arrives, replace the adapted copy `VerifyMooneyeMbc.cmake` with one parameterised verifier.
- **Host haptics for MBC5 rumble:** map `gbb_rumble_state` samples to a host haptic API in the player; needs a real device, an intensity policy and a tested opt-out.
- **Packed 256-byte MBC2 save interop:** import/export of two-nibbles-per-byte saves from other emulators, with named fixtures and format limits.

## Deferred from Phase 9 (revisable direction, not authorization)

- **BGB/VBA-M RTC footer adapter:** import and export of the emulator-specific save footer, with named fixtures; Phase 9 defines only the GabbaBoy block.
- **Mealybug `mbc3_rtc`:** after rights gate G1 clears for that suite.
- **gbclock:** after rights gate G3.
- **CGB double-speed RTC assertion:** Phase 11, when the CGB speed switch exists.
- **Paused-time recovery:** time passing while the player is paused but open is not recovered; revisit with an explicit host policy.
- **`gbb_probe_rom` `has_rtc`:** a probe field for timer cartridges, if a consumer needs it.

## Deferred from Phase 10 (revisable direction, not authorization)

- **DMG FF4C-FF7F and `unused_hwio-GS`:** the DMG profile keeps these addresses fail-closed. Reading them as `$FF` (needed for the DMG variant of `unused_hwio`) is an owner decision that needs a hardware-backed oracle for the DMG revision.
- **CGB CPU/DMA separate-bus model:** CGB OAM DMA keeps the DMG rule (CPU sees only HRAM); recorded as `expected-failure:cgb-separate-buses`. A real model needs its own oracle.
- **DMG OAM DMA sources E0-FF and ROM sources:** unmodelled; revisit with a DMG-specific oracle.
- **RP/IR port and FF76/FF77:** the infrared port and the CGB PCM readback registers stay deferred and fail closed.
- **AGE `ly-cgbE` and `lcd-align-ly-cgbE`:** PPU-timing ROMs; revisit when CGB PPU timing exists and the fixtures' eligibility is recorded.
- **Instruction-count benchmark proxy:** a deterministic cost proxy to complement the advisory wall-clock banking benchmark, which fired its review trigger on a loaded host.
- **Flipping `boot_hwio-C` and `unused_hwio-C` to pass:** both are expected-unsupported in `fixtures/mooneye-cgb/ELIGIBILITY.md`; they stop on the unbuilt FF76/FF77 registers and are planned to flip in Phase 14.
- **Release-mode model gates:** `verify-model-gates.py --release` still fails on the open `research:11` rows by design; they resolve in the CGB rendering phase.

### Closeout revision 5 — 2026-10-31

v0.3 is archived with the owner-selected overrides and deferrals in [closeout](../milestones/v0.3-CLOSEOUT.md). The standalone closeout-scan helper still fails two self-test cases under OpenGSD 1.19.0; review its assumptions against the current scanner contract before reuse, then repair or retire it with meaningful controls. It is not a product defect and is outside CTest. RM-024/025 and optional published-state verification retain their triggers; their deferral is now owner accepted.

### Kickoff revision 6 — 2026-10-31

The owner started v0.4 Evidence Floor planning with a bounded CGB acceptance-harness repair, a two-candidate conditional rights gate, acid2/gbmicrotest admission, and scene-first agent-owned regressions. Retain root MIT, defer full libretro while promoting it to a near-term candidate, and treat direct Steam Deck/SSH use as exploratory. libfuturo remains independent coordination context. No game fixture is admitted yet; no phase execution has started.

### Roadmap approval revision 7 — 2026-10-31

The owner approved the four-phase v0.4 roadmap. RM-004 is committed in active ROADMAP.md; Phase 20 remains unplanned and unstarted. The owner chooses when to begin it with `/gsd-plan-phase 20`.
