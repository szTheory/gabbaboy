---
phase: GB-20-fixture-admission-tune-up
fixed_at: 2026-11-01T02:31:01Z
review_path: .planning/phases/GB-20-fixture-admission-tune-up/20-REVIEW.md
iteration: 2
findings_in_scope: 5
fixed: 5
skipped: 0
status: all_fixed
---

# Phase 20: Code Review Fix Report

**Fixed at:** 2026-11-01T02:31:01Z
**Source review:** `.planning/phases/GB-20-fixture-admission-tune-up/20-REVIEW.md`
**Iteration:** 2

**Summary:**
- Findings in scope: 5
- Fixed: 5
- Skipped: 0

## Fixed Issues

### CR-05: Release verification can still load a checker selected by tagged build code

**Files modified:** `.github/workflows/release.yml`, `.github/scripts/verify-workflow-policy.py`, `tests/data/workflow-policy-controls.json`, `tests/scripts/verify-release-candidate.sh`, `tests/scripts/verify-workflow-policy-coverage.py`
**Commit:** `c3562ff8`
**Applied fix:** Moved Linux release-product verification into the fresh `publish-qualified-release` job. That job checks out the trusted workflow revision under `trusted/`, downloads the five named candidate artifacts as data, then runs the trusted verifier before draft validation. The candidate verifier always chooses its checked-out sibling checker; environment overrides and `RUNNER_TEMP` cannot choose or replace that path. Two controls provide a conflicting environment value and a replaced temporary checker and confirm the trusted checker remains selected. **Fixed; requires human verification of the trust-boundary logic.**

### CR-06: A fenced code example satisfies the notice digest table check

**Files modified:** `tests/scripts/verify-fixture-admission.py`
**Commit:** `14836d5b`
**Applied fix:** The notice parser now ignores fenced Markdown blocks and HTML comments before looking for the digest table. Added matching fake-table negatives in both inactive regions. **Fixed; requires human verification of the Markdown parsing logic.**

### CR-07: Workflow policy accepts an untrusted Python executable through a PATH assignment

**Files modified:** `.github/scripts/verify-workflow-policy.py`, `tests/data/workflow-policy-controls.json`, `tests/scripts/verify-workflow-policy-coverage.py`
**Commit:** `dd334abe`
**Applied fix:** Exact workflow command checks now require the observed shell assignment vector to equal the expected vector. Added a mutation that prefixes the product check with `PATH=/tmp/attacker`; the policy rejects it. **Fixed; requires human verification of the command-validation logic.**

### WR-04: Workflow coverage self-test is pinned to the pre-fix policy source

**Files modified:** `tests/scripts/verify-workflow-policy-coverage.py`
**Commit:** `680255b3`
**Applied fix:** Updated the reviewed policy source pin to commit `dd334abec23f563f6995963a72f9cd6ac0cd9ed3` and SHA-256 `c7e8c8a41e6ee3cc60a036d4c0a3b34b50f87af0959afb1e56e0e5d43161a6a1`. Narrowly normalized the publisher token-scope text anchor in the historical mutation fixture so the baseline AST comparison accounts for that workflow structure change while retaining the other baseline checks. **Fixed.**

### WR-05: Git blob stream reads have no deadline

**Files modified:** `tests/scripts/verify-fixture-admission.py`
**Commit:** `ee4fd369`
**Applied fix:** Git blob stdout is read on a bounded reader thread while the caller enforces one deadline across stream consumption and child completion. Timeout and read failures terminate and reap the child, close the stream, and join the reader. Added a fake stalled process control that verifies timeout rejection and cleanup. **Fixed; requires human verification of the timeout and cleanup logic.**

## Verification

Verification ran in the main checkout because `.planning/config.json` sets `workflow.use_worktrees` to `false`.

- `python3 -I tests/scripts/verify-fixture-admission.py --self-test` — passed with 58 negative controls, including inactive Markdown tables and stalled-child cleanup.
- `python3 -I tests/scripts/verify-workflow-policy-coverage.py --self-test --root . --rev HEAD` — passed with 72 controls.
- `cmake -S . -B build` — passed and configured the registered coverage tests against current source revision `ee4fd369d5e318c9d416534f92aeee0d45ecd2e5`.
- Registered CTest controls `fixture_admission_controls`, `workflow_policy_group_release_jobs`, `workflow_policy_coverage`, and `workflow_policy_coverage_controls` — all passed. The release policy group covers the conflicting environment, replaced temporary checker, and PATH-assignment mutations; the coverage controls report 72 controls.
- `python3 -c` AST parsing and `git diff --check` passed for the corresponding source changes.

No fixture payloads, admission status, manifests, notice contents, or licensing decisions were changed. The work did not advance beyond Phase 20.

---

_Fixed: 2026-11-01T02:31:01Z_  
_Fixer: the agent (gsd-code-fixer)_  
_Iteration: 2_
