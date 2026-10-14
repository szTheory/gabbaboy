---
phase: "12"
slug: "cgb-double-speed"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
status: validated
nyquist_compliant: true
wave_0_complete: true
created: "2026-10-13"
---

# Phase 12 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution. Source: `12-RESEARCH.md` § Validation Architecture; decisions in `12-CONTEXT.md` D-01..D-45. Zero human UAT (D-069): every row has an automated check and a negative control.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | CTest over C executables (`REQUIRE` macros), CMake `-P` verifiers, stdlib Python verifiers (`python3 -I`), configure-time core mutants, white-box single-TU tests |
| **Config file** | `CMakePresets.json` (`phase1`, `phase1-asan` Linux-only); inventories `tests/expected-tests.txt`, `tests/player/expected-tests.txt` |
| **Quick run command** | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --test-dir build -R '^(cgb_speed_\|cgb_partition_\|age_\|cgb_fuzz_speed_)' --output-on-failure --no-tests=error` |
| **Full suite command** | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --test-dir build -j8 --output-on-failure --no-tests=error` |
| **Identity gate** | `ctest --test-dir build -R '^(dmg_baseline\|cgb_dmg_identity\|cgb_speed_identity\|banking_tracer_digest_unchanged)' --output-on-failure --no-tests=error && bash tests/scripts/verify-dmg-baseline.sh` |
| **Estimated runtime** | quick ~10 s; full ~60 s local Debug (`-j8`); hosted ASan leg must stay inside the GB-CI-004 budget |

(Inside table cells `\|` is regex alternation; drop the backslash when typing.)

---

## Sampling Rate

- **After every task commit:** the plan's own `-R` prefix (seconds), plus the identity gate on any task that edits `src/core/gabbaboy.c`.
- **After every plan wave:** full suite command.
- **Before `/gsd-verify-work`:** full suite green locally, and exact-head hosted CI green on every leg (Linux, macOS, Windows, ASan/UBSan, cmake floor, fixture-repro, player job).
- **Max feedback latency:** 60 s locally.

---

## Ordering rule (D-37)

Every white-box expectation of the stall length derives from `GBB_SPEED_SWITCH_STALL_T` (never a numeric literal; enforced by a grep gate in plans 12-01, 12-07, 12-09 and 12-14). The committed-core AGE `spsw-div` window is re-measured by `age_stall_window` in plan 12-09, which runs before every constant-derived pin: original-fixture digests (12-10/12-11), the player RGBA digest (12-12), partition windows (12-14), AGE signatures and budgets other than spsw-div's (12-16), the sensitivity record (12-17) and the numeric doc-contract phrases (added in 12-09 itself, after the measurement).

---

## Per-Task Verification Map

Per-task rows are filled in by the planner and executors. The requirement-level contract they must cover:

| Req / Decision | Behaviour | Plan | Test Type | Automated Command (`-R`) | Negative control | Status |
|---|---|---|---|---|---|---|
| D-45 | Pre-change CGB single-speed identity pin recorded before any core edit | 12-01 | white-box pin | `'^cgb_speed_identity_pin$'` | `cgb_speed_identity_pin_flipped` | ✅ green |
| D-13 | One trace record at STOP retire, none per stall chunk, no speed field | 12-01 | white-box | `'^cgb_speed_tracer_switch$'` | static assert on `sizeof(gbb_trace_record)`; stall-only call must return `trace_count` 0 | ✅ green |
| D-25 | Mutant harness: multi-site anchors, exactly-once guard | 12-03 | configure-time | `'^cgb_speed_mutant_'` | `cgb_speed_mutant_anchor_guard` (duplicated anchor must stop generation); every pair has a mask-0 control | ✅ green |
| SC1 / D-03 | KEY1 `$7E`→`$7F`→`$FE`→`$7E` | 12-06 | white-box | `'^cgb_speed_key1_readback$'` | M10 (KEY1 bit 0 not cleared) | ✅ green |
| SC1 / D-03 | KEY0 writes never switch | 12-06 | white-box | `'^cgb_speed_key0_no_switch$'` | M32 (a KEY0 write toggles `double_speed`) | ✅ green |
| SC1 / D-10 | Cost, bus offsets and interrupt/halt literals scale by `cpu_ticks` | 12-03 | white-box | `'^cgb_speed_cpu_ticks$'` | M18 (three sites: cost, bus_read and bus_write offsets unscaled) | ✅ green |
| SC1 / D-10 | Timer, serial and OAM DMA run at 2× per scanline; remainders survive a switch | 12-05 | white-box | `'^cgb_speed_(timer\|serial\|dma)_scaling$'`, `'^cgb_speed_remainder_across_switch$'` | M2, M3, M11, M14, M15 | ✅ green |
| SC1 / D-11 | APU tap is bit 12 at normal speed and bit 13 at double; sequencer stays 512 Hz | 12-05 | white-box | `'^cgb_speed_apu_tap$'` | M4 | ✅ green |
| SC1 / D-10 | PPU, APU and RTC unscaled; structural scan | 12-05 | white-box + scan | `'^cgb_speed_ppu_apu_rtc_unscaled$'`, `'^cgb_speed_domains_scan'` | M1, M12, M17, `cgb_speed_domains_scan_mutated` | ✅ green |
| SC1 / D-22 | Original fixture probes with first-principles expectations | 12-10 | fixture + derivation | `'^cgb_speed_fixture_probes$'`, `'^cgb_speed_expectations_'` | tampered table; factor-3 derivation | ✅ green |
| SC2 / D-22 | Hostile entry points (selector byte) | 12-11 | fixture | `'^cgb_speed_fixture_hostile$'` | `cgb_speed_expectations_hostile_tampered`; selector 0/9 markers | ✅ green |
| D-22 | Fixture rebuilds byte-exactly | 12-13 | repro | `'^cgb_speed_repro_'` | tool-failure and missing-pin stubs | ✅ green |
| D-15, D-41 | Fixture audio and frame digests | 12-10 | core digest | `'^cgb_speed_fixture_(audio\|frame)_digest'` | M17 (APU 2×), M1 (PPU follows CPU) | ✅ green |
| SC1 / D-19, D-20, D-44 | AGE ROMs pinned by measurement; spsw-div passes | 12-09, 12-16 | third-party | `'^age_'` | `age_fixture_digest_tampered`, signature flip rule, `age-expected-failure-now-passes` | ✅ green |
| D-19 | AGE rebuild gate | 12-02, 12-16 | repro | `'^age_repro_'` | `age_repro_compare_tampered` (flipped ROM byte → `result=differs`), `age_repro_selfcheck_tampered` | ✅ green |
| D-37 | Committed-core spsw-div window re-measured before any constant-derived pin | 12-09 | third-party + mutant | `'^age_stall_window$'` | the window edges themselves (offsets lo-1 and hi+1 must fail) | ✅ green |
| D-21 | Stall sensitivity sweep recorded and enforced | 12-17 | third-party + mutant | `'^age_sensitivity_'` | recorded discriminating set must match | ✅ green |
| SC2 / D-37, D-06 | Stall = `GBB_SPEED_SWITCH_STALL_T` T at the destination speed in whole M-cycle steps | 12-01, 12-03, 12-07 | white-box + static assert | `'^cgb_speed_stall_length$'`, `'^cgb_speed_stall_static_assert_mutant$'` | M6, M21, M28, static-assert mutant | ✅ green |
| SC2 / D-07 | Devices advance during the stall | 12-07 | white-box | `'^cgb_speed_stall_devices_advance$'` | M7 | ✅ green |
| SC2 / D-06, D-13 | Never STOPPED/HALTED_IDLE; BUDGET semantics | 12-07 | white-box + API | `'^cgb_speed_never_stopped$'`, `'^cgb_speed_budget_semantics$'` | M5, M9 | ✅ green |
| SC2 / D-01, D-39 | DMG, compat and unarmed STOP byte-identical | 12-06 | existing + white-box | `'^cgb_stop_'`, `'^cgb_speed_dmg_unarmed_unchanged$'` | M8, M30 | ✅ green |
| SC2 / D-02, D-36 | Decision table cases 1–4 | 12-06 | white-box | `'^cgb_speed_stop_cases$'` | M19, M20, M27 | ✅ green |
| SC2 / D-04 | Operand independence | 12-06 | white-box | `'^cgb_speed_stop_operand$'` | M33 (operand $FF changes the switch) | ✅ green |
| SC2 / D-04 | STOP fetched from `$FF04` | 12-06 | white-box | `'^cgb_speed_stop_prefetch_ff04$'` | `cgb_speed_stop_prefetch_ff04_negative` (fetched byte not `$10` must fail) | ✅ green |
| SC2 / D-38 | Switch STOP costs 2 M at the executing speed | 12-06 | white-box | `'^cgb_speed_stop_cost$'` | M29 | ✅ green |
| SC2 / D-08, D-34 | Interrupt wake at M boundary, IME on and off | 12-07 | white-box | `'^cgb_speed_wake_'` | M13, M16 | ✅ green |
| SC2 / D-08 | `EI; STOP` retires EI before the stall | 12-07 | white-box | `'^cgb_speed_ei_stop$'` | M34 (STOP fallthrough / EI delay undone before the stall; two independently exercised anchors) | ✅ green |
| SC2 / D-09 | Realignment into normal speed | 12-07 | white-box | `'^cgb_speed_realign$'` | M23 | ✅ green |
| SC2 / D-18 | Reset clears each new field | 12-03 | white-box | `'^cgb_speed_reset_'` | M24, M25, M26 | ✅ green |
| SC2 / D-28, D-40 | Headroom pre-check before mutation | 12-07 | white-box | `'^cgb_speed_headroom$'` | M22 | ✅ green |
| SC3 / D-26 | Partitioned run equals a single run; stall-end windows on the real constant both directions; pending IRQ / held-plus-pending at STOP | 12-14 | white-box | `'^cgb_partition_'` | joypad shift by one M (digest must change); inert-input check; M16; snapshot fidelity | ✅ green |
| SC3 / D-24 | Every expected-failure row names a `pinned_by` test of current behaviour that is in the inventory | 12-17 | CMake + Python | `'^cgb_speed_dispositions'`, `'^cgb_speed_xfail_'` | `cgb_speed_dispositions_mutated` (reason edited), `cgb_speed_dispositions_pinned_by_missing`; pin negatives (M7, M14, `--write-ff54`, `--poke-oam`) | ✅ green |
| SC3 / D-12 | No `research:12` remains; gate rows and tags agree | 12-08 | scanner | `'^model_gates'` | reverted row | ✅ green |
| D-27, D-43 | Fuzz `cgb_speed` mode invariants | 12-15 | fuzz regression | `'^cgb_fuzz_speed_'` | inverted oracle raises `contract_failures` | ✅ green |
| D-15, D-41 | Player smoke RGBA digest; claims text agrees | 12-12 | player e2e (macOS job) | `'^player_cgb_speed_smoke'`, `'^player_(limitations\|claims_agree)'` | wrong SHA; PPU-follows-CPU mutant; missing phrase | ✅ green |
| D-16, D-42 | Installed consumers run inline speed guest in partitions | 12-12 | installed | `'^installed_consumer_'` | unarmed twin guest must be rejected by the same checker | ✅ green |
| D-14 | No new public symbol | 12-12, 12-18 | existing | `'^cgb_consumer_symbol_coverage'` | existing selftest | ✅ green |
| D-17 | Docs agree with code and gates | 12-08, 12-09, 12-18 | doc contracts | `'^(cgb_speed_profile_contract\|cgb_adr_half_dot_contract\|cgb_native_guide_contract\|cgb_tables_io\|cgb_speed_docs_no_stale_claims)'` | missing-phrase selftests; stale-claim mutated copy | ✅ green |
| D-29, D-30, D-31 | ASan wall time recorded; bench advisory; SUMMARY coverage schema | 12-19 | recorded + CTest | `'^summary_coverage'`, `12-BENCH.md` | existing wrong-digest controls | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `cgb_speed_identity_pin` recorded from the unmodified core (D-45)
- [x] `tests/test_cgb_speed_internal.c` and the `gbb_test_speed_state` seam
- [x] Runtime-mask mutant generator `cmake/P12Mutants.cmake` (multi-site anchors, ≤6 builds, exactly-once anchors with a guard control)
- [x] `fixtures/age/` (13 ROMs, rights, manifest), `reproduce-age.sh` and `test-reproduce-age.sh`; `tests/test_age.c`
- [x] `fixtures/cgb-speed/` with `derive-cgb-speed-expectations.py` and `reproduce-cgb-speed.sh`
- [x] `tests/external/cgb-speed-dispositions.json` and its verifier (with the `pinned_by` inventory check)
- [x] `tests/fuzz/fuzz_core.dict`

---

## Manual-Only Verifications

All phase behaviors have automated verification (D-069). Hosted-only legs (Linux ASan and the macOS player job) are automated in CI, not manual.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Audited local full-suite feedback: 36.36s at `12bb1e1`; hosted-only timings are recorded separately in `12-BENCH.md`.
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** automated validation audit 2026-10-14; no human checkpoint required.

## Audited Task Coverage

All 49 tasks across 19 plans have an automated command. Their implementation and negative-control mappings are recorded above and in each SUMMARY coverage block. No new test gap was found.

| Task | Wave | Requirement | Deliverable | Automated verification and evidence | Status |
|---|---|---|---|---|---|---|
| 12-01-01 | 1 | CGB-06 | Task 1: Pre-change CGB single-speed identity pin from the unmodified core (D-45; precedes the tracer because the pin must be recorded before any core edit) | [12-01 automated verify](12-01-PLAN.md); [12-01 evidence](12-01-SUMMARY.md) | green |
| 12-01-02 | 1 | CGB-06 | Task 2: Tracer - KEY1 arm + STOP case 4 switches speed, resets DIV, loads and consumes a persisted stall end-to-end, with the D-13 trace rule | [12-01 automated verify](12-01-PLAN.md); [12-01 evidence](12-01-SUMMARY.md) | green |
| 12-02-01 | 1 | CGB-06 | Task 1: Tracer - spsw-div-cgbBCE rebuilt from the pinned commit, manifest row, self-check, compare and compare-built end-to-end | [12-02 automated verify](12-02-PLAN.md); [12-02 evidence](12-02-SUMMARY.md) | green |
| 12-02-02 | 1 | CGB-06 | Task 2: Eligibility and warning files, notices, offline rebuild negative controls and the fixture-repro step | [12-02 automated verify](12-02-PLAN.md); [12-02 evidence](12-02-SUMMARY.md) | green |
| 12-03-01 | 2 | CGB-06 | Task 1: Tracer - multi-site runtime-mask mutant harness end-to-end, proven by M5 and M7 and by an anchor-guard negative control | [12-03 automated verify](12-03-PLAN.md); [12-03 evidence](12-03-SUMMARY.md) | green |
| 12-03-02 | 2 | CGB-06 | Task 2: cpu_ticks contract case and the three-site M18 mutant (D-10) | [12-03 automated verify](12-03-PLAN.md); [12-03 evidence](12-03-SUMMARY.md) | green |
| 12-03-03 | 2 | CGB-06 | Task 3: Per-field reset tests with reset-omission mutants (D-18) | [12-03 automated verify](12-03-PLAN.md); [12-03 evidence](12-03-SUMMARY.md) | green |
| 12-04-01 | 2 | CGB-06 | Task 1: Tracer - spsw-tima-cgbE rebuilt, row added, compared byte-identical through the manifest-driven script | [12-04 automated verify](12-04-PLAN.md); [12-04 evidence](12-04-SUMMARY.md) | green |
| 12-04-02 | 2 | CGB-06 | Task 2: The other 11 ROMs, their rows and the exclusion check | [12-04 automated verify](12-04-PLAN.md); [12-04 evidence](12-04-SUMMARY.md) | green |
| 12-05-01 | 3 | CGB-06 | Task 1: Tracer - timer path at double speed end-to-end (cpu_tick restructure, tick-unit reload, TIMA per scanline doubles) | [12-05 automated verify](12-05-PLAN.md); [12-05 evidence](12-05-SUMMARY.md) | green |
| 12-05-02 | 3 | CGB-06 | Task 2: Serial, OAM DMA, APU tap and remainders across a switch | [12-05 automated verify](12-05-PLAN.md); [12-05 evidence](12-05-SUMMARY.md) | green |
| 12-05-03 | 3 | CGB-06 | Task 3: PPU, APU and RTC stay in master time - unit case, structural scan and mutants | [12-05 automated verify](12-05-PLAN.md); [12-05 evidence](12-05-SUMMARY.md) | green |
| 12-06-01 | 4 | CGB-06 | Task 1: Tracer - pending-IRQ STOP (case 3) switches without a stall, is 1 byte, and dispatches with IME set | [12-06 automated verify](12-06-PLAN.md); [12-06 evidence](12-06-SUMMARY.md) | green |
| 12-06-02 | 4 | CGB-06 | Task 2: Held button, operand independence, FF04 fetch, switch cost, DMG/unarmed identity and the KEY1/KEY0 contract | [12-06 automated verify](12-06-PLAN.md); [12-06 evidence](12-06-SUMMARY.md) | green |
| 12-07-01 | 5 | CGB-06 | Task 1: Tracer - a timer interrupt raised during the stall ends it at an M-cycle boundary and dispatches with IME set | [12-07 automated verify](12-07-PLAN.md); [12-07 evidence](12-07-SUMMARY.md) | green |
| 12-07-02 | 5 | CGB-06 | Task 2: IME-off wake, EI;STOP, M-boundary sampling and the D-09 realignment tail | [12-07 automated verify](12-07-PLAN.md); [12-07 evidence](12-07-SUMMARY.md) | green |
| 12-07-03 | 5 | CGB-06 | Task 3: Stall length, budget and stop-reason semantics, devices advancing and the headroom pre-check | [12-07 automated verify](12-07-PLAN.md); [12-07 evidence](12-07-SUMMARY.md) | green |
| 12-08-01 | 6 | CGB-06 | Task 1: Tracer - resolve GATE-65 at the divider_reset call sites end-to-end through the scanner | [12-08 automated verify](12-08-PLAN.md); [12-08 evidence](12-08-SUMMARY.md) | green |
| 12-08-02 | 6 | CGB-06 | Task 2: Remaining D-12 dispositions, new GATE-84.. rows, GATE-62 retag with GBB_MG_STOP_TAG_REGEX, no-phase-12-rows check | [12-08 automated verify](12-08-PLAN.md); [12-08 evidence](12-08-SUMMARY.md) | green |
| 12-08-03 | 6 | CGB-06 | Task 3: docs/cgb-profile.md - implemented STOP table, stall derivation, resolved timeline, expected-failure names and a doc contract | [12-08 automated verify](12-08-PLAN.md); [12-08 evidence](12-08-SUMMARY.md) | green |
| 12-09-01 | 7 | CGB-06 | Task 1: Tracer - tests/test_age.c judges spsw-div-cgbBCE as a pass end-to-end with a measured budget | [12-09 automated verify](12-09-PLAN.md); [12-09 evidence](12-09-SUMMARY.md) | green |
| 12-09-02 | 7 | CGB-06 | Task 2: Public mutant library, test_age_p12 and age_stall_window re-measure with the D-37 re-pin rule | [12-09 automated verify](12-09-PLAN.md); [12-09 evidence](12-09-SUMMARY.md) | green |
| 12-09-03 | 7 | CGB-06 | Task 3: Record the measured window in docs/cgb-profile.md and add the numeric contract phrases | [12-09 automated verify](12-09-PLAN.md); [12-09 evidence](12-09-SUMMARY.md) | green |
| 12-10-01 | 8 | CGB-06 | Task 1: Tracer - speed.gb TIMA-per-line, KEY1 and lines-across-STOP probes, manifest, derivation and host verdict end-to-end | [12-10 automated verify](12-10-PLAN.md); [12-10 evidence](12-10-SUMMARY.md) | green |
| 12-10-02 | 8 | CGB-06 | Task 2: Remaining probes and bounds, with the tampered-table and factor-3 derivation controls | [12-10 automated verify](12-10-PLAN.md); [12-10 evidence](12-10-SUMMARY.md) | green |
| 12-10-03 | 8 | CGB-06 | Task 3: Core-level audio and frame digests of speed.gb with the APU-2x and PPU-follows-CPU controls | [12-10 automated verify](12-10-PLAN.md); [12-10 evidence](12-10-SUMMARY.md) | green |
| 12-11-01 | 9 | CGB-06 | Task 1: Tracer - speed-hostile.gb selector 1 (IE set, IRQ pending, IME 1) end-to-end through the derivation and the host test | [12-11 automated verify](12-11-PLAN.md); [12-11 evidence](12-11-SUMMARY.md) | green |
| 12-11-02 | 9 | CGB-06 | Task 2: Entries 2-8 and the tampered-outcome control | [12-11 automated verify](12-11-PLAN.md); [12-11 evidence](12-11-SUMMARY.md) | green |
| 12-12-01 | 9 | CGB-06 | Task 1: Tracer - player_cgb_speed_smoke over speed.gb end-to-end with wrong-SHA and PPU-follows-CPU controls | [12-12 automated verify](12-12-PLAN.md); [12-12 evidence](12-12-SUMMARY.md) | green |
| 12-12-02 | 9 | CGB-06 | Task 2: D-41 claims edit on all five surfaces with the claims-agree phrase | [12-12 automated verify](12-12-PLAN.md); [12-12 evidence](12-12-SUMMARY.md) | green |
| 12-12-03 | 9 | CGB-06 | Task 3: Installed C and C++ consumers run an inline speed guest in partitions | [12-12 automated verify](12-12-PLAN.md); [12-12 evidence](12-12-SUMMARY.md) | green |
| 12-13-01 | 10 | CGB-06 | Task 1: Tracer - reproduce-cgb-speed.sh rebuilds both cgb-speed ROMs byte-identically from the manifest | [12-13 automated verify](12-13-PLAN.md); [12-13 evidence](12-13-SUMMARY.md) | green |
| 12-13-02 | 10 | CGB-06 | Task 2: Offline repro controls, Windows removal list and the fixture-repro step | [12-13 automated verify](12-13-PLAN.md); [12-13 evidence](12-13-SUMMARY.md) | green |
| 12-14-01 | 11 | CGB-06 | Task 1: Tracer - stall-start window partition sweep with the full digest, end-to-end, and the M16 mutant failing it | [12-14 automated verify](12-14-PLAN.md); [12-14 evidence](12-14-SUMMARY.md) | green |
| 12-14-02 | 11 | CGB-06 | Task 2: Real-constant stall-end windows in both directions via a white-box snapshot, plus interior, seeded, budget and scenario cases | [12-14 automated verify](12-14-PLAN.md); [12-14 evidence](12-14-SUMMARY.md) | green |
| 12-14-03 | 11 | CGB-06 | Task 3: Sensitivity controls - the digest must change for a one-M joypad shift and for a mutated digest input | [12-14 automated verify](12-14-PLAN.md); [12-14 evidence](12-14-SUMMARY.md) | green |
| 12-15-01 | 12 | CGB-06 | Task 1: Tracer - fuzz_speed mode with invariants, the arm-and-switch seed and its positive control, end-to-end | [12-15 automated verify](12-15-PLAN.md); [12-15 evidence](12-15-SUMMARY.md) | green |
| 12-15-02 | 12 | CGB-06 | Task 2: Seven more seeds, the inverted-oracle control, the dictionary and -dict= in run-bounded-fuzz.sh | [12-15 automated verify](12-15-PLAN.md); [12-15 evidence](12-15-SUMMARY.md) | green |
| 12-16-01 | 13 | CGB-06 | Task 1: Tracer - dispositions JSON drives configure-time age_ generation for spsw-div (moved from its manual registration) and spsw-stop-prefetch, end-to-end | [12-16 automated verify](12-16-PLAN.md); [12-16 evidence](12-16-SUMMARY.md) | green |
| 12-16-02 | 13 | CGB-06 | Task 2: The other 11 ROMs measured and pinned with measurement-decided dispositions | [12-16 automated verify](12-16-PLAN.md); [12-16 evidence](12-16-SUMMARY.md) | green |
| 12-16-03 | 13 | CGB-06 | Task 3: CTest guards for the vendored bytes (digest, self-check, offline rebuild controls, install scan) and the Linux digest record | [12-16 automated verify](12-16-PLAN.md); [12-16 evidence](12-16-SUMMARY.md) | green |
| 12-17-01 | 14 | CGB-06 | Task 1: Tracer - speed-switch-pause-ppu-output pinned by a new test, recorded with pinned_by, and verified against the inventory with a negative control | [12-17 automated verify](12-17-PLAN.md); [12-17 evidence](12-17-SUMMARY.md) | green |
| 12-17-02 | 14 | CGB-06 | Task 2: The other three pin tests, every remaining row, non-vendored suites, the full verifier and the docs mirror | [12-17 automated verify](12-17-PLAN.md); [12-17 evidence](12-17-SUMMARY.md) | green |
| 12-17-03 | 14 | CGB-06 | Task 3: D-21 sensitivity sweep recorded in the dispositions file and enforced | [12-17 automated verify](12-17-PLAN.md); [12-17 evidence](12-17-SUMMARY.md) | green |
| 12-18-01 | 15 | CGB-06 | Task 1: Tracer - native-integration guide and header comments state master-time budgets and the stall stop reason, enforced by the guide contract | [12-18 automated verify](12-18-PLAN.md); [12-18 evidence](12-18-SUMMARY.md) | green |
| 12-18-02 | 15 | CGB-06 | Task 2: Release notes, preview, cartridge and RTC docs, and the stale-claim scanner with its control | [12-18 automated verify](12-18-PLAN.md); [12-18 evidence](12-18-SUMMARY.md) | green |
| 12-19-01 | 16 | CGB-06 | Task 1: Tracer - adopted decisions, lessons and the research-index entry, each pointing at evidence that exists | [12-19 automated verify](12-19-PLAN.md); [12-19 evidence](12-19-SUMMARY.md) | green |
| 12-19-02 | 16 | CGB-06 | Task 2: 12-BENCH.md - advisory benchmark, hosted ASan wall time against GB-CI-004, mutant build count, full-suite evidence | [12-19 automated verify](12-19-PLAN.md); [12-19 evidence](12-19-SUMMARY.md) | green |
| 12-19-03 | 16 | CGB-06 | Task 3: COVERAGE.md declaration, SUMMARY coverage check and the stage handoff without starting Phase 13 | [12-19 automated verify](12-19-PLAN.md); [12-19 evidence](12-19-SUMMARY.md) | green |

### Current evidence

- Root tail run at `12bb1e13533cc9738239a3d51d156d610c32cb37`: `ctest --test-dir build --output-on-failure --no-tests=error -j8` passed 897/897 in 36.36 seconds.
- `python3 -I .planning/phases/GB-12-cgb-double-speed/verify-closeout-contract.py --self-test` passed its positive case and 17 scratch mutations.
- Exact hosted source receipt at `301f1b05577e6d35a4c3a756ded1ec15a4082c8d`: PR CI `38502094649`, fixture reproduction `38502094682`, and package smoke `38502094771` passed. ASan ran 892/892 with zero skips; native Windows ran its platform-adjusted inventory. The player package and installed consumers passed in hosted lanes. Later local commits through `12bb1e1` add closeout metadata and its validator; final-head hosted checks remain required before the final handoff.
- Physical hardware, unadmitted suites and unresolved model effects are evidence exclusions in the dispositions; they are not manual UAT checkpoints. No libFuzzer campaign is claimed locally.

## Validation Audit 2026-10-14

| Metric | Count |
|---|---|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
