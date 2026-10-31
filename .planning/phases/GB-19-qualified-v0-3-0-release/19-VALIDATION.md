---
phase: "19"
slug: "qualified-v0-3-0-release"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: validated
nyquist_compliant: true
wave_0_complete: true
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
- **Max feedback latency:** 60 seconds per CTest (TIMEOUT ≤ 60) for every per-task quick check. The long lanes below are approved exceptions; L-1 to L-3 are not per-task quick loops, and L-4 covers the existing policy workload, now partitioned under D-127 into semantic groups each retaining its 180-second bound, bounded by its registered TIMEOUT with its post-change time recorded.

### Approved latency exceptions

| Id | Where | What | Why it cannot be < 60 s | Bound |
|----|-------|------|-------------------------|-------|
| L-1 | 19-05 Task 3, second `<automated>` block (wave-level, run once) | `v02_consumer_controls_c`, `v02_consumer_controls_cpp` | existing consumer build-and-install CTests registered with TIMEOUT 600 and COST 600 (`tests/CMakeLists.txt` ~1495-1502); the new host-smoke work lives in their shared static part | 600 s each, once per plan |
| L-2 | 19-06 Tasks 1 and 4; 19-01 Task 4 (player package build) | full `ctest --preset phase1` suite, the player tree (`verify-phase3-player.sh --build-package`, `^(player_|core_linkage_)`), `build/preflight/run.sh` | D-19 requires the full suite and the player tree on the synthetic 0.3.0 tree; each CTest inside still has TIMEOUT ≤ 60 except the L-1 pair | several minutes; run after the task's quick checks pass |
| L-3 | 19-01 Task 2 (D-06 dry run), 19-03 Task 3 (perf-attribution, 150-minute cap), 19-06 Tasks 1 and 4, 19-07 Tasks 1-4 | waiting on hosted runs (`gh run watch`, `gh pr checks --watch`) | remote workflow durations, not local checks; each verify after the wait is a sub-60 s read-only `gh` query | each workflow's own job timeouts |
| L-4 | policy quick checks in 19-01, 19-04, 19-05 and 19-07; D-127 recovery before a fresh 19-07 window | `workflow_policy_group_ci`, `workflow_policy_group_release_jobs`, `workflow_policy_group_release_support`, `workflow_policy_group_rehearsal`, `workflow_policy_group_ledger`, `workflow_policy_group_helpers` | D-127 preserves all 412 isolated CLI mutation cases plus individual helper/positive/platform cases from reviewed baseline `70d3e422`; the former aggregate timed out on Windows. The immutable ID/CTest coverage checks and their negative controls stay at or below 60 seconds | 180 seconds per semantic group, unchanged; no job/performance limit increase. Record each measured group duration and actual executed-ID coverage at the final candidate; the former aggregate measured 49.9 seconds at f80bdf54 and later failed at its 180-second limit on Windows |

---

## Per-Task Verification Map

| Req / SC | Plan | Behavior | Test Type | Automated Command (`ctest -R`) | Negative control | Status |
|----------|------|----------|-----------|--------------------------------|------------------|--------|
| SC1 / V1 | 19-04 | R2 at W is the binding rehearsal; a run that names another revision, or postdates the merge, is rejected | unit + replay | `^(release_lifecycle_(replay\|controls)\|release_nightly_(gate\|controls)\|workflow_policy_(check\|group_[a-z_]+\|coverage(_controls)?))$` | postdated run, late attempt 2, non-PR-head tree-equal, missing `merged_at`, other run id, PR event/fork/path, inactive record, R2 red while R1 green; `--merged-at` without `--attempt-jobs` (and the reverse); candidate bind call without `--pr-head`, `--merged-at` or `--attempt-jobs` (policy mutants) | ✅ covered |
| SC1 / V2 | 19-04 | Window record is legal only when `release_version` equals the tree version | unit | `^release_window_(contract\|controls)$` | stale active record after a bump | ✅ covered |
| SC1 / V3 | 19-04 | Pre-tag gate workflow is pinned and fatal | policy | `^workflow_policy_(check\|group_[a-z_]+\|coverage(_controls)?)$` | masked gate, subject code run, `pull_request_target`, wrong base | ✅ covered |
| SC1 / V4 | 19-01 | Tree-equal citations proved against the revision under test (`--main-ref` default `HEAD`); scratch 0.3.0 passes `--check --release-head` against a heads-plus-tags remote clone | unit | `^workflow_policy_(check\|group_[a-z_]+\|coverage(_controls)?)$` | tree mismatch, anchor off main, absent job name, ceil(2×p50) over timeout, a pruned tree-equal citation or a main-only clone (refused) while a plain row citing an absent merged-PR head passes; a fake git refusing `origin/` still passes default `--check` | ✅ covered |
| D-01 disclosure | 19-01 (rule), 19-06 (applied) | Every ledger row whose job body PR A changed carries the body-change disclosure | policy | `^workflow_policy_(group_[a-z_]+\|coverage(_controls)?)$`; 19-06 Task 4 `--check --disclosure-base f80bdf54…` | changed body without the phrase (scratch-git control); one disclosure stripped from a scratch copy of the PR A head | ✅ covered |
| SC2 / V5 | 19-03 | Claims are validated and rendered; ledger is a generator fixed point | unit | `^(support_claims(_controls)?\|release_disclosure_(generator\|controls)\|v02_support_ledger(_controls)?\|support_ledger_binding(_controls)?)$` | D-14 controls 1–9, incl. a seeded unscoped claim | ✅ covered |
| SC2 / V6 | 19-03 | Release-notes rules and adoption patterns | unit | `^(v02_adoption_docs(_controls)?\|v02_game_claims(_controls)?)$` | D-14 control 10 | ✅ covered |
| SC2 / V7 | 19-03 | No interop claim names SameBoy, BGB, BESS or mGBA | unit | `^doc_no_interop_claims$` | D-14 control 11 | ✅ covered |
| SC3 / V8 | 19-05 | Perf-gate receipt is emitted, uploaded (also from a red gate run, `if: always()` directly after the gate step) and verified; the documented one realtime retry stays reachable and the kept receipt is the deciding attempt's | unit + policy | `^(perf_gate_receipt_controls\|perf_gate_retry_controls\|v02_delivery_controls\|workflow_policy_(group_[a-z_]+\|coverage(_controls)?))$` | ratio over limit, other SHA, PR event, wrong limits blob; upload without `if: always()` and upload moved after the seeded-regression step (policy mutants, artifact-flow); attempt 1 below the floor then attempt 2 passing must exit 0 with attempt 2's `realtime_min` (not attempt 1's, and no `perf-receipt-output` collision); both attempts below the floor exit 1 keeping attempt 2's receipt; an Ir refusal is not retried and still leaves its receipt | ✅ covered |
| SC3 / V9 | 19-05 | Consumer receipt carries `host_smoke` | unit | `^(v02_delivery_controls\|v02_consumer_controls_(c\|cpp)\|installed_host_smoke)$` | `host_smoke` missing or not passed | ✅ covered |
| SC3 / V10 | 19-05 | Published-asset readback reconciles against the pre-publish inventory persisted as a workflow artifact before publish | unit + replay + policy | `^(v03_dispositions(_controls)?\|v03_readback(_controls)?\|release_lifecycle_post_tag_(trust\|capture_source\|draft_assets\|recovery_sums\|consumer\|publication\|coverage)_controls\|workflow_policy_(group_[a-z_]+\|coverage(_controls)?))$` | asset set or id drift, digest vs `SHA256SUMS`, sidecar blob, draft, tag SHA or tree, another revision's receipt, an unsourced or altered inventory; final-gate without the inventory write; upload step deleted or moved after publish-draft | ✅ covered |
| D-07 | 19-01 | Player build linkage is clean | integration | `ctest --test-dir build-player -R '^core_linkage_'` | `mutant` name restored; double link restored | ✅ covered |
| D-08 | 19-01, 19-02, 19-06 | WR-C04, IN-08 (19-01); IN-05, IN-02 (19-02); IN-07 (19-06) | policy + unit | `^(workflow_policy_(check\|group_[a-z_]+\|coverage(_controls)?)\|v02_fuzz_controls\|test_budget(_controls)?\|state_format_contract\|v02_adoption_docs_controls)$` | head-copy mutant; missing `persist-credentials: false`; header-edit fuzz control; IN-02 sentence omission; IN-07 phrase omission and a retry tamper-overclaim | ✅ covered |
| D-09 | 19-02 | WR-A05 and IN-01 | unit | `^(state_refusal.*\|state_canonical\|state_semantic_bounds\|state_codec_mutant_controls\|state_portable_pins\|state_pin_controls\|state_continuation.*)$` | range-check removal mutant; byte-identical goldens and pins | ✅ covered |
| D-21 | 19-04 (inventory, captures incl. `ci_run`), 19-05 (its own forms) | `POST_TAG_ENDPOINTS` covers every gh form in the lifecycle, judges and release.yml, each replayed with REQUIRED_PATHS or policy-pinned | replay + policy | `^(release_lifecycle_(replay\|controls\|post_tag_(trust\|capture_source\|draft_assets\|recovery_sums\|consumer\|publication\|coverage)_controls)\|workflow_policy_(group_[a-z_]+\|coverage(_controls)?))$` | unrouted lifecycle endpoint; new release.yml form not in the table; replayed entry without REQUIRED_PATHS; perf receipt over the release-please run shape; renamed perf-gate download | ✅ covered |
| D-25 | 19-06 (19-03 for the retired host entries) | Docs are coherent, the CHANGELOG first heading is a version, the D-16/D-25/OQ-5 release.md prose and the unreleased.md stub are pinned, and the retired `unreleased_host_entries` coverage lives in the claim validator | unit | `^(changelog_first_heading(_controls)?\|doc_links_versions(_controls)?\|v02_adoption_docs(_controls)?\|support_claims_controls\|doc_contract_.*\|cgb_corpus_claims\|cgb_hdma_claims_contract)$` | `## Unreleased` above a version; stale ledger link; each pinned phrase omitted; the stub phrase dropped or a pending v0.3.0 section re-added; a host CTest or PLAY-01 dropped from the claims (control 8b) | ✅ covered |
| D-10 / D-16 | 19-02 | RM-024 deferrals and the RM-032 v0.4 row are recorded | unit | `^planning_hygiene_controls$` | each of the eight deferral pins removed from FUTURE-MILESTONES.md text | ✅ covered |
| REL-01 trace | 19-07 | REL-01 checked and its traceability row Complete on main after PR B | point-in-time | 19-07 Task 4 second `<automated>` block (`git show origin/main:.planning/REQUIREMENTS.md`) | the same predicate is false at `f80bdf54` | ✅ covered |
| D-19 | 19-06 | Pre-flight 0.3.0 tree is green locally; the hosted pre-flight on the transient `rehearsal/v0.3.0` runs all six producer lanes green, past their derive steps, then the branch is deleted (19-06-D2) | integration | scratch tree: full suite, player tree, lifecycle replay, `--release-notes`, `--check --release-head --git-root <remote clone>`, derive and verify-subject for `rehearsal/v0.3.0`, judge differential (phase-branch judge passes every step; f80bdf54 judge under its own argv recorded per step as exit code plus message key, with no usage key; f80bdf54 judge under H' argv predicts one outcome line `success` or `failure\|<step>\|<exit>\|<key>`; each judge work directory holds `git worktree add` checkouts, `subject` at H' and `trusted-judge` at the judge revision; `uses:` steps not emulated, so a hosted failure there fails closed); key rule: committed `tests/scripts/verify-judge-outcome.py`, CTest `judge_outcome_controls` (19-06 Task 1 first `<automated>` block); hosted: 19-06 Task 1 third `<automated>` block | bump-only tree fails; `rehearsal/preflight-v0.3.0` derive refused; `judge_outcome_controls` refuses an empty failed-step log and a failure without an exit-code line as undecidable, and over prefixed `--log-failed` fixtures never lets another job's lines (corpus `full_ctest`, continue-on-error) or a non-failed judge step decide the key; the hosted judge outcome line (step, exit code and key) must equal the predicted line, so a usage or receipt refusal never reads as a REJECT set or a pass; branch absent afterwards | ✅ covered |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] New CTests: `support_claims`, `support_claims_controls`, `perf_gate_receipt_controls`, `perf_gate_retry_controls`, `judge_outcome_controls`, `v03_readback`, `v03_readback_controls`, `changelog_first_heading`, `changelog_first_heading_controls`, and `doc_links_versions` with its controls.
  - Register each in `tests/CMakeLists.txt` and append it to `tests/expected-tests.txt`.
  - Give `LABELS planning` to each one that reads `.planning/`.
  - Set an explicit TIMEOUT ≤ 60 on each.
- [x] Split `release_lifecycle_controls`: it already takes 51 s of its 60 s budget.
- [x] No framework install is needed.

---

## Manual-Only Verifications

None. Every phase behavior has automated verification (D-069). The owner-only decisions are not verifications: the immutable-releases toggle, a defective tagged tree, and any widening of the Ir limit.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter — D134 refusal controls close the reopened schema gap

**Validation:** Automated coverage is present for all eight executed plans. Owner scope decisions are recorded separately and are not test passes.

## Wave 1 Integration Evidence

The full phase1 build and 1,681-test run at `01e3354a279a68158735b02cd42386e9cb837620` found 19 failed or dependency-blocked cases. This was a failing integration run, not a release qualification pass. The original JUnit is `build/phase19-wave1.xml`.

- State inventory parsing and invariant-aware count poisoning were repaired in `7efc2c3da28d3edfcb3416d4f5cfbc401c0863ac`; the affected state selection passed 48/48, including all fork-mutant shards and their dependencies. Evidence is recorded in 19-02-SUMMARY.md.
- The new adoption test's timeout returned to 60 seconds, and performance floor validation now binds the original policy receipt at the immutable limits base in `3d6e0a6debb7c3a2b31b8acb7b268cacfd96dd5a`. Limits and the refreshed notes receipt were unchanged. Fifteen focused cases passed; the remaining approval case was sandbox-blocked. Evidence is recorded in 19-03-SUMMARY.md and `build/phase19-wave1-perf-fix-3d6e0a6d.xml`.
- At `cb1bb07440f8df5cf1c845eb8c638b86c673bdb4`, the scoped rerun with access for temporary Git worktrees passed 3/3: `v02_performance_controls`, `v02_delivery_controls`, and `release_review_approval`. JUnit: `build/phase19-wave1-sandbox-rerun.xml`.

All failures from the Wave 1 run are covered by these repairs and focused reruns. Schema/UI gates were non-blocking; codebase drift skipped because no structure map exists. This closes Wave 1 integration only; REL-01 and phase verification remain pending.

## Wave 2 Integration Evidence

At `8c906de57abe9337d3c1784221b5659a1e46b256`, phase1 configure/build passed and the complete CTest suite passed 1,682/1,682 with four parallel workers. JUnit: `build/phase19-wave2.xml`; log: `build/phase19-wave2-ctest.log`. The suite ran with scoped access for its temporary Git worktrees, and retained every test and timeout. Schema and UI gates were non-blocking; codebase drift skipped because no structure map exists. REL-01 remains pending until publication and readback; 19-04 supplies rehearsal-binding coverage only.

## Wave 3 Integration Evidence

At `2be716eb`, configure/build passed. The 1,685-test integration run recorded 13 timeouts across unrelated cases, one dependency-blocked case, and a missing planning label on `v03_readback_controls`. Several reported timeout durations substantially exceeded the configured limits; those failed results remain in `build/phase19-wave3.xml` and are not a passing full-suite claim.

The failed-case rerun, including fixture dependencies, passed 139/140 without source changes; only the known label defect remained (`build/phase19-wave3-rerun.xml`). All timed-out cases passed in that rerun. Commit `1b9540f6` adds the planning label to the shared-module readback test. The affected selection passed 5/5: readback controls, test budget and controls, planning labels and controls (`build/phase19-wave3-label-fix.xml`). The timeout-generated dense-input fixture was preserved under `build/phase19-wave3-timeout-artifacts/`.

These checks resolve the failures from the integration run without changing limits or omitting cases. Schema/UI gates were non-blocking; codebase drift skipped because no structure map exists. Phase 19 remains active at plan 19-06; REL-01 remains pending.


## Final execution validation map

All 29 tasks across 19-01..19-08 declare automated commands (38 automated blocks), and the authored map above names their refusing controls. Plans 19-01..19-05 remain backed by their implementation and integration records. The frozen 19-06 halted summary is a historical pre-merge snapshot; its operational closure is independently recorded in 19-07 through the qualified PR A, renewed preflight and actual protected merges. The reserved 19-08 was used, with approved D-130..D-133 continuations; no second gap or automatic next phase is introduced.

At committed source 8a561c58, the focused release/readback/recovery/disclosure/window/policy selection passed 19/19, including the actual published readback, wrong G/S identity controls, tagged-ledger byte-flip refusal, active-window refusals and complete/disjoint policy coverage. The recovery suite retains all original controls and now proves 93 refusals plus 12 positives. Live summary-coverage, planning-label and documentation-link checks with controls passed after the final summaries were authored. The original first failure, HTTP200 association drift and no-write UTF-8 entrypoint failure remain recorded; they are not reclassified as passes.

L-4 measured semantic-group times at 8a561c58: CI15.71s, release jobs28.85s, release support6.80s, rehearsal17.24s, ledger5.08s, helpers5.84s. Coverage0.95s and coverage controls1.95s. Existing group TIMEOUT180 remains unchanged; the old49.9s aggregate is historical. Raw-log observer verification accepts the actual timestamped W verdict/R2 binding and refuses wrong-run and inactive substitutions; echoed shell patterns are excluded (`build/phase19-window/prb-observer-check.json`).

D-132/D-133 entrypoint qualification exercised the actual main operator against intercepted transport, including the old str/bytes failure, the two-call UTF-8 correction, pre/post body negatives and no real mutation. The actual separately marked same-ID association restoration and sole retry then passed. Public captures contain bounded sanitized projections and raw-byte digests; actual publication is proven independently in 19-release-readback.json.

The final local full-suite/player-package qualification, canonical security/code reviews and exact-head hosted protected checks remain mandatory before PR B merge. The REL-01 main-boundary predicate is replayed against the immutable actual squash and must refuse the pending f80bdf54 base; its final evidence and boundary SHA belong only in local continue.md. This validation map specifies that automated gate without claiming a future merge. No manual-only verification or human UAT is added. Final owner route is `/gsd-verify-work 19`, never an automatic milestone audit.

## Validation Audit 2026-10-31

| Metric | Count |
|---|---|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |


## Post-review schema gap hold

Final code review found an uncovered malformed-schema acceptance at pre-publish/readback/fixture/ledger boundaries and a registry root-type diagnostic gap. Current-source reproduction accepts JSON true and1.0 inventory versions and true registry version; array registry raises AttributeError. Existing successful checks and actual integer-schema release evidence remain valid, but the missing refusal controls prevent final validation closure. A private isolated bounded repair is being prepared for the required owner scope decision. No active implementation change, new test target, timeout/policy relaxation or live release action is authorized by this note. Re-run affected controls and independent review after scope approval; final qualification remains pending.

## Validation Audit 2026-10-31

| Metric | Count |
|---|---|
| Gaps found | 2 |
| Resolved | 0 |
| Escalated | 2 |


## D-134 gap closure evidence

The owner approved the pinned seven-path repair. At committed d2c0dc95, all eight affected existing CTests passed without skips, including actual v0.3.0 readback, inventory/readback/disposition schema negatives, valid schema-1/schema-2 ledgers, capture/fixture schemas and non-object workflow registry rejection. Existing control floors/markers are raised to the measured51/120/99/72; no timeout or baseline assertion changed and no target was added. The initial isolated marker mismatch remains historical. Fresh independent security recheck reproduced the baseline acceptance, confirmed correct rejection with recomputed raw-inventory hashes and reclosed T-19-22. Both validation gaps now have automated refusal and valid-input positive checks. The final full local/player/consumer and exact-head hosted gates remain mandatory before the existing PR B merge.

## Validation Audit 2026-10-31

| Metric | Count |
|---|---|
| Gaps found | 2 |
| Resolved | 2 |
| Escalated | 0 |
