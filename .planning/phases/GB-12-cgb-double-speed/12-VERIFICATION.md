---
phase: GB-12-cgb-double-speed
verified: 2026-10-14T15:05:03Z
status: passed
score: 109/109 must-haves verified
covered_files:
  - ".github/scripts/test-inventory-cleanup.sh"
  - ".github/scripts/verify-test-inventory.sh"
  - ".github/workflows/ci.yml"
  - ".github/workflows/fixture-repro.yml"
  - ".github/workflows/preview.yml"
  - ".gitignore"
  - ".planning/phases/GB-12-cgb-double-speed/12-01-PLAN.md"
  - ".planning/phases/GB-12-cgb-double-speed/12-01-SUMMARY.md"
  - ".planning/phases/GB-12-cgb-double-speed/12-02-PLAN.md"
  - ".planning/phases/GB-12-cgb-double-speed/12-02-SUMMARY.md"
  - ".planning/phases/GB-12-cgb-double-speed/12-03-PLAN.md"
  - ".planning/phases/GB-12-cgb-double-speed/12-03-SUMMARY.md"
  - ".planning/phases/GB-12-cgb-double-speed/12-04-PLAN.md"
  - ".planning/phases/GB-12-cgb-double-speed/12-04-SUMMARY.md"
  - ".planning/phases/GB-12-cgb-double-speed/12-05-PLAN.md"
  - ".planning/phases/GB-12-cgb-double-speed/12-05-SUMMARY.md"
  - ".planning/phases/GB-12-cgb-double-speed/12-06-PLAN.md"
  - ".planning/phases/GB-12-cgb-double-speed/12-06-SUMMARY.md"
  - ".planning/phases/GB-12-cgb-double-speed/12-07-PLAN.md"
  - ".planning/phases/GB-12-cgb-double-speed/12-07-SUMMARY.md"
  - ".planning/phases/GB-12-cgb-double-speed/12-08-PLAN.md"
  - ".planning/phases/GB-12-cgb-double-speed/12-08-SUMMARY.md"
  - ".planning/phases/GB-12-cgb-double-speed/12-09-PLAN.md"
  - ".planning/phases/GB-12-cgb-double-speed/12-09-SUMMARY.md"
  - ".planning/phases/GB-12-cgb-double-speed/12-10-PLAN.md"
  - ".planning/phases/GB-12-cgb-double-speed/12-10-SUMMARY.md"
  - ".planning/phases/GB-12-cgb-double-speed/12-11-PLAN.md"
  - ".planning/phases/GB-12-cgb-double-speed/12-11-SUMMARY.md"
  - ".planning/phases/GB-12-cgb-double-speed/12-12-PLAN.md"
  - ".planning/phases/GB-12-cgb-double-speed/12-12-SUMMARY.md"
  - ".planning/phases/GB-12-cgb-double-speed/12-13-PLAN.md"
  - ".planning/phases/GB-12-cgb-double-speed/12-13-SUMMARY.md"
  - ".planning/phases/GB-12-cgb-double-speed/12-14-PLAN.md"
  - ".planning/phases/GB-12-cgb-double-speed/12-14-SUMMARY.md"
  - ".planning/phases/GB-12-cgb-double-speed/12-15-PLAN.md"
  - ".planning/phases/GB-12-cgb-double-speed/12-15-SUMMARY.md"
  - ".planning/phases/GB-12-cgb-double-speed/12-16-PLAN.md"
  - ".planning/phases/GB-12-cgb-double-speed/12-16-SUMMARY.md"
  - ".planning/phases/GB-12-cgb-double-speed/12-17-PLAN.md"
  - ".planning/phases/GB-12-cgb-double-speed/12-17-SUMMARY.md"
  - ".planning/phases/GB-12-cgb-double-speed/12-18-PLAN.md"
  - ".planning/phases/GB-12-cgb-double-speed/12-18-SUMMARY.md"
  - ".planning/phases/GB-12-cgb-double-speed/12-19-PLAN.md"
  - ".planning/phases/GB-12-cgb-double-speed/12-19-SUMMARY.md"
  - ".planning/phases/GB-12-cgb-double-speed/12-UAT.md"
  - ".planning/phases/GB-12-cgb-double-speed/verify-closeout-contract.py"
  - ".planning/phases/GB-12-cgb-double-speed/verify-uat-contract.py"
  - "README.md"
  - "THIRD_PARTY_NOTICES.md"
  - "cmake/ExpectedTests.cmake"
  - "cmake/P12Mutants.cmake"
  - "cmake/ScaleSanitizerTimeouts.cmake"
  - "docs/cartridge-and-saves.md"
  - "docs/cgb-profile.md"
  - "docs/mbc3-rtc-evidence.md"
  - "docs/model-gates.md"
  - "docs/native-integration.md"
  - "docs/preview.md"
  - "docs/support/unreleased.md"
  - "fixtures/age/ELIGIBILITY.md"
  - "fixtures/age/LICENSE.txt"
  - "fixtures/age/SOURCES.md"
  - "fixtures/age/WARNING.md"
  - "fixtures/age/manifest.json"
  - "fixtures/age/spsw-ch2-lc-delay-cgbBCE.gb"
  - "fixtures/age/spsw-div-cgbBCE.gb"
  - "fixtures/age/spsw-interrupts-cgbE.gb"
  - "fixtures/age/spsw-mode0-cgbBCE.gb"
  - "fixtures/age/spsw-stop-prefetch-cgbBCE.gb"
  - "fixtures/age/spsw-tima-cgbBC.gb"
  - "fixtures/age/spsw-tima-cgbE.gb"
  - "fixtures/age/stat-mode-cgbE.gb"
  - "fixtures/age/stat-mode-ds-cgbBCE.gb"
  - "fixtures/age/stat-mode-sprites-dmgC-cgbBCE.gb"
  - "fixtures/age/stat-mode-sprites-ds-cgbBCE.gb"
  - "fixtures/age/stat-mode-window-cgbBCE.gb"
  - "fixtures/age/stat-mode-window-ds-cgbBCE.gb"
  - "fixtures/cgb-speed/LICENSE.txt"
  - "fixtures/cgb-speed/common.inc"
  - "fixtures/cgb-speed/manifest.json"
  - "fixtures/cgb-speed/speed-hostile.asm"
  - "fixtures/cgb-speed/speed-hostile.gb"
  - "fixtures/cgb-speed/speed.asm"
  - "fixtures/cgb-speed/speed.gb"
  - "include/gabbaboy/gabbaboy.h"
  - "src/core/gabbaboy.c"
  - "src/core/gabbaboy_test.h"
  - "src/player/limitations.h"
  - "src/player/main.c"
  - "tests/CMakeLists.txt"
  - "tests/check_no_phase12_rows.cmake"
  - "tests/check_no_stale_speed_claims.cmake"
  - "tests/check_sanitizer_timeout_policy.cmake"
  - "tests/cmake/timeout-policy/CMakeLists.txt"
  - "tests/cmake/timeout-policy/child/CMakeLists.txt"
  - "tests/consumers/c/main.c"
  - "tests/consumers/cpp/main.cpp"
  - "tests/data/cgb-speed-expectations.txt"
  - "tests/expected-tests.txt"
  - "tests/external/cgb-speed-dispositions.json"
  - "tests/fuzz/fuzz_core.dict"
  - "tests/fuzz_core.c"
  - "tests/player/CMakeLists.txt"
  - "tests/player/cgb_smoke.cmake"
  - "tests/player/expected-tests.txt"
  - "tests/player/test_limitations.c"
  - "tests/scripts/derive-cgb-speed-expectations.py"
  - "tests/scripts/reproduce-age.sh"
  - "tests/scripts/reproduce-cgb-speed.sh"
  - "tests/scripts/run-bounded-fuzz.sh"
  - "tests/scripts/test-reproduce-age.sh"
  - "tests/scripts/test-reproduce-cgb-speed.sh"
  - "tests/scripts/verify-cgb-speed-dispositions.py"
  - "tests/scripts/verify-speed-domains.py"
  - "tests/test_age.c"
  - "tests/test_cgb_partition.c"
  - "tests/test_cgb_speed_fixture.c"
  - "tests/test_cgb_speed_internal.c"
  - "tests/test_cgb_tables.c"
  - "tests/test_cgb_visibility.c"
  - "tests/test_fuzz_core.c"
covered_digest: "v3:sha256:561b22625520a939bbf8fb6ba0364cd76db8bb6afd64ee1b4bad50bb7081891f"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 109/109
  gaps_closed: []
  gaps_remaining: []
  regressions: []
---

# Phase 12: CGB Double Speed Verification Report

**Phase Goal:** CGB software can switch speed through KEY1 and STOP, with CPU-side devices running at twice the rate while PPU and APU timing are unchanged.
**Verified:** 2026-10-14T15:05:03Z
**Status:** passed
**Re-verification:** Yes — metadata correction and automated UAT closure

## Goal Achievement

The goal is implemented in `src/core/gabbaboy.c` and exercised through public run paths and targeted core tests. KEY1 arms the switch; only CGB hardware profile plus CGB execution mode plus armed KEY1 takes the switching STOP path. STOP retires at the executing speed, resets DIV before toggling speed, clears the arm bit, and starts a named persisted stall. The stall advances CPU-clocked devices at destination speed while PPU/APU master-time progression remains unchanged. The build and tests connect these paths through CTest and the player smoke harness.

| # | Observable truth | Status | Evidence |
|---|---|---|---|
| 1 | In CGB mode, KEY1 plus STOP switches CPU/timer/serial/OAM-DMA to double speed while PPU and APU timing remain on the master timeline. | ✓ VERIFIED | `cgb_speed_tracer_switch`, `cgb_speed_timer_scaling`, `cgb_speed_serial_scaling`, `cgb_speed_dma_scaling`, `cgb_speed_apu_tap`, `cgb_speed_ppu_apu_rtc_unscaled`; 53 original guest checks and frame/PCM digest checks pass. |
| 2 | The switch uses the declared STOP/stall semantics, advances devices during the stall, and leaves DMG/unarmed paths unchanged, including hostile pre-switch cases. | ✓ VERIFIED | Named STOP case, STOP cost, stall length/budget/headroom/device, timer IRQ guest, DMG control, hostile guest and negative-mutant tests pass. STOP switch stall is `0x20004` destination-speed CPU T; the model-qualified AGE acceptance interval is `[0x20004, 0x20007]`. |
| 3 | Runs partitioned across switch/stall boundaries produce the same state as uninterrupted runs, and unresolved oracle behavior has explicit model-qualified dispositions. | ✓ VERIFIED | Both-direction boundary checks plus 256 seeded multi-cut cases pass; exact-signature AGE dispositions and closeout contract positive/negative controls pass. |

### Plan Must-Haves

All 106 plan-level truth assertions from the 19 plans were checked against implementation, test wiring, named test results, evidence inputs, or explicit negative controls. Together with the three roadmap success criteria, the score is 109/109. The table identifies the primary evidence for each plan; detailed test and artifact evidence follows.

| Plan | Truths | Primary codebase evidence |
|---|---:|---|
| 12-01 | 10 | Pre-change identity pins and flip control; KEY1/STOP retire, reset, stall and trace assertions in `tests/test_cgb_speed_internal.c`. |
| 12-02 | 7 | Fixture rights, provenance and model boundaries in `fixtures/cgb-speed/` and `fixtures/age/`. |
| 12-03 | 5 | Runtime-mask mutant harness and negative controls are registered in CTest. |
| 12-04 | 3 | Existing CGB vendored-fixture inventory and byte-exact fixture verification are retained and pass. |
| 12-05 | 6 | CPU clock scaling tests cover timer, serial, OAM-DMA, APU tap and unscaled PPU/APU/RTC domains. |
| 12-06 | 7 | STOP decision cases cover held/pending inputs, operands, KEY1 read/write and DMG/compat controls. |
| 12-07 | 8 | Stall run-loop branch, device progress, budgets, wake behavior, realignment and headroom checks. |
| 12-08 | 6 | AGE model/eligibility gates and named outcome scope in `tests/external/cgb-speed-dispositions.json`. |
| 12-09 | 6 | AGE measurements and stall-window test use pinned inputs and the declared model-specific verdict driver. |
| 12-10 | 4 | Reproduction path and its regression tests rebuild and check the original CGB speed guest. |
| 12-11 | 3 | Hostile pre-switch selector is an in-memory ROM mutation with ten exercised selector cases. |
| 12-12 | 5 | Player smoke and consumer-facing claims are connected to the built player and CTest inventory. |
| 12-13 | 2 | Byte-exact guest rebuild is checked by the fixture reproduction path. |
| 12-14 | 8 | `tests/test_cgb_partition.c` checks both switch/stall edges and 256 seeded multi-cut partitions against uninterrupted execution. |
| 12-15 | 5 | Deterministic seeded speed-state/property checks are registered; no libFuzzer campaign is claimed. |
| 12-16 | 5 | Each admitted AGE image is measured against its pinned exact signature. |
| 12-17 | 5 | Expected failures have reason/model/signature dispositions; gate mutation controls reject altered or missing dispositions. |
| 12-18 | 5 | `docs/cgb-profile.md` states host-visible speed behavior and model/fixture limits. |
| 12-19 | 6 | Closeout contract positive case and 17 scratch mutations validate required closeout evidence. |

All 46 declared plan artifact entries pass the OpenGSD artifact checks. The key-link query verified 9/30 links mechanically. The remaining links use descriptive `from` labels rather than root-relative paths, so I traced their source and target in the implementation, tests, CMake, workflow, and documentation. These traces confirm STOP state flows through retirement into the run-loop stall, device ticks use the intended clock domain, fixtures flow through the emulator into checked output, test names flow through CMake and the expected-test inventory, and model dispositions flow through the validators and test driver. For the fixture expectations link, CMake passes `tests/data/cgb-speed-expectations.txt` to the runtime test at `tests/CMakeLists.txt:3250-3253`; the table does not repeat its filename internally. There are no orphaned plan requirement IDs.

## Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `src/core/gabbaboy.c` | KEY1 state, STOP transition, and destination-speed stall | ✓ VERIFIED | Non-stub implementation; KEY1, reset, decode/retire, and run-loop stall paths are connected. The switch path does not set the DMG `stopped` state. |
| `tests/test_cgb_speed_internal.c` | State/clock/STOP behavior and controls | ✓ VERIFIED | Registered and exercised; includes named behavior checks and mutant/control pairs. |
| `tests/test_cgb_speed_fixture.c` | Guest-driven integration evidence | ✓ VERIFIED | Loads the original guest via the public CGB API, runs it through `gbb_run`, and checks WRAM observations and output digests. |
| `tests/test_cgb_partition.c` | Partition invariance | ✓ VERIFIED | Compares serialized state for uninterrupted and partitioned public runs, including seeded cuts. |
| `tests/test_age.c`, `tests/external/cgb-speed-dispositions.json` | Qualified external oracle outcomes | ✓ VERIFIED | Pinned ROM signatures are matched against named model-qualified outcomes, including expected failures. |
| `tests/CMakeLists.txt`, `tests/expected-tests.txt` | Test registration and inventory | ✓ VERIFIED | Tests are built and registered; coverage consistency checks pass. |
| `fixtures/cgb-speed/` manifest, source and license | Redistributable original guest | ✓ VERIFIED | Project-authored guest and MIT terms are documented; its output is a model test, not hardware evidence. |
| `tests/scripts/verify-speed-domains.py` | CPU/master clock-domain invariant check | ✓ VERIFIED | Connected to the test suite; mutant controls detect scaling PPU/APU channels or RTC incorrectly. |
| `docs/cgb-profile.md` | Host-facing behavior and limitations | ✓ VERIFIED | Updated claims match implemented behavior and do not assert hardware qualification. |

The declaration-level checks reported 46/46 artifacts passing. Source/test/doc files above also pass the substantive and wiring checks; the guest-to-core-to-observation path is traced below.

## Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| KEY1 register handling | STOP execution | `key1_armed` and `stop_case()` | ✓ WIRED | Read/write gating is profile/mode aware; switch requires armed CGB execution. |
| STOP execute/retire | Run-loop stall | `stop_switch_pending` and `cpu_stall_*` | ✓ WIRED | Switch occurs at retirement, DIV reset precedes toggle, arm clears, then the dedicated stall branch consumes time before normal interrupt dispatch. |
| CPU instruction/bus clocks | Timer, serial, DMA | `cpu_tick` and speed-shifted costs/offsets | ✓ WIRED | Targeted rate tests and source audit show CPU-side domains double. |
| CPU double-speed flag | PPU/APU/RTC master timeline | half-dot advancement and APU frame tap | ✓ WIRED | PPU, APU channels/output and RTC remain unscaled; only the APU frame tap follows the required CPU clock domain. |
| CGB guest ROM | Core execution | `gbb_create` → `gbb_load_rom` → `gbb_run` | ✓ WIRED | Guest checks observations produced by execution; the expected table is independently derived, not generated from the observed run. |
| Mutated/partitioned runs | State comparison and negative controls | test-only state access, digest and deterministic cuts | ✓ WIRED | Both stall-edge directions and 256 seeded multi-cut cases are exercised. |
| Tests | Build/CI inventory | CMake registration and expected-test inventory | ✓ WIRED | Current configured build includes the phase tests; baseline and closeout controls pass. |

## Data-Flow Trace (Level 4)

| Artifact | Data variable | Source | Produces real execution data | Status |
|---|---|---|---|---|
| `tests/test_cgb_speed_fixture.c` | Guest WRAM output | Original assembled `fixtures/cgb-speed/speed.gb`, loaded by the public core API and executed with `gbb_run` | Yes; checks 53 runtime observations | ✓ FLOWING |
| `tests/test_cgb_speed_fixture.c` | Frame and PCM digests | Frames/audio copied from the emulated core across 60 frames | Yes; regression digest checks include mutants that must change when output timing is incorrectly scaled | ✓ FLOWING |
| `tests/test_age.c` | AGE outcome signature | Pinned external ROM execution under the declared CGB model and exact signature table | Yes; verdict distinguishes pass from expected fail | ✓ FLOWING |
| `tests/test_cgb_partition.c` | Serialized machine-state digest | Real public-run state after identical guest execution under different run partitions | Yes; comparison is metamorphic evidence, not a hardware oracle | ✓ FLOWING |

## Behavioral Spot-Checks

| Behavior | Command/check | Result | Status |
|---|---|---|---|
| KEY1/STOP, CPU-clocked scaling, master-clock invariants, stall semantics | `ctest --test-dir build -R '^(cgb_speed_tracer_switch|cgb_speed_timer_scaling|cgb_speed_serial_scaling|cgb_speed_dma_scaling|cgb_speed_apu_tap|cgb_speed_ppu_apu_rtc_unscaled|cgb_speed_stall_length|cgb_speed_stall_devices_advance|cgb_speed_stop_cases|cgb_speed_budget_semantics)$' --output-on-failure --no-tests=error -j1` | 10/10 passed | ✓ PASS |
| Fixture observations, frame/PCM digests, and model-qualified STAT outcomes | Targeted CTest fixture/AGE/STAT selection | 8/8 passed; guest reports 53 checks; 60-frame output digests match | ✓ PASS |
| Natural timer IRQ across EI;STOP, STOP EI path, and hostile pre-switch inputs | `ctest --test-dir build -R '^(cgb_speed_stop_guest_timer_irq|cgb_speed_ei_stop|cgb_speed_fixture_hostile)$' --output-on-failure -j1` | 3/3 passed; the timer guest reaches the ordinary `gbb_run` interrupt dispatch path; hostile selector covers 10 cases | ✓ PASS |
| AGE stall window, DIV/TIMA dispositions, and switch/stall partition windows | Targeted verbose CTest AGE and partition selection | 9/9 passed; DIV and STOP-prefetch pass; TIMA and other unresolved rows match their exact-signature expected-failure dispositions; both partition directions and 256 seeded cuts pass | ✓ PASS |
| Complete configured regression suite | `cmake --preset phase1 && cmake --build --preset phase1 && CTEST_PARALLEL_LEVEL=8 ctest --preset phase1 --output-on-failure --no-tests=error` | Fresh configure/build and 898/898 tests passed in 107.00 s at implementation head `da98d56ef8fadadf34ae951b337dcdecce495936` | ✓ PASS |
| DMG compatibility baseline | `bash tests/scripts/verify-dmg-baseline.sh` | Pass: 313 inventory, 15 Mooneye, 20 acceptance, 2 benchmark observations; zero changed rows | ✓ PASS |
| Closeout contract and negative controls | `python3 -I .planning/phases/GB-12-cgb-double-speed/verify-closeout-contract.py --self-test` | Positive case and 17 scratch-mutation controls pass | ✓ PASS |
| Automated UAT closure contract | `python3 -I .planning/phases/GB-12-cgb-double-speed/verify-uat-contract.py --self-test` | Exact one-to-one mapping of 73 coverage rows passes; all 9 weakened-record mutations are rejected | ✓ PASS |

## UAT Closure and Fresh Evidence

The current [12-UAT.md](12-UAT.md) records 73/73 automated deliverables, zero issues, and zero human checkpoints. OpenGSD's coverage classifier reports all 73 rows `auto_passed`, with zero `present` rows or errors; all 19 SUMMARY coverage blocks pass schema validation, including the 3/3 `summary_coverage` checks. The closeout contract also passes its positive case and 17 negative controls. The added UAT closure checker validates the session mapping and negative controls; it is not a production or registered test change. No production code, registered tests, build configuration, workflow, or fixture changed after implementation head `da98d56ef8fadadf34ae951b337dcdecce495936`.

The bounded commit audit found one mistyped metadata value: plan 12-04's `plan_head_after` in its SUMMARY. The full SHA is now `ec5dc8a28daf54a722f4da9b036c5fa48690bc6e`; its task commits remain ancestors, and all 19 bounded plan commit windows reconcile. This correction does not change implementation or behavioral evidence.

One earlier isolated M7 control run failed once without retained diagnostic output; its cause remains unknown. The same control passed 100 repeated runs, and the fresh 898-test suite passed. No assertion or pin was changed to accommodate that event.

## Probe Execution

No phase plan or summary declares a `probe-*.sh` path, and no conventional `scripts/*/tests/probe-*.sh` file exists. The phase's reproduction, closeout and baseline checks are covered by the named CTest/script checks above.

## Requirements Coverage

| Requirement | Source plan | Description | Status | Evidence |
|---|---|---|---|---|
| CGB-06 | 12-01 through 12-19 | CGB software switches through KEY1 and STOP; CPU-side clock domains run at double rate while PPU/APU master timing remains correct | ✓ SATISFIED | Implementation and named behavior tests; original guest, exact-signature AGE scope, partition checks, and unchanged DMG baseline. No additional phase-mapped requirement is orphaned. |

## Prohibition Checks

The 48 plan prohibitions use the older `{statement, requirement}` form and do not declare `verification` tiers. Each was checked against implementation, the relevant deterministic test/negative control, or the documented fixture/claim boundary. No unresolved prohibition was found. In particular, the public C/C++ ABI gains no speed getter; DMG, compat and unarmed STOP remain covered; the stall does not become a fake STOP/HALT; fixture rights and provenance are explicit; and user-facing claims do not promote model tests into hardware qualifications.

## Model-Qualified Outcomes and Limits

The AGE evidence is deliberately narrow: only `spsw-div` (5/5) and `spsw-stop-prefetch` (1/1) are passes. The other 11 admitted ROM outcomes are exact-signature, model-qualified expected failures, not failures silently counted as passes and not hardware evidence. TIMA remains an expected failure at 5/8 on CGB-E and 7/8 on CGB-BC. The adopted switch stall is `0x20004` destination-speed T, within the passing AGE interval `0x20004..0x20007`; the available model evidence does not distinguish every value in that interval. The DIV oracle does not detect the M28 mutation that adds a half-dot when switching into double speed; the `spsw-mode0` oracle does detect it. Speed-dependent STAT/mode-3 behavior remains outside this phase's contract. No physical console qualification or libFuzzer campaign is claimed.

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---:|---|---|---|
| — | — | None in phase implementation, test, fixture, or documentation deliverables | — | No blocker or stub pattern found. |

## Human Verification Required

None. Per the project automation contract, phase deliverables have automated checks and negative controls; this phase has no visual UI, hardware qualification requirement, credentialed integration, or unresolved runtime invariant requiring a manual checkpoint.

## External Exact-Revision CI

The current exact tested source head is `da98d56ef8fadadf34ae951b337dcdecce495936`: [CI 38569486172](https://github.com/szTheory/gabbaboy/actions/runs/38569486172), [fixture reproduction 38569486169](https://github.com/szTheory/gabbaboy/actions/runs/38569486169), and [package smoke 38569486126](https://github.com/szTheory/gabbaboy/actions/runs/38569486126) all succeeded, with all 19 PR-event jobs successful. ASan/UBSan ran 893/893 tests in 1089.77 seconds; native Linux/macOS/Windows, CMake 3.25 floor, player package, required-native, installed C/C++ consumers, and fixture reproductions passed. Push-event skipped jobs are excluded. The verification/UAT metadata revision recorded here still needs exact-head hosted checks after it is committed; these source-head receipts do not certify that later metadata commit.

## Gaps Summary

No codebase gaps block the Phase 12 goal. Implementation, data flow, test wiring, all 109 roadmap/plan truths, 46 plan artifacts, requirement CGB-06, automated UAT closure, and the unchanged DMG baseline are verified. Declared model limits remain explicit and are not presented as physical hardware facts.

---

_Verified: 2026-10-14T15:05:03Z_
_Verifier: the agent (gsd-verifier)_
