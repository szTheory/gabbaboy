# Phase 23 Qualification Evidence

## Revisions

| Identity | Commit | Meaning |
|---|---|---|
| Reviewed implementation | `0a7b2b37644f20e43da813b67561587bbd0f86e5` | Exact source read by the three independent reviewers. |
| Review evidence | `e4fec7198d8488b4c0271a1363695e8c395248d3` | Commit containing the three reports bound to the reviewed implementation. |
| Local qualification run | `e4fec7198d8488b4c0271a1363695e8c395248d3` | Exact configured source used for the focused selection and final full relocated run. |

The review-evidence gate passed at the qualification commit. The evidence-only candidate remains subject to live required checks for its exact PR head before merge. The v0.4.0 version PR, tag, and publication are outside this phase task.

## Local verification

| Check | Result |
|---|---|
| `cmake --preset cmake-3.25.3-relocated` | Passed at `e4fec719`; CMake recorded the report-bound source revision. |
| `cmake --build build-cmake-3.25.3-relocated --parallel 4` | Passed at `e4fec719` (339 build steps). |
| Review-evidence self-test | Passed: 33 positive cases and 28 controls at implementation `0a7b2b37`. |
| Real review-evidence gate | Passed at qualification `e4fec719`: 3 independent reports, 46 findings, no open correctness/security or high/critical/blocking finding. SEC-23-09 remains a low-severity availability note. |
| Focused Phase 23 selection | Passed 55/55 in 429.81 seconds with four CTest workers. It covered all 32 docs-control shards, report and release/consumer controls, fixture policy, planning checks, and the relocated CMake-floor contract. |
| Full relocated CTest suite | Passed 1,774/1,774 in 841.80 seconds with four workers at `e4fec719`. The installed-tree JUnit inventory check verified 1,774 executed cases and none skipped. |
| Test-budget check | Passed for 1,774 tests; 120 timeout rows are allowlisted and 11 player rows are skipped by the existing budget policy. |
| Planning-label inventory | Passed: 1,774 tests, 64 labelled planning. Its self-test passed 27 controls. |
| CMake-floor policy | Self-test passed 63 controls; live policy check and `bash -n .github/scripts/verify-cmake-floor.sh` passed. The registered relocated CTest passed in both focused and full runs. |

The focused log is `/private/tmp/phase23-focused-e4fec719.log`. The successful full log is `/private/tmp/phase23-full-e4fec719.log`. CTest wrote JUnit to `build-cmake-3.25.3-relocated/build-cmake-3.25.3-relocated/phase23-floor-final.xml`; its installed inventory verification passed. Build outputs and logs are local evidence, not source inputs.

## Sandbox diagnosis

The first full attempt in the default sandbox completed 1,769 tests and reported five failures. Four performance/review tests could not create temporary Git worktrees because the sandbox denied writes under `.git`; the delivery control then saw the checkout error instead of its intended malformed-evidence refusal. The five affected tests passed 5/5 when rerun with Git metadata access, then the complete relocated suite passed 1,774/1,774 under that same access. No source change was needed for this environment issue.

## CI efficiency and hosted evidence

Two earlier hosted CMake-floor runs at `4183ea298bd134578576bdb186b29ba4661dd6b3` exposed that the job ran the full suite on both the base and relocated builds. On slow hosted runners, the additional Phase 23 docs controls pushed CTest past its 90-second per-test limit and left the 40-minute job with little headroom. The floor script now keeps its focused adapter and no-host-clock checks on the base tree, installs and relocates the package, then runs the complete expected inventory once on the relocated build. It also verifies the installed JUnit inventory. The floor-policy checker pins the 3.25.3 tools, required build/install order, one canonical unfiltered relocated CTest invocation, and installed inventory check.

The local macOS run verifies the configured test suite and installed consumers; it does not execute the Linux x86_64 CMake 3.25.3 download/build job. Current exact-head hosted results, queue and dependency waits, and release-gate eligibility are pending until the current PR candidate has completed its required workflows.

## Evidence boundaries

No candidate game or diagnostic fixture was fetched, admitted, or run for Phase 23 qualification. REL-01, DIAG-01, DIAG-02, and RIGHTS-01 remain Pending where their evidence gates are unresolved. Local tests do not qualify or publish v0.4.0; exact-head hosted checks, fixture reproduction, package/consumer checks, and live branch-protection eligibility remain required.
