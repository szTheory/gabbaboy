#!/usr/bin/env python3
"""Fail-closed admission check for the vendored Libbet fixture (GAME-01, gate G5).

Standard library only; run as `python3 -I`. The checks bind the committed ROM bytes, header,
rights manifest (one record per file in the frozen build closure), licence text and notices.
Nothing here fetches upstream or executes anything from a source tree.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import pathlib
import posixpath
import re
import stat
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
MANIFEST_PATH = "fixtures/libbet/manifest.json"
ROM_PATH = "fixtures/libbet/libbet.gb"

# D-01: the admitted image. The upstream commit is the source identity; the tag is mutable.
ROM_SHA256 = "3607412031c8287cf878299ce96e581e85b852dde703806343b95576fa3ff1a9"
ROM_SIZE = 32768
ROM_HEADER = {"title": "LIBBET", "cartridge_type": 0, "cgb_flag": 0x80, "sgb_flag": 3}
PINNED_COMMIT = "46a765a2c01701bffb8c0b7dd6e4be3a6b193090"
EVIDENCE_PREFIX = f"https://github.com/pinobatch/libbet/blob/{PINNED_COMMIT}/"

# D-04c: SHA-256 of the sorted closure_files joined with LF plus a trailing LF. Required CI has
# no Libbet source tree, so this constant is what notices a dropped closure entry there.
EXPECTED_CLOSURE_SHA256 = "5e8b363d75611d265a31de54da0cc46228548364dfc368adc50eebe1274d09ab"
D04C_NAMED = [
    "src/hardware.inc",
    "tilesets/Libbet.ec",
    "tilesets/Libbet.png",
    "tilesets/Libbet_title.png",
    "tilesets/bigdigits.png",
    "tilesets/floorborder-sgb.png",
    "tilesets/floorborder.png",
    "tilesets/floorpieces.png",
    "tilesets/roll32.png",
    "tilesets/sgbborder.png",
    "tilesets/vwf7_cp144p.png",
]

# D-08/D-09: WRAM addresses of the progress predicate and the ROM bytes that anchor them.
PREDICATE_ADDRESSES = {
    "cur_floor": "0xC57F",
    "attract_mode": "0xC580",
    "hw_capability": "0xC5A3",
    "cur_score": "0xC4ED",
    "cursor_y": "0xC4EB",
    "floor_width": "0xC4E8",
    "floor_height": "0xC4E9",
    "max_score": "0xC4EC",
}
PREDICATE_ANCHORS = {
    "cur_floor": ("0x155C", "AF EA 7F C5 E0 43 E0 42"),
    "attract_mode": ("0x153A", "E6 04 EA 80 C5"),
    "hw_capability": ("0x14FB", "FA A3 C5 1F 30"),
    "cur_score": ("0x15A6", "AF EA 92 C5 EA ED C4 EA 8D C5 EA 8E C5 EA 90 C5 3D"),
    "cursor_y": ("0x1680", "FA EB C4 3C 20"),
}

HEX64 = re.compile(r"[0-9a-f]{64}")
RUN_URL = re.compile(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/actions/runs/[0-9]+(?:/attempts/[0-9]+)?")
PLACEHOLDERS = {"", "unknown", "tbd", "todo", "n/a", "none"}
RECORD_FIELDS = ("path", "kind", "author", "licence", "evidence")
HOSTED_ABSENT_STATEMENT = "No hosted reproduction run URL exists yet"

BUILD_DIRS = ("src", "tilesets", "tools")
MAX_SOURCE_FILE = 1 << 20

GITATTRIBUTES_LINES = [
    "fixtures/libbet/libbet.gb -text",
    "fixtures/libbet/manifest.json text eol=lf",
    "fixtures/libbet/LICENSE.txt text eol=lf",
    "fixtures/libbet/SOURCES.md text eol=lf",
    "tests/acceptance/** text eol=lf",
    "tests/baseline/** text eol=lf",
]


def fail(token: str, detail: str | None = None) -> None:
    raise ValueError(token if detail is None else f"{token}: {detail}")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            fail("manifest-invalid", f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def reject_constant(name):
    fail("manifest-invalid", f"non-finite JSON constant {name}")


def parse_manifest(raw: bytes) -> dict:
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        fail("manifest-invalid", f"not valid UTF-8: {error}")
    try:
        data = json.loads(text, object_pairs_hook=unique_pairs, parse_constant=reject_constant)
    except json.JSONDecodeError as error:
        fail("manifest-invalid", str(error))
    if not isinstance(data, dict):
        fail("manifest-invalid", "top level is not an object")
    return data


def section(parent: dict, key: str, where: str) -> dict:
    value = parent.get(key)
    if not isinstance(value, dict):
        fail("manifest-invalid", f"{where}.{key} is missing or not an object")
    return value


def is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def closure_digest(paths) -> str:
    return sha256_hex(("\n".join(sorted(paths)) + "\n").encode("ascii"))


def check_record(record, expected_path: str) -> None:
    for field in RECORD_FIELDS:
        value = record.get(field)
        if not isinstance(value, str) or value.strip().lower() in PLACEHOLDERS:
            fail("embedded-asset-field-invalid", f"{expected_path} {field}")
    digest = record.get("sha256")
    if not isinstance(digest, str) or not HEX64.fullmatch(digest):
        fail("embedded-asset-field-invalid", f"{expected_path} sha256")
    if record["evidence"] != EVIDENCE_PREFIX + expected_path:
        fail("embedded-asset-field-invalid", f"{expected_path} evidence")


def verify_data(manifest: dict, rom: bytes, license_bytes: bytes) -> dict:
    """Check one parsed manifest against ROM and licence bytes; return a small summary."""
    if manifest.get("schema") != 1 or manifest.get("id") != "libbet":
        fail("manifest-invalid", "schema must be 1 and id must be libbet")
    rom_meta = section(manifest, "rom", "manifest")
    if rom_meta.get("path") != ROM_PATH:
        fail("manifest-invalid", f"rom.path must be {ROM_PATH}")
    header = section(rom_meta, "header", "rom")
    source = section(manifest, "source", "manifest")
    licence = section(manifest, "license", "manifest")
    credits = section(manifest, "credits", "manifest")
    korth = section(credits, "korth_permission", "credits")
    rights = section(manifest, "rights", "manifest")
    repro = section(manifest, "reproducibility", "manifest")
    if licence.get("spdx") != "Zlib" or licence.get("file") != "LICENSE.txt":
        fail("manifest-invalid", "license must be Zlib with file LICENSE.txt")

    # ROM identity: size, digest, header (each its own token).
    declared_size = rom_meta.get("size_bytes")
    if not is_int(declared_size) or declared_size != ROM_SIZE or len(rom) != ROM_SIZE:
        fail("rom-size-mismatch", f"declared={declared_size!r} actual={len(rom)} expected={ROM_SIZE}")
    declared_digest = rom_meta.get("sha256")
    actual_digest = sha256_hex(rom)
    if not isinstance(declared_digest, str) or not HEX64.fullmatch(declared_digest) \
            or declared_digest != actual_digest or actual_digest != ROM_SHA256:
        fail("rom-digest-mismatch", f"declared={declared_digest!r} actual={actual_digest}")
    if rom[0x134:0x13B] != b"LIBBET\x00":
        fail("rom-header-mismatch", "title bytes at 0x134..0x13A are not LIBBET")
    header_checks = (("title", "LIBBET", None), ("cartridge_type", rom[0x147], 0x147),
                     ("cgb_flag", rom[0x143], 0x143), ("sgb_flag", rom[0x146], 0x146))
    for key, actual, offset in header_checks:
        declared = header.get(key)
        if declared != actual or declared != ROM_HEADER[key] or (key != "title" and not is_int(declared)):
            fail("rom-header-mismatch", f"{key} declared={declared!r} rom={actual!r}")

    # Rights: embedded assets, one record per closure file.
    assets = rights.get("embedded_assets")
    if not isinstance(assets, list) or not assets:
        fail("embedded-assets-empty", "rights.embedded_assets is missing or empty")
    closure = rights.get("closure_files")
    if not isinstance(closure, list) or not closure or not all(isinstance(p, str) and p for p in closure):
        fail("manifest-invalid", "rights.closure_files must be a non-empty list of paths")
    records: dict[str, list] = {}
    for record in assets:
        if not isinstance(record, dict) or not isinstance(record.get("path"), str):
            fail("embedded-asset-field-invalid", "a record has no path")
        records.setdefault(record["path"], []).append(record)
    for path in closure:
        count = len(records.get(path, ()))
        if count == 0:
            fail("embedded-asset-missing", path)
        if count > 1:
            fail("embedded-asset-duplicate", path)
    for path in closure:
        check_record(records[path][0], path)

    if source.get("commit") != PINNED_COMMIT:
        fail("source-commit-mismatch", f"{source.get('commit')!r}")
    license_digest = licence.get("license_sha256")
    if not isinstance(license_digest, str) or not HEX64.fullmatch(license_digest) \
            or license_digest != sha256_hex(license_bytes):
        fail("license-digest-mismatch", f"declared={license_digest!r} actual={sha256_hex(license_bytes)}")
    if korth.get("classification") != "limitation":
        fail("korth-permission-misclassified", f"{korth.get('classification')!r}")
    excerpt = credits.get("readme_excerpt")
    if not isinstance(excerpt, str) or "Martin Korth" not in excerpt or "Damian Yerrick" not in excerpt \
            or not isinstance(korth.get("quote"), str) or not korth["quote"].strip():
        fail("manifest-invalid", "credits must carry the README excerpt and the Korth quote")

    url = repro.get("hosted_run_url")
    if url is not None and (not isinstance(url, str) or not RUN_URL.fullmatch(url)):
        fail("reproducibility-url-invalid", repr(url))
    statement, recipe = repro.get("statement"), repro.get("recipe")
    if not isinstance(statement, str) or not statement.strip() or not isinstance(recipe, str) or not recipe.strip():
        fail("manifest-invalid", "reproducibility statement and recipe are required")
    if url is None and HOSTED_ABSENT_STATEMENT not in statement:
        fail("reproducibility-claim-invalid", "no hosted run URL, so the statement must say none exists yet")

    note = manifest.get("scope_note")
    if not isinstance(note, str) or not note.strip():
        fail("scope-note-missing", "scope_note is missing or empty")
    for key in ("no_music", "outside_closure", "closure_derivation", "closure_exclusions"):
        if key not in rights:
            fail("manifest-invalid", f"rights.{key} is missing")
    if rights["no_music"] is not True or rights["outside_closure"] != ["07-biggar/", "hopesup/"]:
        fail("manifest-invalid", "rights must record no music and the two out-of-closure directories")

    check_predicates(manifest, rom)

    if len(set(closure)) != len(closure):
        fail("closure-digest-mismatch", "duplicate closure_files path")
    digest = closure_digest(closure)
    if digest != EXPECTED_CLOSURE_SHA256:
        fail("closure-digest-mismatch", f"closure_files sha256={digest}")
    for path in D04C_NAMED:
        if path not in records:
            fail("embedded-asset-missing", path)
    for path in sorted(records):
        if path not in set(closure):
            fail("embedded-asset-extra", path)
    exclusions = rights["closure_exclusions"]
    if not isinstance(exclusions, list) or not exclusions:
        fail("closure-exclusion-invalid", "closure_exclusions must be a non-empty list")
    for entry in exclusions:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str) \
                or not isinstance(entry.get("reason"), str) or not entry["reason"].strip():
            fail("closure-exclusion-invalid", "each exclusion needs a path and a reason")
        if entry["path"] in closure:
            fail("closure-exclusion-invalid", f"{entry['path']} is also in closure_files")
    return {"rom_sha256": actual_digest, "closure_files": len(closure), "embedded_assets": len(assets)}


def check_predicates(manifest: dict, rom: bytes) -> None:
    table = manifest.get("predicate_addresses")
    if not isinstance(table, dict):
        fail("predicate-addresses-invalid", "predicate_addresses is missing")
    for name, address in PREDICATE_ADDRESSES.items():
        entry = table.get(name)
        if not isinstance(entry, dict) or entry.get("address") != address \
                or not isinstance(entry.get("derivation"), str) or not entry["derivation"].strip():
            fail("predicate-addresses-invalid", name)
        anchor = entry.get("rom_anchor")
        expected = PREDICATE_ANCHORS.get(name)
        if expected is None:
            if anchor is not None:
                fail("predicate-addresses-invalid", f"{name} must not carry an anchor")
            continue
        if not isinstance(anchor, dict) or (anchor.get("offset"), anchor.get("bytes")) != expected:
            fail("predicate-anchor-mismatch", name)
        offset, hexbytes = int(expected[0], 16), bytes.fromhex(expected[1])
        if rom[offset:offset + len(hexbytes)] != hexbytes:
            fail("predicate-anchor-mismatch", f"{name} ROM bytes at {expected[0]}")


def read_inputs(manifest_path: pathlib.Path) -> tuple[bytes, dict, bytes, bytes]:
    try:
        raw = manifest_path.read_bytes()
    except OSError as error:
        fail("manifest-invalid", f"cannot read {manifest_path.name}: {error.strerror}")
    manifest = parse_manifest(raw)
    try:
        with open(ROOT / ROM_PATH, "rb") as handle:
            rom = handle.read(ROM_SIZE + 1)
    except OSError as error:
        fail("rom-missing", f"{ROM_PATH}: {error.strerror}")
    try:
        license_bytes = (ROOT / "fixtures/libbet/LICENSE.txt").read_bytes()
    except OSError as error:
        fail("license-digest-mismatch", f"cannot read LICENSE.txt: {error.strerror}")
    return raw, manifest, rom, license_bytes


# ---------------------------------------------------------------------------------------------
# Notices and attributes
# ---------------------------------------------------------------------------------------------

def check_notices_text(notices: str, attributes: str, manifest_raw: bytes, rom_sha: str, license_sha: str) -> None:
    rows = [line for line in notices.splitlines() if line.lstrip().startswith("|") and "fixtures/libbet" in line]
    if not rows:
        fail("notice-missing", "no THIRD_PARTY_NOTICES.md row names fixtures/libbet")
    row = rows[0]
    for label, needle in (("manifest sha256", sha256_hex(manifest_raw)), ("ROM sha256", rom_sha),
                          ("LICENSE.txt sha256", license_sha), ("zlib", "zlib"),
                          ("Damian Yerrick credit", "Damian Yerrick"), ("Martin Korth credit", "Martin Korth"),
                          ("CC0 note", "CC0-1.0")):
        if needle not in row:
            fail("notice-missing", f"Libbet row lacks {label}")
    if "separately listed Libbet fixture" not in notices:
        fail("notice-missing", "intro sentence does not separate the Libbet fixture from project-authored ROMs")
    present = {line.strip() for line in attributes.splitlines()}
    for line in GITATTRIBUTES_LINES:
        if line not in present:
            fail("attributes-missing", line)


def check_notices(manifest_raw: bytes, manifest: dict) -> None:
    try:
        notices = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
        attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        fail("notice-missing", f"cannot read notices or attributes: {error}")
    check_notices_text(notices, attributes, manifest_raw, manifest["rom"]["sha256"],
                       manifest["license"]["license_sha256"])


# ---------------------------------------------------------------------------------------------
# Redistribution guard: the ROM must not appear in an installed or packaged tree
# ---------------------------------------------------------------------------------------------

def scan_dir(directory: pathlib.Path) -> int:
    if not directory.is_dir():
        fail("scan-dir-empty", f"{directory.name} is not a directory")
    count = 0
    for current, dirs, files in os.walk(directory, followlinks=False):
        dirs.sort()
        for name in sorted(files) + dirs:
            path = pathlib.Path(current, name)
            relative = path.relative_to(directory).as_posix()
            if any("libbet" in part.lower() for part in relative.split("/")):
                fail("libbet-installed", relative)
        for name in sorted(files):
            path = pathlib.Path(current, name)
            relative = path.relative_to(directory).as_posix()
            info = os.lstat(path)
            count += 1
            # A symlink is hashed through its target; a file of any other size cannot match.
            target = os.stat(path) if stat.S_ISLNK(info.st_mode) and path.exists() else info
            if stat.S_ISREG(target.st_mode) and target.st_size == ROM_SIZE:
                with open(path, "rb") as handle:
                    if sha256_hex(handle.read(ROM_SIZE + 1)) == ROM_SHA256:
                        fail("libbet-installed", relative)
    if count == 0:
        fail("scan-dir-empty", f"{directory.name} contains no files")
    return count


# ---------------------------------------------------------------------------------------------
# Build-closure derivation (read-only: nothing in the tree is executed or followed)
# ---------------------------------------------------------------------------------------------

def read_tree(src_dir: pathlib.Path) -> dict[str, pathlib.Path]:
    """Return {relative posix path: path} for the makefile and every file under the build dirs."""
    files: dict[str, pathlib.Path] = {}
    makefile = src_dir / "makefile"
    if not makefile.is_file() or makefile.is_symlink():
        fail("source-tree-invalid", "makefile is missing or not a regular file")
    files["makefile"] = makefile
    for directory in BUILD_DIRS:
        base = src_dir / directory
        if not base.is_dir() or base.is_symlink():
            fail("source-tree-invalid", f"{directory}/ is missing or not a directory")
        for current, dirs, names in os.walk(base, followlinks=False):
            dirs.sort()
            for name in sorted(names):
                path = pathlib.Path(current, name)
                relative = path.relative_to(src_dir).as_posix()
                info = os.lstat(path)
                if not stat.S_ISREG(info.st_mode):
                    fail("source-tree-invalid", f"{relative} is not a regular file")
                if info.st_size > MAX_SOURCE_FILE:
                    fail("source-tree-invalid", f"{relative} exceeds 1 MiB")
                files[relative] = path
            for name in dirs:
                if os.path.islink(pathlib.Path(current, name)):
                    fail("source-tree-invalid", f"{pathlib.Path(current, name).relative_to(src_dir).as_posix()} is a symlink")
    if makefile.stat().st_size > MAX_SOURCE_FILE:
        fail("source-tree-invalid", "makefile exceeds 1 MiB")
    return files


def read_text(path: pathlib.Path) -> str:
    return path.read_bytes().decode("utf-8", errors="replace")


def strip_make_comment(line: str) -> str:
    out = []
    index = 0
    while index < len(line):
        char = line[index]
        if char == "\\" and index + 1 < len(line):
            out.append(line[index:index + 2])
            index += 2
            continue
        if char == "#":
            break
        out.append(char)
        index += 1
    return "".join(out)


def make_logical_lines(text: str) -> list[str]:
    """Join backslash continuations, then drop # comments."""
    logical, current = [], ""
    for raw in text.splitlines():
        if raw.endswith("\\"):
            current += raw[:-1] + " "
            continue
        logical.append(current + raw)
        current = ""
    if current:
        logical.append(current)
    return [strip_make_comment(line) for line in logical]


def make_words(line: str) -> list[str]:
    """Split on whitespace outside $(...) / ${...} so a function call is one word."""
    words, current, depth, index = [], [], 0, 0
    while index < len(line):
        char = line[index]
        if char == "$" and index + 1 < len(line) and line[index + 1] in "({":
            depth += 1
            current.append(char + line[index + 1])
            index += 2
            continue
        if depth and char in ")}":
            depth -= 1
        if char.isspace() and depth == 0:
            if current:
                words.append("".join(current))
                current = []
        else:
            current.append(char)
        index += 1
    if current:
        words.append("".join(current))
    return words


WILDCARD = re.compile(r"\$[({]\s*wildcard\s+([^)}]*)[)}]")
ASSIGNMENT = re.compile(r"[A-Za-z_][A-Za-z0-9_.]*\s*(?::|\+|\?|!|::)?=")
DIRECTIVE = re.compile(r"(?:ifdef|ifndef|ifeq|ifneq|else|endif|include|-include|sinclude|define|endef|export|override|vpath)\b")


def word_bounded(needle: str, token: str) -> bool:
    return re.search(r"(?<![A-Za-z0-9_])" + re.escape(needle) + r"(?![A-Za-z0-9_])", token) is not None


def split_rule(line: str):
    """Return (targets, prerequisites) for a rule line, else None."""
    if line.startswith("\t"):
        return None
    stripped = line.strip()
    if not stripped or ASSIGNMENT.match(stripped) or DIRECTIVE.match(stripped):
        return None
    depth = 0
    for index, char in enumerate(stripped):
        if char == "$" and index + 1 < len(stripped) and stripped[index + 1] in "({":
            depth += 1
        elif depth and char in ")}":
            depth -= 1
        elif char == ":" and depth == 0 and stripped[index + 1:index + 2] != "=":
            return make_words(stripped[:index]), make_words(stripped[index + 1:].split(";", 1)[0])
    return None


def include_targets(text: str) -> list[str]:
    targets = []
    pattern = re.compile(r'^\s*(?:[A-Za-z_.][\w.]*:{1,2}\s*)?(?i:include|incbin)\s+"([^"]*)"')
    for line in text.splitlines():
        match = pattern.match(line.split(";", 1)[0])
        if match:
            targets.append(match.group(1))
    return targets


def python_imports(text: str) -> list[str]:
    names = []
    for line in text.splitlines():
        match = re.match(r"\s*from\s+([A-Za-z_][\w.]*)\s+import\b", line)
        if match:
            names.append(match.group(1))
            continue
        match = re.match(r"\s*import\s+(.+?)\s*(?:#.*)?$", line)
        if match:
            for part in match.group(1).split(","):
                words = part.split()
                if words and re.fullmatch(r"[A-Za-z_][\w.]*", words[0]):
                    names.append(words[0])
    return names


def derive_closure(src_dir: pathlib.Path, declared: list[str], exclusions: list[str]) -> tuple[list[str], str]:
    tree = read_tree(src_dir)
    exclusion_set = set(exclusions)
    for path in exclusions:
        if path not in tree or path == "makefile":
            fail("closure-exclusion-invalid", f"{path} is not a file under src/, tilesets/ or tools/")

    make_lines = make_logical_lines(read_text(tree["makefile"]))
    globs: list[str] = []
    literal_tokens: list[str] = []
    rules = []
    for line in make_lines:
        for match in WILDCARD.finditer(line):
            globs.extend(match.group(1).split())
        literal_tokens.extend(WILDCARD.sub(" ", line).split())
        rule = split_rule(line)
        if rule is not None:
            rules.append(rule)

    src_texts = {path: read_text(file) for path, file in tree.items()
                 if path.startswith("src/") and path.endswith((".z80", ".inc"))}
    directive_targets = [(path, target) for path, text in sorted(src_texts.items())
                         for target in include_targets(text)]
    py_imports = {path: python_imports(read_text(file)) for path, file in sorted(tree.items())
                  if path.startswith("tools/") and path.endswith(".py") and path not in exclusion_set}

    for path in exclusions:
        base, stem = posixpath.basename(path), posixpath.splitext(posixpath.basename(path))[0]
        for token in literal_tokens:
            if any(word_bounded(needle, token) for needle in (path, base, stem)):
                fail("closure-exclusion-referenced", f"{path} (makefile token {token!r})")
        for pattern in globs:
            if fnmatch.fnmatchcase(path, pattern):
                fail("closure-exclusion-referenced", f"{path} (makefile glob {pattern!r})")
        for targets, prerequisites in rules:
            if "%" in prerequisites:
                for target in targets:
                    if "%" in target:
                        candidate = path + target.split("%", 1)[1]
                        if any(candidate in token for token in literal_tokens) \
                                or any(candidate == t or t.endswith("/" + candidate) for _, t in directive_targets):
                            fail("closure-exclusion-referenced", f"{path} (pattern rule expands to {candidate})")
        for tool, names in py_imports.items():
            if any(name == stem or name.split(".")[0] == stem for name in names):
                fail("closure-exclusion-referenced", f"{path} (imported by {tool})")
        for source, target in directive_targets:
            if target == path or posixpath.basename(target) == base:
                fail("closure-exclusion-referenced", f"{path} ({source} includes {target!r})")

    derived = sorted(path for path in tree if path not in exclusion_set)
    missing = sorted(set(derived) - set(declared))
    extra = sorted(set(declared) - set(derived))
    if missing or extra:
        fail("closure-derivation-mismatch", f"missing={','.join(missing) or '-'} extra={','.join(extra) or '-'}")

    derived_set = set(derived)
    for source, target in directive_targets:
        if target.startswith("obj/gb/") and ".." not in target.split("/"):
            continue
        if target.startswith("src/") and target in derived_set and ".." not in target.split("/"):
            continue
        fail("include-outside-closure", f"{source} -> {target}")
    for targets, prerequisites in rules:
        if not any(t == "$(title).gb" or t.startswith("obj/gb/") for t in targets):
            continue
        for word in prerequisites:
            if word.startswith(("$(", "${")):
                match = WILDCARD.fullmatch(word)
                if match and not all(g.startswith(BUILD_DIRS_PREFIX) and ".." not in g.split("/")
                                     for g in match.group(1).split()):
                    fail("prerequisite-outside-closure", word)
                continue
            if ".." in word.split("/") or word.startswith("/"):
                fail("prerequisite-outside-closure", word)
            if word.startswith(("obj/gb/",) + BUILD_DIRS_PREFIX) or word in derived_set:
                continue
            fail("prerequisite-outside-closure", word)
    return derived, closure_digest(derived)


BUILD_DIRS_PREFIX = tuple(f"{d}/" for d in BUILD_DIRS)


# ---------------------------------------------------------------------------------------------
# Self-test: every control must be rejected with its own token
# ---------------------------------------------------------------------------------------------

def expect(token: str, action, label: str) -> None:
    try:
        action()
    except ValueError as error:
        if not str(error).startswith(token):
            fail("self-test", f"{label}: expected {token}, got {error}")
        return
    fail("self-test", f"{label}: mutation was accepted")


def deepcopy(value):
    return json.loads(json.dumps(value))


def write_tree(root: pathlib.Path, files: dict[str, str | bytes]) -> None:
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))


SYNTHETIC_MAKEFILE = (
    "# tools/unused.py is named only in this comment, which is dropped\n"
    "title:=g\n"
    "objlist := a\n"
    "obj/gb/%.o: src/%.z80 src/hardware.inc src/global.inc\n"
    "\t${RGBASM} -h -o $@ $<\n"
    "$(title).gb: $(foreach o,$(objlist),obj/gb/$(o).o)\n"
    "\t$(RGBLINK) -o$@ $^\n"
    "obj/gb/pic.2bpp: tilesets/pic.png\n"
    "\t${RGBGFX} -o $@ $<\n"
    "%.pb16: tools/tool.py %\n"
    "\t$(PY) $^ $@\n"
    "obj/gb/a.o: obj/gb/pic.2bpp.pb16 \\\n"
    "  obj/gb/pic.2bpp\n"
    "obj/gb/local.z80: tools/tool.py $(wildcard src/*.z80)\n"
    "\t$(PY) $^ -o $@\n"
    "obj/gb/index.txt: makefile\n"
)
SYNTHETIC_FILES = {
    "makefile": SYNTHETIC_MAKEFILE,
    "src/a.z80": '; the word unused here is a comment\ninclude "src/hardware.inc"\ninclude "src/global.inc"\n'
                 'data: incbin "obj/gb/pic.2bpp.pb16"\n',
    "src/hardware.inc": "; hw\n",
    "src/global.inc": "; global\n",
    "tilesets/pic.png": b"\x89PNG\r\n",
    "tools/tool.py": '"""Docs: from its clipping rectangle at a position."""\nimport sys\nfrom os import path\n',
    "tools/unused.py": "import os\n",
}
SYNTHETIC_CLOSURE = ["makefile", "src/a.z80", "src/global.inc", "src/hardware.inc", "tilesets/pic.png", "tools/tool.py"]


def synthetic_variant(root: pathlib.Path, **changes) -> pathlib.Path:
    files = dict(SYNTHETIC_FILES)
    files.update(changes)
    write_tree(root, files)
    return root


def derive_self_test() -> None:
    exclusions = ["tools/unused.py"]
    with tempfile.TemporaryDirectory(prefix="gabbaboy-libbet-closure-") as temporary:
        base = pathlib.Path(temporary)
        # Positive: comment-only mentions of the exclusion stem and docstring prose never match.
        derived, digest = derive_closure(synthetic_variant(base / "ok"), SYNTHETIC_CLOSURE, exclusions)
        if derived != SYNTHETIC_CLOSURE or digest != closure_digest(SYNTHETIC_CLOSURE):
            fail("self-test", "synthetic closure was not derived as declared")
        # GAME-01 omission negative test: the declared list omits src/global.inc.
        omitted = [p for p in SYNTHETIC_CLOSURE if p != "src/global.inc"]
        try:
            derive_closure(base / "ok", omitted, exclusions)
        except ValueError as error:
            if not str(error).startswith("closure-derivation-mismatch") or "missing=src/global.inc" not in str(error):
                fail("self-test", f"omission reported wrongly: {error}")
        else:
            fail("self-test", "closure omission was accepted")
        extra = SYNTHETIC_CLOSURE + ["tools/ghost.py"]
        expect("closure-derivation-mismatch", lambda: derive_closure(base / "ok", extra, exclusions), "extra path")

        variants = {
            "recipe names the exclusion": ("closure-exclusion-referenced",
                {"makefile": SYNTHETIC_MAKEFILE + "obj/gb/x.o: obj/gb/y\n\t$(PY) tools/unused.py obj/gb/x\n"}),
            "wildcard glob covers the exclusion": ("closure-exclusion-referenced",
                {"makefile": SYNTHETIC_MAKEFILE + "obj/gb/w.z80: $(wildcard tools/*.py)\n"}),
            "bare % pattern expands to the exclusion": ("closure-exclusion-referenced",
                {"makefile": SYNTHETIC_MAKEFILE + "obj/gb/q.o: tools/unused.py.pb16\n"}),
            "a closure tool imports the exclusion": ("closure-exclusion-referenced",
                {"tools/tool.py": "import unused\n"}),
            "an include names the exclusion basename": ("closure-exclusion-referenced",
                {"src/a.z80": 'include "unused.py"\n'}),
            "include outside the closure": ("include-outside-closure",
                {"src/a.z80": 'include "src/missing.inc"\n'}),
            "prerequisite outside the closure": ("prerequisite-outside-closure",
                {"makefile": SYNTHETIC_MAKEFILE + "obj/gb/z.o: /etc/passwd\n"}),
        }
        for number, (label, (token, change)) in enumerate(variants.items()):
            tree = synthetic_variant(base / f"variant-{number}", **change)
            expect(token, lambda tree=tree: derive_closure(tree, SYNTHETIC_CLOSURE, exclusions), label)
        expect("source-tree-invalid", lambda: derive_closure(base / "empty-never-created", SYNTHETIC_CLOSURE, exclusions),
               "missing tree")


def scan_self_test(rom: bytes) -> None:
    with tempfile.TemporaryDirectory(prefix="gabbaboy-libbet-scan-") as temporary:
        base = pathlib.Path(temporary)
        clean = base / "clean"
        write_tree(clean, {"share/readme.txt": "hello\n", "bin/tool": b"\x00\x01"})
        if scan_dir(clean) != 2:
            fail("self-test", "clean tree was not scanned as two files")
        write_tree(base / "digest", {"share/payload.bin": rom})
        expect("libbet-installed", lambda: scan_dir(base / "digest"), "renamed ROM copy")
        write_tree(base / "named", {"share/Libbet-notes.txt": "x\n"})
        expect("libbet-installed", lambda: scan_dir(base / "named"), "libbet in a file name")
        write_tree(base / "dirname", {"share/libbet/readme.txt": "x\n"})
        expect("libbet-installed", lambda: scan_dir(base / "dirname"), "libbet in a directory name")
        (base / "empty").mkdir()
        expect("scan-dir-empty", lambda: scan_dir(base / "empty"), "empty directory")
        expect("scan-dir-empty", lambda: scan_dir(base / "missing"), "missing directory")


def notices_self_test(manifest_raw: bytes, manifest: dict) -> None:
    rom_sha, lic_sha = manifest["rom"]["sha256"], manifest["license"]["license_sha256"]
    row = (f"| Libbet and the Magic Floor | zlib, Damian Yerrick and Martin Korth, hardware.inc CC0-1.0 | "
           f"`fixtures/libbet/manifest.json`: `{sha256_hex(manifest_raw)}` | `{rom_sha}` | `{lic_sha}` |")
    intro = "The separately listed Libbet fixture is third-party.\n"
    attributes = "\n".join(GITATTRIBUTES_LINES) + "\n"
    check_notices_text(intro + row + "\n", attributes, manifest_raw, rom_sha, lic_sha)
    expect("notice-missing", lambda: check_notices_text(intro, attributes, manifest_raw, rom_sha, lic_sha), "no row")
    expect("notice-missing", lambda: check_notices_text(intro + row.replace(lic_sha, "0" * 64) + "\n", attributes,
                                                        manifest_raw, rom_sha, lic_sha), "wrong licence digest")
    expect("notice-missing", lambda: check_notices_text(row + "\n", attributes, manifest_raw, rom_sha, lic_sha),
           "intro still claims every ROM is project-authored")
    expect("attributes-missing", lambda: check_notices_text(intro + row + "\n", attributes.replace(
        GITATTRIBUTES_LINES[0] + "\n", ""), manifest_raw, rom_sha, lic_sha), "ROM -text line removed")


def self_test() -> None:
    raw, manifest, rom, license_bytes = read_inputs(ROOT / MANIFEST_PATH)
    verify_data(manifest, rom, license_bytes)

    def mutated(change) -> dict:
        copy = deepcopy(manifest)
        change(copy)
        return copy

    def run(change, label, token, rom_bytes=rom):
        expect(token, lambda: verify_data(mutated(change), rom_bytes, license_bytes), label)

    run(lambda m: m["rights"].__setitem__("embedded_assets", []), "empty assets (D-05)", "embedded-assets-empty")
    run(lambda m: m["rights"].pop("embedded_assets"), "assets key missing", "embedded-assets-empty")
    run(lambda m: m["rights"]["embedded_assets"].pop(0), "one closure record removed (D-05)", "embedded-asset-missing")
    run(lambda m: m["rights"]["embedded_assets"][0].__setitem__("licence", "unknown"),
        "licence unknown (D-05)", "embedded-asset-field-invalid")
    run(lambda m: m["rights"]["embedded_assets"][0].__setitem__("licence", "UNKNOWN"),
        "licence UNKNOWN", "embedded-asset-field-invalid")
    run(lambda m: m["rights"]["embedded_assets"][0].__setitem__("author", ""),
        "empty author", "embedded-asset-field-invalid")
    run(lambda m: m["rights"]["embedded_assets"][0].__setitem__("sha256", m["rights"]["embedded_assets"][0]["sha256"].upper()),
        "uppercase record digest", "embedded-asset-field-invalid")
    run(lambda m: m["rights"]["embedded_assets"][0].__setitem__("evidence", "https://example.com/x"),
        "evidence not at the pinned commit", "embedded-asset-field-invalid")
    run(lambda m: m["rom"].__setitem__("sha256", ("0" if m["rom"]["sha256"][0] != "0" else "1") + m["rom"]["sha256"][1:]),
        "changed ROM digest (D-05)", "rom-digest-mismatch")
    run(lambda m: m["rom"]["header"].__setitem__("cartridge_type", 1), "changed header byte (D-05)", "rom-header-mismatch")
    run(lambda m: m["rom"].__setitem__("size_bytes", ROM_SIZE - 1), "wrong declared size", "rom-size-mismatch")
    changed = bytearray(rom)
    changed[0x4000] ^= 1
    run(lambda m: None, "changed ROM byte", "rom-digest-mismatch", bytes(changed))
    run(lambda m: m["rights"]["closure_files"].remove("src/global.inc"),
        "src/global.inc removed from closure_files", "closure-digest-mismatch")
    run(lambda m: m["source"].__setitem__("commit", "0" * 40), "wrong commit", "source-commit-mismatch")
    run(lambda m: m["license"].__setitem__("license_sha256", "0" * 64), "wrong licence digest", "license-digest-mismatch")
    run(lambda m: m["credits"]["korth_permission"].__setitem__("classification", "licence-grant"),
        "Korth permission misclassified", "korth-permission-misclassified")
    run(lambda m: m["reproducibility"].__setitem__("hosted_run_url", "https://example.com/run"),
        "bad hosted run URL", "reproducibility-url-invalid")
    run(lambda m: m["reproducibility"].__setitem__("statement", "Reproduced on hosted Linux."),
        "hosted claim without a run URL", "reproducibility-claim-invalid")
    run(lambda m: m.__setitem__("scope_note", " "), "empty scope note", "scope-note-missing")
    run(lambda m: m["predicate_addresses"]["cur_floor"]["rom_anchor"].__setitem__("bytes", "AF EA 7F C5 E0 43 E0 43"),
        "changed anchor text", "predicate-anchor-mismatch")
    run(lambda m: m["predicate_addresses"]["cur_score"].__setitem__("address", "0xC4EE"),
        "changed predicate address", "predicate-addresses-invalid")
    run(lambda m: m["rights"]["closure_exclusions"][0].__setitem__("reason", ""),
        "exclusion without a reason", "closure-exclusion-invalid")

    text = raw.decode("utf-8")
    duplicated = text.replace('"schema": 1,', '"schema": 1,\n  "schema": 1,', 1)
    if duplicated == text:
        fail("self-test", "could not build the duplicate-key mutation")
    expect("manifest-invalid", lambda: parse_manifest(duplicated.encode("utf-8")), "duplicate JSON key")
    expect("manifest-invalid", lambda: parse_manifest(raw + b"\xff"), "malformed UTF-8")
    expect("manifest-invalid", lambda: parse_manifest(b"\xef\xbb\xbf" + raw), "UTF-8 byte-order mark")
    expect("manifest-invalid", lambda: parse_manifest(b"[]"), "non-object manifest")

    derive_self_test()
    scan_self_test(rom)
    notices_self_test(raw, manifest)
    print("libbet admission self-test passed: five D-05 mutations, duplicate key, encoding, closure omission, "
          "closure derivation rules, install-tree scan and notice controls")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--manifest", type=pathlib.Path, default=ROOT / MANIFEST_PATH)
    parser.add_argument("--check-notices", action="store_true",
                        help="also require the THIRD_PARTY_NOTICES.md row and the .gitattributes lines")
    parser.add_argument("--scan-dir", type=pathlib.Path, metavar="DIR",
                        help="fail if DIR holds the Libbet ROM (by digest) or any path naming libbet")
    parser.add_argument("--derive-closure", type=pathlib.Path, metavar="SRC_DIR",
                        help="re-derive the build closure from a checked-out Libbet source tree (read-only)")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        if args.self_test:
            self_test()
            return 0
        if args.scan_dir is not None:
            print(f"libbet absent from scanned tree files={scan_dir(args.scan_dir)}")
            return 0
        raw, manifest, rom, license_bytes = read_inputs(args.manifest)
        summary = verify_data(manifest, rom, license_bytes)
        print(f"libbet admission verified rom_sha256={summary['rom_sha256']} "
              f"closure_files={summary['closure_files']} embedded_assets={summary['embedded_assets']}")
        if args.check_notices:
            check_notices(raw, manifest)
            print("libbet notices and attributes verified")
        if args.derive_closure is not None:
            rights = manifest["rights"]
            derived, digest = derive_closure(args.derive_closure, rights["closure_files"],
                                             [entry["path"] for entry in rights["closure_exclusions"]])
            print(f"libbet closure derived files={len(derived)} sha256={digest}")
    except (ValueError, OSError) as error:
        print(f"libbet admission verification failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
