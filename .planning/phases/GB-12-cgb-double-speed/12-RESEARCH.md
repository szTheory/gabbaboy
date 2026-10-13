# Phase 12: CGB Double Speed - Research

**Researched:** 2026-10-13
**Domain:** Portable C GB/GBC emulator core: CPU-speed clock domain, STOP speed switch with an explicit stall, partition-equivalent run loop, hardware-ROM oracle admission
**Confidence:** HIGH for the code map and test infrastructure (all read this session); MEDIUM-HIGH for the AGE outcome predictions (measured on a throwaway prototype, not on committed code); MEDIUM for hosted-CI timing (extrapolated)

**Method note.** The discussion already did the external hardware research (SameBoy `stop()`, AGE row list, Pan Docs rejection). This document does not repeat it. It maps the implementation onto THIS codebase and de-risks it with a scratch prototype: a patched copy of `src/core/gabbaboy.c` (about 130 changed lines, not committed, not in the repo) was built into a copy of the repo and run against (a) the whole existing CTest suite and (b) the 13 AGE ROMs rebuilt from the pinned commit with RGBDS 1.0.1. Results are tagged `[VERIFIED: prototype]`. The prototype is evidence about the design, not a deliverable; the planner must re-derive every number from the committed implementation.

<user_constraints>
## User Constraints (from CONTEXT.md)

Full text lives in `.planning/phases/GB-12-cgb-double-speed/12-CONTEXT.md` (D-01..D-36). The headline of every locked decision is repeated here verbatim; the sub-bullets of each decision are binding too and are not re-copied.

### Locked Decisions
- **D-01: The switch path is gated by `model_is_cgb(m) && exec_mode == GBB_MODE_CGB && key1_armed`.**
- **D-02: The decision table is SameBoy's `stop()` (`Core/sm83_cpu.c` ~L385-455, `c4cf7abab79a`), triangulated with AGE.**
- **D-03: KEY1 reads `$7E | (double_speed << 7) | key1_armed` on the CGB profile in CGB mode.**
- **D-04: STOP decides its D-02 case first, then preflights only the bytes it actually fetches**
- **D-05: Duration is `GBB_SPEED_SWITCH_STALL_T = 0x20008` CPU T-cycles at the new (destination) speed.**
- **D-06: The stall is persisted state, consumed by its own run-loop branch.**
- **D-07: Every device keeps advancing during the stall:**
- **D-08: An interrupt ends the stall early, like a HALT wake.**
- **D-09: A CPU-to-PPU phase policy on entering normal speed.**
- **D-10: Scaling.**
- **D-11: The APU frame-sequencer DIV tap is `divider_counter` bit 12 (`0x1000`) at normal speed and bit 13 (`0x2000`) at double speed,**
- **D-12: The `research:12` gate dispositions.**
- **D-13: Budgets, frames and the trace stay in master half-dots.**
- **D-14: No public ABI change.**
- **D-15: The player is unchanged**
- **D-16: Installed consumers (C and C++) run the speed fixture in partitions through `gbb_run`**
- **D-17: Docs are updated in-phase:**
- **D-18: Reset clears `double_speed`, the stall and `key1_armed`**
- **D-19: Admit 13 AGE ROMs under `fixtures/age/`**
- **D-20: The AGE protocol is Mooneye-style**
- **D-21: Stall sensitivity sweep.**
- **D-22: Original fixture `fixtures/cgb-speed/`**
- **D-23: Other suites.**
- **D-24: Dispositions go in a new `tests/external/cgb-speed-dispositions.json`.**
- **D-25: Mutant set.**
- **D-26: Partition test `cgb_partition_*`.**
- **D-27: Fuzz.**
- **D-28: Headroom test.**
- **D-29: ASan/UBSan budget (GB-CI-004).**
- **D-30: Benchmark is advisory only.**
- **D-31: Every plan SUMMARY `coverage:` block uses the GSD block schema**
- **D-32: Wave order.**
- **D-33: Double speed and HDMA do not run in parallel (ROADMAP).**
- **D-34: Wake is sampled only at CPU M-cycle boundaries during the stall.**
- **D-35: The CGB-E one-M-cycle quirks are named expected failures by default.**
- **D-36: The held-button rule (D-02 case 1) applies to the armed path only in Phase 12.**

### Claude's Discretion
- Internal names, and whether `cpu_stall_kind` is an enum or a `uint8_t`.
- The fixture ROM layout and probe line counts within D-22.
- Merging mutants to save compiles.
- Plan granularity within the D-32 waves.

### Deferred Ideas (OUT OF SCOPE)
- **Phase 13:** HDMA during the stall (`expected-failure:speed-switch-hdma-hblank-across-stall` until then), attached to `cpu_stalled()`.
- **Phase 14:** GATE-41/GATE-62 DMG STOP wake research, `spsw-ch2-lc-delay`, the SameSuite KEY1/PCM ROMs, CGB mode-3 length (`spsw-mode0` SCX rows, ds STAT fallbacks), and the STOP-triggered OAM bug (`expected-failure:speed-switch-stop-oam-bug`).
- **v0.3:** save-state serialisation of the D-17 field list.
- **Future:** a public speed getter for debuggers or an OSD (additive).

### Owner veto window (from CONTEXT, unchanged)
D-05 stall length; D-02/D-08 hostile cases follow SameBoy and are tagged UNKNOWN; D-19 vendoring 13 AGE ROMs (about 416 KiB) into required CI; D-14 no public speed getter or stop reason; D-09 alignment policy; D-02 case 1 held button sends the CPU into HALT; D-12 deferral of GATE-41 and the DMG/unarmed part of GATE-62 to Phase 14; D-26 reduced partition sweep.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CGB-06 | CGB software can switch to double speed via KEY1 and STOP: CPU, timer, serial and OAM DMA run at twice the rate while PPU and APU timing are unchanged, the switch pause is modelled, and partitioned runs stay equivalent. | Code Map (sections A-G) names every conversion site; "Evidence against locked decisions" fixes the stall constant with measured AGE windows; Validation Architecture maps all three roadmap success criteria and every D-xx to named CTests with negative controls; the prototype passed the full existing suite and `spsw-div`/`spsw-stop-prefetch` (see AGE table). |
</phase_requirements>

## Project Constraints (from AGENTS.md)

There is no CLAUDE.md; `AGENTS.md` is authoritative. Directives that bind this phase:

- Original portable C core, explicit ownership and error behaviour, bounded public operations, no hidden globals. Host timing, filesystem and UI stay in adapters. [VERIFIED: AGENTS.md "Engineering rules"]
- Stop after each phase. Never auto-advance. Keep `workflow.auto_advance` and `workflow._auto_chain_active` false. Handoff must name the stage, the next phase by number and title, and one copy-paste GSD command; persist it in STATE.md. [VERIFIED: AGENTS.md "Workflow contract"]
- D-069: every deliverable gets an automated check with a negative control; `/gsd-verify-work` needs zero human checkpoints. Plan SUMMARY `coverage:` entries use the GSD block schema (`id`, `description`, `human_judgment`, block-style `verification` items with `kind` unit/integration/e2e/automated_ui/other, `ref`, `status: pass`; no flow items, no `ctest` kind, no inline `#` comments); the `summary_coverage` CTest rejects anything else. [VERIFIED: AGENTS.md]
- Phase branches and PRs when a remote exists; merge only the reviewed/tested revision with required checks satisfied (memory: squash merge when exact-head CI is green, pre-authorized). Keep main releasable; update source, API docs, examples, tests and limitation notes together.
- Guard ROM/save/state boundaries against overflow, truncation, excess allocation/work and partial mutation (drives the D-28 headroom pre-check below). Distinguish hardware-backed tests, differential oracle results, metamorphic properties, regression fixtures and private observations; declare model applicability, exclusions and expected-failure reasons.
- No Nintendo boot ROMs, commercial images, unlicensed homebrew. Every third-party fixture needs documented redistribution rights and a digest (drives `fixtures/age/` rights files and the install-scan guard).
- Prefer copy over dependency (memory): small helpers are copied (xorshift, dispositions verifier, `check_no_phase12_rows.cmake`), no new libraries or Actions.
- Keep `.planning/context/DECISIONS.md` (next free id is D-084), `LESSONS.md`, `research/INDEX.md` current. [VERIFIED: DECISIONS.md rows D-083 is last]

## Summary

Everything in D-01..D-36 is implementable inside the current architecture without an ABI change. The core already has one clock (`time_half_dots`), one device scheduler (`advance_devices_to`, `src/core/gabbaboy.c:2833-2923`) and a run loop (`gbb_run_internal`, `:3914-4053`) whose HALT branch is the exact shape the stall branch should copy. A scratch prototype that applies `cpu_ticks` scaling at five sites (instruction cost, `bus_read`/`bus_write` offsets, `enter_interrupt`, the interrupt/halt literals, and tick-unit countdowns for timer reload, serial and OAM DMA), moves the APU tap, and adds a stall branch passed 680 of the 686 registered CTests **with no test edits**, including `dmg_baseline`, every Mooneye timer/serial/DMA case, libbet acceptance and the tracer digest `4c7a57ff3d50d228` (the six failures were the expected `cgb_stop_armed_cgb` flip, three model-gate tests that reject untagged new helper functions, and two summary-coverage tests that failed only because the scratch copy omitted `.planning/phases`). Normal-speed behaviour is therefore byte-identical under D-10's tick-unit countdowns. [VERIFIED: prototype]

Two findings change planning and are written up under "Evidence against locked decisions": (1) the literal D-05 constant `0x20008` makes `spsw-div-cgbBCE` fail 0/5 in the exact D-02/D-06/D-10 model, while `0x20004..0x20007` passes 5/5, so the named constant must be derived (D-05 itself says the binding quantity is the DIV-reset-to-resume distance) and `0x20004` (32769 M-cycles) is the clean choice; (2) the player text surfaces "double speed ... not claimed or implemented" in five places, so "player unchanged" cannot include `limitations.h`. The prototype also shows that only `spsw-div` and `spsw-stop-prefetch` pass among the AGE speed ROMs; the other 11 are expected-failure candidates and the three single-speed STAT controls already fail on current main, so Wave 5 should be planned as "pin signatures and dispositions", not "make ROMs pass".

**Primary recommendation:** Lead with a tracer plan that adds `double_speed`/stall fields, KEY1 readback, a minimal case-4 switch, `divider_reset()`, the five `cpu_ticks` sites and a minimal stall branch, flips `cgb_stop_armed_cgb`, and proves it with one white-box test plus a runtime-selected mutant; vendor the AGE ROMs on an independent track from day one (needs no core code, and it is the only way to learn the Linux RGBDS digests early).

## Evidence against locked decisions

These are concrete conflicts between a locked decision and evidence gathered this session. Each lists a recommended resolution that stays inside the spirit of the decision. None is acted on without owner/planner confirmation; items E1-E3 should be recorded in DECISIONS (D-084+).

**E1. D-05 literal constant and D-02 "STOP is 1 M".** [VERIFIED: prototype] A stall counted from the DIV reset at STOP retire (D-02 case 3, D-06) with the literal 0x20008 T at the destination speed fails `spsw-div-cgbBCE`. Sweep of the stall in T (identical for STOP = 1 M and STOP = 2 M on this ROM):

| stall T | 0x20000 | 0x20002 | 0x20003 | **0x20004** | **0x20005** | **0x20006** | **0x20007** | 0x20008 | 0x20009 | 0x20104 |
|---|---|---|---|---|---|---|---|---|---|---|
| `spsw-div` rows ok | 0/5 | 0/5 | 0/5 | **5/5** | **5/5** | **5/5** | **5/5** | 0/5 | 0/5 | 0/5 |

The pass window is exactly four T wide, `[0x20004, 0x20007]`. `0x20004` is `0x20008` minus the 4 T that SameBoy's `div_cycles` quirk removes when IME = 0 (CONTEXT D-05 names the quirk), and it is the only M-aligned value in the window: 131076 T = 32769 M-cycles, so a stall of whole M-cycle steps (D-06, D-34) ends exactly at a CPU boundary in both directions (131076 half-dots to double, 262152 to normal). The D-09 realignment does not move this window. The D-21 "stall ±1 M" mutants (`0x20000`, `0x20008`) both fail `spsw-div`, so the mutant discriminates; a "+1 half-dot to double" mutant (`0x20005`) stays inside the window and is NOT detected by AGE (record as a named insensitivity: the low two bits of the constant are not evidenced).
**Recommendation:** keep the name `GBB_SPEED_SWITCH_STALL_T`, set it to `0x20004`, derive it in `docs/cgb-profile.md` as "SameBoy 0x20008 minus the 4 T SameBoy removes at IME = 0, pinned by the AGE `spsw-div` window [0x20004,0x20007]", add `_Static_assert(GBB_SPEED_SWITCH_STALL_T % GBB_T_PER_M == 0, "half-dot timeline: ...")` plus a static-assert mutant in the style of `cgb_adr_half_dot_static_assert_mutant`, and update the D-05 figures (131080/262160 become 131076/262152; line counts about 143.7/287.5 are unchanged to the first decimal). This is D-05's own "binding requirement" clause applied, not a reversal.

**E1b. STOP length on the switch path.** [VERIFIED: prototype] Making STOP cost 2 M (16 half-dots at normal speed) on the switch path, with the DIV reset still at retire and the stall still `0x20004`, moves `spsw-tima-cgbBC` from 4/8 to 7/8 rows and changes `spsw-tima-cgbE` from 6/8 to 5/8; `spsw-div`, `spsw-stop-prefetch` and `spsw-interrupts-cgbE` (9/11) do not move. SameBoy's STOP is 2 M; D-02 states GabbaBoy's is 1 M (`:3581`). The B/C rows are fully explained by 2 M; the remaining `tima-cgbBC` failure is the 4 KHz 1-to-0 edge (row 2), and the `tima-cgbE` failures are rows 2, 6, 7 (the D-35 class). **Recommendation:** treat "STOP cost on the armed switch path" as an explicit, named, tested choice (default: 2 M, decode cost 16 for D-02 cases 3 and 4 only; DMG/unarmed/compat STOP stays 8 so the DMG baseline is untouched). If the owner prefers D-02's literal 1 M, nothing else changes and the `tima` rows pin different signatures.

**E2. D-15 "The player is unchanged (`session.c`, `audio.c`, `limitations.h`)".** [VERIFIED: src/player/limitations.h:5] The pinned limitations text contains: `CGB mode-3 timing, double speed and HDMA are not claimed or implemented`. The same claim sits in `README.md` (line 11 paragraph), `.github/workflows/preview.yml` (two `capability_limits` strings, lines 51 and 98), and the `Claims:` help text at `src/player/main.c:401`. After Phase 12 the statement is false for double speed. It is pinned verbatim by `player_limitations` (`tests/player/test_limitations.c:8`) and cross-checked by `player_claims_agree` (phrase list `no colour correction`, `DMG APU model`, `--model auto|dmg|cgb`, `no palette flag`, `CGB mode-3 timing` at `tests/player/CMakeLists.txt:381-383`). Neither list contains "double speed", so nothing machine-checks that phrase. **Recommendation:** "player unchanged" means no functional change to `session.c`/`audio.c`/`main.c` logic; a claims-only edit to those five surfaces (drop "double speed", keep "CGB mode-3 timing ... and HDMA are not claimed or implemented") is required, edited atomically with `test_limitations.c`, and add one phrase to the claims-agree list so the new wording is agreed everywhere. Because player tests only run on the macOS player job, make this its own task with the player job as its verification.

**E2b. D-15 "pins the RGBA frame digest and the audio digest".** [VERIFIED: src/player/main.c:2332-2420] `--smoke-colour` runs 30 frames (`PLAYER_COLOUR_SMOKE_FRAMES`), clears audio each frame (`player_audio_clear`) and prints `rgba_sha256`, `distinct`, `title_token` and 40 hard-coded spot pixels for `colour-attr.gb`. It computes no audio digest. **Recommendation:** the player-level `player_cgb_speed_smoke` pins the RGBA digest only (new `GBB_CHECK=speed` branch in `tests/player/cgb_smoke.cmake` that ignores the 40-spot grid); the audio-digest and "APU at 2x"/"PPU follows CPU" mutants are verified at core level through `gbb_run_audio` over the same fixture (`cgb_speed_fixture_audio_digest`). A player-binary core mutant is possible with the existing trick (mutant static library listed before `gabbaboy_accept`, player sources compiled directly) but costs a macOS-only build of seven player sources per mutant; keep it to the PPU-follows-CPU mutant if the owner wants a literal D-15 control.

**E3. D-02 "the APU edge included" in a helper shared by both STOP paths vs D-01 "DMG-profile STOP path stays byte-identical".** [VERIFIED: src/core/gabbaboy.c:1951-1957 and :4036-4044] Today the DIV-write reset clocks the sequencer on a falling edge (`if (apu_falling_edge) apu_sequencer_clock(m);`) and the GATE-65 STOP reset does not. A shared helper that always clocks the APU would change the DMG sleep path. **Recommendation:** `static void divider_reset(gbb_instance *m, int clock_apu_edge)`; the DMG/unarmed STOP passes 0 (byte-identical), the DIV write and the armed switch pass 1. Evaluate the edge with the tap of the speed in effect BEFORE the flip (call the helper before toggling `double_speed`), otherwise the sequencer can clock spuriously at the switch.

**E4. D-28 "run must return INVALID_STATE with no mutation" before a switch near `UINT64_MAX`.** The instruction path only checks `UINT64_MAX - time_half_dots < cost` (`:4011`), i.e. 8 half-dots; the stall would then fail after the switch had already mutated state. **Recommendation:** for D-02 case 4 add a pre-check at the STOP preflight that the headroom covers `cost + GBB_SPEED_SWITCH_STALL_T * 2 + 4` (worst case to-normal plus the D-09 extension) and return `GBB_STOP_INVALID_STATE` before any mutation; the stall branch keeps its per-step check as defence in depth. The prototype lacks this; M9/D-28's mutant is "drop the pre-check".

**E5. D-16 "Installed consumers ... run the speed fixture".** [VERIFIED: cmake/RunInstalledConsumer.cmake] The installed-consumer tests only receive `share/gabbaboy/fixtures/tracer/tracer.gb`, and the install scan allows only the `tracer`, `visible-demo`, `mbc1-continuation` fixture directories. `fixtures/cgb-speed` is not installed. **Recommendation:** each consumer builds a ≤40-byte guest inline (as `cgb_api_smoke` already does at `tests/consumers/c/main.c:69-76`), runs it in partitions through `gbb_run`, and checks `consumed_half_dots`, the stop reason and frame generation. Do not widen the install allow-list for a test input (D-055 precedent).

**E6. D-27 "A libFuzzer dictionary entry".** No `.dict` file or `-dict=` argument exists today (`tests/scripts/run-bounded-fuzz.sh`). It is new, tiny infrastructure: `tests/fuzz/fuzz_core.dict` plus `-dict=` on the two `fuzz_binary` invocations; keep the `FUZZ_RUN_LIMIT UINT64_C(2048)` and `FUZZ_INPUT_HALF_DOT_LIMIT UINT64_C(8192)` defines unchanged because `run-bounded-fuzz.sh --self-test` greps them; the speed mode needs its own larger limit define (precedent: `FUZZ_PALETTE_HALF_DOT_LIMIT`), since one stall is 131076 half-dots.

**E7 (informational). D-29 timings.** Measured here: 22 ns/half-dot Debug (`measure_core`, Apple silicon), about 92 ns/half-dot for an ad-hoc `-O0 -fsanitize=address,undefined` build; CONTEXT's 47 ns is a plausible hosted-Linux Debug figure. The partition test is feasible only with early-truncated windows and a white-box-seeded short stall (Validation Architecture, "Partition feasibility").

## Architectural Responsibility Map

The "tiers" of this project are not web tiers; they are the layers named in AGENTS.md.

| Capability | Primary tier | Secondary tier | Rationale |
|------------|--------------|----------------|-----------|
| KEY1 arm/readback, STOP decision table, speed flip, stall state | Core (`src/core/gabbaboy.c`) | Docs/gate table | Guest-visible hardware behaviour; the host sees only KEY1 bit 7 (D-14). |
| `cpu_ticks` scaling of cost, bus offsets, timer/serial/DMA countdowns | Core device scheduler (`advance_devices_to`, `bus_read`/`bus_write`, run loop) | - | One master clock; only CPU-side devices scale (D-10, D-070). |
| PPU, APU channels, PCM sample clock, RTC | Core, unchanged | Structural check script | Must never read `double_speed`; enforced by a scanner plus mutants (M1, M12). |
| Budget semantics (`consumed_half_dots`, `GBB_STOP_BUDGET` mid-stall) | Core run loop | Public header comments | Hosts rely on BUDGET vs HALTED_IDLE (`src/player/main.c:652`). |
| Hardware-ROM oracle verdicts (AGE) | Test tier (`tests/test_age.c`, manifest, dispositions JSON) | CI fixture-repro | Third-party bytes, rights files, digest-pinned rebuild. |
| Original fixture and first-principles expectations | Test tier (`fixtures/cgb-speed`, `derive-cgb-speed-expectations.py`) | Fixture-repro workflow | Derivation never reads the emulator (D-22). |
| Player claims text | Player adapter surfaces (`limitations.h`, README, `preview.yml`, help text) | Claims-agree test | Evidence in E2. |
| Installed-consumer partition check | Consumers (`tests/consumers/{c,cpp}/main.*`) | - | Inline guest, public API only (E5). |

## Standard Stack

No new libraries, submodules, Actions or package installs (STACK.md rule, copy-over-dependency memory).

### Core
| Component | Version | Purpose | Why standard here |
|-----------|---------|---------|-------------------|
| ISO C17 + CMake/CTest/Ninja | CMake >= 3.25 floor (local 4.4.3), Ninja 1.13.2 | Core and every test | Existing; `cmake-3.25.3` preset enforces the floor [VERIFIED: CMakePresets.json] |
| RGBDS | **1.0.1** (pinned; macOS zip SHA-256 `2f6f13c6ec984313656c07b08d97dfcd3a471c7d3901d3ff486e5814bb503645`, Linux x86_64 `80a5cad8dae27e24e46a93041352c47cadbc165103983f41c2b3082c42f6dad9`) | Original fixture and AGE rebuild | Pin lives in every `fixtures/*/manifest.json`; the host has Homebrew 1.0.4, which must NOT be used (bytes could differ) [VERIFIED: fixtures/cgb-colour/manifest.json; `rgbasm --version` = v1.0.4 on PATH] |
| Python 3 stdlib, run `python3 -I` | 3.14.4 local | Expectation derivation, dispositions verifier, structural scanner | Project norm [VERIFIED: tests/CMakeLists.txt `Python3_EXECUTABLE -I`] |
| CMake `-P` scripts + `expect_exit.cmake` | - | Negative controls with exact exit codes | Existing [VERIFIED: tests/expect_exit.cmake] |
| `src/accept` (`gbb_accept_sha256_hex`, PCM/RGB digests) | - | Digests in test drivers | Existing; no new hash code |

### Supporting
| Item | Purpose | When to use |
|------|---------|-------------|
| `cmake/VerifyFixtureManifest.cmake` | Size + SHA-256 of every `fixtures[]` row, files resolved next to the manifest | `age_fixture_digest`, `cgb_speed_fixture_digest` |
| `cmake/ScanForbiddenFixtures.cmake` | Install-tree redistribution scan by size and digest | `age_not_installed` (+ selftest) |
| `cmake/VerifyDocContract.cmake` | Every `gbb_*`/`GBB_*` identifier in a doc must be declared; required phrases | Doc edits (see Pitfall 11) |
| `tests/check_no_phase11_rows.cmake` | Template to copy for `check_no_phase12_rows.cmake` | `model_gates_no_phase12_rows` |
| SDL3 3.4.18 (player job only) | Player smoke | `player_cgb_speed_smoke` |

### Alternatives Considered
| Instead of | Could use | Tradeoff |
|------------|-----------|----------|
| One mutant core build per mutant (Phase 7-11 pattern) | One runtime-selected mutant mask in a single mutated copy (recommended) | 1-2 builds instead of up to 17; every mutant keeps an exactly-once anchor and its own named CTest; the same executable passes with mask 0 (stronger in-mutant control). Costs one small generator function. |
| New 4th runner suite for AGE | Dedicated `tests/test_age.c` driver using the same `LD B,B` convention | Runner suites are admitted by manifest SHA-256 and print Mooneye-specific receipt fields (`src/runner/main.c:334-367`); a driver avoids coupling and can read WRAM for the D-20 signature. |
| `gbb_runner_capture_ldbb` | Plain loop with `gbb_run` + trace for opcode `0x40` | The capture helper copies a frame per 2048-half-dot chunk; the plain loop is cheaper and enough. |

**Installation:** none. Pinned RGBDS for fixture work: download `rgbds-macos.zip` v1.0.1 (digest above) into a scratch directory and put it first on `PATH`; CI uses the Linux archive named in the manifests.

**Version verification:** local toolchain read this session: cmake 4.4.3, ninja 1.13.2, python 3.14.4, Apple clang 21.0.0, bash 5.2.37, git 2.41.0. RGBDS 1.0.1 was verified by SHA-256 of the archive and `rgbasm v1.0.1` before building the AGE ROMs.

## Package Legitimacy Audit

This phase installs no external packages. The only third-party inputs are (a) the RGBDS 1.0.1 archives already pinned by digest in six existing manifests and (b) source files from `c-sp/age-test-roms` at commit `1f5bc10e2cb60b86c19f8d0287ff78f410c4f639` (git tree `2fece1a678edb18c1664efd7328a430a79c70be4`, fetched into a clean directory and the HEAD/tree hashes compared this session). No `gsd-tools package-legitimacy` run is applicable.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| (none) | - | - | - | - | - | - |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Code Map (core, current HEAD `a719721`)

All line numbers are from `src/core/gabbaboy.c` read this session unless another path is given.

### A. State
- Struct `gbb_instance` spans `:323-450`. KEY1 storage: `uint8_t key1_armed, bcps, ocps, ff72, ff73, ff74, ff75;` (`:341`); its comment at `:338-340` ("the speed switch is not built; STOP ignores it") is stale. CPU run flags: `int halted, stopped, halt_bug;` (`:420`). Divider: `uint8_t divider_phase;` (`:391`), `uint16_t divider_counter;` (`:392`). Countdowns: `uint8_t timer_reload_remaining;` (`:409`), `uint16_t serial_edge_remaining;` (`:412`). Clock: `uint64_t time_half_dots;` (`:422`).
- **Add after `:420`:** `uint8_t double_speed, cpu_stall_kind, stop_switch_pending; uint32_t cpu_stall_half_dots;` (`stop_switch_pending` carries the D-02 case from `execute()` to the retire block; a run-loop local is not possible because `execute()` returns void).
- ABI neutrality: the instance is opaque and allocated with `calloc(1, sizeof(*m))` (`:3207`); the only `offsetof` uses are the APU wave reset (`:1519-1521`); `GBB_INFO_SIZE_V1` guards `gbb_info`, not the instance. Adding fields changes no public size. `cgb_consumer_symbol_coverage` is unaffected because no public symbol is added. [VERIFIED: grep + reads]
- `cpu_stall_kind` values (recommended): `NONE=0`, `SPEED_SWITCH=1`, `SWITCH_REALIGN=2` (D-09's 4-half-dot tail must NOT be cut short by the wake check; see Pitfall 8). Provide `static int cpu_stalled(const gbb_instance *m)` for Phase 13.

### B. Every place that converts master half-dots to CPU time today

| # | Site (lines) | Current text (verbatim) | Change |
|---|--------------|-------------------------|--------|
| 1 | `instruction_cost` `:3599` | `static uint8_t instruction_cost(const gbb_instance *m, decoded d) { (void)m; return d.ticks; }` | `(uint8_t)(d.ticks >> m->double_speed)`; all `decoded.ticks` are multiples of 8 (8..48 at `:3560-3595`) so the shift is exact |
| 2 | `bus_read` `:1696` | `advance_devices_to(m, m->instruction_start_half_dots + offset);` | `+ (offset >> m->double_speed)`; every literal offset in `execute`/`push16`/`pop16` is a multiple of 8 |
| 3 | `bus_write` `:2090` | `uint64_t timestamp = m->instruction_start_half_dots + offset;` | same shift |
| 4 | `bus_write` TMA coincidence `:2092-2093` | `timestamp - m->time_half_dots == m->timer_reload_remaining)` | compare against `timer_reload_hd(m)`; omitting this silently mixes tick and half-dot units |
| 5 | `enter_interrupt` `:3867` | `advance_devices_to(m, m->instruction_start_half_dots + 8u);` | `(8u >> m->double_speed)` (the pushes at `:3871` go through `bus_write`) |
| 6 | interrupt entry in the run loop `:3948-3961` | `if (40u > budget_half_dots - result.consumed_half_dots) return result;` / `audio_preflight(instance, 40u)` / `UINT64_MAX - instance->time_half_dots < 40u` / `+ 40u` / `result.consumed_half_dots += 40;` | one local `irq_cost = 40u >> double_speed` |
| 7 | HALT branch `:3976-3983` | `if (budget_half_dots - result.consumed_half_dots < 8u) return result;` ... `advance_devices(instance, 8u);` `result.consumed_half_dots += 8u;` | one local `m_cycle = 8u >> double_speed` |
| 8 | TIMA reload start `:1720` | `m->timer_reload_remaining = 8u;` | `4u` (CPU T-ticks) |
| 9 | TIMA reload countdown `:2838-2839` | `if (m->timer_reload_pending && m->timer_reload_remaining != 0 && --m->timer_reload_remaining == 0) {` | gate on `cpu_tick` |
| 10 | serial start `:1985`, reload `:2857` | `if (value & 1u) m->serial_edge_remaining = 1024u;` / `m->serial_edge_remaining = 1024u;` | `512u` |
| 11 | serial countdown `:2849-2850` | `m->serial_edge_remaining != 0 && --m->serial_edge_remaining == 0) {` | gate on `cpu_tick` |
| 12 | OAM DMA byte period `:26`, `:2750` | `#define GBB_DMA_BYTE_PERIOD_HALF_DOTS 8u` / `if (++m->dma_phase < GBB_DMA_BYTE_PERIOD_HALF_DOTS) return;` | count `dma_phase` in CPU ticks (period 4), call only on `cpu_tick` (`:2919`); `:212-213` static assert stays true if the macro keeps its meaning; docs name the macro (`docs/cgb-profile.md:638`) |
| 13 | divider `:2860-2869` | `m->divider_phase ^= 1u;` then `if (m->divider_phase == 0) {` ... `(m->divider_counter & 0x1000u)` | normal speed: toggle phase, tick on phase 0; double speed: tick every half-dot; tap `0x1000` -> `0x2000` |
| 14 | DIV write `:1951-1957` | `int apu_falling_edge = (m->divider_counter & 0x1000u) != 0u;` | move into `divider_reset()` with the speed's tap |

**Must stay in master time (never read `double_speed`):** PPU stepping `:2920-2921` (`m->ppu_half_phase ^= 1u; if (m->ppu_half_phase == 0) ppu_advance_dot(m);`), APU channel timers `:2870-2901`, `apu_sample_phase`/PCM `:2902-2918`, RTC (`rtc_*`, anchored on `time_half_dots`), frame length (`GBB_DOTS_PER_LINE * GBB_LINES_PER_FRAME * GBB_HALF_DOTS_PER_DOT == 140448u`, `:210`).

**`advance_devices_to` restructure (prototype, passes the full suite):**
```c
if (!m->double_speed) m->divider_phase ^= 1u;                      /* toggle moved to the top of the iteration */
const int cpu_tick = m->double_speed || m->divider_phase == 0;     /* P12-M3 */
if (cpu_tick && m->timer_reload_pending && m->timer_reload_remaining != 0 &&
    --m->timer_reload_remaining == 0) { /* unchanged body */ }
if (cpu_tick && m->serial_active && (m->serial_control & 1u) != 0 &&
    m->serial_edge_remaining != 0 && --m->serial_edge_remaining == 0) { /* unchanged body, reload 512u */ }
if (cpu_tick) {                                                    /* was: toggle then if (phase == 0) */
    const uint16_t tap = m->double_speed ? 0x2000u : 0x1000u;      /* P12-M4 */
    const int apu_signal_before = (m->divider_counter & tap) != 0u;
    ++m->divider_counter; m->div = (uint8_t)(m->divider_counter >> 8);
    timer_set_signal(m, timer_input(m), m->time_half_dots);
    if (apu_signal_before && (m->divider_counter & tap) == 0u) apu_sequencer_clock(m);
}
/* APU channels, PCM, then */ if (cpu_tick) dma_advance_half_dot(m);   /* P12-M14 */
m->ppu_half_phase ^= 1u; if (m->ppu_half_phase == 0) ppu_advance_dot(m);    /* P12-M1 anchor: never reads double_speed */
```
Why moving the toggle is safe: at normal speed every device-visible write happens at an even offset from `instruction_start_half_dots`, and every reset of the phase (`divider_reset`, post-boot) happens at a tick boundary, so a countdown loaded at a tick fires the same half-dot as before (8 half-dots = 4 ticks). The full suite including `dmg_baseline` confirmed this empirically. [VERIFIED: prototype]

### C. Run loop (`gbb_run_internal`, `:3914-4053`)
Branch order today: locked `:3920`; stopped `:3921-3945`; interrupt dispatch `:3946-3969`; halted `:3970-3990`; fetch/decode/execute `:3991-4050`. The D-06 stall branch goes **between stopped and interrupt dispatch**, copying the HALT branch (not the stopped branch). Quotes to preserve: `GBB_STOP_NO_PROGRESS` is assigned only at `:3941` (`result.reason = GBB_STOP_NO_PROGRESS;`), inside the stopped branch.
```c
if (cpu_stalled(instance)) {                                      /* P12-M13/M16: wake check here, per step */
    if (stall_kind == SPEED_SWITCH && (ie & interrupt_flags & 0x1Fu) != 0) { end_stall(instance); continue; }
    const uint64_t quantum = instance->double_speed ? 4u : 8u;     /* one CPU M-cycle */
    const uint64_t step = stall < quantum ? stall : quantum;       /* last step may be shorter (D-09 tail = 4) */
    if (budget_half_dots - result.consumed_half_dots < step) return result;           /* BUDGET, consumed unchanged */
    if (!audio_preflight(instance, step)) { result.reason = GBB_STOP_OUTPUT_FULL; return result; }
    if (UINT64_MAX - instance->time_half_dots < step) { result.reason = GBB_STOP_INVALID_STATE; return result; }
    advance_devices(instance, step); instance->cpu_stall_half_dots -= (uint32_t)step; /* P12-M7 freezes this */
    result.consumed_half_dots += step;
    if (stall == 0) finish_stall_into_realign_or_end(instance);   /* D-09 */
    else if (wake) end_stall(instance);
    continue;
}
```
The switch itself is applied in a new block after `:4035` (`if (instance->ime_delay != 0 && --instance->ime_delay == 0) instance->ime = 1;`) and before the GATE-65 block at `:4036-4044`, so `EI; STOP` retires its IME delay first (D-08). Applying it before `advance_devices_to(instance, instance->instruction_start_half_dots + cost)` would be wrong: the STOP cycle must still elapse at the old speed.

### D. STOP decode and execute
- Decode `:3581`: `return (decoded){(uint8_t)(op == 0x10 ? 2 : 1), (uint8_t)((op == 0xC9 || op == 0xD9) ? 32 : 8), 1};` - size 2, cost 8 for all paths today.
- Execute `:3814-3823`: the `UNKNOWN GATE-62 research:12` tag, the `CGB_ONLY GATE-74` tag and the latch (`m->bus_unsupported=1; m->bus_unsupported_address=0xFF4Du;`), then the shared `m->pc=(uint16_t)(pc+2); m->stopped=1; break;`.
- Add `static int stop_case(const gbb_instance *m)` returning 0 (DMG/unarmed/compat path, unchanged), 1 (held button, nothing pending: operand fetched, enter existing HALT, KEY1 stays armed), 2 (held button, pending: 1 byte, no halt), 3 (armed, pending, switch without stall, 1 byte), 4 (armed, switch with stall, 2 bytes). Held test is `(joypad_value(m) & 0x0Fu) != 0x0Fu` (`joypad_value` at `:1451`); pending is `(m->ie & m->interrupt_flags & 0x1Fu) != 0`. **Call it from both `decode()` and `execute()`** so `d.size` (which feeds `instruction_reads_supported`, `:3615-3616`: `for (unsigned i = 0; i < d.size; ++i) if (!read_supported(m, instruction_address(m, m->pc, i))) return 0;`) and the trace record's `opcode_size` (`save_trace`, `:3877-3882`) agree. Nothing advances between decode and execute, so both calls see the same IE/IF/P1.
- D-04's FF04 fetch is allowed: `io_visibility` rows `0x04..0x07` are `IO_EXISTING_ROW` (`:1136-1139`) and the CGB branch of `read_supported_map` returns `io_cgb_cell(m, address)->kind != IO_DEFERRED_RW` (`:2103-2104`). The prototype passes `spsw-stop-prefetch-cgbBCE` (STOP executed from FF04). [VERIFIED: reads + prototype]

### E. Shared DIV reset
- DIV write today (`:1951-1957`): clears counter/div/phase, `timer_set_signal(m, timer_input(m), m->time_half_dots)`, then clocks the sequencer on the old tap's falling edge.
- GATE-65 today (`:4036-4044`): same first three statements plus `timer_set_signal(...)`, then `result.reason=GBB_STOP_STOPPED; return result;` - no APU edge.
- New: `static void divider_reset(gbb_instance *m, int clock_apu_edge)` (see E3). Tag `GATE-31` (DIV write) and `GATE-65` rows against the helper's call sites; the helper itself takes a `GATE-00 BOTH basis=` function tag.

### F. Reset
`reset_state` `:1378-1448`: `m->halted = 0;` (`:1411`) `m->stopped = 0;` (`:1412`) `m->halt_bug = 0;` (`:1413`). Add `double_speed`, `cpu_stall_kind`, `cpu_stall_half_dots`, `stop_switch_pending` and `key1_armed` in this block (D-18). `key1_armed` is also written by `post_boot_apply` (`case PB_KEY1: m->key1_armed = v; break;`, `:1037`) but the explicit clear keeps the test independent of the table. `reset_state` is called from `gbb_create`, `gbb_reset` and `gbb_load_rom` (`:3212`, `:3238`, `:3279`).

### G. KEY1 and table mirrors
- Read `:1328` `case IO_KEY1: return (uint8_t)(0x7Eu | (m->key1_armed & 1u));` -> add `((m->double_speed & 1u) << 7)`. Write `:1348` `case IO_KEY1: m->key1_armed = (uint8_t)(value & 1u); break;` is correct as is.
- Table row `:1209`: `[0x4D] = { IOC(DMG_STOP), IOC(KEY1), IOC(CONST_FF), IOS_PANDOCS }, /* KEY1: speed switch; only the armed bit is kept, no double speed is built */` - update the comment.
- The doc mirror text is generated from C: `tests/test_cgb_tables.c:288` `case IO_KEY1: snprintf(rd, rd_n, "$7E or armed bit"); snprintf(wr, wr_n, "bit 0 arms the switch"); return 1;` must change together with `docs/cgb-profile.md:302` (`| $FF4D | CGB | $7E or armed bit | bit 0 arms the switch | IMPL | PANDOCS |`), otherwise `cgb_tables_io` fails. KEY0: row `:1208` reads `$FF`, writes ignored; D-03's "KEY0 can never change speed" is a test, not code.

### H. Input and wake
`apply_input_events_now` (`:2150-2173`) runs from `advance_devices_to` every half-dot (`:2836`) and at run start (`:3918`). Button events only latch IF through `joypad_request_falling_edge` (`:2163-2170`); `GBB_INPUT_STOP_WAKE` acts only `if (m->stopped && event.value == 1u)` (`:2160`), so the stall never needs a STOP_WAKE path (D-06 "never sets stopped").

### I. Test seam
`src/core/gabbaboy_test.h` declares only `gbb_test_last_unsupported_address`; other seams (`gbb_test_cpu_snapshot`, `gbb_test_bank_state`) are `extern`-declared in test files. Add `gbb_test_speed_state(const gbb_instance *, uint8_t *double_speed, uint8_t *stall_kind, uint32_t *stall_half_dots, uint8_t *key1_armed)` to the header so public-API tests, the fuzz target and consumers-of-seams can read the state without struct access (D-14 stays true: private, not installed).

## Test Infrastructure Map

### Registration and inventory
- Every test is `add_test` in `tests/CMakeLists.txt` (2498 lines; core inventory 691 names in `tests/expected-tests.txt`). The last statement calls `gabbaboy_verify_registered_tests()` (`cmake/ExpectedTests.cmake:7-28`), which sorts both sets and aborts configure on any difference. [VERIFIED: reads]
- `cmake/ExpectedTests.cmake:16-21` removes bash-only tests on Windows: `if(WIN32) list(REMOVE_ITEM expected_tests cgb_bench_ab_selftest ... cgb_colour_repro_tool_failure cgb_colour_repro_missing_pin)`. **Every new bash-only test (`age_repro_*`, `cgb_speed_repro_*`) must be added to that list** or the Windows leg fails at configure. Installed tests are removed when `GBB_TEST_INSTALL_PREFIX` is empty (`:11-15`).
- Player inventory: `tests/player/expected-tests.txt` (93 lines) is consumed by an `if/elseif` chain in `tests/player/CMakeLists.txt` that ends `message(FATAL_ERROR "Unknown player_cgb_ test in inventory: ${test_name}")` (`:181`); each new `player_cgb_*` name needs its own branch. The player job runs only with `GABBABOY_BUILD_PLAYER` (macOS, SDL3 3.4.18 `EXACT`).
- Parallel-safe editing convention from Phase 11: `# --- Phase 11 plan 11-NN begin ---` / `# --- Phase 11 plan 11-NN end ---` blocks (e.g. `tests/CMakeLists.txt:1916`, `:2033`). Use `# --- Phase 12 plan 12-NN begin/end ---`; append `expected-tests.txt` lines as one contiguous block per plan.
- Sanitizer timeouts: the tail of `tests/CMakeLists.txt` multiplies every explicit `TIMEOUT` by 3 when `GABBABOY_ENABLE_SANITIZERS` is on (LESSONS GB-CI-004). Tests without an explicit TIMEOUT are not scaled; give every new heavy test an explicit one.

### Configure-time mutant pattern (D-046, D-061) and how Phase 11 used it
`gbb_colour_mutant(name test_source fail_test control_test anchor replacement failing_case failing_regex control_case)` (`tests/CMakeLists.txt:1942-1990`): reads the core text once, requires the anchor to occur exactly once forward and in reverse (`string(FIND ...)` vs `... REVERSE`, else `message(FATAL_ERROR ...)`), writes `gabbaboy_colour_mutant_<name>.c` into the build tree, then either (a) compiles the white-box test with `-DGBB_COLOUR_CORE_SOURCE="<path>"` so the test `#include`s the mutant (`tests/test_cgb_colour_internal.c:7-10`), or (b) builds a STATIC `gabbaboy_core_colour_mutant_<name>` linked before `gabbaboy_accept` so every core symbol resolves to the mutant. It registers a failing test (`expect_exit.cmake`, exit 1 + regex, `ASAN_OPTIONS=detect_leaks=0`) and a control test (exit 0). It is invoked 26 times in Phase 11, i.e. one core copy and one executable per mutant. Siblings: `gbb_rtc_mutant` (`:101`), `gbb_banking_mutant` (`:243`), model-gate real-file mutants (`:1747-1795`), the ADR static-assert mutant (`cgb_adr_half_dot_static_assert_mutant`, `:1671-1691`, PASS_REGULAR_EXPRESSION `half-dot timeline:`), and the fuzz-oracle mutant (`cgb_fuzz_palette_mutant_no_mask` + `_control`, `:2406-2440`).

**Measured build cost (this host):** compiling the 4126-line core is 0.23 s with `-O0 -g -fsanitize=address,undefined` and 0.11 s without; the whole 220-target Debug build of the scratch repo copy took 1.2 s wall at high parallelism. Compile cost is not the constraint on mutant count; configure-time `file(READ)` + `string(FIND)` and link/test run time are. Hosted runners are slower but the order of magnitude holds. [VERIFIED: measured]

**Recommended merge design (Claude's discretion: "Merging mutants to save compiles").** Generate ONE mutated core copy per consumer kind, where each tagged anchor line `... /* P12-M<n> */` is replaced by a runtime-selected form, e.g. anchor `const uint16_t tap = m->double_speed ? 0x2000u : 0x1000u; /* P12-M4 */` becomes `const uint16_t tap = GBB_P12_MUT(4) ? 0x1000u : (m->double_speed ? 0x2000u : 0x1000u);`, with `extern unsigned gbb_p12_mutants; #define GBB_P12_MUT(n) ((gbb_p12_mutants >> (n)) & 1u)` and `unsigned gbb_p12_mutants;` prepended to the TU. The white-box test takes `--mutants <mask>`; the failing CTest runs `exe <case> --mutants <1<<n>` expecting exit 1 + a named regex; its control runs the SAME executable with mask 0 (exit 0) and an unrelated case under the mutant (exit 0). Anchors keep the exactly-once rule per tag (a helper function applies it to a list of `(n, anchor, replacement)` triples). This yields two builds in total: one white-box executable (all 17 mutants) and one STATIC mutant library with `void gbb_p12_set_mutants(unsigned)` for any public-API consumer (D-15's PPU/APU controls at core level, fuzz). That satisfies D-25's "at most 6 mutant library builds" with margin; state the count in the closing summary. Equivalent-mutant caveat (D-09): a "±1 half-dot to normal" mutant is excluded.

### Model-gate machinery
- Scanner `tests/scripts/verify-model-gates.py` (601 lines): R1 every top-level function needs a `MODEL:` tag in the comment block directly above it; R2 code tags and doc rows are a bijection by `GATE-NN` with identical class, guard and resolution (Site/Note columns are NOT compared); R3 `UNKNOWN` needs `research:N` or `expected-failure:reason`; R4 `DMG_ONLY`/`CGB_ONLY` need their `GUARD` token within 12 code lines after the tag; R5 a `BOTH` tag whose next 12 code lines contain a hazard token (`0xFF4x-7x` literal, `stopped`, `halt_bug`, `dma_`, `apu_power`, `ppu_mode`, `return 0xFFu`) needs `basis=`. Current run: `model-gates pass functions=163 gates=84 unknown=39` and `self-test pass mutants=18`. [VERIFIED: ran it]
- CTests: `model_gates` expects `functions=1[2-9][0-9]` (`tests/CMakeLists.txt:1743`; room for 36 more functions), `model_gates_selftest`, real-file mutants (a) deleted STOP tag, (b) untagged function, (c) doc row mismatch, and `model_gates_release_blocked` (expects exit 1 `gate-unresolved-unknown` while any `research:` remains).
- **Anchor that must change in the same commit** (`tests/CMakeLists.txt:1760-1761`): `set(GBB_MG_STOP_TAG_REGEX "[ ]*/\\* MODEL: UNKNOWN GATE-[0-9][0-9] research:12 -- STOP, including CGB speed switch \\*/\n")`. It must match exactly one tag in the core; the retained GATE-62 tag text (D-12: DMG/unarmed STOP, `research:14`) becomes the new target, e.g. `... research:14 -- STOP (DMG and unarmed paths) ...`. The prototype confirmed the scanner rejects every new helper that lacks a tag (`gate-untagged-function: timer_reload_hd`), which is also how the three failing model-gate tests will behave if a plan forgets the tags.
- `model_gates_no_phase11_rows` + `_mutated_doc` (`:2446-2465`) use `tests/check_no_phase11_rows.cmake` (needle `research:11`). Copy it to `tests/check_no_phase12_rows.cmake` (needle `research:12`, token `phase-12-row-open`) with its own mutated-doc control (revert one row to `research:12`).

### External-suite dispositions and the AGE protocol
- Closest analog for `tests/external/cgb-speed-dispositions.json`: `tests/external/cgb-ppu-dispositions.json` (schema `gabbaboy-external-dispositions-v1`; per-suite `repository`, `commit`, `licence`, `vendored`, rows with `case`, `upstream_path`, `disposition`, `reason`, `decision`, `owner_phase`), `tests/scripts/verify-external-dispositions.py` (112 lines, offline, mirrors a docs block between `<!-- cgb-external-dispositions-begin -->` and `-end -->`, lists tracked files and forbids `m3-bg-` names), tests `cgb_external_dispositions` and `cgb_external_dispositions_mutated` (`:2347-2373`, anchor edit of one reason). Copy it (do not generalise; D-24 keeps the Phase 11 pair unchanged) and add `signature_sha256` and `flip_rule`.
- **No AGE ROM bytes and no `age_` test exist today.** `git ls-files fixtures` has no AGE path; `expected-tests.txt` has no `age_` name. The Phase 11 JSON records AGE `m3-bg-*` as `"vendored": false` and the verifier asserts that exact value (`need(suite.get("vendored") is False, f"{name}-vendored")`), which stays true (the m3-bg ROMs stay out) but will read oddly beside `fixtures/age/`; add a one-paragraph scope note in `docs/cgb-profile.md` rather than editing the Phase 11 file.
- The Mooneye CGB runner suite (`src/runner/main.c:109-114` `cgb_cases[]`, admitted by manifest SHA-256 at `:131-143`, PC table cross-checked by `cmake/VerifyMooneyeCgb.cmake`) detects completion at a fixed `result_pc` holding opcode `0x40`. AGE needs a different decision rule: the first executed `LD B,B` (opcode `0x40`) is the verdict point; pass iff `B,C,D,E,H,L = 3,5,8,13,21,34`, else the fail site sets only `B = 0` (`src/_include/test-setup.inc`, `show_final_screen`). [VERIFIED: fetched source at the pinned commit]

### Fixture rebuild machinery (templates for `fixtures/cgb-speed` and `fixtures/age`)
- Original-fixture template: `fixtures/cgb-colour/` with `manifest.json` (`build` pin block, `source_sha256`, `fixtures[]` with per-ROM `recipe {source, defines, rgbfix_flags}`), `LICENSE.txt`, shared `common.inc`; `tests/scripts/reproduce-cgb-colour.sh` rebuilds each row under pinned RGBDS and compares bytes, validating every recipe field with allow-list regexes and passing arguments as lists; `tests/scripts/test-reproduce-cgb-colour.sh` drives `cgb_colour_repro_tool_failure` and `cgb_colour_repro_missing_pin`; digest test `cgb_colour_fixture_digest` via `cmake/VerifyFixtureManifest.cmake`.
- Third-party template: `tests/scripts/reproduce-magentests.sh` (`--self-check` offline: manifest rows vs script table, SOURCES.md pins; `--compare`: shallow `git fetch` of the pinned commit, `rev-parse` equality check, rebuild, byte compare) and `fixtures/magentests/{manifest.json,SOURCES.md,ELIGIBILITY.md,LICENSE.txt}`; scan guard `magentests_not_installed` (+ `_selftest`) built from `cmake/ScanForbiddenFixtures.cmake`.
- `.github/workflows/fixture-repro.yml` (job `fixture-repro`, ubuntu-22.04, 15 min) contains one inline Python block that asserts every fixture manifest carries the same RGBDS pin; it names each manifest explicitly (`cgb_colour = json.loads(...)`). A new `cgb-speed` manifest must be added to that block (copy the `cgb_colour_build` loop) or the pin-equality guarantee silently excludes it. AGE rebuild fits as a step in the same job (RGBDS 1.0.1 already on PATH) or as a sibling job like `magentests-repro`.

### Partition, fuzz, coverage, bench
- Partition analogs: `halt_timer_partition` (`tests/test_control.c:191`), `rtc_slice_invariance` (`tests/test_mbc3_rtc_internal.c:501`, caps `{64u, 4096u, 100000u, 3u * SECOND}` and 64-half-dot slices "the finest a whole instruction fits in"). White-box includes of the core: `tests/test_cgb_colour_internal.c`, `tests/test_mbc3_rtc_internal.c`, `tests/test_banking_internal.c` (has `rng_next`, `:26`, to copy for the seeded sweep; `tests/test_loader_fuzz.c:27` has an xorshift32).
- Budget semantics to preserve and test: `tests/test_control.c:46-47` `r = gbb_run(m, 39, trace, 8); REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 0 ...` (interrupt entry needs 40); `tests/test_api.c:94` sub-instruction budget returns `consumed_half_dots == 0`.
- Fuzz: `tests/fuzz_core.c` (470 lines) dispatches in `gbb_fuzz_core_one_input` by `data[0]`: bit 7 = CGB profile, `cgb && (data[0] & 0x40u)` -> `fuzz_cgb_io`, `cgb && (data[0] & 0x20u)` -> `fuzz_palette`, `(data[0] & 3u) == 2u` synth-length, `== 0u` loader, else stateful. A speed mode needs a free selector, e.g. `cgb && (data[0] & 0x70u) == 0x10u` tested before the `& 3u` branches. Standalone contract counter: `gbb_fuzz_core_contract_failures()`; seeds in `tests/test_fuzz_core.c` (`run_cgb_seeds`, `run_profile_select`, `run_palette_seeds`); registered as `fuzz_core_regressions`, `cgb_fuzz_io_regressions`, `cgb_fuzz_profile_select`, `cgb_fuzz_palette_regressions`. `tests/scripts/run-bounded-fuzz.sh --fast` runs only `battery_api_fuzz|loader_boundary_fuzz|fuzz_core_regressions`.
- `tests/scripts/verify-summary-coverage.py --since 11` validates every Phase >= 11 SUMMARY; tests `summary_coverage`, `summary_coverage_selftest` (`mutants=1[2-9]`), `summary_coverage_phase10_rejected`.
- Bench: `measure_core --no-trace --profile cgb <rom>` prints `elapsed_ns=... correctness_digest_fnv1a64=...`; the DMG tracer digest must stay `4c7a57ff3d50d228`. Prototype vs baseline on `fixtures/tracer/tracer.gb` (3 alternating runs): 22.3/23.0/22.3 ms vs 22.6/22.2/21.8 ms with identical digests, i.e. no measurable slowdown from `cpu_tick`. [VERIFIED: measured]
- ASan: CI job `linux-asan-ubsan` (`.github/workflows/ci.yml:153`, `timeout-minutes: 30`) runs `ctest --preset phase1-asan --parallel 4`. `GABBABOY_ENABLE_SANITIZERS` is Linux-only (`CMakeLists.txt:7-9` fatal on other systems), so `phase1-asan` cannot run on this macOS host; use an ad-hoc `-fsanitize=address,undefined` compile of a driver for local timing and rely on the hosted leg for the preset.

## AGE Fixtures (measured, pinned commit)

Rebuild recipe (the upstream `Makefile`, run directly, from a clean `git fetch --depth 1` of `1f5bc10e...`, HEAD and tree `2fece1a6...` verified): `rgbasm -Weverything -I src -I src/_include -o X.o src/<dir>/X.asm` ; `rgblink -t -n X.sym -m X.map -o X.gb X.o` ; `rgbfix -v -p 255 X.gb`, with RGBDS **1.0.1** (macOS archive SHA-256 verified). Two independent builds were byte-identical. The upstream repo ships **sources only** (no prebuilt ROM at this commit), so the rebuild is the provenance. `rgbasm` prints only `-Wobsolete` warnings. Digests below are macOS builds, **provisional until the Linux fixture-repro leg confirms them** (D-19). [VERIFIED: local build; Linux equality is [ASSUMED]]

| ROM (`fixtures/age/`) | SHA-256 | $143 | TEST_RESULTS | expected table @ ROM, rows | half-dots to `LD B,B` (prototype) |
|---|---|---|---|---|---|
| `spsw-div-cgbBCE.gb` | `2c836288b58651f72a335417f11ba346863145dd9996048979ad8e5b9cd0aa7b` | C0 | `$C000` | `$144A`, 5 | 22,702,808 |
| `spsw-tima-cgbE.gb` | `3cb0918fb194d2704bb57f2afd5af3be21b5e97e269fde5224c34914d5f5936e` | C0 | `$C000` | `$144A`, 8 | 12,550,812 |
| `spsw-tima-cgbBC.gb` | `2fcfdc0d8595b642cfc1c16cab42f619a13b9a0d20e668a9c471436573a2e860` | C0 | `$C000` | `$144A`, 8 | 12,549,756 |
| `spsw-stop-prefetch-cgbBCE.gb` | `df782c73f08c6778c7b926c6a4ebbd0816c58b53faf4b6abf5b2b812766eab4f` | C0 | `$C000` | `$144A`, 1 | 1,318,096 |
| `spsw-interrupts-cgbE.gb` (from `caution/`) | `bd240315c0b8e7fd5f0d0521785c6c5a10769dae36339e88d777fc507bca44b6` | C0 | `$C000` | `$144A`, 11 | 759,272 |
| `spsw-mode0-cgbBCE.gb` | `07eefc27d8bdd98569510ebef662aba388715bbe5ddf9993763fbf1aab290f2e` | C0 | `$C000` | `$144A`, 15 | 1,698,540 |
| `spsw-ch2-lc-delay-cgbBCE.gb` | `76920fa2f63f5a5b9b8b907b98a78e06410d88fb09491826f3930dedf96cff19` | C0 | `$C000` | `$144A`, 8 | 35,229,800 |
| `stat-mode-ds-cgbBCE.gb` | `c371664f71cb95b6de9cf9a1ecd4ff80147b5603b08deacea7c9495eb45d1cf0` | C0 | `$C600` | `$1B0A`, 14 | 20,731,704 |
| `stat-mode-cgbE.gb` (control) | `b2789ba04e79c25aba7a947e0d4b7938171457960264702dbaa4826acfdb2fc3` | 80 | `$C600` | `$1B0A`, 14 | 11,609,024 |
| `stat-mode-sprites-ds-cgbBCE.gb` | `3ee5bb3fc7fa724a832a082dd8c4979af5abb3f837dbc489a2f04cdf2332a64d` | C0 | `$C400` | `$22C0`, 16 | 1,823,908 |
| `stat-mode-sprites-dmgC-cgbBCE.gb` (control) | `173ff267a4ecbd2e5bb3bd209f7b08c971900d54382bd6281969c7a3a98507c1` | 80 | `$C400` | `$2185`, 10 | 1,528,240 |
| `stat-mode-window-ds-cgbBCE.gb` | `055c641aaf9464b637f6206126a165fa23433fbced0d5fbafa0d3cdb813aaa41` | C0 | `$C300` | `$174A`, 16 | 2,803,880 |
| `stat-mode-window-cgbBCE.gb` (control) | `69fb62868aa256ff79e77cabb88caab9db43dbe302eb6f4628550d99b7ef12da` | 80 | `$C200` | `$164A`, 16 | 2,970,032 |

- All 13 are 32,768 bytes (13 x 32 KiB = 416 KiB), numeric-result tests (only `test-setup.inc` mentions `CART_IS_VISUAL_TEST`; none of the 13 sets it), so no screenshot canonicaliser is needed. All 13 share the verdict sites: pass `LD B,B` at `$13CD` (preceded by `ld l,34`), fail `LD B,B` at `$13D9` (preceded by `ld b,0`). `show_final_screen` is `$13B2`. `TEST_RESULTS` is 128 bytes (16 rows x 8) at the address in the table (from the linker `.sym`; record it per ROM in the manifest, the address is NOT constant); the expected rows are in ROM at `EXPECTED_TEST_RESULTS` (first byte = row count, then 8 bytes per row). A host computes the per-row pass mask by comparing WRAM `TEST_RESULTS + 8*row` with ROM `expected + 1 + 8*row`; the ROM's own verdict is the cross-check.
- Header `$143` is `C0` (CGB only) for the speed-switch and `-ds-` ROMs, `80` for the three single-speed controls; both run in CGB mode on the CGB profile.
- `SWITCH_SPEED` macro (`src/_include/macros.inc`): `ld a, $30` / `ldh [rP1], a` / `ld a, 1` / `ldh [rKEY1], a` / `stop`. P1 = `$30` selects no row, so the held-button test is false; RGBDS 1.0.1 emits `10 00` (operand `$00`), which is why D-04's operand-value tests matter. Test setup clears IE/IF (`xor a` / `ldh [rIE], a` / `ldh [rIF], a`).
- Rights/provenance files to write (D-19): `LICENSE.txt` (verbatim upstream MIT text, Copyright (c) 2021 Christoph Sprenger; upstream `LICENSE` SHA-256 `f369002da7f08e78ebfc2d9febbfb0316c78f535569e63b84cca8804a234fcef`), the font is "Cellphone Font" by domsson (CC0; cite in `THIRD_PARTY_NOTICES.md` and `SOURCES.md`), `hardware.inc` is a pre-CC0 equates-only copy (no code bytes), `WARNING.md` copy (upstream SHA-256 `ea6ef51eb73adc814ff1d9015c4c1fdaa6947d0cb2f0c430fda828ca354005ed`) marked "emulator-only", `ELIGIBILITY.md` (author-attested hardware, never a reproducible receipt), `manifest.json` (per ROM: `file`, `size_bytes`, `sha256`, `source_path`, `test_results_address`, `expected_address`, `rows`, `pass_pc`, `fail_pc`, `budget_half_dots`, verbatim `Verified:` header lines, build recipe). `fixtures[]` with `file`/`size_bytes`/`sha256` makes the manifest directly usable by `VerifyFixtureManifest.cmake` and `ScanForbiddenFixtures.cmake`.
- **Pitfall for the scan guard:** `cmake/ScanForbiddenFixtures.cmake:68` fails when the lower-cased install path matches the label as a regex (`if(lowered MATCHES "${forbidden_label}")`). A label of `age` would match any path containing "package" or "image". Use the label `fixtures/age` (or `age-test-roms`); the size+digest match is the real guard.

### Measured behaviour of the 13 ROMs (prototype, not committed code)
Prototype model: D-01..D-11 as locked, stall 0x20004 T, STOP 2 M on the switch path (the 1 M column is in E1b). "Current main" is the committed core, where every speed ROM stops at its first armed STOP with `GBB_STOP_UNSUPPORTED_BUS` (the GATE-74 latch).

| ROM | Current main | Prototype (rows ok) | Expected disposition |
|---|---|---|---|
| `spsw-div-cgbBCE` | stops at first STOP | **5/5, LD B,B pass** | pass (window [0x20004,0x20007]) |
| `spsw-stop-prefetch-cgbBCE` | stops | **1/1, pass** | pass |
| `spsw-tima-cgbE` | stops | 5/8 (rows 2, 6, 7 = 65/16 KHz and 4 KHz 1-to-0 immediate-increment edges) | `expected-failure:cgb-e-div-reset-immediate-increment-delay` (D-35) |
| `spsw-tima-cgbBC` | stops | 7/8 (row 2 only) | expected failure; per D-19 contingency BOTH tima rows are pinned expected failures and the "core is not B/C-flavoured" claim is dropped |
| `spsw-interrupts-cgbE` | stops | 9/11 (rows 0 and 2: TIMA `07` vs `08`, DIV `0f` vs `10`; rows 3-10, the case-3 pending-IRQ switch rows, pass) | expected failure (D-35 `OFS_B` dispatch offset); rows 3-10 are positive evidence for D-02 case 3 |
| `spsw-mode0-cgbBCE` | stops | 0/15 | expected failure (`ds-lcd-cpu-alignment`, `cgb-mode3-length`) |
| `spsw-ch2-lc-delay-cgbBCE` | stops | 3/8 | expected failure (`apu-lc-delay-after-switch`, owner 14) |
| `stat-mode-ds`, `-sprites-ds`, `-window-ds` | stops | 0/14, 2/16, 0/16 | expected failure (`cgb-mode3-length`, owner 14) |
| controls `stat-mode-cgbE`, `stat-mode-window-cgbBCE`, `stat-mode-sprites-dmgC-cgbBCE` | **already fail on main**: 5/14, 0/16, 3/10 rows, fail `LD B,B` | unchanged | confirms the D-19 fallback: the ds failures belong to Phase 14, not to speed |

So only two of the 13 are pass targets. Plan the AGE wave as "pin exact signatures and dispositions with flip rules"; do not budget time for making the other rows pass (D-21 forbids tuning).

**Runtime/budget for tests:** total about 128 million half-dots for all 13 (`spsw-ch2` 35.2 M, `spsw-div` 22.7 M, `stat-mode-ds` 20.7 M are the long ones). Measured: `spsw-ch2` 0.27 s at `-O1`, 3.25 s ad-hoc `-O0` ASan; `spsw-div` 1.96 s ASan. These exceed D-29's "about 1 s" because a ROM cannot be sliced; set `TIMEOUT 120` (x3 under sanitizers) and record the measured wall time. Per-ROM budget: follow D-050 (measured, times 2, rounded up to the next 1,000,000 half-dots, recorded in the manifest).

## Model-gates document (`docs/model-gates.md`)

Rows live in the table between `<!-- model-gates-begin -->` (`:42`) and `<!-- model-gates-end -->` (`:129`). Current text of every row Phase 12 touches [VERIFIED: file read]:

| Gate | Current row (Class / Guard / Resolution / Site / Note) | D-12 target |
|---|---|---|
| GATE-30 | `UNKNOWN / - / research:12 / write8 / DMA restart and period` | `BOTH`, `basis=...` (scaled period; R5 needs a basis because `dma_` follows the tag) |
| GATE-31 | `UNKNOWN / - / research:12 / write8 / DIV write resets the counter and clocks the frame sequencer` | `BOTH`, `basis=` (speed-dependent tap via `divider_reset`) |
| GATE-41 | `UNKNOWN / - / research:12 / apply_input_events_now / STOP wake conditions` | `research:14` |
| GATE-52 | `UNKNOWN / - / research:12 / dma_start / DMA restart behaviour` | `UNKNOWN`, `expected-failure:cgb-dma-restart-oracle-only` |
| GATE-53 | `UNKNOWN / - / research:12 / dma_advance_half_dot / DMA byte period` | `BOTH`, `basis=` (tick-scaled) |
| GATE-56 | `UNKNOWN / - / research:12 / advance_devices_to / frame sequencer taps a DIV bit that moves in double speed` | `CGB_ONLY`, `GUARD=double_speed` |
| GATE-62 | `UNKNOWN / - / research:12 / execute / STOP, including CGB speed switch` | split: keep as `research:14` for DMG/unarmed STOP; the switch moves to new rows |
| GATE-65 | `UNKNOWN / - / research:12 / gbb_run_internal / DIV reset on STOP` | `BOTH`, `basis=`, site becomes the helper/call sites |
| GATE-74 | `CGB_ONLY / model_is_cgb / - / execute / STOP with KEY1 armed latches bus_unsupported at FF4D instead of sleeping; the speed switch is DEFERRED(12) (D-23)` | reword to the implemented switch |
| GATE-54, GATE-55 | `UNKNOWN / - / research:14 / advance_devices_to / ...` | stay `research:14`; the tick-unit change is declared by the new scaling row |
| new GATE-84.. | - | switch decision (`stop_case`), stall branch, wake, D-09 realignment, `cpu_ticks` scaling row (`CGB_ONLY`, `GUARD=double_speed`, listing every site in section B) |

The "Release status" paragraph is `docs/model-gates.md:155-165`: its sentence "Phase 12 owns `research:12` (STOP, DMA and double-speed timing) and Phase 14 owns `research:14` ..." must be rewritten so that no `research:12` remains (new test `model_gates_no_phase12_rows`). Add a "Phase 12 dispositions" table in the style of the existing "Phase 11 dispositions" section (`:131-153`).

Gate numbering: the highest row is GATE-83 (`:128`); new ids start at GATE-84. Because R2 ignores the Site column, a moved GATE-65 only needs its class/guard/resolution to match the new tag.

## Docs to update (D-17), exact places

| File | Place | Edit |
|---|---|---|
| `docs/cgb-profile.md` | `:301-303` FF4D rows; `:465-472` "STOP with KEY1 armed" (`DEFERRED(12)`); `:634-641` "Half-dot timeline (D-070)" incl. the `[VERIFY]` sentence at `:640` | KEY1 read text (must equal `tests/test_cgb_tables.c:288`); STOP section; resolve `[VERIFY]` (stall counted at destination speed, DIV reset at STOP, APU tap); derivation of `GBB_SPEED_SWITCH_STALL_T` and the AGE conflict note vs Pan Docs; future save-state field list; `expected-failure:*` names; AGE scope note |
| `docs/model-gates.md` | table + "Release status" + new "Phase 12 dispositions" | see above |
| `docs/native-integration.md` | `:143` "Limitations: no double speed, no HDMA, ..." | drop "no double speed"; add master-time budget note and "the pause returns `GBB_STOP_BUDGET`"; keep the CGB-guide required phrases (`"stop with `GBB_STOP_UNSUPPORTED_BUS`"` etc., `tests/CMakeLists.txt:1580-1588`) |
| `docs/support/unreleased.md` | `:35` ("no CGB double-speed clock assertion"), `:42` ("Not implemented: double speed (Phase 12), HDMA (Phase 13) ...") | rewrite |
| `docs/preview.md` | `:76` ("The preview does not implement ... CGB double-speed clock behavior ...") | rewrite |
| `docs/cartridge-and-saves.md` | `:438` ("... CGB, CGB double-speed clock behavior, MBC30 ...") | reword |
| `docs/mbc3-rtc-evidence.md` | `:265` ("No CGB double-speed clock independence (planned for the CGB phase)") | now evidenced by `cgb_speed_*` RTC controls (M12) |
| `include/gabbaboy/gabbaboy.h` | comment block at `:262-276` | comments only: stall returns `GBB_STOP_BUDGET`, budgets are master time at both speeds (D-14) |
| E2 surfaces | `src/player/limitations.h:5`, `tests/player/test_limitations.c:8`, `README.md` (paragraph at line 11), `.github/workflows/preview.yml` lines 51 and 98, `src/player/main.c:401` | claims-only edit (E2) |
| `THIRD_PARTY_NOTICES.md` | new AGE entry | MIT + CC0 font + pre-CC0 `hardware.inc` note |

## Architecture Patterns

### System Architecture Diagram

```
host gbb_run(budget_half_dots)                      guest: LD A,1; LDH ($4D),A; STOP
        |                                                    |
        v                                                    v
 [run loop gbb_run_internal]  locked? -> LOCKUP
        |
        +-- stopped?  ------------------------------------------- DMG/unarmed/compat sleep path (unchanged, GATE-62 -> research:14)
        |
        +-- cpu_stalled?  (NEW)  wake check -> step 1 CPU M-cycle (8 hd normal, 4 hd double)
        |        |                  audio_preflight, headroom, advance_devices(step), counter -= step
        |        +-- counter==0 or woken -> D-09 realign tail (entering normal at time%8==4: +4 hd, no wake check)
        |
        +-- IME && IE&IF&$1F -> interrupt entry (cost 40 >> double_speed)
        +-- halted -> M-cycle step (8 >> double_speed), wake per step
        +-- fetch -> decode(size,cost from stop_case) -> preflight (only fetched bytes) -> execute
                         |                                   |
                         |                          STOP case 1: HALT   2: 1 byte   3: switch, no stall   4: switch + stall
                         v
                 advance_devices_to(start + cost>>ds)  ==  master loop, one half-dot per iteration:
                    input events -> [cpu_tick? reload, serial, divider/APU tap, DMA]  -> APU channels -> PCM -> PPU dot (every 2 hd)
                         |
                 retire: ime_delay -> (case 3/4) flip double_speed, clear KEY1 bit 0, divider_reset(apu_edge) , load stall (case 4)
```

### Recommended additions (project structure)
```
src/core/gabbaboy.c            # fields, stop_case, divider_reset, cpu_stalled, stall branch, switch block, cpu_ticks sites
src/core/gabbaboy_test.h       # + gbb_test_speed_state
tests/test_cgb_speed_internal.c# white-box (includes core or GBB_P12_CORE_SOURCE): tracer, scaling, cases, wake, realign, reset, headroom, mutants
tests/test_cgb_partition.c     # white-box partition sweeps (or folded into the file above)
tests/test_age.c               # AGE driver: table + --print-signature + disposition check
tests/scripts/derive-cgb-speed-expectations.py, verify-cgb-speed-dispositions.py, verify-speed-domains.py
tests/scripts/reproduce-cgb-speed.sh, reproduce-age.sh, test-reproduce-*.sh
tests/external/cgb-speed-dispositions.json
tests/check_no_phase12_rows.cmake
tests/fuzz/fuzz_core.dict
fixtures/cgb-speed/ (asm, common.inc, manifest.json, LICENSE.txt)   fixtures/age/ (13 ROMs + 5 rights/provenance files)
```

### Pattern 1: Tick-unit countdowns (D-10)
**What:** store timer-reload and serial countdowns in CPU T-ticks and OAM DMA phase in CPU ticks; decrement only on the tick phase (`cpu_tick`). **When:** every CPU-side countdown. **Why:** no fractional remainder exists at a speed switch (the countdown simply continues at the new rate). Equivalence at normal speed is proven by `dmg_baseline` and the Mooneye timer/serial/DMA cases. Add `timer_reload_hd()` for the one place that needs half-dots (TMA coincidence) and keep the invariant "all instruction costs and bus offsets are multiples of 8 half-dots" as a `_Static_assert`-style table check or a unit test over `decode()` costs.

### Pattern 2: Stall branch = HALT branch + counter (D-06, D-34)
Copy `:3970-3990` structure: wake check at loop top and after each step, `audio_preflight`, `UINT64_MAX` headroom, `advance_devices`, `consumed +=`; report `GBB_STOP_BUDGET` (never `HALTED_IDLE`/`STOPPED`); never touch `halted`/`stopped`/`halt_bug`. Because steps are single M-cycles, wake time is a pure function of master time, which is what makes partition equality hold; the prototype passed 387 single-cut positions in three windows (around 72, 131,150 and 400,000 half-dots of a 700,000-half-dot run) with zero mismatches in the compared state. [VERIFIED: prototype]

### Pattern 3: Switch at retire, after the IME delay
Apply the case-3/4 effects in the run loop after `ime_delay` handling and before the GATE-65 block. Case 4 loads `cpu_stall_half_dots = GBB_SPEED_SWITCH_STALL_T * (double_speed ? 1u : 2u)` (destination speed, after the flip). The tail rule (D-09) is part of the persisted counter.

### Pattern 4: Runtime-selected mutants in one mutated core copy
See "Recommended merge design". Each anchor is a single tagged line written when the production line is written (CONTEXT D-25: tagged `/* P12-M<n> */` when the code is written).

### Pattern 5: White-box seeded stall for partition sweeps
Run the guest to STOP retire with an exact budget, then (identically in the reference and every partitioned run) overwrite `m->cpu_stall_half_dots` with a short value before cutting. The invariance property does not depend on the constant, and each cut then costs a few thousand half-dots instead of 131,076. Keep a handful of cuts against the real constant.

### Pattern 6: Table-first, doc-mirrored change
KEY1 row: C table (`io_visibility` row comment), `tests/test_cgb_tables.c` text generator, and the `docs/cgb-profile.md` block change in one commit (see Code Map G).

### Anti-Patterns to Avoid
- **Reusing `halted = 1` for the stall** (changes the stop reason to `HALTED_IDLE`; the player's `advance_to` treats any reason other than `BUDGET`/`OUTPUT_FULL` as a fatal guest stop, `src/player/main.c:652-657`).
- **An atomic or looped pause** (262,152 half-dots exceeds the 140,448-half-dot frame budget; the host loop would never complete it).
- **Stepping `min(budget, stall, event)`** (wake would depend on where the host cut the budget; D-26/D-34).
- **Putting `double_speed` anywhere in `ppu_*`, `apu_*`, `rtc_*`** (enforced by `tests/scripts/verify-speed-domains.py` plus M1/M12).
- **Tuning the stall constant or the shared DIV-reset helper to make an AGE row pass** (D-21, D-35).
- **Building the E-quirks into `divider_reset`** (D-35: only through its own decision row).

## Don't Hand-Roll

| Problem | Don't build | Use instead | Why |
|---------|-------------|-------------|-----|
| SHA-256 / PCM digests in test drivers | new hash code | `gbb_accept_sha256_hex`, `gbb_accept_pcm_digest_*` (`src/accept`) | existing, already tested; `tests/test_age.c` links `gabbaboy_accept` |
| Manifest digest checks | per-test file hashing | `cmake/VerifyFixtureManifest.cmake` | handles size+digest, empty-array failure |
| Install redistribution guard | a new scanner | `cmake/ScanForbiddenFixtures.cmake` with label `fixtures/age` | matches by size and digest, has a renamed-copy selftest |
| JSON in C | a parser | CMake `string(JSON ...)` at configure time (generate `add_test` rows from the dispositions file) or Python `-I` verifier | STACK.md: no JSON library in C |
| Seeded randomness | `rand()` / new RNG | copy `rng_next` (`tests/test_banking_internal.c:26`) | deterministic, seed printed on failure |
| RGBDS provisioning | a new download path | the existing pinned archive logic in `fixture-repro.yml` and `reproduce-*.sh` | digest-pinned already |
| Expected-value tables for speed behaviour | reading the emulator | `derive-cgb-speed-expectations.py` from 4194304 Hz, 456 dots/line, TAC periods, serial bit time, factor, constant | D-22 independence |
| Doc adequacy | human reading | `VerifyDocContract.cmake` phrases/identifiers | D-069 |
| Mutant exactly-once logic | ad-hoc `string(REPLACE)` | one helper applying a list of `(n, anchor, replacement)` triples with forward/reverse `string(FIND)` | drifted anchors become configure failures |

**Key insight:** every new check in this phase has a copyable precedent in the repo; the only genuinely new mechanisms are the runtime mutant mask, the seeded-stall white-box seam, and the AGE verdict driver.

## Common Pitfalls

### Pitfall 1: The stall constant fails its own binding oracle
**What goes wrong:** `GBB_SPEED_SWITCH_STALL_T = 0x20008` gives `spsw-div` 0/5. **Why:** GabbaBoy resets DIV at STOP retire (1 or 2 M after fetch), SameBoy's reset sits earlier in its 2 M STOP and it removes 4 T at IME = 0. **Avoid:** derive and name the constant from the DIV-reset-to-resume distance (E1) and keep the derivation in `docs/cgb-profile.md`. **Warning sign:** `spsw-div` rows `01` where `00` is expected.

### Pitfall 2: Half-dot vs tick units mixed at one site
**What goes wrong:** the TMA-coincidence test at `:2092-2093` still compares half-dots to a tick counter, or a DMA/serial site keeps `8u`/`1024u`. **Why:** units are implicit. **Avoid:** the 14-row table in Code Map B as a checklist, M15 (countdown kept in half-dots) and M11 (remainder dropped). **Warning sign:** Mooneye `tim*`/`tma_write_reloading`, `serial_*`, `test_dma` failures at NORMAL speed.

### Pitfall 3: DMG byte identity moves
**What goes wrong:** the shared reset clocks the APU on the DMG STOP path, or STOP cost/size changes for unarmed STOP. **Avoid:** `clock_apu_edge` parameter (E3); STOP cost/size change only when `stop_case() != 0`. **Gate:** `dmg_baseline`, `acceptance_*`, tracer digest `4c7a57ff3d50d228`, `cgb_runner_profile_dmg_identity_*`, plus the new pre-change pin test (below). Capture the pin BEFORE editing the core.

### Pitfall 4: `decode()` and `execute()` disagree about STOP
Size/cost come from `decode()`, side effects from `execute()`. Use one `stop_case()` in both; test operand `$00` and `$FF` and the 1-byte cases with the next byte placed as a marker opcode (it must execute).

### Pitfall 5: Switch applied at the wrong moment
Before `advance_devices_to(start + cost)` the STOP M-cycle runs at the wrong speed; before the `ime_delay` line `EI; STOP` loses its IME. Apply after `:4035`, before `:4036`.

### Pitfall 6: APU edge with the wrong tap
Call `divider_reset()` before flipping `double_speed` (tap of the old speed), then flip.

### Pitfall 7: Wrong stop reason
The stall must never produce `GBB_STOP_HALTED_IDLE`/`STOPPED`/`NO_PROGRESS`; hosts and the player treat those as idle or fatal. Test `reason == GBB_STOP_BUDGET` with `consumed > 0` for a budget that ends mid-stall, and `consumed == 0` for a budget below one M-cycle (mirrors `tests/test_control.c:46-47`).

### Pitfall 8: Realignment shortened by the wake check
D-09's 4-half-dot tail for an early wake into normal speed (and the case-3 switch to normal with no stall) must run even though `IE & IF` is already non-zero. Use a separate kind (`SWITCH_REALIGN`) that skips the wake test, otherwise the tail is dropped exactly when it matters. The AGE `spsw-div` result did not change with the tail on or off in the prototype, so the tail is only evidenced by unit tests and the odd-mode named failure.

### Pitfall 9: Headroom
D-28 needs the pre-check in E4; test with `time_half_dots = UINT64_MAX - 100` (white-box) before an armed STOP and assert no field changed (use the digest from D-26).

### Pitfall 10: Model-gate scanner
Every new `static` helper needs a `MODEL:` tag (`gate-untagged-function`), every `BOTH` branch near `stopped`/`halt_bug`/`dma_` needs `basis=`, `CGB_ONLY` needs the guard token within 12 code lines, rows must stay in ascending id order, and `GBB_MG_STOP_TAG_REGEX` must be updated in the same commit or configure fails.

### Pitfall 11: Doc contracts
`cgb_adr_half_dot_contract` scans the paragraph starting "The `uint64_t` half-dot master timeline" for required phrases (including `never reads `double_speed``) and checks every `GBB_*` identifier named there is declared in `src/core/gabbaboy.c` or the public header; a new `GBB_SPEED_SWITCH_STALL_T` mention is fine only if it is `#define`d in the core. `cgb_native_guide_contract` requires its phrase list to survive native-integration edits (e.g. "stop with `GBB_STOP_UNSUPPORTED_BUS`"; still true for the other deferred registers). `cgb_tables_io` compares the KEY1 row text.

### Pitfall 12: Inventory plumbing
Windows removal list (`cmake/ExpectedTests.cmake:16-21`), `tests/player/CMakeLists.txt` branch per new `player_cgb_*` name, `tests/expected-tests.txt` appended in the same commit as the `add_test`.

### Pitfall 13: Install-scan label collision
See AGE section: label `fixtures/age`, not `age`.

### Pitfall 14: fixture-repro pin cross-check omission
The inline Python block in `fixture-repro.yml` names each manifest; add `cgb-speed`.

### Pitfall 15: AGE expectations
Do not promise passes beyond `spsw-div` and `spsw-stop-prefetch`; the three controls already fail on main; the `-ds-` rows are mode-3 length (Phase 14). The Linux leg may differ from the macOS digests (unlikely, unverified): the first CI run is the confirmation, so vendor early.

### Pitfall 16: Fuzz plumbing
Do not edit `FUZZ_RUN_LIMIT` / `FUZZ_INPUT_HALF_DOT_LIMIT` (`run-bounded-fuzz.sh --self-test` greps them); the speed mode needs its own limit above 131,076 half-dots per stall; use `gbb_test_speed_state` for the invariants.

### Pitfall 17: Player smoke shape
The smoke prints a colour-attr-specific spot grid; the new `GBB_CHECK=speed` branch must ignore it and pin only `rgba_sha256` (+ `title_token`), and the guest must finish drawing within 30 frames (4.2 M half-dots; four stalls cost about 0.6 M).

### Pitfall 18: Hosted ASan cannot be reproduced locally
`phase1-asan` is Linux-only; record hosted timings in the PR and compare against LESSONS GB-CI-004 (826-915 s serial-equivalent at `--parallel 4`, 30-minute job limit).

## Code Examples

Derived from the scratch prototype (not committed); adapt names. [VERIFIED: prototype]

### D-02 decision table
```c
/* 0: not the switch path (DMG, compat, unarmed). 1: held button, nothing pending -> HALT, operand fetched.
 * 2: held button, pending -> 1 byte. 3: switch, no stall, 1 byte. 4: switch + stall, 2 bytes. */
static int stop_case(const gbb_instance *m) {
    if (!(model_is_cgb(m) && m->exec_mode == GBB_MODE_CGB && (m->key1_armed & 1u) != 0u)) return 0;
    const int held = (joypad_value(m) & 0x0Fu) != 0x0Fu;
    const int pending = (m->ie & m->interrupt_flags & 0x1Fu) != 0;
    if (held) return pending ? 2 : 1;
    return pending ? 3 : 4;
}
/* execute(), case 0x10: */
{ const int sc = stop_case(m);
  if (sc == 0) { m->pc = (uint16_t)(pc + 2); m->stopped = 1; break; }
  if (sc == 1) { m->pc = (uint16_t)(pc + 2); m->halted = 1; break; }
  if (sc == 2) { m->pc = (uint16_t)(pc + 1); break; }
  m->pc = (uint16_t)(pc + (sc == 3 ? 1 : 2)); m->stop_switch_pending = (uint8_t)sc; break; }
```

### Switch block (run loop, after the `ime_delay` line)
```c
if (instance->stop_switch_pending) {
    const int sc = instance->stop_switch_pending; instance->stop_switch_pending = 0;
    divider_reset(instance, 1);                       /* old-speed tap, APU edge included */
    instance->double_speed ^= 1u; instance->key1_armed = 0;
    if (sc == 4) { instance->cpu_stall_kind = SPEED_SWITCH;
                   instance->cpu_stall_half_dots = GBB_SPEED_SWITCH_STALL_T * (instance->double_speed ? 1u : 2u); }
    /* D-09 for sc == 3 into normal speed: schedule the realign tail directly (kind SWITCH_REALIGN). */
}
```

### AGE verdict and signature (driver)
```c
/* first executed LD B,B = verdict point */
pass = (b==3 && c==5 && d==8 && e==13 && h==21 && l==34);
for (row = 0; row < rows; ++row) mask |= (memcmp(wram + test_results + 8*row, rom + expected + 1 + 8*row, 8) == 0) << row;
signature = sha256(wram[test_results .. test_results+rows*8) || mask_le16);   /* compare with signature_sha256 */
/* never reaching LD B,B within the budget -> distinct exit code (hang/timeout red) */
```

### Runtime mutant helper (CMake sketch)
```cmake
function(gbb_p12_make_mutant_core out_path)   # ARGN: <n> <anchor> <replacement> triples
  file(READ ${PROJECT_SOURCE_DIR}/src/core/gabbaboy.c text)
  foreach(...)  # string(FIND text anchor first); string(FIND text anchor last REVERSE); fail unless first==last!=-1
    string(REPLACE "${anchor}" "${replacement}" text "${text}")   # replacement uses GBB_P12_MUT(n)
  endforeach()
  file(WRITE ${CMAKE_CURRENT_BINARY_DIR}/gabbaboy_p12_mutants.c
    "unsigned gbb_p12_mutants;\n#define GBB_P12_MUT(n) ((gbb_p12_mutants >> (n)) & 1u)\n${text}")
endfunction()
```

## State of the Art

| Old approach | Current approach | When changed | Impact |
|--------------|------------------|--------------|--------|
| Pan Docs: pause 2050 M-cycles, DIV frozen | Stall about 32769 M at the destination speed, devices keep running | AGE hardware rows (`spsw-tima` TIMA `$80`, `spsw-div`), SameBoy `0x20008`, Gambatte to-normal | The 16x difference is the main finding; the 2050 M figure and "DIV does not tick" are rejected (D-05, D-07). |
| GATE-74 fail-closed latch on armed STOP | Real switch with stall | Phase 12 | `cgb_stop_armed_cgb` flips; the DMG/unarmed/compat sleep path is unchanged. |
| Half-dot countdowns | CPU-tick countdowns | Phase 12 (D-10) | No remainder at a switch; normal speed byte-identical. |

**Deprecated/outdated:** the `[VERIFY]` sentence in `docs/cgb-profile.md:640`; the `DEFERRED(12)` text (`docs/cgb-profile.md:467`, `docs/model-gates.md:119`); the "planned" double-speed wording in `docs/cartridge-and-saves.md:438` and `docs/mbc3-rtc-evidence.md:265`; the player claims in E2.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The Linux RGBDS 1.0.1 rebuild of the 13 AGE ROMs equals the macOS digests | AGE Fixtures | Manifest digests must be re-pinned after the first fixture-repro run; vendor early to learn this |
| A2 | Hosted ASan runs at roughly 1.6x the local ad-hoc ASan cost (CONTEXT's factor) | Validation Architecture | Partition and AGE test budgets may need a further cut |
| A3 | The 2 M STOP on the switch path reflects hardware; the evidence is a prototype fit to author-attested AGE rows, not a datasheet | E1b | If wrong, only the `tima` signatures change; the stall window and `spsw-div`/`stop-prefetch` passes do not |
| A4 | The committed implementation will reproduce the prototype's AGE row counts | AGE Fixtures | Signatures are generated from the committed core, so a different count only changes pinned values |
| A5 | SameBoy/Gambatte/Pan Docs statements quoted from CONTEXT (`stop()` table, `0x20008`, `div_cycles` quirk) were not re-verified here | E1 | The window finding stands independently (it is a direct measurement) |
| A6 | A "+1 half-dot to double" stall mutant is undetectable by AGE (window is 4 T wide) | E1 | If a future ROM discriminates it, add it to D-21 |
| A7 | Edits to `README.md`/`preview.yml`/`limitations.h` need owner awareness because they are public claims | E2 | Low: the change removes a now-false claim |

## Open Questions

1. **STOP cost on the switch path (1 M per D-02 or 2 M per E1b)?**
   - Known: window for the stall is identical; B/C `tima` rows prefer 2 M; E rows prefer 1 M by accident of the quirk.
   - Unclear: owner preference given D-02's literal text.
   - Recommendation: 2 M for cases 3/4 only, recorded as a DECISIONS row; tests parameterised by a named constant `GBB_STOP_SWITCH_COST_HALF_DOTS`.
2. **Where the D-15 audio digest lives** (E2b). Recommendation: core-level `cgb_speed_fixture_audio_digest`; player pins RGBA only.
3. **Realign kind and the case-3-into-normal tail** (Pitfall 8): confirm `SWITCH_REALIGN` as a third `cpu_stall_kind` value.
4. **Fuzz selector bit**: `(data[0] & 0x70u) == 0x10u` proposed; check no existing seed uses `0x9x`.
5. **Hosted ASan total**: the closing plan must measure and record added wall time (D-29); no number exists yet.
6. **Does the owner want the E2 claims edit inside Phase 12** (recommended) or deferred to Phase 15? A stale "double speed not implemented" claim shipped in a preview package is the risk of deferring.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| cmake / ninja / C compiler | all | yes | 4.4.3 / 1.13.2 / Apple clang 21 | - |
| Python 3 (`-I`) | verifiers, derive script | yes | 3.14.4 | - |
| bash, git, curl | repro scripts, AGE fetch | yes | 5.2.37 / 2.41.0 / 8.7.1 | - |
| RGBDS **1.0.1** | fixture + AGE rebuild | not on PATH (Homebrew has 1.0.4) | scratch copy verified | download the pinned archive (digest in manifests); never use 1.0.4 |
| Network to github.com | AGE fetch, RGBDS download | yes | - | none for `--compare`; `--self-check` is offline |
| Linux + sanitizers (`phase1-asan`) | ASan leg | no (macOS host) | - | hosted CI; ad-hoc local `-fsanitize` timing |
| SDL3 3.4.18 / player build | `player_cgb_speed_smoke` | `build-player/` exists | - | macOS player job; plan must say so |
| Docker | none required | `/usr/local/bin/docker` present, daemon state unknown | - | not used |

**Missing dependencies with no fallback:** none. **With fallback:** pinned RGBDS (download), Linux ASan (hosted CI).

## Validation Architecture

Nyquist validation is enabled (`.planning/config.json` `workflow.nyquist_validation: true`; `workflow.test_command` = `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error`). Every test below needs a CTest name in `tests/expected-tests.txt` (D-31), an exact-exit negative control (D-069), and a stdout token where `PASS_REGULAR_EXPRESSION`/`expect_exit.cmake` is used. **Reading the tables:** inside table cells `\|` stands for the regex alternation `|`; drop the backslash when you type the `-R` pattern.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | CTest over C executables with `REQUIRE` macros and TAP-ish output; CMake `-P` verifiers; stdlib Python verifiers (`python3 -I`); configure-time core mutants; white-box single-TU tests that `#include` the core |
| Config file | `CMakePresets.json` presets `phase1` (Debug, `build/`), `phase1-asan` (Linux only), `cmake-3.25.3`; inventory `tests/expected-tests.txt` (core), `tests/player/expected-tests.txt` (player) |
| Quick run command | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --test-dir build -R '^(cgb_speed_\|cgb_partition_\|age_\|cgb_fuzz_)' --output-on-failure --no-tests=error` |
| Full suite command | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --test-dir build -j8 --output-on-failure --no-tests=error` (the Phase 11-size suite takes about 43 s wall locally; budget +15 s) |
| DMG/CGB-normal identity gate | `ctest --test-dir build -R '^(dmg_baseline\|cgb_dmg_identity\|cgb_speed_identity\|banking_tracer_digest_unchanged\|cgb_runner_profile_dmg_identity)' --output-on-failure --no-tests=error` plus `measure_core --no-trace fixtures/tracer/tracer.gb` digest `4c7a57ff3d50d228` |
| Hosted-only | `ctest --preset phase1-asan --parallel 4 ...` (Linux job), `bash tests/scripts/verify-phase3-player.sh --build-package` (macOS player job) |

### Phase Requirements to Test Map (names are proposals; the planner owns final names)

| Req / Decision | Behaviour | Test Type | Automated Command (`ctest --test-dir build -R ...`) | File Exists? | Negative control |
|---|---|---|---|---|---|
| SC1 / D-03 | KEY1 reads `$7E` -> `$7F` armed -> `$FE` double -> `$7E` after return; compat/DMG unchanged; KEY0 writes never change speed or mode | white-box | `'^cgb_speed_key1_readback$'`, `'^cgb_speed_key0_no_switch$'` | Wave 0 | mutant M10 (KEY1 bit 0 not cleared); assert KEY1 after a KEY0 write sequence |
| SC1 / D-10 | Instruction cost, bus offsets, interrupt/halt literals halve in double speed (a `decode()` cost table walk + a timed program at each speed) | white-box | `'^cgb_speed_cpu_ticks$'` | Wave 0 | M15-style mutant: cost not shifted |
| SC1 / D-10 | TIMA/DIV per scanline double; pending TIMA reload keeps its remaining ticks across a switch; `remainder < period` after a switch | white-box | `'^cgb_speed_timer_scaling$'`, `'^cgb_speed_remainder_across_switch$'` | Wave 0 | M3 (timer not scaled), M11 (remainder dropped), M15 (half-dot units) |
| SC1 / D-10 | Serial internal clock: 8 bits in 4096 T at both speeds (lines halve) | white-box | `'^cgb_speed_serial_scaling$'` | Wave 0 | M2 |
| SC1 / D-10 | OAM DMA byte period halves in master time; the 159/161 M-cycle straddle; period survives a mid-DMA switch | white-box | `'^cgb_speed_dma_scaling$'` | Wave 0 | M14 |
| SC1 / D-11 | APU frame sequencer stays 512 Hz in master time; DIV-write/STOP reset edge uses the right tap | white-box | `'^cgb_speed_apu_tap$'` | Wave 0 | M4 |
| SC1 / D-10, D-13 | PPU line length (456 dots = 912 half-dots), frame (140448) and PCM sample count per master interval and RTC seconds are identical at both speeds | white-box + scan | `'^cgb_speed_ppu_apu_rtc_unscaled$'`, `'^cgb_speed_domains_scan$'` | Wave 0 | M1 (PPU scaled), M12 (RTC reads speed), scanner mutant adding `double_speed` to a `ppu_*`/`apu_*`/`rtc_*` function |
| SC1 / D-22 | Original fixture: per-phase probes (single, double, single, double): TIMA/DIV per line, serial lines, NR52 ch1 length by line, DMA straddle, KEY1 readbacks, lines across STOP; host recomputes every verdict from raw WRAM samples | fixture + stdlib derivation | `'^cgb_speed_fixture_digest$'`, `'^cgb_speed_fixture_probes$'`, `'^cgb_speed_expectations_(derive\|tampered\|factor3)$'` | Wave 0 | tampered expected table fails; clean core passes; derivation with speed factor 3 must fail the host verdicts |
| SC1 / D-19, D-20 | AGE `spsw-div` and `spsw-stop-prefetch` pass (LD B,B regs + per-row mask); applicable AGE speed and ds-STAT ROMs have pinned signatures | third-party | `'^age_'` | Wave 0 | a tampered ROM digest (fixture_digest), a signature edit in a configure-time copy of the JSON, a core mutant (stall +-1 M) that flips `spsw-div` to fail, "expected failure now passes" must fail until promoted |
| SC2 / D-05, D-06 | Stall = `GBB_SPEED_SWITCH_STALL_T` T at the destination speed in whole M-cycle steps (131076 / 262152 half-dots); `_Static_assert` multiple of `GBB_T_PER_M` | white-box + compile-time | `'^cgb_speed_stall_length$'`, `'^cgb_adr_half_dot_static_assert_mutant$'` (existing pattern; add a stall twin) | Wave 0 | M6 (+-1 quantum), M9 (stall not bounded by budget) |
| SC2 / D-07 | During the stall PPU/APU/timer/serial/DMA keep advancing (LY changes, DIV/TIMA tick at the new rate, PCM frames produced) | white-box | `'^cgb_speed_stall_devices_advance$'` | Wave 0 | M7 (devices frozen) |
| SC2 / D-06 | The stall never sets `stopped`, never reports STOPPED/HALTED_IDLE/NO_PROGRESS; sub-M-cycle budget returns BUDGET with `consumed == 0`; mid-stall budget BUDGET with `consumed > 0` | white-box + public API | `'^cgb_speed_never_stopped$'`, `'^cgb_speed_budget_semantics$'` | Wave 0 | M5 (stall sets `stopped`) |
| SC2 / D-01 | Switch only on CGB profile + CGB mode + armed; DMG profile, compat mode and unarmed STOP are byte-identical to today | white-box + existing | `'^cgb_stop_(unarmed_cgb\|compat_ignores_key1\|dmg_control)$'`, `'^cgb_speed_dmg_unarmed_unchanged$'` | exists / Wave 0 | M8 (not gated on CGB mode) |
| SC2 / D-02, D-04, D-36 | Decision table: operand `$00` vs `$FF` equal; case 1 (held button -> HALT, KEY1 stays armed, DIV not reset), case 2 (1 byte, no HALT), case 3 (pending IRQ: switch, no stall, 1 byte, dispatch if IME), case 4; unarmed held-button STOP unchanged | white-box | `'^cgb_speed_stop_cases$'`, `'^cgb_speed_stop_operand$'` | Wave 0 | flip each case predicate in a mutant (extra bit in M8 family) |
| SC2 / D-08, D-34 | IE&IF&$1F raised during the stall ends it at an M-cycle boundary; IME on dispatches, IME off resumes after STOP, no halt bug; `EI; STOP` | white-box | `'^cgb_speed_wake_ime_on$'`, `'^cgb_speed_wake_ime_off$'`, `'^cgb_speed_ei_stop$'` | Wave 0 | M13 (no wake), M16 (wake sampled per run call fails D-26) |
| SC2 / D-09 | Entering normal speed at `time%8==4` costs 4 more half-dots (stall end, early wake, case 3); recorded as `expected-failure:speed-switch-odd-mode-alignment` | white-box | `'^cgb_speed_realign$'` | Wave 0 | realign dropped |
| SC2 / D-18 | Reset clears `double_speed`, the stall and `key1_armed`, each with its own test | white-box | `'^cgb_speed_reset_(double_speed\|stall\|key1)$'` | Wave 0 | omit that field from `reset_state` in a mutant |
| SC2 / D-28 | `time_half_dots` near `UINT64_MAX` before an armed STOP -> `GBB_STOP_INVALID_STATE`, no field changed | white-box | `'^cgb_speed_headroom$'` | Wave 0 | drop the pre-check |
| SC3 / D-26 | Partitioned run equals one run across a switch and the stall (explicit digest of CPU regs, `time_half_dots`, device phases, frame digest, PCM, serial output, RTC, IF/KEY1/DIV/TIMA/LY/STAT reads) | white-box | `'^cgb_partition_'` (`stall_start_window`, `stall_end_window_seeded`, `interior_points`, `seeded_multicut`, `hostile_ie`, `held_button`, `lcd_off`, `back_to_back`, `chained`, `zero_and_subquantum`) | Wave 0 | sensitivity: shift a joypad event by one M-cycle (digest MUST change), mutate one digest input (MUST change); M16 must fail |
| SC3 / D-24 | Every named expected failure has a dispositions row pinned to current behaviour with a flip rule | CMake + Python | `'^cgb_speed_dispositions$'`, `'^cgb_speed_dispositions_mutated$'` | Wave 0 | one reason edited in a configure-time copy |
| SC3 / D-12 | No `research:12` anywhere in the gate table or core; scanner passes with the new rows | CMake + scanner | `'^model_gates'` (all), `'^model_gates_no_phase12_rows'` + `_mutated_doc` | exists + Wave 0 | existing real-file mutants + a reverted row |
| D-25 | Mutant set: 17 named mutants M1-M16 + APU-2x; each fails its named case and the same binary passes with mask 0 | configure-time | `'^cgb_speed_mutant_'` | Wave 0 | built in |
| D-27 | Fuzz `cgb_speed` mode: 8 seeds with positive controls; invariants (time monotonic and equal to the sum of consumed, `consumed <= budget`, `double_speed => CGB mode`, KEY1 consistent, never STOPPED for a CGB-mode switch, stall <= constant); one inverted oracle must raise `contract_failures` | fuzz regression | `'^cgb_fuzz_speed_regressions$'`, `'^cgb_fuzz_speed_oracle_mutant$'` + `_control` | Wave 0 | oracle mutant (compile definition on `fuzz_core.c`, no core mutant needed) |
| D-15 | Player smoke over the speed fixture pins the RGBA digest; PPU-follows-CPU mutant fails it | player e2e | `ctest -R '^player_cgb_speed_smoke'` (macOS player job) | Wave 0 | wrong pinned SHA; PPU-follows-CPU mutant (and, at core level, APU-2x via `cgb_speed_fixture_audio_digest`) |
| D-16 | Installed C and C++ consumers run an inline speed guest in partitions | installed | `'^installed_consumer_(c\|cpp)$'` | exists, extend | existing symbol-removal selftest style |
| D-14 | No public symbol added | existing | `'^cgb_consumer_symbol_coverage'` | exists | existing selftest |
| D-17 | Docs agree with code/gates | doc contracts | `'^(cgb_adr_half_dot_contract\|cgb_native_guide_contract\|cgb_tables_io\|model_gates)'` | exists, extend | existing missing-phrase/undeclared selftests; mutated KEY1 row |
| D-29, D-30 | ASan budget recorded; `measure_core --profile cgb` double-speed workload recorded (advisory) | recorded evidence | hosted job time + `12-BENCH.md`; `'^cgb_measure_core_cgb_profile$'` | exists | wrong-digest controls exist (`cgb_bench_ab_*`) |
| Pre-change pin | CGB single-speed behaviour (colour fixtures' frames + PCM, banking guest, a timer/serial/DMA program) is byte-identical to HEAD `a719721` | white-box pin | `'^cgb_speed_identity_pin$'` | Wave 0 (record FIRST) | flip one pinned digest (`--flip` style) |

### Sampling Rate
- **Per task commit:** the plan's own prefix, e.g. `ctest --test-dir build -R '^cgb_speed_(tracer|key1|stall)' --output-on-failure --no-tests=error` after `cmake --build --preset phase1` (seconds).
- **Per wave merge:** the quick run command above plus the DMG/CGB-normal identity gate; before declaring a core wave done run the full suite with `-j8`.
- **Phase gate:** full suite green locally; exact-head hosted CI green on all legs (Linux, macOS, Windows, ASan/UBSan, cmake floor, fixture-repro, player job); then `/gsd-verify-work`.

### Partition feasibility (D-26, D-29)
Measured: 22 ns/half-dot Debug and about 92 ns/half-dot ad-hoc ASan on this host (CONTEXT's 47 ns Debug figure is the hosted-Linux basis). A 1 s ASan budget is about 10 M half-dots here and 6 M hosted. Stall lengths: 131,076 half-dots to double, 262,152 to normal.
- Stall-start window (+-64 half-dots, 129 cuts): truncate every run to 4,096 half-dots after STOP retire; cost about 129 x 4.4 k = 0.6 M half-dots per scenario.
- Stall-end window: seed `cpu_stall_half_dots` (white-box, identically in the reference and each partitioned run, after running to STOP retire with an exact budget) to about 512; 129 cuts x about 1.5 k = 0.2 M half-dots. Keep ONE real-constant run per direction.
- Interior fixed points (powers of two and M-cycle boundaries +-1, about 24 per scenario) against the real constant: 24 x 140 k = 3.4 M half-dots (to-double) or 24 x 270 k = 6.5 M (to-normal); keep the to-normal real-constant scenario to 8 points.
- 256 seeded multi-cut cases with at least two cuts inside the stall: seed the stall to about 4,096; 256 x about 6 k = 1.5 M half-dots.
- Split scenarios into separate CTests so each stays near the 1 s ASan target; set explicit `TIMEOUT` (x3 under sanitizers).
- Prototype check: 387 single-cut positions (windows around 72, 131,150 and 400,000 half-dots) vs one reference run over 700,000 half-dots gave 0 mismatches in the compared state (consumed, HRAM samples, PC/SP/A). [VERIFIED: prototype]

### Wave 0 Gaps
- [ ] `tests/test_cgb_speed_internal.c` (+ partition cases), `tests/test_age.c`
- [ ] `fixtures/cgb-speed/` (asm, manifest, LICENSE), `fixtures/age/` (13 ROMs + rights/provenance files + manifest)
- [ ] `tests/scripts/{derive-cgb-speed-expectations.py, verify-cgb-speed-dispositions.py, verify-speed-domains.py, reproduce-cgb-speed.sh, reproduce-age.sh, test-reproduce-*.sh}`, `tests/external/cgb-speed-dispositions.json`, `tests/check_no_phase12_rows.cmake`, `tests/fuzz/fuzz_core.dict`
- [ ] Pre-change identity pin recorded from the UNMODIFIED core before any `gabbaboy.c` edit
- [ ] `gbb_test_speed_state` seam; mutant generator in `tests/CMakeLists.txt`; `cmake/ExpectedTests.cmake` Windows list; `tests/player/CMakeLists.txt` branches; `fixture-repro.yml` steps and pin cross-check
- Framework install: none.

## Security Domain

`security_enforcement` is enabled (ASVS level 1, block on high; `.planning/config.json`).

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication / V3 Session | no | no accounts or sessions; CI uses short-lived tokens only |
| V4 Access Control | no | - |
| V5 Input Validation | yes | guest-controlled KEY1/STOP/IE/IF/P1 sequences handled by a closed decision table; operand value ignored; fail-closed preflight of only fetched bytes (D-04, D-073); manifests/recipes validated by allow-list regexes in repro scripts; JSON via CMake `string(JSON)` / Python stdlib |
| V6 Cryptography | no new use | SHA-256 only as integrity pins (existing `src/accept/sha256.c`) |
| V12 Files and Resources | yes | ROM/save/state bounds: no new allocation; `cpu_stall_half_dots` is `uint32_t` bounded by the constant plus 4; `UINT64_MAX` headroom pre-check before any mutation (E4) |
| V14 Configuration / supply chain | yes | AGE pinned by commit and tree, ROMs by SHA-256, rights files, install-scan guard, RGBDS archive digest pins, no new Actions or packages |

### Known Threat Patterns for this stack
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Hostile guest keeps arming KEY1 and executing STOP to stretch emulated time or starve the host | DoS | each stall is bounded (<= 262,156 half-dots) and consumed only within the caller's budget; every step re-checks budget, audio capacity and headroom; fuzz mode `cgb_speed` with invariants |
| Time-counter overflow near `UINT64_MAX` mid-switch leaving a half-applied switch | Tampering | pre-check before the switch plus per-step check; `cgb_speed_headroom` |
| Stale stall/double-speed state after reset or ROM swap leaking between guests | Info disclosure / Tampering | D-18 reset clears and per-field tests; instance isolation tests (`cgb_instance_isolation`) |
| Third-party ROM with unclear rights or swapped bytes in required CI | Tampering / Repudiation | MIT + CC0 documentation, pinned commit/tree, SHA-256 manifest, fixture-repro byte rebuild, `age_not_installed` scan so the ROMs never ship in packages |
| Recipe-field injection in repro scripts | Tampering | argument lists, allow-list regexes (copy `reproduce-cgb-colour.sh`) |
| Hang in a third-party ROM wedging CI | DoS | per-ROM measured budget (x2), explicit `TIMEOUT`, distinct timeout exit code |

## Recommended plan decomposition (aligned to D-32; tracer first)

D-32's six waves are kept as the ordering of CORE work (a single owner of `src/core/gabbaboy.c` at a time). Two things are re-ordered for risk: the thin vertical slice leads (user instruction), and the AGE vendoring runs as an independent track from the start because it needs no core code and it is the only route to learn the Linux digests early. File ownership for parallelism: `src/core/gabbaboy.c` one plan at a time; `tests/CMakeLists.txt` and `tests/expected-tests.txt` via per-plan marker blocks; docs per plan.

| # | Plan | Wave (D-32) | Depends on | Delivers | Key tests |
|---|------|-------------|------------|----------|-----------|
| 12-01 | **Tracer slice** | 1+2 (thin) | - | FIRST commit: pre-change identity pins recorded from the unmodified core (`cgb_speed_identity_pin`). THEN: fields, `gbb_test_speed_state`, KEY1 readback, minimal `stop_case` (case 4 only), `divider_reset(clock_apu_edge)`, `cpu_ticks` at the five sites (cost, bus offsets, interrupt/halt literals), minimal stall branch, GATE-74 latch removed, `cgb_stop_armed_cgb` flipped, reset clears; runtime-mask mutant generator with two mutants (M5, M7) | `cgb_speed_tracer_switch` (arm + STOP flips KEY1 `$7F` -> `$FE`, loads the stall, resets DIV) with `cgb_speed_mutant_*` controls; full suite green; model-gate tags/rows for the new helpers so `model_gates` stays green |
| 12-02 | Device scaling | 2 | 12-01 | tick-unit countdowns (reload, serial, DMA), divider per half-dot in double speed, APU tap, `timer_reload_hd`, GATE-30/31/53/54/55/56 rows, scaling gate row | `cgb_speed_{cpu_ticks,timer_scaling,serial_scaling,dma_scaling,apu_tap,remainder_across_switch,ppu_apu_rtc_unscaled}`, `cgb_speed_domains_scan`, mutants M1-M4, M11, M12, M14, M15, `dmg_baseline` |
| 12-03 | STOP decision table, wake, realign, headroom | 3 | 12-02 | cases 1-3, D-04 preflight, D-08 wake, D-09 tail kind, D-34 sampling, D-28 pre-check, D-36 | `cgb_speed_{stop_cases,stop_operand,wake_*,ei_stop,realign,never_stopped,budget_semantics,headroom,dmg_unarmed_unchanged}`, M8, M9, M10, M13, M16 |
| 12-04 | Gate dispositions and stall constant | 3 | 12-03 | D-12 rows/tags (incl. GATE-41 -> 14, GATE-52, GATE-62 split, GATE-74 reword, new GATE-84..), `GBB_MG_STOP_TAG_REGEX` update, `GBB_SPEED_SWITCH_STALL_T` static assert + mutant, `check_no_phase12_rows.cmake` | `model_gates*`, `model_gates_no_phase12_rows` (+ mutated doc), stall static-assert mutant |
| 12-05 | Original fixture | 4 | 12-03 | `fixtures/cgb-speed/`, derivation script, host test, repro script + fixture-repro step, `test-reproduce-*` controls | `cgb_speed_fixture_*`, `cgb_speed_expectations_*`, `cgb_speed_fixture_audio_digest` |
| 12-06 | Partition tests | 4 | 12-03 | window, seeded-stall and multi-cut sweeps, sensitivity controls | `cgb_partition_*` |
| 12-07 | Fuzz | 4 | 12-03 | `cgb_speed` mode, 8 seeds with controls, oracle mutant, dictionary | `cgb_fuzz_speed_*` |
| 12-08 | **AGE vendoring (independent track, may start at once)** | 5 (early) | - | `fixtures/age/` 13 ROMs + rights files + manifest, `reproduce-age.sh` (`--self-check`/`--compare`), fixture-repro step, `age_not_installed` (+selftest), `THIRD_PARTY_NOTICES.md` | `age_fixture_digest`, `age_repro_selfcheck`, `age_not_installed*` |
| 12-09 | AGE driver, dispositions, sensitivity sweep | 5 | 12-03, 12-08 | `tests/test_age.c`, `cgb-speed-dispositions.json` + verifier + docs mirror, D-21 sweep results recorded | `age_*` (13), `cgb_speed_dispositions*` |
| 12-10 | Player claims, smoke, consumers | 6 | 12-05 | E2 claims edit, `player_cgb_speed_smoke` (+ mutants), inline-guest consumers | `player_cgb_speed_*` (macOS job), `installed_consumer_*` |
| 12-11 | Docs | 6 | 12-04, 12-09 | all files in "Docs to update"; D-070 `[VERIFY]` resolved | doc contracts, `cgb_tables_io` |
| 12-12 | Close-out | 6 | all | `measure_core` double-speed record (`12-BENCH.md`), hosted ASan wall time vs GB-CI-004, mutant build count, DECISIONS D-084+ (stall constant, STOP cost, `clock_apu_edge`, claims edit), LESSONS, STATE handoff naming Phase 13 "CGB HDMA" and its exact `/gsd-plan-phase 13` command, summary coverage blocks | `summary_coverage`, full suite, hosted CI |

Notes for the planner: (1) 12-01 must not start with the `gabbaboy.c` edit; its first task records the pins. (2) 12-02 through 12-04 are sequential on one file; 12-05/06/07 can run in parallel after 12-03 (tests only). (3) 12-08 can start on day one and should reach CI early. (4) Every plan SUMMARY uses the block coverage schema (D-31). (5) Stop after the phase; do not chain into Phase 13 (D-33, AGENTS.md).

## Sources

### Primary (HIGH confidence) - read this session
- `src/core/gabbaboy.c` (struct, KEY1/IO tables, timer/serial/DMA/divider/APU/advance, decode/execute/STOP, run loop), `src/core/gabbaboy_test.h`, `include/gabbaboy/gabbaboy.h`
- `tests/CMakeLists.txt` (registration, mutants, model gates, dispositions, ADR, guide contracts, fixtures), `cmake/{ExpectedTests,VerifyFixtureManifest,ScanForbiddenFixtures,VerifyDocContract,RunInstalledConsumer}.cmake`, `tests/expect_exit.cmake`, `tests/check_no_phase11_rows.cmake`
- `tests/{fuzz_core.c,test_fuzz_core.c,test_control.c,test_cgb_visibility.c,test_cgb_tables.c,test_cgb_colour_internal.c,measure_core.c}`, `tests/consumers/c/main.c`, `tests/player/{CMakeLists.txt,cgb_smoke.cmake,claims_agree.cmake}`, `tests/scripts/{verify-model-gates.py,verify-external-dispositions.py,reproduce-cgb-colour.sh,reproduce-magentests.sh,run-bounded-fuzz.sh}`, `tests/external/cgb-ppu-dispositions.json`
- `docs/{model-gates,cgb-profile,native-integration,preview,cartridge-and-saves,mbc3-rtc-evidence}.md`, `docs/support/unreleased.md`, `src/player/{main.c,limitations.h}`, `README.md`, `.github/workflows/{ci,fixture-repro,preview}.yml`
- `.planning/{STATE,REQUIREMENTS,config}`, `.planning/context/{DECISIONS,LESSONS}.md`, `.planning/research/v0.2/STACK.md`, Phase 11 `11-RESEARCH.md` and `12-CONTEXT.md`/`12-DISCUSSION-LOG.md`
- AGE source at `c-sp/age-test-roms@1f5bc10e2cb60b86c19f8d0287ff78f410c4f639` (git tree `2fece1a678edb18c1664efd7328a430a79c70be4`): `Makefile`, `src/_include/{test-setup,macros,utilities}.inc`, the 13 ROM sources, `src/speed-switch/caution/WARNING.md`, `LICENSE`
- Local measurements: Debug and ad-hoc ASan timings, 13-ROM rebuild with RGBDS 1.0.1 (archive digest verified), full-suite run of the prototype copy, AGE row matrices

### Secondary (MEDIUM)
- SameBoy `c4cf7abab79a`, Gambatte, Pan Docs, mGBA facts as summarised in `12-CONTEXT.md` (not re-fetched)

### Tertiary (LOW)
- Hosted CI timing extrapolation from LESSONS GB-CI-004 numbers

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - nothing new; pins read from manifests.
- Architecture / code map: HIGH - every cited line was read; the conversion table was validated by a prototype that passed the whole existing suite.
- AGE outcomes: MEDIUM-HIGH - prototype, tagged as such; signatures must come from the committed core.
- Pitfalls: HIGH for codebase-specific ones (each was observed or read); MEDIUM for hosted timing.

**Research date:** 2026-10-13
**Valid until:** 2026-11-12 (the repo is the moving part; re-check line numbers if `src/core/gabbaboy.c` changes before planning)

