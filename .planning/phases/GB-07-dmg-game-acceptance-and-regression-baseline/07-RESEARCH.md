# Phase 7: DMG Game Acceptance and Regression Baseline - Research

**Researched:** 2026-10-10
**Domain:** Portable C17 Game Boy emulator test harness (runner, CTest inventory, CI, SDL3 player smoke), fixture rights admission, frozen regression baseline
**Confidence:** HIGH for code seams and CI mechanics (read in this session); MEDIUM for the two pre-freeze investigations (hypotheses, not conclusions)

<user_constraints>
## User Constraints (from 07-CONTEXT.md)

The authoritative text is `.planning/phases/GB-07-dmg-game-acceptance-and-regression-baseline/07-CONTEXT.md` (D-01..D-38). It is LOCKED. This block lists each decision in condensed form; if wording differs, CONTEXT.md wins.

### Locked Decisions
- **A. Admission (GAME-01, G5).** D-01 vendor digest-pinned `fixtures/libbet/libbet.gb` (SHA-256 `3607412031c8287cf878299ce96e581e85b852dde703806343b95576fa3ff1a9`, 32768 B, commit `46a765a2c01701bffb8c0b7dd6e4be3a6b193090`, never the tag); D-02 separate opt-in `.github/workflows/libbet-repro.yml` + `tests/scripts/reproduce-libbet.sh` (RGBDS 0.7.0 by archive SHA-256, Pillow 12.3.0 via `pip --require-hashes`, `contents: read`, never writes back, not folded into `fixture-repro.yml`); D-03 reproducibility statement only after a real run URL exists; D-04 G5 checklist (a)-(f); D-05 fail-closed Python verifier + 5 mutated-manifest negative CTests + 1 positive control; D-06 `THIRD_PARTY_NOTICES.md` row, `fixtures/libbet/SOURCES.md`, `.gitattributes`; D-07 no game swap, stop and report the missing item.
- **B. Predicate/input/controls (GAME-02, EVID-01).** D-08 guest-state predicate on 2 consecutive frame boundaries; D-09 compiled address table keyed by ROM digest with ROM anchor bytes, named predicate `libbet-tutorial-cleared`; D-10 `gbinput 1` grammar; D-11 time units `hd`/`f`(=140448)/`s`(=8388608), 600 s ceiling; D-12 parse bounds and `invalid-script: line N: <reason>` exit 2; D-13 acceptance script content; D-14 controls N1/N2/N3 + truth table + core-mutant; D-15 `advance_to(deadline)`; D-16 PCM evidence and non-silence gate (p2p >= 2048 and >= 4800 changes per channel, window `play_start`..`T_hit+1 s`); D-17 SGB tolerance; D-18 two-pass stall diagnosis; D-19 two pre-freeze investigations (mixer +-32768, early Start taps).
- **C. Runner/manifest (EVID-01).** D-20 compiled Mooneye `cases[]` and its manifest digest unchanged; new `tests/acceptance/cases.txt` key=value; D-21 key whitelist; D-22 `case_applicability()` semantics and exit 4; D-23 CLI (`--acceptance`, `--case|--suite`, `--model`, `--revision`, `--failure-dir`, `--receipt`, `--observe`); exit codes 0/1/2/3/4; D-24 canonical RGB digest (`GBB-RGB888-v1 160x144\n` header + 160x144x3 bytes; shade map 255/170/85/0; PPM on failure only); D-25 checkpoints `title`/`play_start`/`mid`/`hit` + rolling digest; D-26 digest independence/labels; D-27 ROM buffers to heap (8 MiB cap); D-28 parser bounds; D-29 harness layout and inventory.
- **D. Baseline + player (EVID-02, GAME-03).** D-30 `tests/baseline/dmg-cpu-b-v1.txt`; D-31 identity definition (inventory = monotonic superset); D-32 benchmarks advisory; D-33 no per-OS ledgers; D-34 approved-change protocol (`baseline: <reason>` commit, `CHANGES.md`, no `--update`); D-35 single entry `tests/scripts/verify-dmg-baseline.sh` registered as CTest, runs in all three native jobs; D-36 `--input-script` on `--smoke-package` path, packaged extracted player, dummy SDL drivers, `smoke_report ...` line, PCM digest equals headless; D-37 player smoke on macOS only; D-38 flag policy.

### Claude's Discretion
- Source file split inside `src/runner/`; helper names; receipt formatting.
- Whether the G5 verifier extends `verify-support-ledger.py` or is a sibling script.
- Exact PCM threshold values after first-run calibration (record observed numbers).
- Plan/wave ordering (suggested: admission, runner parser/digest/stepping, acceptance+controls+investigations, player smoke, baseline freeze last).

### Deferred Ideas (OUT OF SCOPE)
Linux/Windows packaged-player smoke; migrating the Mooneye table into `cases.txt`; `fibonacci-ldbb`/`screen-text`/`rtc_policy` oracles; benchmark regression threshold; promoting `libbet-repro` to required; second game (Tobu Tobu Girl, needs G2); independent-emulator cross-checks committed to the repo.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| GAME-01 | Admit one rights-clear DMG game under a fail-closed manifest | Fixture layout and CTest patterns (Standard Stack, Code Examples 1); verifier negative-control design; G5 closure; Windows python pitfall |
| GAME-02 | Scripted emulated-time input reaches guest-memory predicate, with no-input negative control, on 3 OSes | Runner seams, predicate/stepping/zero-consume evidence, timing budgets measured under Debug and ASan, exit-code wrapper pattern |
| GAME-03 | Packaged SDL3 player launches game, passes automated input/progress/audio smoke | Player CLI parse seam, `advance_to`, ns/half-dot round trip proof, macOS-only gating, PR-only `player_required` finding |
| EVID-01 | Runner captures `LD B,B` frame as canonical RGB digest, replays input, honours model fields, no new dependency | Runner seams; Mooneye frame availability measurement (two of three cases complete no frame); `test_runner.c` textual-include constraint |
| EVID-02 | Frozen DMG baseline + single byte-identity check | Inventory mechanism, baseline layout, per-OS and line-ending pitfalls, benchmark reuse |
</phase_requirements>

## Summary

The discuss phase fixed the design; this research establishes where the code is, what will break when it is changed, and what the cost is. Five facts materially affect planning. First, `tests/test_runner.c` does `#include "../src/runner/main.c"` (textual unity), so splitting the runner into several translation units, moving the static SHA-256 and moving ROM buffers to the heap (D-27) all require editing `test_runner.c` and CMake in the same change. Second, the Mooneye `LD B,B` frame (D-30 "`mooneye.<id>` canonical frame digest") does not exist for two of the three admitted cases: `tim00` and `tim00_div_trigger` reach `LD B,B` at 35048 and 32920 half-dots, before the first frame completes (~140448 half-dots), so `gbb_copy_frame` returns `GBB_FRAME_NOT_READY` (17). `daa` completes a frame (12 generations) and the frame is uniformly shade 0. The baseline and D-24's "no completed frame is an error" rule need an explicit reconciliation (Open Question 1). Third, a 3600-frame Libbet run costs 11.2 s on a Debug (-O0) core and 84.5 s under ASan/UBSan on this machine, and ci.yml runs the full CTest inventory under both. Test timeouts and control budgets must be chosen deliberately. Fourth, no existing core CTest case calls `bash` or `python3`; Windows CI has never run either from CTest, so the verifier registration is a real platform risk. Fifth, the mixer investigation has a concrete lead: Libbet writes NR50=`$77`, NR51=`$FF` and the core multiplies each channel by `(NR50 volume + 1)` without scaling, so a single full-volume pulse (14336 x 8) exceeds s16 by 3.5x before the saturating conversion.

**Primary recommendation:** Build a small shared acceptance library (`src/accept/`: sha256, input_script, digest, predicate table, deadline stepper) compiled once and linked into the runner, `test_runner`, and the player adapter. Implement the baseline comparator as a CMake script-mode check with `tests/scripts/verify-dmg-baseline.sh` as a thin `bash` entry point. Resolve the mixer investigation before any PCM digest is blessed. Freeze the baseline last.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Guest stepping, JOYP, PCM, frame copy | Core library (`src/core/gabbaboy.c`, public API) | none | Integer-only, deterministic; the evidence source. Not modified except if D-19(i) finds a defect |
| Input script parse, predicate table, deadline stepping, RGB/PCM digest | New shared acceptance library (adapter-side, no host timing) | Runner + player | Host-independent, shared by both frontends so player PCM equals runner PCM |
| Case file parsing, applicability, receipts, exit codes | Runner (`gabbaboy-runner`) | none | Developer diagnostic tool; the only place that reads files for acceptance |
| Rights/provenance admission | Python verifier (`python3 -I`, stdlib) + CTest | opt-in repro workflow | JSON manifests are metadata only; runner never parses JSON (D-20) |
| Baseline ledger + identity check | CMake script / bash entry, text-only compare | CI jobs | Ledger is plain `key<TAB>value`; check compares text from `--observe` output |
| Player smoke | SDL3 player (`--smoke-package --input-script`) | `verify-phase3-player.sh` | Same session step and input path as keyboard; macOS package only (D-37) |
| Required-gate aggregation | `ci.yml` `required-native` + `check-player-result.sh` | none | Existing exact-head mechanism (D-017) |

## Standard Stack

No new runtime or build dependencies. Everything is existing in-repo code or the standard toolchain already required.

### Core
| Component | Version / Source | Purpose | Why Standard |
|-----------|------------------|---------|--------------|
| C17 + CMake >= 3.25 (floor job runs 3.25.3) | `CMakeLists.txt:1` `cmake_minimum_required(VERSION 3.25)` [VERIFIED: CMakeLists.txt:1] | Build, CTest | Existing; keep every new CMake construct valid at 3.25 (`string(REPLACE)`, `string(JSON)` (3.19), `file(STRINGS)`, generator expressions are fine) |
| Runner SHA-256 (`src/runner/main.c:62-85`) | in-repo | All digests | Owner preference "copy over dependency"; move into a shared `.c` rather than duplicate |
| Python 3 stdlib, `python3 -I` | `tests/scripts/verify-support-ledger.py` pattern | G5 verifier | Existing pattern (D-05); locate via `find_package(Python3 COMPONENTS Interpreter REQUIRED)` as `tests/player/CMakeLists.txt` already does, never a bare `python3` in `add_test` (Windows) |
| CTest + `verify-test-inventory.sh` | `.github/scripts/verify-test-inventory.sh` | Exact inventory | Existing (GB-CI-003) |

### Supporting / opt-in (not in required path)
| Tool | Version | Purpose | Note |
|------|---------|---------|------|
| RGBDS | 0.7.0 (Linux `f67bc8fd...c3297210`, macOS `f2aee823...a385a583a16` per D-02) | `libbet-repro.yml` only | Values locked by CONTEXT.md, carried over `[CITED: 07-CONTEXT.md D-02]`; not re-verified this session |
| Pillow | 12.3.0 via `pip --require-hashes` | `libbet-repro.yml` only | Same; build-time only, never installed globally |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Python verifier for G5 | `cmake -P` with `string(JSON)` | Removes Python from Windows CTest, but D-05 chose Python; keep Python and use `find_package` |
| `bash` baseline script as the check itself | CMake script-mode check wrapped by the `.sh` | See Pitfall 4 |

**Installation:** none. **Package Legitimacy Audit:** no package is added to any required path; `Packages removed [SLOP]: none`, `[SUS]: none`. The two opt-in tools above are exactly those locked in D-02 and run only inside the non-required workflow (the planner should still pin by hash as D-02 states; they are `[ASSUMED]` here for registry legitimacy because the check seam was not run).

## Architecture Patterns

### Data flow
```
cases.txt (key=value) --parse/validate whole file--> case[] --applicability(model,revision)--> eligible | excluded(exit 4) | xfail
  case.input_script --parse (all-or-nothing)--> events[] (absolute half-dots)
  ROM (heap, size+SHA checked) --gbb_load_rom--> instance
  loop: queue next <=64 events inside window -> advance_to(deadline) [gbb_run_audio, accept HALTED_IDLE, zero-consume tolerance]
        -> per completed frame: gbb_copy_frame -> rolling digest; checkpoint capture (first frame completed >= requested time)
        -> PCM -> whole-stream SHA-256 (LE int16 L,R) + window stats
        -> frame boundary: predicate(gbb_peek_ram) x2 consecutive -> T_hit
  -> receipt line(s) / --observe digests / PPM only on failure -> exit 0/1/2/3/4
baseline check: build -> ctest (JUnit) + runner --observe (all workloads) --> text compare vs tests/baseline/dmg-cpu-b-v1.txt (+ CHANGES.md rule)
player: packaged player --smoke-package --input-script -> same parser/predicate/stepper -> smoke_report line (PCM digest == headless)
```

### Recommended file list (create / modify)

**Create**
- `fixtures/libbet/{libbet.gb,manifest.json,LICENSE.txt,SOURCES.md}`
- `tests/scripts/verify-libbet-admission.py` (or extend `verify-support-ledger.py`; discretion), `tests/scripts/reproduce-libbet.sh`, `.github/workflows/libbet-repro.yml`
- `src/accept/{sha256.[ch],input_script.[ch],digest.[ch],predicate.[ch],stepper.[ch]}` (names are discretion; keep out of `src/core`)
- `src/runner/{cases.c,acceptance.c}` (case-file parser, applicability, run orchestration) plus `main.c` edits
- `tests/acceptance/{CMakeLists.txt,cases.txt,inputs/*.input,negative/*}`
- `tests/test_acceptance_parse.c`, `tests/test_acceptance_predicate.c` (truth table + anchor bytes), `tests/expect_exit.cmake` (exit code + regex wrapper)
- `tests/baseline/{dmg-cpu-b-v1.txt,CHANGES.md}`, `tests/scripts/verify-dmg-baseline.sh`, `cmake/VerifyDmgBaseline.cmake`
- `docs/` addition: Libbet scope statement + player-platform limitation in the next support ledger (`docs/support/`; the existing ledger is `docs/support/v0.1.0.md`, verified by `tests/scripts/verify-support-ledger.py` against Git tags, so add a new ledger file only per its versioning rule, not by editing v0.1.0)

**Modify**
- `CMakeLists.txt`: runner sources; `add_library` for shared acceptance code; extend the `git diff --quiet HEAD -- CMakeLists.txt include/gabbaboy/gabbaboy.h src/core/gabbaboy.c src/runner/main.c` list (lines ~49-50) so build-qualification covers the new files `[VERIFIED: CMakeLists.txt]`; player adapter gets the shared sources
- `tests/CMakeLists.txt`: `add_subdirectory(acceptance)`, `set_tests_properties(... TIMEOUT)`, update `runner_help` expectations (`tests/verify_runner_help.cmake` lists required help strings)
- `tests/test_runner.c` (textual include, `MAX_ROM` stack arrays), `tests/expected-tests.txt`, `tests/player/expected-tests.txt` + `tests/player/CMakeLists.txt` foreach branches
- `src/player/main.c` (CLI parse at ~2092-2125 and `run_smoke`), `tests/scripts/verify-phase3-player.sh`
- `.gitattributes`, `THIRD_PARTY_NOTICES.md`, `.github/workflows/ci.yml` (only if a step is needed beyond CTest; see Pitfall 6), `.planning/context/{DECISIONS,LESSONS}.md`

### Pattern 1: Deadline stepping (D-15)
Existing player `advance_to` (`src/player/main.c:580-621`) is the template: it loops `gbb_run_audio` with `budget = remaining`, treats `GBB_STOP_BUDGET` and `GBB_STOP_OUTPUT_FULL` as continue, and returns on `consumed == 0`. It does NOT accept `GBB_STOP_HALTED_IDLE` (it errors "Guest stopped"), but Libbet is halted-idle in 3801 of 3811 calls (measured below), so the shared stepper must accept HALTED_IDLE.

Measured on the pinned ROM, 3600 frames, `gbb_run_audio(budget=end-t, 4000-frame buffer)`: `t=505612800 calls=3811 zero=0 idle=3801 min=-32768 max=32265` (left channel) [VERIFIED: scratchpad probe run this session]. Note: no zero-consume occurred in this loop shape (budget = remaining to a far deadline); zero-consume was observed in the discuss research only near a short deadline (remainder 8). Keep the D-15 tolerance and a hard iteration guard regardless.

### Pattern 2: Exit-code assertion wrapper
CTest `WILL_FAIL` accepts any non-zero exit, which cannot distinguish exit 1 from 2/3/4 (all new codes carry meaning). Use a `cmake -P` wrapper like the existing `tests/expect_runner_failure.cmake`, generalised to `-DGBB_EXPECT_CODE=<n> -DGBB_EXPECT_REGEX=<re>` and comparing the exact code. Note that file treats `result MATCHES "^-1$"` specially; a new wrapper must compare numerically.

### Anti-Patterns to Avoid
- Introducing `SKIP_RETURN_CODE` for exit 4 (forbidden by D-22 and rejected by `verify-test-inventory.sh`, which fails on any `<skipped`) [VERIFIED: .github/scripts/verify-test-inventory.sh:20-23].
- Adding a second copy of SHA-256 in the player (move the one in `main.c`).
- Counting completed PPU frames as the time base (drift while LCD is off).
- Hashing `printf`-formatted text or struct memory (D-33).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SHA-256 | A second implementation | Move the existing one (`src/runner/main.c:62-85`) to a shared file | Already tested by Mooneye digests |
| JSON in C | A mini JSON parser | Python verifier for JSON; runner reads `key=value` only | D-20 |
| Bounded file read | New `fread` helpers | `read_bounded` (`main.c:87`), generalised to heap + larger cap | Existing overflow checks |
| Exact-test-inventory | New inventory scheme | `tests/expected-tests.txt` + `gabbaboy_verify_registered_tests()` | Two checkers already enforce it |
| Benchmark protocol | New timing harness | `tests/measure_core.c` + `tests/scripts/measure-release-baseline.sh` | Already records revision/build/hardware/samples/uncertainty |
| Windows CRLF handling | Ad hoc `tr` calls | `.gitattributes eol=lf` for digested text + `\r` strip in the comparator | See Pitfall 3 |

## Runtime State Inventory
Not a rename/refactor phase. Omitted. (One migration-like element: ROM buffers moving from stack to heap, D-27; code-only.)

## Exact Code Seams (verified this session)

**`src/runner/main.c` (288 lines)**
- `#define MAX_MANIFEST 65536u`, `#define MAX_ROM 32768u` [VERIFIED: main.c:15-16]. `uint8_t rom[MAX_ROM+1]` stack arrays at `run_one` (main.c:210) and `uint8_t manifest_bytes[MAX_MANIFEST+1]` (main.c:278); `load_case_rom` takes `uint8_t rom[MAX_ROM+1]` (main.c:111) and requires `n==MAX_ROM` (exact 32768).
- `fixture_case cases[]` compiled table (main.c:44-60), three Mooneye cases with `pass_registers {3,5,8,13,21,34}` and `fail_registers {0x42 x6}`, budgets 2000000/200000/200000 half-dots. `MOONEYE_MANIFEST_SHA256 "98a1799b..."` (main.c:26). D-20: leave unchanged.
- Existing exit codes: 0 pass, 1 fail, 2 invalid input, 3 unsupported/timeout (`run_one` main.c:220, `main` main.c:266-288). `main` first checks `argc==2&&strncmp(argv[1],"--",2)!=0` -> `run_original_tracer` (a bare ROM path); keep that path intact.
- CLI is a hand-rolled `for` loop over `argv` with `--manifest/--case/--suite/--receipt/--help`; anything else -> `invalid-arguments` exit 2. `print_usage` text is asserted by `tests/verify_runner_help.cmake` (requires strings `--manifest <manifest.json> --case <id> [--receipt]` and `--manifest <manifest.json> --suite [--receipt]`); new usage lines must be added without removing these.
- Trace/protocol: `run_guest` uses `gbb_run_ex` with a 128-record trace, 4096 diagnostics, chunk `RUN_CHUNK 2048` half-dots; Mooneye result is `opcode[0]==0x40` (LD B,B) at `result_pc` with register closure. `suite_counts_valid(eligible,executed)` requires `eligible!=0 && eligible==executed`.
- `read_bounded(path, buf, capacity, &len)` uses `fopen(path,"rb")` and reads `capacity+1` to detect overflow (main.c:87-91): the pattern D-28 asks to reuse.

**`tests/test_runner.c`** textually includes the runner: `#define main gbb_runner_program_main` / `#include "../src/runner/main.c"` / `#undef main` [VERIFIED: tests/test_runner.c:6-9], and uses `uint8_t rom[MAX_ROM+1]`, `read_bounded`, `hash_matches`, `cases[0]`, `run_guest` directly (test_runner.c:24-30). Any signature change (heap ROM, moved SHA) breaks this file. `tests/scripts/verify-phase2-hosted.sh:37` also lists `src/runner/main.c tests/test_runner.c tests/CMakeLists.txt tests/expected-tests.txt` as watched paths; review it when files move.

**`include/gabbaboy/gabbaboy.h` (contracts the harness depends on)**
- `gbb_queue_events`: "Copies events into a fixed 64-event per-instance queue. Timestamps are absolute half-dot ticks and must be nondecreasing within the batch and no earlier than the instance's current time." Over-capacity returns `GBB_EVENT_QUEUE_FULL` (checked before content); rejected batches append nothing; consumed events free capacity [VERIFIED: gabbaboy.h:157-172].
- `gbb_button` enum: `RIGHT=0, LEFT=1, UP=2, DOWN=3, A=4, B=5, SELECT=6, START=7` (matches the D-10 button list order) [VERIFIED: gabbaboy.h:58-67]. Events: `GBB_INPUT_BUTTON_PRESS = 3`, `GBB_INPUT_BUTTON_RELEASE = 4`; struct `gbb_input_event {uint64_t at_half_dots; gbb_input_event_kind kind; uint8_t value;}` [VERIFIED: gabbaboy.h:51-73].
- `gbb_copy_frame(instance, pixels, capacity_bytes, pitch_bytes, gbb_frame_info*)` -> shade bytes 0..3; `gbb_frame_info {width,height,generation,completion_half_dots}`; `GBB_FRAME_NOT_READY` only after valid args; reset invalidates the frame [VERIFIED: gabbaboy.h:115-120,173-185].
- `gbb_run_audio(instance, budget, frames, frame_capacity, &count)`: 48 kHz s16 L,R; stops with `GBB_STOP_OUTPUT_FULL` before an instruction that could exceed capacity; returns early with `GBB_STOP_HALTED_IDLE` [VERIFIED: gabbaboy.h:213-223 and enum at 38-49]. `gbb_stop_reason` values: `BUDGET=0, UNSUPPORTED_OPCODE, TRACE_FULL, INVALID_STATE, UNSUPPORTED_BUS, LOCKUP, HALTED_IDLE, STOPPED, NO_PROGRESS, OUTPUT_FULL = TRACE_FULL`.
- `gbb_peek_ram`: WRAM C000-DFFF (+echo) and HRAM only; other addresses return 0xFF [VERIFIED: gabbaboy.h:224-227]. All Libbet predicate addresses are WRAM (`$C4E8..$C5A3`), so this suffices.
- No public API change is needed or recommended.

**`src/core/gabbaboy.c` JOYP** (for the core-mutant, D-14): `joypad_value` at lines 532-538:
`if ((m->joypad_select & 0x20u) == 0) lines &= (uint8_t)~((m->joypad_buttons >> 4) & 0x0Fu);` and `if ((m->joypad_select & 0x10u) == 0) lines &= (uint8_t)~(m->joypad_buttons & 0x0Fu);` [VERIFIED: src/core/gabbaboy.c:532-538]. Mutant pattern candidate: replace the first condition's `& 0x20u) == 0` with `& 0x20u) != 0`. Configure must fail unless the pattern occurs exactly once (count with `string(FIND)` or `string(REGEX MATCHALL)`). Event application is at lines 1004-1011 (`joypad_buttons |= 1u<<value`).

**Player (`src/player/main.c`, 2271 lines)**
- Diagnostic dispatch at 2091-2125: booleans `smoke`, `audio_dummy_smoke`, `audio_measure`, `audio_device_status`, `package_smoke = argc == 3 && strcmp(argv[1], "--smoke-package") == 0`, `battery_store`, `battery_resume`; the usage guard rejects any other argc shape. Adding `--smoke-package <invalid-rom> --input-script <file>` needs a new argc shape (5 args) in both the boolean and the guard, and the usage string at line 2113.
- `package_smoke` -> `run_smoke(&app, demo_rom_path, invalid_rom, argv[0], battery_fixture_path)` (line ~2222). The demo ROM path comes from `resolve_demo_rom_path(requested_demo_rom, package_smoke)` (packaged resolution). The Libbet ROM must be resolved the same way from the package (see below) and the package assembler must include it.
- `advance_to` at 580-621 (above); `smoke_send_z` (1466-1495) shows how the smoke injects SDL key events with a bounded timestamp: it computes `elapsed = cursor - anchor` and sends at `host_anchor_ns + ns(elapsed + 8 half-dots)`. A scripted smoke must use exact script times, not `cursor + 8`, or its events will land at different half-dots than the headless run and the PCM digests will differ.
- Key mapping (`src/player/input.c`): RIGHT/LEFT/UP/DOWN -> arrows, `A` -> Z, `B` -> X, `START` -> Return, `SELECT` -> Right Shift [VERIFIED: src/player/input.c:`map_scancode`]. The script's `tap START` therefore drives `SDL_SCANCODE_RETURN`.
- Time conversion is exact for script times: `player_input_half_dots_to_nanoseconds` rounds UP, `player_input_nanoseconds_to_half_dots` truncates; the round trip returns the original half-dot because the ceil excess is < 1 ns (~0.0084 half-dot) [VERIFIED: src/player/input.c:7-38 plus arithmetic]. Pending input queue: capacity 64, normal 56 (`PLAYER_INPUT_QUEUE_CAPACITY 64u`, `PLAYER_INPUT_NORMAL_CAPACITY 56u`) [VERIFIED: src/player/input.h]; feed in windows, as the runner does.
- Player PCM goes through `player_audio_submit` in 512-frame chunks; core partition invariance (test `audio_partition`, `docs/audio-and-playback.md` "guest partition digest") makes the PCM stream independent of chunking, so a digest taken from the frames returned by `gbb_run_audio` inside the player equals the headless digest if events fire at identical half-dots.

**CMake / CTest**
- `tests/CMakeLists.txt` registers one `add_test` per case; ends with `gabbaboy_verify_registered_tests()` (line 364) which compares sorted registered names to `tests/expected-tests.txt` and fails configure on any difference, except the five `installed_*` names which are removed when `GBB_TEST_INSTALL_PREFIX` is unset [VERIFIED: cmake/ExpectedTests.cmake]. Therefore: add each new name to `tests/expected-tests.txt` in the same change or configure fails.
- Runner-process tests get `TIMEOUT 30` via a single `set_tests_properties(...)` list at lines 297-307 [VERIFIED: tests/CMakeLists.txt:297-307]. New acceptance tests need their own larger TIMEOUT (see Pitfall 2).
- Player tests: `tests/player/CMakeLists.txt` loops over `tests/player/expected-tests.txt` names and dispatches by regex (`^player_session_[a-z0-9_]+$`, `^player_input_...`); a new name that matches no branch must be handled (read the remaining lines of that file before adding names). The player build runs in the macOS package job via `tests/scripts/verify-phase3-player.sh --build-package`; its smoke is invoked at line 250: `"$player_bin" --smoke-package "$demo_license" >"$smoke_output" 2>&1` followed by `grep -Fq 'player smoke passed:'` and `grep -Fq 'packaged MBC1 continuation fixture resumed in a fresh process'`. The script exports `SDL_AUDIO_DRIVER=dummy` and `SDL_VIDEO_DRIVER=dummy` (lines 328-329) [VERIFIED: tests/scripts/verify-phase3-player.sh].

**CI (`.github/workflows/ci.yml`, 203 lines)**
- Jobs: `native-linux` (ubuntu-22.04), `native-macos` (macos-14), `native-windows` (windows-2022; ctest step has `shell: bash`), `linux-sanitizers` (ASan/UBSan, `ctest --preset phase1-asan`), `cmake-floor-3-25-3`, `player-gate`, `macos-player-package`, `required-native` aggregating all [VERIFIED: ci.yml]. Every native/sanitizer job runs `verify-test-inventory.sh build/ctest.xml tests/expected-tests.txt` (Windows and macOS and Linux with `--installed`). The floor job runs the same inventory via `.github/scripts/verify-cmake-floor.sh` with CMake 3.25.3. All presets are `CMAKE_BUILD_TYPE: Debug` [VERIFIED: CMakePresets.json:5-8].
- **Finding (D-37):** `player-gate` sets `player_required=${{ github.event_name == 'pull_request' }}` and `check-player-result.sh` accepts `false:skipped`. So on a `push` run the packaged-player smoke is skipped and the aggregate still passes; it is only enforced on `pull_request`. D-37 asks to "check that PR-only gating cannot let a merge revision omit the smoke". Verification is therefore a documentation-plus-test item: the self-test table in `check-player-result.sh` (rows like `success|true|skipped|fail`, `success|false|skipped|pass`) already encodes this. Ensure the smoke runs inside the existing `macos-player-package` job (not a new one) so `required-native` keeps failing when it is skipped on a PR; do not add a new job unless it is added to `needs:` and to the shell loop. Merge protection uses the PR check, which is satisfied.
- The `required-native` shell loop lists results explicitly; a new job must be added to `needs`, the env block and the loop.
- Actions are SHA-pinned (`actions/checkout@11bd719...`, `upload-artifact@ea165f8...`); reuse those exact pins in `libbet-repro.yml`.

**Conventions to copy**
- `.gitattributes` is 8 lines; the existing patterns are `fixtures/mooneye/manifest.json -text`, and per-file `text eol=lf` for the MBC1 asm/manifest/LICENSE plus `-text` for the `.gb` [VERIFIED: .gitattributes]. Add the same per-file lines for `fixtures/libbet/*`, `tests/acceptance/**` (`cases.txt`, `*.input`), `tests/baseline/*`. Note `fixtures/mooneye/*.gb` are not listed; do not rely on a glob existing.
- Manifest style: `fixtures/tracer/manifest.json` (fields `id, source, license, build{...}, rom, sha256, profile{...}, protocol{...}`) [VERIFIED: fixtures/tracer/manifest.json:1-40]; Mooneye adds `suite{revision,tree_sha1,license,upstream}`, `builder{...}`, `excluded_candidates[]`. Libbet needs a new `rights.embedded_assets[]` array (D-04c).
- `THIRD_PARTY_NOTICES.md` is a table with columns Material / Rights / Source+manifest SHA-256 / ROM SHA-256 / Notice SHA-256 and says "The three ROMs used in release and consumer smoke tests are original project-authored material; they are not commercial game images or third-party ROMs." That sentence becomes false once Libbet (third-party, zlib) is added; amend it in the same change [VERIFIED: THIRD_PARTY_NOTICES.md:1-14].
- `fixtures/mooneye/SOURCES.md` layout: sections with gate status blocks (`<!-- BEGIN PLAN ... -->`), exact revisions, run URLs, local-vs-hosted byte comparisons; mirror it.
- `Install rules` in root `CMakeLists.txt` install tracer/visible-demo/mbc1 fixtures to `share/gabbaboy/fixtures/*`; do NOT install the Libbet ROM into the core package (third-party game; not needed by consumer smoke). It only needs to reach the macOS player package (see Open Question 3).

## Measured Facts (this session, scratch probes linked against current `src/core/gabbaboy.c`)

| Measurement | Result |
|---|---|
| Libbet ROM digest | `3607412031c8287cf878299ce96e581e85b852dde703806343b95576fa3ff1a9` (matches D-01) [VERIFIED: shasum on scratch ROM] |
| 3600-frame Libbet run, Debug -O0, no sanitizers | 11.2 s wall (single thread, arm64 macOS) |
| Same run, ASan+UBSan -O0 | 84.5 s user, 89.6 s wall |
| `gbb_run_audio` loop shape | 3811 calls / 3801 HALTED_IDLE / 0 zero-consume |
| Left channel extremes over 60 s | min `-32768`, max `32265` |
| Mooneye `daa` | `LD B,B` at 1804576 half-dots; `gbb_copy_frame` OK, generation 12, `completion_half_dots=1676256`; frame all shade 0 (23040 px) |
| Mooneye `tim00` | `LD B,B` at 35048; `gbb_copy_frame` returns 17 (`GBB_FRAME_NOT_READY`) |
| Mooneye `tim00_div_trigger` | `LD B,B` at 32920; `GBB_FRAME_NOT_READY` |

Consequences: (a) budget accept runs to `T_hit + 1 s` (not 3600 frames) and keep controls at a reduced budget (about 1100-1200 frames, since the measured hit is near frame 894); (b) CTest timeouts for Libbet cases must be >= 300 s on the sanitizer job; (c) 4 Libbet runs plus 4 control runs plus a baseline pass is roughly 4-8 minutes extra on the ASan job and ~1-2 minutes on the others; the CI job timeout is 30 min, so budget the sum when adding cases (the baseline script should reuse a single `--observe` run per workload, not re-run each CTest case's output).

## Common Pitfalls

### Pitfall 1: Textual include of `main.c` in `test_runner.c`
**What goes wrong:** Splitting the runner into several `.c` files, moving SHA-256, or changing `load_case_rom`/`read_bounded` signatures breaks `tests/test_runner.c` at compile time (it names `MAX_ROM`, `cases`, `hash_matches`, `read_bounded`, `run_guest`). Static-name collisions are also possible (`rotr`, `cases`).
**How to avoid:** Put shared code in a static library with headers; keep `main.c` self-contained for the Mooneye path or update `test_runner.c` in the same task. Run `cmake --build` and the 7 `runner_*` tests as the task gate.
**Warning signs:** `test_runner` link errors, duplicate `static` symbols.

### Pitfall 2: Sanitizer and Debug runtime of Libbet runs
**What goes wrong:** A 60-emulated-second default budget costs ~85 s under ASan per run; the existing `TIMEOUT 30` list would fail the new tests spuriously; a cluster of controls could push `linux-sanitizers` toward its 30 min limit.
**How to avoid:** Give acceptance tests an explicit `TIMEOUT 300`; make accept stop at `T_hit + 1 s`; give controls `budget_half_dots` ~1.2k frames; do not run the same workload in both a CTest case and the baseline check unless the baseline reuses receipts.

### Pitfall 3: Windows line endings and binary mode in digested text
**What goes wrong:** `windows-2022` checkouts with autocrlf convert `*.input`, `cases.txt`, ledger and manifest; the case file pins `input_sha256` on raw bytes, so CRLF fails digest (safe) but looks like a flaky platform bug. Runner stdout in text mode emits `\r\n`; a bash/awk comparator then sees `\r` in values.
**How to avoid:** `.gitattributes text eol=lf` per file for every digested text (existing precedent: MBC1 files); add a CTest that asserts the checked-out `input` bytes digest equals the pinned value (so a CRLF checkout fails loudly with a distinct message); strip `\r` in the comparator; open files `rb`/`wb` (D-28); write PPM with `wb`; hash only serialized buffers; serialize PCM to little-endian bytes explicitly (do not hash the `int16_t` array memory; a big-endian host would differ, and the AGENTS.md rule forbids raw struct dumps).

### Pitfall 4: `bash` and `python3` inside CTest on Windows
**What goes wrong:** No existing core CTest case invokes `bash` or `python3` (checked `tests/CMakeLists.txt` and `cmake/*.cmake`: only the player subtree uses `find_package(Python3 ... REQUIRED)`). A bare `bash` in `add_test` on Windows may resolve to `System32\bash.exe` (WSL launcher) depending on PATH. A bare `python3` may be absent.
**How to avoid:** Use `find_package(Python3 COMPONENTS Interpreter REQUIRED)` and `${Python3_EXECUTABLE} -I script.py`. For the baseline check, implement the comparison in `cmake/VerifyDmgBaseline.cmake` (runs on all OSes with the CMake already required, valid at the 3.25 floor) and make `tests/scripts/verify-dmg-baseline.sh` a thin bash wrapper that calls it; register the CTest case with `${CMAKE_COMMAND} -P` (as `mooneye_fixture_digest` already does, tests/CMakeLists.txt:227-230). This still gives D-35 its "single entry point" while avoiding a first-time Windows bash dependency. If the planner insists on the literal bash registration, make a Wave 0 CI spike that proves `bash` resolution on `windows-2022` first. [ASSUMED: WSL bash shadowing on windows-2022 runners; behaviour not tested here.]

### Pitfall 5: Exit-code semantics vs CTest
`WILL_FAIL` is too weak; `SKIP_RETURN_CODE` is forbidden. Use the exact-code wrapper (Pattern 2). Exit 4 for an excluded model must be asserted by its own named test (D-22).

### Pitfall 6: Inventory and player-gate drift
Every new CTest name must appear in `tests/expected-tests.txt` (core jobs and floor job) and player names in `tests/player/expected-tests.txt` (51 names; it is in the macOS package job only). The player smoke with `--input-script` is a package-script step, not a CTest name; make it print a distinctive line and have `verify-phase3-player.sh` grep for it, exactly like lines 250-258.

### Pitfall 7: Baseline self-reference
`frozen_revision` is the commit the digests were recorded at; the ledger itself lives in a later commit. D-34 forbids `src/` changes in `baseline:` commits, so the Phase 7 freeze commit must come after all src changes (including any D-19 fix) and `frozen_revision` must be an ancestor commit that contains those src changes. The inventory identity (D-31) lists names from the JUnit report; names appear sorted by `sed ... | LC_ALL=C sort` in `verify-test-inventory.sh`, so store them sorted with `LC_ALL=C`.

### Pitfall 8: Mooneye `LD B,B` frame digest for ROMs with no completed frame
See Open Question 1. Do not synthesize an all-zero frame (D-24 forbids it).

### Pitfall 9: Libbet header `$143=$80`
The core loaded the ROM without error in all probes (CGB-compatible flag on a DMG profile). Keep a CTest that asserts `gbb_load_rom` succeeds and the profile reports DMG; do not infer CGB behaviour (`hw_capability` stays 0 per D-17).

### Pitfall 10: Earlier double-counting of "time"
Event timestamps must be >= the instance's current time at queue time; a stepper that overshoots the deadline by one instruction would reject the next event (`GBB_INVALID_EVENT`). The core preflights whole instructions so it never overshoots a budget; queue events for a window before stepping into it (the player queue's own bound is 56 normal).

## Pre-freeze Investigations (D-19), where to look

### (i) Mixer reaching +-32768
Code path: `audio_current_mix` (`src/core/gabbaboy.c:198-231`) [VERIFIED]: pulse/wave/noise sample = `volume*2048 - 16384` (range -16384..+14336) multiplied by `(NR50 & 7) + 1` (1..8) per side and summed over four channels with no normalisation. `audio_process_sample` (lines 177-192) feeds `audio_mix_level` through `audio_round_q15` and `audio_saturate_s16` (`INT16_MAX/INT16_MIN` clamp), then the DMG high-pass (`GBB_AUDIO_HPF_Q15 32648`, line 19) with a second saturation. Libbet's `audio_init` writes `rNR51 = $FF` and `rNR50 = $77` [VERIFIED: libbet `src/audio.z80` lines ~226-236 in scratch clone], i.e. all channels both sides at master volume 7 -> factor 8. One full-volume pulse reaches 14336x8 = 114688 > 32767, so clipping at the `audio_saturate_s16` stage is expected for any loud Libbet effect. `docs/audio-and-playback.md` documents the resampler, HPF and saturation but states no amplitude scale, and `tests/test_audio.c` `audio_saturation` (lines 334-350) only checks the clamp with `INT32_MAX/MIN` inputs, so no existing test pins the intended scale.
Next step: compare against the Pan Docs mixer description (each DAC output scaled to a nominal +-1 range, four channels summed, master volume `(vol+1)/8`) before deciding fix vs document. Hypothesis (not confirmed): the model lacks a headroom divisor (about 1/32 for four channels at `/8` master) [ASSUMED]. If it is a defect, the fix changes every PCM digest, the authored signal-vector digest `202a3e9f96f3cead`, and partition digest `b5bb127cdda6a035` (docs/audio-and-playback.md) and the audio unit tests; it must land and be reviewed before any PCM digest is recorded, and the player gain (default 100%, range 0-200%) interacts with it. Expected-outcome record: `LESSONS.md` + `DECISIONS.md` entry with the evidence either way.

### (ii) Early repeated Start taps start the game by f270; single taps f290-f440 do nothing
Code path in the pinned Libbet source (`src/intro.z80`, scratch clone): the title/intro ends with a loop at `.vtimeout` (lines ~308-322): `ld bc, 180*256+120`; each pass calls `read_pad`, `audio_update`, `wait_vblank_irq`; "C unskippable vblanks, then B skippable ones"; after the 120 unskippable passes, `new_keys & (PADF_START|PADF_A)` ends the loop. Before it, the page/roll loop uses `cursor_x` as the page index and compares it to 192 (line ~300-303), which is the overlaid variable the discuss research flagged. Working hypothesis (not proven): repeated early taps advance or skip pages in the roll loop (START/A processed there), shortening the intro, whereas a single tap during the unskippable 120-vblank window is discarded because `new_keys` is only examined after the window. Verify by instrumenting a scratch run (peek `cursor_x`, `new_keys`) and by reading `intro.z80` roll loop lines ~200-300 and `pads.z80` `read_pad` (new_keys derivation). Fix the emulator only if JOYP polling/timing deviates from what the source implies (e.g. a missed press held across vblank). Record the outcome either way. [ASSUMED hypothesis]

## Code Examples

### 1. Core-mutant generation (CMake, 3.25-safe)
```cmake
# tests/acceptance/CMakeLists.txt
file(READ "${PROJECT_SOURCE_DIR}/src/core/gabbaboy.c" GBB_CORE_TEXT)
set(GBB_JOYP_PATTERN "if ((m->joypad_select & 0x20u) == 0)")
string(FIND "${GBB_CORE_TEXT}" "${GBB_JOYP_PATTERN}" GBB_PATTERN_AT)
if(GBB_PATTERN_AT EQUAL -1)
  message(FATAL_ERROR "core-mutant pattern is missing; JOYP source changed")
endif()
string(REPLACE "${GBB_JOYP_PATTERN}" "if ((m->joypad_select & 0x20u) != 0)"
  GBB_MUTANT_TEXT "${GBB_CORE_TEXT}")
file(WRITE "${CMAKE_CURRENT_BINARY_DIR}/gabbaboy_joyp_mutant.c" "${GBB_MUTANT_TEXT}")
```
Also assert exactly one occurrence (compare lengths or use `string(REGEX MATCHALL)`). `file(WRITE)` on a text read round-trips `\r\n` unchanged on 3.25 (verify on Windows CI; a CRLF checkout of `gabbaboy.c` is not expected because the repo has no autocrlf rule for sources, but the mutant must still compile). Note `string(REPLACE)` mangles `;` in CMake lists: `file(READ)` content containing `;` is fine in a quoted argument but do not pass it through `foreach`/list functions. [ASSUMED: behaviour of `;` in 3.25 string ops; confirm with a configure run.]

### 2. Exact-exit-code wrapper
```cmake
# tests/expect_exit.cmake  (-DGBB_CMD="a;b;c" -DGBB_EXPECT_CODE=4 -DGBB_EXPECT_REGEX="reason=unsupported-model")
execute_process(COMMAND ${GBB_CMD} RESULT_VARIABLE rc OUTPUT_VARIABLE out ERROR_VARIABLE err)
if(NOT "${rc}" STREQUAL "${GBB_EXPECT_CODE}")
  message(FATAL_ERROR "expected exit ${GBB_EXPECT_CODE}, got ${rc}: ${out}${err}")
endif()
if(NOT "${out}${err}" MATCHES "${GBB_EXPECT_REGEX}")
  message(FATAL_ERROR "missing '${GBB_EXPECT_REGEX}': ${out}${err}")
endif()
```

### 3. Verifier negative tests (Python mutation of a manifest copy)
Mutated manifest copies are written at configure time (like `runner-bad-manifest.json` in tests/CMakeLists.txt:275-290) or by the Python script's own `--self-test`; each CTest asserts non-zero exit AND a distinct stderr message (use the wrapper). Five required mutations from D-05: empty `rights.embedded_assets`; one closure record removed; licence `unknown`; changed ROM digest; changed header byte. Positive control passes the committed manifest.

### 4. Canonical RGB digest (D-24)
```c
/* header then 160*144*3 bytes, shade -> {255,170,85,0} replicated to R,G,B */
sha_update(&c, (const uint8_t *)"GBB-RGB888-v1 160x144\n", 22);
```
(The header is 22 bytes: 13 for `GBB-RGB888-v1`, 1 space, 7 for `160x144`, 1 newline. Use `strlen` on a named constant in code rather than a literal. Add a test that hashes a known synthetic frame to a hard-coded digest computed by an independent tool such as `python3 -I` hashlib; that also supplies the D-26 independent check of the digest definition.)

### 5. PCM serialization
Serialize each `gbb_audio_frame` as 4 bytes: `left & 0xFF, (left >> 8) & 0xFF, right & 0xFF, (right >> 8) & 0xFF` (convert via `uint16_t`), then feed SHA-256. Never `sha_update` on the struct array.

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| Screenshot/frame-digest only gates (blind to attract mode) | Guest-memory predicate + paired negative controls + digests as regression labels | Locked by D-08/D-26 |
| Completed-frame counts as time | Master-timeline half-dots | Locked by D-10/D-11 |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `bash` in CTest on windows-2022 might resolve to WSL `System32\bash.exe` | Pitfall 4 | Low: the CMake-script design avoids it either way |
| A2 | Mixer lacks headroom normalisation relative to Pan Docs `(vol+1)/8` scaling; fix would change all PCM digests | Investigations (i) | A fix may be unnecessary (document-only) or larger; schedule investigation first |
| A3 | Early-tap behaviour is explained by intro page-skip vs unskippable vblank window | Investigations (ii) | Could hide a real JOYP timing defect; instrument before concluding |
| A4 | `;` handling in `string(REPLACE)`/`file(WRITE)` of C source at CMake 3.25 | Code Example 1 | Mutant fails to compile; caught at first configure |
| A5 | RGBDS 0.7.0/Pillow 12.3.0 legitimacy for the opt-in job (values taken from CONTEXT.md; the legitimacy seam was not run) | Standard Stack | Opt-in job only; planner should gate with a human-verify task if desired |
| A6 | Linux/Windows runtimes for Libbet cases are within the same order of magnitude as the macOS measurements | Pitfall 2 | Timeouts need adjustment after the first CI run |

## Open Questions

1. **Mooneye frame digests for tim00 / tim00_div_trigger (D-24 vs D-30).**
   - Known: only `daa` completes a frame before `LD B,B` (uniform shade 0, so a weak regression signal); the two timer ROMs never complete a frame by the result breakpoint.
   - Unclear: whether D-30 intends `mooneye.<id>` lines to carry a frame digest for each case.
   - Recommendation: record for the baseline `mooneye.<id>.frame` as either a digest or the explicit token `not-ready` (an observation, not an error), and keep D-24's "error" rule for acceptance checkpoints only. This is a minimal wording reconciliation, not a design change; the planner should surface it in the plan rather than silently choose. The registers closure and the `LD B,B` half-dot time already are the stronger identity signal for these ROMs.
2. **Control-case form.** D-14 says each control "must fail the predicate with exit non-zero" while D-22 defines `model_fail` as a strict expected failure. Recommendation: N1/N2 are separate case lines with `model_fail=dmg-cpu-b expect_fail_reason=predicate-not-reached`; the runner reports `status=xfail` (exit 0 on the expected failure, exit 1 if it unexpectedly passes). The "exit non-zero" assertion is done by the core-mutant test, which runs the real accept case against the mutant runner and must see exit 1, and by N3 `--mutate drop:START` run in `--observe` plus compare mode. State this explicitly in the plan so the 5 control tests are unambiguous.
3. **Where the Libbet ROM enters the macOS player package.** D-36 requires the packaged, extracted player to launch Libbet. Today the package carries `demo.gb` and the MBC1 continuation fixture (see `packaged_battery_rom_path`, `resolve_demo_rom_path`, and the package assembly/verification in `verify-phase3-player.sh` and `tests/scripts/verified_player_output_dir.py`, which check package metadata digests). Adding a third-party ROM to the distributable player archive changes release/redistribution scope (zlib attribution must then ship in the package notices). Recommendation: the planner decides between (a) packaging the ROM plus its LICENSE and notice (must also update the package-content verifiers and `THIRD_PARTY_NOTICES.md`), or (b) the smoke takes the ROM and script as external path arguments from the repo checkout inside the CI job, running on the extracted player but not shipping the game. Option (b) matches D-37's "no new platform packaging" and avoids a redistribution decision; confirm with the owner only if (a) is wanted.
4. **`hw_capability` expectation field.** D-21's `expect_hw_capability` is per-profile; Phase 7 has one profile. Keep the key but only accept `0`.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| C compiler / CMake / Ninja | Build, CTest | yes (used for probes) | clang on macOS arm64 | none needed |
| Python 3 (`python3 -I`) | G5 verifier, repro | yes locally; Windows CI via `find_package(Python3)` | 3.14 local | `string(JSON)` in CMake |
| Git Bash `bash` on Windows runner | existing CI steps only | yes (ctest step uses `shell: bash`) | - | CMake script check (recommended) |
| SDL3 3.4.18 + dummy drivers | player smoke (macOS package job) | yes in CI (existing) | exact 3.4.18 [VERIFIED: CMakeLists.txt `find_package(SDL3 3.4.18 EXACT ...)`] | none |
| RGBDS 0.7.0, Pillow 12.3.0 | `libbet-repro.yml` only | not needed locally; scratch venv/rgbds exist from discuss | - | job is opt-in |
| Network | repro workflow only | n/a | - | required path never fetches |

**Missing blocking dependencies:** none for the required path.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | CTest (CMake 3.25+) over custom C test executables (`REQUIRE`/`PASS` style, no external framework) plus Python `-I` stdlib scripts and `cmake -P` checks |
| Config file | `tests/CMakeLists.txt`; `tests/acceptance/CMakeLists.txt` (new); inventory `tests/expected-tests.txt` (184 names) and `tests/player/expected-tests.txt` (51) |
| Quick run command | `cmake --build build && ctest --test-dir build -R 'acceptance_parse\|libbet_admission\|acceptance_predicate\|runner_' --output-on-failure` |
| Full suite command | `ctest --test-dir build --output-on-failure --no-tests=error --output-junit ctest.xml && bash .github/scripts/verify-test-inventory.sh build/ctest.xml tests/expected-tests.txt --installed` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| GAME-01 | Positive admission passes; 5 mutated manifests each fail with distinct message; ROM digest/size/header pinned; closure complete | python + cmake | `ctest -R 'libbet_admission'` (proposed names `libbet_admission_pass`, `libbet_admission_empty_assets`, `..._missing_record`, `..._unknown_licence`, `..._bad_digest`, `..._bad_header`) | Wave 0 |
| GAME-01 | `LICENSE.txt` text and notices row present | cmake/python | `ctest -R libbet_notice` | Wave 0 |
| GAME-02 | Scripted input reaches predicate; recorded frame + PCM digests | CTest runner | `ctest -R acceptance_libbet-dmg` | Wave 0 |
| GAME-02 | No-input (N1), SELECT (N2), `--mutate drop:START` (N3) fail the predicate | CTest runner + wrapper | `ctest -R 'acceptance_.*control'` | Wave 0 |
| GAME-02 | Core mutant fails the gate | CTest (mutant runner) | `ctest -R acceptance_core_mutant` | Wave 0 |
| GAME-02 | Predicate truth table; anchor bytes verified after ROM digest | C unit | `ctest -R acceptance_predicate` | Wave 0 |
| EVID-01 | Case/script parser boundary matrix and negative files | C unit | `ctest -R acceptance_parse` | Wave 0 |
| EVID-01 | `case_applicability` incl. `unsupported-model` exit 4, `target-revision` exclusion, both-lists parse error | CTest + wrapper | `ctest -R 'acceptance_.*_excluded_'` | Wave 0 |
| EVID-01 | RGB digest definition vs independent Python digest of a synthetic frame; PPM only on failure | C unit + python | `ctest -R acceptance_rgb_digest` | Wave 0 |
| EVID-01 | `LD B,B` frame capture on Mooneye `daa`; `not-ready` reporting for timer ROMs | CTest | `ctest -R acceptance_ldbb` | Wave 0 |
| GAME-03 | Packaged player smoke: `smoke_report ... predicate=pass pcm_nonsilent=1 pcm_sha256=<headless>`; no-input control fails | package script (macOS) | `bash tests/scripts/verify-phase3-player.sh --build-package` (existing job) | extend |
| GAME-03 | Session-level negative controls | player CTest | `ctest -R player_session_script` (names in `tests/player/expected-tests.txt`) | Wave 0 |
| EVID-02 | Ledger matches recomputed digests on Linux/macOS/Windows; frozen inventory subset; CHANGES rule | cmake script | `ctest -R dmg_baseline` | Wave 0 |
| EVID-02 | Baseline checker self-tests: modified digest fails; missing line fails; unknown extra line fails; removed frozen test name fails | cmake script | `ctest -R 'dmg_baseline_(modified\|missing\|extra\|inventory)'` | Wave 0 |

### Sampling Rate
- **Per task commit:** quick run command for the touched area (<30 s on Debug for parser/unit tests; Libbet cases excluded).
- **Per wave merge:** full suite command; Linux ASan variant for waves that touch runner or core.
- **Phase gate:** full suite green on all five native jobs (exact head) and `macos-player-package` green on the PR; then baseline check green.

### Wave 0 Gaps
- [ ] `tests/acceptance/CMakeLists.txt` and all new test executables/scripts above
- [ ] `tests/expect_exit.cmake` (exact exit-code wrapper)
- [ ] A Windows spike (CI only): confirm `find_package(Python3)` and `cmake -P` ledger comparison work on `windows-2022` before depending on them
- [ ] Independent digest vectors: a Python hashlib script that computes the RGB-digest vector for a synthetic frame (D-26 anti-circularity)
- [ ] Frame/PCM threshold calibration record (first CI run), recorded with observed values

## Security Domain

`security_enforcement` is enabled in `.planning/config.json` [VERIFIED: .planning/config.json]. This phase is a local diagnostic tool plus fixture admission, not a networked service.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V5 Input Validation | yes | Bounded parse of case file/script (sizes, line counts, charset, checked arithmetic, all-or-nothing); heap ROM with 8 MiB cap and exact size+SHA before core load |
| V12 Files | yes | Relative paths only (no `..`, leading `/` or `\`, `:`, empty segments); `rb`/`wb` only; failure-dir must exist and be writable else exit 2; PPM id `[a-z0-9-]` |
| V10 Malicious Code / supply chain | yes | Commit pinned (not tag), digest-pinned ROM, required CI never fetches; opt-in repro job `contents: read`, no secrets, actions SHA-pinned |
| V6 Cryptography | no (SHA-256 for identity, not security) | reuse existing implementation |
| V2/V3/V4 | no | n/a |

### Known Threat Patterns
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal via case-file `rom=`/`input_script=` | Tampering / Info disclosure | Reject `..`, absolute, drive, UNC; resolve relative to the cases file directory |
| Integer overflow in time suffix arithmetic | DoS / Tampering | Checked cursor math, 600 s ceiling, `at_half_dots` monotonic |
| Oversized/NUL/non-ASCII inputs | DoS | D-12/D-28 limits; tested by the boundary matrix |
| Partial mutation on bad input | Tampering | Validate whole file before any run or write |
| Rights laundering (unrecorded embedded asset) | Repudiation | Fail-closed verifier + closure list + negative tests |
| Output file clobber | Tampering | `--failure-dir` explicit, ids validated, no env activation (D-38) |

## Suggested Wave Decomposition

Constraint reminder (AGENTS.md): stop after the phase; no auto-advance. Branch `gsd/phase-07-dmg-game-acceptance-and-regression-baseline` already exists.

- **Wave 0 (infra/spikes, small, parallel):** Windows CTest spike for Python/cmake-script; `tests/expect_exit.cmake`; independent digest vector script; decide Open Questions 1-3.
- **Wave 1A (GAME-01) and Wave 1B (EVID-01 foundations) in parallel (disjoint files):**
  - 1A: vendor `fixtures/libbet/*`, manifest with `rights.embedded_assets`, verifier + 6 CTests, `.gitattributes`, `THIRD_PARTY_NOTICES.md`, `SOURCES.md`, `libbet-repro.yml` + `reproduce-libbet.sh` (workflow runs only on dispatch; the hosted reproduction URL is recorded later, D-03).
  - 1B: shared `src/accept/*` library (sha256 move, input_script parser, digest, stepper), case-file parser + `case_applicability`, heap ROM (D-27), `test_runner.c` and CMake updates, parse boundary tests, `runner_help` text update. Gate: the 7 existing `runner_*` and 3 `mooneye_case_*` tests unchanged and green (D-20: Mooneye digest identical).
- **Wave 2 (GAME-02):** compiled predicate table + anchor-byte test (depends on 1A ROM and 1B library); `--acceptance`/`--observe`/`--mutate`/`--failure-dir`; `tests/acceptance/{cases.txt,inputs/*}`; checkpoint/rolling/PCM digests and non-silence gate; controls N1/N2/N3, truth table, core-mutant library+runner; SGB assertion (D-17); two-pass stall diagnosis (D-18); inventory updates. First CI run calibrates PCM thresholds.
- **Wave 3 (investigations, sequential before any digest is blessed):** D-19(i) mixer, D-19(ii) early taps; each ends with an evidence record in `DECISIONS.md`/`LESSONS.md` and, if a defect, the fix plus updated audio vectors. Then bless acceptance digests (inspect each failure-path PPM once and record, D-26).
- **Wave 4 (GAME-03):** player `--input-script` on `--smoke-package`, scripted events through SDL key events at exact times (not `cursor+8`), `smoke_report` line, no-input control, `verify-phase3-player.sh` grep, session-level negative controls in `tests/player/*`, limitation note (macOS only). Depends on 1B shared library and Wave 2 predicate. PCM digest compared to the headless value recorded in Wave 2/3.
- **Wave 5 (EVID-02, last):** `tests/baseline/dmg-cpu-b-v1.txt`, `CHANGES.md`, `cmake/VerifyDmgBaseline.cmake` + `verify-dmg-baseline.sh`, CTest registration + inventory, `--print-candidate`, benchmark digest line (reuse `measure_core`, advisory), ledger/doc updates, freeze in a separate `baseline:` commit after all `src/` changes; cross-OS identity confirmed on the PR run (D-33), then the final aggregate gate.

## Sources

### Primary (HIGH confidence, read this session)
- `src/runner/main.c`, `include/gabbaboy/gabbaboy.h`, `src/core/gabbaboy.c` (lines 140-260, 520-540, 1000-1012), `src/player/main.c` (580-621, 1460-1500, 1930-1970, 2085-2271), `src/player/input.{c,h}`, `src/player/session.h`
- `CMakeLists.txt`, `CMakePresets.json`, `tests/CMakeLists.txt`, `tests/player/CMakeLists.txt`, `cmake/ExpectedTests.cmake`, `tests/test_runner.c`, `tests/expect_runner_failure.cmake`, `tests/verify_runner_help.cmake`
- `.github/workflows/ci.yml`, `.github/scripts/verify-test-inventory.sh`, `.github/scripts/check-player-result.sh`, `.github/scripts/verify-cmake-floor.sh`, `tests/scripts/verify-phase3-player.sh`
- `.gitattributes`, `THIRD_PARTY_NOTICES.md`, `fixtures/tracer/manifest.json`, `fixtures/mooneye/{manifest.json,SOURCES.md}`, `docs/audio-and-playback.md`
- `07-CONTEXT.md` and the discuss-phase predicate report (scratch)
- Local probes (scratch, linked against the current core) for Mooneye frame availability, Libbet runtime, stepping loop shape and PCM extremes

### Secondary / Tertiary
- Libbet source (`intro.z80`, `audio.z80`, `main.z80`) from the scratch clone at the pinned commit: used for investigation leads only.
- Pan Docs APU mixer scale: referenced from memory and `docs/audio-and-playback.md`; not fetched this session (LOW; hence A2).

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH, no new dependencies, all in-repo.
- Architecture / seams: HIGH, files read and probes run.
- Pitfalls: HIGH for items measured or read; MEDIUM for Windows bash/python resolution (A1).
- Investigations: MEDIUM-LOW, hypotheses with code pointers.

**Research date:** 2026-10-10
**Valid until:** 2026-11-09 (code seams change with every merged phase; re-read `main.c` and `ci.yml` if any other phase lands first)
