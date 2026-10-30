---
phase: GB-19-qualified-v0-3-0-release
reviewed: 2026-10-30T12:20:50Z
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
  warning: 0
  info: 0
  total: 0
status: clean
review_base: f80bdf54c6c7d81e8e21f0275b43cda6edf6c8c4
review_head: 8f4deeddd07ddf06f9927a1c6c571b717732b06e
fix_round_delta: 41cf7cdce42b4dc6dc1dbda8cda7c3215868d3c2..8f4deeddd07ddf06f9927a1c6c571b717732b06e
---

# Phase 19: Code Review Report — Approved Rescope Review

**Reviewed:** 2026-10-30T12:20:50Z
**Depth:** standard
**Files Reviewed:** 56
**Status:** clean

## Summary

This is the single additional review authorized by owner decision D-121 after the two recorded rounds. D-122 records the owner's D-09 acknowledgment. Neither decision waives actual Windows CI, source-bound performance evidence, final preflight or branch protection.

Reviewed the exact two-file delta `41cf7cdce42b4dc6dc1dbda8cda7c3215868d3c2..8f4deeddd07ddf06f9927a1c6c571b717732b06e`, preserving the original 56-file Phase 19 source scope and prior finding dispositions. The only behavior change is the Windows Bash selection used by the workflow-policy guard controls, plus registration of its added control counts. The recognized paths cover the Git for Windows layouts used by `cmd`, `bin`, `mingw64`, and `usr`; resolved Bash candidates must stay inside the resolved Git root and outside the Windows system root. The POSIX executable choice remains the literal `bash`. No new correctness or security defect was verified.

This review does not claim Windows CI success. The actual hosted `windows-2022` `workflow_policy_controls` run remains required to prove the native path handling and process launch.

## Prior Findings and Dispositions

The prior findings remain resolved as documented in [Review-Fix Round 1](https://github.com/szTheory/gabbaboy/blob/33d3d63d1a079e6c4ce72b863e25033cc80c43de/.planning/phases/GB-19-qualified-v0-3-0-release/19-REVIEW.md) and [Review-Fix Round 2](https://github.com/szTheory/gabbaboy/blob/634a4c4ffa8ae0a6e4646628faf241ebd616ea0a/.planning/phases/GB-19-qualified-v0-3-0-release/19-REVIEW.md): CR-01 production release readback inventory compatibility, CR-02 prepublish frozen-inventory comparison, WR-01 path traversal in changed-path exclusion, and IR-01 judge CLI argument parsing. The API pagination concern remains unreachable through the bounded 22-asset qualification path. The shallow subject checkout versus full-history local differential remains a coverage limitation, with no subject-side ancestry query verified.

The earlier lifecycle serialization change is execution-verified on the local macOS run at `0fec185`: `release_lifecycle_controls` passed in 18.30 seconds and `release_lifecycle_post_tag_controls` passed in 23.87 seconds, with their original 60-second limits and control floors intact. That CMake content is unchanged at this rescope head.

## Rescope Review

### Windows Bash resolver — no finding

**Files:** `.github/scripts/verify-workflow-policy.py:4509-4773`; `tests/cmake/ci-lanes.cmake:89-99`
**Assessment:** The resolver obtains `git.exe` through `shutil.which`, canonicalizes it, rejects an executable or installation root under `SystemRoot`/`WINDIR`, and accepts only the recognized `cmd`, `bin`, `mingw64/bin`, and `usr/bin` parent layouts. It derives Bash candidates from that same root, resolves each candidate, rejects targets outside the Git root or under the Windows system root, and fails closed when Git or a bundled Bash candidate is unavailable. The normal Windows Git for Windows wrapper location, `C:\Program Files\Git\bin\bash.exe`, is the first candidate for the standard `cmd\git.exe` layout. GitHub's Windows Server 2022 runner image lists Git Bash at that location, and Git for Windows documents `bin\bash.exe` as the wrapper that sets `MSYSTEM`/`PATH` before launching `usr\bin\bash.exe` ([Windows 2022 runner image](https://github.com/actions/runner-images/blob/main/images/windows/Windows2022-Readme.md), [Git for Windows wrapper documentation](https://gitforwindows.org/git-wrapper.html)).

The new isolated resolver controls exercise three accepted Git layouts, non-Windows behavior, missing Git, missing `git.exe`, unsupported layout, a system-directory Git executable, and refusal to fall back to a WSL `System32\bash.exe`. A separate disposable symlink reproduction on this host also confirmed that a Bash candidate resolving outside the Git root is rejected. The embedded controls do not include a dedicated symlink-escape case, so that path is not protected by a persistent regression control.

The guard's three existing behavior cases remain intact and run through the selected executable: allow an untagged release rehearsal, refuse an existing release tag, and skip the tag lookup for a non-release rehearsal branch. The prior relative `git.log` plus temporary working-directory correction remains in place. No production workflow guard logic changed.

### Control-count floors — no finding

**File:** `tests/cmake/ci-lanes.cmake:89-99`
**Assessment:** The Windows minimum increases from 421 to 426 and the POSIX minimum from 448 to 453, exactly accounting for five added negative controls on either platform. The new resolver contributes four positive controls (three supported Windows layouts plus the unchanged POSIX selection check), and the final positive count adds those to the existing accepted cases. The CTest timeout remains 180 seconds; the success regex and parsed minimum-count contract remain unchanged.

The global `unittest.mock` import adds only a standard-library import to normal `--check` invocations; its patch helpers are used by the bounded self-test controls. No package dependency or unbounded work was introduced, and no performance defect is supported by the evidence.

## Validation and Limits

- The bounded resolver controls were run directly on this POSIX host: `negative=5 positive=4`. The disposable symlink escape reproduction also failed closed.
- The executor's revision-bound local CTest log for `8f4deed` shows all five selected tests passing; `workflow_policy_controls` completed in 61.85 seconds. The configure log identifies the local environment as AppleClang/macOS. This is not Windows validation.
- The hosted Windows `workflow_policy_controls` job must still pass before the Windows path can be considered verified. The local path tests use POSIX filesystem semantics and cannot prove Windows junction, case-folding, or `CreateProcess` behavior.

---

_Reviewed: 2026-10-30T12:20:50Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
