#!/usr/bin/env python3
"""Verify compiled portable state pins against immutable source and compatibility history."""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile


ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
GOLDEN_PATH = "tests/baseline/state-goldens-v1.json"
COMPATIBILITY_PATH = "tests/data/state-compatibility.json"
EVIDENCE_REF = "phase:GB-17-native-save-state-core/17-05-SUMMARY.md"
PLANNING_COMPONENT = "." + "planning"
PHASES_COMPONENT = "ph" + "ases"
OWNER_RULES_FILE = "AGENTS" + ".md"
DECISIONS_FILE = PLANNING_COMPONENT + "/context/DECISIONS.md"
SOURCE_INPUTS = (
    "CMakeLists.txt",
    "src/core/gabbaboy.c",
    "include/gabbaboy/gabbaboy.h",
    "tests/test_state_codec.c",
)
FIXTURE_IDS = (
    "dmg-rom-only",
    "cgb-compat-mbc3-rtc-audio",
    "cgb-native-mbc5-hdma-audio",
)


class Rejected(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def reject(code, message):
    raise Rejected(code, message)


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def digest_bytes(value):
    return hashlib.sha256(value).hexdigest()


def digest_json(value):
    return digest_bytes(canonical_json(value))


def run_git(repo, *args, allow_missing=False):
    result = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    if allow_missing and result.returncode != 0:
        return None
    if result.returncode != 0:
        reject("immutable-source", "git %s failed" % " ".join(args))
    return result.stdout


def immutable_revision(repo, revision):
    if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40}", revision):
        reject("immutable-revision", "revision must be a resolved lowercase 40-hex commit")
    resolved = run_git(repo, "rev-parse", "--verify", revision + "^{commit}").strip()
    if resolved != revision:
        reject("immutable-revision", "revision did not resolve to itself as a commit")
    return revision


def source_file(repo, revision, path, allow_missing=False):
    result = subprocess.run(["git", "-C", repo, "cat-file", "-e", revision + ":" + path],
                            capture_output=True)
    if result.returncode != 0:
        if allow_missing:
            return None
        reject("immutable-source", "required source file is absent from the selected commit")
    return run_git(repo, "show", revision + ":" + path)


def resolve_immutable_reference(repo, revision, reference, allow_unanchored=False):
    """Resolve logical phase references exclusively from the selected commit's tree."""
    if not isinstance(reference, str):
        reject("immutable-reference", "immutable reference must be a string")
    if "#" in reference:
        logical_path, anchor = reference.split("#", 1)
        if not anchor or not re.fullmatch(r"[A-Za-z0-9-]+", anchor):
            reject("immutable-reference", "decision reference anchor is malformed")
    elif allow_unanchored:
        logical_path, anchor = reference, None
    else:
        reject("immutable-reference", "decision reference must name an immutable file and anchor")
    if logical_path == OWNER_RULES_FILE:
        path = OWNER_RULES_FILE
    elif logical_path == "DECISIONS.md":
        path = DECISIONS_FILE
    elif logical_path.startswith("phase:"):
        suffix = logical_path[len("phase:"):]
        parts = suffix.split("/")
        if len(parts) != 2 or not parts[0].startswith("GB-17-") or not re.fullmatch(
                r"17-[A-Z0-9-]+\.(?:md|json)", parts[1]):
            reject("immutable-reference", "logical phase reference is outside the Phase 17 evidence namespace")
        tree = run_git(repo, "ls-tree", "-r", "--name-only", revision).splitlines()
        candidates = []
        for candidate in tree:
            candidate_parts = candidate.split("/")
            if (len(candidate_parts) >= 4 and candidate_parts[0] == PLANNING_COMPONENT and
                    candidate_parts[-2:] == parts):
                candidates.append(candidate)
        if len(candidates) != 1:
            reject("immutable-reference", "logical phase reference is absent or ambiguous in the selected commit")
        path = candidates[0]
    else:
        reject("immutable-reference", "decision reference uses an unsupported logical namespace")
    content = source_file(repo, revision, path)
    if anchor is not None:
        normalized_anchor = re.sub(r"[^a-z0-9]", "", anchor.lower())
        if not any(normalized_anchor in re.sub(r"[^a-z0-9]", "", line.lower())
                   for line in content.splitlines()):
            reject("immutable-reference", "logical decision reference anchor is absent from the selected commit")
    return path, content


def validate_pin_fixture_wiring(cmake):
    compact = re.sub(r"\s+", " ", cmake)
    requirements = (
        r"add_test\(NAME state_pin_planning\b",
        r"set_tests_properties\(state_pin_planning PROPERTIES LABELS \"planning\" FIXTURES_SETUP gbb_state_pin_evidence\)",
        r"set_tests_properties\(state_portable_pins PROPERTIES FIXTURES_REQUIRED gbb_state_pin_evidence\)",
    )
    if any(not re.search(pattern, compact) for pattern in requirements):
        reject("pin-fixture", "compiled pin test must require the build-free planning evidence fixture")


def parse_json_text(text, what):
    try:
        value = json.loads(text)
    except (TypeError, ValueError) as error:
        reject("%s-format" % what, "%s is not valid JSON: %s" % (what, error))
    if not isinstance(value, dict):
        reject("%s-format" % what, "%s must be a JSON object" % what)
    return value


def state_tokens(repo, revision):
    cmake = source_file(repo, revision, "CMakeLists.txt")
    core = source_file(repo, revision, "src/core/gabbaboy.c")
    version = re.search(r"(?m)^project\(GabbaBoy\s+VERSION\s+(\d+)\.(\d+)\.(\d+)\s+LANGUAGES\s+C\)", cmake)
    format_match = re.search(r"(?m)^#define\s+GBB_STATE_FORMAT_VERSION\s+(\d+)u?\s*$", core)
    behavior_match = re.search(r"(?m)^#define\s+GBB_STATE_BEHAVIOR_VERSION\s+(\d+)u?\s*$", core)
    if not version or bool(format_match) != bool(behavior_match):
        reject("state-token-source", "release token is absent or only one state compatibility token is declared")
    tokens = {
        "release": {"major": int(version.group(1)), "minor": int(version.group(2)),
                    "patch": int(version.group(3))},
        "format_version": int(format_match.group(1)) if format_match else None,
        "behavior_version": int(behavior_match.group(1)) if behavior_match else None,
    }
    if any(component > 65535 for component in tokens["release"].values()):
        reject("state-token-source", "release token exceeds the portable header width")
    return tokens


def validate_pin_document(document, what):
    required = {"schema", "release", "format_version", "behavior_version", "fixtures"}
    if set(document) != required or document.get("schema") != "state-goldens-v1":
        reject("%s-schema" % what, "%s has unknown or missing top-level fields" % what)
    release = document.get("release")
    if not isinstance(release, dict) or set(release) != {"major", "minor", "patch"} or \
            any(type(release[key]) is not int or release[key] < 0 or release[key] > 65535
                for key in ("major", "minor", "patch")):
        reject("%s-schema" % what, "%s release triplet is malformed" % what)
    for token in ("format_version", "behavior_version"):
        if type(document.get(token)) is not int or document[token] < 1 or document[token] > 65535:
            reject("%s-schema" % what, "%s %s must be a positive u16" % (what, token))
    fixtures = document.get("fixtures")
    if not isinstance(fixtures, list) or tuple(row.get("id") for row in fixtures
                                                if isinstance(row, dict)) != FIXTURE_IDS:
        reject("%s-schema" % what, "%s fixture ids differ from the required ordered set" % what)
    keys = {"id", "profile", "mode", "cartridge", "fixture", "state_size",
            "rom_sha256", "state_sha256"}
    for row in fixtures:
        if not isinstance(row, dict) or set(row) != keys:
            reject("%s-schema" % what, "%s fixture has unknown or missing fields" % what)
        if any(not isinstance(row[key], str) or not row[key] for key in
               ("id", "profile", "mode", "cartridge", "fixture")):
            reject("%s-schema" % what, "%s fixture labels must be non-empty strings" % what)
        if type(row["state_size"]) is not int or row["state_size"] < 64 or row["state_size"] > 524352:
            reject("%s-schema" % what, "%s state_size is outside the bounded wire format" % what)
        for key in ("rom_sha256", "state_sha256"):
            if not isinstance(row[key], str) or not re.fullmatch(r"[0-9a-f]{64}", row[key]):
                reject("%s-schema" % what, "%s %s must be 64 lowercase hex digits" % (what, key))
    return document


def document_tokens(document):
    return {"release": document["release"], "format_version": document["format_version"],
            "behavior_version": document["behavior_version"]}


def load_optional_commit_json(repo, revision, path, what):
    text = source_file(repo, revision, path, allow_missing=True)
    return None if text is None else parse_json_text(text, what)


def validate_evidence_record(repo, evidence):
    if not isinstance(evidence, dict) or set(evidence) != {"revision", "summary_path", "description"}:
        reject("disposition-evidence", "continuation evidence must identify a revision, summary and description")
    evidence_revision = immutable_revision(repo, evidence["revision"])
    if evidence["summary_path"] != EVIDENCE_REF or not isinstance(evidence["description"], str) or \
            not evidence["description"].strip():
        reject("disposition-evidence", "continuation evidence must cite the completed snapshot-fork summary")
    return evidence_revision


def verify_evidence(repo, base_revision, evidence, current_revision=None, initial=False):
    evidence_revision = validate_evidence_record(repo, evidence)
    evidence_base = base_revision if not initial else current_revision
    ancestor = subprocess.run(["git", "-C", repo, "merge-base", "--is-ancestor",
                               evidence_revision, evidence_base], capture_output=True)
    if ancestor.returncode != 0:
        message = ("continuation evidence is not present before the immutable base" if not initial
                   else "initial continuation evidence is not present at the selected source revision")
        reject("disposition-evidence-stale", message)
    if initial:
        base_before_evidence = subprocess.run(["git", "-C", repo, "merge-base", "--is-ancestor",
                                               base_revision, evidence_revision], capture_output=True)
        if base_before_evidence.returncode != 0:
            reject("disposition-evidence-stale", "initial evidence is not descended from the selected pre-state base")
    summary_path, summary = resolve_immutable_reference(repo, evidence_revision, evidence["summary_path"],
                                                        allow_unanchored=True)
    if summary_path.split("/")[-1] != "17-05-SUMMARY.md":
        reject("disposition-evidence", "continuation evidence resolved to the wrong summary file")
    required_claims = ("status: complete", "198 serialized fields", "14 in-flight categories")
    if any(claim not in summary for claim in required_claims):
        reject("disposition-evidence", "snapshot-fork summary lacks complete field/category evidence")


def verify_decision_references(repo, revision, references):
    for reference in references:
        resolve_immutable_reference(repo, revision, reference)


def validate_compatibility(repo, base_revision, current_revision, base_golden,
                           current_golden, base_tokens, current_tokens, compatibility,
                           validate_planning_evidence=True):
    if not isinstance(compatibility, dict) or set(compatibility) != {"schema", "dispositions"} or \
            compatibility.get("schema") != "state-compatibility-v1" or \
            not isinstance(compatibility.get("dispositions"), list):
        reject("compatibility-schema", "compatibility data must use state-compatibility-v1 dispositions")
    old_sha = None if base_golden is None else digest_json(base_golden)
    new_sha = digest_json(current_golden)
    matches = [row for row in compatibility["dispositions"]
               if isinstance(row, dict) and row.get("base_revision") == base_revision and
               row.get("old_golden_sha256") == old_sha and row.get("new_golden_sha256") == new_sha and
               row.get("tokens_before") == base_tokens and row.get("tokens_after") == current_tokens]
    if len(matches) != 1:
        reject("compatibility-missing", "changed pins or tokens need one exact immutable-base disposition")
    row = matches[0]
    required = {"id", "kind", "accepted", "approved_by", "approval_basis", "decision_refs",
                "decision", "rationale",
                "base_revision", "old_golden_sha256", "new_golden_sha256", "tokens_before",
                "tokens_after", "affected_semantics", "evidence"}
    if row.get("kind") == "pre-first-state-release-evolution":
        required |= {"base_state_release_exists"}
    else:
        required |= {"required_token"}
    approver = row.get("approved_by")
    if set(row) != required or row.get("accepted") is not True or \
            approver not in ("phase-owner", "delegated-phase-orchestrator") or not row.get("id") or \
            not isinstance(row.get("approval_basis"), str) or not row["approval_basis"].strip() or \
            (approver == "delegated-phase-orchestrator" and OWNER_RULES_FILE not in row["approval_basis"]) or \
            not isinstance(row.get("decision_refs"), list) or not row["decision_refs"] or \
            any(not isinstance(item, str) or not item.strip() for item in row["decision_refs"]) or \
            not isinstance(row.get("decision"), str) or not row["decision"].strip() or \
            not isinstance(row.get("rationale"), str) or not row["rationale"].strip() or \
            not isinstance(row.get("affected_semantics"), list) or not row["affected_semantics"]:
        reject("compatibility-disposition", "disposition is incomplete or has no explicit phase-owner acceptance")
    validate_evidence_record(repo, row["evidence"])
    if validate_planning_evidence:
        verify_evidence(repo, base_revision, row["evidence"], current_revision=current_revision,
                        initial=row["kind"] == "pre-first-state-release-evolution")
        verify_decision_references(repo, current_revision, row["decision_refs"])

    if row["kind"] == "pre-first-state-release-evolution":
        no_prior_tokens = base_tokens["format_version"] is None and base_tokens["behavior_version"] is None
        unchanged_existing_tokens = (base_tokens["format_version"] is not None and
                                     base_tokens["behavior_version"] is not None and
                                     base_tokens == current_tokens)
        if row["base_state_release_exists"] is not False or old_sha is not None or \
                not (no_prior_tokens or unchanged_existing_tokens) or \
                base_tokens["release"] != current_tokens["release"]:
            reject("compatibility-pre-release", "initial state baseline needs no prior pins and either absent or unchanged state tokens")
        if current_tokens["release"] != {"major": 0, "minor": 2, "patch": 1}:
            reject("compatibility-pre-release", "pre-first-release evolution cannot relabel the 0.2.1 pins")
    elif row["kind"] in ("format-change", "behavior-change", "release-change"):
        required_token = {"format-change": "format_version", "behavior-change": "behavior_version",
                          "release-change": "release"}[row["kind"]]
        if row.get("required_token") != required_token or base_tokens[required_token] == current_tokens[required_token]:
            reject("required-token-unchanged", "the disposition's required compatibility token did not change")
    else:
        reject("compatibility-disposition", "unknown compatibility disposition kind")


def run_emitter(executable):
    if not isinstance(executable, str) or not os.path.isfile(executable):
        reject("compiled-emitter", "--check must name the built test_state_codec executable")
    try:
        result = subprocess.run([executable, "state_portable_pins"], capture_output=True,
                                text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        reject("compiled-emitter", "compiled state-pin emitter could not complete")
    if result.returncode != 0 or result.stderr:
        reject("compiled-emitter", "compiled state-pin emitter returned an error")
    actual = parse_json_text(result.stdout, "compiled-emission")
    required = {"schema", "release", "format_version", "behavior_version", "fixtures"}
    if set(actual) != required or actual.get("schema") != "state-pin-emission-v1":
        reject("compiled-emission", "compiled state-pin output has unknown or missing fields")
    return actual


def verify_snapshot(repo, source_revision, base_revision, actual,
                    validate_planning_evidence=True):
    source_revision = immutable_revision(repo, source_revision)
    base_revision = immutable_revision(repo, base_revision)
    ancestry = subprocess.run(["git", "-C", repo, "merge-base", "--is-ancestor",
                               base_revision, source_revision], capture_output=True)
    if ancestry.returncode != 0:
        reject("immutable-base", "base revision is not an ancestor of the selected source commit")
    current_golden_text = source_file(repo, source_revision, GOLDEN_PATH)
    validate_pin_fixture_wiring(source_file(repo, source_revision, "tests/CMakeLists.txt"))
    current_golden = validate_pin_document(parse_json_text(current_golden_text, "state-goldens"), "current pins")
    current_tokens = state_tokens(repo, source_revision)
    if document_tokens(current_golden) != current_tokens:
        reject("release-token-mismatch", "golden release/format/behavior tokens differ from immutable source")
    if actual != dict(current_golden, schema="state-pin-emission-v1"):
        reject("pin-mismatch", "compiled canonical state bytes differ from the immutable fixture pins")

    base_golden_text = source_file(repo, base_revision, GOLDEN_PATH, allow_missing=True)
    base_golden = None
    if base_golden_text is not None:
        base_golden = validate_pin_document(parse_json_text(base_golden_text, "base state-goldens"), "base pins")
    base_tokens = state_tokens(repo, base_revision)
    if base_golden is not None and document_tokens(base_golden) != base_tokens:
        reject("base-token-mismatch", "immutable base pins differ from its declared release/format/behavior tokens")
    changed = base_golden != current_golden or base_tokens != current_tokens
    if not changed:
        return {"source_revision": source_revision, "base_revision": base_revision,
                "golden_sha256": digest_json(current_golden), "base_golden_sha256": digest_json(base_golden)
                if base_golden is not None else None}

    compatibility = load_optional_commit_json(repo, source_revision, COMPATIBILITY_PATH,
                                              "state-compatibility")
    if compatibility is None:
        reject("compatibility-missing", "changed pins or tokens need committed state-compatibility.json")
    validate_compatibility(repo, base_revision, source_revision, base_golden,
                           current_golden, base_tokens, current_tokens, compatibility,
                           validate_planning_evidence=validate_planning_evidence)
    return {"source_revision": source_revision, "base_revision": base_revision,
            "golden_sha256": digest_json(current_golden), "base_golden_sha256": digest_json(base_golden)
            if base_golden is not None else None}


def planning_check(repo, source_revision, base_revision):
    source_revision = immutable_revision(repo, source_revision)
    base_revision = immutable_revision(repo, base_revision)
    validate_pin_fixture_wiring(source_file(repo, source_revision, "tests/CMakeLists.txt"))
    ancestry = subprocess.run(["git", "-C", repo, "merge-base", "--is-ancestor",
                               base_revision, source_revision], capture_output=True)
    if ancestry.returncode != 0:
        reject("immutable-base", "base revision is not an ancestor of the selected source commit")
    current_text = source_file(repo, source_revision, GOLDEN_PATH)
    current = validate_pin_document(parse_json_text(current_text, "state-goldens"), "current pins")
    current_tokens = state_tokens(repo, source_revision)
    if document_tokens(current) != current_tokens:
        reject("release-token-mismatch", "golden release/format/behavior tokens differ from immutable source")
    base_text = source_file(repo, base_revision, GOLDEN_PATH, allow_missing=True)
    base = None if base_text is None else validate_pin_document(
        parse_json_text(base_text, "base state-goldens"), "base pins")
    base_tokens = state_tokens(repo, base_revision)
    if base is not None and document_tokens(base) != base_tokens:
        reject("base-token-mismatch", "immutable base pins differ from its declared compatibility tokens")
    if base == current and base_tokens == current_tokens:
        return {"source_revision": source_revision, "base_revision": base_revision,
                "evidence": "not-required-no-change"}
    compatibility = load_optional_commit_json(repo, source_revision, COMPATIBILITY_PATH,
                                              "state-compatibility")
    if compatibility is None:
        reject("compatibility-missing", "changed pins or tokens need committed state-compatibility.json")
    validate_compatibility(repo, base_revision, source_revision, base, current,
                           base_tokens, current_tokens, compatibility,
                           validate_planning_evidence=True)
    return {"source_revision": source_revision, "base_revision": base_revision,
            "evidence": "immutable-phase-references-and-summary-pass"}


def source_input_digest(repo, revision):
    inputs = {path: digest_bytes(source_file(repo, revision, path).encode("utf-8"))
              for path in SOURCE_INPUTS}
    return digest_json(inputs)


def check_command(repo, source_revision, base_revision, executable):
    actual = run_emitter(executable)
    result = verify_snapshot(repo, source_revision, base_revision, actual,
                             validate_planning_evidence=False)
    return {**result, "source_input_sha256": source_input_digest(repo, source_revision),
            "compiled_executable_sha256": digest_bytes(open(executable, "rb").read()),
            "fixture_count": len(actual["fixtures"]),
            "fixtures": [{key: row[key] for key in
                          ("id", "profile", "mode", "cartridge", "fixture", "state_size",
                           "rom_sha256", "state_sha256")} for row in actual["fixtures"]]}


def write_receipt(path, platform, result):
    if not isinstance(platform, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", platform):
        reject("receipt-platform", "receipt platform must be a short portable label")
    receipt = {
        "schema": "state-pin-receipt-v1",
        "platform": platform,
        "source_revision": result["source_revision"],
        "base_revision": result["base_revision"],
        "golden_sha256": result["golden_sha256"],
        "source_input_sha256": result["source_input_sha256"],
        "compiled_executable_sha256": result["compiled_executable_sha256"],
        "fixture_count": result["fixture_count"],
        "fixtures": result["fixtures"],
    }
    target = os.path.abspath(path)
    parent = os.path.dirname(target)
    if not os.path.isdir(parent):
        reject("receipt-output", "receipt parent directory must already exist")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                         dir=parent, prefix=".state-pin-receipt-",
                                         delete=False) as handle:
            temporary = handle.name
            json.dump(receipt, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary, target)
    except OSError:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)
        reject("receipt-output", "could not atomically write the state-pin receipt")


def write_git_file(repo, path, content):
    target = os.path.join(repo, path)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8") as handle:
        handle.write(content)


def commit_fixture(repo, message):
    environment = dict(os.environ)
    environment.update({"GIT_AUTHOR_NAME": "GabbaBoy contributors",
                        "GIT_AUTHOR_EMAIL": "gabbaboy@users.noreply.github.com",
                        "GIT_COMMITTER_NAME": "GabbaBoy contributors",
                        "GIT_COMMITTER_EMAIL": "gabbaboy@users.noreply.github.com",
                        "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull})
    for args in (("add", "-A"), ("commit", "-q", "-m", message)):
        result = subprocess.run(["git", "-C", repo, *args], capture_output=True,
                                text=True, env=environment)
        if result.returncode != 0:
            reject("self-test-failed", "synthetic immutable history could not be committed")
    return run_git(repo, "rev-parse", "HEAD").strip()


def fixture_pin_document():
    return {
        "schema": "state-goldens-v1",
        "release": {"major": 0, "minor": 2, "patch": 1},
        "format_version": 1,
        "behavior_version": 1,
        "fixtures": [
            {"id": "dmg-rom-only", "profile": "DMG-CPU-B", "mode": "DMG",
             "cartridge": "ROM-only", "fixture": "state-codec-synthetic-v1", "state_size": 189176,
             "rom_sha256": "a" * 64, "state_sha256": "1" * 64},
            {"id": "cgb-compat-mbc3-rtc-audio", "profile": "CGB-CPU-E",
             "mode": "CGB-DMG-compatibility", "cartridge": "MBC3-RTC-RAM",
             "fixture": "state-codec-synthetic-v1", "state_size": 197368,
             "rom_sha256": "b" * 64, "state_sha256": "2" * 64},
            {"id": "cgb-native-mbc5-hdma-audio", "profile": "CGB-CPU-E", "mode": "CGB-native",
             "cartridge": "MBC5-rumble-RAM", "fixture": "state-codec-synthetic-v1",
             "state_size": 197368, "rom_sha256": "c" * 64, "state_sha256": "3" * 64},
        ],
    }


def initial_disposition(base_revision, golden, evidence_revision, tokens_before=None,
                        tokens_after=None):
    if tokens_after is None:
        tokens_after = {"release": {"major": 0, "minor": 2, "patch": 1},
                        "format_version": 1, "behavior_version": 1}
    if tokens_before is None:
        tokens_before = tokens_after
    return {
        "id": "initial-state-pin-baseline",
        "kind": "pre-first-state-release-evolution",
        "accepted": True,
        "approved_by": "delegated-phase-orchestrator",
        "approval_basis": "Delegated orchestrator approval under " + OWNER_RULES_FILE +
                          " routine in-phase authorization for the initial 0.2.1 state baseline.",
        "decision_refs": [OWNER_RULES_FILE + "#Workflow-contract",
                          "phase:GB-17-native-save-state-core/17-RESEARCH.md#D-01",
                          "phase:GB-17-native-save-state-core/17-06-PLAN.md#Task-1",
                          "phase:GB-17-native-save-state-core/17-06-PLAN.md#Task-3"],
        "decision": "D-01 permits a documented initial baseline before the first state release; this creates the first pins at the existing release version.",
        "rationale": "These 0.2.1 pins establish the initial portable baseline; they do not imply compatibility among arbitrary unreleased builds or infer semantic equivalence.",
        "base_revision": base_revision,
        "old_golden_sha256": None,
        "new_golden_sha256": digest_json(golden),
        "tokens_before": tokens_before,
        "tokens_after": tokens_after,
        "affected_semantics": ["canonical serialized bytes for DMG, CGB compatibility, and native CGB fixtures"],
        "base_state_release_exists": False,
        "evidence": {"revision": evidence_revision, "summary_path": EVIDENCE_REF,
                     "description": "Independent snapshot continuation covers 153 corpus cases, 198 fields, and 14 applicable in-flight categories."},
    }


def self_test():
    controls = 0
    with tempfile.TemporaryDirectory(prefix="state-pins-selftest-") as scratch:
        repo = os.path.join(scratch, "repo")
        os.makedirs(repo)
        subprocess.run(["git", "-C", repo, "init", "-q", "-b", "main"], check=True)
        valid_wiring = """project(GabbaBoy VERSION 0.2.1 LANGUAGES C)
add_test(NAME state_pin_planning COMMAND verifier --planning-check)
set_tests_properties(state_pin_planning PROPERTIES LABELS "planning" FIXTURES_SETUP gbb_state_pin_evidence)
set_tests_properties(state_portable_pins PROPERTIES FIXTURES_REQUIRED gbb_state_pin_evidence)
"""
        validate_pin_fixture_wiring(valid_wiring)
        controls = 1
        for label, broken in (
            ("omitted immutable-evidence fixture", valid_wiring.replace(
                "FIXTURES_REQUIRED gbb_state_pin_evidence", "FIXTURES_REQUIRED missing_fixture")),
            ("incorrect immutable-evidence fixture", valid_wiring.replace(
                "FIXTURES_SETUP gbb_state_pin_evidence", "FIXTURES_SETUP missing_fixture")),
            ("unlabelled planning evidence test", valid_wiring.replace('LABELS "planning" ', "")),
        ):
            try:
                validate_pin_fixture_wiring(broken)
            except Rejected as error:
                if error.code != "pin-fixture":
                    reject("self-test-failed", "%s produced the wrong rejection" % label)
            else:
                reject("self-test-failed", "%s was accepted" % label)
            controls += 1
        write_git_file(repo, "CMakeLists.txt", valid_wiring)
        write_git_file(repo, os.path.join("tests", "CMakeLists.txt"), valid_wiring)
        write_git_file(repo, OWNER_RULES_FILE, "# Workflow contract\n")
        write_git_file(repo, DECISIONS_FILE, "| D-113 | State compatibility contract |\n| D-120 | Release version contract |\n")
        write_git_file(repo, "src/core/gabbaboy.c", "/* no state support declared at this base */\n")
        base_revision = commit_fixture(repo, "synthetic pre-state base")
        resolve_immutable_reference(repo, base_revision, "DECISIONS.md#D-113")
        controls += 1
        try:
            resolve_immutable_reference(repo, base_revision, "DECISIONS.md#D-999")
        except Rejected as error:
            if error.code != "immutable-reference":
                reject("self-test-failed", "missing decision anchor produced the wrong rejection")
        else:
            reject("self-test-failed", "missing decision anchor was accepted")
        controls += 1
        write_git_file(repo, "src/core/gabbaboy.c",
                       "#define GBB_STATE_FORMAT_VERSION 1u\n#define GBB_STATE_BEHAVIOR_VERSION 1u\n")
        summary = "---\nstatus: complete\n---\nSnapshot forks cover 198 serialized fields and 14 in-flight categories.\n"
        phase_summary_path = os.path.join(PLANNING_COMPONENT, PHASES_COMPONENT,
                                          "GB-17-native-save-state-core", "17-05-SUMMARY.md")
        phase_research_path = os.path.join(PLANNING_COMPONENT, PHASES_COMPONENT,
                                           "GB-17-native-save-state-core", "17-RESEARCH.md")
        phase_plan_path = os.path.join(PLANNING_COMPONENT, PHASES_COMPONENT,
                                       "GB-17-native-save-state-core", "17-06-PLAN.md")
        write_git_file(repo, phase_summary_path, summary)
        write_git_file(repo, phase_research_path, "- **D-01: synthetic decision**\n")
        write_git_file(repo, phase_plan_path, "<name>Task 1: synthetic task</name>\n<name>Task 3: synthetic task</name>\n")
        state_support_base = commit_fixture(repo, "synthetic state support without pins")
        golden = fixture_pin_document()
        write_git_file(repo, GOLDEN_PATH, json.dumps(golden, indent=2, sort_keys=True) + "\n")
        no_disposition_revision = commit_fixture(repo, "pins without disposition")
        actual = dict(golden, schema="state-pin-emission-v1")

        def rejected(name, code, action):
            nonlocal controls
            try:
                action()
            except Rejected as error:
                if error.code != code:
                    reject("self-test-failed", "%s produced unexpected rejection %s" % (name, error.code))
            else:
                reject("self-test-failed", "%s unexpectedly passed" % name)
            controls += 1

        rejected("missing pre-release disposition", "compatibility-missing",
                 lambda: verify_snapshot(repo, no_disposition_revision, base_revision, actual))

        current_tokens = document_tokens(golden)
        compatibility = {"schema": "state-compatibility-v1", "dispositions": [
            initial_disposition(base_revision, golden, state_support_base,
                                {"release": {"major": 0, "minor": 2, "patch": 1},
                                 "format_version": None, "behavior_version": None}, current_tokens),
            initial_disposition(state_support_base, golden, state_support_base,
                                current_tokens, current_tokens)]}
        write_git_file(repo, COMPATIBILITY_PATH, json.dumps(compatibility, indent=2, sort_keys=True) + "\n")
        accepted_revision = commit_fixture(repo, "explicit pre-release disposition")
        verified = verify_snapshot(repo, accepted_revision, base_revision, actual)
        if verified["golden_sha256"] != digest_json(golden):
            reject("self-test-failed", "explicit pre-release disposition lost its pin digest")
        controls += 1
        verify_snapshot(repo, accepted_revision, state_support_base, actual)
        controls += 1

        bad_reference = json.loads(json.dumps(compatibility))
        bad_reference["dispositions"][0]["decision_refs"][1] = (
            "phase:GB-17-native-save-state-core/17-99-PLAN.md#Task-1")
        write_git_file(repo, COMPATIBILITY_PATH, json.dumps(bad_reference, indent=2, sort_keys=True) + "\n")
        bad_reference_revision = commit_fixture(repo, "unresolvable immutable phase reference")
        rejected("incorrect immutable phase reference", "immutable-reference",
                 lambda: verify_snapshot(repo, bad_reference_revision, base_revision, actual))

        bad_summary = "---\nstatus: complete\n---\nSnapshot continuation evidence is incomplete.\n"
        write_git_file(repo, phase_summary_path, bad_summary)
        bad_summary_revision = commit_fixture(repo, "incomplete continuation summary")
        bad_evidence = json.loads(json.dumps(compatibility))
        bad_evidence["dispositions"][0]["evidence"]["revision"] = bad_summary_revision
        write_git_file(repo, COMPATIBILITY_PATH, json.dumps(bad_evidence, indent=2, sort_keys=True) + "\n")
        bad_evidence_revision = commit_fixture(repo, "incorrect immutable continuation evidence")
        rejected("incorrect immutable summary evidence", "disposition-evidence",
                 lambda: verify_snapshot(repo, bad_evidence_revision, base_revision, actual))

        write_git_file(repo, phase_summary_path, summary)
        write_git_file(repo, COMPATIBILITY_PATH, json.dumps(compatibility, indent=2, sort_keys=True) + "\n")
        accepted_revision = commit_fixture(repo, "restore accepted phase evidence")

        missing_basis = json.loads(json.dumps(compatibility))
        missing_basis["dispositions"][0]["approval_basis"] = " "
        write_git_file(repo, COMPATIBILITY_PATH, json.dumps(missing_basis, indent=2, sort_keys=True) + "\n")
        missing_basis_revision = commit_fixture(repo, "delegated disposition without approval basis")
        rejected("delegated approval without basis", "compatibility-disposition",
                 lambda: verify_snapshot(repo, missing_basis_revision, base_revision, actual))

        altered_actual = json.loads(json.dumps(actual))
        altered_actual["fixtures"][0]["state_sha256"] = "0" * 64
        rejected("altered compiled pin", "pin-mismatch",
                 lambda: verify_snapshot(repo, accepted_revision, base_revision, altered_actual))

        relabelled_golden = json.loads(json.dumps(golden))
        relabelled_golden["release"]["minor"] = 3
        write_git_file(repo, GOLDEN_PATH,
                       json.dumps(relabelled_golden, indent=2, sort_keys=True) + "\n")
        relabelled_revision = commit_fixture(repo, "relabel 0.2.1 pins as 0.3.0")
        wrong_release = dict(relabelled_golden, schema="state-pin-emission-v1")
        rejected("0.3.0 relabel", "release-token-mismatch",
                 lambda: verify_snapshot(repo, relabelled_revision, base_revision, wrong_release))

        write_git_file(repo, GOLDEN_PATH, json.dumps(golden, indent=2, sort_keys=True) + "\n")
        write_git_file(repo, COMPATIBILITY_PATH,
                       json.dumps(compatibility, indent=2, sort_keys=True) + "\n")
        accepted_revision = commit_fixture(repo, "restore accepted baseline after relabel control")

        subprocess.run(["git", "-C", repo, "checkout", "-qb", "evidence-side", accepted_revision],
                       check=True)
        write_git_file(repo, "unrelated-evidence.txt", "separate evidence branch\n")
        unrelated_evidence = commit_fixture(repo, "unrelated evidence branch")
        subprocess.run(["git", "-C", repo, "checkout", "-q", "main"], check=True)
        stale_compatibility = json.loads(json.dumps(compatibility))
        stale_compatibility["dispositions"][0]["evidence"]["revision"] = unrelated_evidence
        write_git_file(repo, COMPATIBILITY_PATH,
                       json.dumps(stale_compatibility, indent=2, sort_keys=True) + "\n")
        stale_revision = commit_fixture(repo, "stale evidence disposition")
        rejected("stale continuation evidence", "disposition-evidence-stale",
                 lambda: verify_snapshot(repo, stale_revision, base_revision, actual))

        # A subsequent changed golden cannot be accepted under the same tokens once a baseline exists.
        write_git_file(repo, COMPATIBILITY_PATH, json.dumps(compatibility, indent=2, sort_keys=True) + "\n")
        accepted_revision = commit_fixture(repo, "restore accepted disposition")
        base_golden = golden
        changed_golden = json.loads(json.dumps(golden))
        changed_golden["fixtures"][0]["state_sha256"] = "4" * 64
        write_git_file(repo, GOLDEN_PATH, json.dumps(changed_golden, indent=2, sort_keys=True) + "\n")
        changed_without_disposition = commit_fixture(repo, "changed pin without token")
        changed_actual = dict(changed_golden, schema="state-pin-emission-v1")
        rejected("changed pin without disposition", "compatibility-missing",
                 lambda: verify_snapshot(repo, changed_without_disposition, accepted_revision,
                                         changed_actual))

        same_token_row = {
            "id": "bad-same-token-change", "kind": "format-change", "accepted": True,
            "approved_by": "phase-owner", "approval_basis": "explicit synthetic owner approval",
            "decision_refs": [OWNER_RULES_FILE + "#Workflow-contract"], "decision": "format changed",
            "rationale": "test control",
            "base_revision": accepted_revision, "old_golden_sha256": digest_json(base_golden),
            "new_golden_sha256": digest_json(changed_golden),
            "tokens_before": document_tokens(base_golden), "tokens_after": document_tokens(changed_golden),
            "affected_semantics": ["test bytes"], "required_token": "format_version",
            "evidence": {"revision": accepted_revision, "summary_path": EVIDENCE_REF,
                         "description": "independent continuation evidence"},
        }
        write_git_file(repo, COMPATIBILITY_PATH,
                       json.dumps({"schema": "state-compatibility-v1", "dispositions": [same_token_row]},
                                  indent=2, sort_keys=True) + "\n")
        same_token_revision = commit_fixture(repo, "same-token disposition")
        rejected("format disposition without format bump", "required-token-unchanged",
                 lambda: verify_snapshot(repo, same_token_revision, accepted_revision, changed_actual))

        # An unrelated same-baseline control passes and remains source/pin equality based.
        write_git_file(repo, GOLDEN_PATH, json.dumps(golden, indent=2, sort_keys=True) + "\n")
        no_change_revision = commit_fixture(repo, "unchanged baseline")
        result = verify_snapshot(repo, no_change_revision, no_change_revision,
                                 dict(golden, schema="state-pin-emission-v1"))
        if result["source_revision"] != no_change_revision:
            reject("self-test-failed", "unchanged pin control used a different immutable revision")
        controls += 1

        try:
            verify_snapshot(repo, base_revision, no_change_revision, actual)
        except Rejected as error:
            if error.code != "immutable-base":
                reject("self-test-failed", "non-ancestor base control had the wrong diagnostic")
        else:
            reject("self-test-failed", "non-ancestor base revision was accepted")
        controls += 1

        try:
            immutable_revision(repo, "HEAD")
        except Rejected as error:
            if error.code != "immutable-revision":
                reject("self-test-failed", "mutable revision control had the wrong diagnostic")
        else:
            reject("self-test-failed", "mutable HEAD revision was accepted")
        controls += 1

        receipt_dir = os.path.join(scratch, "receipts")
        os.makedirs(receipt_dir)
        receipt_path = os.path.join(receipt_dir, "state-pin-receipt.json")
        receipt_result = {
            "source_revision": no_change_revision,
            "base_revision": base_revision,
            "golden_sha256": digest_json(golden),
            "source_input_sha256": "a" * 64,
            "compiled_executable_sha256": "b" * 64,
            "fixture_count": len(golden["fixtures"]),
            "fixtures": golden["fixtures"],
        }
        write_receipt(receipt_path, "linux-x64", receipt_result)
        with open(receipt_path, encoding="utf-8") as handle:
            receipt = json.load(handle)
        if set(receipt) != {"schema", "platform", "source_revision", "base_revision", "golden_sha256",
                            "source_input_sha256", "compiled_executable_sha256", "fixture_count", "fixtures"} or \
                receipt["schema"] != "state-pin-receipt-v1" or receipt["fixtures"] != golden["fixtures"]:
            reject("self-test-failed", "state-pin receipt omitted a required identity or included unexpected fields")
        controls += 1
        try:
            write_receipt(receipt_path, "../private-host-path", receipt_result)
        except Rejected as error:
            if error.code != "receipt-platform":
                reject("self-test-failed", "invalid receipt platform had the wrong diagnostic")
        else:
            reject("self-test-failed", "invalid receipt platform was accepted")
        controls += 1

    print("state-pin-controls pass controls=%d" % controls)


def main(argv):
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--rev")
    parser.add_argument("--base")
    parser.add_argument("--check")
    parser.add_argument("--receipt")
    parser.add_argument("--platform")
    parser.add_argument("--planning-check", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--repo", default=ROOT)
    options = parser.parse_args(argv)
    try:
        if options.self_test:
            self_test()
            return 0
        if options.planning_check:
            if not options.rev or not options.base:
                reject("usage", "--planning-check requires immutable --rev and --base commits")
            result = planning_check(options.repo, options.rev, options.base)
            print("state-pin-planning pass revision=%s base=%s evidence=%s" %
                  (result["source_revision"], result["base_revision"], result["evidence"]))
            return 0
        if not options.rev or not options.base or not options.check:
            reject("usage", "--check requires --rev, --base, and the compiled test_state_codec executable")
        result = check_command(options.repo, options.rev, options.base, options.check)
        receipt_path = options.receipt or os.environ.get("GBB_STATE_PIN_RECEIPT")
        platform = options.platform or os.environ.get("GBB_STATE_PLATFORM")
        if receipt_path:
            if not platform:
                reject("receipt-platform", "a receipt requires --platform or GBB_STATE_PLATFORM")
            write_receipt(receipt_path, platform, result)
        print("state-pins pass revision=%s base=%s fixtures=%d golden_sha256=%s source_input_sha256=%s executable_sha256=%s" %
              (result["source_revision"], result["base_revision"], result["fixture_count"],
               result["golden_sha256"], result["source_input_sha256"],
               result["compiled_executable_sha256"]))
        return 0
    except Rejected as error:
        sys.stderr.write("REJECT %s: %s\n" % (error.code, error))
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
