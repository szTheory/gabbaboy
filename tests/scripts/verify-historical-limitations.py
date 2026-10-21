#!/usr/bin/env python3
"""Keep fresh evidence and unrecoverable historical facts apart (P7-02, P7-03, P12-01).

Three audit debts name facts that no later run can recover: the audio-saturation
test was never shown red against the pre-fix core (D-027, D-043), one isolated M7
control failure kept no diagnostic (Phase 12 follow-up), and the Libbet Linux
reproduction had no hosted run (D-039). A fresh passing run proves the current
source, not what happened then. This checker holds three records to that line:

  * 15.1-historical-limitations.json  per-item disposition, original text digest
  * 15.1-local-evidence.json          fresh suite, baseline and control results
  * 15.1-hosted-evidence.json         hosted run, job, artifact and log identities

--check validates them against the live scope, decision and source files.
--self-test mutates valid synthetic records one fact at a time and requires each
mutation to be rejected with its own diagnostic code, and valid records to pass.
--produce-local runs the fresh controls and writes the local record.
--produce-historical writes the historical record from the live originals.
A self-test fixture is not hosted, hardware or historical proof.
"""

from __future__ import annotations

import argparse
import copy
import datetime
import hashlib
import json
import os
import pathlib
import platform
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
PHASE_DIR = ROOT / ".planning/phases/GB-15.1-release-hardening-and-milestone-debt-closure"
ITEM_IDS = ("P7-02", "P7-03", "P12-01")
SCHEMA = 1
M7_ATTEMPTS = 100
M7_TESTS = "^cgb_speed_mutant_m7_xfail_ppu(_control)?$"
SAT_DIAG = "loud_peak >= 8192 && loud_peak < INT16_MAX"
SAT_SUCCESS = "ok 1 - audio_saturation"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
SHA40 = re.compile(r"^[0-9a-f]{40}$")
LIBBET_LINE = re.compile(r"^libbet reproduction: identical sha256=([0-9a-f]{64})$")
# The decision rows and the follow-up paragraph that carry the historical facts. Their digests are
# recorded so a later edit of the original wording is noticed rather than silently re-read.
FACT_SOURCES = {
    "P7-02": [("decision_row", "D-039")],
    "P7-03": [("decision_row", "D-027"), ("decision_row", "D-043")],
    "P12-01": [("followup_paragraph", "12-REVIEW-FOLLOWUP")],
}


class Rejected(Exception):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sanitize(text: str) -> str:
    """Strip host paths, user names and credential-shaped words from retained diagnostics."""
    text = text.replace(str(ROOT), "<repo>")
    home = str(pathlib.Path.home())
    text = text.replace(home, "<home>")
    user = os.environ.get("USER") or os.environ.get("USERNAME") or ""
    if len(user) > 2:
        text = re.sub(re.escape(user), "<user>", text)
    text = re.sub(r"\bgh[pousr]_[A-Za-z0-9_]{8,}", "<token>", text)
    text = re.sub(r"(?i)(token|secret|password)=\S+", r"\1=<redacted>", text)
    return text


# --------------------------------------------------------------------------------------------
# Live originals
# --------------------------------------------------------------------------------------------
def load_scope() -> dict[str, str]:
    scope = json.loads((PHASE_DIR / "15.1-SCOPE.json").read_text(encoding="utf-8"))
    return {item["id"]: item["description"] for item in scope["items"] if item["id"] in ITEM_IDS}


def decision_row(decision_id: str) -> str:
    for line in (ROOT / ".planning/context/DECISIONS.md").read_text(encoding="utf-8").splitlines():
        if line.startswith(f"| {decision_id} |"):
            return line
    raise Rejected(f"decision row {decision_id} not found")


def followup_paragraph() -> str:
    path = next((ROOT / ".planning/phases").glob("GB-12-*/12-REVIEW-FOLLOWUP.md"))
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("The earlier `cgb_speed_mutant_m7_xfail_ppu` one-off failure"):
            return line
    raise Rejected("Phase 12 follow-up paragraph not found")


def live_fact_digests() -> dict[str, str]:
    facts = {}
    for decision in ("D-027", "D-039", "D-043"):
        facts[decision] = sha256_text(decision_row(decision))
    facts["12-REVIEW-FOLLOWUP"] = sha256_text(followup_paragraph())
    return facts


def libbet_rom_sha256() -> str:
    return sha256_bytes((ROOT / "fixtures/libbet/libbet.gb").read_bytes())


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args], check=True, capture_output=True, text=True).stdout


class LiveContext:
    """Repository facts the validator consults; the self-test substitutes a synthetic one."""

    def __init__(self) -> None:
        self.scope = load_scope()
        self.facts = live_fact_digests()
        self.rom_sha256 = libbet_rom_sha256()

    def is_ancestor(self, sha: str) -> bool:
        return subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", sha, "HEAD"],
                              capture_output=True).returncode == 0

    def changed_paths(self, old: str, new: str) -> list[str]:
        return [p for p in git("diff", "--name-only", f"{old}..{new}").splitlines() if p]


# --------------------------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------------------------
HISTORIC_KEYS = {
    "P7-03": ("historic_red", "recovered_historic_red", "fresh_sensitivity",
              "historic_unknown_fresh_sensitivity", {"fresh_sensitivity"}),
    "P12-01": ("historic_diagnostic", "recovered_historic_diagnostic", "fresh_repeat",
               "historic_unknown_fresh_controls", {"fresh_repeat", "failure_retention_fixture"}),
}


def validate_item(item_id: str, item: dict | None, doc: dict, local: dict | None, ctx) -> list[str]:
    problems: list[str] = []
    if item is None:
        return [f"missing_item:{item_id}: scope item has no disposition record"]
    original = ctx.scope.get(item_id)
    if item.get("original_text") != original or item.get("original_sha256") != sha256_text(original or ""):
        problems.append(f"original_changed:{item_id}: the recorded audit text differs from the scope original")
    facts = {f.get("ref"): f.get("sha256") for f in item.get("facts", [])}
    for _, ref in FACT_SOURCES[item_id]:
        if facts.get(ref) != ctx.facts.get(ref):
            problems.append(f"fact_digest:{item_id}: {ref} digest differs from the live original")
    if item_id == "P7-02":
        if item.get("historic_status") != "unverified":
            problems.append("historic_status:P7-02: a Linux reproduction is unverified until a hosted run proves it")
        if item.get("disposition") not in ("hosted_verified", "external_limitation"):
            problems.append("disposition:P7-02: must be hosted_verified or external_limitation")
        return problems
    status_key, recovered_key, _, disposition, allowed = HISTORIC_KEYS[item_id]
    if item.get("historic_status") != "unknown" or item.get(status_key) != "unknown":
        problems.append(f"historic_status:{item_id}: the old failing run or diagnostic must stay unknown")
    if item.get(recovered_key) is not False or any(
            k.startswith("recovered") and item.get(k) is not False for k in item):
        problems.append(f"recovered_historic:{item_id}: a fresh run cannot claim to recover missing history")
    if item.get("disposition") != disposition:
        problems.append(f"disposition:{item_id}: must be {disposition}")
    fresh = item.get("fresh_evidence", [])
    kinds = set()
    for entry in fresh:
        kind = entry.get("kind")
        if kind not in allowed:
            problems.append(f"fresh_kind:{item_id}: {kind!r} is not fresh evidence for this item")
            continue
        kinds.add(kind)
        control = ((local or {}).get("controls") or {}).get(entry.get("local_ref"))
        if not control or control.get("kind") != kind:
            problems.append(f"fresh_ref:{item_id}: {entry.get('local_ref')!r} is not a {kind} control in the local record")
    for missing in sorted(allowed - kinds):
        problems.append(f"fresh_missing:{item_id}: no {missing} evidence is referenced")
    return problems


def validate_local(local: dict | None, doc: dict) -> list[str]:
    if local is None:
        return ["local_missing: the local evidence record is required"]
    problems: list[str] = []
    if local.get("schema") != SCHEMA:
        problems.append("local_schema: unsupported schema")
    if not SHA40.match(str(local.get("source_sha", ""))) or local.get("source_sha") != doc.get("source_sha"):
        problems.append("local_source: local evidence is not bound to the recorded tested source")
    if local.get("tracked_clean") is not True:
        problems.append("local_dirty: the run was not made on a clean tracked tree")
    toolchain = local.get("toolchain") or {}
    if not all(toolchain.get(k) for k in ("cmake", "cc", "python", "system")):
        problems.append("local_toolchain: toolchain identity is incomplete")
    commands = {c.get("id"): c for c in local.get("commands", [])}
    suite = commands.get("ctest_full")
    if not suite:
        problems.append("ctest_missing: the full suite run is absent")
    else:
        if suite.get("exit") != 0 or suite.get("result") != "pass":
            problems.append("ctest_failed: the full suite did not pass")
        if suite.get("tests_failed") != 0:
            problems.append("ctest_failed: failing tests are recorded")
        total, passed = suite.get("tests_total"), suite.get("tests_passed")
        if not isinstance(total, int) or total < 1 or passed != total:
            problems.append(f"ctest_count: passed {passed!r} of {total!r}")
        if suite.get("tests_not_run") != 0:
            problems.append("ctest_not_run: skipped or not-run tests are recorded")
        if not HEX64.match(str(suite.get("log_sha256", ""))) or not suite.get("seconds", 0) > 0:
            problems.append("ctest_log: log digest or duration is missing")
    baseline = commands.get("dmg_baseline")
    if not baseline or baseline.get("exit") != 0 or baseline.get("result") != "pass" \
            or not HEX64.match(str(baseline.get("log_sha256", ""))):
        problems.append("dmg_baseline: the frozen DMG baseline did not pass with a retained log")
    controls = local.get("controls") or {}
    audio = controls.get("audio_saturation") or {}
    if audio.get("kind") != "fresh_sensitivity" or not audio.get("mutation"):
        problems.append("audio_control: the saturation sensitivity record is missing or unlabelled")
    if audio.get("control_exit") != 0 or audio.get("control_success_line") is not True:
        problems.append("audio_control: the unmutated source did not pass the saturation test")
    if audio.get("mutant_exit") in (0, None):
        problems.append("audio_mutant_survived: reintroducing the pre-fix scaling did not fail the test")
    if SAT_DIAG not in str(audio.get("mutant_diagnostic", "")):
        problems.append("audio_mutant_diagnostic: the mutant did not fail on the headroom assertion")
    if audio.get("mutant_success_output_absent") is not True:
        problems.append("audio_success_output: the mutant printed the success line")
    repeats = controls.get("m7_repeats") or {}
    entries = repeats.get("entries") or []
    if repeats.get("kind") != "fresh_repeat" or repeats.get("attempts") != M7_ATTEMPTS \
            or len(entries) != M7_ATTEMPTS \
            or repeats.get("passed") != sum(1 for e in entries if e.get("exit") == 0) \
            or repeats.get("passed", 0) + repeats.get("failed", 0) != M7_ATTEMPTS:
        problems.append(f"m7_attempts: need {M7_ATTEMPTS} consistently recorded attempts")
    if repeats.get("tests_matched") != 2:
        problems.append("m7_attempts: the selector must match exactly the M7 mutant and its control")
    if repeats.get("failed") != 0:
        problems.append("m7_failed: a fresh M7 attempt failed; the pass disposition does not hold")
    for entry in entries:
        if entry.get("exit") != 0 and not (entry.get("retained") and HEX64.match(str(entry.get("retained_sha256", "")))
                                           and entry.get("retained_bytes", 0) > 0):
            problems.append(f"m7_unretained: failing attempt {entry.get('attempt')} kept no diagnostic")
    retention = controls.get("m7_retention") or {}
    if retention.get("kind") != "failure_retention_fixture" or retention.get("diagnostic_retained") is not True \
            or retention.get("retained_contains_marker") is not True \
            or not HEX64.match(str(retention.get("retained_sha256", ""))) \
            or not isinstance(retention.get("failed_attempt"), int) \
            or not 1 <= retention["failed_attempt"] <= retention.get("attempts", 0):
        problems.append("m7_retention_fixture: a provoked failure did not retain its diagnostic")
    return problems


def validate_workflow(rec: dict, hosted: dict, ctx) -> list[str]:
    wid = rec.get("id")
    problems: list[str] = []
    if rec.get("claim") == "verified":
        if rec.get("status") != "completed" or rec.get("conclusion") != "success":
            problems.append(f"hosted_conclusion:{wid}: run is {rec.get('status')}/{rec.get('conclusion')}, not completed/success")
        if not isinstance(rec.get("run_id"), int) or rec.get("run_id", 0) < 1:
            problems.append(f"hosted_run:{wid}: run id is missing")
        if not isinstance(rec.get("run_attempt"), int) or rec.get("run_attempt", 0) < 1:
            problems.append(f"hosted_attempt:{wid}: run attempt is missing")
        if rec.get("head_sha") != hosted.get("source_sha"):
            problems.append(f"hosted_head:{wid}: run head differs from the pushed source")
        jobs = rec.get("jobs") or []
        if not jobs or any(j.get("status") != "completed" or j.get("conclusion") != "success" for j in jobs):
            problems.append(f"hosted_job:{wid}: a job is absent, skipped or not successful")
        if not HEX64.match(str(rec.get("log_sha256", ""))):
            problems.append(f"hosted_log:{wid}: downloaded log digest is missing")
        if wid == "libbet-repro":
            match = LIBBET_LINE.match(str(rec.get("result_line", "")))
            if not match or match.group(1) != ctx.rom_sha256:
                problems.append("hosted_result:libbet-repro: log result is not an identical rebuild of the vendored ROM")
        if wid == "release-rehearsal":
            artifacts = rec.get("artifacts") or []
            if not artifacts or any(not re.fullmatch(r"sha256:[0-9a-f]{64}", str(a.get("digest", "")))
                                    or not a.get("id") for a in artifacts):
                problems.append("hosted_artifact:release-rehearsal: producer artifacts lack identity or digest")
    elif rec.get("claim") == "not_verified":
        if not str(rec.get("limitation", "")).strip():
            problems.append(f"limitation_empty:{wid}: an unverified hosted record must state why")
        if rec.get("status") == "completed" and rec.get("conclusion") == "success":
            problems.append(f"limitation_claims_pass:{wid}: a successful run cannot be recorded as unverified")
    else:
        problems.append(f"hosted_claim:{wid}: claim must be verified or not_verified")
    return problems


def validate(doc: dict, local: dict | None, hosted: dict | None, ctx) -> list[str]:
    problems: list[str] = []
    if doc.get("schema") != SCHEMA:
        problems.append("schema: unsupported historical-limitations schema")
    if not SHA40.match(str(doc.get("source_sha", ""))):
        problems.append("source_sha: tested source must be a full commit id")
    elif not ctx.is_ancestor(doc["source_sha"]):
        problems.append("source_sha: tested source is not an ancestor of HEAD")
    items = {i.get("id"): i for i in doc.get("items", [])}
    for item_id in ITEM_IDS:
        problems += validate_item(item_id, items.get(item_id), doc, local, ctx)
    problems += validate_local(local, doc)

    libbet_item = items.get("P7-02") or {}
    if hosted is None:
        problems.append("hosted_missing: the hosted evidence record is required")
        return problems
    if hosted.get("obtained_via") != "gh_api":
        problems.append("hosted_obtained: identities must be read from the hosting API, not a submitted receipt")
    if hosted.get("receipt_labels_used") is not False:
        problems.append("hosted_receipt_label: run identity was taken from a receipt label")
    if not SHA40.match(str(hosted.get("source_sha", ""))):
        problems.append("hosted_source: pushed source must be a full commit id")
    else:
        if hosted.get("tested_source_sha") != doc.get("source_sha"):
            problems.append("hosted_tested_source: hosted record is not bound to the locally tested source")
        elif hosted["source_sha"] != doc.get("source_sha"):
            drift = [p for p in ctx.changed_paths(doc["source_sha"], hosted["source_sha"])
                     if not p.startswith(".planning/")]
            if drift:
                problems.append(f"covered_drift: {len(drift)} covered path(s) changed between the tested and pushed source")
    records = {w.get("id"): w for w in hosted.get("workflows", [])}
    for wid in ("libbet-repro", "release-rehearsal"):
        if wid not in records:
            problems.append(f"hosted_missing:{wid}: no record, not even an unverified one")
        else:
            problems += validate_workflow(records[wid], hosted, ctx)
    record = records.get(libbet_item.get("hosted_ref"))
    if libbet_item.get("disposition") == "hosted_verified":
        if not record or record.get("claim") != "verified":
            problems.append("limitation_not_hosted: hosted_verified needs a verified libbet-repro record")
    elif libbet_item.get("disposition") == "external_limitation":
        if not str(libbet_item.get("limitation", "")).strip():
            problems.append("limitation_empty:P7-02: an external limitation must say what blocks qualification")
        if record and record.get("claim") == "verified":
            problems.append("limitation_claims_pass:P7-02: limitation cites a record that claims a pass")
    return problems


# --------------------------------------------------------------------------------------------
# Fresh controls
# --------------------------------------------------------------------------------------------
def run_attempts(command: list[str], count: int, retain_dir: pathlib.Path) -> dict:
    """Run a command `count` times. Every failing attempt keeps its sanitized output on disk."""
    attempts = []
    retain_dir.mkdir(parents=True, exist_ok=True)
    for number in range(1, count + 1):
        start = datetime.datetime.now(datetime.timezone.utc)
        proc = subprocess.run(command, capture_output=True, text=True)
        seconds = (datetime.datetime.now(datetime.timezone.utc) - start).total_seconds()
        output = sanitize(proc.stdout + proc.stderr)
        entry = {"attempt": number, "exit": proc.returncode, "seconds": round(seconds, 3),
                 "output_sha256": sha256_text(output)}
        if proc.returncode != 0:
            retained = retain_dir / f"attempt-{number:03d}.txt"
            retained.write_text(output, encoding="utf-8")
            entry["retained"] = retained.name
            entry["retained_sha256"] = sha256_text(output)
            entry["retained_bytes"] = len(output.encode("utf-8"))
        attempts.append(entry)
    return {"attempts": count, "passed": sum(1 for a in attempts if a["exit"] == 0),
            "failed": sum(1 for a in attempts if a["exit"] != 0), "entries": attempts}


def retention_fixture(tmp: pathlib.Path) -> dict:
    """Provoke a failure on attempt 2 of 3 and prove the sanitized diagnostic stays on disk."""
    marker = tmp / "count"
    script = ("import pathlib,sys\n"
              f"p=pathlib.Path({str(marker)!r}); n=int(p.read_text())+1 if p.exists() else 1\n"
              "p.write_text(str(n))\n"
              "if n==2: print('DIAG-MARKER failure on attempt 2'); sys.exit(1)\n")
    result = run_attempts([sys.executable, "-I", "-c", script], 3, tmp / "retained")
    failed = [e for e in result["entries"] if e["exit"] != 0]
    if len(failed) != 1 or failed[0]["attempt"] != 2 or "retained" not in failed[0]:
        raise Rejected(f"retention fixture did not keep the failing attempt: {result}")
    text = (tmp / "retained" / failed[0]["retained"]).read_text(encoding="utf-8")
    if "DIAG-MARKER" not in text or sha256_text(text) != failed[0]["retained_sha256"]:
        raise Rejected("retained diagnostic is missing its marker or digest")
    if any("retained" in e for e in result["entries"] if e["exit"] == 0):
        raise Rejected("a passing attempt retained output")
    return {"kind": "failure_retention_fixture", "attempts": 3, "failed_attempt": 2,
            "diagnostic_retained": True, "retained_sha256": failed[0]["retained_sha256"],
            "retained_contains_marker": True}


def has_success_line(text: str) -> bool:
    """True only for the exact TAP success line; 'not ok 1 - ...' contains it as a substring."""
    return any(line.strip() == SAT_SUCCESS for line in text.splitlines())


def audio_saturation_sensitivity() -> dict:
    """Reintroduce the pre-fix mixer scaling in a scratch copy and require the saturation test to fail.

    This is fresh sensitivity evidence about the current test. It is not the missing pre-fix red run
    from 07-03 (D-043): that run never happened and cannot be recovered."""
    compiler = shutil.which("cc") or shutil.which("gcc") or shutil.which("clang")
    if not compiler:
        raise Rejected("no C compiler for the saturation mutation")
    source = (ROOT / "src/core/gabbaboy.c").read_text(encoding="utf-8")
    fixed = "#define GBB_AUDIO_MIX_HEADROOM_DIV 16\n"
    if source.count(fixed) != 1:
        raise Rejected("the headroom divisor definition is not unique; update the mutation anchor")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = pathlib.Path(tmp)
        results = {}
        for name, text in (("control", source),
                           ("mutant", source.replace(fixed, "#define GBB_AUDIO_MIX_HEADROOM_DIV 1\n"))):
            core = tmp_path / f"{name}.c"
            core.write_text(text, encoding="utf-8")
            exe = tmp_path / f"test_audio_{name}"
            build = subprocess.run([compiler, "-std=c17", f"-I{ROOT / 'include'}", f"-I{ROOT / 'src/core'}",
                                    str(ROOT / "tests/test_audio.c"), str(core), "-o", str(exe)],
                                   capture_output=True, text=True)
            if build.returncode != 0:
                raise Rejected(f"saturation {name} did not compile: {sanitize(build.stderr)[:400]}")
            run = subprocess.run([str(exe), "audio_saturation"], capture_output=True, text=True, cwd=ROOT)
            results[name] = (run.returncode, sanitize(run.stdout + run.stderr))
    diagnostic = next((line for line in results["mutant"][1].splitlines() if SAT_DIAG in line), "")
    return {
        "kind": "fresh_sensitivity",
        "mutation": "GBB_AUDIO_MIX_HEADROOM_DIV 16 -> 1",
        "control_exit": results["control"][0], "control_success_line": has_success_line(results["control"][1]),
        "mutant_exit": results["mutant"][0], "mutant_diagnostic": diagnostic,
        "mutant_success_output_absent": not has_success_line(results["mutant"][1]),
    }


def tool_version(command: list[str]) -> str:
    try:
        out = subprocess.run(command, capture_output=True, text=True).stdout
    except OSError:
        return ""
    return sanitize(out.splitlines()[0]) if out else ""


def parse_ctest(text: str) -> dict:
    # CTest prints "100% tests passed out of N" when nothing failed and
    # "P% tests passed, F tests failed out of N" otherwise; accept exactly those two forms.
    clean = re.search(r"^100% tests passed out of (\d+)$", text, re.M)
    summary = re.search(r"^(\d+)% tests passed, (\d+) tests failed out of (\d+)$", text, re.M)
    if clean:
        failed, total = 0, int(clean.group(1))
    elif summary:
        failed, total = int(summary.group(2)), int(summary.group(3))
    else:
        raise Rejected("ctest summary line not found in the log")
    seconds = re.search(r"Total Test time \(real\) =\s+([0-9.]+) sec", text)
    return {"tests_total": total, "tests_failed": failed, "tests_passed": total - failed,
            "tests_not_run": len(re.findall(r"\*\*\*(?:Not Run|Skipped)", text)),
            "ctest_seconds": float(seconds.group(1)) if seconds else 0.0}


def produce_local(args) -> int:
    if not (args.build_dir and args.out and args.source_sha and args.retain_dir):
        raise Rejected("--produce-local requires --build-dir, --source-sha, --out and --retain-dir")
    head = git("rev-parse", "HEAD").strip()
    if args.source_sha != head:
        raise Rejected("the tested source must be the current HEAD")
    dirty = [line for line in git("status", "--porcelain", "--untracked-files=no").splitlines()
             if not line[3:].startswith(".planning/")]
    if dirty:
        raise Rejected(f"tracked non-planning files are modified: {len(dirty)}")
    commands = []
    for spec in args.command:
        cid, _, log = spec.partition("=")
        log_path = pathlib.Path(log)
        meta = json.loads(pathlib.Path(str(log_path) + ".meta").read_text(encoding="utf-8"))
        text = log_path.read_text(encoding="utf-8", errors="replace")
        entry = {"id": cid, "command": sanitize(meta["command"]), "exit": meta["exit"],
                 "seconds": meta["seconds"], "log_sha256": sha256_bytes(log_path.read_bytes())}
        if cid == "ctest_full":
            parsed = parse_ctest(text)
            entry.update(parsed)
            entry["seconds"] = parsed["ctest_seconds"] or entry["seconds"]
            entry["result"] = "pass" if meta["exit"] == 0 and parsed["tests_failed"] == 0 else "fail"
        else:
            entry["result"] = "pass" if meta["exit"] == 0 else "fail"
        commands.append(entry)
    audio = audio_saturation_sensitivity()
    if audio["control_exit"] != 0:
        raise Rejected("the unmutated saturation control failed")
    repeats = run_attempts(
        ["ctest", "--test-dir", str(args.build_dir), "-R", M7_TESTS, "--no-tests=error", "--output-on-failure"],
        M7_ATTEMPTS, args.retain_dir)
    listing = subprocess.run(["ctest", "--test-dir", str(args.build_dir), "-N", "-R", M7_TESTS],
                             capture_output=True, text=True).stdout
    repeats.update(kind="fresh_repeat", tests=M7_TESTS,
                   tests_matched=int(re.search(r"Total Tests: (\d+)", listing).group(1)))
    with tempfile.TemporaryDirectory() as tmp:
        retention = retention_fixture(pathlib.Path(tmp))
    record = {
        "schema": SCHEMA, "source_sha": head, "tracked_clean": True,
        "toolchain": {"cmake": tool_version(["cmake", "--version"]), "cc": tool_version(["cc", "--version"]),
                      "python": platform.python_version(),
                      "system": f"{platform.system()} {platform.machine()}"},
        "commands": commands,
        "controls": {"audio_saturation": audio, "m7_repeats": repeats, "m7_retention": retention},
        "historic_claims": "none: fresh runs prove the current source only",
    }
    args.out.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"local-evidence written source={head[:12]} m7_passed={repeats['passed']}/{repeats['attempts']} "
          f"audio_mutant_exit={audio['mutant_exit']}")
    return 0


def produce_historical(args) -> int:
    if not (args.local and args.hosted and args.out):
        raise Rejected("--produce-historical requires --local, --hosted and --out")
    ctx = LiveContext()
    local = json.loads(args.local.read_text(encoding="utf-8"))
    hosted = json.loads(args.hosted.read_text(encoding="utf-8"))
    libbet = next(w for w in hosted["workflows"] if w["id"] == "libbet-repro")
    items = []
    for item_id in ITEM_IDS:
        item = {"id": item_id, "source": ".planning/v0.2-MILESTONE-AUDIT.md",
                "original_text": ctx.scope[item_id], "original_sha256": sha256_text(ctx.scope[item_id]),
                "facts": [{"ref": ref, "sha256": ctx.facts[ref]} for _, ref in FACT_SOURCES[item_id]]}
        if item_id == "P7-02":
            item["historic_status"] = "unverified"
            item["hosted_ref"] = "libbet-repro"
            if libbet["claim"] == "verified":
                item["disposition"] = "hosted_verified"
            else:
                item["disposition"] = "external_limitation"
                item["limitation"] = libbet["limitation"]
        elif item_id == "P7-03":
            item.update(historic_status="unknown", historic_red="unknown", recovered_historic_red=False,
                        disposition="historic_unknown_fresh_sensitivity",
                        fresh_evidence=[{"kind": "fresh_sensitivity", "local_ref": "audio_saturation"}])
        else:
            item.update(historic_status="unknown", historic_diagnostic="unknown",
                        recovered_historic_diagnostic=False, disposition="historic_unknown_fresh_controls",
                        fresh_evidence=[{"kind": "fresh_repeat", "local_ref": "m7_repeats"},
                                        {"kind": "failure_retention_fixture", "local_ref": "m7_retention"}])
        items.append(item)
    doc = {"schema": SCHEMA, "plan": "15.1-16", "source_sha": local["source_sha"],
           "local_evidence": args.local.name, "hosted_evidence": args.hosted.name, "items": items}
    args.out.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print(f"historical-limitations written items={len(items)}")
    return 0


# --------------------------------------------------------------------------------------------
# Self-test
# --------------------------------------------------------------------------------------------
class SyntheticContext:
    def __init__(self) -> None:
        self.scope = {i: f"original text of {i}" for i in ITEM_IDS}
        self.facts = {k: sha256_text(k) for k in ("D-027", "D-039", "D-043", "12-REVIEW-FOLLOWUP")}
        self.rom_sha256 = sha256_text("rom")
        self.ancestors = {"a" * 40, "b" * 40}
        self.changes: dict[tuple[str, str], list[str]] = {}

    def is_ancestor(self, sha: str) -> bool:
        return sha in self.ancestors

    def changed_paths(self, old: str, new: str) -> list[str]:
        return self.changes.get((old, new), [])


SOURCE = "a" * 40
PUSHED = "b" * 40


def synthetic_local() -> dict:
    entries = [{"attempt": n, "exit": 0, "seconds": 0.05, "output_sha256": sha256_text(str(n))}
               for n in range(1, M7_ATTEMPTS + 1)]
    return {
        "schema": SCHEMA,
        "source_sha": SOURCE,
        "tracked_clean": True,
        "toolchain": {"cmake": "cmake version 4.0.0", "cc": "cc 1", "python": "3.14", "system": "Test arm64"},
        "commands": [
            {"id": "ctest_full", "command": "ctest --preset phase1 --output-on-failure --no-tests=error",
             "exit": 0, "result": "pass", "seconds": 440.0, "log_sha256": sha256_text("ctest"),
             "tests_total": 1170, "tests_passed": 1170, "tests_failed": 0, "tests_not_run": 0},
            {"id": "dmg_baseline", "command": "bash tests/scripts/verify-dmg-baseline.sh --build-dir build",
             "exit": 0, "result": "pass", "seconds": 30.0, "log_sha256": sha256_text("dmg")},
        ],
        "controls": {
            "audio_saturation": {
                "kind": "fresh_sensitivity",
                "mutation": "GBB_AUDIO_MIX_HEADROOM_DIV 16 -> 1",
                "control_exit": 0, "control_success_line": True, "mutant_exit": 1,
                "mutant_diagnostic": "tests/test_audio.c:378: " + SAT_DIAG,
                "mutant_success_output_absent": True,
            },
            "m7_repeats": {
                "kind": "fresh_repeat", "tests": M7_TESTS,
                "tests_matched": 2, "attempts": M7_ATTEMPTS, "passed": M7_ATTEMPTS, "failed": 0,
                "entries": entries,
            },
            "m7_retention": {
                "kind": "failure_retention_fixture", "attempts": 3, "failed_attempt": 2,
                "diagnostic_retained": True, "retained_sha256": sha256_text("fixture diagnostic"),
                "retained_contains_marker": True,
            },
        },
    }


def synthetic_hosted(verified: bool = True) -> dict:
    libbet = {
        "id": "libbet-repro", "workflow_path": ".github/workflows/libbet-repro.yml",
        "run_id": 1001, "run_attempt": 1, "event": "workflow_dispatch", "head_sha": PUSHED,
        "head_branch": "gsd/phase", "status": "completed", "conclusion": "success",
        "jobs": [{"id": 2001, "name": "libbet-repro", "status": "completed", "conclusion": "success"}],
        "log_sha256": sha256_text("libbet log"),
        "result_line": "libbet reproduction: identical sha256=" + sha256_text("rom"),
        "claim": "verified",
    }
    rehearsal = {
        "id": "release-rehearsal", "workflow_path": ".github/workflows/release-rehearsal.yml",
        "run_id": 1002, "run_attempt": 1, "event": "push", "head_sha": PUSHED,
        "head_branch": "rehearsal/x", "status": "completed", "conclusion": "success",
        "jobs": [{"id": 2002, "name": "rehearse-corpus-and-support-sidecar", "status": "completed",
                  "conclusion": "success"}],
        "artifacts": [{"name": "support-ledger", "id": 3001, "size": 10, "digest": "sha256:" + "c" * 64}],
        "log_sha256": sha256_text("rehearsal log"), "claim": "verified",
    }
    if not verified:
        for rec in (libbet, rehearsal):
            rec.update(claim="not_verified", conclusion="failure",
                       limitation="the judge job reads the default branch")
            rec["jobs"][0]["conclusion"] = "failure"
            rec.pop("result_line", None)
    return {"schema": SCHEMA, "source_sha": PUSHED, "tested_source_sha": SOURCE,
            "obtained_via": "gh_api", "receipt_labels_used": False, "workflows": [libbet, rehearsal]}


def synthetic_historical(hosted_verified: bool = True) -> dict:
    ctx = SyntheticContext()
    items = []
    for item_id in ITEM_IDS:
        item = {
            "id": item_id, "source": ".planning/v0.2-MILESTONE-AUDIT.md",
            "original_text": ctx.scope[item_id], "original_sha256": sha256_text(ctx.scope[item_id]),
            "facts": [{"ref": ref, "sha256": ctx.facts[ref]}
                      for _, ref in FACT_SOURCES[item_id]],
        }
        if item_id == "P7-02":
            item["historic_status"] = "unverified"
            if hosted_verified:
                item.update(disposition="hosted_verified", hosted_ref="libbet-repro")
            else:
                item.update(disposition="external_limitation", hosted_ref="libbet-repro",
                            limitation="the hosted run did not complete as a pass; local macOS reproduction only")
        elif item_id == "P7-03":
            item.update(historic_status="unknown", historic_red="unknown", recovered_historic_red=False,
                        disposition="historic_unknown_fresh_sensitivity",
                        fresh_evidence=[{"kind": "fresh_sensitivity", "local_ref": "audio_saturation"}])
        else:
            item.update(historic_status="unknown", historic_diagnostic="unknown",
                        recovered_historic_diagnostic=False,
                        disposition="historic_unknown_fresh_controls",
                        fresh_evidence=[{"kind": "fresh_repeat", "local_ref": "m7_repeats"},
                                        {"kind": "failure_retention_fixture", "local_ref": "m7_retention"}])
        items.append(item)
    return {"schema": SCHEMA, "plan": "15.1-16", "source_sha": SOURCE, "items": items}


def item_of(doc: dict, item_id: str) -> dict:
    return next(i for i in doc["items"] if i["id"] == item_id)


def self_test() -> int:
    ctx = SyntheticContext()
    ctx.changes[(SOURCE, PUSHED)] = [".planning/phases/x/15.1-16-SUMMARY.md"]
    positives = 0
    for verified in (True, False):
        problems = validate(synthetic_historical(verified), synthetic_local(), synthetic_hosted(verified), ctx)
        if problems:
            raise Rejected(f"valid synthetic records (hosted_verified={verified}) were rejected: {problems}")
        positives += 1

    # (code, mutation) where a mutation edits deep copies of (doc, local, hosted).
    def doc_(fn):
        return lambda d, l, h: fn(d)

    def local_(fn):
        return lambda d, l, h: fn(l)

    def hosted_(fn):
        return lambda d, l, h: fn(h)

    def ctl(l, name):
        return l["controls"][name]

    def cmd(l, cid):
        return next(c for c in l["commands"] if c["id"] == cid)

    def wf(h, wid):
        return next(w for w in h["workflows"] if w["id"] == wid)

    controls: list[tuple[str, object, bool]] = [
        # historical facts must stay unknown and immutable
        ("recovered_historic:P7-03", doc_(lambda d: item_of(d, "P7-03").update(recovered_historic_red=True)), True),
        ("historic_status:P7-03", doc_(lambda d: item_of(d, "P7-03").update(historic_red="red")), True),
        ("fresh_kind:P7-03", doc_(lambda d: item_of(d, "P7-03")["fresh_evidence"].append(
            {"kind": "historic_red", "local_ref": "audio_saturation"})), True),
        ("recovered_historic:P12-01", doc_(lambda d: item_of(d, "P12-01").update(
            recovered_historic_diagnostic=True)), True),
        ("historic_status:P12-01", doc_(lambda d: item_of(d, "P12-01").update(
            historic_diagnostic="captured")), True),
        ("fresh_kind:P12-01", doc_(lambda d: item_of(d, "P12-01")["fresh_evidence"].append(
            {"kind": "historic_diagnostic", "local_ref": "m7_repeats"})), True),
        ("original_changed:P7-03", doc_(lambda d: item_of(d, "P7-03").update(
            original_text="rewritten", original_sha256=sha256_text("rewritten"))), True),
        ("fact_digest:P12-01", doc_(lambda d: item_of(d, "P12-01")["facts"][0].update(sha256="0" * 64)), True),
        ("missing_item:P12-01", doc_(lambda d: d["items"].remove(item_of(d, "P12-01"))), True),
        ("fresh_ref:P7-03", doc_(lambda d: item_of(d, "P7-03")["fresh_evidence"][0].update(local_ref="absent")), True),
        ("local_source", lambda d, l, h: l.update(source_sha="d" * 40), True),
        # fresh suite and baseline
        ("ctest_failed", local_(lambda l: cmd(l, "ctest_full").update(tests_failed=1, tests_passed=1169)), True),
        ("ctest_count", local_(lambda l: cmd(l, "ctest_full").update(tests_passed=1000)), True),
        ("ctest_not_run", local_(lambda l: cmd(l, "ctest_full").update(tests_not_run=2)), True),
        ("dmg_baseline", local_(lambda l: cmd(l, "dmg_baseline").update(result="fail", exit=1)), True),
        # fresh sensitivity: the intended mutation must be caught, with its own diagnostic
        ("audio_mutant_survived", local_(lambda l: ctl(l, "audio_saturation").update(mutant_exit=0)), True),
        ("audio_mutant_diagnostic", local_(lambda l: ctl(l, "audio_saturation").update(
            mutant_diagnostic="unrelated failure")), True),
        ("audio_success_output", local_(lambda l: ctl(l, "audio_saturation").update(
            mutant_success_output_absent=False)), True),
        ("audio_control", local_(lambda l: ctl(l, "audio_saturation").update(control_exit=1)), True),
        ("audio_control", local_(lambda l: ctl(l, "audio_saturation").update(control_success_line=False)), True),
        ("m7_attempts", local_(lambda l: ctl(l, "m7_repeats").update(tests_matched=0)), True),
        # M7 repeats and diagnostic retention
        ("m7_attempts", local_(lambda l: ctl(l, "m7_repeats").update(attempts=99)), True),
        ("m7_unretained", local_(lambda l: (
            ctl(l, "m7_repeats")["entries"][4].update(exit=1),
            ctl(l, "m7_repeats").update(passed=99, failed=1))), True),
        ("m7_retention_fixture", local_(lambda l: ctl(l, "m7_retention").update(diagnostic_retained=False)), True),
        # hosted identities
        ("hosted_missing", lambda d, l, h: (h.update(workflows=[w for w in h["workflows"]
                                                                if w["id"] != "libbet-repro"])), True),
        ("hosted_head", hosted_(lambda h: wf(h, "libbet-repro").update(head_sha="e" * 40)), True),
        ("hosted_conclusion", hosted_(lambda h: wf(h, "libbet-repro").update(conclusion="skipped")), True),
        ("hosted_job", hosted_(lambda h: wf(h, "libbet-repro").update(jobs=[])), True),
        ("hosted_job", hosted_(lambda h: wf(h, "libbet-repro")["jobs"][0].update(conclusion="skipped")), True),
        ("hosted_log", hosted_(lambda h: wf(h, "libbet-repro").pop("log_sha256")), True),
        ("hosted_result", hosted_(lambda h: wf(h, "libbet-repro").update(
            result_line="libbet reproduction: identical sha256=" + "9" * 64)), True),
        ("hosted_result", hosted_(lambda h: wf(h, "libbet-repro").update(
            result_line="libbet reproduction: differs built=1 vendored=2")), True),
        ("hosted_artifact", hosted_(lambda h: wf(h, "release-rehearsal")["artifacts"][0].pop("digest")), True),
        ("hosted_receipt_label", hosted_(lambda h: h.update(receipt_labels_used=True)), True),
        ("hosted_obtained", hosted_(lambda h: h.update(obtained_via="receipt")), True),
        ("hosted_attempt", hosted_(lambda h: wf(h, "libbet-repro").update(run_attempt=0)), True),
    ]
    rejected = 0
    for code, mutate, _ in controls:
        d, l, h = synthetic_historical(True), synthetic_local(), synthetic_hosted(True)
        mutate(d, l, h)
        problems = validate(d, l, h, ctx)
        if not any(p.startswith(code) for p in problems):
            raise Rejected(f"intended defect {code!r} was not rejected with its own diagnostic: {problems}")
        rejected += 1

    drift_ctx = SyntheticContext()
    drift_ctx.changes[(SOURCE, PUSHED)] = ["src/core/gabbaboy.c"]
    drift = validate(synthetic_historical(True), synthetic_local(), synthetic_hosted(True), drift_ctx)
    if not any(p.startswith("covered_drift") for p in drift):
        raise Rejected(f"covered-input drift between tested and hosted source was accepted: {drift}")
    rejected += 1

    # limitation variants: an external limitation must say why and must not claim a pass
    limitation_controls = [
        ("limitation_empty", lambda d, l, h: item_of(d, "P7-02").update(limitation="")),
        ("limitation_claims_pass", lambda d, l, h: wf(h, "libbet-repro").update(
            claim="verified", conclusion="success")),
        ("limitation_not_hosted", lambda d, l, h: item_of(d, "P7-02").update(disposition="hosted_verified")),
    ]
    for code, mutate in limitation_controls:
        d, l, h = synthetic_historical(False), synthetic_local(), synthetic_hosted(False)
        mutate(d, l, h)
        problems = validate(d, l, h, ctx)
        if not any(p.startswith(code) for p in problems):
            raise Rejected(f"intended defect {code!r} was not rejected with its own diagnostic: {problems}")
        rejected += 1

    # a failing TAP line must not pass for the success line it contains
    if not has_success_line("1..1\nok 1 - audio_saturation\n") or has_success_line(
            "1..1\nnot ok 1 - audio_saturation\n"):
        raise Rejected("success-line detector confused 'not ok' with 'ok'")

    # the suite log parser: both CTest summary forms, and nothing else, count as a result
    clean = parse_ctest("100% tests passed out of 12\nTotal Test time (real) =   3.50 sec\n")
    failing = parse_ctest("99% tests passed, 1 tests failed out of 12\n   1 - x (Failed)\n")
    notrun = parse_ctest("100% tests passed out of 12\n  3/12 Test #3: a ...***Skipped\n")
    if (clean["tests_total"], clean["tests_failed"], clean["tests_passed"]) != (12, 0, 12) \
            or (failing["tests_failed"], failing["tests_passed"]) != (1, 11) or notrun["tests_not_run"] != 1:
        raise Rejected(f"suite log parser misread a summary: {clean} {failing} {notrun}")
    for bad in ("", "tests passed\n", "50% tests passed\n"):
        try:
            parse_ctest(bad)
        except Rejected:
            continue
        raise Rejected(f"suite log parser accepted a log without a summary line: {bad!r}")

    # the retention plumbing: a failing attempt must keep its sanitized diagnostic on disk
    with tempfile.TemporaryDirectory() as tmp:
        retention_fixture(pathlib.Path(tmp))

    print(f"historical-limitations self-test pass positives={positives} rejected_controls={rejected} "
          "retention_fixture=1")
    return 0


# --------------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------------
def check(evidence: pathlib.Path, strict_head: bool) -> int:
    doc = json.loads(evidence.read_text(encoding="utf-8"))
    base = evidence.parent
    local = json.loads((base / doc["local_evidence"]).read_text(encoding="utf-8")) if doc.get("local_evidence") else None
    hosted = json.loads((base / doc["hosted_evidence"]).read_text(encoding="utf-8")) if doc.get("hosted_evidence") else None
    ctx = LiveContext()
    problems = validate(doc, local, hosted, ctx)
    if strict_head and doc.get("source_sha"):
        drift = [p for p in ctx.changed_paths(doc["source_sha"], "HEAD") if not p.startswith(".planning/")]
        if drift:
            problems.append(f"covered_drift_head: {len(drift)} covered path(s) changed since the tested source")
    if problems:
        for problem in problems:
            print(f"historical-limitations rejected: {problem}", file=sys.stderr)
        return 1
    dispositions = ",".join(f"{i['id']}={i['disposition']}" for i in doc["items"])
    print(f"historical-limitations pass items={len(doc['items'])} {dispositions}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--evidence", type=pathlib.Path)
    parser.add_argument("--strict-head", action="store_true",
                        help="also fail when covered (non-.planning) paths changed since the tested source")
    parser.add_argument("--produce-local", action="store_true")
    parser.add_argument("--produce-historical", action="store_true")
    parser.add_argument("--build-dir", type=pathlib.Path)
    parser.add_argument("--source-sha")
    parser.add_argument("--command", action="append", default=[], metavar="ID=LOG")
    parser.add_argument("--out", type=pathlib.Path)
    parser.add_argument("--retain-dir", type=pathlib.Path)
    parser.add_argument("--local", type=pathlib.Path)
    parser.add_argument("--hosted", type=pathlib.Path)
    args = parser.parse_args()
    try:
        if args.self_test:
            return self_test()
        if args.check:
            if not args.evidence:
                parser.error("--check requires --evidence")
            return check(args.evidence, args.strict_head)
        if args.produce_local:
            return produce_local(args)
        if args.produce_historical:
            return produce_historical(args)
        parser.error("choose --self-test, --check, --produce-local or --produce-historical")
    except (Rejected, OSError, KeyError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"historical-limitations rejected: {sanitize(str(exc))}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
