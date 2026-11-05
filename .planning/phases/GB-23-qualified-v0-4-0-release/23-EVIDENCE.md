# Phase 23 Qualification Evidence

## Revisions

| Identity | Commit | Meaning |
|---|---|---|
| Implementation | `1f97d44fd7d43c1edc88588f404de9b9322d33fb` | Exact source reviewed by the three independent reviewers. |
| Review evidence | `dbb3199ff62f4315b0fc122598905c72cb0b2faa` | Commit containing all three source-bound review reports. |
| Local qualification run | `dbb3199ff62f4315b0fc122598905c72cb0b2faa` | Candidate head configured and used for the focused and full local runs below. |

The full suite ran at the report commit above. Subsequent commits contain only the fixed Phase 23 evidence/validation paths accepted by the review-evidence gate. The current branch head is the PR candidate; read its exact SHA from GitHub when opening the PR and require hosted checks for that exact head. The v0.4.0 version PR, tag, and publication remain out of scope for this plan.

## Local verification

| Check | Result |
|---|---|
| `cmake --preset phase1 && cmake --build --preset phase1` | Passed at the report-bound candidate. |
| Real report gate with implementation `1f97d44f...` and qualification `dbb3199f...` | Passed: 3 independent reports, 46 findings, no open correctness/security or high/critical/blocking finding. |
| Focused Phase 23 selection | Passed 56/56 in 447.84 seconds with four CTest workers. The test covered all 32 docs-control shards, both review-evidence tests, release/consumer/adoption contracts, path/cap/lifecycle controls, and the planning lane. |
| Full configured CTest suite | Passed 1,767/1,767 in 951.31 seconds with four CTest workers. |
| Test-budget check | Passed for all 1,767 tests; 120 timeout rows are allowlisted and 11 player rows are skipped by its existing policy. |
| Direct planning-label inventory | Passed: 1,767 tests, 63 labelled planning. |
| Direct review-evidence self-test | Passed: 33 positive cases and 28 controls. |
| Direct planning-label self-test | Passed: 27 controls, including fake outer `cmake` and stale valid source-revision rejection. |
| No-phase-path scan/self-test | Passed: 597 tracked files, 12 exact allowlists, 19 controls. |
| Plan-cap/planning-hygiene checks | Passed: four phases, 38 plans, 96 controls. |
| Post-tag recovery controls | Passed: 99 controls and 12 positive checks. |

CTest output from the focused and full runs was preserved locally. The full run log is `/private/tmp/phase23-full-dbb3199ff62f4315b0fc122598905c72cb0b2faa.log`; the CTest build directory also retains its `Testing/Temporary/LastTest.log` output.

## Evidence-only candidate check

After the report commit, candidate `a8ae26d037049686d44ac3b76f97910baa492c3f` passed the real-report gate with implementation `1f97d44fd7d43c1edc88588f404de9b9322d33fb`; the gate verified all differences since implementation were on the fixed evidence/validation allowlist. Configure/build then passed, followed by the review-evidence contract/control and planning-label contract/control CTests (4/4). The 1,767-test full suite was not repeated after this evidence-only advance; its reviewed code and test tree are unchanged, and final exact-head hosted checks remain required.

## Superseded attempts and diagnosis

The earlier full run passed 1,763/1,767 tests. Its four failures were test-harness assumptions: historical Git-object paths were not allowlisted, planning-read CTests lacked the planning label, cap accounting left no gap reserve, and lifecycle recovery assertions were pinned to an older checker/count. These causes were corrected and directly tested before the final full run.

A default-sandbox focused attempt was stopped after denied `/bin/ps` calls led two documentation shards to time out. It is incomplete evidence; the final 56-test focused run passed with the test subprocesses permitted.

## Evidence boundaries

No candidate game or diagnostic fixture was fetched, admitted, or run for Phase 23 qualification. REL-01, DIAG-01, DIAG-02, and RIGHTS-01 remain Pending where their evidence gates are unresolved. This local suite does not qualify or publish v0.4.0; native hosted checks, fixture reproduction, package/consumer checks, live branch-protection eligibility, and the exact PR head remain to be observed.
