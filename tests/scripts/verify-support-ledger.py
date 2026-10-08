#!/usr/bin/env python3
"""Validate the stable support ledger and bind it to an immutable Git tag."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
LEDGER = pathlib.Path("docs/support/v0.1.0.md")
BEGIN = "<!-- support-ledger-data-begin -->"
END = "<!-- support-ledger-data-end -->"
CASE_IDS = [
    "mooneye-acceptance-instr-daa",
    "mooneye-acceptance-timer-tim00",
    "mooneye-acceptance-timer-tim00-div-trigger",
]


def fail(message: str) -> None:
    raise ValueError(message)


def parse_ledger(raw: bytes) -> dict:
    try:
        source = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        fail(f"ledger is not valid UTF-8: {error}")
    if "\ufffd" in source:
        fail("ledger contains Unicode replacement character")
    if re.search(r"(?im)^\s*[\"']?source_(?:sha|revision)[\"']?\s*[:=]\s*[\"']?[0-9a-f]{40}", source):
        fail("tracked ledger must not embed a future/full source SHA")
    if BEGIN not in source or END not in source or source.count(BEGIN) != 1 or source.count(END) != 1:
        fail("ledger must contain exactly one delimited structured data block")
    block = source.split(BEGIN, 1)[1].split(END, 1)[0]
    match = re.search(r"```json\s*(.*?)\s*```", block, re.S)
    if not match:
        fail("ledger structured data block is missing fenced JSON")
    try:
        data = json.loads(match.group(1), object_pairs_hook=unique_pairs)
    except (json.JSONDecodeError, ValueError) as error:
        fail(f"invalid or duplicate-key ledger JSON: {error}")
    validate_data(data)
    return data


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            fail(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def validate_data(data: dict) -> None:
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        fail("unsupported ledger schema")
    if data.get("version") != "0.1.0" or data.get("boot") != "skipped":
        fail("ledger version/profile identity is missing or unstable")
    if data.get("model") != "bootless DMG-CPU-B deterministic software profile":
        fail("ledger must name the scoped bootless DMG-CPU-B model")
    if data.get("broad_game_claim") is not False or data.get("physical_dmg_observations") != 0:
        fail("ledger contains a broad-game or unsupported physical-hardware claim")
    cases = data.get("executed_cases")
    ids = [case.get("id") for case in cases] if isinstance(cases, list) else []
    if ids != CASE_IDS or len(set(ids)) != len(ids):
        fail("eligible cases are missing, duplicated, or not in stable manifest order")
    if data.get("eligible_denominator") != len(CASE_IDS) or data.get("executed_denominator") != len(CASE_IDS):
        fail("ledger denominator does not equal the fixed executed corpus")
    if any(case.get("status") != "pass" for case in cases):
        fail("case outcomes must be explicit and nonempty")
    if data.get("failures") != []:
        fail("current failures must be represented explicitly (empty list means none)")
    if not data.get("known_issues") or len(set(data["known_issues"])) != len(data["known_issues"]):
        fail("known issues are missing or duplicated")
    if not data.get("fixture_classes") or len(set(data["fixture_classes"])) != len(data["fixture_classes"]):
        fail("fixture classes are missing or duplicated")
    if not re.fullmatch(r"[0-9a-f]{40}", data.get("corpus_revision", "")):
        fail("exact corpus revision is missing or malformed")
    exclusions = data.get("excluded_cartridges")
    limitations = data.get("limitations")
    evidence = data.get("evidence_classes")
    if not exclusions or len(set(exclusions)) != len(exclusions):
        fail("missing or duplicate exclusions")
    if not limitations or len(set(limitations)) != len(limitations):
        fail("missing or duplicate limitations")
    if not evidence or len(set(evidence)) != len(evidence):
        fail("missing or duplicate evidence classes")
    if not any("physical DMG" in item for item in limitations):
        fail("physical-hardware limitation is missing")
    if any(re.search(r"\b(all|every|most)\s+games?\b|compatible with games", item, re.I)
           for item in limitations):
        fail("broad game compatibility wording detected")
    paths = data.get("manifest_paths")
    digests = data.get("manifest_sha256")
    if not isinstance(paths, list) or len(paths) != 4 or len(set(paths)) != len(paths):
        fail("fixture/corpus manifest identities are missing or duplicated")
    if not isinstance(digests, dict) or set(digests) != set(paths):
        fail("manifest digest map does not match the listed manifests")
    for path, value in digests.items():
        if not re.fullmatch(r"[0-9a-f]{64}", value):
            fail(f"malformed SHA-256 for {path}")


def manifest_identity(raw: bytes, path: str) -> dict:
    try:
        manifest = json.loads(raw.decode("utf-8", errors="strict"), object_pairs_hook=unique_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        fail(f"invalid tagged manifest {path}: {error}")
    return {"path": path, "sha256": hashlib.sha256(raw).hexdigest(),
            "id": manifest.get("id", manifest.get("suite", {}).get("name"))}


def validate_manifest_set(data: dict, manifests: dict[str, bytes]) -> list[dict]:
    identities = []
    for path in data["manifest_paths"]:
        if path not in manifests:
            fail(f"missing fixture/corpus manifest: {path}")
        identity = manifest_identity(manifests[path], path)
        if identity["sha256"] != data["manifest_sha256"][path]:
            fail(f"fixture/corpus manifest digest mismatch: {path}")
        identities.append(identity)
    corpus = json.loads(manifests["fixtures/mooneye/manifest.json"].decode("utf-8"))
    eligible = [fixture["id"] for fixture in corpus.get("fixtures", []) if fixture.get("eligible") is True]
    if eligible != CASE_IDS:
        fail("eligible corpus order or denominator differs from the pinned manifest")
    if corpus.get("suite", {}).get("revision") != data["corpus_revision"]:
        fail("corpus revision differs from the pinned manifest")
    return identities


def git(*args: str, cwd: pathlib.Path = ROOT) -> bytes:
    try:
        return subprocess.check_output(["git", *args], cwd=cwd, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as error:
        fail(f"git {' '.join(args)} failed: {error.stderr.decode(errors='replace').strip()}")


def build_sidecar(tag: str, source_sha: str, repo_root: pathlib.Path = ROOT) -> dict:
    if not re.fullmatch(r"v0\.1\.0", tag):
        fail("tag must match this versioned ledger")
    if not re.fullmatch(r"[0-9a-f]{40}", source_sha):
        fail("source SHA must be a full lowercase Git commit SHA")
    actual_sha = git("rev-parse", f"{tag}^{{commit}}", cwd=repo_root).decode().strip()
    if actual_sha != source_sha:
        fail("supplied source SHA does not resolve from the requested tag")
    ledger_raw = git("show", f"{tag}:{LEDGER.as_posix()}", cwd=repo_root)
    data = parse_ledger(ledger_raw)
    manifests = {path: git("show", f"{tag}:{path}", cwd=repo_root) for path in data["manifest_paths"]}
    identities = validate_manifest_set(data, manifests)
    blob_oid = git("rev-parse", f"{tag}:{LEDGER.as_posix()}", cwd=repo_root).decode().strip()
    return {
        "schema_version": 1,
        "version": data["version"],
        "tag": tag,
        "source_sha": source_sha,
        "ledger": {"path": LEDGER.as_posix(), "git_blob_oid": blob_oid,
                   "sha256": hashlib.sha256(ledger_raw).hexdigest()},
        "fixture_manifest_identities": identities,
        "corpus_revision": data["corpus_revision"],
        "eligible_denominator": data["eligible_denominator"],
        "executed_denominator": data["executed_denominator"],
        "executed_cases": data["executed_cases"],
        "failures": data["failures"],
        "known_issues": data["known_issues"],
        "fixture_classes": data["fixture_classes"],
        "limitations": data["limitations"],
        "physical_dmg_observations": data["physical_dmg_observations"],
        "broad_game_claim": False,
        "self_hash": None,
    }


def verify_sidecar_data(observed: dict, expected: dict) -> None:
    if not isinstance(observed, dict) or observed != expected:
        fail("sidecar source SHA, tagged ledger blob, or fixture/corpus identity differs from the tag")


def self_test() -> None:
    raw = (ROOT / LEDGER).read_bytes()
    data = parse_ledger(raw)
    manifests = {path: (ROOT / path).read_bytes() for path in data["manifest_paths"]}
    validate_manifest_set(data, manifests)
    mutations = [
        raw + b"\nsource_sha: 0123456789012345678901234567890123456789\n",
        raw.replace(b'"executed_denominator": 3', b'"executed_denominator": 2'),
        raw.replace(b'"broad_game_claim": false', b'"broad_game_claim": true'),
        raw.replace(b'"status": "pass"', b'"status": "pass", "status": "fail"', 1),
        raw.replace(b'mooneye-acceptance-timer-tim00-div-trigger', b'mooneye-acceptance-timer-tim00'),
        raw.replace(b'"corpus_revision": "31510e12eea6286d36eea060a6adde755e1067aa"',
                    b'"corpus_revision": "21510e12eea6286d36eea060a6adde755e1067aa"'),
        raw.replace(b'"fixtures/tracer/manifest.json": "5928', b'"fixtures/tracer/manifest.json": "0928'),
        raw + b"\xff",
    ]
    for changed in mutations:
        try:
            altered = parse_ledger(changed)
            validate_manifest_set(altered, manifests)
        except (ValueError, KeyError):
            continue
        fail("self-test mutation was accepted")
    try:
        mismatched = dict(manifests)
        mismatched["fixtures/tracer/manifest.json"] += b"tamper"
        validate_manifest_set(data, mismatched)
    except (ValueError, KeyError):
        pass
    else:
        fail("self-test accepted altered tagged manifest bytes")
    fixture_sidecar = {"tag": "v0.1.0", "source_sha": "a" * 40,
                       "ledger_sha256": hashlib.sha256(raw).hexdigest(),
                       "manifest_sha256": data["manifest_sha256"]}
    for key, value in (("source_sha", "b" * 40), ("ledger_sha256", "0" * 64),
                       ("manifest_sha256", {"fixtures/tracer/manifest.json": "0" * 64})):
        altered = dict(fixture_sidecar)
        altered[key] = value
        try:
            verify_sidecar_data(altered, fixture_sidecar)
        except ValueError:
            continue
        fail("self-test accepted altered sidecar identity")
    with tempfile.TemporaryDirectory(prefix="gabbaboy-support-ledger-") as temporary:
        repository = pathlib.Path(temporary)
        for relative in [LEDGER.as_posix(), *data["manifest_paths"]]:
            destination = repository / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, destination)
        environment = dict(os.environ)
        environment.update({"GIT_AUTHOR_NAME": "GabbaBoy Test", "GIT_AUTHOR_EMAIL": "test@example.invalid",
                            "GIT_COMMITTER_NAME": "GabbaBoy Test", "GIT_COMMITTER_EMAIL": "test@example.invalid"})
        subprocess.run(["git", "init", "-q"], cwd=repository, env=environment, check=True)
        subprocess.run(["git", "add", LEDGER.as_posix(), *data["manifest_paths"]],
                       cwd=repository, env=environment, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "fixture"], cwd=repository,
                       env=environment, check=True)
        fake_sha = git("rev-parse", "HEAD", cwd=repository).decode().strip()
        subprocess.run(["git", "tag", "v0.1.0", fake_sha], cwd=repository, env=environment, check=True)
        generated = build_sidecar("v0.1.0", fake_sha, repository)
        if generated["source_sha"] != fake_sha or generated["ledger"]["sha256"] != hashlib.sha256(raw).hexdigest():
            fail("self-test generated sidecar does not bind exact source and ledger bytes")
        for key in ("source_sha", "ledger", "fixture_manifest_identities"):
            altered = dict(generated)
            altered[key] = None
            try:
                verify_sidecar_data(altered, generated)
            except ValueError:
                continue
            fail(f"self-test accepted altered sidecar {key}")
    print("support ledger self-test passed: tagged sidecar binding, scope, corpus order, digests, malformed UTF-8, duplicate keys, denominator and claim controls")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--tag")
    parser.add_argument("--source-sha")
    parser.add_argument("--output", type=pathlib.Path)
    parser.add_argument("--verify-sidecar", type=pathlib.Path)
    args = parser.parse_args()
    try:
        if args.self_test:
            self_test()
            return 0
        if not (args.tag and args.source_sha and (args.output or args.verify_sidecar)):
            parser.error("supply --tag, --source-sha and --output or --verify-sidecar, or use --self-test")
        sidecar = build_sidecar(args.tag, args.source_sha)
        if args.verify_sidecar:
            observed = json.loads(args.verify_sidecar.read_text(encoding="utf-8"))
            verify_sidecar_data(observed, sidecar)
            print(f"verified source-bound support sidecar for {args.tag} ({args.source_sha})")
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(sidecar, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print(f"wrote source-bound support sidecar for {args.tag} ({args.source_sha})")
    except (ValueError, KeyError, OSError) as error:
        print(f"support-ledger verification failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
