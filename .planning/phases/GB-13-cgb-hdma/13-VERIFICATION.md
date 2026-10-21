---
phase: 13-cgb-hdma
verified: '2026-10-20T23:31:32Z'
status: passed
score: 37/37 must-haves verified
covered_files:
- .gitattributes
- .github/workflows/ci.yml
- .github/workflows/fixture-repro.yml
- .github/workflows/preview.yml
- .gitignore
- .planning/phases/GB-13-cgb-hdma/13-01-PLAN.md
- .planning/phases/GB-13-cgb-hdma/13-01-SUMMARY.md
- .planning/phases/GB-13-cgb-hdma/13-02-PLAN.md
- .planning/phases/GB-13-cgb-hdma/13-02-SUMMARY.md
- .planning/phases/GB-13-cgb-hdma/13-03-PLAN.md
- .planning/phases/GB-13-cgb-hdma/13-03-SUMMARY.md
- .planning/phases/GB-13-cgb-hdma/13-04-PLAN.md
- .planning/phases/GB-13-cgb-hdma/13-04-SUMMARY.md
- .planning/phases/GB-13-cgb-hdma/13-05-PLAN.md
- .planning/phases/GB-13-cgb-hdma/13-05-SUMMARY.md
- .planning/phases/GB-13-cgb-hdma/13-06-PLAN.md
- .planning/phases/GB-13-cgb-hdma/13-06-SUMMARY.md
- .planning/phases/GB-13-cgb-hdma/13-07-PLAN.md
- .planning/phases/GB-13-cgb-hdma/13-07-SUMMARY.md
- .planning/phases/GB-13-cgb-hdma/13-08-PLAN.md
- .planning/phases/GB-13-cgb-hdma/13-08-SUMMARY.md
- .planning/phases/GB-13-cgb-hdma/13-09-PLAN.md
- .planning/phases/GB-13-cgb-hdma/13-09-RED-evidence.json
- .planning/phases/GB-13-cgb-hdma/13-09-SUMMARY.md
- .planning/phases/GB-13-cgb-hdma/13-09-TASK2-RED-evidence.json
- .planning/phases/GB-13-cgb-hdma/13-10-PLAN.md
- .planning/phases/GB-13-cgb-hdma/13-10-SUMMARY.md
- .planning/phases/GB-13-cgb-hdma/13-11-PLAN.md
- .planning/phases/GB-13-cgb-hdma/13-11-SUMMARY.md
- .planning/phases/GB-13-cgb-hdma/13-12-PLAN.md
- .planning/phases/GB-13-cgb-hdma/13-12-SUMMARY.md
- .planning/phases/GB-13-cgb-hdma/13-ASAN-ADDED-COST.json
- .planning/phases/GB-13-cgb-hdma/13-BENCH.md
- .planning/phases/GB-13-cgb-hdma/13-REFRESH-GATES.md
- .planning/phases/GB-13-cgb-hdma/13-UAT.md
- .planning/phases/GB-13-cgb-hdma/COVERAGE.md
- .planning/phases/GB-13-cgb-hdma/verify-hdma-closure.py
- .planning/phases/GB-13-cgb-hdma/verify-hdma-source-revision.py
- .planning/phases/GB-13-cgb-hdma/verify-uat-contract.py
- README.md
- cmake/ExpectedTests.cmake
- cmake/GabbaBoyConfig.cmake.in
- cmake/P12Mutants.cmake
- cmake/P13Mutants.cmake
- cmake/PreviewPackageSmoke.cmake
- cmake/RunInstalledConsumer.cmake
- cmake/ScanForbiddenFixtures.cmake
- cmake/VerifyInstalledPackage.cmake
- docs/cgb-profile.md
- docs/model-gates.md
- docs/native-integration.md
- docs/preview.md
- docs/support/unreleased.md
- fixtures/cgb-hdma/LICENSE.txt
- fixtures/cgb-hdma/hblank.asm
- fixtures/cgb-hdma/hblank.gb
- fixtures/cgb-hdma/manifest.json
- fixtures/magentests/ELIGIBILITY.md
- fixtures/magentests/LICENSE.txt
- fixtures/magentests/SOURCES.md
- fixtures/magentests/hblank_vram_dma.gbc
- fixtures/magentests/manifest.json
- fixtures/samesuite/ELIGIBILITY.md
- fixtures/samesuite/LICENSE.txt
- fixtures/samesuite/gbc_dma_cont.gb
- fixtures/samesuite/gdma_addr_mask.gb
- fixtures/samesuite/hdma_lcd_off.gb
- fixtures/samesuite/hdma_mode0.gb
- fixtures/samesuite/manifest.json
- src/core/gabbaboy.c
- src/player/limitations.h
- src/player/main.c
- tests/CMakeLists.txt
- tests/acceptance/CMakeLists.txt
- tests/cgb_consumer_symbol_coverage.cmake
- tests/consumers/c/CMakeLists.txt
- tests/consumers/c/main.c
- tests/consumers/cpp/CMakeLists.txt
- tests/consumers/cpp/main.cpp
- tests/expected-tests.txt
- tests/external/cgb-hdma-dispositions.json
- tests/external/cgb-speed-dispositions.json
- tests/fuzz_core.c
- tests/player/CMakeLists.txt
- tests/player/cgb_smoke.cmake
- tests/player/claims_agree.cmake
- tests/player/expected-tests.txt
- tests/player/test_limitations.c
- tests/scripts/cgb-hdma-prohibition.test.cjs
- tests/scripts/phase13-handoff-continuity.test.cjs
- tests/scripts/reproduce-cgb-hdma.sh
- tests/scripts/reproduce-magentests.sh
- tests/scripts/reproduce-samesuite.sh
- tests/scripts/test_hdma_remote_evidence.py
- tests/scripts/test_magentests_hdma_registration.py
- tests/scripts/test_reproduce_magentests.py
- tests/scripts/verify-cgb-hdma-claims.py
- tests/scripts/verify-cgb-hdma-dispositions.py
- tests/scripts/verify-uat-closure.py
- tests/test_cgb_hdma.c
- tests/test_cgb_hdma_internal.c
- tests/test_cgb_hdma_partition.c
- tests/test_cgb_partition.c
- tests/test_cgb_speed_internal.c
- tests/test_cgb_visibility.c
- tests/test_magentests.c
- tests/test_samesuite_hdma.c
covered_digest: v3:sha256:521a2fc4b77822add035be56319fbdb56f5fdfb0e8c7004881868a7d6247632c
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 37/37
  gaps_closed: []
  gaps_remaining: []
  regressions: []
---

# Phase 13: CGB HDMA Verification Report

**Phase Goal:** CGB software can use general-purpose and HBlank VRAM DMA with hardware-shaped CPU stall, cancel and readback, bounded per run.
**Verified:** 2026-10-20T23:31:32Z
**Status:** passed
**Re-verification:** Yes — refresh of completed implementation; no plan replay.

## Goal Achievement

Independently recounted scope: **three roadmap criteria plus34 plan truths =37**, **49 artifact declarations (35 distinct paths)**, **12 key-link declarations**, **one test-tier prohibition**. The twelve SUMMARYs contain **45 coverage blocks and93 verification references**; the old209-entry claim is not retained. CGB-07 is the only requirement mapped to Phase13 and all twelve plans claim it; no orphan requirement.

Fresh unchanged source `a5f0d5962acb5eefa0143f7cde5942725ad2ac79`: parent configure/build and complete core regression **1144/1144 in438.76s**, rebuilt SDL player selection **98/98 in19.87s**, zero skips. Verifier inspected both logs and independently ran the focused positive/negative checks below. The table's fresh-native/player references mean those current receipts. Historical measurements/rebuild/hosted receipts retain their own revisions; they do not establish current-head remote readiness.

### Observable Truths

| # | Truth | Status | Evidence |
|---:|---|---|---|
| 1 | General-purpose DMA stalls the CPU for the transfer and HBlank DMA moves one block per visible-line mode-0 entry, both writing to the current VRAM bank, verified by SameSuite `dma/*` ROMs and original fixtures. | ✓ VERIFIED | `src/core/gabbaboy.c` admits bounded blocks and commits them through selected VBK; passing `cgb_hdma_timing_policy`, `cgb_hdma_guest_banks`, `cgb_hdma_original_fixture`, and four SameSuite cases are in the fresh native report. |
| 2 | Cancelling via HDMA5 bit 7, HDMA5 readback, HALT during a transfer, LCD-off and invalid sources follow stated behaviors with tests; unresearched cases are recorded as unspecified rather than invented. | ✓ VERIFIED | Register state and documented POLICY/UNKNOWN cases in core/docs; passing `cgb_hdma_state_matrix`, `cgb_hdma_trigger_matrix`, `cgb_hdma_guest_halt`, `cgb_hdma_address_matrix`, `cgb_hdma_overflow_policy`, and `samesuite_hdma_hdma_lcd_off`; focused state/address/HALT checks also passed. |
| 3 | Every transfer is bounded (at most 128 blocks) and partitioned runs stay equivalent across transfers; MagenTests `hblank_vram_dma` passes with its oracle class recorded, and Mealybug `hdma_*-C` results are informational CGB-C evidence outside the CGB-E denominator. | ✓ VERIFIED | `hdma_state` bounds to 128 blocks; partition suite passes at both speeds and critical cuts; `magentests_hblank_vram_dma` passes; documentation and disposition contracts state selected oracle class, Mealybug `not-run:rights-gate-G1`, and physical CGB-E UNKNOWN/POLICY. |
| 4 | D-01/D-02/D-03/D-09: A real FF51–FF55 transfer at both late-access seams preserves whole instructions, event order, time conservation and bounded outputs before any expansion. | ✓ VERIFIED | Source scheduler and bounded half-dot transfer logic; `cgb_hdma_tracer_ld_sp`, `cgb_hdma_tracer_cb`, `cgb_hdma_tracer_partition`, output/control cases pass in the fresh native report. |
| 5 | D-04/D-11: FF51–54 read FF as POLICY; CGB DMA uses narrow mapper/storage access and selected-bank VRAM writes. | ✓ VERIFIED | `src/core/gabbaboy.c` uses `hdma_source_read`, `cart_read`/`wram_byte`, snapshots VBK, and returns documented FF visibility; `cgb_hdma_visibility`, `cgb_hdma_address_matrix`, and bank guest tests pass. |
| 6 | D-08/D-22/D-24: Model timing and support claims remain qualified, executable and paired with negative controls. | ✓ VERIFIED | `docs/cgb-profile.md`, support/player docs, claim checker and mutated controls; `cgb_hdma_claims_contract`, native selector, selftest, and player claim positive/mutated tests pass. |
| 7 | D-04/D-05/D-06: Guest start/read/cancel is exactly 83→02→00→80 with explicit active-write/restart cells and 1–128 block bounds. | ✓ VERIFIED | State/trigger matrices cover active write and cancellation; resource bound tests and guest HALT/transfer checks pass in native and player reports. |
| 8 | D-07/D-08: Only the initial kick and genuine visible HBlank admission transfer; every data block uses 64 master half-dots at either speed. | ✓ VERIFIED | Admission and timing policies in `hdma_advance_half_dot`/scheduler; `cgb_hdma_trigger_matrix`, timing/speed, and no-false-trigger mutant/control cases pass. |
| 9 | D-11/D-12/D-13/D-24: Valid mapped blocks preserve prefix data; invalid sources and destination overflow terminate safely with stated qualified status. | ✓ VERIFIED | Address and overflow matrices assert preserved prefix/termination; passing mutant/control twins and docs state supported and unknown cases. |
| 10 | D-10/D-14: HALT, STOP, speed switch and DMA have independent progress and wake rules; IRQ wake cannot erase a steal. | ✓ VERIFIED | `cgb_hdma_guest_halt`, `cgb_hdma_stop_policy`, `cgb_hdma_competing_stalls`, speed policy, and lost-IRQ/steal controls pass in the native report. |
| 11 | D-08/D-19: Original guests program actual DMA registers, switch banks and fail a guest-visible CPU-steal timing discriminator when stealing is omitted. | ✓ VERIFIED | CPU-programmed guest harness, bank assertions, `cgb_hdma_guest_steal`, no-steal mutant and passing control are in fresh native/player JUnit; focused guest-steal check passed. |
| 12 | D-09/D-24: The real scheduler preserves previous bus/device order and migrated Phase12 anchors retain their original sensitivity. | ✓ VERIFIED | Device ordering is explicit in scheduler; OAM-order controls and migrated-anchor guard pass, with inherited speed anchor tests in fresh native suite. |
| 13 | D-15/D-20: Uninterrupted and critical-cut runs at both speeds match hidden state, guest memory and timestamped outputs. | ✓ VERIFIED | `cgb_hdma_partition_midbyte`, windows, multicuts, output comparisons, and lost-remainder/order negative controls pass; focused midbyte partition check passed. |
| 14 | D-01/D-15: Create/reset/successful load clear DMA, failed load preserves active progress, and independent instances remain isolated. | ✓ VERIFIED | Lifecycle tests and controls exercise reset/load/instance behavior; `cgb_hdma_lifecycle` and `cgb_hdma_lifecycle_controls` pass. |
| 15 | D-20/D-22: Bounded hostile seeds and all capacity/headroom paths have matching defect controls and truthful campaign status. | ✓ VERIFIED | Resource/hostile-seed tests and controls pass; `13-BENCH.md` and closure checks bound claims and report no local fuzz campaign. |
| 16 | D-19/D-20: Guest no-steal and every selected HDMA fault are rejected by a behavioral predicate with a passing mask-zero twin. | ✓ VERIFIED | Runtime mutant matrix has paired named controls; all mutant/control cases are present and passing in the native and player JUnit reports. |
| 17 | D-21: Mutation compilation stays bounded and ASan/native cost is measured with existing parallelism/timeouts. | ✓ VERIFIED | Historical bounded shared-mutant build and added ASan cost remain recorded at actual source in 13-BENCH.md; current lane contract retains parallel4/timeout45. No fresh sanitizer/benchmark claimed. |
| 18 | D-24: Migrated P12 anchors remain unique and disposition semantics retain sensitivity. | ✓ VERIFIED | Anchor guard, disposition positive/mutated cases, and inherited CGB speed disposition tests pass in fresh native/player reports. |
| 19 | D-16: Exactly gbc_dma_cont, gdma_addr_mask, hdma_lcd_off and hdma_mode0 are admitted at f15645fb049a47ea235f6d2c9a033e72d8087901 with X11/G7 and CC0 closure. | ✓ VERIFIED | Four pinned SameSuite manifest rows, license/source/tool/digest checks and named execution tests pass; manifest, eligibility and rebuild script are connected by CTest. |
| 20 | D-02/D-21/D-22: Existing pinned RGBDS1.0.1 and fixture-repro lane reproduce exact bytes, rejecting tampered pins/rows/digests without new dependencies or jobs. | ✓ VERIFIED | Pinned fixture recipe, provenance and negative contracts remain wired. Historical 0f15a05 exact-head fixture-repro7/7 retained; no fresh local rebuild (RGBDS1.0.4 differs from1.0.1). |
| 21 | D-17: hblank_vram_dma source3f9c090f16e5a721db776febb9ba7d773e1c819c/0.5.0 release matches e8124ce687d37a2402e20af92af1299610bfbda0871d605084c0bba2bf57135c and rebuild. | ✓ VERIFIED | Magen manifest pins release/source/digest; `magentests_fixture_digest`, manifest/rebuild controls, and `magentests_hblank_vram_dma` pass; focused Magen case passed. |
| 22 | D-17/D-19/D-22: Guest data and source-derived green-screen structure gate success before a digest; wrong-HALT/bank/no-transfer twins fail specifically. | ✓ VERIFIED | Magen harness checks guest outputs and structural screen before digest; named control tests pass in native/player JUnit. |
| 23 | D-21: Existing Magen/reproduction/CTest lanes gain this single case without hardware claims or a new mandatory emulator. | ✓ VERIFIED | One Magen test is registered in existing targets and expected-test inventory; structural/docs contracts preserve software-only evidence boundary. |
| 24 | D-19/D-23: An original CPU-programmed DMA guest produces a source-derived visible pattern and guest pass/fail status, with a no-transfer twin. | ✓ VERIFIED | Original fixture manifest ties source to ROM; guest asserts visible result and status; player `player_cgb_hdma_smoke` and no-transfer twin pass. |
| 25 | D-21/D-23/D-24: The existing player smoke proves this same guest through the unchanged consumer API with structural pixels before a digest, without adding a UI flow or third-party install fixture. | ✓ VERIFIED | Existing player path and API unchanged; player target checks structural pixels before digest and control; `player_cgb_hdma_smoke`, no-transfer, and claim checks pass. |
| 26 | D-06/D-16: The exact four unmodified SameSuite cases execute with guest data/readback assertions and model-qualified dispositions. | ✓ VERIFIED | Four named `samesuite_hdma_*` tests pass; test names and disposition JSON reconcile with the exact pinned corpus. |
| 27 | D-17/D-18: Magen is differential evidence; absent Mealybug reports not-run:rights-gate-G1, CGB-C informational only, outside the CGB-E denominator. | ✓ VERIFIED | Documentation, eligibility/disposition records and claims contracts encode this boundary; optional Mealybug remains absent and outside denominator. |
| 28 | D-19/D-20/D-21/D-24: Core, evidence metadata, claims mirrors and mutation controls agree; missing files and arbitrary mutant failures never count as passes. | ✓ VERIFIED | Claims/disposition closure validators and mutation controls pass; native inventory includes missing/arbitrary-failure negative controls; fresh native/player suites pass. |
| 29 | D-01/D-23: Installed C and C++ callers run an inline original DMA guest across bounded partitions through unchanged public functions. | ✓ VERIFIED | Both installed consumer callers execute the inline guest through public functions; relocated installed-consumer JUnit is 6/6 with zero failures/errors/skips. |
| 30 | D-19/D-21/D-23: Both consumers check guest FF55/data/timing and a disabled-transfer twin; packages keep SameSuite/Magen/Mealybug excluded without allow-list expansion. | ✓ VERIFIED | C/C++ consumer tests include positive and disabled controls; package forbidden-fixture scans and allowlist checks pass in current installed/package lane. |
| 31 | D-24: Every native/player/package claim agrees with delivered qualified HDMA behavior while preserving mode3/APU/hardware/game limits. | ✓ VERIFIED | Claim mirrors and negative mutation controls pass; support docs explicitly keep mode3/APU/commercial-game/physical-hardware limits. |
| 32 | D-01/D-23: Documentation uses only declared unchanged public consumer functions and describes bounded DMA progression. | ✓ VERIFIED | README, native integration and support docs describe unchanged APIs and bounded runs; docs contract tests pass. |
| 33 | D-18/D-22: Model/oracle/rights qualifications and documentation have automated positive and mutated negative contracts with no routine human UAT. | ✓ VERIFIED | Claims checker, disposition checker, player contract and mutated controls pass; no plan human-check blocks or probe scripts are declared. |
| 34 | D-21: Existing native/sanitizer/reproduction/consumer/package lanes run an exact inventory with measured added ASan and mutant cost and unchanged parallel4/timeout policy. | ✓ VERIFIED | Current core1144/1144 and rebuilt player selection98/98 pass. Lane contract:6 targets,92core HDMA,2player HDMA,parallel4,timeout45;4 rejection controls. Historical ASan/cost/hosted receipts remain revision-qualified. |
| 35 | D-18/D-22: The claim-language prohibition is machine-proven fail-first and resolves green/unflagged through the actual OpenGSD gate before verify-work; physical UNKNOWN is preserved. | ✓ VERIFIED | Actual installed OpenGSD1.18.0 producer executes saved descriptor through helper APIs: green/unflagged/located/test/node-test with passed failFirst=true and violation-fixture proof after bad/clean/live checks. Old full wrapper pin1.16.0 remains incompatible. |
| 36 | D-22/D-24: Current-revision evidence and machine-readable coverage qualify all delivered claims; skipped/stale remote checks cannot prove the revision green. | ✓ VERIFIED | Fresh unchanged a5f0d5962acb5eefa0143f7cde5942725ad2ac79 passes core1144/1144,player98/98,all12 bounded task windows,zero changed DMG rows. Canonical UAT45/45 with19 controls; no current-head hosted readiness inferred. |
| 37 | D-25: Planning stops before execution; after Phase13 execution/verification the durable route is Phase14 CGB-E Model Qualification and Corpus, never auto-advanced. | ✓ VERIFIED | Historical planning/execution pause checked only at completed immutable e7ba52c81446096a9f6b5bf660d7721ea561eaa4: original pure handoff_values accepts own STATE/continuation/config and rejects4 route/flag mutations. No assertion against live historical route or current-HEAD ancestry. |

**Score:**37/37 verified; zero behavior-unverified truths and zero overrides. Behavioral rows have executed behavioral predicates and defect controls, not presence-only inference.

### Required Artifacts

`query verify.artifacts` ran separately on every current plan: **49/49** declarations pass existence/substance. Current implementation, harness, provenance, claim and build files were inspected for actual use. No orphan,stub or hollow output found.

| Plan | Declared artifact paths | Status |
|---|---|---|
| 13-01-PLAN | `src/core/gabbaboy.c`, `tests/test_cgb_hdma_internal.c`, `tests/CMakeLists.txt`, `tests/expected-tests.txt` | VERIFIED; substantive and wired through checks below |
| 13-02-PLAN | `src/core/gabbaboy.c`, `tests/test_cgb_hdma_internal.c`, `tests/CMakeLists.txt`, `tests/expected-tests.txt` | VERIFIED; substantive and wired through checks below |
| 13-03-PLAN | `src/core/gabbaboy.c`, `tests/test_cgb_hdma.c`, `tests/CMakeLists.txt`, `tests/expected-tests.txt` | VERIFIED; substantive and wired through checks below |
| 13-04-PLAN | `tests/test_cgb_hdma_partition.c`, `tests/test_cgb_partition.c`, `tests/CMakeLists.txt`, `tests/expected-tests.txt` | VERIFIED; substantive and wired through checks below |
| 13-05-PLAN | `src/core/gabbaboy.c`, `cmake/P13Mutants.cmake`, `tests/test_cgb_hdma.c`, `tests/CMakeLists.txt` | VERIFIED; substantive and wired through checks below |
| 13-06-PLAN | `fixtures/samesuite/manifest.json`, `fixtures/samesuite/LICENSE.txt`, `fixtures/samesuite/gbc_dma_cont.gb`, `tests/scripts/reproduce-samesuite.sh` | VERIFIED; substantive and wired through checks below |
| 13-07-PLAN | `fixtures/magentests/hblank_vram_dma.gbc`, `fixtures/magentests/manifest.json`, `fixtures/magentests/SOURCES.md`, `fixtures/magentests/ELIGIBILITY.md` | VERIFIED; substantive and wired through checks below |
| 13-08-PLAN | `fixtures/cgb-hdma/hblank.asm`, `fixtures/cgb-hdma/hblank.gb`, `fixtures/cgb-hdma/manifest.json`, `fixtures/cgb-hdma/LICENSE.txt` | VERIFIED; substantive and wired through checks below |
| 13-09-PLAN | `tests/test_samesuite_hdma.c`, `tests/external/cgb-hdma-dispositions.json`, `tests/scripts/verify-cgb-hdma-dispositions.py`, `tests/CMakeLists.txt` | VERIFIED; substantive and wired through checks below |
| 13-10-PLAN | `tests/consumers/c/main.c`, `tests/consumers/cpp/main.cpp`, `cmake/PreviewPackageSmoke.cmake`, `cmake/ScanForbiddenFixtures.cmake` | VERIFIED; substantive and wired through checks below |
| 13-11-PLAN | `docs/native-integration.md`, `docs/support/unreleased.md`, `docs/preview.md`, `README.md` | VERIFIED; substantive and wired through checks below |
| 13-12-PLAN | `.planning/phases/GB-13-cgb-hdma/13-01-PLAN.md`, `tests/scripts/cgb-hdma-prohibition.test.cjs`, `.planning/phases/GB-13-cgb-hdma/13-BENCH.md`, `.planning/phases/GB-13-cgb-hdma/verify-hdma-closure.py`, `tests/CMakeLists.txt` | VERIFIED; substantive and wired through checks below |

### Key Link Verification

The generic `query verify.key-links` returns0/12 with `Target not referenced in source`: declarations express behavioral relationships rather than direct imports from source to target. This CLI result is not presented as a pass. Manual tracing and executed predicates verify the actual joins:

| Plan | Declared from→to | Actual wiring | Status |
|---|---|---|---|
|01|core→internal harness|tests/CMakeLists.txt:422–448 compiles isolated core into harness and registers tracer/state predicates|WIRED|
|02|core→internal harness|same target invokes real FF51–55/scheduler for state,timing,trigger,address,overflow controls|WIRED|
|03|core→public harness|registered public gbb_run guest programs registers,HALT/IRQ,banks; steal mutant/control discriminates CPU progress|WIRED|
|04|HDMA partition→inherited partition|separate CTest targets compare explicit hidden-state/output hashes and inherited anchors; direct harness import unnecessary|WIRED|
|05|core→P13Mutants|tests/CMakeLists.txt:412 includes generator; count-checked core anchors feed shared test-only mask build; production mask zero|WIRED|
|06|SameSuite manifest→licence|reproduce-samesuite validates exact four-row source/include/licence/tool/digest closure; existing workflow invokes recipe|WIRED|
|07|Magen ROM→manifest|CTest passes pinned ROM to source-derived guest/map/HALT/green-pixel oracle; provenance/digest/registration contracts bind manifest|WIRED|
|08|assembly→original ROM|manifest/reproduction binds source,digest,recipe; public/player use actual ROM and no-transfer twin|WIRED|
|09|SameSuite harness→dispositions|CTest binds four exact cases; disposition checker reconciles source/test/result/denominator;16 mutations rejected|WIRED|
|10|C→C++ consumers|separate relocated configurations use exact installed package prefix; matching bounded inline guests and disabled twins|WIRED|
|11|native docs→support|claims checker reads8 actual surfaces and declared API symbols;7 claim mutations and3 bad subjects rejected|WIRED|
|12|Node prohibition→BENCH|saved descriptor projects actual claim adapter; current producer checks bad/clean/live; lane/source/remote contracts qualify BENCH receipts|WIRED|

### Data-Flow Trace (Level4)

| Artifact | Output | Source and flow | Status |
|---|---|---|---|
|core|VRAM bytes,FF55,CPU progress|guest bus writes→hdma_register_write→GDMA/visible-HBlank request→preflight/admit→cart_read/wram_byte→per-block VBK→four-half-dot byte commit→remaining/status|FLOWING|
|SameSuite|guest data/readback/status|pinned unmodified ROM→CPU/bus observations→source-derived memory/readback predicates; no-copy controls|FLOWING|
|Magen|map/HALT/green screen|pinned ROM→real core→guest state and structural green pixels before digest; wrong-HALT/bank/no-transfer twins|FLOWING|
|original/player|RGB555 pattern|original source/ROM→public/player execution→source-derived pixel structure before digest; no-transfer twin|FLOWING|
|installed C/C++|FF55,data,DIV timing|inline guest→unchanged installed API→bounded partitions→status/data/steal predicates; disabled twin prevents FF55=FF alone passing|FLOWING|
|claims/dispositions|qualified5/5 software count|actual8 surfaces and exact fixture records→closed-set validators; absent optional CGB-C excluded|FLOWING|

Core inspection checks whole-block source/destination validation before admission,masked1–128 block bound,widened destination continuation,VBK snapshot per block,finite byte counters,and output/time preflight before progress. Speed-switch/DMA residuals have separate ownership; DMA service precedes IRQ dispatch/new opcode; shared tick explicitly orders OAM→HDMA→PPU. State/lifecycle/stall/partition and fault controls exercise these invariants.

### Behavioral Spot-Checks

| Behavior | Command / selection | Fresh result | Status |
|---|---|---|---|
|state,cancel,HALT,address,lifecycle,resources,competing stalls,partition,steal and fixture execution|`ctest --test-dir build -R '^(cgb_hdma_(state_matrix|state_matrix_controls|guest_steal|guest_steal_no_steal_mutant|guest_steal_no_steal_control|partition_midbyte|partition_controls|address_matrix|address_matrix_controls|lifecycle|lifecycle_controls|competing_stalls|competing_stalls_controls|resource_bounds|resource_bounds_controls|guest_halt)|samesuite_hdma_(gbc_dma_cont|gdma_addr_mask|hdma_lcd_off|hdma_mode0)|magentests_hblank_vram_dma|cgb_hdma_magen_controls)$' --output-on-failure --no-tests=error --parallel 4`|21/21,0.48s,zero skips; partition_controls is unmatched and not counted as an additional executed test|PASS|
|claim consistency|`python3 -I tests/scripts/verify-cgb-hdma-claims.py --native-player` and `--self-test`|8 surfaces;7 claim mutations+3 subject rejections|PASS|
|model/rights/dispositions|`python3 -I tests/scripts/verify-cgb-hdma-dispositions.py --complete` and `--self-test`|5/5 software cases;CGB-C not-run:rights-gate-G1;16 controls|PASS|
|canonical UAT|`python3 -I tests/scripts/verify-uat-closure.py .planning/phases/GB-13-cgb-hdma --self-test`|45 deliverables;19 rejected controls;zero human|PASS|
|lane policy|`python3 -I .planning/phases/GB-13-cgb-hdma/verify-hdma-closure.py --lane` and `--lane-self-test`|6 targets,92core HDMA,2player HDMA,parallel4,timeout45;4 controls|PASS|
|full regression/player|parent fresh configured core/player commands; verifier inspected command logs|1144/1144 and98/98; no repeated full suite by verifier|PASS|

Current full core includes installed consumer/package execution. `13-REFRESH-GATES.md` records additional fresh applicability evidence: source27/27,remote-receipt positive+16 negatives,reproduction self-tests and shell syntax,retained25-threat security and24-task Nyquist coverage. Frozen DMG rows changed:0. All12 bounded task windows reconcile. Canonical13-UAT.md was rewritten/checked with the shared closure checker.

### Prohibition Enforcement / Runtime Compatibility

The sole prohibition prevents author/differential agreement or optional CGB-C evidence being presented as physical CGB-E qualification. Its saved resolved/test/node-test descriptor targets `tests/scripts/cgb-hdma-prohibition.test.cjs`; the adapter invokes the actual claim checker against GSD_PROHIB_SUBJECT or checkout and distinguishes the intended qualification assertion from arbitrary tool failure. Parent executed the actual installed OpenGSD1.18.0 producer using saved descriptor/helper APIs. Verifier inspected its result: **green,flagged:false,located:true,tier:test,kind:node-test**, non-empty **passed:true,failFirst:true,failFirstProof:violation-fixture**, after bad/clean/live execution. All1/1 prohibitions verified; none silently unflagged without enforcement.

The old full closeout/prohibition wrapper pins OpenGSD1.16.0 and rejects1.18.0. It remains **unavailable**, not green; no wrapper/pin was weakened. Direct actual current producer provides prohibition evidence. At immutable completed boundary `e7ba52c81446096a9f6b5bf660d7721ea561eaa4`, original pure handoff_values accepts that commit's STATE/continuation/config and rejects4 stale-route/auto-flag controls. Live historical routes or current-HEAD ancestry are not substituted for those point-in-time facts.

### Historical Evidence and Applicability

13-BENCH.md retains separate receipts at690c081,reviewed0f15a05,published b7b4418,UAT e556c1b,focused consumer eeb1ce9,and local0f1bb34. Previously verified exact-head PR-event receipts at0f15a05:CI38671449176 (8/8;ASan989/989),fixture38671449191 (7/7),preview38671449197 (4/4). At b7b4418:CI38677996444,fixture38677996408,preview38677996566 covered19 successful jobs. These are historical receipts,not fresh GitHub queries or proof of current-head remote readiness.

Pinned fixture provenance,digests and executable software predicates remain covered. Local RGBDS1.0.4 differs from required1.0.1; no fresh local pinned byte rebuild. Historical rebuilds retain source/tool/revision qualifications. Historical shared-mutant/ASan costs retain revision,build,model,workload,digest,sample and uncertainty information; single observations do not establish throughput change. No new sanitizer runtime,host-fuzz campaign,benchmark,hardware,perceptual,hosted or release qualification.

### Probe Execution

No explicit probe-*.sh declared by Phase13 PLAN/SUMMARY files. Required runnable claims,disposition,lane,source,reproduction and closure checks are accounted for here/REFRESH-GATES. No missing required probe.

### Requirements Coverage

| Requirement | Plans | Description | Status | Evidence |
|---|---|---|---|---|
|CGB-07|13-01..13-12|General/HBlank DMA with CPU stall,cancel,HDMA5 readback,HALT,bounded per run|SATISFIED|3 roadmap+34 plan truths,actual guest/state/fault controls,installed consumers/player,45 UAT deliverables/93 verification refs;no orphan Phase13 requirement|

### Anti-Patterns and Retained Debt

Installed scope resolver:resolved,task-commits,71 commits,64 non-planning paths,base8091fb591de7fb68e666be01d344f5f26ebedc5c,no missing/outside/unreachable paths. Verifier scanned current text paths for TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER:zero matches. Inspected core paths are substantive,bounded and connected. Inversion checked false FF55-only success,partial-invalid-block mutation,and lost DMA state across stalls/partitions; consumer disabled twins,mapping matrices and lifecycle/partition controls exercise them. No uncovered software-contract failure was established in this bounded review.

| Concern | Classification | Evidence / disposition |
|---|---|---|
|duplicate core library links|WARNING;retained build debt|Historical warning emitted in current build; accept exports core transitively while AGE/speed targets link it directly. Remains in deferred-items.md; no debt acceptance or false closure.|
|old closeout wrapper|WARNING;tool compatibility limit|1.16.0 pin rejects installed1.18.0; direct actual producer and boundary pure predicate supply narrow evidence; full wrapper remains unavailable.|
|local pinned fixture rebuild|Evidence limit|1.0.4 is not1.0.1; no fresh rebuild assertion; historical qualified receipt and fresh provenance/digest controls retained.|

### Advisory (New Scope, Unevidenced)

No new unevidenced blocker. Existing build warning remains explicit debt.

### Human Verification Required

None for this software contract. Physical CGB-E remains UNKNOWN/POLICY; optional Mealybug CGB-C is rights-gated/not-run/informational,outside5/5 software denominator. D-06/Pan Docs discrepancy,mode3 timing,analog/perceptual output and general-game compatibility remain excluded claims,not invented manual UAT. Exact reviewed-revision remote checks remain merge gates.

### Gaps Summary

All37 truths,49 artifact declarations,12 actual relationships and1 prohibition verified; zero missing/stub artifacts,unverified behaviors,or blocking software gaps. No plan replay,debt acceptance,merge,release or phase advance. Current owner-controlled handoff remains orchestrator-owned.

---

_Verified: 2026-10-20T23:31:32Z_
_Verifier: the agent (gsd-verifier)_
