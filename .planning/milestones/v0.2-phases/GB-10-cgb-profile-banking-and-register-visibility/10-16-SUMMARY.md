---
phase: 10-cgb-profile-banking-and-register-visibility
plan: 16
subsystem: runner-fixtures-tests
tags: [cgb, mooneye, runner, expected-unsupported, pc-table, div-sweep, tamper-control]
requires:
  - phase: 10-cgb-profile-banking-and-register-visibility
    provides: "10-14 Mooneye CGB derivative ROMs and manifest; 10-15 digest/inventory verifier; 10-06 compat post-boot row"
provides:
  - "src/runner/main.c third Mooneye suite: per-row profile, expect_stop, expect_stop_address; expected-unsupported and unexpected-pass statuses"
  - "cmake/VerifyMooneyeCgb.cmake pc-table mode tying cgb_cases[] to the manifest and its raw SHA"
  - "tests/test_mooneye_cgb_div_sweep.c real-ROM DIV phase sweep (A1)"
  - "12 new CTest names, all cgb_-prefixed"
affects: [18, 19, 20, 14]
actuals:
  tokens: 9800
  tasks: 3
  commits: 3
tech-stack:
  added: []
  patterns:
    - "Trailing struct columns keep legacy positional initialisers valid"
    - "Expectation tamper controls load the row expectation from a configure-time manifest copy inside a test_runner case, so the raw-SHA gate cannot mask the check"
key-files:
  created: [tests/test_mooneye_cgb_div_sweep.c]
  modified: [src/runner/main.c, fixtures/mooneye-cgb/manifest.json, fixtures/mooneye-cgb/ELIGIBILITY.md, cmake/VerifyMooneyeCgb.cmake, tests/scripts/reproduce-mooneye-cgb.sh, tests/test_runner.c, tests/CMakeLists.txt, tests/expected-tests.txt]
key-decisions:
  - "The refused address of an expected-unsupported stop is read through the core's existing private seam gbb_test_last_unsupported_address, because the public run result carries no address and a refused pre-flight read stops before its instruction is traced"
  - "Assert-style ROMs use pass_cb == fail_cb == 0x4000 (check_asserts_cb); boot_regs-cgb also lists the invalid_sp inline quit site 0x01da as a fail callback"
  - "An explicit --profile that differs from a suite's profile excludes the whole suite (exit 4); the row, not the command line, otherwise chooses the run profile"
requirements-completed: []
status: complete
commits: 3
plan_head_before: b2cee89cbe1dded7d3081d1a9a6a13ad031dfbd4
plan_head_after: 63bb82b4cdf36fd5426ee888d8aeeb3ba1fe871f
duration: 40 min
completed: 2026-10-12
coverage:
  - id: D1
    description: "The qualified CGB corpus reports boot_regs_cgb and boot_div_cgbABCDE as passing CGB-CPU-E cases"
    requirement: CGB-01
    human_judgment: false
    verification:
      - kind: unit
        ref: "CTest cgb_corpus_mooneye_boot_regs_cgb"
        status: pass
      - kind: unit
        ref: "CTest cgb_corpus_mooneye_boot_div_cgbABCDE"
        status: pass
  - id: D2
    description: "The current qualified corpus retains boot_hwio_C and unused_hwio_C as exact expected-failure rows, separate from Phase 10 expected-unsupported results"
    requirement: CGB-02
    human_judgment: false
    verification:
      - kind: unit
        ref: "CTest cgb_corpus_mooneye_boot_hwio_C and cgb_corpus_mooneye_unused_hwio_C"
        status: pass
      - kind: unit
        ref: "CTest cgb_mooneye_required_suite"
        status: pass
  - id: D3
    description: "Current corpus controls reject unknown manifests, digest, inventory and PC-table tampering"
    human_judgment: false
    verification:
      - kind: unit
        ref: "CTest cgb_mooneye_unknown_manifest, cgb_mooneye_digest_tamper, cgb_mooneye_inventory_tamper, and cgb_mooneye_pc_table_tamper"
        status: pass
      - kind: unit
        ref: "CTest cgb_corpus_mooneye_controls"
        status: pass
  - id: D4
    description: "CGB Mooneye observation remains not-applicable and the frozen DMG baseline has no changed rows"
    human_judgment: false
    verification:
      - kind: unit
        ref: "CTest cgb_mooneye_observe_not_applicable"
        status: pass
      - kind: other
        ref: "bash tests/scripts/verify-dmg-baseline.sh"
        status: pass
  - id: D5
    description: "The real CGB boot_div ROM keeps the exact divider window in both phases, and a shifted window is rejected"
    requirement: CGB-01
    human_judgment: false
    verification:
      - kind: unit
        ref: "CTest cgb_postboot_div_real_rom_sweep"
        status: pass
      - kind: unit
        ref: "CTest cgb_postboot_div_real_rom_sweep_shifted"
        status: pass
---

# Phase 10 Plan 16: Mooneye CGB Runner Suite and Real-ROM DIV Sweep Summary

The runner now runs the four Mooneye CGB derivatives as a third SHA-gated suite with per-row profiles and an honest `expected-unsupported` status, and the real `boot_div-cgbABCDE` ROM independently confirms the frozen compat DIV cell 0x2678.

## Accomplishments

- **Third suite (D-26).** `fixture_case` gained trailing `profile`, `expect_stop`, `expect_stop_address` columns, so every DMG and mbc row is byte-for-byte unchanged. `MOONEYE_CGB_MANIFEST_SHA256` gates the raw manifest bytes; `cgb_cases[]` sits between `gbb:cgb-rows-begin` and `gbb:cgb-rows-end`. The suite category printing was generalised (`suite_def.categories`), with identical DMG and mbc output.
- **Statuses.** `boot_regs-cgb` and `boot_div-cgbABCDE` report `status=pass profile=CGB-CPU-E` (callback 0x4000, result 0x4327, about 34.7k half-dots). `boot_hwio-C` and `unused_hwio-C` report `status=expected-unsupported stop=unsupported-bus address=ff76` and exit 0 only on that exact stop; a pass is `unexpected-pass` (exit 1) and any other stop is `fail` (exit 1). The suite prints `suite eligible=4 executed=4 status=pass`, a per-category line and `suite expected-unsupported=2/2`.
- **pc-table verifier.** `VerifyMooneyeCgb.cmake` pc-table mode pins each compiled row to the manifest (ids, digests, PCs, budget, size, fail list, profile and expectation) and finally checks the define equals the manifest's SHA-256. Manifest rows gained `result_pc`, `pass_callback_pc`, `fail_callback_pcs`, `budget_half_dots` from the linker `.sym` of a byte-identical rebuild (all four built ROMs `cmp`-equal the committed ROMs); `ELIGIBILITY.md` carries the PC table and `reproduce-mooneye-cgb.sh --facts` now prints the shared assert callback.
- **A1 resolved on the real ROM.** `test_mooneye_cgb_div_sweep` sweeps divider_counter 0x2670..0x2680 x both phases on `boot_div-cgbABCDE.gb`: the passing set is exactly 0x2678..0x267B (mask 0xF00 in both phases). It agrees with 10-06's synthetic guest; no table change is needed. The default compat instance also passes, and every start must reach its verdict, so a hang cannot read as "not passing".

## Verification

- `ctest --preset phase1`: 524 of 524 passed (181.8 s); the previous baseline was 512, plus these 12 new names. `bash tests/scripts/verify-dmg-baseline.sh`: `baseline status=pass`. Model-gate and install-scan tests are in the suite and pass.
- Negative controls (each verified to fail for the named reason): `cgb_mooneye_unknown_manifest` (one appended byte, exit 2 `invalid-manifest`); `cgb_mooneye_pc_table_tamper` (result_pc 0x4328, exit 1 `pc-table-mismatch: mooneye-misc-boot-regs-cgb result_pc`); `cgb_mooneye_expected_unsupported_tamper` (manifest says boot_hwio-C passes -> status `unsupported`, code 3; wrong address 0xFF77 -> `fail wrong-stop-address`; boot_regs-cgb declared expected-unsupported -> `unexpected-pass`); `cgb_postboot_div_real_rom_sweep_shifted` (window asserted at 0x2679 -> exit 1 with the observed mask).
- Acceptance greps: `gbb:cgb-rows-begin` = 1; `MOONEYE_CGB_MANIFEST_SHA256` = 2; Task 1 names = 2; Task 2 names = 8; `expected-unsupported` in main.c = 7; sweep name = 1.

## Deviations from Plan

**1. [Rule 3 - Blocking] Refused address via the core's private test seam.** The plan says to read the faulting address from the last recorded bus access or from the instruction operand. For boot_hwio-C the stop is a refused pre-flight read, which happens before the instruction is traced, and the public API exposes no register state or address, so neither source exists in the runner. The runner declares and calls the existing read-only seam `gbb_test_last_unsupported_address` (the same seam tests already use). No core file changed. Commit 2d8ae33.

**2. [Rule 3 - Blocking] Sweep test takes the result PC as a third argument.** The plan passes only the callback PC. The Mooneye assert ROMs run their callback (0x4000) before setting the Fibonacci registers at the `LD B,B` (0x4327), so the pass registers exist only at the result PC (the runner's own predicate). The test takes both PCs. Commit 63bb82b.

**3. [Rule 2 - Missing coverage] Extra negative controls.** Added `cgb_postboot_div_real_rom_sweep_shifted` and two further sub-controls (wrong address, passing ROM) inside `cgb_mooneye_expected_unsupported_tamper`, per D-069. They are in `tests/expected-tests.txt`.

**4. Tracer slice.** The tracer commit already carried all four rows in `cgb_cases[]` because `pc-table` requires the compiled rows to equal the four-row manifest; the expected-unsupported evaluation arrived with Task 2, and the staged rows were not registered as tests before then.

**Total deviations:** 4 (2 Rule 3, 1 Rule 2, 1 note). **Impact:** none on scope; hardware evidence unchanged.

## Known Stubs

None.

## Threat Flags

None. T-10-23 mitigations are implemented: raw manifest SHA gate, per-ROM digest check, pc-table verifier with tamper control, expected-unsupported tamper control.

## Next

Ready for 10-17 (CGB-03) per the phase plan order; phase-level stop rules in AGENTS.md apply after the last plan.

## Self-Check: PASSED

Files exist (`tests/test_mooneye_cgb_div_sweep.c`, `fixtures/mooneye-cgb/manifest.json`, `cmake/VerifyMooneyeCgb.cmake`); commits f4c60ce, 2d8ae33, 63bb82b are ancestors of HEAD; all task acceptance criteria and the full suite re-ran green after the last code change.

## 15.1-19 Fresh Applicability Evidence

The Phase 10 verification and producer record above is preserved as historical evidence. Phase 14 commit `c771b1b` replaced the older four-case Mooneye CTest naming with the inventory-bound CGB corpus. In the current model, `boot_hwio-C` and `unused_hwio-C` remain expected-failure (`xfail`) dispositions; this does not rewrite the Phase 10 expected-unsupported results as current guest passes.

On 2026-10-21, the focused current corpus, suite, negative controls, observation check, and real-ROM DIV checks passed 13/13:

```text
ctest --test-dir build --output-on-failure -R '^(cgb_corpus_mooneye_(boot_regs_cgb|boot_div_cgbABCDE|boot_hwio_C|unused_hwio_C|controls)|cgb_mooneye_(required_suite|observe_not_applicable|unknown_manifest|pc_table_tamper|digest_tamper|inventory_tamper)|cgb_postboot_div_real_rom_sweep(_shifted)?)$'
```

The passing suite includes the explicit expected-failure corpus rows, unknown-manifest and digest/inventory/PC-table rejection, observation-not-applicable behavior, the exact real-ROM DIV window, and its shifted-window negative control. `bash tests/scripts/verify-dmg-baseline.sh` also passed with zero changed rows. These checks establish current applicability for the normalized mappings; the earlier Phase 10 run details remain the original historical record.
