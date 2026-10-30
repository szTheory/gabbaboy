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
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


class ContractError(Exception):
    pass


def run(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)


def parse_cmake_cache_text(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in text.splitlines():
        if line.startswith(("#", "//")):
            continue
        match = re.match(r"^([^:#]+):[^=]+=([^\r\n]*)$", line)
        if match:
            values[match.group(1)] = match.group(2)
    return values


def read_cmake_cache(build_dir: Path) -> dict[str, str]:
    cache = build_dir / "CMakeCache.txt"
    if not cache.is_file():
        raise ContractError(f"configured CMake cache is missing: {cache}")
    return parse_cmake_cache_text(cache.read_text(encoding="utf-8", errors="replace"))


def cmake_bool(value: str, name: str) -> bool:
    normalized = value.strip().upper()
    if normalized in {"ON", "TRUE", "YES", "Y", "1"}:
        return True
    if normalized in {"OFF", "FALSE", "NO", "N", "0", ""}:
        return False
    raise ContractError(f"CMake cache option {name} has invalid boolean value: {value!r}")


def cmake_executable_suffix(cache: dict[str, str], *, host_is_windows: bool | None = None) -> str:
    if "CMAKE_EXECUTABLE_SUFFIX" in cache:
        return cache["CMAKE_EXECUTABLE_SUFFIX"]
    system_name = cache.get("CMAKE_SYSTEM_NAME", "").strip().lower()
    windows_host = os.name == "nt" if host_is_windows is None else host_is_windows
    return ".exe" if system_name.startswith("windows") or windows_host else ""


def _target_paths(build_dir: Path, relative_paths: list[Path], configuration: str) -> list[Path]:
    candidates: list[Path] = []
    for relative in relative_paths:
        candidates.append(build_dir / relative.parent / configuration / relative.name)
        candidates.append(build_dir / configuration / relative)
    return candidates


def resolve_cmake_artifact(build_dir: Path, relative_paths: list[Path], cache: dict[str, str],
                           *, configuration: str = "", label: str) -> tuple[Path, str]:
    """Find an artifact from a single- or multi-configuration CMake build."""
    configurations = [item.strip() for item in cache.get("CMAKE_CONFIGURATION_TYPES", "").split(";")
                     if item.strip()]
    if not configurations:
        candidates = [build_dir / relative for relative in relative_paths]
        found = next((candidate for candidate in candidates if candidate.is_file()), None)
        if found is None:
            raise ContractError(f"{label} is missing; checked: {', '.join(map(str, candidates))}")
        return found, ""

    selected = configuration.strip() or os.environ.get("CTEST_CONFIGURATION_TYPE", "").strip()
    if selected:
        if selected not in configurations:
            raise ContractError(
                f"CMake configuration {selected!r} is not in CMAKE_CONFIGURATION_TYPES: "
                f"{', '.join(configurations)}")
        candidates = _target_paths(build_dir, relative_paths, selected)
        found = next((candidate for candidate in candidates if candidate.is_file()), None)
        if found is not None:
            return found, selected
        # A multi-config project may explicitly set an output directory that omits
        # the configuration component. Honor it only after checking the selected
        # configuration-specific locations.
        direct = [build_dir / relative for relative in relative_paths]
        found = next((candidate for candidate in direct if candidate.is_file()), None)
        if found is not None:
            return found, selected
        raise ContractError(f"{label} for configuration {selected} is missing; checked: "
                            f"{', '.join(map(str, candidates + direct))}")

    matches: list[tuple[Path, str]] = []
    for candidate_config in configurations:
        candidates = _target_paths(build_dir, relative_paths, candidate_config)
        found = next((candidate for candidate in candidates if candidate.is_file()), None)
        if found is not None:
            matches.append((found, candidate_config))
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise ContractError(f"{label} exists in multiple configurations; pass --configuration: "
                            f"{', '.join(config for _path, config in matches)}")
    # Some projects explicitly override output directories in multi-config builds.
    candidates = [build_dir / relative for relative in relative_paths]
    found = next((candidate for candidate in candidates if candidate.is_file()), None)
    if found is not None:
        return found, ""
    checked = [str(path) for config in configurations
               for path in _target_paths(build_dir, relative_paths, config)] + list(map(str, candidates))
    raise ContractError(f"{label} is missing; checked: {', '.join(checked)}")


def installed_consumer_link_options(cache: dict[str, str],
                                    configured_options: str | None = None) -> str:
    """Match the package consumer tests: link sanitizer runtimes when the core was instrumented."""
    if configured_options and configured_options.strip():
        return configured_options.strip()
    if cmake_bool(cache.get("GABBABOY_ENABLE_SANITIZERS", "OFF"), "GABBABOY_ENABLE_SANITIZERS"):
        return "-fsanitize=address,undefined"
    return ""


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
    match = re.search(
        r"STATE_FIELD_TREATMENT\s*\[\s*\]\s*(?:GBB_MAYBE_UNUSED\s*)?=\s*\{(.*?)\};",
        core, re.S)
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


def parse_census_rows(text: str, *, source: str) -> list[tuple[int, str, int, int, int, str]]:
    rows: list[tuple[int, str, int, int, int, str]] = []
    for line in text.splitlines():
        if line.startswith("|"):
            columns = [column.strip() for column in line.strip().strip("|").split("|")]
        elif source == "state_record_field" and "|" in line:
            columns = [column.strip() for column in line.split("|")]
        else:
            continue
        if len(columns) != 6 or not columns[0].isdigit():
            continue
        try:
            order = int(columns[0])
            path = columns[1].strip("`")
            offset, count, width = int(columns[2]), int(columns[3]), int(columns[4])
        except ValueError as error:
            raise ContractError(f"unparsed {source} field census row: {line}") from error
        rows.append((order, path, offset, count, width, columns[5]))
    if len(rows) != 198:
        raise ContractError(f"{source} field census must have 198 data rows, found {len(rows)}")
    if [row[0] for row in rows] != list(range(198)):
        raise ContractError(f"{source} field census order must be consecutive from zero")
    if len({row[1] for row in rows}) != len(rows):
        raise ContractError(f"{source} field census contains duplicate qualified ids")
    return rows


def verify_field_census_document(document: str, executable_output: str) -> None:
    marker = "## Field census and accepted domains"
    start = document.find(marker)
    if start < 0:
        raise ContractError("state-format.md is missing the field census section")
    end = document.find("\n## ", start + len(marker))
    section = document[start:] if end < 0 else document[start:end]
    required_header = "| Order | Qualified id | Offset | Max count | Width | Treatment |"
    if required_header not in section:
        raise ContractError("state-format.md field census has the wrong column contract")
    documented = parse_census_rows(section, source="documented")
    emitted = parse_census_rows(executable_output, source="state_record_field")
    if documented != emitted:
        mismatch = next((index for index, pair in enumerate(zip(documented, emitted))
                         if pair[0] != pair[1]), None)
        if mismatch is None:
            mismatch = min(len(documented), len(emitted))
        expected = documented[mismatch] if mismatch < len(documented) else "<missing>"
        actual = emitted[mismatch] if mismatch < len(emitted) else "<missing>"
        raise ContractError(f"documented field census differs at row {mismatch}: document={expected}, executable={actual}")


def field_census_self_test() -> None:
    rows = [(index, f"field_{index}", index * 4, 1, 4, "serialize")
            for index in range(198)]
    def render(items: list[tuple[int, str, int, int, int, str]]) -> str:
        return "\n".join(f"| {order} | `{path}` | {offset} | {count} | {width} | {treatment} |"
                         for order, path, offset, count, width, treatment in items)
    document = "## Field census and accepted domains\n\n" \
               "| Order | Qualified id | Offset | Max count | Width | Treatment |\n" \
               "|---:|---|---:|---:|---:|---|\n" + render(rows)
    verify_field_census_document(document, render(rows))
    bad_width = list(rows)
    bad_width[93] = (*bad_width[93][:4], 8, bad_width[93][5])
    try:
        verify_field_census_document(document, render(bad_width))
    except ContractError as error:
        if "differs at row 93" not in str(error):
            raise ContractError(f"wrong census width-control diagnostic: {error}") from error
    else:
        raise ContractError("field census width negative control survived")
    omitted = render(rows[:-1])
    try:
        verify_field_census_document(document, omitted)
    except ContractError as error:
        if "must have 198 data rows" not in str(error):
            raise ContractError(f"wrong census omission-control diagnostic: {error}") from error
    else:
        raise ContractError("field census omission negative control survived")


def run_field_census(args: argparse.Namespace, root: Path, core: str) -> None:
    live_sources = (
        ("src/core/gabbaboy.c", core),
        ("tests/test_state_codec.c", git_show(root, args.rev, "tests/test_state_codec.c")),
        ("tests/CMakeLists.txt", git_show(root, args.rev, "tests/CMakeLists.txt")),
    )
    for relative, immutable in live_sources:
        path = root / relative
        if not path.is_file() or path.read_text() != immutable:
            raise ContractError(f"live {relative} differs from immutable --rev")
    document = git_show(root, args.rev, "docs/state-format.md")
    if (root / "docs/state-format.md").read_text() != document:
        raise ContractError("live docs/state-format.md differs from immutable --rev")
    if args.census_exe is None or not args.census_exe.is_file():
        raise ContractError("--field-census requires --census-exe PATH")
    emitted = run([str(args.census_exe), "state_field_census"], cwd=root)
    if emitted.returncode != 0:
        raise ContractError(f"immutable state census executable failed ({emitted.returncode}): {emitted.stdout}{emitted.stderr}")
    verify_field_census_document(document, emitted.stdout)
    print(f"state field census pass source={args.rev} rows=198 executable_sha256={sha256_file(args.census_exe)}")


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


def objdump_symbol_records(objdump_text: str) -> list[dict[str, str]]:
    """Read object symbols with their section and object-file provenance.

    GNU and LLVM objdump use the same symbol-table shape for ELF and COFF. LLVM's
    Mach-O output also names the segment and section on each symbol row. Keeping
    those coordinates is necessary: nm's one-letter ELF classes collapse
    `.data.rel.ro` into D even for compiler-emitted const relocation tables.
    """
    records: list[dict[str, str]] = []
    current_object = "<object>"
    current_format = ""
    in_symbol_table = False
    in_sections = False
    section_names: dict[int, str] = {}
    for line in objdump_text.splitlines():
        format_match = re.match(r"^(.*?):\s+file format\s+(\S+)", line.strip())
        if format_match:
            current_object = format_match.group(1)
            current_format = format_match.group(2).lower()
            in_symbol_table = False
            in_sections = False
            section_names = {}
            continue
        if line.strip() == "Sections:":
            in_sections = True
            in_symbol_table = False
            continue
        if line.strip() == "SYMBOL TABLE:":
            in_symbol_table = True
            in_sections = False
            continue
        if in_sections:
            section_match = re.match(r"^\s*(\d+)\s+(\S+)\s+[0-9A-Fa-f]{4,}\s", line)
            if section_match:
                index = int(section_match.group(1))
                if current_format.startswith(("coff", "pe-", "pei-")):
                    # LLVM COFF and GNU BFD PE/PEI section tables are zero-based;
                    # symbol section numbers are one-based.
                    index += 1
                section_names[index] = section_match.group(2)
            continue
        if not in_symbol_table:
            continue
        coff_match = re.match(
            r"^\[\s*\d+\]\(sec\s+(-?\d+)\).*?\(ty\s+(\d+)\).*?\s(\S+)\s*$", line)
        if coff_match:
            section_index, symbol_type, symbol = (int(coff_match.group(1)),
                                                   int(coff_match.group(2)),
                                                   coff_match.group(3))
            section = section_names.get(section_index)
            if section_index <= 0 or section is None or symbol_type != 0 or symbol == section:
                continue
            records.append({"object": current_object, "section": section, "symbol": symbol,
                            "kind": "object", "address": ""})
            continue
        parts = line.split()
        if len(parts) < 3 or not re.fullmatch(r"[0-9A-Fa-f]+", parts[0]):
            continue
        section_index = next((index for index, token in enumerate(parts[1:], start=1)
                              if token in {"*COM*", "*ABS*", "*UND*", "asan_globals", "asan_liveness"} or
                              token.startswith(".") or
                              re.fullmatch(r"__[A-Za-z0-9_$]+,__?[A-Za-z0-9_$.-]+", token)), None)
        if section_index is None or section_index == len(parts) - 1:
            continue
        section = parts[section_index]
        symbol = parts[-1]
        symbol_flags = " ".join(parts[1:section_index])
        if section == "*UND*" or "F" in symbol_flags.split():
            continue
        if symbol == section:
            # Section symbols (for example, `.data`) are not file-scope objects.
            if is_sanitizer_metadata_section(section):
                records.append({"object": current_object, "section": section, "symbol": symbol,
                                "kind": "section"})
            continue
        if section != "*COM*" and "O" not in symbol_flags.split() and \
                not is_writable_tls_section(section):
            continue
        records.append({"object": current_object, "section": section, "symbol": symbol,
                        "kind": "common" if section == "*COM*" else "object",
                        "address": parts[0]})
    return records


def is_writable_tls_section(section: str) -> bool:
    lowered = section.lower()
    if "," in lowered:
        segment, subsection = (item.strip("_") for item in lowered.split(",", 1))
        return segment in {"data", "data_const"} and subsection in {
            "thread_data", "thread_bss", "tdata", "tbss"
        }
    return bool(re.fullmatch(r"\.(?:tdata|tbss|tcommon|tls)(?:[.$].*)?", lowered) or
                lowered.startswith(".gnu.linkonce.t."))


def is_sanitizer_metadata_section(section: str) -> bool:
    lowered = section.lower()
    return ("asan_globals" in lowered or "asan_liveness" in lowered or
            lowered.startswith(".asan$") or lowered.startswith("asan$"))


def is_readonly_relocation_section(section: str) -> bool:
    lowered = section.lower()
    if "," in lowered:
        segment, subsection = lowered.split(",", 1)
        segment = segment.strip("_")
        subsection = subsection.strip("_")
        return segment in {"data", "data_const"} and subsection == "const"
    return lowered == ".data.rel.ro" or lowered.startswith(".data.rel.ro.")


def is_known_readonly_section(section: str) -> bool:
    lowered = section.lower()
    if "," in lowered:
        segment, _ = lowered.split(",", 1)
        return segment.strip("_") in {"text", "text_const", "data_const", "const", "ld"}
    return lowered.startswith((
        ".rodata", ".rdata", ".text", ".debug", ".zdebug", ".eh_frame", ".note",
        ".comment", ".llvm", ".stab", ".init_array", ".fini_array", ".CRT$",
        ".pdata", ".xdata", ".drectve", ".ARM.attributes", ".gnu.attributes",
    ))


def writable_symbols(objdump_text: str) -> list[str]:
    records = objdump_symbol_records(objdump_text)
    sanitizer_objects = {record["object"] for record in records
                         if is_sanitizer_metadata_section(record["section"])}
    named_symbols = {(record["object"], record["section"], record.get("address"))
                     for record in records if record["kind"] == "object" and
                     not re.fullmatch(r"ltmp[0-9]+", record["symbol"])}
    writable: list[str] = []
    for record in records:
        section = record["section"]
        symbol = record["symbol"]
        lowered = section.lower()
        if record["kind"] == "section":
            continue
        if "," in section and re.fullmatch(r"ltmp[0-9]+", symbol) and \
                (record["object"], section, record.get("address")) in named_symbols:
            # LLVM's Mach-O assembler emits local ltmp labels beside the named
            # object at the same location; they are not separate C globals.
            continue
        if is_sanitizer_metadata_section(section):
            continue
        normalized_symbol = symbol.strip("_").lower()
        if record["object"] in sanitizer_objects and (
                normalized_symbol == "asan_globals_registered" or
                normalized_symbol.startswith(("asan_global_", "asan_binder_", "odr_asan_gen_"))):
            # These exact names are emitted into a unit that carries the
            # compiler's dedicated ASan metadata section. The structural section
            # requirement prevents a user global with a coincidental name from
            # being exempted in an ordinary object.
            continue
        if record["kind"] == "common":
            writable.append(symbol)
            continue
        if is_readonly_relocation_section(section) or is_known_readonly_section(section):
            continue
        if "," in lowered:
            segment, subsection = (item.strip("_") for item in lowered.split(",", 1))
            if segment == "data" and subsection in {"mod_init_func", "mod_term_func"}:
                continue
            if segment == "data" and subsection in {
                "data", "bss", "common", "thread_data", "thread_bss", "tdata", "tbss"
            }:
                writable.append(symbol)
            elif segment == "data_const" and subsection in {"data", "bss", "thread_data", "thread_bss"}:
                writable.append(symbol)
            elif segment in {"data", "data_const"}:
                # Unknown allocated data sections fail closed until classified.
                writable.append(symbol)
            continue
        if re.fullmatch(r"\.(?:data|bss|sdata|sbss|tdata|tbss|tcommon|tls|common)(?:\..*)?", lowered) or \
                lowered.startswith((".gnu.linkonce.d.", ".gnu.linkonce.b.", ".tls$")):
            writable.append(symbol)
        elif not is_known_readonly_section(section):
            # An object symbol in an unrecognized section is not silently treated
            # as immutable. This also catches toolchain-specific writable sections.
            writable.append(symbol)
    return sorted(set(writable))


def verify_object_symbols(objdump: str, library: Path) -> dict[str, object]:
    if not library.is_file():
        raise ContractError(f"core library does not exist: {library}")
    result = run([objdump, "-h", "-t", str(library)])
    if result.returncode != 0:
        raise ContractError(f"objdump could not inspect {library}: {result.stderr.strip()}")
    if "file format" not in result.stdout or "SYMBOL TABLE:" not in result.stdout:
        raise ContractError(f"objdump did not provide object format and symbol-table evidence for {library}")
    if not objdump_symbol_records(result.stdout):
        raise ContractError(f"objdump reported no object symbols for {library}")
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
    decorated_treatments = (
        'static const state_field_treatment_rule STATE_FIELD_TREATMENT[] '
        'GBB_MAYBE_UNUSED = { { "keep", STATE_TREAT_SERIALIZE, "explicit" } };')
    if parse_treatments(decorated_treatments) != [
            ("keep", "STATE_TREAT_SERIALIZE", "explicit")]:
        raise ContractError("decorated STATE_FIELD_TREATMENT positive control failed")
    try:
        parse_treatments("static const state_field_treatment_rule OTHER[] = {};\n")
    except ContractError as error:
        if "STATE_FIELD_TREATMENT table is missing" not in str(error):
            raise ContractError(f"wrong missing-treatment diagnostic: {error}") from error
    else:
        raise ContractError("missing STATE_FIELD_TREATMENT negative control survived")
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


def assert_symbol_control(label: str, objdump_text: str, expected: set[str]) -> None:
    actual = set(writable_symbols(objdump_text))
    if actual != expected:
        raise ContractError(f"{label} section classification mismatch: expected {sorted(expected)}, got {sorted(actual)}")


def objdump_format_controls_self_test() -> None:
    mach_o = """/tmp/core.o: file format mach-o arm64
SYMBOL TABLE:
0000000000000000 g O __DATA,__data _seed_external
0000000000000004 l O __DATA,__bss _seed_static
0000000000000008 l O __DATA,__thread_data _seed_tls
000000000000000c g O __DATA,__const _const_relocated_pointer
0000000000000010 l O __DATA,__asan_globals ___asan_global_seed
0000000000000014 l O __DATA,__asan_liveness ___asan_binder_seed
0000000000000018 *COM* 0000000000000004 .hidden ____asan_globals_registered
"""
    gnu_elf = """core.o: file format elf64-x86-64
SYMBOL TABLE:
0000000000000000 g O .data 0000000000000004 seed_external
0000000000000004 l O .bss 0000000000000004 seed_static
0000000000000008 g O .tdata 0000000000000004 seed_tls
000000000000000c l O .rodata 0000000000000008 const_table
0000000000000014 l O .data.rel.ro.local 0000000000000010 const_pointer_table
"""
    llvm_elf_asan = """core.o: file format elf64-x86-64
SYMBOL TABLE:
0000000000000000 g O .data 0000000000000004 seed_external
0000000000000004 l O .tbss 0000000000000004 seed_tls
0000000000000008 l O .data.rel.ro.STATE_FIELDS 0000000000000010 STATE_FIELDS
0000000000000018 l O .asan_globals 0000000000000020 __asan_global_seed
0000000000000038 l O .asan_liveness 0000000000000008 __asan_binder_seed
0000000000000040 *COM* 0000000000000004 ____asan_globals_registered
"""
    coff = """core.obj: file format pe-x86-64
SYMBOL TABLE:
00000000 g O .data 00000004 _seed_external
00000004 l O .bss 00000004 _seed_static
00000008 g O .tls$ 00000004 _seed_tls
0000000c l O .rdata$const 00000008 _const_relocated_pointer
00000014 l O .ASAN$GL 00000020 __asan_global_seed
"""
    llvm_coff = """core.obj: file format coff-x86-64

Sections:
  0 .text 00000010 0000000000000000 TEXT
  1 .data 00000008 0000000000000000 DATA
  2 .bss 00000004 0000000000000000 BSS
  3 .rdata 00000010 0000000000000000 DATA
  4 .tls$ 00000008 0000000000000000 DATA

SYMBOL TABLE:
[13](sec  1)(fl 0x00)(ty  20)(scl   2)(nx 0) 0x00000000 read_globals
[14](sec  2)(fl 0x00)(ty   0)(scl   3)(nx 0) 0x00000004 _seed_static
[15](sec  2)(fl 0x00)(ty   0)(scl   2)(nx 0) 0x00000000 _seed_external
[16](sec  3)(fl 0x00)(ty   0)(scl   2)(nx 0) 0x00000000 _seed_common
[17](sec  4)(fl 0x00)(ty   0)(scl   2)(nx 0) 0x00000000 _const_relocated_pointer
[18](sec  5)(fl 0x00)(ty   0)(scl   3)(nx 0) 0x00000000 _seed_tls
"""
    gnu_pei = """core.obj: file format pei-x86-64

Sections:
  0 .text 00000010 0000000000000000 0000000000000000 00000000 2**2
  1 .data 00000008 0000000000000000 0000000000000000 00000010 2**2
  2 .bss 00000004 0000000000000000 0000000000000000 00000018 2**2
  3 .rdata 00000010 0000000000000000 0000000000000000 0000001c 2**2
  4 .tls$ 00000008 0000000000000000 0000000000000000 0000002c 2**2

SYMBOL TABLE:
[  1](sec  1)(fl 0x00)(ty  20)(scl   2)(nx 0) 0x00000000 read_globals
[  2](sec  2)(fl 0x00)(ty   0)(scl   3)(nx 0) 0x00000004 _seed_static
[  3](sec  2)(fl 0x00)(ty   0)(scl   2)(nx 0) 0x00000000 _seed_external
[  4](sec  4)(fl 0x00)(ty   0)(scl   2)(nx 0) 0x00000000 _const_relocated_pointer
[  5](sec  5)(fl 0x00)(ty   0)(scl   3)(nx 0) 0x00000000 _seed_tls
"""
    sanitizer_name_lookalike = """core.o: file format elf64-x86-64
SYMBOL TABLE:
0000000000000000 *COM* 0000000000000004 ____asan_globals_registered
"""
    assert_symbol_control("Mach-O", mach_o, {"_seed_external", "_seed_static", "_seed_tls"})
    assert_symbol_control("GNU ELF", gnu_elf, {"seed_external", "seed_static", "seed_tls"})
    assert_symbol_control("LLVM ELF with ASan", llvm_elf_asan, {"seed_external", "seed_tls"})
    assert_symbol_control("COFF", coff, {"_seed_external", "_seed_static", "_seed_tls"})
    assert_symbol_control("LLVM COFF", llvm_coff,
                          {"_seed_static", "_seed_external", "_seed_common", "_seed_tls"})
    assert_symbol_control("GNU PEI", gnu_pei,
                          {"_seed_static", "_seed_external", "_seed_tls"})
    assert_symbol_control("ordinary sanitizer-name lookalike", sanitizer_name_lookalike,
                          {"____asan_globals_registered"})
    print("state object-section controls pass formats=Mach-O,GNU-ELF,LLVM-ELF,COFF,GNU-PEI const-relocations=accepted sanitizer-metadata=isolated")


def globals_self_test(objdump: str, cc: str) -> None:
    objdump_format_controls_self_test()
    with tempfile.TemporaryDirectory(prefix="gabbaboy-state-symbols-") as temp:
        root = Path(temp)
        source, obj = root / "globals.c", root / "globals.o"
        source.write_text(
            "int gbb_seed_global = 1; static volatile int gbb_seed_static = 3; "
            "_Thread_local int gbb_seed_tls = 4; const int gbb_seed_ro = 2; "
            "const int * const gbb_seed_ro_ptr = &gbb_seed_ro; "
            "int gbb_seed_read(void) { return gbb_seed_static + gbb_seed_tls; }\n")
        compile_result = run(shlex.split(cc) + ["-c", str(source), "-o", str(obj)])
        if compile_result.returncode != 0:
            raise ContractError(f"global negative-control compile failed: {compile_result.stderr.strip()}")
        inspect = run([objdump, "-h", "-t", str(obj)])
        if inspect.returncode != 0:
            raise ContractError(f"objdump global negative-control failed: {inspect.stderr.strip()}")
        symbols = writable_symbols(inspect.stdout)
        if not any("gbb_seed_global" in name for name in symbols):
            raise ContractError("object control missed the seeded external writable global")
        if not any("gbb_seed_static" in name for name in symbols):
            raise ContractError("object control missed the seeded file-static writable global")
        if not any("gbb_seed_tls" in name for name in symbols):
            raise ContractError("object control missed the seeded thread-local writable global")
        if any("gbb_seed_ro" in name for name in symbols):
            raise ContractError("object control misclassified immutable storage or const-pointer relocation")

        clang = shutil.which("clang")
        if clang:
            cross_obj = root / "globals-cross-elf.o"
            cross_compile = run([clang, "--target=x86_64-unknown-linux-gnu", "-c",
                                 str(source), "-o", str(cross_obj)])
            if cross_compile.returncode != 0:
                raise ContractError(f"cross-target ELF global control compile failed: {cross_compile.stderr.strip()}")
            cross_inspect = run([objdump, "-h", "-t", str(cross_obj)])
            if cross_inspect.returncode != 0:
                raise ContractError(f"cross-target ELF objdump control failed: {cross_inspect.stderr.strip()}")
            tls_line = next((line for line in cross_inspect.stdout.splitlines()
                             if "gbb_seed_tls" in line and ".tdata" in line), None)
            if tls_line is None:
                raise ContractError("cross-target ELF control did not emit the seeded TLS symbol in .tdata")
            tls_parts = tls_line.split()
            tls_section_index = tls_parts.index(".tdata")
            if "O" in tls_parts[1:tls_section_index]:
                raise ContractError("cross-target ELF TLS control no longer exercises a symbol row without O")
            cross_symbols = writable_symbols(cross_inspect.stdout)
            if not any("gbb_seed_tls" in name for name in cross_symbols):
                raise ContractError("object control missed cross-target TLS symbol without the O flag")

        asan_compile = run(shlex.split(cc) + ["-fsanitize=address", "-c", str(source), "-o", str(obj)])
        if asan_compile.returncode == 0:
            asan_inspect = run([objdump, "-h", "-t", str(obj)])
            if asan_inspect.returncode != 0:
                raise ContractError(f"objdump sanitizer control failed: {asan_inspect.stderr.strip()}")
            symbols = writable_symbols(asan_inspect.stdout)
            for expected in ("gbb_seed_global", "gbb_seed_static", "gbb_seed_tls"):
                if not any(expected in name for name in symbols):
                    raise ContractError(f"sanitizer object control missed writable source symbol {expected}")
            if any("asan_globals_registered" in name or "asan_global_" in name or
                   "asan_binder_" in name for name in symbols):
                raise ContractError("sanitizer compiler metadata was misclassified as core mutable storage")


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
        "`gbb_state_size` and `gbb_save_state` return `GBB_STATE_INVALID_CONTENT` for a live machine that breaks a state invariant; states produced by this emulator are not expected to.",
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
        pass
    else:
        raise ContractError("state documentation magic negative control survived")

    in_02_claim = (
        "`gbb_state_size` and `gbb_save_state` return `GBB_STATE_INVALID_CONTENT` for a live machine "
        "that breaks a state invariant; states produced by this emulator are not expected to."
    )
    mutant = state_format.replace(in_02_claim, "", 1)
    if mutant == state_format:
        raise ContractError("state documentation IN-02 mutant was not seeded")
    try:
        verify_state_documentation(mutant, cartridge_saves)
    except ContractError as error:
        if in_02_claim not in str(error):
            raise ContractError("state documentation IN-02 negative control rejected the wrong claim") from error
        return
    raise ContractError("state documentation IN-02 negative control survived")


def version_component_self_test(cmake: str, module: Path, root: Path, rev: str) -> None:
    if not module.is_file():
        raise ContractError(f"state release version helper is missing: {module}")
    with tempfile.TemporaryDirectory(prefix="gabbaboy-state-version-") as temp:
        control_root = Path(temp)
        escaped_module = str(module.resolve()).replace("\\", "\\\\").replace('"', '\\"')
        project = control_root / "CMakeLists.txt"
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
            result = run([cmake, "-S", str(control_root), "-B", str(control_root / ("valid-" + version.replace(".", "-"))),
                          f"-DGBB_VERSION_UNDER_TEST={version}"])
            expected_line = "state version parsed=" + version
            if result.returncode != 0 or expected_line not in result.stdout:
                raise ContractError(f"valid state version control failed for {version}: {result.stdout}{result.stderr}")
        for version in invalid:
            result = run([cmake, "-S", str(control_root), "-B", str(control_root / ("invalid-" + re.sub(r"[^A-Za-z0-9]+", "-", version))),
                          f"-DGBB_VERSION_UNDER_TEST={version}"])
            if result.returncode == 0 or "GabbaBoy state release version" not in result.stdout + result.stderr:
                raise ContractError(f"invalid state version control survived for {version}: {result.stdout}{result.stderr}")
        immutable_cmake = git_show(root, rev, "CMakeLists.txt")
        immutable_version = re.search(r"^project\(GabbaBoy VERSION ([^\s)]+)", immutable_cmake, re.M)
        if immutable_version is None or len(immutable_version.group(1).split(".")) != 3:
            raise ContractError("immutable CMakeLists.txt has no three-part GabbaBoy project version")
        release_version = immutable_version.group(1)
        cache = control_root / "project" / "CMakeCache.txt"
        cache.parent.mkdir()
        cache.write_text(f"CMAKE_PROJECT_VERSION:STATIC={release_version}\n")
        expected_triplet = tuple(release_version.split("."))
        if state_release_from_cmake_cache(cache, module, cmake, root, rev) != expected_triplet:
            raise ContractError("CMake cache release triplet control returned the wrong version")
        cache.write_text(f"CMAKE_PROJECT_VERSION:STATIC={release_version}.4\n")
        try:
            state_release_from_cmake_cache(cache, module, cmake, root, rev)
        except ContractError:
            pass
        else:
            raise ContractError("CMake cache invalid release version control survived")


def state_release_from_cmake_cache(cache: Path, module: Path, cmake: str,
                                   root: Path, rev: str) -> tuple[str, str, str]:
    if not cache.is_file():
        raise ContractError(f"CMake cache is missing: {cache}")
    if not module.is_file():
        raise ContractError(f"state release version helper is missing: {module}")
    immutable_cmake = git_show(root, rev, "CMakeLists.txt")
    immutable_version = re.search(r"^project\(GabbaBoy VERSION ([^\s)]+)", immutable_cmake, re.M)
    if immutable_version is None:
        raise ContractError("immutable CMakeLists.txt has no GabbaBoy project version")
    cache_text = cache.read_text(errors="replace")
    match = re.search(r"^CMAKE_PROJECT_VERSION:STATIC=(.*)$", cache_text, re.M)
    if match is None or not match.group(1):
        raise ContractError(f"CMake cache has no CMAKE_PROJECT_VERSION: {cache}")
    if match.group(1) != immutable_version.group(1):
        raise ContractError(
            f"CMake cache release version {match.group(1)} differs from immutable --rev {rev} "
            f"version {immutable_version.group(1)}")
    with tempfile.TemporaryDirectory(prefix="gabbaboy-state-cache-version-") as temp:
        root = Path(temp)
        project = root / "CMakeLists.txt"
        project.write_text(
            "cmake_minimum_required(VERSION 3.25)\n"
            "project(StateVersionCacheProbe NONE)\n"
            'include("${GBB_STATE_VERSION_MODULE}")\n'
            'gbb_parse_state_release_version("${GBB_PROJECT_VERSION_UNDER_TEST}" GBB_MAJOR GBB_MINOR GBB_PATCH)\n'
            'message(STATUS "GBB_STATE_RELEASE_TRIPLET=${GBB_MAJOR}.${GBB_MINOR}.${GBB_PATCH}")\n')
        result = run([cmake, "-S", str(root), "-B", str(root / "build"),
                      f"-DGBB_STATE_VERSION_MODULE={module.resolve()}",
                      f"-DGBB_PROJECT_VERSION_UNDER_TEST={match.group(1)}"])
        if result.returncode != 0:
            raise ContractError(
                f"CMake rejected source release version {match.group(1)} using StateVersion.cmake: "
                f"{result.stdout}{result.stderr}")
        parsed = re.search(r"GBB_STATE_RELEASE_TRIPLET=([0-9]+)\.([0-9]+)\.([0-9]+)", result.stdout)
        if parsed is None:
            raise ContractError("StateVersion.cmake did not report a validated release triplet")
        return parsed.group(1), parsed.group(2), parsed.group(3)


def run_format_contract(args: argparse.Namespace, root: Path, core: str, header: str) -> None:
    verify_public_state_contract(header, core)
    state_format = git_show(root, args.rev, "docs/state-format.md")
    cartridge_saves = git_show(root, args.rev, "docs/cartridge-and-saves.md")
    verify_state_documentation(state_format, cartridge_saves)
    verify_state_documentation_negative_control(state_format, cartridge_saves)
    if args.version_module is None or args.api is None or args.rom is None or args.cmake is None:
        raise ContractError("--format-contract requires --version-module, --api, --rom and --cmake")
    version_component_self_test(args.cmake, args.version_module, root, args.rev)
    if not args.api.is_file():
        raise ContractError(f"format proof executable is missing: {args.api}")
    result = run([str(args.api), "format_contract", str(args.rom)], cwd=root)
    if result.returncode != 0:
        raise ContractError(f"format proof executable failed ({result.returncode}): {result.stdout}{result.stderr}")
    print(f"state format contract pass source={args.rev} docs_control=pass version_controls=10 api={result.stdout.strip() or 'pass'}")


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
    cache_values = read_cmake_cache(args.build_dir)
    _api_path, build_configuration = resolve_cmake_artifact(
        args.build_dir,
        [Path("tests") / ("test_state_api" + cmake_executable_suffix(cache_values))],
        cache_values, configuration=args.configuration, label="pre-codec proof executable")
    with tempfile.TemporaryDirectory(prefix="gabbaboy-state-tracer-") as temp:
        temp_root = Path(temp)
        prefix = temp_root / "prefix"
        install_command = [args.cmake, "--install", str(args.build_dir), "--prefix", str(prefix)]
        if build_configuration:
            install_command.extend(["--config", build_configuration])
        install = run(install_command, cwd=root)
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
        link_options = installed_consumer_link_options(
            cache_values, os.environ.get("GBB_SANITIZER_LINK_OPTIONS"))
        if link_options:
            configure_cmd.append("-DCMAKE_EXE_LINKER_FLAGS=" + link_options)
        configured = run(configure_cmd, cwd=root)
        if configured.returncode != 0:
            raise ContractError(f"installed client configure failed ({configured.returncode}): {configured.stdout}{configured.stderr}")
        child_cache = read_cmake_cache(build_dir)
        build_command = [args.cmake, "--build", str(build_dir)]
        if build_configuration:
            build_command.extend(["--config", build_configuration])
        built = run(build_command, cwd=root)
        if built.returncode != 0:
            raise ContractError(f"installed client build failed ({built.returncode}): {built.stdout}{built.stderr}")
        exe, _client_configuration = resolve_cmake_artifact(
            build_dir,
            [Path("state_tracer_client" + cmake_executable_suffix(child_cache))],
            child_cache, configuration=build_configuration,
            label="installed tracer client executable")
        traced = run([str(exe), str(args.rom.resolve())], cwd=root)
        if traced.returncode != 0:
            raise ContractError(f"installed continuation tracer failed ({traced.returncode}): {traced.stdout}{traced.stderr}")
        receipt_label = (str(receipt_path.relative_to(root)) if receipt_path.is_relative_to(root)
                         else receipt_path.name)
        print(f"state installed tracer pass source={args.rev} receipt={receipt_label} output={traced.stdout.strip()}")


def run_precodec(args: argparse.Namespace, root: Path) -> None:
    core = git_show(root, args.rev, "src/core/gabbaboy.c")
    header = git_show(root, args.rev, "include/gabbaboy/gabbaboy.h")
    source_file = root / "src/core/gabbaboy.c"
    if not source_file.is_file() or source_file.read_text() != core:
        raise ContractError("live core source differs from the immutable --rev")
    verify_inventory(core, header)
    cache_values = read_cmake_cache(args.build_dir)
    library, build_configuration = resolve_cmake_artifact(
        args.build_dir,
        [Path("libgabbaboy_core.a"), Path("gabbaboy_core.lib")],
        cache_values, configuration=args.configuration, label="core static library")
    object_receipt = verify_object_symbols(args.objdump, library)
    api, build_configuration = resolve_cmake_artifact(
        args.build_dir,
        [Path("tests") / ("test_state_api" + cmake_executable_suffix(cache_values))],
        cache_values, configuration=build_configuration or args.configuration,
        label="proof executable")
    proof_results: dict[str, str] = {}
    for case in ("size_bound", "audio_bound"):
        result = run([str(api), case], cwd=root)
        if result.returncode != 0:
            raise ContractError(f"{case} proof executable failed ({result.returncode}): {result.stdout}{result.stderr}")
        proof_results[case] = result.stdout.strip() or "pass"
    self_test = run([sys.executable, str(root / "tests/scripts/verify-state-contract.py"),
                     "--self-test", "--control", "all", "--objdump", args.objdump, "--cc", args.cc], cwd=root)
    if self_test.returncode != 0:
        raise ContractError(f"inventory/global negative controls failed: {self_test.stdout}{self_test.stderr}")
    source_hash, descriptor_hash, input_hash = source_digest(root, args.rev)
    receipt = {
        "schema": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": args.rev,
        "core_source_sha256": source_hash,
        "descriptor_range_constants_sha256": descriptor_hash,
        "proof_input_sha256": input_hash,
        "proof_executable_sha256": sha256_file(api),
        "cmake_generator": cache_values.get("CMAKE_GENERATOR", "unknown"),
        "c_compiler": cache_values.get("CMAKE_C_COMPILER", "unknown"),
        "library": str(library.relative_to(root)) if library.is_relative_to(root) else library.name,
        "library_sha256": object_receipt["library_sha256"],
        "proof_results": proof_results,
        "negative_controls": "pass",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(f"state pre-codec proof pass source={args.rev} descriptors={descriptor_hash} executable={receipt['proof_executable_sha256']}")


def revision_controls_self_test(root: Path, cmake: str) -> None:
    script = Path(__file__).resolve()
    cases = (
        ([], "an immutable --rev is required"),
        (["--rev", "unknown"], "--rev must be a resolved immutable 40-hex commit"),
        (["--rev", "0" * 40], "git show "),
    )
    for revision_args, expected in cases:
        result = run([sys.executable, str(script), "--inventory", "--repo", str(root), *revision_args],
                     cwd=root)
        if result.returncode != 1 or expected not in result.stdout + result.stderr:
            raise ContractError(
                f"state evidence revision control did not reject {revision_args or ['missing --rev']}: "
                f"exit={result.returncode} output={result.stdout}{result.stderr}")
    with tempfile.TemporaryDirectory(prefix="gabbaboy-state-release-revision-") as temp:
        cache = Path(temp) / "CMakeCache.txt"
        cache.write_text("CMAKE_PROJECT_VERSION:STATIC=0.2.1\n")
        shared_args = ["--state-release-from-cache", str(cache), "--version-module",
                       str(root / "cmake/StateVersion.cmake"), "--cmake", cmake,
                       "--repo", str(root)]
        for revision_args, expected in cases:
            result = run([sys.executable, str(script), *shared_args, *revision_args], cwd=root)
            if result.returncode != 1 or expected not in result.stdout + result.stderr:
                raise ContractError(
                    f"release-version checker did not fail closed for {revision_args or ['missing --rev']}: "
                    f"exit={result.returncode} output={result.stdout}{result.stderr}")
    build_consumer_controls_self_test()
    print("state revision controls pass missing=refused unknown=refused missing_object=refused")


def build_consumer_controls_self_test() -> None:
    if cmake_executable_suffix({"CMAKE_SYSTEM_NAME": "Windows"}, host_is_windows=False) != ".exe":
        raise ContractError("Windows executable suffix control failed")
    with tempfile.TemporaryDirectory(prefix="gabbaboy-state-build-paths-") as temp:
        root = Path(temp)
        single = root / "single"
        single_api = single / "tests" / "test_state_api"
        single_api.parent.mkdir(parents=True)
        single_api.write_bytes(b"native executable fixture")
        single_cache = parse_cmake_cache_text(
            "CMAKE_BUILD_TYPE:STRING=Debug\nCMAKE_SYSTEM_NAME:STRING=Linux\n")
        resolved, configuration = resolve_cmake_artifact(
            single, [Path("tests/test_state_api")], single_cache, label="single-config control")
        if resolved != single_api or configuration:
            raise ContractError("single-config executable path control failed")

        multi = root / "multi"
        debug_api = multi / "tests" / "Debug" / "test_state_api.exe"
        debug_api.parent.mkdir(parents=True)
        debug_api.write_bytes(b"Debug executable fixture")
        multi_cache = parse_cmake_cache_text(
            "CMAKE_CONFIGURATION_TYPES:STRING=Debug;Release\nCMAKE_SYSTEM_NAME:STRING=Windows\n")
        resolved, configuration = resolve_cmake_artifact(
            multi, [Path("tests/test_state_api.exe")], multi_cache, label="multi-config control")
        if resolved != debug_api or configuration != "Debug":
            raise ContractError("unique multi-config executable lookup failed")
        release_api = multi / "tests" / "Release" / "test_state_api.exe"
        release_api.parent.mkdir(parents=True)
        release_api.write_bytes(b"Release executable fixture")
        try:
            resolve_cmake_artifact(
                multi, [Path("tests/test_state_api.exe")], multi_cache, label="ambiguous control")
        except ContractError as error:
            if "pass --configuration" not in str(error):
                raise ContractError(f"ambiguous configuration control reported the wrong error: {error}") from error
        else:
            raise ContractError("multi-config executable lookup silently selected one of two outputs")
        selected, configuration = resolve_cmake_artifact(
            multi, [Path("tests/test_state_api.exe")], multi_cache,
            configuration="Release", label="selected-config control")
        if selected != release_api or configuration != "Release":
            raise ContractError("explicit multi-config executable lookup failed")

        try:
            resolve_cmake_artifact(
                multi, [Path("tests/missing.exe")], multi_cache,
                configuration="Release", label="missing executable control")
        except ContractError as error:
            if "missing executable control for configuration Release is missing" not in str(error):
                raise ContractError(f"missing executable control reported the wrong error: {error}") from error
        else:
            raise ContractError("missing executable control was accepted")

    if installed_consumer_link_options({"GABBABOY_ENABLE_SANITIZERS": "OFF"}) != "":
        raise ContractError("non-sanitized consumer unexpectedly received sanitizer flags")
    expected_sanitizers = "-fsanitize=address,undefined"
    if installed_consumer_link_options({"GABBABOY_ENABLE_SANITIZERS": "ON"}) != expected_sanitizers:
        raise ContractError("sanitized consumer is missing configured sanitizer link flags")
    if installed_consumer_link_options(
            {"GABBABOY_ENABLE_SANITIZERS": "OFF"}, "-fsanitize=address,undefined") != expected_sanitizers:
        raise ContractError("explicit sanitizer link options were not propagated")
    try:
        installed_consumer_link_options({"GABBABOY_ENABLE_SANITIZERS": "maybe"})
    except ContractError as error:
        if "invalid boolean value" not in str(error):
            raise ContractError(f"invalid sanitizer cache control reported the wrong error: {error}") from error
    else:
        raise ContractError("invalid sanitizer cache value was accepted")
    print("state build consumer controls pass windows_suffix=resolved multi_config=selected ambiguity=refused sanitizer_link=propagated")


def verify_live_revision_file(relative: str, immutable: str, live: str) -> None:
    if live != immutable:
        raise ContractError(f"live {relative} differs from immutable --rev")


def purity_contract_self_test() -> None:
    verify_live_revision_file("self-test", "immutable source", "immutable source")
    try:
        verify_live_revision_file("self-test", "immutable source", "changed working tree")
    except ContractError as error:
        if "differs from immutable --rev" not in str(error):
            raise ContractError(f"purity revision negative control reported the wrong error: {error}") from error
    else:
        raise ContractError("purity working-tree mismatch negative control survived")
    print("state purity contract control pass working_tree_mismatch=refused")


def run_purity(args: argparse.Namespace, root: Path) -> None:
    if args.probe is None or not args.probe.is_file():
        raise ContractError("--purity requires --probe PATH")
    if not re.fullmatch(r"[0-9a-f]{40}", args.rev):
        raise ContractError("--rev must be a resolved immutable 40-hex commit")
    relatives = (
        "src/core/gabbaboy.c",
        "include/gabbaboy/gabbaboy.h",
        "tests/test_state_alloc.c",
        "tests/CMakeLists.txt",
        "tests/expected-tests.txt",
        "tests/scripts/verify-state-contract.py",
    )
    for relative in relatives:
        immutable = git_show(root, args.rev, relative)
        live_path = root / relative
        if not live_path.is_file():
            raise ContractError(f"live source file is missing: {relative}")
        verify_live_revision_file(relative, immutable, live_path.read_text())

    revision = run([str(args.probe), "--source-revision"], cwd=root)
    if revision.returncode != 0 or revision.stdout.strip() != f"source_revision={args.rev}":
        raise ContractError(
            f"purity probe revision does not match immutable --rev {args.rev}: "
            f"exit={revision.returncode} output={revision.stdout}{revision.stderr}")
    result = run([str(args.probe), "state_purity"], cwd=root)
    if result.returncode != 0:
        raise ContractError(
            f"immutable purity probe failed ({result.returncode}): {result.stdout}{result.stderr}")
    controls = run([str(args.probe), "state_purity_controls"], cwd=root)
    if controls.returncode != 0:
        raise ContractError(
            f"immutable purity probe controls failed ({controls.returncode}): "
            f"{controls.stdout}{controls.stderr}")
    print(f"state purity pass source={args.rev} probe_sha256={sha256_file(args.probe)} "
          f"result={result.stdout.strip()} controls={controls.stdout.strip()}")


def load_boundary_module():
    """The boundary facts live in state_boundary.py; the other modes of this checker never read planning files."""
    import importlib.util
    path = Path(__file__).resolve().parent / "state_boundary.py"
    spec = importlib.util.spec_from_file_location("gbb_state_boundary", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_boundary_mode(args: argparse.Namespace, root: Path) -> int:
    module = load_boundary_module()
    try:
        if args.self_test:
            return module.boundary_self_test(root, args.rev)
        result = module.run_boundary(root, args.rev)
    except module.ContractError as error:
        raise ContractError(str(error)) from None
    print("state boundary pass " + " ".join(f"{key}={value}" for key, value in result.items()))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", action="store_true")
    parser.add_argument("--field-census", action="store_true")
    parser.add_argument("--globals", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--precodec", action="store_true")
    parser.add_argument("--format-contract", action="store_true")
    parser.add_argument("--tracer", action="store_true")
    parser.add_argument("--purity", action="store_true")
    parser.add_argument("--boundary", action="store_true")
    parser.add_argument("--state-release-from-cache", type=Path)
    parser.add_argument("--control", choices=("inventory", "field-census", "globals", "revision", "purity", "all"), default="all")
    parser.add_argument("--rev", required=False)
    parser.add_argument("--library", type=Path)
    parser.add_argument("--build-dir", type=Path, default=Path("build"))
    parser.add_argument("--output", type=Path, default=Path("build/state-precodec-proof.json"))
    parser.add_argument("--version-module", type=Path)
    parser.add_argument("--api", type=Path)
    parser.add_argument("--census-exe", type=Path)
    parser.add_argument("--probe", type=Path)
    parser.add_argument("--rom", type=Path)
    parser.add_argument("--cmake", default="cmake")
    parser.add_argument("--objdump", default=os.environ.get("CMAKE_OBJDUMP", "objdump"))
    parser.add_argument("--cc", default=os.environ.get("CC", "cc"))
    parser.add_argument("--generator", default="")
    parser.add_argument("--configuration", default="")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.repo.resolve()
    try:
        if args.state_release_from_cache is not None:
            if args.rev is None:
                raise ContractError("an immutable --rev is required")
            if args.version_module is None:
                raise ContractError("--state-release-from-cache requires --version-module PATH")
            version = state_release_from_cmake_cache(args.state_release_from_cache,
                                                     args.version_module, args.cmake, root, args.rev)
            print(".".join(version))
            return 0
        if args.boundary:
            return run_boundary_mode(args, root)
        if args.self_test:
            if args.control in ("inventory", "all"):
                inventory_self_test()
            if args.control in ("field-census", "all"):
                field_census_self_test()
            if args.control in ("globals", "all"):
                globals_self_test(args.objdump, args.cc)
            if args.control in ("revision", "all"):
                revision_controls_self_test(root, args.cmake)
            if args.control in ("purity", "all"):
                purity_contract_self_test()
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
        if args.field_census:
            run_field_census(args, root, core)
            return 0
        if args.globals:
            if args.library is None:
                raise ContractError("--globals requires --library PATH")
            result = verify_object_symbols(args.objdump, args.library)
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
        if args.purity:
            run_purity(args, root)
            return 0
        raise ContractError("select --inventory, --field-census, --globals, --self-test, --precodec, --tracer or --purity")
    except (ContractError, OSError) as error:
        print(f"state contract failure: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
