---
phase: GB-02-dmg-cpu-bus-and-time
verified: 2026-10-06T21:40:15Z
status: gaps_found
score: 1/5 roadmap truths verified
covered_files:
  - .github/scripts/verify-test-inventory.sh
  - .github/workflows/ci.yml
  - .github/workflows/fixture-repro.yml
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-01-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-01-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-02-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-02-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-03-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-03-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-04-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-04-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-05-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-05-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-06-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-06-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-07-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-07-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-08-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-08-SUMMARY.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-09-PLAN.md
  - .planning/phases/GB-02-dmg-cpu-bus-and-time/02-09-SUMMARY.md
  - CMakeLists.txt
  - README.md
  - cmake/ExpectedTests.cmake
  - cmake/VerifyMooneye.cmake
  - fixtures/mooneye/FONT-LICENSE.txt
  - fixtures/mooneye/LICENSE.txt
  - fixtures/mooneye/SOURCES.md
  - fixtures/mooneye/daa.gb
  - fixtures/mooneye/font-source.c
  - fixtures/mooneye/manifest.json
  - fixtures/mooneye/tim00.gb
  - fixtures/mooneye/tim00_div_trigger.gb
  - fixtures/tracer/manifest.json
  - fixtures/tracer/tracer.asm
  - fixtures/tracer/tracer.gb
  - include/gabbaboy/gabbaboy.h
  - src/core/gabbaboy.c
  - src/runner/main.c
  - tests/CMakeLists.txt
  - tests/consumers/c/main.c
  - tests/consumers/cpp/main.cpp
  - tests/expected-tests.txt
  - tests/scripts/verify-phase2-installed.sh
  - tests/test_api.c
  - tests/test_bus.c
  - tests/test_control.c
  - tests/test_cpu.c
  - tests/test_diagnostics.c
  - tests/test_events.c
  - tests/test_loader.c
  - tests/test_runner.c
  - tests/test_serial.c
  - tests/test_timer.c
  - tests/test_tracer.c
covered_digest: "v3:sha256:52418e7d4a9a52d65fd07b8c0d723764faeee5f39dcd747cd91c4fc360a017d1"
behavior_unverified: 0
overrides_applied: 0
gaps:
  - truth: "[CR-01] The declared post-boot DMG profile initializes F according to the loaded ROM header checksum."
    status: failed
    reason: "reset_state hard-codes F to 0x80. The declared profile requires F=0x80 for a zero header checksum and F=0xB0 for a nonzero checksum, including after reset."
    artifacts:
      - path: "src/core/gabbaboy.c"
        issue: "reset_state sets F=0x80 without consulting the loaded ROM checksum."
    missing:
      - "Derive post-boot/reset F from the loaded ROM's checksum profile, with regression cases for zero and nonzero checksums."
  - truth: "[CR-02] Unconditional RET and RETI read the stack at the declared timed bus phases."
    status: failed
    reason: "The shared RET/RETI branch uses the later stack-read offsets intended for taken conditional RET."
    artifacts:
      - path: "src/core/gabbaboy.c"
        issue: "Unconditional RET/RETI call pop16 at offsets 16/24, while POP uses offsets 8/16."
    missing:
      - "Use POP-PC stack-read phases for RET/RETI; retain the additional condition-check cycle for taken RET cc."
      - "Add independent bus-observer regressions for RET, RETI, and taken RET cc."
  - truth: "[CR-05] The eligible Mooneye corpus excludes PPU-dependent cases and reaches the declared CPU/timer result protocol."
    status: failed
    reason: "D-09 excludes PPU-dependent source closures, but all three admitted closures reach common/lib/is_ppu_broken.s and read LY at FF44 before assertions and the LD B,B protocol. Rights, digests and reproduction are valid; applicability admission is not. All three current runs stop unsupported."
    artifacts:
      - path: "fixtures/mooneye/manifest.json"
        issue: "Three PPU-dependent source closures are admitted into the eligible denominator despite the D-09 exclusion."
      - path: "fixtures/mooneye/SOURCES.md"
        issue: "The LY/protocol dependency is documented as a gap, but the admitted closures remain unchanged."
    missing:
      - "Remove PPU-dependent closures from eligibility or provide a source-qualified completion path consistent with the declared phase scope."
      - "Reproduce and digest-check any changed fixture bytes, then require every eligible CPU/timer ROM to reach its real result protocol and pass the strict offline suite."
  - truth: "[CR-03] A pending IME enable is not postponed by consecutive EI instructions."
    status: failed
    reason: "Each EI unconditionally resets ime_delay to 2. With EI; EI and a pending enabled interrupt, the second EI restarts the delay and allows the following opcode to execute before interrupt entry."
    artifacts:
      - path: "src/core/gabbaboy.c"
        issue: "Opcode 0xFB assigns ime_delay=2 without preserving an already active EI delay."
      - path: "tests/test_control.c"
        issue: "EI delay cases cover EI+NOP and EI+DI, but not consecutive EI with a pending interrupt."
    missing:
      - "Preserve the scheduled enable across consecutive EI instructions and test vector entry before the next opcode."
  - truth: "[CR-04] Interrupt diagnostics are emitted in nondecreasing timestamp order."
    status: failed
    reason: "Interrupt entry appends IF acknowledgement at start+8 before push16 advances devices through start+16; a timer diagnostic in that interval is appended later despite an earlier timestamp."
    artifacts:
      - path: "src/core/gabbaboy.c"
        issue: "enter_interrupt observes IF at offset 8, then push16 advances the device timeline to offset 16."
    missing:
      - "Advance device diagnostics in timestamp order around IF acknowledgement and stack writes."
      - "Add an interrupt-entry case with a timer deadline inside the entry window and assert adjacent diagnostic timestamps are nondecreasing."
---

# Phase 2: DMG CPU, Bus, and Time Verification Report

**Phase Goal:** As a core integrator, I want to run the declared DMG instruction and timing behavior deterministically, so that I can reproduce diagnostic failures.
**Verified:** 2026-10-06T21:40:15Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## User Flow Coverage

| Step | Expected | Evidence in codebase | Status |
|---|---|---|---|
| Load and run through the public core | An integrator can load a declared ROM-only DMG profile and execute guest instructions within bounded calls. | Public API, ROM validation, CPU/bus implementation, and installed C/C++ consumers are present. The fresh relocated Linux check passed all five installed runner/C/C++ checks. | ✓ VERIFIED |
| Observe deterministic instruction, device, and partition behavior | Repeating an equal timestamped input/time workload across partitions yields the same supported state and outputs. | `tests/test_events.c` covers equal-time queue ordering, atomic rejection, partition equality and device deadlines; timer/serial/cpu focused cases pass. Known CPU profile and RET timing defects remain, so the full declared profile behavior is not achieved. | ✗ FAILED |
| Reproduce diagnostic corpus results | The pinned CPU/timer cases reach their declared guest result protocol and produce retained evidence. | At revision `c583e338a48f70e83573da700722dcbefa4b705a`, normal and ASan/UBSan Linux runs each execute 94 cases: 90 pass, 4 fail, 0 skip. The three ROMs stop as unsupported at the common LY `FF44` read; the strict corpus gate exits 8. | ✗ FAILED |

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | The declared DMG profile produces expected base/CB instruction, flag, arithmetic, address, and bus-access timing results, with explicit illegal-opcode behavior. (CPU-01) | ✗ FAILED | Source review at `src/core/gabbaboy.c:119-120,655-658` shows startup F ignores the ROM header checksum and unconditional RET/RETI use offsets 16/24. RGBDS v1.0.1 documents RET/RETI as four cycles and taken RET cc as five; RET/RETI are POP-PC paths. Existing broad tests pass but do not check these phases. [Pinned RGBDS opcode reference](https://rgbds.gbdev.io/docs/v1.0.1/gbz80.7). |
| 2 | Model-applicable cases observe expected interrupt entry, EI delay, HALT/HALT-bug, STOP, reset, and deterministic post-boot results. (CPU-02) | ✗ FAILED | `tests/test_control.c` exercises a single EI followed by a NOP and an interrupt, but not consecutive EI. `src/core/gabbaboy.c:693,851` resets then decrements the delay, so EI;EI extends the pending enable. `reset_state` also hard-codes F. |
| 3 | Guests observe the declared memory mapping, divider/timer edges and reload races, and disconnected serial behavior at timed access boundaries. (CPU-03) | ✓ VERIFIED (owned cases only; requirement remains pending) | Owned bus, timer and serial test families pass in the 90/94 normal run and cover supported map, divider edge/reload collisions and disconnected serial behavior. Fixture rights, digests and byte reproduction are valid, but the admitted source closures violate D-09's PPU-dependency exclusion and therefore do not qualify applicability. CPU-03 remains pending while the phase gate fails. |
| 4 | Equal timestamped inputs and elapsed emulated time produce equal supported state/output across different run partitions; LCD-off, HALT/STOP, lockup, and full output capacity return within the caller's bounded contract. (CPU-04) | ✗ FAILED | Event partition and bounded outcome cases pass, but interrupt diagnostic records can be out of chronological order: `enter_interrupt` appends IF at `start+8` before `push16` advances devices through `start+16` (`src/core/gabbaboy.c:711-717`). The public API promises chronological diagnostics. |
| 5 | A headless run reports pass/fail/timeout/unsupported against a pinned eligible CPU/timer corpus with model/boot/protocol identity and sufficient retained trace evidence to reproduce failures. (CPU-05) | ✗ FAILED | Runner controls cover the four status classes and malformed/missing fixture paths. On the actual fixed set, `final.log` records `eligible=3 executed=3 status=fail`; DAA, tim00, and tim00-div-trigger each report `status=unsupported`, `stop=core-stop`, with 128 recent diagnostics, before reaching the LD B,B protocol. CTest exits 8. |

**Score:** 1/5 roadmap truths verified; behavior-unverified: 0.

### Plan Must-Haves (Deduplicated)

| Plan truth | Status | Evidence |
|---|---|---|
| D-01 base instruction, CB semantics, and model-specific interrupt behavior | ✗ FAILED | RET/RETI timed stack phases and startup flags are wrong; consecutive EI restarts the delay. CB matrix and other instruction coverage pass. |
| D-02 unused opcodes lock persistently; reset clears lockup | ✓ VERIFIED | `tests/test_cpu.c` illegal-lockup case and `tests/test_control.c` reset-lockup case pass in the reported full run. |
| D-03 ROM-only WRAM/echo/HRAM mapping and unsupported absent-cartridge reads | ✓ VERIFIED | `tests/test_bus.c` runs guest WRAM/echo/HRAM and absent cartridge cases; unsupported reads are explicit. |
| D-04 divider falling edges, writes, reload and collision rules | ✓ VERIFIED | `tests/test_timer.c` selector, DIV/TAC, overflow/reload, TIMA/TMA collision cases pass in the full run. |
| D-05 disconnected serial behavior; runner alone interprets LD B,B | ✓ VERIFIED | `tests/test_serial.c` internal/external clock cases pass; core decodes LD B,B as ordinary instruction while `src/runner/main.c` recognizes the result protocol. |
| D-06 full instruction/deadline preflight preserves state and consumes no time on incomplete operations | ✓ VERIFIED | Bus, conditional-stack, CB-budget, event-boundary, timer-mid-instruction, and diagnostic-capacity cases pass; bounded admission paths are present in `gbb_run`/`gbb_run_ex`. |
| D-07 timestamped queue validation and partition equality | ✓ VERIFIED | `tests/test_events.c` covers equal timestamp caller order, atomic invalid/excess batch rejection and equal-elapsed partition behavior; cases pass. |
| D-08 bounded lockup, HALT/STOP, unsupported bus and output-full outcomes | ✓ VERIFIED | Control, bus and output-capacity tests pass; outcomes are distinct and bounded. |
| D-09 nonzero immutable eligible set independently admitted by source/license/model/boot/protocol review and excluding PPU-dependent closures | ✗ FAILED | Rights, digests, pinned sources and byte reproduction are valid, but all three admitted closures include `is_ppu_broken.s`, which reads LY (`FF44`) before assertions/protocol. The context excludes PPU-dependent closures from the denominator, so current applicability admission is invalid. |
| D-10 pinned source/include/asset closure, builder, notices, digests, profile, boot, protocol, budget and malformed-metadata rejection | ✓ VERIFIED | `fixtures/mooneye/manifest.json`, licenses, sources and `cmake/VerifyMooneye.cmake` contain the pinned build/provenance fields; fixture digest/inventory checks pass. This does not establish runtime qualification. |
| D-11 distinct runner statuses, eligible/executed counts and bounded diagnostic receipts | ✓ VERIFIED | `tests/test_runner.c` negative/status controls and `tests/test_diagnostics.c` bound/canary cases pass; observed failing corpus receipts retain recent records and identity fields. |
| D-12 installed C/C++ public consumers and offline tests | ✓ VERIFIED | Relocated install helper and fresh installed consumers pass. The Linux suite used checked-in bytes with no network dependency. |

## Required Artifacts

The runtime artifact-query verbs returned `total: 0` for the phase PLAN files, so they provided no per-artifact evaluation. I checked the declared artifacts and their use directly.

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `include/gabbaboy/gabbaboy.h` | Public bounded CPU/time/API contract | ✓ VERIFIED | Substantive API declarations and contracts are consumed by core, runner, and installed C/C++ examples. |
| `src/core/gabbaboy.c` | CPU, bus, timer, serial, interrupt, event and diagnostic implementation | ✗ FAILED | Substantive and wired, but has four core correctness defects described in CR-01 through CR-04. |
| `tests/test_cpu.c`, `tests/test_control.c` | CPU matrices and state/timing regressions | ⚠️ PARTIAL | Registered and executed, but miss RET/RETI stack phases and repeated-EI behavior; tests therefore cannot protect those claims. |
| `tests/test_bus.c`, `tests/test_timer.c`, `tests/test_serial.c`, `tests/test_events.c` | Mapped bus, timed devices and deterministic events | ✓ VERIFIED | Real guest programs drive supported address/device paths; named focused cases pass. |
| `fixtures/mooneye/manifest.json`, `fixtures/mooneye/*.gb` | Pinned, applicable corpus, source identity and protocol | ✗ FAILED | Rights, digests and reproduction are valid; applicability is not: all three closures are PPU-dependent, contrary to D-09, and execution stops before protocol completion. |
| `src/runner/main.c`, `tests/test_runner.c`, `tests/test_diagnostics.c` | Distinct statuses and replayable bounded receipts | ⚠️ PARTIAL | Correctly reports unsupported and emits bounded history, but current admitted ROMs all fail before protocol results. |
| `tests/scripts/verify-phase2-installed.sh`, C/C++ consumers | Relocated public package/time consumer checks | ✓ VERIFIED | Fresh relocated Linux install executed the installed runner, C consumer and C++ consumer checks successfully. |
| `.github/workflows/ci.yml`, `tests/expected-tests.txt`, `.github/scripts/verify-test-inventory.sh` | Fail-closed CI inventory and sanitizer checks | ⚠️ PARTIAL | Inventory catches failures; the current required suite is red, so CI cannot qualify Phase 2. Hosted exact-SHA green evidence was not supplied. |

## Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `gbb_run` | timed `read8`/`write8` and bus outcome | instruction preflight then timed bus phases | ✓ WIRED | Real guest bus cases exercise state, bus access, and unsupported stop paths. |
| opcode metadata | preflight cost | decoder metadata and instruction cost | ✓ WIRED | Full costs are computed before execution; whole-operation bounds cases pass. |
| instruction execution | timed CPU/timer phases | bus observer and device timeline | ⚠️ PARTIAL | RET/RETI select wrong phases; interrupt entry appends the IF diagnostic before advancing device time to later stack phases. |
| IE/IF/IME | interrupt preflight, stack and vector | `pending_interrupt` / `enter_interrupt` | ⚠️ PARTIAL | Vector/stack path is exercised; repeated EI has incorrect delay semantics and diagnostic order can break. |
| timestamp queue | instance state and STOP wake/device deadlines | queue admission then event timeline | ✓ WIRED | Queue and partition cases pass with instance-owned inputs. |
| timer/serial registers | falling edges, reload and serial completion | timed bus writes and `advance_devices_to` | ✓ WIRED | Named timer/serial tests exercise real decoded writes and timed callbacks. |
| pinned fixture sources | checked-in ROM/digest and offline CTest | WLA-DX recipe, verifier and manifest | ✓ WIRED | Reproduction and digest checks are recorded as passing. |
| eligible manifest | runner denominator and per-ROM result | `run_one` / suite inventory | ✓ WIRED | Denominator remains 3 and executed count is 3; each result is unsupported, so qualification fails honestly. |
| fixture bytes | runner protocol and diagnostic receipt | load, guest execution, LD B,B result and recent trace | ⚠️ PARTIAL | Real ROM bytes flow through the core and receipts retain history, but unsupported LY prevents the declared protocol stage. |
| installed `GabbaBoy::core` | C/C++ consumers and timestamped API | relocated package configure/link/run | ✓ WIRED | Fresh installed consumer checks passed. |
| CTest inventory | CI result | expected test list and JUnit failure gate | ✓ WIRED | The gate detects failed rows and exits nonzero; current corpus failures therefore stop qualification. |

## Data-Flow Trace (Level 4)

| Artifact | Data variable | Source | Produces real data | Status |
|---|---|---|---|---|
| Runner → core | loaded ROM and machine state | Checked-in, digest-verified fixture bytes pass through `gbb_load_rom` and the decoder/bus | Yes; no synthetic pass data | ✓ FLOWING |
| Core → diagnostic records | instruction, bus, timer, and result/stop state | Per-call caller-owned output populated during actual execution | Yes; failing cases retain 128 recent records | ✓ FLOWING, with chronological-order defect during interrupt entry |
| Manifest → suite result | eligible/executed counts and each protocol result | Fixed three-entry manifest-driven loop | Yes; output states 3 eligible, 3 executed, suite fail | ✓ FLOWING, but required protocol is unreachable |

## Behavioral Spot-Checks

| Behavior | Command/evidence | Result | Status |
|---|---|---|---|
| Full normal Linux suite | `/private/tmp/gabbaboy-phase2-boundary-normal/final.log`, revision `c583e338a48f70e83573da700722dcbefa4b705a` | 90/94 pass, 4 fail, 0 skipped; CTest exit 8. Failures: required suite and all three individual Mooneye cases. | ✗ FAIL |
| Full Linux ASan/UBSan suite | Supplied independent run evidence for the same source revision | 90/94 pass, same four corpus failures, 0 skipped; no sanitizer finding. | ✗ FAIL |
| Relocated installed qualification | `/private/tmp/gabbaboy-boundary-helper-final.log` | 95/99 pass, same four corpus failures; all five installed runner/C/C++ checks pass; helper exits 8 and stops. | ✗ FAIL |
| Required corpus protocol | Normal log and installed helper receipts | All three report `status=unsupported`; common `quit.s` path reads LY `FF44` before the LD B,B result signature. Fixed denominator remains 3/3, with suite status fail. | ✗ FAIL |
| RET/RETI phase timing | `src/core/gabbaboy.c:655-658`, compared with pinned RGBDS instruction reference | Shared implementation calls `pop16(...,16,24)` for unconditional RET/RETI; POP uses `8,16`; official reference identifies RET/RETI as four-cycle POP-PC forms and taken RET cc as five cycles. Existing tests do not assert these phases. | ✗ FAIL |
| Consecutive EI | `src/core/gabbaboy.c:693,851`; `tests/test_control.c:72-90` | EI resets delay to 2 on each opcode; current regression covers EI+NOP and EI+DI, not EI+EI. The second EI postpones enable. | ✗ FAIL |
| Interrupt diagnostic ordering | `src/core/gabbaboy.c:711-717` | IF record at offset 8 is appended before `push16` advances devices through offset 16. A timer record in that interval can be appended later with an earlier timestamp. | ✗ FAIL |
| Post-boot F profile | `src/core/gabbaboy.c:119-120`; README profile definition | Reset always sets F to `0x80`; declared profile selects `0x80` for zero checksum and `0xB0` for nonzero checksum. | ✗ FAIL |

## Probe Execution

No `probe-*.sh` paths are declared by the plans or discovered in the project. The strict CTest suite and installed helper are the phase's runnable acceptance probes; both were executed in independent Linux builds and failed on the same four corpus cases. No substitute probe was used.

| Probe | Command | Result | Status |
|---|---|---|---|
| Normal and ASan/UBSan full suite | Linux phase2 CTest inventories | Same four Mooneye failures; 90/94 pass in each run | FAILED |
| Installed package helper | `bash tests/scripts/verify-phase2-installed.sh` in Linux AMD64 container | 95/99 pass; helper rejects failed suite; installed consumer cases themselves pass | FAILED |

## Requirements Coverage

| Requirement | Source plans | Description | Status | Evidence |
|---|---|---|---|---|
| CPU-01 | 02-02, 02-03, 02-07, 02-09 | Correct tested base/CB semantics, flags, addresses and bus timing; explicit illegal behavior | BLOCKED | The base matrix misses wrong RET/RETI bus phases, and startup F is profile-inaccurate. Lockup and CB coverage pass but do not satisfy the whole contract. |
| CPU-02 | 02-04, 02-06, 02-09 | Interrupt, EI delay, HALT/HALT-bug, STOP, reset and deterministic post-boot behavior | BLOCKED | Repeated EI postpones IME; post-boot F ignores checksum. Other control tests passing cannot close those required states. |
| CPU-03 | 02-01, 02-05, 02-06, 02-07, 02-09 | Declared memory map, divider/timer edges/reload races and disconnected serial behavior | BLOCKED — requirement remains pending | Owned bus/timer/serial cases pass for the declared implementation paths, but the required eligible set is not validly admitted: timer ROM closures are PPU-dependent. This supports the owned-case verdict above but does not complete CPU-03 qualification. |
| CPU-04 | 02-01, 02-02, 02-04, 02-06, 02-08, 02-09 | Partition determinism and bounded LCD-off/HALT/STOP/lockup/output outcomes | BLOCKED | Event partitions and bounded stops pass, but diagnostics can be returned out of timestamp order during interrupt entry, violating deterministic caller evidence. |
| CPU-05 | 02-07, 02-08, 02-09 | Pinned CPU/timer corpus reports scoped results and retained replay evidence | BLOCKED | The fixed eligible ROMs stop as unsupported before protocol completion; strict suite and installed qualification fail. |

All five requirements are mapped in the phase plans and roadmap; none is orphaned. REQUIREMENTS.md still marks all five pending, consistent with this report.

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| — | — | No unreferenced TBD/FIXME/XXX debt markers, placeholder implementations, or hardcoded empty guest-output stubs found in the reviewed implementation set. | — | — |

## Human Verification Required

None. The identified gaps are deterministic implementation and corpus-qualification defects with automated reproduction paths; manual acknowledgement cannot close them. No routine UAT is required for this headless phase.

## Gaps Summary

Five actionable gaps block the goal: (1) derive reset/post-boot F from the loaded ROM checksum profile; (2) correct RET/RETI timed stack reads and add direct phase regressions; (3) preserve the scheduled EI enable across consecutive EI and test the pending-interrupt sequence; (4) emit timer and IF/stack diagnostics in chronological order with a deadline-during-entry regression; and (5) replace or repair the source-qualified corpus path so each pinned CPU/timer ROM reaches its declared result protocol and the full strict suite passes. The artifact is substantive and broadly wired, but the current results do not establish the full DMG instruction/timing profile or reproducible corpus qualification. These gaps are not explicitly completed by later milestone success criteria, so they remain actionable in Phase 2.

---

_Verified: 2026-10-06T21:40:15Z_  
_Verifier: the agent (gsd-verifier)_
