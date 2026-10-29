---
phase: "19"
slug: "qualified-v0-3-0-release"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-29"
---

# Phase 19 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: `19-RESEARCH.md` § Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | CTest over python3 checkers and C test executables (`expect_exit.cmake` wrapper) |
| **Config file** | `CMakePresets.json` (`phase1`), `tests/CMakeLists.txt`, `tests/cmake/*.cmake`, `cmake/ExpectedTests.cmake`, `tests/expected-tests.txt` |
| **Quick run command** | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --test-dir build -R '<regex>' --output-on-failure --no-tests=error && bash .github/scripts/verify-test-inventory.sh --self-test` |
| **Full suite command** | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error`, plus the player tree (`ctest --test-dir build-player -R '^(player_\|core_linkage_)'`) |
| **Estimated runtime** | quick ≤ 60 s per checker; full suite several minutes |

---

## Sampling Rate

- **After every task commit:** the narrow `-R` regex for the touched checker. Commit, then reconfigure, before any test that reads the configure-time `HEAD` (replay, gate, pin).
- **After every plan wave:** the union of the wave's regexes plus `workflow_policy_*`, `planning_labels`, `test_budget` and `summary_coverage_live`.
- **Before `/gsd-verify-work`:** the full suite, the player tree and the scratch 0.3.0 pre-flight must be green. Re-verify once, at the final head only (D-103).
- **Max feedback latency:** 60 seconds per CTest (TIMEOUT ≤ 60).

---

## Per-Task Verification Map

| Req / SC | Plan | Behavior | Test Type | Automated Command (`ctest -R`) | Negative control | Status |
|----------|------|----------|-----------|--------------------------------|------------------|--------|
| SC1 / V1 | 19-04 | R2 at W is the binding rehearsal; a run that names another revision, or postdates the merge, is rejected | unit + replay | `^(release_lifecycle_(replay\|controls)\|release_nightly_(gate\|controls)\|workflow_policy_(check\|controls))$` | postdated run, late attempt 2, non-PR-head tree-equal, missing `merged_at`, other run id, PR event/fork/path, inactive record, R2 red while R1 green | ⬜ pending |
| SC1 / V2 | 19-04 | Window record is legal only when `release_version` equals the tree version | unit | `^release_window_(contract\|controls)$` | stale active record after a bump | ⬜ pending |
| SC1 / V3 | 19-04 | Pre-tag gate workflow is pinned and fatal | policy | `^workflow_policy_(check\|controls)$` | masked gate, subject code run, `pull_request_target`, wrong base | ⬜ pending |
| SC1 / V4 | 19-01 | Tree-equal citations; scratch 0.3.0 passes `--check --release-head` | unit | `^workflow_policy_(check\|controls)$` | tree mismatch, anchor off main, absent job name, ceil(2×p50) over timeout, missing branch or object | ⬜ pending |
| SC2 / V5 | 19-03 | Claims are validated and rendered; ledger is a generator fixed point | unit | `^(support_claims(_controls)?\|release_disclosure_(generator\|controls)\|v02_support_ledger(_controls)?\|support_ledger_binding(_controls)?)$` | D-14 controls 1–9, incl. a seeded unscoped claim | ⬜ pending |
| SC2 / V6 | 19-03 | Release-notes rules and adoption patterns | unit | `^(v02_adoption_docs(_controls)?\|v02_game_claims(_controls)?)$` | D-14 control 10 | ⬜ pending |
| SC2 / V7 | 19-03 | No interop claim names SameBoy, BGB, BESS or mGBA | unit | `^doc_no_interop_claims$` | D-14 control 11 | ⬜ pending |
| SC3 / V8 | 19-05 | Perf-gate receipt is emitted, uploaded and verified | unit | `^(perf_gate_receipt_controls\|v02_delivery_controls)$` | ratio over limit, other SHA, PR event, wrong limits blob | ⬜ pending |
| SC3 / V9 | 19-05 | Consumer receipt carries `host_smoke` | unit | `^(v02_delivery_controls\|v02_consumer_controls_(c\|cpp)\|installed_host_smoke)$` | `host_smoke` missing or not passed | ⬜ pending |
| SC3 / V10 | 19-05 | Published-asset readback reconciles | unit | `^(v03_dispositions(_controls)?\|v03_readback(_controls)?)$` | asset set or id drift, digest vs `SHA256SUMS`, sidecar blob, draft, tag SHA or tree, another revision's receipt | ⬜ pending |
| D-07 | 19-01 | Player build linkage is clean | integration | `ctest --test-dir build-player -R '^core_linkage_'` | `mutant` name restored; double link restored | ⬜ pending |
| D-08 | 19-02 | WR-C04, IN-05, IN-07, IN-08 | policy + unit | `^(workflow_policy_(check\|controls)\|v02_fuzz_controls\|test_budget(_controls)?)$` | head-copy mutant; missing `persist-credentials: false` | ⬜ pending |
| D-09 | 19-02 | WR-A05 and IN-01 | unit | `^(state_refusal.*\|state_canonical\|state_semantic_bounds\|state_codec_mutant_controls\|state_portable_pins\|state_pin_controls\|state_continuation.*)$` | range-check removal mutant; byte-identical goldens and pins | ⬜ pending |
| D-21 | 19-04 | Replay covers every post-tag endpoint | replay | `^release_lifecycle_(replay\|controls)$` | unexpected endpoint; missing capture | ⬜ pending |
| D-25 | 19-06 | Docs are coherent and the CHANGELOG first heading is a version | unit | `^(changelog_first_heading(_controls)?\|doc_links_versions(_controls)?\|unreleased_host_entries\|doc_contract_.*)$` | `## Unreleased` above a version; stale ledger link | ⬜ pending |
| D-19 | 19-06 | Pre-flight 0.3.0 tree is green | integration | scratch tree: full suite, player tree, lifecycle replay, `--release-notes`, `--check --release-head` | this is the version PR's negative control | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] New CTests: `support_claims`, `support_claims_controls`, `perf_gate_receipt_controls`, `v03_readback`, `v03_readback_controls`, `changelog_first_heading`, `changelog_first_heading_controls`, and `doc_links_versions` with its controls.
  - Register each in `tests/CMakeLists.txt` and append it to `tests/expected-tests.txt`.
  - Give `LABELS planning` to each one that reads `.planning/`.
  - Set an explicit TIMEOUT ≤ 60 on each.
- [ ] Split `release_lifecycle_controls`: it already takes 51 s of its 60 s budget.
- [ ] No framework install is needed.

---

## Manual-Only Verifications

None. Every phase behavior has automated verification (D-069). The owner-only decisions are not verifications: the immutable-releases toggle, a defective tagged tree, and any widening of the Ir limit.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
