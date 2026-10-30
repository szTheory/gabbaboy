---
phase: GB-19-qualified-v0-3-0-release
reviewed: 2026-10-30T13:02:21Z
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
review_head: dedeb22a5528b0ec6bb3cb4845a535303f66ccd4
fix_round_delta: b33fa6bab36fc675cafd7d0cce7a874d501af88d..dedeb22a5528b0ec6bb3cb4845a535303f66ccd4
---

# Phase 19: Code Review Report — Approved Rescope Review

**Reviewed:** 2026-10-30T13:02:21Z
**Depth:** standard
**Files Reviewed:** 56
**Status:** clean

## Summary

This continues the single bounded resolver fix/review authorized by D-121; actual Windows validation exposed an equivalent Git installation layout before that scope was complete. The original two rounds remain recorded and no counter is reset. D-122 resolves the D-09 acknowledgment. No unrelated change, limit waiver or branch-protection bypass is authorized.

This report preserves the original 56-file Phase 19 scope and prior finding dispositions. The first approved rescope review covered `41cf7cdce42b4dc6dc1dbda8cda7c3215868d3c2..8f4deeddd07ddf06f9927a1c6c571b717732b06e`; this continuation reviews the single-file follow-up `b33fa6bab36fc675cafd7d0cce7a874d501af88d..dedeb22a5528b0ec6bb3cb4845a535303f66ccd4`. It adds the `ucrt64/bin/git.exe` Git for Windows layout to the same-root Bash resolver and one positive fixture for selecting the top-level `Git/bin/bash.exe`. No unrelated source or test contract changed, and no new correctness or security defect was verified.

This review does not claim Windows CI success. The actual hosted `windows-2022` `workflow_policy_controls` run remains required to prove the native path handling and process launch.

## Prior Findings and Dispositions

The prior findings remain resolved as documented in [Review-Fix Round 1](https://github.com/szTheory/gabbaboy/blob/33d3d63d1a079e6c4ce72b863e25033cc80c43de/.planning/phases/GB-19-qualified-v0-3-0-release/19-REVIEW.md) and [Review-Fix Round 2](https://github.com/szTheory/gabbaboy/blob/634a4c4ffa8ae0a6e4646628faf241ebd616ea0a/.planning/phases/GB-19-qualified-v0-3-0-release/19-REVIEW.md): CR-01 production release readback inventory compatibility, CR-02 prepublish frozen-inventory comparison, WR-01 path traversal in changed-path exclusion, and IR-01 judge CLI argument parsing. The API pagination concern remains unreachable through the bounded 22-asset qualification path. The shallow subject checkout versus full-history local differential remains a coverage limitation, with no subject-side ancestry query verified.

The earlier lifecycle serialization change is execution-verified on the local macOS run at `0fec185`: `release_lifecycle_controls` passed in 18.30 seconds and `release_lifecycle_post_tag_controls` passed in 23.87 seconds, with their original 60-second limits and control floors intact. That CMake content is unchanged at this rescope head.

## Initial Rescope Review at `8f4deed`

### Windows Bash resolver — no finding

**Files:** `.github/scripts/verify-workflow-policy.py:4509-4773`; `tests/cmake/ci-lanes.cmake:89-99`
**Assessment:** At `8f4deed`, the resolver obtained `git.exe` through `shutil.which`, canonicalized it, rejected an executable or installation root under `SystemRoot`/`WINDIR`, and accepted the recognized `cmd`, `bin`, `mingw64/bin`, and `usr/bin` parent layouts. It derived Bash candidates from that same root, resolved each candidate, rejected targets outside the Git root or under the Windows system root, and failed closed when Git or a bundled Bash candidate was unavailable. The normal Windows Git for Windows wrapper location, `C:\Program Files\Git\bin\bash.exe`, was the first candidate for the standard `cmd\git.exe` layout. GitHub's Windows Server 2022 runner image lists Git Bash at that location, and Git for Windows documents `bin\bash.exe` as the wrapper that sets `MSYSTEM`/`PATH` before launching `usr\bin\bash.exe` ([Windows 2022 runner image](https://github.com/actions/runner-images/blob/main/images/windows/Windows2022-Readme.md), [Git for Windows wrapper documentation](https://gitforwindows.org/git-wrapper.html)).

The new isolated resolver controls exercise three accepted Git layouts, non-Windows behavior, missing Git, missing `git.exe`, unsupported layout, a system-directory Git executable, and refusal to fall back to a WSL `System32\bash.exe`. A separate disposable symlink reproduction on this host also confirmed that a Bash candidate resolving outside the Git root is rejected. The embedded controls do not include a dedicated symlink-escape case, so that path is not protected by a persistent regression control.

The guard's three existing behavior cases remain intact and run through the selected executable: allow an untagged release rehearsal, refuse an existing release tag, and skip the tag lookup for a non-release rehearsal branch. The prior relative `git.log` plus temporary working-directory correction remains in place. No production workflow guard logic changed.

### Control-count floors — no finding

**File:** `tests/cmake/ci-lanes.cmake:89-99`
**Assessment:** At `8f4deed`, the Windows minimum increased from 421 to 426 and the POSIX minimum from 448 to 453, exactly accounting for five added negative controls on either platform. The resolver then contributed four positive controls (three supported Windows layouts plus the unchanged POSIX selection check), and the final positive count added those to the existing accepted cases. The CTest timeout remained 180 seconds; the success regex and parsed minimum-count contract remained unchanged.

The global `unittest.mock` import adds only a standard-library import to normal `--check` invocations; its patch helpers are used by the bounded self-test controls. No package dependency or unbounded work was introduced, and no performance defect is supported by the evidence.

## Validation and Limits

- At `8f4deed`, the bounded resolver controls were run directly on this POSIX host: `negative=5 positive=4`. The disposable symlink escape reproduction also failed closed.
- The executor's revision-bound local CTest log for `8f4deed` shows all five selected tests passing; `workflow_policy_controls` completed in 61.85 seconds. The configure log identifies the local environment as AppleClang/macOS. This is not Windows validation.
- The hosted Windows `workflow_policy_controls` job must still pass before the Windows path can be considered verified. The local path tests use POSIX filesystem semantics and cannot prove Windows junction, case-folding, or `CreateProcess` behavior.

## Follow-up: `ucrt64` Layout

The red case at the prior head was a valid `Git/ucrt64/bin/git.EXE` installation. The follow-up adds `ucrt64` alongside `mingw64` and `usr` in the architecture-root recognition branch (`.github/scripts/verify-workflow-policy.py:4544-4550`), updates the unsupported-layout diagnostic, and adds a fixture whose executable is `Git/ucrt64/bin/git.exe` while the selected Bash remains `Git/bin/bash.exe` (`.github/scripts/verify-workflow-policy.py:4618-4634`). The case-insensitive executable-name check already accepts `.EXE`; `git_parent.name` and `grandparent_name` are also case-folded before layout matching. Root resolution and both Git-root/SystemRoot containment checks are unchanged, so the added layout uses the same fail-closed path checks.

The prior negative and positive controls, count floors, three tag-guard cases, 180-second CTest timeout, and output/count assertions are unchanged. The current bounded resolver controls report five negatives and five positives; the self-test also passed all three tag-guard scenarios. The targeted local revision-bound `workflow_policy_controls` CTest passed in 56.18 seconds. The old resolver's rejected `ucrt64` fixture was retained as red evidence. These are not physical Windows validation: the current CTest log and configure tree are on macOS, and the earlier Windows runs at the superseded revision were canceled. Require a fresh hosted Windows run at `dedeb22` before claiming the native `ucrt64` behavior is proven. No canceled or prior-revision result is counted as green.

---

_Reviewed: 2026-10-30T13:02:21Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
