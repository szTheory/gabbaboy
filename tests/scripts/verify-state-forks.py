#!/usr/bin/env python3
"""Run and check immutable-revision native save-state fork evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = "tests/data/state-forks.json"
ROM_SUFFIXES = (".gb", ".gbc")
REVISION = re.compile(r"^[0-9a-f]{40}$")


class ForkError(Exception):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob(rev: str, path: str, repo: Path) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{rev}:{path}"], cwd=repo,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if result.returncode:
        raise ForkError(f"immutable revision {rev} has no readable {path}: {result.stderr.decode(errors='replace').strip()}")
    return result.stdout


def checked_rev(value: str, repo: Path) -> str:
    if not REVISION.fullmatch(value):
        raise ForkError("--rev must be a resolved immutable 40-character lowercase commit")
    result = subprocess.run(["git", "cat-file", "-e", f"{value}^{{commit}}"], cwd=repo,
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=False)
    if result.returncode:
        raise ForkError(f"--rev is not an available commit: {value}")
    return value


def load_spec(rev: str, repo: Path) -> tuple[dict, bytes]:
    raw = git_blob(rev, SPEC_PATH, repo)
    try:
        spec = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ForkError(f"invalid immutable {SPEC_PATH}: {exc}") from exc
    if spec.get("schema") != "gabbaboy-state-forks-v1":
        raise ForkError("unknown state-forks specification schema")
    if spec.get("corpus_union", {}).get("oracle_replay_claim") is not False:
        raise ForkError("fork evidence must remain labelled snapshot-equivalence, not oracle replay")
    return spec, raw


def manifest_cases(rev: str, repo: Path, spec: dict, verify_blobs: bool) -> list[dict]:
    cases: list[dict] = []
    ids: set[str] = set()
    listed_manifests = {item["path"] for item in spec.get("fixture_manifests", [])}
    tree = subprocess.run(["git", "ls-tree", "-r", "--name-only", rev, "--", "fixtures"],
                          cwd=repo, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          text=True, check=False)
    if tree.returncode:
        raise ForkError(f"cannot enumerate immutable fixture tree: {tree.stderr.strip()}")
    actual_manifests = {line for line in tree.stdout.splitlines() if line.endswith("/manifest.json")}
    if actual_manifests != listed_manifests:
        raise ForkError(f"fixture manifest union differs from immutable tree: missing={sorted(actual_manifests-listed_manifests)} extra={sorted(listed_manifests-actual_manifests)}")
    catalogs: dict[str, dict] = {}
    for item in spec.get("disposition_catalogs", []):
        raw = git_blob(rev, item["path"], repo)
        if digest(raw) != item.get("sha256"):
            raise ForkError(f"disposition catalog digest changed at {item['path']}")
        try:
            catalogs[item["path"]] = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ForkError(f"invalid disposition catalog {item['path']}: {exc}") from exc
    cgb_catalog_path = "tests/external/cgb-corpus-inventory.json"
    cgb_catalog = catalogs.get(cgb_catalog_path)
    cgb_rows = {row.get("id"): row for row in cgb_catalog.get("cases", [])} if cgb_catalog else {}
    if cgb_catalog is None or len(cgb_rows) != 107:
        raise ForkError("CGB corpus disposition inventory must retain all 107 rows")
    dispositions = {}
    for row in cgb_rows.values():
        status = row.get("evaluator_disposition", {}).get("state")
        if status == "expected-failure": dispositions["expected_failure"] = dispositions.get("expected_failure", 0) + 1
        elif status == "pass": dispositions["pass"] = dispositions.get("pass", 0) + 1
        elif status in {"prior-observation", "prior-phase-observation"}:
            dispositions["prior_observation"] = dispositions.get("prior_observation", 0) + 1
        else:
            raise ForkError(f"unknown CGB corpus disposition for {row.get('id')}: {status}")
    if dispositions != {"expected_failure": 82, "pass": 16, "prior_observation": 9}:
        raise ForkError(f"CGB corpus expected outcome classes changed: {dispositions}")
    for item in spec.get("fixture_manifests", []):
        path = item["path"]
        raw = git_blob(rev, path, repo)
        if digest(raw) != item.get("sha256"):
            raise ForkError(f"fixture manifest digest changed at {path}")
        try:
            manifest = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ForkError(f"invalid fixture manifest {path}: {exc}") from exc
        rows = manifest.get("fixtures", [])
        before = len(cases)
        for row in rows:
            filename = row.get("file") or row.get("rom")
            if isinstance(filename, dict):
                filename = filename.get("path")
            if not isinstance(filename, str) or not filename.lower().endswith(ROM_SUFFIXES):
                continue
            rom_path = filename if filename.startswith("fixtures/") else str(Path(path).parent / filename)
            case = make_case(path, row, rom_path)
            add_case(case, cases, ids)
        root_rom = manifest.get("rom")
        if isinstance(root_rom, dict):
            filename = root_rom.get("path")
            rom_sha = root_rom.get("sha256")
            rom_size = root_rom.get("size_bytes")
            row = {"id": Path(path).parent.name, "file": filename,
                   "sha256": rom_sha, "size_bytes": rom_size}
        else:
            filename = root_rom
            row = {"id": Path(path).parent.name, "file": filename,
                   "sha256": manifest.get("sha256"),
                   "size_bytes": manifest.get("size_bytes")}
        if isinstance(filename, str) and filename.lower().endswith(ROM_SUFFIXES):
            rom_path = filename if filename.startswith("fixtures/") else str(Path(path).parent / filename)
            add_case(make_case(path, row or {"id": Path(path).parent.name, "file": filename}, rom_path),
                     cases, ids)
        count = len(cases) - before
        if count != item.get("rom_rows"):
            raise ForkError(f"{path}: spec says {item.get('rom_rows')} ROM rows, immutable manifest contains {count}")
        if verify_blobs:
            for case in cases[before:]:
                verify_rom(rev, repo, case)

    for item in spec.get("acceptance_lists", []):
        raw = git_blob(rev, item["path"], repo)
        if digest(raw) != item.get("sha256"):
            raise ForkError(f"acceptance list digest changed at {item['path']}")
        rows = [line.strip() for line in raw.decode("utf-8").splitlines()
                if line.strip() and not line.lstrip().startswith("#")]
        if len(rows) != item.get("case_rows"):
            raise ForkError(f"{item['path']}: acceptance row count differs from the pinned inventory")
        before = len(cases)
        for line in rows:
            values = dict(part.split("=", 1) for part in line.split() if "=" in part)
            case_id = values.get("id")
            rom_path = values.get("rom")
            if not case_id or not rom_path:
                raise ForkError(f"unparseable acceptance row in {item['path']}: {line}")
            case = {
                "id": f"accept:{case_id}", "source": item["path"], "rom": rom_path,
                "sha256": values.get("rom_sha256"), "size_bytes": int(values.get("rom_size", "0")),
                "profile": "cgb" if "cgb-cpu-e" in values.get("model_pass", "") else "dmg",
                "oracle_disposition": {key: value for key, value in values.items()
                                       if key not in {"id", "rom", "rom_sha256", "rom_size", "input_script", "input_sha256"}},
            }
            add_case(case, cases, ids)
        if len(cases) - before != item.get("case_rows"):
            raise ForkError(f"{item['path']}: acceptance row count differs from the pinned inventory")
        if verify_blobs:
            for case in cases[before:]:
                verify_rom(rev, repo, case)

    by_digest = {}
    for case in cases:
        by_digest.setdefault(case["sha256"], []).append(case)
    missing_cgb = []
    for case_id, disposition in cgb_rows.items():
        identity = str(disposition.get("qualified_identity", disposition.get("case_identity", "")))
        matches = re.findall(r"#([0-9a-f]{64})", identity)
        fixture_digest = matches[-1] if matches else None
        matching_cases = by_digest.get(fixture_digest, [])
        if not matching_cases:
            output_id = str(disposition.get("output_id", ""))
            output_tail = output_id.rsplit(":", 1)[-1]
            suite = disposition.get("suite")
            if suite == "samesuite":
                source_id = str(disposition.get("source_id", ""))
                source_stem = Path(source_id).stem
                matching_cases = [case for case in cases
                                  if case["source"] == "fixtures/samesuite/manifest.json"
                                  and Path(case["rom"]).stem == source_stem]
            else:
                matching_cases = [case for case in cases
                                  if (suite == "magentests" and case["source"] == "fixtures/magentests/manifest.json"
                                      or suite == "mooneye" and case["source"] == "fixtures/mooneye-cgb/manifest.json")
                                  and Path(case["rom"]).stem.lower() == output_tail.lower()]
        if not matching_cases:
            missing_cgb.append(case_id)
            continue
        eligible_case = next((case for case in matching_cases if case["profile"] == "cgb"), None)
        if eligible_case is None:
            missing_cgb.append(case_id)
            continue
        eligible_case.setdefault("cgb_corpus_dispositions", []).append({
            "id": case_id,
            "evaluator_disposition": disposition.get("evaluator_disposition"),
            "execution": disposition.get("execution"),
            "author_expectation": disposition.get("author_expectation"),
            "qualified_identity": disposition.get("qualified_identity"),
        })
    if missing_cgb:
        raise ForkError(f"CGB disposition catalog rows have no matching CGB ROM digest in the fixture union: {missing_cgb[:8]}")
    acid_exclusions = [item for item in spec.get("excluded", []) if item.get("path") == "tests/acid2/manifest.json"]
    if len(acid_exclusions) != 1 or "rights-gated" not in acid_exclusions[0].get("reason", ""):
        raise ForkError("optional Acid2 rights/bytes exclusion must stay explicit")
    if len(cases) != spec.get("expected_case_count"):
        raise ForkError(f"corpus union has {len(cases)} rows, expected {spec.get('expected_case_count')}")
    return cases


def make_case(manifest_path: str, row: dict, rom_path: str) -> dict:
    filename = row.get("file") or row.get("rom")
    if isinstance(filename, dict):
        filename = filename.get("path")
    case_key = row.get("id") or row.get("alias") or Path(filename).stem
    profile = profile_for(manifest_path, row, filename)
    disposition_keys = ("expect", "expected", "expected_role", "expected_disposition",
                        "observed_disposition", "evaluator_status", "author_expectation",
                        "note", "evidence_class", "model", "model_pass", "model_fail", "mode")
    return {
        "id": f"{Path(manifest_path).parent.name}:{case_key}",
        "source": manifest_path,
        "rom": rom_path,
        "sha256": row.get("sha256"),
        "size_bytes": row.get("size_bytes"),
        "profile": profile,
        "oracle_disposition": {key: row[key] for key in disposition_keys if key in row},
    }


def profile_for(manifest_path: str, row: dict, filename: str) -> str:
    model = str(row.get("model", "")).lower()
    model_pass = row.get("model_pass", [])
    if isinstance(model_pass, list):
        model_pass = " ".join(model_pass)
    if "dmg" in model or "dmg-cpu-b" in str(model_pass).lower():
        return "dmg"
    if "cgb" in model or "cgb-cpu-e" in str(model_pass).lower():
        return "cgb"
    name = Path(filename).name.lower()
    if "banking-dmg" in name or manifest_path.startswith("fixtures/mooneye/") or manifest_path.startswith("fixtures/mooneye-mbc/"):
        return "dmg"
    if manifest_path.startswith(("fixtures/age/", "fixtures/cgb-", "fixtures/magentests/",
                                 "fixtures/samesuite/", "fixtures/mooneye-cgb/")):
        return "cgb"
    return "dmg"


def add_case(case: dict, cases: list[dict], ids: set[str]) -> None:
    if not case.get("sha256") or not case.get("rom"):
        raise ForkError(f"case has no digest/ROM path: {case.get('id')}")
    if case["id"] in ids:
        raise ForkError(f"duplicate fork case id: {case['id']}")
    ids.add(case["id"])
    cases.append(case)


def verify_rom(rev: str, repo: Path, case: dict) -> None:
    raw = git_blob(rev, case["rom"], repo)
    if digest(raw) != case["sha256"]:
        raise ForkError(f"immutable ROM digest mismatch: {case['id']} ({case['rom']})")
    if case.get("size_bytes") is not None and len(raw) != int(case["size_bytes"]):
        raise ForkError(f"immutable ROM size mismatch: {case['id']} ({case['rom']})")
    live = repo / case["rom"]
    if not live.is_file() or digest(live.read_bytes()) != case["sha256"]:
        raise ForkError(f"working fixture missing/stale relative to immutable input: {case['id']}")


def parse_runner_output(output: str) -> tuple[list[dict], list[dict], list[dict], list[dict], list[dict], list[dict]]:
    fields: list[dict] = []
    categories: list[dict] = []
    constants: list[dict] = []
    seed_boundaries: list[dict] = []
    public_state_seeds: list[dict] = []
    boundary_predicates: list[dict] = []
    for line in output.splitlines():
        if line.startswith("field-witness "):
            parts = dict(part.split("=", 1) for part in line.split()[1:] if "=" in part)
            if parts.get("discriminator") != "nondefault" or parts.get("treatment") != "serialize":
                raise ForkError(f"malformed/non-discriminating field witness: {line}")
            fields.append(parts)
        elif line.startswith("category-witness "):
            categories.append(dict(part.split("=", 1) for part in line.split()[1:] if "=" in part))
        elif line.startswith("constant-witness "):
            constants.append(dict(part.split("=", 1) for part in line.split()[1:] if "=" in part))
        elif line.startswith("seed-boundary "):
            seed_boundaries.append(dict(part.split("=", 1) for part in line.split()[1:] if "=" in part))
        elif line.startswith("public-state-seed "):
            public_state_seeds.append(dict(part.split("=", 1) for part in line.split()[1:] if "=" in part))
        elif line.startswith("boundary-predicate "):
            boundary_predicates.append(dict(part.split("=", 1) for part in line.split()[1:] if "=" in part))
    return fields, categories, constants, seed_boundaries, public_state_seeds, boundary_predicates


def run_shard(args: argparse.Namespace) -> None:
    rev = checked_rev(args.rev, args.repo)
    spec, spec_raw = load_spec(rev, args.repo)
    cases = manifest_cases(rev, args.repo, spec, verify_blobs=False)
    if args.shards < 1 or args.shard < 0 or args.shard >= args.shards:
        raise ForkError("invalid matrix shard coordinates")
    selected = [(index, case) for index, case in enumerate(cases) if index % args.shards == args.shard]
    if not selected:
        raise ForkError(f"matrix shard {args.shard} is unexpectedly empty")
    results = []
    for index, case in selected:
        verify_rom(rev, args.repo, case)
        command = [str(args.test_exe), "case", case["id"], str(args.repo / case["rom"]), case["profile"]]
        proc = subprocess.run(command, cwd=args.repo, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, text=True, check=False)
        fields, categories, constants, _, _, _ = parse_runner_output(proc.stdout)
        if proc.returncode != 0:
            raise ForkError(f"fork case failed id={case['id']} exit={proc.returncode}\n{proc.stdout[-12000:]}")
        results.append({"index": index, **case, "field_witnesses": fields,
                        "category_witnesses": categories,
                        "constant_witnesses": constants,
                        "stdout_sha256": hashlib.sha256(proc.stdout.encode()).hexdigest()})
    generated_results = []
    generated_jobs = [(fixture, profile)
                      for fixture in spec.get("generated_field_fixtures", [])
                      for profile in fixture.get("profiles", [])]
    for generated_index, (fixture, profile) in enumerate(generated_jobs):
        if generated_index % args.shards != args.shard:
            continue
        prefix_budget = fixture.get("prefix_budgets", {}).get(profile)
        if not isinstance(prefix_budget, int) or prefix_budget <= 0:
            raise ForkError(f"generated fixture lacks a positive profile prefix budget: {fixture.get('id')} {profile}")
        proc = subprocess.run([str(args.test_exe), "generated_fields", fixture["id"], profile,
                               "--budget", str(prefix_budget)],
                              cwd=args.repo, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, text=True, check=False)
        if proc.returncode != 0:
            raise ForkError(f"generated field fork failed id={fixture.get('id')} profile={profile} exit={proc.returncode}\n{proc.stdout[-12000:]}")
        header = next((line for line in proc.stdout.splitlines()
                       if line.startswith("generated-rom ")), None)
        if header is None:
            raise ForkError(f"generated field fork omitted ROM identity: {fixture.get('id')} {profile}")
        identity = dict(part.split("=", 1) for part in header.split()[1:] if "=" in part)
        if (identity.get("id") != fixture.get("id") or identity.get("profile") != profile or
            identity.get("sha256") != fixture.get("sha256") or
            int(identity.get("size", "0")) != fixture.get("size_bytes")):
            raise ForkError(f"generated field fixture identity differs from immutable spec: {header}")
        fields, categories, constants, seeds, public_seeds, boundary_predicates = parse_runner_output(proc.stdout)
        generated_results.append({
            "id": f"generated:{fixture['id']}:{profile}",
            "fixture_id": fixture["id"], "source": fixture["source"],
            "sha256": fixture["sha256"], "size_bytes": fixture["size_bytes"],
            "profile": profile, "prefix_budget": prefix_budget,
            "boundary_origin": fixture.get("boundary_origin"),
            "boundary_predicate": fixture.get("boundary_predicate"),
            "seed_boundaries": seeds, "public_state_seeds": public_seeds,
            "boundary_predicates": boundary_predicates,
            "field_witnesses": fields,
            "category_witnesses": categories, "constant_witnesses": constants,
            "stdout_sha256": hashlib.sha256(proc.stdout.encode()).hexdigest(),
        })
    report = {
        "schema": "gabbaboy-state-fork-shard-v1", "rev": rev,
        "spec_sha256": digest(spec_raw), "shard": args.shard, "shards": args.shards,
        "runner_sha256": digest(args.test_exe.read_bytes()), "cases": results,
        "generated_field_cases": generated_results,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(f"state-fork shard pass shard={args.shard}/{args.shards} cases={len(results)} generated={len(generated_results)} fields={sum(len(x['field_witnesses']) for x in results + generated_results)}")


def matrix_summary(args: argparse.Namespace) -> None:
    rev = checked_rev(args.rev, args.repo)
    spec, spec_raw = load_spec(rev, args.repo)
    expected = manifest_cases(rev, args.repo, spec, verify_blobs=False)
    by_id: dict[str, dict] = {}
    generated_by_id: dict[str, dict] = {}
    for shard in range(args.shards):
        path = args.report_dir / f"state-fork-matrix-shard-{shard}.json"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ForkError(f"missing/invalid fork shard report {path}: {exc}") from exc
        if data.get("rev") != rev or data.get("spec_sha256") != digest(spec_raw) or data.get("shard") != shard or data.get("shards") != args.shards:
            raise ForkError(f"stale or misbound fork shard report: {path}")
        for case in data.get("cases", []):
            if case["id"] in by_id:
                raise ForkError(f"duplicate case across shards: {case['id']}")
            by_id[case["id"]] = case
        for case in data.get("generated_field_cases", []):
            if case["id"] in generated_by_id:
                raise ForkError(f"duplicate generated field case across shards: {case['id']}")
            generated_by_id[case["id"]] = case
    expected_ids = {case["id"] for case in expected}
    if set(by_id) != expected_ids:
        missing = sorted(expected_ids - set(by_id))
        extra = sorted(set(by_id) - expected_ids)
        raise ForkError(f"matrix coverage mismatch: missing={missing[:5]} extra={extra[:5]}")
    ordered = [by_id[case["id"]] for case in expected]
    expected_generated = {
        f"generated:{fixture['id']}:{profile}"
        for fixture in spec.get("generated_field_fixtures", [])
        for profile in fixture.get("profiles", [])
    }
    if set(generated_by_id) != expected_generated:
        raise ForkError(f"generated field fixture coverage mismatch: missing={sorted(expected_generated-set(generated_by_id))} extra={sorted(set(generated_by_id)-expected_generated)}")
    generated_ordered = [generated_by_id[key] for key in sorted(expected_generated)]
    for case in generated_ordered:
        fixture = next(item for item in spec["generated_field_fixtures"]
                       if item["id"] == case["fixture_id"])
        if case.get("sha256") != fixture["sha256"] or case.get("size_bytes") != fixture["size_bytes"]:
            raise ForkError(f"generated field fixture digest/size mismatch: {case['id']}")
    all_cases = ordered + generated_ordered
    report = {
        "schema": "gabbaboy-state-fork-report-v1", "rev": rev,
        "spec_sha256": digest(spec_raw), "snapshot_equivalence": True,
        "oracle_replay_claim": False, "case_count": len(ordered), "cases": ordered,
        "generated_field_case_count": len(generated_ordered),
        "generated_field_cases": generated_ordered,
        "field_witnesses": sorted({row["id"] for case in all_cases for row in case["field_witnesses"]}),
        "category_witnesses": sorted({row["id"] for case in all_cases for row in case["category_witnesses"]}),
        "expected_failure_cases": [case["id"] for case in ordered if any(
            str(value).lower() in {"expected-failure", "xfail", "fail"}
            for key, value in case.get("oracle_disposition", {}).items()
            if key in {"expect", "expected", "expected_disposition", "evaluator_status", "expected_role"})],
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(f"state-fork matrix pass cases={len(ordered)} generated={len(generated_ordered)} field_paths={len(report['field_witnesses'])} categories={','.join(report['category_witnesses'])}")


def field_paths_from_source(source: str) -> set[str]:
    match = re.search(r"static const state_field_descriptor STATE_FIELDS\[\] = \{(.*?)\n\};", source, re.S)
    if not match:
        raise ForkError("immutable core source has no STATE_FIELDS descriptor table")
    return set(re.findall(r'\{\s*\d+u,\s*"([^\"]+)"', match.group(1)))


def validate_report(report: dict, spec: dict, source: str, rev: str) -> list[str]:
    if report.get("schema") != "gabbaboy-state-fork-report-v1" or report.get("rev") != rev:
        raise ForkError("fork report is not bound to the requested immutable revision")
    if report.get("snapshot_equivalence") is not True or report.get("oracle_replay_claim") is not False:
        raise ForkError("fork report mislabels snapshot equivalence/oracle replay")
    if report.get("case_count") != spec.get("expected_case_count") or len(report.get("cases", [])) != spec.get("expected_case_count"):
        raise ForkError("fork report is incomplete")
    expected_generated = {
        f"generated:{fixture['id']}:{profile}": (fixture, profile)
        for fixture in spec.get("generated_field_fixtures", [])
        for profile in fixture.get("profiles", [])
    }
    generated_cases = report.get("generated_field_cases", [])
    if report.get("generated_field_case_count") != len(expected_generated) or len(generated_cases) != len(expected_generated):
        raise ForkError("generated field fixture report is incomplete")
    generated_ids = {case.get("id") for case in generated_cases}
    if generated_ids != set(expected_generated):
        raise ForkError(f"generated field fixture identities differ from spec: missing={sorted(set(expected_generated)-generated_ids)} extra={sorted(generated_ids-set(expected_generated))}")
    for case in generated_cases:
        fixture, profile = expected_generated[case["id"]]
        if (case.get("fixture_id") != fixture["id"] or case.get("profile") != profile or
            case.get("sha256") != fixture["sha256"] or case.get("size_bytes") != fixture["size_bytes"] or
            case.get("source") != fixture["source"] or
            case.get("prefix_budget") != fixture.get("prefix_budgets", {}).get(profile) or
            case.get("boundary_origin") != fixture.get("boundary_origin") or
            case.get("boundary_predicate") != fixture.get("boundary_predicate")):
            raise ForkError(f"generated field fixture identity/digest mismatch: {case.get('id')}")
        seed_boundaries = case.get("seed_boundaries", [])
        if len(seed_boundaries) != 1:
            raise ForkError(f"generated save boundary lacks one measured public run: {case.get('id')}")
        seed = seed_boundaries[0]
        try:
            requested, consumed, time = (int(seed[key]) for key in ("requested", "consumed", "time"))
            reason = int(seed["reason"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ForkError(f"malformed generated save-boundary measurement: {case.get('id')}") from exc
        if (seed.get("case") != case.get("id") or requested != case.get("prefix_budget") or
            consumed <= 0 or consumed > requested or time != consumed or reason < 0):
            raise ForkError(f"generated save-boundary measurement differs from fixture contract: {case.get('id')}")
        expected_seeded = fixture.get("seeded_wire_fields", [])
        public_seeds = case.get("public_state_seeds", [])
        if expected_seeded:
            if (len(public_seeds) != 1 or public_seeds[0].get("case") != case.get("id") or
                public_seeds[0].get("origin") != "crc-valid-public-load" or
                public_seeds[0].get("fields", "").split(",") != expected_seeded):
                raise ForkError(f"generated accepted-state load witness differs from fixture contract: {case.get('id')}")
        elif public_seeds:
            raise ForkError(f"unlisted generated accepted-state load in {case.get('id')}")
        expected_values = fixture.get("required_boundary_values", {})
        actual_values = {}
        for row in case.get("boundary_predicates", []):
            if row.get("case") != case.get("id"):
                raise ForkError(f"boundary predicate witness is attributed to another case: {case.get('id')}")
            try:
                actual_values[row["id"]] = int(row["value"])
            except (KeyError, TypeError, ValueError) as exc:
                raise ForkError(f"malformed boundary predicate witness: {case.get('id')}") from exc
        if actual_values != expected_values:
            raise ForkError(f"generated boundary values differ from executable predicate contract in {case.get('id')}")
        witnessed_fields = {row.get("id") for row in case.get("field_witnesses", [])}
        missing_fields = set(fixture.get("required_fields", [])) - witnessed_fields
        if missing_fields:
            raise ForkError(f"generated boundary predicate fields are unwitnessed in {case.get('id')}: {sorted(missing_fields)}")
        witnessed_categories = {row.get("id") for row in case.get("category_witnesses", [])}
        required_case_categories = fixture.get("required_categories_by_profile", {}).get(
            profile, fixture.get("required_categories", []))
        missing_case_categories = set(required_case_categories) - witnessed_categories
        if missing_case_categories:
            raise ForkError(f"generated boundary predicate categories are unwitnessed in {case.get('id')}: {sorted(missing_case_categories)}")
    fields = field_paths_from_source(source)
    all_cases = report["cases"] + generated_cases
    actual_witnesses: set[str] = set()
    actual_categories: set[str] = set()
    actual_constants: set[tuple[str, str]] = set()
    constant_specs = [item for item in spec.get("constant_dispositions", []) if isinstance(item, dict)]
    constants_by_path = {item.get("path"): item for item in constant_specs}
    required_categories = {item["id"] for item in spec.get("in_flight_categories", [])}
    for case in all_cases:
        case_id = case.get("id")
        if not isinstance(case_id, str):
            raise ForkError("fork case has no stable identity")
        for row in case.get("field_witnesses", []):
            if row.get("case") != case_id:
                raise ForkError(f"field witness is attributed to another case: {case_id}")
            field_id = row.get("id")
            if field_id not in fields:
                raise ForkError(f"unknown field witness: {field_id}")
            try:
                value, default = int(row["value"], 16), int(row["default"], 16)
                offset, count = int(row["offset"]), int(row["count"])
                width, index = int(row["width"]), int(row["index"])
            except (KeyError, TypeError, ValueError) as exc:
                raise ForkError(f"malformed field witness for {field_id}") from exc
            if (row.get("discriminator") != "nondefault" or row.get("treatment") != "serialize" or
                value == default or offset < 0 or count <= 0 or width <= 0 or not 0 <= index < count):
                raise ForkError(f"field witness is not an actual non-default serialized value: {field_id}")
            actual_witnesses.add(field_id)
        for row in case.get("category_witnesses", []):
            if row.get("case") != case_id or row.get("id") not in required_categories:
                raise ForkError(f"unknown/misattributed in-flight category witness in {case_id}")
            actual_categories.add(row["id"])
        for row in case.get("constant_witnesses", []):
            if row.get("case") != case_id:
                raise ForkError(f"constant witness is attributed to another case: {case_id}")
            try:
                value = int(row["value"])
                result_code = int(row["consumer_result"])
                address = int(row["address"], 16)
            except (KeyError, TypeError, ValueError) as exc:
                raise ForkError(f"malformed constant/consuming-path witness in {case_id}") from exc
            disposition = constants_by_path.get(row.get("id"))
            if (disposition is None or value != disposition.get("value") or
                result_code < 0 or address == 0):
                raise ForkError(f"constant/consuming-path witness has invalid observation: {case_id}")
            actual_constants.add((row.get("id", ""), case_id))
    witnessed = set(report.get("field_witnesses", []))
    if witnessed != actual_witnesses:
        raise ForkError("field witness summary differs from case-level observed values")
    explicit = set()
    for item in constant_specs:
        path = item.get("path")
        test_cases = item.get("tests")
        if (not path or not item.get("invariant") or not isinstance(test_cases, list) or
            not test_cases or not item.get("consumer")):
            raise ForkError("constant disposition lacks path, invariant, test or consuming-path evidence")
        if path in explicit:
            raise ForkError(f"duplicate constant disposition: {path}")
        explicit.add(path)
        if not isinstance(item.get("value"), int):
            raise ForkError(f"constant disposition lacks an exact invariant value: {path}")
    allowed_constants = {(item["path"], test_case) for item in constant_specs
                         for test_case in item["tests"]}
    if actual_constants != allowed_constants:
        raise ForkError(f"constant disposition witness mismatch: missing={sorted(allowed_constants-actual_constants)} extra={sorted(actual_constants-allowed_constants)}")
    unknown = (witnessed | explicit) - fields
    if unknown:
        raise ForkError(f"unknown field disposition/witness: {sorted(unknown)[:5]}")
    missing = fields - witnessed - explicit
    if missing:
        raise ForkError(f"serialized field lacks non-default witness or justified disposition: {sorted(missing)[:12]}")
    observed = set(report.get("category_witnesses", []))
    if observed != actual_categories:
        raise ForkError("category witness summary differs from case-level save-boundary witnesses")
    missing_categories = required_categories - observed
    if missing_categories:
        raise ForkError(f"in-flight category lacks save-boundary witness: {sorted(missing_categories)}")
    return []


def self_test(report: dict, spec: dict, source: str, rev: str) -> None:
    corrupted = json.loads(json.dumps(report))
    for case in corrupted.get("cases", []) + corrupted.get("generated_field_cases", []):
        case["category_witnesses"] = [row for row in case.get("category_witnesses", [])
                                       if row.get("id") != "hdma_byte_phase"]
    corrupted["category_witnesses"] = [row for row in corrupted.get("category_witnesses", [])
                                        if row != "hdma_byte_phase"]
    try:
        validate_report(corrupted, spec, source, rev)
    except ForkError as exc:
        if "in-flight category lacks" not in str(exc):
            raise ForkError(f"census negative control failed for wrong reason: {exc}") from exc
    else:
        raise ForkError("census negative control passed after removing hdma_byte_phase")
    corrupted = json.loads(json.dumps(report))
    if not corrupted.get("field_witnesses"):
        raise ForkError("cannot exercise default-only field control: no witnesses exist")
    missing_field = corrupted["field_witnesses"][0]
    for case in corrupted.get("cases", []) + corrupted.get("generated_field_cases", []):
        case["field_witnesses"] = [row for row in case.get("field_witnesses", [])
                                   if row.get("id") != missing_field]
    corrupted["field_witnesses"] = [row for row in corrupted["field_witnesses"]
                                    if row != missing_field]
    try:
        validate_report(corrupted, spec, source, rev)
    except ForkError as exc:
        if "serialized field lacks" not in str(exc):
            raise ForkError(f"field negative control failed for wrong reason: {exc}") from exc
    else:
        raise ForkError("field negative control passed after deleting a field witness")
    corrupted = json.loads(json.dumps(report))
    witness = next(row for case in corrupted["cases"] + corrupted["generated_field_cases"]
                   for row in case.get("field_witnesses", []))
    witness["default"] = witness["value"]
    try:
        validate_report(corrupted, spec, source, rev)
    except ForkError as exc:
        if "non-default serialized value" not in str(exc):
            raise ForkError(f"default-only field control failed for wrong reason: {exc}") from exc
    else:
        raise ForkError("census negative control passed after making a field witness default-only")
    print("state-fork census self-test pass missing-category=refused missing-field-witness=refused default-only-field=refused")


def check_report(args: argparse.Namespace) -> None:
    rev = checked_rev(args.rev, args.repo)
    spec, _ = load_spec(rev, args.repo)
    source = git_blob(rev, "src/core/gabbaboy.c", args.repo).decode("utf-8")
    try:
        report = json.loads(args.check.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ForkError(f"cannot read fork report {args.check}: {exc}") from exc
    validate_report(report, spec, source, rev)
    print(f"state-fork census pass rev={rev} cases={report['case_count']} fields={len(report['field_witnesses'])} categories={len(report['category_witnesses'])}")
    if args.self_test:
        self_test(report, spec, source, rev)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rev")
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--matrix-shard", action="store_true")
    parser.add_argument("--matrix-summary", action="store_true")
    parser.add_argument("--test-exe", type=Path)
    parser.add_argument("--shard", type=int, default=0)
    parser.add_argument("--shards", type=int, default=16)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--report-dir", type=Path)
    parser.add_argument("--check", type=Path)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--mutants", action="store_true")
    parser.add_argument("--build-dir", type=Path)
    args = parser.parse_args()
    args.repo = args.repo.resolve()
    if args.test_exe:
        args.test_exe = args.test_exe.resolve()
    if args.report:
        args.report = args.report.resolve()
    if args.report_dir:
        args.report_dir = args.report_dir.resolve()
    if args.check:
        args.check = args.check.resolve()
    return args


def main() -> int:
    args = parse_args()
    try:
        if args.matrix_shard:
            if not args.test_exe or not args.report or not args.rev:
                raise ForkError("--matrix-shard needs --rev, --test-exe and --report")
            run_shard(args)
        elif args.matrix_summary:
            if not args.report or not args.report_dir or not args.rev:
                raise ForkError("--matrix-summary needs --rev, --report and --report-dir")
            matrix_summary(args)
        elif args.check:
            if not args.rev:
                raise ForkError("--check needs --rev")
            check_report(args)
        elif args.self_test:
            raise ForkError("--self-test must accompany --check REPORT --rev SHA")
        elif args.mutants:
            raise ForkError("--mutants implementation is not yet available")
        else:
            raise ForkError("select --matrix-shard, --matrix-summary, --check, or --mutants")
    except ForkError as exc:
        print(f"verify-state-forks: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
