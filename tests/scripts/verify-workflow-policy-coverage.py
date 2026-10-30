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
import subprocess
import sys
from pathlib import Path

if not __debug__ or sys.flags.optimize:
    raise SystemExit("verify-workflow-policy-coverage must not run with python -O")

ROOT = Path(__file__).resolve().parents[2]
BASELINE_COMMIT = "70d3e42225c14e636876aad6697672ec08d861b3"
POLICY_PATH = ".github/scripts/verify-workflow-policy.py"
POLICY_SHA256 = "c5aa1d60a2391e7126e714bcf101292dc86c75ddd1cd6167aea55cdb8b629083"
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
ALL_PLATFORMS = ("posix", "windows")
POSIX_ONLY = ("posix",)


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
    """Remove only verified coverage markers and group-only guards before baseline AST comparison."""
    def visit_FunctionDef(self, node: ast.FunctionDef):
        node = self.generic_visit(node)
        if node.name == "self_test":
            node.body = [stmt for stmt in node.body if not (
                isinstance(stmt, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "run_helpers"
                                                     for target in stmt.targets))]
        return node

    def visit_Expr(self, node: ast.Expr):
        value = node.value
        if isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id == "_mark_policy_control":
            return None
        if isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute) and value.func.attr == "add_argument":
            if value.args and isinstance(value.args[0], ast.Constant) and value.args[0].value in ("--group", "--completed-file"):
                return None
        return self.generic_visit(node)

    def visit_If(self, node: ast.If):
        node = self.generic_visit(node)
        if isinstance(node.test, ast.Name) and node.test.id == "run_helpers":
            return node.body
        return node

    def visit_Call(self, node: ast.Call):
        node = self.generic_visit(node)
        if isinstance(node.func, ast.Name) and node.func.id == "run_policy_self_test":
            return ast.copy_location(ast.Call(func=ast.Name(id="self_test", ctx=ast.Load()),
                                              args=[node.args[0]], keywords=[]), node)
        return node


def verify_source_identity(baseline: bytes, current: bytes) -> None:
    try:
        baseline_tree = ast.parse(baseline, filename=POLICY_PATH)
        current_tree = ast.parse(current, filename=POLICY_PATH)
    except SyntaxError as error:
        reject(f"workflow-policy source does not parse: {error}")
    baseline_functions = {node.name: node for node in baseline_tree.body
                          if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    current_functions = {node.name: node for node in current_tree.body
                         if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    added_functions = set(current_functions) - set(baseline_functions)
    if added_functions != {"_policy_control_id", "_record_policy_completion", "_mark_policy_control", "run_policy_self_test"}:
        reject(f"workflow-policy selector functions differ from the approved set: {sorted(added_functions)}")
    for name, baseline_node in baseline_functions.items():
        if name not in current_functions:
            reject(f"baseline checker function was removed: {name}")
        if name in ("self_test", "main"):
            continue
        normalized = _StripMarkersAndSelectors().visit(copy.deepcopy(current_functions[name]))
        if ast.dump(normalized, include_attributes=False) != ast.dump(baseline_node, include_attributes=False):
            reject(f"baseline checker function or assertion semantics changed: {name}")

    current_self_test = _StripMarkersAndSelectors().visit(copy.deepcopy(current_functions["self_test"]))
    if ast.dump(current_self_test, include_attributes=False) != ast.dump(baseline_functions["self_test"], include_attributes=False):
        reject("self-test assertion/oracle statements changed outside verified group guards and completion markers")
    current_main = _StripMarkersAndSelectors().visit(copy.deepcopy(current_functions["main"]))
    if ast.dump(current_main, include_attributes=False) != ast.dump(baseline_functions["main"], include_attributes=False):
        reject("main CLI production path changed outside the self-test selector extension")

    baseline_imports = [node for node in baseline_tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
    current_imports = [node for node in current_tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
    if any(ast.dump(node, include_attributes=False) not in {ast.dump(item, include_attributes=False) for item in current_imports}
           for node in baseline_imports):
        reject("baseline module imports changed")
    baseline_import_dumps = [ast.dump(node, include_attributes=False) for node in baseline_imports]
    added_imports = []
    for node in current_imports:
        dumped = ast.dump(node, include_attributes=False)
        if dumped in baseline_import_dumps:
            baseline_import_dumps.remove(dumped)
        else:
            added_imports.append(dumped)
    allowed_import = ast.dump(ast.parse("import hashlib").body[0], include_attributes=False)
    if added_imports != [allowed_import]:
        reject("workflow-policy added imports beyond the stable-ID hash dependency")
    # Top-level baseline constants/classes and module guard are exact; selector globals are the only new assignments.
    base_nonfunctions = [node for node in baseline_tree.body if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Import, ast.ImportFrom))]
    current_nonfunctions = [node for node in current_tree.body if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Import, ast.ImportFrom))]
    base_by_name = {}
    current_by_name = {}
    for node in base_nonfunctions:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            names = [item.id for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
                     for item in ast.walk(target) if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Store)]
            for name in names:
                base_by_name[name] = node
    for node in current_nonfunctions:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            names = [item.id for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
                     for item in ast.walk(target) if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Store)]
            for name in names:
                current_by_name[name] = node
    for name, node in base_by_name.items():
        if name not in current_by_name or ast.dump(node, include_attributes=False) != ast.dump(current_by_name[name], include_attributes=False):
            reject(f"baseline production constant changed: {name}")
    added_assignments = set(current_by_name) - set(base_by_name)
    allowed_assignments = {"_POLICY_PARTITION_GROUPS", "_ACTIVE_POLICY_GROUP", "_ACTIVE_POLICY_CONTROLS",
                           "_COMPLETED_POLICY_CONTROLS"}
    if added_assignments != allowed_assignments:
        reject(f"workflow-policy selector constants differ from the approved set: {sorted(added_assignments)}")
    expected_assignments = ast.parse(
        "_POLICY_PARTITION_GROUPS = ('ci', 'release_jobs', 'release_support', 'rehearsal', 'ledger', 'helpers')\n"
        "_ACTIVE_POLICY_GROUP: str | None = None\n"
        "_ACTIVE_POLICY_CONTROLS: dict[str, dict] = {}\n"
        "_COMPLETED_POLICY_CONTROLS: set[str] = set()\n"
    ).body
    expected_assignment_dumps = {ast.dump(node, include_attributes=False) for node in expected_assignments}
    actual_assignment_dumps = {ast.dump(current_by_name[name], include_attributes=False) for name in allowed_assignments}
    if actual_assignment_dumps != expected_assignment_dumps:
        reject("workflow-policy selector constants changed")
    base_classes = [node for node in base_nonfunctions if isinstance(node, ast.ClassDef)]
    current_classes = [node for node in current_nonfunctions if isinstance(node, ast.ClassDef)]
    if [ast.dump(node, include_attributes=False) for node in base_classes] != [ast.dump(node, include_attributes=False) for node in current_classes]:
        reject("baseline production classes changed")
    base_side_effects = [node for node in base_nonfunctions
                         if not isinstance(node, (ast.Assign, ast.AnnAssign, ast.ClassDef))]
    current_side_effects = [node for node in current_nonfunctions
                            if not isinstance(node, (ast.Assign, ast.AnnAssign, ast.ClassDef))]
    if [ast.dump(node, include_attributes=False) for node in base_side_effects] != [ast.dump(node, include_attributes=False) for node in current_side_effects]:
        reject("baseline module-level control flow or side effects changed")


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
        if isinstance(item, dict) and isinstance(item.get("name"), str):
            result[item["name"]] = item.get("value")
    return result


def _wrapper_command(test: dict) -> tuple[list[str], dict[str, object]]:
    command = [str(value) for value in test.get("command", [])]
    properties = _test_properties(test)
    cmd = next((item.partition("=")[2] for item in command if item.startswith("-DGBB_CMD=")), "")
    return cmd.split(";") if cmd else [], properties


def _has_argument(command: list[str], prefix: str, expected: str | None = None) -> bool:
    for part in command:
        if part.startswith(prefix):
            return expected is None or part.partition("=")[2] == expected
    return False


def validate_cmake_registration(ci_lanes: str) -> None:
    registered = re.findall(r"gbb_add_ci_lane_test\((workflow_policy_group_[a-z_]+)\b", ci_lanes)
    if sorted(registered) != sorted(GROUPS.values()):
        reject("tests/cmake/ci-lanes.cmake group declarations do not match the immutable registry")
    expected_controls = ["workflow_policy_coverage", "workflow_policy_coverage_controls"]
    found_controls = re.findall(r"gbb_add_ci_lane_test\((workflow_policy_coverage(?:_controls)?)\b", ci_lanes)
    if sorted(found_controls) != sorted(expected_controls):
        reject("tests/cmake/ci-lanes.cmake coverage controls do not match the immutable registration contract")
    if re.search(r"gbb_add_ci_lane_test\(workflow_policy_controls\b", ci_lanes):
        reject("tests/cmake/ci-lanes.cmake still registers the stale aggregate policy test")


def validate_registration(root: Path, expected_tests: list[str], ctest_tests: list[dict],
                          ci_lanes: str | None = None) -> None:
    if len(expected_tests) != len(set(expected_tests)):
        reject("tests/expected-tests.txt contains duplicate test names")
    inventory = set(expected_tests)
    if not EXPECTED_TEST_NAMES <= inventory:
        reject("tests/expected-tests.txt is missing a workflow-policy group or coverage test")
    if "workflow_policy_controls" in inventory:
        reject("legacy aggregate workflow_policy_controls registration is stale")

    actual_by_name: dict[str, list[dict]] = {}
    for test in ctest_tests:
        name = test.get("name")
        if isinstance(name, str):
            actual_by_name.setdefault(name, []).append(test)
    for name in EXPECTED_TEST_NAMES | {"workflow_policy_check"}:
        if len(actual_by_name.get(name, [])) != 1:
            reject(f"CTest must register {name} exactly once")
    if "workflow_policy_controls" in actual_by_name:
        reject("CTest still registers the stale aggregate workflow_policy_controls test")
    completion_paths: set[str] = set()
    for name in EXPECTED_TEST_NAMES:
        test = actual_by_name[name][0]
        command, properties = _wrapper_command(test)
        raw_command = [str(value) for value in test.get("command", [])]
        timeout = properties.get("TIMEOUT")
        if ("-P" not in raw_command or not any(part.replace("\\", "/").endswith("tests/expect_exit.cmake")
                                              for part in raw_command)
                or not _has_argument(raw_command, "-DGBB_EXPECT_CODE=", "0")):
            reject(f"CTest {name} lost the exact exit-plus-marker wrapper")
        if name in GROUPS.values():
            group = next(group for group, test_name in GROUPS.items() if test_name == name)
            if str(timeout) not in ("180", "180.0"):
                reject(f"CTest {name} must retain its 180-second timeout")
            if ("--self-test" not in command or "--group" not in command or group not in command
                    or "--completed-file" not in command or not any(POLICY_PATH in part for part in command)):
                reject(f"CTest {name} does not invoke its exact policy group through the production wrapper")
            completed_index = command.index("--completed-file")
            expected_completion_name = f"workflow-policy-{GROUP_COMPLETION_FILES[group]}.json"
            if completed_index + 1 >= len(command) or Path(command[completed_index + 1]).name != expected_completion_name:
                reject(f"CTest {name} does not write its own group-specific completion file")
            completion_arg = next((part.partition("=")[2] for part in raw_command
                                   if part.startswith("-DGBB_EXPECT_FILE=")), "")
            if (not completion_arg or Path(completion_arg).name != expected_completion_name
                    or completion_arg in completion_paths):
                reject(f"CTest {name} has a missing or shared completion-file destination")
            completion_paths.add(completion_arg)
            if (not _has_argument(raw_command, "-DGBB_EXPECT_REGEX=", f"PASS: workflow policy group {group} controls=[0-9]+ ids_sha256=[0-9a-f]+")
                    or not _has_argument(raw_command, "-DGBB_EXPECT_FILE_FRESH=", "TRUE")
                    or not _has_argument(raw_command, "-DGBB_EXPECT_FILE=")):
                reject(f"CTest {name} does not require a fresh completion file and unique success marker")
        elif name == "workflow_policy_coverage":
            if (str(timeout) not in ("60", "60.0") or not any(Path(part).name == Path(__file__).name for part in command) or "--check" not in command
                    or "--rev" not in command or not any(re.fullmatch(r"[0-9a-f]{40,64}", part) for part in command)
                    or not _has_argument(raw_command, "-DGBB_EXPECT_REGEX=", "PASS: workflow policy coverage controls=[0-9]+ groups=6 platform=(posix|windows)")):
                reject("workflow_policy_coverage is not the immutable registry/CTest checker")
        elif name == "workflow_policy_coverage_controls":
            if (str(timeout) not in ("30", "30.0") or not any(Path(part).name == Path(__file__).name for part in command) or "--self-test" not in command
                    or "--rev" not in command or not any(re.fullmatch(r"[0-9a-f]{40,64}", part) for part in command)
                    or not _has_argument(raw_command, "-DGBB_EXPECT_REGEX=", "PASS: workflow policy coverage self-test controls=12")):
                reject("workflow_policy_coverage_controls is not the registry negative-control suite")
        elif name == "workflow_policy_check":
            if (not any(POLICY_PATH in part for part in command) or "--check" not in command
                    or str(timeout) not in ("60", "60.0")):
                reject("workflow_policy_check must remain the separate 60-second production checker invocation")

    if ci_lanes is None:
        ci_lanes = (root / "tests/cmake/ci-lanes.cmake").read_text(encoding="utf-8")
    validate_cmake_registration(ci_lanes)


def _self_test(root: Path, revision: str) -> int:
    candidate = resolve_commit(root, revision)
    source = baseline_source(root)
    expected = manifest_for(source)
    candidate_source = git_text(root, candidate, POLICY_PATH)
    ci_lanes = "\n".join(
        [f"gbb_add_ci_lane_test({name} 0 marker 180 \"\")" for name in GROUPS.values()]
        + ["gbb_add_ci_lane_test(workflow_policy_coverage 0 marker 60 \"\")",
           "gbb_add_ci_lane_test(workflow_policy_coverage_controls 0 marker 30 \"\")"]
    )
    manifest = copy.deepcopy(expected)
    validate_manifest(manifest, expected)

    for name, mutate, reason in (
        ("omission", lambda value: value["controls"].pop(), "baseline control IDs"),
        ("duplicate", lambda value: value["controls"].append(copy.deepcopy(value["controls"][0])), "duplicate"),
    ):
        mutant = copy.deepcopy(manifest)
        mutate(mutant)
        try:
            validate_manifest(mutant, expected)
        except CoverageError as error:
            if reason not in str(error):
                reject(f"negative control {name} refused for the wrong reason: {error}")
        else:
            reject(f"negative control {name} was accepted")

    for name, field, value in (("wrong-group", "group", "helpers"), ("wrong-platform", "platforms", ["windows"])):
        mutant = copy.deepcopy(manifest)
        target = next(row for row in mutant["controls"] if row["group"] != "helpers")
        target[field] = value
        try:
            validate_manifest(mutant, expected)
        except CoverageError as error:
            if "group/platform/semantics" not in str(error):
                reject(f"negative control {name} refused for the wrong reason: {error}")
        else:
            reject(f"negative control {name} was accepted")

    listed = sorted(EXPECTED_TEST_NAMES | {"workflow_policy_check"})
    ctest = []
    for group, name in GROUPS.items():
        marker = f"PASS: workflow policy group {group} controls=[0-9]+ ids_sha256=[0-9a-f]+"
        completed = f"/tmp/workflow-policy-{GROUP_COMPLETION_FILES[group]}.json"
        command = ["cmake", f"-DGBB_CMD=python;-I;{POLICY_PATH};--self-test;--group;{group};--completed-file;{completed}",
                   "-DGBB_EXPECT_CODE=0", f"-DGBB_EXPECT_REGEX={marker}", f"-DGBB_EXPECT_FILE={completed}",
                   "-DGBB_EXPECT_FILE_FRESH=TRUE", "-P", "tests/expect_exit.cmake"]
        ctest.append({"name": name, "command": command, "properties": [{"name": "TIMEOUT", "value": "180"}]})
    ctest.extend([
        {"name": "workflow_policy_coverage", "command": ["cmake", "-DGBB_CMD=python;-I;tests/scripts/verify-workflow-policy-coverage.py;--check;--rev;" + candidate,
                                                                 "-DGBB_EXPECT_CODE=0", "-DGBB_EXPECT_REGEX=PASS: workflow policy coverage controls=[0-9]+ groups=6 platform=(posix|windows)", "-P", "tests/expect_exit.cmake"],
         "properties": [{"name": "TIMEOUT", "value": "60"}]},
        {"name": "workflow_policy_coverage_controls", "command": ["cmake", "-DGBB_CMD=python;-I;tests/scripts/verify-workflow-policy-coverage.py;--self-test;--rev;" + candidate,
                                                                          "-DGBB_EXPECT_CODE=0", "-DGBB_EXPECT_REGEX=PASS: workflow policy coverage self-test controls=12", "-P", "tests/expect_exit.cmake"],
         "properties": [{"name": "TIMEOUT", "value": "30"}]},
        {"name": "workflow_policy_check", "command": ["cmake", "-DGBB_CMD=python;-I;" + POLICY_PATH + ";--check",
                                                             "-DGBB_EXPECT_CODE=0", "-DGBB_EXPECT_REGEX=PASS:", "-P", "tests/expect_exit.cmake"],
         "properties": [{"name": "TIMEOUT", "value": "60"}]},
    ])
    validate_registration(root, listed, ctest, ci_lanes)
    try:
        validate_registration(root, [name for name in listed if name != GROUPS["ledger"]], ctest, ci_lanes)
    except CoverageError:
        pass
    else:
        reject("negative control missing CTest inventory registration was accepted")
    try:
        validate_registration(root, listed, [test for test in ctest if test["name"] != GROUPS["ledger"]], ci_lanes)
    except CoverageError:
        pass
    else:
        reject("negative control missing configured CTest registration was accepted")
    try:
        validate_cmake_registration(ci_lanes.replace(f"gbb_add_ci_lane_test({GROUPS['ledger']}", "# removed registration\ngbb_add_ci_lane_test(omitted_group"))
    except CoverageError:
        pass
    else:
        reject("negative control missing CMake group declaration was accepted")

    current = candidate_source
    verify_source_identity(source, current)
    changed = current.replace(b'"PASS: workflow privilege and trust wiring"', b'"PASS: weakened workflow judge"', 1)
    try:
        verify_source_identity(source, changed)
    except CoverageError:
        pass
    else:
        reject("negative control changed production function source was accepted")

    namespace = {"__name__": "candidate_workflow_policy", "__file__": str(root / POLICY_PATH)}
    exec(compile(candidate_source, POLICY_PATH, "exec"), namespace)
    recorder = namespace.get("_record_policy_completion")
    if not callable(recorder):
        reject("candidate checker is missing its runtime completion-ID validator")
    sample = {"group": "ci", "platforms": list(ALL_PLATFORMS)}
    control_id = "mutation-test-id"
    completed = set()
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
        else:
            reject(f"runtime completion negative {name} was accepted")
    return 12


def _check(root: Path, build_dir: Path, revision: str) -> None:
    candidate = resolve_commit(root, revision)
    source = baseline_source(root)
    expected = manifest_for(source)
    try:
        manifest = json.loads(git_text(root, candidate, "tests/data/workflow-policy-controls.json").decode("utf-8"))
    except (OSError, ValueError, UnicodeDecodeError) as error:
        reject(f"workflow-policy control registry is unreadable: {error}")
    validate_manifest(manifest, expected)
    verify_source_identity(source, git_text(root, candidate, POLICY_PATH))
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
    validate_registration(root, expected_tests, ctest_tests, ci_lanes)
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
