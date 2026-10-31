---
phase: "16"
slug: "tune-up-and-v0-2-debt-closure"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: validated
nyquist_compliant: true
wave_0_complete: true
created: "2026-10-24"
---

# Phase 16 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution. Source: `16-RESEARCH.md` § Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | CTest (CMake floor 3.25; hosted native Linux/macOS/Windows plus ASan lane) with Python 3 stdlib checkers in `tests/scripts/` |
| **Config file** | `CMakePresets.json` (`phase1`, `phase1-asan`, `cmake-3.25.3`); registrations in `tests/CMakeLists.txt` and new per-area `tests/cmake/*.cmake` includes |
| **Quick run command** | `ctest --preset phase1 -R '^<area_prefix>' --no-tests=error` |
| **Full suite command** | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` |
| **Estimated runtime** | quick ~30 seconds; full suite per hosted p50 (~15 min Linux) |

---

## Sampling Rate

- **After every task commit:** Run the targeted `-R` regex for the area touched, plus `python3 -I .github/scripts/verify-workflow-policy.py --check` after any workflow edit
- **After every plan wave:** Run the full suite command and `--self-test` of every checker added or changed
- **Before `/gsd-verify-work`:** Full suite green at the exact head; hosted `required-native`, `fixture-repro`, `preview-package-smoke`, rehearsal and judge green at the release head; closure via `tests/scripts/verify-uat-closure.py`
- **Max feedback latency:** 60 seconds for targeted checks

---

## Per-Task Verification Map

| Req | Behavior | Test Type | Automated Command | Negative Control | File Exists | Status |
|-----|----------|-----------|-------------------|------------------|-------------|--------|
| TUNE-01 | No tracked text outside `.planning/` names `.planning/phases` except allowlisted spellings | unit/lint | `ctest -R '^no_phase_paths'` (+ `no_phase_paths_controls`) | Seeded fixture per spelling and scope root rejects; stale zero-hit allowlist row fails | ✅ | ✅ green |
| TUNE-01 | Retargeted v0.2 readers pass from archive with minimum counts | integration | existing `summary_coverage`, `closeout_dispositions_*`, `historical_limitations_*`, `cgb_red_evidence_privacy*`, `uat_closure_*` | Empty dir fails on `--min-files` / `GBB_EXPECT_MIN_KEY` | ✅ | ✅ green |
| TUNE-02 | Phase 8 verifiers pass, self-test, reject wrong boundary | integration | `ctest -R '^phase8_(closure|player)_'` | `--boundary v0.2.0` fails; self-test `rejected_controls` >= 157 | ✅ | ✅ green |
| TUNE-03 | Perf gate parser/arithmetic/schema/realtime floor on canned data | unit | `ctest -R '^perf_gate'` (`perf_gate_controls`, `_canned_pass`, `_canned_ir_over_limit`, `_canned_realtime_under_floor`, `_limits_schema`) | Over-limit Ir, under-floor multiple, digest mismatch, vacuous input each fail | ✅ | ✅ green |
| TUNE-03 | Hosted gate rejects seeded regression | hosted integration | `perf-gate` job in ci.yml (`run-perf-gate.sh --gate/--seeded-regression/--noop-twin`) | Patch fails with digest equal; no-op twin passes | ✅ hosted | ✅ green |
| TUNE-03 | Attribution receipt consistent | unit | `ctest -R '^perf_attribution'` (`perf_attribution`, `perf_attribution_merges`) | Dropped commit, altered row/delta rejected | ✅ | ✅ green |
| TUNE-04 | Per-test TIMEOUT ratchet | unit/integration | `ctest -R '^test_budget'` (`test_budget`, `test_budget_controls`) | Over-budget fixture, raised ceiling, expired allowlist row fail | ✅ | ✅ green |
| TUNE-04 | Timeout ledger rules | unit | `workflow_policy_check`, `workflow_policy_controls` | Edited timeout, missing row, >60% ratio, no doubled run, `provisional` at release head fail | ✅ | ✅ green |
| TUNE-04 | Bounded ASan stall replay | integration | `acceptance_stall_bounded`, `acceptance_stall_diagnosis*` | PR lane without bounded case or with full replay fails | ✅ | ✅ green |
| TUNE-04 | Planning-only classifier | unit | `classify_changes_controls`, `classify_changes_src_rejected` | `src/`/`tests/` change, rename out of `src/`, `..`, symlink, empty diff classify `full` | ✅ | ✅ green |
| TUNE-05 | Plan-cap check | unit | `ctest -R '^plan_cap'` | Over-cap, missing cap line, cap > 12 fail | ✅ | ✅ green |
| TUNE-05 | LESSONS unique ids | unit | `ctest -R '^lessons_unique'` | Duplicate id fixture fails | ✅ | ✅ green |
| TUNE-05 | STATE size bound | unit | `ctest -R '^state_size'` | Oversized fixture fails | ✅ | ✅ green |
| TUNE-05 | Playstead docs | unit | `ctest -R '^playstead_docs'` | Stale-statement fixtures fail; required adoption sentences remain | ✅ | ✅ green |
| TUNE-06 | v0.2.0 ledger freeze | unit | `ctest -R '^ledger_freeze'` (`ledger_freeze`, `ledger_freeze_controls`, `support_ledger_binding*`) | Flipped byte, wrong pin, edit outside appended block fail | ✅ | ✅ green |
| TUNE-06 | Version-agnostic ledger/adoption checks | integration | existing `v02_support_ledger*`, `v02_adoption_docs*` | Wrong-version fixture rejected | ✅ | ✅ green |
| TUNE-06 | Release-note needles | unit | `v02_adoption_docs_controls` (51 rejected controls incl. `release-notes-perf-disclosure-missing`); gate: release.yml `--release-notes` | Notes without +8.3% disclosure rejected | ✅ | ✅ green |
| TUNE-06 | Disposition record and publication facts | boundary (point-in-time) | `v03_dispositions`, `v03_dispositions_controls` (point-in-time `--rev`); `verify-published-release-assets.py` readback in release workflow | Closure without tag-bound digests or readback rejected | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/cmake/` per-area include mechanism, included before `gabbaboy_verify_registered_tests()` (16-01)
- [x] Checkers and fixtures: `verify-no-phase-paths.py`, perf parser and receipt checker, test-budget checker, classifier, plan-cap, LESSONS, STATE, Playstead, ledger freeze, disposition record — each with CTest and `tests/expected-tests.txt` line
- [x] `tests/data/` canned cachegrind and timing outputs
- [x] `.github/ci-timeouts.json`, `tests/ci/test-budget-allowlist`, `tests/baseline/perf-gate-v1.txt`
- [x] CTest wrappers for `verify-workflow-policy.py --check` and `--self-test`
- No framework install needed

---

## Manual-Only Verifications

All phase behaviors have automated verification.

Residual notes (not manual UAT, no new code required): the hosted `perf-gate` job and the release readback (`verify-published-release-assets.py`, `verify-release-source-proof.py`) run only on hosted CI or in the release workflow, with their own `--self-test` negative controls, and are not registered as local CTests; their recorded evidence is `16-release-readback.json` and `16-07-SUMMARY.md`. Hosted-only facts (valgrind Ir gate, release publication readback) are checked by automated hosted jobs and point-in-time boundary checkers, not human readings.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** validated 2026-10-26 (targeted `ctest -R` on existing `build/`: 60 tests across the rows above, all passed; `verify-v02-adoption.py --self-test docs` 51/51 rejected)
