# Phase 24: Resolve remaining v0.4 evidence and verification gaps — Pattern Map

**Mapped:** 2026-11-18 (D-215 recovery scope)
**Files analyzed:** 3 directly reviewed checker/harness targets plus 3 existing analogs and their test wiring
**Analogs found:** 3 / 3 target files; no direct analog for bounded AST call-flow and complete derived-path containment

## Scope and authority

This map supports replanning only. D-215 selects one correction in the existing Phase 24 plan for CR-01–CR-04 and WR-01/WR-02. It does not authorize implementation, tests, configure/build, review, CI, push, or merge. Keep the D-209 dispositions (seven complete, FIXT-01 Pending), failed unreplayed Acid2 result, D-103 stop, required matrix coverage, and all later closure boundaries unchanged. Use the standard library and existing self-test/CTest identities; add no dependency or test identity.

## File Classification

| Existing target | Role | Data flow | Closest analog | Match quality |
|-----------------|------|-----------|----------------|---------------|
| `tests/scripts/verify-no-phase-paths.py` | utility / policy checker | tracked-file batch scan and AST transform | Same file's `SPELLINGS`, token-to-AST site mapping, and source-control self-tests; `verify-planning-hygiene.py` supplies immutable-source roles | Partial: scanner and causal-control seams exist; escapes, helper-parameter flow, and decoded values are not proven |
| `tests/scripts/verify-diagnostic-evidence.py` | utility / evidence validator | immutable Git object read and report transform | Same file's byte-returning `git`, `load_snapshot`, and `boundary_history_control` | Strong for immutable bytes and point-in-time histories; current/historical selection still infers mode from archive presence |
| `tests/scripts/verify-dense-input.py` | test harness / candidate validator | subprocess request-response and temporary Git/file I/O | `verify-fixture-admission.py` raw pin validation plus `verify-planning-hygiene.py:git_run` environment isolation | Partial: candidate identity and ancestry controls exist, but the helper uses text mode and inherits Git redirection variables |

## Pattern Assignments

### `tests/scripts/verify-no-phase-paths.py` (utility, tracked-file batch scan)

**Analog:** Existing AST/token/source-span and self-test machinery in the same checker, especially `_source_path_sites`, `_fixture_root_contract`, `_reader_target`, `_validate_path_readers`, and `self_test_planning_hygiene_path_contract` (lines 216–265, 292–386, 394–474, 484–604).

**AST/source-site pattern** (lines 216–265):

```python
tree = ast.parse(source, filename=PLANNING_HYGIENE_FILE)
tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
...
for hit in SPELLINGS.finditer(source):
    ...
    token = next((item for item in tokens
                  if item.type in {tokenize.STRING, getattr(tokenize, "FSTRING_MIDDLE", -1)}
                  and ...), None)
```

Keep the repository-wide lexical scan, must-scan list, exact historical JSON exception, and count allowlist controls. Extend the structural contract to inspect decoded AST string values and only narrowly supported constant construction. Do not execute source or use `ast.literal_eval` as a general evaluator. Make every current occurrence map to one exact value, source location, binding/callee role, and use; retain same-count substitution negatives.

**Containment and reader pattern** (lines 292–305, 376–474):

```python
def _is_temporary_path(node: ast.AST, roots: set[str]) -> bool:
    if isinstance(node, ast.Name):
        return node.id in roots
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        return _is_temporary_path(node.left, roots)
```

The current helper establishes only that the left side originated at an approved root; it does not inspect all suffix components. Replace that assumption with a bounded static proof over the complete expression: reject absolute components, `..`, unproven dynamic components and root rebinding, then establish lexical component containment beneath the verified disposable root. Track protected values through local call arguments to parameters and into readers; fail closed for unknown consumers instead of accepting a helper by name. Add causal tests for decoded/concatenated values, helper-parameter reads and component/root escape. Runtime filesystem symlink resolution is outside the selected finite AST seam: claim no symlink containment and add no symlink test/platform dependency. An actual symlink-based read escape revealed during execution stops as a new out-of-scope trust/correctness issue.

**Existing self-test pattern** (lines 525–604):

```python
try:
    validate_planning_hygiene_source(source)
except LintError as error:
    raise LintError("planning-hygiene path self-test: production source was rejected: %s" % error) from None
...
def expect_rejected(label: str, candidate: str, reason: str, same_count: bool = False) -> None:
    ...
    if str(error).startswith(reason):
        ...
```

Reuse the production-file positive, reason-specific rejection helper, and same-lexical-count assertion. Extend this seam; do not add a CTest identity or count-only exemption.

### `tests/scripts/verify-diagnostic-evidence.py` (immutable evidence validator)

**Analog:** Its existing byte-oriented Git and snapshot flow (lines 223–305), current route contract (603–640), and synthetic boundary controls (1173–1198).

**Git-object read pattern** (lines 223–242):

```python
def git(root: pathlib.Path, *args: str, limit: int = MAX_OUTPUT) -> bytes:
    code, out, err = run(["git", *args], root, limit=limit)
    if code:
        ...
    return out
```

```python
content = git(root, "show", f"{revision}:{path}", limit=MAX_BYTES + 1)
```

Retain full-revision Git reads and raw blob bytes. Make current recovery validation require both archived v0.4 blobs and the active root route. Historical validation should be selected only by an explicit full-revision/boundary contract, never by absence of archive files.

**Mode-selection seam:** `selected_snapshot_paths` (lines 277–289) currently branches on whether the archive pair exists. `validate_recovery_route` (630–640) also returns early when both archives are absent. Do not copy this inference into the correction: reject a missing archive pair for current candidates, while keeping explicit historical-boundary checks available.

**Reason-specific synthetic history pattern** (lines 1173–1198):

```python
def expect_reject(fn, reason: str, label: str) -> None:
    try:
        fn()
    except Reject as error:
        if str(error).startswith(reason):
            return
        raise Reject(f"control-wrong-reason:{label}:{error}") from None
    raise Reject(f"control-accepted-mutant:{label}")
```

`boundary_history_control` creates and commits a `TemporaryDirectory` Git repository, tests a historical boundary, then verifies a later route fails for the specific reason. Extend the existing `phase22_evidence_controls` contract with paired archive-removal and current-route negatives; preserve the genuine pinned historical boundary positive.

### `tests/scripts/verify-dense-input.py` (temporary candidate-Git harness)

**Analog:** Use the established sanitization in `tests/scripts/verify-planning-hygiene.py:220–223` and raw-pin validation in `tests/scripts/verify-fixture-admission.py:771–787`. Do not reuse this file's text-mode helper for integrity bytes.

**Current helper to replace or split** (`verify-dense-input.py:134–137`):

```python
def git(repo: Path, *args: str, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(repo), *args], cwd=repo, text=True,
                          input=input_text, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          check=False)
```

This helper decodes and normalizes output and inherits ambient Git variables. Preserve its human-readable call sites where suitable, but isolate the temporary Git commands from `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE`, and other repository-redirection variables; assert `--absolute-git-dir` and candidate `HEAD` identify the disposable subject.

**Sanitized environment pattern** (`verify-planning-hygiene.py:220–223`):

```python
def git_run(repo: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    env = {k: v for k, v in os.environ.items()
           if k in ("PATH", "SYSTEMROOT", "TMPDIR", "TEMP", "TMP")}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                          check=False, env=env, timeout=60)
```

Use a narrow allowlisted child environment for all temporary-repository operations, adding only required fixture configuration. Keep output binary for pins and validate raw ASCII bytes as exactly 40 lowercase hex characters, optionally no terminator, LF, or CRLF; reject bare CR and all extra bytes. `verify-fixture-admission.py:771–787` already reads the pin as bytes, decodes strict ASCII, and applies the exact `(?:\n|\r\n)?` terminator grammar before commit/ancestry checks.

The existing `active_admission_pins`, `validate_candidate_git_context`, and `candidate_git_context_controls` (lines 140–217) are the right fixture seam. Add the malformed-byte and hostile-environment cases there, asserting refusal/subject identity before configure. Preserve the separate baseline object store, Gitless negatives, and any later matrix-only execution boundary.

## Existing Test Wiring (preserve)

- `tests/CMakeLists.txt:3004–3020` registers `no_phase_paths_controls` (self-test with a 16-control floor) and `no_phase_paths` (tracked-tree scan with a 380-file floor). Reuse both names and keep the existing pass/failure contracts.
- `tests/CMakeLists.txt:3785–3799` registers `phase22_evidence_contract` and `phase22_evidence_controls`; the controls already create isolated Git history and verify exact refusal reasons.
- `tests/cmake/hygiene.cmake:73–85` registers `plan_cap` and `planning_hygiene_controls` with existing bounds; preserve the 125-control floor and 30-second timeout unless measured diagnosis justifies an in-scope same-coverage change.
- `tests/cmake/ci-lanes.cmake:147–148` registers `workflow_policy_coverage_controls`; retain its existing control identity.
- `tests/scripts/verify-planning-hygiene.py:220–223` and `tests/scripts/verify-fixture-admission.py:771–787` are analog/reference files, not new change targets for the six D-214 findings.

## Shared Patterns

### Immutable input and output

Use validated full commit identities and `git show <revision>:<path>`/`git cat-file` for facts. Keep Git blobs as bytes until a strict decoding boundary. Report specific rejection causes through the existing `Reject`/`LintError` types and prove each negative fails for the intended reason.

### Temporary Git repositories

Build fixture repositories only inside existing `TemporaryDirectory` self-tests. Remove inherited repository redirection variables, disable global/system Git config, and assert the disposable repository's Git directory and `HEAD` before trusting object or ancestry results.

### Test efficiency and scope

Run syntax, identity, and direct causal controls before focused CTests. Reuse existing controls and CTest registration; do not add dependencies or permanent checks without repeat value. Keep all required protected PR contexts; record measured queue, dependency, job/step durations and timeout headroom in Phase 24 evidence. A CI-waiter redesign remains out of scope.

## No Direct Analog Found

There is no existing source analyzer that proves (a) decoded path-value flow from local callers to helper parameters and readers and (b) containment of every dynamically composed path beneath a temporary root. Implement this as a finite, fail-closed extension of `verify-no-phase-paths.py` using Python's existing `ast`, `tokenize`, and `pathlib` machinery. Do not add an analyzer framework or dependency.

## Metadata

**Analog search scope:** `tests/scripts/`, relevant CMake test registrations, and existing planning-hygiene / fixture-admission Git helpers.
**Files read:** the three D-214 review targets, two existing Git/pin analogs, and four existing CTest registration points.
**Source tracking:** each named analog is a tracked source file (`git ls-files` returned it).
**Planning boundary:** D-215 context only; no source or test file was modified and no check was run here.
