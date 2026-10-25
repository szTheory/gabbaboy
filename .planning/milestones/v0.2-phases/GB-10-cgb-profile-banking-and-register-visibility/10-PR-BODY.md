## Phase 10: CGB profile, banking and register visibility

Adds the `GBB_PROFILE_CGB_CPU_E` profile with CGB and DMG-compatibility execution modes, VRAM (2x8 KiB) and WRAM (8x4 KiB) banking, a per-cell register visibility matrix for DMG, CGB and CGB-in-compat, a model-gate audit of the core (`docs/model-gates.md`, scanner `tests/scripts/verify-model-gates.py`), original banking fixtures, four CGB Mooneye derivatives and a half-dot timeline ADR for the later double-speed work. There is no CGB colour, no double speed and no HDMA yet; none of this is game-compatibility evidence.

The DMG profile stays byte-identical to the v0.1 baseline: `tests/baseline` is unchanged, the frozen tracer digest `correctness_digest_fnv1a64=4c7a57ff3d50d228` still holds, and no line was removed from `tests/expected-tests.txt` (541 executed cases locally, none skipped).

### Owner veto items (veto window: before this PR merges)

1. **`gbb_info` ABI and `struct_size` convention (D-02).** One sized, fixed-width info struct shared by probe and instance, appended to the public header; callers set `struct_size` so later fields can be added.
2. **PGB rejection with `GBB_UNSUPPORTED_EXECUTION_MODE` (D-03).** Header `$143` bits 2-3 (PGB) are rejected on every profile; bit 6 is ignored as on hardware.
3. **`gbb_copy_frame` returns `GBB_UNSUPPORTED_PROFILE` on the CGB profile (D-05).** Until Phase 11 defines colour output. This is the only change to an existing function and is scoped to the new profile.
4. **DMG FF4C-FF7F kept fail-closed (D-09).** The DMG profile row is unchanged and keeps stopping with `GBB_STOP_UNSUPPORTED_BUS`; reading them as `$FF` (and so admitting `unused_hwio-GS`) is deferred.
5. **+5% benchmark review trigger, and it fired (D-22).** The advisory A/B (`10-BENCH.md`, interleaved pairs, 30 samples, Apple M5 Pro, Release, digest verified on every run) puts Phase 10 at 105.6 to 107.3 percent of the frozen Phase 7 baseline across three headline runs, i.e. roughly 6 to 7 percent slower on the DMG hot path from the per-access bank indirection. Against the Phase 9 head the median is 100.67 (within noise) but min-of-n is 103.5, so the cost cannot be split between phases. The host was loaded (load average about 10), per-pair SD was 9 to 11 percent, and no hosted timing was collected; treat it as advisory. No optimisation was done in this PR. The owner decides whether it warrants performance work (DECISIONS D-016).
6. **IE bits 5-7 stored on the CGB profile only (OQ2, D-071).** The DMG profile keeps `ie & $1F` with bits 5-7 reading 1; dispatch masks with `$1F` on both.

**D-29 judgement.** The API additions are one profile value, two enums, five flag bits, one struct, two functions and one error code, all appended, plus the one scoped change in item 3. Nothing changes on `GBB_PROFILE_DMG_CPU_B`. As with Phase 9 D-17 this is treated as append-only and auto-followed; the owner may veto before merge.

### Requirement to evidence

Evidence head: `d260a7dec5af333d79ff1b698382a9399ee8f11b` (pull_request-event runs: [ci 38315850467](https://github.com/szTheory/gabbaboy/actions/runs/38315850467), [fixture-repro 38315850478](https://github.com/szTheory/gabbaboy/actions/runs/38315850478), [preview-package-smoke 38315850473](https://github.com/szTheory/gabbaboy/actions/runs/38315850473), success on attempt 2 after its 1500 s wait for `ci` expired). Earlier evidence head `2fe078e8f08ed98ba0ac0e244971e7c0ead16b1e` ([ci 38299323863](https://github.com/szTheory/gabbaboy/actions/runs/38299323863)) predates the review fixes.

Execute-phase tail (after the first evidence head): Nyquist validation `validated`/`nyquist_compliant: true` (4 gaps filled, new `cgb_fuzz_profile_select`); security 33/33 threats closed, `threats_open: 0` (10-SECURITY.md); code review 0 critical / 4 warning / 5 info, 8 fixed and 1 no-change (10-REVIEW-DISPOSITION.md); regression gate 541/541 CTest with installed inventory, `baseline status=pass`, model gates pass, macOS player package gate passed; gsd-verifier `passed` 4/4 (10-VERIFICATION.md). One more CI defect was fixed: the Windows inventory script now also skips the bash-only `cgb_mooneye_repro_requires_manifest`.

| Requirement | Evidence | Class |
|---|---|---|
| CGB-01 profile, probe, info, modes, post-boot | `cgb_probe_*`, `cgb_postboot_*` (including `cgb_postboot_dmg_pin` and its flipped/checksum controls), `cgb_cgb_only_on_dmg`, `cgb_runner_profile_*`, `cgb_mooneye_case_boot_regs-cgb`, `cgb_mooneye_case_boot_div-cgbABCDE` | Regression and differential; the two Mooneye ROMs are author-attested hardware results (`boot_div` applies to CGB A-E only); CGB post-boot cells are Pan Docs, SameBoy or policy, not hardware observation |
| CGB-02 model-gate audit, visibility matrix, KEY0 lock | `verify-model-gates.py` (147 functions, 76 gates, 40 unknown; no `research:10` tag line left), `cgb_visibility_matrix_{dmg,cgb,compat}` plus sweep/flip/deferred controls, `cgb_key0_lock_*` | Static audit plus per-cell tests with negative controls |
| CGB-03 VRAM/WRAM banking, echo RAM, OAM DMA sources | `banking_*` (metamorphic flat-reference, echo and DMA mutants with controls), `cgb_banking_guest_{cgb,compat,dmg}`, `cgb_banking_fixture_digest`, `banking_bus_conflict_cgb_pin` | Original-fixture regression plus metamorphic; no hardware oracle for the CGB DMA bus (expected failure `cgb-separate-buses`) |

Exact-head required checks (all success at the evidence head): native-linux-x64, native-macos-arm64, native-windows-x64, linux-asan-ubsan, cmake-floor-3.25.3, player-gate, macos-player-package, required-native. Fixture reproduction (all success): fixture-repro (CGB banking `result=byte-identical roms=2`), mooneye-original-repro, mooneye-candidate-repro, mooneye-mbc-repro, magentests-repro, rtc3test-repro, mooneye-cgb-repro (`result=byte-identical roms=4`). Local: 541/541 CTest, inventory verified, macOS player package gate passed. The `phase1-asan` preset cannot be configured on the macOS author host (Linux-only); sanitizer evidence is the hosted `linux-asan-ubsan` job.

### Verification

`/gsd-verify-work 10` passed: 12/12 UAT items automated, no human checkpoint (`10-UAT.md`); local 541/541 CTest with the installed inventory, `baseline status=pass`, model gates pass; verification `passed` 4/4, `threats_open: 0`.

### Deferred and limitations

Deferred (see `.planning/context/FUTURE-MILESTONES.md`): DMG FF4C-FF7F `$FF` and `unused_hwio-GS`; a CGB CPU/DMA separate-bus model; DMG OAM DMA sources E0-FF and ROM sources; RP/IR and FF76/FF77; AGE `ly-cgbE` and `lcd-align-ly-cgbE`; an instruction-count benchmark proxy; flipping `boot_hwio-C` and `unused_hwio-C` (both expected-unsupported, stop at FF76) to pass; release-mode model gates.

Limits: no CGB colour, no double speed, no HDMA; deferred registers fail closed; two Mooneye ROMs are expected-unsupported and not counted as passes; no commercial game or boot ROM is involved.

Two CI defects were found at the first push and fixed within this PR: the CGB banking ROMs were on disk but matched the `*.gb` ignore rule (added explicit admissions; bytes unchanged and equal to the manifest digests), and the Windows inventory check did not mirror the CMake exclusion of the bash-only `cgb_bench_ab_*` controls.

This PR stays open until `/gsd-verify-work 10` passes; the squash merge happens only afterwards at an exact-head green head.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
