# Phase 24: Resolve remaining v0.4 evidence and verification gaps — Pattern Map

**Mapped:** 2026-11-19 (D-219 refresh)
**Files analyzed:** 9 existing checker, test, and CMake files
**Analogs found:** 6 / 6 modified source files

## File Classification

| Modified file | Role | Data flow | Closest analog | Match quality |
|---|---|---|---|---|
| `tests/scripts/verify-dense-input.py` | test utility / candidate validator | batch Git object reads and disposable repo controls | `verify-state-forks.py` Git reader and replacement-ref controls | strong |
| `tests/scripts/verify-diagnostic-evidence.py` | evidence validator | immutable snapshot reads, report validation, bounded child processes | `verify-workflow-policy-coverage.py` immutable source reader | strong |
| `tests/scripts/verify-no-phase-paths.py` | static source checker | tracked-tree scan plus AST/source-contract validation | `verify-planning-hygiene.py` finite AST and causal-control seam | exact role match |
| `tests/scripts/verify-planning-hygiene.py` | planning contract checker | immutable Git snapshot and planning-file validation | `verify-no-phase-paths.py` path-source contract and self-test seam | exact role match |
| `tests/scripts/verify-state-forks.py` | inventory CLI / test harness | immutable tree census, manifest expansion, optional test orchestration | its existing `inventory_controls` and `parse_args` paths | exact local pattern |
| `tests/scripts/verify-workflow-policy-coverage.py` | CI contract checker | pinned source reads and configured CTest inventory | `verify-diagnostic-evidence.py` Git-only environment and byte reader | strong |

No source files, test identities, or CMake registrations are proposed as new. Each row refers to tracked source; `git ls-files` confirmed the six checkers, `tests/CMakeLists.txt`, `tests/cmake/hygiene.cmake`, and `tests/cmake/ci-lanes.cmake` are tracked.

## Pattern Assignments

### `tests/scripts/verify-dense-input.py`

**Analog:** `tests/scripts/verify-state-forks.py`, lines 68–91.

**Git reader pattern:** Keep the object reader byte-oriented, disable replacements at the Git invocation, and pass an explicit child environment. Current analog:

```python
return subprocess.run(["git", "--no-replace-objects", "-C", str(repo), *args],
                      cwd=repo, env=git_environment(), input=input_bytes,
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                      check=False, timeout=timeout)
```

`verify-dense-input.py` already has the same base at lines 44–57 (`_git_environment`, `git_bytes`) and a raw-byte admission-pin contract at lines 160–196. Preserve the explicit LF/CRLF/no-terminator allowlist and keep replacement-ref, decoy, and hostile-environment controls causally tied to the actual reader (`candidate_git_context_controls`, lines 298–411). The existing test currently changes `_git_environment` via `globals()` at lines 388–399; D-219 specifically directs refactoring self-test global swaps to explicit inputs where practical, which also makes this proof surface easier to audit.

### `tests/scripts/verify-diagnostic-evidence.py`

**Analog:** `tests/scripts/verify-workflow-policy-coverage.py`, lines 176–208 and 258–262.

**Git-only subprocess boundary:** `verify-diagnostic-evidence.py` deliberately has a generic bounded `run()` at lines 175–242 and a separate `git()` that supplies `git_environment()` at lines 245–251. Keep Git-specific sanitization at that call seam; do not silently change the environment policy for unrelated child programs. The source analog uses the same direct shape:

```python
return subprocess.run(["git", "--no-replace-objects", "-C", str(root), *args],
                      cwd=root, env=git_environment(), capture_output=True,
                      check=False, timeout=timeout)
```

`verify-workflow-policy-coverage.py` then uses one `git_text(root, revision, path)` helper to reject failed immutable reads (lines 185–208, 258–262). In the diagnostic checker, the natural integration point is `git()`; its current `run(["git", "--no-replace-objects", *args], ..., env=git_environment())` is lines 245–251. Keep the bounded output and refusal shape, and add replacement/redirect controls through the synthetic-repository self-test path rather than executing any excluded game/ROM case. D-219 also requires route/archive positives and negatives remain tied to the immutable snapshot (`validate_recovery_route`, lines 656–671).

### `tests/scripts/verify-no-phase-paths.py`

**Analog:** `tests/scripts/verify-planning-hygiene.py`, lines 2260–2335 and 3058 onward.

**Finite AST contract:** Use `ast.parse`, a small enumerated set of relevant AST forms, and stable reason codes. The existing checker already has `_reflectively_writes_binding(tree, names)` (lines 501–536), `_approved_git_object_adapters(tree)` (638–695), `_validate_immutable_revision_proof(tree)` (981–1017), and `validate_planning_hygiene_source(source)` (2260–2299). These are the closest project-local patterns for binding proof and should be extended narrowly. For example, the current revision guard checks that a full-match guard precedes a Git read and rejects revision rebinding with a semantic reason:

```python
if not guard_lines or not git_read_lines or min(guard_lines) >= min(git_read_lines):
    raise LintError("REJECT planning-path-git-command: %s lost its pre-read full-commit guard" % name)
if _revision_binding_changed(function, "rev"):
    raise LintError("REJECT planning-path-git-command: %s rebinds its validated revision" % name)
```

The production self-test uses generated source mutations and checks their refusal reasons (`mutated`, `expect_accepted`, `expect_rejected`; lines 3050–3095). Follow this style for static mutants: parse and validate source without importing or executing the injected program. For CLI-level source/scan controls, preserve the existing `argparse` mutually-exclusive `--check` / `--self-test` group and main error reporting at lines 3184–3198.

### `tests/scripts/verify-planning-hygiene.py`

**Analog:** `tests/scripts/verify-no-phase-paths.py`, lines 148–180 and 2260–2335.

**Immutable Git and path proof:** `git_run(repo, *args)` centralizes a narrow environment, `--no-replace-objects`, and the existing bounded immutable-object cache (lines 221–244). `immutable_blob(repo, revision, path)` validates a full SHA before `ls-tree` and rejects non-regular blobs before reading (247–265). `read_rev(repo, rev)` validates the revision before the snapshot and callers use that same revision (320–342). Preserve these direct helpers; do not add a general Git wrapper or broaden the accepted revision shape. For D-219, make the static proof cover the runtime binding and all supported revision bindings through the caller chain, including the pinned archive identity.

**Test seam:** The direct source-only contract in `verify-no-phase-paths.py` validates the production source and then mutates in-memory source strings for causal acceptance/refusal (lines 2302–2335). Prefer explicit fixture parameters over mutating the module namespace in self-tests, as required by D-219.

### `tests/scripts/verify-state-forks.py`

**Analog:** Its own production parser and pre-effect inventory branch (`parse_args`, lines 1467–1507; `main`, 1510–1527) plus `inventory_cli_controls`, lines 848–871.

**CLI ordering pattern:** Parse, normalize `Path` inputs, then reject inventory-mode conflicts before `checked_rev`, Git reads, or output creation. The current production guard first checks every conflicting mode and input:

```python
if any(conflicting_modes) or any(value is not None for value in conflicting_inputs):
    raise ForkError("--inventory-controls is exclusive with every other mode and mode-specific input")
```

Its production-CLI negative invokes the script as a child and proves the requested output does not exist; it also retains a materialization-only positive (`inventory_cli_controls`, lines 848–870). Expand this contract to one negative per conflicting operation/input class while keeping the valid `--inventory-controls --rev ... --repo ...` positive. Use this seam rather than a helper-only assertion. Keep the current NUL-delimited, strictly decoded manifest census at lines 116–134 and its expected 153-case/exclusion controls at 780–845.

### `tests/scripts/verify-workflow-policy-coverage.py`

**Analog:** `tests/scripts/verify-diagnostic-evidence.py`, lines 158–172 and 245–262.

**Pinned source and CTest inventory pattern:** Keep immutable Git reads in a single byte-returning helper and decode only at the documented text boundary. `git_environment()` retains a small allowlist and neutralizes system/global config; `git_read()` uses `--no-replace-objects` (lines 176–188). `baseline_source`, `reviewed_policy_source`, and `git_text` verify process success and exact content digest/identity (191–218, 258–262). `_check` binds these reads to a resolved candidate, reads the configured CTest JSON inventory, and rejects missing CMake/Python cache values (3280–3320). Preserve the candidate-bound validation and don't change required test membership as part of D-219.

## Shared Patterns

### Immutable Git readers

**Sources:** `verify-state-forks.py:68–91`, `verify-dense-input.py:44–57`, `verify-diagnostic-evidence.py:158–172,245–251`, `verify-planning-hygiene.py:221–244`, `verify-workflow-policy-coverage.py:176–188`.

Use direct existing helpers with explicit `--no-replace-objects`, byte capture for immutable blobs, a minimal environment that does not inherit Git repository/index/object/namespace selectors, explicit cwd/repository, and bounded timeouts. Preserve each checker's existing output/error conventions. Test hostile redirection with a decoy and assert the intended candidate data plus untouched decoy state; avoid introducing a shared generalized wrapper.

### Static proof and causal controls

**Sources:** `verify-no-phase-paths.py:501–536,638–695,981–1017,2302–2335`; `verify-state-forks.py:780–871`.

Follow finite standard-library AST checks: identify the exact binding/call shapes the proof accepts, refuse unmodeled reflection/rebinding with a reason specific enough for the control to assert, and keep a valid source positive. Static mutants are parsed, not executed. CLI mutants run only the production command with disposable inputs and assert refusal occurs before Git or filesystem effects.

### CTest wiring and fast feedback

The existing seven focused tests are: `plan_cap` and `planning_hygiene_controls` in `tests/cmake/hygiene.cmake:71–85`; `phase22_evidence_controls` and `phase22_evidence_contract` in `tests/CMakeLists.txt:3784–3799`; `no_phase_paths_controls` and `no_phase_paths` in `tests/CMakeLists.txt:3001–3020`; and `workflow_policy_coverage_controls` in `tests/cmake/ci-lanes.cmake:144–148`. The controls go through `expect_exit.cmake` with expected status/output and explicit floors. The diagnostic control is `RUN_SERIAL` with its existing 60-second timeout; hygiene retains its 30-second limit and 125-control floor. Preserve identities, ordering, deadlines, floors and required protected contexts. Run cheap syntax, source/commit identity, and direct causal controls before these registered tests.

## No Analog Found

None for the six existing checker files. D-219 reuses existing AST, Git, argparse, self-test, and CTest patterns; it does not call for a new subsystem or dependency.

## Metadata

**Analog search scope:** the six D-219 checker sources, their existing test seams, and CTest/CMake registrations named above.
**Pattern extraction date:** 2026-11-19.
