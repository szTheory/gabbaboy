#!/usr/bin/env python3
"""TUNE-01 phase-path lint: tracked tests, scripts, docs and workflows never read the live phases directory.

Contract (Phase 16 D-06, D-07):

* Every git-tracked text file outside .planning/ is scanned. Binary files (a NUL byte in the first
  8 KiB, the same rule as grep -I) are out of scope, and so is a bare "phases/" that lacks the
  .planning parent; both edges are recorded here because the edge probe left them unclassified.
* Four spellings of the live phases directory are rejected: the literal, joined segments (a quoted
  ".planning" followed by a quoted "phases" through a comma, a division or a plus), backslash
  separators, and the ${PROJECT_SOURCE_DIR}-prefixed form. The accepted spelling names a completed
  milestone archive: .planning/milestones/v<N>.<M>-phases/.
* Exceptions live in one count-pinned allowlist of (file, max hits, reason). A file with more hits than
  its pin fails, and a row whose observed hits fall below its pin is stale and fails, so a retargeted
  reader cannot leave a loose exception behind.
* The success line prints files=N exactly once. The CTest pins a floor on N, and a fixed list of
  must-scan files proves the walk reached the files that matter.

The lint must spell the forbidden forms in its own patterns and fixtures; its own row in the
allowlist is a measured count, not an obfuscation.
"""
from __future__ import annotations

import argparse
import ast
import collections
import hashlib
import io
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import tokenize
from pathlib import Path

if not __debug__ or sys.flags.optimize:
    raise SystemExit("verify-no-phase-paths must not run with python -O")

ROOT = Path(__file__).resolve().parents[2]

# (file, max hits, reason). Counts are measured on the tree with --check --report and pinned exactly.
ALLOWLIST = (
    ("tests/CMakeLists.txt", 1,
     "GBB_LIVE_PHASES_DIR definition, the single allowlisted spelling of the live phases directory (D-07)"),
    ("tests/scripts/verify-phase8-closure-contract.py", 1,
     "PHASE constant: Phase 8 boundary-commit reads, a point-in-time git show path (D-06)"),
    ("tests/scripts/verify-diagnostic-evidence.py", 1,
     "BOUNDARY_PATHS reads one Phase 22 boundary file through the selected immutable commit snapshot"),
    ("tests/scripts/verify-support-ledger.py", 4,
     "duplicated immutable Phase 21/22 evidence-path pins resolved from Git objects, not the live phases tree"),
    ("tests/scripts/verify-review-evidence.py", 10,
     "six fixed report paths plus four disposable committed-fixture paths, never live-tree path traversal"),
    ("tests/data/support-claims-v0.4.json", 4,
     "version-bound Phase 21/22 verification, UAT, and evidence paths read at pinned historical commits, not from the live planning tree"),
    ("docs/support/v0.4.0.md", 4,
     "four generated immutable Phase 21/22 GitHub blob links from pinned evidence revisions, not live-tree reads"),
    ("tests/scripts/state_boundary.py", 1,
     "PHASES_AT_REV constant: Phase 17 boundary facts listed with git inside one named commit (--rev), a point-in-time path (D-06, 17-11)"),
    ("tests/scripts/verify-closeout-dispositions.py", 1,
     "legacy-prefix rewrite for archived records: the prefix the pinned JSON records were written with"),
    ("tests/scripts/verify-closeout-scan.py", 4,
     "temp-fixture layout strings built inside a throwaway repository, not reads of the live tree"),
    ("tests/data/closeout-scan-14-uat-review.md", 6,
     "byte copy of the archived 14-UAT-REVIEW.md seed for verify-closeout-scan.py, D-08"),
    ("tests/scripts/verify-no-phase-paths.py", 17,
     "the lint's spelling patterns, exact historical-path exception and positive/negative self-test fixtures"),
)

HISTORICAL_V04_EVIDENCE_FILE = "tests/data/v04-closeout.json"
HISTORICAL_V04_EVIDENCE_PATH = ".planning/phases/GB-22-composition-and-microtest-evidence/22-CONTEXT.md"
HISTORICAL_V04_EVIDENCE_LOCATIONS = (
    ("sources", 2, "components", 4, "evidence", 0),
    ("sources", 3, "components", 4, "evidence", 0),
)
PLANNING_HYGIENE_FILE = "tests/scripts/verify-planning-hygiene.py"

# Files the walk must reach, or the scan is vacuous.
MUST_SCAN = (
    "tests/CMakeLists.txt",
    "tests/scripts/verify-summary-coverage.py",
    "tests/scripts/verify-closeout-dispositions.py",
    "tests/scripts/verify-diagnostic-evidence.py",
    PLANNING_HYGIENE_FILE,
    HISTORICAL_V04_EVIDENCE_FILE,
)

# One alternation so each spot is counted once. The prefixed form is tried first.
SPELLINGS = re.compile(
    r"(?P<prefixed>\$\{PROJECT_SOURCE_DIR\}/\.planning/phases(?![\w-]))"
    r"|(?P<literal>\.planning/phases(?![\w-]))"
    r"|(?P<backslash>\.planning\\+phases(?![\w-]))"
    r"|(?P<joined>[\"']\.planning/?[\"']\)?\s*(?:,|/|\+)\s*[\"']phases[\"'])"
)
SNIFF_BYTES = 8192
PLANNING_HYGIENE_ARCHIVE_REVISION = "96d502d4733ac54aa8bf7fbfd7813065143771dc"

# Each path-bearing token in verify-planning-hygiene.py has a named owner and role. Module
# constants feed immutable Git snapshots; the historical mapping pins each requirement's
# original report. Function-local literals are either immutable report lookups or fixture paths
# created below self_test's TemporaryDirectory root. This is deliberately independent of the
# number of lexical hits.
PLANNING_HYGIENE_PATH_SITES = (
    ("module:PHASES_AT_REV", "93a487b8daa508ef9898ccfed7504812480990fa9ee370bbdea6abb99ce4eb79", "immutable Git tree path prefix"),
    ("module:V04_GAP_REPORT_PATH", "f4fc136d99098f78e72df6bff5e47f7e01f19022670ca50ab09672c74ac0f166", "current report path read from the selected immutable snapshot"),
    ("module:V04_GAP_SOURCE_PATHS[3]", "4150eae0e6cac689c527ac0268f35ce44411543f9033c7039b6bcfeff83566bb", "bounded source path in the immutable assessment snapshot"),
    ("module:V04_GAP_SOURCE_PATHS[4]", "c89267a4f5020381c92e357908dfbc8dfb42b5becea0d5e3e6bfe5662401bec4", "historical report path in the immutable assessment snapshot"),
    ("module:V04_GAP_SOURCE_PATHS[5]", "993af3738e7fa4bec922be67da7b77c350399b8435fa5af33ba9fd73e8db9d0d", "historical report path in the immutable assessment snapshot"),
    ("module:V04_GAP_SOURCE_PATHS[6]", "468da0dcbeff9d2be30d3dc8125ca12740a0998275f557207bd4af5ea0cf6efa", "historical report path in the immutable assessment snapshot"),
    ("module:V04_GAP_SOURCE_PATHS[7]", "26741716d6c36787261908c578f384564ddd0e25589395dee1d3776adbb795e0", "historical report path in the immutable assessment snapshot"),
    ("module:V04_GAP_SOURCE_PATHS[8]", "66e87758298f2e708026a0c699ea64f804829dbe9e5be0f483ed720ea047d5e1", "historical report path in the immutable assessment snapshot"),
    ("module:V04_GAP_HISTORICAL_REPORTS[GAME-01]", "993af3738e7fa4bec922be67da7b77c350399b8435fa5af33ba9fd73e8db9d0d", "GAME-01 original-owner report lookup in the immutable snapshot"),
    ("module:V04_GAP_HISTORICAL_REPORTS[GAME-02]", "993af3738e7fa4bec922be67da7b77c350399b8435fa5af33ba9fd73e8db9d0d", "GAME-02 original-owner report lookup in the immutable snapshot"),
    ("module:V04_GAP_HISTORICAL_REPORTS[FIXT-01]", "993af3738e7fa4bec922be67da7b77c350399b8435fa5af33ba9fd73e8db9d0d", "FIXT-01 original-owner report lookup in the immutable snapshot"),
    ("module:V04_GAP_HISTORICAL_REPORTS[RIGHTS-01]", "c89267a4f5020381c92e357908dfbc8dfb42b5becea0d5e3e6bfe5662401bec4", "RIGHTS-01 original-owner report lookup in the immutable snapshot"),
    ("module:V04_GAP_HISTORICAL_REPORTS[DIAG-01]", "468da0dcbeff9d2be30d3dc8125ca12740a0998275f557207bd4af5ea0cf6efa", "DIAG-01 original-owner report lookup in the immutable snapshot"),
    ("module:V04_GAP_HISTORICAL_REPORTS[DIAG-02]", "468da0dcbeff9d2be30d3dc8125ca12740a0998275f557207bd4af5ea0cf6efa", "DIAG-02 original-owner report lookup in the immutable snapshot"),
    ("module:V04_GAP_HISTORICAL_REPORTS[FEED-01]", "993af3738e7fa4bec922be67da7b77c350399b8435fa5af33ba9fd73e8db9d0d", "FEED-01 original-owner report lookup in the immutable snapshot"),
    ("module:V04_GAP_HISTORICAL_REPORTS[REL-01]", "26741716d6c36787261908c578f384564ddd0e25589395dee1d3776adbb795e0", "REL-01 original-owner report lookup in the immutable snapshot"),
    ("function:check_v04_gap_assessment", "b2d50d138e2bd32f6ebdb8947c56d0167acb973c8efd6a59dc030f99d52d9f28", "historical report key used to read an already validated immutable snapshot"),
    ("function:check_v04_gap_handoff", "b9c67c57430a22d428b86056cffc1c6e05eb4409e41d17a9c4810a1c65a50b5c", "fixed handoff paths loaded through commit_file from one validated revision"),
    ("function:self_test_plan_cap_rev", "732ff08d3a5399b19b1e562f13677bfae69716a0a9828cf691ea7a8e87cda50d", "temporary plan-cap fixture path below a validated temporary root"),
    ("function:self_test_plan_cap_rev", "9c142e2a92e12557315b349b62416bbbd0f16396cb70046ee6d061dce381ae6d", "temporary plan-cap mutant path below the validated temporary root"),
    ("function:self_test_plan_cap_rev", "9c142e2a92e12557315b349b62416bbbd0f16396cb70046ee6d061dce381ae6d", "temporary plan-cap mutant path below the validated temporary root"),
    ("function:self_test_plan_cap_rev", "62e843dfe56c4c86767f7812725460f5c1260d6dffbeee28103b1c142e10289d", "temporary plan-cap mutant path below the validated temporary root"),
    ("function:self_test_plan_cap_rev", "62e843dfe56c4c86767f7812725460f5c1260d6dffbeee28103b1c142e10289d", "temporary plan-cap mutant path below the validated temporary root"),
    ("function:self_test_plan_cap_rev", "62e843dfe56c4c86767f7812725460f5c1260d6dffbeee28103b1c142e10289d", "temporary plan-cap mutant path below the validated temporary root"),
    ("function:self_test_v04_gap_assessment", "b9c67c57430a22d428b86056cffc1c6e05eb4409e41d17a9c4810a1c65a50b5c", "temporary assessment fixture path below the validated temporary root"),
    ("function:self_test_v04_gap_assessment", "c89267a4f5020381c92e357908dfbc8dfb42b5becea0d5e3e6bfe5662401bec4", "temporary pinned-input fixture path below the validated temporary root"),
    ("function:self_test_v04_gap_assessment", "993af3738e7fa4bec922be67da7b77c350399b8435fa5af33ba9fd73e8db9d0d", "temporary pinned-input fixture path below the validated temporary root"),
    ("function:self_test_v04_reconciliation", "e5bb2bb03d2228fe62db84da53299ef75c4a10709f5172246591a71b7f518595", "temporary Phase 20-23.1 fixture paths below the validated temporary root"),
)


class LintError(Exception):
    pass


def need(condition: bool, message: str) -> None:
    if not condition:
        raise LintError(message)


def tracked_files(root: Path) -> list[str]:
    result = subprocess.run(["git", "-C", str(root), "ls-files", "-z"], check=False, capture_output=True)
    need(result.returncode == 0, "REJECT git-ls-files: %s" % result.stderr.decode("utf-8", "replace").strip())
    return sorted(name for name in result.stdout.decode("utf-8", "surrogateescape").split("\0") if name)


def read_text(root: Path, name: str) -> str | None:
    path = root / name
    try:
        info = os.lstat(path)
    except OSError:
        return None
    if not stat.S_ISREG(info.st_mode):
        return None
    data = path.read_bytes()
    if b"\0" in data[:SNIFF_BYTES]:
        return None
    return data.decode("utf-8", "replace")


def _parents(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    return {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}


def _is_descendant(node: ast.AST, ancestor: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
    current = node
    while current in parents:
        current = parents[current]
        if current is ancestor:
            return True
    return False


def _path_site_context(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> str:
    current = node
    while current in parents:
        current = parents[current]
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return "function:" + current.name

    assignment = None
    current = node
    while current in parents:
        current = parents[current]
        if isinstance(current, (ast.Assign, ast.AnnAssign)):
            assignment = current
            break
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            break
    if assignment is None:
        raise LintError("REJECT planning-path-context: path token has no named function or module binding")
    targets = assignment.targets if isinstance(assignment, ast.Assign) else [assignment.target]
    binding = ast.unparse(targets[0])
    value = assignment.value

    if binding == "V04_GAP_SOURCE_PATHS":
        for container in ast.walk(value):
            if isinstance(container, (ast.Tuple, ast.List)):
                for index, element in enumerate(container.elts):
                    if _is_descendant(node, element, parents) or node is element:
                        return f"module:{binding}[{index}]"
    if binding == "V04_GAP_HISTORICAL_REPORTS":
        for container in ast.walk(value):
            if isinstance(container, ast.Dict):
                for key, item in zip(container.keys, container.values):
                    if key is not None and (_is_descendant(node, item, parents) or node is item):
                        return f"module:{binding}[{ast.literal_eval(key)}]"
    return "module:" + binding


def _source_path_sites(source: str) -> collections.Counter[tuple[str, str]]:
    """Map every lexical hit to one exact AST owner and token instead of accepting a hit count."""
    try:
        tree = ast.parse(source, filename=PLANNING_HYGIENE_FILE)
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except (SyntaxError, tokenize.TokenError, IndentationError) as error:
        raise LintError("REJECT planning-path-parse: %s" % error.__class__.__name__) from None
    parents = _parents(tree)
    line_starts = [0]
    for match in re.finditer("\n", source):
        line_starts.append(match.end())
    sites: collections.Counter[tuple[str, str]] = collections.Counter()

    for hit in SPELLINGS.finditer(source):
        start_line = source.count("\n", 0, hit.start())
        start_column = hit.start() - (line_starts[start_line] if start_line < len(line_starts) else 0)
        end_line = source.count("\n", 0, hit.end())
        end_column = hit.end() - (line_starts[end_line] if end_line < len(line_starts) else 0)
        token = next((item for item in tokens
                      if item.type in {tokenize.STRING, getattr(tokenize, "FSTRING_MIDDLE", -1)}
                      and (item.start[0] - 1, item.start[1]) <= (start_line, start_column)
                      and (item.end[0] - 1, item.end[1]) >= (end_line, end_column)), None)
        if token is None:
            raise LintError("REJECT planning-path-token: lexical hit is not inside one Python string token")

        candidates = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Constant, ast.JoinedStr)):
                continue
            if isinstance(node, ast.Constant) and not isinstance(node.value, str):
                continue
            start = (node.lineno - 1, node.col_offset)
            end = (node.end_lineno - 1, node.end_col_offset)
            if start <= (start_line, start_column) and end >= (end_line, end_column):
                candidates.append(node)
        if not candidates:
            raise LintError("REJECT planning-path-ast: lexical hit has no string expression in the AST")
        node = min(candidates, key=lambda item: (item.end_lineno - item.lineno,
                                                  item.end_col_offset - item.col_offset))
        current = node
        while current in parents and not isinstance(current, ast.JoinedStr):
            current = parents[current]
        if isinstance(current, ast.JoinedStr):
            node = current
            token_value = ast.get_source_segment(source, current) or token.string
        else:
            token_value = token.string
        token_digest = hashlib.sha256(token_value.encode("utf-8")).hexdigest()
        sites[(_path_site_context(node, parents), token_digest)] += 1
    return sites


def _assigned_names(target: ast.AST) -> set[str]:
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, (ast.Tuple, ast.List)):
        return set().union(*(_assigned_names(item) for item in target.elts))
    return set()


def _has_path_spelling(node: ast.AST, source_lines: list[str]) -> bool:
    start_line, end_line = node.lineno - 1, node.end_lineno - 1
    start_column, end_column = node.col_offset, node.end_col_offset
    if start_line == end_line:
        segment = source_lines[start_line][start_column:end_column]
    else:
        segment = (source_lines[start_line][start_column:]
                   + "".join(source_lines[start_line + 1:end_line])
                   + source_lines[end_line][:end_column])
    return SPELLINGS.search(segment) is not None


def _uses_name(node: ast.AST, names: set[str]) -> bool:
    return any(isinstance(item, ast.Name) and item.id in names for item in ast.walk(node))


def _is_temporary_path(node: ast.AST, roots: set[str]) -> bool:
    if isinstance(node, ast.Name):
        return node.id in roots
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        return _is_temporary_path(node.left, roots)
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id == "Path" and node.args:
            return _is_temporary_path(node.args[0], roots)
        if isinstance(node.func, ast.Name) and node.func.id == "make_phases" and node.args:
            return _is_temporary_path(node.args[0], roots)
        if isinstance(node.func, ast.Name) and node.func.id in ("sorted", "list") and node.args:
            return _is_temporary_path(node.args[0], roots)
        if isinstance(node.func, ast.Attribute) and node.func.attr in ("iterdir", "glob", "rglob"):
            return _is_temporary_path(node.func.value, roots)
    return False


def _is_temporary_directory_context(node: ast.AST) -> bool:
    return (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name) and node.func.value.id == "tempfile"
            and node.func.attr == "TemporaryDirectory")


def _fixture_root_contract(tree: ast.Module) -> dict[str, set[str]]:
    """Prove approved self-tests receive a TemporaryDirectory root before allowing fixture paths."""
    functions = {node.name: node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    root_specs = {
        "self_test_plan_cap_rev": (("repo", "rev-repo"), ("d205_root", "d205-path"),
                                   ("d205_repo", "d205-rev-repo")),
        "self_test_v04_gap_assessment": (("repo", "v04-gap-assessment-repo"),),
        "self_test_v04_reconciliation": (("repo", "v04-reconciliation-repo"),),
    }
    parent = _parents(tree)
    temp_context = None
    for item in ast.walk(functions.get("self_test", ast.Module(body=[], type_ignores=[]))):
        if isinstance(item, ast.With) and any(_is_temporary_directory_context(context.context_expr)
                                              for context in item.items):
            temp_context = item
            break
    if temp_context is None:
        raise LintError("REJECT planning-path-fixture-root: self_test has no TemporaryDirectory scope")
    base_assignment = any(isinstance(node, ast.Assign)
                          and any(isinstance(target, ast.Name) and target.id == "base" for target in node.targets)
                          and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name)
                          and node.value.func.id == "Path" and node.value.args
                          and isinstance(node.value.args[0], ast.Name)
                          and node.value.args[0].id == "scratch"
                          for node in ast.walk(temp_context))
    if not base_assignment:
        raise LintError("REJECT planning-path-fixture-root: base is not derived from TemporaryDirectory scratch")
    routed: set[str] = set()
    for node in ast.walk(temp_context):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
            continue
        if node.func.id in root_specs and node.args and isinstance(node.args[0], ast.Name) and node.args[0].id == "base":
            routed.add(node.func.id)
    if routed != set(root_specs):
        raise LintError("REJECT planning-path-fixture-root: named fixture checks are not all rooted at base")

    roots_by_function: dict[str, set[str]] = {}
    for name, specs in root_specs.items():
        function = functions.get(name)
        if function is None or not function.args.args or function.args.args[0].arg != "base":
            raise LintError("REJECT planning-path-fixture-root: %s does not accept the verified base" % name)
        names = {"base"}
        for target_name, directory in specs:
            rooted = False
            for node in ast.walk(function):
                if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.BinOp):
                    continue
                if (not any(isinstance(target, ast.Name) and target.id == target_name for target in node.targets)
                        or not isinstance(node.value.op, ast.Div)
                        or not isinstance(node.value.left, ast.Name) or node.value.left.id != "base"
                        or not isinstance(node.value.right, ast.Constant) or node.value.right.value != directory):
                    continue
                rooted = True
                names.add(target_name)
            if not rooted:
                raise LintError("REJECT planning-path-fixture-root: %s is not below TemporaryDirectory base" % target_name)
        roots_by_function[name] = names
    roots_by_function["self_test"] = {"scratch", "base"}
    return roots_by_function


def _reader_target(call: ast.Call) -> ast.AST | None:
    if isinstance(call.func, ast.Name) and call.func.id == "open" and call.args:
        return call.args[0]
    if not isinstance(call.func, ast.Attribute):
        return None
    if call.func.attr in {"read_text", "read_bytes", "open", "iterdir", "glob", "rglob",
                          "is_file", "is_dir", "exists", "stat", "resolve"}:
        return call.func.value
    if (isinstance(call.func.value, ast.Name) and call.func.value.id in {"os", "glob"}
            and call.func.attr in {"walk", "listdir", "scandir"} and call.args):
        return call.args[0]
    if (isinstance(call.func.value, ast.Attribute) and isinstance(call.func.value.value, ast.Name)
            and call.func.value.value.id == "os" and call.func.value.attr == "path"
            and call.func.attr in {"exists", "isfile", "isdir"} and call.args):
        return call.args[0]
    return None


def _validate_path_readers(source: str, tree: ast.Module,
                           roots_by_function: dict[str, set[str]]) -> None:
    parents = _parents(tree)
    source_lines = source.splitlines(keepends=True)
    functions = [node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    functions.sort(key=lambda item: (len(list(_ancestor_chain(item, parents))), item.lineno))
    scope_for: dict[ast.AST, ast.AST | None] = {}
    for node in ast.walk(tree):
        scope_for[node] = next((ancestor for ancestor in _ancestor_chain(node, parents)
                                if isinstance(ancestor, (ast.FunctionDef, ast.AsyncFunctionDef))), None)

    assignments: dict[ast.AST | None, list[tuple[ast.AST, list[ast.AST], set[str], bool]]] = {}
    loops: dict[ast.AST | None, list[ast.For]] = {}
    with_roots: dict[ast.AST | None, set[str]] = {}
    readers: list[tuple[ast.AST, ast.AST, ast.AST | None]] = []
    for node in ast.walk(tree):
        scope = scope_for[node]
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            names = {item.id for item in ast.walk(node.value) if isinstance(item, ast.Name)}
            assignments.setdefault(scope, []).append((node.value, targets, names,
                                                        _has_path_spelling(node.value, source_lines)))
        elif isinstance(node, ast.For):
            loops.setdefault(scope, []).append(node)
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                if _is_temporary_directory_context(item.context_expr) and item.optional_vars is not None:
                    with_roots.setdefault(scope, set()).update(_assigned_names(item.optional_vars))
        elif isinstance(node, ast.Call):
            target = _reader_target(node)
            if target is not None:
                readers.append((node, target, scope))

    path_names_by_scope: dict[ast.AST | None, set[str]] = {}
    root_names_by_scope: dict[ast.AST | None, set[str]] = {}
    for scope in [None, *functions]:
        parent_scope = (next((ancestor for ancestor in _ancestor_chain(scope, parents)
                              if isinstance(ancestor, (ast.FunctionDef, ast.AsyncFunctionDef))), None)
                        if scope is not None else None)
        path_names = set(path_names_by_scope.get(parent_scope, set()))
        root_names = set(root_names_by_scope.get(parent_scope, set()))
        root_names.update(roots_by_function.get(scope.name, set()) if scope is not None else ())
        root_names.update(with_roots.get(scope, set()))
        items = assignments.get(scope, [])
        changed = True
        while changed:
            changed = False
            for value, targets, names, direct_path in items:
                if direct_path or names.intersection(path_names):
                    for target in targets:
                        before = len(path_names)
                        path_names.update(_assigned_names(target))
                        changed |= len(path_names) != before
                if _is_temporary_path(value, root_names):
                    for target in targets:
                        before = len(root_names)
                        root_names.update(_assigned_names(target))
                        changed |= len(root_names) != before
        path_names_by_scope[scope] = path_names
        root_names_by_scope[scope] = root_names

    # Propagate names yielded by a directory iterator beneath a verified temporary root.
    changed = True
    while changed:
        changed = False
        for scope, scoped_loops in loops.items():
            roots = root_names_by_scope.setdefault(scope, set())
            for loop in scoped_loops:
                if _is_temporary_path(loop.iter, roots):
                    before = len(roots)
                    roots.update(_assigned_names(loop.target))
                    changed |= len(roots) != before

    for _call, target, scope in readers:
        path_names = path_names_by_scope.get(scope, set())
        if not _has_path_spelling(target, source_lines) and not _uses_name(target, path_names):
            continue
        roots = root_names_by_scope.get(scope, set())
        if scope is None or not _is_temporary_path(target, roots):
            owner = scope.name if scope is not None else "module"
            raise LintError("REJECT live-phase-path-reader: %s reads a phase path outside a verified fixture root" % owner)


def _ancestor_chain(node: ast.AST, parents: dict[ast.AST, ast.AST]):
    current = node
    while current in parents:
        current = parents[current]
        yield current


def validate_planning_hygiene_source(source: str) -> None:
    """Enforce the exact finite path-use contract, immutable revision, and fixture roots."""
    try:
        tree = ast.parse(source, filename=PLANNING_HYGIENE_FILE)
    except (SyntaxError, IndentationError) as error:
        raise LintError("REJECT planning-path-parse: %s" % error.__class__.__name__) from None
    revision = [node.value for node in tree.body if isinstance(node, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == "V04_D209_ARCHIVE_REV"
                        for target in node.targets)]
    if (len(revision) != 1 or not isinstance(revision[0], ast.Constant)
            or revision[0].value != PLANNING_HYGIENE_ARCHIVE_REVISION):
        raise LintError("REJECT planning-path-revision: D-209 archive identity changed or is ambiguous")

    actual = _source_path_sites(source)
    expected = collections.Counter((context, digest) for context, digest, _role in PLANNING_HYGIENE_PATH_SITES)
    expected_contexts = {context for context, _token in expected}
    actual_contexts = {context for context, _token in actual}
    unknown = actual_contexts - expected_contexts
    if unknown:
        raise LintError("REJECT planning-path-unclassified: %s" % sorted(unknown)[0])
    for (context, token), count in actual.items():
        allowed = expected[(context, token)]
        if allowed == 0:
            raise LintError("REJECT planning-path-value-changed: %s" % context)
        if count > allowed:
            raise LintError("REJECT planning-path-site-duplicate: %s" % context)
    missing = [(context, token) for (context, token), count in expected.items()
               if actual[(context, token)] < count]
    if missing:
        raise LintError("REJECT planning-path-site-missing: %s" % missing[0][0])

    roots = _fixture_root_contract(tree)
    _validate_path_readers(source, tree, roots)


def validate_planning_hygiene_path_contract(root: Path) -> None:
    source = read_text(root, PLANNING_HYGIENE_FILE)
    need(source is not None, "REJECT planning-path-must-scan: %s was not read as text" % PLANNING_HYGIENE_FILE)
    validate_planning_hygiene_source(source)


def self_test_planning_hygiene_path_contract() -> int:
    """Exercise the finite source contract and its causal path-reader negatives."""
    source_path = ROOT / PLANNING_HYGIENE_FILE
    source = source_path.read_text(encoding="utf-8")
    controls = 0

    binding_line = next(line for line in source.splitlines() if line.startswith("PHASES_AT_REV = "))
    path_token = binding_line.partition("=")[2].strip()
    finite_fixture = (
        "PHASES_AT_REV = " + path_token + "\n"
        "def read_rev(repo, revision):\n"
        "    return git_run(repo, 'show', revision + ':' + PHASES_AT_REV)\n"
    )
    expected_fixture = collections.Counter({
        ("module:PHASES_AT_REV", hashlib.sha256(path_token.encode("utf-8")).hexdigest()): 1,
    })
    need(_source_path_sites(finite_fixture) == expected_fixture,
         "planning-hygiene path self-test: finite immutable-source fixture was not classified")
    controls += 1

    try:
        validate_planning_hygiene_source(source)
    except LintError as error:
        raise LintError("planning-hygiene path self-test: production source was rejected: %s" % error) from None
    controls += 1
    original_lexical_count = len(list(SPELLINGS.finditer(source)))

    def expect_rejected(label: str, candidate: str, reason: str, same_count: bool = False) -> None:
        nonlocal controls
        if same_count:
            need(len(list(SPELLINGS.finditer(candidate))) == original_lexical_count,
                 "%s: mutation changed the lexical hit count" % label)
        try:
            validate_planning_hygiene_source(candidate)
        except LintError as error:
            need(str(error).startswith(reason), "%s: refused for %r instead of %s" % (label, str(error), reason))
            controls += 1
            return
        raise LintError("%s: unsafe path-use mutation was accepted" % label)

    extra_path = source + "\nUNCLASSIFIED_PATH = " + path_token + "\n"
    expect_rejected("unclassified path literal", extra_path, "REJECT planning-path-unclassified")

    changed_path = source.replace("24-EVIDENCE.md", "25-EVIDENCE.md", 1)
    need(changed_path != source, "path-value mutation did not find its source site")
    expect_rejected("changed approved path", changed_path, "REJECT planning-path-value-changed", same_count=True)

    changed_revision = source.replace(PLANNING_HYGIENE_ARCHIVE_REVISION, "f" * 40, 1)
    need(changed_revision != source, "archive revision mutation did not find its source site")
    expect_rejected("changed archive revision", changed_revision, "REJECT planning-path-revision")

    report_line = next(line for line in source.splitlines() if line.startswith("V04_GAP_REPORT_PATH = "))
    missing_site = source.replace(report_line + "\n", "", 1)
    need(missing_site != source, "missing-site mutation did not find its source site")
    expect_rejected("missing classified site", missing_site, "REJECT planning-path-site-missing")
    duplicated_site = source.replace(report_line, report_line + "\n" + report_line, 1)
    expect_rejected("duplicate classified site", duplicated_site, "REJECT planning-path-site-duplicate")

    escaped_root = source.replace("repo = base / \"rev-repo\"", "repo = Path(\".\")", 1)
    need(escaped_root != source, "fixture-root mutation did not find its source site")
    expect_rejected("fixture read root escape", escaped_root, "REJECT planning-path-fixture-root")

    reader_mutations = (
        ("PHASES_AT_REV alias reader",
         "\ndef injected_alias_reader():\n    alias = PHASES_AT_REV\n    return Path(alias).read_text(encoding=\"utf-8\")\n"),
        ("approved path passed to open",
         "\ndef injected_open_reader():\n    return open(V04_GAP_REPORT_PATH, encoding=\"utf-8\").read()\n"),
        ("approved path passed to read_text",
         "\ndef injected_text_reader():\n    return Path(V04_GAP_REPORT_PATH).read_text(encoding=\"utf-8\")\n"),
        ("approved path passed to read_bytes",
         "\ndef injected_bytes_reader():\n    return Path(V04_GAP_REPORT_PATH).read_bytes()\n"),
        ("approved path passed to traversal",
         "\ndef injected_tree_reader():\n    return Path(V04_GAP_SOURCE_PATHS[3]).rglob(\"*\")\n"),
    )
    for label, addition in reader_mutations:
        expect_rejected(label, source + addition, "REJECT live-phase-path-reader", same_count=True)
    return controls


def v04_closeout_path_fixture(path: str = HISTORICAL_V04_EVIDENCE_PATH) -> str:
    sources = [{"components": [{} for _ in range(5)]} for _ in range(4)]
    for source_index in (2, 3):
        sources[source_index]["components"][4] = {"evidence": [path]}
    return json.dumps({"sources": sources}, indent=2) + "\n"


def exact_historical_evidence_lines(name: str, text: str) -> set[int]:
    """Allow only the two exact D-209 provenance values in their known JSON fields."""
    if name != HISTORICAL_V04_EVIDENCE_FILE:
        return set()

    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise LintError("REJECT historical-evidence-structure: duplicate JSON object key")
            result[key] = value
        return result

    try:
        document = json.loads(text, object_pairs_hook=unique_object)
        observed = []
        for location in HISTORICAL_V04_EVIDENCE_LOCATIONS:
            value = document
            for part in location:
                value = value[part]
            observed.append(value)
    except LintError:
        raise
    except (json.JSONDecodeError, KeyError, IndexError, TypeError):
        raise LintError("REJECT historical-evidence-structure: v04-closeout.json is not the pinned JSON shape") from None
    if observed != [HISTORICAL_V04_EVIDENCE_PATH] * 2 or text.count(HISTORICAL_V04_EVIDENCE_PATH) != 2:
        raise LintError("REJECT historical-evidence-cardinality: expected exactly two fixed provenance values")
    token = json.dumps(HISTORICAL_V04_EVIDENCE_PATH, ensure_ascii=False)
    lines = {number for number, line in enumerate(text.splitlines(), start=1) if line.strip() == token}
    if len(lines) != 2:
        raise LintError("REJECT historical-evidence-content: provenance values must occupy complete JSON lines")
    return lines


def scan(root: Path) -> tuple[int, dict[str, list[tuple[int, str]]], set[str]]:
    scanned: set[str] = set()
    hits: dict[str, list[tuple[int, str]]] = {}
    for name in tracked_files(root):
        if name == ".planning" or name.startswith(".planning/"):
            continue
        text = read_text(root, name)
        if text is None:
            continue
        scanned.add(name)
        exception_lines = exact_historical_evidence_lines(name, text)
        for match in SPELLINGS.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            if line in exception_lines:
                continue
            hits.setdefault(name, []).append((line, match.lastgroup or "?"))
    return len(scanned), hits, scanned


def check(root: Path, allowlist=ALLOWLIST, must_scan=MUST_SCAN, report: bool = False) -> tuple[int, int]:
    files, hits, scanned = scan(root)
    for name in must_scan:
        need(name in scanned, "REJECT must-scan-missing: %s was not scanned" % name)
    if PLANNING_HYGIENE_FILE in scanned:
        validate_planning_hygiene_path_contract(root)
    pins: dict[str, int] = {}
    for name, maximum, reason in allowlist:
        need(bool(reason.strip()), "REJECT allowlist-reason: %s has no reason" % name)
        need(name not in pins, "REJECT allowlist-duplicate: %s appears twice" % name)
        pins[name] = maximum
    for name in sorted(hits):
        found = hits[name]
        if report:
            print("hits %s %d" % (name, len(found)), file=sys.stderr)
        if name == PLANNING_HYGIENE_FILE:
            continue
        if name not in pins:
            raise LintError("REJECT phase-path: %s:%d %s spelling of the live phases directory"
                            % (name, found[0][0], found[0][1]))
        if len(found) > pins[name]:
            raise LintError("REJECT over-max: %s has %d hits, allowlist pins %d (first excess at line %d)"
                            % (name, len(found), pins[name], found[pins[name]][0]))
    for name, maximum in sorted(pins.items()):
        observed = len(hits.get(name, []))
        need(observed == maximum, "REJECT stale-allowlist: %s has %d hits, allowlist pins %d" % (name, observed, maximum))
    return files, len(pins)


def run_check(args) -> int:
    files, allowlisted = check(ROOT, report=args.report)
    print("no-phase-paths pass files=%d allowlisted=%d" % (files, allowlisted))
    return 0


# ---- self-test -----------------------------------------------------------------------------------

CLEAN_FILES = {
    "tests/CMakeLists.txt": "set(GBB_V02 ${PROJECT_SOURCE_DIR}/.planning/milestones/v0.2-phases)\n",
    "tests/scripts/reader.py": "ARCHIVE = '.planning/milestones/v0.2-phases/GB-15'\n",
    "cmake/module.cmake": "message(STATUS read)\n",
    ".github/workflows/ci.yml": "name: ci\n",
    "docs/evidence.md": "See [v0.1](../.planning/milestones/v0.1-phases/GB-01/x.md) and a bare phases/ note.\n",
    "README.md": "# fixture\n",
    HISTORICAL_V04_EVIDENCE_FILE: v04_closeout_path_fixture(),
    ".planning/phases/GB-16/note.md": "planning files may name their own directory: .planning/phases\n",
}
BINARY_BODY = b"\0\x01 .planning/phases hidden in a binary\n"


def make_fixture(root: Path, files: dict[str, str], binary: bool = True) -> None:
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    if binary:
        blob = root / "tests" / "data" / "blob.bin"
        blob.parent.mkdir(parents=True, exist_ok=True)
        blob.write_bytes(BINARY_BODY)
    for command in (["init", "-q"], ["add", "-A", "-f"]):
        done = subprocess.run(["git", "-C", str(root)] + command, check=False, capture_output=True)
        need(done.returncode == 0, "fixture git %s failed" % command[0])


def expect_rejected(label: str, prefix: str, files: dict[str, str], allowlist=(), must_scan=()) -> None:
    with tempfile.TemporaryDirectory(prefix="gbb-no-phase-paths-") as name:
        root = Path(name)
        make_fixture(root, files)
        try:
            check(root, allowlist=allowlist, must_scan=must_scan)
        except LintError as error:
            need(str(error).startswith(prefix), "%s: rejected with %r, wanted %s" % (label, str(error), prefix))
            return
        raise LintError("%s: accepted a violation" % label)


def expect_accepted(label: str, files: dict[str, str], allowlist=(), must_scan=()) -> None:
    with tempfile.TemporaryDirectory(prefix="gbb-no-phase-paths-") as name:
        root = Path(name)
        make_fixture(root, files)
        try:
            check(root, allowlist=allowlist, must_scan=must_scan)
        except LintError as error:
            raise LintError("%s: rejected a clean tree: %s" % (label, error))


def mutated(files: dict[str, str], name: str, old: str, new: str) -> dict[str, str]:
    changed = dict(files)
    original = changed[name]
    changed[name] = original.replace(old, new)
    need(changed[name] != original, "%s: inactive mutation" % name)
    return changed


def self_test() -> int:
    controls = self_test_planning_hygiene_path_contract()
    expect_accepted("clean tree", CLEAN_FILES)
    controls += 1
    expect_accepted("exact archived v0.4 evidence paths", CLEAN_FILES)
    controls += 1
    wrong_location = dict(CLEAN_FILES)
    wrong_document = json.loads(wrong_location[HISTORICAL_V04_EVIDENCE_FILE])
    wrong_document["sources"][3]["components"][3] = wrong_document["sources"][3]["components"][4]
    wrong_document["sources"][3]["components"][4] = {}
    wrong_location[HISTORICAL_V04_EVIDENCE_FILE] = json.dumps(wrong_document, indent=2) + "\n"
    expect_rejected("two historical paths at wrong structural locations", "REJECT historical-evidence-structure",
                    wrong_location)
    controls += 1
    duplicate_key = dict(CLEAN_FILES)
    duplicate_key[HISTORICAL_V04_EVIDENCE_FILE] = duplicate_key[HISTORICAL_V04_EVIDENCE_FILE].replace(
        '"sources": [', '"sources": [], "sources": [', 1)
    expect_rejected("duplicate JSON key in historical evidence", "REJECT historical-evidence-structure",
                    duplicate_key)
    controls += 1
    changed_path = dict(CLEAN_FILES)
    changed_path[HISTORICAL_V04_EVIDENCE_FILE] = changed_path[HISTORICAL_V04_EVIDENCE_FILE].replace(
        HISTORICAL_V04_EVIDENCE_PATH, ".planning/phases/GB-23-qualified-v0-4-0-release/23-CONTEXT.md", 1)
    expect_rejected("two-hit path substitution", "REJECT historical-evidence-cardinality", changed_path)
    controls += 1
    duplicate_path = dict(CLEAN_FILES)
    duplicate_document = json.loads(duplicate_path[HISTORICAL_V04_EVIDENCE_FILE])
    duplicate_document["sources"][0]["extra_evidence"] = [HISTORICAL_V04_EVIDENCE_PATH]
    duplicate_path[HISTORICAL_V04_EVIDENCE_FILE] = json.dumps(duplicate_document, indent=2) + "\n"
    expect_rejected("additional historical-path occurrence", "REJECT historical-evidence-cardinality",
                    duplicate_path)
    controls += 1
    added_reader = dict(CLEAN_FILES)
    added_reader["tests/scripts/reader.py"] += (
        "ARCHIVE = '.planning/phases/GB-22-composition-and-microtest-evidence/22-CONTEXT.md'\n")
    expect_rejected("historical provenance does not permit a live reader", "REJECT phase-path", added_reader)
    controls += 1
    # A real accepted milestone link, the bare directory name and a binary body all pass.
    need(".planning/milestones/v0.1-phases" in CLEAN_FILES["docs/evidence.md"], "fixture lost its v0.1 link")
    need(b".planning/phases" in BINARY_BODY, "binary fixture lost its hidden path")
    expect_accepted("milestone link, bare phases/ and binary skipped", CLEAN_FILES)
    controls += 1

    spellings = (
        ("literal", "OLD = '.planning/phases/GB-07'\n"),
        ("joined os.path.join", "OLD = os.path.join('.planning', 'phases', 'GB-07')\n"),
        ("joined Path division", "OLD = Path('.planning') / 'phases' / 'GB-07'\n"),
        ("backslash", "OLD = '.planning\\\\phases\\\\GB-07'\n"),
        ("prefixed", "set(X \"${PROJECT_SOURCE_DIR}/.planning/phases/GB-07\")\n"),
    )
    for label, body in spellings:
        files = mutated(CLEAN_FILES, "tests/scripts/reader.py", "ARCHIVE = '.planning/milestones/v0.2-phases/GB-15'\n", body)
        expect_rejected("spelling " + label, "REJECT phase-path", files)
        controls += 1

    boundary_file = "tests/scripts/verify-diagnostic-evidence.py"
    boundary_path = 'BOUNDARY_PATHS = (".planning/phases/GB-22-composition-and-microtest-evidence/.continue-here.md",)\n'
    boundary_fixture = dict(CLEAN_FILES)
    boundary_fixture[boundary_file] = boundary_path
    expect_accepted("immutable boundary path pin", boundary_fixture,
                    allowlist=((boundary_file, 1, "point-in-time boundary path"),),
                    must_scan=(boundary_file,))
    controls += 1
    over_pinned_boundary = dict(boundary_fixture)
    over_pinned_boundary[boundary_file] += boundary_path
    expect_rejected("boundary path over-max", "REJECT over-max", over_pinned_boundary,
                    allowlist=((boundary_file, 1, "point-in-time boundary path"),),
                    must_scan=(boundary_file,))
    controls += 1

    phase_root = ".planning/phases"
    phase_link_rows = (
        ("Phase 21 verification", "bef2cfbdbdd0fc9b2d78631586827e29e0241b3b",
         "/GB-21-cgb-game-progress-and-scene-regressions/21-VERIFICATION.md"),
        ("Phase 21 UAT evidence", "bef2cfbdbdd0fc9b2d78631586827e29e0241b3b",
         "/GB-21-cgb-game-progress-and-scene-regressions/21-UAT-EVIDENCE.md"),
        ("Phase 22 evidence", "d18db4c56d2a79e6138df37a9d16e3d346a86e13",
         "/GB-22-composition-and-microtest-evidence/22-EVIDENCE.md"),
        ("Phase 22 UAT", "d18db4c56d2a79e6138df37a9d16e3d346a86e13",
         "/GB-22-composition-and-microtest-evidence/22-UAT.md"),
    )
    output_name = "docs/support/v0.4.0.md"
    output_allowlist = ((output_name, 4, "four immutable historical output links"),)
    four_links = "\n".join(
        f"[{label}](https://github.com/szTheory/gabbaboy/blob/{revision}/{phase_root}{suffix})"
        for label, revision, suffix in phase_link_rows
    ) + "\n"
    expect_accepted("four immutable Phase 21/22 output links",
                    {output_name: four_links}, allowlist=output_allowlist)
    controls += 1
    fifth_link = four_links.splitlines()[0] + "\n"
    expect_rejected("fifth duplicate immutable output link", "REJECT over-max",
                    {output_name: four_links + fifth_link}, allowlist=output_allowlist)
    controls += 1

    leak = "OLD = '.planning/phases/GB-07'\n"
    for name in ("tests/scripts/reader.py", "cmake/module.cmake", ".github/workflows/ci.yml", "docs/evidence.md", "README.md"):
        changed = dict(CLEAN_FILES)
        original = changed[name]
        changed[name] = original + leak
        need(changed[name] != original, name + ": inactive mutation")
        expect_rejected("scope root " + name, "REJECT phase-path", changed)
        controls += 1

    # Allowlist behavior: an exact pin passes, over-max and stale rows fail, and reasons are mandatory.
    pinned = dict(CLEAN_FILES)
    pinned["tests/scripts/reader.py"] = CLEAN_FILES["tests/scripts/reader.py"] + leak
    expect_accepted("exact pin", pinned, allowlist=(("tests/scripts/reader.py", 1, "fixture"),))
    controls += 1
    expect_rejected("over-max row", "REJECT over-max", pinned,
                    allowlist=(("tests/scripts/reader.py", 0, "fixture"),))
    controls += 1
    expect_rejected("stale row", "REJECT stale-allowlist", CLEAN_FILES,
                    allowlist=(("tests/scripts/reader.py", 1, "fixture"),))
    controls += 1
    expect_rejected("row without reason", "REJECT allowlist-reason", pinned,
                    allowlist=(("tests/scripts/reader.py", 1, " "),))
    controls += 1
    expect_rejected("must-scan file absent", "REJECT must-scan-missing", CLEAN_FILES,
                    must_scan=("tests/scripts/does-not-exist.py",))
    controls += 1
    print("no-phase-paths self-test pass controls=%d" % controls)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="scan the tracked tree")
    mode.add_argument("--self-test", action="store_true", help="run the negative controls")
    parser.add_argument("--report", action="store_true", help="print per-file hit counts to stderr")
    args = parser.parse_args()
    try:
        return self_test() if args.self_test else run_check(args)
    except LintError as error:
        print(str(error) if str(error).startswith("REJECT") else "REJECT lint: %s" % error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
