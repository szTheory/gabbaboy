#!/usr/bin/env python3
"""Validate the stable support ledger and bind it to an immutable Git tag."""
from __future__ import annotations

import argparse
import collections
import copy
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
# Set only by --evidence-only while verifying an already attached sidecar in a job that did not build the
# product: the receipt then lives outside the checkout and the producer's build files are absent. Source
# inputs, the receipt's content and every build file that IS present are still checked; generation and
# --check-current never relax anything.
EVIDENCE_ONLY = False
# Ledgers are versioned when the support scope changes, not on every release.
# A release binds the newest ledger at or below its own version, read from the
# tagged tree, so a fixes-only patch release reuses the unchanged ledger.
LEDGER_DIR = "docs/support"
LEDGER_NAME = re.compile(r"v(\d+)\.(\d+)\.(\d+)\.md")
TAG = re.compile(r"v(\d+)\.(\d+)\.(\d+)")
BEGIN = "<!-- support-ledger-data-begin -->"
END = "<!-- support-ledger-data-end -->"
MAX_LEDGER_BYTES = 32 * 1024 * 1024
MAX_RECEIPT_BYTES = 32 * 1024 * 1024
MAX_INPUT_BYTES = 32 * 1024 * 1024
V2_REQUIRED_CASES = 107
V2_MODEL = "CGB-CPU-E"
V2_MANIFEST_PATHS = [
    "fixtures/age/manifest.json",
    "fixtures/magentests/manifest.json",
    "fixtures/mooneye-cgb/manifest.json",
    "fixtures/samesuite/manifest.json",
]
V2_DISPOSITION_PATHS = [
    "tests/external/cgb-apu-dispositions.json",
    "tests/external/cgb-ppu-dispositions.json",
    "tests/external/cgb-speed-dispositions.json",
]
CASE_IDS = [
    "mooneye-acceptance-instr-daa",
    "mooneye-acceptance-timer-tim00",
    "mooneye-acceptance-timer-tim00-div-trigger",
]


def fail(message: str) -> None:
    raise ValueError(message)


def version_key(match: re.Match) -> tuple[int, int, int]:
    return tuple(int(part) for part in match.groups())


def select_ledger(names: list[str], tag: str) -> str:
    """Select only a ledger from this tag's major/minor support scope."""
    tag_match = TAG.fullmatch(tag)
    if not tag_match:
        fail("tag must be a vX.Y.Z release tag")
    release = version_key(tag_match)
    candidates = []
    for name in names:
        match = LEDGER_NAME.fullmatch(name)
        version = version_key(match) if match else None
        if version and version[:2] == release[:2] and version <= release:
            candidates.append((version, name))
    if not candidates:
        if release == (0, 2, 0):
            fail("exact v0.2.0 support ledger is missing")
        fail("no support ledger exists in this release's major/minor scope")
    return f"{LEDGER_DIR}/{max(candidates)[1]}"


def ledger_version(path: str) -> str:
    return ".".join(LEDGER_NAME.fullmatch(pathlib.PurePosixPath(path).name).groups())


def tree_version(root: pathlib.Path = ROOT) -> str:
    """The release version of a tree: CMake project VERSION, which must equal the release-please manifest entry.

    A pre-release suffix is out of scope (release-please emits plain X.Y.Z here), and a disagreement is a hard
    failure rather than a choice of one source (D-28).
    """
    try:
        cmake = (root / "CMakeLists.txt").read_text(encoding="utf-8")
        manifest = json.loads((root / ".release-please-manifest.json").read_text(encoding="utf-8"),
                              object_pairs_hook=unique_pairs)
    except (OSError, ValueError) as error:
        fail(f"REJECT version-unreadable: {error}")
    match = re.search(r"^project\(\s*\w+\s+VERSION\s+(\d+\.\d+\.\d+)[\s)]", cmake, re.M)
    if not match:
        fail("REJECT version-missing: CMakeLists.txt has no plain X.Y.Z project VERSION")
    manifest_version = manifest.get(".") if type(manifest) is dict else None
    if type(manifest_version) is not str or manifest_version != match.group(1):
        fail(f"REJECT version-mismatch: CMakeLists.txt {match.group(1)} differs from "
             f".release-please-manifest.json {manifest_version!r}")
    return match.group(1)


def tree_ledger(root: pathlib.Path = ROOT) -> str:
    """The newest ledger in this tree's major/minor scope that is not above its version."""
    try:
        names = sorted(entry.name for entry in (root / LEDGER_DIR).iterdir())
    except OSError as error:
        fail(f"REJECT ledger-dir-unreadable: {error}")
    return select_ledger(names, "v" + tree_version(root))


def derive_rehearsal_tag(ref: str, root: pathlib.Path = ROOT) -> str:
    """The rehearsal branch rehearsal/vX.Y.Z names the tag; it must be the rehearsed tree's own version, never a default."""
    match = re.fullmatch(r"rehearsal/(v\d+\.\d+\.\d+)", ref)
    if not match:
        fail(f"REJECT rehearsal-ref: {ref!r} is not rehearsal/vX.Y.Z")
    version = tree_version(root)
    if match.group(1) != "v" + version:
        fail(f"REJECT rehearsal-ref-version: {ref!r} names {match.group(1)} but the rehearsed tree is v{version}")
    return "REHEARSAL_TAG=" + match.group(1)


README_LEDGER_LINK = re.compile(r"\[versioned\s+support\s+ledger\]\(docs/support/(v\d+\.\d+\.\d+\.md)\)")


def check_binding(root: pathlib.Path = ROOT) -> tuple[str, str]:
    """README must link the ledger this tree's version selects, not an older or newer one (D-28)."""
    version = tree_version(root)
    selected = tree_ledger(root)
    try:
        readme = (root / "README.md").read_text(encoding="utf-8")
    except OSError as error:
        fail(f"REJECT readme-unreadable: {error}")
    links = [match.group(1) for match in README_LEDGER_LINK.finditer(readme)]
    if links != [pathlib.PurePosixPath(selected).name]:
        fail(f"REJECT readme-ledger-link: README links {links or 'no versioned support ledger'}, "
             f"but version {version} binds {selected}")
    return version, selected


def self_test_binding() -> int:
    """Private fixture trees: main-like, window-like, and each way the binding can break."""
    def tree(base: pathlib.Path, version: str, manifest: str, ledgers: list[str], readme_link: str) -> pathlib.Path:
        base.mkdir()
        (base / "CMakeLists.txt").write_text(
            f"project(GabbaBoy VERSION {version} LANGUAGES C) # x-release-please-version\n")
        (base / ".release-please-manifest.json").write_text(json.dumps({".": manifest}) + "\n")
        (base / LEDGER_DIR).mkdir(parents=True)
        for name in ledgers:
            (base / LEDGER_DIR / name).write_text("ledger\n")
        (base / "README.md").write_text(
            f"The [versioned support ledger](docs/support/{readme_link}) defines the scope.\n")
        return base

    controls = 0
    with tempfile.TemporaryDirectory(prefix="gabbaboy-binding-") as temporary:
        root = pathlib.Path(temporary)
        positives = (
            ("main", ("0.2.0", "0.2.0", ["v0.1.0.md", "v0.2.0.md"], "v0.2.0.md"), ("0.2.0", "docs/support/v0.2.0.md")),
            ("window", ("0.2.1", "0.2.1", ["v0.1.0.md", "v0.2.0.md", "v0.2.1.md"], "v0.2.1.md"),
             ("0.2.1", "docs/support/v0.2.1.md")),
            ("patch", ("0.2.2", "0.2.2", ["v0.2.0.md", "v0.2.1.md"], "v0.2.1.md"), ("0.2.2", "docs/support/v0.2.1.md")),
        )
        for name, args, expected in positives:
            if check_binding(tree(root / name, *args)) != expected:
                fail(f"{name}-like tree did not bind {expected[1]}")
        negatives = (
            ("readme-links-older-ledger", ("0.2.1", "0.2.1", ["v0.2.0.md", "v0.2.1.md"], "v0.2.0.md"), "readme-ledger-link"),
            ("readme-links-future-ledger", ("0.2.0", "0.2.0", ["v0.2.0.md", "v0.2.1.md"], "v0.2.1.md"), "readme-ledger-link"),
            ("manifest-cmake-mismatch", ("0.2.1", "0.2.0", ["v0.2.0.md", "v0.2.1.md"], "v0.2.1.md"), "version-mismatch"),
            ("version-without-ledger", ("0.3.0", "0.3.0", ["v0.2.0.md"], "v0.2.0.md"), "no support ledger exists"),
        )
        for name, args, reason in negatives:
            try:
                check_binding(tree(root / name, *args))
            except ValueError as error:
                if reason not in str(error):
                    fail(f"{name}: rejected for the wrong reason: {error}")
                controls += 1
            else:
                fail(f"{name}: the binding check accepted it")
        for name, ref, args, reason in (
            ("derive-ref-for-another-version", "rehearsal/v0.2.0", ("0.2.1", "0.2.1", ["v0.2.1.md"], "v0.2.1.md"), "rehearsal-ref-version"),
            ("derive-ref-without-a-version", "rehearsal/phase-15.1-79e20f3", ("0.2.0", "0.2.0", ["v0.2.0.md"], "v0.2.0.md"), "rehearsal-ref"),
        ):
            try:
                derive_rehearsal_tag(ref, tree(root / name, *args))
            except ValueError as error:
                if reason not in str(error):
                    fail(f"{name}: rejected for the wrong reason: {error}")
                controls += 1
            else:
                fail(f"{name}: the rehearsal tag derivation accepted it")
        if derive_rehearsal_tag("rehearsal/v0.2.1", root / "window") != "REHEARSAL_TAG=v0.2.1":
            fail("the window-like tree did not derive its own rehearsal tag")
    return controls


# The v0.2.0 ledger is frozen (D-29, TUNE-06): its tag blob and working bytes are pinned, and the working file may differ
# from the tag only by the one disclosed #93 (09805f3) performance-history block inserted at a pinned offset.
FREEZE_TAG = "v0.2.0"
FREEZE_PATH = f"{LEDGER_DIR}/v0.2.0.md"
TAG_BLOB_SHA256 = "a542a5c01e236246f83d4f1b67aba20f2a9200e74e5ffe70b930daf9f3af2b8f"
WORKING_SHA256 = "c47ff12b089fd386ebe1dd1a16d4ceaefc9fd60d072acdce510267c3dff19a9e"
APPENDED_BLOCK_OFFSET = 7233
APPENDED_BLOCK_LENGTH = 794
APPENDED_BLOCK_SHA256 = "1422b9ebb82e20ffabe8c0072551cbbc2520fee4420ce201359913085a065b7d"
FREEZE_PINS = (TAG_BLOB_SHA256, WORKING_SHA256, APPENDED_BLOCK_OFFSET, APPENDED_BLOCK_LENGTH, APPENDED_BLOCK_SHA256)


def read_freeze_tag_blob(tag: str = FREEZE_TAG, path: str = FREEZE_PATH) -> bytes:
    result = subprocess.run(["git", "show", f"{tag}:{path}"], cwd=ROOT, capture_output=True, check=False)
    if result.returncode != 0 or not result.stdout:
        fail(f"REJECT tag-missing: {tag}:{path} is unreadable; fetch the tag (fetch-depth: 0) before checking the freeze")
    return result.stdout


def judge_freeze(tag_raw: bytes, working_raw: bytes, pins: tuple = FREEZE_PINS) -> int:
    """Return the block's line count when the working bytes are the tag blob plus the one pinned block."""
    tag_sha, working_sha, offset, length, block_sha = pins
    if sha256(tag_raw) != tag_sha:
        fail(f"REJECT tag-blob-digest: the {FREEZE_TAG} blob digest {sha256(tag_raw)} is not the pinned {tag_sha}")
    if sha256(working_raw) != working_sha:
        fail(f"REJECT working-digest: {FREEZE_PATH} digest {sha256(working_raw)} is not the pinned {working_sha}")
    if len(working_raw) != len(tag_raw) + length or \
            working_raw[:offset] + working_raw[offset + length:] != tag_raw:
        fail("REJECT edit-outside-block: the working file is not the tag blob plus exactly the one disclosed block")
    block = working_raw[offset:offset + length]
    if sha256(block) != block_sha:
        fail("REJECT block-digest: the disclosed #93 performance-history block differs from its pinned digest")
    return block.count(b"\n")


def check_freeze() -> str:
    tag_raw = read_freeze_tag_blob()
    working_raw = bounded_file(ROOT / FREEZE_PATH, MAX_LEDGER_BYTES, "ledger")
    lines = judge_freeze(tag_raw, working_raw)
    return f"ledger-freeze pass tag={sha256(tag_raw)} working={sha256(working_raw)} appended_lines={lines}"


def self_test_freeze() -> int:
    tag_raw = read_freeze_tag_blob()
    working_raw = bounded_file(ROOT / FREEZE_PATH, MAX_LEDGER_BYTES, "ledger")
    if judge_freeze(tag_raw, working_raw) < 1:
        fail("the positive freeze control found no disclosed block")

    def flipped(raw: bytes, index: int) -> bytes:
        return raw[:index] + bytes([raw[index] ^ 1]) + raw[index + 1:]

    def repin(raw: bytes) -> tuple:
        # Pin the mutated working digest too, so only the structural rule can reject it.
        return (TAG_BLOB_SHA256, sha256(raw), APPENDED_BLOCK_OFFSET, APPENDED_BLOCK_LENGTH, APPENDED_BLOCK_SHA256)

    inserted = working_raw[:100] + b"x" + working_raw[100:]
    edited = flipped(working_raw, 500)
    block_edited = flipped(working_raw, APPENDED_BLOCK_OFFSET + 10)
    cases = (
        ("flipped-byte-in-tag-blob", flipped(tag_raw, 500), working_raw, FREEZE_PINS, "tag-blob-digest"),
        ("flipped-byte-in-working-file", tag_raw, edited, FREEZE_PINS, "working-digest"),
        ("wrong-tag-pin", tag_raw, working_raw, ("0" * 64,) + FREEZE_PINS[1:], "tag-blob-digest"),
        ("wrong-working-pin", tag_raw, working_raw, (FREEZE_PINS[0], "0" * 64) + FREEZE_PINS[2:], "working-digest"),
        ("extra-insertion-outside-the-block", tag_raw, inserted, repin(inserted), "edit-outside-block"),
        ("equal-length-edit-outside-the-block", tag_raw, edited, repin(edited), "edit-outside-block"),
        ("block-removed", tag_raw, tag_raw, repin(tag_raw), "edit-outside-block"),
        ("block-edited", tag_raw, block_edited, repin(block_edited), "block-digest"),
    )
    controls = 0
    for name, tag_case, working_case, pins, reason in cases:
        try:
            judge_freeze(tag_case, working_case, pins)
        except ValueError as error:
            if reason not in str(error):
                fail(f"{name}: rejected for the wrong reason: {error}")
            controls += 1
        else:
            fail(f"{name}: the freeze check accepted it")
    try:
        read_freeze_tag_blob("v0.0.0-no-such-tag")
    except ValueError as error:
        if "tag-missing" not in str(error):
            fail(f"a missing tag was rejected for the wrong reason: {error}")
        controls += 1
    else:
        fail("a missing tag was accepted")
    return controls


def working_tree_ledger() -> str:
    # Keep the legacy validator's fixture fixed as newer ledger schemas arrive.
    return f"{LEDGER_DIR}/v0.1.0.md"


def parse_ledger(raw: bytes, expected_version: str) -> dict:
    if len(raw) > MAX_LEDGER_BYTES:
        fail("ledger exceeds the bounded read size")
    try:
        source = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        fail(f"ledger is not valid UTF-8: {error}")
    if "\ufffd" in source:
        fail("ledger contains Unicode replacement character")
    if re.search(r"(?im)^\s*[\"']?(?:source_sha|release_source_sha)[\"']?\s*[:=]\s*[\"']?[0-9a-f]{40}", source):
        fail("tracked ledger must not embed a future/full release source SHA")
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
    if type(data) is dict and any(type(data.get(key)) is str and
                                  re.fullmatch(r"[0-9a-f]{40,64}", data[key])
                                  for key in ("source_sha", "release_source_sha")):
        fail("tracked ledger must not embed a future/full release source SHA")
    validate_data(data, expected_version)
    return data


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            fail(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def validate_data(data: dict, expected_version: str) -> None:
    if isinstance(data, dict) and data.get("schema_version") == 2:
        validate_data_v2(data, expected_version)
        return
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        fail("unsupported ledger schema")
    if data.get("version") != expected_version or data.get("boot") != "skipped":
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


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_sha256(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded)


def relative_path(value: object, code: str = "input-path-invalid") -> str:
    if (type(value) is not str or not value or len(value) > 4096 or "\0" in value or
            "\\" in value or value.startswith("/") or re.match(r"^[A-Za-z]:", value) or
            any(part in ("", ".", "..") for part in value.split("/"))):
        fail(code)
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeEncodeError:
        fail(code + ":not-utf8")
    return value


def path_content_identity(rows: list[dict], contents: dict[str, bytes], domain: bytes) -> str:
    """Hash exact UTF-8 path bytes and exact file bytes with unambiguous framing."""
    digest = hashlib.sha256()
    digest.update(domain + b"\0")
    for row in sorted(rows, key=lambda item: relative_path(item.get("path")).encode("utf-8")):
        name = relative_path(row.get("path"))
        path_raw = name.encode("utf-8", errors="strict")
        if name not in contents:
            fail("build-evidence-identity-incomplete")
        raw = contents[name]
        digest.update(len(path_raw).to_bytes(8, "big"))
        digest.update(path_raw)
        digest.update(len(raw).to_bytes(8, "big"))
        digest.update(sha256(raw).encode("ascii"))
    return digest.hexdigest()


def immutable_git_file(repo_root: pathlib.Path, revision: str, relative: str,
                       limit: int = MAX_INPUT_BYTES) -> bytes:
    """Read a bounded file blob from a recorded producer commit, ignoring replace refs."""
    relative_path(relative, "source-input-path-invalid")
    if re.fullmatch(r"[0-9a-f]{40,64}", revision or "") is None:
        fail("source producer revision is malformed")
    environment = os.environ.copy()
    environment.update({
        "GIT_NO_LAZY_FETCH": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_TERMINAL_PROMPT": "0",
    })
    object_name = f"{revision}:{relative}"
    try:
        size = subprocess.run(["git", "cat-file", "-s", object_name], cwd=repo_root,
                              stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, text=True, check=False, timeout=10,
                              env=environment)
        if size.returncode != 0 or re.fullmatch(r"[0-9]+\n?", size.stdout) is None:
            fail("source producer object unavailable:" + relative)
        byte_count = int(size.stdout.strip())
        if byte_count > limit:
            fail("source producer object too large:" + relative)
        content = subprocess.run(["git", "cat-file", "blob", object_name], cwd=repo_root,
                                 stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, check=False, timeout=10,
                                 env=environment)
    except (OSError, subprocess.TimeoutExpired):
        fail("source producer object unavailable:" + relative)
    if content.returncode != 0 or len(content.stdout) != byte_count:
        fail("source producer object unavailable:" + relative)
    return content.stdout


def bounded_file(path: pathlib.Path, limit: int, code: str) -> bytes:
    try:
        size = path.stat().st_size
        if size > limit:
            fail(code + ":too-large")
        raw = path.read_bytes()
    except OSError as error:
        fail(code + ":unavailable")
    if len(raw) > limit:
        fail(code + ":too-large")
    return raw


def strict_json(raw: bytes, label: str) -> dict:
    try:
        text = raw.decode("utf-8", errors="strict")
        value = json.loads(text, object_pairs_hook=unique_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError):
        fail(label + ":invalid-json-or-duplicate-key")
    except ValueError as error:
        fail(label + ":" + str(error))
    if type(value) is not dict:
        fail(label + ":invalid-json-root")
    return value


def read_repo_file(repo_root: pathlib.Path, value: object, limit: int, code: str) -> tuple[str, bytes]:
    relative = relative_path(value, code)
    root = repo_root.resolve()
    path = (root / relative).resolve(strict=True)
    try:
        path.relative_to(root)
    except ValueError:
        fail(code + ":outside-root")
    if not path.is_file():
        fail(code + ":not-file")
    return relative, bounded_file(path, limit, code)


def _sha_field(value: object, code: str) -> None:
    if type(value) is not str or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        fail(code)


def _sorted_unique_strings(value: object, code: str) -> list[str]:
    if (type(value) is not list or not value or any(type(item) is not str or not item for item in value) or
            len(set(value)) != len(value) or value != sorted(value)):
        fail(code)
    return value


def _count_suite_model_modes(bindings: list[dict], observations: list[dict]) -> list[dict]:
    eligible = collections.Counter()
    observed = collections.defaultdict(list)
    for row in bindings:
        key = (row["suite"], row["model"], row["mode"], row["speed"])
        eligible[key] += 1
    for row in observations:
        key = (row["suite"], row["model"], row["mode"], row["speed"])
        observed[key].append(row)
    result = []
    for suite, model, mode, speed in sorted(eligible):
        rows = observed.get((suite, model, mode, speed), [])
        assertion_rows = [item for row in rows for item in row["assertions"]]
        executed = sum(row["executed"] is True for row in rows)
        actual_pass = sum(row["observed_result"] == "pass" and row["evaluator_status"] == "pass"
                          for row in rows)
        actual_fail = sum(row["observed_result"] == "fail" for row in rows)
        matched = sum(row["matched_xfail"] is True for row in rows)
        result.append({
            "suite": suite,
            "model": model,
            "mode": mode,
            "speed": speed,
            "boot": "skipped",
            "eligible": eligible[(suite, model, mode, speed)],
            "attempted": sum(row["attempted"] is True for row in rows),
            "executed": executed,
            "actual_pass": actual_pass,
            "actual_fail": actual_fail,
            "matched_xfail": matched,
            "excluded": sum(row["excluded"] is True for row in rows),
            "not_run": eligible[(suite, model, mode, speed)] - executed,
            "assertions": len(assertion_rows),
            "passing_assertions": sum(row.get("observed_result") == "pass" and
                                      row.get("evaluator_status") == "pass" for row in assertion_rows),
            "failing_assertions": sum(row.get("observed_result") == "fail" for row in assertion_rows),
        })
    if set(observed) != set(eligible):
        fail("receipt-suite-model-mode-membership-mismatch")
    return result


def _count_receipt_cases(observations: list[dict]) -> dict:
    assertion_rows = [item for row in observations for item in row["assertions"]]
    actual_pass = sum(row["observed_result"] == "pass" and row["evaluator_status"] == "pass"
                      for row in observations)
    actual_fail = sum(row["observed_result"] == "fail" for row in observations)
    executed = sum(row["executed"] is True for row in observations)
    return {
        "admitted_cases": len(observations),
        "applicable_cases": len(observations),
        "required_eligible_cases": len(observations),
        "attempted_cases": sum(row["attempted"] is True for row in observations),
        "completed_cases": executed,
        "observed_pass_cases": actual_pass,
        "observed_fail_cases": actual_fail,
        "matched_xfail_cases": sum(row["matched_xfail"] is True for row in observations),
        "excluded_cases": sum(row["excluded"] is True for row in observations),
        "not_run_cases": len(observations) - executed,
        "assertions": len(assertion_rows),
        "passing_assertions": sum(row.get("observed_result") == "pass" and
                                   row.get("evaluator_status") == "pass" for row in assertion_rows),
        "failing_assertions": sum(row.get("observed_result") == "fail" for row in assertion_rows),
        "image_pixels": sum(row["details"].get("image_pixels", 0) for row in observations),
        "pixel_mismatches": sum(row["details"].get("pixel_mismatches", 0) for row in observations),
    }


def validate_data_v2(data: dict, expected_version: str, expected_case_count: int = V2_REQUIRED_CASES) -> None:
    if type(data) is not dict or data.get("schema_version") != 2:
        fail("unsupported ledger schema")
    if not re.fullmatch(r"0\.[23]\.[0-9]+", expected_version) or data.get("version") != expected_version:
        fail("v0.2/v0.3 ledger version/profile identity is missing or unstable")
    game = data.get("game_evidence")
    if (type(game) is not dict or game.get("status") != "absent" or
            game.get("statement") != "No CGB game-level evidence exists"):
        fail("v0.2 CGB game-evidence absence statement is missing")
    scope = data.get("scope")
    expected_scope = ({
        "models": ["CGB-CPU-E", "DMG-CPU-B"],
        "corpus_model": "CGB-CPU-E",
        "modes": ["compat", "native"],
        "boot": "skipped",
        "physical_cgb_e": "UNKNOWN/POLICY",
    } if expected_version.startswith("0.2.") else {
        "models": ["CGB-CPU-E", "DMG-CPU-B"],
        "corpus_model": "CGB-CPU-E",
        "modes": ["cgb-compat", "cgb-native", "dmg"],
        "boot": "skipped",
        "physical_cgb_e": "UNKNOWN/POLICY",
    })
    if scope != expected_scope:
        fail("v0.2/v0.3 model, execution-mode, boot, or physical-evidence scope mismatch")

    source_inputs = data.get("source_inputs")
    if type(source_inputs) is not list or not source_inputs:
        fail("source-input inventory is empty or missing")
    input_paths = []
    input_by_path = {}
    for row in source_inputs:
        if type(row) is not dict:
            fail("source-input row is malformed")
        relative_path(row.get("path"))
        _sha_field(row.get("sha256"), "source-input SHA-256 is malformed")
        if type(row.get("size_bytes")) is not int or row["size_bytes"] < 0:
            fail("source-input size is malformed")
        input_paths.append(row["path"])
        input_by_path[row["path"]] = row
    if len(input_paths) != len(set(input_paths)):
        fail("source-input path is duplicated")
    if input_paths != sorted(input_paths):
        fail("source-input paths are not in stable order")

    manifest_rows = data.get("manifest_identities")
    disposition_rows = data.get("disposition_identities")
    for label, rows in (("manifest", manifest_rows), ("disposition", disposition_rows)):
        if type(rows) is not list or not rows:
            fail(label + " identities are empty or missing")
        paths = []
        for row in rows:
            if type(row) is not dict:
                fail(label + " identity row is malformed")
            relative_path(row.get("path"))
            _sha_field(row.get("sha256"), label + " SHA-256 is malformed")
            if type(row.get("size_bytes")) is not int or row["size_bytes"] < 0:
                fail(label + " size is malformed")
            paths.append(row["path"])
        if len(paths) != len(set(paths)):
            fail(label + " path is duplicated")
    if [row["path"] for row in manifest_rows] != V2_MANIFEST_PATHS:
        fail("manifest identity paths differ from the admitted suite manifests")
    if [row["path"] for row in disposition_rows] != V2_DISPOSITION_PATHS:
        fail("disposition identity paths differ from the admitted disposition files")
    for row in [*manifest_rows, *disposition_rows]:
        source_row = input_by_path.get(row["path"])
        if (source_row is None or source_row["sha256"] != row["sha256"] or
                source_row["size_bytes"] != row["size_bytes"]):
            fail("manifest or disposition identity differs from source inputs:" + row["path"])

    inventory = data.get("inventory")
    if type(inventory) is not dict:
        fail("independent inventory is missing")
    relative_path(inventory.get("path"))
    _sha_field(inventory.get("sha256"), "independent inventory SHA-256 is malformed")
    inventory_source = input_by_path.get(inventory["path"])
    if (inventory["path"] != "tests/external/cgb-corpus-inventory.json" or
            inventory_source is None or inventory_source["sha256"] != inventory["sha256"]):
        fail("independent inventory identity differs from source inputs")
    case_ids = _sorted_unique_strings(inventory.get("case_ids"), "required inventory membership is empty, duplicated, or unordered")
    if len(case_ids) != expected_case_count or inventory.get("required_case_count") != expected_case_count:
        fail("required inventory membership is incomplete or narrowed")
    bindings = inventory.get("case_bindings")
    if type(bindings) is not list or [row.get("id") for row in bindings if type(row) is dict] != case_ids:
        fail("independent inventory case bindings are incomplete or duplicated")
    for row in bindings:
        if (type(row) is not dict or type(row.get("id")) is not str or
                type(row.get("suite")) is not str or row.get("model") != V2_MODEL or
                row.get("mode") not in ("compat", "native") or
                row.get("speed") not in ("normal", "double") or
                type(row.get("test_name")) is not str or not row["test_name"] or
                type(row.get("source_id")) is not str or not row["source_id"] or
                type(row.get("source_path")) is not str or not row["source_path"] or
                type(row.get("source_revision")) is not str or
                not re.fullmatch(r"[0-9a-f]{40,64}", row["source_revision"]) or
                type(row.get("output_id")) is not str or not row["output_id"] or
                type(row.get("output_path")) is not str or not row["output_path"] or
                type(row.get("output_sha256")) is not str or
                not re.fullmatch(r"[0-9a-f]{64}", row["output_sha256"]) or
                type(row.get("assertion_ids")) is not list or not row["assertion_ids"] or
                any(type(item) is not str or not item for item in row["assertion_ids"]) or
                len(set(row["assertion_ids"])) != len(row["assertion_ids"]) or
                type(row.get("expected_failure")) is not bool or
                row.get("disposition_state") not in
                ("pass", "expected-failure", "prior-phase-observation", "prior-observation") or
                type(row.get("disposition_value")) is not str or not row["disposition_value"] or
                row["expected_failure"] != (row["disposition_state"] == "expected-failure")):
            fail("independent inventory case binding is malformed")
        relative_path(row["source_path"])
        relative_path(row["output_path"])
        if row.get("expected_signature_sha256") is not None:
            _sha_field(row["expected_signature_sha256"], "expected failure signature is malformed")

    receipt = data.get("receipt")
    if type(receipt) is not dict:
        fail("complete corpus receipt identity is missing")
    relative_path(receipt.get("path"))
    for field in ("sha256", "identity_sha256", "input_identity_sha256", "run_id", "source_inputs_sha256"):
        _sha_field(receipt.get(field), "receipt " + field + " is malformed")
    if (type(receipt.get("producer_revision")) is not str or
            not re.fullmatch(r"[0-9a-f]{40,64}", receipt["producer_revision"])):
        fail("receipt producer revision is malformed")
    if receipt["source_inputs_sha256"] != canonical_sha256(source_inputs):
        fail("receipt source-input identity digest mismatch")
    if receipt.get("model") != "CGB-CPU-E selected software model" or receipt.get("hardware_qualified") is not False:
        fail("receipt contains a model or hardware-qualification mismatch")
    run = receipt.get("run")
    if (type(run) is not dict or run.get("id") != receipt.get("run_id") or
            type(run.get("ctest_cases")) is not int or
            run.get("ctest_cases") != expected_case_count + 1 or
            type(run.get("ctest_total_cases")) is not int or
            run.get("ctest_total_cases") < run.get("ctest_cases")):
        fail("receipt CTest run is incomplete or has a mismatched denominator")
    _sha_field(run.get("ctest_log_sha256"), "receipt CTest log SHA-256 is malformed")
    _sha_field(run.get("run_nonce_sha256"), "receipt run nonce SHA-256 is missing")
    if receipt.get("case_ids") != case_ids:
        fail("receipt case membership differs from the independent inventory")
    observations = receipt.get("case_observations")
    if type(observations) is not list:
        fail("receipt case observations are missing")
    observation_ids = [row.get("id") for row in observations if type(row) is dict]
    if observation_ids != case_ids:
        fail("receipt case membership is incomplete, duplicated, or out of order")
    binding_by_id = {row["id"]: row for row in bindings}
    for row in observations:
        if type(row) is not dict:
            fail("receipt case observation is malformed")
        binding = binding_by_id[row["id"]]
        producer_case = row.get("producer_case")
        if (type(producer_case) is not dict or producer_case.get("id") != row["id"] or
                row.get("case_sha256") != canonical_sha256(producer_case) or
                row.get("assertions") != producer_case.get("assertions") or
                row.get("details") != producer_case.get("details") or
                row.get("observed_result") != producer_case.get("observed_result") or
                row.get("evaluator_status") != producer_case.get("evaluator_status") or
                row.get("matched_xfail") != producer_case.get("matched_xfail")):
            fail("receipt observation fields differ from its source-bound producer case")
        if any(row.get(field) != binding[field] for field in
               ("suite", "model", "mode", "speed", "test_name")):
            fail("receipt case binding differs from the independent inventory")
        evidence = row.get("evidence")
        if (type(evidence) is not dict or any(evidence.get(field) != binding[field] for field in
                ("source_id", "source_path", "source_revision", "output_id", "output_path", "output_sha256"))):
            fail("receipt source/output evidence differs from the independent inventory")
        if (row.get("expected_failure") is not binding["expected_failure"] or
                producer_case.get("evaluator_disposition") != binding["disposition_value"]):
            fail("receipt expected-failure disposition differs from independent inventory")
        if (row.get("boot") != "skipped" or row.get("attempted") is not True or
                row.get("executed") is not True or row.get("excluded") is not False or
                type(row.get("matched_xfail")) is not bool or
                row.get("observed_result") not in ("pass", "fail") or
                row.get("evaluator_status") not in ("pass", "xfail")):
            fail("receipt contains an incomplete or invalid case observation")
        expected_failure = binding["expected_failure"]
        if expected_failure:
            if (row["observed_result"] != "fail" or row["evaluator_status"] != "xfail" or
                    row["matched_xfail"] is not True):
                fail("receipt unexpected pass or unmatched expected failure")
        elif (row["observed_result"] != "pass" or row["evaluator_status"] != "pass" or
              row["matched_xfail"] is not False):
            fail("receipt unexpected failure or xfail-as-pass disposition")
        assertions = row.get("assertions")
        if type(assertions) is not list or not assertions:
            fail("receipt assertion membership is missing")
        assertion_ids = []
        for assertion in assertions:
            if (type(assertion) is not dict or type(assertion.get("id")) is not str or
                    not assertion["id"] or assertion.get("expected_disposition") != "pass" or
                    assertion.get("observed_result") not in ("pass", "fail") or
                    assertion.get("evaluator_status") not in ("pass", "xfail")):
                fail("receipt assertion row is malformed")
            assertion_ids.append(assertion["id"])
            if assertion.get("signature_sha256") is not None:
                _sha_field(assertion["signature_sha256"], "receipt assertion signature is malformed")
        if assertion_ids != binding["assertion_ids"]:
            fail("receipt assertion IDs or signatures differ from inventory membership")
        expected_signature = binding.get("expected_signature_sha256")
        observed_signatures = [item.get("signature_sha256") for item in assertions
                               if item.get("signature_sha256") is not None]
        if (expected_signature is not None and observed_signatures and
                expected_signature not in observed_signatures):
            fail("receipt expected failure signature changed")
        if type(row.get("details")) is not dict:
            fail("receipt case details are malformed")
        _sha_field(row.get("case_sha256"), "receipt case identity SHA-256 is malformed")
        _sha_field(row.get("assertion_signatures_sha256"), "receipt assertion signatures SHA-256 is malformed")
        if row["case_sha256"] != canonical_sha256(row.get("producer_case")):
            fail("receipt case identity digest mismatch")
        if row["assertion_signatures_sha256"] != canonical_sha256(assertions):
            fail("receipt assertion signature digest mismatch")

    expected_suite_counts = _count_suite_model_modes(bindings, observations)
    if receipt.get("suite_model_mode_counts") != expected_suite_counts:
        fail("receipt per-suite model/mode counts do not derive from case rows")
    expected_counts = _count_receipt_cases(observations)
    claimed_counts = receipt.get("counts")
    if type(claimed_counts) is not dict or any(claimed_counts.get(key) != value
                                             for key, value in expected_counts.items()):
        fail("receipt global counts do not derive from complete case and assertion rows")
    if (expected_counts["observed_pass_cases"] + expected_counts["observed_fail_cases"] != expected_case_count or
            expected_counts["observed_fail_cases"] != expected_counts["matched_xfail_cases"] or
            expected_counts["not_run_cases"] != 0 or expected_counts["excluded_cases"] != 0):
        fail("receipt pass, xfail, exclusion, or not-run totals do not close")

    artifacts = receipt.get("build_artifacts")
    if type(artifacts) is not list or not artifacts:
        fail("receipt build artifact identities are missing")
    artifact_paths = []
    for row in artifacts:
        if type(row) is not dict:
            fail("receipt build artifact is malformed")
        relative_path(row.get("path"))
        _sha_field(row.get("sha256"), "receipt build artifact SHA-256 is malformed")
        if type(row.get("size_bytes")) is not int or row["size_bytes"] < 0:
            fail("receipt build artifact size is malformed")
        artifact_paths.append(row["path"])
    if len(artifact_paths) != len(set(artifact_paths)):
        fail("receipt build artifact path is duplicated")


def _case_binding_rows(inventory: dict) -> list[dict]:
    sources = {row.get("id"): row for row in inventory.get("source_candidates", []) if type(row) is dict}
    outputs = {row.get("id"): row for row in inventory.get("outputs", []) if type(row) is dict}
    bindings = []
    for case in inventory.get("cases", []):
        if type(case) is not dict or type(case.get("id")) is not str:
            fail("inventory case is malformed")
        source = sources.get(case.get("source_id"))
        output = outputs.get(case.get("output_id"))
        rows = case.get("assertion_contract", {}).get("rows")
        if type(source) is not dict or type(output) is not dict or type(rows) is not list or not rows:
            fail("inventory case source, output, or assertion contract is missing")
        disposition = case.get("evaluator_disposition", {})
        bindings.append({
            "id": case["id"],
            "suite": case.get("suite"),
            "model": case.get("model"),
            "mode": case.get("mode"),
            "speed": case.get("speed"),
            "test_name": case.get("test_binding", {}).get("ctest_name"),
            "source_id": case.get("source_id"),
            "source_path": source.get("source_path"),
            "source_revision": source.get("source_commit"),
            "output_id": case.get("output_id"),
            "output_path": output.get("output_path"),
            "output_sha256": output.get("sha256"),
            "assertion_ids": [row.get("id") for row in rows if type(row) is dict],
            "expected_failure": disposition.get("state") == "expected-failure",
            "disposition_state": disposition.get("state"),
            "disposition_value": disposition.get("value"),
            "expected_signature_sha256": disposition.get("signature_sha256") or None,
        })
    bindings.sort(key=lambda row: row["id"])
    ids = [row["id"] for row in bindings]
    if len(ids) != len(set(ids)):
        fail("inventory case IDs are duplicated")
    return bindings


def _receipt_observations(receipt: dict, bindings: list[dict]) -> list[dict]:
    by_id = {row["id"]: row for row in bindings}
    observations = []
    seen = set()
    for producer_case in receipt.get("cases", []):
        if type(producer_case) is not dict or type(producer_case.get("id")) is not str:
            fail("receipt case is malformed")
        case_id = producer_case["id"]
        if case_id in seen or case_id not in by_id:
            fail("receipt case membership is duplicated or unknown")
        seen.add(case_id)
        binding = by_id[case_id]
        evidence = producer_case.get("evidence")
        if type(evidence) is not dict:
            fail("receipt source/output evidence is missing")
        for field in ("source_id", "source_path", "output_id", "output_path", "output_sha256"):
            if evidence.get(field) != binding[field]:
                fail("receipt source/output binding mismatch:" + case_id)
        if evidence.get("source_revision") != binding["source_revision"]:
            fail("receipt source revision mismatch:" + case_id)
        disposition = producer_case.get("evaluator_disposition")
        expected_failure = binding["expected_failure"]
        if disposition != binding["disposition_value"]:
            fail("receipt evaluator disposition differs from inventory:" + case_id)
        assertions = producer_case.get("assertions")
        if type(assertions) is not list:
            fail("receipt assertion rows are missing:" + case_id)
        observations.append({
            "id": case_id,
            "suite": producer_case.get("suite"),
            "model": producer_case.get("model"),
            "mode": producer_case.get("mode"),
            "speed": producer_case.get("speed"),
            "test_name": producer_case.get("test_name"),
            "boot": "skipped",
            "attempted": producer_case.get("attempted") is True,
            "executed": producer_case.get("completed") is True,
            "excluded": False,
            "observed_result": producer_case.get("observed_result"),
            "evaluator_status": producer_case.get("evaluator_status"),
            "matched_xfail": producer_case.get("matched_xfail"),
            "expected_failure": binding["expected_failure"],
            "evidence": {field: evidence.get(field) for field in (
                "source_id", "source_path", "source_revision", "output_id", "output_path", "output_sha256",
                "manifest_ref")},
            "details": producer_case.get("details", {}),
            "assertions": assertions,
            "case_sha256": canonical_sha256(producer_case),
            "assertion_signatures_sha256": canonical_sha256(assertions),
            "producer_case": producer_case,
        })
    if seen != set(by_id):
        fail("receipt is missing required inventory cases")
    observations.sort(key=lambda row: row["id"])
    return observations


def _validate_run_identity(receipt: dict, inventory_sha256: str) -> dict:
    identity = receipt.get("identity")
    run = receipt.get("run")
    if type(identity) is not dict or type(run) is not dict or receipt.get("status") != "complete":
        fail("corpus receipt is incomplete")
    if receipt.get("failure_codes") != [] or identity.get("hardware_qualified") is not False:
        fail("corpus receipt carries failure or hardware qualification")
    if identity.get("inventory_sha256") != inventory_sha256:
        fail("receipt inventory digest differs from independent inventory bytes")
    for field in ("identity_sha256", "input_identity_sha256", "core_revision", "run_id"):
        value = identity.get(field)
        if type(value) is not str or not re.fullmatch(r"[0-9a-f]{40,64}", value):
            fail("receipt identity field is malformed:" + field)
    if (run.get("id") != identity.get("run_id") or
            type(run.get("ctest_cases")) is not int or
            run.get("ctest_cases") != V2_REQUIRED_CASES + 1):
        fail("receipt run identity or case denominator mismatch")
    if (type(run.get("ctest_total_cases")) is not int or
            run.get("ctest_total_cases") < run.get("ctest_cases")):
        fail("receipt CTest denominator is incomplete")
    if (type(run.get("started_at_ns")) is not int or type(run.get("completed_at_ns")) is not int or
            run["completed_at_ns"] <= run["started_at_ns"]):
        fail("receipt run timestamps are invalid")
    _sha_field(run.get("ctest_log_sha256"), "receipt CTest log identity is malformed")
    _sha_field(run.get("run_nonce_sha256"), "receipt run nonce is missing")
    identity_body = dict(identity)
    claimed_identity_sha = identity_body.pop("identity_sha256")
    if canonical_sha256(identity_body) != claimed_identity_sha:
        fail("receipt identity digest does not match its fields")
    return identity


def build_v2_data(receipt: dict, receipt_raw: bytes, inventory: dict, inventory_raw: bytes,
                  repo_root: pathlib.Path, receipt_path: str,
                  tagged_inputs: dict[str, bytes] | None = None, *, version: str) -> dict:
    inventory_sha = sha256(inventory_raw)
    identity = _validate_run_identity(receipt, inventory_sha)
    bindings = _case_binding_rows(inventory)
    case_ids = [row["id"] for row in bindings]
    if len(case_ids) != V2_REQUIRED_CASES or inventory.get("counts", {}).get("required_cases") != V2_REQUIRED_CASES:
        fail("independent inventory required denominator is not 107")
    observations = _receipt_observations(receipt, bindings)
    identity_case_ids = identity.get("case_ids")
    if identity_case_ids != case_ids:
        fail("receipt and independent inventory IDs differ")
    assertion_ids = {row["id"]: row["assertion_ids"] for row in bindings}
    if identity.get("assertion_ids") != assertion_ids:
        fail("receipt assertion IDs differ from independent inventory contracts")
    suite_counts = _count_suite_model_modes(bindings, observations)
    counts = _count_receipt_cases(observations)
    source_inputs = identity.get("input_hashes")
    if type(source_inputs) is not list or not source_inputs:
        fail("receipt source input hash list is missing")
    input_paths = []
    for row in source_inputs:
        if type(row) is not dict:
            fail("receipt source input hash row is malformed")
        relative_path(row.get("path"))
        _sha_field(row.get("sha256"), "receipt source input SHA-256 is malformed")
        if type(row.get("size_bytes")) is not int or row["size_bytes"] < 0:
            fail("receipt source input size is malformed")
        input_paths.append(row["path"])
    if len(input_paths) != len(set(input_paths)):
        fail("receipt source input path is duplicated")
    source_inputs = sorted(source_inputs, key=lambda row: row["path"])

    def identities(paths: list[str]) -> list[dict]:
        rows = []
        for relative in paths:
            if tagged_inputs is not None and relative in tagged_inputs:
                name, raw = relative, tagged_inputs[relative]
                if len(raw) > MAX_INPUT_BYTES:
                    fail("evidence-input:too-large")
            else:
                name, raw = read_repo_file(repo_root, relative, MAX_INPUT_BYTES, "evidence-input")
            strict_json(raw, "evidence-input:" + name)
            rows.append({"path": name, "sha256": sha256(raw), "size_bytes": len(raw)})
        return rows

    source_candidate_counts = inventory.get("counts", {}).get("by_suite", {})
    excluded_by_suite = collections.Counter(
        row.get("suite") for row in inventory.get("source_candidates", [])
        if type(row) is dict and row.get("selection", {}).get("state") == "excluded")
    output_case_ids = {case.get("output_id") for case in inventory.get("cases", []) if type(case) is dict}
    outside_outputs = sum(row.get("id") not in output_case_ids for row in inventory.get("outputs", [])
                          if type(row) is dict)
    inventory_data = {
        "path": "tests/external/cgb-corpus-inventory.json",
        "sha256": inventory_sha,
        "required_case_count": V2_REQUIRED_CASES,
        "case_ids": case_ids,
        "case_bindings": bindings,
        "source_candidates_by_suite": {
            suite: {
                "discovered": values.get("source_candidates", 0),
                "required": values.get("required_cases", 0),
                "excluded": excluded_by_suite.get(suite, 0),
            } for suite, values in sorted(source_candidate_counts.items())
        },
        "admitted_outputs": inventory.get("counts", {}).get("admitted_outputs"),
        "outputs_outside_required_case_set": outside_outputs,
    }
    receipt_data = {
        "path": receipt_path,
        "sha256": sha256(receipt_raw),
        "identity_sha256": identity["identity_sha256"],
        "input_identity_sha256": identity["input_identity_sha256"],
        "source_inputs_sha256": canonical_sha256(source_inputs),
        "producer_revision": identity["core_revision"],
        "run_id": receipt["run"]["id"],
        "model": identity.get("model"),
        "hardware_qualified": identity.get("hardware_qualified"),
        "run": {key: receipt["run"].get(key) for key in (
            "id", "ctest_cases", "ctest_total_cases", "ctest_log_sha256", "run_nonce_sha256")},
        "counts": counts,
        "suite_model_mode_counts": suite_counts,
        "case_ids": case_ids,
        "case_observations": observations,
        "build_artifacts": identity.get("build_artifacts"),
    }
    return {
        "schema_version": 2,
        "version": version,
        "game_evidence": {
            "status": "absent",
            "statement": "No CGB game-level evidence exists",
        },
        "scope": {
            "models": ["CGB-CPU-E", "DMG-CPU-B"],
            "corpus_model": "CGB-CPU-E",
            "modes": (["compat", "native"] if version.startswith("0.2.") else
                      ["cgb-compat", "cgb-native", "dmg"]),
            "boot": "skipped",
            "physical_cgb_e": "UNKNOWN/POLICY",
        },
        "source_inputs": sorted(source_inputs, key=lambda row: row["path"]),
        "manifest_identities": identities(V2_MANIFEST_PATHS),
        "disposition_identities": identities(V2_DISPOSITION_PATHS),
        "inventory": inventory_data,
        "receipt": receipt_data,
    }


def stable_v2_evidence(data: dict) -> dict:
    """Project away only producer/run/build provenance from ledger equality."""
    stable = copy.deepcopy(data)
    receipt = stable.get("receipt")
    if type(receipt) is not dict:
        fail("complete corpus receipt identity is missing")
    for field in ("sha256", "identity_sha256", "input_identity_sha256",
                  "producer_revision", "run_id"):
        receipt.pop(field, None)
    run = receipt.get("run")
    if type(run) is not dict:
        fail("receipt CTest run is incomplete")
    receipt["run"] = {"ctest_cases": run.get("ctest_cases")}
    artifacts = receipt.get("build_artifacts")
    if type(artifacts) is not list:
        fail("receipt build artifact identities are missing")
    receipt["build_artifacts"] = [{"path": row.get("path")} for row in artifacts
                                  if type(row) is dict]
    return stable


def render_v2_ledger(data: dict, disclosure: dict | None = None) -> str:
    # The historical performance disclosure is rendered from validated, source-bound managed input
    # (tests/data/release-disclosure.json, D-19), never inserted by hand after generation.
    if disclosure is None:
        disclosure = load_disclosure(ROOT)
    counts = data["receipt"]["counts"]
    suite_rows = data["receipt"]["suite_model_mode_counts"]
    lines = [
        f"# GabbaBoy v{data['version']} support ledger",
        "",
        f"This ledger records implemented scope and the software evidence available for the v{data['version']} release. The CGB corpus is a bounded test-ROM set, not a game library or hardware qualification. Boot ROMs are skipped; the CGB corpus ran on the selected CGB-CPU-E software model. Physical CGB-E remains UNKNOWN/POLICY.",
        "",
        "## Models and execution modes",
        "",
        "- **DMG-CPU-B:** bootless deterministic DMG software profile. The Libbet and the Magic Floor v0.08 headless acceptance is a separate single-game software result. Packaged-player game smoke is macOS-only; headless acceptance runs on Linux, macOS and Windows.",
        "- **CGB-CPU-E:** selected CGB software model, with native CGB mode and DMG compatibility mode selected from the cartridge header. Test-ROM execution is bootless. A test-ROM result applies only to the recorded model, mode, speed, case and assertion rows.",
        "- **Boot path:** skipped for both profiles. Startup state is emulator policy. No physical startup or boot-ROM behavior is asserted.",
        "",
        "## CGB test-ROM evidence",
        "",
        f"The historical producer receipt records {counts['required_eligible_cases']} eligible cases, {counts['attempted_cases']} attempted, {counts['completed_cases']} completed, {counts['observed_pass_cases']} actual guest passes, {counts['observed_fail_cases']} actual guest failures, {counts['matched_xfail_cases']} matched expected failures, {counts['excluded_cases']} excluded and {counts['not_run_cases']} not run. There are {counts['assertions']} assertion rows ({counts['passing_assertions']} passing and {counts['failing_assertions']} failing). Fresh receipts must reproduce these stable case and assertion observations; matched expected failures remain failures and never increase the guest-pass total.",
        "",
        "| Suite | Model | Mode | Speed | Eligible | Attempted | Executed | Guest pass | Guest fail | Matched xfail | Excluded | Not run | Assertions | Assertion pass | Assertion fail |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in suite_rows:
        lines.append("| {suite} | {model} | {mode} | {speed} | {eligible} | {attempted} | {executed} | {actual_pass} | {actual_fail} | {matched_xfail} | {excluded} | {not_run} | {assertions} | {passing_assertions} | {failing_assertions} |".format(**row))
    lines.extend([
        "",
        "The structured block preserves the historical receipt's exact case membership, source/output identities, inventory dispositions, assertion IDs, observed assertion rows, nonce-bound CTest run identity, receipt bytes, source inputs and build artifacts. A fresh receipt is checked against the same stable evidence and its own actual source and build bytes. Suite source provenance and each case's source revision remain attached to the inventory bindings. The source trees retain independent author expectations; evaluator outcomes are not rewritten to match them.",
        "",
        "## Implemented cartridge and save matrix",
        "",
        "These are documented loader/core capabilities. The corpus rows above identify which model/mode combinations were exercised; they do not qualify every mapper and profile combination or game.",
        "",
        "| Mapper and header types | ROM / RAM bounds | Battery image and additional behavior |",
        "|---|---|---|",
        "| ROM-only `$00` | 32 KiB ROM; no RAM | No battery image |",
        "| Standard MBC1 `$01`/`$02`/`$03` | ROM size codes `$00`–`$06` (32 KiB–2 MiB). `$01` has no RAM; `$02` is volatile; `$03` is battery-backed. RAM is 8 KiB, or 32 KiB only through 512 KiB ROM. | Type `$03` persists RAM. MBC1M wiring is unsupported. |",
        "| MBC2 `$05`/`$06` | ROM size codes `$00`–`$03` (32–256 KiB); 512 built-in 4-bit cells and no header RAM | Type `$06` image is canonical 512 bytes; packed 256-byte files are unsupported |",
        "| MBC3 `$0F`–`$13` | ROM size codes `$00`–`$06` (32 KiB–2 MiB); 4 MiB length ceiling. `$0F`/`$11` have no RAM; `$10` has timer and 8/32 KiB RAM; `$12` volatile 8/32 KiB; `$13` battery 8/32 KiB. | `$0F`/`$10` use emulated-time RTC and a 21-byte versioned clock block; `$13` persists RAM. MBC30 is rejected. |",
        "| MBC5 `$19`–`$1E` | ROM size codes `$00`–`$08` (32 KiB–8 MiB); `$19`/`$1C` have no RAM, others support 8/32/64/128 KiB by type. | `$1B`/`$1E` persist RAM. `$1C`–`$1E` expose rumble-line state, with no host haptics or physical rumble claim. |",
        "",
        "Battery export/import is caller-buffer based and atomic on rejected input. MBC3 wall-clock catch-up is an explicit host call; the core never reads the host clock. RTC, mapper and save-format behavior are software evidence, not physical-board or cross-emulator compatibility claims. See [cartridge and save contract](../cartridge-and-saves.md).",
        "",
        "## Reconciled prior scope entries",
        "",
        "- **DMG game acceptance:** Libbet and the Magic Floor v0.08 has a ROM-bound, headless DMG-CPU-B acceptance predicate. This is evidence for one game on that software profile. Packaged-player smoke is macOS-only; a hosted reproduction run remains pending because the workflow has not been dispatched.",
        "- **MBC2 and MBC5 evidence:** Mooneye emulator-only MBC2 (7/7) and MBC5 (8/8) test ROMs were run on the DMG-CPU-B software profile from test-ROM revision `31510e12eea6286d36eea060a6adde755e1067aa`. Those counts are test-ROM results, not CGB evidence, broad game compatibility, MBC5 RAM qualification or physical rumble behavior.",
        "- **MBC3 and RTC:** RTC-capable `$0F`/`$10` cartridges advance from emulated half-dots; explicit host catch-up is separate. The 21-byte clock block, import bounds, phase preservation, and MBC1/MBC2/MBC3/MBC5 battery persistence are software contracts. No physical MBC3 or RTC observation is available; MBC30 is rejected.",
        "- **CGB profile and colour:** CGB-CPU-E exposes header-selected native or DMG-compatibility execution, CGB register/banking behavior and raw RGB555 frame output. Software fixtures and differential results cover named cases only; there is no perceptual color evidence or general game claim.",
        "- **CGB speed and HDMA:** double-speed execution keeps budgets in master half-dots; GDMA and HBlank DMA follow the documented bounded block model. The known `$83` → `$02` → `$00` → `$80` HDMA sequence remains unresolved against Pan Docs. No physical CGB-E timing qualification is made.",
        "- **CGB digital APU reads:** native CGB guest reads of FF76/FF77 expose digital DAC inputs on the CGB-CPU-E software model; CGB compatibility mode reads `$FF`. Player playback continues to use the scoped DMG APU model. This says nothing about analog output or perceptual audio quality.",
        "",
        "## Game-level evidence, known issues and exclusions",
        "",
        "**No CGB game-level evidence exists.** The CGB corpus consists of bounded emulator/test ROMs. The separate DMG Libbet acceptance does not establish CGB game behavior. No uncertain game image is admitted by this ledger.",
        "",
        "Known limitations include skipped boot ROMs; no physical DMG-CPU-B or CGB-CPU-E qualification; no general game compatibility percentage; no CGB mode-3 timing qualification; no analog audio, perceptual color/audio, or physical rumble claim; no MBC1M or MBC30 support; and no Linux/Windows packaged-player game smoke. CGB-CPU-E's current APU, PPU and speed limitations remain profile/model-specific as described in the CGB corpus and profile documentation.",
        "",
        *disclosure_paragraphs(disclosure, data["version"]),
        "Evidence classes are kept distinct: source-backed expectations, admitted fixture bytes, independent inventory and assertion contracts, local software execution receipts, differential observations, project-authored regression tests, and game-level acceptance. Physical-hardware evidence is absent for this ledger.",
        "",
        "The receipt below is a historical producer snapshot: its exact bytes, producer revision, run identity and build artifacts identify that earlier run. A fresh receipt must independently validate its source and build bytes and reproduce the same stable corpus evidence before a release sidecar is created. The sidecar binds that supplied receipt's digest, producer revision, run identity and build artifacts alongside the tagged source and exact ledger blob; tag verification never regenerates this ledger. This tracked ledger intentionally contains no release source SHA.",
        "",
        "<!-- support-ledger-data-begin -->",
        "```json",
        json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False),
        "```",
        "<!-- support-ledger-data-end -->",
        "",
        "The chronological pending entries were reconciled into this versioned ledger. See the [CGB corpus contract](../cgb-corpus.md), [CGB profile](../cgb-profile.md), [game acceptance](../game-acceptance.md) and [cartridge/save contract](../cartridge-and-saves.md) for operational details.",
        "",
    ])
    return "\n".join(lines)


def render_v3_ledger(data: dict, disclosure: dict | None = None, claims: dict | None = None) -> str:
    """Render the v2 fixed point plus a section sourced only from validated v0.3 claims."""
    if disclosure is None:
        disclosure = load_disclosure(ROOT)
    if claims is None:
        claims = load_claims(ROOT, current_git_revision())
    if not str(data.get("version", "")).startswith("0.3."):
        fail("v0.3 renderer requires a v0.3.x ledger")
    rendered = render_v2_ledger(data, disclosure)
    disclosure_block = "\n".join(disclosure_paragraphs(disclosure, data["version"]))
    position = rendered.find(disclosure_block)
    if position < 0 or rendered.find(disclosure_block, position + 1) >= 0:
        fail("v0.3 renderer could not locate the historical disclosure block exactly once")
    claim_block = "\n".join(claim_paragraphs(claims, data["version"]))
    return rendered[:position] + claim_block + "\n" + rendered[position:]


def create_current_ledger(receipt_path: pathlib.Path, output: pathlib.Path | None = None,
                          root: pathlib.Path = ROOT) -> dict:
    receipt_path = receipt_path.resolve(strict=True)
    try:
        receipt_rel = receipt_path.relative_to(root.resolve()).as_posix()
    except ValueError:
        fail("receipt path must stay inside the repository")
    if receipt_rel != "build/cgb-corpus-receipt.json":
        fail("current support ledger requires the canonical build/cgb-corpus-receipt.json path")
    inventory_path = root / "tests/external/cgb-corpus-inventory.json"
    inventory_raw = bounded_file(inventory_path, MAX_INPUT_BYTES, "inventory")
    inventory = strict_json(inventory_raw, "inventory")
    receipt_raw = bounded_file(receipt_path, MAX_RECEIPT_BYTES, "receipt")
    receipt = strict_json(receipt_raw, "receipt")
    run_inventory_validator(root)
    version = tree_version(root)
    data = build_v2_data(receipt, receipt_raw, inventory, inventory_raw, root, receipt_rel, version=version)
    identity = receipt.get("identity", {})
    current = current_git_revision(root)
    if identity.get("core_revision") == current:
        run_existing_receipt_validator(receipt_path, inventory)
    else:
        check_source_ancestry(identity.get("core_revision", ""), current, root)
    validate_data_v2(data, version)
    validate_source_bindings(data, root)
    write_generated_ledger(data, root, output)
    return data


def write_generated_ledger(data: dict, root: pathlib.Path, output: pathlib.Path | None = None) -> pathlib.Path:
    """The writer tail of --write-current: refuse a tagged tracked target, then write the generator bytes."""
    default_target = root / f"{LEDGER_DIR}/v{data['version']}.md"
    target = output if output is not None else default_target
    refuse_tagged_target(root, data["version"], target, default_target)
    # Bytes, not text mode: the ledger is digest-bound and must not gain CRLF on Windows (GB-CI-011).
    if tuple(int(part) for part in data["version"].split(".")) >= (0, 3, 0):
        try:
            rev = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root,
                                          stderr=subprocess.DEVNULL, text=True).strip()
        except (OSError, subprocess.CalledProcessError):
            fail("REJECT claims-input-invalid: immutable revision is unavailable")
        claims = load_claims(root, rev)
        target.write_bytes(render_v3_ledger(data, load_disclosure(root), claims).encode("utf-8"))
    else:
        target.write_bytes(render_v2_ledger(data).encode("utf-8"))
    return target


def validate_source_bindings(data: dict, repo_root: pathlib.Path,
                             source_bytes: dict[str, bytes] | None = None,
                             source_revision: str | None = None,
                             include_build: bool = True) -> None:
    root = repo_root.resolve()
    for section, rows in (("source", data.get("source_inputs")),
                          ("build", data.get("receipt", {}).get("build_artifacts"))):
        if section == "build" and not include_build:
            continue
        if type(rows) is not list:
            fail(section + " input identities are missing")
        for row in rows:
            if type(row) is not dict:
                fail(section + " input identity is malformed")
            if section == "source" and source_bytes is not None:
                if row.get("path") not in source_bytes:
                    fail(section + "-input:missing-tagged-byte")
                name, raw = row["path"], source_bytes[row["path"]]
                if len(raw) > MAX_INPUT_BYTES:
                    fail(section + "-input:too-large")
            elif section == "source" and source_revision is not None:
                name = relative_path(row.get("path"), "source-input-path-invalid")
                raw = immutable_git_file(root, source_revision, name)
            else:
                if (section == "build" and EVIDENCE_ONLY and type(row.get("path")) is str
                        and not (root / row["path"]).exists()):
                    continue
                name, raw = read_repo_file(root, row.get("path"), MAX_INPUT_BYTES, section + "-input")
            if sha256(raw) != row.get("sha256") or len(raw) != row.get("size_bytes"):
                fail(section + " input is stale:" + name)


def build_evidence_scope(receipt: dict, repo_root: pathlib.Path) -> dict:
    rows = receipt.get("identity", {}).get("build_artifacts")
    if type(rows) is not list or not rows:
        fail("build-evidence-identities-empty")
    contents: dict[str, bytes] = {}
    missing = []
    for row in rows:
        if type(row) is not dict:
            fail("build-evidence-identity-malformed")
        name = relative_path(row.get("path"), "build-evidence-path-invalid")
        path = (repo_root.resolve() / name).resolve()
        try:
            path.relative_to(repo_root.resolve())
        except ValueError:
            fail("build-evidence-path-outside-root")
        if not path.exists():
            missing.append(name)
            continue
        if not path.is_file():
            fail("build input is stale:" + name)
        raw = bounded_file(path, MAX_INPUT_BYTES, "build-input")
        if sha256(raw) != row.get("sha256") or len(raw) != row.get("size_bytes"):
            fail("build input is stale:" + name)
        contents[name] = raw

    required = len(rows)
    observed = len(contents)
    skipped = len(missing)
    if skipped and not EVIDENCE_ONLY:
        fail(f"build-evidence-unavailable: observed={observed} skipped={skipped}")
    if skipped and observed:
        fail(f"build-evidence-partial: observed={observed} skipped={skipped}")
    # Declared rows are bound using the receipt's size and content digest, not synthetic bytes.
    declared = hashlib.sha256(b"gabbaboy-build-declared-identity-v1\0")
    for row in sorted(rows, key=lambda item: relative_path(item.get("path")).encode("utf-8")):
        path_raw = relative_path(row.get("path")).encode("utf-8", errors="strict")
        declared.update(len(path_raw).to_bytes(8, "big"))
        declared.update(path_raw)
        declared.update(row["size_bytes"].to_bytes(8, "big"))
        declared.update(row["sha256"].encode("ascii"))
    declared_identity = declared.hexdigest()
    retained_identity = (path_content_identity(rows, contents,
                                              b"gabbaboy-build-retained-identity-v1")
                         if observed == required else None)
    return {
        "scope": "retained-build" if observed == required else "receipt-only",
        "qualification_status": "qualified" if observed == required else "not-established",
        "required_count": required,
        "observed_count": observed,
        "skipped_count": skipped,
        "receipt_declared_identity_sha256": declared_identity,
        "retained_build_identity_sha256": retained_identity,
    }


def current_git_revision(repo_root: pathlib.Path = ROOT) -> str:
    return git("rev-parse", "HEAD", cwd=repo_root).decode("ascii", "strict").strip()


def check_source_ancestry(source_revision: str, current_revision: str,
                          repo_root: pathlib.Path = ROOT) -> None:
    try:
        subprocess.run(["git", "merge-base", "--is-ancestor", source_revision, current_revision],
                       cwd=repo_root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       check=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        fail("receipt producer revision is not an ancestor of the current source")


def run_inventory_validator(repo_root: pathlib.Path = ROOT) -> None:
    validator = repo_root / "tests/scripts/verify-cgb-corpus-inventory.py"
    command = [sys.executable, "-I", str(validator), "--bindings"]
    try:
        completed = subprocess.run(command, cwd=repo_root, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, timeout=60, check=False)
    except (OSError, subprocess.SubprocessError) as error:
        fail("independent inventory validator unavailable")
    if completed.returncode != 0:
        fail("independent inventory validator failed: " + completed.stderr.strip())


def run_existing_receipt_validator(receipt_path: pathlib.Path, inventory: dict,
                                   repo_root: pathlib.Path = ROOT,
                                   source_revision: str | None = None,
                                   inventory_raw: bytes | None = None,
                                   input_bytes: dict[str, bytes] | None = None) -> None:
    script = repo_root / "tests/scripts/verify-cgb-corpus-claims.py"
    spec = importlib.util.spec_from_file_location("gabbaboy_cgb_claims", script)
    if spec is None or spec.loader is None:
        fail("existing corpus report validator unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        module.validate_receipt(receipt_path, inventory, source_revision=source_revision,
                                allow_ancestor=source_revision is not None,
                                repo_root=repo_root, inventory_raw=inventory_raw,
                                input_bytes=input_bytes)
    except module.ContractError as error:
        fail("existing corpus report validator failed: " + str(error))


def check_ledger_static(root: pathlib.Path = ROOT, run_inventory: bool = True, ledger_rel: str | None = None) -> dict:
    """Receipt-free currency check of the tracked ledger bound to this tree's version.

    The tracked ledger carries a historical producer snapshot. Source digests are checked against
    that immutable producer revision, not today's checkout; build artifacts require the full receipt-
    bound check where they were produced.
    """
    ledger_rel = ledger_rel or tree_ledger(root)
    version = ledger_version(ledger_rel)
    ledger = parse_ledger(bounded_file(root / ledger_rel, MAX_LEDGER_BYTES, "ledger"), version)
    if run_inventory:
        run_inventory_validator(root)
    validate_data_v2(ledger, version)
    revision = ledger["receipt"]["producer_revision"] if root.resolve() == ROOT.resolve() else None
    validate_source_bindings(ledger, root, source_revision=revision, include_build=False)
    return ledger


def check_current(receipt_path: pathlib.Path) -> dict:
    receipt_path = receipt_path.resolve(strict=True)
    try:
        receipt_rel = receipt_path.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        fail("receipt path must stay inside the repository")
    if receipt_rel != "build/cgb-corpus-receipt.json":
        fail("current support ledger requires the canonical build/cgb-corpus-receipt.json path")
    ledger_rel = tree_ledger(ROOT)
    version = ledger_version(ledger_rel)
    ledger_path = ROOT / ledger_rel
    ledger = parse_ledger(bounded_file(ledger_path, MAX_LEDGER_BYTES, "ledger"), version)
    inventory_path = ROOT / "tests/external/cgb-corpus-inventory.json"
    inventory_raw = bounded_file(inventory_path, MAX_INPUT_BYTES, "inventory")
    inventory = strict_json(inventory_raw, "inventory")
    receipt_raw = bounded_file(receipt_path, MAX_RECEIPT_BYTES, "receipt")
    receipt = strict_json(receipt_raw, "receipt")
    run_inventory_validator()
    data = build_v2_data(receipt, receipt_raw, inventory, inventory_raw, ROOT, receipt_rel, version=version)
    identity = receipt.get("identity", {})
    current = current_git_revision()
    if identity.get("core_revision") == current:
        run_existing_receipt_validator(receipt_path, inventory)
    else:
        check_source_ancestry(identity.get("core_revision", ""), current)
    validate_data_v2(ledger, version)
    validate_data_v2(data, version)
    validate_source_bindings(data, ROOT)
    if stable_v2_evidence(ledger) != stable_v2_evidence(data):
        fail("v0.2 ledger stable evidence differs from the current receipt, inventory, source inputs, or assertions")
    return ledger


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


def tagged_file(repo_root: pathlib.Path, tag: str, relative: str, limit: int) -> bytes:
    relative_path(relative, "tagged-input-path-invalid")
    raw = git("show", f"{tag}:{relative}", cwd=repo_root)
    if len(raw) > limit:
        fail("tagged-input-too-large:" + relative)
    return raw


def tagged_files(repo_root: pathlib.Path, tag: str, names: list[str], limit: int) -> dict[str, bytes]:
    """Read many tagged blobs through one `git cat-file --batch` process.

    A sidecar build reads every covered source input from the tag; one `git show` per file costs a
    process spawn each, which made the self-test brush the Windows CTest budget. Names that cannot
    travel on a batch input line (CR/LF) keep the single-file path, so no accepted path is lost.
    """
    contents: dict[str, bytes] = {}
    batch = [name for name in dict.fromkeys(names) if "\n" not in name and "\r" not in name]
    for name in batch:
        relative_path(name, "tagged-input-path-invalid")
    if batch:
        request = "".join(f"{tag}:{name}\n" for name in batch).encode("utf-8")
        try:
            output = subprocess.run(["git", "cat-file", "--batch"], cwd=repo_root, input=request,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout
        except subprocess.CalledProcessError as error:
            fail(f"git cat-file --batch failed: {error.stderr.decode(errors='replace').strip()}")
        offset = 0
        for name in batch:
            end = output.find(b"\n", offset)
            header = output[offset:end].split(b" ") if end >= 0 else []
            if len(header) != 3 or header[1] != b"blob" or not header[2].isdigit():
                fail(f"git show {tag}:{name} failed: tagged object is missing or not a file")
            size = int(header[2])
            start = end + 1
            if output[start + size:start + size + 1] != b"\n":
                fail(f"git show {tag}:{name} failed: truncated batch output")
            raw = output[start:start + size]
            offset = start + size + 1
            if len(raw) > limit:
                fail("tagged-input-too-large:" + name)
            contents[name] = raw
    for name in names:
        if name not in contents:
            contents[name] = tagged_file(repo_root, tag, name, limit)
    return contents


def build_v2_sidecar(tag: str, source_sha: str, repo_root: pathlib.Path,
                     ledger: str, ledger_raw: bytes, data: dict,
                     receipt_path: pathlib.Path | None) -> dict:
    if receipt_path is None:
        fail("schema-2 sidecars require --receipt PATH")
    try:
        if not receipt_path.is_absolute():
            receipt_path = repo_root / receipt_path
        receipt_path = receipt_path.resolve(strict=True)
        if EVIDENCE_ONLY:
            receipt_rel = data.get("receipt", {}).get("path")
        else:
            receipt_rel = receipt_path.relative_to(repo_root.resolve()).as_posix()
    except (OSError, ValueError):
        fail("receipt path must stay inside the tagged repository")
    if receipt_rel != data.get("receipt", {}).get("path"):
        fail("receipt path differs from the tracked ledger identity")

    tagged_inputs = {}
    source_rows = data.get("source_inputs")
    if type(source_rows) is not list or not source_rows:
        fail("tagged support ledger has no covered source inputs")
    for row in source_rows:
        if type(row) is not dict:
            fail("tagged source input identity is malformed")
    names = [relative_path(row.get("path")) for row in source_rows]
    blobs = tagged_files(repo_root, tag, names, MAX_INPUT_BYTES)
    for name, row in zip(names, source_rows):
        raw = blobs[name]
        if sha256(raw) != row.get("sha256") or len(raw) != row.get("size_bytes"):
            fail("tagged source input differs from ledger:" + name)
        tagged_inputs[name] = raw
    inventory_path = data["inventory"]["path"]
    inventory_raw = tagged_inputs.get(inventory_path)
    if inventory_raw is None or sha256(inventory_raw) != data["inventory"]["sha256"]:
        fail("tagged independent inventory identity mismatch")
    inventory = strict_json(inventory_raw, "tagged-inventory")
    for section in ("manifest_identities", "disposition_identities"):
        for row in data[section]:
            raw = tagged_inputs.get(row["path"])
            if raw is None or sha256(raw) != row["sha256"] or len(raw) != row["size_bytes"]:
                fail("tagged " + section.removesuffix("_identities") + " identity mismatch:" + row["path"])
            strict_json(raw, "tagged-input:" + row["path"])

    receipt_raw = bounded_file(receipt_path, MAX_RECEIPT_BYTES, "receipt")
    receipt = strict_json(receipt_raw, "receipt")
    identity = _validate_run_identity(receipt, sha256(inventory_raw))
    producer_revision = identity["core_revision"]
    check_source_ancestry(producer_revision, source_sha, repo_root)
    derived = build_v2_data(receipt, receipt_raw, inventory, inventory_raw,
                            repo_root, receipt_rel, tagged_inputs, version=ledger_version(ledger))
    validate_data_v2(data, ledger_version(ledger))
    validate_data_v2(derived, ledger_version(ledger))
    if stable_v2_evidence(derived) != stable_v2_evidence(data):
        fail("tagged ledger stable evidence differs from complete receipt or tagged source inputs")
    validate_source_bindings(derived, repo_root, tagged_inputs)
    build_evidence = build_evidence_scope(receipt, repo_root)
    head = git("rev-parse", "HEAD", cwd=repo_root).decode("ascii", "strict").strip()
    if head == source_sha:
        run_inventory_validator(repo_root)
        run_existing_receipt_validator(receipt_path, inventory, repo_root, source_sha,
                                       inventory_raw, tagged_inputs)

    blob_oid = git("rev-parse", f"{tag}:{ledger}", cwd=repo_root).decode().strip()
    relation = "exact" if producer_revision == source_sha else "ancestor"
    return {
        "schema_version": 2,
        "version": tag[1:],
        "tag": tag,
        "source_sha": source_sha,
        "ledger_version": data["version"],
        "ledger": {"path": ledger, "git_blob_oid": blob_oid,
                   "sha256": sha256(ledger_raw)},
        "manifest_identities": data["manifest_identities"],
        "inventory_sha256": data["inventory"]["sha256"],
        "disposition_identities": data["disposition_identities"],
        "corpus_receipt_sha256": derived["receipt"]["sha256"],
        "corpus_receipt_producer_revision": producer_revision,
        "corpus_receipt_source_relation": relation,
        "corpus_receipt_identity_sha256": derived["receipt"]["identity_sha256"],
        "corpus_receipt_input_identity_sha256": derived["receipt"]["input_identity_sha256"],
        "corpus_receipt_run_id": derived["receipt"]["run_id"],
        "corpus_run": derived["receipt"]["run"],
        "corpus_receipt_build_artifacts": derived["receipt"]["build_artifacts"],
        "build_evidence": build_evidence,
        "covered_source_inputs": data["source_inputs"],
        "suite_model_mode_counts": data["receipt"]["suite_model_mode_counts"],
        "case_counts": data["receipt"]["counts"],
        "game_evidence": data["game_evidence"],
        "self_hash": None,
    }


def build_sidecar(tag: str, source_sha: str, repo_root: pathlib.Path = ROOT,
                  receipt_path: pathlib.Path | None = None) -> dict:
    if not re.fullmatch(r"[0-9a-f]{40}", source_sha):
        fail("source SHA must be a full lowercase Git commit SHA")
    actual_sha = git("rev-parse", f"{tag}^{{commit}}", cwd=repo_root).decode().strip()
    if actual_sha != source_sha:
        fail("supplied source SHA does not resolve from the requested tag")
    names = git("ls-tree", "--name-only", f"{tag}:{LEDGER_DIR}", cwd=repo_root).decode().split()
    ledger = select_ledger(names, tag)
    ledger_raw = git("show", f"{tag}:{ledger}", cwd=repo_root)
    data = parse_ledger(ledger_raw, ledger_version(ledger))
    if data.get("schema_version") == 2:
        return build_v2_sidecar(tag, source_sha, repo_root, ledger, ledger_raw, data, receipt_path)
    if receipt_path is not None:
        fail("--receipt is only accepted for schema-2 support ledgers")
    manifests = {path: git("show", f"{tag}:{path}", cwd=repo_root) for path in data["manifest_paths"]}
    identities = validate_manifest_set(data, manifests)
    blob_oid = git("rev-parse", f"{tag}:{ledger}", cwd=repo_root).decode().strip()
    return {
        "schema_version": 1,
        "version": tag[1:],
        "ledger_version": data["version"],
        "tag": tag,
        "source_sha": source_sha,
        "ledger": {"path": ledger, "git_blob_oid": blob_oid,
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
    expected_build = expected.get("build_evidence", {})
    observed_build = observed.get("build_evidence", {}) if type(observed) is dict else {}
    if expected_build.get("scope") == "receipt-only":
        if (type(observed_build) is not dict or observed_build.get("scope") != "receipt-only" or
                observed_build != expected_build):
            fail("build-evidence-unavailable: retained-build qualification requires every artifact; "
                 f"observed={expected_build.get('observed_count')} "
                 f"skipped={expected_build.get('skipped_count')}")
    elif expected_build.get("scope") == "retained-build" and observed_build != expected_build:
        fail("retained build-evidence identity differs from independently observed bytes")
    if not isinstance(observed, dict) or observed != expected:
        fail("sidecar source SHA, tagged ledger blob, or fixture/corpus identity differs from the tag")


ATTACHED_CONSISTENT = ("attached retained-build evidence consistent; "
                       "qualification established by the producer job of the same run/head")


def verify_attached_sidecar(observed: dict, expected: dict) -> str | None:
    """Verify a sidecar attached as downloaded evidence whose producer job held the build tree.

    The local expectation is receipt-only because the build is absent here. A retained-build sidecar is
    consistent with that only when everything outside build_evidence matches exactly and the build
    identity it claims agrees with the receipt (required count and receipt-declared digest). This
    never qualifies anything: the producer job of the same run and head did, and only it can.
    Returns the consistency statement, or None when the ordinary comparison applied."""
    expected_build = expected.get("build_evidence") if type(expected) is dict else None
    observed_build = observed.get("build_evidence") if type(observed) is dict else None
    if type(expected_build) is not dict or type(observed_build) is not dict:
        fail("attached-evidence-malformed: build_evidence is missing")
    if expected_build.get("scope") != "receipt-only" or observed_build.get("scope") != "retained-build":
        verify_sidecar_data(observed, expected)
        return None
    required = expected_build.get("required_count")
    retained = observed_build.get("retained_build_identity_sha256")
    if (type(required) is not int or required < 1 or
            observed_build.get("qualification_status") != "qualified" or
            observed_build.get("required_count") != required or
            observed_build.get("observed_count") != required or
            observed_build.get("skipped_count") != 0 or
            type(retained) is not str or not re.fullmatch(r"[0-9a-f]{64}", retained)):
        fail("attached-evidence-build-count: attached retained-build evidence does not cover every required artifact")
    if (type(observed_build.get("receipt_declared_identity_sha256")) is not str or
            observed_build.get("receipt_declared_identity_sha256") !=
            expected_build.get("receipt_declared_identity_sha256")):
        fail("attached-evidence-declared-identity: receipt-declared build identity differs from the receipt")
    if ({k: v for k, v in observed.items() if k != "build_evidence"} !=
            {k: v for k, v in expected.items() if k != "build_evidence"}):
        fail("sidecar source SHA, tagged ledger blob, or fixture/corpus identity differs from the tag")
    return ATTACHED_CONSISTENT


def _schema2_test_data(cases: int = 2) -> dict:
    # cases=2 is the historical fixture; cases=1 keeps only case-a for single-entry controls.
    if cases not in (1, 2):
        fail("schema-2 test fixture supports one or two cases")
    case_ids = ["case-a", "case-b"][:cases]
    source_raw = b"input"
    binary_raw = b"binary"
    evidence_raw = b"identity"
    bindings = []
    observations = []
    for case_id, expected_failure, observed, status, matched, signature, assertion_id in (
        ("case-a", False, "pass", "pass", False, None, "case-a:assertion-a"),
        ("case-b", True, "fail", "xfail", True, "1" * 64, "case-b:assertion-b"),
    )[:cases]:
        assertion = {
            "id": assertion_id,
            "expected_disposition": "pass",
            "observed_result": observed,
            "evaluator_status": status,
        }
        if signature:
            assertion["signature_sha256"] = signature
        binding = {
            "id": case_id,
            "suite": "age",
            "model": V2_MODEL,
            "mode": "native",
            "speed": "normal",
            "test_name": "test_" + case_id,
            "source_id": case_id,
            "source_path": "src/" + case_id,
            "source_revision": "a" * 40,
            "output_id": case_id,
            "output_path": "fixtures/" + case_id,
            "output_sha256": "b" * 64,
            "assertion_ids": [assertion_id],
            "expected_failure": expected_failure,
            "disposition_state": "expected-failure" if expected_failure else "pass",
            "disposition_value": "expected-failure:fixture" if expected_failure else "pass",
            "expected_signature_sha256": signature,
        }
        producer_case = {
            "id": case_id,
            "suite": "age",
            "model": V2_MODEL,
            "mode": "native",
            "speed": "normal",
            "test_name": "test_" + case_id,
            "attempted": True,
            "completed": True,
            "observed_result": observed,
            "evaluator_status": status,
            "matched_xfail": matched,
            "evaluator_disposition": binding["disposition_value"],
            "assertions": [assertion],
            "evidence": {"source_id": case_id, "source_path": "src/" + case_id,
                         "source_revision": "a" * 40, "output_id": case_id,
                         "output_path": "fixtures/" + case_id, "output_sha256": "b" * 64,
                         "manifest_ref": "fixtures/manifest.json"},
            "details": {},
        }
        bindings.append(binding)
        observations.append({
            "id": case_id,
            "suite": "age",
            "model": V2_MODEL,
            "mode": "native",
            "speed": "normal",
            "test_name": producer_case["test_name"],
            "boot": "skipped",
            "attempted": True,
            "executed": True,
            "excluded": False,
            "observed_result": observed,
            "evaluator_status": status,
            "matched_xfail": matched,
            "expected_failure": expected_failure,
            "evidence": producer_case["evidence"],
            "details": {},
            "assertions": [assertion],
            "case_sha256": canonical_sha256(producer_case),
            "assertion_signatures_sha256": canonical_sha256([assertion]),
            "producer_case": producer_case,
        })
    identities = [
        *[{"path": path, "size_bytes": len(evidence_raw), "sha256": sha256(evidence_raw)}
          for path in V2_MANIFEST_PATHS],
        *[{"path": path, "size_bytes": len(evidence_raw), "sha256": sha256(evidence_raw)}
          for path in V2_DISPOSITION_PATHS],
        {"path": "tests/external/cgb-corpus-inventory.json", "size_bytes": len(evidence_raw),
         "sha256": sha256(evidence_raw)},
    ]
    source_inputs = sorted([
        {"path": "tests/input.dat", "size_bytes": len(source_raw), "sha256": sha256(source_raw)},
        *identities,
    ], key=lambda row: row["path"])
    suite_counts = _count_suite_model_modes(bindings, observations)
    counts = _count_receipt_cases(observations)
    return {
        "schema_version": 2,
        "version": "0.2.0",
        "game_evidence": {"status": "absent", "statement": "No CGB game-level evidence exists"},
        "scope": {"models": ["CGB-CPU-E", "DMG-CPU-B"], "corpus_model": "CGB-CPU-E",
                  "modes": ["compat", "native"], "boot": "skipped",
                  "physical_cgb_e": "UNKNOWN/POLICY"},
        "source_inputs": source_inputs,
        "manifest_identities": [row for row in identities if row["path"] in V2_MANIFEST_PATHS],
        "disposition_identities": [row for row in identities if row["path"] in V2_DISPOSITION_PATHS],
        "inventory": {"path": "tests/external/cgb-corpus-inventory.json",
                      "sha256": sha256(evidence_raw),
                      "required_case_count": cases, "case_ids": list(case_ids),
                      "case_bindings": bindings,
                      "source_candidates_by_suite": {"age": {"discovered": cases, "required": cases, "excluded": 0}},
                      "admitted_outputs": cases, "outputs_outside_required_case_set": 0},
        "receipt": {"path": "build/cgb-corpus-receipt.json", "sha256": "f" * 64,
                    "identity_sha256": "0" * 64, "input_identity_sha256": "1" * 64,
                    "source_inputs_sha256": canonical_sha256(source_inputs), "run_id": "2" * 64,
                    "producer_revision": "5" * 40,
                    "model": "CGB-CPU-E selected software model", "hardware_qualified": False,
                    "run": {"id": "2" * 64, "ctest_cases": cases + 1, "ctest_total_cases": 1133,
                            "ctest_log_sha256": "3" * 64, "run_nonce_sha256": "4" * 64},
                    "counts": counts, "suite_model_mode_counts": suite_counts,
                    "case_ids": list(case_ids), "case_observations": observations,
                    "build_artifacts": [{"path": "build/bin.dat", "size_bytes": len(binary_raw),
                                         "sha256": sha256(binary_raw)}]},
    }


def self_test_v2() -> None:
    """Exercise schema-2 acceptance and the production validator's named controls."""
    data = _schema2_test_data()
    evidence_raw = b"identity"
    validate_data_v2(data, "0.2.0", expected_case_count=2)
    controls = []
    positive_checks = ["complete-schema2-fixture"]

    def below_selected_total(value: dict) -> None:
        value["receipt"]["run"]["ctest_total_cases"] = 2

    try:
        altered = copy.deepcopy(data)
        below_selected_total(altered)
        validate_data_v2(altered, "0.2.0", expected_case_count=2)
    except ValueError as error:
        if "mismatched denominator" not in str(error):
            fail("below-selected CTest total produced the wrong diagnostic")
        controls.append("ctest-total-below-selected")
    else:
        fail("self-test accepted a CTest total below its selected corpus stream")

    altered = copy.deepcopy(data)
    altered["receipt"]["run"]["ctest_total_cases"] = "1133"
    try:
        validate_data_v2(altered, "0.2.0", expected_case_count=2)
    except ValueError as error:
        if "mismatched denominator" not in str(error):
            fail("non-integer CTest total produced the wrong diagnostic")
        controls.append("ctest-total-noninteger")
    else:
        fail("self-test accepted a non-integer CTest total")

    def rejected(name: str, mutate, expected: str) -> None:
        altered = copy.deepcopy(data)
        mutate(altered)
        try:
            validate_data_v2(altered, "0.2.0", expected_case_count=2)
        except ValueError as error:
            if expected not in str(error):
                fail("self-test control has wrong diagnostic:" + name + ":" + str(error))
            controls.append(name)
        else:
            fail("self-test mutation was accepted:" + name)

    rejected("empty-inventory", lambda value: value["inventory"].update(case_ids=[]),
             "required inventory membership")
    rejected("null-inventory", lambda value: value["inventory"].update(case_ids=None),
             "required inventory membership")
    rejected("narrowed-inventory", lambda value: value["inventory"].update(case_ids=["case-a"]),
             "incomplete or narrowed")
    rejected("duplicate-inventory-id", lambda value: value["inventory"].update(case_ids=["case-a", "case-a"]),
             "duplicated")
    rejected("missing-required-case", lambda value: value["receipt"]["case_observations"].pop(),
             "case membership")
    rejected("empty-build-evidence", lambda value: value["receipt"].update(build_artifacts=[]),
             "receipt build artifact identities are missing")
    rejected("null-build-evidence", lambda value: value["receipt"].update(build_artifacts=None),
             "receipt build artifact identities are missing")

    def xfail_as_pass(value: dict) -> None:
        row = value["receipt"]["case_observations"][1]
        row.update(observed_result="pass", evaluator_status="pass", matched_xfail=False)
        row["producer_case"].update(observed_result="pass", evaluator_status="pass", matched_xfail=False)
        row["case_sha256"] = canonical_sha256(row["producer_case"])
        row["assertion_signatures_sha256"] = canonical_sha256(row["assertions"])
        value["receipt"]["counts"] = _count_receipt_cases(value["receipt"]["case_observations"])
        value["receipt"]["suite_model_mode_counts"] = _count_suite_model_modes(
            value["inventory"]["case_bindings"], value["receipt"]["case_observations"])

    rejected("xfail-as-pass", xfail_as_pass, "unexpected pass or unmatched expected failure")

    def missing_assertion(value: dict) -> None:
        row = value["receipt"]["case_observations"][0]
        row["assertions"] = []
        row["producer_case"]["assertions"] = []
        row["case_sha256"] = canonical_sha256(row["producer_case"])
        row["assertion_signatures_sha256"] = canonical_sha256([])
        value["receipt"]["counts"] = _count_receipt_cases(value["receipt"]["case_observations"])
        value["receipt"]["suite_model_mode_counts"] = _count_suite_model_modes(
            value["inventory"]["case_bindings"], value["receipt"]["case_observations"])

    rejected("missing-assertion", missing_assertion, "assertion membership is missing")

    def changed_signature(value: dict) -> None:
        row = value["receipt"]["case_observations"][1]
        row["assertions"][0]["signature_sha256"] = "9" * 64
        row["producer_case"]["assertions"][0]["signature_sha256"] = "9" * 64
        row["case_sha256"] = canonical_sha256(row["producer_case"])
        row["assertion_signatures_sha256"] = canonical_sha256(row["assertions"])

    rejected("changed-assertion-signature", changed_signature, "expected failure signature changed")
    rejected("unexpected-pass", xfail_as_pass, "unexpected pass or unmatched expected failure")

    try:
        strict_json(b"{\"id\":1,\"id\":2}", "self-test")
    except ValueError as error:
        if "duplicate JSON key" not in str(error):
            fail("duplicate-key control produced the wrong diagnostic")
        controls.append("duplicate-json-key")
    else:
        fail("self-test accepted duplicate JSON keys")
    try:
        strict_json(b"\xff", "self-test")
    except ValueError as error:
        if "invalid-json-or-duplicate-key" not in str(error):
            fail("malformed UTF-8 control produced the wrong diagnostic")
        controls.append("malformed-utf8")
    else:
        fail("self-test accepted malformed UTF-8")

    composed, decomposed = "caf\u00e9", "cafe\u0301"
    if composed == decomposed or sha256(composed.encode("utf-8")) == sha256(decomposed.encode("utf-8")):
        fail("self-test Unicode identity was normalized")
    if _sorted_unique_strings(sorted([composed, decomposed]), "Unicode IDs changed") != sorted([composed, decomposed]):
        fail("self-test exact decoded IDs were changed")
    composed_path, decomposed_path = "fixtures/caf\u00e9.gb", "fixtures/cafe\u0301.gb"
    one_row = [{"path": composed_path}]
    if (relative_path(composed_path) != composed_path or
            path_content_identity(one_row, {composed_path: b"fixture\0bytes"}, b"utf8-fixture") ==
            path_content_identity([{"path": decomposed_path}],
                                  {decomposed_path: b"fixture\0bytes"}, b"utf8-fixture")):
        fail("self-test UTF-8 path identity normalized distinct byte paths")
    try:
        relative_path("fixtures/invalid-\udcff.gb")
    except ValueError as error:
        if "not-utf8" not in str(error):
            fail("invalid UTF-8 path produced the wrong diagnostic")
        controls.append("invalid-utf8-path")
    else:
        fail("self-test accepted a path that cannot be represented as UTF-8 bytes")
    positive_checks.append("exact-unicode-id-and-byte-digest")

    with tempfile.TemporaryDirectory(prefix="gabbaboy-support-ledger-inputs-") as temporary:
        temp_root = pathlib.Path(temporary)
        (temp_root / "tests").mkdir()
        (temp_root / "build").mkdir()
        (temp_root / "tests/input.dat").write_bytes(b"input")
        (temp_root / "build/bin.dat").write_bytes(b"binary")
        for row in data["source_inputs"]:
            if row["path"] == "tests/input.dat":
                continue
            destination = temp_root / row["path"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(evidence_raw)
        validate_source_bindings(data, temp_root)
        (temp_root / "tests/input.dat").write_bytes(b"changed")
        try:
            validate_source_bindings(data, temp_root)
        except ValueError as error:
            if "source input is stale" not in str(error):
                fail("stale-source control produced the wrong diagnostic")
            controls.append("stale-source-input")
        else:
            fail("self-test accepted stale source input")
        (temp_root / "tests/input.dat").write_bytes(b"input")
        (temp_root / "build/bin.dat").write_bytes(b"changed")
        try:
            validate_source_bindings(data, temp_root)
        except ValueError as error:
            if "build input is stale" not in str(error):
                fail("stale-build control produced the wrong diagnostic")
            controls.append("stale-build-artifact")
        else:
            fail("self-test accepted stale build artifact")
    # SHIP-09 empty and single-entry edges: an empty or one-entry ledger must not stand in
    # for the required inventory.
    try:
        parse_ledger(b"", "0.2.0")
    except ValueError as error:
        if "exactly one delimited structured data block" not in str(error):
            fail("empty-ledger-file produced the wrong diagnostic: " + str(error))
        controls.append("empty-ledger-file")
    else:
        fail("empty-ledger-file: parse_ledger accepted a zero-byte ledger")
    empty_block = (BEGIN + "\n```json\n{}\n```\n" + END + "\n").encode("utf-8")
    try:
        parse_ledger(empty_block, "0.2.0")
    except ValueError as error:
        if "unsupported ledger schema" not in str(error):
            fail("empty-structured-block produced the wrong diagnostic: " + str(error))
        controls.append("empty-structured-block")
    else:
        fail("empty-structured-block: parse_ledger accepted an empty JSON object")
    empty_rows = copy.deepcopy(data)
    empty_rows["inventory"].update(case_ids=[], case_bindings=[])
    empty_rows["receipt"].update(case_ids=[], case_observations=[],
                                 counts=_count_receipt_cases([]),
                                 suite_model_mode_counts=_count_suite_model_modes([], []))
    try:
        validate_data_v2(empty_rows, "0.2.0", expected_case_count=2)
    except ValueError as error:
        if "required inventory membership" not in str(error):
            fail("empty-ledger-rows produced the wrong diagnostic: " + str(error))
        controls.append("empty-ledger-rows")
    else:
        fail("empty-ledger-rows: validate_data_v2 accepted a ledger with no case rows")
    single = _schema2_test_data(cases=1)
    validate_data_v2(single, "0.2.0", expected_case_count=1)
    positive_checks.append("single-entry-schema2-fixture")
    try:
        validate_data_v2(single, "0.2.0", expected_case_count=2)
    except ValueError as error:
        if "incomplete or narrowed" not in str(error):
            fail("single-entry-below-required produced the wrong diagnostic: " + str(error))
        controls.append("single-entry-below-required")
    else:
        fail("single-entry-below-required: a one-case ledger satisfied a two-case requirement")
    # SHIP-09 encoding edges: ledger identity is the SHA-256 of the exact bytes, and the
    # size bound counts bytes, not characters.
    lf_rel = tree_ledger(ROOT)
    lf_version = ledger_version(lf_rel)
    lf_raw = bounded_file(ROOT / lf_rel, MAX_LEDGER_BYTES, "ledger")
    lf_data = parse_ledger(lf_raw, lf_version)
    lf_sidecar = {"tag": "v" + lf_version, "ledger_sha256": sha256(lf_raw)}

    def identity_rejected(name: str, variant_raw: bytes) -> None:
        if sha256(variant_raw) == sha256(lf_raw):
            fail(name + ": variant bytes have the same digest as the LF ledger")
        if parse_ledger(variant_raw, lf_version) != lf_data:
            fail(name + ": variant did not parse to data equal to the LF ledger")
        try:
            verify_sidecar_data({**lf_sidecar, "ledger_sha256": sha256(variant_raw)}, lf_sidecar)
        except ValueError:
            controls.append(name)
        else:
            fail(name + ": sidecar digest of a different byte encoding was accepted")

    identity_rejected("crlf-ledger-identity-is-bytes", lf_raw.replace(b"\n", b"\r\n"))
    # Pinned branch: parse_ledger decodes with plain utf-8, which keeps U+FEFF as text, and
    # nothing rejects it. A BOM copy therefore parses equal but is a different byte identity.
    # If parsing is changed to reject a BOM this control fails so the change is deliberate.
    try:
        identity_rejected("bom-ledger-identity", b"\xef\xbb\xbf" + lf_raw)
    except ValueError as error:
        if str(error).startswith("bom-ledger-identity:"):
            raise
        fail("bom-ledger-identity: parse_ledger rejected a BOM-prefixed ledger; "
             "pinned branch is accept-with-different-digest (" + str(error) + ")")
    two_byte = "\u00e9".encode("utf-8")
    oversized = two_byte * (MAX_LEDGER_BYTES // 2) + b"x"
    if len(oversized) != MAX_LEDGER_BYTES + 1 or len(oversized.decode("utf-8")) >= MAX_LEDGER_BYTES:
        fail("byte-length-bound: fixture does not separate byte count from character count")
    try:
        parse_ledger(oversized, "0.2.0")
    except ValueError as error:
        if "bounded read size" not in str(error):
            fail("byte-length-bound produced the wrong diagnostic: " + str(error))
        controls.append("byte-length-bound")
    else:
        fail("byte-length-bound: parse_ledger accepted a ledger over the byte bound")
    if not controls:
        fail("self-test selected zero rejection controls")
    print("support ledger v0.2 self-test passed: positive=" + str(len(positive_checks)) +
          " rejected_controls=" + str(len(controls)) +
          " controls=" + ",".join(controls))


def self_test() -> None:
    ledger = working_tree_ledger()
    current = ledger_version(ledger)
    raw = (ROOT / ledger).read_bytes()
    data = parse_ledger(raw, current)
    manifests = {path: (ROOT / path).read_bytes() for path in data["manifest_paths"]}
    validate_manifest_set(data, manifests)
    mutations = [
        raw + b"\nsource_sha: 0123456789012345678901234567890123456789\n",
        raw.replace(b'"executed_denominator": 3', b'"executed_denominator": 2'),
        raw.replace(f'"version": "{current}"'.encode(), b'"version": "9.9.9"'),
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
            altered = parse_ledger(changed, current)
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
    names = ["v0.1.0.md", "v0.2.0.md", "README.md"]
    for tag, expected in (("v0.1.0", "v0.1.0.md"), ("v0.1.1", "v0.1.0.md"), ("v0.1.10", "v0.1.0.md"),
                          ("v0.2.0", "v0.2.0.md"), ("v0.2.1", "v0.2.0.md")):
        if select_ledger(names, tag) != f"{LEDGER_DIR}/{expected}":
            fail(f"self-test selected the wrong ledger for {tag}")
    for tag in ("v0.0.9", "v0.1", "0.1.1", "v0.1.1-rc1", "v1.0.0"):
        try:
            select_ledger(names, tag)
        except ValueError:
            continue
        fail(f"self-test accepted tag without an applicable ledger: {tag}")
    for missing_names, tag in ((["v0.1.0.md"], "v0.2.0"),
                               (["v0.1.0.md"], "v0.2.1")):
        try:
            select_ledger(missing_names, tag)
        except ValueError:
            continue
        fail("self-test allowed exact-ledger or cross-scope fallback")
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
        for relative in [ledger, *data["manifest_paths"]]:
            destination = repository / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, destination)
        environment = dict(os.environ)
        environment.update({"GIT_AUTHOR_NAME": "GabbaBoy Test", "GIT_AUTHOR_EMAIL": "test@example.invalid",
                            "GIT_COMMITTER_NAME": "GabbaBoy Test", "GIT_COMMITTER_EMAIL": "test@example.invalid"})
        subprocess.run(["git", "init", "-q"], cwd=repository, env=environment, check=True)
        subprocess.run(["git", "add", ledger, *data["manifest_paths"]],
                       cwd=repository, env=environment, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "fixture"], cwd=repository,
                       env=environment, check=True)
        fake_sha = git("rev-parse", "HEAD", cwd=repository).decode().strip()
        patch_tag = "v{}.{}.{}".format(*(int(part) + (index == 2) for index, part in enumerate(current.split("."))))
        for tag in (f"v{current}", patch_tag):
            subprocess.run(["git", "tag", tag, fake_sha], cwd=repository, env=environment, check=True)
        generated = build_sidecar(f"v{current}", fake_sha, repository)
        if generated["source_sha"] != fake_sha or generated["ledger"]["sha256"] != hashlib.sha256(raw).hexdigest():
            fail("self-test generated sidecar does not bind exact source and ledger bytes")
        patch = build_sidecar(patch_tag, fake_sha, repository)
        if (patch["tag"], patch["version"], patch["ledger_version"]) != (patch_tag, patch_tag[1:], current) \
                or patch["ledger"] != generated["ledger"]:
            fail("self-test patch release did not bind the unchanged lower ledger")
        for key in ("source_sha", "ledger", "fixture_manifest_identities"):
            altered = dict(generated)
            altered[key] = None
            try:
                verify_sidecar_data(altered, generated)
            except ValueError:
                continue
            fail(f"self-test accepted altered sidecar {key}")
    print("support ledger self-test passed: tagged sidecar binding, newest-applicable ledger selection, scope, corpus order, digests, malformed UTF-8, duplicate keys, denominator and claim controls")


def self_test_static_ledger() -> None:
    """Drive check_ledger_static through its production entry over a private copy of the covered inputs."""
    ledger_rel = tree_ledger(ROOT)
    ledger = parse_ledger(bounded_file(ROOT / ledger_rel, MAX_LEDGER_BYTES, "ledger"), ledger_version(ledger_rel))
    rows = ledger["source_inputs"]
    if not rows:
        fail("static ledger self-test has no covered source inputs")
    producer = ledger["receipt"]["producer_revision"]
    with tempfile.TemporaryDirectory(prefix="gabbaboy-static-ledger-") as temporary:
        copy_root = pathlib.Path(temporary)
        for relative in [ledger_rel]:
            target = copy_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / relative).read_bytes())
        for row in rows:
            relative = row["path"]
            target = copy_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(immutable_git_file(ROOT, producer, relative))
        check_ledger_static(copy_root, run_inventory=False, ledger_rel=ledger_rel)
        controls = 0
        victim = copy_root / rows[0]["path"]
        original = victim.read_bytes()
        victim.write_bytes(original + b"\n")
        try:
            check_ledger_static(copy_root, run_inventory=False, ledger_rel=ledger_rel)
        except ValueError as error:
            if "source input is stale" not in str(error):
                fail("static ledger control rejected a changed covered input for the wrong reason: " + str(error))
            controls += 1
        else:
            fail("static ledger accepted a changed covered source input")
        victim.write_bytes(original)
        victim.unlink()
        try:
            check_ledger_static(copy_root, run_inventory=False, ledger_rel=ledger_rel)
        except (ValueError, OSError):
            controls += 1
        else:
            fail("static ledger accepted a missing covered source input")
        victim.write_bytes(original)
        # Added-case and removed-case inventory controls: the denominator is exact, so a ledger that claims
        # one more or one fewer required case than the independent inventory must be rejected by the
        # production entry for the membership reason, never by an unrelated parse error.
        ledger_bytes = (ROOT / ledger_rel).read_bytes()
        denominator = b'"required_case_count": %d' % V2_REQUIRED_CASES
        if ledger_bytes.count(denominator) != 1:
            fail("static ledger self-test: the required-case denominator must appear exactly once")
        for label, count in (("added-case-inventory", V2_REQUIRED_CASES + 1),
                             ("removed-case-inventory", V2_REQUIRED_CASES - 1)):
            (copy_root / ledger_rel).write_bytes(
                ledger_bytes.replace(denominator, b'"required_case_count": %d' % count))
            try:
                check_ledger_static(copy_root, run_inventory=False, ledger_rel=ledger_rel)
            except ValueError as error:
                if "required inventory membership is incomplete or narrowed" not in str(error):
                    fail("static ledger control " + label + " was rejected for the wrong reason: " + str(error))
                controls += 1
            else:
                fail("static ledger accepted a " + label + " denominator")
        (copy_root / ledger_rel).write_bytes(b"not a ledger\n")
        try:
            check_ledger_static(copy_root, run_inventory=False, ledger_rel=ledger_rel)
        except ValueError:
            controls += 1
        else:
            fail("static ledger accepted an unparseable ledger")
    if controls != 5:
        fail("static ledger self-test did not run all of its controls")
    print("support ledger static self-test passed: positive=1 rejected_controls=5 controls=changed-covered-input,missing-covered-input,added-case-inventory,removed-case-inventory,unparseable-ledger")


def self_test_v2_sidecar() -> None:
    """Exercise full-membership sidecars without relying on ignored build outputs."""
    global EVIDENCE_ONLY
    ledger_path = ROOT / tree_ledger(ROOT)
    ledger_raw = bounded_file(ledger_path, MAX_LEDGER_BYTES, "ledger")
    data = parse_ledger(ledger_raw, ledger_version(ledger_path.name))
    validate_data_v2(data, data["version"])
    receipt_path = pathlib.Path("build/cgb-corpus-receipt.json")
    # The tracked ledger is a frozen producer snapshot. Its source identity must
    # be read from that receipt's immutable producer commit, not today's HEAD.
    base_revision = data["receipt"]["producer_revision"]
    source_bytes = {}
    for row in data["source_inputs"]:
        raw = git("show", f"{base_revision}:{row['path']}")
        if sha256(raw) != row["sha256"] or len(raw) != row["size_bytes"]:
            fail("self-test tagged source differs from the tracked ledger:" + row["path"])
        source_bytes[row["path"]] = raw
    inventory_raw = source_bytes[data["inventory"]["path"]]
    inventory = strict_json(inventory_raw, "self-test-inventory")
    author_env = dict(os.environ)
    author_env.update({
        "GIT_AUTHOR_NAME": "GabbaBoy Test",
        "GIT_AUTHOR_EMAIL": "test@example.invalid",
        "GIT_COMMITTER_NAME": "GabbaBoy Test",
        "GIT_COMMITTER_EMAIL": "test@example.invalid",
    })
    controls = []
    positive_checks = []

    def git_fixture(repo: pathlib.Path, *args: str) -> str:
        completed = subprocess.run(["git", *args], cwd=repo, env=author_env,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, check=False, timeout=30)
        if completed.returncode != 0:
            fail("self-test Git fixture command failed: " + completed.stderr.strip())
        return completed.stdout.strip()

    def expect_rejected(name: str, action, expected: str) -> None:
        try:
            action()
        except ValueError as error:
            if expected not in str(error):
                fail("v0.2 sidecar control has wrong diagnostic:" + name + ":" + str(error))
            controls.append(name)
            return
        fail("v0.2 sidecar control was accepted:" + name)

    with tempfile.TemporaryDirectory(prefix="gabbaboy-v2-sidecar-") as temporary:
        temp_root = pathlib.Path(temporary)
        repository = temp_root / "tagged-repository"
        completed = subprocess.run(["git", "clone", "--shared", "--no-tags", "--no-checkout",
                                    str(ROOT), str(repository)],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, check=False, timeout=60)
        if completed.returncode != 0:
            fail("v0.2 sidecar fixture clone failed: " + completed.stderr.strip())
        git_fixture(repository, "checkout", "-b", "support-ledger-v2-self-test", base_revision)
        destination_receipt = repository / receipt_path
        destination_receipt.parent.mkdir(parents=True, exist_ok=True)

        def make_receipt(run_key: str) -> tuple[dict, bytes, dict[str, bytes]]:
            build_artifacts = []
            artifact_bytes = {}
            for old in data["receipt"]["build_artifacts"]:
                relative = old["path"]
                raw = ("synthetic sidecar contract artifact\n" + run_key + "\n" + relative + "\n").encode()
                artifact_bytes[relative] = raw
                build_artifacts.append({"path": relative, "size_bytes": len(raw), "sha256": sha256(raw)})
                destination = repository / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(raw)

            run_id = sha256(("synthetic-run:" + run_key).encode("ascii"))
            run_nonce_sha256 = sha256(("synthetic-nonce:" + run_key).encode("ascii"))
            log_sha256 = sha256(("synthetic-ctest-log:" + run_key).encode("ascii"))
            bindings = data["inventory"]["case_bindings"]
            case_names = sorted(row["test_name"] for row in bindings)
            identity = {
                "core_revision": base_revision,
                "run_id": run_id,
                "input_identity_sha256": sha256(("synthetic-input-identity:" + run_key).encode("ascii")),
                "inventory_sha256": sha256(inventory_raw),
                "hardware_qualified": False,
                "model": "CGB-CPU-E selected software model",
                "case_ids": data["inventory"]["case_ids"],
                "assertion_ids": {row["id"]: row["assertion_ids"] for row in bindings},
                "case_ctest_names": case_names,
                "aggregate_ctest_names": ["cgb_samesuite_apu_suite"],
                "ctest_names": sorted([*case_names, "cgb_samesuite_apu_suite"]),
                "ctest_log_sha256": log_sha256,
                "input_hashes": data["source_inputs"],
                "build_artifacts": build_artifacts,
            }
            identity["identity_sha256"] = canonical_sha256(identity)
            receipt = {
                "schema": "gabbaboy-cgb-corpus-receipt-v1",
                "version": 1,
                "status": "complete",
                "failure_codes": [],
                "identity": identity,
                "run": {
                    "id": run_id,
                    "started_at_ns": 100,
                    "completed_at_ns": 200,
                    "ctest_cases": V2_REQUIRED_CASES + 1,
                    "ctest_total_cases": 1133,
                    "ctest_log_sha256": log_sha256,
                    "run_nonce_sha256": run_nonce_sha256,
                },
                "cases": [copy.deepcopy(row["producer_case"])
                          for row in data["receipt"]["case_observations"]],
            }
            raw = json.dumps(receipt, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True).encode("utf-8") + b"\n"
            destination_receipt.write_bytes(raw)
            return receipt, raw, artifact_bytes

        receipt, receipt_raw, first_artifact_bytes = make_receipt("first-independent-run")
        fixture_data = build_v2_data(receipt, receipt_raw, inventory, inventory_raw,
                                     repository, receipt_path.as_posix(), source_bytes, version="0.2.0")
        validate_data_v2(fixture_data, "0.2.0")
        # The private fixture repository is always the v0.2.0 tag; only the version field may differ from the tracked ledger.
        if stable_v2_evidence(fixture_data) != stable_v2_evidence({**data, "version": "0.2.0"}):
            fail("synthetic full-membership receipt differs from stable historical evidence")
        ledger_text = render_v2_ledger(fixture_data)
        # The writer output for an independent synthetic receipt carries the generated disclosure and is a
        # generator fixed point, so --write-current needs no hand-inserted prose (RM-028, D-19).
        if disclosure_paragraphs(load_disclosure(ROOT), "0.2.0")[0] not in ledger_text:
            fail("synthetic-receipt ledger lacks the generated historical performance disclosure")
        require_generated(ledger_text.encode("utf-8"), "synthetic-receipt ledger", "0.2.0", load_disclosure(ROOT))
        # Drive the writer tail of --write-current into a disposable output: the bytes are the generator
        # output (no text-mode newline translation), and a tagged tracked target is refused untouched.
        preview = repository / receipt_path.parent / "disclosure-preview.md"
        written = write_generated_ledger(fixture_data, ROOT, preview)
        if written != preview or preview.read_bytes() != ledger_text.encode("utf-8"):
            fail("write-current writer did not emit the exact generator bytes")
        fixture_ledger = repository / "docs/support/v0.2.0.md"
        fixture_ledger.parent.mkdir(parents=True, exist_ok=True)
        fixture_ledger.write_text(ledger_text, encoding="utf-8")
        git_fixture(repository, "add", "docs/support/v0.2.0.md")
        git_fixture(repository, "commit", "-m", "test: create complete v0.2 sidecar contract fixture")
        source_sha = git_fixture(repository, "rev-parse", "HEAD")
        for tag in ("v0.2.0", "v0.2.1"):
            git_fixture(repository, "tag", tag, source_sha)
        # A tagged release's tracked ledger is historical: the writer refuses it and leaves the bytes untouched.
        tracked_before = fixture_ledger.read_bytes()
        try:
            write_generated_ledger(fixture_data, repository)
        except ValueError as error:
            if "ledger-target-tagged" not in str(error):
                fail(f"write-current mis-rejected a tagged target: {error}")
        else:
            fail("write-current accepted a tagged tracked target")
        if fixture_ledger.read_bytes() != tracked_before:
            fail("write-current modified tagged ledger bytes")
        # Keep HEAD at the receipt producer's base revision so this synthetic
        # contract fixture cannot be mistaken for a CTest execution receipt.
        git_fixture(repository, "checkout", "--detach", base_revision)

        generated = build_sidecar("v0.2.0", source_sha, repository, receipt_path)
        if (generated.get("schema_version") != 2 or
                generated.get("ledger", {}).get("path") != "docs/support/v0.2.0.md" or
                generated.get("corpus_receipt_sha256") != sha256(receipt_raw) or
                generated.get("corpus_receipt_sha256") == data["receipt"]["sha256"] or
                generated.get("corpus_receipt_producer_revision") != receipt["identity"]["core_revision"] or
                generated.get("corpus_receipt_identity_sha256") != receipt["identity"]["identity_sha256"] or
                generated.get("corpus_receipt_input_identity_sha256") != receipt["identity"]["input_identity_sha256"] or
                generated.get("corpus_receipt_run_id") != receipt["run"]["id"] or
                generated.get("corpus_run") != fixture_data["receipt"]["run"] or
                generated.get("corpus_receipt_build_artifacts") != fixture_data["receipt"]["build_artifacts"] or
                generated.get("corpus_receipt_source_relation") != "ancestor" or
                generated.get("game_evidence") != data["game_evidence"]):
            fail("v0.2 sidecar positive fixture did not bind the exact tagged inputs")
        positive_checks.append("positive-v0.2-tagged-sidecar")

        second_receipt, second_raw, second_artifact_bytes = make_receipt("second-independent-run")
        second_sidecar = build_sidecar("v0.2.0", source_sha, repository, receipt_path)
        if (second_sidecar.get("corpus_receipt_sha256") != sha256(second_raw) or
                second_sidecar.get("corpus_receipt_sha256") == generated.get("corpus_receipt_sha256") or
                second_sidecar.get("corpus_receipt_run_id") == generated.get("corpus_receipt_run_id") or
                second_sidecar.get("corpus_receipt_build_artifacts") == generated.get("corpus_receipt_build_artifacts")):
            fail("independent fresh receipt provenance was not rebound to its supplied bytes and artifacts")
        positive_checks.append("independent-run-stable-ledger-and-fresh-provenance")

        patch_sidecar = build_sidecar("v0.2.1", source_sha, repository, receipt_path)
        if (patch_sidecar.get("ledger") != second_sidecar.get("ledger") or
                patch_sidecar.get("tag") != "v0.2.1" or
                patch_sidecar.get("corpus_receipt_sha256") != second_sidecar.get("corpus_receipt_sha256")):
            fail("v0.2 patch tag did not reuse its same-scope ledger")
        positive_checks.append("v0.2-patch-compatibility")

        # Downloaded-evidence verification (publish job): the receipt is an asset outside the checkout and
        # the producer's build files are absent. Only this opt-in mode accepts that; a present but altered
        # build file, and an outside receipt without the opt-in, are still rejected.
        outside_receipt = temp_root / "downloaded" / "cgb-corpus-receipt.json"
        outside_receipt.parent.mkdir()
        outside_receipt.write_bytes(second_raw)
        expect_rejected("receipt-outside-checkout-without-evidence-only",
                        lambda: build_sidecar("v0.2.0", source_sha, repository, outside_receipt),
                        "receipt path must stay inside the tagged repository")
        build_files = {row["path"]: (repository / row["path"]).read_bytes()
                       for row in second_receipt["identity"]["build_artifacts"]}
        for relative in build_files:
            (repository / relative).unlink()
        destination_receipt.unlink()
        try:
            expect_rejected("absent-build-without-evidence-only",
                            lambda: build_sidecar("v0.2.0", source_sha, repository, outside_receipt),
                            "receipt path must stay inside the tagged repository")
            cli_script = repository / "tests/scripts/verify-support-ledger.py"
            cli_script.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(pathlib.Path(__file__).resolve(), cli_script)
            retained_sidecar_path = temp_root / "retained-build-sidecar.json"
            retained_sidecar_path.write_text(
                json.dumps(second_sidecar, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            command = [sys.executable, "-I", str(cli_script), "--tag", "v0.2.0",
                       "--source-sha", source_sha, "--receipt", str(outside_receipt),
                       "--verify-sidecar", str(retained_sidecar_path), "--evidence-only"]
            completed = subprocess.run(command, cwd=repository, env=author_env,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       text=True, check=False, timeout=120)
            if completed.returncode == 0:
                fail("evidence-only CLI qualified a retained-build sidecar after all build artifacts "
                     f"were absent: exit={completed.returncode}; stdout={completed.stdout.strip()!r}; "
                     f"stderr={completed.stderr.strip()!r}")
            if "build-evidence-unavailable" not in completed.stderr:
                fail("evidence-only CLI rejected all-missing build evidence for the wrong reason: " +
                     completed.stderr.strip())
            if "verified source-bound support sidecar" in completed.stdout:
                fail("evidence-only CLI emitted qualifying success after every build artifact was absent")
            controls.append("cli-all-build-artifacts-absent-is-nonqualifying")
            EVIDENCE_ONLY = True
            downloaded = build_sidecar("v0.2.0", source_sha, repository, outside_receipt)
            expected_receipt_only = {
                "scope": "receipt-only",
                "qualification_status": "not-established",
                "required_count": len(build_files),
                "observed_count": 0,
                "skipped_count": len(build_files),
                "receipt_declared_identity_sha256": second_sidecar["build_evidence"][
                    "receipt_declared_identity_sha256"],
                "retained_build_identity_sha256": None,
            }
            if (downloaded.get("build_evidence") != expected_receipt_only or
                    downloaded.get("corpus_receipt_sha256") != second_sidecar.get("corpus_receipt_sha256") or
                    downloaded.get("corpus_receipt_build_artifacts") !=
                    second_sidecar.get("corpus_receipt_build_artifacts")):
                fail("downloaded receipt-only evidence overstated absent build bytes or changed receipt identity")
            receipt_only_path = temp_root / "receipt-only-sidecar.json"
            receipt_only_path.write_text(json.dumps(downloaded, indent=2, sort_keys=True) + "\n",
                                         encoding="utf-8")
            receipt_only_command = [sys.executable, "-I", str(cli_script), "--tag", "v0.2.0",
                                    "--source-sha", source_sha, "--receipt", str(outside_receipt),
                                    "--verify-sidecar", str(receipt_only_path), "--evidence-only"]
            completed = subprocess.run(receipt_only_command, cwd=repository, env=author_env,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       text=True, check=False, timeout=120)
            if (completed.returncode != 0 or
                    "qualification=not-established observed=0 skipped=" not in completed.stdout or
                    "verified source-bound support sidecar" in completed.stdout):
                fail("receipt-only CLI did not emit a scoped nonqualification result: "
                     f"exit={completed.returncode}; stdout={completed.stdout.strip()!r}; "
                     f"stderr={completed.stderr.strip()!r}")
            positive_checks.append("cli-receipt-only-scope-explicitly-nonqualifying")
            # Attached evidence: the producer job held the build, this job does not (D-112 gap round).
            attached_command = [sys.executable, "-I", str(cli_script), "--tag", "v0.2.0",
                                "--source-sha", source_sha, "--receipt", str(outside_receipt),
                                "--evidence-only", "--attached-evidence", "--verify-sidecar"]

            def run_attached(name: str, sidecar: dict):
                path = temp_root / (name + ".json")
                path.write_text(json.dumps(sidecar, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                return subprocess.run([*attached_command, str(path)], cwd=repository, env=author_env,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                      check=False, timeout=120)

            consistent = run_attached("attached-consistent", second_sidecar)
            if (consistent.returncode != 0 or ATTACHED_CONSISTENT not in consistent.stdout or
                    "verified source-bound support sidecar" in consistent.stdout or
                    "qualification=qualified" in consistent.stdout):
                fail("consistent attached retained-build evidence was not accepted as non-qualifying: "
                     f"exit={consistent.returncode}; stdout={consistent.stdout.strip()!r}; "
                     f"stderr={consistent.stderr.strip()!r}")
            positive_checks.append("cli-attached-retained-build-consistent")
            plain = subprocess.run([*attached_command[:-3], "--verify-sidecar",
                                    str(temp_root / "attached-consistent.json"), "--evidence-only"],
                                   cwd=repository, env=author_env, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True, check=False, timeout=120)
            if plain.returncode == 0 or "build-evidence-unavailable" not in plain.stderr:
                fail("evidence-only without --attached-evidence must still reject a retained-build sidecar")
            controls.append("evidence-only-alone-still-never-qualifies")

            def attached_mutant(name: str, mutate, expected_error: str) -> None:
                # In process: each CLI spawn is expensive on the Windows runner and the CLI path is covered above.
                variant = copy.deepcopy(second_sidecar)
                before = json.dumps(variant, sort_keys=True)
                mutate(variant)
                if json.dumps(variant, sort_keys=True) == before:
                    fail("attached-evidence mutation was inactive:" + name)
                expect_rejected(name, lambda: verify_attached_sidecar(variant, downloaded), expected_error)

            attached_mutant("attached-tampered-declared-identity",
                            lambda v: v["build_evidence"].update(receipt_declared_identity_sha256="0" * 64),
                            "attached-evidence-declared-identity")
            attached_mutant("attached-changed-non-build-field",
                            lambda v: v.update(inventory_sha256="f" * 64),
                            "differs from the tag")
            attached_mutant("attached-required-count-mismatch",
                            lambda v: v["build_evidence"].update(required_count=v["build_evidence"]["required_count"] + 1,
                                                                 observed_count=v["build_evidence"]["required_count"] + 1),
                            "attached-evidence-build-count")
            attached_mutant("attached-partial-observed-count",
                            lambda v: v["build_evidence"].update(observed_count=v["build_evidence"]["required_count"] - 1,
                                                                 skipped_count=1),
                            "attached-evidence-build-count")
            attached_mutant("attached-retained-without-identity",
                            lambda v: v["build_evidence"].update(retained_build_identity_sha256=None),
                            "attached-evidence-build-count")
            attached_mutant("attached-receipt-only-claims-qualification",
                            lambda v: v["build_evidence"].update(
                                scope="receipt-only", observed_count=0, skipped_count=v["build_evidence"]["required_count"],
                                retained_build_identity_sha256=None),
                            "build-evidence-unavailable")
            partial_name = sorted(build_files)[0]
            (repository / partial_name).parent.mkdir(parents=True, exist_ok=True)
            (repository / partial_name).write_bytes(build_files[partial_name])
            completed = subprocess.run(receipt_only_command, cwd=repository, env=author_env,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       text=True, check=False, timeout=120)
            if (completed.returncode == 0 or "build-evidence-partial" not in completed.stderr or
                    "verified source-bound support sidecar" in completed.stdout):
                fail("evidence-only CLI did not reject partial build evidence with its intended diagnostic: "
                     f"exit={completed.returncode}; stdout={completed.stdout.strip()!r}; "
                     f"stderr={completed.stderr.strip()!r}")
            controls.append("cli-partial-build-evidence-rejected")
            (repository / partial_name).unlink()
            tampered = sorted(build_files)[0]
            (repository / tampered).parent.mkdir(parents=True, exist_ok=True)
            (repository / tampered).write_bytes(build_files[tampered] + b"tampered\n")
            expect_rejected("present-build-file-still-checked-in-evidence-only",
                            lambda: build_sidecar("v0.2.0", source_sha, repository, outside_receipt),
                            "build input is stale")
        finally:
            EVIDENCE_ONLY = False
            for relative, raw in build_files.items():
                (repository / relative).parent.mkdir(parents=True, exist_ok=True)
                (repository / relative).write_bytes(raw)
            destination_receipt.write_bytes(second_raw)

        expect_rejected("missing-v2-receipt",
                        lambda: build_sidecar("v0.2.0", source_sha, repository),
                        "schema-2 sidecars require --receipt")
        expect_rejected("wrong-tag-source-sha",
                        lambda: build_sidecar("v0.2.0", "0" * 40, repository, receipt_path),
                        "supplied source SHA does not resolve")
        for key, value in (("source_sha", "0" * 40),
                           ("ledger", {**second_sidecar["ledger"], "git_blob_oid": "0" * 40}),
                           ("corpus_receipt_sha256", "0" * 64),
                           ("inventory_sha256", "0" * 64),
                           ("corpus_receipt_run_id", "0" * 64),
                           ("corpus_receipt_build_artifacts", []),
                           ("disposition_identities", []),
                           ("covered_source_inputs", []),
                           ("suite_model_mode_counts", []),
                           ("game_evidence", {"status": "present"})):
            altered = copy.deepcopy(second_sidecar)
            altered[key] = value
            expect_rejected("altered-sidecar-" + key,
                            lambda altered=altered: verify_sidecar_data(altered, second_sidecar),
                            "sidecar source SHA")

        saved_receipt = destination_receipt.read_bytes()
        changed_bytes = saved_receipt + b" \n"
        destination_receipt.write_bytes(changed_bytes)
        changed_bytes_sidecar = build_sidecar("v0.2.0", source_sha, repository, receipt_path)
        if (changed_bytes_sidecar.get("corpus_receipt_sha256") != sha256(changed_bytes) or
                changed_bytes_sidecar.get("corpus_receipt_sha256") == second_sidecar.get("corpus_receipt_sha256")):
            fail("receipt byte-identity control did not use the supplied receipt bytes")
        expect_rejected("old-sidecar-after-receipt-bytes-change",
                        lambda: verify_sidecar_data(second_sidecar, changed_bytes_sidecar),
                        "sidecar source SHA")
        destination_receipt.write_bytes(saved_receipt)
        positive_checks.append("fresh-receipt-byte-digest")

        changed_outcome = copy.deepcopy(second_receipt)
        passing_case = next(row for row in changed_outcome["cases"]
                            if row["observed_result"] == "pass")
        passing_case.update(observed_result="fail", evaluator_status="xfail", matched_xfail=True)
        changed_outcome_raw = json.dumps(changed_outcome, sort_keys=True,
                                         separators=(",", ":"), ensure_ascii=True).encode() + b"\n"
        destination_receipt.write_bytes(changed_outcome_raw)
        expect_rejected("changed-case-outcome",
                        lambda: build_sidecar("v0.2.0", source_sha, repository, receipt_path),
                        "unexpected failure")
        destination_receipt.write_bytes(saved_receipt)

        changed_assertion = copy.deepcopy(second_receipt)
        assertion_case = changed_assertion["cases"][0]
        assertion = assertion_case["assertions"][0]
        assertion["observed_result"] = "fail" if assertion.get("observed_result") == "pass" else "pass"
        changed_assertion_raw = json.dumps(changed_assertion, sort_keys=True,
                                           separators=(",", ":"), ensure_ascii=True).encode() + b"\n"
        destination_receipt.write_bytes(changed_assertion_raw)
        expect_rejected("changed-assertion-observation",
                        lambda: build_sidecar("v0.2.0", source_sha, repository, receipt_path),
                        "stable evidence differs")
        destination_receipt.write_bytes(saved_receipt)
        artifact_path = next(iter(second_artifact_bytes))
        artifact_file = repository / artifact_path
        artifact_file.write_bytes(second_artifact_bytes[artifact_path] + b"changed")
        expect_rejected("changed-build-artifact-bytes",
                        lambda: build_sidecar("v0.2.0", source_sha, repository, receipt_path),
                        "build input is stale")
        artifact_file.write_bytes(second_artifact_bytes[artifact_path])

        source_path = data["source_inputs"][0]["path"]
        git_fixture(repository, "checkout", "-b", "sidecar-mutated-source", source_sha)
        source_file = repository / source_path
        source_file.write_bytes(source_file.read_bytes() + b"\nself-test source mutation\n")
        git_fixture(repository, "add", source_path)
        git_fixture(repository, "commit", "-m", "test: mutate covered source identity")
        changed_source_sha = git_fixture(repository, "rev-parse", "HEAD")
        git_fixture(repository, "tag", "v0.2.4", changed_source_sha)
        git_fixture(repository, "checkout", "--detach", base_revision)
        expect_rejected("changed-tagged-source-input",
                        lambda: build_sidecar("v0.2.4", changed_source_sha, repository, receipt_path),
                        "tagged source input differs from ledger")

        base_ledger_text = ledger_text

        def tagged_ledger_variant(name: str, tag: str, mutate) -> None:
            branch = "sidecar-" + name
            git_fixture(repository, "checkout", "-b", branch, source_sha)
            variant = {**copy.deepcopy(data), "version": "0.2.0"}  # the private fixture repository is always the v0.2.0 tag
            mutate(variant)
            text = base_ledger_text
            start = text.index(BEGIN)
            end = text.index(END, start)
            block_start = text.index("```json", start)
            json_start = text.index("\n", block_start) + 1
            json_end = text.rindex("```", json_start, end)
            rewritten = (text[:json_start] + json.dumps(variant, indent=2, sort_keys=True, ensure_ascii=False) +
                         "\n" + text[json_end:])
            (repository / "docs/support/v0.2.0.md").write_text(rewritten, encoding="utf-8")
            git_fixture(repository, "add", "docs/support/v0.2.0.md")
            git_fixture(repository, "commit", "-m", "test: alter disposition identities")
            variant_sha = git_fixture(repository, "rev-parse", "HEAD")
            git_fixture(repository, "tag", tag, variant_sha)
            git_fixture(repository, "checkout", "--detach", base_revision)
            expect_rejected(name,
                            lambda: build_sidecar(tag, variant_sha, repository, receipt_path),
                            "disposition")

        tagged_ledger_variant("omitted-disposition-identity", "v0.2.2",
                              lambda altered: altered["disposition_identities"].pop())
        tagged_ledger_variant("duplicate-disposition-identity", "v0.2.3",
                              lambda altered: altered["disposition_identities"].append(
                                  copy.deepcopy(altered["disposition_identities"][0])))

    with tempfile.TemporaryDirectory(prefix="gabbaboy-v2-scope-") as temporary:
        repository = pathlib.Path(temporary)
        legacy = repository / "docs/support/v0.1.0.md"
        legacy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / "docs/support/v0.1.0.md", legacy)
        subprocess.run(["git", "init", "-q"], cwd=repository, env=author_env, check=True)
        subprocess.run(["git", "add", "docs/support/v0.1.0.md"], cwd=repository,
                       env=author_env, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "fixture"], cwd=repository,
                       env=author_env, check=True)
        missing_sha = git_fixture(repository, "rev-parse", "HEAD")
        git_fixture(repository, "tag", "v0.2.0", missing_sha)
        git_fixture(repository, "tag", "v0.2.1", missing_sha)
        expect_rejected("missing-exact-v0.2-ledger",
                        lambda: build_sidecar("v0.2.0", missing_sha, repository),
                        "exact v0.2.0 support ledger is missing")
        expect_rejected("cross-scope-fallback",
                        lambda: build_sidecar("v0.2.1", missing_sha, repository),
                        "major/minor scope")

    if not positive_checks:
        fail("v0.2 sidecar self-test selected zero positive checks")
    print("support ledger v0.2 sidecar self-test passed: positive=" +
          str(len(positive_checks)) + " rejected_controls=" + str(len(controls)) +
          " positives=" + ",".join(positive_checks) +
          " controls=" + ",".join(controls))


# RM-028 / D-19: the historical performance disclosure is generator output. Its facts live in one validated,
# source-bound managed input and are rendered into every ledger by render_v2_ledger, so --write-current never
# needs hand-inserted prose and a hand edit or a rewritten historical metric is caught by byte comparison.
DISCLOSURE_PATH = "tests/data/release-disclosure.json"
MAX_DISCLOSURE_BYTES = 64 * 1024
DISCLOSURE_MODELS = ("DMG-CPU-B",)
DISCLOSURE_TOP_KEYS = {"schema_version", "kind", "historical", "current_interpretation"}
DISCLOSURE_HISTORICAL_KEYS = {
    "comparison_release", "baseline_release", "candidate_source", "baseline_source", "workload", "model",
    "fixture", "half_dot_budget", "correctness_digest", "platform", "paired_samples", "warmups",
    "delta_percent", "margin_percent", "disposition",
}
DISCLOSURE_INTERPRETATION_KEYS = {"applies_after_version", "text"}
DISCLOSURE_TEXT = re.compile(r"[\x20-\x7e]{1,800}")


def _disclosure_invalid(reason: str) -> None:
    fail("REJECT disclosure-input-invalid: " + reason)


def _disclosure_int(value: object, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        _disclosure_invalid(f"{name} must be an integer in [{low}, {high}]")
    return value


def _disclosure_pattern(value: object, name: str, pattern: str) -> str:
    if type(value) is not str or re.fullmatch(pattern, value) is None:
        _disclosure_invalid(f"{name} is malformed")
    return value


def _disclosure_keys(value: object, name: str, expected: set) -> dict:
    if type(value) is not dict:
        _disclosure_invalid(f"{name} must be an object")
    missing = sorted(expected - set(value))
    unknown = sorted(set(value) - expected)
    if missing:
        _disclosure_invalid(f"{name} omits {','.join(missing)}")
    if unknown:
        _disclosure_invalid(f"{name} has unclassified field {','.join(unknown)}")
    return value


def validate_disclosure(data: object, root: pathlib.Path = ROOT, bind: bool = True) -> dict:
    """Validate shape, value domains and (with bind) the source identities against immutable Git objects."""
    data = _disclosure_keys(data, "disclosure", DISCLOSURE_TOP_KEYS)
    if data["schema_version"] != 1 or type(data["schema_version"]) is not int:
        _disclosure_invalid("schema_version must be 1")
    if data["kind"] != "historical-performance-disclosure":
        _disclosure_invalid("kind must be historical-performance-disclosure")
    historical = _disclosure_keys(data["historical"], "historical", DISCLOSURE_HISTORICAL_KEYS)
    for name in ("comparison_release", "baseline_release"):
        _disclosure_pattern(historical[name], name, r"v\d+\.\d+\.\d+")
    for name in ("candidate_source", "baseline_source"):
        _disclosure_pattern(historical[name], name, r"[0-9a-f]{40}")
    _disclosure_pattern(historical["workload"], "workload", r"[a-z0-9][a-z0-9-]{2,63}")
    if historical["model"] not in DISCLOSURE_MODELS:
        _disclosure_invalid("model is not a disclosed software model")
    fixture = _disclosure_keys(historical["fixture"], "fixture", {"path", "sha256"})
    try:
        relative_path(fixture["path"], "fixture-path-invalid")
    except ValueError:
        _disclosure_invalid("fixture path is malformed")
    _disclosure_pattern(fixture["sha256"], "fixture sha256", r"[0-9a-f]{64}")
    _disclosure_int(historical["half_dot_budget"], "half_dot_budget", 1, 10**12)
    _disclosure_pattern(historical["correctness_digest"], "correctness_digest", r"[0-9a-f]{16}")
    _disclosure_pattern(historical["platform"], "platform", r"[A-Za-z0-9][A-Za-z0-9 _.-]{0,63}")
    _disclosure_int(historical["paired_samples"], "paired_samples", 1, 100000)
    _disclosure_int(historical["warmups"], "warmups", 0, 10000)
    _disclosure_pattern(historical["delta_percent"], "delta_percent", r"[0-9]{1,3}\.[0-9]{2}")
    _disclosure_pattern(historical["margin_percent"], "margin_percent", r"[0-9]{1,3}\.[0-9]{2}")
    _disclosure_pattern(historical["disposition"], "disposition", r"[a-z][a-z-]{2,63}")
    interpretation = _disclosure_keys(data["current_interpretation"], "current_interpretation",
                                      DISCLOSURE_INTERPRETATION_KEYS)
    _disclosure_pattern(interpretation["applies_after_version"], "applies_after_version", r"\d+\.\d+\.\d+")
    text = _disclosure_pattern(interpretation["text"], "interpretation text", DISCLOSURE_TEXT.pattern)
    for word in ("advisory", "blocking"):
        if word not in text:
            _disclosure_invalid(f"interpretation text must state the {word} status")
    if bind:
        if tag_commit(root, historical["comparison_release"]) != historical["candidate_source"]:
            fail("REJECT disclosure-source-unbound: candidate_source is not the "
                 f"{historical['comparison_release']} tag commit")
        if tag_commit(root, historical["baseline_release"]) != historical["baseline_source"]:
            fail("REJECT disclosure-source-unbound: baseline_source is not the "
                 f"{historical['baseline_release']} tag commit")
        blob = immutable_git_file(root, historical["candidate_source"], fixture["path"], MAX_INPUT_BYTES)
        if sha256(blob) != fixture["sha256"]:
            fail("REJECT disclosure-fixture-unbound: the fixture digest is not the candidate-source blob digest")
    return data


def load_disclosure(root: pathlib.Path = ROOT, bind: bool = True) -> dict:
    raw = bounded_file(root / DISCLOSURE_PATH, MAX_DISCLOSURE_BYTES, "disclosure-input")
    return validate_disclosure(strict_json(raw, "disclosure-input"), root, bind)


# D-11 / D-13: support claims are reviewed managed input. Their enums and required
# exclusions live here so editing the JSON cannot widen the supported surface.
CLAIMS_PATH = "tests/data/support-claims-v0.3.json"
MAX_CLAIMS_BYTES = 64 * 1024
CLAIMS_TOP_KEYS = {"schema_version", "kind", "applies_from_version", "claims", "non_claims"}
CLAIM_KEYS = {"id", "requirements", "statement", "models", "modes", "corpus",
              "platforms", "surface", "evidence", "non_claims"}
CLAIM_MODELS = {"DMG-CPU-B", "CGB-CPU-E"}
CLAIM_MODES = {"dmg", "cgb-compat", "cgb-native"}
CLAIM_PLATFORMS = {"linux-x64", "macos-arm64", "windows-x64"}
CLAIM_SURFACES = {"core-api", "runner-host-mode", "macos-player"}
REQUIRED_CLAIM_IDS = {
    "state-api", "state-continuation", "state-refusal", "state-canonical-pins",
    "state-battery-rtc", "host-raw-save", "host-signals-exit", "host-format-table", "player-slots",
}
REQUIRED_NON_CLAIMS = {
    "no-cross-version-state", "no-third-party-state-interop", "no-power-loss-durability",
    "no-windows-host-mode", "no-linux-windows-player", "no-cgb-game-level-evidence",
    "no-oracle-replay-from-forks", "no-crc-authentication", "no-runner-wall-clock",
    "no-playstead-live-integration",
}
REQUIRED_CLAIM_EVIDENCE = {
    "host_continuation", "host_cadence_retry", "host_signal_term", "host_exit_table_codes",
    "save_format_files", "save_format_completeness", "save_format_freeze", "host_contract_json",
    "host_contract_docs", "installed_host_smoke", "slot_message_table", "slot_reanchor_plan",
    "input_clock_after_load",
}
REQUIRED_CLAIM_REQUIREMENTS = {"HOST-01", "HOST-02", "HOST-03", "PLAY-01"}
CLAIM_TEXT = re.compile(r"[\x20-\x7e]{1,600}")
CLAIM_ID = re.compile(r"[a-z][a-z0-9-]{1,63}")
CLAIM_REQUIREMENT = re.compile(r"[A-Z]+-[0-9]{2}")


def _claims_invalid(reason: str) -> None:
    fail("REJECT claims-input-invalid: " + reason)


def _claims_keys(value: object, name: str, expected: set[str]) -> dict:
    if type(value) is not dict:
        _claims_invalid(f"{name} must be an object")
    missing = sorted(expected - set(value))
    unknown = sorted(set(value) - expected)
    if missing:
        _claims_invalid(f"{name} omits {','.join(missing)}")
    if unknown:
        _claims_invalid(f"{name} has unclassified field {','.join(unknown)}")
    return value


def _claims_tree_version(root: pathlib.Path, rev: str) -> str:
    raw = immutable_git_file(root, rev, "CMakeLists.txt", MAX_INPUT_BYTES)
    match = re.search(rb"^project\(\s*\w+\s+VERSION\s+(\d+\.\d+\.\d+)[\s)]", raw, re.M)
    if match is None:
        _claims_invalid("CMakeLists.txt has no plain X.Y.Z project VERSION")
    return match.group(1).decode("ascii")


def _claim_inventory(raw: bytes, path: str) -> set[str]:
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        _claims_invalid(f"{path} is not UTF-8")
    names = {line.strip() for line in text.splitlines()
             if line.strip() and not line.lstrip().startswith("#")}
    if not names or any(re.fullmatch(r"[A-Za-z0-9_-]+", name) is None for name in names):
        _claims_invalid(f"{path} is not a plain CTest name inventory")
    return names


def validate_claims(data: object, root: pathlib.Path, rev: str) -> dict:
    """Validate claim shape and recompute scope counts from immutable source objects."""
    data = _claims_keys(data, "claims", CLAIMS_TOP_KEYS)
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        _claims_invalid("schema_version must be 1")
    if data["kind"] != "scoped-support-claims" or data["applies_from_version"] != "0.3.0":
        _claims_invalid("kind or applies_from_version is not the v0.3.0 claims profile")

    tree_version = _claims_tree_version(root, rev)
    facts: dict[str, int] = {}
    for path, key, name in (
        ("tests/data/state-forks.json", "expected_case_count", "state-forks continuation cases"),
        ("tests/baseline/state-goldens-v1.json", "fixtures", "state portable golden pins"),
        ("docs/host-contract.json", "save_formats", "host save-format contract sections"),
        ("docs/host-contract.json", "exit_codes", "host exit-code definitions"),
    ):
        raw = immutable_git_file(root, rev, path, MAX_INPUT_BYTES)
        source = strict_json(raw, "claim-derived-input")
        if key == "expected_case_count":
            count = source.get(key)
        elif path.endswith("state-goldens-v1.json"):
            count = len(source.get(key, [])) if type(source.get(key)) is list else None
            release = source.get("release")
            pin_version = ".".join(str(release.get(part)) for part in ("major", "minor", "patch")) \
                if type(release) is dict else None
            if pin_version != tree_version:
                fail("REJECT claim-pins-stale: state goldens release differs from the CMake tree version")
        else:
            value = source.get(key)
            count = len(value) if type(value) in (dict, list) else None
        if type(count) is not int or count < 0:
            _claims_invalid(f"{path} does not contain a countable {key}")
        facts[name] = count

    state_forks = strict_json(immutable_git_file(root, rev, "tests/data/state-forks.json", MAX_INPUT_BYTES),
                              "claim-derived-input")
    if type(state_forks.get("expected_case_count")) is not int:
        _claims_invalid("state-forks expected_case_count is malformed")
    inventories = {
        "tests/expected-tests.txt": _claim_inventory(
            immutable_git_file(root, rev, "tests/expected-tests.txt", MAX_INPUT_BYTES),
            "tests/expected-tests.txt"),
        "tests/player/expected-tests.txt": _claim_inventory(
            immutable_git_file(root, rev, "tests/player/expected-tests.txt", MAX_INPUT_BYTES),
            "tests/player/expected-tests.txt"),
    }
    registered = set.union(*inventories.values())
    slot_tests = {name for name in registered
                  if name.startswith(("slot_", "player_slot_")) or name == "input_clock_after_load"}
    facts["player slot test inventory"] = len(slot_tests)

    cmake = immutable_git_file(root, rev, "cmake/ExpectedTests.cmake", MAX_INPUT_BYTES)
    try:
        cmake_text = cmake.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        _claims_invalid("cmake/ExpectedTests.cmake is not UTF-8")
    cmake_text = re.sub(r"(?m)#.*$", "", cmake_text)
    excluded_blocks = re.findall(r"list\s*\(\s*REMOVE_ITEM\s+expected_tests(.*?)\)", cmake_text, re.S)
    if not excluded_blocks:
        _claims_invalid("cmake/ExpectedTests.cmake has no expected_tests WIN32 removal list")
    win_excluded = set()
    for block in excluded_blocks:
        win_excluded.update(re.findall(r"[A-Za-z][A-Za-z0-9_]*", block))

    claims = data["claims"]
    if type(claims) is not list or len(claims) != len(REQUIRED_CLAIM_IDS):
        _claims_invalid("claims must contain exactly nine rows")
    non_claims = data["non_claims"]
    if type(non_claims) is not list:
        _claims_invalid("non_claims must be a list")
    non_claim_ids = set()
    for row in non_claims:
        row = _claims_keys(row, "non-claim", {"id", "statement"})
        if type(row["id"]) is not str or CLAIM_ID.fullmatch(row["id"]) is None:
            _claims_invalid("non-claim id is malformed")
        if type(row["statement"]) is not str or CLAIM_TEXT.fullmatch(row["statement"]) is None:
            _claims_invalid("non-claim statement is malformed ASCII text")
        if row["id"] in non_claim_ids:
            _claims_invalid(f"duplicate non-claim id {row['id']}")
        non_claim_ids.add(row["id"])
    if non_claim_ids != REQUIRED_NON_CLAIMS:
        missing = sorted(REQUIRED_NON_CLAIMS - non_claim_ids)
        fail("REJECT non-claim-missing: " + ",".join(missing or sorted(non_claim_ids - REQUIRED_NON_CLAIMS)))

    claim_ids = set()
    evidence_union: set[str] = set()
    requirement_union: set[str] = set()
    for index, raw_claim in enumerate(claims):
        if type(raw_claim) is not dict:
            _claims_invalid(f"claims[{index}] must be an object")
        # Scope omissions have their own stable D-14 diagnostic, including an omitted key.
        for axis in ("models", "platforms", "corpus", "surface"):
            value = raw_claim.get(axis)
            if axis == "surface":
                if type(value) is not str or not value:
                    fail(f"REJECT claim-scope-missing: claims[{index}] has missing or empty {axis}")
            elif type(value) is not list or not value:
                fail(f"REJECT claim-scope-missing: claims[{index}] has missing or empty {axis}")
        claim = _claims_keys(raw_claim, f"claims[{index}]", CLAIM_KEYS)
        claim_id = claim["id"]
        if type(claim_id) is not str or CLAIM_ID.fullmatch(claim_id) is None:
            _claims_invalid(f"claims[{index}].id is malformed")
        if claim_id in claim_ids:
            _claims_invalid(f"duplicate claim id {claim_id}")
        claim_ids.add(claim_id)
        if type(claim["statement"]) is not str or CLAIM_TEXT.fullmatch(claim["statement"]) is None:
            _claims_invalid(f"{claim_id}.statement is malformed ASCII text")
        if type(claim["models"]) is not list or not claim["models"] or any(
                type(item) is not str or item not in CLAIM_MODELS for item in claim["models"]):
            _claims_invalid(f"{claim_id}.models is outside the declared model enum")
        if type(claim["modes"]) is not list or not claim["modes"] or \
                any(type(item) is not str or item not in CLAIM_MODES for item in claim["modes"]):
            _claims_invalid(f"{claim_id}.modes is outside the declared mode enum")
        if type(claim["surface"]) is not str or claim["surface"] not in CLAIM_SURFACES:
            _claims_invalid(f"{claim_id}.surface is outside the declared surface enum")
        if type(claim["platforms"]) is not list or not claim["platforms"]:
            fail(f"REJECT claim-scope-missing: {claim_id}.platforms is empty")
        if any(type(item) is not str or item not in CLAIM_PLATFORMS for item in claim["platforms"]):
            fail(f"REJECT claim-platform-unpackaged: {claim_id} names a platform outside the package matrix")
        requirements = claim["requirements"]
        if type(requirements) is not list or not requirements or any(
                type(item) is not str or CLAIM_REQUIREMENT.fullmatch(item) is None for item in requirements):
            fail(f"REJECT claim-unbacked: {claim_id} has no valid requirement backing")
        requirement_union.update(requirements)
        corpus = claim["corpus"]
        if type(corpus) is not list or not corpus:
            fail(f"REJECT claim-scope-missing: {claim_id}.corpus is empty")
        for item in corpus:
            item = _claims_keys(item, f"{claim_id}.corpus row", {"name", "count"})
            name, count = item["name"], item["count"]
            if type(name) is not str or name not in facts or type(count) is not int:
                _claims_invalid(f"{claim_id}.corpus contains an unknown corpus or malformed count")
            if count != facts[name]:
                fail(f"REJECT claim-corpus-drift: {claim_id} {name} expected {facts[name]} observed {count}")
        evidence = claim["evidence"]
        if type(evidence) is not list or not evidence:
            fail(f"REJECT claim-unbacked: {claim_id} has no deciding CTest evidence")
        for name in evidence:
            if type(name) is not str or name not in registered:
                fail(f"REJECT claim-evidence-unregistered: {claim_id} cites {name!r}")
        evidence_union.update(evidence)
        if claim["surface"] == "macos-player" and set(claim["platforms"]) - {"macos-arm64"}:
            fail(f"REJECT claim-platform-unexercised: {claim_id} player surface is not packaged there")
        if "windows-x64" in claim["platforms"] and set(evidence) & win_excluded:
            fail(f"REJECT claim-platform-unexercised: {claim_id} cites a CTest removed on Windows")
        if type(claim["non_claims"]) is not list or not claim["non_claims"] or any(
                type(item) is not str or item not in non_claim_ids for item in claim["non_claims"]):
            _claims_invalid(f"{claim_id}.non_claims must reference declared non-claim ids")
    if claim_ids != REQUIRED_CLAIM_IDS:
        _claims_invalid("claim id set differs from the required nine D-13 rows")
    missing_evidence = sorted(REQUIRED_CLAIM_EVIDENCE - evidence_union)
    missing_requirements = sorted(REQUIRED_CLAIM_REQUIREMENTS - requirement_union)
    if missing_evidence or missing_requirements:
        missing = [*("evidence:" + item for item in missing_evidence),
                   *("requirement:" + item for item in missing_requirements)]
        fail("REJECT claim-unbacked: missing " + ",".join(missing))
    return data


def load_claims(root: pathlib.Path, rev: str) -> dict:
    raw = immutable_git_file(root, rev, CLAIMS_PATH, MAX_CLAIMS_BYTES)
    return validate_claims(strict_json(raw, "claims-input"), root, rev)


def claim_paragraphs(claims: dict, version: str) -> list[str]:
    """Render reviewed claim data as Markdown paragraphs with blank separators."""
    paragraphs = [
        "## Scoped support claims",
        f"Applies from v{claims['applies_from_version']} and describes software evidence for v{version}.",
        "**Boot:** skipped. The following claims are bounded by model, mode, corpus, platform, and surface.",
        "",
    ]
    for claim in claims["claims"]:
        models = ", ".join(claim["models"])
        modes = ", ".join(claim["modes"])
        platforms = ", ".join(claim["platforms"])
        corpus = "; ".join(f"{row['name']} ({row['count']})" for row in claim["corpus"])
        evidence = ", ".join(f"`{name}`" for name in claim["evidence"])
        paragraphs.extend([
            f"- **{claim['id']}:** {claim['statement']} Scope: models {models}; modes {modes}; "
            f"platforms {platforms}; surface {claim['surface']}; corpus {corpus}.",
            f"  Requirements: {', '.join(claim['requirements'])}. Evidence: {evidence}.",
            "",
        ])
    paragraphs.extend(["## Non-claims", ""])
    for item in claims["non_claims"]:
        paragraphs.extend([f"- **{item['id']}:** {item['statement']}", ""])
    return paragraphs


def disclosure_paragraphs(disclosure: dict, version: str) -> list[str]:
    """The ledger paragraphs, each followed by the blank separator line."""
    h = disclosure["historical"]
    block = (
        f"**The historical evidence for the DMG performance limitation:** the archived {h['comparison_release']} performance receipt\n"
        f"compares candidate source `{h['candidate_source']}` with\n"
        f"baseline source `{h['baseline_source']}`. Its\n"
        f"`{h['workload']}` workload uses {h['model']},\n"
        f"`{h['fixture']['path']}` (SHA-256\n"
        f"`{h['fixture']['sha256']}`), a\n"
        f"{h['half_dot_budget']:,} half-dot budget, and correctness digest `{h['correctness_digest']}`. The\n"
        f"{h['platform']} comparison used {h['paired_samples']} paired samples after {h['warmups']} warmups and recorded\n"
        f"**+{h['delta_percent']}% slower** with an approximate 95% mean margin of ±{h['margin_percent']}%; the historical\n"
        f"disposition was `{h['disposition']}`. This source-bound result\n"
        "is not a current approval, fresh result, or equivalent-speed claim.")
    paragraphs = [block, ""]
    interpretation = disclosure["current_interpretation"]
    after = tuple(int(part) for part in interpretation["applies_after_version"].split("."))
    if tuple(int(part) for part in version.split(".")) > after:
        paragraphs.extend([interpretation["text"], ""])
    return paragraphs


def refuse_tagged_target(root: pathlib.Path, version: str, target: pathlib.Path, default_target: pathlib.Path) -> None:
    """--write-current must never rewrite the tracked ledger of a release that already has its tag."""
    if target.resolve() != default_target.resolve():
        return
    result = subprocess.run(["git", "rev-parse", "--verify", "-q", f"refs/tags/v{version}^{{commit}}"], cwd=root,
                            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            check=False, timeout=10, env=git_environment())
    if result.returncode == 0:
        fail(f"REJECT ledger-target-tagged: v{version} is already tagged; its tracked ledger bytes are historical "
             "(write a disposable preview with --output)")


# RM-028 / D-19: the tagged ledgers must be fixed points of the actual generator. A ledger is accepted as
# generated only when rendering its own structured data reproduces its exact bytes, so any hand edit outside
# the generator (including a hand-inserted performance disclosure) is rejected.
DISCLOSED_LEDGERS = (
    # (tracked path, immutable tag whose blob must equal the tracked bytes, or None when a freeze check owns it)
    ("docs/support/v0.2.0.md", None),
    ("docs/support/v0.2.1.md", "v0.2.1"),
)


def git_environment() -> dict:
    environment = os.environ.copy()
    environment.update({
        "GIT_NO_LAZY_FETCH": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_TERMINAL_PROMPT": "0",
    })
    return environment


def tag_commit(root: pathlib.Path, tag: str) -> str:
    """Resolve a release tag to its commit, ignoring replace refs; a missing tag is a hard failure."""
    if TAG.fullmatch(tag) is None:
        fail(f"REJECT tag-malformed: {tag!r} is not a vX.Y.Z release tag")
    result = subprocess.run(["git", "rev-parse", "--verify", "-q", f"refs/tags/{tag}^{{commit}}"], cwd=root,
                            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, check=False, timeout=10, env=git_environment())
    value = result.stdout.strip()
    if result.returncode != 0 or re.fullmatch(r"[0-9a-f]{40,64}", value) is None:
        fail(f"REJECT tag-missing: {tag} is unreadable; fetch the tag (fetch-depth: 0) before checking the disclosure")
    return value


def first_difference(expected: bytes, observed: bytes) -> str:
    expected_lines = expected.split(b"\n")
    observed_lines = observed.split(b"\n")
    for index in range(max(len(expected_lines), len(observed_lines))):
        left = expected_lines[index] if index < len(expected_lines) else b"<end>"
        right = observed_lines[index] if index < len(observed_lines) else b"<end>"
        if left != right:
            return f"line {index + 1}"
    return "none"


def require_generated(raw: bytes, label: str, version: str, disclosure: dict,
                      root: pathlib.Path = ROOT, rev: str | None = None) -> bytes:
    """The bytes the actual generator renders from this ledger's own structured data; they must equal the ledger."""
    data = parse_ledger(raw, version)
    if tuple(int(part) for part in version.split(".")) >= (0, 3, 0):
        if rev is None:
            try:
                rev = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root,
                                              stderr=subprocess.DEVNULL, text=True).strip()
            except (OSError, subprocess.CalledProcessError):
                fail("REJECT claims-input-invalid: immutable revision is unavailable")
        claims = load_claims(root, rev)
        generated = render_v3_ledger(data, disclosure, claims).encode("utf-8")
    else:
        generated = render_v2_ledger(data, disclosure).encode("utf-8")
    if generated != raw:
        fail(f"REJECT ledger-not-generated: {label} is not the exact generator output "
             f"(first difference at {first_difference(generated, raw)})")
    return generated


def self_test_claims(root: pathlib.Path, rev: str) -> tuple[int, int]:
    """Prove the v0.3 generator path and one scoped-input refusal beside positives."""
    claims = load_claims(root, rev)
    positives = 1
    raw_v021 = immutable_git_file(root, rev, "docs/support/v0.2.1.md", MAX_LEDGER_BYTES)
    disclosure_raw = immutable_git_file(root, rev, DISCLOSURE_PATH, MAX_DISCLOSURE_BYTES)
    disclosure = validate_disclosure(strict_json(disclosure_raw, "disclosure-input"), root)
    old_data = parse_ledger(raw_v021, "0.2.1")
    require_generated(raw_v021, "docs/support/v0.2.1.md", "0.2.1", disclosure, root, rev)
    positives += 1

    v3_data = copy.deepcopy(old_data)
    v3_data["version"] = "0.3.0"
    v3_data["scope"]["modes"] = ["cgb-compat", "cgb-native", "dmg"]
    synthetic = render_v3_ledger(v3_data, disclosure, claims).encode("utf-8")
    if "## Scoped support claims" not in synthetic or "## Non-claims" not in synthetic:
        fail("v0.3 synthetic generator omitted the managed claims section")
    if require_generated(synthetic, "synthetic v0.3.0 ledger", "0.3.0", disclosure, root, rev) != synthetic:
        fail("v0.3 synthetic ledger was not a generator fixed point")
    positives += 1

    controls = 0
    invalid_scope = copy.deepcopy(claims)
    invalid_scope["claims"][0]["platforms"] = []
    try:
        validate_claims(invalid_scope, root, rev)
    except ValueError as error:
        if "claim-scope-missing" not in str(error):
            fail(f"claim scope control was rejected for the wrong reason: {error}")
    else:
        fail("claim scope control was accepted")
    controls += 1

    # Use create_current_ledger for a private 0.2 data seed, then render the
    # synthetic 0.3.0 ledger and exercise the production schema-2 sidecar path.
    from unittest import mock
    with tempfile.TemporaryDirectory(prefix="gabbaboy-claims-sidecar-") as temporary:
        fixture = pathlib.Path(temporary) / "repo"
        fixture.mkdir()

        def fixture_git(*arguments: str, capture: bool = False) -> str:
            result = subprocess.run(["git", *arguments], cwd=fixture, check=True,
                                    stdout=subprocess.PIPE if capture else subprocess.DEVNULL,
                                    stderr=subprocess.PIPE, text=True)
            return result.stdout.strip() if capture else ""

        fixture_git("init", "-q")
        fixture_git("config", "user.name", "GabbaBoy Automation")
        fixture_git("config", "user.email", "automation@users.noreply.github.com")
        (fixture / "CMakeLists.txt").write_text(
            "project(GabbaBoy VERSION 0.2.1 LANGUAGES C) # x-release-please-version\n", encoding="utf-8")
        (fixture / ".release-please-manifest.json").write_text('{".":"0.2.1"}\n', encoding="utf-8")
        (fixture / "tests/external").mkdir(parents=True)
        (fixture / "tests/external/cgb-corpus-inventory.json").write_text('{"synthetic":true}\n', encoding="utf-8")
        (fixture / "docs/support").mkdir(parents=True)
        (fixture / "build").mkdir()
        for path in ("CMakeLists.txt", ".release-please-manifest.json", "tests/external/cgb-corpus-inventory.json"):
            fixture_git("add", path)
        fixture_git("commit", "-q", "-m", "fixture base")
        fixture_revision = fixture_git("rev-parse", "HEAD", capture=True)
        receipt_path = fixture / "build/cgb-corpus-receipt.json"
        receipt_path.write_text(json.dumps({"identity": {"core_revision": fixture_revision}}) + "\n",
                                 encoding="utf-8")
        preview_path = fixture / "build/generated-v2.md"
        module = sys.modules[__name__]
        with mock.patch.object(module, "run_inventory_validator"), \
                mock.patch.object(module, "build_v2_data", return_value=copy.deepcopy(old_data)), \
                mock.patch.object(module, "run_existing_receipt_validator"), \
                mock.patch.object(module, "validate_data_v2"), \
                mock.patch.object(module, "validate_source_bindings"):
            synthetic_data = create_current_ledger(receipt_path, preview_path, fixture)

        synthetic_data = copy.deepcopy(synthetic_data)
        synthetic_data["version"] = "0.3.0"
        synthetic_data["scope"]["modes"] = ["cgb-compat", "cgb-native", "dmg"]
        source_raw = b'{"source":"claims fixture"}\n'
        inventory_raw = b'{"inventory":"claims fixture"}\n'
        source_path = "tests/data/claims-fixture.json"
        inventory_path = "tests/data/inventory-fixture.json"
        (fixture / "tests/data").mkdir(parents=True)
        (fixture / source_path).write_bytes(source_raw)
        (fixture / inventory_path).write_bytes(inventory_raw)
        synthetic_data["source_inputs"] = [
            {"path": source_path, "sha256": sha256(source_raw), "size_bytes": len(source_raw)},
            {"path": inventory_path, "sha256": sha256(inventory_raw), "size_bytes": len(inventory_raw)},
        ]
        synthetic_data["inventory"] = {"path": inventory_path, "sha256": sha256(inventory_raw)}
        synthetic_data["manifest_identities"] = []
        synthetic_data["disposition_identities"] = []
        synthetic_data["receipt"]["path"] = "build/cgb-corpus-receipt.json"
        ledger_rel = "docs/support/v0.3.0.md"
        ledger_raw = render_v3_ledger(synthetic_data, disclosure, claims).encode("utf-8")
        (fixture / ledger_rel).write_bytes(ledger_raw)
        for path in (source_path, inventory_path, ledger_rel):
            fixture_git("add", path)
        fixture_git("commit", "-q", "-m", "synthetic v0.3.0 ledger")
        fixture_git("tag", "v0.3.0")
        source_sha = fixture_git("rev-parse", "HEAD", capture=True)
        fixture_git("commit", "--allow-empty", "-q", "-m", "post-tag fixture head")
        with mock.patch.object(module, "_validate_run_identity", return_value={"core_revision": source_sha}), \
                mock.patch.object(module, "check_source_ancestry"), \
                mock.patch.object(module, "build_v2_data", return_value=copy.deepcopy(synthetic_data)), \
                mock.patch.object(module, "validate_data_v2"), \
                mock.patch.object(module, "stable_v2_evidence", return_value="same"), \
                mock.patch.object(module, "validate_source_bindings"), \
                mock.patch.object(module, "build_evidence_scope", return_value={"scope": "receipt-only"}):
            sidecar = build_v2_sidecar("v0.3.0", source_sha, fixture, ledger_rel, ledger_raw,
                                       synthetic_data, receipt_path)
        expected_oid = fixture_git("rev-parse", f"v0.3.0:{ledger_rel}", capture=True)
        if (sidecar.get("schema_version") != 2 or
                sidecar.get("ledger", {}).get("git_blob_oid") != expected_oid or
                sidecar.get("ledger", {}).get("sha256") != sha256(ledger_raw)):
            fail("synthetic v0.3 sidecar did not bind its ledger blob and claims bytes")
        positives += 1
    return positives, controls


def check_claims(root: pathlib.Path, rev: str) -> tuple[int, int]:
    claims = load_claims(root, rev)
    return len(claims["claims"]), len(claims["non_claims"])


def run_adoption_over_ledger(ledger_rel: str, ledger_raw: bytes, root: pathlib.Path = ROOT) -> None:
    """Run the actual adoption verifier over a disposable tree whose tree ledger is the supplied generated bytes."""
    script = root / "tests/scripts/verify-v02-adoption.py"
    spec = importlib.util.spec_from_file_location("gbb_verify_v02_adoption", script)
    adoption = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = adoption
    try:
        spec.loader.exec_module(adoption)
        with tempfile.TemporaryDirectory(prefix="gabbaboy-disclosure-adoption-") as temp:
            scratch = pathlib.Path(temp)
            adoption.copy_inputs(root, scratch)
            target = scratch / adoption.LEDGER
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(ledger_raw)
            result = subprocess.run([sys.executable, "-I", str(script), "--check", "docs", "--root", str(scratch)],
                                    cwd=root, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                                    check=False, timeout=45)
    finally:
        sys.modules.pop(spec.name, None)
    if result.returncode != 0:
        fail(f"REJECT adoption-rejected: {ledger_rel}: " + (result.stderr.strip() or result.stdout.strip()))


def require_tagged(root: pathlib.Path, ledger_rel: str, tag: str, raw: bytes) -> None:
    blob = immutable_git_file(root, tag_commit(root, tag), ledger_rel, MAX_LEDGER_BYTES)
    if blob != raw:
        fail(f"REJECT tagged-ledger-changed: {ledger_rel} differs from the {tag} tag blob")


def check_disclosure_generator(root: pathlib.Path = ROOT) -> tuple[int, int]:
    """Tagged ledgers are unchanged tag bytes, are generator fixed points and pass the adoption verifier."""
    checked = 0
    tagged = 0
    disclosure = load_disclosure(root)
    tree_ledger_rel = tree_ledger(root)
    paths = list(DISCLOSED_LEDGERS)
    if tree_ledger_rel not in {entry[0] for entry in paths}:
        paths.append((tree_ledger_rel, None))
    for ledger_rel, tag in paths:
        version = ledger_version(ledger_rel)
        raw = bounded_file(root / ledger_rel, MAX_LEDGER_BYTES, "ledger")
        if tag is not None:
            require_tagged(root, ledger_rel, tag, raw)
            tagged += 1
        require_generated(raw, ledger_rel, version, disclosure)
        checked += 1
    tree_raw = bounded_file(root / tree_ledger_rel, MAX_LEDGER_BYTES, "ledger")
    run_adoption_over_ledger(tree_ledger_rel, tree_raw, root)
    return checked, tagged


def self_test_disclosure(root: pathlib.Path = ROOT) -> tuple[int, int]:
    """Positive generator checks plus discriminating omission, value, source and handwritten-bypass controls.

    Every negative control must be rejected with its own diagnostic; an unrelated positive control runs
    alongside so a crash or setup failure cannot be mistaken for a semantic rejection.
    """
    positives = 0
    controls = 0
    disclosure = load_disclosure(root)
    positives += 1
    checked, tagged = check_disclosure_generator(root)
    if checked < 2 or tagged < 1:
        fail("disclosure self-test selected too few historical ledgers")
    positives += 1

    ledger_rel = "docs/support/v0.2.1.md"
    raw = bounded_file(root / ledger_rel, MAX_LEDGER_BYTES, "ledger")
    data = parse_ledger(raw, "0.2.1")
    text = raw.decode("utf-8")
    historical_block = disclosure_paragraphs(disclosure, "0.2.1")[0]
    if historical_block not in text:
        fail("the generated historical block is absent from the tagged ledger")

    # The current advisory interpretation is rendered only for ledgers after the last tagged version, and the
    # rendered ledger still passes the downstream adoption verifier (the unrelated passing control).
    current = render_v2_ledger({**data, "version": "0.2.2"}, disclosure)
    interpretation = disclosure["current_interpretation"]["text"]
    if interpretation not in current or interpretation in text:
        fail("the current interpretation is not scoped to ledgers after the tagged version")
    if current.count(historical_block) != 1:
        fail("a later ledger lost or duplicated the historical block")
    run_adoption_over_ledger(ledger_rel, current.encode("utf-8"), root)
    positives += 1

    def expect_rejected(name: str, action, reason: str) -> None:
        nonlocal controls
        try:
            action()
        except ValueError as error:
            if reason not in str(error):
                fail(f"disclosure control {name} was rejected for the wrong reason: {error}")
        else:
            fail(f"disclosure control {name} was accepted")
        controls += 1

    def mutated(change) -> dict:
        value = copy.deepcopy(disclosure)
        change(value)
        return value

    def validate(value: object, bind: bool = True):
        return lambda: validate_disclosure(value, root, bind)

    # Input omission, unclassified fields and malformed values.
    expect_rejected("omit-historical-block", validate(mutated(lambda v: v.pop("historical"))),
                    "disclosure-input-invalid")
    expect_rejected("omit-paired-samples", validate(mutated(lambda v: v["historical"].pop("paired_samples"))),
                    "disclosure-input-invalid")
    expect_rejected("omit-interpretation", validate(mutated(lambda v: v.pop("current_interpretation"))),
                    "disclosure-input-invalid")
    expect_rejected("unclassified-readiness-field",
                    validate(mutated(lambda v: v["historical"].update(approved=True))), "unclassified field")
    expect_rejected("boolean-for-count",
                    validate(mutated(lambda v: v["historical"].update(warmups=True))), "warmups")
    expect_rejected("interpretation-drops-advisory-status",
                    validate(mutated(lambda v: v["current_interpretation"].update(text="Timing is fine."))),
                    "interpretation text must state")
    expect_rejected("duplicate-json-key",
                    lambda: strict_json(b'{"schema_version": 1, "schema_version": 1}', "disclosure-input"),
                    "duplicate JSON key")

    # Source binding: identities must be the tagged commits and the fixture digest the candidate-source blob.
    expect_rejected("unbound-candidate-source",
                    validate(mutated(lambda v: v["historical"].update(
                        candidate_source=v["historical"]["baseline_source"]))), "disclosure-source-unbound")
    expect_rejected("unbound-baseline-source",
                    validate(mutated(lambda v: v["historical"].update(
                        baseline_source=v["historical"]["candidate_source"]))), "disclosure-source-unbound")
    expect_rejected("unbound-fixture-digest",
                    validate(mutated(lambda v: v["historical"]["fixture"].update(sha256="0" * 64))),
                    "disclosure-fixture-unbound")
    expect_rejected("missing-release-tag",
                    validate(mutated(lambda v: v["historical"].update(comparison_release="v9.9.9"))),
                    "tag-missing")

    # A rewritten historical metric is well-formed input, so only the exact-bytes comparison and the
    # downstream adoption verifier can reject it.
    altered = mutated(lambda v: v["historical"].update(delta_percent="14.87"))
    validate_disclosure(altered, root)
    altered_ledger = render_v2_ledger(data, altered).encode("utf-8")
    expect_rejected("altered-historical-value",
                    lambda: require_tagged(root, ledger_rel, "v0.2.1", altered_ledger), "tagged-ledger-changed")
    expect_rejected("altered-historical-value-adoption",
                    lambda: run_adoption_over_ledger(ledger_rel, altered_ledger, root),
                    "historical-performance-disclosure-missing")

    # Omission: a ledger regenerated without the block fails adoption; the fixed point also fails.
    omitted = text.replace(historical_block + "\n\n", "", 1).encode("utf-8")
    if omitted == raw:
        fail("the omission control did not remove the block")
    expect_rejected("omitted-disclosure-adoption",
                    lambda: run_adoption_over_ledger(ledger_rel, omitted, root),
                    "historical-performance-disclosure-missing")
    expect_rejected("omitted-disclosure-not-generated",
                    lambda: require_generated(omitted, ledger_rel, "0.2.1", disclosure), "ledger-not-generated")

    # Handwritten-success bypass: every required phrase is present, so adoption passes, but the bytes are not
    # generator output and the fixed point rejects them.
    reworded = text.replace("## Reconciled prior scope entries", "## Reconciled earlier scope entries", 1).encode("utf-8")
    run_adoption_over_ledger(ledger_rel, reworded, root)
    expect_rejected("handwritten-prose-edit",
                    lambda: require_generated(reworded, ledger_rel, "0.2.1", disclosure), "ledger-not-generated")
    relocated = text.replace(historical_block + "\n\n", "", 1) + "\n" + historical_block + "\n"
    run_adoption_over_ledger(ledger_rel, relocated.encode("utf-8"), root)
    expect_rejected("handwritten-disclosure-relocated",
                    lambda: require_generated(relocated.encode("utf-8"), ledger_rel, "0.2.1", disclosure),
                    "ledger-not-generated")

    # Tagged bytes: a tracked tagged ledger that differs from its tag blob in a single byte is rejected.
    flipped = bytearray(raw)
    flipped[100] ^= 1
    expect_rejected("tagged-ledger-byte-flip",
                    lambda: require_tagged(root, ledger_rel, "v0.2.1", bytes(flipped)), "tagged-ledger-changed")

    # --write-current may not rewrite the tracked ledger of a tagged release, but a disposable output and an
    # untagged version are accepted.
    default_target = root / ledger_rel
    expect_rejected("write-current-tagged-target",
                    lambda: refuse_tagged_target(root, "0.2.1", default_target, default_target),
                    "ledger-target-tagged")
    refuse_tagged_target(root, "0.2.1", root / "build/disclosure-preview.md", default_target)
    refuse_tagged_target(root, "9.9.9", root / "docs/support/v9.9.9.md", root / "docs/support/v9.9.9.md")
    positives += 1
    return positives, controls


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--self-test-v2", action="store_true")
    parser.add_argument("--tag")
    parser.add_argument("--source-sha")
    parser.add_argument("--output", type=pathlib.Path)
    parser.add_argument("--verify-sidecar", type=pathlib.Path)
    parser.add_argument("--check-current", action="store_true")
    parser.add_argument("--check-freeze", action="store_true",
                        help="the v0.2.0 ledger is the tag blob plus only the disclosed #93 block (D-29)")
    parser.add_argument("--self-test-freeze", action="store_true")
    parser.add_argument("--check-binding", action="store_true",
                        help="README links the ledger this tree's CMake/manifest version selects (D-28)")
    parser.add_argument("--self-test-binding", action="store_true")
    parser.add_argument("--derive-rehearsal-tag", metavar="REF",
                        help="print REHEARSAL_TAG=vX.Y.Z when REF is rehearsal/vX.Y.Z for this tree's own version")
    parser.add_argument("--root", type=pathlib.Path, default=ROOT,
                        help="tree to read the version from with --derive-rehearsal-tag (default: this checkout)")
    parser.add_argument("--print-version", action="store_true",
                        help="print the tree version (CMake project VERSION cross-checked with the manifest)")
    parser.add_argument("--check-ledger", action="store_true",
                        help="receipt-free check of the tracked ledger for this tree's version against its covered source inputs")
    parser.add_argument("--check-disclosure", action="store_true",
                        help="the tagged ledgers are unchanged tag bytes and exact generator output (RM-028, D-19)")
    parser.add_argument("--self-test-disclosure", action="store_true")
    parser.add_argument("--check-claims", action="store_true",
                        help="validate the immutable v0.3.0 managed support claims at --rev")
    parser.add_argument("--self-test-claims", action="store_true",
                        help="run v0.3.0 claim renderer positives and seeded rejection controls at --rev")
    parser.add_argument("--rev", help="full immutable 40-hex commit id for claims input and source facts")
    parser.add_argument("--write-current", action="store_true")
    parser.add_argument("--receipt", type=pathlib.Path)
    parser.add_argument("--attached-evidence", action="store_true",
                        help="with --verify-sidecar --evidence-only: accept a retained-build sidecar consistent with the "
                             "receipt; reports consistency, never qualification")
    parser.add_argument("--evidence-only", action="store_true",
                        help="with --verify-sidecar: the receipt is a downloaded asset and the producer's build is absent")
    args = parser.parse_args()
    if args.evidence_only:
        if not args.verify_sidecar:
            parser.error("--evidence-only is only accepted with --verify-sidecar")
        global EVIDENCE_ONLY
        EVIDENCE_ONLY = True
    if args.attached_evidence and not (args.verify_sidecar and args.evidence_only):
        parser.error("--attached-evidence requires --verify-sidecar and --evidence-only")
    try:
        if args.self_test_v2:
            self_test_v2()
            return 0
        if args.self_test:
            self_test()
            self_test_v2()
            self_test_v2_sidecar()
            self_test_static_ledger()
            positives, controls = self_test_disclosure()
            print(f"release-disclosure controls pass positives={positives} controls={controls}")
            return 0
        if args.print_version:
            print(tree_version())
            return 0
        if args.derive_rehearsal_tag is not None:
            print(derive_rehearsal_tag(args.derive_rehearsal_tag, args.root.resolve()))
            return 0
        if args.check_freeze:
            print(check_freeze())
            return 0
        if args.self_test_freeze:
            print(f"ledger-freeze self-test pass controls={self_test_freeze()}")
            return 0
        if args.check_binding:
            version, ledger = check_binding()
            print(f"support-ledger binding pass version={version} ledger={ledger}")
            return 0
        if args.self_test_binding:
            print(f"support-ledger binding self-test pass controls={self_test_binding()}")
            return 0
        if args.check_ledger:
            data = check_ledger_static()
            print("support-ledger static pass version=" + data["version"] + " cases=" +
                  str(data["receipt"]["counts"]["completed_cases"]) +
                  " source-inputs=" + str(len(data["source_inputs"])))
            return 0
        if args.check_current:
            if not args.receipt:
                parser.error("--check-current requires --receipt PATH")
            data = check_current(args.receipt)
            counts = data["receipt"]["counts"]
            print("support-ledger current pass version=" + data["version"] + " cases=" +
                  str(counts["completed_cases"]) +
                  " passes=" + str(counts["observed_pass_cases"]) +
                  " matched-xfails=" + str(counts["matched_xfail_cases"]) +
                  " assertions=" + str(counts["assertions"]))
            return 0
        if args.self_test_disclosure:
            positives, controls = self_test_disclosure()
            print(f"release-disclosure controls pass positives={positives} controls={controls}")
            return 0
        if args.check_disclosure:
            checked, tagged = check_disclosure_generator()
            print(f"release-disclosure generator pass ledgers={checked} tagged={tagged}")
            return 0
        if args.check_claims:
            if args.rev is None:
                parser.error("--check-claims requires --rev FULL_SHA")
            claims_count, non_claim_count = check_claims(ROOT, args.rev)
            print(f"support-claims pass claims={claims_count} non_claims={non_claim_count} rev={args.rev}")
            return 0
        if args.self_test_claims:
            if args.rev is None:
                parser.error("--self-test-claims requires --rev FULL_SHA")
            positives, controls = self_test_claims(ROOT, args.rev)
            print(f"support-claims controls pass positives={positives} controls={controls}")
            return 0
        if args.write_current:
            if not args.receipt:
                parser.error("--write-current requires --receipt PATH")
            data = create_current_ledger(args.receipt, args.output)
            counts = data["receipt"]["counts"]
            print("support-ledger wrote version=" + data["version"] + " cases=" +
                  str(counts["completed_cases"]) +
                  " passes=" + str(counts["observed_pass_cases"]) +
                  " matched-xfails=" + str(counts["matched_xfail_cases"]) +
                  " assertions=" + str(counts["assertions"]))
            return 0
        if not (args.tag and args.source_sha and (args.output or args.verify_sidecar)):
            parser.error("supply --tag, --source-sha and --output or --verify-sidecar, or use --self-test")
        sidecar = build_sidecar(args.tag, args.source_sha, ROOT, args.receipt)
        if args.verify_sidecar:
            observed = strict_json(bounded_file(args.verify_sidecar, MAX_LEDGER_BYTES,
                                                "sidecar"), "sidecar")
            if args.attached_evidence:
                statement = verify_attached_sidecar(observed, sidecar)
                if statement is not None:
                    print(statement)
                    return 0
            else:
                verify_sidecar_data(observed, sidecar)
            scope = sidecar.get("build_evidence", {})
            if scope.get("qualification_status") == "not-established":
                print("verified receipt-only support evidence; qualification=not-established "
                      f"observed={scope['observed_count']} skipped={scope['skipped_count']}")
            else:
                print(f"verified source-bound support sidecar for {args.tag} ({args.source_sha}) "
                      f"qualification=qualified build-evidence={scope.get('scope')} "
                      f"observed={scope.get('observed_count')} skipped={scope.get('skipped_count')}")
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(sidecar, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print(f"wrote source-bound support sidecar for {args.tag} ({args.source_sha})")
    except (ValueError, KeyError, OSError, TypeError, AttributeError, IndexError,
            subprocess.SubprocessError) as error:
        print(f"support-ledger verification failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
