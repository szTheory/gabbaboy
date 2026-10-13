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

## Per-Task Verification Map

Per-task rows are filled in by the planner and executors. The requirement-level contract they must cover:

| Req / Decision | Behaviour | Test Type | Automated Command (`-R`) | Negative control | Status |
|---|---|---|---|---|---|
| D-45 | Pre-change CGB single-speed identity pin recorded before any core edit | white-box pin | `'^cgb_speed_identity_pin$'` | flipped pinned digest | ⬜ pending |
| SC1 / D-03 | KEY1 `$7E`→`$7F`→`$FE`→`$7E`; KEY0 never switches | white-box | `'^cgb_speed_key1_'`, `'^cgb_speed_key0_no_switch$'` | M10 | ⬜ pending |
| SC1 / D-10 | Cost, bus offsets and interrupt/halt literals scale by `cpu_ticks` | white-box | `'^cgb_speed_cpu_ticks$'` | M15 | ⬜ pending |
| SC1 / D-10 | Timer, serial and OAM DMA run at 2× per scanline; remainders survive a switch | white-box | `'^cgb_speed_(timer\|serial\|dma)_scaling$'`, `'^cgb_speed_remainder_across_switch$'` | M2, M3, M11, M14 | ⬜ pending |
| SC1 / D-11 | APU tap is bit 12 at normal speed and bit 13 at double; sequencer stays 512 Hz | white-box | `'^cgb_speed_apu_tap$'` | M4 | ⬜ pending |
| SC1 / D-10 | PPU, APU and RTC unscaled; structural scan | white-box + scan | `'^cgb_speed_ppu_apu_rtc_unscaled$'`, `'^cgb_speed_domains_scan'` | M1, M12, scanner mutant | ⬜ pending |
| SC1 / D-22 | Original fixture probes with first-principles expectations | fixture + derivation | `'^cgb_speed_fixture_'`, `'^cgb_speed_expectations_'` | tampered table; factor-3 derivation | ⬜ pending |
| SC1 / D-19, D-20, D-44 | AGE `spsw-div` and `spsw-stop-prefetch` pass; others pinned | third-party | `'^age_'` | ROM digest tamper, signature edit, stall ±1 M mutant | ⬜ pending |
| SC2 / D-37, D-06 | Stall = `GBB_SPEED_SWITCH_STALL_T` in whole M-cycle steps (131076 / 262152 half-dots) | white-box + static assert | `'^cgb_speed_stall_length$'`, stall static-assert mutant | M6, M9 | ⬜ pending |
| SC2 / D-07 | Devices advance during the stall | white-box | `'^cgb_speed_stall_devices_advance$'` | M7 | ⬜ pending |
| SC2 / D-06, D-13 | Never STOPPED/HALTED_IDLE; BUDGET semantics | white-box + API | `'^cgb_speed_never_stopped$'`, `'^cgb_speed_budget_semantics$'` | M5 | ⬜ pending |
| SC2 / D-01, D-39 | DMG, compat and unarmed STOP byte-identical | existing + white-box | `'^cgb_stop_'`, `'^cgb_speed_dmg_unarmed_unchanged$'` | M8 | ⬜ pending |
| SC2 / D-02, D-04, D-36, D-38 | Decision table cases 1–4, operand independence, switch cost | white-box | `'^cgb_speed_stop_(cases\|operand\|cost)$'` | per-case predicate mutants | ⬜ pending |
| SC2 / D-08, D-34 | Interrupt wake at M boundary, IME on and off, `EI; STOP` | white-box | `'^cgb_speed_wake_'`, `'^cgb_speed_ei_stop$'` | M13, M16 | ⬜ pending |
| SC2 / D-09 | Realignment into normal speed | white-box | `'^cgb_speed_realign$'` | realign dropped | ⬜ pending |
| SC2 / D-18 | Reset clears each new field | white-box | `'^cgb_speed_reset_'` | field omitted from reset | ⬜ pending |
| SC2 / D-28, D-40 | Headroom pre-check before mutation | white-box | `'^cgb_speed_headroom$'` | pre-check dropped | ⬜ pending |
| SC3 / D-26 | Partitioned run equals a single run across switch and stall | white-box | `'^cgb_partition_'` | joypad shift by one M (digest must change); M16 | ⬜ pending |
| SC3 / D-24 | Dispositions pinned with flip rule | CMake + Python | `'^cgb_speed_dispositions'` | edited reason in copy | ⬜ pending |
| SC3 / D-12 | No `research:12` remains; gate rows and tags agree | scanner | `'^model_gates'` | reverted row | ⬜ pending |
| D-25 | M1–M16 each fail their case; mask 0 passes | configure-time | `'^cgb_speed_mutant_'` | built in | ⬜ pending |
| D-27, D-43 | Fuzz `cgb_speed` mode invariants | fuzz regression | `'^cgb_fuzz_speed_'` | inverted oracle raises `contract_failures` | ⬜ pending |
| D-15, D-41 | Player smoke RGBA digest; claims text agrees | player e2e (macOS job) | `'^player_cgb_speed_smoke'`, `'^player_(limitations\|claims_agree)'` | wrong SHA; PPU-follows-CPU mutant; missing phrase | ⬜ pending |
| D-16, D-42 | Installed consumers run inline speed guest in partitions | installed | `'^installed_consumer_'` | existing selftests | ⬜ pending |
| D-14 | No new public symbol | existing | `'^cgb_consumer_symbol_coverage'` | existing selftest | ⬜ pending |
| D-17 | Docs agree with code and gates | doc contracts | `'^(cgb_adr_half_dot_contract\|cgb_native_guide_contract\|cgb_tables_io)'` | missing-phrase selftests | ⬜ pending |
| D-29, D-30, D-31 | ASan wall time recorded; bench advisory; SUMMARY coverage schema | recorded + CTest | `'^summary_coverage'`, `12-BENCH.md` | existing wrong-digest controls | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `cgb_speed_identity_pin` recorded from the unmodified core (D-45)
- [ ] `tests/test_cgb_speed_internal.c` and the `gbb_test_speed_state` seam
- [ ] Runtime-mask mutant generator in `tests/CMakeLists.txt` (≤6 builds, exactly-once anchors)
- [ ] `fixtures/age/` (13 ROMs, rights, manifest) and `reproduce-age.sh`; `tests/test_age.c`
- [ ] `fixtures/cgb-speed/` with `derive-cgb-speed-expectations.py` and `reproduce-cgb-speed.sh`
- [ ] `tests/external/cgb-speed-dispositions.json` and its verifier
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
