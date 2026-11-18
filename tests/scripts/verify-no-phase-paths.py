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
import ntpath
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
from dataclasses import dataclass
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


def _literal_string(node: ast.AST, names: dict[str, str] | None = None, depth: int = 0) -> str | None:
    """Fold only statically known strings and path joins; never evaluate inspected source."""
    if depth > 12:
        return None
    names = names or {}
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        return names.get(node.id)
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "chr"
            and len(node.args) == 1 and not node.keywords):
        argument = node.args[0]
        if (isinstance(argument, ast.Constant) and type(argument.value) is int
                and 0 <= argument.value <= 0x10FFFF):
            return chr(argument.value)
        return None
    if isinstance(node, ast.JoinedStr):
        parts = []
        for item in node.values:
            if isinstance(item, ast.Constant) and isinstance(item.value, str):
                parts.append(item.value)
            elif isinstance(item, ast.FormattedValue):
                value = _literal_string(item.value, names, depth + 1)
                if value is None:
                    return None
                parts.append(value)
            else:
                return None
        return "".join(parts)
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Div)):
        left = _literal_string(node.left, names, depth + 1)
        right = _literal_string(node.right, names, depth + 1)
        if left is None or right is None:
            return None
        if isinstance(node.op, ast.Add):
            return left + right
        # pathlib-style joining: an absolute right side replaces its left side.
        if right.startswith(("/", "\\")) or ntpath.splitdrive(right)[0]:
            return right
        return left.rstrip("/\\") + "/" + right.lstrip("/\\")
    if isinstance(node, ast.Subscript):
        value = _literal_string(node.value, names, depth + 1)
        index = node.slice
        if value is None or not isinstance(index, ast.Constant) or not isinstance(index.value, int):
            return None
        try:
            return value[index.value]
        except IndexError:
            return None
    return None


def _literal_path_string(node: ast.AST, names: dict[str, str] | None = None, depth: int = 0) -> str | None:
    """Fold only literal pathlib/os.path construction, without evaluating source."""
    if depth > 12:
        return None
    names = names or {}
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        left = _literal_path_string(node.left, names, depth + 1)
        right = _literal_string(node.right, names, depth + 1)
        if left is None or right is None:
            return None
        if right.startswith(("/", "\\")) or ntpath.splitdrive(right)[0]:
            return right
        return left.rstrip("/\\") + "/" + right.lstrip("/\\")
    if isinstance(node, ast.Call):
        function = node.func
        is_constructor = ((isinstance(function, ast.Name) and function.id in
                           {"Path", "PurePath", "PosixPath", "WindowsPath"})
                          or (isinstance(function, ast.Attribute) and function.attr in
                              {"Path", "PurePath", "PosixPath", "WindowsPath"}))
        if is_constructor and node.args:
            parts = [_literal_string(item, names, depth + 1) for item in node.args]
            if any(item is None for item in parts):
                return None
            folded = parts[0]
            for part in parts[1:]:
                assert part is not None and folded is not None
                folded = (part if part.startswith(("/", "\\")) or ntpath.splitdrive(part)[0]
                          else folded.rstrip("/\\") + "/" + part.lstrip("/\\"))
            return folded
        if isinstance(function, ast.Attribute) and function.attr == "joinpath":
            folded = _literal_path_string(function.value, names, depth + 1)
            parts = [_literal_string(item, names, depth + 1) for item in node.args]
            if folded is None or any(item is None for item in parts):
                return None
            for part in parts:
                assert part is not None
                folded = (part if part.startswith(("/", "\\")) or ntpath.splitdrive(part)[0]
                          else folded.rstrip("/\\") + "/" + part.lstrip("/\\"))
            return folded
        if (isinstance(function, ast.Attribute) and function.attr == "join"
                and isinstance(function.value, ast.Attribute) and function.value.attr == "path"):
            parts = [_literal_string(item, names, depth + 1) for item in node.args]
            if not parts or any(item is None for item in parts):
                return None
            folded = parts[0]
            for part in parts[1:]:
                assert part is not None and folded is not None
                folded = (part if part.startswith(("/", "\\")) or ntpath.splitdrive(part)[0]
                          else folded.rstrip("/\\") + "/" + part.lstrip("/\\"))
            return folded
    return _literal_string(node, names, depth + 1)


def _protected_path_text(value: str) -> bool:
    return SPELLINGS.search(value.replace("\\", "/")) is not None


def _has_path_spelling(node: ast.AST, source_lines: list[str], names: dict[str, str] | None = None) -> bool:
    # AST Constant.value is already Python-decoded: \x2e, \u002e, and adjacent literals
    # therefore receive the same semantic check as their unescaped source spelling.
    folded = _literal_string(node, names)
    if folded is not None and _protected_path_text(folded):
        return True
    for item in ast.walk(node):
        if isinstance(item, ast.Constant) and isinstance(item.value, str) and _protected_path_text(item.value):
            return True
    if not hasattr(node, "lineno") or not hasattr(node, "end_lineno"):
        return False
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


def _safe_relative_component(node: ast.AST, names: dict[str, str] | None = None) -> bool:
    value = _literal_string(node, names)
    if value is None or not value or value.startswith(("/", "\\")) or ntpath.splitdrive(value)[0]:
        return False
    normalized = value.replace("\\", "/")
    return all(component not in ("", "..") for component in normalized.split("/"))


def _is_temporary_path(node: ast.AST, roots: set[str], names: dict[str, str] | None = None) -> bool:
    if isinstance(node, ast.Name):
        return node.id in roots
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        return (_is_temporary_path(node.left, roots, names)
                and _safe_relative_component(node.right, names))
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id == "Path" and node.args:
            return _is_temporary_path(node.args[0], roots, names)
        if isinstance(node.func, ast.Name) and node.func.id == "make_phases" and node.args:
            return _is_temporary_path(node.args[0], roots, names)
        if isinstance(node.func, ast.Name) and node.func.id in ("sorted", "list") and node.args:
            return _is_temporary_path(node.args[0], roots, names)
        if isinstance(node.func, ast.Attribute) and node.func.attr in ("iterdir", "glob", "rglob"):
            return _is_temporary_path(node.func.value, roots, names)
    return False


def _has_temporary_origin(node: ast.AST, roots: set[str],
                          assignments: list[tuple[ast.AST, list[ast.AST], set[str], bool]],
                          names: dict[str, str] | None = None,
                          seen: frozenset[str] = frozenset()) -> bool:
    """Track whether a possibly-escaped expression was ever derived from a proven temp root."""
    names = names or {}
    if isinstance(node, ast.Name):
        if node.id in roots:
            return True
        if node.id in seen:
            return False
        return any(node.id in _assigned_names(target)
                   and _has_temporary_origin(value, roots, assignments, names, seen | {node.id})
                   for value, targets, _referenced, _direct in assignments for target in targets)
    if isinstance(node, ast.BinOp):
        return (_has_temporary_origin(node.left, roots, assignments, names, seen)
                or _has_temporary_origin(node.right, roots, assignments, names, seen))
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in {"Path", "make_phases"}:
            return bool(node.args) and _has_temporary_origin(node.args[0], roots, assignments, names, seen)
        if isinstance(node.func, ast.Attribute) and node.func.attr in {"iterdir", "glob", "rglob"}:
            return _has_temporary_origin(node.func.value, roots, assignments, names, seen)
    return False


@dataclass(frozen=True)
class _PathFact:
    text: str | None = None
    protected: bool = False
    temporary_origin: bool = False
    contained: bool = False
    callable_name: str | None = None
    callable_target: ast.AST | None = None


def _merge_path_facts(*facts: _PathFact) -> _PathFact:
    protected = any(item.protected for item in facts)
    origins = [item for item in facts if item.temporary_origin]
    return _PathFact(protected=protected,
                     temporary_origin=bool(origins),
                     contained=bool(origins) and all(item.contained for item in origins),
                     callable_name=(facts[0].callable_name if facts and
                                    all(item.callable_name == facts[0].callable_name for item in facts) else None),
                     callable_target=(facts[0].callable_target if facts and
                                      all(item.callable_target is facts[0].callable_target for item in facts) else None))


def _approved_git_object_adapters(tree: ast.Module) -> set[ast.AST]:
    """Return only the exact reviewed Git subprocess adapter, rejecting body changes."""
    candidates = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                  and node.name == "git_run"]
    if len(candidates) != 1 or not isinstance(candidates[0], ast.FunctionDef):
        raise LintError("REJECT planning-path-git-adapter: expected one top-level synchronous git_run")

    expected = ast.parse("""def _expected_git_run(repo, *args):
    env = {k: v for k, v in os.environ.items() if k in ("PATH", "SYSTEMROOT", "TMPDIR", "TEMP", "TMP")}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=False, env=env, timeout=60)
""").body[0]
    actual = candidates[0]
    def argument_shape(arguments: ast.arguments) -> tuple[object, ...]:
        return (
            tuple(item.arg for item in arguments.posonlyargs),
            tuple(item.arg for item in arguments.args),
            arguments.vararg.arg if arguments.vararg is not None else None,
            tuple(item.arg for item in arguments.kwonlyargs),
            tuple(ast.dump(item, include_attributes=False) if item is not None else None
                  for item in arguments.kw_defaults),
            arguments.kwarg.arg if arguments.kwarg is not None else None,
            tuple(ast.dump(item, include_attributes=False) for item in arguments.defaults),
        )
    if (actual.decorator_list or argument_shape(actual.args) != argument_shape(expected.args)
            or ast.dump(ast.Module(body=actual.body, type_ignores=[]), include_attributes=False) !=
            ast.dump(ast.Module(body=expected.body, type_ignores=[]), include_attributes=False)):
        raise LintError("REJECT planning-path-git-adapter: approved immutable Git adapter wrapper or body changed")
    return {actual}


def _has_chr_binding(tree: ast.Module) -> bool:
    """Treat a source-local chr binding as unknown rather than assuming the built-in."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == "chr" and isinstance(node.ctx, ast.Store):
            return True
        if isinstance(node, ast.arg) and node.arg == "chr":
            return True
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == "chr":
            return True
        if isinstance(node, ast.alias) and (node.asname == "chr" or
                                            (node.asname is None and node.name.split(".", 1)[0] == "chr")):
            return True
        if isinstance(node, ast.ExceptHandler) and node.name == "chr":
            return True
        if isinstance(node, (ast.Global, ast.Nonlocal)) and "chr" in node.names:
            return True
    return False


def _validate_decoded_path_flow(source: str, tree: ast.Module,
                                roots_by_function: dict[str, set[str]]) -> None:
    """Check decoded values and bounded helper calls without importing or executing source."""
    trusted_git_adapters = _approved_git_object_adapters(tree)
    parents = _parents(tree)
    functions = [node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    chr_shadowed = _has_chr_binding(tree)
    for reader in ast.walk(tree):
        if not isinstance(reader, ast.Call):
            continue
        target = _reader_target(reader)
        if target is not None and any(
                isinstance(item, ast.Call) and isinstance(item.func, ast.Name) and item.func.id == "chr"
                for item in ast.walk(target)):
            if chr_shadowed:
                raise LintError("REJECT live-phase-path-reader: chr is shadowed in an unresolved reader path")
    scope_by_node: dict[ast.AST, ast.AST | None] = {}
    nodes_by_scope: dict[ast.AST | None, list[ast.AST]] = {None: []}
    for node in ast.walk(tree):
        scope = next((ancestor for ancestor in _ancestor_chain(node, parents)
                      if isinstance(ancestor, (ast.FunctionDef, ast.AsyncFunctionDef))), None)
        scope_by_node[node] = scope
        nodes_by_scope.setdefault(scope, []).append(node)
    function_parent = {node: scope_by_node[node] for node in functions}
    by_parent: dict[tuple[ast.AST | None, str], list[ast.AST]] = {}
    for function in functions:
        by_parent.setdefault((function_parent[function], function.name), []).append(function)

    def scope_of(node: ast.AST) -> ast.AST | None:
        return scope_by_node.get(node)

    def direct_scope_nodes(function: ast.AST) -> list[ast.AST]:
        return [function, *nodes_by_scope.get(function, [])]

    def function_path_builders() -> set[ast.AST]:
        builders: set[ast.AST] = set()
        changed = True
        while changed:
            changed = False
            for function in functions:
                if function in builders:
                    continue
                assigned = {name: value for node in direct_scope_nodes(function)
                            if isinstance(node, (ast.Assign, ast.AnnAssign))
                            for value in [node.value]
                            for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
                            for name in _assigned_names(target)}
                returns = [node.value for node in direct_scope_nodes(function)
                           if isinstance(node, ast.Return) and node.value is not None]
                def is_path_expr(node: ast.AST, seen: frozenset[str] = frozenset()) -> bool:
                    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
                        return True
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name) and node.func.id == "Path":
                            return True
                        if isinstance(node.func, ast.Name):
                            candidates = [item for item in builders if item.name == node.func.id]
                            if candidates:
                                return True
                    if isinstance(node, ast.Name) and node.id not in seen and node.id in assigned:
                        return is_path_expr(assigned[node.id], seen | {node.id})
                    return False
                if any(is_path_expr(node) for node in returns):
                    builders.add(function)
                    changed = True
        return builders

    path_builders = function_path_builders()
    function_used_names = {
        function: {node.id for node in direct_scope_nodes(function) if isinstance(node, ast.Name)}
        for function in functions
    }

    module_env: dict[str, _PathFact] = {}
    for statement in tree.body:
        if isinstance(statement, ast.Assign):
            value = _literal_string(statement.value, {name: fact.text for name, fact in module_env.items()
                                                      if fact.text is not None})
            literal_protected = any(isinstance(item, ast.Constant) and isinstance(item.value, str)
                                    and _protected_path_text(item.value) for item in ast.walk(statement.value))
            inherited = _merge_path_facts(*[module_env[item.id] for item in ast.walk(statement.value)
                                            if isinstance(item, ast.Name) and item.id in module_env])
            fact = _PathFact(text=value,
                             protected=(literal_protected or inherited.protected
                                        or (value is not None and _protected_path_text(value))))
            for target in statement.targets:
                for name in _assigned_names(target):
                    module_env[name] = fact
        elif isinstance(statement, ast.AnnAssign) and statement.value is not None:
            value = _literal_string(statement.value, {name: fact.text for name, fact in module_env.items()
                                                      if fact.text is not None})
            literal_protected = any(isinstance(item, ast.Constant) and isinstance(item.value, str)
                                    and _protected_path_text(item.value) for item in ast.walk(statement.value))
            inherited = _merge_path_facts(*[module_env[item.id] for item in ast.walk(statement.value)
                                            if isinstance(item, ast.Name) and item.id in module_env])
            for name in _assigned_names(statement.target):
                module_env[name] = _PathFact(text=value,
                                             protected=(literal_protected or inherited.protected or
                                                        (value is not None and _protected_path_text(value))))

    # The lexical inventory stays authoritative for exact source sites. This second pass sees
    # decoded constants and finite AST compositions even when they add no lexical hit.
    module_strings = {name: fact.text for name, fact in module_env.items() if fact.text is not None}
    literal_names_by_scope: dict[ast.AST | None, dict[str, str]] = {}
    for scope in [None, *functions]:
        names = dict(module_strings)
        if scope is not None:
            scoped_assignments = sorted(
                (node for node in nodes_by_scope.get(scope, ())
                 if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None),
                key=lambda node: (node.lineno, node.col_offset))
            for _ in range(min(len(scoped_assignments), 12)):
                changed = False
                for statement in scoped_assignments:
                    value = _literal_string(statement.value, names)
                    if value is None:
                        continue
                    targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
                    for target in targets:
                        for name in _assigned_names(target):
                            if name not in names:
                                names[name] = value
                                changed = True
                if not changed:
                    break
        literal_names_by_scope[scope] = names
    path_flow_names_by_scope: dict[ast.AST | None, set[str]] = {}
    for node in ast.walk(tree):
        scope = scope_of(node)
        folded = _literal_path_string(node, literal_names_by_scope.get(scope, {}))
        if folded is not None and _protected_path_text(folded):
            path_flow_names_by_scope.setdefault(scope, set()).update(
                item.id for item in ast.walk(node) if isinstance(item, ast.Name))

    def resolve_name(name: str, scope: ast.AST | None) -> tuple[ast.AST | None, bool]:
        current = scope
        while True:
            candidates = by_parent.get((current, name), [])
            if candidates:
                return (candidates[0], False) if len(candidates) == 1 else (None, True)
            if current is None:
                break
            current = function_parent.get(current)
        return None, False

    def resolve_call(call: ast.Call, scope: ast.AST | None,
                     env: dict[str, _PathFact] | None = None) -> tuple[ast.AST | None, bool]:
        if not isinstance(call.func, ast.Name):
            return None, False
        alias = (env or {}).get(call.func.id, _PathFact())
        if alias.callable_target is not None:
            return alias.callable_target, False
        return resolve_name(call.func.id, scope)

    def parameter_nodes(function: ast.AST) -> list[ast.arg]:
        arguments = function.args
        optional = [item for item in (arguments.vararg, arguments.kwarg) if item is not None]
        return [*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs, *optional]

    def bind_call(call: ast.Call, function: ast.AST) -> tuple[dict[str, ast.AST], bool]:
        params = parameter_nodes(function)
        bound: dict[str, ast.AST] = {}
        positional = [*function.args.posonlyargs, *function.args.args]
        ambiguous = False
        extra_positional: list[ast.expr] = []
        for index, actual in enumerate(call.args):
            if index >= len(positional):
                if function.args.vararg is None:
                    ambiguous = True
                else:
                    extra_positional.append(actual.value if isinstance(actual, ast.Starred) else actual)
                continue
            if isinstance(actual, ast.Starred):
                ambiguous = True
                continue
            bound[positional[index].arg] = actual
        if extra_positional and function.args.vararg is not None:
            bound[function.args.vararg.arg] = ast.Tuple(elts=extra_positional, ctx=ast.Load())
        names = {item.arg for item in params}
        extra_keywords: list[ast.expr] = []
        for keyword in call.keywords:
            if keyword.arg is None:
                if function.args.kwarg is None:
                    ambiguous = True
                else:
                    extra_keywords.append(keyword.value)
                continue
            if keyword.arg not in names or keyword.arg in bound:
                if function.args.kwarg is None:
                    ambiguous = True
                else:
                    extra_keywords.append(keyword.value)
                continue
            bound[keyword.arg] = keyword.value
        if extra_keywords and function.args.kwarg is not None:
            bound[function.args.kwarg.arg] = ast.Dict(keys=[None] * len(extra_keywords), values=extra_keywords)
        defaults = [None] * (len(positional) - len(function.args.defaults)) + list(function.args.defaults)
        for parameter, default in zip(positional, defaults):
            if parameter.arg not in bound and default is not None:
                bound[parameter.arg] = default
        for parameter, default in zip(function.args.kwonlyargs, function.args.kw_defaults):
            if parameter.arg not in bound and default is not None:
                bound[parameter.arg] = default
        return bound, ambiguous

    def fact_from_text(value: str | None) -> _PathFact:
        return _PathFact(text=value,
                         protected=value is not None and _protected_path_text(value))

    def component_is_safe(value: str | None) -> bool:
        if value is None or not value or value.startswith(("/", "\\")) or ntpath.splitdrive(value)[0]:
            return False
        return all(part not in ("", "..") for part in value.replace("\\", "/").split("/"))

    def join_facts(left: _PathFact, right: _PathFact) -> _PathFact:
        text = None
        if left.text is not None and right.text is not None:
            text = (right.text if right.text.startswith(("/", "\\")) or ntpath.splitdrive(right.text)[0]
                    else left.text.rstrip("/\\") + "/" + right.text.lstrip("/\\"))
        origin = left.temporary_origin or right.temporary_origin
        contained = (left.temporary_origin and left.contained and component_is_safe(right.text)
                     and not right.temporary_origin)
        return _PathFact(text=text,
                         protected=left.protected or right.protected
                         or (text is not None and _protected_path_text(text)),
                         temporary_origin=origin, contained=contained)

    def bind_facts(call: ast.Call, function: ast.AST,
                   caller_env: dict[str, _PathFact], depth: int,
                   visiting: frozenset[ast.AST]) -> tuple[dict[str, _PathFact], bool]:
        bound_nodes, ambiguous = bind_call(call, function)
        facts = {name: eval_expr(expr, caller_env, scope_of(call), depth + 1, visiting)
                 for name, expr in bound_nodes.items()}
        return facts, ambiguous

    harmless_value_calls = {"str", "repr", "len", "bool", "bytes", "tuple", "list", "dict", "set",
                            "sorted", "min", "max", "sum", "any", "all", "enumerate", "zip", "range",
                            "iter", "next", "print", "format", "hash", "id", "isinstance", "getattr",
                            "hasattr", "compile", "json.dumps", "SystemExit", "RuntimeError", "ValueError",
                            "TypeError", "OSError", "AssertionError", "sha1", "sha256", "sha512", "dirname",
                            "basename", "normpath", "commonpath"}
    harmless_value_methods = {"startswith", "endswith", "split", "rsplit", "replace", "strip", "rstrip",
                              "lstrip", "lower", "upper", "casefold", "encode", "decode", "format",
                              "search", "match", "fullmatch", "find", "count", "get", "items", "keys",
                              "values", "append", "extend", "add", "update", "copy", "join"}
    source_lines = source.splitlines(keepends=True)

    def needs_decoded_flow() -> bool:
        protected_names = {name for name, fact in module_env.items() if fact.protected}
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            target = _reader_target(node)
            if target is not None and any(
                    isinstance(item, ast.Call) and isinstance(item.func, ast.Name) and item.func.id == "chr"
                    for item in ast.walk(target)):
                return True
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                continue
            if _protected_path_text(node.value):
                raw = ast.get_source_segment(source, node) or ""
                if not SPELLINGS.search(raw):
                    return True

        # A path may become sensitive only after finite pieces are joined, e.g.
        # Path("\\x2eplanning") / "phases". Detect the composed value before
        # deciding that the decoded-flow pass is unnecessary.
        for node in ast.walk(tree):
            folded = _literal_path_string(node, literal_names_by_scope.get(scope_of(node), {}))
            raw = ast.get_source_segment(source, node) or ""
            if folded is not None and _protected_path_text(folded) and not SPELLINGS.search(raw):
                return True

        def names_in(node: ast.AST) -> set[str]:
            return {item.id for item in ast.walk(node) if isinstance(item, ast.Name)}

        tainted_names_cache: dict[ast.AST, set[str]] = {}

        def tainted_scope_names(function: ast.AST) -> set[str]:
            if function in tainted_names_cache:
                return tainted_names_cache[function]
            tainted = set(protected_names)
            changed = True
            while changed:
                changed = False
                for statement in direct_scope_nodes(function):
                    if isinstance(statement, (ast.For, ast.AsyncFor)) \
                            and names_in(statement.iter).intersection(tainted):
                        before = len(tainted)
                        tainted.update(_assigned_names(statement.target))
                        changed |= len(tainted) != before
                    if not isinstance(statement, (ast.Assign, ast.AnnAssign)):
                        continue
                    value = statement.value
                    if _has_path_spelling(value, source_lines, module_strings) \
                            or names_in(value).intersection(tainted):
                        targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
                        for target in targets:
                            before = len(tainted)
                            tainted.update(_assigned_names(target))
                            changed |= len(tainted) != before
            tainted_names_cache[function] = tainted
            return tainted

        def carries(node: ast.AST, tainted: set[str]) -> bool:
            return (_has_path_spelling(node, source_lines, module_strings)
                    or bool(names_in(node).intersection(tainted)))

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or _reader_target(node) is None:
                continue
            scope = scope_of(node)
            if scope is not None and (scope.name == "self_test" or scope.name.startswith("self_test_")):
                continue
            tainted = set(protected_names)
            if scope is not None:
                tainted |= tainted_scope_names(scope)
            if carries(_reader_target(node), tainted):
                return True

        def is_path_component(node: ast.AST) -> bool:
            current = node
            while current in parents:
                parent = parents[current]
                if isinstance(parent, ast.BinOp) and isinstance(parent.op, ast.Div) and parent.right is current:
                    return True
                if isinstance(parent, ast.Call):
                    args = list(parent.args)
                    if (isinstance(parent.func, ast.Name) and parent.func.id in
                            {"Path", "PurePath", "PosixPath", "WindowsPath"} and current in args[1:]):
                        return True
                    if (isinstance(parent.func, ast.Attribute) and parent.func.attr == "join"
                            and current in args[1:]):
                        return True
                current = parent
            return False

        def helper_can_read(function: ast.AST, tainted_params: set[str],
                            seen: frozenset[ast.AST] = frozenset()) -> bool:
            if function in seen:
                return bool(tainted_params)
            tainted = tainted_scope_names(function) | tainted_params
            for node in direct_scope_nodes(function):
                if not isinstance(node, ast.Call):
                    continue
                target = _reader_target(node)
                if target is not None and carries(target, tainted):
                    return True
                callee, ambiguous = resolve_call(node, scope_of(node))
                if callee is not None:
                    bound, binding_ambiguous = bind_call(node, callee)
                    if ambiguous or binding_ambiguous:
                        if any(carries(actual, tainted) for actual in bound.values()):
                            return True
                        continue
                    forwarded = {parameter for parameter, actual in bound.items() if carries(actual, tainted)}
                    if forwarded and helper_can_read(callee, forwarded, seen | {function}):
                        return True
                elif any(carries(actual, tainted) for actual in [*node.args, *(item.value for item in node.keywords)]):
                    name = (node.func.id if isinstance(node.func, ast.Name) else
                            node.func.attr if isinstance(node.func, ast.Attribute) else "dynamic")
                    if name not in harmless_value_calls and name not in harmless_value_methods:
                        return True
            return False

        for function in functions:
            nodes = direct_scope_nodes(function)
            parameter_names = {item.arg for item in parameter_nodes(function)}
            reader_uses_parameter = any(isinstance(node, ast.Call) and _reader_target(node) is not None
                                        and bool(names_in(_reader_target(node)).intersection(parameter_names))
                                        for node in nodes)
            for default in [*function.args.defaults, *function.args.kw_defaults]:
                if default is not None and carries(default, protected_names) and reader_uses_parameter:
                    return True
            local_protected = any(isinstance(node, ast.Name) and node.id in protected_names for node in nodes)
            if local_protected:
                for node in nodes:
                    if isinstance(node, ast.Constant) and isinstance(node.value, str):
                        normalized = node.value.replace("\\", "/")
                        if is_path_component(node) and (normalized == ".." or
                                                        (normalized != "/" and
                                                         (normalized.startswith("/")
                                                          or ntpath.splitdrive(node.value)[0]))):
                            return True
                    if isinstance(node, ast.Call):
                        if (isinstance(node.func, ast.Attribute) and node.func.attr == "relpath") or (
                                isinstance(node.func, ast.Attribute) and node.func.attr == "join"
                                and isinstance(node.func.value, ast.Attribute)
                                and node.func.value.attr == "path"):
                            return True
            has_temp_scope = any(isinstance(node, ast.With) and any(
                _is_temporary_directory_context(item.context_expr) for item in node.items) for node in nodes)
            if local_protected and has_temp_scope:
                if any(isinstance(node, (ast.Assign, ast.AnnAssign))
                       and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name)
                       and node.value.func.id == "Path" and node.value.args
                       and isinstance(node.value.args[0], ast.Name) and node.value.args[0].id == "ROOT"
                       and bool(_assigned_names(node.targets[0] if isinstance(node, ast.Assign) else node.target)
                                .intersection({"base", "root", "repo"})) for node in nodes):
                    return True
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            scope = scope_of(node)
            tainted = set(protected_names)
            if scope is not None:
                tainted |= tainted_scope_names(scope)
            if any(carries(actual, tainted) for actual in [*node.args, *(item.value for item in node.keywords)]):
                function, ambiguous = resolve_call(node, scope)
                actuals = [*node.args, *(item.value for item in node.keywords)]
                if function is None:
                    name = (node.func.id if isinstance(node.func, ast.Name) else
                            node.func.attr if isinstance(node.func, ast.Attribute) else "dynamic")
                    if ambiguous or name not in harmless_value_calls | harmless_value_methods:
                        return True
                else:
                    bound, binding_ambiguous = bind_call(node, function)
                    forwarded = {parameter for parameter, actual in bound.items() if carries(actual, tainted)}
                    if binding_ambiguous or (forwarded and helper_can_read(function, forwarded)):
                        return True
        if any(function in path_builders and any(isinstance(node, ast.Call)
                                                 and isinstance(node.func, ast.Attribute)
                                                 and node.func.attr == "relpath"
                                                 for node in direct_scope_nodes(function))
               for function in functions):
            return True
        for function in functions:
            nodes = direct_scope_nodes(function)
            if not any(isinstance(node, ast.With) and any(_is_temporary_directory_context(item.context_expr)
                                                          for item in node.items) for node in nodes):
                continue
            builder_targets = set()
            for node in nodes:
                if isinstance(node, (ast.Assign, ast.AnnAssign)) and isinstance(node.value, ast.Call) \
                        and isinstance(node.value.func, ast.Name) \
                        and any(item.name == node.value.func.id for item in path_builders):
                    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                    builder_targets.update(set().union(*(_assigned_names(target) for target in targets)))
            if builder_targets and any(isinstance(node, ast.Call) and _reader_target(node) is not None
                                       and bool(names_in(_reader_target(node)).intersection(builder_targets))
                                       for node in nodes):
                return True
        return False

    if not needs_decoded_flow():
        return

    analyzed_contexts: set[tuple[object, ...]] = set()
    analyzed_results: dict[tuple[object, ...], _PathFact] = {}
    active_functions: set[ast.AST] = set()
    call_budget = 0

    def eval_expr(node: ast.AST, env: dict[str, _PathFact], scope: ast.AST | None,
                  depth: int, visiting: frozenset[ast.AST]) -> _PathFact:
        if depth > 18:
            return _merge_path_facts(*[env.get(name, module_env.get(name, _PathFact()))
                                       for name in _assigned_names(node)])
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return fact_from_text(node.value)
        if isinstance(node, ast.Name):
            if node.id in env:
                return env[node.id]
            if node.id in module_env:
                return module_env[node.id]
            if node.id in {"Path", "PurePath", "PosixPath", "WindowsPath"}:
                return _PathFact(callable_name=node.id)
            function, ambiguous = resolve_name(node.id, scope)
            if function is not None:
                return _PathFact(callable_target=function)
            if ambiguous:
                return _PathFact()
            return _PathFact()
        if isinstance(node, ast.JoinedStr):
            value = _literal_string(node, {name: fact.text for name, fact in env.items() if fact.text is not None}
                                     | module_strings)
            inherited = _merge_path_facts(*[eval_expr(item.value, env, scope, depth + 1, visiting)
                                            for item in node.values if isinstance(item, ast.FormattedValue)])
            return _PathFact(text=value or inherited.text,
                             protected=inherited.protected or (value is not None and _protected_path_text(value)),
                             temporary_origin=inherited.temporary_origin,
                             contained=inherited.contained)
        if isinstance(node, ast.BinOp):
            left = eval_expr(node.left, env, scope, depth + 1, visiting)
            right = eval_expr(node.right, env, scope, depth + 1, visiting)
            left_text = left.text
            right_text = right.text
            if isinstance(node.op, ast.Add):
                text = (left_text + right_text) if left_text is not None and right_text is not None else None
                return _PathFact(text=text,
                                 protected=left.protected or right.protected
                                 or (text is not None and _protected_path_text(text)),
                                 temporary_origin=left.temporary_origin or right.temporary_origin,
                                 contained=(left.contained and right.contained
                                            if left.temporary_origin or right.temporary_origin else False))
            if isinstance(node.op, ast.Div):
                return join_facts(left, right)
            return _merge_path_facts(left, right)
        if isinstance(node, ast.Subscript):
            base = eval_expr(node.value, env, scope, depth + 1, visiting)
            literal = _literal_string(node, {name: fact.text for name, fact in env.items() if fact.text is not None}
                                      | module_strings)
            if literal is not None:
                return fact_from_text(literal)
            return base
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "chr":
                literal = _literal_string(
                    node, {name: fact.text for name, fact in env.items() if fact.text is not None} | module_strings)
                if literal is not None:
                    return fact_from_text(literal)
                return _PathFact(protected=True)
            reader_target = _reader_target(node)
            if reader_target is not None:
                target_fact = eval_expr(reader_target, env, scope, depth + 1, visiting)
                if target_fact.protected:
                    owner = scope.name if scope is not None else "module"
                    if target_fact.temporary_origin and not target_fact.contained:
                        raise LintError("REJECT temporary-path-containment: %s has an unproven temporary path component"
                                        % owner)
                    if not target_fact.temporary_origin:
                        raise LintError("REJECT live-phase-path-reader: %s reads a protected path outside a verified fixture root"
                                        % owner)
            if ((isinstance(node.func, ast.Name) and node.func.id in
                 {"Path", "PurePath", "PosixPath", "WindowsPath"})
                    or (isinstance(node.func, ast.Attribute) and node.func.attr in
                        {"Path", "PurePath", "PosixPath", "WindowsPath"})) and node.args:
                result = eval_expr(node.args[0], env, scope, depth + 1, visiting)
                for component in node.args[1:]:
                    result = join_facts(result, eval_expr(component, env, scope, depth + 1, visiting))
                return result
            if isinstance(node.func, ast.Name):
                constructor = env.get(node.func.id, _PathFact()).callable_name
                if constructor in {"Path", "PurePath", "PosixPath", "WindowsPath"} and node.args:
                    result = eval_expr(node.args[0], env, scope, depth + 1, visiting)
                    for component in node.args[1:]:
                        result = join_facts(result, eval_expr(component, env, scope, depth + 1, visiting))
                    return result
            if (isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Attribute)
                    and isinstance(node.func.value.value, ast.Name) and node.func.value.value.id == "os"
                    and node.func.value.attr == "path" and node.func.attr == "join" and node.args):
                result = eval_expr(node.args[0], env, scope, depth + 1, visiting)
                for component in node.args[1:]:
                    result = join_facts(result, eval_expr(component, env, scope, depth + 1, visiting))
                return result
            if isinstance(node.func, ast.Attribute) and node.func.attr == "joinpath" and node.args:
                result = eval_expr(node.func.value, env, scope, depth + 1, visiting)
                for component in node.args:
                    result = join_facts(result, eval_expr(component, env, scope, depth + 1, visiting))
                return result
            if (isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Attribute)
                    and isinstance(node.func.value.value, ast.Name) and node.func.value.value.id == "os"
                    and node.func.value.attr == "path" and node.func.attr == "relpath"):
                facts = [eval_expr(item, env, scope, depth + 1, visiting) for item in node.args]
                return _PathFact(protected=any(item.protected for item in facts),
                                 temporary_origin=any(item.temporary_origin for item in facts),
                                 contained=False)
            if isinstance(node.func, ast.Attribute):
                eval_expr(node.func.value, env, scope, depth + 1, visiting)
            function, ambiguous = resolve_call(node, scope, env)
            actual_facts = [eval_expr(item, env, scope, depth + 1, visiting) for item in node.args]
            actual_facts += [eval_expr(item.value, env, scope, depth + 1, visiting) for item in node.keywords]
            if function is not None:
                # Only the structurally verified immutable Git-object adapter is allowed to
                # receive a protected path as a Git revision/tree operand.
                if function in trusted_git_adapters:
                    return _merge_path_facts(*actual_facts)
                closure_has_path = any(name in function_used_names.get(function, set())
                                       and (item.protected or item.temporary_origin)
                                       for name, item in env.items())
                if any(item.protected or item.temporary_origin for item in actual_facts) or (
                        function_parent[function] is not None and closure_has_path):
                    nonlocal call_budget
                    call_budget += 1
                    if call_budget > 4000:
                        raise LintError("REJECT live-phase-path-flow: bounded helper analysis exhausted")
                    facts, binding_ambiguous = bind_facts(node, function, env, depth, visiting)
                    if binding_ambiguous or ambiguous:
                        if any(item.protected for item in actual_facts):
                            detail = "helper resolution" if ambiguous else "argument binding"
                            raise LintError("REJECT live-phase-path-flow: ambiguous protected-path %s at line %d"
                                            % (detail, node.lineno))
                        return _PathFact(temporary_origin=any(item.temporary_origin for item in actual_facts),
                                         contained=False)
                    if function in visiting:
                        if any(item.protected or item.temporary_origin for item in facts.values()):
                            raise LintError("REJECT live-phase-path-flow: recursive protected-path helper")
                        return _PathFact(temporary_origin=any(item.temporary_origin for item in facts.values()),
                                         contained=False)
                    closure_state = tuple(sorted((name, env[name].text, env[name].protected,
                                                  env[name].temporary_origin, env[name].contained)
                                                 for name in function_used_names.get(function, set())
                                                 if name in env))
                    key = (id(function), tuple(sorted((name, fact.text, fact.protected,
                                                       fact.temporary_origin, fact.contained)
                                                      for name, fact in facts.items())), closure_state)
                    if key in analyzed_contexts:
                        return analyzed_results.get(key, _PathFact())
                    analyzed_contexts.add(key)
                    try:
                        returned = analyze_function(function, facts, env, depth + 1, visiting | {function})
                    except LintError as error:
                        raise LintError("%s via helper call at line %d" % (error, node.lineno)) from None
                    analyzed_results[key] = returned
                    return returned
            if ambiguous and any(item.protected for item in actual_facts):
                raise LintError("REJECT live-phase-path-flow: ambiguous protected-path helper binding")
            if any(item.protected for item in actual_facts):
                if isinstance(node.func, ast.Name):
                    callee_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    callee_name = node.func.attr
                else:
                    callee_name = "dynamic"
                qualified = ("json.dumps" if isinstance(node.func, ast.Attribute)
                             and isinstance(node.func.value, ast.Name) and node.func.value.id == "json"
                             else callee_name)
                if qualified not in harmless_value_calls and callee_name not in harmless_value_methods:
                    raise LintError("REJECT live-phase-path-flow: unclassified protected-path helper %s at line %d"
                                    % (qualified, node.lineno))
            elif any(item.temporary_origin for item in actual_facts):
                if isinstance(node.func, ast.Name):
                    callee_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    callee_name = node.func.attr
                else:
                    callee_name = "dynamic"
                if callee_name not in harmless_value_calls and callee_name not in harmless_value_methods:
                    raise LintError("REJECT temporary-path-containment: unclassified temporary-path helper %s at line %d"
                                    % (callee_name, node.lineno))
            return _merge_path_facts(*actual_facts)
        if isinstance(node, ast.Attribute):
            return eval_expr(node.value, env, scope, depth + 1, visiting)
        if isinstance(node, ast.UnaryOp):
            return eval_expr(node.operand, env, scope, depth + 1, visiting)
        return _merge_path_facts(*[eval_expr(item, env, scope, depth + 1, visiting)
                                   for item in ast.iter_child_nodes(node)])

    def merge_env(target: dict[str, _PathFact], branches: list[dict[str, _PathFact]]) -> None:
        names = set().union(*(branch.keys() for branch in branches))
        for name in names:
            values = [branch.get(name, target.get(name, module_env.get(name, _PathFact()))) for branch in branches]
            text = values[0].text if values and all(item.text == values[0].text for item in values) else None
            origin = any(item.temporary_origin for item in values)
            target[name] = _PathFact(text=text,
                                     protected=any(item.protected for item in values),
                                     temporary_origin=origin,
                                     contained=origin and all(not item.temporary_origin or item.contained
                                                              for item in values))

    path_builder_names = {function.name for function in path_builders}

    def statement_relevant(statement: ast.stmt, env: dict[str, _PathFact], function: ast.AST | None) -> bool:
        if function in path_builders:
            return True
        if isinstance(statement, (ast.Assign, ast.AnnAssign)):
            targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
            assigned = set().union(*(_assigned_names(target) for target in targets))
            if assigned.intersection(path_flow_names_by_scope.get(function, set())):
                return True
        literal_names = {name: fact.text for name, fact in {**module_env, **env}.items()
                         if fact.text is not None}
        if isinstance(statement, (ast.Assign, ast.AnnAssign)):
            value = statement.value
            if isinstance(value, ast.Name) and value.id in {"Path", "PurePath", "PosixPath", "WindowsPath"}:
                return True
            if isinstance(value, ast.Name) and resolve_name(value.id, function)[0] is not None:
                return True
        for node in ast.walk(statement):
            folded_path = _literal_path_string(node, literal_names)
            if folded_path is not None and _protected_path_text(folded_path):
                return True
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and _protected_path_text(node.value):
                return True
            if isinstance(node, ast.Name):
                fact = env.get(node.id, module_env.get(node.id, _PathFact()))
                if fact.protected or fact.temporary_origin:
                    return True
            if isinstance(node, ast.Call):
                if _reader_target(node) is not None:
                    return True
                if isinstance(node.func, ast.Name) and node.func.id in path_builder_names:
                    return True
        return False

    def process_block(statements: list[ast.stmt], env: dict[str, _PathFact], function: ast.AST | None,
                      depth: int, visiting: frozenset[ast.AST], returns: list[_PathFact]) -> None:
        scope = function
        for statement in statements:
            if not statement_relevant(statement, env, function):
                continue
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            if isinstance(statement, ast.Assign):
                fact = eval_expr(statement.value, env, scope, depth + 1, visiting)
                for target in statement.targets:
                    for name in _assigned_names(target):
                        old = env.get(name, _PathFact())
                        if old.temporary_origin and not fact.temporary_origin:
                            fact = _PathFact(text=fact.text, protected=fact.protected,
                                             temporary_origin=True, contained=False)
                        env[name] = fact
            elif isinstance(statement, ast.AnnAssign) and statement.value is not None:
                fact = eval_expr(statement.value, env, scope, depth + 1, visiting)
                for name in _assigned_names(statement.target):
                    old = env.get(name, _PathFact())
                    env[name] = (_PathFact(text=fact.text, protected=fact.protected,
                                           temporary_origin=True, contained=False)
                                 if old.temporary_origin and not fact.temporary_origin else fact)
            elif isinstance(statement, (ast.With, ast.AsyncWith)):
                for item in statement.items:
                    fact = (_PathFact(temporary_origin=True, contained=True)
                            if _is_temporary_directory_context(item.context_expr) else
                            eval_expr(item.context_expr, env, scope, depth + 1, visiting))
                    if item.optional_vars is not None:
                        for name in _assigned_names(item.optional_vars):
                            env[name] = fact
                process_block(statement.body, env, function, depth + 1, visiting, returns)
            elif isinstance(statement, ast.If):
                eval_expr(statement.test, env, scope, depth + 1, visiting)
                branches = []
                for body in (statement.body, statement.orelse):
                    branch = dict(env)
                    process_block(body, branch, function, depth + 1, visiting, returns)
                    branches.append(branch)
                merge_env(env, branches)
            elif isinstance(statement, (ast.For, ast.AsyncFor, ast.While)):
                test = statement.iter if isinstance(statement, (ast.For, ast.AsyncFor)) else statement.test
                iterable_fact = eval_expr(test, env, scope, depth + 1, visiting)
                branch = dict(env)
                if isinstance(statement, (ast.For, ast.AsyncFor)):
                    for name in _assigned_names(statement.target):
                        branch[name] = iterable_fact
                process_block(statement.body, branch, function, depth + 1, visiting, returns)
                merge_env(env, [env, branch])
                if statement.orelse:
                    process_block(statement.orelse, env, function, depth + 1, visiting, returns)
            elif isinstance(statement, (ast.Try, getattr(ast, "TryStar", ast.Try))):
                branch = dict(env)
                process_block(statement.body, branch, function, depth + 1, visiting, returns)
                branches = [branch]
                for handler in statement.handlers:
                    handler_env = dict(env)
                    process_block(handler.body, handler_env, function, depth + 1, visiting, returns)
                    branches.append(handler_env)
                merge_env(env, branches)
                process_block(statement.orelse, env, function, depth + 1, visiting, returns)
                process_block(statement.finalbody, env, function, depth + 1, visiting, returns)
            elif isinstance(statement, ast.Return):
                fact = eval_expr(statement.value, env, scope, depth + 1, visiting) if statement.value else _PathFact()
                returns.append(fact)
            elif isinstance(statement, ast.Expr):
                eval_expr(statement.value, env, scope, depth + 1, visiting)
            else:
                # Inspect expressions embedded in declarations/assertions without interpreting code.
                for child in ast.iter_child_nodes(statement):
                    if isinstance(child, ast.expr):
                        eval_expr(child, env, scope, depth + 1, visiting)

    def analyze_function(function: ast.AST, arguments: dict[str, _PathFact],
                         closure: dict[str, _PathFact], depth: int,
                         visiting: frozenset[ast.AST]) -> _PathFact:
        if function in active_functions and any(item.protected for item in arguments.values()):
            raise LintError("REJECT live-phase-path-flow: recursive protected-path helper")
        active_functions.add(function)
        env = dict(module_env)
        env.update(closure)
        env.update(arguments)
        for name in roots_by_function.get(function.name, set()):
            env.setdefault(name, _PathFact(temporary_origin=True, contained=True))
        positional = [*function.args.posonlyargs, *function.args.args]
        defaults = [None] * (len(positional) - len(function.args.defaults)) + list(function.args.defaults)
        for parameter, default in zip(positional, defaults):
            if parameter.arg not in arguments and default is not None:
                env[parameter.arg] = eval_expr(default, env, function, depth + 1, visiting)
        for parameter, default in zip(function.args.kwonlyargs, function.args.kw_defaults):
            if parameter.arg not in arguments and default is not None:
                env[parameter.arg] = eval_expr(default, env, function, depth + 1, visiting)
        for parameter in parameter_nodes(function):
            env.setdefault(parameter.arg, _PathFact())
        returns: list[_PathFact] = []

        # Reader checks run against the same evolving bindings used for helper return analysis.
        process_block(function.body, env, function, depth, visiting, returns)
        # A helper's own component must be proven when its incoming root is proven. An
        # unresolved caller component remains unknown (fixture labels may come from a bounded
        # loop) and is not promoted into proof of either escape or safety.
        if function in path_builders and any(fact.temporary_origin and fact.contained
                                             for fact in arguments.values()):
            for result in returns:
                if result.temporary_origin and not result.contained:
                    facts = [(name, item.text, item.temporary_origin, item.contained)
                             for name, item in arguments.items()]
                    raise LintError("REJECT temporary-path-containment: %s returns an escaped temporary path (text=%r args=%r)"
                                    % (function.name, result.text, facts))
        active_functions.discard(function)
        return _merge_path_facts(*returns) if returns else _PathFact()

    # Run each declared function once as an entry point; relevant helper calls are followed with
    # their local argument and closure facts. This catches direct aliases plus positional,
    # keyword, default and nested helper flow while leaving unrelated functions as unknown.
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or scope_of(node) is not None:
            continue
        actuals = [eval_expr(item, module_env, None, 0, frozenset()) for item in node.args]
        actuals.extend(eval_expr(item.value, module_env, None, 0, frozenset()) for item in node.keywords)
        if _reader_target(node) is not None or any(item.protected or item.temporary_origin for item in actuals):
            eval_expr(node, module_env, None, 0, frozenset())

    for function in functions:
        if function_parent[function] is not None:
            continue
        if function.name == "self_test" or function.name.startswith("self_test_"):
            # These large test drivers are already covered by the lexical/fixture-root pass.
            # Their newly appended causal fixtures are separate injected_* functions below.
            continue
        body_nodes = direct_scope_nodes(function)
        positional = [*function.args.posonlyargs, *function.args.args]
        symbolic_root_builder = False
        if function in path_builders and positional and positional[0].arg == "root":
            other_parameters = {item.arg for item in parameter_nodes(function)} - {positional[0].arg}
            dynamic_return_component = any(isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div)
                                           and any(isinstance(child, ast.Name) and child.id in other_parameters
                                                   for child in ast.walk(node.right))
                                           for node in body_nodes)
            symbolic_root_builder = not dynamic_return_component
        relevant = (function.name in roots_by_function
                    or symbolic_root_builder
                    or any(isinstance(node, ast.Call) and _reader_target(node) is not None
                           and any(isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
                                   and child.func.id == "chr"
                                   for child in ast.walk(_reader_target(node)))
                           for node in body_nodes)
                    or any((folded := _literal_path_string(node,
                                                           literal_names_by_scope.get(function, {}))) is not None
                           and _protected_path_text(folded) for node in body_nodes)
                    or any(isinstance(node, ast.Name) and module_env.get(node.id, _PathFact()).protected
                           for node in body_nodes)
                    or any(isinstance(node, ast.Constant) and isinstance(node.value, str)
                           and _protected_path_text(node.value) for node in body_nodes)
                    or (any(isinstance(node, ast.With) and any(_is_temporary_directory_context(item.context_expr)
                                                              for item in node.items) for node in body_nodes)
                        and any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                                and any(builder.name == node.func.id for builder in path_builders)
                                for node in body_nodes)))
        if not relevant:
            continue
        seed = {name: _PathFact(temporary_origin=True, contained=True)
                for name in roots_by_function.get(function.name, set())}
        if symbolic_root_builder and positional:
            analyze_function(function, {positional[0].arg: _PathFact(temporary_origin=True, contained=True)},
                             seed, 0, frozenset({function}))
            continue
        analyze_function(function, {}, seed, 0, frozenset({function}))


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
    _validate_decoded_path_flow(source, tree, roots)
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

    need(_literal_string(ast.parse("chr(46)", mode="eval").body) == "."
         and all(_literal_string(ast.parse(expression, mode="eval").body) is None for expression in (
             "chr(True)", "chr(46, 47)", "chr(-1)", "chr(0x110000)", "chr(codepoint)",
             "chr(46, placeholder=0)")),
         "chr literal folding accepted an invalid or nonliteral form")
    controls += 1

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

    def validate_decoded_flow(candidate: str) -> None:
        try:
            tree = ast.parse(candidate, filename=PLANNING_HYGIENE_FILE)
        except (SyntaxError, IndentationError) as error:
            raise LintError("REJECT planning-path-parse: %s" % error.__class__.__name__) from None
        roots = _fixture_root_contract(tree)
        _validate_decoded_path_flow(candidate, tree, roots)

    def expect_flow_rejected(label: str, candidate: str, reason: str, same_count: bool = False) -> None:
        nonlocal controls
        if same_count:
            need(len(list(SPELLINGS.finditer(candidate))) == original_lexical_count,
                 "%s: mutation changed the lexical hit count" % label)
        try:
            validate_decoded_flow(candidate)
        except LintError as error:
            need(str(error).startswith(reason), "%s: refused for %r instead of %s"
                 % (label, str(error), reason))
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

    contained_helper = source + r'''
def injected_fixture_builder(root, name):
    child = root / name
    return child / "probe.md"

def injected_contained_fixture_reader():
    with tempfile.TemporaryDirectory() as scratch:
        base = Path(scratch)
        path = injected_fixture_builder(base, "sample")
        return path.read_text(encoding="utf-8")
'''
    try:
        validate_decoded_flow(contained_helper)
    except LintError as error:
        raise LintError("contained fixture helper positive: refused: %s" % error) from None
    controls += 1

    reader_mutations = (
        ("chr-built escaped path reader",
         r'''
def injected_chr_reader():
    return Path(chr(46) + "planning/phases/private.md").read_text(encoding="utf-8")
'''),
        ("unresolved chr path reader",
         r'''
def injected_unresolved_chr_reader(codepoint):
    return Path(chr(codepoint) + "planning/phases/private.md").read_text(encoding="utf-8")
'''),
        ("shadowed chr path reader",
         r'''
def chr(codepoint):
    return "."

def injected_shadowed_chr_reader():
    return Path(chr(46) + "planning/phases/private.md").read_text(encoding="utf-8")
'''),
        ("escaped decoded path reader",
         r'''
def injected_escaped_reader():
    return Path("\x2eplanning/phases/private.md").read_text(encoding="utf-8")
'''),
        ("unicode escaped path reader",
         r'''
def injected_unicode_escaped_reader():
    return Path("\u002eplanning/phases/private.md").read_bytes()
'''),
        ("adjacent escaped path fragments",
         r'''
def injected_adjacent_reader():
    return Path("\x2e" "planning/" "phases/private.md").read_text(encoding="utf-8")
'''),
        ("escaped path fragments joined with Path division",
         r'''
def injected_fragment_join_reader():
    return (Path("\x2eplanning") / "phases/private.md").read_text(encoding="utf-8")
'''),
        ("escaped path fragments joined by constructor",
         r'''
def injected_fragment_constructor_reader():
    return Path("\x2eplanning", "phases/private.md").read_text(encoding="utf-8")
'''),
        ("escaped path fragments through a local alias",
         r'''
def injected_fragment_alias_reader():
    fragment = "\x2eplanning"
    return (Path(fragment) / "phases/private.md").read_text(encoding="utf-8")
'''),
        ("PHASES_AT_REV alias reader",
         "\ndef injected_alias_reader():\n    alias = PHASES_AT_REV\n    return Path(alias).read_text(encoding=\"utf-8\")\n"),
        ("path through positional and keyword helpers",
         r'''
def injected_helper_reader(path):
    return Path(path).read_text(encoding="utf-8")

def injected_helper_forwarder(path):
    return injected_helper_reader(path=path)

def injected_helper_caller():
    alias = PHASES_AT_REV
    return injected_helper_forwarder(alias)
'''),
        ("default helper argument reader",
         r'''
def injected_default_reader(path=PHASES_AT_REV):
    return Path(path).read_bytes()

def injected_default_caller():
    return injected_default_reader()
'''),
        ("keyword open helper reader",
         r'''
def injected_open_helper(path):
    return open(path, encoding="utf-8").read()

def injected_open_caller():
    return injected_open_helper(path=PHASES_AT_REV)
'''),
        ("nested traversal helper reader",
         r'''
def injected_traversal_helper(path):
    return Path(path).rglob("*")

def injected_traversal_caller():
    return injected_traversal_helper(PHASES_AT_REV)
'''),
        ("aliased helper reader",
         r'''
def injected_alias_reader(path):
    return Path(path).read_text(encoding="utf-8")

def injected_alias_caller():
    reader = injected_alias_reader
    return reader(PHASES_AT_REV)
'''),
        ("recursive protected helper",
         r'''
def injected_recursive_reader(path):
    if path:
        return injected_recursive_reader(path)
    return Path(path).read_text(encoding="utf-8")

def injected_recursive_caller():
    return injected_recursive_reader(PHASES_AT_REV)
'''),
        ("approved path passed to open",
         "\ndef injected_open_reader():\n    return open(V04_GAP_REPORT_PATH, encoding=\"utf-8\").read()\n"),
        ("approved path passed to read_text",
         "\ndef injected_text_reader():\n    return Path(V04_GAP_REPORT_PATH).read_text(encoding=\"utf-8\")\n"),
        ("approved path passed to read_bytes",
         "\ndef injected_bytes_reader():\n    return Path(V04_GAP_REPORT_PATH).read_bytes()\n"),
        ("approved path passed to traversal",
         "\ndef injected_tree_reader():\n    return Path(V04_GAP_SOURCE_PATHS[3]).rglob(\"*\")\n"),
        ("parent component escapes temporary root",
         r'''
def injected_parent_escape_reader():
    with tempfile.TemporaryDirectory() as scratch:
        base = Path(scratch)
        repo = base / "rev-repo"
        escaped = repo / ".." / PHASES_AT_REV
        return escaped.read_text(encoding="utf-8")
'''),
        ("dynamic component escapes temporary root",
         r'''
def injected_dynamic_escape_reader():
    with tempfile.TemporaryDirectory() as scratch:
        base = Path(scratch)
        repo = base / "rev-repo"
        escaped = repo / os.path.relpath(ROOT, repo) / PHASES_AT_REV
        return escaped.read_text(encoding="utf-8")
'''),
        ("absolute component escapes temporary root",
         r'''
def injected_absolute_escape_reader():
    with tempfile.TemporaryDirectory() as scratch:
        base = Path(scratch)
        escaped = base / Path("/outside") / PHASES_AT_REV
        return escaped.read_text(encoding="utf-8")
'''),
        ("absolute Path constructor escapes temporary root",
         r'''
def injected_absolute_constructor_escape_reader():
    with tempfile.TemporaryDirectory() as scratch:
        base = Path(scratch)
        escaped = Path(base, "/outside", PHASES_AT_REV)
        return escaped.read_text(encoding="utf-8")
'''),
        ("dynamic join escapes temporary root",
         r'''
def injected_dynamic_join_escape_reader():
    with tempfile.TemporaryDirectory() as scratch:
        base = Path(scratch)
        repo = base / "rev-repo"
        escaped = os.path.join(repo, os.path.relpath(ROOT, repo), PHASES_AT_REV)
        return Path(escaped).read_text(encoding="utf-8")
'''),
        ("relpath escapes temporary root",
         r'''
def injected_relpath_escape_reader():
    with tempfile.TemporaryDirectory() as scratch:
        repo = Path(scratch)
        escaped = Path(os.path.relpath(ROOT / PHASES_AT_REV, repo))
        return escaped.read_text(encoding="utf-8")
'''),
        ("aliased Path constructor escapes temporary root",
         r'''
def injected_aliased_path_escape_reader():
    with tempfile.TemporaryDirectory() as scratch:
        base = Path(scratch)
        path_factory = Path
        escaped = path_factory(base, "/outside", PHASES_AT_REV)
        return escaped.read_text(encoding="utf-8")
'''),
        ("temporary root rebinding",
         r'''
def injected_rebound_root_reader():
    with tempfile.TemporaryDirectory() as scratch:
        base = Path(scratch)
        base = Path(ROOT)
        return (base / PHASES_AT_REV).read_text(encoding="utf-8")
'''),
    )
    for label, addition in reader_mutations:
        if "temporary root" in label or "rebinding" in label:
            reason = "REJECT temporary-path-containment"
        elif "recursive protected helper" in label:
            reason = "REJECT live-phase-path-flow"
        else:
            reason = "REJECT live-phase-path-reader"
        expect_flow_rejected(label, source + addition, reason, same_count=True)

    git_run_line = ('    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, '
                     'check=False, env=env, timeout=60)')
    need(git_run_line in source, "git_run adapter mutation did not find its approved body")
    git_run_mutant = source.replace(git_run_line,
                                    "    (repo / args[-1]).iterdir()\n" + git_run_line, 1)
    expect_flow_rejected("git_run body traversal mutation", git_run_mutant,
                         "REJECT planning-path-git-adapter", same_count=True)
    git_run_definition = "def git_run(repo: Path, *args: str) -> subprocess.CompletedProcess[bytes]:"
    need(git_run_definition in source, "git_run decorator mutation did not find its approved definition")
    git_run_decorator_mutant = source.replace(git_run_definition,
                                              "@injected_wrapper\n" + git_run_definition, 1)
    expect_flow_rejected("git_run wrapper mutation", git_run_decorator_mutant,
                         "REJECT planning-path-git-adapter", same_count=True)

    module_reader = source + r'''
def injected_module_reader(path):
    return Path(path).read_text(encoding="utf-8")

injected_module_reader(PHASES_AT_REV)
'''
    expect_flow_rejected("module-scope protected helper flow", module_reader,
                         "REJECT live-phase-path-reader", same_count=True)

    module_container_reader = source + r'''
PATH_ALIAS = V04_GAP_SOURCE_PATHS[3]

def injected_module_container_reader(path):
    return Path(path).read_text(encoding="utf-8")

def injected_module_container_caller():
    return injected_module_container_reader(PATH_ALIAS)
'''
    expect_flow_rejected("module container subscript helper flow", module_container_reader,
                         "REJECT live-phase-path-reader", same_count=True)

    module_container_loop = source + r'''
def injected_module_container_loop_reader():
    for path in V04_GAP_SOURCE_PATHS:
        Path(path).read_text(encoding="utf-8")
'''
    expect_flow_rejected("module container loop reader", module_container_loop,
                         "REJECT live-phase-path-reader", same_count=True)

    escaped_helper_return = source.replace(
        'phases = root / "phases"',
        'phases = root / os.path.relpath(ROOT, root) / "phases"', 1)
    need(escaped_helper_return != source, "temporary helper-return mutation did not find its source site")
    expect_flow_rejected("temporary helper return escapes root", escaped_helper_return,
                         "REJECT temporary-path-containment", same_count=True)
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
