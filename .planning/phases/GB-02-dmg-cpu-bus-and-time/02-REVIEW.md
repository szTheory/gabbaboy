---
phase: GB-02-dmg-cpu-bus-and-time
reviewed: 2026-10-06T21:32:24Z
depth: standard
files_reviewed: 35
files_reviewed_list:
  - .github/scripts/verify-test-inventory.sh
  - .github/workflows/ci.yml
  - .github/workflows/fixture-repro.yml
  - .gitignore
  - CMakeLists.txt
  - README.md
  - cmake/ExpectedTests.cmake
  - cmake/VerifyMooneye.cmake
  - fixtures/mooneye/FONT-LICENSE.txt
  - fixtures/mooneye/LICENSE.txt
  - fixtures/mooneye/SOURCES.md
  - fixtures/mooneye/font-source.c
  - fixtures/mooneye/manifest.json
  - fixtures/tracer/manifest.json
  - fixtures/tracer/tracer.asm
  - include/gabbaboy/gabbaboy.h
  - src/core/gabbaboy.c
  - src/runner/main.c
  - tests/CMakeLists.txt
  - tests/consumers/c/main.c
  - tests/consumers/cpp/main.cpp
  - tests/expect_runner_failure.cmake
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
findings:
  critical: 5
  warning: 0
  info: 0
  total: 5
status: issues_found
---

# Phase GB-02: Code Review Report

**Reviewed:** 2026-10-06T21:32:24Z  
**Depth:** standard  
**Files Reviewed:** 35  
**Status:** issues_found

## Summary

Review covered the 35 explicit Phase 2 text files and the core callees involved in CPU execution, timed bus accesses, interrupt handling, diagnostics, fixture qualification, and CI gating. Five BLOCKER findings remain. Four are CPU/profile/API correctness defects in the core. The fixed three-ROM suite is also not qualified: every ROM reaches a shared LY read before its declared LD B,B result protocol, so the required suite fails with unsupported bus behavior. Current evidence reports 90/94 passing locally and no hosted exact-SHA green result; passing focused corrections do not close these blockers.

## Narrative Findings (AI reviewer)

### CR-01: BLOCKER — Post-boot F ignores the cartridge header checksum

**File:** `src/core/gabbaboy.c:119-122`

**Issue:** `reset_state` always initializes F to `0x80`. The documented DMG-CPU-B profile says the header checksum selects F: `0x80` when the checksum is zero and `0xB0` otherwise ([README.md:95-100](README.md#L95)). The checked-in tracer uses the nonzero-checksum profile, but starts with the wrong flags. Conditional CPU behavior at the first instructions can therefore differ from the declared startup state. Reset also needs to restore the same ROM-specific profile state.

**Fix:** Set the post-boot F value from the loaded ROM's header checksum on load and reset, retaining `0x80` only for a zero checksum; add cases for both checksum values that inspect the initial trace state and branch outcome. If the intended profile is instead checksum-independent, change the profile contract and all fixture claims consistently.

### CR-02: BLOCKER — Unconditional RET and RETI read the stack one machine cycle late

**File:** `src/core/gabbaboy.c:655-658`

**Issue:** Taken conditional RET has an extra condition-check cycle, so its low/high stack reads at offsets 16/24 are appropriate. Unconditional RET and RETI have no such cycle, but the shared branch uses those same offsets while `decode` assigns them the 32-half-dot four-cycle cost. Their reads should occupy the earlier stack phases (offsets 8/16, as POP does), with the final return cycle following them. This makes timer/event observations and bus diagnostics wrong around RET/RETI even though instruction totals and final SP/PC pass. The base matrix tests only total time and final state, so it cannot detect this phase error.

**Fix:** Choose the stack-read offsets by instruction form: unconditional RET/RETI use the two POP read phases; taken RET cc retains its later phases. Add timed-observer tests for both cases and assert the event ordering against an independent expected sequence. The pinned [RGBDS v1.0.1 opcode reference](https://rgbds.gbdev.io/docs/v1.0.1/gbz80.7) distinguishes four-cycle RET from five-cycle taken RET cc.

### CR-03: BLOCKER — Repeated EI postpones IME for an extra instruction

**File:** `src/core/gabbaboy.c:692-694`, `src/core/gabbaboy.c:849-851`

**Issue:** Each EI unconditionally resets `ime_delay` to 2, then the run loop decrements it after that instruction. With `EI; EI; NOP` and an enabled pending interrupt, the second EI restarts the countdown, so the NOP executes before interrupt entry. The first EI's one-instruction delay should expire after the second EI; repeated EI must not postpone that already scheduled enable.

**Fix:** Represent the pending enable as an instruction-boundary latch that cannot be restarted by a subsequent EI, or preserve the active countdown when EI executes. Add a pending-interrupt regression for consecutive EI instructions and assert vector entry before the following instruction.

### CR-04: BLOCKER — Interrupt diagnostics can violate chronological order

**File:** `src/core/gabbaboy.c:711-718`

**Issue:** `enter_interrupt` appends the IF-acknowledge bus record at `start+8` before `push16` advances devices through `start+16`. If a timer diagnostic occurs between those times, it is appended after the IF record with an earlier timestamp. `gbb_run_ex` promises chronological diagnostics in [include/gabbaboy/gabbaboy.h:99-106](../../include/gabbaboy/gabbaboy.h#L99), and the C/C++ consumers check that contract. The interrupt path therefore can return a non-chronological record array.

**Fix:** Advance the shared timeline to the IF-acknowledge phase before appending/mutating that bus operation, and ensure all device deadline records are emitted before later-timestamp CPU records. Add an interrupt-entry test with a timer edge/reload inside the entry window and assert every adjacent diagnostic timestamp is nondecreasing.

### CR-05: BLOCKER — The required Mooneye corpus cannot reach its declared result protocol

**File:** `fixtures/mooneye/manifest.json:27-28`, `fixtures/mooneye/SOURCES.md:35-39`

**Issue:** The manifest marks the inventory complete and admits all three ROMs, but each source closure includes `common/lib/quit.s` and `common/lib/is_ppu_broken.s`; the latter reads LY at `FF44` before the LD B,B result breakpoint. The Phase 2 bus intentionally rejects this unsupported PPU read, so the runner returns unsupported and none of the required CPU/timer cases can pass. This is a confirmed eligibility/qualification gap, not an emulator result to work around. The current validation record shows the required CTests fail, and there is no hosted exact-SHA green evidence.

**Fix:** Keep the required IDs and strict gate intact while preparing a source-qualified completion path or alternate pinned fixtures whose real execution reaches the CPU/timer protocol without PPU access. Rebuild and digest-verify the bytes, update source/protocol/rights evidence, and make the complete offline suite pass before claiming CPU-05 or Phase 2 qualification. Do not substitute fabricated LY behavior or weaken the expected gate.

---

_Reviewed: 2026-10-06T21:32:24Z_  
_Reviewer: the agent (gsd-code-reviewer)_  
_Depth: standard_
