---
phase: "17"
slug: "native-save-state-core"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-26"
---

# Phase 17 — Validation Strategy

This is a planning contract. New tests and implementation are pending; no state qualification is claimed.

## Test Infrastructure

| Property | Value |
|----------|-------|
| Framework | Existing C17/C++ compiled consumers, CTest, Python checker self-tests, Clang sanitizer/libFuzzer lanes |
| Config file | CMakePresets.json; tests/CMakeLists.txt; tests/cmake/areas.cmake; tests/expected-tests.txt |
| Quick run command | Plan-specific named CTests with `--output-on-failure --no-tests=error`, after configure/build |
| Full suite command | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` |
| Runtime | Measure during execution; do not infer acceptance from duration or run counts |

## Sampling Rate

- Every task runs its focused positive and intended negative controls before its commit.
- Every wave runs the changed integration paths and existing budget/inventory checks.
- Run the full suite once at the final source head, followed by exact-revision hosted checks required for merge; re-run only when later changes invalidate evidence.
- Reuse existing platform, package, sanitizer and fuzz jobs. Planning-only CI does not establish implementation qualification.

## Per-Task Verification Map

All32 task rows are pending creation/execution. Commands assume checkout root and proven build/build-asan layout. New tests/CLI names are created and registered with timeout/expected inventory in the owning task. No passing implementation evidence is claimed.

| Task | Exact automated command | Intended failing signal | Threat Ref | Status |
|---|---|---|---|---|
| 17-01.1 | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --test-dir build -R '^(preview_package_smoke&#124;state_(inventory&#124;inventory_controls&#124;globals&#124;globals_controls&#124;size_bound&#124;audio_bound&#124;precodec_gate))$' --output-on-failure --no-tests=error` | Any inventory/nm/proof/control/package test is absent or nonzero; an unclassified member/global/oversized field/widened audio domain survives; proof receipt predates actual successful executable evidence or binds different descriptor inputs. | T-17-01,T-17-02,T-17-03 | pending |
| 17-01.2 | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --test-dir build -R '^state_precodec_gate$' --output-on-failure --no-tests=error && ctest --test-dir build -R '^state_(size_bound&#124;audio_bound&#124;format_contract&#124;tracer)$' --output-on-failure --no-tests=error` | Pre-codec gate/receipt is missing, stale or nonzero before the first acceptance; installed symbols do not link; future continuation/canonical bytes differ; version truncation or no-op restore survives. | T-17-01,T-17-02,T-17-03 | pending |
| 17-01.3 | `cmake --preset phase1 -DCMAKE_INSTALL_PREFIX="$PWD/build/state-prefix" && cmake --build --preset phase1 && cmake --install build && test -f build/state-prefix/include/gabbaboy/gabbaboy.h && cmake --preset phase1 -DGBB_TEST_INSTALL_PREFIX="$PWD/build/state-prefix" && ctest --test-dir build -R '^(installed_consumer_(c&#124;cpp)&#124;preview_package_smoke&#124;state_tracer)$' --output-on-failure --no-tests=error` | Install fails to create actual header/exported library, an installed symbol/call is missing, old errors renumber, or poisoned buffer/tail and future continuation differ. | T-17-01,T-17-02,T-17-03 | pending |
| 17-02.1 | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --test-dir build -R '^state_(identity&#124;codec_matrix&#124;tracer)$' --output-on-failure --no-tests=error` | Wrong ROM/token/mode is accepted; failed load changes identity; per-call hash occurs; any mode/mapper cannot continue; a CRC collision aliases identity. | T-17-04,T-17-05 | pending |
| 17-02.2 | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --test-dir build -R '^state_(canonical&#124;semantic_bounds&#124;identity&#124;audio_bound&#124;size_bound)$' --output-on-failure --no-tests=error` | A semantic-invalid fixture passes, resave changes any accepted byte, a width/endian/override mutant survives, or a declared relationship has no consuming-code bound. | T-17-04,T-17-05 | pending |
| 17-03.1 | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --test-dir build -R '^state_(observers&#124;rtc_palette&#124;tracer)$' --output-on-failure --no-tests=error` | Future output differs, host clock/catch-up fires, raw state normalizes, projected equal bytes bump counters, changed bytes do not bump exactly once, or saturation wraps. | T-17-06,T-17-07,T-17-08 | pending |
| 17-03.2 | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --test-dir build -R '^state_(refusal&#124;refusal_controls&#124;semantic_bounds)$' --output-on-failure --no-tests=error` | Any refused operation changes one destination/output byte, compound errors choose the wrong code, short headers read beyond their size, or premature-apply survives. | T-17-06,T-17-07,T-17-08 | pending |
| 17-03.3 | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --test-dir build -R '^state_(purity&#124;purity_controls&#124;globals&#124;globals_controls)$' --output-on-failure --no-tests=error` | Any call allocates/hashes, size/save mutates instance/RAM, independent instances interfere, or an instrumented defect goes undetected. | T-17-06,T-17-07,T-17-08 | pending |
| 17-04.1 | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --test-dir build -R '^state_(horizon&#124;horizon_wrappers&#124;horizon_sentinels)$' --output-on-failure --no-tests=error` | Any wrapper crosses the cap, over-cap load succeeds, an atomic operation partially advances, legitimate sentinel refuses, or post-run state cannot reload. | T-17-09,T-17-10,T-17-11 | pending |
| 17-04.2 | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --test-dir build -R '^state_(horizon_events&#124;horizon_closure&#124;canonical&#124;audio_bound)$' --output-on-failure --no-tests=error` | cap+1 event/span is admitted, rejected admission changes state/queue, equal-time order changes, or a legal run exits the accepted save/load domain. | T-17-09,T-17-10,T-17-11 | pending |
| 17-04.3 | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --test-dir build -R '^state_horizon_(mutants&#124;mutant_controls)$' --output-on-failure --no-tests=error` | Any independent guard survives, a mutation never executes, unrelated control fails, or harness accepts compile failure as a kill. | T-17-09,T-17-10,T-17-11 | pending |
| 17-05.1 | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --test-dir build -R '^state_(fork_matrix&#124;slice_invariance)$' --output-on-failure --no-tests=error` | Any eligible corpus entry is omitted, target is not fresh/poisoned, later frame/sample/result differs, or slice-only comparison is presented as fork proof. | T-17-12,T-17-13 | pending |
| 17-05.2 | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --test-dir build -R '^state_fork_(census&#124;census_controls)$' --output-on-failure --no-tests=error` | Any required category/field lacks a witnessed non-default discriminator or justified tested treatment, or a seeded missing-category report passes. | T-17-12,T-17-13 | pending |
| 17-05.3 | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --test-dir build -R '^state_fork_(mutants&#124;mutant_controls)$' --output-on-failure --no-tests=error` | A declared field drop survives, fixture never exercises its field, wrong discrepancy/control is counted as kill, or missing mutant is ignored. | T-17-12,T-17-13 | pending |
| 17-06.1 | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --test-dir build -R '^state_(portable_pins&#124;pin_controls&#124;codec_matrix)$' --output-on-failure --no-tests=error` | Emitted bytes differ from pins, altered pin survives, base/disposition/token binding is absent, or platform-specific metadata enters bytes. | T-17-14,T-17-15,T-17-16 | pending |
| 17-06.2 | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --test-dir build -R '^state_(load_fuzz&#124;fuzz_controls&#124;horizon_closure)$' --output-on-failure --no-tests=error && bash tests/scripts/run-bounded-fuzz.sh --self-test` | State target is absent from real campaign, no semantic witness appears, refused bytes mutate, accepted resave/closure fails, or omission/shallow target control passes. | T-17-14,T-17-15,T-17-16 | pending |
| 17-06.3 | `python3 -I .github/scripts/verify-workflow-policy.py --check && python3 -I .github/scripts/verify-workflow-policy.py --self-test && cmake --preset phase1 -DCMAKE_INSTALL_PREFIX="$PWD/build/state-prefix" && cmake --build --preset phase1 && cmake --install build && test -f build/state-prefix/include/gabbaboy/gabbaboy.h && cmake --preset phase1 -DGBB_TEST_INSTALL_PREFIX="$PWD/build/state-prefix" && ctest --test-dir build -R '^(state_portable_pins&#124;installed_consumer_(c&#124;cpp)&#124;preview_package_smoke)$' --output-on-failure --no-tests=error` | A native OS/consumer/state-fuzz lane is unbound/omitted, workflow-policy mutation survives, or hosted claims name a different head. | T-17-14,T-17-15,T-17-16 | pending |
| 17-07.1 | `python3 -I tests/scripts/verify-v02-performance.py --self-test && cmake --preset phase1 && ctest --test-dir build -R '^perf_advisory_(pipeline&#124;controls)$' --output-on-failure --no-tests=error` | Triggered valid receipt blocks/pends/requires review, producer/verifier schema disagrees, or malformed/unbound evidence succeeds. | T-17-17,T-17-18 | pending |
| 17-07.2 | `python3 -I tests/scripts/verify-perf-gate.py --self-test && cmake --preset phase1 && ctest --test-dir build -R '^(perf_limit_ratchet&#124;perf_repeat_controls&#124;perf_gate_canned_ir_over_limit&#124;perf_gate_canned_realtime_under_floor)$' --output-on-failure --no-tests=error` | Unapproved widening succeeds, Ir/realtime becomes advisory, or repeat-two digest/consumption mismatch is ignored. | T-17-17,T-17-18 | pending |
| 17-07.3 | `python3 -I tests/scripts/verify-v02-delivery.py --self-test && python3 -I .github/scripts/verify-workflow-policy.py --check && python3 -I .github/scripts/verify-workflow-policy.py --self-test && bash .github/scripts/verify-release-gates.sh --self-test` | Any production consumer retains timing-only blocker or skips Ir/realtime/correctness; malformed/unbound advisory passes. | T-17-17,T-17-18 | pending |
| 17-08.1 | `python3 -I tests/scripts/verify-support-ledger.py --self-test && cmake --preset phase1 && ctest --test-dir build -R '^release_disclosure_(generator&#124;controls)$' --output-on-failure --no-tests=error` | Generated ledger needs hand edits, tagged bytes change, required disclosure is absent, or malformed inputs pass. | T-17-19,T-17-20 | pending |
| 17-08.2 | `cmake --preset phase1 && ctest --test-dir build -R '^release_window_(contract&#124;controls)$' --output-on-failure --no-tests=error` | Stale regenerated/reviewed content passes, a relevant edit leaves freeze valid, or an inactive example asserts release readiness. | T-17-19,T-17-20 | pending |
| 17-08.3 | `python3 -I .github/scripts/verify-workflow-policy.py --check && python3 -I .github/scripts/verify-workflow-policy.py --self-test && python3 -I tests/scripts/verify-version-window.py --self-test` | Production regeneration bypasses window identity, a relevant path/check is excluded, or RM-027 is incorrectly marked closed. | T-17-19,T-17-20 | pending |
| 17-09.1 | `cmake --preset phase1 && ctest --test-dir build -R '^release_lifecycle_(replay&#124;controls)$' --output-on-failure --no-tests=error` | Production workflow does not call extracted lifecycle, replay bypasses actual verifier, non-git path fails, unexpected API call occurs, or live publication is attempted. | T-17-21,T-17-22,T-17-23 | pending |
| 17-09.2 | `python3 -I tests/scripts/verify-release-lifecycle.py --self-test && python3 -I .github/scripts/verify-release-source-proof.py --self-test` | Capture provenance/digest/schema is absent, invented repository field is required, a stale/tampered/partial set succeeds, or fixture changes bypass production code. | T-17-21,T-17-22,T-17-23 | pending |
| 17-09.3 | `python3 -I tests/scripts/verify-release-lifecycle.py --self-test && bash .github/scripts/verify-release-gates.sh --self-test && python3 -I .github/scripts/verify-workflow-policy.py --check && python3 -I .github/scripts/verify-workflow-policy.py --self-test` | Retry overwrites identical attachments, tampered data reaches publish decision, independent check is missing/misordered, or mutation controls pass for an unrelated reason. | T-17-21,T-17-22,T-17-23 | pending |
| 17-10.1 | `bash .github/scripts/verify-release-gates.sh --self-test && python3 -I .github/scripts/verify-release-source-proof.py --self-test && python3 -I .github/scripts/check-required-native.py --self-test && python3 -I .github/scripts/verify-workflow-policy.py --check && python3 -I .github/scripts/verify-workflow-policy.py --self-test && python3 -I tests/scripts/verify-release-lifecycle.py --self-test` | Wrong producer/event/source/app or duplicate manifest is accepted; chosen run is unverified; retry tamper check regresses. | T-17-24,T-17-25,T-17-26 | pending |
| 17-10.2 | `python3 -I tests/scripts/verify-phase8-closure-contract.py --self-test && python3 -I tests/scripts/verify-phase8-player-contract.py --self-test && python3 -I tests/scripts/verify-test-budget.py --self-test && python3 -I tests/scripts/verify-planning-hygiene.py --self-test && cmake --preset phase1 && ctest --test-dir build -R '^(phase8_(closure&#124;player)_contract_selftest&#124;test_budget&#124;plan_cap&#124;planning_hygiene_controls)$' --output-on-failure --no-tests=error` | Retargeted tag, reused-ref new row, suffixed over-cap plan or fifth phase passes; checker reads live facts instead of immutable boundary. | T-17-24,T-17-25,T-17-26 | pending |
| 17-10.3 | `python3 -I .github/scripts/verify-workflow-policy.py --check && python3 -I .github/scripts/verify-workflow-policy.py --self-test && python3 -I tests/scripts/verify-hdma-lane.py --lane-self-test && python3 -I tests/scripts/verify-perf-gate.py --self-test` | Timeout lacks real eligible evidence, title/label dedupe is fuzzy, skipped HDMA passes/wrong reason qualifies, repeat-two validation regresses, or issue writes occur in dry-run. | T-17-24,T-17-25,T-17-26 | pending |
| 17-11.1 | `cmake --preset phase1 && ctest --test-dir build -R '^release_review_(approval&#124;controls)$' --output-on-failure --no-tests=error && python3 -I tests/scripts/verify-perf-gate.py --self-test` | Any of eight mutants passes, approval is requested for advisory timing, unverified owner fields are accepted/written, or approval overrides correctness/realtime. | T-17-27,T-17-28,T-17-29 | pending |
| 17-11.2 | `cmake --preset phase1 && ctest --test-dir build -R '^(release_nightly_(gate&#124;controls)&#124;state_boundary_controls)$' --output-on-failure --no-tests=error` | Any of six mutants passes, output is written on refusal, timestamp/source boundary is stale, or checker depends on mutable live route/ancestry. | T-17-27,T-17-28,T-17-29 | pending |
| 17-11.3 | `python3 -I tests/scripts/verify-release-gates.py --self-test && python3 -I tests/scripts/verify-release-lifecycle.py --self-test && python3 -I .github/scripts/verify-workflow-policy.py --check && python3 -I .github/scripts/verify-workflow-policy.py --self-test && cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` | A gate is defined but not production-called, one of 8+6 mutants survives, full suite/required exact-head checks fail/skip/stale, boundary facts use live HEAD, or work advances Phase 18. | T-17-27,T-17-28,T-17-29 | pending |

## Creation and execution ordering

- 17-01.1: extend existing compiled package tracer; create/run inventory/nm defects and executable size/audio proofs before codec implementation/acceptance. state_precodec_gate emits build/state-precodec-proof.json only after passing actual tests, negative controls and immutable input/build binding.
- 17-01.2: assert the proof receipt, rerun the gate before first codec acceptance, implement complete codec/API/SHA and run real installed state tracer in this same plan. Changed descriptor/range inputs require renewed proof. 17-01.3 creates/checks actual build/state-prefix via configured CMake installation, then checked-in installed C/C++ consumers.
- 17-02..03: expand mode/mapper/canonical/refusal/observer/purity discriminators. Whole-instance and owned-RAM no-write oracles include late-failure controls.
- 17-04: create all public wrapper/event/span/peripheral cap cases before each independent guard; require witnessed missing-guard mutants including per-tick HDMA.
- 17-05: actual fork output precedes census; all category/non-default field witnesses precede mutation evidence. Missing-category, removed-mutant and unexercised-mutant cases fail.
- 17-06: compiled portable pins/immutable ratchet precede native-OS wiring; semantic target/omission controls precede hosted campaign claims. Existing real installed/package/fuzz lanes remain required.
- 17-07: actual producer/verifier/reuse advisory receipt precedes production aggregate/attach/release consumers. Ir1.10/realtime4.02 and both repeated digest/consumption checks remain blocking.
- 17-08: managed generator/window contract tests precede production regeneration.
- 17-09: production lifecycle extraction/registration precedes captured realistic API/retry evidence. Replay transport cannot publish live.
- 17-10: extend existing CTest-owned selftests for WR/IN findings; real report-red timing evidence precedes closing its timeout citation.
- 17-11: register approval/nightly/boundary tests when created, then invoke actual production gates. Full suite and required exact-head hosted checks run once at final reviewed head; do not refresh older phases.

## Required negative inventories

Review approval: non-owner; wrong issue; wrong digest; missing approval wording; prefix-only digest; unrecorded issue; predating comment; prefilled owner fields. Nightly: non-success; wrong head; skipped/failed replay; in-progress; no run at head; older green behind newer red. Every control requires its intended diagnostic and unrelated passing case. Approval applies only to deterministic Ir exception/limit acceptance, never ordinary advisory timing.

Horizon: STOP wait; CPU stall; HDMA tick; IRQ; HALT; instruction; speed-switch reservation; peripheral addition; ordinary event; borrowed span. Field-drop inventory and observed categories are in17-05, with no quota/count substitution.

## Wave 0 requirements

No checker-only feature plan or new framework install. The leading17-01 task uses the existing production compiled core/package tracer and gates actual size/audio proofs alongside inventory/nm before17-01.2 accepts codec bytes. Source-changing acceptance inputs invalidate the proof receipt. Stop/rescope if inductive audio bounds, fixed-size sum or validate/apply symmetry cannot be proved.

Checkers materialize immutable source via --rev and bind compiled evidence separately. Plan11 boundary checks read point-in-time facts/timestamps from the literal boundary commit, never current HEAD routes/ancestry. Actual T-17-01..29 are unique; no dependency-install boundary is in scope (reserved SC is conditional exclusion outside tables).

## Manual-only verification

All in-scope deterministic contracts are automated; no human UAT checkpoint is planned. API-shaped replay proves deterministic production logic, not live GitHub permissions/publication. Real credential/hardware/perceptual limitations remain honestly scoped outside these checks.

## Validation sign-off

- [ ] Every final task has executable automated verification with adjacent fails_when.
- [ ] Every deliverable has positive and intended negative controls.
- [ ] Test ordering, CTest inventory/timeouts and phase-unique threat links are complete.
- [ ] SUMMARY coverage uses block schema: id, description, human_judgment:false; verification block items kind/ref/status:pass, no flow maps/ctest kind/inline comments.
- [ ] At verify-work use tests/scripts/verify-uat-closure.py with --write evidence and --self-test; no handwritten UAT/local copy.
- [ ] Final source-head suite and required exact-revision hosted checks pass.
- [ ] Validated/Nyquist flags change only after real execution evidence.

Approval pending execution evidence. This remains a draft planning contract.
