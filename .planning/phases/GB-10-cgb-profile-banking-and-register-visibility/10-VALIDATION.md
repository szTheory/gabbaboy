---
phase: "10"
slug: "cgb-profile-banking-and-register-visibility"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-12"
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution. Source: `10-RESEARCH.md` § Validation Architecture. Every deliverable has an automated check with a negative control (D-069); no manual UAT.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | CTest over C executables (`REQUIRE` macros); CMake `-P` verifiers; stdlib Python verifiers run as `python3 -I` with `--self-test` |
| **Config file** | `CMakePresets.json` (presets `phase1`, `phase1-asan`, `cmake-3.25.3`) |
| **Quick run command** | `ctest --preset phase1 -R '^(cgb_\|banking_\|model_gates)' --output-on-failure --no-tests=error` |
| **Full suite command** | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error && bash tests/scripts/verify-dmg-baseline.sh` |
| **Estimated runtime** | ~120 seconds (full suite, local) |

---

## Sampling Rate

- **After every task commit:** the narrow `ctest -R` for the touched area; plus `bash tests/scripts/verify-dmg-baseline.sh` after any task that edits `src/core/gabbaboy.c`
- **After every plan wave:** full suite on `phase1`, then `phase1-asan` for core-touching waves
- **Before `/gsd-verify-work`:** full suite green on every required CI leg at the exact PR head; baseline `status=pass`; fixture repro `result=byte-identical`
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Req / Decision | Behavior | Test Type | Automated Command | Negative control | Status |
|----------------|----------|-----------|-------------------|------------------|--------|
| CGB-01 / D-01 | create CGB; unknown profiles rejected | unit | `ctest -R '^cgb_profile_'` | profile 3 must fail | ⬜ pending |
| CGB-01 / D-02..D-04 | probe/get_info matrix, struct_size handshake, error parity | unit | `ctest -R '^cgb_(probe\|info)_'` | skewed probe, shrunk struct | ⬜ pending |
| CGB-01 / D-03 | PGB rejected on CGB only | unit | `ctest -R '^cgb_probe_pgb'` | same ROM loads on DMG | ⬜ pending |
| CGB-01 / D-05 | copy_frame unsupported on CGB | unit | `ctest -R '^cgb_copy_frame'` | DMG call succeeds | ⬜ pending |
| CGB-01 / D-06 | C tables == docs mirror, provenance rules | unit + CMake | `ctest -R '^cgb_tables'` | mutated doc / table / reasonless POLICY | ⬜ pending |
| CGB-01 / D-06, D-19 | DMG column equals pre-refactor literals | unit + baseline | `ctest -R '^cgb_postboot_dmg_pin'` + `verify-dmg-baseline.sh` | flipped literal | ⬜ pending |
| CGB-01 / D-07 | compat/CGB CPU rows, DIV phase | unit | `ctest -R '^cgb_postboot_'` | counter 0x2677 fails DIV guest | ⬜ pending |
| CGB-02 / D-08 | model-gate scanner R1-R5 | script | `ctest -R '^model_gates'` | 5 mutants | ⬜ pending |
| CGB-02 / D-09..D-11 | visibility matrix per cell, DEFERRED stops | unit | `ctest -R '^cgb_visibility_'` | flipped byte; wrong column | ⬜ pending |
| CGB-02 / D-12 | KEY0 locked | unit | `ctest -R '^cgb_key0_lock'` | VBK probe compat vs CGB | ⬜ pending |
| CGB-02 / D-23 | STOP with KEY1 armed unsupported on CGB | unit | `ctest -R '^cgb_stop_'` | DMG stops with STOPPED | ⬜ pending |
| CGB-03 / D-13..D-15 | DMG flat reference; CGB banking diverges | white-box | `ctest -R '^banking_'` | echo-ignores-bank / DMA wrong-bank mutants | ⬜ pending |
| CGB-03 / D-18 | original banking fixture | fixture | `ctest -R '^cgb_banking_'` | patched expected -> `$EE` | ⬜ pending |
| D-20/D-21 | ADR static asserts + doc tie | compile + CMake | `ctest -R '^cgb_adr_half_dot'` | doc missing symbol | ⬜ pending |
| D-22 | A/B bench receipt + digest | script | `ctest -R '^cgb_bench_ab'` | wrong digest, missing field | ⬜ pending |
| D-25 | runner `--profile`, DMG output unchanged | runner | `ctest -R '^runner_(profile\|model)'` + baseline | CGB grep for `dmg-cpu-b` empty | ⬜ pending |
| D-26 | Mooneye CGB admissions | runner/verifier | `ctest -R '^cgb_mooneye_'` | tampered digest; expected-unsupported that passes | ⬜ pending |
| D-27 | fuzz/consumers both profiles | fuzz/unit | `ctest -R '^(loader_\|battery_api_fuzz\|fuzz_core_regressions\|installed_consumer)'` + ASan | skewed probe | ⬜ pending |
| D-28 | docs contract | CMake | `ctest -R '^cgb_native_guide_contract'` | missing phrase selftest | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_cgb_tables.c`, `tests/test_cgb_visibility.c`, `tests/test_cgb_profile.c`, `tests/test_banking.c`, `tests/test_banking_internal.c`
- [ ] `tests/scripts/verify-model-gates.py` with `--self-test` mutants
- [ ] `docs/cgb-profile.md` and `docs/model-gates.md` with table markers
- [ ] `fixtures/cgb-banking/` and `fixtures/mooneye-cgb/`
- [ ] Bench A/B mode and CTest self-test
- [ ] New test names appended to `tests/expected-tests.txt`

---

## Manual-Only Verifications

All phase behaviors have automated verification. Owner veto items (CONTEXT § veto window) are decisions, not verification steps.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
