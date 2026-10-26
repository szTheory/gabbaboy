#!/usr/bin/env python3
"""Fail-closed source inventory and pre-codec proof receipt for native states.

All source checks are read from the requested immutable git object. The compiled
library scan is deliberately separate: source review cannot prove that the built
core has no writable file-scope storage.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


class ContractError(Exception):
    pass


def run(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)


def git_show(root: Path, rev: str, path: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{40}", rev):
        raise ContractError("--rev must be a resolved immutable 40-hex commit")
    result = run(["git", "show", f"{rev}:{path}"], cwd=root)
    if result.returncode != 0:
        raise ContractError(f"git show {rev}:{path} failed: {result.stderr.strip()}")
    return result.stdout


def strip_comments(text: str) -> str:
    return re.sub(r"/\*.*?\*/|//[^\n]*", "", text, flags=re.S)


def struct_bodies(text: str) -> dict[str, str]:
    clean = strip_comments(text)
    found: dict[str, str] = {}
    typedef = re.compile(r"typedef\s+struct(?:\s+\w+)?\s*\{(.*?)\}\s*(\w+)\s*;", re.S)
    for match in typedef.finditer(clean):
        name, body = match.group(2), match.group(1)
        if name in found:
            raise ContractError(f"duplicate struct declaration: {name}")
        found[name] = body
    instance = re.search(r"struct\s+gbb_instance\s*\{(.*?)\}\s*;", clean, re.S)
    if instance:
        if "gbb_instance" in found:
            raise ContractError("duplicate struct declaration: gbb_instance")
        found["gbb_instance"] = instance.group(1)
    return found


def declaration_records(body: str) -> list[tuple[str, str, bool, bool, str]]:
    """Return name, base type, pointer, array and preprocessor discriminator."""
    records: list[tuple[str, str, bool, bool, str]] = []
    conditions: list[str] = []
    buffer = ""
    declaration_condition = ""
    for line in body.splitlines():
        directive = re.match(r"\s*#\s*(if|ifdef|ifndef|else|elif|endif)\b(.*)", line)
        if directive:
            kind, expression = directive.group(1), directive.group(2).strip()
            if kind in ("if", "ifdef", "ifndef"):
                conditions.append(f"{kind} {expression}".strip())
            elif kind == "else" and conditions:
                conditions[-1] = f"else({conditions[-1]})"
            elif kind == "elif" and conditions:
                conditions[-1] = f"elif({expression})"
            elif kind == "endif" and conditions:
                conditions.pop()
            continue
        if not buffer.strip():
            declaration_condition = " & ".join(conditions)
        buffer += " " + line
        while ";" in buffer:
            statement, buffer = buffer.split(";", 1)
            statement = re.sub(r"\s+", " ", statement).strip()
            if not statement:
                declaration_condition = " & ".join(conditions)
                continue
            parts = [part.strip() for part in statement.split(",")]
            first = parts[0]
            match = re.search(r"(\*\s*)?([A-Za-z_]\w*)\s*((?:\[[^\]]*\]\s*)*)$", first)
            if not match:
                raise ContractError(f"unparsed struct member declaration: {statement}")
            base = first[:match.start()].strip()
            pointer = bool(match.group(1)) or "*" in base
            base = re.sub(r"\*", "", base).strip()
            name = match.group(2)
            array = bool(match.group(3).strip())
            if not base or not name:
                raise ContractError(f"unparsed struct member declaration: {statement}")
            records.append((name, base, pointer, array, declaration_condition))
            for declarator in parts[1:]:
                match = re.fullmatch(r"\s*(\*\s*)?([A-Za-z_]\w*)\s*((?:\[[^\]]*\]\s*)*)\s*", declarator)
                if not match:
                    raise ContractError(f"unparsed comma-separated member: {statement}")
                records.append((match.group(2), base, bool(match.group(1)) or pointer,
                                bool(match.group(3).strip()), declaration_condition))
            declaration_condition = " & ".join(conditions)
    if buffer.strip():
        raise ContractError(f"unterminated struct member declaration: {buffer.strip()}")
    return records


def flattened_instance(core: str, header: str) -> list[dict[str, str]]:
    types = struct_bodies(header)
    types.update(struct_bodies(core))
    if "gbb_instance" not in types:
        raise ContractError("gbb_instance declaration was not parsed")
    output: list[dict[str, str]] = []

    def descend(type_name: str, prefix: str, inherited_condition: str, stack: tuple[str, ...]) -> None:
        if type_name in stack:
            raise ContractError(f"recursive instance member type at {prefix}: {type_name}")
        body = types.get(type_name)
        if body is None:
            raise ContractError(f"nested struct type {type_name} has no parsed declaration at {prefix}")
        members = declaration_records(body)
        if not members:
            raise ContractError(f"empty or unparsed member inventory for {type_name} at {prefix or '<root>'}")
        names: set[str] = set()
        for name, base, pointer, array, condition in members:
            if name in names:
                raise ContractError(f"duplicate member declaration {prefix + name}")
            names.add(name)
            path = f"{prefix}{name}"
            condition_path = " & ".join(part for part in (inherited_condition, condition) if part)
            nested_type = base.removeprefix("struct ").strip()
            if not pointer and nested_type in types:
                child_prefix = path + ("[]" if array else "") + "."
                descend(nested_type, child_prefix, condition_path, (*stack, type_name))
            else:
                output.append({"path": path, "type": nested_type, "pointer": str(pointer),
                               "array": str(array), "condition": condition_path})

    descend("gbb_instance", "", "", ())
    if not output:
        raise ContractError("empty flattened gbb_instance inventory")
    paths = [item["path"] for item in output]
    if len(paths) != len(set(paths)):
        raise ContractError("duplicate qualified member path")
    return output


def parse_treatments(core: str) -> list[tuple[str, str, str]]:
    match = re.search(r"STATE_FIELD_TREATMENT\s*\[\s*\]\s*=\s*\{(.*?)\};", core, re.S)
    if not match:
        raise ContractError("STATE_FIELD_TREATMENT table is missing")
    rows = re.findall(r'\{\s*"([^"\n]+)"\s*,\s*(STATE_TREAT_[A-Z_]+)\s*,\s*"([^"\n]+)"\s*\}', match.group(1))
    if not rows:
        raise ContractError("STATE_FIELD_TREATMENT is empty or unparsed")
    if len(rows) != len(set(row[0] for row in rows)):
        raise ContractError("duplicate STATE_FIELD_TREATMENT rule")
    return rows


def treatment_for(path: str, rows: list[tuple[str, str, str]]) -> tuple[str, str]:
    matches = [(len(pattern.replace("*", "")), disposition, reason)
               for pattern, disposition, reason in rows if fnmatch.fnmatchcase(path, pattern)]
    if not matches:
        raise ContractError(f"unclassified instance member: {path}")
    matches.sort(reverse=True)
    if len(matches) > 1 and matches[0][0] == matches[1][0]:
        raise ContractError(f"ambiguous treatment rules for {path}")
    return matches[0][1], matches[0][2]


def verify_fixture_coverage(items: list[dict[str, str]],
                            rows: list[tuple[str, str, str]],
                            descriptors: set[str]) -> None:
    serialized = []
    for item in items:
        disposition, _reason = treatment_for(item["path"], rows)
        if disposition == "STATE_TREAT_SERIALIZE":
            serialized.append(item["path"])
    missing = sorted(path for path in serialized if path not in descriptors)
    if missing:
        raise ContractError("serialized member(s) missing from STATE_FIELDS: " + ", ".join(missing))


def parse_state_fields(core: str) -> list[dict[str, str]]:
    match = re.search(r"STATE_FIELDS\s*\[\s*\]\s*=\s*\{(.*?)\};", core, re.S)
    if not match:
        raise ContractError("STATE_FIELDS wire table is missing")
    rows = re.findall(r'\{\s*(\d+)u\s*,\s*"([^"\n]+)"\s*,\s*(\d+)u\s*,\s*([^,}]+)', match.group(1))
    if not rows:
        raise ContractError("STATE_FIELDS is empty or unparsed")
    result = [{"order": order, "path": path, "width": width, "count": count.strip()}
              for order, path, width, count in rows]
    orders = [int(row["order"]) for row in result]
    if orders != list(range(len(orders))):
        raise ContractError("STATE_FIELDS order must be explicit and consecutive from zero")
    paths = [row["path"] for row in result]
    if len(paths) != len(set(paths)):
        raise ContractError("duplicate STATE_FIELDS wire path")
    return result


def verify_audio_edge_schedule(core: str) -> None:
    begin = core.find("STATE_AUDIO_EDGE_BOUND_BEGIN")
    end = core.find("STATE_AUDIO_EDGE_BOUND_END", begin + 1)
    if begin < 0 or end < 0:
        raise ContractError("production audio edge-bound markers are missing")
    block = core[begin:end]
    if block.count("audio_add_edge(") != 2:
        raise ContractError("production audio block must contain exactly one possible edge per channel per half-dot")
    if block.count("audio_current_mix(") != 1 or block.count("audio_process_sample(") != 1:
        raise ContractError("production audio block no longer proves one mix evaluation and at most one sample consume")
    if "m->apu_sample_phase += GBB_AUDIO_SAMPLE_RATE;" not in block:
        raise ContractError("audio edge block is detached from the sample phase accumulator")
    if "m->apu_sample_phase >= GBB_AUDIO_CLOCK_HALF_DOTS" not in block:
        raise ContractError("audio edge block no longer consumes only at the fixed sample threshold")
    if "GBB_AUDIO_SAMPLE_RATE < GBB_AUDIO_CLOCK_HALF_DOTS" not in core:
        raise ContractError("audio rate must be below the clock so a half-dot emits at most one sample")
    calls = len(re.findall(r"\baudio_add_edge\s*\(", core))
    if calls != 7:
        raise ContractError(f"unexpected audio_add_edge call-site count {calls}; audit every production/test path")


def verify_inventory(core: str, header: str) -> dict[str, object]:
    inventory = flattened_instance(core, header)
    treatments = parse_treatments(core)
    classified: dict[str, dict[str, str]] = {}
    for item in inventory:
        disposition, reason = treatment_for(item["path"], treatments)
        item["disposition"] = disposition.removeprefix("STATE_TREAT_").lower()
        item["reason"] = reason
        classified[item["path"]] = item
    verify_audio_edge_schedule(core)
    fields = parse_state_fields(core)
    descriptor_paths = {field["path"] for field in fields}
    missing = sorted(path for path, item in classified.items()
                     if item["disposition"] == "serialize" and path not in descriptor_paths)
    extra = sorted(path for path in descriptor_paths
                   if path not in classified or classified[path]["disposition"] != "serialize")
    if missing:
        raise ContractError("serialized member(s) missing from STATE_FIELDS: " + ", ".join(missing))
    if extra:
        raise ContractError("STATE_FIELDS path(s) are not classified as serialized: " + ", ".join(extra))
    return {"members": classified, "fields": fields, "rules": len(treatments)}


def writable_symbols(nm_text: str) -> list[str]:
    writable: list[str] = []
    for line in nm_text.splitlines():
        if re.search(r"\(__DATA\s*,\s*__(?:data|bss|common|thread_data|thread_bss)\)", line):
            writable.append(line.split()[-1])
            continue
        match = re.search(r"\s([BbCcDdGgSs])\s+([^\s]+)$", line)
        if match:
            writable.append(match.group(2))
    return sorted(set(writable))


def verify_nm(nm: str, library: Path) -> dict[str, object]:
    if not library.is_file():
        raise ContractError(f"core library does not exist: {library}")
    result = run([nm, "-a", "-m", str(library)])
    if result.returncode != 0:
        raise ContractError(f"nm could not inspect {library}: {result.stderr.strip()}")
    symbols = writable_symbols(result.stdout)
    if symbols:
        raise ContractError("writable file-scope core symbol(s): " + ", ".join(symbols))
    return {"library_sha256": hashlib.sha256(library.read_bytes()).hexdigest(), "writable_symbols": []}


def inventory_self_test() -> None:
    base = """typedef struct {
 uint8_t keep;
} child;
struct gbb_instance {
 child nested;
 uint8_t root;
#if GBB_TEST_SWITCH
 uint8_t conditional;
#endif
};
"""
    actual = flattened_instance(base, "")
    if {item["path"] for item in actual} != {"nested.keep", "root", "conditional"}:
        raise ContractError("inventory positive control failed")
    if not next(item for item in actual if item["path"] == "conditional")["condition"]:
        raise ContractError("conditional discriminator was not retained")
    rules = [("nested.*", "STATE_TREAT_SERIALIZE", "nested fields are explicit"),
             ("root", "STATE_TREAT_EXCLUDE", "root observer excluded"),
             ("conditional", "STATE_TREAT_EXCLUDE", "conditional test field excluded")]
    verify_fixture_coverage(actual, rules, {"nested.keep"})
    mutants = (
        (base.replace("uint8_t root;", "uint8_t root;\n uint8_t added_top;"), "added_top"),
        (base.replace("uint8_t keep;", "uint8_t keep;\n uint8_t added_nested;"), "nested.added_nested"),
        (base.replace("uint8_t conditional;", "uint8_t conditional;\n uint8_t added_conditional;"), "added_conditional"),
    )
    for mutant, expected in mutants:
        try:
            verify_fixture_coverage(flattened_instance(mutant, ""), rules, {"nested.keep"})
        except ContractError as error:
            if expected not in str(error):
                raise ContractError(f"wrong inventory mutant diagnostic: {error}") from error
        else:
            raise ContractError(f"inventory mutant survived: {expected}")
    duplicate_member = base.replace("uint8_t root;", "uint8_t root;\n uint8_t root;")
    try:
        flattened_instance(duplicate_member, "")
    except ContractError as error:
        if "duplicate member declaration root" not in str(error):
            raise ContractError(f"wrong duplicate-member diagnostic: {error}") from error
    else:
        raise ContractError("duplicate member mutant survived")
    try:
        flattened_instance("struct gbb_instance {};", "")
    except ContractError:
        pass
    else:
        raise ContractError("empty inventory mutant survived")
    for empty_or_duplicate in (
        "static state_field_descriptor STATE_FIELDS[] = {};",
        'static state_field_descriptor STATE_FIELDS[] = {{ 0u, "x", 1u, 1u }, { 1u, "x", 1u, 1u }};'
    ):
        try:
            parse_state_fields(empty_or_duplicate)
        except ContractError:
            pass
        else:
            raise ContractError("empty or duplicate STATE_FIELDS mutant survived")
    audio_stub = """#define GBB_AUDIO_SAMPLE_RATE 1
#define GBB_AUDIO_CLOCK_HALF_DOTS 2
_Static_assert(GBB_AUDIO_SAMPLE_RATE < GBB_AUDIO_CLOCK_HALF_DOTS, "sample rate");
static void audio_add_edge(void) {}
static void test_kernel(void) { audio_add_edge(); audio_add_edge(); }
static void test_edge(void) { audio_add_edge(); audio_add_edge(); }
/* STATE_AUDIO_EDGE_BOUND_BEGIN */
m->apu_sample_phase += GBB_AUDIO_SAMPLE_RATE;
audio_current_mix(m, &left, &right);
audio_add_edge();
audio_add_edge();
if (m->apu_sample_phase >= GBB_AUDIO_CLOCK_HALF_DOTS) audio_process_sample(m);
/* STATE_AUDIO_EDGE_BOUND_END */
"""
    verify_audio_edge_schedule(audio_stub)
    try:
        verify_audio_edge_schedule(audio_stub.replace(
            "/* STATE_AUDIO_EDGE_BOUND_END */",
            "audio_add_edge();\n/* STATE_AUDIO_EDGE_BOUND_END */"))
    except ContractError:
        pass
    else:
        raise ContractError("extra-edge schedule mutant survived")


def globals_self_test(nm: str, cc: str) -> None:
    with tempfile.TemporaryDirectory(prefix="gabbaboy-state-nm-") as temp:
        root = Path(temp)
        source, obj = root / "globals.c", root / "globals.o"
        source.write_text("int gbb_seed_global = 1; static volatile int gbb_seed_static = 3; const int gbb_seed_ro = 2; int gbb_seed_read(void) { return gbb_seed_static; }\n")
        compile_result = run(shlex.split(cc) + ["-c", str(source), "-o", str(obj)])
        if compile_result.returncode != 0:
            raise ContractError(f"global negative-control compile failed: {compile_result.stderr.strip()}")
        nm_result = run([nm, "-a", "-m", str(obj)])
        if nm_result.returncode != 0:
            raise ContractError(f"nm global negative-control failed: {nm_result.stderr.strip()}")
        symbols = writable_symbols(nm_result.stdout)
        if not any("gbb_seed_global" in name for name in symbols):
            raise ContractError("nm control missed the seeded external writable global")
        if not any("gbb_seed_static" in name for name in symbols):
            raise ContractError("nm control missed the seeded file-static writable global")
        if any("gbb_seed_ro" in name for name in symbols):
            raise ContractError("nm control misclassified immutable read-only storage")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_digest(root: Path, rev: str) -> tuple[str, str, str]:
    core = git_show(root, rev, "src/core/gabbaboy.c")
    header = git_show(root, rev, "include/gabbaboy/gabbaboy.h")
    source_hash = hashlib.sha256(core.encode()).hexdigest()
    treatment_start = core.find("static const state_field_treatment_rule STATE_FIELD_TREATMENT[]")
    treatment_end = core.find("};", treatment_start) + 2 if treatment_start >= 0 else -1
    fields_start = core.find("static const state_field_descriptor STATE_FIELDS[]")
    fields_end = core.find("};", fields_start) + 2 if fields_start >= 0 else -1
    audio_start = core.find("static const int16_t audio_step_q15")
    audio_end = core.find("};", audio_start) + 2 if audio_start >= 0 else -1
    if min(treatment_start, treatment_end, fields_start, fields_end, audio_start, audio_end) < 0:
        raise ContractError("field descriptor/range source markers are missing")
    bounds_start = core.find("#define GBB_STATE_AUDIO_MIX_MIN")
    bounds_end = core.find("static int16_t audio_saturate_s16", bounds_start)
    if bounds_start < 0 or bounds_end < 0:
        raise ContractError("audio range source markers are missing")
    descriptor_material = (core[treatment_start:treatment_end] + core[fields_start:fields_end] +
                           core[bounds_start:bounds_end] + core[audio_start:audio_end])
    descriptor_hash = hashlib.sha256(descriptor_material.encode()).hexdigest()
    input_hash = hashlib.sha256((core + "\0" + header).encode()).hexdigest()
    return source_hash, descriptor_hash, input_hash


def run_precodec(args: argparse.Namespace, root: Path) -> None:
    core = git_show(root, args.rev, "src/core/gabbaboy.c")
    header = git_show(root, args.rev, "include/gabbaboy/gabbaboy.h")
    source_file = root / "src/core/gabbaboy.c"
    if not source_file.is_file() or source_file.read_text() != core:
        raise ContractError("live core source differs from the immutable --rev")
    verify_inventory(core, header)
    library = args.build_dir / "libgabbaboy_core.a"
    nm_receipt = verify_nm(args.nm, library)
    api = args.build_dir / "tests" / "test_state_api"
    if not api.is_file():
        raise ContractError(f"proof executable is missing: {api}")
    proof_results: dict[str, str] = {}
    for case in ("size_bound", "audio_bound"):
        result = run([str(api), case], cwd=root)
        if result.returncode != 0:
            raise ContractError(f"{case} proof executable failed ({result.returncode}): {result.stdout}{result.stderr}")
        proof_results[case] = result.stdout.strip() or "pass"
    self_test = run([sys.executable, str(root / "tests/scripts/verify-state-contract.py"),
                     "--self-test", "--control", "all", "--nm", args.nm, "--cc", args.cc], cwd=root)
    if self_test.returncode != 0:
        raise ContractError(f"inventory/global negative controls failed: {self_test.stdout}{self_test.stderr}")
    source_hash, descriptor_hash, input_hash = source_digest(root, args.rev)
    cache = args.build_dir / "CMakeCache.txt"
    cache_text = cache.read_text(errors="replace") if cache.is_file() else ""
    compiler_match = re.search(r"^CMAKE_C_COMPILER:FILEPATH=(.*)$", cache_text, re.M)
    generator_match = re.search(r"^CMAKE_GENERATOR:INTERNAL=(.*)$", cache_text, re.M)
    receipt = {
        "schema": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": args.rev,
        "core_source_sha256": source_hash,
        "descriptor_range_constants_sha256": descriptor_hash,
        "proof_input_sha256": input_hash,
        "proof_executable_sha256": sha256_file(api),
        "cmake_generator": generator_match.group(1) if generator_match else "unknown",
        "c_compiler": compiler_match.group(1) if compiler_match else "unknown",
        "library": str(library.relative_to(root)) if library.is_relative_to(root) else library.name,
        "library_sha256": nm_receipt["library_sha256"],
        "proof_results": proof_results,
        "negative_controls": "pass",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(f"state pre-codec proof pass source={args.rev} descriptors={descriptor_hash} executable={receipt['proof_executable_sha256']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", action="store_true")
    parser.add_argument("--globals", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--precodec", action="store_true")
    parser.add_argument("--tracer", action="store_true")
    parser.add_argument("--control", choices=("inventory", "globals", "all"), default="all")
    parser.add_argument("--rev", required=False)
    parser.add_argument("--library", type=Path)
    parser.add_argument("--build-dir", type=Path, default=Path("build"))
    parser.add_argument("--output", type=Path, default=Path("build/state-precodec-proof.json"))
    parser.add_argument("--nm", default=os.environ.get("CMAKE_NM", "nm"))
    parser.add_argument("--cc", default=os.environ.get("CC", "cc"))
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.repo.resolve()
    try:
        if args.self_test:
            if args.control in ("inventory", "all"):
                inventory_self_test()
            if args.control in ("globals", "all"):
                globals_self_test(args.nm, args.cc)
            print(f"state contract controls pass control={args.control}")
            return 0
        if args.rev is None:
            raise ContractError("an immutable --rev is required")
        core = git_show(root, args.rev, "src/core/gabbaboy.c")
        header = git_show(root, args.rev, "include/gabbaboy/gabbaboy.h")
        if args.inventory:
            result = verify_inventory(core, header)
            print(f"state inventory pass members={len(result['members'])} fields={len(result['fields'])}")
            return 0
        if args.globals:
            if args.library is None:
                raise ContractError("--globals requires --library PATH")
            result = verify_nm(args.nm, args.library)
            print(f"state globals pass library_sha256={result['library_sha256']}")
            return 0
        if args.precodec:
            run_precodec(args, root)
            return 0
        if args.tracer:
            raise ContractError("--tracer is implemented with the installed API in the next plan task")
        raise ContractError("select --inventory, --globals, --self-test, --precodec or --tracer")
    except (ContractError, OSError) as error:
        print(f"state contract failure: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
