# Phase 19 approved Windows workflow-policy harness rescope

## Observed failure

- Frozen source: `e0ca6463c3b6379fe65f28bb1fa0673be79ee071`.
- Exact-head PR CI: run [41033238701](https://github.com/szTheory/gabbaboy/actions/runs/41033238701), job `native-windows-x64` (`123987817960`).
- CTest case: `workflow_policy_controls`, 1.54 seconds, failed at case 1224/1558; the separate production `workflow_policy_check` passed in the same stream.
- Preserved job log: `build/preflight/runs/e0ca6463c3b6379fe65f28bb1fa0673be79ee071-final-20261030-e0ca6463/job-123987817960-logs-02.zip` (GitHub's completed-job endpoint returned text with ANSI/CRLF, not a ZIP archive).
- Failure text: `self-test release tag guard failed to allow an untagged release`; added diagnostics reported `exit=1 git_calls=0 log_read_error=none`, stdout `Windows Subsystem for Linux has no installed distributions`, and empty stderr.
- Source trace: `.github/scripts/verify-workflow-policy.py` invokes `subprocess.run(["bash", "-c", ...])` in `rehearsal_tag_guard_controls` (around line 4523). The bare `bash` resolves to the Windows WSL app-execution alias on this hosted runner rather than Git for Windows Bash. The fake Git function and relative `TAG_GIT_LOG` were never reached.

## Approved bounded scope

The second formal review-fix round was closed and E0 was frozen before this independent Windows failure arrived. The project AGENTS.md caps review-fix rounds at two and requires a rescope when correctness remains unresolved. The owner explicitly approved the recommended bounded rescope on 2026-10-30; D-121 records the exception.

The approved change is limited to the test harness shell resolver and its existing CTest control floor:

**Exception budget:** one additional consolidated source-fix round and independent re-review, followed by complete platform CI and a coherent synthetic preflight at the settled head. The two earlier rounds remain recorded; their count is not reset. Any further unresolved correctness or security finding stops this scope for another owner decision.

1. On Windows, resolve Git for Windows' `bash.exe` deterministically from the resolved Git executable's installation root (`.../Git/cmd/git.exe` → `.../Git/bin/bash.exe`, or the equivalent bundled `bin` layout). Do not select `System32\\bash.exe` / the WSL alias. On non-Windows, retain the existing `bash` lookup.
2. Fail closed with the selected candidate and lookup result if no supported Bash executable exists; never skip the Windows control and never reinterpret an unavailable shell as a passing guard check.
3. Add durable resolver controls: a positive invocation using a seeded supported executable path, plus negative cases for a missing executable and an alias/unsupported candidate. Keep the three existing real guard assertions intact: untagged rehearsal passes and records one fake Git call, existing v0.3.0 tag refuses and records one call, and unrelated rehearsal branch skips Git. Keep all captured stdout/stderr/exit/log-count diagnostics.
4. Re-run the control locally, then require the complete registered `workflow_policy_controls` suite and full Windows test inventory to pass on a real hosted Windows runner, including all three real tag-guard scenarios and the new resolver controls. Use measured control counts. No Bash package install, production guard change, timeout change, assertion/count weakening, main push, version window, tag, or release publication.

This exception would be limited to the identified test-harness process-resolution defect. Any unrelated CI failure or additional correctness/security finding would require a new rescope rather than expansion of this proposal. The owner also acknowledged the separate D-09 amendment; D-122 records that decision. All automated merge and release gates remain mandatory.

## Current execution facts

- E0 H0/H1/H-prime: `59ed280652edbe683aa68650f0817885333677de` / `2c6c8a675a9aece27cd8cd598a71470b4f7451d7` / `58b51a707834db51a175d66723c4b5d0d8a8d878`.
- Fresh local H-prime gates passed: installed-prefix CTest 1690/1690, CGB 107/107, Release player 108/108, Debug plus linkage 110/110.
- E0 rehearsal [41034255964](https://github.com/szTheory/gabbaboy/actions/runs/41034255964) completed all six producer lanes; the exact judge outcome matched the local prediction, the W-equivalent fixed point passed, and the transient branch was deleted. These are E0 facts, not qualification of the forthcoming fixed source.
- PR #133 remains unmergeable at E0 because both exact-head CI runs failed the Windows harness; preview smoke failed downstream. Continue plan 19-06 at the approved fixed source, then merge only after fresh required evidence and branch protection pass. Plan 19-07 starts only after the guarded PR A merge and #131 regeneration.

The resolver scope itself makes no main/tag/publication change. The original guarded Phase 19 merge and release sequence remains authorized after its required evidence and branch protection pass; stop at the Phase 19 execution boundary.

## In-scope platform-validation evidence

The first candidate's actual b33 Windows check revealed `Git/ucrt64/bin/git.EXE`, an equivalent bundled layout covered by this approved scope. Its correction is `dedeb22a5528b0ec6bb3cb4845a535303f66ccd4`: the existing root mapping includes ucrt64 and one positive fixture proves top-level `Git/bin/bash.exe` selection. The old immutable resolver rejects that valid layout; the correction passes. Negative controls, floors, production guards and timeouts are unchanged. This is completion of the same resolver validation, not a fourth round or a budget reset. Actual fresh Windows CI remains required; canceled b33 runs supply no completion evidence.
