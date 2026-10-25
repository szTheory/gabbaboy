---
phase: 10-cgb-profile-banking-and-register-visibility
plan: 18
subsystem: test-coverage
tags: [fuzz, loader, consumers, isolation, d-27, d-19, cgb]
requires:
  - phase: 10-cgb-profile-banking-and-register-visibility
    provides: "10-17 benchmark; CGB profile, probe/info API, bank-state seam from earlier plans"
provides:
  - "tests/fuzz_core.c selects the profile from data[0] bit 7 and runs a CGB guest I/O path with bank invariants"
  - "CTest cgb_fuzz_io_regressions, cgb_loader_matrix, cgb_loader_fuzz_parity, cgb_instance_isolation"
  - "cgb_api_smoke in the installed C and C++ consumers"
affects: [19, 20]
actuals:
  tokens: 8200
  tasks: 3
  commits: 3
key-files:
  created: []
  modified:
    - tests/fuzz_core.c
    - tests/test_fuzz_core.c
    - tests/test_loader_matrix.c
    - tests/test_loader_fuzz.c
    - tests/test_instance_concurrency.c
    - tests/consumers/c/main.c
    - tests/consumers/cpp/main.cpp
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
key-decisions:
  - "Fuzz profile bit is data[0] bit 7; the original 0xFF minimized reproducer therefore now runs on the CGB profile, and a bit-7-clear twin (0x7F) keeps the same decoder path on the DMG profile"
  - "CGB guest I/O operations use three input bytes (selector, value, address) instead of two so the written value and the target address are independent"
requirements-completed: []
status: complete
commits: 3
plan_head_before: d1c5e5c7ca4fbe7f88306331d4c7f53714292345
plan_head_after: d69645bcfbaecd0a99f5de29214fa3bad272161b
duration: 45 min
completed: 2026-10-12
coverage:
  - id: D1
    description: "CGB-profile fuzz path: random LDH reads/writes over FF00-FF7F plus VBK/SVBK end in budget, idle or unsupported-bus stops, bank state stays bounded; DMG banks stay 0/1"
    human_judgment: false
    verification:
      - kind: integration
        ref: "CTest cgb_fuzz_io_regressions"
        status: pass
      - kind: integration
        ref: "CTest fuzz_core_regressions"
        status: pass
  - id: D2
    description: "Header cases x both profiles through the loader matrix, with a skewed oracle that must be detected"
    human_judgment: false
    verification:
      - kind: integration
        ref: "CTest cgb_loader_matrix"
        status: pass
  - id: D3
    description: "Probe/load parity over a deterministic fuzz corpus on both profiles, with a skewed probe that must be detected"
    human_judgment: false
    verification:
      - kind: integration
        ref: "CTest cgb_loader_fuzz_parity"
        status: pass
  - id: D4
    description: "DMG trace digest unchanged beside a CGB instance, interleaved and on two threads"
    human_judgment: false
    verification:
      - kind: integration
        ref: "CTest cgb_instance_isolation"
        status: pass
  - id: D5
    description: "Installed C and C++ consumers exercise every new public symbol"
    human_judgment: false
    verification:
      - kind: integration
        ref: "build/consumer-c/consumer-c fixtures/tracer/tracer.gb"
        status: pass
      - kind: integration
        ref: "build/consumer-cpp/consumer-cpp fixtures/tracer/tracer.gb"
        status: pass
---

# Phase 10 Plan 18: CGB fuzz, loader, consumer and isolation coverage Summary

Profile-parameterised fuzz entry with a CGB guest I/O path and bank-state invariants, loader matrix and probe/load parity over both profiles with detected skew controls, a DMG-versus-CGB instance isolation digest test, and CGB smoke in the installed C and C++ consumers.

## Accomplishments

- `tests/fuzz_core.c`: `data[0]` bit 7 picks the profile (clear = DMG-CPU-B, existing behaviour), bit 6 with bit 7 routes to `fuzz_cgb_io`, which builds a ROM of up to 64 guest operations (`LD A,n; LDH (a),A` or `LDH A,(a)` over FF00-FF7F, with a selector that redirects to FF4F/FF70) followed by HALT, runs under the frozen `FUZZ_RUN_LIMIT`, and requires a budget, halted-idle or unsupported-bus stop. `require_banks` asserts DMG (0, 1) and CGB (vram <= 1, wram 1..7) after stateful steps, after the synthesised-length path and at the end of every input. `GBB_UNSUPPORTED_EXECUTION_MODE` is allowed in the synthesised-length result set on the CGB profile only (a fuzzed `$143` is applied there). All `FUZZ_` literals and the names `loader_boundary_fuzz`, `battery_api_fuzz`, `fuzz_core_regressions` are unchanged; `run-bounded-fuzz.sh --self-test` passes.
- `cgb_fuzz_io_regressions` runs `test_fuzz_core cgb` with seeds that write SVBK 0 then 6, VBK 1, a wide LCDC/DMA/boot/KEY1/HDMA sweep, PGB and `$C0` headers on the CGB profile, plus a seam control that proves a guest writing VBK=1 and SVBK=5 is visible through `gbb_test_bank_state`.
- `cgb_loader_matrix` (35280 cases): matrix x `$143` in {00, 80, C0, 81, 84, 88, FF} x both profiles, `gbb_load_rom` and `gbb_probe_rom` against the independent `expected_result` oracle plus the D-03 PGB term, with mode and `GBB_INFO_CGB_ONLY_ON_DMG` literals on acceptance. The same sweep against an oracle that applies the PGB term on DMG too must report at least one mismatch.
- `cgb_loader_fuzz_parity` (8000 probe/load pairs from a fixed-seed xorshift corpus); a probe wrapper that answers OK for any PGB `$143` must be detected.
- `cgb_instance_isolation`: DMG tracer digest (FNV-1a over trace fields, 64 slices) is identical alone, interleaved on one thread with a CGB instance hammering VBK/SVBK, and with the CGB instance on a second thread; the control asserts the CGB neighbour changed its own banks, the DMG instance stayed (0, 1), and a one-byte guest change alters the digest.
- `cgb_api_smoke` in `tests/consumers/c/main.c` and `tests/consumers/cpp/main.cpp`: `$C0` probe on DMG (mode DMG plus the CGB-only flag), CGB create/load/`gbb_get_info` (mode CGB, profile 2, struct_size 28), `struct_size` 0 returns `GBB_INVALID_ARGUMENT` with the buffer untouched, PGB `$84` refused on probe and load, `gbb_copy_frame` returns `GBB_UNSUPPORTED_PROFILE`.

## Verification

- Full `phase1` suite: 531/531 passed (about 170 s on a loaded host); no timeouts.
- Negative controls exercised: lowering the CGB wram bound in `require_banks` from 7 to 4 made `cgb_fuzz_io_regressions` abort; flipping the expected mode in the C consumer made `installed_consumer_c` fail; the skew loops in the matrix and parity cases fail the test if they report zero mismatches.
- `phase1-asan` is Linux only (`GABBABOY_ENABLE_SANITIZERS is supported only on Linux`), so it could not be configured on this macOS host. Substitute run: the same sources compiled directly with `-fsanitize=address,undefined -fno-sanitize-recover=undefined` ran clean for `test_fuzz_core` (default and `cgb`), `cgb_loader_matrix`, `loader` and `cgb_loader_fuzz_parity`, `concurrent_independent_instances`, `cgb_instance_isolation`, plus a 30000-input random driver through `gbb_fuzz_core_one_input` (two thirds with the CGB bits forced). The Linux ASan leg in CI remains the authoritative run.

## Deviations from Plan

**1. [Rule 3 - Blocking] Stale installed-package prefix**
- **Found during:** Task 3
- **Issue:** `build/package-prefix` (a gitignored cache install) predated `gbb_info`, so the installed consumers failed to compile.
- **Fix:** Re-ran `cmake --install build --prefix build/package-prefix`. No tracked file changed.
- **Commit:** none

**2. [Plan interpretation] Profile bit versus existing seed**
- **Found during:** Task 1
- **Issue:** The plan says bit 7 is unused, but the original minimized reproducer begins `0xFF`. It now selects the CGB profile.
- **Fix:** Kept it as a CGB-profile regression and added `0x7F` twin (bit 7 clear) so the DMG decoder path keeps the original coverage.
- **Commit:** 4a08747

**3. [Plan interpretation] Three bytes per guest operation**
- The plan says "each pair of bytes"; a pair cannot express value, address and a bank-register selector independently, so operations use selector, value and address bytes. The 64-operation bound is unchanged.

**4. [Environment] ASan preset unavailable on macOS** (see Verification); direct sanitizer builds substituted.

**Total deviations:** 1 auto-fixed (Rule 3), 3 documented interpretations. **Impact:** none on scope.

## Known Stubs

None.

## Threat Flags

None. No new network, file or trust-boundary surface; threats T-10-25 and T-10-26 are mitigated by the frozen fuzz bounds and the bank-state invariants above.

## Next

Ready for 10-19.

## Self-Check: PASSED

- Modified files present on disk (9 files listed in key-files).
- Commits 4a08747, 00eeb99, d69645b are ancestors of HEAD.
- Acceptance greps: `FUZZ_INPUT_LIMIT 65536u` count 1; `GBB_UNSUPPORTED_EXECUTION_MODE` in fuzz_core.c at least 1; `^cgb_fuzz_io_regressions$` 1; the three `cgb_` loader/isolation names 3; `GBB_PROFILE_CGB_CPU_E` in both consumers; `gbb_get_info` in the C++ consumer.

## 15.1-19 Fresh Applicability Evidence

On 2026-10-21, current focused fuzz, loader, parity, and instance-isolation checks passed 5/5:

```text
ctest --test-dir build --output-on-failure -R '^(cgb_fuzz_io_regressions|fuzz_core_regressions|cgb_loader_matrix|cgb_loader_fuzz_parity|cgb_instance_isolation)$'
```

Both existing installed-package consumer executables also passed when run with the tracer fixture:

```text
build/consumer-c/consumer-c fixtures/tracer/tracer.gb
build/consumer-cpp/consumer-cpp fixtures/tracer/tracer.gb
```

These are focused current-source checks. The Phase 10 sanitizer and full-suite record above remains historical; this note does not claim a new sanitizer run.
