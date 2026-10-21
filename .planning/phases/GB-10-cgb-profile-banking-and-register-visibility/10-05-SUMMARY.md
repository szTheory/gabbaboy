---
phase: 10-cgb-profile-banking-and-register-visibility
plan: 05
subsystem: core-api
tags: [cgb, public-api, probe, info, pgb, abi]
requires: ["10-04"]
provides:
  - "GBB_PROFILE_CGB_CPU_E = 2, GBB_UNSUPPORTED_EXECUTION_MODE, gbb_exec_mode, gbb_cgb_support, GBB_INFO_* flags, gbb_info (28 bytes), gbb_probe_rom, gbb_get_info appended to the public header"
  - "validate_header(profile, ...) with the D-03 PGB rejection as its last check (GATE-67, CGB_ONLY)"
  - "instance profile/exec_mode/header fields committed with the ROM swap; model_is_dmg/model_is_cgb helpers"
  - "tests/test_cgb_profile.c: 12 cgb_* cases with an independent oracle and a skewed-validator parity control"
affects: [10-06]
tech-stack:
  added: []
  patterns: ["sized out-struct with struct_size handshake", "probe and load share one validator", "parity loop with a deliberately skewed control"]
key-files:
  created:
    - tests/test_cgb_profile.c
  modified:
    - include/gabbaboy/gabbaboy.h
    - src/core/gabbaboy.c
    - src/runner/acceptance.h
    - docs/model-gates.md
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
key-decisions:
  - "gbb_create still returns GBB_UNSUPPORTED_PROFILE for the CGB profile; Plan 10-06 flips it"
  - "info_store writes field by field and sets struct_size to 28; the V1 floor check guarantees every field fits"
  - "The runner-local CGB constant now aliases GBB_PROFILE_CGB_CPU_E (it lives in src/runner/acceptance.h, not acceptance.c)"
requirements-completed: []
duration: 35 min
completed: 2026-10-12
status: complete
commits: 1
plan_head_before: a28205c4d5c9d410da63f810fc1fc0d7e56756a2
plan_head_after: 7492cbc1f11c86bbf631c220d84fd5e83ea8b187
actuals:
  tokens: 22000
  tasks: 3
  commits: 1
coverage:
  - id: D1
    description: "The profile and info API preserves its probe, lifecycle, argument, and sized-structure contract."
    requirement: CGB-01
    verification:
      - kind: integration
        ref: "ctest --test-dir build/phase15_1_13 -R '^(cgb_probe_tracer|cgb_info_no_rom|cgb_info_after_load|cgb_info_reset_constant|cgb_info_failed_load_unchanged|cgb_info_struct_size|cgb_profile_unknown|cgb_probe_args)$' --output-on-failure"
        status: pass
    human_judgment: false
  - id: D2
    description: "The $143 mapping and PGB rejection agree between probe and load, and a skewed-validator control is detected."
    requirement: CGB-01
    verification:
      - kind: integration
        ref: "ctest --test-dir build/phase15_1_13 -R '^(cgb_probe_matrix|cgb_probe_pgb|cgb_probe_parity)$' --output-on-failure"
        status: pass
    human_judgment: false
---

# Phase 10 Plan 05: CGB profile probe and info API Summary

Appended the CGB profile value, `gbb_probe_rom`/`gbb_get_info` with a `struct_size` handshake, and the PGB rejection (`GBB_UNSUPPORTED_EXECUTION_MODE`) on the CGB profile; `gbb_create` still rejects the CGB profile until Plan 10-06.

## Accomplishments

- Public header: every addition is appended (one profile value, one error code, two enums, five flag bits, `gbb_info` with `GBB_INFO_SIZE_V1` 28, two functions). The core static-asserts the struct size.
- `validate_header` takes the profile; the PGB check is last, after the MBC30 variant check, tagged `GATE-67 CGB_ONLY GUARD=GBB_PROFILE_CGB_CPU_E` with its doc row. Probe and load share this one function, so order and errors match by construction and by test.
- Instance carries profile, exec mode and header facts; the mode commits with the ROM swap after both allocations, so a failed load leaves `gbb_get_info` unchanged and `gbb_reset` never changes it.
- 12 CTest cases (`cgb_probe_tracer` ... `cgb_probe_args`) use an independent oracle typed from the loader matrix plus the D-03 PGB term, and literal `$143` support rows. `cgb_probe_parity` sweeps 23 types x 14 ROM codes x 8 RAM codes x 3 lengths x 2 checksums x 7 `$143` values on both profiles (probe vs load on DMG, probe vs oracle on CGB) and requires at least one mismatch from a skewed validator that checks PGB before the checksum.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Plan error] MBC3 $13 has no timer**
- **Found during:** Task 2 (`cgb_info_after_load` failed with flags 0x05, wanted 0x0D)
- **Issue:** The plan expected `HAS_RTC` for type `$13` (MBC3+RAM+BATTERY). Only `$0F` and `$10` carry the timer.
- **Fix:** The test now expects RTC for `$10` and `$0F`, and battery-without-RTC for `$13`. The core was right.
- **Files modified:** tests/test_cgb_profile.c
- **Commit:** 7492cbc

**2. [Rule 3 - Location] Runner CGB constant lives in acceptance.h**
- **Found during:** Task 1. The plan named acceptance.c; the `#define` is in src/runner/acceptance.h. Updated there.

**3. [Process] Tasks 1-3 committed as one commit**
- The three tasks share one header, one core change and one test file, so they were verified together and committed once (7492cbc) instead of three times.

**Total deviations:** 3 (1 plan-expectation fix, 1 location, 1 commit granularity). **Impact:** none on behaviour.

## Verification

- Full suite `ctest --preset phase1`: 442/442 passed (includes loader_*, model_gates*, cgb_runner_profile_*, installed_consumer_*).
- `bash tests/scripts/verify-dmg-baseline.sh`: `baseline status=pass`.
- Acceptance greps: `GBB_PROFILE_CGB_CPU_E = 2` present; 6 `GBB_INFO_*` defines; `static int model_is_cgb` present; `GBB_UNSUPPORTED_EXECUTION_MODE` appears 3 times in the header.
- `cgb_probe_parity` negative control: skewed validator produces mismatches, so the loop can fail.

## Known Stubs

None. `model_is_cgb` is used by load; no CGB-profile behaviour is claimed beyond probe, because `gbb_create` still rejects the profile.

## Threat Flags

None beyond the plan's threat model; T-10-06 (`struct_size`), T-10-07 (probe reuses the ceiling check, allocates nothing) and T-10-08 (mode commits with the swap) are covered by `cgb_info_struct_size`, `cgb_probe_parity` and `cgb_info_failed_load_unchanged`.

## Notes

- Requirement CGB-01 is not marked complete: Plans 10-06 and later still declare it.
- Ready for Plan 10-06 (flip `gbb_create` for the CGB profile; add load to the CGB side of the parity loop).

## Self-Check: PASSED
