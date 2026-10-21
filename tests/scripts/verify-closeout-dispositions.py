#!/usr/bin/env python3
"""Hold every Phase 15.1 debt disposition to its preserved source and its evidence.

Phase 15.1 inherited 24 scope items: 21 audit debts plus the closeout-scan, link-warning and
summary-schema issues. 15.1-DISPOSITIONS.json gives each one an individual disposition. This
checker keeps those records honest:

  * the 24 IDs, their original text and their status are bound to the immutable audit commit
    named by 15.1-SCOPE.json, never to live ancestry or routes
  * a repaired item names source that exists, a positive and a negative control
  * a historical unknown stays unknown; fresh evidence is not recovery
  * a hosted claim must equal a run identity read through the hosting API, not a receipt label
  * a limitation stays open, never counts as a pass and is never recorded as owner acceptance
  * the shipped v0.2.0 identity and the required checks cannot be altered
  * a delivery receipt (optional) must show every required check completed with success on one head

--check validates the files. --self-test builds a private fixture repository and drives this very
CLI over mutated copies: each defect must exit nonzero with its own REJECT code and no success line.
A fixture is not hosted, hardware or historical proof, and this checker never reads GitHub; the live
comparison belongs to verify-v02-delivery.py --stage phase-pr.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
PHASE_REL = ".planning/phases/GB-15.1-release-hardening-and-milestone-debt-closure/"
DEFAULT_DISPOSITIONS = ROOT / PHASE_REL / "15.1-DISPOSITIONS.json"
SCHEMA = 1
SELF = pathlib.Path(__file__).resolve()

SHA64 = re.compile(r"^[0-9a-f]{64}$")
SHA40 = re.compile(r"^[0-9a-f]{40}$")
DEBT_ID = re.compile(r"^P\d+-\d+$")
CLASSES = ("repaired_defect", "qualified_advisory", "fresh_evidence", "historical_unknown", "external_limitation")
CLOSURES = ("closed", "closed_with_residual", "limitation_open")
EVIDENCE_KINDS = ("unit", "integration", "e2e", "automated_ui", "other")
REQUIRED_CHECKS = ("required-native", "fixture-repro", "preview-package-smoke")
LIMITATION_KINDS = ("external_limitation", "owner_decision", "historical_unknown", "flagged_assumption", "residual")
REQUIRED_LIMITATIONS = (
    "LIM-SUPPORT-LEDGER-PIN", "LIM-PERF-REVIEW", "LIM-TRUSTED-JUDGE", "LIM-HIST-AUDIO-RED", "LIM-HIST-M7",
    "LIM-SHIP11-UNCLASSIFIED", "LIM-RESIDUAL-WRITE-JOBS", "LIM-REHEARSAL-FAILED", "LIM-NO-HOST-WRONG-ROM",
    "LIM-PROHIBITION-FLAGS",
)
HISTORICAL_IDS = ("P7-03", "P12-01")
HOSTED_ITEM_WORKFLOWS = {"P7-02": "libbet-repro"}
# The shipped v0.2.0 identity, read from the Phase 15 published delivery receipt. Pinned here so that
# editing the record and its receipt together is still noticed.
SHIPPED = {
    "tag": "v0.2.0",
    "source_sha": "ab301aa69b1f085050fd66bf7b1378863a0821f2",
    "release_id": 418219852,
    "published_at": "2026-10-20T10:25:34Z",
    "published_receipt": ".planning/phases/GB-15-cgb-acceptance-support-ledger-and-v0-2-0-release/15-delivery-receipt.json",
}


class Rejected(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def reject(code: str, message: str):
    raise Rejected(code, message)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(path: pathlib.Path, code: str = "schema-malformed"):
    def pairs(items):
        seen = {}
        for key, value in items:
            if key in seen:
                reject(code, f"{path.name} repeats the key {key!r}")
            seen[key] = value
        return seen
    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs)
    except (OSError, ValueError) as exc:
        raise Rejected(code, f"{path.name} cannot be read as JSON: {exc}") from exc


def text(value, label: str, code: str = "schema-malformed") -> str:
    if not isinstance(value, str) or not value.strip():
        reject(code, f"{label} must be a non-empty string")
    return value


def git_show(root: pathlib.Path, commit: str, path: str) -> str:
    done = subprocess.run(["git", "-C", str(root), "show", f"{commit}:{path}"], capture_output=True, timeout=60)
    if done.returncode != 0:
        reject("audit-commit-unreadable",
               f"{path} cannot be read at the immutable audit commit {commit[:12]}; fetch full history")
    return done.stdout.decode("utf-8")


def audit_debts(root: pathlib.Path, commit: str) -> list[str]:
    """The 21 audit debt strings exactly as the milestone audit recorded them at the audit commit."""
    audit = git_show(root, commit, ".planning/v0.2-MILESTONE-AUDIT.md")
    return [json.loads(m) for m in re.findall(r'^      - (".*")$', audit.split("---")[1], re.M)]


# --------------------------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------------------------
def check_scope(doc: dict, scope_path: pathlib.Path, root: pathlib.Path) -> dict[str, dict]:
    pin = doc.get("scope")
    if not isinstance(pin, dict):
        reject("schema-malformed", "scope pin is missing")
    if sha256_bytes(scope_path.read_bytes()) != pin.get("sha256"):
        reject("scope-pin-mismatch", "the scope inventory differs from the digest recorded when it was dispositioned")
    scope = load_json(scope_path)
    commit = scope.get("source_head")
    if not isinstance(commit, str) or not SHA40.match(commit) or commit != pin.get("source_head"):
        reject("scope-pin-mismatch", "the scope audit commit differs from the recorded one")
    items = scope.get("items")
    if not isinstance(items, list) or len(items) != pin.get("item_count"):
        reject("scope-changed", "the scope item count differs from the recorded inventory")
    if any(i.get("status") != "open" for i in items):
        reject("scope-changed", "a scope item status was edited; original statuses must stay open")
    debts = [i for i in items if DEBT_ID.match(i.get("id", ""))]
    expected = audit_debts(root, commit)
    if [i["description"] for i in debts] != expected or len(expected) != scope.get("audit_debt_count"):
        reject("audit-source-mismatch", "scope text differs from the debts recorded at the immutable audit commit")
    for item in items:
        if not DEBT_ID.match(item["id"]):
            git_show(root, commit, item["source"])  # the original source file existed at the audit commit
    return {i["id"]: i for i in items}


def check_evidence_files(doc: dict, base: pathlib.Path) -> dict[str, dict]:
    pins = doc.get("evidence_pins")
    if not isinstance(pins, dict) or set(pins) != {"15.1-hosted-evidence.json", "15.1-local-evidence.json",
                                                   "15.1-historical-limitations.json"}:
        reject("schema-malformed", "evidence_pins must name the hosted, local and historical records")
    loaded = {}
    for name, digest in pins.items():
        path = base / name
        if not path.is_file() or sha256_bytes(path.read_bytes()) != digest:
            reject("evidence-pin-mismatch", f"{name} differs from the digest this disposition was written against")
        loaded[name] = load_json(path)
    return loaded


def check_hosted(item: dict, hosted_doc: dict) -> None:
    claim = item["hosted"]
    if not isinstance(claim, dict) or item["id"] not in HOSTED_ITEM_WORKFLOWS:
        reject("hosted-identity-unverified", f"{item['id']} carries a hosted claim without an admitted workflow")
    if claim.get("obtained_via") != "gh_api" or claim.get("receipt_labels_used") is not False \
            or hosted_doc.get("obtained_via") != "gh_api" or hosted_doc.get("receipt_labels_used") is not False:
        reject("hosted-identity-unverified", f"{item['id']} hosted identity was not read through the hosting API")
    runs = [w for w in hosted_doc.get("workflows", []) if w.get("id") == claim.get("workflow")]
    if claim.get("workflow") != HOSTED_ITEM_WORKFLOWS[item["id"]] or len(runs) != 1:
        reject("hosted-identity-unverified", f"{item['id']} names a workflow without exactly one recorded run")
    run = runs[0]
    for key in ("run_id", "run_attempt", "head_sha", "conclusion"):
        if claim.get(key) != run.get(key):
            reject("hosted-identity-unverified", f"{item['id']} hosted {key} differs from the API-read run")
    jobs = run.get("jobs") or []
    if claim.get("conclusion") != "success" or run.get("status") != "completed" or not jobs \
            or any(j.get("conclusion") != "success" or j.get("head_sha") != run.get("head_sha") for j in jobs):
        reject("hosted-identity-unverified", f"{item['id']} hosted run did not complete with every job successful")


def check_items(doc: dict, scope_items: dict[str, dict], root: pathlib.Path, evidence: dict) -> dict[str, int]:
    items = doc.get("items")
    if not isinstance(items, list):
        reject("schema-malformed", "items must be a list")
    ids = [i.get("id") for i in items if isinstance(i, dict)]
    if ids != list(scope_items) or len(set(ids)) != len(ids):
        missing = sorted(set(scope_items) - set(ids))
        reject("id-set-mismatch", f"dispositions must cover the scope IDs in order, once each; missing {missing}")
    limitation_doc = evidence["15.1-historical-limitations.json"]
    historical = {i["id"]: i for i in limitation_doc.get("items", [])}
    counts = {c: 0 for c in CLOSURES}
    for item in items:
        iid, original = item["id"], scope_items[item["id"]]
        if item.get("source") != original["source"]:
            reject("source-mismatch", f"{iid} source differs from the scope source {original['source']}")
        if item.get("original_text") != original["description"] \
                or item.get("original_sha256") != sha256_bytes(original["description"].encode("utf-8")):
            reject("original-text-changed", f"{iid} original text differs from the preserved scope text")
        if item.get("classification") not in CLASSES or item.get("closure") not in CLOSURES:
            reject("schema-malformed", f"{iid} classification or closure is not an admitted value")
        if item.get("owner_accepted") is not False:
            reject("owner-acceptance-inferred", f"{iid} records owner acceptance; none is given by phase authorization")
        plans = item.get("plans")
        if not isinstance(plans, list) or not plans or not all(isinstance(p, str) and re.match(r"^15\.1-\d\d$", p) for p in plans):
            reject("schema-malformed", f"{iid} must name the owning plans")
        for plan in plans:
            if not (root / PHASE_REL / f"{plan}-SUMMARY.md").is_file() and plan != "15.1-17":
                reject("schema-malformed", f"{iid} names {plan} but its SUMMARY is absent")
        sources = item.get("affected_source")
        if not isinstance(sources, list) or not sources:
            reject("affected-source-missing", f"{iid} names no affected source")
        for rel in sources:
            relpath = pathlib.PurePosixPath(text(rel, f"{iid} affected source"))
            if relpath.is_absolute() or ".." in relpath.parts or not (root / rel).exists():
                reject("affected-source-missing", f"{iid} affected source {rel} does not exist in the tree")
        for field in ("positive_evidence", "negative_evidence"):
            rows = item.get(field)
            if not isinstance(rows, list) or not rows:
                reject("evidence-missing", f"{iid} has no {field}")
            for row in rows:
                if not isinstance(row, dict) or row.get("kind") not in EVIDENCE_KINDS:
                    reject("evidence-missing", f"{iid} {field} row has no admitted kind")
                text(row.get("ref"), f"{iid} {field} ref", "evidence-missing")
        closure = item["closure"]
        counts[closure] += 1
        if closure != "closed":
            if not isinstance(item.get("remaining_uncertainty"), str) or not item["remaining_uncertainty"].strip() \
                    or item.get("owner_decision_required") is not True \
                    or not isinstance(item.get("owner_decision"), str) or not item["owner_decision"].strip():
                reject("limitation-silent", f"{iid} is not closed but states no remaining uncertainty and owner decision")
        if iid in HISTORICAL_IDS:
            past = historical.get(iid, {})
            historic = item.get("historic")
            if item["classification"] != "historical_unknown" or closure != "limitation_open" \
                    or not isinstance(historic, dict) or historic.get("status") != "unknown" \
                    or historic.get("recovered") is not False or past.get("historic_status") != "unknown" \
                    or past.get("recovered_historic_red", False) or past.get("recovered_historic_diagnostic", False):
                reject("historic-pass-fabricated", f"{iid} turns an unrecoverable historical fact into a pass")
        elif item["classification"] == "historical_unknown" or "historic" in item:
            reject("historic-pass-fabricated", f"{iid} claims a historical unknown that the inventory does not record")
        if "hosted" in item:
            check_hosted(item, evidence["15.1-hosted-evidence.json"])
        elif iid in HOSTED_ITEM_WORKFLOWS:
            reject("hosted-identity-unverified", f"{iid} lost its hosted identity record")
    return counts


def check_limitations(doc: dict, evidence: dict) -> int:
    rows = doc.get("limitations")
    if not isinstance(rows, list):
        reject("schema-malformed", "limitations must be a list")
    seen = {r.get("id"): r for r in rows if isinstance(r, dict)}
    if len(seen) != len(rows):
        reject("limitation-missing", "limitations repeat an ID or hold a malformed row")
    for lid in REQUIRED_LIMITATIONS:
        if lid not in seen:
            reject("limitation-missing", f"required limitation {lid} is absent; remaining limits must stay visible")
    for row in rows:
        if row.get("status") != "open" or row.get("counts_as_pass") is not False or row.get("owner_accepted") is not False:
            reject("limitation-accepted", f"{row.get('id')} is closed, counted as a pass or recorded as owner accepted")
        if row.get("kind") not in LIMITATION_KINDS or not all(isinstance(row.get(k), str) and row[k].strip()
                                                              for k in ("title", "evidence", "owner_decision")):
            reject("schema-malformed", f"{row.get('id')} lacks a kind, title, evidence or owner decision")
        if not isinstance(row.get("affects"), list) or not row["affects"]:
            reject("schema-malformed", f"{row.get('id')} names no affected items")
    rehearsal = [w for w in evidence["15.1-hosted-evidence.json"].get("workflows", []) if w.get("id") == "release-rehearsal"]
    if rehearsal and rehearsal[0].get("conclusion") != "success" and "LIM-REHEARSAL-FAILED" not in seen:
        reject("limitation-missing", "a failed hosted rehearsal must stay a limitation")
    return len(rows)


def check_markdown(doc: dict, dispositions: pathlib.Path) -> None:
    """The human-readable companion must name every ID and limitation so a reader sees none vanish."""
    md = dispositions.with_suffix(".md")
    if not md.is_file():
        reject("markdown-incomplete", f"{md.name} is missing")
    body = md.read_text(encoding="utf-8")
    for key in [i["id"] for i in doc["items"]] + [row["id"] for row in doc["limitations"]]:
        if f"`{key}`" not in body:
            reject("markdown-incomplete", f"{md.name} does not mention {key}")


def check_shipped_and_checks(doc: dict, root: pathlib.Path) -> None:
    shipped = doc.get("shipped_release")
    if not isinstance(shipped, dict):
        reject("shipped-release-altered", "shipped release identity is missing")
    for key, value in SHIPPED.items():
        if shipped.get(key) != value:
            reject("shipped-release-altered", f"shipped release {key} differs from the published v0.2.0 identity")
    if shipped.get("republished") is not False:
        reject("shipped-release-altered", "v0.2.0 must not be recorded as republished")
    receipt = root / SHIPPED["published_receipt"]
    if not receipt.is_file() or sha256_bytes(receipt.read_bytes()) != shipped.get("published_receipt_sha256"):
        reject("shipped-release-altered", "the published delivery receipt differs from the digest recorded for it")
    published = load_json(receipt, "shipped-release-altered")
    if (published.get("tag"), published.get("source_sha"), published.get("release_id")) != \
            (SHIPPED["tag"], SHIPPED["source_sha"], SHIPPED["release_id"]):
        reject("shipped-release-altered", "the published delivery receipt names a different release")
    if tuple(doc.get("required_checks", ())) != REQUIRED_CHECKS:
        reject("required-checks-altered", "required checks must be exactly " + ", ".join(REQUIRED_CHECKS))
    if doc.get("owner_acceptance") != "none":
        reject("owner-acceptance-inferred", "the record must state owner_acceptance none")


def check_receipt(receipt_path: pathlib.Path, doc: dict) -> str:
    receipt = load_json(receipt_path, "receipt-malformed")
    if not isinstance(receipt, dict) or receipt.get("schema_version") != 1 or receipt.get("stage") != "phase-pr" \
            or sorted(receipt.get("required_checks", [])) != sorted(doc["required_checks"]):
        reject("receipt-malformed", "receipt is not a version 1 phase-pr receipt naming exactly the required checks")
    if receipt.get("obtained_via") != "gh_api":
        reject("receipt-malformed", "receipt checks must be read through the hosting API, not self-attested")
    pr = receipt.get("phase_pr")
    head = pr.get("head_sha") if isinstance(pr, dict) else None
    if not isinstance(head, str) or not SHA40.match(head) or type(pr.get("number")) is not int:
        reject("receipt-malformed", "receipt has no pull request number and exact head")
    runs = receipt.get("workflow_runs")
    if not isinstance(runs, list) or not runs:
        reject("receipt-malformed", "receipt lists no workflow runs")
    checks = receipt.get("check_runs")
    if not isinstance(checks, list):
        reject("receipt-malformed", "receipt has no check_runs readback")
    for name in REQUIRED_CHECKS:
        rows = [c for c in checks if isinstance(c, dict) and c.get("name") == name]
        if not rows:
            reject("required-check-missing", f"required check {name} is absent from the readback")
        for row in rows:
            if row.get("head_sha") != head:
                reject("required-check-not-success", f"required check {name} ran on another head")
            if row.get("status") != "completed" or row.get("conclusion") != "success":
                reject("required-check-not-success",
                       f"required check {name} is {row.get('status')}/{row.get('conclusion')}, not completed/success")
    return f"receipt head={head[:12]} checks={len(REQUIRED_CHECKS)}"


def check(dispositions: pathlib.Path, scope_path: pathlib.Path | None, root: pathlib.Path,
          receipt: pathlib.Path | None) -> str:
    doc = load_json(dispositions)
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA or doc.get("plan") != "15.1-17":
        reject("schema-malformed", "not a version 1 plan 15.1-17 disposition record")
    scope_file = scope_path or (root / text((doc.get("scope") or {}).get("file"), "scope file"))
    scope_items = check_scope(doc, scope_file, root)
    evidence = check_evidence_files(doc, dispositions.parent)
    check_shipped_and_checks(doc, root)
    counts = check_items(doc, scope_items, root, evidence)
    limitations = check_limitations(doc, evidence)
    check_markdown(doc, dispositions)
    tail = f" {check_receipt(receipt, doc)}" if receipt else ""
    return (f"closeout-dispositions pass items={len(doc['items'])} closed={counts['closed']} "
            f"closed_with_residual={counts['closed_with_residual']} limitation_open={counts['limitation_open']} "
            f"limitations={limitations} owner_accepted=0{tail}")


# --------------------------------------------------------------------------------------------
# Self-test: drive this CLI over a private fixture repository
# --------------------------------------------------------------------------------------------
def write_json(path: pathlib.Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def edit_json(path: pathlib.Path, fn) -> None:
    value = json.loads(path.read_text(encoding="utf-8"))
    fn(value)
    write_json(path, value)


def git(root: pathlib.Path, *args: str) -> str:
    env = {"GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
           "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "fixture@example.invalid", "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
           "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null"}
    done = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, env=env, timeout=60)
    if done.returncode != 0:
        raise RuntimeError(f"fixture git {args[0]} failed: {done.stderr.strip()}")
    return done.stdout.strip()


def build_fixture(base: pathlib.Path) -> pathlib.Path:
    """A private repository holding a synthetic audit commit and copies of the real records."""
    real = json.loads(DEFAULT_DISPOSITIONS.read_text(encoding="utf-8"))
    real_scope = json.loads((ROOT / real["scope"]["file"]).read_text(encoding="utf-8"))
    root = base / "fixture"
    phase = root / PHASE_REL
    phase.mkdir(parents=True)
    git(root, "init", "-q")
    debts = [i["description"] for i in real_scope["items"] if DEBT_ID.match(i["id"])]
    audit = "---\ndebt:\n" + "".join(f"      - {json.dumps(d)}\n" for d in debts) + "---\naudit body\n"
    (root / ".planning").mkdir(exist_ok=True)
    (root / ".planning/v0.2-MILESTONE-AUDIT.md").write_text(audit, encoding="utf-8")
    for item in real_scope["items"]:
        if not DEBT_ID.match(item["id"]):
            target = root / item["source"]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("original source of " + item["id"] + "\n", encoding="utf-8")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "fixture audit commit")
    commit = git(root, "rev-parse", "HEAD")
    real_scope["source_head"] = commit
    write_json(phase / "15.1-SCOPE.json", real_scope)
    for name in real["evidence_pins"]:
        shutil.copyfile(ROOT / PHASE_REL / name, phase / name)
    published = root / SHIPPED["published_receipt"]
    published.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / SHIPPED["published_receipt"], published)
    for item in real["items"]:
        for rel in item["affected_source"]:
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("fixture source\n", encoding="utf-8")
        for plan in item["plans"]:
            (phase / f"{plan}-SUMMARY.md").write_text("fixture summary\n", encoding="utf-8")
    real["scope"]["source_head"] = commit
    real["scope"]["sha256"] = sha256_bytes((phase / "15.1-SCOPE.json").read_bytes())
    write_json(phase / "15.1-DISPOSITIONS.json", real)
    shutil.copyfile(DEFAULT_DISPOSITIONS.with_suffix(".md"), phase / "15.1-DISPOSITIONS.md")
    head = "a" * 40
    write_json(root / "receipt.json", {
        "schema_version": 1, "stage": "phase-pr", "obtained_via": "gh_api", "required_checks": sorted(REQUIRED_CHECKS),
        "phase_pr": {"number": 1, "head_sha": head}, "workflow_runs": [{"id": 1, "attempt": 1}],
        "check_runs": [{"name": n, "id": i, "head_sha": head, "status": "completed", "conclusion": "success"}
                       for i, n in enumerate(REQUIRED_CHECKS, 1)]})
    return root


def item_of(doc: dict, iid: str) -> dict:
    return next(i for i in doc["items"] if i["id"] == iid)


def run_cli(root: pathlib.Path, *extra: str) -> subprocess.CompletedProcess:
    phase = root / PHASE_REL
    return subprocess.run([sys.executable, "-I", str(SELF), "--check", "--root", str(root),
                           "--dispositions", str(phase / "15.1-DISPOSITIONS.json"), *extra],
                          capture_output=True, text=True, timeout=120)


def controls(root: pathlib.Path):
    """(label, expected REJECT code, mutate(case_root)) for every defect the plan names, plus the neighbours."""
    d = lambda r: r / PHASE_REL / "15.1-DISPOSITIONS.json"
    s = lambda r: r / PHASE_REL / "15.1-SCOPE.json"
    hosted = lambda r: r / PHASE_REL / "15.1-hosted-evidence.json"
    items = lambda fn: (lambda r: edit_json(d(r), lambda v: fn(v)))

    def repin_scope(r):
        edit_json(d(r), lambda v: v["scope"].update(sha256=sha256_bytes(s(r).read_bytes())))

    def rewrite_scope_text(r):
        edit_json(s(r), lambda v: v["items"][0].update(description="weakened finding"))
        repin_scope(r)

    def flip_scope_status(r):
        edit_json(s(r), lambda v: v["items"][3].update(status="fixed"))
        repin_scope(r)

    def drop_id(v):
        v["items"].pop(5)

    def fab_history(v):
        item_of(v, "P7-03")["historic"] = {"status": "pass", "recovered": True}

    def reclassify_history(v):
        item_of(v, "P12-01").update(classification="fresh_evidence", closure="closed")

    def receipt_hosted(v):
        item_of(v, "P7-02")["hosted"].update(obtained_via="receipt")

    def wrong_run(v):
        item_of(v, "P7-02")["hosted"].update(run_id=1)

    def rehearsal_as_proof(v):
        item_of(v, "P7-02")["hosted"].update(workflow="release-rehearsal", run_id=39645769068, conclusion="failure")

    def bad_head(v):
        item_of(v, "P7-02")["hosted"].update(head_sha="b" * 40)

    def skipped_check(r):
        edit_json(r / "receipt.json", lambda v: v["check_runs"][2].update(conclusion="skipped"))

    def missing_check(r):
        edit_json(r / "receipt.json", lambda v: v["check_runs"].pop(1))

    def stale_check(r):
        edit_json(r / "receipt.json", lambda v: v["check_runs"][0].update(head_sha="c" * 40))

    def pending_check(r):
        edit_json(r / "receipt.json", lambda v: v["check_runs"][0].update(status="in_progress", conclusion=None))

    def self_attested(r):
        edit_json(r / "receipt.json", lambda v: v.pop("obtained_via"))

    def alter_receipt(r):
        published = r / SHIPPED["published_receipt"]
        edit_json(published, lambda v: v.update(source_sha="d" * 40))

    def accept_limitation(v):
        v["limitations"][0].update(counts_as_pass=True)

    def drop_limitation(v):
        v["limitations"] = [x for x in v["limitations"] if x["id"] != "LIM-SHIP11-UNCLASSIFIED"]

    def hosted_edit(r):
        edit_json(hosted(r), lambda v: v["workflows"][0].update(conclusion="failure"))

    return [
        ("a dropped scope ID", "id-set-mismatch", items(drop_id)),
        ("a changed original description in the record", "original-text-changed",
         items(lambda v: v["items"][2].update(original_text="weakened finding"))),
        ("a changed original description in the scope with a refreshed pin", "audit-source-mismatch", rewrite_scope_text),
        ("a scope status flipped to fixed", "scope-changed", flip_scope_status),
        ("a scope inventory edited after dispositioning", "scope-pin-mismatch",
         lambda r: edit_json(s(r), lambda v: v.update(name="renamed"))),
        ("a fabricated historic pass", "historic-pass-fabricated", items(fab_history)),
        ("a historical unknown reclassified as fresh evidence", "historic-pass-fabricated", items(reclassify_history)),
        ("a receipt-only hosted identity", "hosted-identity-unverified", items(receipt_hosted)),
        ("a hosted run id that the API record does not hold", "hosted-identity-unverified", items(wrong_run)),
        ("a failed rehearsal presented as the hosted proof", "hosted-identity-unverified", items(rehearsal_as_proof)),
        ("a hosted head that differs from the recorded run", "hosted-identity-unverified", items(bad_head)),
        ("a hosted record edited after dispositioning", "evidence-pin-mismatch", hosted_edit),
        ("a mismatched item source", "source-mismatch",
         items(lambda v: v["items"][0].update(source=".planning/STATE.md"))),
        ("a skipped required check", "required-check-not-success", skipped_check),
        ("a pending required check", "required-check-not-success", pending_check),
        ("a required check on another head", "required-check-not-success", stale_check),
        ("a missing required check", "required-check-missing", missing_check),
        ("a self-attested receipt", "receipt-malformed", self_attested),
        ("an altered shipped release source", "shipped-release-altered",
         items(lambda v: v["shipped_release"].update(source_sha="e" * 40))),
        ("an altered shipped release id", "shipped-release-altered",
         items(lambda v: v["shipped_release"].update(release_id=1))),
        ("a v0.2.0 republication claim", "shipped-release-altered",
         items(lambda v: v["shipped_release"].update(republished=True))),
        ("an altered published receipt", "shipped-release-altered", alter_receipt),
        ("an altered required-check list", "required-checks-altered",
         items(lambda v: v.update(required_checks=["required-native"]))),
        ("inferred owner acceptance on an item", "owner-acceptance-inferred",
         items(lambda v: v["items"][0].update(owner_accepted=True))),
        ("an unresolved limitation without uncertainty or owner decision", "limitation-silent",
         items(lambda v: item_of(v, "P15-01").update(remaining_uncertainty="", owner_decision=None,
                                                    owner_decision_required=False))),
        ("a limitation counted as a pass", "limitation-accepted", items(accept_limitation)),
        ("a dropped SHIP-11 flagged assumption", "limitation-missing", items(drop_limitation)),
        ("a companion document that drops an ID", "markdown-incomplete",
         lambda r: (d(r).with_suffix(".md")).write_text("# empty\n", encoding="utf-8")),
        ("an item without a negative control", "evidence-missing",
         items(lambda v: v["items"][4].update(negative_evidence=[]))),
        ("an item naming source that does not exist", "affected-source-missing",
         items(lambda v: v["items"][1]["affected_source"].append("src/not-a-real-file.c"))),
    ]


def self_test() -> int:
    rejected = 0
    with tempfile.TemporaryDirectory(prefix="closeout-dispositions-") as tmp:
        base = pathlib.Path(tmp)
        fixture = build_fixture(base)
        ok = run_cli(fixture, "--receipt", str(fixture / "receipt.json"))
        if ok.returncode != 0 or "closeout-dispositions pass items=24" not in ok.stdout:
            raise SystemExit(f"self-test positive fixture failed: {ok.stderr.strip() or ok.stdout.strip()}")
        bare = run_cli(fixture)
        if bare.returncode != 0 or "closeout-dispositions pass items=24" not in bare.stdout:
            raise SystemExit(f"self-test positive without receipt failed: {bare.stderr.strip()}")
        for index, (label, code, mutate) in enumerate(controls(fixture)):
            case = base / f"case{index}"
            shutil.copytree(fixture, case, symlinks=True)
            mutate(case)
            result = run_cli(case, "--receipt", str(case / "receipt.json"))
            if result.returncode == 0 or "closeout-dispositions pass" in result.stdout:
                raise SystemExit(f"self-test accepted {label}")
            if f"REJECT {code}:" not in result.stderr:
                raise SystemExit(f"self-test {label}: expected REJECT {code}, got: {result.stderr.strip()[:200]}")
            rejected += 1
    print(f"closeout-dispositions self-test pass positives=2 rejected_controls={rejected}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--root", type=pathlib.Path, default=ROOT)
    parser.add_argument("--dispositions", type=pathlib.Path, default=DEFAULT_DISPOSITIONS)
    parser.add_argument("--scope", type=pathlib.Path)
    parser.add_argument("--receipt", type=pathlib.Path, help="optional phase-pr delivery receipt to check structurally")
    args = parser.parse_args()
    try:
        if args.self_test:
            return self_test()
        if args.check:
            print(check(args.dispositions, args.scope, args.root.resolve(), args.receipt))
            return 0
        parser.error("choose --self-test or --check")
    except Rejected as exc:
        print(f"REJECT {exc.code}: {exc.message}", file=sys.stderr)
        return 1
    except (OSError, KeyError, TypeError, AttributeError, subprocess.SubprocessError) as exc:
        print(f"REJECT schema-malformed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
