---
phase: "12"
slug: "cgb-double-speed"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
status: draft
nyquist_compliant: false
wave_0_complete: false
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
| D-45 | Pre-change CGB single-speed identity pin recorded before any core edit | 12-01 | white-box pin | `'^cgb_speed_identity_pin$'` | `cgb_speed_identity_pin_flipped` | ⬜ pending |
| D-13 | One trace record at STOP retire, none per stall chunk, no speed field | 12-01 | white-box | `'^cgb_speed_tracer_switch$'` | static assert on `sizeof(gbb_trace_record)`; stall-only call must return `trace_count` 0 | ⬜ pending |
| D-25 | Mutant harness: multi-site anchors, exactly-once guard | 12-03 | configure-time | `'^cgb_speed_mutant_'` | `cgb_speed_mutant_anchor_guard` (duplicated anchor must stop generation); every pair has a mask-0 control | ⬜ pending |
| SC1 / D-03 | KEY1 `$7E`→`$7F`→`$FE`→`$7E` | 12-06 | white-box | `'^cgb_speed_key1_readback$'` | M10 (KEY1 bit 0 not cleared) | ⬜ pending |
| SC1 / D-03 | KEY0 writes never switch | 12-06 | white-box | `'^cgb_speed_key0_no_switch$'` | M32 (a KEY0 write toggles `double_speed`) | ⬜ pending |
| SC1 / D-10 | Cost, bus offsets and interrupt/halt literals scale by `cpu_ticks` | 12-03 | white-box | `'^cgb_speed_cpu_ticks$'` | M18 (three sites: cost, bus_read and bus_write offsets unscaled) | ⬜ pending |
| SC1 / D-10 | Timer, serial and OAM DMA run at 2× per scanline; remainders survive a switch | 12-05 | white-box | `'^cgb_speed_(timer\|serial\|dma)_scaling$'`, `'^cgb_speed_remainder_across_switch$'` | M2, M3, M11, M14, M15 | ⬜ pending |
| SC1 / D-11 | APU tap is bit 12 at normal speed and bit 13 at double; sequencer stays 512 Hz | 12-05 | white-box | `'^cgb_speed_apu_tap$'` | M4 | ⬜ pending |
| SC1 / D-10 | PPU, APU and RTC unscaled; structural scan | 12-05 | white-box + scan | `'^cgb_speed_ppu_apu_rtc_unscaled$'`, `'^cgb_speed_domains_scan'` | M1, M12, M17, `cgb_speed_domains_scan_mutated` | ⬜ pending |
| SC1 / D-22 | Original fixture probes with first-principles expectations | 12-10 | fixture + derivation | `'^cgb_speed_fixture_probes$'`, `'^cgb_speed_expectations_'` | tampered table; factor-3 derivation | ⬜ pending |
| SC2 / D-22 | Hostile entry points (selector byte) | 12-11 | fixture | `'^cgb_speed_fixture_hostile$'` | `cgb_speed_expectations_hostile_tampered`; selector 0/9 markers | ⬜ pending |
| D-22 | Fixture rebuilds byte-exactly | 12-13 | repro | `'^cgb_speed_repro_'` | tool-failure and missing-pin stubs | ⬜ pending |
| D-15, D-41 | Fixture audio and frame digests | 12-10 | core digest | `'^cgb_speed_fixture_(audio\|frame)_digest'` | M17 (APU 2×), M1 (PPU follows CPU) | ⬜ pending |
| SC1 / D-19, D-20, D-44 | AGE ROMs pinned by measurement; spsw-div passes | 12-09, 12-16 | third-party | `'^age_'` | `age_fixture_digest_tampered`, signature flip rule, `age-expected-failure-now-passes` | ⬜ pending |
| D-19 | AGE rebuild gate | 12-02, 12-16 | repro | `'^age_repro_'` | `age_repro_compare_tampered` (flipped ROM byte → `result=differs`), `age_repro_selfcheck_tampered` | ⬜ pending |
| D-37 | Committed-core spsw-div window re-measured before any constant-derived pin | 12-09 | third-party + mutant | `'^age_stall_window$'` | the window edges themselves (offsets lo-1 and hi+1 must fail) | ⬜ pending |
| D-21 | Stall sensitivity sweep recorded and enforced | 12-17 | third-party + mutant | `'^age_sensitivity_'` | recorded discriminating set must match | ⬜ pending |
| SC2 / D-37, D-06 | Stall = `GBB_SPEED_SWITCH_STALL_T` T at the destination speed in whole M-cycle steps | 12-01, 12-03, 12-07 | white-box + static assert | `'^cgb_speed_stall_length$'`, `'^cgb_speed_stall_static_assert_mutant$'` | M6, M21, M28, static-assert mutant | ⬜ pending |
| SC2 / D-07 | Devices advance during the stall | 12-07 | white-box | `'^cgb_speed_stall_devices_advance$'` | M7 | ⬜ pending |
| SC2 / D-06, D-13 | Never STOPPED/HALTED_IDLE; BUDGET semantics | 12-07 | white-box + API | `'^cgb_speed_never_stopped$'`, `'^cgb_speed_budget_semantics$'` | M5, M9 | ⬜ pending |
| SC2 / D-01, D-39 | DMG, compat and unarmed STOP byte-identical | 12-06 | existing + white-box | `'^cgb_stop_'`, `'^cgb_speed_dmg_unarmed_unchanged$'` | M8, M30 | ⬜ pending |
| SC2 / D-02, D-36 | Decision table cases 1–4 | 12-06 | white-box | `'^cgb_speed_stop_cases$'` | M19, M20, M27 | ⬜ pending |
| SC2 / D-04 | Operand independence | 12-06 | white-box | `'^cgb_speed_stop_operand$'` | M33 (operand $FF changes the switch) | ⬜ pending |
| SC2 / D-04 | STOP fetched from `$FF04` | 12-06 | white-box | `'^cgb_speed_stop_prefetch_ff04$'` | `cgb_speed_stop_prefetch_ff04_negative` (fetched byte not `$10` must fail) | ⬜ pending |
| SC2 / D-38 | Switch STOP costs 2 M at the executing speed | 12-06 | white-box | `'^cgb_speed_stop_cost$'` | M29 | ⬜ pending |
| SC2 / D-08, D-34 | Interrupt wake at M boundary, IME on and off | 12-07 | white-box | `'^cgb_speed_wake_'` | M13, M16 | ⬜ pending |
| SC2 / D-08 | `EI; STOP` retires EI before the stall | 12-07 | white-box | `'^cgb_speed_ei_stop$'` | M34 (EI delay undone before the stall) | ⬜ pending |
| SC2 / D-09 | Realignment into normal speed | 12-07 | white-box | `'^cgb_speed_realign$'` | M23 | ⬜ pending |
| SC2 / D-18 | Reset clears each new field | 12-03 | white-box | `'^cgb_speed_reset_'` | M24, M25, M26 | ⬜ pending |
| SC2 / D-28, D-40 | Headroom pre-check before mutation | 12-07 | white-box | `'^cgb_speed_headroom$'` | M22 | ⬜ pending |
| SC3 / D-26 | Partitioned run equals a single run; stall-end windows on the real constant both directions; pending IRQ / held-plus-pending at STOP | 12-14 | white-box | `'^cgb_partition_'` | joypad shift by one M (digest must change); inert-input check; M16; snapshot fidelity | ⬜ pending |
| SC3 / D-24 | Every expected-failure row names a `pinned_by` test of current behaviour that is in the inventory | 12-17 | CMake + Python | `'^cgb_speed_dispositions'`, `'^cgb_speed_xfail_'` | `cgb_speed_dispositions_mutated` (reason edited), `cgb_speed_dispositions_pinned_by_missing`; pin negatives (M7, M14, `--write-ff54`, `--poke-oam`) | ⬜ pending |
| SC3 / D-12 | No `research:12` remains; gate rows and tags agree | 12-08 | scanner | `'^model_gates'` | reverted row | ⬜ pending |
| D-27, D-43 | Fuzz `cgb_speed` mode invariants | 12-15 | fuzz regression | `'^cgb_fuzz_speed_'` | inverted oracle raises `contract_failures` | ⬜ pending |
| D-15, D-41 | Player smoke RGBA digest; claims text agrees | 12-12 | player e2e (macOS job) | `'^player_cgb_speed_smoke'`, `'^player_(limitations\|claims_agree)'` | wrong SHA; PPU-follows-CPU mutant; missing phrase | ⬜ pending |
| D-16, D-42 | Installed consumers run inline speed guest in partitions | 12-12 | installed | `'^installed_consumer_'` | unarmed twin guest must be rejected by the same checker | ⬜ pending |
| D-14 | No new public symbol | 12-12, 12-18 | existing | `'^cgb_consumer_symbol_coverage'` | existing selftest | ⬜ pending |
| D-17 | Docs agree with code and gates | 12-08, 12-09, 12-18 | doc contracts | `'^(cgb_speed_profile_contract\|cgb_adr_half_dot_contract\|cgb_native_guide_contract\|cgb_tables_io\|cgb_speed_docs_no_stale_claims)'` | missing-phrase selftests; stale-claim mutated copy | ⬜ pending |
| D-29, D-30, D-31 | ASan wall time recorded; bench advisory; SUMMARY coverage schema | 12-19 | recorded + CTest | `'^summary_coverage'`, `12-BENCH.md` | existing wrong-digest controls | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `cgb_speed_identity_pin` recorded from the unmodified core (D-45)
- [ ] `tests/test_cgb_speed_internal.c` and the `gbb_test_speed_state` seam
- [ ] Runtime-mask mutant generator `cmake/P12Mutants.cmake` (multi-site anchors, ≤6 builds, exactly-once anchors with a guard control)
- [ ] `fixtures/age/` (13 ROMs, rights, manifest), `reproduce-age.sh` and `test-reproduce-age.sh`; `tests/test_age.c`
- [ ] `fixtures/cgb-speed/` with `derive-cgb-speed-expectations.py` and `reproduce-cgb-speed.sh`
- [ ] `tests/external/cgb-speed-dispositions.json` and its verifier (with the `pinned_by` inventory check)
- [ ] `tests/fuzz/fuzz_core.dict`

---

## Manual-Only Verifications

All phase behaviors have automated verification (D-069). Hosted-only legs (Linux ASan and the macOS player job) are automated in CI, not manual.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
