# Phase 13 final-wave evidence and cost record

These are bounded software-fixture and test-suite measurements. They do not qualify physical CGB-E hardware and are not emulator-throughput claims.

## Evidence revision and host

- Source revision: `690c081e3714aa1039263255d572b6d0d06dad8e`
- The local measurements below were run against this source revision. Later documentation-only heads preserve the measured source identity; each pushed PR head still requires its own exact-head checks before it can be called green.
- Runtime-mask mutant build-cost source revision: `41bb9bf9258f529e394ac14cf1396928281cdee0`.
- Phase 12 inventory baseline: `8091fb591de7fb68e666be01d344f5f26ebedc5c` (`tests/expected-tests.txt`, 898 names).
- Host class: Darwin arm64. Compiler: Apple clang 21.0.0. Generator: Ninja. Native/player CMake build type: Debug; C compilation uses `-g -std=c17`.
- Model scope: the full suites mix unit, integration, fixture, mutation, and packaging checks. HDMA behavior-specific fixture evidence uses the bootless CGB-CPU-E software model. Physical CGB-E remains UNKNOWN/POLICY.
- Samples: one full-suite run per configuration, no warm-up. CTest wall time and aggregate per-test time are different quantities. One sample does not estimate variance; uncertainty is not quantified (not zero). These are lane-cost observations, not emulator-speed measurements or comparable performance claims.

## Full test lanes

| Lane | Command and workload | Result | Output digest |
|---|---|---|---|
| Native Debug | Darwin arm64, Apple clang 21.0.0, CMake 4.4.3, Ninja; `cmake --preset phase1 && cmake --build --preset phase1 && ctest --test-dir build --parallel 4 --output-on-failure --no-tests=error --output-junit build/phase13-wave10-native-690c081.xml` | 993/993 passed, 0 failed/errors/skipped; CTest wall 85.16 s | `build/build/phase13-wave10-native-690c081.xml`, SHA-256 `616e607d867b3184078cf7929f0806abf38fbcd6d197e22014bcf11b58baf1e1` |
| SDL3 player Debug | Darwin arm64, Apple clang 21.0.0, CMake 4.4.3, Ninja; existing `build-player` package uses SDL 3.4.18; `cmake --build build-player && ctest --test-dir build-player --parallel 4 --output-on-failure --no-tests=error --output-junit build-player/phase13-wave10-player-690c081.xml` | 1,086/1,086 passed, 0 failed/errors/skipped; CTest wall 100.35 s | `build-player/build-player/phase13-wave10-player-690c081.xml`, SHA-256 `27e32fd1dfc4e663810ea0fedecbc4f6fbef80e994b01f47531c5d80024f1976` |
| Relocated installed consumers and preview package | Darwin arm64; six exact CTest targets: `preview_package_smoke`, `installed_runner_smoke`, and C/C++ phase1/phase2 consumers; configured `GBB_TEST_INSTALL_PREFIX=relocated-prefix` | 6/6 passed, 0 failed/errors/skipped; CTest wall 1.78 s | `build/phase13-wave10-installed-690c081.xml`, SHA-256 `e6444ccf70ce75a894218ba762099750ca8781a869e311bd930efefe9c406082` |

Against Phase 12's 898-name expected-test inventory at `8091fb591de7fb68e666be01d344f5f26ebedc5c`, the native report has 993 names, 95 added and none removed. The 95 added cases' individual CTest durations sum to 7.290 s on this Debug host; this is not the parallel wall-time increment. Five newly registered local-only Python contracts are included in that inventory. The current JUnit contains 29 `cgb_hdma_mutant_*` cases totaling 0.397 s, including the anchor guard and mask-zero controls. The representative no-copy mutant/control pair took 0.022 s aggregate.

## Debug ASan/UBSan lane

The local command `cmake --preset phase1-asan` stops at the repository's explicit platform guard: `GABBABOY_ENABLE_SANITIZERS is supported only on Linux`. No sanitizer run or local ASan cost is claimed on Darwin. The existing CI policy remains Linux `phase1-asan --parallel 4`, a 30-minute job timeout, and the existing per-test timeout scaling. Historical PR-event run `38661411340` at source `e9bc47ed30f5eb4ee1303c06153303c2deb6bea3` passed Linux job `116183292071`: 988/988 tests, no skips, CTest wall 847.53 s. This is historical evidence only. Exact-source PR-event run `38662784214` at source `690c081e3714aa1039263255d572b6d0d06dad8e` passed Linux ASan/UBSan job `116187705198`: 988 executed cases, none skipped, zero failures, CTest wall 676.28 s. Its separate no-host-clock check, bounded-fuzz self-test, and three deterministic fuzz regressions passed; the log states the configured `fuzz_core` target is unavailable. This is test-harness evidence only and not a host-fuzzer campaign. No stale, skipped, or absent check is treated as green.

## Runtime-mask mutant build cost

The current HDMA runtime-mask cases share `test_cgb_hdma` and the generated `gabbaboy_core_p13_mutants` translation unit; adding one CTest mask does not create a per-mutant executable or a new compilation target. A scratch-only source invalidation of that combined generated translation unit measures the rebuild cost of changing one generated mutant source site:

| Measurement | Command scope | Wall time | Steps/result |
|---|---|---:|---|
| Configure | `cmake -S . -B build/phase13-mutant-cost -G Ninja -DCMAKE_BUILD_TYPE=Debug -DBUILD_TESTING=ON -DGABBABOY_BUILD_PLAYER=OFF` | 1.184 s | pass |
| Cold HDMA runtime-mask target | `cmake --build build/phase13-mutant-cost --target test_cgb_hdma --verbose` | 0.209 s | 4 Ninja steps; executable SHA-256 `85e21320d7b566a733875acc6fd20884d17cabc479246a9028dd9a83028e40f8` |
| One combined mutant-source invalidation | Append a scratch-only comment to generated `build/phase13-mutant-cost/tests/gabbaboy_p13_mutants.c`, then rebuild the same target | 0.190 s | 3 Ninja steps: compile the shared mutant TU, relink its archive, relink `test_cgb_hdma` |
| One representative mutant and mask-zero control | `cgb_hdma_mutant_no_copy` plus `cgb_hdma_mutant_no_copy_control`, in the native full report | 0.022 s aggregate | Both passed |

Phase 12's local Debug record measured 16 steps/0.25 s for a broader set of internal, public-library, and partition mutant targets. The scopes differ, so the figures are descriptive only; no improvement is attributed to Phase 13. Each mutant-cost measurement has one sample, no warm-up, and uncertainty is not quantified (not zero). At current source `690c081`, the 29 `cgb_hdma_mutant_*` tests total 0.397 s; their one-sample lane cost is descriptive only and not comparable as a performance change against Phase 12.

## Pinned fixture and claim-prohibition evidence

- Original project-authored HDMA ROM: `fixtures/cgb-hdma/hblank.gb`, 32,768 bytes, SHA-256 `f21cdc65d24f98cbf7713686c96a5e41f29e6769f78fc6a6f61b0d230ebbf431`; local source/license checks and self-test controls passed, and the RGBDS 1.0.1 rebuild was byte-identical. The task-local macOS archive SHA-256 is `2f6f13c6ec984313656c07b08d97dfcd3a471c7d3901d3ff486e5814bb503645`.
- SameSuite's four admitted DMA fixtures rebuilt byte-identically at pinned source revision `f15645fb049a47ea235f6d2c9a033e72d8087901` with RGBDS 1.0.1. Mutation controls for license, source, tool, digest, D-06 expectation, and extra rows passed.
- MagenTests 0.5.0's pinned source rebuild was byte-identical with RGBDS 0.6.1. The verified macOS x86-64 archive SHA-256 is `65929a5483c89b20955df0d78ceb87744d8ad0cf7c80919f6ee9ef90fc55c08d`; no Mealybug bytes were fetched.
- The actual OpenGSD prohibition producer returned green, unflagged, located, `test`/`node-test`, with non-empty passed, fail-first, and `violation-fixture` evidence. The committed RED test is `e8308d2359d23abf67df314ce761b56ed1d288e8`; its isolated committed snapshot failed the named Node assertion on the expected CGB-C/physical-CGB-E diagnostic and passed `gsd_run check tdd-red-evidence`. Clean-subject and live-checkout GREEN checks passed. Missing/empty subjects, always-green/empty-TAP adapters, and a live unqualified claim were rejected. The public Python `--prohibitions`, `--prohibitions-self-test`, and `--handoff` commands resolve the installed OpenGSD runtime without a `GSD_TOOLS` override; an invalid explicit override fails.
- The prohibition projection clears only the machine-checkable claim safeguard. Optional CGB-C material remains rights-gated, informational, and outside the CGB-E denominator; the separate generic unresolved edge remains open.

## Exact-source hosted workflow status

- PR-event workflow run `38662784214` targets source `690c081e3714aa1039263255d572b6d0d06dad8e` and completed success. All jobs passed: `linux-asan-ubsan` (988 executed, none skipped, 676.28 s CTest), `cmake-floor-3.25.3` (CMake 3.25.3 inventories: 988 base cases in 632.69 s and 993 relocated installed cases in 650.32 s, none skipped), `native-macos-arm64` (993 executed, none skipped, 628.13 s CTest), `native-windows-x64` (981 passed, 495.80 s CTest), `native-linux-x64` (993 passed, 475.61 s CTest), `player-gate`, `macos-player-package`, and aggregate `required-native`. Windows `samesuite_repro_selfcheck` passed in 4.87 s; macOS and Linux no-host-clock checks passed.
- The macOS player-package job `116187733769` passed its 98 player-specific tests (17.34 s CTest) and extracted SDL 3.4.18 package smoke; package SHA-256 `3cb71a0118f5d60c81efad862406360c8999785c2aa3bb72a3d6ac433bd4d18b`. The run's initial macOS queue (job start record 00:55:37Z, runner assignment at 01:16:48Z) had no runner assigned and no check annotations. GitHub Status at 01:14:30Z reported all systems operational and no unresolved incidents; the official runner-images label table lists `macos-14` for macOS 14 Arm64. The deprecation notice's brownout windows did not include this run's Oct 15 00:55Z queue interval; the next scheduled brownout begins Oct 16 at 14:00Z. The jobs later received runners and passed. No label or timeout change was made.
- Fixture/reproduction run `38662784222` at source `690c081e3714aa1039263255d572b6d0d06dad8e` completed 8/8 jobs successfully, including SameSuite and MagenTests byte-identical rebuilds.
- Matching package preview run `38662784151` completed success for the same tested source and exact CI linkage. Linux and macOS installed-package jobs each passed `preview_package_smoke` and their external consumer checks (CTest target wall 1.38 s and 2.47 s respectively); macOS player-package smoke downloaded and passed the package built for `690c081e3714aa1039263255d572b6d0d06dad8e`. Aggregate `preview-package-smoke` job `116197591830` passed.
- These CI conclusions belong to source `690c081e3714aa1039263255d572b6d0d06dad8e`. The local `e56ead2` BENCH commit is documentation-only, and final review/verification metadata has not yet been published; exact final metadata-head CI remains pending parent closeout.

## Scope limits

Do not generalize these software observations to DMA timing across other model variants, mode-3 behavior, APU behavior, commercial-game compatibility, or physical CGB-E qualification. The `CGB-CPU-E` selected software model and guest fixtures remain the stated applicability boundary. No host-fuzzer campaign is claimed.
