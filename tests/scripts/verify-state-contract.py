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


def verify_public_state_contract(header: str, core: str) -> None:
    clean_header = strip_comments(header)
    error_enum = next((match for match in re.finditer(
        r"typedef\s+enum\s*\{(.*?)\}\s*(\w+)\s*;", clean_header, re.S)
        if match.group(2) == "gbb_error"), None)
    if error_enum is None:
        raise ContractError("public gbb_error enum is missing")
    values: dict[str, int] = {}
    value = -1
    for part in error_enum.group(1).split(","):
        part = part.strip()
        if not part:
            continue
        match = re.fullmatch(r"([A-Za-z_]\w*)\s*(?:=\s*(\d+))?", part)
        if not match:
            raise ContractError(f"unparsed public error enumerator: {part}")
        value = int(match.group(2)) if match.group(2) is not None else value + 1
        values[match.group(1)] = value
    old_errors = [name for name in values if not name.startswith("GBB_STATE_")]
    if len(old_errors) < 21 or any(values[name] != index for index, name in enumerate(old_errors[:21])):
        raise ContractError("existing public gbb_error values 0..20 changed")
    expected_errors = {
        "GBB_STATE_NO_ROM": 21,
        "GBB_STATE_BAD_FORMAT": 22,
        "GBB_STATE_UNSUPPORTED_VERSION": 23,
        "GBB_STATE_IDENTITY_MISMATCH": 24,
        "GBB_STATE_SIZE_MISMATCH": 25,
        "GBB_STATE_CORRUPT": 26,
        "GBB_STATE_INVALID_CONTENT": 27,
    }
    for name, expected in expected_errors.items():
        if values.get(name) != expected:
            raise ContractError(f"{name} must have frozen numeric value {expected}")
    signatures = (
        r"gbb_error\s+gbb_state_size\s*\(\s*const\s+gbb_instance\s*\*\s*\w+\s*,\s*size_t\s*\*\s*\w+\s*\)\s*;",
        r"gbb_error\s+gbb_save_state\s*\(\s*const\s+gbb_instance\s*\*\s*\w+\s*,\s*uint8_t\s*\*\s*\w+\s*,\s*size_t\s+\w+\s*\)\s*;",
        r"gbb_error\s+gbb_load_state\s*\(\s*gbb_instance\s*\*\s*\w+\s*,\s*const\s+uint8_t\s*\*\s*\w+\s*,\s*size_t\s+\w+\s*\)\s*;",
    )
    for signature in signatures:
        if not re.search(signature, clean_header):
            raise ContractError("public state API declaration is missing or has the wrong signature")
    required_core = (
        "state_walk", "state_validate", "state_apply", "state_crc32", "state_sha256",
        "rom_sha256", "GBB_STATE_FORMAT_VERSION", "GBB_STATE_BEHAVIOR_VERSION",
    )
    missing = [name for name in required_core if name not in core]
    if missing:
        raise ContractError("state codec implementation is missing: " + ", ".join(missing))


def verify_state_documentation(state_format: str, cartridge_saves: str) -> None:
    state_format = re.sub(r"\s+", " ", state_format)
    cartridge_saves = re.sub(r"\s+", " ", cartridge_saves)
    required_format_claims = (
        "| 0 | 4 | Magic | ASCII `GBBS` |",
        "| 4 | 2 | Format version | `1` |",
        "| 6 | 2 | Header size | `64` |",
        "| 20 | 32 | ROM identity | SHA-256 of the complete loaded ROM |",
        "| 60 | 4 | CRC-32 | CRC described below |",
        "The check value for ASCII `123456789` is `0xCBF43926`.",
        "198 typed descriptors",
        "maximum admitted descriptor body is 320184 bytes",
        "maximum emitted state is 320248 bytes",
        "`GBB_STATE_INVALID_CONTENT`",
        "externally serialized",
        "does not allocate memory or hash the ROM per call",
    )
    missing = [claim for claim in required_format_claims if claim not in state_format]
    if missing:
        raise ContractError("state-format.md is missing contract claim: " + missing[0])
    required_battery_claims = (
        "## Native machine states",
        "[`state-format.md`](state-format.md)",
        "buffers must remain valid during the call and must not overlap the instance",
        "The API has no filesystem access",
    )
    missing = [claim for claim in required_battery_claims if claim not in cartridge_saves]
    if missing:
        raise ContractError("cartridge-and-saves.md is missing state API claim: " + missing[0])


def verify_state_documentation_negative_control(state_format: str, cartridge_saves: str) -> None:
    mutant = state_format.replace("ASCII `GBBS`", "ASCII `GBBX`", 1)
    if mutant == state_format:
        raise ContractError("state documentation magic mutant was not seeded")
    try:
        verify_state_documentation(mutant, cartridge_saves)
    except ContractError:
        return
    raise ContractError("state documentation magic negative control survived")


def version_component_self_test(cmake: str, module: Path) -> None:
    if not module.is_file():
        raise ContractError(f"state release version helper is missing: {module}")
    with tempfile.TemporaryDirectory(prefix="gabbaboy-state-version-") as temp:
        root = Path(temp)
        escaped_module = str(module.resolve()).replace("\\", "\\\\").replace('"', '\\"')
        project = root / "CMakeLists.txt"
        project.write_text(
            "cmake_minimum_required(VERSION 3.25)\n"
            "project(StateVersionControl NONE)\n"
            f'include("{escaped_module}")\n'
            'gbb_parse_state_release_version("${GBB_VERSION_UNDER_TEST}" GBB_MAJOR GBB_MINOR GBB_PATCH)\n'
            'message(STATUS "state version parsed=${GBB_MAJOR}.${GBB_MINOR}.${GBB_PATCH}")\n'
        )
        valid = ("0.2.1", "65535.65535.65535")
        invalid = ("-1.0.0", "1.0", "1.0.0.1", "1.a.0", "65536.0.0", "1.65536.0")
        for version in valid:
            result = run([cmake, "-S", str(root), "-B", str(root / ("valid-" + version.replace(".", "-"))),
                          f"-DGBB_VERSION_UNDER_TEST={version}"])
            expected_line = "state version parsed=" + version
            if result.returncode != 0 or expected_line not in result.stdout:
                raise ContractError(f"valid state version control failed for {version}: {result.stdout}{result.stderr}")
        for version in invalid:
            result = run([cmake, "-S", str(root), "-B", str(root / ("invalid-" + re.sub(r"[^A-Za-z0-9]+", "-", version))),
                          f"-DGBB_VERSION_UNDER_TEST={version}"])
            if result.returncode == 0 or "GabbaBoy state release version" not in result.stdout + result.stderr:
                raise ContractError(f"invalid state version control survived for {version}: {result.stdout}{result.stderr}")


def run_format_contract(args: argparse.Namespace, root: Path, core: str, header: str) -> None:
    verify_public_state_contract(header, core)
    state_format = git_show(root, args.rev, "docs/state-format.md")
    cartridge_saves = git_show(root, args.rev, "docs/cartridge-and-saves.md")
    verify_state_documentation(state_format, cartridge_saves)
    verify_state_documentation_negative_control(state_format, cartridge_saves)
    if args.version_module is None or args.api is None or args.rom is None or args.cmake is None:
        raise ContractError("--format-contract requires --version-module, --api, --rom and --cmake")
    version_component_self_test(args.cmake, args.version_module)
    if not args.api.is_file():
        raise ContractError(f"format proof executable is missing: {args.api}")
    result = run([str(args.api), "format_contract", str(args.rom)], cwd=root)
    if result.returncode != 0:
        raise ContractError(f"format proof executable failed ({result.returncode}): {result.stdout}{result.stderr}")
    print(f"state format contract pass source={args.rev} docs_control=pass version_controls=8 api={result.stdout.strip() or 'pass'}")


def run_tracer(args: argparse.Namespace, root: Path, core: str, header: str) -> None:
    source_file = root / "src/core/gabbaboy.c"
    header_file = root / "include/gabbaboy/gabbaboy.h"
    if source_file.read_text() != core or header_file.read_text() != header:
        raise ContractError("installed tracer source differs from immutable --rev")
    verified = verify_inventory(core, header)
    source_hash, descriptor_hash, input_hash = source_digest(root, args.rev)
    receipt_path = args.build_dir / "state-precodec-proof.json"
    if not receipt_path.is_file():
        raise ContractError("state_precodec_gate receipt is missing before installed tracer")
    receipt = json.loads(receipt_path.read_text())
    if (receipt.get("source_commit") != args.rev or
            receipt.get("descriptor_range_constants_sha256") != descriptor_hash or
            receipt.get("core_source_sha256") != source_hash or
            receipt.get("proof_input_sha256") != input_hash or
            receipt.get("negative_controls") != "pass"):
        raise ContractError("pre-codec receipt is stale or does not bind the installed tracer revision")
    if not verified["fields"]:
        raise ContractError("installed tracer has no immutable state field inventory")
    if args.rom is None or not args.rom.is_file():
        raise ContractError("--tracer requires the original ROM-only DMG fixture")
    with tempfile.TemporaryDirectory(prefix="gabbaboy-state-tracer-") as temp:
        temp_root = Path(temp)
        prefix = temp_root / "prefix"
        install = run([args.cmake, "--install", str(args.build_dir), "--prefix", str(prefix)], cwd=root)
        if install.returncode != 0:
            raise ContractError(f"temporary install failed ({install.returncode}): {install.stdout}{install.stderr}")
        installed_header = prefix / "include/gabbaboy/gabbaboy.h"
        installed_config = prefix / "lib/cmake/GabbaBoy/GabbaBoyConfig.cmake"
        if not installed_header.is_file() or not installed_config.is_file():
            raise ContractError("temporary install lacks the public header or exported package config")
        client_source = temp_root / "client.c"
        client_source.write_text(r'''#include <gabbaboy/gabbaboy.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define REQUIRE(x) do { if (!(x)) { fprintf(stderr, "tracer:%d: %s\\n", __LINE__, #x); return 1; } } while (0)

static uint8_t *read_file(const char *path, size_t *out_size) {
    FILE *file = fopen(path, "rb");
    if (!file || fseek(file, 0, SEEK_END) != 0) { if (file) fclose(file); return NULL; }
    long length = ftell(file);
    if (length < 0 || fseek(file, 0, SEEK_SET) != 0) { fclose(file); return NULL; }
    uint8_t *bytes = (uint8_t *)malloc((size_t)length);
    if (!bytes || fread(bytes, 1, (size_t)length, file) != (size_t)length) {
        free(bytes); fclose(file); return NULL;
    }
    fclose(file); *out_size = (size_t)length; return bytes;
}

static int same_run(gbb_run_result a, gbb_run_result b) {
    return a.consumed_half_dots == b.consumed_half_dots && a.reason == b.reason &&
           a.trace_count == b.trace_count && a.diagnostic_count == b.diagnostic_count &&
           a.lockup_pc == b.lockup_pc && a.lockup_opcode == b.lockup_opcode;
}

static int run_audio(gbb_instance *instance, uint64_t budget, gbb_audio_frame *frames,
                     size_t capacity, size_t *count, gbb_run_result *result) {
    *result = gbb_run_audio(instance, budget, frames, capacity, count);
    if (result->reason != GBB_STOP_BUDGET)
        fprintf(stderr, "run_audio budget=%llu reason=%d consumed=%llu frames=%zu\\n",
                (unsigned long long)budget, (int)result->reason,
                (unsigned long long)result->consumed_half_dots, *count);
    return result->reason == GBB_STOP_BUDGET && result->consumed_half_dots <= budget &&
           result->consumed_half_dots != 0u;
}

static int save_bytes(const gbb_instance *instance, uint8_t *bytes, size_t size) {
    return gbb_save_state(instance, bytes, size) == GBB_OK;
}

int main(int argc, char **argv) {
    REQUIRE(argc == 2);
    size_t rom_size = 0;
    uint8_t *rom = read_file(argv[1], &rom_size);
    REQUIRE(rom != NULL);
    gbb_instance *source = NULL, *target = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &source) == GBB_OK);
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &target) == GBB_OK);
    REQUIRE(gbb_load_rom(source, rom, rom_size) == GBB_OK);
    REQUIRE(gbb_load_rom(target, rom, rom_size) == GBB_OK);
    gbb_audio_frame prefix_a[2048], prefix_b[2048], future_a[2048], future_b[2048];
    size_t prefix_a_count = 0, prefix_b_count = 0, future_a_count = 0, future_b_count = 0;
    gbb_run_result prefix_a_result, prefix_b_result, future_a_result, future_b_result;
    REQUIRE(run_audio(source, 100000u, prefix_a, 2048u, &prefix_a_count, &prefix_a_result));
    REQUIRE(run_audio(target, 100000u, prefix_b, 2048u, &prefix_b_count, &prefix_b_result));
    REQUIRE(same_run(prefix_a_result, prefix_b_result));
    REQUIRE(prefix_a_count == prefix_b_count &&
            memcmp(prefix_a, prefix_b, prefix_a_count * sizeof(prefix_a[0])) == 0);
    REQUIRE(prefix_a_count != 0u && gbb_peek_ram(source, 0xC000u) == 0x5Au &&
            gbb_peek_ram(source, 0xC001u) == 0xA5u);
    size_t state_size = 0;
    REQUIRE(gbb_state_size(source, &state_size) == GBB_OK && state_size >= 64u);
    size_t target_size = 0;
    REQUIRE(gbb_state_size(target, &target_size) == GBB_OK && target_size == state_size);
    uint8_t *snapshot = (uint8_t *)malloc(state_size);
    uint8_t *expected = (uint8_t *)malloc(state_size);
    uint8_t *actual = (uint8_t *)malloc(state_size);
    REQUIRE(snapshot && expected && actual);
    REQUIRE(save_bytes(source, snapshot, state_size));
    REQUIRE(run_audio(source, 200000u, future_a, 2048u, &future_a_count, &future_a_result));
    REQUIRE(save_bytes(source, expected, state_size));
    REQUIRE(run_audio(target, 200000u, future_b, 2048u, &future_b_count, &future_b_result));
    REQUIRE(same_run(future_a_result, future_b_result));
    REQUIRE(future_a_count == future_b_count &&
            memcmp(future_a, future_b, future_a_count * sizeof(future_a[0])) == 0);
    REQUIRE(save_bytes(target, actual, state_size) && memcmp(expected, actual, state_size) == 0);

    REQUIRE(gbb_reset(target) == GBB_OK);
    REQUIRE(gbb_load_state(target, snapshot, state_size) == GBB_OK);
    REQUIRE(run_audio(target, 200000u, future_b, 2048u, &future_b_count, &future_b_result));
    REQUIRE(same_run(future_a_result, future_b_result));
    REQUIRE(future_a_count == future_b_count &&
            memcmp(future_a, future_b, future_a_count * sizeof(future_a[0])) == 0);
    REQUIRE(save_bytes(target, actual, state_size) && memcmp(expected, actual, state_size) == 0);
    printf("installed state tracer pass state_bytes=%zu prefix_audio=%zu future_audio=%zu\\n",
           state_size, prefix_a_count, future_a_count);
    free(snapshot); free(expected); free(actual); free(rom);
    gbb_destroy(source); gbb_destroy(target);
    return 0;
}
''')
        cmake_lists = temp_root / "CMakeLists.txt"
        cmake_lists.write_text(
            "cmake_minimum_required(VERSION 3.25)\n"
            "project(GabbaBoyInstalledStateTracer LANGUAGES C)\n"
            "find_package(GabbaBoy CONFIG REQUIRED)\n"
            "add_executable(state_tracer_client client.c)\n"
            "target_link_libraries(state_tracer_client PRIVATE GabbaBoy::core)\n"
            "target_compile_features(state_tracer_client PRIVATE c_std_17)\n"
            "set_target_properties(state_tracer_client PROPERTIES C_EXTENSIONS OFF)\n"
        )
        build_dir = temp_root / "client-build"
        configure_cmd = [args.cmake, "-S", str(temp_root), "-B", str(build_dir),
                         "-DCMAKE_PREFIX_PATH=" + str(prefix),
                         "-DCMAKE_C_COMPILER=" + args.cc]
        if args.generator:
            configure_cmd.extend(["-G", args.generator])
        configured = run(configure_cmd, cwd=root)
        if configured.returncode != 0:
            raise ContractError(f"installed client configure failed ({configured.returncode}): {configured.stdout}{configured.stderr}")
        built = run([args.cmake, "--build", str(build_dir)], cwd=root)
        if built.returncode != 0:
            raise ContractError(f"installed client build failed ({built.returncode}): {built.stdout}{built.stderr}")
        exe = build_dir / "state_tracer_client"
        if os.name == "nt":
            exe = exe.with_suffix(".exe")
        traced = run([str(exe), str(args.rom.resolve())], cwd=root)
        if traced.returncode != 0:
            raise ContractError(f"installed continuation tracer failed ({traced.returncode}): {traced.stdout}{traced.stderr}")
        print(f"state installed tracer pass source={args.rev} receipt={receipt_path.relative_to(root)} output={traced.stdout.strip()}")


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
    parser.add_argument("--format-contract", action="store_true")
    parser.add_argument("--tracer", action="store_true")
    parser.add_argument("--control", choices=("inventory", "globals", "all"), default="all")
    parser.add_argument("--rev", required=False)
    parser.add_argument("--library", type=Path)
    parser.add_argument("--build-dir", type=Path, default=Path("build"))
    parser.add_argument("--output", type=Path, default=Path("build/state-precodec-proof.json"))
    parser.add_argument("--version-module", type=Path)
    parser.add_argument("--api", type=Path)
    parser.add_argument("--rom", type=Path)
    parser.add_argument("--cmake", default="cmake")
    parser.add_argument("--nm", default=os.environ.get("CMAKE_NM", "nm"))
    parser.add_argument("--cc", default=os.environ.get("CC", "cc"))
    parser.add_argument("--generator", default="")
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
        if args.format_contract:
            run_format_contract(args, root, core, header)
            return 0
        if args.tracer:
            run_tracer(args, root, core, header)
            return 0
        raise ContractError("select --inventory, --globals, --self-test, --precodec or --tracer")
    except (ContractError, OSError) as error:
        print(f"state contract failure: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
