#!/usr/bin/env python3
"""Release gates: owner approval of a deterministic Ir exception and exact-head nightly replay evidence.

Phase 17 RM-030, decisions D-18, D-22 and D-23. This is production gate code, not a lifecycle replay. Stdlib only,
it refuses python -O, and every contract rule raises GateError instead of using assert.

Modes
  --digest --measurement FILE
      Print the full canonical SHA-256 of a deterministic Ir measurement (the object verify-perf-gate.py writes
      with --emit-exception-measurement). The owner approves exactly this digest.
  --review-approval --comment-json FILE --decision FILE --measurement FILE --rev SHA
        [--repository OWNER/REPO] [--output FILE] [--exception-receipt FILE]
      Verify one OWNER comment on the recorded review issue. The issue, the comment link and the approving login
      must belong to --repository (default szTheory/gabbaboy, the project repository; hosted callers pass
      $GITHUB_REPOSITORY). The expected repository never comes from the decision file, which the change author
      controls: the owner of any repository is OWNER there, so an issue elsewhere proves nothing. The only approvable event is a deterministic Ir
      exception: a widened ir_ratio_limit, bound to the measurement digest, the accepted cause, the per-ROM band
      and the approved limit. Ordinary advisory paired timing never needs approval and approval never makes wrong
      correctness, safety or realtime evidence pass: verify-perf-gate.py still judges all of those. The owner
      fields of the decision are empty before verification and are copied mechanically from the verified comment
      only after every check passed, into NEW files; the input decision is never altered and a refusal writes
      nothing.
  --nightly-gate --runs-json FILE --run-json FILE --head SHA --output FILE [--rev SHA] [--branch NAME]
        [--checked-at TIMESTAMP]
      Judge saved `gh run list` and `gh run view` JSON of nightly-asan. The newest eligible run at the exact head
      must be completed with success and its asan-full-replay job must have succeeded (skipped is not success).
      A newer red or in-progress run at the head, a newer run at another head, no run at the head or a different
      tree than --rev all refuse. A source-bound receipt is written, exclusively, on success alone.
  --self-test [SUITE] --rev SHA
      SUITE is review-approval, review-controls, nightly-gate or nightly-controls; without one, all four.

--rev is a resolved immutable 40-hex commit. Source facts are read with git from that commit and never from the
live tree; a name, a short or upper-case id or an unresolvable id is refused.
"""
from __future__ import annotations

import copy
import datetime
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from fractions import Fraction
from pathlib import Path

if not __debug__ or sys.flags.optimize:
    sys.stderr.write("verify-release-gates.py must not run with python -O\n")
    raise SystemExit(1)

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
POLICY_FILE = "tests/baseline/perf-gate-v1.txt"
DECISION_SCHEMA = "release-ir-exception-decision-v1"
NIGHTLY_SCHEMA = "release-nightly-gate-receipt-v1"
NIGHTLY_WORKFLOW_NAME = "nightly-asan"
NIGHTLY_REPLAY_JOB = "asan-full-replay"
NIGHTLY_EVENTS = ("workflow_dispatch", "schedule")
OWNER_FIELDS = ("reviewer_identity", "review_reference", "reviewed_at")
DECISION_KEYS = {"schema", "review_issue_number", "review_issue_url", "review_issue_created_at",
                 "accepted_cause", "accepted_cause_reference", "approved_ir_ratio_limit", "measurement_sha256",
                 "per_rom_band"} | set(OWNER_FIELDS)
TIMESTAMP = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ")
SHA40 = re.compile(r"[0-9a-f]{40}")
SHA64 = re.compile(r"[0-9a-f]{64}")
FRACTION = re.compile(r"[1-9][0-9]*/[1-9][0-9]*")
ISSUE_URL = re.compile(r"https://api\.github\.com/repos/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/issues/([1-9][0-9]*)")
# The project repository. A review issue, comment link or approving login anywhere else is refused (17-REVIEW CR-C01).
PROJECT_REPOSITORY = "szTheory/gabbaboy"
REPOSITORY = re.compile(r"([A-Za-z0-9](?:[A-Za-z0-9-]{0,38}))/([A-Za-z0-9_.-]{1,100})")


class GateError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def need(condition: bool, code: str, message: str) -> None:
    if not condition:
        raise GateError(code, message)


# ---------------------------------------------------------------------------------------------------------------
# shared helpers

_PERF = None


def perf_gate():
    """The deterministic gate module: one canonical digest and one exception verifier, never reimplemented."""
    global _PERF
    if _PERF is None:
        spec = importlib.util.spec_from_file_location("gbb_verify_perf_gate", HERE / "verify-perf-gate.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _PERF = module
    return _PERF


def _reject_duplicates(pairs):
    keys = [key for key, _ in pairs]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate object key")
    return dict(pairs)


def read_json(path, code: str):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.loads(handle.read(), object_pairs_hook=_reject_duplicates)
    except (OSError, ValueError) as error:
        raise GateError(code, "cannot read %s as JSON: %s" % (path, error)) from None


def parse_ts(value, code: str, what: str) -> datetime.datetime:
    need(isinstance(value, str) and TIMESTAMP.fullmatch(value) is not None, code,
         "%s is not a UTC timestamp like 2026-10-26T02:02:17Z: %r" % (what, value))
    return datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")


def git(*arguments: str, cwd=None) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *arguments], cwd=cwd or REPO_ROOT, capture_output=True, text=True, check=False)


def resolve_commit(revision, code: str, what: str) -> str:
    need(isinstance(revision, str) and SHA40.fullmatch(revision) is not None, code,
         "%s must be a resolved immutable 40-hex commit" % what)
    resolved = git("rev-parse", "--verify", "%s^{commit}" % revision)
    need(resolved.returncode == 0 and resolved.stdout.strip() == revision, code,
         "%s does not resolve to that exact commit" % what)
    return revision


def tree_of(commit: str, code: str) -> str:
    tree = git("rev-parse", "--verify", "%s^{tree}" % commit)
    need(tree.returncode == 0 and SHA40.fullmatch(tree.stdout.strip()) is not None, code,
         "no tree for commit %s" % commit)
    return tree.stdout.strip()


def new_file_text(path: str, text: str) -> None:
    with open(path, "x", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def write_new_files(items: list) -> None:
    """Create every file or none: a second failure removes the first."""
    made = []
    try:
        for path, text in items:
            new_file_text(path, text)
            made.append(path)
    except OSError as error:
        for path in made:
            try:
                os.unlink(path)
            except OSError:
                pass
        raise GateError("output-exists", "cannot create the output file: %s" % error) from None


# ---------------------------------------------------------------------------------------------------------------
# deterministic Ir exception approval

MEASUREMENT_KEYS = {"limits_base_revision", "limits_base_sha256", "source", "build", "workload", "per_rom"}
PER_ROM_KEYS = {"base_ir", "head_ir_repeats", "ratio_band", "base_identity", "head_repeat_identities"}


def validate_measurement(measurement) -> None:
    """The measurement is the digest's subject, so it must be a closed, internally consistent object."""
    perf = perf_gate()
    need(isinstance(measurement, dict) and set(measurement) == MEASUREMENT_KEYS, "measurement-schema",
         "the measurement fields differ from the closed schema")
    need(SHA40.fullmatch(str(measurement["limits_base_revision"])) is not None, "measurement-schema",
         "limits_base_revision is not a full commit id")
    need(SHA64.fullmatch(str(measurement["limits_base_sha256"])) is not None, "measurement-schema",
         "limits_base_sha256 is not a SHA-256")
    source, build = measurement["source"], measurement["build"]
    need(isinstance(source, dict) and set(source) == {"base_revision", "head_revision"} and
         all(SHA40.fullmatch(str(value)) for value in source.values()), "measurement-schema",
         "source revisions are not full commit ids")
    need(isinstance(build, dict) and set(build) == {"base_identity_sha256", "head_identity_sha256"} and
         all(SHA64.fullmatch(str(value)) for value in build.values()), "measurement-schema",
         "build identities are not SHA-256 values")
    workload = measurement["workload"]
    need(isinstance(workload, dict) and set(workload) == {"id", "roms"} and workload["id"] == perf.WORKLOAD and
         isinstance(workload["roms"], dict) and set(workload["roms"]) == set(perf.ROMS), "measurement-schema",
         "workload identity differs from %s" % perf.WORKLOAD)
    per_rom = measurement["per_rom"]
    need(isinstance(per_rom, dict) and set(per_rom) == set(perf.ROMS), "measurement-schema",
         "per-ROM evidence does not cover exactly the gated ROMs")
    for rom in perf.ROMS:
        pin, entry = workload["roms"][rom], per_rom[rom]
        need(isinstance(pin, dict) and set(pin) == set(perf.ROM_FIELDS) and
             SHA64.fullmatch(str(pin["sha256"])) and re.fullmatch(r"[0-9a-f]{16}", str(pin["digest"])) and
             type(pin["consumed_half_dots"]) is int and pin["consumed_half_dots"] > 0, "measurement-schema",
             "%s workload pin is malformed" % rom)
        need(isinstance(entry, dict) and set(entry) == PER_ROM_KEYS, "measurement-schema",
             "%s per-ROM fields differ from the closed schema" % rom)
        base_ir, repeats = entry["base_ir"], entry["head_ir_repeats"]
        need(type(base_ir) is int and base_ir > 0 and isinstance(repeats, list) and len(repeats) == 2 and
             all(type(ir) is int and ir > 0 for ir in repeats), "measurement-schema",
             "%s instruction counts are malformed" % rom)
        # The correctness evidence is part of the digest: a measurement of other bytes is not approvable.
        identity = {"workload": perf.WORKLOAD, "digest": pin["digest"], "consumed_half_dots": pin["consumed_half_dots"]}
        need(entry["base_identity"] == identity and entry["head_repeat_identities"] == [identity, identity],
             "measurement-correctness-mismatch", "%s correctness identity differs from the workload pin" % rom)
        band = entry["ratio_band"]
        need(isinstance(band, dict) and set(band) == {"min", "max"}, "measurement-schema",
             "%s ratio band is malformed" % rom)
        ratios = [Fraction(ir, base_ir) for ir in repeats]
        need(band == {"min": perf.fraction_text(min(ratios)), "max": perf.fraction_text(max(ratios))},
             "measurement-band-mismatch", "%s ratio band is not the band of its instruction counts" % rom)


def measurement_digest(measurement) -> str:
    validate_measurement(measurement)
    return perf_gate().canonical_sha(measurement)


def base_ir_limit(measurement) -> Fraction:
    """The widened-from limit, read from the immutable base commit the measurement names (never the live tree)."""
    base_rev = resolve_commit(measurement["limits_base_revision"], "review-source-mismatch",
                              "the measurement's limits base revision")
    shown = git("show", "%s:%s" % (base_rev, POLICY_FILE))
    need(shown.returncode == 0, "review-source-mismatch", "the limits base has no %s" % POLICY_FILE)
    need(hashlib.sha256(shown.stdout.encode("utf-8")).hexdigest() == measurement["limits_base_sha256"],
         "review-source-mismatch", "the limits base bytes differ from the measurement's limits_base_sha256")
    found = re.search(r"(?m)^ir_ratio_limit=([1-9][0-9]*)/([1-9][0-9]*)$", shown.stdout)
    need(found is not None, "review-source-mismatch", "the limits base has no exact ir_ratio_limit")
    return Fraction(int(found.group(1)), int(found.group(2)))


def approval_text(decision: dict, digest: str, measurement: dict) -> str:
    bands = ", ".join("%s=%s..%s" % (rom, measurement["per_rom"][rom]["ratio_band"]["min"],
                                      measurement["per_rom"][rom]["ratio_band"]["max"])
                      for rom in perf_gate().ROMS)
    return ("Approved: deterministic-ir-exception for measurement %s; limit %s; cause: %s; reference: %s; bands: %s" %
            (digest, decision["approved_ir_ratio_limit"], decision["accepted_cause"],
             decision["accepted_cause_reference"], bands))


def review_approval(comment, decision, measurement, rev, repository=PROJECT_REPOSITORY):
    """Verify one owner comment. Returns (completed_decision, exception_receipt); writes nothing."""
    perf = perf_gate()
    expected = REPOSITORY.fullmatch(repository) if isinstance(repository, str) else None
    need(expected is not None, "usage", "--repository must be OWNER/REPO, got %r" % (repository,))
    rev = resolve_commit(rev, "review-source-mismatch", "--rev")
    digest = measurement_digest(measurement)
    need(measurement["source"]["head_revision"] == rev, "review-source-mismatch",
         "the measurement was taken at another source revision than --rev")
    base_limit = base_ir_limit(measurement)

    need(isinstance(decision, dict) and set(decision) == DECISION_KEYS and decision["schema"] == DECISION_SCHEMA,
         "review-decision-schema", "the decision fields differ from the closed %s schema" % DECISION_SCHEMA)
    number, url = decision["review_issue_number"], decision["review_issue_url"]
    located = ISSUE_URL.fullmatch(url) if isinstance(url, str) else None
    need(type(number) is int and number > 0 and located is not None and int(located.group(3)) == number and
         isinstance(decision["review_issue_created_at"], str) and
         TIMESTAMP.fullmatch(decision["review_issue_created_at"]) is not None,
         "review-issue-unrecorded", "the decision does not record the review issue number, API url and creation time")
    # GitHub owner and repository names compare case-insensitively.
    need((located.group(1).casefold(), located.group(2).casefold()) ==
         (expected.group(1).casefold(), expected.group(2).casefold()), "review-wrong-repository",
         "the review issue %r is not in the project repository %s" % (url, repository))
    need(all(decision[field] == "" for field in OWNER_FIELDS), "review-fields-prefilled",
         "the owner-derived fields must be empty before verification")
    cause, reference = decision["accepted_cause"], decision["accepted_cause_reference"]
    need(isinstance(cause, str) and 0 < len(cause) <= 512 and cause == cause.strip() and
         re.fullmatch(r"[^\x00-\x1f\x7f]+", cause) is not None and isinstance(reference, str) and
         re.fullmatch(r"https://[^\s]+", reference) is not None, "review-decision-schema",
         "the accepted cause must be one printable line of at most 512 characters with an https reference")
    limit_text = decision["approved_ir_ratio_limit"]
    need(isinstance(limit_text, str) and FRACTION.fullmatch(limit_text) is not None and
         perf.fraction_text(Fraction(limit_text)) == limit_text, "review-decision-schema",
         "the approved limit must be a reduced exact fraction")
    approved = Fraction(limit_text)
    need(decision["per_rom_band"] == {rom: measurement["per_rom"][rom]["ratio_band"] for rom in perf.ROMS},
         "review-decision-schema", "the decision's per-ROM band differs from the measurement")

    comment_keys = ("user", "author_association", "issue_url", "created_at", "html_url", "body")
    need(isinstance(comment, dict) and all(key in comment for key in comment_keys) and
         isinstance(comment["user"], dict) and isinstance(comment["user"].get("login"), str) and
         re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})", comment["user"]["login"]) is not None and
         isinstance(comment["body"], str), "review-comment-schema", "the comment is not a GitHub issue comment")
    need(comment["author_association"] == "OWNER", "review-not-owner",
         "the approving comment author_association is %r, not OWNER" % comment["author_association"])
    need(comment["user"]["login"].casefold() == expected.group(1).casefold(), "review-not-owner",
         "the approving login %r is not the owner of %s" % (comment["user"]["login"], repository))
    need(comment["issue_url"] == url, "review-wrong-issue",
         "the comment belongs to %r, not to the recorded review issue %r" % (comment["issue_url"], url))
    comment_time = parse_ts(comment["created_at"], "review-comment-schema", "the comment created_at")
    need(comment_time > parse_ts(decision["review_issue_created_at"], "review-issue-unrecorded",
                                 "review_issue_created_at"), "review-comment-predates-issue",
         "the comment is not newer than the review issue")
    owner, repo = located.group(1), located.group(2)
    need(isinstance(comment["html_url"], str) and re.fullmatch(
        r"https://github\.com/%s/%s/issues/%d#issuecomment-[1-9][0-9]*" % (re.escape(owner), re.escape(repo), number),
        comment["html_url"]) is not None, "review-reference-invalid",
         "the comment link is not a comment of the recorded review issue")
    need(decision["measurement_sha256"] == digest, "review-digest-mismatch",
         "the decision's measurement digest is not the canonical digest of the measurement")
    body = comment["body"].strip()
    quoted = re.search(r"measurement ([0-9A-Za-z]+)", body)
    if quoted is not None:
        need(quoted.group(1) == digest, "review-digest-mismatch",
             "the approval names %r, not the full measurement digest" % quoted.group(1))
    need(body == approval_text(decision, digest, measurement), "review-text-mismatch",
         "the comment is not the exact approval wording for this measurement, limit, cause and bands")

    unsigned = {"schema": perf.EXCEPTION_SCHEMA, "accepted_cause": cause, "accepted_cause_reference": reference,
                "approved_ir_ratio_limit": limit_text, "measurement": measurement, "measurement_sha256": digest}
    receipt = dict(unsigned, external_verification={"status": "verified", "reference": comment["html_url"],
                                                    "receipt_sha256": perf.canonical_sha(unsigned)})
    # The receipt is judged by the same verifier verify-perf-gate.py --evaluate applies, so a limit that does not
    # cover the measured band, one that is not a widening, or a measurement that needed no exception cannot pass here.
    with tempfile.TemporaryDirectory(prefix="gbb-release-gates-") as scratch:
        probe = Path(scratch) / "receipt.json"
        probe.write_text(json.dumps(receipt, sort_keys=True), encoding="utf-8", newline="\n")
        try:
            perf.verify_deterministic_exception(str(probe), approved, base_limit, measurement)
        except perf.Rejected as error:
            raise GateError("review-" + error.code, str(error)) from None
    completed = dict(decision, reviewer_identity=comment["user"]["login"], review_reference=comment["html_url"],
                     reviewed_at=comment["created_at"])
    return completed, receipt


def run_review_approval(options: dict) -> str:
    comment = read_json(options["comment-json"], "review-comment-schema")
    decision = read_json(options["decision"], "review-decision-schema")
    measurement = read_json(options["measurement"], "measurement-schema")
    outputs = [(options[name], None) for name in ("output", "exception-receipt") if name in options]
    for path, _ in outputs:
        need(not os.path.lexists(path), "output-exists", "%s already exists and is never overwritten" % path)
    completed, receipt = review_approval(comment, decision, measurement, options["rev"],
                                         options.get("repository", PROJECT_REPOSITORY))
    texts = {"output": json.dumps(completed, sort_keys=True, indent=2) + "\n",
             "exception-receipt": json.dumps(receipt, sort_keys=True, indent=2) + "\n"}
    write_new_files([(options[name], texts[name]) for name in ("output", "exception-receipt") if name in options])
    return "release-gates review-approval pass issue=%d digest=%s" % (decision["review_issue_number"],
                                                                     measurement_digest(measurement))


# ---------------------------------------------------------------------------------------------------------------
# exact-head nightly replay evidence

RUN_KEYS = ("databaseId", "attempt", "headSha", "headBranch", "event", "status", "conclusion", "createdAt",
            "workflowName")


def run_entry(value, what: str, *, view: bool = False) -> dict:
    need(isinstance(value, dict) and all(key in value for key in RUN_KEYS), "nightly-input-schema",
         "%s is missing a run field" % what)
    need(type(value["databaseId"]) is int and value["databaseId"] > 0 and type(value["attempt"]) is int and
         value["attempt"] >= 1 and isinstance(value["headSha"], str) and SHA40.fullmatch(value["headSha"]) and
         all(isinstance(value[key], str) for key in ("headBranch", "event", "status", "conclusion",
                                                      "workflowName")), "nightly-input-schema",
         "%s has a malformed run field" % what)
    parse_ts(value["createdAt"], "nightly-input-schema", "%s createdAt" % what)
    if view:
        parse_ts(value.get("updatedAt"), "nightly-input-schema", "%s updatedAt" % what)
        need(isinstance(value.get("jobs"), list) and all(isinstance(job, dict) for job in value["jobs"]),
             "nightly-input-schema", "%s has no job list" % what)
    return value


def newest_key(run: dict):
    return (run["createdAt"], run["databaseId"], run["attempt"])


def nightly_gate(runs, run, head, rev, branch, checked_at):
    """Return the source-bound receipt for the newest eligible exact-head nightly run, or raise."""
    head = resolve_commit(head, "nightly-head-unresolved", "--head")
    head_tree = tree_of(head, "nightly-head-unresolved")
    source = head
    if rev is not None:
        source = resolve_commit(rev, "nightly-source-mismatch", "--rev")
        need(tree_of(source, "nightly-source-mismatch") == head_tree, "nightly-source-mismatch",
             "the nightly head and --rev have different trees")
    need(isinstance(runs, list), "nightly-input-schema", "the run list is not a JSON array")
    listed = [run_entry(item, "run list entry %d" % index) for index, item in enumerate(runs)]
    need(len({item["databaseId"] for item in listed}) == len(listed), "nightly-input-schema",
         "the run list repeats a run id")
    eligible = [item for item in listed if item["workflowName"] == NIGHTLY_WORKFLOW_NAME and
                item["event"] in NIGHTLY_EVENTS and (branch is None or item["headBranch"] == branch)]
    at_head = [item for item in eligible if item["headSha"] == head]
    need(at_head, "nightly-no-run-at-head", "no nightly-asan run exists at head %s" % head)
    newest_anywhere = max(eligible, key=newest_key)
    need(newest_anywhere["headSha"] == head, "nightly-head-mismatch",
         "a newer nightly-asan run (%d) is at head %s, which supersedes this head" %
         (newest_anywhere["databaseId"], newest_anywhere["headSha"]))
    newest = max(at_head, key=newest_key)
    viewed = run_entry(run, "the viewed run", view=True)
    need(viewed["headSha"] == head, "nightly-head-mismatch", "the viewed run is at head %s, not %s" %
         (viewed["headSha"], head))
    need((viewed["databaseId"], viewed["attempt"]) == (newest["databaseId"], newest["attempt"]),
         "nightly-not-newest", "the viewed run %d/%d is not the newest run at the head (%d/%d)" %
         (viewed["databaseId"], viewed["attempt"], newest["databaseId"], newest["attempt"]))
    need(all(viewed[key] == newest[key] for key in ("workflowName", "event", "headBranch", "createdAt")),
         "nightly-run-mismatch", "the viewed run disagrees with its run-list entry")
    need(viewed["status"] == "completed", "nightly-in-progress", "the newest run at the head is %s" % viewed["status"])
    need(viewed["conclusion"] == "success", "nightly-not-success",
         "the newest run at the head concluded %r" % viewed["conclusion"])
    replay = [job for job in viewed["jobs"] if job.get("name") == NIGHTLY_REPLAY_JOB]
    need(len(replay) == 1 and replay[0].get("status") == "completed" and replay[0].get("conclusion") == "success",
         "nightly-replay-not-success",
         "the %s job did not run to success (skipped does not count)" % NIGHTLY_REPLAY_JOB)
    started = parse_ts(replay[0].get("startedAt"), "nightly-timestamp", "the replay startedAt")
    finished = parse_ts(replay[0].get("completedAt"), "nightly-timestamp", "the replay completedAt")
    created = parse_ts(viewed["createdAt"], "nightly-timestamp", "createdAt")
    updated = parse_ts(viewed["updatedAt"], "nightly-timestamp", "updatedAt")
    need(created <= started <= finished <= updated, "nightly-timestamp",
         "the run and replay timestamps are not ordered created <= started <= completed <= updated")
    checked = parse_ts(checked_at, "nightly-timestamp", "checked_at")
    need(checked >= updated, "nightly-timestamp", "checked_at precedes the completion of the run it checks")
    return {
        "schema": NIGHTLY_SCHEMA,
        "run_id": viewed["databaseId"],
        "attempt": viewed["attempt"],
        "workflow": NIGHTLY_WORKFLOW_NAME,
        "event": viewed["event"],
        "branch": viewed["headBranch"],
        "head_sha": head,
        "tree_sha": head_tree,
        "source_sha": source,
        "conclusion": viewed["conclusion"],
        "replay_job_conclusion": replay[0]["conclusion"],
        "run_created_at": viewed["createdAt"],
        "run_completed_at": viewed["updatedAt"],
        "checked_at": checked_at,
    }


def run_nightly_gate(options: dict) -> str:
    output = options["output"]
    need(not os.path.lexists(output), "nightly-output-exists", "%s already exists and is never overwritten" % output)
    runs = read_json(options["runs-json"], "nightly-input-schema")
    run = read_json(options["run-json"], "nightly-input-schema")
    checked_at = options.get("checked-at") or datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")
    receipt = nightly_gate(runs, run, options["head"], options.get("rev"), options.get("branch"), checked_at)
    write_new_files([(output, json.dumps(receipt, sort_keys=True, indent=2) + "\n")])
    return "release-gates nightly-gate pass run_id=%d head=%s" % (receipt["run_id"], receipt["head_sha"])


# ---------------------------------------------------------------------------------------------------------------
# command line

VALUE_OPTIONS = {"comment-json", "decision", "measurement", "rev", "output", "exception-receipt", "runs-json",
                 "run-json", "head", "branch", "checked-at", "repository"}
MODES = {"digest": {"measurement"},
         "review-approval": {"comment-json", "decision", "measurement", "rev"},
         "nightly-gate": {"runs-json", "run-json", "head", "output"}}
OPTIONAL = {"review-approval": {"output", "exception-receipt", "repository"}, "nightly-gate": {"rev", "branch", "checked-at"}}


def parse_arguments(argv: list) -> tuple:
    need(argv, "usage", "choose --digest, --review-approval, --nightly-gate or --self-test")
    mode = argv[0]
    need(mode.startswith("--") and mode[2:] in set(MODES) | {"self-test"}, "usage", "unknown mode %r" % mode)
    mode = mode[2:]
    rest, options = argv[1:], {}
    if mode == "self-test":
        suite = None
        if rest and not rest[0].startswith("--"):
            suite, rest = rest[0], rest[1:]
        need(suite in (None, "review-approval", "review-controls", "nightly-gate", "nightly-controls"), "usage",
             "unknown self-test suite %r" % suite)
        options["suite"] = suite
    index = 0
    while index < len(rest):
        name = rest[index]
        need(name.startswith("--") and name[2:] in VALUE_OPTIONS and index + 1 < len(rest), "usage",
             "unknown option or missing value near %r" % name)
        need(name[2:] not in options, "usage", "%s given twice" % name)
        options[name[2:]] = rest[index + 1]
        index += 2
    if mode == "self-test":
        need(set(options) <= {"suite", "rev"} and "rev" in options, "usage", "--self-test needs --rev SHA")
    else:
        allowed = MODES[mode] | OPTIONAL.get(mode, set())
        need(MODES[mode] <= set(options) and set(options) <= allowed, "usage",
             "--%s takes %s (optional: %s)" % (mode, " ".join("--" + n for n in sorted(MODES[mode])),
                                              " ".join("--" + n for n in sorted(OPTIONAL.get(mode, set())))))
    return mode, options


def main(argv: list) -> int:
    try:
        mode, options = parse_arguments(argv)
        if mode == "digest":
            print("measurement_sha256=%s" % measurement_digest(read_json(options["measurement"], "measurement-schema")))
        elif mode == "review-approval":
            print(run_review_approval(options))
        elif mode == "nightly-gate":
            print(run_nightly_gate(options))
        else:
            for line in self_test(options["suite"], options["rev"]):
                print(line)
    except GateError as error:
        sys.stderr.write("REJECT %s: %s\n" % (error.code, error))
        return 1
    return 0


# ---------------------------------------------------------------------------------------------------------------
# self-test: every control runs the production functions above; the CLI is driven for exit codes and for the
# promise that a refusal writes nothing and an approval never edits its input.

# The positives use the project repository; an identical approval in any other repository is a negative control.
PROJECT_OWNER = PROJECT_REPOSITORY.split("/")[0]
REVIEW_ISSUE_API = "https://api.github.com/repos/%s/issues/122" % PROJECT_REPOSITORY
REVIEW_COMMENT_URL = "https://github.com/%s/issues/122#issuecomment-6406576530" % PROJECT_REPOSITORY
FOREIGN_REPOSITORY = "example-owner/example-repo"
BASE_TIME = "2026-10-28T03:00:00Z"


class Ledger:
    def __init__(self) -> None:
        self.controls = 0
        self.positives = 0
        self.failures: list = []

    def rejects(self, name: str, code: str, call) -> None:
        self.controls += 1
        try:
            call()
        except GateError as error:
            if error.code != code:
                self.failures.append("%s: refused with %s (%s), expected %s" % (name, error.code, error, code))
            return
        self.failures.append("%s: was accepted, expected %s" % (name, code))

    def passes(self, name: str, call):
        self.positives += 1
        try:
            return call()
        except GateError as error:
            self.failures.append("%s: refused with %s (%s)" % (name, error.code, error))
        return None

    def check(self, name: str, condition: bool, detail: str = "", control: bool = False) -> None:
        if control:
            self.controls += 1
        else:
            self.positives += 1
        if not condition:
            self.failures.append("%s: %s" % (name, detail or "condition failed"))

    def summary(self, suite: str) -> str:
        if self.failures:
            for failure in self.failures:
                sys.stderr.write("self-test control failed: %s\n" % failure)
            raise GateError("self-test-failed", "%d of %d checks failed in %s" %
                            (len(self.failures), self.controls + self.positives, suite))
        return "release-gates self-test pass suite=%s controls=%d positives=%d" % (suite, self.controls, self.positives)


def spawn(script: Path, *arguments: str):
    process = subprocess.run([sys.executable, "-I", str(script), *arguments], capture_output=True, text=True,
                             check=False)
    return process.returncode, process.stdout, process.stderr


def write_text(path: Path, text: str) -> str:
    path.write_text(text, encoding="utf-8", newline="\n")
    return str(path)


class ReviewFixture:
    """A real measurement: verify-perf-gate.py run over the canned over-budget head with a widened limit."""

    def __init__(self, scratch: Path, rev: str):
        perf = perf_gate()
        self.perf, self.scratch, self.rev = perf, scratch, rev
        original = Path(perf.DEFAULT_LIMITS).read_text(encoding="utf-8")
        self.limits = write_text(scratch / "limits-widened.txt",
                                 re.sub(r"(?m)^ir_ratio_limit=.*$", "ir_ratio_limit=112/100", original))
        self.base_identity, self.head_identity = "a" * 64, "b" * 64
        self.measurement_path = scratch / "measurement.json"
        code, _, error = spawn(HERE / "verify-perf-gate.py", *self.evaluate_arguments("head-over"),
                               "--emit-exception-measurement", str(self.measurement_path))
        need(code == 1 and "REJECT ir-limit-widening-unapproved" in error and self.measurement_path.is_file(),
             "self-test-failed", "the canned over-budget head did not produce a measurement: %s" % error.strip())
        self.measurement = read_json(self.measurement_path, "measurement-schema")
        self.digest = measurement_digest(self.measurement)

    def evaluate_arguments(self, head: str, *extra: str):
        perf = self.perf
        return ("--evaluate", "--limits", self.limits, "--base", os.path.join(perf.DATA, "base"),
                "--head", os.path.join(perf.DATA, head), "--base-rev", perf.LIMITS_BASE_REV,
                "--source-base-rev", perf.V020_SHA, "--source-head-rev", self.rev,
                "--build-base-identity", self.base_identity, "--build-head-identity", self.head_identity, *extra)

    def decision(self, limit: str = "28/25", cause: str = "deterministic Ir growth accepted for the state codec") -> dict:
        return {"schema": DECISION_SCHEMA, "review_issue_number": 122, "review_issue_url": REVIEW_ISSUE_API,
                "review_issue_created_at": "2026-10-26T00:30:57Z", "accepted_cause": cause,
                "accepted_cause_reference": "https://example.invalid/decisions/ir-exception",
                "approved_ir_ratio_limit": limit, "measurement_sha256": self.digest,
                "per_rom_band": {rom: self.measurement["per_rom"][rom]["ratio_band"] for rom in self.perf.ROMS},
                "reviewer_identity": "", "review_reference": "", "reviewed_at": ""}

    def comment(self, decision: dict, **changes) -> dict:
        comment = {"id": 6406576530, "user": {"login": PROJECT_OWNER, "id": 1}, "author_association": "OWNER",
                   "issue_url": decision["review_issue_url"], "created_at": "2026-10-26T02:02:17Z",
                   "html_url": REVIEW_COMMENT_URL,
                   "body": approval_text(decision, self.digest, self.measurement)}
        comment.update(changes)
        return comment

    def approve(self, decision=None, comment=None, measurement=None, rev=None, repository=PROJECT_REPOSITORY):
        decision = self.decision() if decision is None else decision
        comment = self.comment(decision) if comment is None else comment
        return review_approval(copy.deepcopy(comment), copy.deepcopy(decision),
                               copy.deepcopy(self.measurement if measurement is None else measurement),
                               rev or self.rev, repository)

    def foreign(self) -> tuple:
        """A self-consistent approval in another repository: its owner is OWNER there, and every other field is right."""
        decision = dict(self.decision(), review_issue_url=REVIEW_ISSUE_API.replace(PROJECT_REPOSITORY, FOREIGN_REPOSITORY))
        comment = self.comment(decision, user={"login": FOREIGN_REPOSITORY.split("/")[0], "id": 2},
                               html_url=REVIEW_COMMENT_URL.replace(PROJECT_REPOSITORY, FOREIGN_REPOSITORY))
        return decision, comment


def self_test_review_approval(ledger: Ledger, fixture: ReviewFixture) -> None:
    perf, scratch = fixture.perf, fixture.scratch
    completed, receipt = ledger.passes("valid owner approval", fixture.approve) or ({}, {})
    ledger.check("owner fields come from the verified comment",
                 (completed.get("reviewer_identity"), completed.get("review_reference"), completed.get("reviewed_at"))
                 == (PROJECT_OWNER, REVIEW_COMMENT_URL, "2026-10-26T02:02:17Z"), "owner fields were not copied")
    ledger.check("receipt is the closed perf-gate schema", receipt.get("schema") == perf.EXCEPTION_SCHEMA and
                 receipt.get("external_verification", {}).get("status") == "verified")

    decision_path = write_text(scratch / "decision.json", json.dumps(fixture.decision(), sort_keys=True))
    comment_path = write_text(scratch / "comment.json", json.dumps(fixture.comment(fixture.decision())))
    before = Path(decision_path).read_bytes()
    out_path, receipt_path = str(scratch / "completed.json"), str(scratch / "receipt.json")
    code, out, err = spawn(Path(__file__).resolve(), "--digest", "--measurement", str(fixture.measurement_path))
    ledger.check("--digest prints the canonical digest", code == 0 and out.strip() == "measurement_sha256=" + fixture.digest,
                 out + err)
    code, out, err = spawn(Path(__file__).resolve(), "--review-approval", "--comment-json", comment_path,
                           "--decision", decision_path, "--measurement", str(fixture.measurement_path),
                           "--rev", fixture.rev, "--output", out_path, "--exception-receipt", receipt_path)
    ledger.check("CLI approval passes", code == 0 and "review-approval pass issue=122" in out and not err.strip(), out + err)
    ledger.check("the input decision is never altered", Path(decision_path).read_bytes() == before)
    ledger.check("the completed decision carries the verified owner fields",
                 read_json(out_path, "x").get("reviewer_identity") == PROJECT_OWNER)

    # The approved receipt reaches the real deterministic ratchet and is the only way a widened limit passes.
    perf_script = HERE / "verify-perf-gate.py"
    code, out, err = spawn(perf_script, *fixture.evaluate_arguments("head-over", "--exception-receipt", receipt_path))
    ledger.check("verified approval reaches the real ratchet", code == 0 and "perf-gate pass ratios" in out, out + err)
    code, out, err = spawn(perf_script, *fixture.evaluate_arguments("head-over"))
    ledger.check("the same widening without approval is refused",
                 code == 1 and "REJECT ir-limit-widening-unapproved" in err, out + err, control=True)
    # Approval never overrides correctness, safety or realtime evidence.
    code, out, err = spawn(perf_script, *fixture.evaluate_arguments("head-digest", "--exception-receipt", receipt_path))
    ledger.check("approval does not excuse a wrong correctness digest",
                 code == 1 and "REJECT workload-digest-mismatch" in err, out + err, control=True)
    realtime = os.path.join(perf.DATA, "realtime-below-floor.txt")
    code, out, err = spawn(perf_script, *fixture.evaluate_arguments("head-over", "--exception-receipt", receipt_path,
                                                                    "--realtime", realtime))
    ledger.check("approval does not excuse a realtime miss",
                 code == 1 and "REJECT realtime-below-floor" in err, out + err, control=True)
    tampered = read_json(receipt_path, "x")
    tampered["accepted_cause"] = "a cause nobody approved"
    code, out, err = spawn(perf_script, *fixture.evaluate_arguments(
        "head-over", "--exception-receipt", write_text(scratch / "tampered.json", json.dumps(tampered))))
    ledger.check("a receipt edited after approval is refused downstream",
                 code == 1 and "REJECT exception-receipt-digest-mismatch" in err, out + err, control=True)
    # Ordinary advisory timing: the unchanged limit passes with no approval, and an approval offered anyway is refused.
    unchanged = [perf.DEFAULT_LIMITS if item == fixture.limits else item for item in fixture.evaluate_arguments("head-pass")]
    code, out, err = spawn(perf_script, *unchanged)
    ledger.check("ordinary advisory timing needs no approval", code == 0 and "perf-gate pass" in out, out + err)
    code, out, err = spawn(perf_script, *unchanged, "--exception-receipt", receipt_path)
    ledger.check("an approval is not accepted for an ordinary run",
                 code == 1 and "REJECT exception-receipt-unexpected" in err, out + err, control=True)
    code, out, err = spawn(HERE / "verify-v02-performance.py", "--self-test-advisory-pipeline")
    ledger.check("a triggered paired-timing receipt succeeds as advisory evidence without a decision",
                 code == 0 and "self-test pass" in out, out + err)


def self_test_review_controls(ledger: Ledger, fixture: ReviewFixture) -> None:
    perf, scratch = fixture.perf, fixture.scratch
    approve = fixture.approve

    def comment_with(**changes):
        return approve(comment=fixture.comment(fixture.decision(), **changes))

    def decision_with(**changes):
        return approve(decision=dict(fixture.decision(), **changes))

    ledger.passes("valid approval before the mutants", approve)
    # The eight named mutants, each with its own intended refusal.
    ledger.rejects("non-owner", "review-not-owner", lambda: comment_with(author_association="MEMBER"))
    ledger.rejects("wrong issue", "review-wrong-issue",
                   lambda: comment_with(issue_url=REVIEW_ISSUE_API.replace("/122", "/123")))
    wrong = "0" * 64
    ledger.rejects("wrong digest", "review-digest-mismatch", lambda: comment_with(
        body=fixture.comment(fixture.decision())["body"].replace(fixture.digest, wrong)))
    ledger.rejects("missing approval text", "review-text-mismatch", lambda: comment_with(body="Looks good to me."))
    ledger.rejects("prefix-only digest", "review-digest-mismatch", lambda: comment_with(
        body=fixture.comment(fixture.decision())["body"].replace(fixture.digest, fixture.digest[:12])))
    ledger.rejects("unrecorded issue", "review-issue-unrecorded",
                   lambda: decision_with(review_issue_number=0, review_issue_url=""))
    ledger.rejects("comment predates issue", "review-comment-predates-issue",
                   lambda: comment_with(created_at="2026-10-25T23:00:00Z"))
    ledger.rejects("prefilled owner fields", "review-fields-prefilled",
                   lambda: decision_with(reviewer_identity="someone", review_reference=REVIEW_COMMENT_URL,
                                         reviewed_at="2026-10-26T02:02:17Z"))
    # Each executor-typed owner field is refused on its own, and owner association is exact.
    for field in OWNER_FIELDS:
        ledger.rejects("prefilled " + field, "review-fields-prefilled", lambda field=field: decision_with(**{field: "x"}))
    for association in ("CONTRIBUTOR", "COLLABORATOR", "NONE", "owner", ""):
        ledger.rejects("association %r" % association, "review-not-owner",
                       lambda association=association: comment_with(author_association=association))
    # The approval binds measurement, cause, limit and band, not only the digest.
    ledger.rejects("decision digest edited", "review-digest-mismatch", lambda: decision_with(measurement_sha256=wrong))
    ledger.rejects("cause edited after approval", "review-text-mismatch", lambda: approve(
        decision=fixture.decision(), comment=fixture.comment(fixture.decision(cause="another cause"))))
    ledger.rejects("limit edited after approval", "review-text-mismatch", lambda: approve(
        decision=fixture.decision(limit="29/25"), comment=fixture.comment(fixture.decision())))
    ledger.rejects("text appended to the approval", "review-text-mismatch", lambda: comment_with(
        body=fixture.comment(fixture.decision())["body"] + " (and more)"))
    ledger.rejects("decision band edited", "review-decision-schema", lambda: decision_with(
        per_rom_band={rom: {"min": "1/1", "max": "1/1"} for rom in perf.ROMS}))
    ledger.rejects("decision gains a field", "review-decision-schema", lambda: decision_with(extra="x"))
    ledger.rejects("cause with a line break", "review-decision-schema", lambda: decision_with(accepted_cause="a\nb"))
    ledger.rejects("unreduced limit", "review-decision-schema", lambda: decision_with(approved_ir_ratio_limit="112/100"))
    ledger.rejects("issue number as text", "review-issue-unrecorded", lambda: decision_with(review_issue_number="122"))
    ledger.rejects("issue url for another number", "review-issue-unrecorded",
                   lambda: decision_with(review_issue_url=REVIEW_ISSUE_API.replace("/122", "/9")))
    ledger.rejects("comment as old as the issue", "review-comment-predates-issue",
                   lambda: comment_with(created_at="2026-10-26T00:30:57Z"))
    ledger.rejects("comment time malformed", "review-comment-schema", lambda: comment_with(created_at="yesterday"))
    ledger.rejects("comment link of another issue", "review-reference-invalid", lambda: comment_with(
        html_url=REVIEW_COMMENT_URL.replace("/issues/122", "/issues/7")))
    # The measurement is the digest's subject: it must be consistent and taken at the named revision.
    forged = copy.deepcopy(fixture.measurement)
    forged["per_rom"]["tracer"]["ratio_band"]["max"] = "1/1"
    ledger.rejects("forged ratio band", "measurement-band-mismatch", lambda: approve(measurement=forged))
    other_identity = copy.deepcopy(fixture.measurement)
    other_identity["per_rom"]["libbet"]["base_identity"]["digest"] = "0" * 16
    ledger.rejects("other correctness evidence", "measurement-correctness-mismatch",
                   lambda: approve(measurement=other_identity))
    ledger.rejects("measurement taken at another revision", "review-source-mismatch",
                   lambda: approve(rev=perf.LIMITS_BASE_REV))
    ledger.rejects("short revision", "review-source-mismatch", lambda: approve(rev=fixture.rev[:12]))
    ledger.rejects("a limit that is no widening", "review-exception-limit-mismatch", lambda: approve(
        decision=fixture.decision(limit="11/10"), comment=fixture.comment(fixture.decision(limit="11/10"))))
    narrow = "1100000001/1000000000"
    ledger.rejects("a limit below the measured band", "review-exception-limit-below-measurement", lambda: approve(
        decision=fixture.decision(limit=narrow), comment=fixture.comment(fixture.decision(limit=narrow))))
    # The approval is bound to the project repository, which comes from the caller and never from the decision (CR-C01).
    # The foreign approval below is otherwise valid: naming its repository as the expected one makes it pass.
    foreign_decision, foreign_comment = fixture.foreign()
    ledger.rejects("an owner approval in another repository", "review-wrong-repository",
                   lambda: approve(decision=foreign_decision, comment=foreign_comment))
    ledger.passes("the same approval passes only where the caller expects that repository",
                  lambda: approve(decision=foreign_decision, comment=foreign_comment, repository=FOREIGN_REPOSITORY))
    ledger.rejects("the project approval under another expected repository", "review-wrong-repository",
                   lambda: approve(repository=FOREIGN_REPOSITORY))
    ledger.rejects("an OWNER comment by another login", "review-not-owner",
                   lambda: comment_with(user={"login": "someone-else", "id": 3}))
    ledger.rejects("a comment link in another repository", "review-reference-invalid", lambda: comment_with(
        html_url=REVIEW_COMMENT_URL.replace(PROJECT_REPOSITORY, FOREIGN_REPOSITORY)))
    ledger.rejects("a malformed expected repository", "usage", lambda: approve(repository="szTheory"))
    ledger.passes("owner and repository compare case-insensitively", lambda: approve(repository=PROJECT_REPOSITORY.upper()))
    # An unrelated edit of the comment is not a defect.
    ledger.passes("unrelated comment fields", lambda: comment_with(reactions={"+1": 3}, id=1))
    ledger.passes("approval after the mutants", approve)

    # A refusal writes nothing and leaves its inputs untouched; an existing output is never overwritten.
    refused = fixture.comment(fixture.decision(), author_association="MEMBER")
    decision_path = write_text(scratch / "refused-decision.json", json.dumps(fixture.decision(), sort_keys=True))
    comment_path = write_text(scratch / "refused-comment.json", json.dumps(refused))
    before = Path(decision_path).read_bytes()
    out_path, receipt_path = scratch / "never-written.json", scratch / "never-written-receipt.json"
    code, _, error = spawn(Path(__file__).resolve(), "--review-approval", "--comment-json", comment_path,
                           "--decision", decision_path, "--measurement", str(fixture.measurement_path),
                           "--rev", fixture.rev, "--output", str(out_path), "--exception-receipt", str(receipt_path))
    ledger.check("a refusal exits 1 with its reason", code == 1 and error.startswith("REJECT review-not-owner:"), error, control=True)
    good_comment_path = write_text(scratch / "foreign-check-comment.json", json.dumps(fixture.comment(fixture.decision())))
    code, _, error = spawn(Path(__file__).resolve(), "--review-approval", "--comment-json", good_comment_path,
                           "--decision", decision_path, "--measurement", str(fixture.measurement_path),
                           "--rev", fixture.rev, "--repository", FOREIGN_REPOSITORY, "--output", str(out_path))
    ledger.check("the CLI --repository is the expected repository", code == 1 and
                 error.startswith("REJECT review-wrong-repository:") and not out_path.exists(), error, control=True)
    ledger.check("a refusal writes no output and edits no input",
                 not out_path.exists() and not receipt_path.exists() and Path(decision_path).read_bytes() == before, control=True)
    existing = scratch / "existing.json"
    existing.write_text("keep", encoding="utf-8")
    good_comment = write_text(scratch / "good-comment.json", json.dumps(fixture.comment(fixture.decision())))
    ledger.rejects("an existing output is not overwritten", "output-exists", lambda: run_review_approval({
        "comment-json": good_comment, "decision": decision_path, "measurement": str(fixture.measurement_path),
        "rev": fixture.rev, "output": str(existing), "exception-receipt": str(scratch / "second.json")}))
    ledger.check("the existing output and the second file are untouched",
                 existing.read_text(encoding="utf-8") == "keep" and not (scratch / "second.json").exists())


def nightly_run(run_id: int, head: str, *, created: str = BASE_TIME, status: str = "completed",
                conclusion: str = "success", event: str = "workflow_dispatch", branch: str = "rehearsal/v0.2.1",
                attempt: int = 1, workflow: str = NIGHTLY_WORKFLOW_NAME) -> dict:
    return {"databaseId": run_id, "attempt": attempt, "headSha": head, "headBranch": branch, "event": event,
            "status": status, "conclusion": conclusion, "createdAt": created, "workflowName": workflow}


def nightly_view(entry: dict, *, replay: str = "success", replay_status: str = "completed",
                 updated: str = "2026-10-28T03:40:05Z", started: str = "2026-10-28T03:00:10Z",
                 finished: str = "2026-10-28T03:40:00Z", jobs=None) -> dict:
    view = dict(entry, updatedAt=updated)
    view["jobs"] = [{"name": NIGHTLY_REPLAY_JOB, "status": replay_status, "conclusion": replay,
                     "startedAt": started, "completedAt": finished}] if jobs is None else jobs
    return view


CHECKED_AT = "2026-10-28T04:00:00Z"


def self_test_nightly_gate(ledger: Ledger, rev: str, scratch: Path) -> None:
    good = nightly_run(500, rev)
    receipt = ledger.passes("newest exact-head success", lambda: nightly_gate(
        [good], nightly_view(good), rev, rev, None, CHECKED_AT)) or {}
    ledger.check("the receipt binds run, head, tree and replay", receipt.get("run_id") == 500 and
                 receipt.get("head_sha") == rev and receipt.get("source_sha") == rev and
                 receipt.get("tree_sha") == tree_of(rev, "x") and receipt.get("replay_job_conclusion") == "success" and
                 receipt.get("checked_at") == CHECKED_AT and receipt.get("conclusion") == "success", str(receipt))
    older_red = nightly_run(400, rev, created="2026-10-27T03:00:00Z", conclusion="failure")
    ledger.passes("an older red run does not poison a newer green one", lambda: nightly_gate(
        [older_red, good], nightly_view(good), rev, None, None, CHECKED_AT))
    other = "1" * 40
    ledger.passes("a branch filter keeps only that branch", lambda: nightly_gate(
        [good, nightly_run(900, other, branch="main", created="2026-10-29T03:00:00Z")], nightly_view(good), rev,
        None, "rehearsal/v0.2.1", CHECKED_AT))
    # The CLI writes the receipt exclusively, on success alone.
    runs = write_text(scratch / "runs.json", json.dumps([good]))
    view = write_text(scratch / "run.json", json.dumps(nightly_view(good)))
    output = scratch / "receipt.json"
    script = Path(__file__).resolve()
    code, out, err = spawn(script, "--nightly-gate", "--runs-json", runs, "--run-json", view, "--head", rev,
                           "--output", str(output), "--checked-at", CHECKED_AT)
    ledger.check("CLI writes the receipt", code == 0 and "nightly-gate pass run_id=500" in out and output.is_file(), out + err)
    ledger.check("the written receipt is the judged one", read_json(output, "x") == receipt)
    first = output.read_bytes()
    code, out, err = spawn(script, "--nightly-gate", "--runs-json", runs, "--run-json", view, "--head", rev,
                           "--output", str(output), "--checked-at", CHECKED_AT)
    ledger.check("an existing receipt is never overwritten",
                 code == 1 and err.startswith("REJECT nightly-output-exists:") and output.read_bytes() == first, err, control=True)
    # Tree equality: a second commit with the same tree is the same source (squash or rehearsal head).
    with tempfile.TemporaryDirectory(prefix="gbb-nightly-tree-") as directory:
        repo = Path(directory)
        steps = [("init", "-q"), ("config", "user.email", "gate@example.invalid"), ("config", "user.name", "gate"),
                 ("config", "commit.gpgsign", "false")]
        for step in steps:
            git(*step, cwd=repo)
        (repo / "file.txt").write_text("one\n", encoding="utf-8", newline="\n")
        git("add", "file.txt", cwd=repo)
        git("commit", "-q", "-m", "one", cwd=repo)
        first_commit = git("rev-parse", "HEAD", cwd=repo).stdout.strip()
        git("commit", "-q", "--allow-empty", "-m", "same tree", cwd=repo)
        same_tree = git("rev-parse", "HEAD", cwd=repo).stdout.strip()
        (repo / "file.txt").write_text("two\n", encoding="utf-8", newline="\n")
        git("commit", "-q", "-am", "two", cwd=repo)
        changed = git("rev-parse", "HEAD", cwd=repo).stdout.strip()
        global REPO_ROOT
        saved, REPO_ROOT = REPO_ROOT, repo
        try:
            entry = nightly_run(600, first_commit)
            ledger.passes("the rehearsed head and the tagged commit share a tree", lambda: nightly_gate(
                [entry], nightly_view(entry), first_commit, same_tree, None, CHECKED_AT))
            ledger.rejects("a different tree is a different source", "nightly-source-mismatch", lambda: nightly_gate(
                [entry], nightly_view(entry), first_commit, changed, None, CHECKED_AT))
        finally:
            REPO_ROOT = saved


def self_test_nightly_controls(ledger: Ledger, rev: str, scratch: Path) -> None:
    other = "1" * 40
    good = nightly_run(500, rev)

    def gate(runs, view, **keywords):
        return lambda: nightly_gate(runs, view, keywords.get("head", rev), keywords.get("rev"), keywords.get("branch"),
                                    keywords.get("checked", CHECKED_AT))

    ledger.passes("valid receipt before the mutants", gate([good], nightly_view(good)))
    # The six named mutants.
    failed = nightly_run(500, rev, conclusion="failure")
    ledger.rejects("failure conclusion", "nightly-not-success", gate([failed], nightly_view(failed)))
    superseding = nightly_run(700, other, created="2026-10-29T03:00:00Z")
    ledger.rejects("wrong head: a newer run at another head supersedes", "nightly-head-mismatch",
                   gate([good, superseding], nightly_view(good)))
    skipped_replay = nightly_view(good, replay="skipped")
    ledger.rejects("skipped replay", "nightly-replay-not-success", gate([good], skipped_replay))
    running = nightly_run(500, rev, status="in_progress", conclusion="")
    ledger.rejects("run in progress", "nightly-in-progress", gate([running], nightly_view(running, replay="", replay_status="in_progress")))
    ledger.rejects("no run at head", "nightly-no-run-at-head", gate([nightly_run(500, other)], nightly_view(nightly_run(500, other))))
    older_green = nightly_run(400, rev, created="2026-10-27T03:00:00Z")
    newer_red = nightly_run(500, rev, conclusion="failure")
    ledger.rejects("older green behind a newer red: the green is not the newest", "nightly-not-newest",
                   gate([older_green, newer_red], nightly_view(older_green)))
    ledger.rejects("older green behind a newer red: the newest is red", "nightly-not-success",
                   gate([older_green, newer_red], nightly_view(newer_red)))
    # Further skipped, failed, missing and in-progress variants.
    ledger.rejects("failed replay", "nightly-replay-not-success", gate([good], nightly_view(good, replay="failure")))
    ledger.rejects("cancelled replay", "nightly-replay-not-success", gate([good], nightly_view(good, replay="cancelled")))
    ledger.rejects("replay job missing", "nightly-replay-not-success", gate([good], nightly_view(good, jobs=[])))
    duplicate = nightly_view(good)["jobs"] * 2
    ledger.rejects("replay job repeated", "nightly-replay-not-success", gate([good], nightly_view(good, jobs=duplicate)))
    ledger.rejects("replay job still running", "nightly-replay-not-success",
                   gate([good], nightly_view(good, replay="", replay_status="in_progress")))
    for label, conclusion in (("cancelled", "cancelled"), ("timed out", "timed_out"), ("skipped", "skipped"), ("neutral", "neutral")):
        entry = nightly_run(500, rev, conclusion=conclusion)
        ledger.rejects("run %s" % label, "nightly-not-success", gate([entry], nightly_view(entry)))
    ledger.rejects("newest run queued", "nightly-in-progress", gate(
        [nightly_run(500, rev, status="queued", conclusion="")],
        nightly_view(nightly_run(500, rev, status="queued", conclusion=""))))
    ledger.rejects("empty run list", "nightly-no-run-at-head", gate([], nightly_view(good)))
    # Eligibility: another workflow, another event or another branch is not this evidence.
    ledger.rejects("another workflow at the head", "nightly-no-run-at-head",
                   gate([nightly_run(500, rev, workflow="ci")], nightly_view(good)))
    ledger.rejects("a pull_request run at the head", "nightly-no-run-at-head",
                   gate([nightly_run(500, rev, event="pull_request")], nightly_view(good)))
    ledger.rejects("another branch under a branch filter", "nightly-no-run-at-head",
                   gate([nightly_run(500, rev, branch="main")], nightly_view(good), branch="rehearsal/v0.2.1"))
    ledger.passes("a scheduled run is eligible", gate([nightly_run(500, rev, event="schedule", branch="main")],
                                                       nightly_view(nightly_run(500, rev, event="schedule", branch="main"))))
    # The viewed run must be exactly the listed newest run.
    ledger.rejects("another attempt of the run", "nightly-not-newest",
                   gate([good], nightly_view(nightly_run(500, rev, attempt=2))))
    ledger.rejects("viewed run at another head", "nightly-head-mismatch", gate([good], nightly_view(nightly_run(500, other))))
    ledger.rejects("viewed run disagrees with its list entry", "nightly-run-mismatch",
                   gate([good], nightly_view(nightly_run(500, rev, event="schedule"))))
    newer_attempt = nightly_run(500, rev, attempt=2, conclusion="failure")
    ledger.rejects("a repeated run id in the list", "nightly-input-schema", gate([good, newer_attempt], nightly_view(good)))
    # Timestamps and malformed input.
    ledger.rejects("checked before the run finished", "nightly-timestamp",
                   gate([good], nightly_view(good), checked="2026-10-28T03:30:00Z"))
    ledger.rejects("checked_at malformed", "nightly-timestamp", gate([good], nightly_view(good), checked="today"))
    ledger.rejects("replay finishes before it starts", "nightly-timestamp", gate(
        [good], nightly_view(good, started="2026-10-28T03:50:00Z", finished="2026-10-28T03:40:00Z")))
    ledger.rejects("run updated before it was created", "nightly-timestamp",
                   gate([good], nightly_view(good, updated="2026-10-28T02:00:00Z")))
    ledger.rejects("created time malformed", "nightly-input-schema",
                   gate([nightly_run(500, rev, created="2026-10-28")], nightly_view(good)))
    ledger.rejects("run list is not an array", "nightly-input-schema", gate({"runs": [good]}, nightly_view(good)))
    ledger.rejects("run field missing", "nightly-input-schema", gate([{key: value for key, value in good.items() if key != "attempt"}], nightly_view(good)))
    ledger.rejects("run id as text", "nightly-input-schema", gate([dict(good, databaseId="500")], nightly_view(good)))
    # The head and the boundary source are immutable commits read with git.
    ledger.rejects("head is a name", "nightly-head-unresolved", gate([good], nightly_view(good), head="HEAD"))
    ledger.rejects("head is not an object", "nightly-head-unresolved",
                   gate([nightly_run(500, other)], nightly_view(nightly_run(500, other)), head=other))
    ledger.rejects("boundary revision of another tree", "nightly-source-mismatch",
                   gate([good], nightly_view(good), rev=perf_gate().LIMITS_BASE_REV))
    ledger.rejects("boundary revision is a name", "nightly-source-mismatch", gate([good], nightly_view(good), rev="HEAD"))
    ledger.passes("unrelated run fields are ignored", gate([dict(good, displayTitle="nightly", url="https://example.invalid/r")],
                                                           dict(nightly_view(good), displayTitle="nightly")))
    # A refusal writes nothing.
    runs = write_text(scratch / "red-runs.json", json.dumps([newer_red]))
    view = write_text(scratch / "red-run.json", json.dumps(nightly_view(newer_red)))
    output = scratch / "must-not-exist.json"
    code, _, error = spawn(Path(__file__).resolve(), "--nightly-gate", "--runs-json", runs, "--run-json", view,
                           "--head", rev, "--output", str(output), "--checked-at", CHECKED_AT)
    ledger.check("a refused nightly gate exits 1 with its reason and writes nothing",
                 code == 1 and error.startswith("REJECT nightly-not-success:") and not output.exists(), error, control=True)
    ledger.passes("receipt after the mutants", gate([good], nightly_view(good)))


def self_test(suite, rev) -> list:
    resolve_commit(rev, "usage", "--rev")
    suites = [suite] if suite else ["review-approval", "review-controls", "nightly-gate", "nightly-controls"]
    lines = []
    with tempfile.TemporaryDirectory(prefix="gbb-release-gates-selftest-") as directory:
        scratch = Path(directory)
        fixture = None
        for name in suites:
            ledger = Ledger()
            part = scratch / name
            part.mkdir()
            if name.startswith("review"):
                fixture = ReviewFixture(part, rev)
                (self_test_review_approval if name == "review-approval" else self_test_review_controls)(ledger, fixture)
            else:
                (self_test_nightly_gate if name == "nightly-gate" else self_test_nightly_controls)(ledger, rev, part)
            lines.append(ledger.summary(name))
    return lines


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
