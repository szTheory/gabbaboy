#!/usr/bin/env python3
"""Pin workflow-policy control IDs to an immutable source and the configured CTest inventory."""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

if not __debug__ or sys.flags.optimize:
    raise SystemExit("verify-workflow-policy-coverage must not run with python -O")

ROOT = Path(__file__).resolve().parents[2]
BASELINE_COMMIT = "70d3e42225c14e636876aad6697672ec08d861b3"
POLICY_PATH = ".github/scripts/verify-workflow-policy.py"
POLICY_SHA256 = "c5aa1d60a2391e7126e714bcf101292dc86c75ddd1cd6167aea55cdb8b629083"
REVIEWED_POLICY_COMMIT = "2c4a66ad50b979bbfcf3bff6cf9f4e644a56d9b7"
REVIEWED_POLICY_SHA256 = "f6092a477be22336ffe585c25508f3e7da761e7b9da3f3716e3f0dbdc302405c"
GROUPS = {
    "ci": "workflow_policy_group_ci",
    "release_jobs": "workflow_policy_group_release_jobs",
    "release_support": "workflow_policy_group_release_support",
    "rehearsal": "workflow_policy_group_rehearsal",
    "ledger": "workflow_policy_group_ledger",
    "helpers": "workflow_policy_group_helpers",
}
GROUP_COMPLETION_FILES = {"ci": "ci", "release_jobs": "release-jobs", "release_support": "release-support",
                          "rehearsal": "rehearsal", "ledger": "ledger", "helpers": "helpers"}
GROUP_BY_WORKFLOW = {
    "ci.yml": "ci", "fixture-repro.yml": "ci", "libbet-repro.yml": "ci", "nightly-asan.yml": "ci",
    "perf-attribution.yml": "ci", "preview.yml": "ci",
    "release.yml": "release_jobs", "lifecycle": "release_support", "script": "release_support",
    "perfgate": "release_support",
    "release-rehearsal.yml": "rehearsal", "release-please.yml": "rehearsal",
    "version-pr-gate.yml": "rehearsal", "config": "rehearsal",
}
EXPECTED_TEST_NAMES = set(GROUPS.values()) | {"workflow_policy_coverage", "workflow_policy_coverage_controls"}
POLICY_TEST_NAMES = EXPECTED_TEST_NAMES | {"workflow_policy_check"}
ALL_PLATFORMS = ("posix", "windows")
POSIX_ONLY = ("posix",)
ADDED_POLICY_FUNCTIONS = {
    "_policy_control_id", "_record_policy_completion", "_mark_policy_control", "run_policy_self_test",
}
ADDED_POLICY_GLOBALS = {
    "_POLICY_PARTITION_GROUPS", "_ACTIVE_POLICY_GROUP", "_ACTIVE_POLICY_CONTROLS", "_COMPLETED_POLICY_CONTROLS",
}
INSTRUMENTED_POLICY_FUNCTIONS = {
    "_window_discovery_shell_controls", "report_red_replay_controls", "_ledger_boundary_controls",
    "_ledger_git_object_controls", "_ledger_disclosure_scratch_controls", "_ledger_release_object_scratch_controls",
    "verify_cited_stub_controls", "rehearsal_bash_resolver_controls", "rehearsal_tag_guard_controls", "self_test",
}


class CoverageError(Exception):
    pass


def stable_id(kind: str, *parts: str) -> str:
    raw = json.dumps([kind, *parts], ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    return f"{kind}-{hashlib.sha256(raw).hexdigest()[:20]}"


def reject(message: str) -> None:
    raise CoverageError(message)


def baseline_source(root: Path) -> bytes:
    result = subprocess.run(["git", "show", f"{BASELINE_COMMIT}:{POLICY_PATH}"], cwd=root,
                            capture_output=True, check=False, timeout=15)
    if result.returncode != 0:
        reject(f"immutable workflow-policy source is unavailable: {result.stderr.decode(errors='replace').strip()}")
    digest = hashlib.sha256(result.stdout).hexdigest()
    if digest != POLICY_SHA256:
        reject(f"immutable workflow-policy source hash changed: {digest}")
    return result.stdout


def reviewed_policy_source(root: Path) -> bytes:
    result = subprocess.run(["git", "show", f"{REVIEWED_POLICY_COMMIT}:{POLICY_PATH}"], cwd=root,
                            capture_output=True, check=False, timeout=15)
    if result.returncode != 0:
        reject(f"reviewed workflow-policy source is unavailable: {result.stderr.decode(errors='replace').strip()}")
    digest = hashlib.sha256(result.stdout).hexdigest()
    if digest != REVIEWED_POLICY_SHA256:
        reject(f"reviewed workflow-policy source hash changed: {digest}")
    return result.stdout


def verify_reviewed_policy_identity(candidate: bytes, reviewed: bytes | None) -> None:
    if reviewed is None:
        reject("reviewed workflow-policy source identity is missing")
    reviewed_digest = hashlib.sha256(reviewed).hexdigest()
    if reviewed_digest != REVIEWED_POLICY_SHA256:
        reject(f"reviewed workflow-policy source identity has the wrong digest: {reviewed_digest}")
    if candidate != reviewed:
        reject("candidate workflow-policy source differs from the exact reviewed snapshot")


def git_text(root: Path, revision: str, path: str) -> bytes:
    result = subprocess.run(["git", "show", f"{revision}:{path}"], cwd=root,
                            capture_output=True, check=False, timeout=15)
    if result.returncode != 0:
        reject(f"immutable candidate source is unavailable: {revision}:{path}")
    return result.stdout


def resolve_commit(root: Path, revision: str) -> str:
    result = subprocess.run(["git", "rev-parse", "--verify", "--quiet", f"{revision}^{{commit}}"], cwd=root,
                            capture_output=True, text=True, check=False, timeout=15)
    commit = result.stdout.strip()
    if result.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40,64}", commit):
        reject(f"candidate revision is not an immutable commit: {revision}")
    return commit


def load_baseline_namespace(source: bytes) -> dict:
    path = str(ROOT / POLICY_PATH)
    namespace = {"__name__": "baseline_workflow_policy", "__file__": path}
    exec(compile(source, path, "exec"), namespace)
    return namespace


def _function_node(tree: ast.Module, name: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    reject(f"baseline helper function is missing: {name}")


def _loop_rows(function: ast.FunctionDef | ast.AsyncFunctionDef, first_target: str) -> list[ast.Tuple]:
    for node in ast.walk(function):
        if isinstance(node, (ast.For, ast.AsyncFor)):
            target = node.target
            names = [item.id for item in ast.walk(target) if isinstance(item, ast.Name)]
            if first_target in names and isinstance(node.iter, ast.Tuple):
                rows = [item for item in node.iter.elts if isinstance(item, ast.Tuple)]
                if rows:
                    return rows
    reject(f"baseline control table is missing for {function.name}:{first_target}")


def _first_string(row: ast.Tuple, where: str) -> str:
    if not row.elts:
        reject(f"empty baseline control row in {where}")
    try:
        value = ast.literal_eval(row.elts[0])
    except (ValueError, TypeError) as error:
        reject(f"baseline control label is not literal in {where}: {error}")
    if not isinstance(value, str):
        reject(f"baseline control label is not text in {where}")
    return value


def _source_for_function(source: bytes, name: str) -> str:
    tree = ast.parse(source, filename=POLICY_PATH)
    node = _function_node(tree, name)
    return ast.get_source_segment(source.decode("utf-8"), node) or ""


def _helper_row(family: str, source_name: str, *parts: str, platforms=ALL_PLATFORMS) -> dict:
    key = [family, *parts]
    return {
        "id": stable_id("helper", *key), "kind": "helper", "key": key, "group": "helpers",
        "platforms": list(platforms), "source": source_name,
    }


def _literal_rows_from_assignment(tree: ast.Module, function_name: str, assignment_name: str) -> list[ast.Tuple]:
    function = _function_node(tree, function_name)
    for node in ast.walk(function):
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == assignment_name
                                                for target in node.targets):
            if isinstance(node.value, ast.Tuple):
                return [item for item in node.value.elts if isinstance(item, ast.Tuple)]
    reject(f"baseline {function_name} control table is missing: {assignment_name}")


def baseline_controls(source: bytes) -> list[dict]:
    namespace = load_baseline_namespace(source)
    tree = ast.parse(source, filename=POLICY_PATH)
    rows: list[dict] = []

    for builder in ("_mutations", "_window_mutations", "_version_pr_gate_mutations"):
        for label, workflow, _edits, expected in namespace[builder]():
            group = GROUP_BY_WORKFLOW.get(workflow)
            if group is None:
                reject(f"baseline mutation workflow has no semantic group: {workflow}")
            key = [label, expected]
            rows.append({
                "id": stable_id("mutation", *key), "kind": "mutation", "key": key, "group": group,
                "platforms": list(ALL_PLATFORMS), "source": builder, "workflow": workflow,
                "expected": expected, "label": label,
            })
    for label, _mutate, _extra, expected in namespace["_ledger_mutations"]():
        key = [label, expected]
        rows.append({
            "id": stable_id("ledger-mutation", *key), "kind": "ledger-mutation", "key": key,
            "group": "ledger", "platforms": list(ALL_PLATFORMS), "source": "_ledger_mutations",
            "expected": expected, "label": label,
        })

    rows.append(_helper_row("baseline-positive-cli", "self_test", "workflow checker accepts the baseline"))
    for (workflow, job_id), _expected in namespace["MACOS_QUALIFICATION_JOBS"].items():
        rows.append(_helper_row("macos-runner-positive", "self_test", workflow, job_id))
    rows.append(_helper_row("release-receipt-runner-positive", "self_test", "macOS receipt runner"))

    # Each named input case is independently marked after all output, status, API and checker-call assertions pass.
    window_function = _function_node(tree, "_window_discovery_shell_controls")
    for row in _loop_rows(window_function, "label"):
        rows.append(_helper_row("window-discovery", "_window_discovery_shell_controls",
                                _first_string(row, "window discovery"), platforms=POSIX_ONLY))
    invalid_rows = _literal_rows_from_assignment(tree, "_window_discovery_shell_controls", "invalid_cases")
    for row in invalid_rows:
        rows.append(_helper_row("window-discovery", "_window_discovery_shell_controls",
                                _first_string(row, "invalid window discovery"), platforms=POSIX_ONLY))
    rows.append(_helper_row("window-discovery", "_window_discovery_shell_controls", "legacy-query", platforms=POSIX_ONLY))

    resolver = _function_node(tree, "rehearsal_bash_resolver_controls")
    for row in _loop_rows(resolver, "label"):
        rows.append(_helper_row("git-bash-resolver", "rehearsal_bash_resolver_controls",
                                _first_string(row, "Git Bash resolver")))
    for label in ("missing Git lookup", "missing git.exe file", "unsupported Git layout",
                  "Windows system-directory alias", "WSL System32 alias refusal", "non-Windows behavior"):
        rows.append(_helper_row("git-bash-resolver", "rehearsal_bash_resolver_controls", label))

    tag_function = _function_node(tree, "rehearsal_tag_guard_controls")
    tag_calls = [node for node in ast.walk(tag_function)
                 if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "run"]
    if len(tag_calls) != 3:
        reject(f"baseline rehearsal tag guard should have three branch scenarios, found {len(tag_calls)}")
    for label in ("untagged release rehearsal", "existing release tag", "non-release rehearsal branch"):
        rows.append(_helper_row("tag-guard", "rehearsal_tag_guard_controls", label))

    ledger_boundary = _function_node(tree, "_ledger_boundary_controls")
    boundary_rows = _loop_rows(ledger_boundary, "label")
    if len(boundary_rows) != 11:
        reject(f"baseline ledger boundary table should have 11 rows, found {len(boundary_rows)}")
    rows.append(_helper_row("ledger-boundary", "_ledger_boundary_controls", "exact ceil ratio passes"))
    rows.append(_helper_row("ledger-boundary", "_ledger_boundary_controls", "tree-equal exact ceil ratio passes"))
    for row in boundary_rows:
        rows.append(_helper_row("ledger-boundary", "_ledger_boundary_controls",
                                _first_string(row, "ledger boundary")))

    git_object = _function_node(tree, "_ledger_git_object_controls")
    expect_calls = [node for node in ast.walk(git_object)
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "expect"]
    if len(expect_calls) != 4:
        reject(f"baseline ledger Git object controls should have four rejection scenarios, found {len(expect_calls)}")
    for label in ("default ref avoids origin", "tree mismatch", "anchor not on main", "unreadable anchor",
                  "explicit origin ref honored"):
        rows.append(_helper_row("ledger-git-object", "_ledger_git_object_controls", label))

    for index, label in enumerate(("changed body without disclosure refused", "disclosed body accepted",
                                   "unchanged body accepted", "disclosure comparison disabled"), start=1):
        rows.append(_helper_row("ledger-disclosure", "_ledger_disclosure_scratch_controls", label))
    if sum(1 for node in ast.walk(_function_node(tree, "_ledger_disclosure_scratch_controls"))
           if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "check") != 4:
        reject("baseline disclosure scratch controls must exercise four comparison states")

    release_object = _function_node(tree, "_ledger_release_object_scratch_controls")
    release_checks = [node for node in ast.walk(release_object)
                      if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "check"]
    if len(release_checks) != 2:
        reject(f"baseline release-object controls should have two CLI cases, found {len(release_checks)}")
    for label in ("retained tree-equal citation accepted", "pruned tree-equal citation refused"):
        rows.append(_helper_row("ledger-release-object", "_ledger_release_object_scratch_controls", label))

    cited_stub = _function_node(tree, "verify_cited_stub_controls")
    cited_runs = [node for node in ast.walk(cited_stub)
                  if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "run"]
    if len(cited_runs) != 3:
        reject(f"baseline verify-cited stub should have three CLI cases, found {len(cited_runs)}")
    for label in ("tree-equal citation accepted", "missing predecessor job refused", "wrong API tree refused"):
        rows.append(_helper_row("verify-cited-stub", "verify_cited_stub_controls", label, platforms=POSIX_ONLY))

    self_test_node = _function_node(tree, "self_test")
    for loop in ast.walk(self_test_node):
        if not isinstance(loop, ast.For) or not isinstance(loop.iter, ast.Tuple):
            continue
        names = [item.id for item in ast.walk(loop.target) if isinstance(item, ast.Name)]
        if "label" not in names:
            continue
        for row in (item for item in loop.iter.elts if isinstance(item, ast.Tuple)):
            label = _first_string(row, "self-test inline labels")
            if label.startswith("WR-C01"):
                rows.append(_helper_row("closed-workflow-set", "self_test", label))
            elif label.startswith("residual job") or label.startswith("exempt job"):
                rows.append(_helper_row("residual-classification", "self_test", label))
            elif label.startswith("credential exemption"):
                rows.append(_helper_row("credential-exemption", "self_test", label))
    formatting_loops = [node for node in ast.walk(self_test_node) if isinstance(node, ast.For)
                        and isinstance(node.target, ast.Name) and node.target.id == "variant"
                        and isinstance(node.iter, ast.Tuple)]
    if len(formatting_loops) != 1 or len(formatting_loops[0].iter.elts) != 3:
        reject("baseline has unexpected equivalent-formatting control table")
    for index in range(1, 4):
        rows.append(_helper_row("formatting-positive", "self_test", str(index)))
    rows.append(_helper_row("hostile-subject", "self_test", "judge and module shadowing refused"))

    red_replay = _function_node(tree, "report_red_replay_controls")
    for name in namespace["_REPORT_SCENARIOS"]:
        rows.append(_helper_row("red-report-scenario", "report_red_replay_controls", name[0], platforms=POSIX_ONLY))
    mutant_rows = _literal_rows_from_assignment(tree, "report_red_replay_controls", "mutants")
    if len(mutant_rows) != 8:
        reject(f"baseline red-report mutant table should have eight rows, found {len(mutant_rows)}")
    for row in mutant_rows:
        rows.append(_helper_row("red-report-mutant", "report_red_replay_controls",
                                _first_string(row, "red-report mutant"), platforms=POSIX_ONLY))

    ids = [row["id"] for row in rows]
    if len(ids) != len(set(ids)):
        reject("baseline workflow-policy control identities are not unique")
    return sorted(rows, key=lambda row: row["id"])


def manifest_for(source: bytes) -> dict:
    baseline_rows = baseline_controls(source)
    rows = [{key: row[key] for key in ("id", "kind", "group", "platforms")} for row in baseline_rows]
    return {
        "schema_version": 1,
        "baseline_commit": BASELINE_COMMIT,
        "baseline_script_sha256": POLICY_SHA256,
        "groups": {name: {"ctest": ctest, "timeout_seconds": 180} for name, ctest in GROUPS.items()},
        "controls": rows,
    }


class _StripMarkersAndSelectors(ast.NodeTransformer):
    """Normalize only the self-test instrumentation and selectors before baseline AST comparison."""

    def __init__(self, *, strip_cli_selectors: bool = False, normalize_self_test: bool = False,
                 strip_markers: bool = False, normalize_main: bool = False):
        self.strip_cli_selectors = strip_cli_selectors
        self.normalize_self_test = normalize_self_test
        self.strip_markers = strip_markers
        self.normalize_main = normalize_main
    def visit_FunctionDef(self, node: ast.FunctionDef):
        node = self.generic_visit(node)
        if node.name == "self_test":
            node.body = [stmt for stmt in node.body if not (
                isinstance(stmt, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "run_helpers"
                                                     for target in stmt.targets))]
        return node

    def visit_Expr(self, node: ast.Expr):
        value = node.value
        if (self.strip_markers and isinstance(value, ast.Call)
                and isinstance(value.func, ast.Name) and value.func.id == "_mark_policy_control"):
            return None
        if (self.strip_cli_selectors and isinstance(value, ast.Call)
                and isinstance(value.func, ast.Attribute) and value.func.attr == "add_argument"):
            if value.args and isinstance(value.args[0], ast.Constant) and value.args[0].value in ("--group", "--completed-file"):
                return None
        return self.generic_visit(node)

    def visit_If(self, node: ast.If):
        node = self.generic_visit(node)
        if (self.normalize_self_test and isinstance(node.test, ast.Name) and node.test.id == "run_helpers"):
            return node.body
        return node

    def visit_Call(self, node: ast.Call):
        node = self.generic_visit(node)
        if self.normalize_main and isinstance(node.func, ast.Name) and node.func.id == "run_policy_self_test":
            return ast.copy_location(ast.Call(func=ast.Name(id="self_test", ctx=ast.Load()),
                                              args=[node.args[0]], keywords=[]), node)
        return node


def _compare_baseline_source_identity(baseline: bytes, current: bytes) -> None:
    try:
        baseline_tree = ast.parse(baseline, filename=POLICY_PATH)
        current_tree = ast.parse(current, filename=POLICY_PATH)
    except SyntaxError as error:
        reject(f"workflow-policy source does not parse: {error}")
    def unique_functions(tree: ast.Module, source_name: str) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
        functions = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
        names = [node.name for node in functions]
        if len(names) != len(set(names)):
            reject(f"{source_name} contains duplicate top-level function definitions")
        return {node.name: node for node in functions}

    baseline_functions = unique_functions(baseline_tree, "immutable workflow-policy source")
    current_functions = unique_functions(current_tree, "candidate workflow-policy source")
    missing_functions = set(baseline_functions) - set(current_functions)
    added_functions = set(current_functions) - set(baseline_functions)
    if missing_functions:
        reject(f"baseline checker functions were removed: {sorted(missing_functions)}")
    if added_functions != ADDED_POLICY_FUNCTIONS:
        reject(f"workflow-policy selector functions differ from the approved set: {sorted(added_functions)}")
    for name in ADDED_POLICY_FUNCTIONS:
        function = current_functions[name]
        if function.decorator_list:
            reject(f"new selector function {name} has an unapproved import-time decorator")
        if any(not isinstance(default, ast.Constant) for default in [*function.args.defaults, *function.args.kw_defaults]
               if default is not None):
            reject(f"new selector function {name} has a nonliteral import-time default")

    # Exactly one of each CLI selector may be added to main; a duplicate option can silently change argparse behavior.
    main_node = current_functions.get("main")
    if main_node is None:
        reject("candidate workflow-policy source is missing main")
    selector_counts = {"--group": 0, "--completed-file": 0}
    for node in ast.walk(main_node):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "add_argument"
                and node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value in selector_counts):
            selector_counts[node.args[0].value] += 1
    if selector_counts != {"--group": 1, "--completed-file": 1}:
        reject("workflow-policy CLI selector arguments are missing or duplicated")
    expected_selector_calls = [
        node for node in ast.parse(
            'parser.add_argument("--group", choices=(*_POLICY_PARTITION_GROUPS, "all"), default="all",\n'
            '                    help="limit --self-test to one registered control group; defaults to all controls")\n'
            'parser.add_argument("--completed-file", type=Path, default=None,\n'
            '                    help="write completed stable control IDs after a successful --self-test")\n'
        ).body
    ]
    actual_selector_calls = [
        node for node in ast.walk(main_node)
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Attribute) and node.value.func.attr == "add_argument"
        and node.value.args and isinstance(node.value.args[0], ast.Constant)
        and node.value.args[0].value in selector_counts
    ]
    if ([ast.dump(node, include_attributes=False) for node in actual_selector_calls]
            != [ast.dump(node, include_attributes=False) for node in expected_selector_calls]):
        reject("workflow-policy group/completion CLI selectors differ from their approved defaults and semantics")

    for name, baseline_node in baseline_functions.items():
        transform = _StripMarkersAndSelectors(
            strip_cli_selectors=(name == "main"), normalize_self_test=(name == "self_test"),
            strip_markers=(name in INSTRUMENTED_POLICY_FUNCTIONS), normalize_main=(name == "main"),
        )
        normalized = transform.visit(copy.deepcopy(current_functions[name]))
        if ast.dump(normalized, include_attributes=False) != ast.dump(baseline_node, include_attributes=False):
            if name == "self_test":
                reject("self-test assertion/oracle statements changed outside verified group guards and completion markers")
            if name == "main":
                reject("main CLI production path changed outside the self-test selector extension")
            reject(f"baseline checker function or assertion semantics changed: {name}")

    expected_assignments = ast.parse(
        "_POLICY_PARTITION_GROUPS = ('ci', 'release_jobs', 'release_support', 'rehearsal', 'ledger', 'helpers')\n"
        "_ACTIVE_POLICY_GROUP: str | None = None\n"
        "_ACTIVE_POLICY_CONTROLS: dict[str, dict] = {}\n"
        "_COMPLETED_POLICY_CONTROLS: set[str] = set()\n"
    ).body
    expected_assignment_dumps = [ast.dump(node, include_attributes=False) for node in expected_assignments]
    if len(expected_assignment_dumps) != len(ADDED_POLICY_GLOBALS):
        reject("internal selector-constant contract is malformed")
    expected_assignment_by_dump = {value: index for index, value in enumerate(expected_assignment_dumps)}
    expected_hash_import = ast.dump(ast.parse("import hashlib").body[0], include_attributes=False)
    consumed_selector_assignments: set[int] = set()
    consumed_hash_import = False
    normalized_current_body: list[ast.stmt] = []
    for node in current_tree.body:
        dumped = ast.dump(node, include_attributes=False)
        if isinstance(node, (ast.Import, ast.ImportFrom)) and dumped == expected_hash_import and not consumed_hash_import:
            consumed_hash_import = True
            continue
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and dumped in expected_assignment_by_dump:
            assignment_index = expected_assignment_by_dump[dumped]
            if assignment_index not in consumed_selector_assignments:
                consumed_selector_assignments.add(assignment_index)
                continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in ADDED_POLICY_FUNCTIONS:
            continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            transform = _StripMarkersAndSelectors(
                strip_cli_selectors=(node.name == "main"), normalize_self_test=(node.name == "self_test"),
                strip_markers=(node.name in INSTRUMENTED_POLICY_FUNCTIONS), normalize_main=(node.name == "main"),
            )
            node = transform.visit(copy.deepcopy(node))
        normalized_current_body.append(node)
    if not consumed_hash_import:
        reject("workflow-policy is missing its approved stable-ID hash import")
    if len(consumed_selector_assignments) != len(expected_assignment_dumps):
        reject("workflow-policy selector constants differ from the approved set")
    if len(ADDED_POLICY_FUNCTIONS & set(current_functions)) != len(ADDED_POLICY_FUNCTIONS):
        reject("workflow-policy selector function set is incomplete")
    normalized_current = ast.Module(body=normalized_current_body, type_ignores=current_tree.type_ignores)
    if ast.dump(normalized_current, include_attributes=False) != ast.dump(baseline_tree, include_attributes=False):
        reject("ordered workflow-policy module differs from the immutable baseline after approved selector normalization")


def verify_source_identity(root: Path, candidate: bytes) -> None:
    """Require the exact reviewed instrumented blob, then retain the independent baseline AST proof."""
    reviewed = reviewed_policy_source(root)
    verify_reviewed_policy_identity(candidate, reviewed)
    _compare_baseline_source_identity(baseline_source(root), candidate)


def validate_manifest(manifest: dict, expected: dict) -> None:
    if manifest.get("schema_version") != 1:
        reject("workflow-policy registry schema version is unsupported")
    if manifest.get("baseline_commit") != BASELINE_COMMIT or manifest.get("baseline_script_sha256") != POLICY_SHA256:
        reject("workflow-policy registry is not anchored to the reviewed baseline")
    if manifest.get("groups") != expected["groups"]:
        reject("workflow-policy group names or 180-second per-group limits differ from the contract")
    rows = manifest.get("controls")
    if not isinstance(rows, list):
        reject("workflow-policy registry controls must be a list")
    ids = [row.get("id") for row in rows if isinstance(row, dict)]
    if len(ids) != len(rows) or len(ids) != len(set(ids)):
        reject("workflow-policy registry contains duplicate or malformed stable IDs")
    if rows != expected["controls"]:
        expected_map = {row["id"]: row for row in expected["controls"]}
        actual_map = {row.get("id"): row for row in rows if isinstance(row, dict)}
        if set(actual_map) != set(expected_map):
            reject("workflow-policy registry omits or adds baseline control IDs")
        for control_id in sorted(expected_map):
            if actual_map[control_id] != expected_map[control_id]:
                reject(f"workflow-policy registry group/platform/semantics differ for {control_id}")
        reject("workflow-policy registry ordering or metadata differs from baseline")
    for platform in ALL_PLATFORMS:
        expected_ids = {row["id"] for row in expected["controls"] if platform in row["platforms"]}
        per_group = [{row["id"] for row in rows if platform in row["platforms"] and row["group"] == group}
                     for group in GROUPS]
        if set().union(*per_group) != expected_ids:
            reject(f"workflow-policy {platform} groups do not cover the complete baseline inventory")
        for index, group_ids in enumerate(per_group):
            if any(group_ids & later for later in per_group[index + 1:]):
                reject(f"workflow-policy {platform} groups overlap")


def _test_properties(test: dict) -> dict[str, object]:
    result = {}
    for item in test.get("properties", []):
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            reject("CTest test contains a malformed property")
        name = item["name"]
        if name in result:
            reject(f"CTest test repeats property {name}")
        result[name] = item.get("value")
    return result


def _same_path(left: str | Path, right: str | Path) -> bool:
    return os.path.normcase(str(Path(left).resolve())) == os.path.normcase(str(Path(right).resolve()))


def _cmake_cache(build_dir: Path) -> dict[str, str]:
    cache_path = build_dir / "CMakeCache.txt"
    try:
        lines = cache_path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        reject(f"configured CMake cache is unavailable: {error}")
    result: dict[str, str] = {}
    for line in lines:
        if line.startswith(("//", "#")) or "=" not in line or ":" not in line.partition("=")[0]:
            continue
        result[line.partition(":")[0]] = line.partition("=")[2]
    return result


def _truthy_cmake(value: str) -> bool:
    return value.upper() in {"ON", "TRUE", "YES", "Y", "1"}


def _parse_wrapper_definitions(test: dict, root: Path, cmake_executable: str) -> dict[str, str]:
    command = [str(value) for value in test.get("command", [])]
    if not command or not _same_path(command[0], cmake_executable):
        reject("CTest does not invoke the configured CMake executable")
    wrapper_path = (root / "tests/expect_exit.cmake").resolve()
    script_positions = [index for index, value in enumerate(command) if value == "-P"]
    if len(script_positions) != 1 or script_positions[0] != len(command) - 2:
        reject("CTest wrapper must have one final -P script argument and no trailing arguments")
    if not _same_path(command[-1], wrapper_path):
        reject("CTest does not invoke the exact tests/expect_exit.cmake wrapper")

    definitions: dict[str, str] = {}
    index = 1
    while index < script_positions[0]:
        part = command[index]
        if part == "-D":
            index += 1
            if index >= script_positions[0]:
                reject("CTest has a dangling -D option")
            assignment = command[index]
        elif part.startswith("-D"):
            assignment = part[2:]
        else:
            reject(f"CTest wrapper has an unapproved CMake argument: {part}")
        match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)(?::[A-Za-z_][A-Za-z0-9_]*)?=(.*)", assignment, re.DOTALL)
        if not match:
            reject(f"CTest wrapper has a malformed -D definition: {assignment}")
        name, value = match.groups()
        if name in definitions:
            reject(f"CTest wrapper repeats or overrides -D{name}")
        definitions[name] = value
        index += 1
    return definitions


def _parse_python_cli(command: list[str], expected_executable: str, expected_script: Path,
                      value_flags: set[str], boolean_flags: set[str]) -> tuple[dict[str, str], set[str]]:
    if len(command) < 3 or not _same_path(command[0], expected_executable):
        reject("CTest does not invoke the configured Python interpreter")
    if command[1] != "-I":
        reject("CTest Python command must place -I immediately before the checker script")
    if not _same_path(command[2], expected_script):
        reject("CTest Python command does not invoke the exact checker script")
    parsed_values: dict[str, str] = {}
    parsed_booleans: set[str] = set()
    index = 3
    while index < len(command):
        token = command[index]
        if not token.startswith("--"):
            reject(f"CTest checker command contains an unapproved positional argument: {token}")
        flag, separator, inline_value = token.partition("=")
        if flag in boolean_flags:
            if separator or flag in parsed_booleans:
                reject(f"CTest checker command repeats or assigns boolean option {flag}")
            parsed_booleans.add(flag)
        elif flag in value_flags:
            if flag in parsed_values:
                reject(f"CTest checker command repeats or overrides {flag}")
            if separator:
                value = inline_value
            else:
                index += 1
                if index >= len(command) or command[index].startswith("--"):
                    reject(f"CTest checker command is missing a value for {flag}")
                value = command[index]
            if not value:
                reject(f"CTest checker command has an empty value for {flag}")
            parsed_values[flag] = value
        else:
            reject(f"CTest checker command contains an unapproved option: {flag}")
        index += 1
    return parsed_values, parsed_booleans


def _path_option_is(values: dict[str, str], flag: str, path: Path) -> bool:
    return flag in values and _same_path(values[flag], path)


def _expected_timeout(name: str, sanitizer_enabled: bool) -> int:
    base = (180 if name in GROUPS.values() else 60 if name == "workflow_policy_coverage"
            else 30 if name == "workflow_policy_coverage_controls" else 60)
    return base * (3 if sanitizer_enabled else 1)


def validate_cmake_registration(ci_lanes: str) -> None:
    calls = re.findall(r"(?im)^\s*gbb_add_ci_lane_test\s*\(\s*([A-Za-z0-9_]+)", ci_lanes)
    policy_calls = [name for name in calls if name.startswith("workflow_policy_")]
    if sorted(policy_calls) != sorted(POLICY_TEST_NAMES):
        reject("tests/cmake/ci-lanes.cmake policy declarations are missing, duplicated, or unexpected")


def validate_registration(root: Path, expected_tests: list[str], ctest_tests: list[dict], ci_lanes: str,
                          *, build_dir: Path, candidate: str, sanitizer_enabled: bool,
                          cmake_executable: str, python_executable: str) -> None:
    if len(expected_tests) != len(set(expected_tests)):
        reject("tests/expected-tests.txt contains duplicate test names")
    inventory = set(expected_tests)
    if not POLICY_TEST_NAMES <= inventory:
        reject("tests/expected-tests.txt is missing a workflow-policy group, coverage test, or production check")
    if any(name.startswith("workflow_policy_") and name not in POLICY_TEST_NAMES for name in inventory):
        reject("tests/expected-tests.txt contains an unexpected workflow-policy registration")

    actual_by_name: dict[str, list[dict]] = {}
    for test in ctest_tests:
        name = test.get("name")
        if isinstance(name, str):
            actual_by_name.setdefault(name, []).append(test)
    actual_policy_names = {name for name in actual_by_name if name.startswith("workflow_policy_")}
    if actual_policy_names != POLICY_TEST_NAMES:
        reject("configured CTest workflow-policy names contain an omission or unexpected group")
    for name in POLICY_TEST_NAMES:
        if len(actual_by_name.get(name, [])) != 1:
            reject(f"CTest must register {name} exactly once")

    completion_paths: set[str] = set()
    for name in sorted(POLICY_TEST_NAMES):
        test = actual_by_name[name][0]
        properties = _test_properties(test)
        if set(properties) != {"TIMEOUT", "WORKING_DIRECTORY"}:
            reject(f"CTest {name} has an unexpected property that can change execution or qualification")
        timeout = properties.get("TIMEOUT")
        expected_timeout = _expected_timeout(name, sanitizer_enabled)
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout != expected_timeout:
            reject(f"CTest {name} must retain its {expected_timeout}-second configured timeout")
        if not _same_path(str(properties.get("WORKING_DIRECTORY", "")), build_dir / "tests"):
            reject(f"CTest {name} has an unexpected working directory")

        definitions = _parse_wrapper_definitions(test, root, cmake_executable)
        cli = definitions.get("GBB_CMD", "").split(";")
        if name in GROUPS.values():
            group = next(group for group, test_name in GROUPS.items() if test_name == name)
            completion_path = build_dir / f"workflow-policy-{GROUP_COMPLETION_FILES[group]}.json"
            cli_values, cli_booleans = _parse_python_cli(
                cli, python_executable, root / POLICY_PATH,
                {"--group", "--root", "--completed-file"}, {"--self-test"},
            )
            if cli_booleans != {"--self-test"} or set(cli_values) != {"--group", "--root", "--completed-file"}:
                reject(f"CTest {name} does not invoke exactly one selected policy self-test group")
            if (cli_values["--group"] != group or not _path_option_is(cli_values, "--root", root)
                    or not _path_option_is(cli_values, "--completed-file", completion_path)):
                reject(f"CTest {name} has a wrong group, root, or completion-file argument")
            completion_key = os.path.normcase(str(completion_path.resolve()))
            if completion_key in completion_paths:
                reject(f"CTest {name} shares a completion-file destination with another group")
            completion_paths.add(completion_key)
            expected_definitions = {
                "GBB_CMD": definitions["GBB_CMD"],
                "GBB_EXPECT_CODE": "0",
                "GBB_EXPECT_REGEX": f"PASS: workflow policy group {group} controls=[0-9]+ ids_sha256=[0-9a-f]+",
                "GBB_EXPECT_FILE": str(completion_path),
                "GBB_EXPECT_FILE_FRESH": "TRUE",
            }
            if not _path_option_is(definitions, "GBB_EXPECT_FILE", completion_path):
                reject(f"CTest {name} does not require its group-specific fresh completion file")
        elif name == "workflow_policy_coverage":
            cli_values, cli_booleans = _parse_python_cli(
                cli, python_executable, root / "tests/scripts/verify-workflow-policy-coverage.py",
                {"--root", "--build-dir", "--rev"}, {"--check"},
            )
            if (cli_booleans != {"--check"} or set(cli_values) != {"--root", "--build-dir", "--rev"}
                    or not _path_option_is(cli_values, "--root", root)
                    or not _path_option_is(cli_values, "--build-dir", build_dir)
                    or cli_values["--rev"] != candidate):
                reject("workflow_policy_coverage does not check the configured build at the exact candidate commit")
            expected_definitions = {
                "GBB_CMD": definitions["GBB_CMD"],
                "GBB_EXPECT_CODE": "0",
                "GBB_EXPECT_REGEX": "PASS: workflow policy coverage controls=[0-9]+ groups=6 platform=(posix|windows)",
            }
        elif name == "workflow_policy_coverage_controls":
            cli_values, cli_booleans = _parse_python_cli(
                cli, python_executable, root / "tests/scripts/verify-workflow-policy-coverage.py",
                {"--root", "--rev"}, {"--self-test"},
            )
            if (cli_booleans != {"--self-test"} or set(cli_values) != {"--root", "--rev"}
                    or not _path_option_is(cli_values, "--root", root) or cli_values["--rev"] != candidate):
                reject("workflow_policy_coverage_controls does not run self-tests at the exact candidate commit")
            expected_definitions = {
                "GBB_CMD": definitions["GBB_CMD"],
                "GBB_EXPECT_CODE": "0",
                "GBB_EXPECT_REGEX": "PASS: workflow policy coverage self-test controls=62",
            }
        else:
            cli_values, cli_booleans = _parse_python_cli(
                cli, python_executable, root / POLICY_PATH, {"--root"}, {"--check"},
            )
            if cli_booleans != {"--check"} or set(cli_values) != {"--root"} or not _path_option_is(cli_values, "--root", root):
                reject("workflow_policy_check must invoke the production --check command at the source root")
            expected_definitions = {
                "GBB_CMD": definitions["GBB_CMD"],
                "GBB_EXPECT_CODE": "0",
                "GBB_EXPECT_REGEX": "PASS: workflow privilege and trust wiring residual_write_jobs=[0-9]+",
            }
        if definitions != expected_definitions:
            reject(f"CTest {name} wrapper definitions differ from the exact exit-plus-marker contract")

    validate_cmake_registration(ci_lanes)


def _self_test(root: Path, revision: str) -> int:
    candidate = resolve_commit(root, revision)
    source = baseline_source(root)
    expected = manifest_for(source)
    candidate_source = git_text(root, candidate, POLICY_PATH)
    build_dir = root / "build/phase19-policy-coverage-fixture"
    cmake_executable = shutil.which("cmake") or "cmake"
    python_executable = sys.executable
    expected_tests = sorted(POLICY_TEST_NAMES)
    ci_lanes = "\n".join(f"gbb_add_ci_lane_test({name} 0 marker 60 \"\")" for name in expected_tests)
    controls = 0

    def rejected(label: str, operation) -> None:
        nonlocal controls
        try:
            operation()
        except CoverageError:
            controls += 1
        else:
            reject(f"negative control {label} was accepted")

    def test_entry(name: str, argv: list[str], marker: str, timeout: int,
                   completion: Path | None = None) -> dict:
        definitions = [
            ("GBB_CMD", ";".join(argv)),
            ("GBB_EXPECT_CODE", "0"),
            ("GBB_EXPECT_REGEX", marker),
        ]
        if completion is not None:
            definitions.extend((("GBB_EXPECT_FILE", str(completion)), ("GBB_EXPECT_FILE_FRESH", "TRUE")))
        command = [cmake_executable, *(f"-D{name}={value}" for name, value in definitions),
                   "-P", str(root / "tests/expect_exit.cmake")]
        return {
            "name": name,
            "command": command,
            "properties": [
                {"name": "TIMEOUT", "value": timeout},
                {"name": "WORKING_DIRECTORY", "value": str(build_dir / "tests")},
            ],
        }

    for name, mutate in (
        ("omission", lambda value: value["controls"].pop()),
        ("duplicate", lambda value: value["controls"].append(copy.deepcopy(value["controls"][0]))),
    ):
        mutant = copy.deepcopy(expected)
        mutate(mutant)
        rejected(name, lambda mutant=mutant: validate_manifest(mutant, expected))
    for name, field, value in (("wrong-group", "group", "helpers"),
                               ("wrong-platform", "platforms", ["windows"])):
        mutant = copy.deepcopy(expected)
        target = next(row for row in mutant["controls"] if row["group"] != "helpers")
        target[field] = value
        rejected(name, lambda mutant=mutant: validate_manifest(mutant, expected))

    tests: list[dict] = []
    for group, name in GROUPS.items():
        completion = build_dir / f"workflow-policy-{GROUP_COMPLETION_FILES[group]}.json"
        marker = f"PASS: workflow policy group {group} controls=[0-9]+ ids_sha256=[0-9a-f]+"
        tests.append(test_entry(name, [python_executable, "-I", str(root / POLICY_PATH), "--self-test",
                                       "--group", group, "--root", str(root), "--completed-file", str(completion)],
                                marker, 180, completion))
    coverage_script = root / "tests/scripts/verify-workflow-policy-coverage.py"
    tests.extend((
        test_entry("workflow_policy_coverage",
                   [python_executable, "-I", str(coverage_script), "--check", "--root", str(root),
                    "--build-dir", str(build_dir), "--rev", candidate],
                   "PASS: workflow policy coverage controls=[0-9]+ groups=6 platform=(posix|windows)", 60),
        test_entry("workflow_policy_coverage_controls",
                   [python_executable, "-I", str(coverage_script), "--self-test", "--root", str(root), "--rev", candidate],
                   "PASS: workflow policy coverage self-test controls=62", 30),
        test_entry("workflow_policy_check",
                   [python_executable, "-I", str(root / POLICY_PATH), "--check", "--root", str(root)],
                   "PASS: workflow privilege and trust wiring residual_write_jobs=[0-9]+", 60),
    ))

    def validate(tests_to_check: list[dict] = tests, names: list[str] = expected_tests, *, sanitizer: bool = False,
                 lanes: str = ci_lanes) -> None:
        validate_registration(root, names, tests_to_check, lanes, build_dir=build_dir, candidate=candidate,
                              sanitizer_enabled=sanitizer, cmake_executable=cmake_executable,
                              python_executable=python_executable)

    validate()
    scaled = copy.deepcopy(tests)
    for test in scaled:
        for prop in test["properties"]:
            if prop["name"] == "TIMEOUT":
                prop["value"] *= 3
    validate(scaled, sanitizer=True)

    reordered = copy.deepcopy(tests)
    for test in reordered:
        command = test["command"]
        script_index = command.index("-P")
        command[1:script_index] = reversed(command[1:script_index])
        cmd_index = next(index for index, arg in enumerate(command) if arg.startswith("-DGBB_CMD="))
        argv = command[cmd_index].partition("=")[2].split(";")
        units: list[list[str]] = []
        index = 3
        while index < len(argv):
            if argv[index] in {"--check", "--self-test"}:
                units.append([argv[index]])
                index += 1
            else:
                units.append(argv[index:index + 2])
                index += 2
        command[cmd_index] = "-DGBB_CMD=" + ";".join(argv[:3] + [part for unit in reversed(units) for part in unit])
    validate(reordered)

    # Inventory omissions, stale rows, and duplicate or unexpected CTest registrations.
    rejected("missing expected inventory row", lambda: validate(tests, [name for name in expected_tests if name != GROUPS["ledger"]]))
    rejected("missing configured CTest registration",
             lambda: validate([test for test in tests if test["name"] != GROUPS["ledger"]]))
    rejected("missing CMake declaration",
             lambda: validate_cmake_registration(ci_lanes.replace(
                 f"gbb_add_ci_lane_test({GROUPS['ledger']}", "# removed\ngbb_add_ci_lane_test(omitted_group")))
    rejected("duplicate CTest registration", lambda: validate([*tests, copy.deepcopy(tests[0])]))
    rejected("unexpected CTest group", lambda: validate([*tests, {**copy.deepcopy(tests[0]),
                                                                    "name": "workflow_policy_group_extra"}]))
    rejected("unexpected expected-test group", lambda: validate(tests, [*expected_tests, "workflow_policy_group_extra"]))

    def set_timeout(test_list: list[dict], value: int) -> None:
        target = next(test for test in test_list if test["name"] == GROUPS["ci"])
        next(prop for prop in target["properties"] if prop["name"] == "TIMEOUT")["value"] = value

    mutant = copy.deepcopy(tests)
    set_timeout(mutant, 540)
    rejected("incorrectly scaled native timeout", lambda: validate(mutant))
    mutant = copy.deepcopy(tests)
    set_timeout(mutant, 180)
    rejected("unscaled sanitizer timeout", lambda: validate(mutant, sanitizer=True))

    def named_test(test_list: list[dict], name: str) -> dict:
        return next(test for test in test_list if test["name"] == name)

    def change_cli(test: dict, argv: list[str]) -> None:
        for index, part in enumerate(test["command"]):
            if part.startswith("-DGBB_CMD="):
                test["command"][index] = "-DGBB_CMD=" + ";".join(argv)
                return
        reject("self-test fixture has no GBB_CMD definition")

    def add_definition(test: dict, definition: str) -> None:
        test["command"].insert(test["command"].index("-P"), definition)

    def replace_definition(test: dict, name: str, value: str) -> None:
        for index, part in enumerate(test["command"]):
            if part.startswith(f"-D{name}="):
                test["command"][index] = f"-D{name}={value}"
                return
        reject(f"self-test fixture has no {name} definition")

    def validate_mutated(mutate, *, sanitizer: bool = False) -> None:
        mutant = copy.deepcopy(tests)
        mutate(mutant)
        validate(mutant, sanitizer=sanitizer)

    ci_name = GROUPS["ci"]
    completion = build_dir / "workflow-policy-ci.json"
    ci_argv = [python_executable, "-I", str(root / POLICY_PATH), "--self-test", "--group", "ci",
               "--root", str(root), "--completed-file", str(completion)]
    helper_marker = "PASS: workflow policy group helpers controls=[0-9]+ ids_sha256=[0-9a-f]+"
    def combined_override(test_list: list[dict]) -> None:
        target = named_test(test_list, ci_name)
        change_cli(target, [*ci_argv, "--group", "helpers"])
        add_definition(target, f"-DGBB_EXPECT_REGEX={helper_marker}")

    rejected("combined extra-group and later marker override", lambda: validate_mutated(combined_override))
    for label, definition in (
        ("typed duplicate command override", "-DGBB_CMD:STRING=echo;PASS"),
        ("typed duplicate exit override", "-DGBB_EXPECT_CODE:STRING=7"),
        ("typed duplicate marker override", "-DGBB_EXPECT_REGEX:STRING=PASS: injected"),
        ("typed duplicate completion override", "-DGBB_EXPECT_FILE:FILEPATH=/tmp/stale.json"),
        ("typed duplicate freshness override", "-DGBB_EXPECT_FILE_FRESH:BOOL=FALSE"),
    ):
        rejected(label, lambda definition=definition: validate_mutated(
            lambda test_list: add_definition(named_test(test_list, ci_name), definition)))
    rejected("single exit override", lambda: validate_mutated(
        lambda test_list: replace_definition(named_test(test_list, ci_name), "GBB_EXPECT_CODE", "7")))
    rejected("single marker override", lambda: validate_mutated(
        lambda test_list: replace_definition(named_test(test_list, ci_name), "GBB_EXPECT_REGEX", "PASS: injected")))
    rejected("single freshness override", lambda: validate_mutated(
        lambda test_list: replace_definition(named_test(test_list, ci_name), "GBB_EXPECT_FILE_FRESH", "FALSE")))
    rejected("single completion override", lambda: validate_mutated(
        lambda test_list: replace_definition(named_test(test_list, ci_name), "GBB_EXPECT_FILE", str(build_dir / "stale.json"))))
    rejected("group wrong script", lambda: validate_mutated(lambda test_list: change_cli(named_test(test_list, ci_name),
        [python_executable, "-I", str(coverage_script), "--self-test", "--group", "ci", "--root", str(root),
         "--completed-file", str(completion)])))
    rejected("Python -c substitution", lambda: validate_mutated(lambda test_list: change_cli(named_test(test_list, ci_name),
        [python_executable, "-I", "-c", "pass()", str(root / POLICY_PATH), "--self-test", "--group", "ci",
         "--root", str(root), "--completed-file", str(completion)])))
    rejected("Python isolation flag moved", lambda: validate_mutated(lambda test_list: change_cli(named_test(test_list, ci_name),
        [python_executable, str(root / POLICY_PATH), "-I", "--self-test", "--group", "ci", "--root", str(root),
         "--completed-file", str(completion)])))
    rejected("wrong policy root", lambda: validate_mutated(lambda test_list: change_cli(named_test(test_list, ci_name),
        [python_executable, "-I", str(root / POLICY_PATH), "--self-test", "--group", "ci", "--root", "/tmp/other",
         "--completed-file", str(completion)])))
    rejected("wrong group value", lambda: validate_mutated(lambda test_list: change_cli(named_test(test_list, ci_name),
        [python_executable, "-I", str(root / POLICY_PATH), "--self-test", "--group", "helpers", "--root", str(root),
         "--completed-file", str(completion)])))
    rejected("duplicate group flag", lambda: validate_mutated(lambda test_list: change_cli(named_test(test_list, ci_name),
        [python_executable, "-I", str(root / POLICY_PATH), "--self-test", "--group", "ci", "--group", "helpers",
         "--root", str(root), "--completed-file", str(completion)])))
    rejected("wrong group completion path", lambda: validate_mutated(lambda test_list: change_cli(named_test(test_list, ci_name),
        [python_executable, "-I", str(root / POLICY_PATH), "--self-test", "--group", "ci", "--root", str(root),
         "--completed-file", str(build_dir / "workflow-policy-helpers.json")])))
    rejected("workflow-policy check echo substitution", lambda: validate_mutated(lambda test_list: change_cli(
        named_test(test_list, "workflow_policy_check"), ["echo", "PASS:"])))
    rejected("wrong exit-plus-marker script", lambda: validate_mutated(lambda test_list:
        named_test(test_list, ci_name)["command"].__setitem__(
            slice(-1, None), [str(root / "tests/scripts/verify-workflow-policy-coverage.py")])))
    rejected("wrong CMake executable", lambda: validate_mutated(lambda test_list:
        named_test(test_list, ci_name)["command"].__setitem__(0, python_executable)))
    rejected("extra ignored CMake argument", lambda: validate_mutated(lambda test_list:
        named_test(test_list, ci_name)["command"].insert(
            named_test(test_list, ci_name)["command"].index("-P"), "--fresh")))

    def change_coverage_cli(test_list: list[dict], name: str, argv: list[str]) -> None:
        change_cli(named_test(test_list, name), argv)

    coverage_script_text = str(coverage_script)
    check_argv = [python_executable, "-I", coverage_script_text, "--check", "--root", str(root),
                  "--build-dir", str(build_dir), "--rev", candidate]
    rejected("stale coverage candidate", lambda: validate_mutated(lambda test_list: change_coverage_cli(
        test_list, "workflow_policy_coverage", [*check_argv[:-1], BASELINE_COMMIT])))
    rejected("duplicate candidate revision", lambda: validate_mutated(lambda test_list: change_coverage_cli(
        test_list, "workflow_policy_coverage", [*check_argv, "--rev", BASELINE_COMMIT])))
    rejected("wrong coverage script", lambda: validate_mutated(lambda test_list: change_coverage_cli(
        test_list, "workflow_policy_coverage", [python_executable, "-I", str(root / POLICY_PATH), *check_argv[3:]])))
    rejected("wrong coverage build directory", lambda: validate_mutated(lambda test_list: change_coverage_cli(
        test_list, "workflow_policy_coverage", [python_executable, "-I", coverage_script_text,
          "--check", "--root", str(root), "--build-dir", "/tmp/other", "--rev", candidate])))
    rejected("coverage mode flag substitution", lambda: validate_mutated(lambda test_list: change_coverage_cli(
        test_list, "workflow_policy_coverage", [python_executable, "-I", coverage_script_text,
          "--self-test", "--root", str(root), "--build-dir", str(build_dir), "--rev", candidate])))
    rejected("coverage-control stale candidate", lambda: validate_mutated(lambda test_list: change_coverage_cli(
        test_list, "workflow_policy_coverage_controls", [python_executable, "-I", coverage_script_text,
          "--self-test", "--root", str(root), "--rev", BASELINE_COMMIT])))
    rejected("coverage marker override", lambda: validate_mutated(lambda test_list: replace_definition(
        named_test(test_list, "workflow_policy_coverage"), "GBB_EXPECT_REGEX", "PASS: injected")))

    reviewed = reviewed_policy_source(root)
    verify_reviewed_policy_identity(candidate_source, reviewed)
    verify_source_identity(root, candidate_source)

    def reject_source_mutant(label: str, mutant: bytes) -> None:
        if mutant == candidate_source:
            reject(f"{label} fixture did not modify the reviewed source")
        try:
            ast.parse(mutant, filename=POLICY_PATH)
        except SyntaxError as error:
            reject(f"{label} fixture is not valid Python: {error}")
        rejected(label, lambda: verify_source_identity(root, mutant))

    changed = candidate_source.replace(b'"PASS: workflow privilege and trust wiring"', b'"PASS: weakened workflow judge"', 1)
    reject_source_mutant("production source mutation", changed)
    changed_selector_default = candidate_source.replace(b'default="all"', b'default="helpers"', 1)
    reject_source_mutant("selector default change", changed_selector_default)
    injected_assignment = candidate_source.replace(
        b"WORKFLOWS = (", b'WORKFLOWS = print("unapproved import-time side effect")\nWORKFLOWS = (', 1)
    reject_source_mutant("module-level assignment side effect", injected_assignment)
    duplicate_function = candidate_source + b"\n\ndef check_all(root):\n    return {}\n"
    reject_source_mutant("duplicate baseline function shadow", duplicate_function)
    decorated_selector = candidate_source.replace(b"def _policy_control_id(", b"@print('unapproved import effect')\ndef _policy_control_id(", 1)
    reject_source_mutant("selector decorator import-time effect", decorated_selector)
    default_effect = candidate_source.replace(
        b"def _policy_control_id(kind: str,", b"def _policy_control_id(kind: str = print('unapproved import effect'),", 1)
    reject_source_mutant("selector default import-time effect", default_effect)

    marker_anchor = b'_mark_policy_control("helper", "window-discovery", "legacy-query")'
    marker_effect = candidate_source.replace(
        marker_anchor,
        b'_mark_policy_control("helper", print("marker side effect") or "window-discovery", "legacy-query")', 1,
    )
    reject_source_mutant("marker argument side effect", marker_effect)
    selector_anchor = b"run_policy_self_test(root, args.group, args.completed_file)"
    selector_effect = candidate_source.replace(
        selector_anchor,
        b'run_policy_self_test(root, print("selector side effect") or args.group, args.completed_file)', 1,
    )
    reject_source_mutant("selector argument side effect", selector_effect)

    runner_doc = b'    """Run the unchanged complete self-test, optionally selecting one frozen mutation family."""\n'
    runner_side_effect = candidate_source.replace(
        runner_doc, runner_doc + b'    print("runner side effect")\n', 1,
    )
    reject_source_mutant("runner body side effect", runner_side_effect)
    runner_global = b"    global _ACTIVE_POLICY_GROUP, _ACTIVE_POLICY_CONTROLS, _COMPLETED_POLICY_CONTROLS\n"
    runner_return = candidate_source.replace(runner_global, runner_global + b"    return\n", 1)
    reject_source_mutant("runner body early return", runner_return)
    runner_call = b"        self_test(root)\n"
    fabricated_runner = candidate_source.replace(
        runner_call,
        b'        if completed_file is not None:\n'
        b'            completed_file.parent.mkdir(parents=True, exist_ok=True)\n'
        b'            completed_file.write_text(json.dumps({"group": group, "control_ids": []}) + "\\n", encoding="utf-8")\n'
        b'        print(f"PASS: workflow policy group {group} controls=0 ids_sha256={\'0\' * 64}")\n'
        b"        return\n"
        + runner_call,
        1,
    )
    reject_source_mutant("fabricated runner completion", fabricated_runner)
    changed_marker = candidate_source.replace(marker_anchor, marker_anchor.replace(b"legacy-query", b"legacy-query-changed"), 1)
    reject_source_mutant("changed marker ID", changed_marker)
    marker_statement = b'        _mark_policy_control("helper", "window-discovery", "legacy-query")\n'
    duplicate_marker = candidate_source.replace(marker_statement, marker_statement * 2, 1)
    reject_source_mutant("duplicated marker call", duplicate_marker)
    changed_selector = candidate_source.replace(
        selector_anchor, b"run_policy_self_test(root, None, args.completed_file)", 1,
    )
    reject_source_mutant("changed selector invocation", changed_selector)
    duplicated_selector = candidate_source.replace(
        selector_anchor, selector_anchor + b"\n            " + selector_anchor, 1,
    )
    reject_source_mutant("duplicated selector invocation", duplicated_selector)
    rejected("missing reviewed source reference", lambda: verify_reviewed_policy_identity(candidate_source, None))
    rejected("wrong reviewed source digest", lambda: verify_reviewed_policy_identity(candidate_source, reviewed + b"\n"))
    rejected("wrong candidate reviewed identity", lambda: verify_reviewed_policy_identity(candidate_source + b"\n", reviewed))

    candidate_namespace = {"__name__": "candidate_workflow_policy", "__file__": str(root / POLICY_PATH)}
    exec(compile(candidate_source, POLICY_PATH, "exec"), candidate_namespace)
    recorder = candidate_namespace.get("_record_policy_completion")
    if not callable(recorder):
        reject("candidate checker is missing its runtime completion-ID validator")
    sample = {"group": "ci", "platforms": list(ALL_PLATFORMS)}
    control_id = "mutation-test-id"
    completed: set[str] = set()
    recorder(completed, control_id, sample, "ci", "posix")
    if completed != {control_id}:
        reject("runtime completion recorder did not retain a valid control ID")
    runtime_cases = (
        ("unknown-ID", "unknown control ID", "ci", "posix", None, set()),
        ("duplicate-ID", "more than once", "ci", "posix", sample, {control_id}),
        ("wrong-group", "out-of-group", "release_jobs", "posix", sample, set()),
        ("wrong-platform", "wrong-platform", "ci", "windows", {"group": "ci", "platforms": ["posix"]}, set()),
    )
    for name, expected_text, group, platform, control, prior in runtime_cases:
        try:
            recorder(set(prior), control_id if name != "unknown-ID" else "unknown-id", control, group, platform)
        except SystemExit as error:
            if expected_text not in str(error):
                reject(f"runtime completion negative {name} refused for the wrong reason: {error}")
            controls += 1
        else:
            reject(f"runtime completion negative {name} was accepted")
    if controls != 62:
        reject(f"workflow-policy coverage self-test has an unexpected negative-control count: {controls}")
    return controls


def _check(root: Path, build_dir: Path, revision: str) -> None:
    candidate = resolve_commit(root, revision)
    source = baseline_source(root)
    expected = manifest_for(source)
    try:
        manifest = json.loads(git_text(root, candidate, "tests/data/workflow-policy-controls.json").decode("utf-8"))
    except (OSError, ValueError, UnicodeDecodeError) as error:
        reject(f"workflow-policy control registry is unreadable: {error}")
    validate_manifest(manifest, expected)
    verify_source_identity(root, git_text(root, candidate, POLICY_PATH))
    expected_tests = git_text(root, candidate, "tests/expected-tests.txt").decode("utf-8").splitlines()
    result = subprocess.run(["ctest", "--test-dir", str(build_dir), "--show-only=json-v1"], cwd=root,
                            capture_output=True, text=True, check=False, timeout=30)
    if result.returncode != 0:
        reject(f"configured CTest inventory is unavailable: {result.stderr.strip()}")
    try:
        ctest_tests = json.loads(result.stdout)["tests"]
    except (ValueError, KeyError, TypeError) as error:
        reject(f"configured CTest inventory is malformed: {error}")
    ci_lanes = git_text(root, candidate, "tests/cmake/ci-lanes.cmake").decode("utf-8")
    cache = _cmake_cache(build_dir)
    cmake_executable = cache.get("CMAKE_COMMAND")
    python_executable = cache.get("_Python3_EXECUTABLE", cache.get("Python3_EXECUTABLE"))
    if not cmake_executable or not python_executable:
        reject("configured CMake/Python executable paths are missing from CMakeCache.txt")
    sanitizer_enabled = _truthy_cmake(cache.get("GABBABOY_ENABLE_SANITIZERS", "OFF"))
    validate_registration(root, expected_tests, ctest_tests, ci_lanes, build_dir=build_dir,
                          candidate=candidate, sanitizer_enabled=sanitizer_enabled,
                          cmake_executable=cmake_executable, python_executable=python_executable)
    platform = "windows" if os.name == "nt" else "posix"
    controls = sum(1 for row in manifest["controls"] if platform in row["platforms"])
    print(f"PASS: workflow policy coverage controls={controls} groups={len(GROUPS)} platform={platform}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="check the frozen IDs and configured CTest listing")
    mode.add_argument("--self-test", action="store_true", help="prove omission, duplication and registration refusals")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--build-dir", type=Path, default=None)
    parser.add_argument("--rev", default="HEAD", help="immutable candidate commit whose source and registrations are checked")
    args = parser.parse_args()
    try:
        if args.self_test:
            controls = _self_test(args.root.resolve(), args.rev)
            print(f"PASS: workflow policy coverage self-test controls={controls}")
            return 0
        if args.build_dir is None:
            reject("--check requires --build-dir for the configured CTest listing")
        _check(args.root.resolve(), args.build_dir.resolve(), args.rev)
        return 0
    except (CoverageError, OSError, ValueError, KeyError, TypeError) as error:
        print(f"REJECT workflow-policy-coverage: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
