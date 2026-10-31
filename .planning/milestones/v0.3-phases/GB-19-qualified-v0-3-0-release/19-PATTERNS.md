# Phase 19: Qualified v0.3.0 Release - Pattern Map

**Mapped:** 2026-10-29
**Files analyzed:** 39 classified rows (each row may group related files; 8 are new files, 31 are edits)
**Analogs found:** 39 / 39 rows at role-match or better; 3 sub-pieces have no in-repo analog (listed under "No Analog Found")
**Tracked-source gate (#3645):** every analog path below was checked with `git ls-files` and is tracked. None is under `.gsd/capabilities/`. No mirror path is emitted.
**Basis:** `19-CONTEXT.md` D-01..D-30 and `19-RESEARCH.md` ("Plans: files, CTests, wiring and overlaps", "Anchor Verification"). Line numbers were re-read this session at branch head `cc3460a4`. Where RESEARCH already gave a line, it is repeated only if it was re-verified.

## File Classification

| New/Modified File | Plan | Role | Data Flow | Closest Analog | Match |
|---|---|---|---|---|---|
| `.github/ci-timeouts.json` | 19-01 | config (ledger data) | batch / validated input | its own normal rows, e.g. `release.yml:candidate-performance` | exact |
| `.github/scripts/verify-workflow-policy.py` (ledger schema, `verify_cited`, mutants) | 19-01 | checker | request-response (REJECT code) | same file `judge_timeout_ledger` 2257-2302, `_ledger_mutations` 3568-3610 | exact |
| `.github/workflows/release-rehearsal.yml` (judge checkout depth) | 19-01 | workflow | event-driven | same file `judge` job 330-400 | exact |
| `tests/cmake/ci-lanes.cmake` (floor 394/375) | 19-01 | config | batch | same file 92-99 | exact |
| `tests/player/CMakeLists.txt` | 19-01 | build config | batch | `tests/cmake/host.cmake` 300-310 (`hostvariant`) | exact |
| `tests/scripts/verify-phase3-player.sh` | 19-01 | script | batch | same file 471 | exact |
| `.github/workflows/ci.yml` (budget step, `persist-credentials`) | 19-02 | workflow | event-driven | `release.yml` 1169-1171 (`git show "${GITHUB_SHA}:..."` trusted copy) | role-match |
| `.github/workflows/libbet-repro.yml` | 19-02 | workflow | event-driven | `perf-attribution.yml` 24-28 (`persist-credentials: false`) | exact |
| `tests/scripts/verify-v02-fuzz.py` (`SOURCE_FILES`) | 19-02 | checker | transform | same file 45-63 | exact |
| `src/core/gabbaboy.c` (`state_apply`, `state_store_host_value`) | 19-02 | core service | transform | same file 4145-4189, 4231-4240, 4723-4769 | exact |
| `tests/CMakeLists.txt` (new `state_refusal_mutant_*`) | 19-02 | test registration | batch | same file `gbb_state_refusal_mutant` 5390-5436 | exact |
| `tests/data/support-claims-v0.3.json` (NEW) | 19-03 | managed input | validated input | `tests/data/release-disclosure.json` via `validate_disclosure` | exact |
| `tests/scripts/verify-support-ledger.py` (`render_v3_ledger`, claims validator) | 19-03 | generator + checker | transform | same file `render_v2_ledger` 1075-1149, `validate_disclosure` 2731-2777 | exact |
| `tests/scripts/verify-v02-adoption.py` (v0.3 notes rules) | 19-03 | checker | request-response | same file 587-625, 731-784 | exact |
| `tests/scripts/verify-no-interop-claims.py` | 19-03 | checker | request-response | same file 35-110 | exact |
| `tests/scripts/verify-version-window.py` (`REQUIRED_MANAGED_INPUTS`) | 19-03 / 19-04 | checker | request-response | same file 47-53, 339 | exact |
| `tests/cmake/host-contract.cmake` (`files=6` -> bump, `unreleased_host_entries`) | 19-03 / 19-06 | test registration | batch | same file 131-155, 221-226 | exact |
| `.github/scripts/verify-release-source-proof.py` (`pr_head`, `not_after`) | 19-04 | trusted judge | request-response | same file `validate_rehearsal_run` 123-146 | exact |
| `.github/workflows/release.yml` (`candidate` step ~141-163, `candidate-fuzz` 1056-1131) | 19-04 / 19-05 | workflow | event-driven | same file | exact |
| `.github/scripts/release-evidence-lifecycle.sh` (nightly-gate, profile string) | 19-04 / 19-05 | script | request-response | same file 307-328, 255-278 | exact |
| NEW pre-tag gate workflow (`pull_request`) | 19-04 | workflow | event-driven | `release-please.yml` job `version-window` 55-140 | role-match |
| `.github/workflows/release-rehearsal.yml` (refuse if tag exists) | 19-04 | workflow | request-response | `release.yml` 105-114 (`gh api .../commits/$RELEASE_TAG`, `.../releases` guard) | role-match |
| `tests/scripts/verify-version-window.py` (D-20 rule) | 19-04 | checker | request-response | same file `check_tracked` 379-390, `check_window` 314-315 | exact |
| `tests/scripts/verify-release-lifecycle.py` (new endpoints, captures) | 19-04 | replay harness | request-response | same file `api()` 390-446, `c_capture_contract` 1323-1362 | exact |
| `tests/data/release-api/captured.json`, `SOURCES.md` | 19-04 | fixture | batch | `SOURCES.md` table + digest line | exact |
| `.github/workflows/release-rehearsal.yml` (package host smoke) | 19-05 | workflow | batch | same file `package` 186-243 | exact |
| `tests/scripts/verify-perf-gate.py` (`--emit-receipt`, `--verify-receipt`) | 19-05 | checker | transform | same file `evaluate` 409-459, `main` 1290-1349 | role-match |
| `tests/scripts/run-perf-gate.sh` (write receipt) | 19-05 | script | file-I/O | same file `evaluate_tree` 146-199 | exact |
| `.github/workflows/ci.yml` `perf-gate` (upload step) | 19-05 | workflow | file-I/O | `ci.yml` 476-485 (`v02-fuzz` upload) | exact |
| `tests/scripts/verify-v02-delivery.py` (`validate_consumer_receipt`) | 19-05 | checker | request-response | same file 222-248 | exact |
| `tests/scripts/test_installed_host.py`, `verify-v02-consumers.py` | 19-05 | test harness | request-response | same files | exact |
| `tests/scripts/verify-v03-dispositions.py` (`--check-readback`) | 19-05 | checker | request-response | same file `check_readback` 244-255 | exact |
| `tests/cmake/perf.cmake` (receipt controls CTest) | 19-05 | test registration | batch | same file 46-76 | exact |
| `docs/release.md`, `docs/native-integration.md`, `docs/support/unreleased.md`, `docs/state-format.md` | 19-06 | docs | n/a | existing text; pins in `verify-v02-adoption.py` 250-260 | exact |
| `CHANGELOG.md` + NEW first-heading checker + CTest | 19-06 | checker | request-response | `verify-no-interop-claims.py` (single-purpose `--rev` doc scan) | role-match |
| NEW docs link check + CTest | 19-06 | checker | request-response | `verify-no-interop-claims.py` | role-match |
| `tests/data/state-compatibility.json` `release-change` row (window only) | 19-06 draft / 19-07 | data | validated input | `verify-state-pins.py` 296-300 | exact |
| `tests/data/version-window.json` (record W, then inactive) | 19-07 | managed record | batch | `verify-version-window.py` `draft_record` 332-361 | exact |
| readback receipt JSON (PR B) | 19-07 | receipt | file-I/O | `16-release-readback.json` shape in `verify-v03-dispositions.py` 398-399 | exact |

## Pattern Assignments

### Priority analog 1: `--self-test` mutant / negative-control block

**Primary analog:** `tests/scripts/verify-support-ledger.py` `self_test_disclosure` (2925-3058). Copy for the D-14 claims controls. It runs an unrelated positive beside every control so a crash cannot pass as a rejection.

```python
# 2959-2968: the control harness (count only when the reason matches)
def expect_rejected(name: str, action, reason: str) -> None:
    nonlocal controls
    try:
        action()
    except ValueError as error:
        if reason not in str(error):
            fail(f"disclosure control {name} was rejected for the wrong reason: {error}")
    else:
        fail(f"disclosure control {name} was accepted")
    controls += 1

def mutated(change) -> dict:
    value = copy.deepcopy(disclosure)
    change(value)
    return value
```

```python
# 2979-2986: omission and unclassified-field controls (model for claim-scope-missing, extra claim field)
expect_rejected("omit-historical-block", validate(mutated(lambda v: v.pop("historical"))),
                "disclosure-input-invalid")
expect_rejected("unclassified-readiness-field",
                validate(mutated(lambda v: v["historical"].update(approved=True))), "unclassified field")
expect_rejected("boolean-for-count",
                validate(mutated(lambda v: v["historical"].update(warmups=True))), "warmups")
```

```python
# 3010-3019 and 3031-3041: well-formed input that only the generator fixed point can reject (D-14 control 9)
altered = mutated(lambda v: v["historical"].update(delta_percent="14.87"))
validate_disclosure(altered, root)          # positive first: the edit is valid input
...
reworded = text.replace("## Reconciled prior scope entries", "## Reconciled earlier scope entries", 1).encode("utf-8")
run_adoption_over_ledger(ledger_rel, reworded, root)     # every required phrase present, adoption passes
expect_rejected("handwritten-prose-edit",
                lambda: require_generated(reworded, ledger_rel, "0.2.1", disclosure), "ledger-not-generated")
```

**Second analog (subprocess CLI + git fixture):** `tests/scripts/verify-v03-dispositions.py` 429-578. `expect_pass` / `expect_reject` (436-446) assert `REJECT {code}:` on stderr; `case(label, code, mutate)` (465-478) commits a mutated record and requires rejection on both the working-tree and `--rev` read paths. Use this style for the readback controls (19-05) and the D-20 stale-active-record control (19-04).

```python
# verify-v03-dispositions.py:440-446
def expect_reject(label: str, result: subprocess.CompletedProcess, code: str) -> None:
    nonlocal controls
    if result.returncode == 0 or "v03-dispositions pass" in result.stdout:
        raise SystemExit(f"self-test accepted {label}")
    if f"REJECT {code}:" not in result.stderr:
        raise SystemExit(f"self-test {label}: expected REJECT {code}, got: {result.stderr.strip()[:240]}")
    controls += 1
```

**Third analog (data-driven mutants through the CLI on a copied tree):** `.github/scripts/verify-workflow-policy.py` `_ledger_mutations` (3568-3610). Each row is `(label, mutate(fixture), extra_cli_args, expected_code)`. `ledger(edit)` (3579-3580) and `both(first, second)` (3582-3586) are the helpers. The D-04 controls (tree mismatch, anchor not on main, ceil(2 x p50), scratch 0.3.0) belong here. In-process precision controls go in `_ledger_boundary_controls` (3613-3645), which calls `judge_timeout_ledger(...)` directly.

```python
# 3603-3605: the existing "VERSION above 0.2.1" mutant. It must keep rejecting a release_bound row at 0.3.0 after D-04 removes all six rows.
("ledger: release_bound row once VERSION is above 0.2.1", lambda fixture: (fixture / "CMakeLists.txt").write_text(
    re.sub(r"VERSION \d+\.\d+\.\d+", "VERSION 0.3.0", (fixture / "CMakeLists.txt").read_text(encoding="utf-8"), count=1), encoding="utf-8"), (), "timeout-ledger-release-bound"),
```

**Fixture caveat for D-04 (new):** the policy fixture (`_copy_fixture`, 2761-2773) copies a closed file list into a plain temp directory. It is not a git repository. The offline rule `cited_tree == tree(tree_equal_sha)` and "ancestor of main" need git objects, so those controls need either an in-process call that injects a `tree_of`/`is_ancestor` callable (the `validate_rehearsal_run(..., tree_of)` precedent, source-proof 123) or a `git init` scratch fixture (the `rehearsal_cli_self_test` precedent, source-proof 410-451). Add any extra files the fixture needs to the `extra` tuple at 2766.

---

### Priority analog 2: REJECT code emission

All checkers print `REJECT <code>: <reason>` on stderr and exit 1. Use the idiom already local to each file; do not unify them.

| File | Mechanism | Lines |
|---|---|---|
| `.github/scripts/verify-workflow-policy.py` | `class Reject(code, message)` builds `f"REJECT {code}: {message}"`; `main` prints `str(exc)` to stderr, returns 1 | 34-37, 3830-3854 (except at 3852) |
| `tests/scripts/verify-v03-dispositions.py` | `Reject(code, message)` + `reject()`; `main` prints `REJECT {error.code}: {error.message}` | 81-89, 595-597 |
| `tests/scripts/verify-support-ledger.py` | `fail(msg)` raises `ValueError`; messages are written `fail("REJECT disclosure-input-invalid: ...")`; `main` prints `support-ledger verification failed: ...` | 56-57, 2703-2704, 3194-3197 |
| `tests/scripts/verify-release-lifecycle.py` | `Reject.__init__` bakes `REJECT {code}:` into the message | 87-90 |
| `tests/scripts/verify-version-window.py` | `reject(code, detail)` raises `WindowError("window-...: detail")` | 60-65 |
| `tests/scripts/verify-perf-gate.py` | `Rejected(code, message)`; `main` writes `REJECT %s: %s\n` | 44-52, 1346-1348 |
| `.github/scripts/verify-release-source-proof.py` | `ValueError`; CLI prints `REJECT: {error}` with no code | 561-563 |

**Plan consequences**

- New claim codes (`claim-scope-missing`, `claim-platform-unpackaged`, `claim-platform-unexercised`, `claim-unbacked`, `claim-evidence-unregistered`, `claim-corpus-drift`, `claim-pins-stale`, `non-claim-missing`) go in `verify-support-ledger.py` as `fail("REJECT <code>: ...")`, matching `_disclosure_invalid` (2703-2704).
- `rehearsal-not-version-pr-head` and `rehearsal-postdates-tag` (D-18) are new codes in `verify-release-source-proof.py`. That file uses uncoded `ValueError` messages and matches controls by substring (`refuse(label, reason, call)`, 322-331). Either add the codes to the message text so the substring match names them, or add a `code` prefix at the CLI (561-563). Do not convert the file to a `Reject` class; the lifecycle replay greps its stderr.
- A control only counts when the reason is its own (`reason in str(error)`); copy that rule.

---

### Priority analog 3: policy exact-set pin in `verify-workflow-policy.py`

**3a. New optional ledger fields (D-04).** Today the normal row is an exact set (the drift RESEARCH flagged):

```python
# verify-workflow-policy.py:2219, 2285-2286
LEDGER_NORMAL_FIELDS = frozenset({"timeout_minutes", "cited_run_id", "cited_sha", "p50_minutes", "samples", "provisional"})
...
        if set(row) != LEDGER_NORMAL_FIELDS:
            raise Reject("timeout-ledger-schema", f"{key}: a row holds exactly {sorted(LEDGER_NORMAL_FIELDS)}")
```

Replace with `required = LEDGER_NORMAL_FIELDS`, `optional = {"tree_equal_sha", "cited_tree", "cited_job_name", "disclosure"}`, reject `set(row) - (required | optional)` and `required - set(row)`, and reject `tree_equal_sha` without `cited_tree` (and the reverse) with the same `timeout-ledger-schema` code. Keep the type checks at 2287-2291 and the Fraction ratio rule at 2294-2296 unchanged. Add the git-object rules inside `check_timeout_ledger` (2305-2325) and not inside `judge_timeout_ledger`, because the latter is pure data and is called in-process by 3618-3620.

**3b. Online `verify_cited` (D-04).** The offline-hostile line is the ancestor check at 2367:

```python
if run["event"] == "pull_request":
    pulls = gh("repos/{owner}/{repo}/commits/%s/pulls" % row["cited_sha"])
    provisional = not any(item.get("merged_at") for item in pulls)
else:
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", row["cited_sha"], "origin/main"], cwd=root, check=False).returncode == 0
    provisional = not ancestor
```

Add: if `tree_equal_sha` is present, compare `run` head tree (via `gh api .../git/commits/<head>` `.tree.sha`) with `cited_tree`, and match the job by `cited_job_name` instead of `display[key]` at 2351. The existing in-file stub-`gh` pattern is `_REPORT_RED_STUB` (2625-2639): a bash `gh` that serves fixtures, refuses everything else with exit 97. Model the automated `--verify-cited` control on it (RESEARCH needs one because the online path cannot be a CTest).

**3c. Workflow-set and trigger pins for the NEW pre-tag gate workflow (OQ-4).**

```python
# 2758 and 2565-2571: the workflow set is CLOSED. A new file is rejected as workflow-unlisted until added here.
WORKFLOWS = ("release-rehearsal.yml", "release.yml", "release-please.yml", "ci.yml", "fixture-repro.yml", "preview.yml", "perf-attribution.yml", "nightly-asan.yml", "libbet-repro.yml")
...
    if present != set(WORKFLOWS):
        raise Reject("workflow-unlisted", ...)
```

Add the new file name to `WORKFLOWS`, add `check_<gate>(root)` to `check_all` (2601-2618), and add the file to `_copy_fixture` is automatic via `WORKFLOWS`.

**3d. The pin set to copy: `check_version_window` (2446-2483) with constants 2409-2421.** The new gate is the same shape (trusted checkout of base, PR head as data, no job-level `timeout-minutes`, per-step bounds). Pins to replicate with new names:

```python
WINDOW_PERMISSIONS = {"contents": "read", "pull-requests": "read"}   # 2417
WINDOW_STEP_TIMEOUT_MAX = 10                                         # 2418
...
    if _permissions(job, tree.get("permissions", {})) != WINDOW_PERMISSIONS:           # 2462
        raise Reject("window-gate-permissions", ...)
    _check_checkout_credentials(name, tree, (WINDOW_JOB,))                             # 2464
    checkouts = _checkouts(job)
    by_path = {step.get("with", {}).get("path"): step.get("with", {}) for step in checkouts}
    if len(checkouts) != 2 or set(by_path) != {"trusted", "version-pr"}:               # 2467
        raise Reject("window-gate-trust", ...)
    if by_path["trusted"].get("ref") != TRUSTED_SHA_REF:                               # 2469
        raise Reject("window-gate-trust", ...)
    for step in job.get("steps", []):                                                  # 2473-2476
        minutes = str(step.get("timeout-minutes", ""))
        if not minutes.isdigit() or not 1 <= int(minutes) <= WINDOW_STEP_TIMEOUT_MAX:
            raise Reject("window-gate-timeout", ...)
    _check_actions(name, tree); _check_disabled(name, tree); _check_ignored_failures(name, tree)
    _check_run_expressions(name, tree); _check_bounded_downloads(name, tree)
    require_call(name, WINDOW_JOB, job, WINDOW_CALL, conditional=True)                  # 2482
```

For a `pull_request` trigger, also copy the explicit trigger rule from `_check_ci_planning_lane` (1590-1591): `if "pull_request_target" in _trigger_names(tree): raise Reject("workflow-trigger", ...)`. For the trusted base checkout use `github.event.pull_request.base.sha` (D-18), not `github.sha`; pin it the way 2469 pins `TRUSTED_SHA_REF`.

**3e. Mutant rows for the gate (copy `_window_mutations` 3516-3558).** One row per pin, each `_m(label, workflow, after_anchor, old, new, expected_code)` (2783-2784):

```python
_m("W17-02 gate no longer waits for regeneration", rp, window, "needs: [release]", "needs: []", "window-gate-order"),
_m("W17-05 gate gains write authority", rp, window, "pull-requests: read", "pull-requests: write", "window-gate-permissions"),
_m("W17-07 checker taken from the version PR head", rp, "name: Check out the trusted main commit\n", "ref: ${{ github.sha }}",
   "ref: ${{ steps.discover.outputs.head }}", "window-gate-trust"),
_m("W17-12 fake green stale window (continue-on-error)", rp, "name: Judge ...\n",
   "        timeout-minutes: 5\n", "        timeout-minutes: 5\n        continue-on-error: true\n", "ignored-gate"),
```

Required mutants for D-18 (RESEARCH V3): gate masked by `continue-on-error`, gate runs subject code, `pull_request_target`, wrong base ref, step without timeout, call removed (`required-command-not-executed`).

**3f. `READONLY_WORKFLOWS` (IN-08).** Add `"libbet-repro.yml"` at line 1536; `check_readonly_workflows` (1540-1549) then calls `_check_checkout_credentials` on it. The mutant row is a copy of 2980-2981:

```python
_m("perf-attribution checkout persists credentials", "perf-attribution.yml", "  attribution:\n", "persist-credentials: false",
   "persist-credentials: true", "checkout-credentials"),
```

For libbet-repro the unmutated file must first gain `persist-credentials: false` (its checkout step at `libbet-repro.yml:17-18` has no `with:`), so the mutant anchor `"  libbet-repro:\n"` and `old` text exist.

**3g. Budget ratchet from the BASE copy (WR-C04).** Current pin is the head-copy command:

```python
# 1339-1341, enforced at 1657-1664
CI_BUDGET_COMMANDS = (
    'python3 -I tests/scripts/verify-test-budget.py --build-dir build --base "$BUDGET_BASE"',
)
```

Change the pin to the `git show` + temp-copy form, keep `CI_BUDGET_BASE_PINS` (1344-1348). The in-repo analog for "judge from a trusted revision's copy" is `release.yml:1171`:

```bash
git show "${GITHUB_SHA}:.github/scripts/verify-release-source-proof.py" > "$RUNNER_TEMP/verify-release-source-proof.py"
python3 -I "$RUNNER_TEMP/verify-release-source-proof.py" --select-performance-run ...
```

and the review's own fix text (`17-REVIEW.md:672-676`):

```yaml
run: |
  git show "$BUDGET_BASE:tests/scripts/verify-test-budget.py" > "$RUNNER_TEMP/verify-test-budget.py"
  python3 -I "$RUNNER_TEMP/verify-test-budget.py" --build-dir build --base "$BUDGET_BASE" --repo "$GITHUB_WORKSPACE"
```

Mutants to add next to 2915-2921: "budget step runs the head copy again" (restore `python3 -I tests/scripts/verify-test-budget.py`), expected `required-command-not-executed`; "head copy's `--self-test` step removed". Verify `verify-test-budget.py` accepts `--repo` before writing the pin.

**3h. Perf-gate artifact pin (19-05).** Copy the `linux-sanitizers` upload pin:

```python
# check_ci 1633-1634
_upload(job, name, "linux-sanitizers", "v02-fuzz-${{ github.run_id }}-${{ github.run_attempt }}",
        ("build-asan/v02-fuzz-receipt.json", "build-asan/fuzz-artifacts/"), retain_on_failure=True)
```

as `_upload(perf_job, name, "perf-gate", "perf-gate-${{ github.run_id }}-${{ github.run_attempt }}", ("<receipt path>",))` after `PERF_GATE_COMMANDS` (1096-1102, enforced 1668-1669). Add a new command string to `PERF_GATE_COMMANDS` for the emitter call.

**3i. Floor.** `tests/cmake/ci-lanes.cmake:92-96` holds the parsed minimum (`negative_controls` 394 POSIX / 375 Windows). Compute the new floor from a real run (`PASS: workflow policy self-test negative_controls=N`), keep the 19-control POSIX-only delta (comment at 89-91), and only raise it.

---

### Priority analog 4: managed-input JSON validator with exact key sets

**Analog:** `tests/scripts/verify-support-ledger.py` lines 2690-2782 (`release-disclosure.json`). Copy this structure for `tests/data/support-claims-v0.3.json`:

```python
# 2690-2700: constants (path, byte bound, exact key sets, ASCII text regex)
DISCLOSURE_PATH = "tests/data/release-disclosure.json"
MAX_DISCLOSURE_BYTES = 64 * 1024
DISCLOSURE_TOP_KEYS = {"schema_version", "kind", "historical", "current_interpretation"}
DISCLOSURE_TEXT = re.compile(r"[\x20-\x7e]{1,800}")

# 2703-2728: single-purpose primitives that all raise through one code
def _disclosure_invalid(reason: str) -> None:
    fail("REJECT disclosure-input-invalid: " + reason)

def _disclosure_int(value, name, low, high):
    if type(value) is not int or not low <= value <= high:       # type() not isinstance(): rejects bool
        _disclosure_invalid(f"{name} must be an integer in [{low}, {high}]")
    return value

def _disclosure_keys(value, name, expected: set) -> dict:        # exact key set, missing AND unknown named
    if type(value) is not dict:
        _disclosure_invalid(f"{name} must be an object")
    missing = sorted(expected - set(value)); unknown = sorted(set(value) - expected)
    ...

# 2733-2736: schema_version/kind pin
data = _disclosure_keys(data, "disclosure", DISCLOSURE_TOP_KEYS)
if data["schema_version"] != 1 or type(data["schema_version"]) is not int: ...
if data["kind"] != "historical-performance-disclosure": ...

# 2767-2776: source binding against immutable git objects (bind=True), a separate REJECT code
if bind:
    if tag_commit(root, historical["comparison_release"]) != historical["candidate_source"]:
        fail("REJECT disclosure-source-unbound: ...")

# 2780-2782: loader = bounded_file + strict_json (duplicate keys rejected) + validate
def load_disclosure(root=ROOT, bind=True) -> dict:
    raw = bounded_file(root / DISCLOSURE_PATH, MAX_DISCLOSURE_BYTES, "disclosure-input")
    return validate_disclosure(strict_json(raw, "disclosure-input"), root, bind)
```

Mapping for the claims file (D-11): top keys `{schema_version, kind: "scoped-support-claims", applies_from_version, claims, non_claims}`; per-claim keys `{id, requirements, statement, models, modes, corpus, platforms, surface, evidence, non_claims}`. Enums for models/modes/platforms/surface live in the checker (like `DISCLOSURE_MODELS` 2692). The required non-claim id list lives in the checker, not the data (D-11). Recompute derived values (153 from `tests/data/state-forks.json` `expected_case_count`, goldens release triplet, `docs/host-contract.json` rows, `tests/expected-tests.txt`, the `if(WIN32)` list in `cmake/ExpectedTests.cmake:16-134`) from source artifacts and reject drift with `claim-corpus-drift` / `claim-pins-stale` / `claim-evidence-unregistered` / `claim-platform-unexercised`, each read with `git show REV:` or `immutable_git_file(root, rev, path, MAX)` (2774) rather than the working tree.

**Managed-input registration:** add the new path to `REQUIRED_MANAGED_INPUTS` in `tests/scripts/verify-version-window.py:47-51`, so a claims edit after review ends the freeze. Also add it to the self-test fixture `build_fixture` (`verify-version-window.py:436-447`, which writes `tests/data/release-disclosure.json` and the generator stand-in). Two seams are driven by that tuple: `validate_record_shape` 221-223 (`window-input-missing`) and `draft_record` 339-343. The existing control at 617-619 (`generator-input-omitted`) deletes one input; extend it to loop over the tuple so the new path is covered.

---

### Priority analog 5: `render_v2_ledger` -> `render_v3_ledger` (D-11)

**Analog:** `tests/scripts/verify-support-ledger.py:1075-1149`. Copy verbatim to `render_v3_ledger(data, disclosure=None, claims=None)` and keep `render_v2_ledger` untouched so v0.2.0/v0.2.1 stay byte-exact. The insertion points inside the line list:

```python
# 1075-1080: signature + managed-input load when not supplied
def render_v2_ledger(data: dict, disclosure: dict | None = None) -> str:
    if disclosure is None:
        disclosure = load_disclosure(ROOT)
    counts = data["receipt"]["counts"]
    ...
# 1135-1136: generated paragraphs come from managed input, spliced into the list (copy this for claims)
        *disclosure_paragraphs(disclosure, data["version"]),
        "Evidence classes are kept distinct: ...",
# 1140-1144: the structured block is json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False)
```

Add `*claim_paragraphs(claims, data["version"]),` between 1133 ("Known limitations ...") and 1135, built like `disclosure_paragraphs` (2785-2805: returns `[block, ""]` pairs). Render claim and non-claim lists from the validated file only; never accept free text from `data`.

**Dispatch:** `require_generated` (2865-2871) hardcodes `render_v2_ledger(parse_ledger(raw, version), disclosure)`. Switch on version `>= 0.3.0` to `render_v3_ledger(..., claims)`. `check_disclosure_generator` (2903-2922) appends the tree ledger to `DISCLOSED_LEDGERS` (2823-2827) automatically, so do not edit that tuple before the tag (it holds tag-blob freezes). `validate_data_v2` (582-586) hard-rejects non-0.2.x:

```python
if not re.fullmatch(r"0\.2\.[0-9]+", expected_version) or data.get("version") != expected_version:
    fail("v0.2 ledger version/profile identity is missing or unstable")
```

Relax that single line (`0\.[23]\.[0-9]+`), because it is also reached from `check_ledger_static`, `check_current`, `build_v2_sidecar` (1455), and `create_current_ledger` (1152). Note the v0.2 scope dict check at 592-599 (`modes: ["compat","native"]`) would reject a 0.3 scope; give 0.3 its own scope branch in the same function (D-11 "own validation branch").

**Sidecar (D-12):** `build_v2_sidecar` (1455) emits `"ledger": {"path", "git_blob_oid", "sha256"}`. There is no key `ledger_blob`; bind claims through `ledger.git_blob_oid` / `ledger.sha256`. Keep `schema_version == 2` (gates hard-require it: `verify-release-gates.sh:256, 423`).

**CLI wiring:** follow `--check-disclosure` / `--self-test-disclosure` (3150-3157) and the `--self-test` fan-out (3106-3113). New flags `--check-claims`, `--self-test-claims`; keep the existing output lines unchanged because `v02_support_ledger_controls` pins `positive=1 rejected_controls=5 controls=changed-covered-input,...` (`tests/CMakeLists.txt:1438`).

---

### Priority analog 6: `validate_rehearsal_run` (D-17, D-18)

**Analog:** `.github/scripts/verify-release-source-proof.py:123-146`. Add `pr_head=None, not_after=None` parameters after `tree_of`; keep the existing checks in order and put the new checks last so existing diagnostics keep priority.

```python
def validate_rehearsal_run(run: Any, tag: str, source_sha: str, repo: str, tree_of: TreeOf) -> None:
    """Raise ValueError unless this run object is the successful rehearsal of exactly the tagged tree."""
    if not isinstance(run, dict) or not _is_id(run.get("id")) or not _is_id(run.get("run_attempt")):
        raise ValueError("rehearsal run object is malformed")
    path = run.get("path")
    if not isinstance(path, str) or path.split("@", 1)[0] != REHEARSAL_WORKFLOW_PATH:
        raise ValueError("run is not a run of the rehearsal workflow")
    if run.get("event") not in REHEARSAL_EVENTS:                      # ("push", "workflow_dispatch")
        raise ValueError(f"rehearsal run was triggered by {run.get('event')!r}, not push or workflow_dispatch")
    ...
    head = run.get("head_sha")
    if head != source_sha:
        head_tree, source_tree = tree_of(head), tree_of(source_sha)
        ...
        if head_tree != source_tree:
            raise ValueError("rehearsal run head tree differs from the tagged tree")
```

New rules (message text must contain the code so substring controls name it): `if pr_head is not None and head != pr_head: raise ValueError("rehearsal-not-version-pr-head: ...")`; `if not_after is not None` compare the attempt's max job `completed_at` to `merged_at`, raising `"rehearsal-postdates-tag: ..."`, and reject a missing `merged_at`. Compare timestamps parsed to `datetime` (the nightly gate uses server ordering, `release-evidence-lifecycle.sh:312-317`), not strings.

**Already available (finding):** the `candidate` job step "Verify merged PR exact-head required evidence" (`release.yml:141-163`) already calls `gh api "repos/$GH_REPO/commits/$SOURCE_SHA/pulls"`, selects the merged PR and exposes its head and number as outputs:

```bash
prs=$(gh api "repos/$GH_REPO/commits/$SOURCE_SHA/pulls")
pr=$(jq -c '[.[] | select(.merged_at != null and .base.ref == "main" and .merge_commit_sha == env.SOURCE_SHA)][0]' <<<"$prs")
pr_head=$(jq -r '.head.sha' <<<"$pr")
...
printf 'head_sha=%s\nmerge_commit_sha=%s\npr_number=%s\n' "$pr_head" "$pr_merge" "$pr_number" >> "$GITHUB_OUTPUT"
```

So assumption A4 in RESEARCH is partly verified for the candidate job: `pr_head` and `merged_at` come from this existing response; add `merged_at` to the step's outputs. `nightly-gate` (`lifecycle_nightly_gate`, `release-evidence-lifecycle.sh:307-328`) does not have this step, so it must fetch the same endpoint itself. That endpoint is not in the replay stub (see analog 11).

**Self-test pattern (copy for each D-18 control):** `rehearsal_reuse_self_test` (298-407). Fixture factory `rehearsal_fixture` (276-295), then:

```python
# 322-334
def refuse(label: str, reason: str, call: Callable[[], Any]) -> None:
    nonlocal controls
    try:
        call()
    except ValueError as error:
        if reason not in str(error):
            raise SystemExit(f"rehearsal-reuse self-test: {label}: refused for the wrong reason: {error}")
        controls += 1
        return
    raise SystemExit(f"rehearsal-reuse self-test accepted {label}")

def run_defect(label: str, reason: str, **changes: Any) -> None:
    refuse(label, reason, lambda: select([dict(run, **changes)], trees))
...
# 340-345 table-driven event/conclusion/status loops
for event in ("pull_request", "pull_request_target", "schedule", "workflow_run", "repository_dispatch", None):
    run_defect(f"event {event}", "was triggered by", event=event)
```

The D-18 controls (postdated run, attempt 2 after the merge, tree-equal non-PR-head, missing `merged_at`, another run id, `pull_request` event, fork, other workflow path, inactive record at W) map onto `run_defect` rows plus `refuse(...)` rows with `pr_head=` / `not_after=`. The R2-red-while-R1-green control is the existing 361-366 pattern ("stale newest run behind which an older valid run exists", reason `head tree differs`): add a sibling that names `R1` explicitly.

**CLI:** extend `--select-performance-run` (534-535, 547-555) with `--pr-head` and `--not-after-json`; keep the `REJECT: {error}` stderr line (562). `REHEARSAL_TAG = "v0.2.1"` at 271 is used only by self-test fixtures (285, 303, ...); optional cosmetic change.

---

### Priority analog 7: CTest registration with TIMEOUT / LABELS + `expected-tests.txt`

Four registration shapes already exist; pick by test kind.

**a) Python checker with a regex + parsed minimum, in the ledger region** (for `support_claims`, `support_claims_controls`): `tests/CMakeLists.txt:1444-1481`.

```cmake
# 1444-1453
function(gbb_add_ledger_contract name regex)
  add_test(NAME ${name}
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_CMD=${Python3_EXECUTABLE};-I;${PROJECT_SOURCE_DIR}/tests/scripts/verify-support-ledger.py;${ARGN}"
      -DGBB_EXPECT_CODE=0
      "-DGBB_EXPECT_REGEX=${regex}"
      ${GBB_LEDGER_MIN}
      -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
  set_tests_properties(${name} PROPERTIES TIMEOUT 60 LABELS "v02")
endfunction()
# 1474-1481: generator test (no minimum) then controls with a parsed minimum
gbb_add_ledger_contract(release_disclosure_generator
  [=[release-disclosure generator pass ledgers=[2-9] tagged=[1-9]]=]
  --check-disclosure)
set(GBB_LEDGER_MIN -DGBB_EXPECT_MIN_KEY=controls -DGBB_EXPECT_MIN_VALUE=15)
gbb_add_ledger_contract(release_disclosure_controls
  [=[release-disclosure controls pass positives=[1-9][0-9]* controls=[1-9][0-9]*]=]
  --self-test-disclosure)
unset(GBB_LEDGER_MIN)
```

The checker must print `controls=N` so `GBB_EXPECT_MIN_KEY=controls` can parse it (`self_test_disclosure` prints `release-disclosure controls pass positives=... controls=...` at 3112/3152).

**b) Any python checker + timeout + label:** `gbb_add_v02_contract(name timeout regex script args...)` at 1407-1421 (label `v02`, timeout per call). Examples 1487-1492 (`release_window_contract`/`_controls`).

**c) Planning-reading tests need `LABELS "planning"`** (`tests/scripts/verify-planning-labels.py`; `v03_dispositions` 1556-1571):

```cmake
add_test(NAME v03_dispositions_controls
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${Python3_EXECUTABLE};-I;${PROJECT_SOURCE_DIR}/tests/scripts/verify-v03-dispositions.py;--self-test"
    -DGBB_EXPECT_CODE=0
    "-DGBB_EXPECT_REGEX=v03-dispositions self-test pass controls=[0-9]+"
    -DGBB_EXPECT_MIN_KEY=controls -DGBB_EXPECT_MIN_VALUE=10
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
set_tests_properties(v03_dispositions_controls PROPERTIES TIMEOUT 60 LABELS "planning")
```

The v0.3.0 readback test reads the receipt under `.planning/phases`: register through `${GBB_LIVE_PHASES_DIR}` (as `GBB_V03_DISPOSITIONS` does at 1555), not a literal path under `tests/`.

**d) `--rev` bound replay tests** (`release_lifecycle_replay` / `_controls`, `release_nightly_*`): `tests/CMakeLists.txt:5517-5535`, `5544-5560`. A case string `"name|mode|regex|key|min"` in a `foreach`; `${GBB_STATE_SOURCE_REV}` is configure-time HEAD, so commit and reconfigure before running. Raise the `95` (`release_lifecycle_controls`) or `37` (`release_nightly_controls`) minimums only after measuring; `release_lifecycle_controls` is at about 51 s of TIMEOUT 60 (RESEARCH Pitfall 2), so split it by a second `foreach` row or add a `verify-test-budget` allowlist row before adding scenarios.

**e) Perf checker:** `tests/cmake/perf.cmake:46-76`. New receipt controls CTest copies `gbb_add_perf_gate_test` + `GBB_PERF_GATE_EXTRA_ARGS -DGBB_EXPECT_MIN_KEY=controls -DGBB_EXPECT_MIN_VALUE=<n>` (74-76). **Trap:** `tests/data/perf-gate/` is a digest-pinned immutable fixture set (`GBB_PERF_GATE_MANIFEST_SHA256` at line 15, configure fails on a changed manifest at 18-20 and on any extra file at 40-43). Do not add receipt fixtures there; build them in a temp directory inside the self-test, or update `SHA256SUMS` and the pinned manifest digest deliberately.

**Inventory:** every new CTest name needs one line in `tests/expected-tests.txt` (1678 lines today). `cmake/ExpectedTests.cmake:134-139` sorts both lists before comparing, so position is free: insert next to the related group (e.g. after `release_disclosure_controls`, line 1165) instead of appending at the tail, which avoids the textual conflicts RESEARCH predicts between parallel plans. Only `if(NOT WIN32)` tests need the extra `list(REMOVE_ITEM ...)` (`ExpectedTests.cmake:16-134`) and `.github/scripts/verify-test-inventory.sh:6-150` edits; keep every new check python-only and cross-platform to avoid that.

**Bumped counts:** `doc_no_interop_claims` expects `files=6 controls=6` (`tests/cmake/host-contract.cmake:225-226`, script print at `verify-no-interop-claims.py:~110`: `files={files} controls={len(REJECTED_CONTROLS) + 1}`). Adding `docs/support/v0.3.0.md` to `FILES` (line 39-40) and widening `PATTERN` (42-44) changes both numbers; update the regex in the same commit. `GBB_REV_WIRING_TESTS` (`host-contract.cmake:232-233`) must keep naming `doc_no_interop_claims`.

---

### Priority analog 8: the 18-04 `hostvariant` rename (D-07, RM-031)

**Analog:** `tests/cmake/host.cmake:300-310` plus its call sites (326-354, 489-548). The precedent in full:

```cmake
# 300-310
# ---- mutant runners (build-tree executables only; nothing mutated is installed) ----
# gbb_host_mutant_runner(name mutant_library): gabbaboy-runner's main.c linked against a mutant host
# library instead of gabbaboy_host. The core arrives once, through gabbaboy_runner_support, and it is the
# NORMAL core: only the host library is mutated. The executable is therefore named `hostvariant`, not
# `mutant`, because verify-core-linkage.py requires every target named *mutant* to link a mutant core.
function(gbb_host_mutant_runner name mutant_library)
  add_executable(gabbaboy-runner-hostvariant-${name} "${PROJECT_SOURCE_DIR}/src/runner/main.c")
  target_link_libraries(gabbaboy-runner-hostvariant-${name} PRIVATE gabbaboy_runner_support ${mutant_library})
  ...
endfunction()
```

CTest names stay `host_*_mutant_*`; only executable target names change (18-04-SUMMARY.md:222). The reason is `verify-core-linkage.py:42`: `MUTANT_NAME = re.compile(r"(mutant|_p1[0-9]$)")` makes any target named `*mutant*` expect a mutant core; `check_line` (133-149) reports `wrong-core: mutant target ... links the normal core`.

**Apply to `tests/player/CMakeLists.txt` (rename list, verified):**

| Line | Current | Becomes |
|---|---|---|
| 187 | `test_player_colour_mutant_rb_swap` | `test_player_colour_playervariant_rb_swap` (also the `$<TARGET_FILE:...>` at 198 via `colour_target`) |
| 219 | `gabbaboy-player-mutant-rb-swap` | `gabbaboy-player-playervariant-rb-swap` |
| 227 | `gabbaboy-player-mutant-dmg-path` | `gabbaboy-player-playervariant-dmg-path` |
| 250, 254, 259, 261 | `test_player_session_mutant_ignores_flag` | `test_player_session_playervariant_ignores_flag` (target name also in the `add_test` command line at 261) |
| 192 | `target_link_libraries(${colour_target} PRIVATE GabbaBoy::core gabbaboy_accept)` | drop `GabbaBoy::core` (`gabbaboy_accept` already brings it): `duplicate-core` for `test_player_colour` and `test_player_colour_mutant_rb_swap` |
| 139-148 | library `gabbaboy-player-mutant-core-m1`, executable `gabbaboy-player-mutant-ppu-follows-cpu` | **Beyond RM-031's list (RESEARCH Drift 6):** this is a real core mutant, but the archive `libgabbaboy-player-mutant-core-m1.a` fails `MUTANT_CORE = ^libgabbaboy_core_[A-Za-z0-9_]+\.a$` (`verify-core-linkage.py:38`), and `gabbaboy-player-adapter` also pulls the normal core |

**Mutant-core naming precedent for the m1 fix:** `tests/CMakeLists.txt:420` `add_library(gabbaboy_core_p13_mutants STATIC ${GBB_P13_MUTANT_CORE})` yields `libgabbaboy_core_p13_mutants.a`, which matches. Name the player library `gabbaboy_core_player_mutant_m1` and keep exactly one core archive on the link line (`gbb_player_mutant_binary` at 26-35 appends `${ARGN}` before `gabbaboy-player-adapter`).

**Negative controls (D-07):** `core_linkage_controls` (`verify-core-linkage.py` 282-380, registered `tests/CMakeLists.txt:1528-1535`, `if(NOT WIN32)`) already feeds `duplicate-core` and `wrong-core` fixtures via `expect_rejection(script, build_dir, mutate_line(commands, "tests/test_age", duplicate), "duplicate-core", "duplicate-core", temp)` (302-304). The "restore the name / restore the double link" controls are a seeded edit of the generated `build.ninja` line, i.e. the same `mutate_line` helper aimed at a player target. Red-before evidence command: `python3 -I tests/scripts/verify-core-linkage.py --check --build-dir build-player` (six violations today).

**Lane filter (D-07):** `tests/scripts/verify-phase3-player.sh:471`:

```bash
ctest --test-dir "$APP_BUILD" --output-on-failure --no-tests=error -R '^player_' \
  --output-junit "$APP_BUILD/ctest-player.xml"
bash "$ROOT_DIR/tests/scripts/verify-dmg-baseline.sh" --build-dir "$APP_BUILD" \
  --junit "$APP_BUILD/ctest-player.xml" --inventory player
```

Widen to `-R '^(player_|core_linkage_)'` as D-07 says, but RESEARCH Pitfall 7/A2 is unproven: extra `core_linkage_*` junit rows may reach the `--inventory player` comparison. Prefer a second `ctest ... -R '^core_linkage_'` line with no `--output-junit`, and prove either choice with a seeded junit.

---

### Priority analog 9: `check_readback` in `verify-v03-dispositions.py` (D-23)

**Analog:** `tests/scripts/verify-v03-dispositions.py` 224-255 (`check_receipt_file`, `check_readback`) and the surrounding `Source` reader (92-130).

```python
# 224-231: {path, sha256} receipt, bytes read by `git show REV:path`, digest-pinned
def check_receipt_file(source: Source, receipt, name: str) -> tuple[bytes, object]:
    if not isinstance(receipt, dict) or set(receipt) != {"path", "sha256"} or not isinstance(receipt["path"], str) \
            or not isinstance(receipt["sha256"], str) or not HEX64.match(receipt["sha256"]):
        reject("receipt-invalid", f"{name} must be {{path, sha256}} with a 64-hex digest")
    raw = source.read(receipt["path"])
    if hashlib.sha256(raw).hexdigest() != receipt["sha256"]:
        reject("receipt-digest-mismatch", f"{name} bytes do not match the recorded SHA-256")
    return raw, parse_json(raw, name, "receipt-invalid")

# 244-255: the current readback predicate (tag, tag_sha, is_draft false, non-empty assets, reconciliation present)
def check_readback(source: Source, receipts: dict) -> None:
    _, readback = check_receipt_file(source, receipts["release_readback"], "release_readback")
    if not isinstance(readback, dict) or readback.get("tag") != receipts["tag"] or readback.get("tag_sha") != receipts["tag_sha"] \
            or readback.get("is_draft") is not False:
        reject("receipt-invalid", "the release readback must record the same tag and tag commit and is_draft false")
    assets = readback.get("assets")
    ...
```

**Important (RESEARCH Drift 3):** `check()` (310-333) pins `record["plan"] == "16-06"` and `REQUIRED` (56-74) is an exact id set, and the 16-06 record is already closed (`pending=0 closed=6`). Do not extend `check()`. Add a new entry point `--check-readback PATH --rev REV [--tag vX.Y.Z]` in `main` (581-601) that reuses `Source`, `check_receipt_file`, and a strengthened `check_readback_v2(source, readback, tag)`, and keep the 16-06 path and `v03_dispositions*` CTests unchanged in meaning.

**New reconciliation elements to add (D-23), each with a `case(...)`-style control:**

| Element | Source of truth | New REJECT code |
|---|---|---|
| tag -> SHA and tree | `git rev-parse TAG^{commit}` / `^{tree}` via the existing `git_tree(repo, sha)` helper (used at 296) | `readback-tag-mismatch` |
| `is_draft: false` | readback JSON (exists at 247) | keep `receipt-invalid` |
| asset-name set and ids vs the pre-publish inventory | `build/release-final/expected-inventory.json` equivalent captured in the receipt | `readback-assets-mismatch` |
| each API `digest` vs its `SHA256SUMS` line | `SHA256SUMS` asset content | `readback-digest-mismatch` |
| `release-receipt.json` digests vs the assets | `release-receipt.json` (`evidence_sha256`, `assets[].sha256`, built at `release-evidence-lifecycle.sh:255-278`) | `readback-receipt-mismatch` |
| sidecar `ledger.git_blob_oid` vs blob of `docs/support/v0.3.0.md` at the tag | `git rev-parse TAG:docs/support/v0.3.0.md` | `readback-ledger-blob-mismatch` |

Self-test style to copy: `build_fixture` (372-401) creates a real git fixture with a tag, then `case(label, code, mutate)` (465-478) commits the mutation and expects `REJECT code:` on both the working-tree and `--rev` paths. The `readback` fixture shape is at 398-399 (`{"tag","tag_sha","is_draft","assets","reconciliation"}`); the committed 16 receipt (`16-release-readback.json`: `tag, tag_sha, tag_tree, is_draft, is_prerelease, release_id, published_at, url, assets[{name,id,size,digest}], reconciliation{...}, release_run, attach_v02_evidence`) is the schema to extend.

**Privacy scan (D-23):** extend `FORBIDDEN_TEXT` (`verify-release-lifecycle.py:164`) coverage to the committed readback and receipt JSON; the same regex is used on the capture at 286-287. `verify-no-phase-paths.py` allows `.planning/` files to name `.planning/phases` freely (RESEARCH), so no allowlist row is needed if the CTest uses `${GBB_LIVE_PHASES_DIR}`.

---

### Priority analog 10: `version-window-gate` job for the NEW pre-tag gate workflow (D-18, OQ-4)

**Analog:** `.github/workflows/release-please.yml` job `version-window` (display name `version-window-gate`), lines 46-140. Copy the full shape into a new workflow file. Differences to apply:

| Aspect | `version-window-gate` (copy) | Pre-tag gate (change) |
|---|---|---|
| Trigger | `push: branches: [main]` + dispatch (3-21) | `pull_request` on the release-please branch only; never `pull_request_target` |
| Trusted checkout | `ref: ${{ github.sha }}` path `trusted` (69-73) | `ref: ${{ github.event.pull_request.base.sha }}` path `trusted`; policy pin like 2469 |
| Data checkout | PR head discovered via `gh pr list` (77-91, 92-99) | `ref: ${{ github.event.pull_request.head.sha }}` path `version-pr`, `fetch-depth: 0`, `persist-credentials: false` |
| Body | `gh api repos/$GH_REPO/pulls/$pr --jq '.body'` (89) | from the event payload (`github.event.pull_request.body`) written to `$RUNNER_TEMP`, so no token read |
| Permissions | `contents: read`, `pull-requests: read` (59-61) | `contents: read`, `actions: read` (needs the run JSON), pin exactly |
| Job timeout | none; every step `timeout-minutes: 5` (the ledger cannot cite a job with no completed run, comment 50-52) | same; then no `ci-timeouts.json` row (RESEARCH Pattern 4) |
| Judge call | `python3 -I trusted/tests/scripts/verify-version-window.py --repo version-pr --rev "$PR_HEAD" --base "$MAIN_SHA" --check tests/data/version-window.json --body "$RUNNER_TEMP/version-pr-body.md"` (132-140) | same with `--base "$BASE_SHA"` (PR base), then `python3 -I trusted/.github/scripts/verify-release-source-proof.py --validate-rehearsal-run ...` for R2 |

Active only when the tracked record is active (the existing script already returns `version-window inactive pass` for an inactive record, `check_window` 292-293), so the job passes during normal development.

**Policy pins and mutants:** see priority analog 3c-3e. The new job is not a required check (OQ-5): GitHub settings are an owner-only change, so `docs/release.md` must state merge discipline is a script precondition in 19-07 and not branch protection.

---

### Priority analog 11: lifecycle replay capture + `SOURCES.md` row (D-21)

**Analog:** `tests/scripts/verify-release-lifecycle.py` stub `api()` (390-446) and the capture machinery; `tests/data/release-api/SOURCES.md` table.

Adding an endpoint touches six places (all in the same file plus the data pair):

1. **Stub route.** A new `elif` in `api()` (before the terminal `else: refuse("unlisted endpoint ...")` at 445-446), shaped like the existing ones:

```python
elif re.fullmatch(r"commits/[0-9a-f]{40}/check-runs", tail) and query == "per_page=100":    # 441-444
    if tail.split("/")[1] != st["check_runs_head"]:
        fail("HTTP 404: Not Found (" + route + ")")
    kind, body = "check_runs", st["check_runs"]
```

   For D-18 the new routes are `commits/<sha>/pulls` (note the existing `re.fullmatch(r"commits/[^/]+", tail)` at 417 does not match a 3-segment path) and `actions/runs/<id>/attempts/<n>/jobs?per_page=100`. Mirror the 434-436 style of pinning the exact query string.
2. **`RESPONSE_KEYS`** (82-83): add the new capture key names; `check_capture` rejects any other set (295-296).
3. **`REQUIRED_PATHS`** (142-160): members production consumers read, e.g. `"pull_requests": ("0.number","0.merged_at","0.merge_commit_sha","0.base.ref","0.head.sha")`; `FORBIDDEN_MEMBERS` (161) only if an invented member must be refused.
4. **Sanitize list.** `main`'s `names` dict (1911-1914) maps capture key to raw filename, and `assemble_capture` (234-262) builds `responses`; add both. Arrays are truncated by `TRUNCATE_ARRAYS` (167).
5. **Capture file + digest.** Regenerate `captured.json` with `python3 -I tests/scripts/verify-release-lifecycle.py --sanitize-capture RAW_DIR tests/data/release-api/captured.json` from read-only `gh api` GETs of the published v0.2.1 (SOURCES.md "Provenance"), then update the digest line:

```
- captured.json sha256: 8f0f8f8b231f5b34df29b256cd9f64e417927325ed68d2f81d901524032ddcf5
- bytes: 108510 (bound: 262144)
```

   `check_capture` requires exactly one `- captured.json sha256: <hex>` line (`SOURCES_DIGEST` 169; reject `capture-digest` at 275-277), LF line endings (`capture-eol`), at most `MAX_CAPTURE_BYTES = 256*1024` (81; `capture-oversize`), and the four sections `Endpoints`, `API version`, `Sanitization`, `Provenance` (278-280). Add a row to the SOURCES.md Endpoints table:

```
| Capture key | Endpoint |
| release | `repos/szTheory/gabbaboy/releases/423802899` |
| pull_request | `repos/szTheory/gabbaboy/pulls/75` |
```

6. **Controls.** `c_capture_contract` (1323-1362): the `mutated(label, code, change, resign=True)` helper re-signs the SOURCES digest after each mutation; copy lines 1342-1351 for the new members (`"a pull-request listing without its merged_at"` -> `capture-schema`). The unexpected-endpoint control `c_unexpected_endpoint_in_script` (1201-1210) stays as is and keeps proving that an unlisted call stops at the transport (`gh-replay-stub: refused: unlisted endpoint`). `control_transport` (1224-1304) lists refusals; add `refuses` rows only for newly *forbidden* forms.

**Scope clarification for D-21:** the replay covers only the seven lifecycle `MODES` (65-73) and `JUDGE_FILES` (55-63). Steps that live only in `release.yml` jobs (for example the `candidate` PR-lookup step at 141-163 and `candidate-performance` at 1159) are not replayed today. Decide per endpoint whether it moves into the lifecycle script (then it is replayed) or stays in `release.yml` (then it is covered only by the policy pin). Any new `JUDGE_FILES` entry also needs `lab_integrity` coverage (1884-1889).

**Timing:** `release_lifecycle_controls` runs about 51 s of TIMEOUT 60 (5519-5535 foreach row). New control functions are appended to `TASK1_CONTROLS` (1848-1849) and run in a thread pool (1875-1880); measure before and add a split or an allowlist row.

---

### `.github/ci-timeouts.json` (config, 19-01)

**Analog:** the normal-row shape, e.g. `release.yml:candidate-performance`:

```json
"release.yml:candidate-performance": {
 "timeout_minutes": 45, "cited_run_id": 39406047351,
 "cited_sha": "08e7309aab699333d73f7ffeae58a5332133f242",
 "p50_minutes": "0.67", "samples": 1, "provisional": false
}
```

and the six `release_bound` rows to convert (`release.yml:attach-v02-evidence`, `release.yml:candidate-fuzz`, `release-rehearsal.yml:judge`, `:corpus`, `:performance`, `:aggregate`; list at `verify-workflow-policy.py:2224-2227`). Proposed shape (RESEARCH "Normal ledger row with the D-04 fields") adds `tree_equal_sha`, `cited_tree`, `cited_job_name`, `disclosure`. `p50_minutes` is `ceil(seconds/60*100)/100` of the cited job (`verify_cited` 2360-2361); `timeout_minutes >= ceil(2 x p50)` (2295). The 8 s `performance` job gives `0.14`.

---

### `src/core/gabbaboy.c` (core, 19-02, WR-A05 + IN-01)

**Analog:** the file's own two switches. `state_store_host_value` (4145-4189) and `state_apply` (4723-4769) duplicate the raw-to-host conversion; only `state_store_host_value` has weak range checks and only `state_apply` runs on the live instance.

```c
/* 4174-4186: the weaker store-path checks (BOOL raw>1, COUNT raw>SIZE_MAX, EVENT_KIND raw>BUTTON_RELEASE) */
case STATE_VALUE_BOOL:  { if (raw > 1u) return 0; const int v = (int)raw; memcpy(address, &v, sizeof(v)); return 1; }
case STATE_VALUE_COUNT: { if (raw > SIZE_MAX) return 0; const size_t v = (size_t)raw; ... }
case STATE_VALUE_EVENT_KIND: { if (raw > (uint64_t)GBB_INPUT_BUTTON_RELEASE) return 0; ... }
/* 4755-4761: state_apply has NO range checks; it trusts state_validate */
case STATE_VALUE_BOOL: { const int v = (int)raw; memcpy(address, &v, sizeof(v)); break; }
```

The validate-side predicate already exists (RESEARCH Drift 4), so the task is a refactor, not moving a predicate:

```c
/* 4231-4240: state_field_kind_valid already rejects BOOL>1, COUNT>GBB_INPUT_EVENT_CAPACITY, EVENT_KIND outside [STOP_WAKE, BUTTON_RELEASE] */
static int state_field_kind_valid(const state_field_descriptor *field, uint64_t raw) {
    ...
    if (field->kind == STATE_VALUE_BOOL && raw > 1u) return 0;
    if (field->kind == STATE_VALUE_COUNT && raw > GBB_INPUT_EVENT_CAPACITY) return 0;
    if (field->kind == STATE_VALUE_EVENT_KIND &&
        (raw < (uint64_t)GBB_INPUT_STOP_WAKE || raw > (uint64_t)GBB_INPUT_BUTTON_RELEASE)) return 0;
```

Plan: one `static void state_raw_to_host(uint8_t *address, const state_field_descriptor *field, uint64_t raw)` (infallible; the I32/I64 sign decode in `state_apply` 4740-4754 is already infallible), called from `state_apply` and `state_store_host_value`; `state_store_host_value` keeps its argument checks (index, storage, stride overflow 4155-4156) and may call `state_field_kind_valid` for range. Follow the file's convention: every function carries a `/* MODEL: BOTH GATE-00 basis="..." */` comment (4144, 4191, 4710, 4722). Do not use `assert` on a fallible return (NDEBUG).

**Control analog (new mutant):** `gbb_state_refusal_mutant(name anchor replacement)` at `tests/CMakeLists.txt:5390-5416` with calls at 5418-5436. It compiles a text-mutated copy of the core against `test_state_internal.c`, expects `FAIL state_refusal` for the mutant and exit 0 on `state_control`, and requires the anchor to occur exactly once (5392-5396).

```cmake
gbb_state_refusal_mutant(apply_before_validation
  [=[if (!state_validate(instance, body, body_size)) return GBB_STATE_INVALID_CONTENT;]=]
  [=[state_apply(instance, body, body_size);
    if (!state_validate(instance, body, body_size)) return GBB_STATE_INVALID_CONTENT;]=])
```

New row: anchor `if (field->kind == STATE_VALUE_BOOL && raw > 1u) return 0;` replaced by an empty string, expected to fail `state_refusal` on a body with BOOL=2. This registers `state_refusal_mutant_<name>` and `state_refusal_mutant_<name>_control`; add both names to `tests/expected-tests.txt` next to 1477-1486. The mutant reads `${gbb_state_internal_core_text}` built from the immutable `GBB_STATE_SOURCE_REV` source, so commit the core change first. IN-01 warnings: `GBB_TEST_STATE_HASH_COUNTER` (gabbaboy.c:26, 68) is the only guard macro today (RESEARCH Drift 5); the cheaper `GBB_MAYBE_UNUSED` attribute needs a before/after warning count from the `cc -std=c17 -Wall -Wextra -Iinclude -DGBB_STATE_RELEASE_*` line in RESEARCH.

---

### `tests/scripts/verify-perf-gate.py` + `run-perf-gate.sh` + `ci.yml perf-gate` (19-05, D-22)

**No receipt exists today** (RESEARCH Drift 2). Three analogs to copy together:

1. **Emit exclusively, before any verdict:** `evaluate` already writes a deterministic-exception measurement with `write_new_text` (400-406, called at 436):

```python
if emit_measurement_path is not None:
    # The exact object the owner approves by digest ... written before any verdict
    write_new_text(emit_measurement_path, json.dumps(measurement, sort_keys=True, indent=2) + "\n")
```

   Add `emit_receipt_path` beside it. `evaluate` computes `base_ir`, `head_ir`, `limit` and `ratio_text` per ROM (442-450) and `multiples` for realtime (452-458); put those into the receipt: `{schema, source_sha, base_sha: V020_SHA, limits_blob, ir: {rom: [repeat1, repeat2]}, digests, realtime_min, tool, run_id, run_attempt}`. `V020_SHA` is already a constant (468) and `LIMITS_BASE_REV` is 40.
2. **Shell passes the path:** `evaluate_tree` in `run-perf-gate.sh:160-162` builds `args=(--evaluate ... )`; append `--emit-receipt "$WORK/perf-gate-receipt.json"`. The same function already calls `--emit-exception-measurement` the same way (172).
3. **Upload and reader:** workflow upload step copies `ci.yml:476-485` (name `perf-gate-${{ github.run_id }}-${{ github.run_attempt }}`, `if-no-files-found: error`, `retention-days: 7`); the reader is the existing trusted `candidate-fuzz` step (`release.yml:1119-1124`):

```bash
gh run download "$run_id" --repo "$GH_REPO" --name "v02-fuzz-$run_id-$attempt" --dir build/ci-fuzz
test -s build/ci-fuzz/v02-fuzz-receipt.json
python3 -I tests/scripts/verify-v02-fuzz.py --verify-hosted --source-sha "$SOURCE_SHA" \
  --run-id "$run_id" --attempt "$attempt" --receipt build/ci-fuzz/v02-fuzz-receipt.json \
  --poll-seconds "$HOSTED_POLL_SECONDS"
```

   Download `perf-gate-$run_id-$attempt` from the same `$run_id` (1113, no new poll). New CLI mode `--verify-receipt PATH --source-sha --run-id --attempt` in `main` (1290-1349). Controls (RESEARCH V8): ratio over limit (`ir-budget-exceeded`), another SHA, a `pull_request` event, a wrong limits blob. `candidate-fuzz` has no job-level `permissions` beyond `actions: read, contents: read` (1064-1066); keep it.

**Carrier decision (OQ-2):** the reader cannot rewrite `v02-fuzz-receipt.json`. RESEARCH recommends embedding a verified `perf_gate` block in `release-receipt.json` built at `release-evidence-lifecycle.sh:255-278` (new key beside `evidence_sha256`), avoiding a new attached asset. The policy list of asset names (`release-evidence-lifecycle.sh` 52, 62, 71, 88, 108-109, 137-139, 154, 175-181, 199-204, 273-274) and `REQUIRED_ASSETS` (`verify-release-gates.sh:21`) stay unchanged on that path.

**Profile string (D-22):** `release-evidence-lifecycle.sh:277`:

```python
"limits": ["DMG-CPU-B deterministic software profile only", "no physical DMG observation", "no Developer ID signature or notarization"],
```

Replace with a version-aware scope string derived from `tag`/`version` already in the heredoc (`release` dict, 255-278), then add a control in `verify-release-lifecycle.py` (`c_*` function style, e.g. `c_non_advisory` pattern around 1195-1198) that asserts the receipt's `limits[0]` for 0.3.0 differs from 0.2.1.

---

### `tests/scripts/verify-v02-delivery.py` `validate_consumer_receipt` (19-05)

**Analog:** same file 222-248. Additive: add `host_smoke` to the exact-key disjunction and a dedicated check.

```python
if (consumer.get("schema_version") != 2 or consumer.get("result") != "passed" ...
        or not isinstance(behaviors, dict) or set(behaviors) != set(BEHAVIORS)
        ...):
    reject("consumer-binding", "downloaded C and C++ consumer receipt is malformed or not bound to this candidate")
```

Add a separate `reject("consumer-host-smoke", ...)` rule requiring `host_smoke == {"result": "passed", "continuation": ..., "preload": ...}` so the diagnostic names the missing part. `BEHAVIORS` lives in `tests/scripts/verify-v02-consumers.py:29-34` (`profile_selection, probe_info, rgb555_frame_copy, rtc_catch_up`); do not add `host_smoke` to `BEHAVIORS` (it is per-language). Producer side: `test_installed_host.py` `main` (172-187) already prints `installed-host pass continuation=01,02 preload=42 controls=1`; give it `--receipt PATH` to write `{result, continuation, preload}`. Rehearsal `package` job calls it next to the consumers step (`release-rehearsal.yml:~231`, after `verify-v02-consumers.py --prefix "$RUNNER_TEMP/v02-extracted" ... --output build/v02-consumer-receipt.json`). The `v02_consumer_controls_c/_cpp` self-tests are 600 s CTests; add work only in the shared static portion.

---

### `tests/scripts/verify-version-window.py` D-20 rule (19-04)

**Analog:** same file. The tree-only version read already exists:

```python
# 242-254
def tree_version(repo: Path, commit: str) -> str:
    cmake = git_blob(repo, commit, "CMakeLists.txt")
    manifest = git_blob(repo, commit, ".release-please-manifest.json")
    ...
    return listed
# 314-315, inside check_window (active path only)
if tree_version(repo, rev) != version:
    reject("window-version-mismatch", f"the tree at {rev[:12]} is not version {version}")
# 379-390: check_tracked (the static CTest path) reads the record at HEAD but does NOT compare versions
state = validate_record_shape(parse_record(raw))
```

The gap D-20 closes is `check_tracked`: an `active` record is legal only when `record["release_version"] == tree_version(repo, head)`. Add that after 386 with code `window-version-mismatch` (reuse the existing code so `rejected(...)` helpers work). No tags or live refs (D-105). Control: copy 609-615 (`record-for-another-version`) with an active record whose `release_version` differs from the bumped tree, exercised through `check_tracked` rather than `check_window`. The CTest regex `release_window_contract` is `version-window contract pass state=(inactive|active) rev=[0-9a-f]+ inputs=[1-9][0-9]*` (`tests/CMakeLists.txt:1488`); keep the output line unchanged. The `controls=([2-9][0-9]|[1-9][0-9][0-9]+)` regex (1491) is a floor-style pattern; adding controls cannot break it.

**Record commands (window):** `python3 -I tests/scripts/verify-version-window.py --rev <H> --base <main-sha> --digest --body <body-file> --pull-request 131 --ci-run-id <id> --rehearsal-run-id <R1> > tests/data/version-window.json`; `draft_record` (332-361) is the shape, `render_record` (364-365) the byte format.

---

### `tests/scripts/verify-v02-adoption.py` v0.3 notes rules (19-03, D-15)

**Analog:** same file. `check_release_notes` (587-625) is a flat sequence of `require(cond, "release-notes-<reason>")`; each new rule is one `require` plus one entry in `run_self_test_release_notes`'s `mutations` tuple (731-784).

```python
# 603-604 (rule shape)
require(ABSENCE_SENTENCE in text, "release-notes-absence-missing")
checks += 1
# 750-752 (control tuple shape): (name, (old, new), expected reason)
("missing-absence", (ABSENCE_SENTENCE, ""), "release-notes-absence-missing"),
```

New required sentences: "Save states load only in the exact GabbaBoy release that wrote them." and "Host mode is POSIX-only; Windows refuses `--save-dir`." Control per sentence (delete it, comment it out). `FALSE_PUBLICATION_CLAIM` (122-126) and the `("makes no publication claim for v0.2.0", "publication-limit-missing")` pin (260) become `RELEASE_VERSION`-derived (`RELEASE_VERSION` at 79); `docs/release.md:6` changes in 19-06 in the same commit. `perf_disclosure_percent` (573-584) reads `tests/baseline/perf-attribution-v1.json`; regeneration is a hosted `perf-attribution.yml` dispatch (OQ-3).

Unscoped-claim adoption patterns (D-14 control 10) follow the existing regex family `FALSE_SIGNING_CLAIM` / `FALSE_PLATFORM_CLAIM` (115-135): compiled `re.compile(..., re.IGNORECASE)`, wired through `require(pattern.search(text) is None, f"release-notes-{reason}")` (616-622) and the `unnegated(...)` helper (623). Add a control whose positive twin carries the scoped wording.

**Interop widening (D-14 control 11):** `verify-no-interop-claims.py:39-48` `FILES` and `PATTERN`:

```python
FILES = ("README.md", "docs/native-integration.md", "docs/cartridge-and-saves.md", "docs/support/unreleased.md",
         "docs/host-contract.json", NOTE)
PATTERN = re.compile(
    r"(?:byte-identical|compatible|interoperab)[^\n]{0,80}mGBA|mGBA[^\n]{0,80}(?:byte-identical|compatible|interoperab)",
    re.IGNORECASE)
```

Replace `mGBA` with `(?:mGBA|SameBoy|BGB|BESS)` in both alternations, extend `REJECTED_CONTROLS` (52-58) with SameBoy, BGB and BESS sentences, add `docs/support/v0.3.0.md` to `FILES` only for revisions where it exists (compute from the tree ledger like `tree_ledger`; `check` reads every file with `git show`, so a missing file raises `file-missing` at 75), and bump `files=`/`controls=` in `host-contract.cmake:225-226`. The `DISCLAIMERS` regex (46-48) lists five phrases; keep them mGBA-agnostic because they already begin with "not byte-identical to" etc.

---

### CHANGELOG first-heading check and docs link check (19-06)

**Analog (shape):** `tests/scripts/verify-no-interop-claims.py` — a stdlib checker that reads files with `git show REV:path` (never the working tree), runs its own accepted and rejected controls in the same run, prints one success line with counts, and emits `REJECT <code>: <message>` on stderr (`read_at` 72-79, `scan` 81-87, `check` 89-104, `main` 106-117). Registration: `host-contract.cmake:221-226` (`add_test(NAME doc_no_interop_claims COMMAND "${Python3_EXECUTABLE}" -I ... --rev "${GBB_HOST_CONTRACT_REV}" --repo "${PROJECT_SOURCE_DIR}")` with `PASS_REGULAR_EXPRESSION` and `TIMEOUT 60`), and add the new names to `GBB_REV_WIRING_TESTS` (232-233) so the HEAD-not-SHA wiring check covers them. Controls: `## Unreleased` above a version -> reject; first heading a `## [X.Y.Z]` link -> accept; docs link to `support/v0.1.0.md` when `v0.3.0.md` exists -> reject. Python-only, no `if(NOT WIN32)` edits.

---

### `tests/data/state-compatibility.json` `release-change` row (19-06 draft, 19-07 window)

**Analog:** `tests/scripts/verify-state-pins.py:296-300` consumes it:

```python
elif row["kind"] in ("format-change", "behavior-change", "release-change"):
    required_token = {"format-change": "format_version", "behavior-change": "behavior_version",
                      "release-change": "release"}[row["kind"]]
    if row.get("required_token") != required_token or base_tokens[required_token] == current_tokens[required_token]:
        reject("required-token-unchanged", "the disposition's required compatibility token did not change")
```

and refuses to relabel 0.2.1 pins for `pre-first-state-release-evolution` at 295. Row fields to copy are the existing `initial-state-pin-mainline-base` entry (keys: `accepted, affected_semantics, approval_basis, approved_by, base_revision, base_state_release_exists, decision, decision_refs, evidence, id, kind, new_golden_sha256, old_golden_sha256, rationale, tokens_after, tokens_before`); add `required_token: "release"`. Hand-authored review content in the version PR (D-19), pre-drafted outside the tree until the window.

---

## Shared Patterns

### Trusted judge, subject as data
**Source:** `.github/workflows/release-rehearsal.yml` `judge` (330-400); `release-please.yml` `version-window` (55-140); `release.yml:1171`.
**Apply to:** the pre-tag gate, every judge call added to `release.yml`, `release-evidence-lifecycle.sh`, `release-rehearsal.yml`.

```yaml
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
  with:
    ref: ${{ github.event.repository.default_branch }}
    path: trusted-judge
    persist-credentials: false
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
  with:
    path: subject
    persist-credentials: false
...
python3 -I trusted-judge/.github/scripts/verify-workflow-policy.py --check --root subject --release-head
```

Shallow-checkout caveat for D-04: both checkouts have default depth, and the policy runs git with `cwd=root` (the subject). The only precedent for bringing subject objects into the trusted checkout is `git -C trusted-judge fetch --no-tags --quiet "$PWD/subject" "$GITHUB_SHA"` (`release-rehearsal.yml:372`, judge step "Verify the retained rehearsal campaign receipt"). For the tree-equality rule, either set `fetch-depth: 0` on `trusted-judge` and give the policy a `--git-root`, or fetch both objects. Pin the choice and add a mutant.

### Exact-action pinning and checkout hygiene
**Source:** `verify-workflow-policy.py` `_check_actions`, `_check_checkout_credentials` (345-346), `_check_disabled`, `_check_ignored_failures`. All workflows use `actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2` and `actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02 # v4.6.2`. Copy these pins verbatim; adding a new action is against the copy-over-dependency rule.
**Apply to:** the new workflow, the libbet-repro fix, the perf-gate upload.

### Immutable-commit reads
**Source:** `verify-v03-dispositions.py` `Source.read` (118-130), `verify-no-interop-claims.py` `read_at` (72-79), `verify-version-window.py` `git_blob`, `verify-support-ledger.py` `immutable_git_file` (2774).
**Apply to:** every new checker (claims derived-value checks, readback, CHANGELOG, docs links). Read with `git show REV:path`, bound the size (`MAX_BYTES`), never `git` against HEAD or a tag name from a checker that runs in the tagged tree's CI (D-20, D-105).

### Control discipline
**Source:** analogs 1 and 2 above. Every new rule gets a negative control whose rejection reason is asserted by code or substring, run in the same invocation as an unrelated positive. The CTest wrapper then enforces a parsed minimum (`GBB_EXPECT_MIN_KEY=controls`), so dropping a control fails.

### Strict JSON for managed inputs
**Source:** `verify-support-ledger.py` `strict_json` (rejects duplicate keys; used at 2782 and exercised at 2992-2994) and `verify-workflow-policy.py` `_ledger_pairs` (2233-2239, `timeout-ledger-schema` on a repeated key). Use one of these for every new JSON reader; do not call bare `json.loads`.

### Byte-exact generated files
**Source:** `write_generated_ledger` / `require_generated` (2865-2871). Write with bytes, LF only (GB-CI-011); the ledger must not embed a full release source SHA (`parse_ledger` rejects `source_sha`/`release_source_sha`); `refuse_tagged_target` (2808-2817) blocks `--write-current` onto a tagged version.

### Privacy scan
**Source:** `verify-release-lifecycle.py:164` `FORBIDDEN_TEXT = /Users/|/home/|<drive>:\\Users|gh[pousr]_...|github_pat_|BEGIN ... PRIVATE KEY`. Apply to every committed JSON receipt or capture added in this phase (readback, perf receipt fixtures, claims file).

---

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| Rehearsal "refuse to run if `vX.Y.Z` exists remotely" step in `release-rehearsal.yml` | workflow step | request-response | The rehearsal token is `contents: read` and no step queries remote tags. Nearest is the `candidate` identity step's `gh api "repos/$GH_REPO/releases?per_page=100"` / `commits/$RELEASE_TAG` pattern (`release.yml:105-114`), which is write-capable context. Use `git ls-remote --tags origin "refs/tags/$REHEARSAL_TAG"` (no token needed on a public repo) and add a policy pin forbidding any other `gh`/network form in the producer jobs. |
| Scoped-claim derived-value cross-checks reading `tests/data/state-forks.json`, `docs/host-contract.json`, and the `if(WIN32)` list in `cmake/ExpectedTests.cmake` | checker | transform | No existing checker joins these three sources. Closest: `verify-state-forks.py` for `expected_case_count`, `verify-host-contract.py` for the host-contract rows, and `verify-test-inventory.sh:6-150` for the WIN32 exclusion list (the claim validator must parse the CMake list itself, as `verify-test-inventory.sh` does with `sed`). Build each as a small helper in `verify-support-ledger.py` that reads via `immutable_git_file`. |
| Hosted-only evidence (perf-gate receipt upload, host smoke on shipped bytes, R1/R2, pre-tag gate run) | evidence | event-driven | Cannot be exercised locally. Prove the validators with fixture receipts and the lifecycle replay; the hosted facts are verified at the window (RESEARCH "Hosted-only evidence"). |

## Metadata

**Analog search scope:** `.github/scripts/`, `.github/workflows/`, `.github/ci-timeouts.json`, `tests/scripts/`, `tests/cmake/`, `tests/CMakeLists.txt`, `tests/player/CMakeLists.txt`, `tests/data/release-api/`, `cmake/ExpectedTests.cmake`, `src/core/gabbaboy.c`, `docs/release.md`, `CHANGELOG.md`, `.planning/phases/GB-17-native-save-state-core/17-REVIEW.md`, `.planning/phases/GB-18-player-save-slots-and-host-contract/18-04-SUMMARY.md`.
**Files read for excerpts:** 33 (large files read by targeted ranges only; no range read twice).
**Pattern extraction date:** 2026-10-29
**Open points the planner must settle before coding (carried from RESEARCH, still open):** OQ-1 (branch retention without a live ref read; recommend object-readability in `--release-head` mode only), OQ-2 (carrier for the perf-gate binding; recommend an embedded `perf_gate` block in `release-receipt.json`), OQ-3 (hosted `perf-attribution.yml` dispatch for the notes Ir figure), OQ-4 (new workflow, recommended), OQ-5 (gate is not a required check).
