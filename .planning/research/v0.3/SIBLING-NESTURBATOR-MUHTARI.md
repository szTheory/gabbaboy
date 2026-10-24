# Sibling lessons for GabbaBoy v0.3: nesturbator and muhtari

Researched 2026-10-24. Read-only inspection of the two sibling repositories (`.planning/`, `AGENTS.md`, git log). I also took a short read-only look at the Playstead pin, because INT-01 depends on it. Nothing was modified, built or checked out.

Evidence labels:
- **[V]** verified here (file:line or a commit sha I read or ran `git log` on).
- **[C]** a claim recorded by the sibling that I did not reproduce.
- **[I]** my inference or recommendation.

Paths are repository-relative to the sibling named.

---

## 0. Executive ranking (by impact on v0.3)

1. **Cap the process machinery before the phase starts.** Both siblings lost days when verification, admission or budget tooling became the deliverable.
   - nesturbator Phase 16 grew to 59 plans and ~185 planning commits over 10 days. It hit a "62 consecutive docs commits" loop, and STATE.md reached 178,715 bytes [V `nesturbator/.planning/forensics/report-20261022-234424.md`; `phases/16-host-evidence-and-roadmap/16-RECOVERY.md`].
   - muhtari v2.0 Phases 5–6 halted repeatedly on a line-budget gate, which was then retired [V `muhtari/.planning/research/proportional-gates/RECOMMENDATION.md`].
   - GabbaBoy 15.1 (36 plans, two gap rounds) is the same pattern.
   - Adopt muhtari's rule 7 verbatim in spirit: at most two code-review fix rounds and one gap round per phase; optional test/tooling improvements become seeds [V `muhtari/AGENTS.md:33-38`].
2. **Copy nesturbator's save-state design (v3 Phase 12) almost wholesale.** It took one phase of 10 plans, with one critical review finding (an overflow hang through a CRC-valid state) [V `nesturbator/.planning/milestones/v3-phases/12-save-states-in-the-library/12-CONTEXT.md`, `12-REVIEW.md:74-93`, fix `c6c1c69`].
3. **INT-01 should be a runner process contract plus Playstead's continuation protocol, not a new adapter framework.** The contract is: qualify / initial-run / continue; exits 0 / 77 / 1; flush on SIGTERM within the 2 s grace [V `muhtari/.planning/preparation/HOSTS-AND-INTEGRATION.md:125-172`; Playstead `playstead-mac/Playstead/Adapter/AdapterPin.json`, `playstead-mac/scripts/ci/continuation_protocol.py` exist at HEAD `c65726a6`].
4. **Decide the closeout policy up front: accept an override closeout for stale fingerprints when the milestone audit re-runs evidence on the merged head.** Do not spend sessions refreshing digests [V `muhtari/.planning/preparation/GSD-HANDOFF.md` §3 "Closeout policy"]. GabbaBoy has paid this cost in both milestones (GB-GSD-008).
5. **Adopt a `PRODUCT-ROADMAP.md` ledger with stable RM IDs, statuses and promotion triggers** (§1). GabbaBoy's `FUTURE-MILESTONES.md` has horizons but no IDs, statuses, review log or archive snapshot.
6. **Write requirements as the command or test that proves them.** muhtari v1.0 did this and shipped four phases in six days; its outcome-phrased v2.0 tune-up then ballooned. This is correlation, not proof [V `muhtari/.planning/milestones/v1.0-REQUIREMENTS.md:26-42` vs `muhtari/.planning/REQUIREMENTS.md:10-13`; I].

---

## 1. Rolling product roadmap with horizons

### What they do [V]

**nesturbator `.planning/PRODUCT-ROADMAP.md`** (123 lines) is the mature form:
- **Header:** `Reviewed: <date> at <boundary>; scope approved by the user.` / `Direction revision: N.` / `Active milestone: …` (lines 3-5).
- **Separation statement:** ROADMAP.md is the execution contract. Planning milestones are not package versions. No dates or future phase numbers are promised (line 7).
- **Horizons table** with planning depth per horizon (lines 11-16):
  - Immediate = requirements, executable phases and automated acceptance.
  - Near = bounded outcome, evidence, prerequisites and promotion trigger, plus one named alternative.
  - Mid = why, dependencies, decision trigger and acceptance direction.
  - Long = value, feasibility questions and conditions for scoping.
- **Status vocabulary** (line 18):
  - The statuses are `committed`, `proposed`, `shipped`, `parked` and `retired`.
  - Only `committed` is in scope.
  - `parked` needs a return trigger; `retired` needs a reason; `shipped` needs milestone, release and acceptance evidence.
  - **Stable RM IDs are never recycled.**
- **Per-horizon tables:** `| ID | Status | Outcome | Execution links / Why and promotion trigger |`.
- **Per-item detail blocks** for Immediate/Near (`### RM-001 …`), with the fields Sources, Acceptance direction, Current observation, "Would change priority if", and Excludes / Discovery gate (lines 40-63).
- **"Recurring policy and historical seed disposition"** table, mapping each seed to where it was delivered, so dormant seeds cannot re-scope shipped work (lines 91-105).
- **Refresh procedure:** run at every new-milestone and complete-milestone step, inside that step, with no extra command (lines 107-113). "Keep the file small … no roadmap service or parser dependency."
- **Review log:** dated bullets (line 115).
- **Archive:** a snapshot is kept at close as `milestones/v3-PRODUCT-ROADMAP.md`.

**muhtari `.planning/PRODUCT-ROADMAP.md`** (68 lines) is the lean form:
- YAML front matter (`title`, `summary`, `read_when`, `updated`). `read_when: "At every new-milestone and complete-milestone step, and when a finding changes priorities."`
- One section per horizon, each naming its milestone, its seed and a **Trigger:** plus a **Why next:** line.
- A **Refresh rule** paragraph: reconcile shipped and partial work, keep debt visible, re-rank, record why the order changed or stayed, present the preferred next scope with alternatives, and promote only owner-approved scope. The file is snapshotted at close. "Future horizons stay less detailed than the current one."
- An explicit **disposition of the weighed-but-deferred alternative** at each boundary ("Browser disposition: considered at this boundary and deferred by owner choice on 2026-10-21").
- A **Decision log** table: `| Date | Change | Why |`.
- The archive snapshot `milestones/v1.0-PRODUCT-ROADMAP.md` differs from the live file only in the Immediate/Near promotion. I diffed them.

### Recommended structure for GabbaBoy [I]

Create `.planning/PRODUCT-ROADMAP.md`. Either supersede `context/FUTURE-MILESTONES.md`, or reduce it to a pointer so the two cannot drift. Use nesturbator's fields at muhtari's length:

```
---
title: Product roadmap (rolling)
read_when: every new-milestone and complete-milestone step; when evidence changes priority
updated: YYYY-MM-DD
---
# Product roadmap: GabbaBoy
Reviewed: <date> at <boundary>; scope approved by owner. Direction revision: N. Active milestone: v0.3 …
(ROADMAP.md = execution contract; milestones ≠ package versions; no dates or future phase numbers.)

## Horizons and commitment   (table: Immediate / Near / Mid / Long → planning depth)
Statuses: committed | proposed | shipped | parked (return trigger) | retired (reason). RM IDs never recycled.

## Immediate — v0.3 States & Integration (committed)
| ID | Status | Outcome | Execution links (REQ IDs, phases) |
### RM-00x: <outcome>   Sources · Acceptance direction · Current observation · Excludes · Would change priority if

## Near   | ID | Status | Outcome | Why and promotion trigger |   (+ named alternative and its disposition)
## Mid    | ID | Status | Outcome | Promotion trigger and evidence |
## Long   | ID | Status | Direction | What must be established before promotion |
## Recurring policy and deferred-item disposition   (Phase 8/9 "deferred" bullets → RM IDs or parked)
## Refresh procedure   (inside new-/complete-milestone; snapshot to milestones/vX.Y-PRODUCT-ROADMAP.md)
## Review log   | Date | Change | Why |
```

Suggested seed rows from GabbaBoy's current FUTURE-MILESTONES content:
- RM-001 states (STATE-01), committed.
- RM-002 Playstead (INT-01), committed.
- RM-003 interop/BESS/save import, proposed, Near.
- RM-004 developer tools/traces, proposed.
- RM-005 further silicon models/SGB/link, Long.
- RM-006 performance/hosts (Wasm, rewind/run-ahead budget), evidence driven.
- RM-007 libretro adapter: parked under D-005, with the return trigger "a consumer needs it".

The "Deferred from Phase 8/9" bullets become parked rows with triggers.

### Did muhtari import a template from its siblings? Yes [V]

muhtari's `LESSONS.md:39-75` lists **33 imported lessons (XFER-001…033)** with source sha/file and local disposition. They came from nesturbator, GabbaBoy, glueyneo, playstead, lattice_stripe and exifcleaner. Its preparation tree (`.planning/preparation/{ARCHITECTURE,CONFORMANCE,DECISIONS,ENGINEERING,GSD-HANDOFF,…}.md`) mirrors nesturbator's preparation files one for one.

The speed came from:
- **XFER-001:** pre-write every artifact GSD would ask for and dry-run the roadmapper on a copy, so the kickoff resumes at roadmap creation (nesturbator `8ae2c6e`, `5e681c8`, both verified to exist, dated 2026-10-02).
- **XFER-002:** Phase 1 is a ROM-free walking skeleton that ships the whole release pipeline.
- **XFER-003:** requirements written as commands.
- **XFER-005:** whole CPU against exhaustive vectors before any game.
- **XFER-006 and XFER-007:** proportional governance; review warnings must not grow into requirements.
- **XFER-010:** decide the closeout policy up front.
- **XFER-012:** timeouts at twice a measured run, citing the run ID.
- **XFER-016:** one integrated playability session.
- **MU-GSD-003:** do not run `/gsd-verify-work` after a passing execute; execute already runs the verifier. Use it only for `human_needed`.
- **MU-GSD-007:** two green roadmap dry runs.

Results [V `muhtari/.planning/MILESTONES.md`]:
- v1.0 ran 2026-10-15 → 2026-10-21: four phases, 73 plans, zero inserted gap phases.
- It closed with an **owner-approved override_closeout**: four stale fingerprints and 15 acknowledged deferrals.
- Plans per phase were 21/16/19/17, so plan count was not small. Velocity came from no gap phases, no re-audit loop and a pre-decided closeout policy.

The caveat [V]: muhtari v2.0 Phase 5 (tune-up, 15 plans, several halted slots) and Phase 6 (halted on a 192-line gate allowance versus a 654-line construction) show that the import did not prevent a later balloon. The balloon came from a gate muhtari built for itself [`muhtari/.planning/ROADMAP.md` Phase 5 notes; `research/proportional-gates/RECOMMENDATION.md`].

---

## 2. Process and velocity

| Milestone | Phases | Plans | Days | Gap phases | Closeout | Evidence |
|---|---|---|---|---|---|---|
| nesturbator v1 | 6 (2 inserted) | 44 | ~7 | 4.1, 4.2 (1 plan each) | override | [V RETROSPECTIVE.md:5-42] |
| nesturbator v2 | 6 | 41 | 2 | none (audit → quick tasks) | override | [V RETROSPECTIVE.md:46-85] |
| nesturbator v3 (states) | 5 | 38 | 3 | none | override, tech_debt | [V RETROSPECTIVE.md:89-128; v3-MILESTONE-AUDIT.md] |
| nesturbator v4 Phase 16 | 1 | **59** | ~10 | recovery contract | — | [V phases/16-*, forensics] |
| muhtari v1.0 | 4 | 73 | 6 | none | override (owner approved) | [V MILESTONES.md] |
| GabbaBoy v0.2 (for comparison) | 10 | 170 | 15 | 15.1 (36 plans, 2 rounds) | override | [V gabbaboy RETROSPECTIVE.md:48-90] |

### What kept phases small [V]

- **Inserted one-plan decimal gap phases**, each closing exactly one requirement gap (nesturbator 4.1, 4.2; `milestones/v3-ROADMAP.md:18-19`).
- **Audit leftovers became quick tasks, not a gap phase** (nesturbator v2, RETROSPECTIVE.md:62).
- **The seam-first plan kept every old hash unchanged.** The later re-pin then had a clean baseline (v2 Phase 6, two plans).
- **Order boards from cheapest to hardest** (v2).
- **Stage claims behind green evidence.** Commit `serialized` first and `deterministic` last, with a configure-time guard (v3 Phase 13 D-18..D-21).
- **Readiness work goes in a small preceding tune-up phase** (v3 Phase 11, four plans): the atomic writer, the `battery_save` rename, and checks that frame-boundary output pointers are NULL and the PCM ring is empty. "State work inherits no v2 debt" (`v3-ROADMAP.md:47-70`).
- **One step per session; execute runs the whole phase in one command,** not one invocation per wave (muhtari RETROSPECTIVE.md:41).

### What ballooned, and why [V]

- **nesturbator Phase 16** ("Discriminating existing RetroArch progression/state evidence"). The scope came from v3 Phase 13 review warnings WR-01..03 about *test code* (`v3-MILESTONE-AUDIT.md` tech_debt), promoted into requirements EVID-01..04.
  - The forensics say each tool or bookkeeping failure "became terminal authority requiring another plan".
  - Each plan inherited all earlier controls: A/B receipts, prewrite snapshots, twelve-row admission, boot-epoch checks.
  - The phase directory reached 6 MB.
  - Recovery retired all of it. The rules were: bind acceptance to product behaviour and the actual tested source; no retry-to-green; keep STATE/ROADMAP short (STATE went from 178,715 B to 4,271 B); escalate repeated administrative failures into simplification, never into a successor plan (forensics "Lessons and correction" 1-7).
- **muhtari Phase 6** had a physical-line ratchet on gate code (192-line allowance, 654-line construction). 91 of those lines were "admission and controls" that existed only to satisfy the counter. It was retired in favour of contract checks plus a bounded architecture review (ENGINEERING §11).
- **nesturbator v3 Phase 12/13.** The fork and rejection matrices were split across waves for size (10 and 8 plans). This is acceptable, but sequential waves on shared files cost wall time (muhtari RETROSPECTIVE.md:26-27, "17 sound waves sequential").
- **Guessed CI timeouts** cancelled healthy macOS Intel jobs on every Phase 13 head. The fix was twice a measured run with its run ID, plus the lint `hygiene.timeout_comments` (RETROSPECTIVE.md:108, 116).

### GabbaBoy-specific signals [V/I]

- GabbaBoy `.planning/STATE.md` is **77,351 bytes** [V `wc -c`]. That is already about 40% of nesturbator's loop-time STATE. Trim it to the current position plus pointers before v0.3, and keep history in git and phase artifacts. [I]
- `context/LESSONS.md` is 135 KB and agents do not read it (GB-GSD-015, XFER-015). Keep converting lessons into AGENTS rules plus checks. [I]
- Recommended v0.3 caps [I], written into AGENTS.md or the v0.3 CONTEXT before discuss:
  - ≤2 review-fix rounds per phase.
  - ≤1 gap round, and a second only with new evidence.
  - Review findings about test or tooling robustness become seeds unless they violate an existing required contract.
  - No new verifier, receipt or admission tool unless it names a concrete fault and has a negative control.
  - A phase that exceeds ~12 plans triggers a scope check rather than further planning.

---

## 3. Save states: what to copy from nesturbator v3 Phase 12

The design was settled in `12-CONTEXT.md` (decisions D-01..D-17) and `milestones/v3-research/{ARCHITECTURE,PITFALLS,SUMMARY}.md`. Implementation: `src/state.c`, 524 lines [V].

### API and buffer contract [V 12-CONTEXT.md:37-52]

```c
size_t nesturbator_state_size(const nesturbator *inst);           /* 0 with no cartridge; constant load→unload */
nesturbator_status nesturbator_save_state(const nesturbator *inst, void *buf, size_t capacity);
nesturbator_status nesturbator_load_state(nesturbator *inst, const void *buf, size_t size);
```

- Save takes `const` (the type documents no mutation). It accepts capacity ≥ size, writes exactly size bytes, never allocates, and leaves the buffer untouched on error. A NULL buf is never a size query.
- Load requires `size == state_size` exactly, so truncated and padded input are both refused.
- A tolerant zero-tail fallback, if a frontend pads, lives only in an adapter, never in the core.

### Format [V 12-CONTEXT.md:136-165; src/state.c:26-29]

- Canonical little-endian bytes, never a struct dump (padding, pointers and enum width differ by platform; PITFALLS 2).
- **64-byte header** with:
  - an 8-byte magic that includes a non-text byte, like PNG, so text-mode mangling is caught;
  - a header-size field;
  - the format version;
  - total size;
  - the behaviour revision (recorded, **not enforced**);
  - cartridge identity (mapper, submapper, region, ROM CRC-32);
  - reserved bytes written as zero and validated as zero;
  - a CRC-32 over everything except the CRC field.
- `STATE_FORMAT_VERSION` is a public macro, kept separate from the ABI version and the package version.
  - **An exact match is required**; there is no converter and no tagged or skippable sections.
  - Before the first release with states, layout changes simply re-pin.
  - After it, any byte-layout or meaning change bumps the version in the same commit.
  - A bump is `feat:` with a changelog note ("older states are refused"), not BREAKING unless the C API changes (D-14).
- One **field-list visitor** per struct with modes SIZE / WRITE / VALIDATE / APPLY. Every board (mapper) must provide a `state` op, or it does not build. RETROSPECTIVE.md:102 says save and load "never drifted" and the rejection sweep "came almost free".
- No committed binary state file. The CI pin is `state_format N` plus per-board state size and state SHA-256 lines in the existing `tests/runner/hashes.txt` (line 114 `state_format 1` [V]). A ctest requires that line to equal the macro (D-15).

### Transactional load: fixed check order, each refusal byte-identical [V 12-CONTEXT.md:56-91]

1. NULL argument → ERR_ARGUMENT.
2. Size < header → STATE_SIZE.
3. Bad magic or version → STATE_FORMAT.
4. No cartridge, or identity mismatch → STATE_CARTRIDGE. **Identity is checked before full length**, because size depends on the cartridge, so another game's state reports "wrong game" rather than "wrong length".
5. Length ≠ state_size or ≠ the header total → STATE_SIZE.
6. CRC → STATE_CHECKSUM.
7. Range, enum and reserved-zero checks → STATE_INVALID.
8. APPLY. **VALIDATE covers exactly the bytes APPLY reads, so APPLY cannot fail.**

There are five appended status codes, one per class, and the enum does not grow with the format. The header documents the order with a "Checks in order:" idiom. JAM and lockup latches are part of the state and validated as 0/1. Load never returns a stop reason (D-06).

### The critical footgun: unbounded time fields [V 12-REVIEW.md:74-93; fix `c6c1c69`]

A CRC-valid state with `ticks = UINT64_MAX` passed VALIDATE. `ppu_ticks + 8 <= ticks` then wrapped, and the next `run_frame` looped about 2^61 times, a denial of service for any host loading untrusted states. The fix was `STATE_TICKS_MAX = 1<<62`, enforced in VALIDATE, plus a regression that sets both counters to UINT64_MAX with a recomputed CRC and runs one frame.

muhtari pre-adopted "ticks capped" in its SEED-002 [V `muhtari/.planning/seeds/SEED-002-states-and-movies.md` Notes].

For GabbaBoy [I]: every 64-bit timeline field must be bounded in VALIDATE so that deadline arithmetic cannot wrap. That covers the master clock, scheduled-event deadlines, the RTC emulated-time base, the APU frame-sequencer position and the HDMA/KEY1 stall counters. Add an "every field at max, with CRC recomputed" sweep.

### Determinism tests [V 12-CONTEXT.md, v3-ROADMAP.md:78-82, 13-CONTEXT.md D-10..D-16]

- **Fork test.** Save at several frames, *including frame 0*, then load into a **fresh instance pre-filled with another game** ("poisoned pre-fill"). Continue and compare every later frame hash, audio hash, tick count and the final state bytes against an uninterrupted run, per board.
- **Save every frame changes no pinned hash.** This proves save is observation-free.
- **Stress image forked at every boundary** (DMA/IRQ heavy), through the same driver.
- **Rejection sweeps** under ci and ASan/UBSan:
  - truncation at every length;
  - every byte flipped, asserting the *expected class per offset*;
  - out-of-range fields with the CRC recomputed, expecting INVALID;
  - another game, another version.
  - Each asserts the instance is byte-identical afterwards.
- **Load-600-times leaves the battery generation unchanged.** A load that changes battery bytes raises the generation exactly once (STATE-05). This avoids 60 Hz `.sav` writes during rewind and silent old-save overwrite (PITFALLS 6).
- **Run-ahead host model** (if or when a libretro or rewind consumer exists):
  - N = 1..3 speculative frames with save/load per frame;
  - visible frame t equals the uninterrupted frame t+N;
  - real-timeline audio and the state bytes at every real boundary match exactly.
  - **Anti-vacuity controls:** a host that skips the load, loads a stale t-1 state, applies input one frame late, or leaks speculative audio must fail the same comparator.
  - Tests may not skip or run zero iterations, and they assert minimum counts (D-16, D-20).
- **Fuzz.** A libFuzzer target on the state loader:
  - a committed corpus of `valid-<cart>` plus a few `reject-*` seeds, replayed as a ci test;
  - a nightly time-boxed run;
  - CRC fix-up lives **in the harness**, never as a fuzz-only flag in the core;
  - oracles use `abort()`, not `assert` (D-31..D-36).
- **Cost.** `--bench-state` reported save and load p50 ≈ 10 µs on arm64 [V 15-03-SUMMARY.md:33-39]. Measure before optimizing; no compression or deltas in the core (v3-REQUIREMENTS Out of Scope).

### Runner as test tooling [V 12-CONTEXT.md:103-134]

- `--state-at-frame N:FILE`, `--load-state FILE` and `--hash-state N`. A rejected state exits 5; an unreadable file exits 1.
- **Frame indices stay absolute from power-on.** After loading frame K, `--frames N` is the end frame. N = K saves the state just loaded, which is a cheap round-trip check.
- **Order:** parse → create → load ROM → load battery → load state → range-check → run.
- **`--movie` together with `--load-state` is refused** until "a movie that starts from a state" is designed (D-12).

### Libretro serialize constraints (for later, or if GabbaBoy ever adds libretro) [V 13-CONTEXT.md:28-56; v3-research/PITFALLS.md:39-49, 90-99]

- The size must be constant from load to unload and 0 with no content. RetroArch sizes its rewind ring from the first call, and run-ahead and netplay allocate once.
- No `SET_SERIALIZATION_QUIRKS` (each disables run-ahead or netplay); a source test asserts it is absent.
- State bytes must be identical across every `GET_SAVESTATE_CONTEXT` and with AV-enable flags on or off.
- Unserialize must work before the first `retro_run` and right after `retro_reset`.
- `.info` `savestate_features` levels (basic < serialized < deterministic) are each claimed only with green proving tests. A configure-time guard maps claim → registered tests (D-18, D-19).

### GabbaBoy-specific state points not covered by the siblings [I]

- **State point.** nesturbator saves only at frame boundaries. GabbaBoy's run API stops on deadlines, idle and output-full (GB-GAME-005/006). Decide whether a state is legal at any stop or only at frame boundaries, and assert that output pointers and PCM queues are empty at that point. nesturbator did this as Phase 11 readiness.
- **Profile identity.** DMG-CPU-B versus CGB-CPU-E, and compatibility mode, go into header identity next to the ROM digest and mapper. A CGB state must not load into a DMG instance.
- **Size.** Size varies by cartridge RAM and profile (CGB WRAM/VRAM banks) but must be constant per load.
- **RTC.** A state restores emulated RTC time, while host catch-up stays host policy. Document that rewinding past an in-game save reverts SRAM *and* RTC registers. The battery block is versioned already; keep the state version separate from it.

---

## 4. libretro and Playstead integration

### What nesturbator learned about libretro [V]

- **Adapter boundary.** The library does no file I/O; the adapter owns no save files; the frontend writes `.srm` (v3 audit, integration section).
- **Tests.** An in-process host calls the real `retro_*` entry points (`tests/libretro/libretro_host.c`), plus one hosted `retroarch-e2e` job driven by RetroArch network commands.
- **What broke:**
  - The single-sample audio callback path was missed and needed gap phase 4.2.
  - Real RetroArch aborts inside the agent sandbox, so the hosted job is the evidence (XFER-011).
  - The e2e ran only on macOS.
  - Its frame-chain checks could not detect a dropped or doubled FRAMEADVANCE (v3 audit WR-01..03). That gap later became the Phase 16 balloon.
  - Retrying non-idempotent host commands is unsafe: "Never blindly retry a host mutation" (forensics lesson 4).

Transferable [I]: keep any real-frontend e2e to one screenshot compare plus one save round trip (XFER-007). Put the precise determinism proofs in an in-process host.

### Playstead's contract (what INT-01 must satisfy) [V]

From muhtari's research of Playstead at `012163f047c3`, which I confirmed is a commit in the Playstead repository (`HOSTS-AND-INTEGRATION.md:125-172`, `nesturbator/.planning/preparation/LIBRETRO-AND-RUNNER.md:91-103`), and from Playstead HEAD `c65726a6` `AdapterPin.json`:

- **The pin** carries:
  - `system`;
  - `emulator`, `version`, `download_url` and `sha256`;
  - `launch.executable_relative_path` and `argument_template` with `{romPath}` and `{saveDir}`;
  - `config_injection`;
  - `save_contract`: `artifact_glob "{saveDir}/{romBaseName}.sav"`, `flush_triggers`, `on_demand_flush_supported`, `worst_case_loss_seconds`, `media` with byte sizes, `size_is_medium_identity`, and `binding_fields` [system_id, save_kind, medium_id, artifact_bytes, rom_sha256];
  - `exit_detection` signatures.
- **Termination.** Playstead sends SIGTERM and escalates to SIGKILL after **2 s**.
  - With the current mGBA pin, SIGTERM is indistinguishable from a crash and is classified `killed`.
  - That pin also has no on-demand flush and up to 24 s of save loss.
  - A GabbaBoy runner that finishes the frame, flushes atomically and exits 0 inside 2 s closes a real gap.
- **Continuation protocol `local-continuation-adapter-v1`:**
  - The actions are qualify, initial-run and continue.
  - Each action gets a fresh private directory, `PATH=/usr/bin:/bin` and no network. muhtari proves there is no socket code with a symbol-allowlist test (a claim; planned for v3).
  - Exits are **0 pass, 77 capability refusal before fixture access, 1 failure after access**.
  - `continue` = a fresh process from a copied save directory, a second movie, and a hash at frame M, with at least two equal oracle hashes.
- **Location.** The protocol script is at Playstead `playstead-mac/scripts/ci/continuation_protocol.py`. The old `docs/CONTINUATION-PROTOCOL.md` cited by muhtari is **not present at Playstead HEAD**. Re-read the live script and pin before writing INT-01 requirements; do not copy muhtari's table blindly. Playstead's live system id list should also be checked for `gb`/`gbc` (muhtari reports `gba gb gbc nes snes md psx` [C]).

### Runner process contract shape (nesturbator v3 Phase 14, 8 plans) [V v3-ROADMAP.md:156-192]

- **Signals.** On SIGTERM/SIGINT the runner finishes the current frame, flushes the battery atomically and exits 0, or 1 if the flush failed or a requested output was not reached. The handler only sets a flag; a second signal kills immediately. Windows Ctrl+Break and console close are handled the same way. Forced termination is documented as unhandleable.
- **One exit-status table** (X-macro) shared by one header, `--help` and the README, with an equality test. Each status has its own test. nesturbator has 0/1/2/4/5, with 3 and 77 reserved; muhtari plans 3 and 77 live.
- **Test with real signals.** "Real-signal and real-Ctrl+Break tests found an EINTR abort in the state read that a simulated stop would have missed" (RETROSPECTIVE.md:104).
- **Atomic replace.** One helper (temp → fsync → rename), with failure injection: an unwritable directory and a directory at the target path must leave the old `.sav` intact with no stale `.tmp` (v3 Phase 11).
- Planned for later (muhtari): `--capabilities` JSON preflight that writes nothing, `--probe` hashes, and `--save-interval` with SIGUSR1 on-demand flush.

### Recommended v0.3 phase shape [I]

Modeled on nesturbator v3, which took 3 days and 38 plans, with one critical finding found by review rather than in production:
1. **State readiness tune-up** (≤5 plans): define the state point and boundary invariants; atomic writer reuse; measured CI budgets; trim STATE.md.
2. **States in the library** (≤10 plans): visitor, header, check order, every-field bounds, fork matrix with poisoned pre-fill for DMG and CGB profiles and each mapper, rejection sweeps, battery-generation rule, runner state options and pins.
3. **State fuzz and cost** (≤5 plans): loader fuzz with a committed corpus replayed in ci, and `--bench-state`. This can fold into phase 2 if small.
4. **Playstead runner contract (INT-01)** (≤8 plans): SIGTERM flush, exit table, `--capabilities`, a pin draft and continuation-protocol qualify/initial-run/continue run against the live Playstead script, with real-signal tests.
5. **Close-out** (≤5 plans): docs and pin review, measured timeouts, release PR green.

---

## 5. Release, CI and test architecture lessons not already in GabbaBoy LESSONS

I checked these against GabbaBoy's lesson headings, RETROSPECTIVE and `ci.yml`.

- **Check that the release PR is green at every phase close.** nesturbator's release PR #35 sat red on `hygiene.format` from v2 to the v3 close, because aligned machine-edited version comments broke the formatter [V `b8e2824` "fix(release): keep version macros stable across digit widths"; RETROSPECTIVE.md:109, 120-121]. Keep machine-edited version strings out of aligned blocks; muhtari uses version-free asset names plus `version.txt` (MU-REL-003).
- **CI push trigger.** GabbaBoy `.github/workflows/ci.yml:6` has an unfiltered `push:` alongside `pull_request:` [V]. muhtari's XFER-021 records that this doubles cost and restricts push to `main`. GabbaBoy's exact-head evidence may rely on branch push runs, so confirm before changing. [I]
- **Skip heavy jobs on planning-only PRs.** Use a `changes` job while the required aggregator still reports; never a trigger-level `paths` filter, which leaves the required check pending (MU-CI-002: nesturbator PR #47 spent 3,089 job-seconds on a `.planning`-only PR [C]). GabbaBoy has many docs-only verification PRs. [I]
- **Every `timeout-minutes` carries the run ID it doubles,** enforced by a lint (nesturbator `hygiene.timeout_comments`) [V RETROSPECTIVE.md:116]. GabbaBoy's GB-CI-010 covers re-running but not the comment lint. [I]
- **Sanitizer lanes check the first frames, not full-length runs.** Full-length hashes stay on build jobs (nesturbator v2 [V RETROSPECTIVE.md:72]).
- **The perf gate uses instruction counts (Cachegrind) between head and merge base.** Arm it only after two zero-spread control runs; a deliberate slowdown needs a reviewed allow-file line [V v3-ROADMAP.md:200-203].
- **Every `.info` or support claim maps to its proving tests at configure time** (claim → registered-tests table) [V 13-CONTEXT D-18]. GabbaBoy's support ledger could use the same guard for "states supported" claims. [I]
- **GSD-specific:**
  - `/gsd-ship` pushes a `[ci skip]` commit, so the squash message must come from the PR title and body (MU-GSD-002).
  - Any argument containing the substring `--auto` chains steps (MU-GSD-004).
  - `branching_strategy: phase` branches only at execute, so discuss and plan commits land on the current branch; branch first (MU-GSD-006).
  - The config writer merges global defaults into the public `config.json`; write it with an empty `GSD_HOME` (MU-GSD-001). Relevant because GabbaBoy has an uncommitted `.planning/config.json` change at session start. [I]
  - These were read in GSD 1.17.0 [C]; re-check them in OpenGSD.
- **Property testing.** A ~60-line seeded splitmix64 harness replaces `theft`, which needs fork/waitpid and so does not work on MSVC (MU-TEST-001) [C].

### Already recorded in GabbaBoy (skipped)

- Exact-head evidence.
- Boundary-commit verifiers (GB-GSD-024).
- Freshness staleness (GB-GSD-008).
- The App token for release PRs (XFER-008 cites GabbaBoy PR #41/#70).
- `.gitignore` fixture exemptions (GB-CART-007).
- Exact test inventories (GB-GSD-017).
- Negative controls asserting a specific reason (GB-CGB-005).
- Game-level progress before breadth (GB-GAME-001).
- Struct compare with padding (GB-GAME-003).
- Split-run and save/load continuation (XFER-004).
- Checkers out of phase directories (GB-GSD-026).

---

## 6. Evidence index

nesturbator:
- `.planning/PRODUCT-ROADMAP.md`
- `.planning/RETROSPECTIVE.md`
- `.planning/STATE.md:100-213`
- `.planning/forensics/report-20261022-234424.md`
- `.planning/phases/16-host-evidence-and-roadmap/16-RECOVERY.md`
- `.planning/milestones/v3-{ROADMAP,REQUIREMENTS,MILESTONE-AUDIT}.md`
- `.planning/milestones/v3-phases/12-save-states-in-the-library/{12-CONTEXT,12-REVIEW,12-REVIEW-DISPOSITION}.md`
- `.planning/milestones/v3-phases/13-rewind-and-run-ahead-in-retroarch/{13-CONTEXT,13-REVIEW}.md`
- `.planning/milestones/v3-research/PITFALLS.md`
- `.planning/seeds/SEED-002-*.md`
- `.planning/preparation/LIBRETRO-AND-RUNNER.md:91-103`
- `src/state.c:26-29,325-329`
- `tests/runner/hashes.txt:114`
- Commits `c6c1c69`, `b8e2824`, `8ae2c6e`, `5e681c8`, `227bd6a`.

muhtari:
- `AGENTS.md:26-49`
- `.planning/LESSONS.md:39-101`
- `.planning/PRODUCT-ROADMAP.md`
- `.planning/milestones/v1.0-PRODUCT-ROADMAP.md`
- `.planning/MILESTONES.md`
- `.planning/RETROSPECTIVE.md`
- `.planning/preparation/GSD-HANDOFF.md` §3
- `.planning/preparation/HOSTS-AND-INTEGRATION.md:23-172`
- `.planning/research/proportional-gates/RECOMMENDATION.md`
- `.planning/seeds/SEED-002-states-and-movies.md`

Playstead (read-only spot check):
- `playstead-mac/Playstead/Adapter/AdapterPin.json`
- `playstead-mac/scripts/ci/continuation_protocol.py`
- HEAD `c65726a6`; cited historical commit `012163f047c3` exists.

GabbaBoy comparison:
- `.planning/STATE.md` (77,351 B)
- `.planning/context/FUTURE-MILESTONES.md`
- `.planning/RETROSPECTIVE.md`
- `.github/workflows/ci.yml:3-6`
