---
phase: "14"
slug: "cgb-e-model-qualification-and-corpus"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-15"
---

# Phase 14 — Validation Strategy

This is a planning contract, not a verification receipt. New behavior, fixtures and checks remain unimplemented. The planner completes the per-task map against its final plan IDs; execution records results. D-069 and context D-20 require an automated discriminator and a negative control for every deliverable.

## Test Infrastructure

| Property | Value |
|---|---|
| Framework | Existing C17 native tests, CTest and Python standard-library scripts |
| Config | `CMakePresets.json`, `tests/CMakeLists.txt`, `tests/expected-tests.txt` |
| Quick run command | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --test-dir build -R '^(apu_.*|cgb_visibility_.*|summary_coverage)$' --output-on-failure --no-tests=error` |
| Full suite command | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` |
| Regression command | `bash tests/scripts/verify-dmg-baseline.sh` |
| Measured planning cost | Research selection: 33 tests in 2.09 s; eight AGE disposition tests in 2.89 s. Phase 13's historical 994-test run was 107 s. These are not future CI guarantees. |

## Sampling Rate

- After every implementation task: build and run its exact named positive/negative tests; assert required CTest membership before filtering.
- After each wave: run affected integration, inventory and shared clock-domain checks; run the frozen DMG baseline after shared core changes.
- At phase verification: full native suite, relevant sanitizer/fixture/consumer/package lanes and complete corpus receipt, reusing existing executions.
- Target focused feedback below 30 seconds excluding build/reproduction; measure new workloads and record a justified budget before increasing timeouts.
- An empty regex result, subset missing required names, stale receipt, changed expected-failure signature, timeout or unexpected pass cannot be green.

## Per-Task Verification Map

The plan-generation pass replaces this seam-level seed with the exact task IDs, waves, test names and unique threat references. New commands must be created by the task that first uses them or an explicit predecessor.

| Planned seam | Requirement | Test type | Automated evidence | Negative discriminator |
|---|---|---|---|---|
| Guest FF56/72–77 and digital APU | CGB-08 | unit/integration | Native guest reads in DMG/native/compat cells; independent nibble/mask/IR policy assertions | Wrong nibble, writable PCM, routing-coupled PCM, leaked mode or wrong mask |
| CH3/NR52/trigger/DIV transitions | CGB-08 | unit/integration | Timed guest transitions and split/unsplit observations | Direct-RAM latch replacement, omitted transition, lost remainder |
| Pinned source inventory/admission | CGB-10 | integration | Source-header selection, rights/build/digest checks; complete SameSuite70 and Mooneye9 selection; AGE6 source/image pairs | Missing/duplicate row, wrong pin, result-selected denominator, unadmitted execution |
| Inherited AGE timing | CGB-08, CGB-10 | integration | Separate assertion masks for normal/DS and native/compat targets; source-backed pixel checks | LY/SCX collapse, stale signature, changed pixel, wrong mode |
| Case/assertion receipt | CGB-10 | integration | Exact required membership and source/build/config identities; one execution stream; observed results distinct from evaluator status | Truncation/timeout, xfail counted pass, stale/unknown/duplicate/missing ID or empty cohort |
| CI and claims closure | CGB-08, CGB-10 | e2e/other | Existing native/sanitizer/repro/package paths; exact tests; semantic docs contracts; strict SUMMARY coverage | Missing required test, weakened claim/coverage, fixture leaked into package |

## Wave 0 Requirements

No new test framework or dependency is required. Each tracer task creates its missing tests before expansion. Plans must order the guest APU tests, new fixture admission and executable oracles, independent source inventory validator, receipt parser and AGE image checks before their consumers. Keep source inventory validation separate from result parsing. Do not insert a horizontal infrastructure-only phase.

## Manual-Only Verifications

All in-scope phase behaviors have automated verification. No routine human UAT is required. Physical CGB-E, analog/perceptual evidence and Phase 15 game/release work remain outside this phase; they are limitations, not invented acceptance checkpoints.

## Evidence and Coverage Format

Every plan SUMMARY uses block-style `coverage` records with `id`, `description`, `human_judgment: false` and block `verification` items containing `kind`, `ref`, `status: pass`. Kinds are `unit`, `integration`, `e2e`, `automated_ui` or `other`. `summary_coverage` must reject malformed or unverified entries. No flow maps, inline comments or `ctest` kind.

## Validation Sign-Off

- [ ] Final task map matches all plans and unique threat IDs.
- [ ] Every task has runnable automated verification and an observable failure signal.
- [ ] Every deliverable has a passing twin and intended negative control.
- [ ] Missing checks are created before first use; no watch-mode commands.
- [ ] Runtime and exact required membership are measured during execution.
- [ ] Phase evidence is fresh; `nyquist_compliant` is set only by validation.

**Approval:** Planning contract pending independent plan check; implementation verification pending.
