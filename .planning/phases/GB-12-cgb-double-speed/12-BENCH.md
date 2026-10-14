# Phase 12 close-out evidence record

Advisory local measurements and exact-head hosted CI evidence for Phase 12. No timing threshold is asserted. The CGB workload and AGE corpus are deterministic software fixtures, not physical hardware evidence.

## Evidence revision and full-suite baseline

- Core/performance-evidence revision: `b03e6a643289dc4bf4134ba1e7cb78609816d04c` (`docs(12-19): record phase decisions and memory`). The later source revision `301f1b05577e6d35a4c3a756ded1ec15a4082c8d` changed only the CI test-inventory platform filter and its self-test; no emulator, public-header, or CTest implementation changed.
- Host class: Darwin arm64. Compiler: Apple clang 21.0.0 (`clang-2100.1.1.101`).
- Build: `cmake --preset phase1` (Debug, `BUILD_TESTING=ON`, `GABBABOY_BUILD_PLAYER=OFF`). Configure/generate: 0.58 s real. Incremental full build: 1.23 s real.
- Full local verification: `ctest --test-dir build -j8 --output-on-failure --no-tests=error`: 897/897 passed, 35.49 s CTest wall time on the current close-out run (earlier full runs took 35.53 s and 36.91 s). The exact current JUnit report also passes `verify-test-inventory.sh` in installed mode: all 897 required tests executed, none skipped. `bash tests/scripts/verify-dmg-baseline.sh`: pass, inventory 313, Mooneye 15, acceptance 20, benchmark 2, no changed rows.
- DMG tracer control, `build/measure_core --no-trace fixtures/tracer/tracer.gb`: 1,000,000 half-dots consumed, budget stop, `correctness_digest_fnv1a64=4c7a57ff3d50d228`. Repeated with the Release measurement binary and the same digest.

## Hosted CI and GB-CI-004 comparison

The exact PR head is `301f1b05577e6d35a4c3a756ded1ec15a4082c8d`, on draft [PR #68](https://github.com/szTheory/gabbaboy/pull/68). CI run IDs: 38502094649, 38502094682, 38502094771. All exact-head PR checks passed: `required-native` job `115655092007`; native Linux, macOS and Windows jobs `115651190908`, `115651190895`, and `115651190903`; CMake floor job `115651190932`; `linux-asan-ubsan` job `115651190687`; player package job `115651217377`; Linux/macOS installed-package smoke jobs `115651191568` and `115651191633`; player-package smoke job `115651191811`; and preview-package smoke job `115655286837`. The sanitizer job wall was 10m06s (job wall 10m06s); CTest test time 579.99 s, with 892/892 passed and none skipped. Comparing test names newly added since the Phase 12 execution start `aac4772` with the exact-job log identifies 206 Phase 12 additions; their individual CTest elapsed times sum to 325.28 s (sum of per-test durations, not wall time). All 206 names were present in that successful run. Fixture reproductions use run `38502094682`. Push-event checks are excluded from this result; the skipped push-event player-package check is not evidence.

On the same exact source revision, Linux fixture-reproduction job `115651190879` used pinned RGBDS 1.0.1 (`80a5cad8dae27e24e46a93041352c47cadbc165103983f41c2b3082c42f6dad9`). It reported `result=byte-identical roms=2` for `speed.gb` and `speed-hostile.gb` and `result=byte-identical` for all 13 AGE ROMs; AGE compare-tampered and selfcheck-tampered controls passed. These results verify generated fixture bytes only, not hardware behavior. The AGE source receipt is also recorded in `fixtures/age/SOURCES.md`; `fixtures/cgb-speed/manifest.json` has no provisional Linux digest statement to replace.

GB-CI-004 records observed ASan CTest wall times of 826–915 seconds at `--parallel 4`, after a prior serial run took 1,194 seconds and a slower pull-request runner hit the 30-minute job cap. The exact PR run's 579.99 s differs numerically by 246.01 s from the historical low end and 335.01 s from its high end; the endpoint deltas (current minus historical) are -246.01 s versus 826 s and -335.01 s versus 915 s. These are different source revisions, test inventories, and runners; the comparison is descriptive only and does not establish a speedup or attribute an improvement to Phase 12. The 325.28 s aggregate above is the separately measured Phase 12 added-test duration. The current sanitizer job took 606 s total under the same 30-minute job cap.

The first exact PR run, `38500963019` at SHA `b03e6a643289dc4bf4134ba1e7cb78609816d04c`, exposed a real Windows inventory-gate failure: all 885 CTests passed, but the verifier expected five bash-only AGE/CGB reproduction tests that CMake correctly omits on WIN32. The H2 correction at `301f1b05577e6d35a4c3a756ded1ec15a4082c8d` adds only those exact exclusions and a self-test proving that required tests cannot disappear and unrelated entries survive. Its exact PR Linux job ran that self-test successfully, and exact PR Windows native CTest plus inventory verification passed. The H1 failure remains recorded rather than being replaced with its later green result.

## Mutant build inventory and local cost

The Phase 12 CMake inventory budgets five distinct core-mutation build sites, below the D-25 ceiling of six: white-box internal runtime-mask tests, the static-assert negative build, the public-library mutant, the partition mutant, and the optional player mutant. The anchor-guard negative control checks source-generation rejection and does not add a compiled core variant.

Mutant core builds: 5 distinct planned build sites (four available in this local configuration; the optional player mutant was exercised by the passing exact-PR macOS package job above).

Fresh Debug scratch measurements on this Darwin arm64 host:

| Measurement | Command scope | Real wall time | Result |
|---|---|---:|---|
| Configure/generate | Ninja, `BUILD_TESTING=ON`, optional player disabled | 0.91 s | pass |
| Compile/link | internal white-box test executable, public AGE mutant library/test, partition test | 0.25 s | pass; 16 build steps including shared dependencies |
| Static-assert negative build | `cgb_speed_stall_static_assert_mutant` CTest | 0.09 s | expected compile rejection observed; CTest passed |
| Optional player mutant | unavailable in local configuration | not measured | SDL3 is not installed; hosted pull-request player-package job passed at the exact evidence SHA |

This is the measured local configure/compile cost for the four locally available variants. The optional player variant is counted in the five-site inventory but is not claimed as a local build; its hosted job result will determine whether it was exercised on the exact PR SHA.

## AGE and partition test wall times

Measured serially with `ctest --test-dir build -R '^(age_|cgb_partition_)' -j1 --output-on-failure --no-tests=error --output-junit /private/tmp/p12-age-partition-junit.xml`. JUnit recorded 27 AGE tests totaling 31.411 s and 18 partition tests totaling 2.304 s; the whole 46-test invocation, including one fixture setup test, took 33.77 s wall time. These are local Debug CTest times, not hosted sanitizer timings.

Oracle scope remains narrow: only `spsw-div-cgbBCE` and `spsw-stop-prefetch-cgbBCE` pass; eleven other admitted AGE cases retain named expected-failure dispositions. The corrected double-only M28 mutation changes the `spsw-mode0-cgbBCE` result but not `spsw-div-cgbBCE`; it is incorrect to claim that AGE fails to detect M28 generally. The `spsw-tima-cgbBC` contingency drops the B/C TIMA claim. These are software-model findings, not hardware results.

| AGE test | Seconds |
|---|---:|
| `age_spsw_div_cgbBCE_timeout` | 0.009 |
| `age_stall_window` | 1.420 |
| `age_spsw_div_cgbBCE` | 0.330 |
| `age_spsw_tima_cgbE` | 0.201 |
| `age_spsw_tima_cgbBC` | 0.196 |
| `age_spsw_stop_prefetch_cgbBCE` | 0.035 |
| `age_spsw_interrupts_cgbE` | 0.022 |
| `age_spsw_mode0_cgbBCE` | 0.048 |
| `age_spsw_ch2_lc_delay_cgbBCE` | 0.535 |
| `age_stat_mode_ds_cgbBCE` | 0.993 |
| `age_stat_mode_cgbE` | 0.414 |
| `age_stat_mode_sprites_ds_cgbBCE` | 0.091 |
| `age_stat_mode_sprites_dmgC_cgbBCE` | 0.053 |
| `age_stat_mode_window_ds_cgbBCE` | 0.147 |
| `age_stat_mode_window_cgbBCE` | 0.110 |
| `age_sensitivity_m6` | 6.555 |
| `age_sensitivity_m21` | 6.589 |
| `age_sensitivity_m28` | 6.606 |
| `age_sensitivity_m27` | 6.616 |
| `age_sensitivity_m28_reference_mutated` | 0.100 |
| `age_fixture_digest` | 0.009 |
| `age_fixture_digest_tampered` | 0.011 |
| `age_not_installed` | 0.013 |
| `age_not_installed_selftest` | 0.012 |
| `age_repro_selfcheck` | 0.033 |
| `age_repro_selfcheck_tampered` | 0.137 |
| `age_repro_compare_tampered` | 0.125 |

| Partition test | Seconds |
|---|---:|
| `cgb_partition_stall_start_window` | 0.096 |
| `cgb_partition_hostile_irq_in_stall` | 0.083 |
| `cgb_partition_mutant_m16` | 0.057 |
| `cgb_partition_mutant_m16_control` | 0.083 |
| `cgb_partition_snapshot_fidelity` | 0.012 |
| `cgb_partition_stall_end_window_to_double` | 0.098 |
| `cgb_partition_stall_end_window_to_normal` | 0.101 |
| `cgb_partition_stall_end_window_seeded` | 0.092 |
| `cgb_partition_interior_points` | 0.021 |
| `cgb_partition_seeded_multicut` | 0.375 |
| `cgb_partition_zero_and_subquantum` | 0.005 |
| `cgb_partition_pending_at_stop` | 0.447 |
| `cgb_partition_held_button` | 0.093 |
| `cgb_partition_lcd_off` | 0.095 |
| `cgb_partition_back_to_back` | 0.198 |
| `cgb_partition_chained` | 0.420 |
| `cgb_partition_sensitivity_joypad_shift` | 0.013 |
| `cgb_partition_sensitivity_digest_input` | 0.015 |

## Advisory CGB release measurement

- Revision: `b03e6a643289dc4bf4134ba1e7cb78609816d04c`; host class: Darwin arm64; compiler: Apple clang 21.0.0 (`clang-2100.1.1.101`).
- Build: Release scratch build, `CMAKE_BUILD_TYPE=Release`, `BUILD_TESTING=ON`, `GABBABOY_BUILD_PLAYER=OFF`, `measure_core` target only; compile flags `-O3 -DNDEBUG -std=c17`.
- Workload: `measure_core --no-trace --profile cgb fixtures/cgb-speed/speed.gb`; CGB-CPU-E, bootless, 1,000,000 half-dots. Input ROM SHA-256: `3c6e88de1e28d47566f7486dd13813c8fb1baf48ee336509e3902bd9ff8e2f3f`.
- Three warm-ups and 30 measured runs. Every run consumed the full budget with a budget stop and returned the same `correctness_digest_fnv1a64=244c987a2da74e65`.
- Median 9.5685 ms; minimum 9.1730 ms; sample standard deviation 0.2723 ms; mean 9.5408 ms; 95% margin of mean `1.96 × SD / sqrt(30)` = 0.0974 ms. This is one advisory sample set; no speedup, timing threshold, or physical-hardware claim is asserted.
- The DMG control `correctness_digest_fnv1a64=4c7a57ff3d50d228` stayed unchanged in both Debug and Release measurement binaries.

Raw sample `elapsed_ns` values (30):

```text
9193000,9256000,9496000,9454000,9221000,9821000,9696000,9623000,9316000,9177000,
9754000,9587000,9197000,9297000,9807000,9545000,9356000,9550000,9779000,9687000,
9621000,9173000,9731000,9758000,9399000,10366000,9767000,9709000,9209000,9680000
```
