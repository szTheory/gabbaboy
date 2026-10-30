---
phase: GB-19-qualified-v0-3-0-release
reviewed: 2026-10-30T09:17:06Z
depth: standard
files_reviewed: 56
files_reviewed_list:
  - .github/ci-timeouts.json
  - .github/scripts/release-evidence-lifecycle.sh
  - .github/scripts/verify-published-release-assets.py
  - .github/scripts/verify-release-source-proof.py
  - .github/scripts/verify-test-inventory.sh
  - .github/scripts/verify-workflow-policy.py
  - .github/workflows/ci.yml
  - .github/workflows/libbet-repro.yml
  - .github/workflows/release-rehearsal.yml
  - .github/workflows/release.yml
  - .github/workflows/version-pr-gate.yml
  - CHANGELOG.md
  - cmake/CheckContractRevWiring.cmake
  - cmake/ExpectedTests.cmake
  - cmake/ResolveContractRevision.cmake
  - docs/native-integration.md
  - docs/release.md
  - docs/state-format.md
  - docs/support/unreleased.md
  - src/core/gabbaboy.c
  - tests/CMakeLists.txt
  - tests/baseline/perf-attribution-v1.json
  - tests/cmake/ci-lanes.cmake
  - tests/cmake/host-contract.cmake
  - tests/cmake/hygiene.cmake
  - tests/cmake/perf.cmake
  - tests/cmake/save-formats.cmake
  - tests/data/release-api/SOURCES.md
  - tests/data/release-api/captured.json
  - tests/data/state-forks.json
  - tests/data/support-claims-v0.3.json
  - tests/expected-tests.txt
  - tests/player/CMakeLists.txt
  - tests/scripts/run-perf-gate.sh
  - tests/scripts/test_installed_host.py
  - tests/scripts/verify-changelog-heading.py
  - tests/scripts/verify-doc-links.py
  - tests/scripts/verify-judge-outcome.py
  - tests/scripts/verify-no-interop-claims.py
  - tests/scripts/verify-perf-gate.py
  - tests/scripts/verify-phase3-player.sh
  - tests/scripts/verify-planning-hygiene.py
  - tests/scripts/verify-release-lifecycle.py
  - tests/scripts/verify-state-contract.py
  - tests/scripts/verify-state-forks.py
  - tests/scripts/verify-state-mutants.py
  - tests/scripts/verify-state-pins.py
  - tests/scripts/verify-support-ledger.py
  - tests/scripts/verify-v02-adoption.py
  - tests/scripts/verify-v02-consumers.py
  - tests/scripts/verify-v02-delivery.py
  - tests/scripts/verify-v02-fuzz.py
  - tests/scripts/verify-v03-dispositions.py
  - tests/scripts/verify-version-window.py
  - tests/test_state_codec.c
  - tests/test_state_fork.c
findings:
  critical: 0
  warning: 1
  info: 0
  total: 1
status: issues_found
review_base: f80bdf54c6c7d81e8e21f0275b43cda6edf6c8c4
review_head: 0fec185016ae4d3578b641ffc694aafdd1d8795c
fix_round_delta: ec56d260df555d68ddf003adf7c5224bfd65ee1f..0fec185016ae4d3578b641ffc694aafdd1d8795c
execution_head: e0ca6463c3b6379fe65f28bb1fa0673be79ee071
---

# Phase 19: Code Review Report — Review-Fix Round 2

**Reviewed:** 2026-10-30T09:17:06Z
**Depth:** standard  
**Files Reviewed:** 56  
**Status:** unresolved Windows execution finding; owner rescope required

## Summary

Re-reviewed the exact two-file round-two delta `ec56d260df555d68ddf003adf7c5224bfd65ee1f..0fec185016ae4d3578b641ffc694aafdd1d8795c` in the context of the original 56-file Phase 19 scope. The changes correct the workflow-policy self-test's temporary Git log path for Windows Bash and serialize two POSIX release lifecycle control suites. The count assertions and 60-second timeout values are unchanged. No new correctness or security finding was verified. This is a source review disposition; it does not substitute for completion of the pending CTest run or hosted Windows CI.

**Subsequent execution finding, recorded by the orchestrator:** Windows CI at E0 disproved the proposed path fix as a sufficient remedy. CI-02 below remains open. Both permitted formal fix rounds are used; the proposed interpreter-selection correction requires the owner's explicit bounded rescope. No third source fix or third review round has been performed.

## Prior Findings and Dispositions

The three original findings and the judge CLI integration mismatch remain resolved as documented in [Review-Fix Round 1](https://github.com/szTheory/gabbaboy/blob/33d3d63d1a079e6c4ce72b863e25033cc80c43de/.planning/phases/GB-19-qualified-v0-3-0-release/19-REVIEW.md): CR-01 production readback inventory compatibility, CR-02 immediate prepublish frozen-inventory comparison, WR-01 path traversal in changed-path exclusion, and IR-01 judge CLI argument parsing.

The API pagination concern remains not a finding: the qualified release inventory is bounded to 22 names and the final-gate and prepublish equality checks reject a truncated or changed list. The shallow subject checkout versus full-history local differential remains a coverage limitation; no ancestry-dependent Git query on subject was verified.

## Round 2 CI Integration Dispositions

### CI-01: Parallel lifecycle control timeouts — source correction and targeted execution verified

**File:** `tests/CMakeLists.txt:5557-5582`
**Disposition:** `release_lifecycle_controls` and `release_lifecycle_post_tag_controls` now have `RUN_SERIAL TRUE`, which keeps either control suite from overlapping other CTest cases and keeps the two suites from overlapping each other. Their existing `TIMEOUT 60`, output regexes, and minimum control counts (95 and 80) are unchanged. This addresses the reported contention path without weakening the test contract. It does not protect against an individual suite exceeding 60 seconds when run alone. The executor's targeted CTest log showed `workflow_policy_controls` passing in 45 seconds and had started `release_lifecycle_controls`; the lifecycle results were not complete in the evidence observed for this review. Completion of both lifecycle controls remains required before treating this correction as execution-verified.

**Subsequent executor verification, reconciled by the orchestrator:** the run with `--parallel 4` at immutable `0fec185016ae4d3578b641ffc694aafdd1d8795c` completed all three controls: workflow policy 45.00s, lifecycle 18.30s and post-tag 23.87s, with zero failures. The log shows the serial suites starting after preceding tests completed. The existing 60-second limits and semantic assertions remain intact. `test-budget` passed against immutable base `f80bdf54c6c7d81e8e21f0275b43cda6edf6c8c4`, its 54 self-test controls passed, the inventory self-test includes missing-test rejection, and Python 3.10 grammar parsing passed. Local evidence is retained in ignored `build/preflight/review/round2-0fec185/`. Final-head remote CI and the repeated coherent preflight remain required.

### CI-02: Windows workflow-policy shell selection — OPEN; round-two correction insufficient

**File:** `.github/scripts/verify-workflow-policy.py:4520-4558`
**Disposition:** The harness now passes the relative name `git.log` and starts Bash with the temporary directory as its working directory. The stub writes to that relative file, and Python reads the corresponding native temporary-directory path, avoiding the prior absolute Windows path crossing into Git Bash. All three guard cases remain asserted: untagged release rehearsal is allowed with one Git call, an existing release tag is refused with one Git call, and a non-release rehearsal branch skips the lookup. Read failures are now explicit and diagnostics include exit status and captured output. The production workflow guard at `.github/workflows/release-rehearsal.yml:350-361` is unchanged. The local targeted `workflow_policy_controls` run passed, but this review did not execute it and that local result does not prove Windows portability. The hosted Windows `workflow_policy_controls` job remains mandatory and pending.

**Actual target-platform result:** [PR CI job 123987817960](https://github.com/szTheory/gabbaboy/actions/runs/41033238701/job/123987817960) and [push CI job 123987812944](https://github.com/szTheory/gabbaboy/actions/runs/41033231735/job/123987812944), both at `e0ca6463c3b6379fe65f28bb1fa0673be79ee071`, failed `workflow_policy_controls`. The new diagnostic is `exit=1 git_calls=0 log_read_error=none`, with stdout `Windows Subsystem for Linux has no installed distributions` and empty stderr. Bare `bash` selected a WSL launcher before the fake Git function or log sink ran. Git for Windows Bash is present: the same job's shell banner names its bundled Bash executable. A relative log path therefore did not address the interpreter-selection defect.

The bounded proposal in ignored `build/preflight/review/19-WINDOWS-RESCOPE.md` selects Git for Windows' bundled interpreter explicitly, adds deterministic selection/refusal controls, retains all real tag scenarios, and requires the full Windows inventory to pass. It is proposed work only; approval remains pending. Production release guards and timeout limits remain unchanged. PR #133 is unmergeable. The separate D-09 acknowledgment also remains pending.

---

_Reviewed: 2026-10-30T09:17:06Z_
_Reviewer: the agent (gsd-code-reviewer)_  
_Depth: standard_
