---
phase: "10"
slug: "cgb-profile-banking-and-register-visibility"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
status: validated
nyquist_compliant: true
wave_0_complete: true
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
| **Estimated runtime** | ~120 seconds (full suite, local) — measured 186 s on the audit host at load average 8 to 9 (see Audit Findings) |

---

## Sampling Rate

- **After every task commit:** the narrow `ctest -R` for the touched area; plus `bash tests/scripts/verify-dmg-baseline.sh` after any task that edits `src/core/gabbaboy.c`
- **After every plan wave:** full suite on `phase1`, then `phase1-asan` for core-touching waves (Linux hosts only; see Audit Findings)
- **Before `/gsd-verify-work`:** full suite green on every required CI leg at the exact PR head; baseline `status=pass`; fixture repro `result=byte-identical`
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Req / Decision | Behavior | Test Type | Automated Command | Negative control | Status |
|----------------|----------|-----------|-------------------|------------------|--------|
| CGB-01 / D-01 | create CGB; unknown profiles rejected | unit | `ctest -R '^cgb_profile_'` | profile 3 must fail (`profile_unknown` checks 0, 3, 255) | ✅ green |
| CGB-01 / D-02..D-04 | probe/get_info matrix, struct_size handshake, error parity | unit | `ctest -R '^cgb_(probe\|info)_'` | skewed probe, shrunk struct | ✅ green |
| CGB-01 / D-03 | PGB rejected on CGB only | unit | `ctest -R '^cgb_probe_pgb'` | same ROM loads on DMG | ✅ green |
| CGB-01 / D-05 | copy_frame unsupported on CGB | unit | `ctest -R '^cgb_copy_frame'` | DMG call succeeds (same test, DMG leg) | ✅ green |
| CGB-01 / D-06 | C tables == docs mirror, provenance rules | unit + CMake | `ctest -R '^cgb_tables'` | mutated doc / table / reasonless POLICY | ✅ green |
| CGB-01 / D-06, D-19 | DMG column equals pre-refactor literals | unit + baseline | `ctest -R '^cgb_postboot_dmg_pin'` + `verify-dmg-baseline.sh` | flipped literal | ✅ green |
| CGB-01 / D-07 | compat/CGB CPU rows, DIV phase | unit | `ctest -R '^cgb_postboot_'` | real-ROM DIV window shifted to `0x2679` fails (`cgb_postboot_div_real_rom_sweep_shifted`); exact passing set `0x2678..0x267B` asserted | ✅ green (control corrected in audit) |
| CGB-01 / D-25 | runner `--profile`, DMG output unchanged | runner | `ctest -R '^cgb_runner_profile_'` + `verify-dmg-baseline.sh` | CGB grep for `dmg-cpu-b` empty; `cgb_runner_profile_dmg_identity_negative` | ✅ green (command corrected in audit) |
| CGB-02 / D-08 | model-gate scanner R1-R5 | script | `ctest -R '^model_gates'` | 18 self-test mutants plus real-file deleted-tag, untagged-function and doc-mismatch controls | ✅ green |
| CGB-02 / D-09..D-11 | visibility matrix per cell, DEFERRED stops | unit | `ctest -R '^cgb_visibility_'` | flipped byte; wrong column | ✅ green |
| CGB-02 / D-12 | KEY0 locked | unit | `ctest -R '^cgb_key0_lock'` | VBK probe compat vs CGB | ✅ green |
| CGB-02 / D-23 | STOP with KEY1 armed unsupported on CGB | unit | `ctest -R '^cgb_stop_'` | DMG stops with STOPPED | ✅ green |
| CGB-03 / D-13..D-15 | DMG flat reference; CGB banking diverges | white-box | `ctest -R '^banking_'` | echo-ignores-bank / DMA wrong-bank mutants | ✅ green |
| CGB-03 / D-18 | original banking fixture | fixture | `ctest -R '^cgb_banking_'` + `reproduce-cgb-banking.sh` | patched expected -> `$EE` | ✅ green (rebuild verified with pinned RGBDS v1.0.1) |
| D-20/D-21 | ADR static asserts + doc tie | compile + CMake | `ctest -R '^cgb_adr_half_dot'` | doc missing symbol | ✅ green |
| D-22 | A/B bench receipt + digest | script | `ctest -R '^cgb_bench_ab'` | wrong digest, missing field | ✅ green |
| D-26 | Mooneye CGB admissions | runner/verifier | `ctest -R '^cgb_mooneye_'` + `reproduce-mooneye-cgb.sh --compare` | tampered digest; expected-unsupported that passes | ✅ green (hosted `mooneye-cgb-repro` also green) |
| D-27 | fuzz/consumers both profiles | fuzz/unit | `ctest -R '^(loader_\|battery_api_fuzz\|fuzz_core_regressions\|installed_consumer\|cgb_fuzz_\|cgb_loader_fuzz_)'` | skewed probe (`cgb_loader_fuzz_parity`); profile-selection mutant (`cgb_fuzz_profile_select`, added in audit). ASan leg hosted-only | ✅ green (+ `cgb_fuzz_profile_select`) |
| D-28 | docs contract | CMake | `ctest -R '^cgb_native_guide_contract'` | missing phrase selftest | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_cgb_tables.c`, `tests/test_cgb_visibility.c`, `tests/test_cgb_profile.c`, `tests/test_banking.c`, `tests/test_banking_internal.c`
- [x] `tests/scripts/verify-model-gates.py` with `--self-test` mutants
- [x] `docs/cgb-profile.md` and `docs/model-gates.md` with table markers
- [x] `fixtures/cgb-banking/` and `fixtures/mooneye-cgb/`
- [x] Bench A/B mode and CTest self-test
- [x] New test names appended to `tests/expected-tests.txt` (including `cgb_fuzz_profile_select`, added in audit)

---

## Manual-Only Verifications

None. All phase behaviors have automated verification. Owner veto items (CONTEXT § veto window) are decisions, not verification steps. Hosted CI legs (`linux-asan-ubsan`, `mooneye-cgb-repro`, `fixture-repro`) are automated checks, recorded as hosted evidence in `10-20-SUMMARY.md`.

---

## Audit Findings (Nyquist audit, 2026-10-12)

Gaps found: 4. Resolved: 4. Escalated: 0. No implementation bug was found; `src/` and `include/` were not modified.

| # | Finding | Class | Resolution |
|---|---------|-------|------------|
| 1 | D-25 command `^runner_(profile\|model)` matched 0 tests (ctest exit 8 under `--no-tests=error`) | map gap | Command corrected to `^cgb_runner_profile_` (7/7 green) |
| 2 | D-07 negative control cited a `counter 0x2677` mutant that exists in no test | map gap | Control corrected to `cgb_postboot_div_real_rom_sweep_shifted` (verified in the full suite) |
| 3 | D-27 `cgb_fuzz_io_regressions` asserted only a 0 return, so an always-DMG selection regression would pass | test gap | Added `cgb_fuzz_profile_select` (bit 7 must select the profile; DMG twins must differ). Mutant forcing DMG fails with `selected profile cgb=0, expected 1`; restored file passes |
| 4 | `reproduce-cgb-banking.sh` refused the host's Homebrew RGBDS v1.0.4 (pinned v1.0.1) | environment | Fetched the pinned upstream v1.0.1 macOS archive (sha256 `2f6f13c6…503645`, matches manifest) into a scratch directory; rebuild printed `result=byte-identical roms=2` |

Warnings (passing with caveats):
- **W1 hosted-only sanitizer leg.** `phase1-asan` cannot configure on macOS (`GABBABOY_ENABLE_SANITIZERS is supported only on Linux`). The sanitizer evidence is the hosted `linux-asan-ubsan` job at the PR #66 exact head (see `10-20-SUMMARY.md`), not a local run.
- **W2 feedback latency.** Full suite measured 186 s real time at host load average 8 to 9, above the 120 s target. The per-area quick commands stay inside budget (for example `^cgb_runner_profile_` 8.6 s). Latency is a host-load effect, not a failure.
- **W3 mooneye and banking reproduction host.** Both reproduction scripts pass locally, but only with the pinned toolchain (RGBDS v1.0.1 for banking; WLA-DX built from its pin for Mooneye). A host with other tool versions will refuse, by design.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [ ] Feedback latency < 120s — full suite 186 s on a loaded host (W2); per-area commands within budget
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** automated validation complete (Nyquist audit, 538/538 CTest green on the local `phase1` preset after the audit changes). Owner sign-off remains with `/gsd-verify-work 10`.

## Validation Audit 2026-10-12

| Metric | Count |
|---|---|
| Gaps found | 4 |
| Resolved | 4 |
| Escalated | 0 |
