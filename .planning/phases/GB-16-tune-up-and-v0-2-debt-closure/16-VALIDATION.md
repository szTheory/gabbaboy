---
phase: "16"
slug: "tune-up-and-v0-2-debt-closure"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
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
| TUNE-01 | No tracked text outside `.planning/` names `.planning/phases` except allowlisted spellings | unit/lint | `ctest -R '^no_phase_paths'` | Seeded fixture per spelling and scope root rejects; stale zero-hit allowlist row fails | ❌ W0 | ⬜ pending |
| TUNE-01 | Retargeted v0.2 readers pass from archive with minimum counts | integration | existing `summary_coverage`, `closeout_dispositions_*`, `historical_limitations_*`, `cgb_red_evidence_privacy*`, `uat_closure_*` | Empty dir fails on `--min-files` / `GBB_EXPECT_MIN_KEY` | partial | ⬜ pending |
| TUNE-02 | Phase 8 verifiers pass, self-test, reject wrong boundary | integration | `ctest -R '^phase8_(closure|player)_'` | `--boundary v0.2.0` fails; self-test `rejected_controls` >= 157 | ❌ W0 | ⬜ pending |
| TUNE-03 | Perf gate parser/arithmetic/schema/realtime floor on canned data | unit | `ctest -R '^perf_gate'` | Over-limit Ir, under-floor multiple, digest mismatch, vacuous input each fail | ❌ W0 | ⬜ pending |
| TUNE-03 | Hosted gate rejects seeded regression | hosted integration | `perf-gate` job scratch-tree patch | Patch fails with digest equal; no-op twin passes | ❌ W0 hosted | ⬜ pending |
| TUNE-03 | Attribution receipt consistent | unit | `ctest -R '^perf_attribution'` | Dropped commit, altered row/delta rejected | ❌ W0 | ⬜ pending |
| TUNE-04 | Per-test TIMEOUT ratchet | unit/integration | `ctest -R '^test_budget'` | Over-budget fixture, raised ceiling, expired allowlist row fail | ❌ W0 | ⬜ pending |
| TUNE-04 | Timeout ledger rules | unit | CTest wrapping `verify-workflow-policy.py` | Edited timeout, missing row, >60% ratio, no doubled run, `provisional` at release head fail | ❌ W0 | ⬜ pending |
| TUNE-04 | Bounded ASan stall replay | integration | sharded `acceptance_stall_diagnosis_*` | PR lane without bounded case or with full replay fails | ❌ W0 | ⬜ pending |
| TUNE-04 | Planning-only classifier | unit | CTest on name-status fixtures | `src/`/`tests/` change, rename out of `src/`, `..`, symlink, empty diff classify `full` | ❌ W0 | ⬜ pending |
| TUNE-05 | Plan-cap check | unit | `ctest -R '^plan_cap'` | Over-cap, missing cap line, cap > 12 fail | ❌ W0 | ⬜ pending |
| TUNE-05 | LESSONS unique ids | unit | `ctest -R '^lessons_unique'` | Duplicate id fixture fails | ❌ W0 | ⬜ pending |
| TUNE-05 | STATE size bound | unit | `ctest -R '^state_size'` | Oversized fixture fails | ❌ W0 | ⬜ pending |
| TUNE-05 | Playstead docs | unit | `ctest -R '^playstead_docs'` | Stale-statement fixtures fail; required adoption sentences remain | ❌ W0 | ⬜ pending |
| TUNE-06 | v0.2.0 ledger freeze | unit | `ctest -R '^ledger_freeze'` | Flipped byte, wrong pin, edit outside appended block fail | ❌ W0 | ⬜ pending |
| TUNE-06 | Version-agnostic ledger/adoption checks | integration | existing `v02_support_ledger*`, `v02_adoption_docs*` | Wrong-version fixture rejected | partial | ⬜ pending |
| TUNE-06 | Release-note needles | unit | `verify-v02-adoption.py --release-notes` self-test | Notes without +8.3% disclosure rejected | ❌ W0 | ⬜ pending |
| TUNE-06 | Disposition record and publication facts | boundary (point-in-time) | CTest on disposition record; post-release commit checker | Closure without tag-bound digests or readback rejected | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/cmake/` per-area include mechanism, included before `gabbaboy_verify_registered_tests()` (16-01)
- [ ] Checkers and fixtures: `verify-no-phase-paths.py`, perf parser and receipt checker, test-budget checker, classifier, plan-cap, LESSONS, STATE, Playstead, ledger freeze, disposition record — each with CTest and `tests/expected-tests.txt` line
- [ ] `tests/data/` canned cachegrind and timing outputs
- [ ] `.github/ci-timeouts.json`, `tests/ci/test-budget-allowlist`, `tests/baseline/perf-gate-v1.txt`
- [ ] CTest wrappers for `verify-workflow-policy.py --check` and `--self-test`
- No framework install needed

---

## Manual-Only Verifications

All phase behaviors have automated verification. Hosted-only facts (valgrind Ir gate, release publication readback) are checked by automated hosted jobs and point-in-time boundary checkers, not human readings.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
