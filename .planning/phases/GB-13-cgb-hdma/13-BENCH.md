# Phase 13 final-wave evidence and cost record

These are bounded software-fixture and test-suite measurements. They do not qualify physical CGB-E hardware and are not emulator-throughput claims.

## Evidence revision and host

- Source revision: `0d5bb9cbfc5dcc730c2d9ce45c6358b79154aaa9`
- Runtime-mask mutant build-cost source revision: `41bb9bf9258f529e394ac14cf1396928281cdee0`.
- Phase 12 inventory baseline: `8091fb591de7fb68e666be01d344f5f26ebedc5c` (`tests/expected-tests.txt`, 898 names).
- Host class: Darwin arm64. Compiler: Apple clang 21.0.0. Generator: Ninja. Native/player CMake build type: Debug; C compilation uses `-g -std=c17`.
- Model scope: the full suites mix unit, integration, fixture, mutation, and packaging checks. HDMA behavior-specific fixture evidence uses the bootless CGB-CPU-E software model. Physical CGB-E remains UNKNOWN/POLICY.
- Samples: one full-suite run per configuration, no warm-up. CTest wall time and aggregate per-test time are different quantities. One sample does not estimate variance or support a performance threshold.

## Full test lanes

| Lane | Command and workload | Result | Output digest |
|---|---|---|---|
| Native Debug | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --test-dir build --parallel 4 --output-on-failure --no-tests=error --output-junit build/phase13-wave10-native-0d5bb9c.xml` | 993/993 passed, 0 failed/errors/skipped; CTest wall 81.02 s | JUnit SHA-256 `94a0786bbfba97970361a23c73bada72b7643c5aac98fb499cf0acfbb64cf765` |
| SDL3 player Debug | Existing `build-player` package uses SDL 3.4.18; `cmake --build build-player && ctest --test-dir build-player --parallel 4 --output-on-failure --no-tests=error --output-junit build-player/phase13-wave10-player-0d5bb9c.xml` | 1,086/1,086 passed, 0 failed/errors/skipped; CTest wall 81.80 s | JUnit SHA-256 `c90c990aa4490e17d71d9532d76461a811a4352fca5c6204c073a4f20ad48eff` |
| Relocated installed consumers and preview package | Six exact CTest targets: `preview_package_smoke`, `installed_runner_smoke`, and C/C++ phase1/phase2 consumers; configured `GBB_TEST_INSTALL_PREFIX=relocated-prefix` | 6/6 passed, 0 failed/errors/skipped; CTest wall 1.19 s | JUnit SHA-256 `96f5bc93ba9bf960200c3d716a2e3f8859ccd05e7ab5a65e145d2eb35f71b65b` |

Against Phase 12's 898-name expected-test inventory at `8091fb591de7fb68e666be01d344f5f26ebedc5c`, the native report has 993 names, 95 added and none removed. The 95 added cases' individual CTest durations sum to 4.252 s on this Debug host; this is not the parallel wall-time increment. Five newly registered local-only Python contracts are included in that inventory. The local JUnit contains 29 HDMA mutant/control cases totaling 0.342 s.

## Debug ASan/UBSan lane

The local command `cmake --preset phase1-asan` stops at the repository's explicit platform guard: `GABBABOY_ENABLE_SANITIZERS is supported only on Linux`. No sanitizer run or local ASan cost is claimed on Darwin. The existing CI policy remains Linux `phase1-asan --parallel 4`, a 30-minute job timeout, and the existing per-test timeout scaling. The PR-event run for source commit `41bb9bf9258f529e394ac14cf1396928281cdee0` is an earlier tested source, not a final-source sanitizer result. The final tested branch head will require its own exact-head PR-event evidence; no stale or skipped result will be used.

## Runtime-mask mutant build cost

The current HDMA runtime-mask cases share `test_cgb_hdma` and the generated `gabbaboy_core_p13_mutants` translation unit; adding one CTest mask does not create a per-mutant executable or a new compilation target. A scratch-only source invalidation of that combined generated translation unit measures the rebuild cost of changing one generated mutant source site:

| Measurement | Command scope | Wall time | Steps/result |
|---|---|---:|---|
| Configure | `cmake -S . -B build/phase13-mutant-cost -G Ninja -DCMAKE_BUILD_TYPE=Debug -DBUILD_TESTING=ON -DGABBABOY_BUILD_PLAYER=OFF` | 1.184 s | pass |
| Cold HDMA runtime-mask target | `cmake --build build/phase13-mutant-cost --target test_cgb_hdma --verbose` | 0.209 s | 4 Ninja steps; executable SHA-256 `85e21320d7b566a733875acc6fd20884d17cabc479246a9028dd9a83028e40f8` |
| One combined mutant-source invalidation | Append a scratch-only comment to generated `build/phase13-mutant-cost/tests/gabbaboy_p13_mutants.c`, then rebuild the same target | 0.190 s | 3 Ninja steps: compile the shared mutant TU, relink its archive, relink `test_cgb_hdma` |
| One representative mutant and mask-zero control | `cgb_hdma_mutant_no_copy` plus `cgb_hdma_mutant_no_copy_control`, in the native full report | 0.021 s aggregate | Both passed |

Phase 12's local Debug record measured 16 steps/0.25 s for a broader set of internal, public-library, and partition mutant targets. The scopes differ, so the figures are descriptive only; no improvement is attributed to Phase 13. Each mutant-cost measurement has one sample, no warm-up, and uncertainty is not estimable. The 29 HDMA mutant/control CTests sum to 0.342 s in the native report at `0d5bb9cbfc5dcc730c2d9ce45c6358b79154aaa9`.

## Pinned fixture and claim-prohibition evidence

- Original project-authored HDMA ROM: `fixtures/cgb-hdma/hblank.gb`, 32,768 bytes, SHA-256 `f21cdc65d24f98cbf7713686c96a5e41f29e6769f78fc6a6f61b0d230ebbf431`; local source/license checks and self-test controls passed, and the RGBDS 1.0.1 rebuild was byte-identical. The task-local macOS archive SHA-256 is `2f6f13c6ec984313656c07b08d97dfcd3a471c7d3901d3ff486e5814bb503645`.
- SameSuite's four admitted DMA fixtures rebuilt byte-identically at pinned source revision `f15645fb049a47ea235f6d2c9a033e72d8087901` with RGBDS 1.0.1. Mutation controls for license, source, tool, digest, D-06 expectation, and extra rows passed.
- MagenTests 0.5.0's pinned source rebuild was byte-identical with RGBDS 0.6.1. The verified macOS x86-64 archive SHA-256 is `65929a5483c89b20955df0d78ceb87744d8ad0cf7c80919f6ee9ef90fc55c08d`; no Mealybug bytes were fetched.
- The actual OpenGSD prohibition producer returned green, unflagged, located, `test`/`node-test`, with non-empty passed, fail-first, and `violation-fixture` evidence. The committed RED test is `e8308d2359d23abf67df314ce761b56ed1d288e8`; its isolated committed snapshot failed the named Node assertion on the expected CGB-C/physical-CGB-E diagnostic and passed `gsd_run check tdd-red-evidence`. Clean-subject and live-checkout GREEN checks passed. Missing/empty subjects, always-green/empty-TAP adapters, and a live unqualified claim were rejected.
- The prohibition projection clears only the machine-checkable claim safeguard. Optional CGB-C material remains rights-gated, informational, and outside the CGB-E denominator; the separate generic unresolved edge remains open.

## Scope limits

Do not generalize these software observations to DMA timing across other model variants, mode-3 behavior, APU behavior, commercial-game compatibility, or physical CGB-E qualification. The `CGB-CPU-E` selected software model and guest fixtures remain the stated applicability boundary. No host-fuzzer campaign is claimed.
