#!/usr/bin/env python3
"""TUNE-04 per-test TIMEOUT ratchet over the real ctest json-v1 inventory (Phase 16, D-18, T-16-08).

Contract:

* ``--build-dir DIR`` runs ``ctest --test-dir DIR --show-only=json-v1`` and reads every test's TIMEOUT
  property. The base budget is 60 s: three times that is 180 s, inside the 300 s hosted sanitizer budget
  (LESSONS GB-CI-004). A test with no TIMEOUT property keeps CTest's 1500 s default, so it counts as over
  budget even when an allowlist row names it. tests/CMakeLists.txt and tests/player/CMakeLists.txt give
  every unset test an explicit base TIMEOUT, so a test registered outside the swept scopes fails here.
* A sanitizer build (GABBABOY_ENABLE_SANITIZERS=ON in CMakeCache.txt) reports TIMEOUTs scaled by 3; the
  checker divides them back so one allowlist serves both builds.
* tests/ci/test-budget-allowlist holds one row per over-budget test: name, ceiling seconds, expires as a
  project minor such as 0.4, ref and shrink trigger, tab-separated. A test above its ceiling fails, a row
  that names an unregistered test is stale, and a row whose expires minor is at or below the project
  version has expired. Rows naming player_* tests are not judged stale when the build has
  GABBABOY_BUILD_PLAYER off; they are counted as player_rows_skipped.
* ``--base REV`` also reads the allowlist at REV (absent there means first seeding), rejects a raised
  ceiling, and resolves every row's ref at REV only: a LESSONS heading token, a DECISIONS D-NNN id or a
  plan id whose PLAN.md path exists at REV. A ref added only in the head commit does not resolve, so a PR
  cannot certify its own row. An unreadable REV fails closed. Without --base refs are checked for syntax.
* The success line prints tests=N once; the CTest pins a floor on N. A non-gating ``slowest:`` block lists
  the ten largest budgets. The CGB GB-CI-007 output parser is not extended.

Run with ``--self-test`` to exercise every rule on fixture inventories and a fixture git repository.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

if not __debug__ or sys.flags.optimize:
    raise SystemExit("verify-test-budget must not run with python -O")

ROOT = Path(__file__).resolve().parents[2]
ALLOWLIST_REL = "tests/ci/test-budget-allowlist"
BASE_LIMIT_SECONDS = 60
SANITIZER_SCALE = 3
SLOWEST_COUNT = 10

LESSON_REF = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-[0-9]{3}$")
DECISION_REF = re.compile(r"^D-[0-9]{3}$")
PLAN_REF = re.compile(r"^[0-9]+(?:\.[0-9]+)*-[0-9]{2,}$")
EXPIRES = re.compile(r"^([0-9]+)\.([0-9]+)$")


@dataclass(frozen=True)
class Row:
    name: str
    ceiling: int
    expires: tuple[int, int]
    ref: str
    shrink: str


class BudgetError(Exception):
    """A usage or environment failure that is not a per-test finding."""


def parse_allowlist(text: str, findings: list[str]) -> dict[str, Row]:
    rows: dict[str, Row] = {}
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) != 5 or not all(f.strip() for f in fields):
            findings.append(f"REJECT malformed-row: line {number} needs name, ceiling, expires, ref, shrink trigger")
            continue
        name, ceiling, expires, ref, shrink = (f.strip() for f in fields)
        match = EXPIRES.match(expires)
        if not ceiling.isdigit() or match is None or int(ceiling) <= BASE_LIMIT_SECONDS:
            findings.append(f"REJECT malformed-row: line {number} ({name}) needs an integer ceiling above "
                            f"{BASE_LIMIT_SECONDS} and expires like 0.4")
            continue
        if not (LESSON_REF.match(ref) or DECISION_REF.match(ref) or PLAN_REF.match(ref)):
            findings.append(f"REJECT ref-unresolved: line {number} ({name}) ref '{ref}' is not a LESSONS id, "
                            "DECISIONS id or plan id")
            continue
        if name in rows:
            findings.append(f"REJECT duplicate-row: {name}")
            continue
        rows[name] = Row(name, int(ceiling), (int(match.group(1)), int(match.group(2))), ref, shrink)
    return rows


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_SYSTEM"] = os.devnull
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                          env=env, check=False)


class BaseView:
    """Point-in-time facts read from one commit, never from the working tree."""

    def __init__(self, repo: Path, rev: str) -> None:
        self.repo = repo
        self.rev = rev
        verify = git(repo, "rev-parse", "--verify", "--quiet", f"{rev}^{{commit}}")
        if verify.returncode != 0:
            raise BudgetError(f"REJECT base-unreadable: {rev} is not a commit in {repo}")
        self._lessons: str | None = None
        self._decisions: str | None = None
        self._plan_paths: set[str] | None = None

    def show(self, path: str) -> str | None:
        exists = git(self.repo, "cat-file", "-e", f"{self.rev}:{path}")
        if exists.returncode != 0:
            return None
        shown = git(self.repo, "show", f"{self.rev}:{path}")
        if shown.returncode != 0:
            raise BudgetError(f"REJECT base-unreadable: git show {self.rev}:{path} failed")
        return shown.stdout

    def allowlist(self) -> str | None:
        return self.show(ALLOWLIST_REL)

    def resolves(self, ref: str) -> bool:
        if DECISION_REF.match(ref):
            if self._decisions is None:
                self._decisions = self.show(".planning/context/DECISIONS.md") or ""
            return re.search(rf"^\|\s*{re.escape(ref)}\s*\|", self._decisions, re.MULTILINE) is not None
        if PLAN_REF.match(ref):
            if self._plan_paths is None:
                listing = git(self.repo, "ls-tree", "-r", "--name-only", self.rev, ".planning")
                if listing.returncode != 0:
                    raise BudgetError(f"REJECT base-unreadable: git ls-tree {self.rev} failed")
                self._plan_paths = set(listing.stdout.splitlines())
            suffix = f"/{ref}-PLAN.md"
            return any(p.endswith(suffix) for p in self._plan_paths)
        if self._lessons is None:
            self._lessons = self.show(".planning/context/LESSONS.md") or ""
        return re.search(rf"^### {re.escape(ref)} /", self._lessons, re.MULTILINE) is not None


def evaluate(tests: dict[str, float | None], rows: dict[str, Row], *, player_on: bool,
             project_minor: tuple[int, int], base: BaseView | None,
             base_rows: dict[str, Row] | None) -> tuple[list[str], int]:
    """Return (findings, player_rows_skipped). ``tests`` maps name to effective base TIMEOUT or None."""
    findings: list[str] = []
    skipped = 0
    for name in sorted(tests):
        timeout = tests[name]
        row = rows.get(name)
        if timeout is None:
            findings.append(f"REJECT over-budget: {name} has no TIMEOUT property (CTest default 1500 s)")
        elif row is None:
            if timeout > BASE_LIMIT_SECONDS:
                findings.append(f"REJECT over-budget: {name} TIMEOUT {timeout:g} s exceeds {BASE_LIMIT_SECONDS} s "
                                "and has no allowlist row")
        elif timeout > row.ceiling:
            findings.append(f"REJECT over-ceiling: {name} TIMEOUT {timeout:g} s exceeds its ceiling {row.ceiling} s")
    for name, row in sorted(rows.items()):
        if name not in tests:
            if name.startswith("player_") and not player_on:
                skipped += 1
            else:
                findings.append(f"REJECT stale-row: {name} is not a registered test")
        if row.expires <= project_minor:
            findings.append(f"REJECT row-expired: {name} expires {row.expires[0]}.{row.expires[1]} at or below "
                            f"project {project_minor[0]}.{project_minor[1]}")
        if base is not None and not base.resolves(row.ref):
            findings.append(f"REJECT ref-unresolved: {name} ref {row.ref} does not resolve at {base.rev}")
        if base_rows is not None and name in base_rows and row.ceiling > base_rows[name].ceiling:
            findings.append(f"REJECT ceiling-raised: {name} ceiling {row.ceiling} s above base "
                            f"{base_rows[name].ceiling} s")
    return findings, skipped


def read_cache(build_dir: Path) -> dict[str, str]:
    cache = build_dir / "CMakeCache.txt"
    try:
        text = cache.read_text(encoding="utf-8")
    except OSError as exc:
        raise BudgetError(f"REJECT cache-unreadable: {cache}: {exc.strerror}") from exc
    values: dict[str, str] = {}
    for line in text.splitlines():
        match = re.match(r"^([A-Za-z0-9_]+):[A-Z]+=(.*)$", line)
        if match:
            values[match.group(1)] = match.group(2)
    return values


def truthy(value: str | None) -> bool:
    return (value or "").upper() in {"ON", "TRUE", "1", "YES", "Y"}


def project_minor_from(root: Path) -> tuple[int, int]:
    text = (root / "CMakeLists.txt").read_text(encoding="utf-8")
    match = re.search(r"project\(\s*\w+\s+VERSION\s+([0-9]+)\.([0-9]+)", text)
    if match is None:
        raise BudgetError("REJECT version-unreadable: no project VERSION in CMakeLists.txt")
    return int(match.group(1)), int(match.group(2))


def load_tests(json_text: str, scale: int) -> dict[str, float | None]:
    try:
        tests = json.loads(json_text)["tests"]
    except (ValueError, KeyError, TypeError) as exc:
        raise BudgetError(f"REJECT inventory-unreadable: ctest json-v1 did not parse: {exc}") from exc
    result: dict[str, float | None] = {}
    for entry in tests:
        timeout = None
        for prop in entry.get("properties", []):
            if prop.get("name") == "TIMEOUT" and float(prop.get("value", 0)) > 0:
                timeout = float(prop["value"]) / scale
        result[entry["name"]] = timeout
    return result


def run_check(build_dir: Path, base_rev: str | None, repo: Path, allowlist_path: Path, ctest: str) -> int:
    cache = read_cache(build_dir)
    scale = SANITIZER_SCALE if truthy(cache.get("GABBABOY_ENABLE_SANITIZERS")) else 1
    listed = subprocess.run([ctest, "--test-dir", str(build_dir), "--show-only=json-v1"],
                            capture_output=True, text=True, check=False)
    if listed.returncode != 0:
        raise BudgetError(f"REJECT inventory-unreadable: ctest exited {listed.returncode}: {listed.stderr.strip()}")
    tests = load_tests(listed.stdout, scale)
    if not tests:
        print("REJECT vacuous: ctest json-v1 listed no tests", file=sys.stderr)
        return 1
    findings: list[str] = []
    try:
        rows = parse_allowlist(allowlist_path.read_text(encoding="utf-8"), findings)
    except OSError as exc:
        raise BudgetError(f"REJECT allowlist-unreadable: {allowlist_path}: {exc.strerror}") from exc
    base = None
    base_rows = None
    if base_rev is not None:
        base = BaseView(repo, base_rev)
        base_text = base.allowlist()
        base_rows = parse_allowlist(base_text, []) if base_text is not None else None
    more, skipped = evaluate(tests, rows, player_on=truthy(cache.get("GABBABOY_BUILD_PLAYER")),
                             project_minor=project_minor_from(repo), base=base, base_rows=base_rows)
    findings.extend(more)
    slowest = sorted(((t, n) for n, t in tests.items() if t is not None), key=lambda p: (-p[0], p[1]))
    print("slowest:")
    for timeout, name in slowest[:SLOWEST_COUNT]:
        print(f"  {timeout:g}s {name}")
    if findings:
        for finding in findings:
            print(finding, file=sys.stderr)
        return 1
    extra = f" player_rows_skipped={skipped}" if skipped else ""
    print(f"test-budget pass tests={len(tests)} allowlisted={len(rows)}{extra}")
    return 0


def self_test() -> int:
    controls = 0

    def expect(label: str, findings: list[str], code: str | None) -> None:
        nonlocal controls
        codes = {f.split(":", 1)[0].removeprefix("REJECT ") for f in findings}
        if code is None:
            assert not findings, f"{label}: expected pass, got {findings}"
        else:
            assert code in codes, f"{label}: expected {code}, got {sorted(codes)}"
        controls += 1

    def row(name: str, ceiling: int = 120, expires: str = "0.4", ref: str = "GB-CI-004") -> Row:
        match = EXPIRES.match(expires)
        assert match
        return Row(name, ceiling, (int(match.group(1)), int(match.group(2))), ref, "shrink when split")

    def judge(tests, rows, *, player_on=False, base=None, base_rows=None, minor=(0, 2)):
        return evaluate(tests, {r.name: r for r in rows}, player_on=player_on, project_minor=minor,
                        base=base, base_rows=base_rows)

    # Budget boundary: exactly 60 passes, 61 without a row fails.
    expect("clean", judge({"a": 30.0, "b": 60.0}, [])[0], None)
    expect("61 over budget", judge({"a": 61.0}, [])[0], "over-budget")
    # Missing TIMEOUT is over budget even when a row names the test.
    expect("untimed", judge({"a": None}, [])[0], "over-budget")
    expect("untimed with row", judge({"a": None}, [row("a")])[0], "over-budget")
    # Ceiling boundary.
    expect("at ceiling", judge({"a": 120.0}, [row("a", 120)])[0], None)
    expect("above ceiling", judge({"a": 121.0}, [row("a", 120)])[0], "over-ceiling")
    # Stale and expired rows.
    expect("stale", judge({"a": 30.0}, [row("gone")])[0], "stale-row")
    expect("expired at version", judge({"a": 120.0}, [row("a", expires="0.2")])[0], "row-expired")
    expect("not expired", judge({"a": 120.0}, [row("a", expires="0.3")])[0], None)
    expect("expired below version", judge({"a": 120.0}, [row("a", expires="0.1")])[0], "row-expired")
    # Player scope: skipped when OFF, stale when ON.
    findings, skipped = judge({"a": 30.0}, [row("player_x")], player_on=False)
    expect("player off", findings, None)
    assert skipped == 1
    expect("player on", judge({"a": 30.0}, [row("player_x")], player_on=True)[0], "stale-row")
    # Ratchet against the base allowlist.
    expect("raised", judge({"a": 120.0}, [row("a", 180)], base_rows={"a": row("a", 120)})[0], "ceiling-raised")
    expect("lowered", judge({"a": 120.0}, [row("a", 120)], base_rows={"a": row("a", 180)})[0], None)
    # Allowlist parser: malformed, duplicate and ref syntax.
    found: list[str] = []
    parse_allowlist("a\t120\t0.4\tGB-CI-004\n", found)
    expect("short row", found, "malformed-row")
    found = []
    parse_allowlist("a\t120\t0.4\tnonsense\ttrigger\n", found)
    expect("ref syntax", found, "ref-unresolved")
    found = []
    parse_allowlist("a\t120\t0.4\tGB-CI-004\tt\na\t90\t0.4\tGB-CI-004\tt\n", found)
    expect("duplicate", found, "duplicate-row")
    found = []
    parsed = parse_allowlist("# c\n\na\t120\t0.4\tGB-CI-004\tt\n", found)
    expect("comments and blanks", found, None)
    assert list(parsed) == ["a"]
    # Inventory parsing: sanitizer scale and TIMEOUT 0.
    doc = json.dumps({"tests": [{"name": "a", "properties": [{"name": "TIMEOUT", "value": 180}]},
                                 {"name": "b", "properties": [{"name": "TIMEOUT", "value": 0}]},
                                 {"name": "c", "properties": []}]})
    scaled = load_tests(doc, SANITIZER_SCALE)
    assert scaled == {"a": 60.0, "b": None, "c": None}
    expect("sanitizer scale", judge({"a": scaled["a"]}, [])[0], None)
    # Vacuous inventory is rejected by the CLI path.
    assert load_tests(json.dumps({"tests": []}), 1) == {}
    controls += 1

    # Ref resolution at the base commit, in a fixture repository.
    with tempfile.TemporaryDirectory(prefix="gbb-test-budget-") as tmp:
        repo = Path(tmp)
        assert git(repo, "init", "-q").returncode == 0
        git(repo, "config", "user.name", "fixture")
        git(repo, "config", "user.email", "fixture@example.invalid")
        git(repo, "config", "commit.gpgsign", "false")

        def commit(files: dict[str, str], message: str) -> str:
            for rel, content in files.items():
                path = repo / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                git(repo, "add", rel)
            assert git(repo, "commit", "-q", "-m", message).returncode == 0
            return git(repo, "rev-parse", "HEAD").stdout.strip()

        base_rev = commit({
            ".planning/context/LESSONS.md": "### GB-CI-004 / 2026-10-13 / Budgets\nbody\n",
            ".planning/context/DECISIONS.md": "| D-107 | something |\n",
            ".planning/milestones/v0.1-phases/GB-01-x/01-02-PLAN.md": "plan\n",
            ".planning/milestones/v0.1-phases/GB-1-x/01.1-03-PLAN.md": "plan\n",
        }, "base")
        # The head adds a lesson, a decision and a plan that the base lacks.
        head_rev = commit({
            ".planning/context/LESSONS.md": "### GB-CI-004 / 2026-10-13 / Budgets\n### GB-CI-099 / now / New\n",
            ".planning/context/DECISIONS.md": "| D-107 | something |\n| D-200 | new |\n",
            ".planning/milestones/v0.1-phases/GB-16-x/16-03-PLAN.md": "plan\n",
        }, "head")
        base = BaseView(repo, base_rev)
        tests = {"a": 120.0}
        for ref in ("GB-CI-004", "D-107", "01-02", "01.1-03"):
            expect(f"ref {ref} resolves at base", judge(tests, [row("a", ref=ref)], base=base)[0], None)
        for ref in ("GB-CI-099", "D-200", "16-03", "GB-CI-123", "D-999", "02-02"):
            expect(f"ref {ref} unresolved at base", judge(tests, [row("a", ref=ref)], base=base)[0],
                   "ref-unresolved")
        # A first seeding (allowlist absent at base) still resolves refs at the base.
        assert base.allowlist() is None
        expect("first seeding head-only ref", judge(tests, [row("a", ref="GB-CI-099")], base=base,
                                                    base_rows=None)[0], "ref-unresolved")
        # A head-only ref resolves once its base is the head: the same row passes at the later base.
        expect("same ref at head base", judge(tests, [row("a", ref="GB-CI-099")],
                                              base=BaseView(repo, head_rev))[0], None)
        # Fail closed on an unreadable base.
        try:
            BaseView(repo, "0" * 40)
        except BudgetError as exc:
            assert "base-unreadable" in str(exc)
            controls += 1
        else:
            raise AssertionError("an unreadable base was accepted")
        # The base allowlist is read from the base commit, not the working tree.
        seeded = commit({ALLOWLIST_REL: "a\t120\t0.4\tGB-CI-004\ttrigger\n"}, "seed")
        (repo / ALLOWLIST_REL).write_text("a\t300\t0.4\tGB-CI-004\ttrigger\n", encoding="utf-8")
        assert BaseView(repo, seeded).allowlist() == "a\t120\t0.4\tGB-CI-004\ttrigger\n"
        controls += 1

    assert controls >= 10
    print(f"test-budget self-test pass controls={controls}")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--build-dir", type=Path)
    parser.add_argument("--base", help="commit holding the allowlist and refs this change is judged against")
    parser.add_argument("--repo", type=Path, default=ROOT, help="repository root (default: this checkout)")
    parser.add_argument("--allowlist", type=Path)
    parser.add_argument("--ctest", default="ctest", help="ctest executable (CTest passes CMAKE_CTEST_COMMAND)")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.self_test:
            return self_test()
        if args.build_dir is None:
            parser.error("--build-dir or --self-test is required")
        allowlist = args.allowlist or args.repo / ALLOWLIST_REL
        return run_check(args.build_dir, args.base, args.repo, allowlist, args.ctest)
    except BudgetError as exc:
        print(exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
