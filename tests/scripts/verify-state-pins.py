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
EVIDENCE_PATH = ".planning/phases/GB-17-native-save-state-core/17-05-SUMMARY.md"
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
    if not version or not format_match or not behavior_match:
        reject("state-token-source", "release, format or behavior tokens are not explicit in source")
    tokens = {
        "release": {"major": int(version.group(1)), "minor": int(version.group(2)),
                    "patch": int(version.group(3))},
        "format_version": int(format_match.group(1)),
        "behavior_version": int(behavior_match.group(1)),
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


def verify_evidence(repo, base_revision, evidence):
    if not isinstance(evidence, dict) or set(evidence) != {"revision", "summary_path", "description"}:
        reject("disposition-evidence", "continuation evidence must identify a revision, summary and description")
    evidence_revision = immutable_revision(repo, evidence["revision"])
    if evidence["summary_path"] != EVIDENCE_PATH or not isinstance(evidence["description"], str) or \
            not evidence["description"].strip():
        reject("disposition-evidence", "continuation evidence must cite the completed snapshot-fork summary")
    ancestor = subprocess.run(["git", "-C", repo, "merge-base", "--is-ancestor",
                               evidence_revision, base_revision], capture_output=True)
    if ancestor.returncode != 0:
        reject("disposition-evidence-stale", "continuation evidence is not present at the immutable base")
    summary = source_file(repo, evidence_revision, EVIDENCE_PATH)
    required_claims = ("status: complete", "198 serialized fields", "14 in-flight categories")
    if any(claim not in summary for claim in required_claims):
        reject("disposition-evidence", "snapshot-fork summary lacks complete field/category evidence")


def validate_compatibility(repo, base_revision, current_revision, base_golden,
                           current_golden, base_tokens, current_tokens, compatibility):
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
    required = {"id", "kind", "accepted", "approved_by", "decision", "rationale",
                "base_revision", "old_golden_sha256", "new_golden_sha256", "tokens_before",
                "tokens_after", "affected_semantics", "evidence"}
    if row.get("kind") == "pre-first-state-release-evolution":
        required |= {"base_state_release_exists"}
    else:
        required |= {"required_token"}
    if set(row) != required or row.get("accepted") is not True or \
            row.get("approved_by") != "phase-owner" or not row.get("id") or \
            not isinstance(row.get("decision"), str) or not row["decision"].strip() or \
            not isinstance(row.get("rationale"), str) or not row["rationale"].strip() or \
            not isinstance(row.get("affected_semantics"), list) or not row["affected_semantics"]:
        reject("compatibility-disposition", "disposition is incomplete or has no explicit phase-owner acceptance")
    verify_evidence(repo, base_revision, row["evidence"])

    if row["kind"] == "pre-first-state-release-evolution":
        if row["base_state_release_exists"] is not False or old_sha is not None or \
                base_tokens != current_tokens:
            reject("compatibility-pre-release", "unchanged tokens are allowed only for the first explicit pre-release baseline")
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


def verify_snapshot(repo, source_revision, base_revision, actual):
    source_revision = immutable_revision(repo, source_revision)
    base_revision = immutable_revision(repo, base_revision)
    current_golden_text = source_file(repo, source_revision, GOLDEN_PATH)
    current_golden = validate_pin_document(parse_json_text(current_golden_text, "state-goldens"), "current pins")
    current_tokens = state_tokens(repo, source_revision)
    if document_tokens(current_golden) != current_tokens:
        reject("release-token-mismatch", "golden release/format/behavior tokens differ from immutable source")
    if actual != {"schema": "state-pin-emission-v1", **current_golden}:
        reject("pin-mismatch", "compiled canonical state bytes differ from the immutable fixture pins")

    base_golden_text = source_file(repo, base_revision, GOLDEN_PATH, allow_missing=True)
    base_golden = None
    if base_golden_text is not None:
        base_golden = validate_pin_document(parse_json_text(base_golden_text, "base state-goldens"), "base pins")
    base_tokens = state_tokens(repo, base_revision)
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
                           current_golden, base_tokens, current_tokens, compatibility)
    return {"source_revision": source_revision, "base_revision": base_revision,
            "golden_sha256": digest_json(current_golden), "base_golden_sha256": digest_json(base_golden)
            if base_golden is not None else None}


def source_input_digest(repo, revision):
    inputs = {path: digest_bytes(source_file(repo, revision, path).encode("utf-8"))
              for path in SOURCE_INPUTS}
    return digest_json(inputs)


def check_command(repo, source_revision, base_revision, executable):
    actual = run_emitter(executable)
    result = verify_snapshot(repo, source_revision, base_revision, actual)
    return {**result, "source_input_sha256": source_input_digest(repo, source_revision),
            "compiled_executable_sha256": digest_bytes(open(executable, "rb").read()),
            "fixture_count": len(actual["fixtures"])}


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


def initial_disposition(base_revision, golden, evidence_revision):
    return {
        "id": "initial-state-pin-baseline",
        "kind": "pre-first-state-release-evolution",
        "accepted": True,
        "approved_by": "phase-owner",
        "decision": "D-02 explicitly permits documented byte evolution before the first state release",
        "rationale": "These 0.2.1 pins establish the initial portable baseline; they do not imply compatibility among arbitrary unreleased builds or infer semantic equivalence.",
        "base_revision": base_revision,
        "old_golden_sha256": None,
        "new_golden_sha256": digest_json(golden),
        "tokens_before": {"release": {"major": 0, "minor": 2, "patch": 1},
                           "format_version": 1, "behavior_version": 1},
        "tokens_after": {"release": {"major": 0, "minor": 2, "patch": 1},
                          "format_version": 1, "behavior_version": 1},
        "affected_semantics": ["canonical serialized bytes for DMG, CGB compatibility, and native CGB fixtures"],
        "base_state_release_exists": False,
        "evidence": {"revision": evidence_revision, "summary_path": EVIDENCE_PATH,
                     "description": "Independent snapshot continuation covers 153 corpus cases, 198 fields, and 14 applicable in-flight categories."},
    }


def self_test():
    controls = 0
    with tempfile.TemporaryDirectory(prefix="state-pins-selftest-") as scratch:
        repo = os.path.join(scratch, "repo")
        os.makedirs(repo)
        subprocess.run(["git", "-C", repo, "init", "-q", "-b", "main"], check=True)
        write_git_file(repo, "CMakeLists.txt", "project(GabbaBoy VERSION 0.2.1 LANGUAGES C)\n")
        write_git_file(repo, "src/core/gabbaboy.c",
                       "#define GBB_STATE_FORMAT_VERSION 1u\n#define GBB_STATE_BEHAVIOR_VERSION 1u\n")
        summary = "---\nstatus: complete\n---\nSnapshot forks cover 198 serialized fields and 14 in-flight categories.\n"
        write_git_file(repo, EVIDENCE_PATH, summary)
        base_revision = commit_fixture(repo, "synthetic base")
        golden = fixture_pin_document()
        write_git_file(repo, GOLDEN_PATH, json.dumps(golden, indent=2, sort_keys=True) + "\n")
        no_disposition_revision = commit_fixture(repo, "pins without disposition")
        actual = {"schema": "state-pin-emission-v1", **golden}

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

        compatibility = {"schema": "state-compatibility-v1", "dispositions": [
            initial_disposition(base_revision, golden, base_revision)]}
        write_git_file(repo, COMPATIBILITY_PATH, json.dumps(compatibility, indent=2, sort_keys=True) + "\n")
        accepted_revision = commit_fixture(repo, "explicit pre-release disposition")
        verified = verify_snapshot(repo, accepted_revision, base_revision, actual)
        if verified["golden_sha256"] != digest_json(golden):
            reject("self-test-failed", "explicit pre-release disposition lost its pin digest")
        controls += 1

        altered_actual = json.loads(json.dumps(actual))
        altered_actual["fixtures"][0]["state_sha256"] = "0" * 64
        rejected("altered compiled pin", "pin-mismatch",
                 lambda: verify_snapshot(repo, accepted_revision, base_revision, altered_actual))

        wrong_release = json.loads(json.dumps(actual))
        wrong_release["release"]["minor"] = 3
        rejected("0.3.0 relabel", "pin-mismatch",
                 lambda: verify_snapshot(repo, accepted_revision, base_revision, wrong_release))

        stale_compatibility = json.loads(json.dumps(compatibility))
        stale_compatibility["dispositions"][0]["evidence"]["revision"] = accepted_revision
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
        changed_actual = {"schema": "state-pin-emission-v1", **changed_golden}
        rejected("changed pin without disposition", "compatibility-missing",
                 lambda: verify_snapshot(repo, changed_without_disposition, accepted_revision,
                                         changed_actual))

        same_token_row = {
            "id": "bad-same-token-change", "kind": "format-change", "accepted": True,
            "approved_by": "phase-owner", "decision": "format changed", "rationale": "test control",
            "base_revision": accepted_revision, "old_golden_sha256": digest_json(base_golden),
            "new_golden_sha256": digest_json(changed_golden),
            "tokens_before": document_tokens(base_golden), "tokens_after": document_tokens(changed_golden),
            "affected_semantics": ["test bytes"], "required_token": "format_version",
            "evidence": {"revision": accepted_revision, "summary_path": EVIDENCE_PATH,
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
                                 {"schema": "state-pin-emission-v1", **golden})
        if result["source_revision"] != no_change_revision:
            reject("self-test-failed", "unchanged pin control used a different immutable revision")
        controls += 1

        try:
            immutable_revision(repo, "HEAD")
        except Rejected as error:
            if error.code != "immutable-revision":
                reject("self-test-failed", "mutable revision control had the wrong diagnostic")
        else:
            reject("self-test-failed", "mutable HEAD revision was accepted")
        controls += 1

    print("state-pin-controls pass controls=%d" % controls)


def main(argv):
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--rev")
    parser.add_argument("--base")
    parser.add_argument("--check")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--repo", default=ROOT)
    options = parser.parse_args(argv)
    try:
        if options.self_test:
            self_test()
            return 0
        if not options.rev or not options.base or not options.check:
            reject("usage", "--check requires --rev, --base, and the compiled test_state_codec executable")
        result = check_command(options.repo, options.rev, options.base, options.check)
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
