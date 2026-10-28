"""Phase 17 boundary facts (17-11, D-22/D-23), read from one literal commit.

Used through `verify-state-contract.py --boundary --rev SHA [--self-test]`. This module is separate so the state
checker's other modes stay free of planning-file knowledge: only the boundary mode reads planning artifacts, and
only from git objects of the named commit.

Every fact below is read with git from the named commit. Nothing consults the working tree, the current HEAD
or whether a later commit reaches the boundary, so a later phase, a squash or an uncommitted edit cannot change
the verdict of an earlier boundary.
"""

from __future__ import annotations

import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import types
from datetime import datetime, timezone
from pathlib import Path

if not __debug__:
    raise SystemExit("state_boundary must not run with python -O")


class ContractError(Exception):
    pass


def run(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)


# One revision's facts are read through one `git cat-file --batch` process, one `git ls-tree` listing and (only when a
# summary names a plan head) one `git rev-list`, instead of a `git show`, `rev-parse` or `merge-base` per fact. The
# self-test runs the boundary about thirty times, and a process per fact (about 1,050 spawns) cost 31 s of the 60 s
# budget on hosted Windows (17-REVIEW WR-B01, LESSONS GB-CI-012). The binding is unchanged: every request names the
# resolved 40-hex --rev, a missing object is refused, and no object above BOUNDARY_OBJECT_LIMIT is read.
BOUNDARY_OBJECT_LIMIT = 8 * 1024 * 1024
_BATCH_HEADER = re.compile(rb"([0-9a-f]{40}) (blob|tree|commit|tag) ([0-9]+)\n")


def _universal_newlines(data: bytes, what: str) -> str:
    """The text `git show` gave through text-mode subprocess: UTF-8 with CRLF and CR read as LF."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ContractError(f"{what} is not UTF-8 text: {error}") from None
    return text.replace("\r\n", "\n").replace("\r", "\n")


class RevisionObjects:
    """A `git cat-file --batch` session for one boundary run. Each request is answered in order and framed by its
    header, so a short read, a missing object or a wrong type is refused instead of misread."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.process = subprocess.Popen(["git", "cat-file", "--batch"], cwd=root, stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self.ancestry: set[str] | None = None

    def __enter__(self) -> "RevisionObjects":
        return self

    def __exit__(self, *exc: object) -> None:
        try:
            if self.process.stdin is not None:
                self.process.stdin.close()
            self.process.wait(timeout=10)
        except (OSError, subprocess.TimeoutExpired):
            self.process.kill()
            self.process.wait()
        finally:
            if self.process.stdout is not None:
                self.process.stdout.close()

    def read(self, spec: str) -> tuple[str, str, bytes] | None:
        """(object id, type, bytes) of `spec`, or None when git reports it missing or ambiguous."""
        boundary_need("\n" not in spec and "\r" not in spec, f"a batch request cannot carry a line break: {spec!r}")
        stdin, stdout = self.process.stdin, self.process.stdout
        boundary_need(stdin is not None and stdout is not None, "git cat-file --batch has no pipes")
        try:
            stdin.write(spec.encode("utf-8") + b"\n")
            stdin.flush()
        except OSError as error:
            raise ContractError(f"git cat-file --batch stopped accepting requests: {error}") from None
        header = stdout.readline()
        found = _BATCH_HEADER.fullmatch(header)
        if found is None:
            boundary_need(header.endswith((b" missing\n", b" ambiguous\n")),
                          f"git cat-file --batch answered {spec!r} with {header[:120]!r}")
            return None
        size = int(found.group(3))
        boundary_need(size <= BOUNDARY_OBJECT_LIMIT, f"{spec} is {size} bytes, above the {BOUNDARY_OBJECT_LIMIT}-byte limit")
        data = stdout.read(size + 1)
        boundary_need(len(data) == size + 1 and data.endswith(b"\n"), f"git cat-file --batch output for {spec} is truncated")
        return found.group(1).decode("ascii"), found.group(2).decode("ascii"), data[:-1]

    def blob(self, rev: str, path: str) -> bytes:
        if "\n" in path or "\r" in path:
            # A name that cannot travel on a batch line keeps the single-file read.
            shown = subprocess.run(["git", "show", f"{rev}:{path}"], cwd=self.root, capture_output=True, check=False)
            boundary_need(shown.returncode == 0, f"git show {rev}:{path} failed")
            boundary_need(len(shown.stdout) <= BOUNDARY_OBJECT_LIMIT, f"{path} is above the object limit")
            return shown.stdout
        answer = self.read(f"{rev}:{path}")
        boundary_need(answer is not None and answer[1] == "blob", f"git show {rev}:{path} failed: no such file at the revision")
        return answer[2]

    def text(self, rev: str, path: str) -> str:
        return _universal_newlines(self.blob(rev, path), f"{path} at {rev}")

    def is_ancestor(self, commit: str, rev: str) -> bool:
        """`git merge-base --is-ancestor commit rev`, from one `git rev-list rev` for the whole run."""
        if self.ancestry is None:
            listed = run(["git", "rev-list", rev], cwd=self.root)
            boundary_need(listed.returncode == 0, f"cannot list the history of {rev}: {listed.stderr.strip()}")
            self.ancestry = set(listed.stdout.split())
        return commit in self.ancestry


PHASES_AT_REV = ".planning/phases"
BOUNDARY_PHASE_DIR = PHASES_AT_REV + "/GB-17-native-save-state-core"
BOUNDARY_REQUIRED_IDS = ("STATE-01", "STATE-02", "STATE-03", "STATE-04", "STATE-05", "STATE-06", "RM-030")
BOUNDARY_RELEASE_BOUND_ROWS = ("release.yml:attach-v02-evidence", "release.yml:candidate-fuzz",
                               "release-rehearsal.yml:judge", "release-rehearsal.yml:corpus",
                               "release-rehearsal.yml:performance", "release-rehearsal.yml:aggregate")
# Phase 16 evidence is history: its bytes are pinned by git blob id (a changed or re-generated receipt is refused).
BOUNDARY_HISTORIC_RECEIPTS = {
    "16-nightly-asan-gate.json": "6203cfce2042fc47b9328fa38fa23c4c180c4b3c",
    "16-perf-review-decision.json": "e615594b91f12f4b608dfc5b3473c1d8c06446b0",
    "16-release-readback.json": "6b488e947b84675c0056c16b32846da7d99d60b1",
    "16-pr-closures.json": "fcbfad7f80db51e32b3f92c4af829f0598d1fada",
}
BOUNDARY_HISTORIC_DIR = PHASES_AT_REV + "/GB-16-tune-up-and-v0-2-debt-closure"
NIGHTLY_RECEIPT_SCHEMA = "release-nightly-gate-receipt-v1"
NIGHTLY_RECEIPT_KEYS = {"schema", "run_id", "attempt", "workflow", "event", "branch", "head_sha", "tree_sha",
                        "source_sha", "conclusion", "replay_job_conclusion", "run_created_at", "run_completed_at",
                        "checked_at"}
BOUNDARY_TIMESTAMP = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ")


def boundary_need(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def boundary_resolve(objects: RevisionObjects, rev: str | None) -> tuple[str, datetime]:
    """The exact commit `rev` names and its committer time (what `git show -s --format=%ct` printed)."""
    boundary_need(isinstance(rev, str) and re.fullmatch(r"[0-9a-f]{40}", rev) is not None,
                  "--rev must be a resolved immutable 40-hex commit")
    answer = objects.read(f"{rev}^{{commit}}")
    boundary_need(answer is not None and answer[0] == rev and answer[1] == "commit",
                  f"--rev {rev} does not resolve to that exact commit")
    head = answer[2].split(b"\n\n", 1)[0]
    committer = re.search(rb"(?m)^committer .* ([0-9]+) [+-][0-9]{4}$", head)
    boundary_need(committer is not None, "cannot read the commit time")
    return rev, datetime.fromtimestamp(int(committer.group(1)), tz=timezone.utc)


def boundary_listing(root: Path, rev: str, prefix: str) -> dict[str, str]:
    """Every file under `prefix` at `rev`, with its object id, from one `git ls-tree`."""
    listing = subprocess.run(["git", "ls-tree", "-r", "-z", rev, "--", prefix], cwd=root, capture_output=True, check=False)
    boundary_need(listing.returncode == 0, f"cannot list {prefix} at {rev}: {listing.stderr.decode(errors='replace').strip()}")
    files: dict[str, str] = {}
    for entry in listing.stdout.split(b"\0"):
        if not entry:
            continue
        found = re.fullmatch(rb"[0-7]{6} (blob|tree|commit) ([0-9a-f]{40})\t(.+)", entry, re.S)
        boundary_need(found is not None, f"unexpected git ls-tree entry {entry[:120]!r}")
        files[found.group(3).decode("utf-8", errors="surrogateescape")] = found.group(2).decode("ascii")
    return files


def boundary_frontmatter(text: str, where: str) -> dict[str, str]:
    found = re.match(r"---\n(.*?)\n---\n", text, re.S)
    boundary_need(found is not None, f"{where} has no front matter")
    values: dict[str, str] = {}
    for line in found.group(1).splitlines():
        field = re.match(r"([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
        if field and field.group(1) not in values:
            values[field.group(1)] = field.group(2).strip()
    return values


def boundary_time(value: object, what: str) -> datetime:
    boundary_need(isinstance(value, str) and BOUNDARY_TIMESTAMP.fullmatch(value) is not None,
                  f"{what} is not a UTC timestamp: {value!r}")
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def boundary_nightly_receipt(text: str, where: str, committed_at: datetime) -> None:
    try:
        receipt = json.loads(text)
    except ValueError as error:
        raise ContractError(f"{where} is not JSON: {error}") from None
    boundary_need(isinstance(receipt, dict) and set(receipt) == NIGHTLY_RECEIPT_KEYS and
                  receipt["schema"] == NIGHTLY_RECEIPT_SCHEMA, f"{where} fields differ from the closed receipt schema")
    boundary_need(receipt["conclusion"] == "success" and receipt["replay_job_conclusion"] == "success",
                  f"{where} records a run that is not a success with a successful replay")
    boundary_need(all(re.fullmatch(r"[0-9a-f]{40}", str(receipt[key])) for key in ("head_sha", "tree_sha", "source_sha")),
                  f"{where} has a malformed head, tree or source id")
    created = boundary_time(receipt["run_created_at"], f"{where} run_created_at")
    completed = boundary_time(receipt["run_completed_at"], f"{where} run_completed_at")
    checked = boundary_time(receipt["checked_at"], f"{where} checked_at")
    boundary_need(created <= completed <= checked, f"{where} timestamps are not ordered created <= completed <= checked")
    boundary_need(checked <= committed_at,
                  f"{where} checked_at is later than the boundary commit that contains it")


def run_boundary(root: Path, rev: str | None) -> dict[str, object]:
    boundary_need(isinstance(rev, str) and re.fullmatch(r"[0-9a-f]{40}", rev) is not None,
                  "--rev must be a resolved immutable 40-hex commit")
    with RevisionObjects(root) as objects:
        return _run_boundary(root, objects, rev)


def _run_boundary(root: Path, objects: RevisionObjects, rev: str) -> dict[str, object]:
    rev, committed_at = boundary_resolve(objects, rev)
    listing = boundary_listing(root, rev, PHASES_AT_REV)
    names = [name for name in listing if name.startswith(BOUNDARY_PHASE_DIR + "/")]
    plans = sorted(name for name in names if re.fullmatch(re.escape(BOUNDARY_PHASE_DIR) + r"/17-\d\d-PLAN\.md", name))
    for number in range(1, 12):
        boundary_need(f"{BOUNDARY_PHASE_DIR}/17-{number:02d}-PLAN.md" in plans, f"plan 17-{number:02d} is missing")
    boundary_need(len(plans) <= 12, f"Phase 17 has {len(plans)} plans; the cap is 11 primary plans plus one gap slot")

    requirements_text = objects.text(rev, ".planning/REQUIREMENTS.md")
    claimed: set[str] = set()
    for plan in plans:
        fields = boundary_frontmatter(objects.text(rev, plan), plan)
        try:
            claimed.update(json.loads(fields.get("requirements", "")))
        except ValueError:
            raise ContractError(f"{plan} requirements are not a JSON list") from None
    boundary_need(set(BOUNDARY_REQUIRED_IDS) <= claimed,
                  f"the plans do not claim {sorted(set(BOUNDARY_REQUIRED_IDS) - claimed)}")
    for identifier in sorted(claimed):
        boundary_need(re.search(r"(?<![A-Za-z0-9-])" + re.escape(identifier) + r"(?![A-Za-z0-9-])", requirements_text)
                      is not None, f"requirement {identifier} is not in REQUIREMENTS.md at the boundary")

    summaries = 0
    for number in range(1, 12):
        path = f"{BOUNDARY_PHASE_DIR}/17-{number:02d}-SUMMARY.md"
        if path not in names:
            # The summary of the last plan is written after its implementation commit; it cannot be in that commit.
            boundary_need(number == 11, f"summary 17-{number:02d} is missing")
            continue
        fields = boundary_frontmatter(objects.text(rev, path), path)
        boundary_need(fields.get("status") == "complete", f"{path} is not status: complete")
        boundary_need(fields.get("plan", "").strip("\"'") == f"{number:02d}", f"{path} names another plan")
        after = fields.get("plan_head_after", "")
        boundary_need(re.fullmatch(r"[0-9a-f]{40}", after) is not None, f"{path} has no plan_head_after commit")
        boundary_need(objects.is_ancestor(after, rev), f"{path} plan_head_after {after} is not part of the boundary history")
        summaries += 1

    phase_pattern = re.compile(r"/(\d+(?:\.\d+)?)-\d\d-(?:PLAN|SUMMARY)\.md$")
    later = [name for name in listing
             if phase_pattern.search(name) and float(phase_pattern.search(name).group(1)) > 17]
    boundary_need(not later, f"work for a later phase exists at the Phase 17 boundary: {later[0] if later else ''}")
    try:
        workflow = json.loads(objects.text(rev, ".planning/config.json")).get("workflow", {})
    except ValueError:
        raise ContractError("config.json is not JSON at the boundary") from None
    boundary_need(workflow.get("auto_advance", False) is False and workflow.get("_auto_chain_active", False) is False,
                  "an auto-advance flag is on at the boundary")

    for name, blob in BOUNDARY_HISTORIC_RECEIPTS.items():
        boundary_need(listing.get(f"{BOUNDARY_HISTORIC_DIR}/{name}") == blob,
                      f"historic Phase 16 receipt {name} is missing or changed")
    receipts = 0
    for name in listing:
        base = name.rsplit("/", 1)[-1]
        if not (base.endswith(".json") and "nightly" in base):
            continue
        if base in BOUNDARY_HISTORIC_RECEIPTS and name.startswith(BOUNDARY_HISTORIC_DIR + "/"):
            continue
        boundary_nightly_receipt(objects.text(rev, name), name, committed_at)
        receipts += 1

    version = re.search(r"(?m)^project\(GabbaBoy VERSION (\d+)\.(\d+)\.(\d+)", objects.text(rev, "CMakeLists.txt"))
    boundary_need(version is not None, "CMakeLists.txt has no project version at the boundary")
    version_tuple = tuple(int(part) for part in version.groups())
    try:
        ledger = json.loads(objects.text(rev, ".github/ci-timeouts.json"))
    except ValueError:
        raise ContractError("ci-timeouts.json is not JSON at the boundary") from None
    bound = sorted(key for key, row in ledger.items() if isinstance(row, dict) and row.get("release_bound") is True)
    row = next((line for line in objects.text(rev, ".planning/context/FUTURE-MILESTONES.md").splitlines()
                if line.startswith("| RM-027 |")), "")
    if version_tuple <= (0, 2, 1):
        boundary_need(bound == sorted(BOUNDARY_RELEASE_BOUND_ROWS),
                      f"the release_bound ledger rows are {bound}, not the six RM-027 rows")
        boundary_need("Phase 19 entry blocker" in row, "RM-027 is no longer named a Phase 19 entry blocker")
    else:
        boundary_need(not bound, f"release_bound rows {bound} expired when the version moved past 0.2.1")
    return {"rev": rev, "plans": len(plans), "summaries": summaries, "requirements": len(claimed),
            "release_bound": len(bound), "version": ".".join(str(part) for part in version_tuple),
            "nightly_receipts": receipts}


def boundary_files_from_rev(root: Path, rev: str) -> dict[str, bytes]:
    """Every file the boundary reads, as bytes from the boundary commit (the self-test fixture seed)."""
    wanted = [name for name in boundary_listing(root, rev, BOUNDARY_PHASE_DIR)
              if re.search(r"/17-\d\d-(PLAN|SUMMARY)\.md$", name)]
    wanted += [f"{BOUNDARY_HISTORIC_DIR}/{name}" for name in BOUNDARY_HISTORIC_RECEIPTS]
    wanted += [".planning/REQUIREMENTS.md", ".planning/config.json", ".planning/context/FUTURE-MILESTONES.md",
               ".github/ci-timeouts.json", "CMakeLists.txt"]
    with RevisionObjects(root) as objects:
        return {name: objects.blob(rev, name) for name in wanted}


def boundary_self_test(root: Path, rev: str | None) -> int:
    real = run_boundary(root, rev)
    rev = str(real["rev"])
    seed = boundary_files_from_rev(root, rev)
    controls = 0
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="gbb-boundary-") as directory:
        repo = Path(directory)
        for step in (["init", "-q"], ["config", "user.email", "boundary@example.invalid"],
                     ["config", "user.name", "boundary"], ["config", "commit.gpgsign", "false"]):
            run(["git", *step], cwd=repo)
        (repo / "history.txt").write_text("history\n", encoding="utf-8", newline="\n")
        run(["git", "add", "history.txt"], cwd=repo)
        run(["git", "commit", "-q", "-m", "history"], cwd=repo)
        history = run(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()

        def commit(files: dict[str, bytes], when: str) -> str:
            for entry in repo.iterdir():
                if entry.name == ".git":
                    continue
                if entry.is_dir():
                    shutil.rmtree(entry)
                else:
                    entry.unlink()
            (repo / "history.txt").write_text("history\n", encoding="utf-8", newline="\n")
            for name, data in files.items():
                target = repo / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            run(["git", "add", "-A"], cwd=repo)
            result = subprocess.run(["git", "commit", "-q", "--allow-empty", "-m", "boundary"], cwd=repo, text=True,
                                    capture_output=True, check=False,
                                    env={**os.environ, "GIT_COMMITTER_DATE": when, "GIT_AUTHOR_DATE": when})
            boundary_need(result.returncode == 0, f"fixture commit failed: {result.stderr.strip()}")
            return run(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()

        # The seed's plan_head_after commits belong to the real repository; give the fixture one of its own.
        base = {name: (re.sub(rb"(?m)^plan_head_after: [0-9a-f]{40}$", b"plan_head_after: " + history.encode(), data)
                       if name.endswith("-SUMMARY.md") else data) for name, data in seed.items()}
        summary_05 = f"{BOUNDARY_PHASE_DIR}/17-05-SUMMARY.md"
        plan_11 = f"{BOUNDARY_PHASE_DIR}/17-11-PLAN.md"
        requirements = ".planning/REQUIREMENTS.md"
        config = ".planning/config.json"
        future = ".planning/context/FUTURE-MILESTONES.md"
        ledger_path = ".github/ci-timeouts.json"
        receipt_path = f"{BOUNDARY_PHASE_DIR}/17-nightly-gate.json"
        good_receipt = {"schema": NIGHTLY_RECEIPT_SCHEMA, "run_id": 5, "attempt": 1, "workflow": "nightly-asan",
                        "event": "workflow_dispatch", "branch": "rehearsal/v0.2.1", "head_sha": "a" * 40,
                        "tree_sha": "b" * 40, "source_sha": "a" * 40, "conclusion": "success",
                        "replay_job_conclusion": "success", "run_created_at": "2026-10-27T03:00:00Z",
                        "run_completed_at": "2026-10-27T03:40:00Z", "checked_at": "2026-10-27T04:00:00Z"}
        when = "2026-10-28T00:00:00+0000"

        def edited(name: str, old: bytes, new: bytes, every: bool = False) -> dict[str, bytes]:
            mutated = dict(base)
            boundary_need(old in mutated[name], f"self-test fixture lacks {old!r} in {name}")
            mutated[name] = mutated[name].replace(old, new, -1 if every else 1)
            return mutated

        def without(name: str) -> dict[str, bytes]:
            return {key: value for key, value in base.items() if key != name}

        def with_receipt(changes: dict[str, object]) -> dict[str, bytes]:
            return {**base, receipt_path: json.dumps({**good_receipt, **changes}).encode()}

        first_bound = next(key for key, row in json.loads(seed[ledger_path]).items()
                           if isinstance(row, dict) and row.get("release_bound"))

        def ledger_with(change, files: dict[str, bytes] | None = None) -> dict[str, bytes]:
            data = json.loads(seed[ledger_path])
            change(data)
            return {**(files if files is not None else base), ledger_path: json.dumps(data).encode()}

        def expect(name: str, files: dict[str, bytes] | None, needle: str | None, *, revision: str | None = None) -> None:
            nonlocal controls
            controls += 1
            target = revision if revision is not None else commit(files if files is not None else base, when)
            try:
                run_boundary(repo, target)
            except ContractError as error:
                if needle is None:
                    failures.append(f"{name}: refused ({error}), expected a pass")
                elif needle not in str(error):
                    failures.append(f"{name}: refused for the wrong reason ({error}), expected {needle!r}")
                return
            if needle is not None:
                failures.append(f"{name}: accepted, expected {needle!r}")

        good = commit(base, when)
        expect("the unmodified boundary passes", None, None, revision=good)
        expect("a short revision", None, "40-hex", revision=good[:12])
        expect("a name is not a revision", None, "40-hex", revision="HEAD")
        expect("an upper-case revision", None, "40-hex", revision=good.upper())
        expect("an unresolvable revision", None, "does not resolve", revision="0" * 40)
        expect("a substituted revision lacks the Phase 17 plans", None, "plan 17-01 is missing", revision=history)
        expect("a plan is missing", without(plan_11), "plan 17-11 is missing")
        extra = {**base, f"{BOUNDARY_PHASE_DIR}/17-12-PLAN.md": base[plan_11],
                 f"{BOUNDARY_PHASE_DIR}/17-13-PLAN.md": base[plan_11]}
        expect("a thirteenth plan exceeds the cap", extra, "the cap is 11 primary plans")
        expect("a summary is missing", without(summary_05), "summary 17-05 is missing")
        expect("a summary is not complete", edited(summary_05, b"status: complete", b"status: partial"), "not status: complete")
        expect("a summary names another plan", edited(summary_05, b'plan: "05"', b'plan: "06"'), "names another plan")
        expect("plan_head_after is not in the boundary history",
               edited(summary_05, history.encode(), b"f" * 40), "not part of the boundary history")
        expect("a claimed requirement is not in REQUIREMENTS.md",
               edited(requirements, b"STATE-06", b"STATE-0X", every=True), "STATE-06 is not in REQUIREMENTS.md")
        expect("auto_advance is on", edited(config, b'"auto_advance": false', b'"auto_advance": true'), "auto-advance")
        expect("the auto chain is active",
               edited(config, b'"_auto_chain_active": false', b'"_auto_chain_active": true'), "auto-advance")
        expect("a later phase has started",
               {**base, PHASES_AT_REV + "/GB-18-player-save-slots/18-01-PLAN.md": b"---\nphase: GB-18\n---\n"},
               "later phase exists")
        historic = f"{BOUNDARY_HISTORIC_DIR}/16-nightly-asan-gate.json"
        expect("a historic receipt was regenerated", {**base, historic: base[historic] + b"\n"}, "missing or changed")
        expect("an RM-027 row was dropped",
               ledger_with(lambda data: data[first_bound].pop("release_bound")), "not the six RM-027 rows")
        expect("a seventh release_bound row appeared",
               ledger_with(lambda data: data.__setitem__("ci.yml:new", {"release_bound": True})), "not the six RM-027 rows")
        expect("RM-027 lost its blocker name",
               edited(future, b"Phase 19 entry blocker", b"Phase 19 note"), "no longer named a Phase 19 entry blocker")
        moved = edited("CMakeLists.txt", b"VERSION 0.2.1", b"VERSION 0.2.2")
        expect("the version moved with release_bound rows left", moved, "expired when the version moved")

        def strip_bound(data):
            for row in data.values():
                if isinstance(row, dict):
                    row.pop("release_bound", None)

        expect("the version moved after the rows were replaced", ledger_with(strip_bound, moved), None)
        expect("a nightly receipt recorded before the commit passes", with_receipt({}), None)
        expect("a nightly receipt checked after its commit", with_receipt({"checked_at": "2026-10-29T00:00:00Z"}),
               "later than the boundary commit")
        expect("a nightly receipt checked before its run completed", with_receipt({"checked_at": "2026-10-27T03:30:00Z"}),
               "timestamps are not ordered")
        expect("a nightly receipt of a failed run", with_receipt({"conclusion": "failure"}), "not a success")
        expect("a nightly receipt of a skipped replay", with_receipt({"replay_job_conclusion": "skipped"}), "not a success")
        expect("a nightly receipt with an extra field", with_receipt({"note": "x"}), "closed receipt schema")
        # The verdict is the commit's own: a live edit or a later commit does not change it.
        kept = commit(base, when)
        (repo / plan_11).unlink()
        expect("an uncommitted deletion does not change the boundary", None, None, revision=kept)
        later_commit = commit(without(plan_11), "2026-10-29T00:00:00+0000")
        expect("a later commit does not change an earlier boundary", None, None, revision=kept)
        expect("the later commit is its own boundary", None, "plan 17-11 is missing", revision=later_commit)

    # The batch framing (WR-B01): a canned answer stream replaces git, so a reader that skipped a check would accept it.
    def framed(name: str, stream: bytes, call, needle: str | None) -> None:
        nonlocal controls
        controls += 1
        objects = RevisionObjects.__new__(RevisionObjects)
        objects.root, objects.ancestry = root, None
        objects.process = types.SimpleNamespace(stdin=io.BytesIO(), stdout=io.BytesIO(stream))
        try:
            call(objects)
        except ContractError as error:
            if needle is None or needle not in str(error):
                failures.append(f"{name}: refused ({error}), expected {needle!r}")
            return
        if needle is not None:
            failures.append(f"{name}: accepted, expected {needle!r}")

    oid = b"c" * 40
    framed("a well-framed blob is read", oid + b" blob 3\nabc\n",
           lambda objects: boundary_need(objects.blob(rev, "x") == b"abc", "wrong bytes"), None)
    framed("a truncated batch object", oid + b" blob 10\nabc\n", lambda objects: objects.blob(rev, "x"), "truncated")
    framed("a batch object without its terminator", oid + b" blob 3\nabcd", lambda objects: objects.blob(rev, "x"), "truncated")
    framed("a batch object above the limit", oid + b" blob %d\n" % (BOUNDARY_OBJECT_LIMIT + 1),
           lambda objects: objects.blob(rev, "x"), "above the")
    framed("a misframed batch header", b"fatal: bad revision\n", lambda objects: objects.blob(rev, "x"), "answered")
    framed("a missing object", rev.encode() + b":x missing\n", lambda objects: objects.blob(rev, "x"), "no such file")
    framed("a directory where a file is read", oid + b" tree 0\n\n", lambda objects: objects.blob(rev, "x"), "no such file")
    framed("a peeled commit that is not --rev", oid + b" commit 0\n\n", lambda objects: boundary_resolve(objects, rev),
           "does not resolve")
    if failures:
        for failure in failures:
            print(f"boundary control failed: {failure}", file=sys.stderr)
        raise ContractError(f"{len(failures)} of {controls} boundary controls failed")
    print(f"state boundary controls pass rev={rev} controls={controls} plans={real['plans']} "
          f"summaries={real['summaries']} release_bound={real['release_bound']}")
    return 0
