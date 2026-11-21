# Phase 24: Resolve remaining v0.4 evidence and verification gaps — Pattern Map

**Mapped:** 2026-11-20 (D-222)
**Files analyzed:** 8 tracked analogs; 1 proposed gate path
**Analogs found:** 4 strong partial matches / 1 promotion-gate subsystem absent

## File Classification

| New/modified surface | Role | Data flow | Closest analog | Match |
|---|---|---|---|---|
| `.github/scripts/phase24-promotion-gate.py` (proposed) | local promotion utility | immutable Git reads + GitHub GETs; candidate-state decision | `.github/scripts/wait-exact-head-ci.py`, `tests/scripts/verify-review-evidence.py` | partial; no existing promotion state machine |
| `.github/scripts/wait-exact-head-ci.py` | CI waiter utility | exact-head request-response | same file; `.github/scripts/verify-release-gates.sh` | strong |
| Existing self-test/policy seam (`workflow_policy_coverage_controls`) | policy/test control | source and command validation | `tests/scripts/verify-workflow-policy-coverage.py` | exact local seam |
| `24-CLOSEOUT.md` | candidate/review/matrix evidence | append-only evidence history | same file, D-220 entries | exact local seam |

**Boundary note:** the refreshed CONTEXT/RESEARCH and the revised sole `24-01-PLAN.md` are D-222. The plan assigns the proposed gate path to T24, binds it before candidate corrections, and specifies fresh-process immutable loading and guarded invocation points. Every analog named here was confirmed tracked with `git ls-files`.

## Pattern Assignments

### `.github/scripts/phase24-promotion-gate.py` (proposed local utility)

**Immutable source loading:** use the byte-oriented Git reader and digest check in `tests/scripts/verify-workflow-policy-coverage.py:176–208,231–235` (`--no-replace-objects`, minimal Git environment, bounded subprocess, `git show <commit>:<path>`, exact SHA-256). `tests/scripts/verify-review-evidence.py:288–299` additionally checks that the executing checker bytes equal its blob at the selected immutable revision. Freeze the gate in a gate-only commit before candidate edits; the local orchestrator must load/verify/run that object, never the candidate checkout copy.

**Candidate identity and scope:** `tests/scripts/verify-dense-input.py:254–286` validates full commit identity, selected Git directory/worktree, exact `HEAD`, and pinned-commit ancestry. `tests/scripts/verify-v03-dispositions.py:186–189,214–228` shows tree resolution plus `merge-base --is-ancestor` and NUL-delimited `git diff --name-only -z` allowlisting. Bind both candidate SHA and tree; decode scope paths strictly and deny unknown paths. Reuse the bounded Git wrapper from the first excerpt rather than the unbounded subprocess calls in the latter helper.

**Current GitHub state:** `wait-exact-head-ci.py:53–64,97–125,160–200,318–325` uses argv-only `gh api`, injected fetchers, strict response shape checks, exact SHA/event/workflow matching, unambiguous newest-run selection, and list/detail identity checks. `.github/scripts/verify-release-gates.sh:1073–1090` is the repository's concrete readback example for current protection, PR base/head/state/mergeability, and check-runs. Adapt the API and identity checks in Python; require exactly the three protected contexts named by D-222 and bind each passing run to the same candidate SHA.

**Deadlines:** `wait-exact-head-ci.py:275–315` already owns a monotonic-style injected clock and fail-closed overall deadline, but its current `gh_get` subprocess at line 58 has no timeout. `tests/scripts/verify-diagnostic-evidence.py:175–242` is the bounded child-process pattern (monotonic deadline, kill on timeout/output cap, explicit failure). Pass each GitHub child only the remaining waiter budget and convert timeout/transport uncertainty into a fail-closed decision by the existing deadline; add a fake-clock/fake-fetcher timeout control.

### JSON, policy, and self-test controls

`tests/scripts/verify-review-evidence.py:106–158,318–340` rejects duplicate JSON keys, requires exact schema/role/independence, distinct reviewers, one shared reviewed SHA, and rejects post-review source drift. Adapt this for separate clean code/security receipts tied to the same SHA/tree. It validates supplied receipt content; it does not authenticate who authored it.

`wait-exact-head-ci.py:635–703` is the causal dependency-control seam. Its current duplicate fixture copies the same job ID, so `_valid_jobs_response` refuses it before the duplicate-name cardinality branch. For the D-222 correction, give the duplicate a distinct positive ID, increment `total_count`, and assert the production check rejects two jobs with the same required name. Reuse the existing waiter/policy self-test and CTest identities; do not add a new identity. `verify-release-gates.sh:815–860` is a useful positive/negative matrix for duplicate, stale, failed, omitted, and wrong-App check records.

### Candidate, review, and matrix evidence

`24-CLOSEOUT.md:502–526` records each candidate SHA/tree, review verdict/report reference, local qualification, and whether push/matrix/merge occurred. Continue that chronology per changed candidate; bind review receipts, local qualification, PR head/base, exact current context/protection readback, matrix run/attempt, and any candidate-two causal failure to the same SHA/tree. Emit a decision record stating checked identities and allow/deny reason.

## Shared Patterns and Limits

- Deny on missing, duplicate, stale, inconsistent, unreadable, or inconclusive evidence. Keep GitHub requests read-only and standard-library based; no privileged workflow over untrusted PR code.
- Candidate two is a separate state transition: require a real in-scope candidate-one matrix failure and a changed causal fix. No unchanged retry or third matrix.
- The trusted local GSD orchestrator must invoke the gate itself immediately before every authorized push, matrix start, and merge; a PR workflow is not the trust root. The guard loaded from the frozen gate-only commit controls this agent route.
- No repository-only guard can stop a separate manual bypass or a malicious PR from editing its own workflow. D-222 accepts that limit; if the independent security review requires server-side enforcement, stop before external changes. Do not alter live protection/rulesets or create a GitHub App.

## No Analog Found

No existing file combines immutable gate-code loading, candidate SHA/tree and scope validation, fresh independent reviews, current protection/context reads, and the two-candidate matrix state machine. The trusted local GSD invocation point also has no repository-only analog; it must be specified in the revised plan.

## Metadata

**Analog search scope:** tracked Python checker/waiter sources, existing release-gate API checks, Phase 23 review-evidence controls, and Phase 24 closeout history.
**Pattern extraction date:** 2026-11-20.
