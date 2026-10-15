---
phase: 13-cgb-hdma
verified: 2026-10-15T03:24:47Z
status: passed
score: 37/37 must-haves verified
covered_files:
  - ".github/workflows/ci.yml"
  - ".github/workflows/fixture-repro.yml"
  - ".github/workflows/preview.yml"
  - ".planning/phases/GB-13-cgb-hdma/13-01-PLAN.md"
  - ".planning/phases/GB-13-cgb-hdma/13-01-SUMMARY.md"
  - ".planning/phases/GB-13-cgb-hdma/13-02-PLAN.md"
  - ".planning/phases/GB-13-cgb-hdma/13-02-SUMMARY.md"
  - ".planning/phases/GB-13-cgb-hdma/13-03-PLAN.md"
  - ".planning/phases/GB-13-cgb-hdma/13-03-SUMMARY.md"
  - ".planning/phases/GB-13-cgb-hdma/13-04-PLAN.md"
  - ".planning/phases/GB-13-cgb-hdma/13-04-SUMMARY.md"
  - ".planning/phases/GB-13-cgb-hdma/13-05-PLAN.md"
  - ".planning/phases/GB-13-cgb-hdma/13-05-SUMMARY.md"
  - ".planning/phases/GB-13-cgb-hdma/13-06-PLAN.md"
  - ".planning/phases/GB-13-cgb-hdma/13-06-SUMMARY.md"
  - ".planning/phases/GB-13-cgb-hdma/13-07-PLAN.md"
  - ".planning/phases/GB-13-cgb-hdma/13-07-SUMMARY.md"
  - ".planning/phases/GB-13-cgb-hdma/13-08-PLAN.md"
  - ".planning/phases/GB-13-cgb-hdma/13-08-SUMMARY.md"
  - ".planning/phases/GB-13-cgb-hdma/13-09-PLAN.md"
  - ".planning/phases/GB-13-cgb-hdma/13-09-SUMMARY.md"
  - ".planning/phases/GB-13-cgb-hdma/13-10-PLAN.md"
  - ".planning/phases/GB-13-cgb-hdma/13-10-SUMMARY.md"
  - ".planning/phases/GB-13-cgb-hdma/13-11-PLAN.md"
  - ".planning/phases/GB-13-cgb-hdma/13-11-SUMMARY.md"
  - ".planning/phases/GB-13-cgb-hdma/13-12-PLAN.md"
  - ".planning/phases/GB-13-cgb-hdma/13-12-SUMMARY.md"
  - ".planning/phases/GB-13-cgb-hdma/13-ASAN-ADDED-COST.json"
  - ".planning/phases/GB-13-cgb-hdma/13-BENCH.md"
  - ".planning/phases/GB-13-cgb-hdma/continue.md"
  - ".planning/phases/GB-13-cgb-hdma/verify-hdma-closure.py"
  - ".planning/phases/GB-13-cgb-hdma/verify-hdma-source-revision.py"
  - "README.md"
  - "cmake/ExpectedTests.cmake"
  - "cmake/GabbaBoyConfig.cmake.in"
  - "cmake/P12Mutants.cmake"
  - "cmake/P13Mutants.cmake"
  - "cmake/PreviewPackageSmoke.cmake"
  - "cmake/RunInstalledConsumer.cmake"
  - "cmake/ScanForbiddenFixtures.cmake"
  - "cmake/VerifyInstalledPackage.cmake"
  - "docs/cgb-profile.md"
  - "docs/model-gates.md"
  - "docs/native-integration.md"
  - "docs/preview.md"
  - "docs/support/unreleased.md"
  - "fixtures/cgb-hdma/LICENSE.txt"
  - "fixtures/cgb-hdma/hblank.asm"
  - "fixtures/cgb-hdma/hblank.gb"
  - "fixtures/cgb-hdma/manifest.json"
  - "fixtures/magentests/ELIGIBILITY.md"
  - "fixtures/magentests/SOURCES.md"
  - "fixtures/magentests/hblank_vram_dma.gbc"
  - "fixtures/magentests/manifest.json"
  - "fixtures/samesuite/ELIGIBILITY.md"
  - "fixtures/samesuite/LICENSE.txt"
  - "fixtures/samesuite/gbc_dma_cont.gb"
  - "fixtures/samesuite/gdma_addr_mask.gb"
  - "fixtures/samesuite/hdma_lcd_off.gb"
  - "fixtures/samesuite/hdma_mode0.gb"
  - "fixtures/samesuite/manifest.json"
  - "src/core/gabbaboy.c"
  - "src/player/limitations.h"
  - "src/player/main.c"
  - "tests/CMakeLists.txt"
  - "tests/acceptance/CMakeLists.txt"
  - "tests/cgb_consumer_symbol_coverage.cmake"
  - "tests/consumers/c/CMakeLists.txt"
  - "tests/consumers/c/main.c"
  - "tests/consumers/cpp/CMakeLists.txt"
  - "tests/consumers/cpp/main.cpp"
  - "tests/expected-tests.txt"
  - "tests/external/cgb-hdma-dispositions.json"
  - "tests/external/cgb-speed-dispositions.json"
  - "tests/fuzz_core.c"
  - "tests/player/CMakeLists.txt"
  - "tests/player/cgb_smoke.cmake"
  - "tests/player/claims_agree.cmake"
  - "tests/player/expected-tests.txt"
  - "tests/scripts/cgb-hdma-prohibition.test.cjs"
  - "tests/scripts/phase13-handoff-continuity.test.cjs"
  - "tests/scripts/reproduce-cgb-hdma.sh"
  - "tests/scripts/reproduce-magentests.sh"
  - "tests/scripts/reproduce-samesuite.sh"
  - "tests/scripts/test_hdma_remote_evidence.py"
  - "tests/scripts/verify-cgb-hdma-claims.py"
  - "tests/scripts/verify-cgb-hdma-dispositions.py"
  - "tests/test_cgb_hdma.c"
  - "tests/test_cgb_hdma_internal.c"
  - "tests/test_cgb_hdma_partition.c"
  - "tests/test_cgb_partition.c"
  - "tests/test_cgb_speed_internal.c"
  - "tests/test_cgb_visibility.c"
  - "tests/test_magentests.c"
  - "tests/test_samesuite_hdma.c"
covered_digest: "v3:sha256:ffff572c9cd25c8c6f516f21738c174dc849f81671e6f180010496565aaf6fcf"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 36/37
  gaps_closed:
    - "Exact-current-revision hosted ASan/UBSan and fixture-reproduction evidence for D-21."
  gaps_remaining: []
  regressions: []
---

# Phase 13: CGB HDMA Verification Report

**Phase Goal:** CGB software can use general-purpose and HBlank VRAM DMA with hardware-shaped CPU stall, cancel and readback, bounded per run.
**Verified:** 2026-10-15T03:24:47Z
**Status:** passed
**Re-verification:** Yes — after exact-head evidence closure

## Goal Achievement

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
| 17 | D-21: Mutation compilation stays bounded and ASan/native cost is measured with existing parallelism/timeouts. | ✓ VERIFIED | `13-BENCH.md` records bounded mutant cost and the exact-head Linux ASan/UBSan inventory at `0f15a05`: 989/989, no skips, with 96 added cases totaling 16.86 s; parallelism/timeouts are unchanged. |
| 18 | D-24: Migrated P12 anchors remain unique and disposition semantics retain sensitivity. | ✓ VERIFIED | Anchor guard, disposition positive/mutated cases, and inherited CGB speed disposition tests pass in fresh native/player reports. |
| 19 | D-16: Exactly gbc_dma_cont, gdma_addr_mask, hdma_lcd_off and hdma_mode0 are admitted at f15645fb049a47ea235f6d2c9a033e72d8087901 with X11/G7 and CC0 closure. | ✓ VERIFIED | Four pinned SameSuite manifest rows, license/source/tool/digest checks and named execution tests pass; manifest, eligibility and rebuild script are connected by CTest. |
| 20 | D-02/D-21/D-22: Existing pinned RGBDS1.0.1 and fixture-repro lane reproduce exact bytes, rejecting tampered pins/rows/digests without new dependencies or jobs. | ✓ VERIFIED | Fixture manifests and reproduction scripts enforce exact pins and negative controls; exact reviewed head `0f15a05` passed the PR-event fixture-reproduction workflow 7/7, including the admitted HDMA fixtures. |
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
| 34 | D-21: Existing native/sanitizer/reproduction/consumer/package lanes run an exact inventory with measured added ASan and mutant cost and unchanged parallel4/timeout policy. | ✓ VERIFIED | GitHub API confirms all jobs completed successfully on exact reviewed behavior head `0f15a05`: CI 8/8 (ASan/UBSan 989/989 with no skips), fixture reproduction 7/7, and preview package 4/4. The source/test/fixture/build/workflow diff from freshly tested `3cdcef2` to `0f15a05` is empty; run IDs and measured costs are recorded in `13-BENCH.md`. |
| 35 | D-18/D-22: The claim-language prohibition is machine-proven fail-first and resolves green/unflagged through the actual OpenGSD gate before verify-work; physical UNKNOWN is preserved. | ✓ VERIFIED | Actual OpenGSD producer clean, violating-subject RED and live GREEN evidence is recorded; projection/gate tests and negative controls pass; CGB-E remains UNKNOWN/POLICY. |
| 36 | D-22/D-24: Current-revision evidence and machine-readable coverage qualify all delivered claims; skipped/stale remote checks cannot prove the revision green. | ✓ VERIFIED | `13-BENCH.md` binds local evidence to `3cdcef2`, records successful exact-head runs at `0f15a05`, and states that later metadata heads need their own checks; closure checker rejects skipped/stale results and machine-readable coverage passes. |
| 37 | D-25: Planning stops before execution; after Phase13 execution/verification the durable route is Phase14 CGB-E Model Qualification and Corpus, never auto-advanced. | ✓ VERIFIED | Continuation now records the completed Phase 13 execution/verification stage, exact automated-UAT command, and Phase 14 as unstarted; the handoff contract passes both its live and completed-stage controls, with auto flags false. |

**Score:** 37/37 truths verified (0 present, behavior-unverified).

### Exact-Head Hosted Evidence

GitHub API results show `pull_request`, `completed`, `success`, and exact head `0f15a05c30a30a0a73b5227906b648e85ae7a280` for all three runs. Every job in each run completed successfully:

| Workflow run | Jobs | Relevant evidence |
|---|---:|---|
| [CI 38671449176](https://github.com/szTheory/gabbaboy/actions/runs/38671449176) | 8/8 | Linux ASan/UBSan 989/989, zero skips, 624.45 s; macOS native 994, Linux native 994, Windows native 982; CMake floor base 989 and relocated install 994; player gate, player package and required-native succeeded. |
| [Fixture reproduction 38671449191](https://github.com/szTheory/gabbaboy/actions/runs/38671449191) | 7/7 | Pinned fixture rebuild and byte-comparison jobs succeeded, including SameSuite and MagenTests. |
| [Preview package 38671449197](https://github.com/szTheory/gabbaboy/actions/runs/38671449197) | 4/4 | Linux/macOS installed-package and consumer smoke, downloaded macOS player package, and aggregate preview gate succeeded. Player package SHA-256: `c9165786b9c1f5cb09644cfaab82cdea2a2f0436706178886263ee223f9ce747`. |

The 96 added sanitizer cases total 16.86 seconds in this single run; uncertainty remains unquantified. Detailed measurements and run identities are in [13-BENCH.md](13-BENCH.md) and [13-ASAN-ADDED-COST.json](13-ASAN-ADDED-COST.json). This closes D-21 at the reviewed behavior revision. The later report/continuation metadata head has not yet been published and retains its own exact-head CI requirement before merge.

## Required Artifacts

The installed artifact verifier checked all plan-declared artifacts: 49/49 passed across the twelve plans. The key implementations are substantive and used by their registered callers/tests. `query verify.key-links` returned “Target not referenced in source” for each generic plan edge; manual source, fixture, CMake, and consumer tracing below confirms the actual links rather than treating that generic matcher result as proof of a broken implementation. Behavioral closure includes the exact-source revision validator and its 26 controls, the hosted-receipt validator with one positive and 16 negative controls, and the live Node handoff test. Installed consumer CMake glue and CI inventory wiring are included in the covered set.

| Artifact group | Status | Details |
|---|---|---|
| `src/core/gabbaboy.c` DMA state, register policy, scheduler and memory mapping | ✓ VERIFIED | Substantive core logic, exercised by internal matrices and CPU-programmed guests. |
| `tests/test_cgb_hdma*.c`, guest/partition/Magen/SameSuite tests | ✓ VERIFIED | Registered native/player tests, assertions inspect guest-visible data/state/time, with paired negative controls. |
| `cmake/P13Mutants.cmake`, `tests/CMakeLists.txt`, expected inventories | ✓ VERIFIED | Mutation variants and test inventory are built/registered; native/player suites reconcile with reports. |
| SameSuite and Magen manifests, fixture sources/ROMs, reproduction scripts | ✓ VERIFIED | Pins, licensing, generated-byte digests and admission boundaries are checked by existing fixture tests. |
| `tests/consumers/{c,cpp}/main.*` and installed package checks | ✓ VERIFIED | Both installed consumers execute guest DMA through public functions; package report passes 6/6. |
| Player smoke and claim surfaces | ✓ VERIFIED | Existing player smoke validates source-derived visible pattern and no-transfer control; claim mirrors have mutation controls. |
| `13-BENCH.md`, `13-ASAN-ADDED-COST.json`, `verify-hdma-closure.py` and `verify-hdma-source-revision.py` | ✓ VERIFIED | Exact-head evidence and closure artifacts are substantive; revision controls reject stale source evidence, and BENCH distinguishes the tested behavior revision from later metadata-head gates. |
| `tests/scripts/test_hdma_remote_evidence.py` and `tests/scripts/phase13-handoff-continuity.test.cjs` | ✓ VERIFIED | Remote-receipt validator controls use a constructed positive receipt and 16 synthetic negatives; the live Node handoff test passes 2/2 for execution and completed-stage routes. Actual GitHub API evidence is recorded separately in `13-ASAN-ADDED-COST.json`. |
| `cmake/ExpectedTests.cmake`, installed-consumer CMake glue and `.github/workflows/ci.yml` | ✓ VERIFIED | Required inventories and relocated C/C++ consumers are registered; exact-head CI and package jobs pass. |

## Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `src/core/gabbaboy.c` | `tests/test_cgb_hdma_internal.c` | CMake internal test target | ✓ WIRED | Test target compiles against test core; fresh native and player JUnit include state/timing/address matrices and controls. |
| `src/core/gabbaboy.c` | `tests/test_cgb_hdma_internal.c` | bounded transfer predicate | ✓ WIRED | Internal fixtures inspect real transfer state and source/destination effects. |
| `src/core/gabbaboy.c` | `tests/test_cgb_hdma.c` | public guest target | ✓ WIRED | CPU guest writes FF registers and checks data, banks, timing, HALT/steal behavior. |
| `tests/test_cgb_hdma_partition.c` | `tests/test_cgb_partition.c` | inherited partition harness | ✓ WIRED | Reuses partition harness and validates continuity, hidden state and output cuts; tests pass. |
| `src/core/gabbaboy.c` | `cmake/P13Mutants.cmake` | generated mutant test core | ✓ WIRED | CMake creates mutation core and named mutant/control cases; these appear and pass in full suites. |
| `fixtures/samesuite/manifest.json` | `fixtures/samesuite/LICENSE.txt` | source/license/pin checks | ✓ WIRED | Manifest license/source admission is enforced by test scripts and four SameSuite cases are executed. |
| `fixtures/magentests/hblank_vram_dma.gbc` | `fixtures/magentests/manifest.json` | digest/source eligibility | ✓ WIRED | Manifest validation and rebuild checks gate the Magen test target. |
| `fixtures/cgb-hdma/hblank.asm` | `fixtures/cgb-hdma/hblank.gb` | pinned guest build | ✓ WIRED | Original assembly source, license and manifest digest are checked against the guest fixture. |
| `tests/test_samesuite_hdma.c` | `tests/external/cgb-hdma-dispositions.json` | executed-case dispositions | ✓ WIRED | Test cases and disposition checks agree; pending/absent data cannot count as a pass. |
| `tests/consumers/c/main.c` | `tests/consumers/cpp/main.cpp` | parallel installed consumers | ✓ WIRED | Not a direct call between files: each is separately wired to the installed library and tests the same inline guest/API contract. |
| `docs/native-integration.md` | `docs/support/unreleased.md` | public API/support claim agreement | ✓ WIRED | Cross-surface contract checks agree on API and qualified behavior. |
| `tests/scripts/cgb-hdma-prohibition.test.cjs` | `13-BENCH.md` | evidence and gate closure | ✓ WIRED | CTest and actual installed OpenGSD gate run RED/clean/live checks; exact-head hosted run identities are recorded in BENCH. |
| `verify-hdma-source-revision.py` | `13-BENCH.md` | source identity / tree-delta contract | ✓ WIRED | Closure runs 26 source-revision controls; the diff from tested `3cdcef2` to exact CI head `0f15a05` is empty for source, test, fixture, build and workflow files. |
| `tests/scripts/test_hdma_remote_evidence.py` | `.planning/phases/GB-13-cgb-hdma/verify-hdma-closure.py::validate_remote_evidence` | constructed positive and negative receipts | ✓ WIRED | The registered control driver validates its synthetic receipt fixtures: one positive and 16 negative controls. It tests the validator contract; it does not fetch GitHub or consume the committed API evidence. |
| `.planning/phases/GB-13-cgb-hdma/13-ASAN-ADDED-COST.json::post_review_hosted_evidence` | `.planning/phases/GB-13-cgb-hdma/13-ASAN-ADDED-COST.json::optional_validator_receipt` | GitHub API run/job/event/head records normalized to the validator schema | ✓ VERIFIED | The committed raw run records include all job outcomes for the three exact-head PR runs; the adjacent normalized receipt records the three authoritative contexts. The strict validator accepted this receipt and rejected its failed-result twin. |
| `tests/scripts/phase13-handoff-continuity.test.cjs` | `continue.md` / `verify-hdma-closure.py` | live and completed-stage handoff | ✓ WIRED | Direct Node test passed 2/2 after the continuation update; it checks the live route, completed-stage route, phase pause and invalid-stage control. |
| `tests/consumers/{c,cpp}/CMakeLists.txt` | `cmake/RunInstalledConsumer.cmake` / `cmake/VerifyInstalledPackage.cmake` | relocated installed consumers | ✓ WIRED | Preview run `38671449197` passed 4/4 jobs; CI run `38671449176` passed all 8, including the CMake-floor relocated inventory. |

## Data-Flow Trace (Level 4)

| Artifact | Data variable | Source | Produces real data | Status |
|---|---|---|---|---|
| DMA transfer core | source bytes / destination VRAM | guest-addressed cartridge/WRAM reads through `cart_read` and `wram_byte`; writes through current VRAM bank | Yes | ✓ FLOWING |
| Guest and partition tests | guest-visible memory, FF55/state, timestamps | actual CPU-executed register writes and reads against the core | Yes | ✓ FLOWING |
| Original visible fixture/player smoke | rendered pattern and guest status | fixture CPU program and source-derived framebuffer pixels | Yes | ✓ FLOWING |
| Magen/SameSuite fixtures | ROM guest output/readback | pinned third-party test ROMs through fixture harness | Yes | ✓ FLOWING |

## Behavioral Spot-Checks

The full fresh-source regression evidence is from source `3cdcef2831ae71564b75186e976296275f59b68d`: native 994/994, player 1087/1087, relocated installed consumers/package 6/6; each report has zero failures, errors, or skips. JUnit files and hashes are identified in `13-BENCH.md`. Focused named tests passed during verification:

| Behavior | Check | Result | Status |
|---|---|---|---|
| HALT during active DMA | `cgb_hdma_guest_halt` | PASS | ✓ PASS |
| CPU steal discriminator | `cgb_hdma_guest_steal` | PASS | ✓ PASS |
| Partition cut in the middle of a block | `cgb_hdma_partition_midbyte` | PASS | ✓ PASS |
| Cancel/readback/lifecycle state | `cgb_hdma_state_matrix` | PASS | ✓ PASS |
| Source/destination address policy | `cgb_hdma_address_matrix` | PASS | ✓ PASS |
| LCD-off SameSuite behavior | `samesuite_hdma_hdma_lcd_off` | PASS | ✓ PASS |
| Magen HBlank DMA result | `magentests_hblank_vram_dma` | PASS | ✓ PASS |

## Probe Execution

No `probe-*.sh` files were found or declared by the Phase 13 plans/summaries; no phase probe required execution.

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| CGB-07 | 13-01 through 13-12 | General-purpose and HBlank VRAM DMA with bounded runs, CPU stalls, cancellation/readback, HALT, mapping and qualified model behavior | ✓ SATISFIED | All observable behavior criteria pass in code, fresh local tests and exact-reviewed-head hosted CI; all 209 machine-readable coverage entries pass. No additional Phase 13 requirement is orphaned. |

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---:|---|---|---|
| — | — | No unreferenced TBD/FIXME/XXX, TODO/HACK/PLACEHOLDER, or empty implementation patterns found in phase-modified files. | — | No anti-pattern blocker. |

## Human Verification Required

None. Physical CGB-E qualification is deliberately UNKNOWN/POLICY and outside this phase's software evidence claim; optional CGB-C Mealybug data is rights-gated, not run, informational only, and outside the CGB-E denominator. The reviewed behavior revision has the required automated lane evidence. The final report/continuation metadata head still needs its own exact-head checks before merge, per the project handoff contract.

## Gaps Summary

All 37 merged roadmap and plan truths are verified. Current-source native, player, installed-consumer, SameSuite, Magen, HALT, cancellation, address, and partition checks pass; exact reviewed behavior head `0f15a05` also passes the required CI, fixture-reproduction, and preview-package jobs. The final report/continuation metadata head remains subject to its own exact-head CI before merge. Physical CGB-E remains UNKNOWN/POLICY, and no Mealybug CGB-C bytes were fetched.

---

_Verified: 2026-10-15T03:24:47Z_
_Verifier: the agent (gsd-verifier)_
