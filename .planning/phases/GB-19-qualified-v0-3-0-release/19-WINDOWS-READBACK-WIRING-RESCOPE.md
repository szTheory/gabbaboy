# Phase 19 bounded Windows readback-wiring repair

Status: approved under D-135. The owner answered “I approve” to this concrete tested two-file repair. Its implementation and qualification below are authorized; no new release action or general review/gap reset is granted.

## Problem and consequence

PR137's exact-head Windows push and PR jobs both fail two tests. The published v0.3.0 release and its actual22-asset record remain valid; these are new closure-test wiring failures, and the merge is stopped.

- `v03_readback` passes a `D:/...` absolute filesystem path to a reader that addresses an immutable Git tree. Git cannot find that path inside the commit, so it correctly refuses with `receipt-missing`.
- The D134 recovery test compares the published-asset helper's checkout bytes with its immutable Git blob. Windows converts this unpinned source to CRLF; the exact-byte guard correctly refuses the mismatch. The helper's code is otherwise unchanged.

The completed PR CI run's independent native jobs pass except Windows; its required-native aggregation fails accordingly. The preview consumers refuse the failed upstream exact-head CI, rather than qualifying a red revision. Their failures are dependency gates, not evidence of a new package defect. No unchanged CI rerun, merge or release edit was attempted. Exact raw/sanitized logs are retained in `build/phase19-window/posttag-recovery/prb-windows-failure/`.

## Exact proposed change

Permit one additional bounded implementation and independent recheck of exactly two existing files in the same unmerged PR137:

1. `tests/CMakeLists.txt`: derive the existing readback argument using `file(RELATIVE_PATH ...)` from `PROJECT_SOURCE_DIR` and `GBB_LIVE_PHASES_DIR`. Pass the resulting repository-relative Git path to the same reader. Keep the immutable revision, tag, expected exit/output, planning label and timeout unchanged.
2. `.gitattributes`: pin only `/.github/scripts/verify-published-release-assets.py` to LF. Preserve the exact-byte guard and the helper's immutable bytes. Do not apply a broad Python-source rule or affect the APU unpinned EOL negative fixture.

No validator or publisher code/data, test target, inventory, control floor, timeout, job, permission, dependency, product/API/state behavior, performance limit, source/policy authority or release asset changes. This corrects the caller and checkout representation; it does not relax either refusing check.

## Concrete tested prototype

- Base: reviewed PR head524ba3f7bf0614c26e00443ac6eafe162ad021ba.
- Isolated prototype:663eb583d02f06d4d32f1e7d556d575bb649a54b, under `build/phase19-window/posttag-recovery/windows-wiring-prototype`.
- Exact two-file patch: `build/phase19-window/posttag-recovery/windows-wiring-prep/windows-readback-wiring.patch`.
- Patch SHA-256: `fa768f81a6cb57157b9815f91cec689d4a03c33048b5123f13f1c1306b64aa66`.
- Detailed report: `build/phase19-window/posttag-recovery/windows-wiring-prep/README.md`, SHA-256 `caac3ffae38c835c1d3211322f763688652202d7ac362b0e6cad18df007bf769`.

Actual hosted Windows logs establish the drive-path refusal. The baseline local POSIX absolute path passes, so it is not misrepresented as Windows reproduction. The fixed CMake command emits `.planning/phases/.../19-release-readback.json`; `PureWindowsPath` confirms no drive or absolute-path component.

A forced `core.autocrlf=true` checkout reproduces the baseline helper failure:488 CRLF sequences make the checkout bytes differ from the LF Git blob, and the existing recovery test refuses. Fixed clones under both true/false autocrlf settings preserve the exact helper blob; an unpinned sibling converts to CRLF in the true setting, proving that conversion was active. The existing readback, readback-control and recovery CTests pass3/3. Missing/drive-absolute readbacks and a changed helper still refuse. Parent re-verification passes the actual22-asset readback and99-control recovery suite, confirms both artifact hashes and clean patch application, and verifies that the active PR's two files remain unchanged.

These local checks are not native Windows qualification. Fresh actual Windows and all other required checks must pass at the new reviewed head after an approved application, before merge.

## Required continuation after approval

Apply only this pinned patch on the same PR137 branch, record the decision without resetting prior rounds, and commit with explicit paths. Run the affected existing checks and preserve the original failed jobs. Obtain fresh independent code/security rechecks of the exact two-file correction and its source/checkout interfaces. Recheck final local qualification appropriate to the changed candidate, and refresh the existing final goal audit/fingerprint for the new covered source, including .gitattributes. Keep frozen19-06 and all existing SUMMARIES unchanged; record new operational evidence in the scope/continuation and final report.

Push the new source revision to PR137, require fresh exact-head hosted checks with every current required instance and concrete skipped-check coverage, then run the production check-pr guard and perform only the originally planned guarded PR B squash. Verify the immutable actual main boundary, inactive window, REL-01 positive/pending-base negative and preserved release identity. Adopt the final owner workspace while preserving owner configuration/instructions/evidence. Finalize the one remaining operational truth in the same goal audit from actual merge/handoff facts, then stop at `/gsd-verify-work 19` without running it or a milestone audit/another phase.

No further body/association PATCH, tag/release change, attachment, publication or release retry is authorized or needed; the sole retry already succeeded. No new plan/gap or general review allowance is granted. Any unrelated unresolved correctness/security finding holds for owner scope resolution. Keep authority and cited rehearsal branches.

## Why this is a new scope decision

D134 authorized an exact seven-file schema patch; .gitattributes is outside it. AGENTS.md also requires: “At most 2 review-fix rounds and 1 gap round per phase. An unresolved correctness or security finding forces a rescope, never a seed.” The existing allowance is exhausted. The least disruptive remedy is this tested two-file caller/checkout repair, with the strict guards preserved.

Recommended decision: approve the bounded two-file repair and its fresh qualification on PR137. The alternative is to keep closure stopped with the published release unchanged. No risk acceptance or further live release action is requested.
