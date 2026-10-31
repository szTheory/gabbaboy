---
status: complete
phase: GB-16-tune-up-and-v0-2-debt-closure
source: 16-01-SUMMARY.md, 16-02-SUMMARY.md, 16-03-SUMMARY.md, 16-04-SUMMARY.md, 16-05-SUMMARY.md, 16-06-SUMMARY.md, 16-07-SUMMARY.md
started: 2026-10-26T15:55:55.480997+00:00
updated: 2026-10-26T16:07:02.237Z
---

## Automated Evidence

Phase 16 verification closed with no human checkpoint (DECISIONS D-069). All 51 deliverables below are copied from the coverage blocks of plan SUMMARYs 16-01..16-07; every verification item is automated and passing. `tests/scripts/verify-uat-closure.py --write` wrote this closure, and its `--self-test` rejects weakened copies.

- Regression gate: on main `be4cee8`, freshly built (`phase1` preset), the full suite `ctest --preset phase1 --parallel 4` passed 1234/1234 in 154 s. The count matches the 1234 cases the verifier enumerated at the boundary.
- Phase verifier: `16-VERIFICATION.md` reports status passed, score 5/5, with evidence taken from a detached worktree at boundary `92364c7`. The 35 planning CTests and 23 named perf, ledger, budget, policy, disposition and adoption tests passed there, and `verify-v03-dispositions.py --check ... --rev 92364c7` passes (rows=26, pending=0).
- Verifier advisories reconciled at this boundary: ci.yml run 40346420094 on `92364c7` completed with conclusion success. Issue #122 is closed. REQUIREMENTS.md shows TUNE-01..06 as Complete.
- Hosted evidence: v0.2.1 is published (tag at `b93137f`). The ci, fixture-repro and release-please runs on main `be4cee8` all completed with conclusion success.
- Code review: `16-REVIEW.md` found 0 critical, 5 warning and 4 info findings. Each one is deferred, with a destination, in `16-REVIEW-DISPOSITION.md`.

Not passes and not owner acceptances: the deferred review findings (WR-01..WR-05, IN-01..IN-04) and the owner-waived gap rounds disclosed in D-112 are recorded dispositions. Phase 17 should read them along with FUTURE-MILESTONES RM-026..RM-029.

## Current Test

[testing complete]

## Tests

### 1. The phase-path lint rejects each forbidden spelling (literal, joined segments, backslash, PROJECT_SOURCE_DIR prefixed) in each scope root, accepts milestone archive links, skips binaries, and fails over-max, stale and reasonless allowlist rows and an unscanned must-scan file.
expected: "The phase-path lint rejects each forbidden spelling (literal, joined segments, backslash, PROJECT_SOURCE_DIR prefixed) in each scope root, accepts milestone archive links, skips binaries, and fails over-max, stale and reasonless allowlist rows and an unscanned must-scan file."
result: pass
source: automated
summary_file: 16-01-SUMMARY.md
coverage_id: D1
evidence: ["python3 -I tests/scripts/verify-no-phase-paths.py --self-test", "ctest -R '^no_phase_paths_controls$'"]

### 2. The lint passes on the moved tree with a count-pinned row for every scanned hit, scanning 407 files against a floor of 380.
expected: "The lint passes on the moved tree with a count-pinned row for every scanned hit, scanning 407 files against a floor of 380."
result: pass
source: automated
summary_file: 16-01-SUMMARY.md
coverage_id: D2
evidence: ["ctest -R '^no_phase_paths$'"]

### 3. Phases 7 through 15.1 (578 tracked files) are archived under .planning/milestones/v0.2-phases as pure renames, GB-16 stays live, and the v0.2 audit script moved beside the audits.
expected: "Phases 7 through 15.1 (578 tracked files) are archived under .planning/milestones/v0.2-phases as pure renames, GB-16 stays live, and the v0.2 audit script moved beside the audits."
result: pass
source: automated
summary_file: 16-01-SUMMARY.md
coverage_id: D3
evidence: ["git diff --cached -M100% --name-status shows 578 R100 renames and no modified or deleted archived file", "ctest -R '^closeout_dispositions_controls$'"]

### 4. Every v0.2 reader reads the archive; the dispositions checker rewrites embedded legacy paths and rejects missing or escaping ones with distinct codes, and the historical glob must match a file.
expected: "Every v0.2 reader reads the archive; the dispositions checker rewrites embedded legacy paths and rejects missing or escaping ones with distinct codes, and the historical glob must match a file."
result: pass
source: automated
summary_file: 16-01-SUMMARY.md
coverage_id: D4
evidence: ["python3 -I tests/scripts/verify-closeout-dispositions.py --self-test", "ctest -R '^(historical_limitations_controls|cgb_corpus_red_evidence_privacy|uat_closure_controls)$'"]

### 5. verify-summary-coverage.py has no default phases directory and gains --min-files; the v0.2 sweep asserts at least 143 files and an empty directory is rejected.
expected: "verify-summary-coverage.py has no default phases directory and gains --min-files; the v0.2 sweep asserts at least 143 files and an empty directory is rejected."
result: pass
source: automated
summary_file: 16-01-SUMMARY.md
coverage_id: D5
evidence: ["ctest -R '^(summary_coverage|summary_coverage_live|summary_coverage_empty_dir_rejected|summary_coverage_selftest)$'"]

### 6. The HDMA lane checker lives in tests/scripts without the ASan timeout, parallelism or TIMEOUT assertions, gains a fixture-repro needle control, and the orphaned Node handoff test is gone.
expected: "The HDMA lane checker lives in tests/scripts without the ASan timeout, parallelism or TIMEOUT assertions, gains a fixture-repro needle control, and the orphaned Node handoff test is gone."
result: pass
source: automated
summary_file: 16-01-SUMMARY.md
coverage_id: D6
evidence: ["ctest -R '^(cgb_hdma_lane_contract|cgb_hdma_lane_contract_selftest|cgb_hdma_remote_evidence_selftest)$'"]

### 7. The per-area CTest hook is included exactly once before the inventory check and sanitizer scaling, and the full suite including dmg_baseline passes after the move.
expected: "The per-area CTest hook is included exactly once before the inventory check and sanitizer scaling, and the full suite including dmg_baseline passes after the move."
result: pass
source: automated
summary_file: 16-01-SUMMARY.md
coverage_id: D7
evidence: ["ctest --preset phase1 --output-on-failure --no-tests=error (1187 of 1187 passed)", "ctest -R '^dmg_baseline$'", "git diff --quiet merge-base HEAD -- src include"]

### 8. The Ir gate evaluator passes a 1.081 pair and exactly 1.10, fails one Ir above with ir-budget-exceeded, and rejects nondeterministic, vacuous (Ir floor and consumed pin), wrong-digest, below-floor realtime and malformed-limits inputs with their own codes, using exact arithmetic including a float-misjudged case.
expected: "The Ir gate evaluator passes a 1.081 pair and exactly 1.10, fails one Ir above with ir-budget-exceeded, and rejects nondeterministic, vacuous (Ir floor and consumed pin), wrong-digest, below-floor realtime and malformed-limits inputs with their own codes, using exact arithmetic including a float-misjudged case."
result: pass
source: automated
summary_file: 16-02-SUMMARY.md
coverage_id: T1
evidence: ["python3 -I tests/scripts/verify-perf-gate.py --self-test", "ctest -R '^perf_gate_'"]

### 9. Canned cachegrind and timing fixtures are immutable: a drifted fixture stops CMake configuration and the canned over-limit and under-floor sets fail through the real CLI.
expected: "Canned cachegrind and timing fixtures are immutable: a drifted fixture stops CMake configuration and the canned over-limit and under-floor sets fail through the real CLI."
result: pass
source: automated
summary_file: 16-02-SUMMARY.md
coverage_id: T2
evidence: ["ctest -R '^(perf_gate_canned_pass|perf_gate_canned_ir_over_limit|perf_gate_canned_realtime_under_floor|perf_gate_limits_schema)$'"]

### 10. The workflow policy requires perf-gate in required-native needs, its result and the three gate commands in ci.yml and the rehearsal, and judges perf-attribution.yml as dispatch-only and read-only; thirteen new mutations are each rejected.
expected: "The workflow policy requires perf-gate in required-native needs, its result and the three gate commands in ci.yml and the rehearsal, and judges perf-attribution.yml as dispatch-only and read-only; thirteen new mutations are each rejected."
result: pass
source: automated
summary_file: 16-02-SUMMARY.md
coverage_id: T3
evidence: ["python3 -I .github/scripts/verify-workflow-policy.py --check", "python3 -I .github/scripts/verify-workflow-policy.py --self-test"]

### 11. The DMG-only adapted harness builds at all 39 selected revisions, from v0.1.0 to HEAD, and reproduces every per-ROM consumed and digest pin, with harness_sha256 equal to the planning-time value.
expected: "The DMG-only adapted harness builds at all 39 selected revisions, from v0.1.0 to HEAD, and reproduces every per-ROM consumed and digest pin, with harness_sha256 equal to the planning-time value."
result: pass
source: automated
summary_file: 16-02-SUMMARY.md
coverage_id: T4
evidence: ["bash tests/scripts/run-perf-gate.sh --attribution-dry-run"]

### 12. The gate driver, seeded regression, no-op twin and attribution emit and check pipeline work end to end, and the attribution self-test rejects eleven receipt mutations with distinct codes.
expected: "The gate driver, seeded regression, no-op twin and attribution emit and check pipeline work end to end, and the attribution self-test rejects eleven receipt mutations with distinct codes."
result: pass
source: automated
summary_file: 16-02-SUMMARY.md
coverage_id: T5
evidence: ["python3 -I tests/scripts/verify-perf-gate.py --self-test"]

### 13. The hosted perf-gate job concluded success on PR A's exact head with the seeded step rejecting (head Ir 265298354 over v0.2.0 Ir 233589980, ratio 1.135, digest unchanged, 2 iterations per half-dot) and the no-op twin passing at ratios tracer=1.083 libbet=1.081 visible-demo=1.080 with realtime_min=6.665.
expected: "The hosted perf-gate job concluded success on PR A's exact head with the seeded step rejecting (head Ir 265298354 over v0.2.0 Ir 233589980, ratio 1.135, digest unchanged, 2 iterations per half-dot) and the no-op twin passing at ratios tracer=1.083 libbet=1.081 visible-demo=1.080 with realtime_min=6.665."
result: pass
source: automated
summary_file: 16-02-SUMMARY.md
coverage_id: T6
evidence: ["gh run view 40154479138 --job 121052802460 -R szTheory/gabbaboy"]

### 14. TUNE-03: the hosted attribution receipt is committed byte-for-byte and recomputed from git history (39 revisions, 20 merges). The realtime floor is staged per D-109, PR A gating at 2.0 and PR B raising it to 4.02 = floor(0.6 x 6.7027); the evaluator refuses a lower floor. LIM-PERF-REVIEW is closed by citing the receipt.
expected: "TUNE-03: the hosted attribution receipt is committed byte-for-byte and recomputed from git history (39 revisions, 20 merges). The realtime floor is staged per D-109, PR A gating at 2.0 and PR B raising it to 4.02 = floor(0.6 x 6.7027); the evaluator refuses a lower floor. LIM-PERF-REVIEW is closed by citing the receipt."
result: pass
source: automated
summary_file: 16-02-SUMMARY.md
coverage_id: T7
evidence: ["python3 -I tests/scripts/verify-perf-gate.py --check-attribution tests/baseline/perf-attribution-v1.json", "ctest -R '^perf_(gate|attribution)'", "ctest --preset phase1"]

### 15. The per-test TIMEOUT ratchet fails a test over 60 s without an allowlist row, a test with no TIMEOUT, a test over its ceiling, a stale or expired row, a raised ceiling, an unresolvable or head-only ref and an unreadable base, and passes the exact boundaries; the real 1202-test inventory passes.
expected: "The per-test TIMEOUT ratchet fails a test over 60 s without an allowlist row, a test with no TIMEOUT, a test over its ceiling, a stale or expired row, a raised ceiling, an unresolvable or head-only ref and an unreadable base, and passes the exact boundaries; the real 1202-test inventory passes."
result: pass
source: automated
summary_file: 16-03-SUMMARY.md
coverage_id: D1
evidence: ["python3 -I tests/scripts/verify-test-budget.py --self-test", "ctest --test-dir build -R '^test_budget'"]

### 16. Every test in the phase1 build and in a player-enabled build has an explicit TIMEOUT after the default-budget sweep (596 of 1194 and 81 of 98 player tests were untimed before).
expected: "Every test in the phase1 build and in a player-enabled build has an explicit TIMEOUT after the default-budget sweep (596 of 1194 and 81 of 98 player tests were untimed before)."
result: pass
source: automated
summary_file: 16-03-SUMMARY.md
coverage_id: D2
evidence: ["ctest --test-dir build --show-only=json-v1 (zero tests without TIMEOUT in phase1 and in a GABBABOY_BUILD_PLAYER=ON build)"]

### 17. ci.yml native-linux runs the ratchet with --base from the PR base or push parent, and the workflow policy rejects a variant that drops --base.
expected: "ci.yml native-linux runs the ratchet with --base from the PR base or push parent, and the workflow policy rejects a variant that drops --base."
result: pass
source: automated
summary_file: 16-03-SUMMARY.md
coverage_id: D3
evidence: ["python3 -I .github/scripts/verify-workflow-policy.py --self-test"]

### 18. acceptance_stall_diagnosis keeps its frozen name and compares two parallel single-replay tests through the gbb_stall_full fixture; acceptance_stall_bounded replays drop:START at 50561280 half-dots from a SHA-256 pinned case file, still fails with predicate-not-reached and produces a deterministic report and PPM; dmg_baseline is unchanged and green.
expected: "acceptance_stall_diagnosis keeps its frozen name and compares two parallel single-replay tests through the gbb_stall_full fixture; acceptance_stall_bounded replays drop:START at 50561280 half-dots from a SHA-256 pinned case file, still fails with predicate-not-reached and produces a deterministic report and PPM; dmg_baseline is unchanged and green."
result: pass
source: automated
summary_file: 16-03-SUMMARY.md
coverage_id: D4
evidence: ["ctest -R '^(acceptance_stall_diagnosis|acceptance_stall_diagnosis_replay_1|acceptance_stall_diagnosis_replay_2|acceptance_stall_bounded|dmg_baseline)$'", "python3 -I tests/scripts/verify-stall-report.py --self-test"]

### 19. The PR ASan acceptance shard excludes the three full stall tests, its expected-shard slice drops the same names, and the policy and corpus inventory pins carry the exact new lines; two new mutations (shard keeps the full replay, shard excludes the bounded test) are rejected.
expected: "The PR ASan acceptance shard excludes the three full stall tests, its expected-shard slice drops the same names, and the policy and corpus inventory pins carry the exact new lines; two new mutations (shard keeps the full replay, shard excludes the bounded test) are rejected."
result: pass
source: automated
summary_file: 16-03-SUMMARY.md
coverage_id: D5
evidence: ["python3 -I .github/scripts/verify-workflow-policy.py --self-test", "python3 -I tests/scripts/verify-cgb-corpus-inventory.py --ci-contract"]

### 20. v02_consumer_controls is split into v02_consumer_controls_c and v02_consumer_controls_cpp through --consumer, the release-gates required list names both, and a guard rejects an unclassified self-test.
expected: "v02_consumer_controls is split into v02_consumer_controls_c and v02_consumer_controls_cpp through --consumer, the release-gates required list names both, and a guard rejects an unclassified self-test."
result: pass
source: automated
summary_file: 16-03-SUMMARY.md
coverage_id: D6
evidence: ["ctest -R '^v02_consumer_controls_(c|cpp)$'", "bash .github/scripts/verify-release-gates.sh --self-test"]

### 21. nightly-asan.yml triggers on schedule and workflow_dispatch only; the replay job is read-only with the exact ctest line, and report-red alone holds issues: write with no checkout; check_nightly() rejects an extra trigger, a write permission on the replay job, a checkout in the report job and a dropped ctest filter.
expected: "nightly-asan.yml triggers on schedule and workflow_dispatch only; the replay job is read-only with the exact ctest line, and report-red alone holds issues: write with no checkout; check_nightly() rejects an extra trigger, a write permission on the replay job, a checkout in the report job and a dropped ctest filter."
result: pass
source: automated
summary_file: 16-03-SUMMARY.md
coverage_id: D7
evidence: ["python3 -I .github/scripts/verify-workflow-policy.py --check", "python3 -I .github/scripts/verify-workflow-policy.py --self-test"]

### 22. The sanitizer timeout policy sweeps stale probe directories, removes its own on success and keeps it on failure; assert-clean mode passes after a pass and a seeded leftover directory makes it fail.
expected: "The sanitizer timeout policy sweeps stale probe directories, removes its own on success and keeps it on failure; assert-clean mode passes after a pass and a seeded leftover directory makes it fail."
result: pass
source: automated
summary_file: 16-03-SUMMARY.md
coverage_id: D8
evidence: ["ctest -R '^sanitizer_timeout_policy_(selftest|temp_clean|temp_clean_control)$'"]

### 23. The full phase1 CTest suite passes at the final head with no src/ or include/ change and the frozen DMG baseline file untouched.
expected: "The full phase1 CTest suite passes at the final head with no src/ or include/ change and the frozen DMG baseline file untouched."
result: pass
source: automated
summary_file: 16-03-SUMMARY.md
coverage_id: D9
evidence: ["ctest --preset phase1 --output-on-failure --no-tests=error"]

### 24. A planning-only change runs one cheap job behind required-native while any src/, include/ or tests/ change still runs the full matrix; the classifier rejects renames out of src/, dot-dot segments, case variants, symlinks, submodules, empty and oversized diffs, a missing or zero base and tags.
expected: "A planning-only change runs one cheap job behind required-native while any src/, include/ or tests/ change still runs the full matrix; the classifier rejects renames out of src/, dot-dot segments, case variants, symlinks, submodules, empty and oversized diffs, a missing or zero base and tags."
result: pass
source: automated
summary_file: 16-04-SUMMARY.md
coverage_id: D1
evidence: ["python3 -I .github/scripts/classify-changes.py --self-test", "ctest --test-dir build -R '^classify_changes_src_rejected$'", "stacked probe PR 108 run 40166565258: planning-checks and required-native success, every heavy job skipped", "PR 107 exact-head runs 40168063465 and 40168065851: every heavy job ran and required-native success"]

### 25. required-native stays the single always() aggregator: kind=full needs every heavy job success and planning-checks skipped, kind=planning needs planning-checks success and every heavy job skipped, any other kind is full, and the three required contexts are unchanged.
expected: "required-native stays the single always() aggregator: kind=full needs every heavy job success and planning-checks skipped, kind=planning needs planning-checks success and every heavy job skipped, any other kind is full, and the three required contexts are unchanged."
result: pass
source: automated
summary_file: 16-04-SUMMARY.md
coverage_id: D2
evidence: ["python3 -I .github/scripts/check-required-native.py --self-test", "python3 -I .github/scripts/verify-workflow-policy.py --self-test"]

### 26. The timeout ledger has one row per job with timeout-minutes in every workflow, each citing a real run, and the policy rejects an edited timeout, a missing row, a p50 above half the timeout, a stale value, a new job without a row, a duplicate key, a provisional row at the release head, a gating p50 of 30.1, release_bound under any other key or after the VERSION expiry, and a normal row without samples.
expected: "The timeout ledger has one row per job with timeout-minutes in every workflow, each citing a real run, and the policy rejects an edited timeout, a missing row, a p50 above half the timeout, a stale value, a new job without a row, a duplicate key, a provisional row at the release head, a gating p50 of 30.1, release_bound under any other key or after the VERSION expiry, and a normal row without samples."
result: pass
source: automated
summary_file: 16-04-SUMMARY.md
coverage_id: D3
evidence: ["ctest --test-dir build -R '^workflow_policy_(check|controls)$'", "python3 -I .github/scripts/verify-workflow-policy.py --check"]

### 27. Every test that reads .planning/ or AGENTS.md carries the planning label, no planning-labelled test names the build tree, and ctest -L planning passes on a configured but unbuilt tree.
expected: "Every test that reads .planning/ or AGENTS.md carries the planning label, no planning-labelled test names the build tree, and ctest -L planning passes on a configured but unbuilt tree."
result: pass
source: automated
summary_file: 16-04-SUMMARY.md
coverage_id: D4
evidence: ["python3 -I tests/scripts/verify-planning-labels.py --self-test", "ctest --test-dir build/phase16_04_unbuilt -L planning --no-tests=error (20 of 20 on a fresh unbuilt configure)"]

### 28. The full suite passes with the new lane, ledger and lint, and git diff of src and include against the plan base is empty.
expected: "The full suite passes with the new lane, ledger and lint, and git diff of src and include against the plan base is empty."
result: pass
source: automated
summary_file: 16-04-SUMMARY.md
coverage_id: D5
evidence: ["cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error (1209 of 1209)", "git diff --quiet 2bd618db0a48587bddedc535bad5722fcbf479aa HEAD -- src include"]

### 29. The annotated tag historical/phase-08-boundary is on origin and peels to 96d5eec977bee99a0629499b89c737415e24184c before any CI run of the Phase 8 CTests.
expected: "The annotated tag historical/phase-08-boundary is on origin and peels to 96d5eec977bee99a0629499b89c737415e24184c before any CI run of the Phase 8 CTests."
result: pass
source: automated
summary_file: 16-05-SUMMARY.md
coverage_id: D1
evidence: ["git ls-remote origin refs/tags/historical/phase-08-boundary and its peeled ref: tag object b4a189e45f9bdffbdc3f2cd07f74679f17068dad peeling to 96d5eec977bee99a0629499b89c737415e24184c"]

### 30. Both Phase 8 verifiers take --boundary, resolve it once with rev-parse, fail closed with a distinct message on an empty, option-shaped or missing revision with no SHA fallback, and report a wrong-but-readable boundary (v0.2.0) as a clause miss.
expected: "Both Phase 8 verifiers take --boundary, resolve it once with rev-parse, fail closed with a distinct message on an empty, option-shaped or missing revision with no SHA fallback, and report a wrong-but-readable boundary (v0.2.0) as a clause miss."
result: pass
source: automated
summary_file: 16-05-SUMMARY.md
coverage_id: D2
evidence: ["python3 -I tests/scripts/verify-phase8-closure-contract.py --self-test", "python3 -I tests/scripts/verify-phase8-player-contract.py --self-test", "ctest --test-dir build -R '^phase8_(closure|player)_contract' (6 of 6)"]

### 31. The six Phase 8 CTests run through expect_exit.cmake with the planning label, the self-test enforces rejected_controls of at least 160, and the wrong-boundary tests forbid the unreadable-boundary message.
expected: "The six Phase 8 CTests run through expect_exit.cmake with the planning label, the self-test enforces rejected_controls of at least 160, and the wrong-boundary tests forbid the unreadable-boundary message."
result: pass
source: automated
summary_file: 16-05-SUMMARY.md
coverage_id: D3
evidence: ["PR 112 head 1ed7dda: ci pull_request run 40209514947 and ci push run 40209512854 concluded success on every full job", "python3 -I tests/scripts/verify-no-phase-paths.py --check"]

### 32. Plan-cap, LESSONS-id and STATE-size checks reject an over-cap phase directory, a missing cap line, cap 13, a cap sum of 41, duplicate and vacuous LESSONS ids and an oversized STATE fixture, and accept the boundary values; the live files pass.
expected: "Plan-cap, LESSONS-id and STATE-size checks reject an over-cap phase directory, a missing cap line, cap 13, a cap sum of 41, duplicate and vacuous LESSONS ids and an oversized STATE fixture, and accept the boundary values; the live files pass."
result: pass
source: automated
summary_file: 16-05-SUMMARY.md
coverage_id: D4
evidence: ["python3 -I tests/scripts/verify-planning-hygiene.py --self-test", "ctest --test-dir build -R '^(plan_cap|lessons_unique_ids|state_size|planning_hygiene_controls)$'"]

### 33. LESSONS.md has each of GB-FIXTURE-003, GB-FIXTURE-004 and GB-TEST-007 once, STATE.md keeps its frontmatter and every kept heading with the historical blocks verbatim in v0.2-STATE-ARCHIVE.md.
expected: "LESSONS.md has each of GB-FIXTURE-003, GB-FIXTURE-004 and GB-TEST-007 once, STATE.md keeps its frontmatter and every kept heading with the historical blocks verbatim in v0.2-STATE-ARCHIVE.md."
result: pass
source: automated
summary_file: 16-05-SUMMARY.md
coverage_id: D5
evidence: ["ctest --test-dir build -R '^(lessons_unique_ids|state_size)$'", "heading survival loop over STATE.md and the archive from the task 2 verify command"]

### 34. README, docs/native-integration.md and PRECEDENT.md state GB, GBC and GBA through mGBA 0.10.5 on Playstead main 234bd45b21 as process adapters, keep both required adoption sentences, and the docs check rejects the stale pin, GBA/mGBA and the current-tense 1de3e95 sentences.
expected: "README, docs/native-integration.md and PRECEDENT.md state GB, GBC and GBA through mGBA 0.10.5 on Playstead main 234bd45b21 as process adapters, keep both required adoption sentences, and the docs check rejects the stale pin, GBA/mGBA and the current-tense 1de3e95 sentences."
result: pass
source: automated
summary_file: 16-05-SUMMARY.md
coverage_id: D6
evidence: ["ctest --test-dir build -R '^(playstead_docs|v02_adoption_docs|v02_adoption_docs_controls)$'"]

### 35. The full suite passes with the new tests and src and include are unchanged against the plan base.
expected: "The full suite passes with the new tests and src and include are unchanged against the plan base."
result: pass
source: automated
summary_file: 16-05-SUMMARY.md
coverage_id: D7
evidence: ["cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error (1227 of 1227)", "git diff --quiet 6e99a953ca9a773b8c501df940a1195661db7b1a HEAD -- src include", "python3 .github/scripts/verify-workflow-policy.py --check"]

### 36. The v0.2.0 ledger is frozen: the tag blob, the working file and the one disclosed #93 block are each pinned by SHA-256, a missing tag fails, and controls reject a flipped byte, a wrong pin, an insertion or equal-length edit outside the block, a removed or edited block and an unreadable tag.
expected: "The v0.2.0 ledger is frozen: the tag blob, the working file and the one disclosed #93 block are each pinned by SHA-256, a missing tag fails, and controls reject a flipped byte, a wrong pin, an insertion or equal-length edit outside the block, a removed or edited block and an unreadable tag."
result: pass
source: automated
summary_file: 16-06-SUMMARY.md
coverage_id: D1
evidence: ["python3 -I tests/scripts/verify-support-ledger.py --check-freeze and --self-test-freeze (controls=9)", "ctest --test-dir build -R '^(ledger_freeze|ledger_freeze_controls)$'"]

### 37. The ledger, adoption and rehearsal checks take the tree version from CMake cross-checked with the manifest, README must link the ledger that version selects, and fixtures reject a README linking an older or future ledger, a manifest and CMake disagreement and a version without a ledger.
expected: "The ledger, adoption and rehearsal checks take the tree version from CMake cross-checked with the manifest, README must link the ledger that version selects, and fixtures reject a README linking an older or future ledger, a manifest and CMake disagreement and a version without a ledger."
result: pass
source: automated
summary_file: 16-06-SUMMARY.md
coverage_id: D2
evidence: ["python3 -I tests/scripts/verify-support-ledger.py --check-binding, --self-test-binding (controls=6) and --self-test", "ctest --test-dir build -R '^(support_ledger_binding|support_ledger_binding_controls|v02_support_ledger|v02_support_ledger_controls|v02_adoption_docs|v02_adoption_docs_controls)$'"]

### 38. verify-v02-adoption.py --release-notes requires the head-versus-v0.2.0 instruction-count disclosure (+8.3%) and the attribution receipt path, and its self-test rejects notes that drop either or hide the line in a comment.
expected: "verify-v02-adoption.py --release-notes requires the head-versus-v0.2.0 instruction-count disclosure (+8.3%) and the attribution receipt path, and its self-test rejects notes that drop either or hide the line in a comment."
result: pass
source: automated
summary_file: 16-06-SUMMARY.md
coverage_id: D3
evidence: ["python3 -I tests/scripts/verify-v02-adoption.py --self-test docs (51 negative controls)"]

### 39. A recorded performance review can be applied in the rehearsal by dispatch and carried to the release by tree equality: verify-v02-performance.py --verify-reuse rejects an unequal tree, a pending receipt and an unreadable candidate, the paired gate is unchanged, and the policy rejects a decision applied without the tree, workflow or branch checks, a decision file inside the checkout, a token on the apply step, a write permission and a reuse without --verify-reuse.
expected: "A recorded performance review can be applied in the rehearsal by dispatch and carried to the release by tree equality: verify-v02-performance.py --verify-reuse rejects an unequal tree, a pending receipt and an unreadable candidate, the paired gate is unchanged, and the policy rejects a decision applied without the tree, workflow or branch checks, a decision file inside the checkout, a token on the apply step, a write permission and a reuse without --verify-reuse."
result: pass
source: automated
summary_file: 16-06-SUMMARY.md
coverage_id: D4
evidence: ["python3 -I tests/scripts/verify-v02-performance.py --self-test (32 tests)", "python3 -I .github/scripts/verify-workflow-policy.py --self-test (259 negative controls)", "rehearsal run 40216415155 on rehearsal/v0.2.0 at bd43d7b: the tag derivation step succeeded in corpus, package and aggregate, and the pending paired measurement was retained as artifact rehearsal-performance-40216415155-1 although the job failed"]

### 40. 16-DISPOSITIONS.json holds 26 rows with the release-linked rows pending-release, verify-v03-dispositions.py accepts closure only with tag-bound receipts read at a commit, and closeout_dispositions_scope_v03 shows the v0.2 owner_accepted=0 expectation stays scoped to the archived record.
expected: "16-DISPOSITIONS.json holds 26 rows with the release-linked rows pending-release, verify-v03-dispositions.py accepts closure only with tag-bound receipts read at a commit, and closeout_dispositions_scope_v03 shows the v0.2 owner_accepted=0 expectation stays scoped to the archived record."
result: pass
source: automated
summary_file: 16-06-SUMMARY.md
coverage_id: D5
evidence: ["python3 -I tests/scripts/verify-v03-dispositions.py --check on the live record (rows=26 pending=5 closed=1 owner_accepted=7) and --self-test (controls=35)", "ctest --test-dir build -R '^(v03_dispositions|v03_dispositions_controls|closeout_dispositions_controls|closeout_dispositions_scope_v03)$'"]

### 41. Every provisional timeout row is gone: changes and planning-checks cite main push runs, fuzz and package cite a probe rehearsal at an ancestor of main, the three rehearsal rows that cannot be green become release_bound, and the policy passes at the release head.
expected: "Every provisional timeout row is gone: changes and planning-checks cite main push runs, fuzz and package cite a probe rehearsal at an ancestor of main, the three rehearsal rows that cannot be green become release_bound, and the policy passes at the release head."
result: pass
source: automated
summary_file: 16-06-SUMMARY.md
coverage_id: D6
evidence: ["python3 -I .github/scripts/verify-workflow-policy.py --check --release-head", "jq '[.[] | select(.provisional == true)] | length' .github/ci-timeouts.json prints 0"]

### 42. The full suite passes with the new tests, the exact head is green on every required context and heavy job, and src and include are unchanged against the plan base.
expected: "The full suite passes with the new tests, the exact head is green on every required context and heavy job, and src and include are unchanged against the plan base."
result: pass
source: automated
summary_file: 16-06-SUMMARY.md
coverage_id: D7
evidence: ["cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error (1233 of 1234 first run, the one no_phase_paths failure fixed and the file's tests rerun green)", "PR 114 head bd43d7b: ci pull_request 40216403568, ci push 40216384921, fixture-repro pull_request 40216403570, fixture-repro push 40216384890 and preview-package-smoke pull_request 40216403621 all concluded success", "git diff --quiet bdb352515128bcb70e26cd8ff6aff22484d6f1e2 bd43d7b2d384020159480289f91bbbc8fbbdc213 -- src include"]

### 43. v0.2.1 is published from PR #75: the tag commit b93137f is the squash of the rehearsed head c6dc575 and has the same tree b02c14b.
expected: "v0.2.1 is published from PR #75: the tag commit b93137f is the squash of the rehearsed head c6dc575 and has the same tree b02c14b."
result: pass
source: automated
summary_file: 16-07-SUMMARY.md
coverage_id: R1
evidence: ["16-release-readback.json: tag v0.2.1, tag_sha b93137f00d07b11dc74e40330e0ddf6029c0677d, tag_tree b02c14bbdc9be80b7aa6b6145cb8b89331388cca, is_draft false, published 2026-10-26T13:52:06Z; git rev-parse b93137f^{tree} equals c6dc575^{tree}"]

### 44. The published asset inventory reconciles: 22 assets whose ids, names and digests match the qualified inventory.
expected: "The published asset inventory reconciles: 22 assets whose ids, names and digests match the qualified inventory."
result: pass
source: automated
summary_file: 16-07-SUMMARY.md
coverage_id: R2
evidence: ["verify-published-release-assets.py read back the release assets: PASS published release asset IDs, names, and digests match the qualified inventory (16-release-readback.json reconciliation)"]

### 45. The exact-head rehearsal is green with the trusted judge, and the operator-dispatched nightly-asan run is green on the same head and tree.
expected: "The exact-head rehearsal is green with the trusted judge, and the operator-dispatched nightly-asan run is green on the same head and tree."
result: pass
source: automated
summary_file: 16-07-SUMMARY.md
coverage_id: R3
evidence: ["release-rehearsal run 40257161612 (all 7 jobs success, judge job 121367397151) and nightly-asan run 40245698754 (asan-full-replay success), both at c6dc575 with tree b02c14b; 16-nightly-asan-gate.json"]

### 46. The performance review is the owner's receipt-bound decision for the exact measurement digest, copied from the owner comment by jq.
expected: "The performance review is the owner's receipt-bound decision for the exact measurement digest, copied from the owner comment by jq."
result: pass
source: automated
summary_file: 16-07-SUMMARY.md
coverage_id: R4
evidence: ["issue #122 comment 6406576530 (OWNER, body equal to the approval line for digest fb254880...a0cd); verify-v02-performance.py --apply-decision and --verify passed on 16-perf-review-decision.json"]

### 47. PRs #78-#92 are closed as superseded by #93 with one comment each; none changes src/ or include/.
expected: "PRs #78-#92 are closed as superseded by #93 with one comment each; none changes src/ or include/."
result: pass
source: automated
summary_file: 16-07-SUMMARY.md
coverage_id: R5
evidence: ["16-pr-closures.json lists 15 CLOSED PRs with closed_at, comment_url and changed_paths; verify-v03-dispositions.py pr-closures rules"]

### 48. The dispositions record closes the four release-linked rows and PR-78-92-SUPERSEDED against tag-bound receipts read at a commit.
expected: "The dispositions record closes the four release-linked rows and PR-78-92-SUPERSEDED against tag-bound receipts read at a commit."
result: pass
source: automated
summary_file: 16-07-SUMMARY.md
coverage_id: R6
evidence: ["python3 -I tests/scripts/verify-v03-dispositions.py --check .planning/phases/GB-16-tune-up-and-v0-2-debt-closure/16-DISPOSITIONS.json (rows=26 pending=0 closed=6 owner_accepted=7)", "ctest -R '^(v03_dispositions|v03_dispositions_controls)$'"]

### 49. The gate fixes carry negative controls: attached retained-build sidecar (6 controls), source-bound rehearsal fuzz receipt (4 plus 3 delivery plus 4 policy controls), GH_REPO recovery from a non-git directory (3 cases), real-shaped check-run repository (9 controls) and retry reuse of attached evidence (3 policy controls).
expected: "The gate fixes carry negative controls: attached retained-build sidecar (6 controls), source-bound rehearsal fuzz receipt (4 plus 3 delivery plus 4 policy controls), GH_REPO recovery from a non-git directory (3 cases), real-shaped check-run repository (9 controls) and retry reuse of attached evidence (3 policy controls)."
result: pass
source: automated
summary_file: 16-07-SUMMARY.md
coverage_id: R7
evidence: ["python3 -I tests/scripts/verify-support-ledger.py --self-test; verify-v02-fuzz.py --self-test; verify-v02-delivery.py --self-test; verify-release-source-proof.py --self-test; verify-workflow-policy.py --self-test (266 negative controls); verify-release-gates.sh --self-test"]

### 50. The D-07 reading of TUNE-01 holds: completed-milestone records are never read from the live phases directory, and current-milestone live reads go only through GBB_LIVE_PHASES_DIR (see 16-01-SUMMARY.md).
expected: "The D-07 reading of TUNE-01 holds: completed-milestone records are never read from the live phases directory, and current-milestone live reads go only through GBB_LIVE_PHASES_DIR (see 16-01-SUMMARY.md)."
result: pass
source: automated
summary_file: 16-07-SUMMARY.md
coverage_id: R8
evidence: ["ctest -R '^no_phase_paths$' (passed in every exact-head required-native run of the window PRs)"]

### 51. git diff --quiet v0.2.0 v0.2.1 -- include holds and the v0.2.0..v0.2.1 src delta is exactly the five planned files.
expected: "git diff --quiet v0.2.0 v0.2.1 -- include holds and the v0.2.0..v0.2.1 src delta is exactly the five planned files."
result: pass
source: automated
summary_file: 16-07-SUMMARY.md
coverage_id: R9
evidence: ["git diff --quiet ab301aa69b1f085050fd66bf7b1378863a0821f2 v0.2.1 -- include; git diff --name-only ab301aa v0.2.1 -- src lists gbb_accept.h, stepper.c, gabbaboy.c, gbb_accept_input.h and acceptance.c only"]

## Summary

total: 51
passed: 51
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none]
