# Sibling-project lessons for GabbaBoy v0.3 (STATE-01 + INT-01)

Date: 2026-10-24. Read-only inspection of genewhip, schwaystation, cogmaster and earthbound-recomp, plus
two Playstead documents because INT-01 targets Playstead. Nothing was built, run or modified. Lessons
already in GabbaBoy `.planning/context/LESSONS.md` (GB-*) or `RETROSPECTIVE.md` are skipped unless a
sibling improved on them.

Legend: **[V]** verified at the cited file:line or commit; **[C]** the sibling claims it and I did not
reproduce it. All paths are relative to the named repository.

---

## 0. Cross-project lesson infrastructure (it exists, and GabbaBoy is a source)

- [V] schwaystation `.planning/LESSONS.md` (179 lines) and cogmaster `.planning/LESSONS.md` (138 lines)
  hold an `XFER-001..105` import ledger, passed along muhtari → cogmaster → schwaystation. **About 20
  rows come from GabbaBoy** (XFER-008, 013, 014, 015, 018, 021, 048–051, 069, 070, 077–079, 102).
  Each row has a local disposition: adopted, strengthened or rejected.
- [V] Both sibling ledgers say "Lessons learned here: None yet". Neither young project has exported
  lessons yet.
- [V] schwaystation LESSONS.md:10-14: rules live in AGENTS.md/DECISIONS, because agents read those files.
  The ledger is told to be re-read at **every discuss step**, not only at kickoff (XFER-059/100: a
  sibling repeated a lesson two weeks after it was exported).
- [V] genewhip `.planning/research/SIBLING-LESSONS.md` (118 lines) and `context/OPERATING.md:136-138` keep
  an export template: observation → evidence → preconditions → impact → recommendation → limits →
  regression.
- [V] schwaystation enforces unique lesson IDs with a test, `policy.lessons_unique` (LESSONS.md:24-26).
  Reason: a sibling ledger reused IDs (XFER-069, sourced from GabbaBoy). GabbaBoy's own LESSONS.md still
  has duplicate IDs: `GB-FIXTURE-001` appears three times (lines 64, 214, 835) and `GB-TEST-001` twice
  (151, 223).

## 1. Process and velocity footguns, and what fixed them

### 1a. Self-imposed time budgets and accounting ceremony stalled a whole phase (genewhip v0.2 Phase 6)
- [V] genewhip `.planning/ROADMAP.md` Phase 6 stands at 5/13 live plans successful, with plans halted
  and superseded. 44 commits touched the phase directory on 2026-10-23/24. In the same window only 6
  commits touched `src/` or `include/`.
- [V] `quick/261024-guy-.../261024-guy-RECOMMENDATIONS.md` says "insufficient time" meant a
  project-defined wall-clock allowance (1,800 s offline, a 9,000 s PEA ceiling, 400.251 s "other"). It
  was not CPU or tokens. Planning, handoffs, polling and bookkeeping consumed the allowance before any
  C compilation. The cause it names: "Engineering effort and execution risk became coupled."
- [V] `context/OPERATING.md:72-89` records the fixes:
  - Forecast the complete delivery path before committing to bounded work.
  - Reserve closeout before starting.
  - Make no unchanged plan/execute loops after a designed stop.
  - Use one coordinator, and add a reviewer only when it can change a decision.
- [V] Converging evidence from other siblings:
  - schwaystation LESSONS XFER-099: a nesturbator plan accepted 0 of 3 tasks in four days, metering
    itself with a monotonic "allowance" and a `sysctl` the sandbox denies.
  - cogmaster AGENTS.md rule 8 bans the whole pattern: no attempt quotas, "formal slots", admission
    ceremonies, lifetime counters, qualification campaigns, self-metering clocks or privileged OS
    queries.
- **Transfer:** GabbaBoy's 15.1 loop (36 plans, verifiers bound to boundary commits) is a milder form of
  the same failure: evidence machinery grew faster than product code. For v0.3, adopt cogmaster rule 8
  verbatim. Stop any plan whose evidence depends on a value the sandbox cannot read.

### 1b. Test the compiled behavior first, not source strings or fabricated JSON (genewhip D123)
- [V] genewhip `06-LEARNINGS.md` §"Compiled feedback before qualification", and OPERATING.md:123.
  Commit `ea0c6ef` removed the only before-capture call. 61 accounting tests (with fake clocks) and 8
  observer checks (source fragments plus authored JSON) all passed, while the real C path never
  executed.
- **Transfer to STATE-01:** the first save-state plan should be a real save → run → load → compare round
  trip through the public API. Do not start with format docs, manifest checkers or evidence parsers.

### 1c. Cap review and gap rounds per phase
- [V] cogmaster AGENTS.md rule 7: at most two code-review fix rounds and one gap round per phase. Code
  review runs **before** verification. Review findings about test or tooling code become seeds, not
  requirements.
- [V] schwaystation AGENTS.md rule 7 adds: a third fix round needs new evidence (XFER-085), and each
  leftover becomes one todo bound to the next plan that adds its first caller.
- [V] cogmaster `phases/03-*/03-REVIEW-DISPOSITION.md` shows the outcome: 2 findings, both fixed, 0 open.
- **Transfer:** directly limits a repeat of 15.1, which had two gap rounds, a validation pass and two
  re-audits.

### 1d. Decide verification freshness and closeout policy up front
- [V] cogmaster `preparation/GSD-HANDOFF.md:109-111`: a fix merged after verification makes it stale.
  Accept an override closeout at milestone end when CI passes on the merged head and the milestone
  audit covers the phase. "Do not spend sessions refreshing digests."
- [V] Same file, lines 83-87: run `/gsd-verify-work` only for `human_needed`. For `gaps_found`, run one
  fresh verifier first (XFER-036/053).
- **Improves on** GB-GSD-008 and RETROSPECTIVE v0.2 lesson 4. GabbaBoy reached the override reactively;
  cogmaster states it as policy before phase 1.

### 1e. Phase and plan sizing, and velocity
- [V] cogmaster ran 3 phases in about 2 days, each one PR plus one release: `ea3bd22` → 0.1.0 (#5),
  `0b88812` → 0.2.0 (#7), `cb13189` → 0.3.0 "playable in RetroArch" (#8). STATE.md:65-101 lists plans
  of 4–50 min (median about 13), 12–17 plans per phase.
- [V] schwaystation AGENTS.md rule 14: plan 1 lands the CMake skeleton and the per-directory test
  inventories. Later plans run in parallel waves unless they share an inventory or header. A plan past
  30 minutes is split. No test is "non-gating".
- [V] genewhip `.planning/estimation-calibration.json`: token estimates against actuals range from 0.5x
  to 16x (32k estimated, 525k actual; 18k estimated, 190k actual). Up-front estimates are unreliable;
  splitting on measured duration is safer.
- [V] cogmaster AGENTS.md rule 9 and GSD-HANDOFF §3: one GSD step per session, and runtime and model
  recorded in STATE.md at every step. This answers GabbaBoy's "model mix: not recorded".
- [V] XFER-093 (cogmaster 01-08 took 45 min against 4–13 min for its siblings): the format gate arrived
  in plan 8 and reformatted earlier files. Land hygiene and format gates in plan 1.

### 1f. Every phase ships a release, and a CI tail is budgeted
- [V] XFER-048, sourced from GabbaBoy v0.2 Phase 15: eight phases merged without a release. Fixed by
  cogmaster and schwaystation AGENTS rule 10: every phase ends in a release, and the release PR is never
  held.
- [V] XFER-065/104 and schwaystation AGENTS rule 10: the post-release `ci:` tail PR (arming the perf
  gate, promoting lanes) is a numbered step before the next discuss.
- [V] XFER-046/092: a requirement must never need a fact that only a published release can show. Such
  criteria are recorded `pending-ship` and confirmed at ship.

### 1g. CI mechanics worth copying
- [V] XFER-012/084 and schwaystation `d8a0ab4` ("set every timeout from this repository's measured
  runs"): timeout = 2x the slowest recent run, with its run ID. Every lane uploads JUnit, and a `-P`
  script computes the value. This turns GB-CI-010 from a re-run habit into an automated derivation.
- [V] XFER-042: a `.planning`-only PR should skip heavy jobs through a `changes` job while the aggregator
  still reports. Never use a trigger-level `paths` filter.
- [V] schwaystation commit `a0a7c79`: an Ir-per-frame perf gate at +1.00 % armed in phase 1 (XFER-051,
  sourced from GabbaBoy 15-05's 23.96 % surprise).

### 1h. Gate-code budgets: absolute, not a ratio
- [V] XFER-086: a "tenth of `src/`" budget was exceeded 2.1–7.4x because gates are front-loaded.
  schwaystation changed it to an absolute line budget per phase plus a ratchet (AGENTS rule 7, commit
  `22f8308` "count the gate code against a 1500-line budget").
- [V] XFER-044: a sibling e2e phase added about 10,250 test lines and changed nothing under `src/`.
  Real-host e2e test code now has a 300-line cap, checked by a test.
- **Transfer:** STATE-01 continuation and INT-01 adapter checks are prime candidates for tooling sprawl.
  Give each phase an absolute tooling-line budget.

### 1i. Small empirical footguns
- [V] earthbound-recomp `RETROSPECTIVE.md` v0.1 "Inefficient":
  - Scratch timings were lost because they lived only in /tmp; one plan spent about 4 sessions on them.
  - Pin the frontend emulator and probe its actual behavior. In Mesen2, F1–F7 collide with
    LoadStateSlot, and `.mmo` playback is GUI-only.
- **Transfer:** keep INT-01 empirical notes in-repo.

## 2. Save-state design

### 2a. cogmaster: a working visitor with five passes [V]
- `src/state.h:1-11`: one field list drives SIZE, WRITE, VALIDATE, APPLY and RECORD. VALIDATE
  range-checks every field without touching the instance, so "once VALIDATE passes, APPLY cannot fail".
  This makes load transactional without copy-on-write.
- `src/state.c:445-480`: load checks argument/content → exact size → body CRC-32 → full VALIDATE →
  APPLY. A refused state changes nothing.
- `src/state.c:1-20, 22-50`, 64-byte header:
  - PNG-style magic that breaks under text-mode transfer;
  - format version, header size, total size, **behaviour revision**, API version;
  - packed profile (machine/region/tv);
  - ROM CRC-32, body CRC-32, frame, ticks, and 12 reserved zero bytes.
- Every field is written byte-wise little-endian. Structs are never copied whole.
- `src/state.c:49-55`: `_Static_assert(sizeof(struct X) == N, "X changed: update X_io")` tripwires. A
  new field fails the build until the visitor visits it.
- RECORD emits name/offset/width/min/max for each field. `tests/core/test_state.c:216-260` (`sweep`)
  uses it to auto-generate an out-of-range rejection for every bounded field.
  `cogmaster__state_seal` (state.h:47-49) re-seals the CRC so mutations reach the range checks.
- `include/cogmaster.h:17`: `COGMASTER_STATE_FORMAT_VERSION 10`, an internal format revised 10 times by
  phase 3. It is not public (state.h:11). The public format freezes in the states milestone
  (ARCHITECTURE.md §7).
- `libretro/libretro.c:373-385` already wires `retro_serialize*` to it. The `.info` `savestate_features`
  claims are staged basic → serialized → deterministic, each behind a test (HOSTS-AND-INTEGRATION.md §1
  `.info` table): "save+load every frame for 600 frames = straight run", plus six-platform state hashes.

### 2b. schwaystation CR-01: the closure property [V]
- `phases/01-*/01-REVIEW.md:164-182`. The loader accepted `ticks == 2^62` and `frame == STATE_FRAME_MAX`,
  but `run_frame` incremented past those limits. The sequence load OK → run OK → save OK → **load
  rejected** was observed as statuses `0 0 0 10`.
- Fix `b7c658a`: one shared invariant for the run limit and the load limit, plus 84 test lines.
- **Transfer (high value):** STATE-01 needs a property test: every accepted state, run N steps, saves to
  a state that is again accepted. Validator bounds must be derived from the same constants the runtime
  enforces.

### 2c. Design guidance from sibling planning [V, planning only]
- cogmaster `seeds/SEED-002` Notes and genewhip REQUIREMENTS.md:57: keep persistent saves, snapshots and
  movies as **three formats with separate version rules**. This matches GabbaBoy D-011.
- cogmaster SEED-002 scope: fork tests at every frame (save, then continue on both branches, and assert
  equal hashes) and hidden-state checkpoints with omitted-field controls (XFER-070).
- schwaystation REQUIREMENTS.md:77: the header binds a behaviour revision and the media identity;
  battery/cards are **outside the state by default**.
- earthbound-recomp ROADMAP.md:171: hash guest state separately from presentation, so render-only
  options never change state hashes. cogmaster's options table marks this "In state hash: yes/no" per
  option.
- genewhip has **no** save-state implementation (`include/genewhip/genewhip.h:17` promises no snapshot
  format). Nothing to inherit there.

## 3. Frontend, Playstead and libretro integration

### 3a. The Playstead continuation gate is blocked on exactly what a native runner supplies [V]
- Playstead `playstead-mac/docs/CONTINUATION-PROTOCOL.md`:
  - The adapter is called with exactly one action: `qualify`, `initial-run` or `continue`.
  - The network is denied and writes are limited to a fresh private directory.
  - `qualify` must leave the directory empty.
  - A pass needs a save transition from empty to populated, a safe exit, a distinct fresh child, a
    completed Continue and **at least two agreeing visible-state oracle runs**.
  - Exit codes: 0 pass, 77 capability refusal before fixture access, 1 failure after fixture access.
- Playstead `.planning/phases/06-*/06-CONTINUATION-QUALIFICATION.md` reports the current result as
  `qualification / blocked-capability` (77). The mGBA 0.10.5 GUI has no noninteractive script loading,
  so deterministic input and a visible-state oracle could not be qualified.
- **Transfer (high value):** a GabbaBoy headless runner already has deterministic input replay and frame
  hashing. INT-01 can be "the first adapter that passes Playstead's continuation gate". cogmaster maps
  each action to runner flags in HOSTS-AND-INTEGRATION.md §4 (`--capabilities`; `--rom --input
  --save-dir --frames`; a fresh process with `--hash`). Copy that mapping.

### 3b. Playstead pin-field footguns (cogmaster HOSTS-AND-INTEGRATION.md §4) [V doc, C on Playstead source]
- Playstead's system list is frozen at `gba gb gbc nes snes md psx unknown`, and the ids must equal the
  file extensions. `gb`/`gbc` are already present, an advantage over cogmaster.
- The installer mounts a DMG and copies one `.app`. A zip/CLI runner pin needs a Playstead-side change.
- `argument_template` substitutes only `{romPath}` and `{saveDir}`. The save contract is a glob plus an
  exact classified size.
- RetroArch on macOS installs no SIGTERM handler, so SIGTERM produces no `.srm` flush. A
  RetroArch-mediated path therefore loses saves on stop unless the autosave interval covers it. Make
  the native runner flush on SIGTERM/SIGINT and exit 0, and say so in `worst_case_loss_seconds`.
- Playstead's GB/GBC play is currently pinned to mGBA (phase `04.6-game-boy-and-game-boy-color-play-and-persistent-saves`,
  `CartridgeQualification.swift`, `SaveCompatibilityGate.swift`). GabbaBoy would be a second GB adapter
  and must meet that existing save-identity gate.
- Playstead `phoenix-console` quick task `261020-v5y` CONTEXT:108-120: the owner leans toward an
  in-game overlay for state capture and load. As of 2026-10-20, Playstead had found **no libretro
  declaration** in GabbaBoy. Agreed: GabbaBoy has no `retro_*` symbols.
- **Decision for INT-01:** native runner adapter versus libretro core. Playstead's frontend UX question
  (overlay) points toward libretro or an in-process API. Its continuation gate points toward the
  headless runner. Resolve this in discuss; INT-01 says "libretro only if its value is demonstrated".

### 3c. libretro contract shape (if adopted) [V]
- cogmaster HOSTS-AND-INTEGRATION.md §1:
  - The adapter is about 350 lines, in nesturbator's shape.
  - `retro_serialize_size` stays constant from load to unload.
  - No `SET_SERIALIZATION_QUIRKS`.
  - Each `.info` claim maps to a guard test at configure time.
  - RetroArch reads the claim level only when the `.info` sits beside the core.
  - Rewind, run-ahead and netplay are disabled above the declared level.
- XFER-011: RetroArch aborts inside the agent sandbox, so the hosted job is the evidence. Real-host e2e
  stays under 300 lines (XFER-044).

## 4. How the young projects bootstrapped

- [V] cogmaster `66fb150` "repository scaffold adapted from muhtari". Phase 1 was a port of muhtari at
  its 0.1.0 pin: 126 files fetched with `gh api`, 8 plans in a day (XFER-094). schwaystation `f84bfb7`
  was adapted from cogmaster.
- [V] The pre-written preparation pack (`preparation/`: ARCHITECTURE, DECISIONS, ENGINEERING,
  HOSTS-AND-INTEGRATION, GSD-HANDOFF, PROMPT-COVERAGE) plus a roadmapper dry run on a copy (XFER-001/038).
  Kickoff resumed at roadmap creation.
- [V] Phase 1 is a content-free walking skeleton: library, runner and libretro core with a test frame,
  6-platform CI and an attested release (XFER-002). The state visitor exists from phase 1: the test card
  round-trips (cogmaster ARCHITECTURE §7; schwaystation `887641f`).
- Adopted up front and visibly paid off [V]:
  - every phase releases (three releases in 2 days);
  - review caps (cogmaster phase 3 had 2 findings, 0 open);
  - perf gate in phase 1;
  - measured timeouts in phase 1 (`d8a0ab4`);
  - format gate in plan 1 (learned from cogmaster 01-08, applied by schwaystation);
  - an absolute gate-line budget.
- Not yet proven: neither project has closed a milestone, run an audit, or faced a debt-closure
  phase. Their velocity claims cover early phases only. schwaystation phase 1 is paused before
  verification (STATE.md, `384ee9d`).
- **Where they improved on GabbaBoy lessons:**
  1. Freshness and closeout: policy set up front, not an override found reactively (§1d).
  2. GB-GSD-015, a lesson becomes a control only as a rule plus a test: lessons were moved into AGENTS
     rules, re-read at every discuss step, with an ID-uniqueness test.
  3. XFER-048: GabbaBoy's deferred release became "every phase releases".
  4. Fuzz harness: a failing harness is a test bug to triage. Targets are report-only until green for N
     runs (XFER-049).
  5. Hosted timeouts: derived automatically from JUnit (XFER-084), not by re-run habit.
  6. GB-GAME / D-101: choose or author the game fixture **before** the milestone starts (XFER-050).

## 5. Rolling roadmap structure

- [V] cogmaster and schwaystation keep three layers:
  - `ROADMAP.md` is the execution contract for the current milestone.
  - `PRODUCT-ROADMAP.md` holds the Immediate/Near/Mid/Long horizons, each naming a seed and a
    **promotion trigger**.
  - `seeds/SEED-00N-*.md` (`status: dormant`, `trigger_when`, scope estimate, breadcrumbs) hold each
    horizon's narrative.
- [V] cogmaster PRODUCT-ROADMAP.md:
  - Refresh rule: at each milestone boundary, reconcile shipped and partial work, keep debt visible,
    re-rank, record why, and move only owner-approved scope to Immediate.
  - The file is snapshotted as `milestones/vX.Y-PRODUCT-ROADMAP.md` at close.
  - Every milestone names "a behaviour a player can see" (XFER-047). Governance never forms a
    milestone of its own.
  - The decision log is a table.
- [V] SEED-007 "milestone tune-up" is the **first phase of every milestone after the first**. It covers:
  - CI efficiency, with timeouts re-derived as 2x the slowest of the last 40 runs;
  - weakest-dimension scoring 1–5 with links;
  - `quality.json` ratchet;
  - doc freshness;
  - a PRODUCT-ROADMAP refresh and a lesson export.
- [V] genewhip OPERATING.md §"At each phase boundary"/milestone: the "weakest useful measured dimension"
  review, and a compact quality table in each SUMMARY (dimension → baseline → change → unknowns → next
  action).
- **Transfer:** GabbaBoy's `FUTURE-MILESTONES.md` is one table. Adding explicit trigger fields and a
  standing tune-up phase 1 would absorb the CI-headroom and freshness debt that 15.1 carried (GB-CI-010,
  GB-GSD-008). It would do this in a small bounded phase rather than an inserted 36-plan one.

## Ranked recommendations for v0.3

1. Adopt cogmaster AGENTS rule 7 and rule 8 verbatim for v0.3: at most 2 review-fix rounds and 1 gap
   round, review before verification, no self-metering or ceremony. Evidence: genewhip Phase 6, XFER-099,
   GabbaBoy 15.1.
2. Build STATE-01 on a SIZE/WRITE/VALIDATE/APPLY/RECORD visitor with `_Static_assert` tripwires, a
   RECORD-driven rejection sweep and a CRC re-seal hook (cogmaster `src/state.{h,c}`,
   `tests/core/test_state.c`). Add the closure property test from schwaystation CR-01, and fork-at-every-frame
   continuation.
3. Make the first STATE plan a compiled public-API round trip (genewhip D123).
4. Frame INT-01 around Playstead's blocked continuation gate. The headless runner can provide
   deterministic input and a visible oracle, which mGBA 0.10.5 cannot. Use cogmaster's action → flag map
   and SIGTERM-flush exit semantics. Settle native runner versus libretro in discuss.
5. Write the closeout and freshness policy into the v0.3 kickoff (cogmaster GSD-HANDOFF:109-111). Run
   verify-work only for `human_needed`.
6. Make each v0.3 phase a release. Budget the `ci:` tail as a numbered step. Derive timeouts from JUnit.
7. Add trigger-bearing seeds, a PRODUCT-ROADMAP refresh rule and a standing tune-up phase. Fix the
   duplicate lesson IDs and add a uniqueness test.
