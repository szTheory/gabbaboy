#!/usr/bin/env python3
"""Classify closeout findings while retaining the installed OpenGSD audit.

Runtime requirement: this check executes an installed OpenGSD (@opengsd/gsd-core) gsd-tools.cjs with node and
verifies its identity before trusting any audit output. The runtime is resolved from, in order: GSD_TOOLS (a file),
then gsd-core/bin/gsd-tools.cjs under CLAUDE_CONFIG_DIR or ~/.claude, then under CODEX_HOME or ~/.codex.

Exit codes: 0 scan clear; 1 blocked by classified findings; 2 scan error (the runtime ran or launched and failed, or
the record could not be written); 3 runtime-unavailable (no installed runtime was found, so nothing was classified).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
import unittest


ROOT = Path(__file__).resolve().parents[2]
REVIEW_SOURCE = (
    ROOT
    / ".planning/phases/GB-14-cgb-e-model-qualification-and-corpus/14-UAT-REVIEW.md"
)
CLASSIFIER_VERSION = "1"
RUNTIME_SUFFIX = "gsd-core/bin/gsd-tools.cjs"
REVIEW_NAME = re.compile(r"^\d+(?:\.\d+)*-UAT-REVIEW\.md$")
CANONICAL_UAT_NAME = re.compile(r"^\d+(?:\.\d+)*-UAT\.md$")


def runtime_candidates() -> list[Path]:
    candidates: list[Path] = []
    configured = os.environ.get("GSD_TOOLS")
    if configured:
        candidates.append(Path(configured).expanduser())
    for variable, fallback in (("CLAUDE_CONFIG_DIR", ".claude"), ("CODEX_HOME", ".codex")):
        home = os.environ.get(variable)
        candidates.append((Path(home).expanduser() if home else Path.home() / fallback) / RUNTIME_SUFFIX)
    return candidates


def installed_tools() -> Path:
    candidates = runtime_candidates()
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise ScanError(
        "runtime-unavailable",
        "no installed OpenGSD runtime was found; set GSD_TOOLS or install under CLAUDE_CONFIG_DIR/~/.claude or CODEX_HOME/~/.codex",
    )


def make_fixture(root: Path) -> None:
    phase = root / ".planning/phases/GB-14-cgb-e-model-qualification-and-corpus"
    phase.mkdir(parents=True)
    (phase / "14-UAT-REVIEW.md").write_text(REVIEW_SOURCE.read_text(encoding="utf-8"), encoding="utf-8")
    (phase / "14-UAT.md").write_text(
        "---\n"
        "status: pending\n"
        "phase: GB-14-cgb-e-model-qualification-and-corpus\n"
        "---\n\n"
        "## Current Test\n"
        "[testing pending]\n\n"
        "### Incomplete scenario\n"
        "result: pending\n",
        encoding="utf-8",
    )


class ScanError(RuntimeError):
    def __init__(self, code: str, message: str, *, raw: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.raw = raw or {}


def _run(command: list[str], root: Path) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, cwd=root, text=True, capture_output=True, check=False)
    except OSError as exc:
        raise ScanError("runtime-launch", f"could not launch installed OpenGSD: {exc}") from exc


def _runtime_command() -> tuple[list[str], dict[str, object]]:
    node = shutil.which("node")
    if node is None:
        raise ScanError("runtime-launch", "Node.js was not found on PATH")
    tool = installed_tools()

    command = [node, str(tool), "runtime-identity", "--raw"]
    result = _run(command, ROOT)
    identity_raw: dict[str, object] = {
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
    if result.returncode != 0:
        raise ScanError("runtime-identity", "installed runtime identity command failed", raw=identity_raw)
    try:
        identity = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ScanError("runtime-identity", "installed runtime identity was not JSON", raw=identity_raw) from exc
    if not isinstance(identity, dict) or identity.get("packageName") != "@opengsd/gsd-core" or not isinstance(identity.get("version"), str):
        raise ScanError("runtime-identity", "installed runtime identity did not prove @opengsd/gsd-core", raw=identity_raw)
    try:
        runtime_revision = "sha256:" + hashlib.sha256(tool.read_bytes()).hexdigest()
    except OSError as exc:
        raise ScanError("runtime-revision", "could not hash the installed runtime entry point", raw=identity_raw) from exc
    return [node, str(tool)], {
        "package_name": identity["packageName"],
        "version": identity["version"],
        "revision": runtime_revision,
        "revision_kind": "installed-entrypoint-sha256",
        "identity_command": identity_raw,
    }


def _project_revision(root: Path) -> str | None:
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--verify", "HEAD"],
            text=True,
            capture_output=True,
            check=False,
            env=environment,
            timeout=3,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    revision = result.stdout.strip()
    return revision if result.returncode == 0 and re.fullmatch(r"[0-9a-fA-F]{40,64}", revision) else None


def _read_review_verdict(root: Path, item: dict[str, object]) -> tuple[bool, str, str | None]:
    phase = item.get("phase")
    filename = item.get("file")
    if not isinstance(phase, str) or Path(phase).name != phase or not isinstance(filename, str) or Path(filename).name != filename:
        return False, "invalid-source-identity", None

    archive_label = item.get("archived_milestone")
    if archive_label is None:
        candidates = [root / ".planning/phases" / phase / filename]
    elif isinstance(archive_label, str):
        parts = archive_label.split("/")
        if len(parts) == 1 and re.fullmatch(r"v[0-9.]+", parts[0]):
            candidates = [root / ".planning/milestones" / f"{parts[0]}-phases" / phase / filename]
        elif len(parts) == 1 and re.fullmatch(r"ws-[A-Za-z0-9._-]+", parts[0]):
            candidates = [root / ".planning/milestones" / parts[0] / "phases" / phase / filename]
        elif len(parts) == 2 and all(re.fullmatch(r"[A-Za-z0-9._-]+", part) for part in parts):
            workstream, version = parts
            base = root / ".planning/workstreams" / workstream / "milestones"
            if re.fullmatch(r"v[0-9.]+", version):
                candidates = [base / f"{version}-phases" / phase / filename]
            elif version.startswith("ws-"):
                candidates = [base / version / "phases" / phase / filename]
            else:
                candidates = []
        else:
            candidates = []
    else:
        candidates = []
    source = None
    for candidate in candidates:
        try:
            candidate.resolve().relative_to(root.resolve())
        except (OSError, ValueError):
            continue
        if candidate.is_file():
            source = candidate
            break
    if source is None:
        return False, "review-source-missing", None
    relative_source = source.relative_to(root).as_posix()
    try:
        if source.stat().st_size > 2 * 1024 * 1024:
            return False, "review-source-exceeds-read-limit", relative_source
        text = source.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return False, "review-source-unreadable", relative_source

    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", text, flags=re.DOTALL)
    if match is None:
        return False, "review-frontmatter-malformed", relative_source
    frontmatter = match.group(1).splitlines()
    statuses = [m.group(1).strip().lower() for line in frontmatter if (m := re.match(r"^status:\s*(.*?)\s*$", line))]
    if statuses != ["clean"]:
        return False, "review-verdict-not-clean-or-ambiguous", relative_source

    findings_index = next((index for index, line in enumerate(frontmatter) if line == "findings:"), None)
    if findings_index is None:
        return False, "review-findings-missing", relative_source
    counts: dict[str, list[int]] = {name: [] for name in ("critical", "warning", "info", "total")}
    for line in frontmatter[findings_index + 1 :]:
        if line and not line[0].isspace():
            break
        count_match = re.match(r"^\s+(critical|warning|info|total):\s*(\d+)\s*$", line)
        if count_match:
            counts[count_match.group(1)].append(int(count_match.group(2)))
    if any(len(values) != 1 for values in counts.values()):
        return False, "review-findings-malformed-or-ambiguous", relative_source
    clean = all(values[0] == 0 for values in counts.values())
    if not clean:
        return False, "review-has-findings", relative_source
    if counts["total"][0] != sum(counts[key][0] for key in ("critical", "warning", "info")):
        return False, "review-findings-total-mismatch", relative_source
    return True, "clean-review-verdict-and-zero-findings", relative_source


def _record_for(category: str, item: object, root: Path, index: int) -> dict[str, object]:
    if not isinstance(item, dict):
        return {"category": category, "index": index, "classification": "malformed-runtime-item", "blocking": True, "raw_item": item}
    record: dict[str, object] = {"category": category, "index": index, "raw_item": item}
    if category != "uat_gaps":
        record.update(classification=f"open-{category}", blocking=True, reason="installed audit-open reported an open item")
        return record

    filename = item.get("file")
    if isinstance(filename, str) and CANONICAL_UAT_NAME.fullmatch(filename):
        record.update(
            classification="pending-canonical-uat",
            blocking=True,
            reason="installed audit-open reported a canonical UAT artifact as incomplete",
        )
        return record
    if isinstance(filename, str) and REVIEW_NAME.fullmatch(filename):
        clean, reason, source = _read_review_verdict(root, item)
        record["source_file"] = source
        if (
            clean
            and item.get("status") == "clean"
            and type(item.get("open_scenario_count")) is int
            and item.get("open_scenario_count") == 0
        ):
            record.update(classification="clean-review", blocking=False, reason=reason)
        else:
            record.update(classification="ambiguous-or-dirty-review", blocking=True, reason=reason)
        return record
    record.update(
        classification="unclassified-uat-artifact",
        blocking=True,
        reason="UAT finding did not match an exact canonical UAT or review filename",
    )
    return record


def _scan(root: Path) -> dict[str, object]:
    raw_identity: dict[str, object] = {}
    raw_audit: dict[str, object] = {"exit_code": None, "stdout": "", "stderr": "", "payload": None}
    project_revision = _project_revision(root)
    try:
        command_prefix, runtime = _runtime_command()
        raw_identity = runtime
        audit = _run([*command_prefix, "audit-open", "--json"], root)
        raw_audit = {"exit_code": audit.returncode, "stdout": audit.stdout, "stderr": audit.stderr, "payload": None}
        if audit.returncode != 0:
            raise ScanError("runtime-audit-open", "installed audit-open returned a nonzero exit", raw=raw_audit)
        try:
            payload = json.loads(audit.stdout)
        except json.JSONDecodeError as exc:
            raise ScanError("runtime-audit-json", "installed audit-open stdout was not JSON", raw=raw_audit) from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("items"), dict):
            raw_audit["payload"] = payload
            raise ScanError("runtime-audit-shape", "installed audit-open JSON did not contain an items object", raw=raw_audit)
        raw_audit["payload"] = payload
        records: list[dict[str, object]] = []
        for category, items in payload["items"].items():
            if not isinstance(items, list):
                records.append({"category": category, "index": 0, "classification": "malformed-runtime-category", "blocking": True, "raw_item": items})
                continue
            for index, item in enumerate(items):
                if isinstance(item, dict) and item.get("scan_error") is True:
                    records.append({"category": category, "index": index, "classification": "scan-error", "blocking": True, "reason": "installed audit-open could not inspect this category", "raw_item": item})
                else:
                    records.append(_record_for(category, item, root, index))
        clean_review = any(record["classification"] == "clean-review" for record in records)
        if project_revision is None:
            records.append(
                {
                    "category": "provenance",
                    "index": 0,
                    "classification": "project-revision-unavailable",
                    "blocking": True,
                    "reason": "project root is not bound to a Git HEAD revision",
                }
            )
        limitation = (
            f"Installed OpenGSD {runtime['version']} reported an exact clean review under raw uat_gaps. The raw output is retained unchanged; only an exact review filename with a clean verdict and four zero finding counts is classified as non-blocking."
            if clean_review
            else "The installed audit-open result is retained unchanged. Only an exact review filename with a clean verdict and four zero finding counts can be classified as non-blocking."
        )
        return {
            "schema": "gabbaboy.closeout-scan.v1",
            "status": "blocked" if any(record["blocking"] for record in records) else "clear",
            "classifier_version": CLASSIFIER_VERSION,
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "project_revision": project_revision,
            "project_revision_status": "bound" if project_revision is not None else "unavailable",
            "runtime": {key: value for key, value in raw_identity.items() if key != "identity_command"},
            "raw_runtime_identity": raw_identity["identity_command"],
            "raw_limitation": limitation,
            "raw_audit_open": raw_audit,
            "records": records,
            "counts": {
                "raw_uat_gaps": len(payload["items"].get("uat_gaps", [])) if isinstance(payload["items"].get("uat_gaps", []), list) else None,
                "clean_reviews": sum(record["classification"] == "clean-review" for record in records),
                "blocking_records": sum(bool(record["blocking"]) for record in records),
            },
            "clean_review_false_positive_observed": clean_review,
        }
    except ScanError as exc:
        return {
            "schema": "gabbaboy.closeout-scan.v1",
            "status": "error",
            "classifier_version": CLASSIFIER_VERSION,
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "project_revision": project_revision,
            "project_revision_status": "bound" if project_revision is not None else "unavailable",
            "error": {"code": exc.code, "diagnostic": str(exc)},
            "runtime": raw_identity,
            "raw_runtime_identity": exc.raw if exc.code.startswith(("runtime-identity", "runtime-revision")) else raw_identity.get("identity_command"),
            "raw_limitation": "The installed runtime output could not be classified; raw output is retained when available.",
            "raw_audit_open": exc.raw if exc.code.startswith("runtime-audit") else raw_audit,
            "records": [],
            "counts": {"raw_uat_gaps": None, "clean_reviews": 0, "blocking_records": None},
            "clean_review_false_positive_observed": False,
        }


def _write_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class CloseoutScanTests(unittest.TestCase):
    def run_wrapper(self, root: Path, output: Path, *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        child_env = os.environ.copy()
        if env:
            child_env.update(env)
        return subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--check", "--root", str(root), "--output", str(output)],
            cwd=ROOT,
            env=child_env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_clean_review_is_nonblocking_but_pending_canonical_uat_blocks(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gabbaboy-closeout-red-") as temp_dir:
            fixture = Path(temp_dir) / "project"
            fixture.mkdir()
            make_fixture(fixture)
            output = Path(temp_dir) / "closeout.json"
            result = self.run_wrapper(fixture, output)
            self.assertEqual(result.returncode, 1, f"pending canonical UAT must block: {result.stdout}\n{result.stderr}")
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "blocked")
            raw_payload = report["raw_audit_open"]["payload"]
            raw_names = [item["file"] for item in raw_payload["items"]["uat_gaps"]]
            self.assertEqual(raw_names, ["14-UAT-REVIEW.md", "14-UAT.md"])
            self.assertIn("14-UAT-REVIEW.md", report["raw_audit_open"]["stdout"])
            review = next(record for record in report["records"] if record["classification"] == "clean-review")
            canonical = next(record for record in report["records"] if record["classification"] == "pending-canonical-uat")
            self.assertFalse(review["blocking"])
            self.assertEqual(review["source_file"], ".planning/phases/GB-14-cgb-e-model-qualification-and-corpus/14-UAT-REVIEW.md")
            self.assertTrue(canonical["blocking"])
            self.assertEqual(canonical["raw_item"]["open_scenario_count"], 1)
            self.assertIn("BLOCKED", result.stdout)
            self.assertNotIn("CLEAR", result.stdout)

    def test_check_output_records_project_and_runtime_revisions(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gabbaboy-closeout-revision-") as temp_dir:
            output = Path(temp_dir) / "closeout.json"
            result = self.run_wrapper(ROOT, output)
            self.assertIn(result.returncode, (0, 1), f"scan command failed instead of classifying findings: {result.stdout}\n{result.stderr}")
            report = json.loads(output.read_text(encoding="utf-8"))
            expected_project = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True
            ).stdout.strip()
            self.assertIn("project_revision", report, "scan record must bind findings to the project revision")
            self.assertEqual(report["project_revision"], expected_project)
            self.assertIn("revision", report["runtime"], "scan record must bind findings to an installed runtime revision")
            self.assertRegex(report["runtime"]["revision"], r"^(?:git:[0-9a-f]{40}|sha256:[0-9a-f]{64})$")

    def test_unknown_dirty_and_malformed_reviews_remain_blocking(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gabbaboy-closeout-review-controls-") as temp_dir:
            root = Path(temp_dir) / "project"
            root.mkdir()
            planning = root / ".planning/phases"
            review_rows = (
                (
                    "GB-15-dirty",
                    "15-UAT-REVIEW.md",
                    "---\nstatus: clean\nfindings:\n  critical: 0\n  warning: 1\n  info: 0\n  total: 1\n---\n",
                ),
                ("GB-16-malformed", "16-UAT-REVIEW.md", "---\nstatus: clean\n---\n"),
                ("GB-17-unknown", "17-UAT-REVIEW-EXTRA.md", "---\nstatus: pending\n---\n"),
            )
            for phase_name, filename, content in review_rows:
                phase = planning / phase_name
                phase.mkdir(parents=True)
                (phase / filename).write_text(content, encoding="utf-8")
            output = Path(temp_dir) / "closeout.json"
            result = self.run_wrapper(root, output)
            self.assertEqual(result.returncode, 1)
            report = json.loads(output.read_text(encoding="utf-8"))
            controls = [record for record in report["records"] if record["category"] == "uat_gaps"]
            self.assertEqual(len(controls), 3)
            self.assertTrue(all(record["blocking"] for record in controls))
            self.assertCountEqual(
                [record["classification"] for record in controls],
                ["ambiguous-or-dirty-review", "ambiguous-or-dirty-review", "unclassified-uat-artifact"],
            )

    def test_duplicate_runtime_findings_are_retained_as_blocking_records(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gabbaboy-closeout-duplicates-") as temp_dir:
            root = Path(temp_dir) / "project"
            root.mkdir()
            make_fixture(root)
            archived = root / ".planning/milestones/v0.2-phases/GB-14-cgb-e-model-qualification-and-corpus"
            archived.mkdir(parents=True)
            (archived / "14-UAT.md").write_text(
                "---\nstatus: pending\n---\n\nresult: pending\n", encoding="utf-8"
            )
            output = Path(temp_dir) / "closeout.json"
            result = self.run_wrapper(root, output)
            self.assertEqual(result.returncode, 1)
            report = json.loads(output.read_text(encoding="utf-8"))
            raw_uat = report["raw_audit_open"]["payload"]["items"]["uat_gaps"]
            self.assertEqual(sum(item["file"] == "14-UAT.md" for item in raw_uat), 2)
            canonical = [record for record in report["records"] if record.get("raw_item", {}).get("file") == "14-UAT.md"]
            self.assertEqual(len(canonical), 2)
            self.assertTrue(all(record["blocking"] for record in canonical))

    def test_archived_review_is_checked_at_its_exact_archive_source(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gabbaboy-closeout-archive-review-") as temp_dir:
            root = Path(temp_dir) / "project"
            root.mkdir()
            make_fixture(root)
            archived = root / ".planning/milestones/v0.2-phases/GB-14-cgb-e-model-qualification-and-corpus"
            archived.mkdir(parents=True)
            (archived / "14-UAT-REVIEW.md").write_text(
                "---\nstatus: clean\nfindings:\n  critical: 0\n  warning: 1\n  info: 0\n  total: 1\n---\n",
                encoding="utf-8",
            )
            output = Path(temp_dir) / "closeout.json"
            result = self.run_wrapper(root, output)
            self.assertEqual(result.returncode, 1)
            report = json.loads(output.read_text(encoding="utf-8"))
            reviews = [record for record in report["records"] if record.get("raw_item", {}).get("file") == "14-UAT-REVIEW.md"]
            active = next(record for record in reviews if "archived_milestone" not in record["raw_item"])
            archived_review = next(record for record in reviews if record["raw_item"].get("archived_milestone") == "v0.2")
            self.assertEqual(active["classification"], "clean-review")
            self.assertTrue(active["blocking"] is False)
            self.assertEqual(archived_review["classification"], "ambiguous-or-dirty-review")
            self.assertTrue(archived_review["blocking"])

    def test_runtime_failure_retains_diagnostics_without_success_output(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gabbaboy-closeout-runtime-error-") as temp_dir:
            root = Path(temp_dir) / "project"
            root.mkdir()
            (root / ".planning").mkdir()
            fake_tools = Path(temp_dir) / "failing-tools.cjs"
            fake_tools.write_text(
                "const args = process.argv.slice(2);\n"
                "if (args[0] === 'runtime-identity') { console.log(JSON.stringify({packageName:'@opengsd/gsd-core',version:'test'})); process.exit(0); }\n"
                "process.stdout.write('raw audit stdout marker\\n');\n"
                "process.stderr.write('raw audit stderr marker\\n');\n"
                "process.exit(17);\n",
                encoding="utf-8",
            )
            output = Path(temp_dir) / "closeout.json"
            result = self.run_wrapper(root, output, env={"GSD_TOOLS": str(fake_tools)})
            self.assertEqual(result.returncode, 2)
            self.assertIn("REJECT runtime-audit-open", result.stderr)
            self.assertNotIn("CLOSEOUT SCAN CLEAR", result.stdout)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "error")
            self.assertEqual(report["raw_audit_open"]["exit_code"], 17)
            self.assertEqual(report["raw_audit_open"]["stdout"], "raw audit stdout marker\n")
            self.assertEqual(report["raw_audit_open"]["stderr"], "raw audit stderr marker\n")

    def test_missing_runtime_exits_distinctly_instead_of_crashing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gabbaboy-closeout-no-runtime-") as temp_dir:
            root = Path(temp_dir) / "project"
            root.mkdir()
            (root / ".planning").mkdir()
            empty_home = Path(temp_dir) / "empty-home"
            empty_home.mkdir()
            output = Path(temp_dir) / "closeout.json"
            result = self.run_wrapper(
                root,
                output,
                env={
                    "GSD_TOOLS": str(Path(temp_dir) / "absent-tools.cjs"),
                    "HOME": str(empty_home),
                    "CLAUDE_CONFIG_DIR": str(empty_home / "claude"),
                    "CODEX_HOME": str(empty_home / "codex"),
                },
            )
            self.assertEqual(result.returncode, 3, f"no runtime must exit 3: {result.stdout}\n{result.stderr}")
            self.assertIn("runtime-unavailable", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            self.assertNotIn("CLOSEOUT SCAN CLEAR", result.stdout)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["error"]["code"], "runtime-unavailable")


def run_self_test() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CloseoutScanTests)
    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        raise SystemExit(run_self_test())
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="run installed audit-open and classify its findings")
    parser.add_argument("--self-test", action="store_true", help="run real-CLI contract controls")
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    parser.add_argument("--output", type=Path, help="write the complete scan record, including raw runtime output")
    args = parser.parse_args()
    if args.self_test:
        raise SystemExit(run_self_test())
    if not args.check:
        parser.error("--check is required")
    root = args.root.resolve()
    if not root.is_dir() or not (root / ".planning").is_dir():
        parser.error("--root must be a directory containing .planning/")
    report = _scan(root)
    if args.output:
        try:
            _write_report(args.output, report)
        except OSError as exc:
            print(f"REJECT output-write: could not retain scan record: {exc}", file=sys.stderr)
            raise SystemExit(2)
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    if report["status"] == "error":
        error = report.get("error", {})
        print(f"REJECT {error.get('code', 'closeout-scan')}: {error.get('diagnostic', 'scan failed')}", file=sys.stderr)
        raise SystemExit(3 if error.get("code") == "runtime-unavailable" else 2)
    if report["status"] == "blocked":
        print(f"BLOCKED closeout scan: {report['counts']['blocking_records']} classified finding(s)")
        raise SystemExit(1)
    print("CLOSEOUT SCAN CLEAR: no unresolved classified findings")
