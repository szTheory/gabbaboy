# Phase 22: Synthetic Composition and Diagnostic Gate Assessment — Pattern Map

**Mapped:** 2026-11-03
**Files analyzed:** 7
**Analogs found:** 7 / 7

## Scope

This map covers only the approved D-142 Windows CI remediation plan. The older Phase 22 acid2, fixture-admission, and microtest patterns remain historical context; they do not authorize real payload, build, admission, or execution work in this rescope.

The exact CTest inventory, test names, assertions, 60-second CTest limits, expected-test policy, and protected CI checks are fixed. Add focused positive and negative cases inside the existing script self-tests and CTest registrations; do not add or remove CTest names.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|------------------|------|-----------|----------------|---------------|
| `tests/scripts/verify-planning-labels.py` | utility / test-inventory linter | request-response, transform | Same file; `tests/scripts/verify-state-forks.py` path normalization | exact |
| `tests/scripts/verify-cgb-progress.py` | utility / immutable-source checker | file I/O, subprocess, batch | Same file; `tests/scripts/verify-phase8-closure-contract.py` disposable Git repository setup | exact |
| `tests/scripts/verify-diagnostic-evidence.py` | utility / evidence checker | file I/O, subprocess, batch | Same file; `tests/scripts/verify-state-horizon.py` CMake path literal | exact |
| `tests/CMakeLists.txt` | configuration / CTest registration | batch | Existing Phase 22 evidence registrations in the same file | boundary; preserve |
| `tests/cmake/ci-lanes.cmake` | configuration / CTest lane registration | batch | Existing `planning_labels_controls` registration | boundary; preserve |
| `tests/expected-tests.txt` | configuration / exact test inventory | batch | Existing immutable named inventory | boundary; preserve |
| `.planning/phases/GB-22-composition-and-microtest-evidence/22-VALIDATION.md` | validation record | transform | Existing phase validation map | update without losing prior evidence |

The three Python checkers are the likely source edits. The CMake files and expected-test list are protected integration boundaries: their current commands and inventory must continue to qualify unchanged. The validation record needs a D-142 entry while preserving its prior Phase 22 evidence.

## Pattern Assignments

### `tests/scripts/verify-planning-labels.py` — preserve exact command matching after path normalization

**Analog:** `tests/scripts/verify-planning-labels.py`, especially `is_phase22_inventory_reader()` (lines 90–121) and `self_test()` (lines 155–231).

The checker already normalizes command tokens before locating the evidence checker and validates the narrow exception by test name, labels, interpreter identity, argument order/count, source revision shape, and configured build directory. The current bug is that it then builds `tail` from the original `command` list and compares the raw path-bearing tokens against `expected_tail`. A Windows-spelled source/build directory can therefore fail even though the command was normalized earlier. This source-level cause is confirmed by the current implementation and Windows positive-control failure.

```python
normalized = [_norm(token) for token in command]
if normalized.count(expected_script) != 1:
    return False
script_index = normalized.index(expected_script)
...
tail = command[script_index + 1:]
if len(tail) != 7 or tail[:4] != expected_tail or tail[5] != "--build-dir":
    return False
```

Use the existing `_norm()` convention (convert `\\` to `/`) consistently for comparisons of path-bearing arguments while retaining exact argument count and order. Extend the current self-test with a Windows-form positive case for the same narrowly allowed inventory reader. Preserve the existing rejection cases for missing `ctest-inventory-only`, executable smuggling, another test name, extra flags, `python -c`, an absolute Python stub, and sibling paths that only resemble the build directory.

**Windows-path analog:** `tests/scripts/verify-state-forks.py` (lines 32–40, 839–841) validates repository paths in host-independent slash form and explicitly resolves a `PureWindowsPath` through Git. Keep path normalization scoped to comparison; do not loosen the exception's command shape.

### `tests/scripts/verify-cgb-progress.py` — retain isolated synthetic Git semantics and expose bounded failure detail

**Analogs:** `tests/scripts/verify-cgb-progress.py` itself (`source_history_controls()`, lines 479–578); `tests/scripts/verify-phase8-closure-contract.py` (`boundary_identity_self_test()`, lines 160–178).

The existing history control uses a temporary repository and deliberately hostile global hook/signing settings. It must continue to prove that those hooks and signing settings cannot affect synthetic history creation. The initial `git init` captures both output streams but currently maps every non-zero result to the same error without including the Git diagnostic:

```python
initialized = subprocess.run(
    ["git", "-C", str(root), "init", "--quiet"], stdin=subprocess.DEVNULL,
    stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, env=git_environment,
)
if initialized.returncode != 0:
    raise CheckError("self-test-source-history-git-init-failed")
```

The remote logs confirm the failing step, not Git's underlying error. Do not assume a cause from this message. Use the existing bounded-output subprocess pattern in `verify-diagnostic-evidence.py:92–156` if useful, and preserve sanitized, bounded diagnostics so the next Windows failure distinguishes an environment/configuration error from another Git failure. The Phase 8 disposable-repository pattern builds a minimal environment with `GIT_CONFIG_GLOBAL` and `GIT_CONFIG_SYSTEM` redirected to null and explicit fixture identity; compare it with the Phase 22 hostile-global-config control before changing isolation, because the latter's hostile hook/signing negative controls are part of the contract.

Keep the current source-history cases: commits predating the checker are skipped, stale committed checker bytes are found, absent paths are distinguished from source errors, and the global hook marker remains absent. Do not turn Git initialization into a skipped or expected-failure path.

### `tests/scripts/verify-diagnostic-evidence.py` — keep immutable policy checks, diagnose configure failures, and bound work

**Analog:** `tests/scripts/verify-diagnostic-evidence.py`, especially `run()` (lines 92–156), `check_expected_policy()` (lines 496–550), `source_archive_configure_control()` (lines 764–800), and `boundary_history_control()` (lines 921–950).

`run()` already drains stdout and stderr concurrently, caps retained output, applies the caller's existing timeout, and returns both streams. Preserve this bounded subprocess behavior. `check_expected_policy()` constructs a synthetic CMake project from the immutable `tests/expected-tests.txt` and `cmake/ExpectedTests.cmake` snapshot and applies the existing `gabbaboy_verify_registered_tests()` policy to the configured test names.

```python
cmake_exe = shutil.which("cmake")
if not cmake_exe:
    raise Reject("cmake-unavailable")
add_tests = "\n".join(
    f'add_test(NAME "{name}" COMMAND "{cmake_exe}" -E true)' for name in sorted(actual)
)
...
code, out, err = run(["cmake", "-S", str(project), "-B", str(project / "build")], project)
if code:
    output = (out + err).decode("utf-8", "replace").casefold()
    if "registered ctest cases differ" in output:
        raise Reject("configured-ctest-inventory-mismatch")
    raise Reject("expected-test-policy-failed")
```

The Windows job currently reports only `expected-test-policy-failed`; the exact CMake error is not in the report. Raw Windows executable-path insertion into a quoted CMake argument is a plausible path-escaping issue, not yet a proven cause. Preserve enough bounded configure detail to identify the error, then fix the demonstrated serialization problem. `tests/scripts/verify-state-horizon.py` provides a concrete CMake-literal pattern (`c_path_literal()`, lines 298–299): normalize backslashes to `/` and escape double quotes before inserting a path into CMake source. Keep the generated project and policy check semantically identical across platforms.

The controls also exercise immutable source-boundary checks, synthetic archive construction/configuration, and failure mutants. A synthetic source-archive configure uses an existing 50-second child limit immediately before the controls pass path; this makes it a candidate for measurement, but the Windows log does not identify which child timed out. Attribute the cost before optimizing and preserve every existing refusal and the 60-second CTest timeout. Do not increase nested or outer time limits, remove a control, or weaken timeout rejection.

### Existing CTest and inventory files — preserve the qualification boundary

**Analogs:** `tests/CMakeLists.txt` (lines 3707–3719), `tests/cmake/ci-lanes.cmake` (lines 151–166), and `tests/expected-tests.txt` (the existing entries for the Phase 22 evidence and planning-label controls).

The evidence contract and control tests are already registered and retain `TIMEOUT 60`. `planning_labels_controls` already runs the current self-test through the planning lane. New self-test cases should run inside these existing test names, preserving the Windows test count of 1,594, exact inventory policy, labels, and pass-expression assertions. Do not create replacement CTest names, expected-test additions/removals, skips, waivers, or timeout changes.

## Shared Patterns

### Keep portability changes exact

Normalize only path-bearing values before equality checks; retain identity checks, exact order/count, test-name/label restrictions, interpreter identity, immutable source revision, and every existing negative control. A Windows-form positive must pass alongside the existing POSIX-form positive, while all bypass mutants remain rejected.

### Preserve bounded subprocess diagnostics

Use the existing `run()` helper in `verify-diagnostic-evidence.py` for bounded output and existing timeouts. On failure, expose a small sanitized diagnostic tied to the specific child operation. Do not print full environment/config files or unbounded subprocess output. Keep the rejection code stable where callers assert it, or update the corresponding assertions without weakening them.

### Keep synthetic Git and CMake fixtures isolated

Temporary repositories, generated CMake projects, snapshots, and archives remain disposable synthetic test data. Preserve source-bound inputs and test-only Git configuration; do not read or modify the user's actual Git configuration, run hooks, require signing credentials, or add real diagnostic payloads.

### Test through existing CTest identities

Add causal positives and negatives to the current self-tests, then run the existing focused CTests. Preserve `tests/expected-tests.txt`, the registered names, and both existing 60-second CTest limits. The final acceptance still requires the full local suite and fresh exact-head required CI on the updated PR.

## No Analog Found

No new code module or CTest registration is authorized or needed by the approved rescope. The existing checker, CMake, subprocess, and temporary-repository patterns cover the likely changes; the remaining Git, expected-policy, and runtime causes must be established from bounded Windows evidence before choosing a fix.

## Metadata

**Analog search scope:** `tests/scripts/`, `tests/CMakeLists.txt`, `tests/cmake/ci-lanes.cmake`, and `tests/expected-tests.txt`.
**Tracked-source gate:** Every existing analog path above was confirmed with `git ls-files -- <path>`.
**Pattern extraction date:** 2026-11-03
