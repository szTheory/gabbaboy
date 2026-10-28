#!/usr/bin/env python3
"""Cumulative DMG performance gate (Phase 16 TUNE-03, decisions D-13..D-17).

The gate compares valgrind cachegrind instruction counts (Ir, --cache-sim=no) of the head build with a
v0.2.0 build made in the same job, plus a native realtime floor. Ir is a deterministic proxy: it does not
see cache or branch effects, so it is a regression tripwire, not a performance claim. The limitation note
lives in the header of tests/baseline/perf-gate-v1.txt.

Modes (stdlib only, refuses python -O):
  --check-limits FILE [--root DIR] [--base-rev SHA]  validate pins and the immutable policy ratchet
  --evaluate --limits FILE --base DIR --head DIR --base-rev SHA [--realtime FILE]
             [--exception-receipt FILE ...identities] [--emit-exception-measurement FILE]
  --self-test                        run every control through the real CLI

Every limit comparison is exact integer or fractions.Fraction arithmetic. No float decides a verdict.
"""
import fractions
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import unittest

if not __debug__:
    sys.stderr.write("verify-perf-gate.py must not run with python -O\n")
    sys.exit(2)

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "data", "perf-gate"))
HALF_DOTS_PER_SECOND = 8388608  # GBB_MASTER_HALF_DOTS_PER_SECOND in src/core/gabbaboy.c
WORKLOAD = "original-wram-tracer-1m-half-dots-v1"
ROMS = ("tracer", "libbet", "visible-demo")
ROM_FIELDS = ("path", "sha256", "digest", "consumed_half_dots")
TOP_KEYS = ("schema", "ir_ratio_limit", "ir_floor", "determinism_limit", "realtime_floor")
POLICY_FILE = "tests/baseline/perf-gate-v1.txt"
LIMITS_BASE_REV = "947d6a9d177af6c04a5f9ea6abcc2c470ab9be57"
EXCEPTION_SCHEMA = "perf-gate-deterministic-exception-v1"


class Rejected(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def reject(code, message):
    raise Rejected(code, message)


def fraction(text, what, pattern=r"\d+(\.\d+)?|\d+/\d+"):
    if not re.fullmatch(pattern, text):
        reject("limits-schema", "%s is not an exact decimal or fraction: %r" % (what, text))
    value = fractions.Fraction(text)
    if value <= 0:
        reject("limits-schema", "%s must be positive: %r" % (what, text))
    return value


def parse_limits(path):
    try:
        with open(path, encoding="utf-8") as handle:
            lines = handle.read().split("\n")
    except OSError as error:
        reject("limits-schema", "cannot read limits file: %s" % error)
    raw = {}
    for number, line in enumerate(lines, 1):
        if not line.strip() or line.startswith("#"):
            continue
        if "=" not in line:
            reject("limits-schema", "line %d is not key=value" % number)
        key, value = line.split("=", 1)
        if key in raw:
            reject("limits-schema", "duplicate key %s" % key)
        raw[key] = value
    allowed = set(TOP_KEYS)
    for rom in ROMS:
        allowed.update("rom.%s.%s" % (rom, field) for field in ROM_FIELDS)
    for key in raw:
        if key not in allowed:
            reject("limits-schema", "unknown key %s" % key)
    for key in sorted(allowed):
        if key not in raw:
            reject("limits-schema", "missing key %s" % key)
    if raw["schema"] != "perf-gate-v1":
        reject("limits-schema", "schema must be perf-gate-v1")
    if not re.fullmatch(r"[1-9][0-9]*", raw["ir_floor"]):
        reject("limits-schema", "ir_floor is not a positive integer")
    limits = {
        "ir_ratio": fraction(raw["ir_ratio_limit"], "ir_ratio_limit", r"\d+/\d+"),
        "ir_floor": int(raw["ir_floor"]),
        "determinism": fraction(raw["determinism_limit"], "determinism_limit", r"\d+/\d+"),
        "realtime_floor": fraction(raw["realtime_floor"], "realtime_floor"),
        "roms": {},
    }
    for rom in ROMS:
        entry = {field: raw["rom.%s.%s" % (rom, field)] for field in ROM_FIELDS}
        if not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]):
            reject("limits-schema", "rom.%s.sha256 is not 64 lowercase hex digits" % rom)
        if not re.fullmatch(r"[0-9a-f]{16}", entry["digest"]):
            reject("limits-schema", "rom.%s.digest is not 16 lowercase hex digits" % rom)
        if not re.fullmatch(r"[1-9][0-9]*", entry["consumed_half_dots"]):
            reject("limits-schema", "rom.%s.consumed_half_dots is not a positive integer" % rom)
        if not re.fullmatch(r"[A-Za-z0-9._/-]+", entry["path"]) or entry["path"].startswith("/") \
                or ".." in entry["path"].split("/"):
            reject("limits-schema", "rom.%s.path is not a repository-relative path" % rom)
        entry["consumed_half_dots"] = int(entry["consumed_half_dots"])
        limits["roms"][rom] = entry
    return limits


def check_limits(path, root):
    limits = parse_limits(path)
    if root is not None:
        for rom, entry in limits["roms"].items():
            try:
                with open(os.path.join(root, entry["path"]), "rb") as handle:
                    actual = hashlib.sha256(handle.read()).hexdigest()
            except OSError as error:
                reject("limits-schema", "cannot read %s: %s" % (entry["path"], error))
            if actual != entry["sha256"]:
                reject("limits-schema", "rom.%s.sha256 pin does not match %s" % (rom, entry["path"]))
    return limits


def read_text(path, code):
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.read()
    except OSError as error:
        reject(code, "cannot read %s: %s" % (path, error))


def parse_cachegrind(path):
    """Total Ir from a cachegrind out-file made with --cache-sim=no."""
    text = read_text(path, "cachegrind-unreadable")
    events = [line for line in text.split("\n") if line.startswith("events:")]
    if len(events) != 1 or events[0].split() != ["events:", "Ir"]:
        reject("cachegrind-format", "%s: the events line must be exactly 'events: Ir'" % path)
    summary = [line for line in text.split("\n") if line.startswith("summary:")]
    if len(summary) != 1 or not re.fullmatch(r"summary: [0-9]+", summary[0]):
        reject("cachegrind-format", "%s: need exactly one 'summary: <Ir>' line" % path)
    return int(summary[0].split()[1])


def parse_measure_line(text, where):
    fields = {}
    for token in text.strip().split(" "):
        if "=" not in token:
            reject("measure-line-format", "%s: token without '=': %r" % (where, token))
        key, value = token.split("=", 1)
        if key in fields:
            reject("measure-line-format", "%s: duplicate field %s" % (where, key))
        fields[key] = value
    for key in ("workload", "consumed_half_dots", "elapsed_ns", "correctness_digest_fnv1a64"):
        if key not in fields:
            reject("measure-line-format", "%s: missing field %s" % (where, key))
    if not re.fullmatch(r"[0-9]+", fields["consumed_half_dots"]) or \
            not re.fullmatch(r"[0-9]+", fields["elapsed_ns"]):
        reject("measure-line-format", "%s: non-integer consumed_half_dots or elapsed_ns" % where)
    return {
        "workload": fields["workload"],
        "consumed": int(fields["consumed_half_dots"]),
        "elapsed_ns": int(fields["elapsed_ns"]),
        "digest": fields["correctness_digest_fnv1a64"],
    }


def read_side(directory, name, repeats, limits):
    side = {}
    fixture_dir = os.path.realpath(directory)
    immutable_canned_fixture = fixture_dir == os.path.realpath(DATA) or \
        fixture_dir.startswith(os.path.realpath(DATA) + os.sep)
    for rom in ROMS:
        irs = [parse_cachegrind(os.path.join(directory, "%s.cg.%d" % (rom, n)))
               for n in range(1, repeats + 1)]
        lines = []
        for repeat in range(1, repeats + 1):
            repeated_path = os.path.join(directory, "%s.line.%d" % (rom, repeat))
            if os.path.isfile(repeated_path):
                line_path = repeated_path
            elif repeat == 1 or immutable_canned_fixture:
                # Checked-in Phase 16 fixtures predate per-repeat measurement lines and are
                # independently SHA-pinned by perf.cmake. Real run directories must provide every repeat.
                line_path = os.path.join(directory, rom + ".line")
            else:
                reject("measure-line-repeat-missing", "%s/%s.line.%d is missing" % (name, rom, repeat))
            line = parse_measure_line(read_text(line_path, "measure-line-format"),
                                      "%s/%s.line.%d" % (name, rom, repeat))
            lines.append(line)
        side[rom] = {"irs": irs, "lines": lines}
    return side


def guard_digest(side, name, limits):
    for rom in ROMS:
        for repeat, line in enumerate(side[rom]["lines"], 1):
            if line["workload"] != WORKLOAD or line["digest"] != limits["roms"][rom]["digest"]:
                reject("workload-digest-mismatch", "%s %s repeat %d: workload %s digest %s, pinned digest %s" %
                       (name, rom, repeat, line["workload"], line["digest"], limits["roms"][rom]["digest"]))


def guard_vacuous(side, name, limits):
    for rom in ROMS:
        pinned = limits["roms"][rom]["consumed_half_dots"]
        for repeat, line in enumerate(side[rom]["lines"], 1):
            if line["consumed"] != pinned:
                reject("proxy-vacuous", "%s %s repeat %d: consumed_half_dots %d, pinned %d" %
                       (name, rom, repeat, line["consumed"], pinned))
        for ir in side[rom]["irs"]:
            if ir <= limits["ir_floor"]:
                reject("proxy-vacuous", "%s %s: Ir %d is not above the %d floor" %
                       (name, rom, ir, limits["ir_floor"]))


def immutable_limits(base_rev):
    if not isinstance(base_rev, str) or re.fullmatch(r"[0-9a-f]{40}", base_rev) is None:
        reject("ratchet-base-invalid", "--base-rev must be a resolved immutable 40-hex commit")
    resolved = subprocess.run(["git", "rev-parse", "--verify", "%s^{commit}" % base_rev],
                              cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    if resolved.returncode != 0 or resolved.stdout.strip() != base_rev:
        reject("ratchet-base-not-commit", "--base-rev does not resolve to that exact commit")
    blob = subprocess.run(["git", "show", "%s:%s" % (base_rev, POLICY_FILE)], cwd=REPO_ROOT,
                          capture_output=True, text=True, check=False)
    if blob.returncode != 0:
        reject("ratchet-base-policy-missing", "the immutable base has no %s" % POLICY_FILE)
    # Windows cannot reopen an open NamedTemporaryFile, so parse a closed file in a private directory.
    with tempfile.TemporaryDirectory(prefix="gbb-perf-limits-") as directory:
        path = os.path.join(directory, "perf-limits.txt")
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(blob.stdout)
        limits = parse_limits(path)
    return blob.stdout, limits


def check_policy_ratchet(current, base):
    for key in ("ir_floor", "determinism", "realtime_floor"):
        if current[key] != base[key]:
            reject("ratchet-hard-limit-changed", "%s changed from immutable value %s to %s" %
                   (key, base[key], current[key]))
    if current["roms"] != base["roms"]:
        reject("ratchet-correctness-identity-changed", "ROM path, SHA, output digest, or consumed pin changed")
    return current["ir_ratio"] > base["ir_ratio"]


def guard_determinism(side, limits):
    for rom in ROMS:
        a, b = side[rom]["irs"]
        # abs(a-b)/min(a,b) > limit, as exact cross-multiplication
        limit = limits["determinism"]
        if abs(a - b) * limit.denominator > limit.numerator * min(a, b):
            reject("proxy-nondeterministic", "head %s: repeat Ir %d and %d differ by more than %s" %
                   (rom, a, b, limit))


def ratio_text(head, base):
    thousandths = (head * 1000) // base
    return "%d.%03d" % (thousandths // 1000, thousandths % 1000)


def realtime_multiples(path, limits):
    """Per ROM: the minimum-elapsed sample after one discarded warm-up line, as an exact Fraction."""
    per_rom = {rom: [] for rom in ROMS}
    for number, line in enumerate(read_text(path, "realtime-format").split("\n"), 1):
        if not line.strip():
            continue
        match = re.fullmatch(r"rom=(\S+) (.*)", line)
        if not match or match.group(1) not in per_rom:
            reject("realtime-format", "%s:%d: line must start with rom=<name>" % (path, number))
        per_rom[match.group(1)].append(parse_measure_line(match.group(2), "%s:%d" % (path, number)))
    result = {}
    for rom in ROMS:
        lines = per_rom[rom]
        if len(lines) != 10:
            reject("realtime-format", "%s: %s needs one warm-up line plus nine samples, found %d" %
                   (path, rom, len(lines)))
        for line in lines:
            if line["workload"] != WORKLOAD or line["digest"] != limits["roms"][rom]["digest"]:
                reject("workload-digest-mismatch", "realtime %s: digest %s, pinned %s" %
                       (rom, line["digest"], limits["roms"][rom]["digest"]))
            if line["consumed"] != limits["roms"][rom]["consumed_half_dots"]:
                reject("proxy-vacuous", "realtime %s: consumed_half_dots %d, pinned %d" %
                       (rom, line["consumed"], limits["roms"][rom]["consumed_half_dots"]))
        samples = lines[1:]  # the first line is the discarded warm-up
        fastest = min(sample["elapsed_ns"] for sample in samples)
        if fastest <= 0:
            reject("realtime-format", "realtime %s: non-positive elapsed_ns" % rom)
        consumed = limits["roms"][rom]["consumed_half_dots"]
        # simulated seconds / wall seconds
        result[rom] = fractions.Fraction(consumed * 10 ** 9, HALF_DOTS_PER_SECOND * fastest)
    return result


def fraction_text(value):
    return "%d/%d" % (value.numerator, value.denominator)


def deterministic_exception_measurement(base_rev, base_limits_text, base, head, limits,
                                        source_base_rev, source_head_rev,
                                        build_base_identity, build_head_identity):
    for name, revision in (("base", source_base_rev), ("head", source_head_rev)):
        if not isinstance(revision, str) or re.fullmatch(r"[0-9a-f]{40}", revision) is None:
            reject("exception-source-build-identity-missing", "%s source revision is not an immutable SHA" % name)
        resolved = subprocess.run(["git", "rev-parse", "--verify", "%s^{commit}" % revision],
                                  cwd=REPO_ROOT, capture_output=True, text=True, check=False)
        if resolved.returncode != 0 or resolved.stdout.strip() != revision:
            reject("exception-source-build-identity-mismatch", "%s source revision is not readable" % name)
    if source_base_rev != V020_SHA:
        reject("exception-source-build-identity-mismatch", "base source is not the pinned v0.2.0 commit")
    for name, identity in (("base", build_base_identity), ("head", build_head_identity)):
        if not isinstance(identity, str) or re.fullmatch(r"[0-9a-f]{64}", identity) is None:
            reject("exception-source-build-identity-missing", "%s build identity is not a SHA-256" % name)
    return {
        "limits_base_revision": base_rev,
        "limits_base_sha256": hashlib.sha256(base_limits_text.encode("utf-8")).hexdigest(),
        "source": {"base_revision": source_base_rev, "head_revision": source_head_rev},
        "build": {"base_identity_sha256": build_base_identity,
                  "head_identity_sha256": build_head_identity},
        "workload": {
            "id": WORKLOAD,
            "roms": {rom: {"path": limits["roms"][rom]["path"],
                            "sha256": limits["roms"][rom]["sha256"],
                            "digest": limits["roms"][rom]["digest"],
                            "consumed_half_dots": limits["roms"][rom]["consumed_half_dots"]}
                     for rom in ROMS},
        },
        "per_rom": {
            rom: {
                "base_ir": base[rom]["irs"][0],
                "head_ir_repeats": list(head[rom]["irs"]),
                "ratio_band": {
                    "min": fraction_text(min(fractions.Fraction(ir, base[rom]["irs"][0])
                                               for ir in head[rom]["irs"])),
                    "max": fraction_text(max(fractions.Fraction(ir, base[rom]["irs"][0])
                                               for ir in head[rom]["irs"])),
                },
                "base_identity": {"workload": base[rom]["lines"][0]["workload"],
                                  "digest": base[rom]["lines"][0]["digest"],
                                  "consumed_half_dots": base[rom]["lines"][0]["consumed"]},
                "head_repeat_identities": [
                    {"workload": line["workload"], "digest": line["digest"],
                     "consumed_half_dots": line["consumed"]}
                    for line in head[rom]["lines"]
                ],
            }
            for rom in ROMS
        },
    }


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def verify_deterministic_exception(path, approved_limit, base_limit, measurement):
    try:
        receipt = json.loads(read_text(path, "exception-receipt-format"))
    except ValueError as error:
        reject("exception-receipt-schema", "exception receipt is not JSON: %s" % error)
    if not isinstance(receipt, dict) or receipt.get("schema") != EXCEPTION_SCHEMA:
        reject("exception-receipt-schema", "schema must be %s" % EXCEPTION_SCHEMA)
    expected_keys = {"schema", "accepted_cause", "accepted_cause_reference", "approved_ir_ratio_limit",
                     "measurement", "measurement_sha256", "external_verification"}
    if set(receipt) != expected_keys:
        reject("exception-receipt-schema", "exception receipt fields differ from the closed schema")
    verification = receipt.get("external_verification")
    if not isinstance(verification, dict) or set(verification) != {"status", "reference", "receipt_sha256"} or \
            verification.get("status") != "verified":
        reject("exception-receipt-unverified", "external verification is absent or not verified")
    reference = verification.get("reference")
    if not isinstance(reference, str) or not re.fullmatch(r"https://[^\s]+", reference):
        reject("exception-receipt-unverified", "external verification reference is invalid")
    cause = receipt.get("accepted_cause")
    cause_reference = receipt.get("accepted_cause_reference")
    if not isinstance(cause, str) or not cause.strip() or len(cause) > 512 or \
            not isinstance(cause_reference, str) or not re.fullmatch(r"https://[^\s]+", cause_reference):
        reject("exception-cause-unaccepted", "an accepted cause and durable reference are required")
    verify_privacy(receipt)
    if receipt.get("approved_ir_ratio_limit") != fraction_text(approved_limit) or approved_limit <= base_limit:
        reject("exception-limit-mismatch", "approved Ir limit does not equal the widened policy value")
    measurement_sha = canonical_sha(measurement)
    if receipt.get("measurement") != measurement or receipt.get("measurement_sha256") != measurement_sha:
        reject("exception-measurement-mismatch", "receipt is not bound to these source, build, workload and Ir observations")
    unsigned = {key: value for key, value in receipt.items() if key != "external_verification"}
    if verification.get("receipt_sha256") != canonical_sha(unsigned):
        reject("exception-receipt-digest-mismatch", "external verification digest does not bind this receipt")
    for rom in ROMS:
        band = measurement["per_rom"][rom]["ratio_band"]
        if fractions.Fraction(band["max"]) > approved_limit:
            reject("exception-limit-below-measurement", "%s measured band exceeds the approved Ir limit" % rom)
    if not any(fractions.Fraction(measurement["per_rom"][rom]["ratio_band"]["max"]) > base_limit
               for rom in ROMS):
        reject("exception-not-needed", "no per-ROM deterministic measurement exceeds the immutable limit")
    return receipt


def write_new_text(path, text):
    """Exclusive create: an existing path is never overwritten (evidence is not replaced)."""
    try:
        with open(path, "x", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    except OSError as error:
        reject("exception-measurement-output", "cannot create %s: %s" % (path, error))


def evaluate(limits_path, base_dir, head_dir, realtime_path, base_rev, exception_path=None,
             source_base_rev=None, source_head_rev=None,
             build_base_identity=None, build_head_identity=None, emit_measurement_path=None):
    if base_rev is None:
        reject("ratchet-base-required", "--evaluate requires --base-rev with an immutable committed limits base")
    limits = parse_limits(limits_path)
    base_limits_text, base_limits = immutable_limits(base_rev)
    needs_exception = check_policy_ratchet(limits, base_limits)
    if needs_exception and exception_path is None and emit_measurement_path is None:
        reject("ir-limit-widening-unapproved", "ir_ratio_limit was widened without a deterministic exception receipt")
    if not needs_exception and exception_path is not None:
        reject("exception-receipt-unexpected", "an exception receipt is only valid for an Ir-limit widening")
    attribution_floor_check(limits_path, limits)
    base = read_side(base_dir, "base", 1, limits)
    head = read_side(head_dir, "head", 2, limits)
    guard_digest(base, "base", limits)
    guard_digest(head, "head", limits)
    guard_vacuous(base, "base", limits)
    guard_vacuous(head, "head", limits)
    guard_determinism(head, limits)
    if needs_exception:
        measurement = deterministic_exception_measurement(
            base_rev, base_limits_text, base, head, limits, source_base_rev, source_head_rev,
            build_base_identity, build_head_identity)
        if emit_measurement_path is not None:
            # The exact object the owner approves by digest (verify-release-gates.py --digest). It is written before
            # any verdict, so a refused widening still leaves the evidence the review needs.
            write_new_text(emit_measurement_path, json.dumps(measurement, sort_keys=True, indent=2) + "\n")
        if exception_path is None:
            reject("ir-limit-widening-unapproved",
                   "ir_ratio_limit was widened without a deterministic exception receipt")
        verify_deterministic_exception(exception_path, limits["ir_ratio"], base_limits["ir_ratio"], measurement)
    parts = []
    for rom in ROMS:
        base_ir = base[rom]["irs"][0]
        head_ir = max(head[rom]["irs"])
        limit = limits["ir_ratio"]
        # head/base > limit, as exact cross-multiplication
        if head_ir * limit.denominator > base_ir * limit.numerator:
            reject("ir-budget-exceeded", "%s: head Ir %d over v0.2.0 Ir %d is ratio %s, above the limit %s" %
                   (rom, head_ir, base_ir, ratio_text(head_ir, base_ir), limit))
        parts.append("%s=%s" % (rom, ratio_text(head_ir, base_ir)))
    if realtime_path is not None:
        multiples = realtime_multiples(realtime_path, limits)
        for rom in ROMS:
            if multiples[rom] < limits["realtime_floor"]:
                reject("realtime-below-floor", "%s: realtime multiple %s is below the floor %s" %
                       (rom, multiples[rom], limits["realtime_floor"]))
        parts.append("realtime_min=%s" % ratio_text(
            min(multiples.values()).numerator, min(multiples.values()).denominator))
    print("perf-gate pass ratios " + " ".join(parts))


# ---------------------------------------------------------------- attribution (D-17)

REPO_ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
DEFAULT_LIMITS = os.path.normpath(os.path.join(HERE, "..", "baseline", "perf-gate-v1.txt"))
V010 = "v0.1.0"
V020 = "v0.2.0"
V020_SHA = "ab301aa69b1f085050fd66bf7b1378863a0821f2"
RULES = {
    "merge_set": "git rev-list --first-parent --merges v0.1.0..v0.2.0",
    "resolution_set": "git rev-list --first-parent v0.1.0..v0.2.0 -- src include",
    "post_v020_set": "git rev-list --first-parent v0.2.0..<head> -- src",
}
HARNESS_ANCHOR = "cgb_form ? GBB_PROFILE_CGB_CPU_E : GBB_PROFILE_DMG_CPU_B"
HARNESS_DMG = "GBB_PROFILE_DMG_CPU_B"
WARM_UP_IR = "none: deterministic instruction count, fresh process per repeat"
HYPOTHESES = ["audio-mix divide-by-16 cost is a hypothesis for the growth, not an established cause"]
PRIVATE_KEY_NAMES = {"host", "hostname", "host_name", "machine_id", "machine_identifier", "serial",
                     "serial_number", "username", "user_name", "compiler_path", "build_path",
                     "working_directory", "home_directory"}
PRIVATE_PATH = re.compile(r"(?<![A-Za-z0-9_.-])/(?:[A-Za-z0-9._-]+/)+[^\s\"']*")
WINDOWS_PATH = re.compile(r"(?:^|\s)[A-Za-z]:[\\/](?:[^\s]+)")
EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PRIVATE_HOSTNAME = re.compile(r"\b(?:[A-Za-z0-9-]+\.)+(?:local|internal|private|example|corp|lan)\b", re.IGNORECASE)


def git(repo, *arguments):
    process = subprocess.run(["git", "-C", repo] + list(arguments), capture_output=True, text=True)
    if process.returncode != 0:
        reject("attribution-git", "git %s failed: %s" % (" ".join(arguments), process.stderr.strip()))
    return process.stdout


def adapt_harness(text):
    """The DMG-only harness: v0.1.0 and the early resolution commits do not define the CGB profile."""
    if text.count(HARNESS_ANCHOR) != 1:
        reject("harness-adapt-anchor", "expected exactly one %r in tests/measure_core.c, found %d" %
               (HARNESS_ANCHOR, text.count(HARNESS_ANCHOR)))
    adapted = text.replace(HARNESS_ANCHOR, HARNESS_DMG)
    return (adapted, hashlib.sha256(text.encode()).hexdigest(), hashlib.sha256(adapted.encode()).hexdigest())


def rev_list(repo, *arguments):
    return [line for line in git(repo, "rev-list", "--first-parent", *arguments).split("\n") if line]


def derive_selection(repo, head):
    """The three D-17 sets in first-parent chronological order, the affects_binary flag per merge, and the
    measured revisions: v0.1.0, merge_set union resolution_set, v0.2.0, post_v020_set and the head."""
    v010 = git(repo, "rev-parse", V010 + "^{commit}").strip()
    v020 = git(repo, "rev-parse", V020 + "^{commit}").strip()
    head = git(repo, "rev-parse", head + "^{commit}").strip()
    chain = list(reversed(rev_list(repo, v010 + ".." + head)))
    position = {sha: index for index, sha in enumerate(chain)}
    if v020 not in position or head not in position:
        reject("attribution-git", "v0.2.0 and the head must lie on the first-parent chain from v0.1.0")
    order = lambda shas: sorted(shas, key=lambda sha: position[sha])
    merges = order(rev_list(repo, "--merges", v010 + ".." + v020))
    resolution = order(rev_list(repo, v010 + ".." + v020, "--", "src", "include"))
    post = order(rev_list(repo, v020 + ".." + head, "--", "src"))
    flags = {sha: bool(git(repo, "diff", "--name-only", sha + "^1", sha, "--", "src", "include").strip())
             for sha in merges}
    wanted = set(merges) | set(resolution) | {v020, head} | set(post)
    measured = [v010] + order(wanted - {v010})
    return {"v010": v010, "v020": v020, "head": head, "merge_set": merges, "resolution_set": resolution,
            "post_v020_set": post, "affects_binary": flags, "measured": measured}


def raw_row_digest(ir):
    return hashlib.sha256(json.dumps(ir, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def floor_two_decimals(multiple):
    return fractions.Fraction((multiple * 6 * 10) // 10 * 100 // 100) if False else \
        fractions.Fraction(int(multiple * fractions.Fraction(6, 10) * 100), 100)


def required_realtime_floor(multiple):
    return max(fractions.Fraction(2), floor_two_decimals(multiple))


def realtime_block(path, limits):
    multiples = realtime_multiples(path, limits)
    per_rom = {rom: [] for rom in ROMS}
    for line in read_text(path, "realtime-format").split("\n"):
        if line.strip():
            match = re.fullmatch(r"rom=(\S+) (.*)", line)
            per_rom[match.group(1)].append(parse_measure_line(match.group(2), path)["elapsed_ns"])
    smallest = min(multiples.values())
    return {"samples_ns": {rom: values[1:] for rom, values in per_rom.items()},
            "warm_up_discarded_runs": 1,
            "multiple": "%d/%d" % (smallest.numerator, smallest.denominator),
            "multiple_2dp": ratio_text(smallest.numerator, smallest.denominator)[:-1]}


def summarize(selection, measurements):
    """Growth per ROM between the measured revisions, attributed to commits by recomputable arithmetic."""
    by_rev = {row["revision"]: row for row in measurements}
    first, v020 = selection["measured"][0], selection["v020"]
    after = selection["measured"][selection["measured"].index(v020) + 1:]
    delta = lambda a, b: {rom: by_rev[b]["ir"][rom][0] - by_rev[a]["ir"][rom][0] for rom in ROMS}
    segment = selection["measured"][1:selection["measured"].index(v020) + 1]
    contributions = []
    previous = first
    for sha in segment:
        step = delta(previous, sha)
        contributions.append({"revision": sha, "ir_delta_total": sum(step.values())})
        previous = sha
    largest = max(contributions, key=lambda row: row["ir_delta_total"])
    return {"v010_to_v020_growth": delta(first, v020),
            "largest_v010_to_v020_revision": largest["revision"],
            "largest_v010_to_v020_ir_delta_total": largest["ir_delta_total"],
            "post_v020_growth": delta(v020, after[-1]) if after else {rom: 0 for rom in ROMS},
            "post_v020_commits": list(selection["post_v020_set"])}


def emit_attribution(options, limits_path):
    limits = parse_limits(limits_path)
    repo = options.get("--repo") or REPO_ROOT
    selection = derive_selection(repo, options["--head"])
    harness_text = git(repo, "show", selection["head"] + ":tests/measure_core.c")
    _, source_sha, adapted_sha = adapt_harness(harness_text)
    measurements = []
    for sha in selection["measured"]:
        directory = os.path.join(options["--meas"], sha)
        side = read_side(directory, sha, 2, limits)
        guard_digest(side, sha, limits)
        guard_vacuous(side, sha, limits)
        guard_determinism(side, limits)
        ir = {rom: side[rom]["irs"] for rom in ROMS}
        measurements.append({"revision": sha, "ir": ir, "raw_row_sha256": raw_row_digest(ir),
                             "digest": {rom: side[rom]["lines"][0]["digest"] for rom in ROMS},
                             "consumed_half_dots": {rom: side[rom]["lines"][0]["consumed"] for rom in ROMS}})
    deltas = []
    for previous, current in zip(measurements, measurements[1:]):
        deltas.append({"revision": current["revision"], "previous": previous["revision"],
                       "ir_delta": {rom: current["ir"][rom][0] - previous["ir"][rom][0] for rom in ROMS}})
    receipt = {
        "schema_version": 1,
        "workload": WORKLOAD,
        "model": "dmg-cpu-b",
        "roms": {rom: {"sha256": limits["roms"][rom]["sha256"], "digest": limits["roms"][rom]["digest"],
                       "consumed_half_dots": limits["roms"][rom]["consumed_half_dots"]} for rom in ROMS},
        "build": {"runner_image": options["--runner-image"], "gcc_version": options["--gcc-version"],
                  "valgrind_version": options["--valgrind-version"],
                  "hardware_class": options["--hardware-class"], "build_type": "Release",
                  "build_command": options["--build-command"],
                  "harness_source_sha256": source_sha, "harness_sha256": adapted_sha},
        "selection": {"rules": dict(RULES), "head": selection["head"],
                      "v010": selection["v010"], "v020": selection["v020"],
                      "merge_set": [{"sha": sha, "affects_binary": selection["affects_binary"][sha]}
                                    for sha in selection["merge_set"]],
                      "resolution_set": selection["resolution_set"],
                      "post_v020_set": selection["post_v020_set"],
                      "measured": selection["measured"]},
        "measurements": measurements,
        "deltas": deltas,
        "attribution": summarize(selection, measurements),
        "realtime": realtime_block(options["--realtime"], limits),
        "warm_up": {"ir": WARM_UP_IR, "realtime_discarded_runs": 1},
        "uncertainty": {"ir_repeat_spread": 0},
        "hypotheses": list(HYPOTHESES),
        "closes": ["LIM-PERF-REVIEW"],
    }
    verify_privacy(receipt)
    with open(options["--out"], "w", encoding="utf-8") as handle:
        json.dump(receipt, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("perf-attribution emitted revisions=%d" % len(measurements))


def verify_privacy(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower().replace("-", "_") in PRIVATE_KEY_NAMES:
                reject("attribution-privacy", "private key name %r" % key)
            verify_privacy(item)
    elif isinstance(value, list):
        for item in value:
            verify_privacy(item)
    elif isinstance(value, str):
        text = re.sub(r"https?://[^\s\"']+", " ", value, flags=re.IGNORECASE)
        if PRIVATE_PATH.search(text) or WINDOWS_PATH.search(value) or EMAIL.search(value) \
                or PRIVATE_HOSTNAME.search(value):
            reject("attribution-privacy", "private path, address or host name in %r" % value[:60])


def check_attribution(path, repo, limits_path):
    limits = parse_limits(limits_path)
    try:
        receipt = json.loads(read_text(path, "attribution-format"))
    except ValueError as error:
        reject("attribution-format", "receipt is not JSON: %s" % error)
    verify_privacy(receipt)
    try:
        counts = check_receipt_shape(receipt, limits, repo)
    except (KeyError, TypeError, IndexError, AttributeError) as error:
        reject("attribution-format", "receipt is missing or mistyped: %r" % error)
    return receipt, counts


def check_receipt_shape(receipt, limits, repo):
    if receipt["schema_version"] != 1 or receipt["workload"] != WORKLOAD or receipt["model"] != "dmg-cpu-b":
        reject("attribution-format", "schema_version, workload or model differs from the contract")
    if not isinstance(receipt.get("warm_up"), dict) or not receipt["warm_up"].get("ir") \
            or receipt["warm_up"].get("realtime_discarded_runs") != 1:
        reject("attribution-warm-up-missing", "warm_up must state the Ir warm-up rule and one discarded realtime run")
    selection = receipt["selection"]
    derived = derive_selection(repo, selection["head"])
    if selection["rules"] != RULES:
        reject("attribution-format", "selection rules differ from the contract command strings")
    if selection["v020"] != derived["v020"] or selection["v010"] != derived["v010"]:
        reject("attribution-merge-set", "v0.1.0 or v0.2.0 does not resolve to the recorded commit")
    if [row["sha"] for row in selection["merge_set"]] != derived["merge_set"]:
        reject("attribution-merge-set", "merge_set differs from %s" % RULES["merge_set"])
    if selection["resolution_set"] != derived["resolution_set"]:
        reject("attribution-resolution-set", "resolution_set differs from %s" % RULES["resolution_set"])
    if selection["post_v020_set"] != derived["post_v020_set"]:
        reject("attribution-post-set", "post_v020_set differs from %s" % RULES["post_v020_set"])
    for row in selection["merge_set"]:
        if row["affects_binary"] is not derived["affects_binary"][row["sha"]]:
            reject("attribution-affects-binary", "affects_binary flag differs for merge %s" % row["sha"])
    if selection["measured"] != derived["measured"] or \
            [row["revision"] for row in receipt["measurements"]] != derived["measured"]:
        reject("attribution-measured-set", "measured revisions differ from v0.1.0, the union of the merge and "
               "resolution sets, v0.2.0, the post-v0.2.0 commits and the head")
    for rom in ROMS:
        pins = limits["roms"][rom]
        if receipt["roms"][rom] != {"sha256": pins["sha256"], "digest": pins["digest"],
                                    "consumed_half_dots": pins["consumed_half_dots"]}:
            reject("attribution-digest-changed", "%s ROM identity differs from the limits pins" % rom)
    for row in receipt["measurements"]:
        if row["raw_row_sha256"] != raw_row_digest(row["ir"]):
            reject("attribution-raw-row", "raw row for %s does not match its digest" % row["revision"])
        for rom in ROMS:
            if row["digest"][rom] != limits["roms"][rom]["digest"] or \
                    row["consumed_half_dots"][rom] != limits["roms"][rom]["consumed_half_dots"]:
                reject("attribution-digest-changed", "%s %s digest or consumed_half_dots changed" %
                       (row["revision"], rom))
            first, second = row["ir"][rom]
            if first != second:
                reject("attribution-repeat-differs", "%s %s repeats differ: %d and %d" %
                       (row["revision"], rom, first, second))
    expected = [{"revision": b["revision"], "previous": a["revision"],
                 "ir_delta": {rom: b["ir"][rom][0] - a["ir"][rom][0] for rom in ROMS}}
                for a, b in zip(receipt["measurements"], receipt["measurements"][1:])]
    if receipt["deltas"] != expected:
        reject("attribution-delta-mismatch", "a stored delta differs from the raw rows")
    if receipt["attribution"] != summarize(derived, receipt["measurements"]):
        reject("attribution-delta-mismatch", "the attribution summary differs from the raw rows")
    build = receipt["build"]
    _, source_sha, adapted_sha = adapt_harness(git(repo, "show", derived["head"] + ":tests/measure_core.c"))
    if build["harness_source_sha256"] != source_sha or build["harness_sha256"] != adapted_sha:
        reject("harness-digest-mismatch", "harness digests differ from the harness re-derived at the receipt head")
    realtime = receipt["realtime"]
    multiples = []
    for rom in ROMS:
        samples = realtime["samples_ns"][rom]
        if len(samples) != 9 or min(samples) <= 0:
            reject("attribution-format", "realtime needs nine positive samples for %s" % rom)
        multiples.append(fractions.Fraction(limits["roms"][rom]["consumed_half_dots"] * 10 ** 9,
                                            HALF_DOTS_PER_SECOND * min(samples)))
    smallest = min(multiples)
    if realtime["multiple"] != "%d/%d" % (smallest.numerator, smallest.denominator):
        reject("attribution-realtime", "realtime multiple differs from the nine samples")
    if receipt["uncertainty"] != {"ir_repeat_spread": 0} or "LIM-PERF-REVIEW" not in receipt["closes"] \
            or not receipt["hypotheses"]:
        reject("attribution-format", "uncertainty, closes or hypotheses differ from the contract")
    return len(derived["measured"]), len(derived["merge_set"]), smallest


def attribution_floor_check(limits_path, limits):
    """When the receipt sits beside the limits file, realtime_floor may not be below max(2.0, 0.6 x multiple)."""
    receipt_path = os.path.join(os.path.dirname(os.path.abspath(limits_path)), "perf-attribution-v1.json")
    if not os.path.exists(receipt_path):
        return
    try:
        receipt = json.loads(read_text(receipt_path, "attribution-format"))
        multiple = fractions.Fraction(receipt["realtime"]["multiple"])
    except (ValueError, KeyError, TypeError, ZeroDivisionError) as error:
        reject("attribution-format", "cannot read the receipt realtime multiple: %r" % error)
    required = required_realtime_floor(multiple)
    if limits["realtime_floor"] < required:
        reject("realtime-floor-below-receipt", "realtime_floor %s is below max(2.0, 0.6 x receipt multiple) = %s" %
               (limits["realtime_floor"], required))


# ---------------------------------------------------------------- self-test

def run_cli(arguments, cwd=None):
    process = subprocess.run([sys.executable, "-I", os.path.abspath(__file__)] + arguments,
                             capture_output=True, text=True, cwd=cwd)
    return process.returncode, process.stdout, process.stderr


def self_test():
    controls = 0
    limits_path = os.path.normpath(os.path.join(HERE, "..", "baseline", "perf-gate-v1.txt"))
    failures = []

    def expect(name, code, arguments, stderr_has=None, stdout_has=None):
        nonlocal controls
        rc, out, err = run_cli(arguments)
        ok = rc == code and (stderr_has is None or stderr_has in err) and \
            (stdout_has is None or stdout_has in out)
        if code == 0 and err.strip():
            ok = False
        if not ok:
            failures.append("%s: rc=%d stdout=%r stderr=%r" % (name, rc, out.strip(), err.strip()))
        controls += 1

    def evaluate_args(base, head, realtime=None, limits=limits_path):
        arguments = ["--evaluate", "--limits", limits, "--base", base, "--head", head,
                     "--base-rev", LIMITS_BASE_REV]
        if realtime:
            arguments += ["--realtime", realtime]
        return arguments

    base = os.path.join(DATA, "base")
    head = lambda case: os.path.join(DATA, "head-" + case)
    expect("canned pass ratio 1.081", 0, evaluate_args(base, head("pass")),
           stdout_has="tracer=1.081 libbet=1.081 visible-demo=1.081")
    expect("ratio exactly 1.10 passes", 0, evaluate_args(base, head("exact")), stdout_has="tracer=1.100")
    expect("one Ir above 1.10 fails", 1, evaluate_args(base, head("over")),
           stderr_has="REJECT ir-budget-exceeded")
    expect("0.03% repeat difference fails", 1, evaluate_args(base, head("nondet")),
           stderr_has="REJECT proxy-nondeterministic")
    expect("Ir at the 100M floor is vacuous", 1, evaluate_args(base, head("vacuous")),
           stderr_has="REJECT proxy-vacuous")
    expect("wrong correctness digest fails", 1, evaluate_args(base, head("digest")),
           stderr_has="REJECT workload-digest-mismatch")
    expect("realtime above the floor passes", 0,
           evaluate_args(base, head("pass"), os.path.join(DATA, "realtime-pass.txt")),
           stdout_has="realtime_min=")
    expect("realtime below the floor fails", 1,
           evaluate_args(base, head("pass"), os.path.join(DATA, "realtime-below-floor.txt")),
           stderr_has="REJECT realtime-below-floor")
    expect("real limits file is valid", 0, ["--check-limits", limits_path], stdout_has="perf-gate limits ok")

    with tempfile.TemporaryDirectory(prefix="perf-gate-selftest-") as scratch:
        original = read_text(limits_path, "limits-schema")

        def variant(name, text):
            path = os.path.join(scratch, name)
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(text)
            return path

        expect("unknown limits key fails", 1, ["--check-limits", variant("unknown", original + "extra=1\n")],
               stderr_has="REJECT limits-schema")
        missing = "\n".join(l for l in original.split("\n") if not l.startswith("rom.libbet.digest="))
        expect("missing ROM field fails", 1, ["--check-limits", variant("missing", missing)],
               stderr_has="REJECT limits-schema")
        nonint = re.sub(r"(?m)^ir_floor=.*$", "ir_floor=1e8", original)
        expect("non-integer value fails", 1, ["--check-limits", variant("nonint", nonint)],
               stderr_has="REJECT limits-schema")

        # Consumed pin: tracer must equal its pinned value exactly.
        shifted = os.path.join(scratch, "head-consumed")
        copy_tree(head("pass"), shifted)
        for repeat in (1, 2):
            edit(os.path.join(shifted, "tracer.line.%d" % repeat),
                 "consumed_half_dots=1000000", "consumed_half_dots=999999")
        expect("consumed 999999 on tracer is vacuous", 1, evaluate_args(base, shifted),
               stderr_has="REJECT proxy-vacuous")

        # Exercise the committed 4.02 floor without mutating the policy: each ROM's integer-nanosecond
        # sample is rounded to the passing side, then moved by one nanosecond to the failing side.
        def realtime_at_floor(one_ns_slower):
            limits = parse_limits(limits_path)
            rows = []
            for rom in ROMS:
                consumed = limits["roms"][rom]["consumed_half_dots"]
                boundary = fractions.Fraction(consumed * 10 ** 9,
                                              HALF_DOTS_PER_SECOND * limits["realtime_floor"])
                elapsed_ns = boundary.numerator // boundary.denominator + int(one_ns_slower)
                observed = fractions.Fraction(consumed * 10 ** 9, HALF_DOTS_PER_SECOND * elapsed_ns)
                if (observed < limits["realtime_floor"]) != one_ns_slower:
                    reject("self-test-failed", "%s did not straddle the immutable realtime floor" % rom)
                for index in range(10):
                    elapsed = elapsed_ns * 2 if index == 0 else elapsed_ns
                    rows.append("rom=%s mode=no-trace workload=%s budget_half_dots=1000000 "
                                "consumed_half_dots=%d stop_reason=0 elapsed_ns=%d "
                                "correctness_digest_fnv1a64=%s" %
                                (rom, WORKLOAD, consumed, elapsed, limits["roms"][rom]["digest"]))
            return "\n".join(rows) + "\n"

        at_floor = variant("at-floor.txt", realtime_at_floor(False))
        below = variant("below-by-one.txt", realtime_at_floor(True))
        expect("realtime at or just above the floor passes", 0,
               evaluate_args(base, head("pass"), at_floor), stdout_has="realtime_min=")
        expect("realtime one step below the floor fails", 1,
               evaluate_args(base, head("pass"), below), stderr_has="REJECT realtime-below-floor")

        # A case a float comparison would misjudge: head/base exceeds 1.10 by 2e-17, which rounds to 1.1.
        big_base, big_head = 10 ** 17, 110000000000000002
        assert float(big_head) / float(big_base) <= 1.1 and big_head * 100 > big_base * 110
        float_base = os.path.join(scratch, "float-base")
        float_head = os.path.join(scratch, "float-head")
        copy_tree(base, float_base)
        copy_tree(head("pass"), float_head)
        for rom in ROMS:
            write_cg(os.path.join(float_base, rom + ".cg.1"), big_base)
            for n in (1, 2):
                write_cg(os.path.join(float_head, "%s.cg.%d" % (rom, n)), big_head)
        expect("float-rounding case is rejected exactly", 1, evaluate_args(float_base, float_head),
               stderr_has="REJECT ir-budget-exceeded")
        big_head_ok = 110 * 10 ** 15
        for rom in ROMS:
            for n in (1, 2):
                write_cg(os.path.join(float_head, "%s.cg.%d" % (rom, n)), big_head_ok)
        expect("exact 1.10 at large magnitude passes", 0, evaluate_args(float_base, float_head))

    controls += attribution_self_test(limits_path, failures)

    if failures:
        for failure in failures:
            sys.stderr.write("self-test control failed: %s\n" % failure)
        reject("self-test-failed", "%d of %d controls failed" % (len(failures), controls))
    print("perf-gate self-test pass controls=%d" % controls)


def make_fixture_repo(root):
    """A private repository shaped like the D-17 history: tags, no-ff merges (one source-free), a squash-style
    source commit before v0.2.0, and source and docs commits after it."""
    environment = dict(os.environ, GIT_AUTHOR_NAME="GabbaBoy contributors", GIT_AUTHOR_EMAIL="noreply@users.noreply.github.com",
                       GIT_COMMITTER_NAME="GabbaBoy contributors", GIT_COMMITTER_EMAIL="noreply@users.noreply.github.com",
                       GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)

    def run(*arguments):
        process = subprocess.run(["git", "-C", root] + list(arguments), capture_output=True, text=True,
                                 env=environment)
        if process.returncode != 0:
            reject("self-test-failed", "fixture git %s: %s" % (" ".join(arguments), process.stderr.strip()))
        return process.stdout.strip()

    def write(name, text):
        path = os.path.join(root, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)

    run("init", "-q", "-b", "main")
    run("config", "commit.gpgsign", "false")
    write("tests/measure_core.c", "int profile = %s;\n" % HARNESS_ANCHOR)
    write("src/core/a.c", "v1\n")
    write("include/a.h", "h1\n")
    run("add", "-A")
    run("commit", "-q", "-m", "baseline")
    run("tag", V010)
    run("checkout", "-q", "-b", "phase-a")
    write("src/core/a.c", "v2\n")
    run("commit", "-q", "-am", "phase a source")
    run("checkout", "-q", "main")
    run("merge", "-q", "--no-ff", "-m", "merge phase a", "phase-a")
    run("checkout", "-q", "-b", "phase-b")
    write("docs/b.md", "b\n")
    run("add", "-A")
    run("commit", "-q", "-m", "phase b docs")
    run("checkout", "-q", "main")
    run("merge", "-q", "--no-ff", "-m", "merge phase b", "phase-b")
    write("src/core/a.c", "v3\n")
    run("commit", "-q", "-am", "squash-style source commit")
    run("tag", V020)
    write("src/core/a.c", "v4\n")
    run("commit", "-q", "-am", "post source one")
    write("docs/c.md", "c\n")
    run("add", "-A")
    run("commit", "-q", "-m", "post docs")
    write("src/core/a.c", "v5\n")
    run("commit", "-q", "-am", "post source two")


def write_measurements(directory, shas):
    limits = parse_limits(DEFAULT_LIMITS)
    for index, sha in enumerate(shas):
        folder = os.path.join(directory, sha)
        os.makedirs(folder)
        for offset, rom in enumerate(ROMS):
            entry = limits["roms"][rom]
            for repeat in (1, 2):
                write_cg(os.path.join(folder, "%s.cg.%d" % (rom, repeat)), 200000000 + 1000000 * index + offset)
            for repeat in (1, 2):
                with open(os.path.join(folder, "%s.line.%d" % (rom, repeat)), "w", encoding="utf-8") as handle:
                    handle.write("mode=no-trace workload=%s budget_half_dots=1000000 consumed_half_dots=%d stop_reason=0 "
                                 "elapsed_ns=10000000 correctness_digest_fnv1a64=%s\n" %
                                 (WORKLOAD, entry["consumed_half_dots"], entry["digest"]))


def attribution_self_test(limits_path, failures):
    controls = 0

    def expect(name, code, arguments, text, where="stderr"):
        nonlocal controls
        rc, out, err = run_cli(arguments)
        stream = err if where == "stderr" else out
        if rc != code or text not in stream:
            failures.append("%s: rc=%d stdout=%r stderr=%r" % (name, rc, out.strip(), err.strip()))
        controls += 1

    with tempfile.TemporaryDirectory(prefix="perf-attribution-selftest-") as scratch:
        repo = os.path.join(scratch, "repo")
        os.makedirs(repo)
        make_fixture_repo(repo)
        selection = derive_selection(repo, "HEAD")
        meas = os.path.join(scratch, "meas")
        os.makedirs(meas)
        write_measurements(meas, selection["measured"])
        realtime = os.path.join(scratch, "realtime.txt")
        with open(realtime, "w", encoding="utf-8") as handle:
            handle.write(realtime_text(10000000, 10000000))
        receipt_path = os.path.join(scratch, "receipt.json")
        rc, out, err = run_cli(["--emit-attribution", "--repo", repo, "--head", "HEAD", "--meas", meas,
                                "--out", receipt_path, "--realtime", realtime, "--runner-image", "self-test-image",
                                "--gcc-version", "gcc self-test", "--valgrind-version", "valgrind-self-test",
                                "--hardware-class", "self-test hardware class",
                                "--build-command", "cc -std=c17 -O3 -DNDEBUG -I$REV/include $HARNESS $REV/src/core/*.c"])
        if rc != 0:
            failures.append("attribution emit: rc=%d stderr=%r" % (rc, err.strip()))
            return controls + 1
        controls += 1
        expect("attribution fixture receipt passes", 0,
               ["--check-attribution", receipt_path, "--repo", repo], "perf-attribution pass revisions=%d merges=2" %
               len(selection["measured"]), "stdout")
        original = json.loads(read_text(receipt_path, "attribution-format"))

        def mutated(name, code, mutate):
            receipt = json.loads(json.dumps(original))
            mutate(receipt)
            path = os.path.join(scratch, name.replace(" ", "-") + ".json")
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(receipt, handle)
            expect(name, 1, ["--check-attribution", path, "--repo", repo], "REJECT %s:" % code)

        def drop_merge(r): del r["selection"]["merge_set"][0]
        def drop_post(r): del r["selection"]["post_v020_set"][-1]
        def extra_commit(r):
            extra = git(repo, "rev-parse", "HEAD~1").strip()
            r["selection"]["measured"].append(extra)
            r["measurements"].append(dict(r["measurements"][-1], revision=extra))
        def raw_row(r):
            r["measurements"][1]["ir"]["tracer"] = [x + 1 for x in r["measurements"][1]["ir"]["tracer"]]
        def repeat_differs(r):
            row = r["measurements"][2]
            row["ir"]["libbet"][1] += 1
            row["raw_row_sha256"] = raw_row_digest(row["ir"])
        def delta(r): r["deltas"][0]["ir_delta"]["tracer"] += 1
        def flip(r): r["selection"]["merge_set"][0]["affects_binary"] = not r["selection"]["merge_set"][0]["affects_binary"]
        def digest(r): r["measurements"][0]["digest"]["tracer"] = "0" * 16
        def warm_up(r): del r["warm_up"]
        def harness(r): r["build"]["harness_sha256"] = "0" * 64
        def private(r): r["build"]["runner_image"] = "/home/runner/work/image"

        mutated("receipt with a dropped merge", "attribution-merge-set", drop_merge)
        mutated("receipt with a dropped post-v0.2.0 commit", "attribution-post-set", drop_post)
        mutated("receipt with an extra measured commit", "attribution-measured-set", extra_commit)
        mutated("receipt with an altered raw row", "attribution-raw-row", raw_row)
        mutated("receipt with differing repeats", "attribution-repeat-differs", repeat_differs)
        mutated("receipt with an altered delta", "attribution-delta-mismatch", delta)
        mutated("receipt with a flipped affects_binary", "attribution-affects-binary", flip)
        mutated("receipt with a changed digest", "attribution-digest-changed", digest)
        mutated("receipt without warm_up", "attribution-warm-up-missing", warm_up)
        mutated("receipt with an altered harness digest", "harness-digest-mismatch", harness)
        mutated("receipt with a private path", "attribution-privacy", private)

        # The harness adaptation refuses a source with no (or two) anchors.
        two = os.path.join(scratch, "two.c")
        with open(two, "w", encoding="utf-8") as handle:
            handle.write(HARNESS_ANCHOR + "\n" + HARNESS_ANCHOR + "\n")
        expect("harness with two anchors is refused", 1, ["--adapt-harness", two, "--out", two + ".out"],
               "REJECT harness-adapt-anchor:")

        # A committed receipt raises the floor: realtime_floor below max(2.0, 0.6 x multiple) is refused.
        beside = os.path.join(scratch, "beside")
        os.makedirs(beside)
        with open(os.path.join(beside, "perf-attribution-v1.json"), "w", encoding="utf-8") as handle:
            json.dump(original, handle)
        required = required_realtime_floor(fractions.Fraction(original["realtime"]["multiple"]))
        text = read_text(limits_path, "limits-schema")
        for name, floor, expected_error in (
                ("realtime_floor below the receipt rule is refused", "2.0", "realtime-floor-below-receipt"),
                ("realtime_floor at the receipt rule passes", "%d.%02d" % divmod(int(required * 100), 100), None)):
            limits_copy = os.path.join(beside, "perf-gate-v1.txt")
            with open(limits_copy, "w", encoding="utf-8") as handle:
                handle.write(re.sub(r"(?m)^realtime_floor=.*$", "realtime_floor=" + floor, text))
            try:
                attribution_floor_check(limits_copy, parse_limits(limits_copy))
                rejected = None
            except Rejected as error:
                rejected = error.code
            if rejected != expected_error:
                failures.append("%s: expected %r, got %r" % (name, expected_error, rejected))
            controls += 1
    return controls


def copy_tree(source, destination):
    os.makedirs(destination)
    for name in os.listdir(source):
        with open(os.path.join(source, name), "rb") as src:
            contents = src.read()
        with open(os.path.join(destination, name), "wb") as dst:
            dst.write(contents)
        if name.endswith(".line"):
            for repeat in (1, 2):
                with open(os.path.join(destination, "%s.%d" % (name, repeat)), "wb") as dst:
                    dst.write(contents)


def edit(path, old, new):
    text = read_text(path, "measure-line-format")
    assert old in text
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text.replace(old, new))


def write_cg(path, ir):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("desc: I1 cache:\ncmd: measure_core --no-trace rom\nevents: Ir\nfl=gabbaboy.c\nfn=main\n"
                     "1 %d\nsummary: %d\n" % (ir, ir))


def realtime_text(warmup_ns, sample_ns):
    limits = parse_limits(os.path.normpath(os.path.join(HERE, "..", "baseline", "perf-gate-v1.txt")))
    rows = []
    for rom in ROMS:
        entry = limits["roms"][rom]
        for index in range(10):
            elapsed = warmup_ns * 2 if index == 0 else sample_ns + (index - 1) * 1000
            rows.append("rom=%s mode=no-trace workload=%s budget_half_dots=1000000 consumed_half_dots=%d "
                        "stop_reason=0 elapsed_ns=%d correctness_digest_fnv1a64=%s" %
                        (rom, WORKLOAD, entry["consumed_half_dots"], elapsed, entry["digest"]))
    return "\n".join(rows) + "\n"


POLICY_BASE_REV = "947d6a9d177af6c04a5f9ea6abcc2c470ab9be57"


class PerfGateLimitRatchetTests(unittest.TestCase):
    def evaluate(self, limits, *, base_rev=POLICY_BASE_REV, realtime=None, exception=None,
                 source_base_rev=None, source_head_rev=None,
                 build_base_identity=None, build_head_identity=None):
        arguments = ["--evaluate", "--limits", limits, "--base", os.path.join(DATA, "base"),
                     "--head", os.path.join(DATA, "head-pass")]
        if base_rev is not None:
            arguments += ["--base-rev", base_rev]
        if realtime is not None:
            arguments += ["--realtime", realtime]
        if exception is not None:
            arguments += ["--exception-receipt", exception]
        for flag, value in (("--source-base-rev", source_base_rev), ("--source-head-rev", source_head_rev),
                            ("--build-base-identity", build_base_identity),
                            ("--build-head-identity", build_head_identity)):
            if value is not None:
                arguments += [flag, value]
        return run_cli(arguments)

    def test_unchanged_limits_pass_against_immutable_base(self):
        rc, out, err = self.evaluate(DEFAULT_LIMITS)
        self.assertEqual(rc, 0, out + err)
        self.assertIn("perf-gate pass", out)

    def test_unapproved_ir_limit_widening_is_rejected(self):
        original = read_text(DEFAULT_LIMITS, "limits-schema")
        with tempfile.TemporaryDirectory(prefix="perf-limit-ratchet-") as scratch:
            path = os.path.join(scratch, "limits.txt")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(re.sub(r"(?m)^ir_ratio_limit=.*$", "ir_ratio_limit=112/100", original))
            rc, out, err = self.evaluate(path)
        self.assertEqual(rc, 1, out + err)
        self.assertIn("REJECT ir-limit-widening-unapproved", err)

    def test_realtime_floor_cannot_be_changed(self):
        original = read_text(DEFAULT_LIMITS, "limits-schema")
        with tempfile.TemporaryDirectory(prefix="perf-limit-floor-ratchet-") as scratch:
            path = os.path.join(scratch, "limits.txt")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(re.sub(r"(?m)^realtime_floor=.*$", "realtime_floor=3.99", original))
            rc, out, err = self.evaluate(path, realtime=os.path.join(DATA, "realtime-pass.txt"))
        self.assertEqual(rc, 1, out + err)
        self.assertIn("REJECT ratchet-hard-limit-changed", err)

    def test_unresolved_base_revision_is_rejected(self):
        rc, out, err = self.evaluate(DEFAULT_LIMITS, base_rev="f" * 40)
        self.assertEqual(rc, 1, out + err)
        self.assertIn("REJECT ratchet-base-not-commit", err)

    def test_missing_base_revision_is_rejected(self):
        rc, out, err = self.evaluate(DEFAULT_LIMITS, base_rev=None)
        self.assertEqual(rc, 1, out + err)
        self.assertIn("REJECT ratchet-base-required", err)

    def test_unverified_exception_receipt_does_not_authorize_widening(self):
        original = read_text(DEFAULT_LIMITS, "limits-schema")
        with tempfile.TemporaryDirectory(prefix="perf-limit-exception-") as scratch:
            limits = os.path.join(scratch, "limits.txt")
            receipt = os.path.join(scratch, "exception.json")
            with open(limits, "w", encoding="utf-8") as handle:
                handle.write(re.sub(r"(?m)^ir_ratio_limit=.*$", "ir_ratio_limit=112/100", original))
            with open(receipt, "w", encoding="utf-8") as handle:
                json.dump({
                    "schema": EXCEPTION_SCHEMA,
                    "accepted_cause": "deterministic hosted regression",
                    "accepted_cause_reference": "https://example.invalid/decision",
                    "approved_ir_ratio_limit": "112/100",
                    "measurement": {},
                    "measurement_sha256": "0" * 64,
                    "external_verification": {
                        "status": "unverified",
                        "reference": "https://example.invalid/verification",
                        "receipt_sha256": "0" * 64,
                    },
                }, handle)
            rc, out, err = self.evaluate(
                limits, exception=receipt, source_base_rev=V020_SHA,
                source_head_rev=POLICY_BASE_REV, build_base_identity="a" * 64,
                build_head_identity="b" * 64)
        self.assertEqual(rc, 1, out + err)
        self.assertIn("REJECT exception-receipt-unverified", err)


class PerfGateExceptionMeasurementTests(unittest.TestCase):
    """--emit-exception-measurement writes the exact object an owner approves by digest, and still refuses."""

    def widened(self, scratch):
        path = os.path.join(scratch, "limits.txt")
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(re.sub(r"(?m)^ir_ratio_limit=.*$", "ir_ratio_limit=112/100",
                                read_text(DEFAULT_LIMITS, "limits-schema")))
        return path

    def evaluate(self, limits, head, *extra):
        return run_cli(["--evaluate", "--limits", limits, "--base", os.path.join(DATA, "base"),
                        "--head", os.path.join(DATA, head), "--base-rev", POLICY_BASE_REV,
                        "--source-base-rev", V020_SHA, "--source-head-rev", POLICY_BASE_REV,
                        "--build-base-identity", "a" * 64, "--build-head-identity", "b" * 64, *extra])

    def test_widening_writes_the_measurement_and_is_still_unapproved(self):
        with tempfile.TemporaryDirectory(prefix="perf-emit-measurement-") as scratch:
            output = os.path.join(scratch, "measurement.json")
            rc, out, err = self.evaluate(self.widened(scratch), "head-over", "--emit-exception-measurement", output)
            self.assertEqual(rc, 1, out + err)
            self.assertIn("REJECT ir-limit-widening-unapproved", err)
            measurement = json.loads(read_text(output, "measurement-format"))
            self.assertEqual(sorted(measurement["per_rom"]), sorted(ROMS))
            self.assertEqual(measurement["source"]["head_revision"], POLICY_BASE_REV)

    def test_an_existing_measurement_file_is_never_overwritten(self):
        with tempfile.TemporaryDirectory(prefix="perf-emit-existing-") as scratch:
            output = os.path.join(scratch, "measurement.json")
            with open(output, "w", encoding="utf-8", newline="\n") as handle:
                handle.write("keep")
            rc, out, err = self.evaluate(self.widened(scratch), "head-over", "--emit-exception-measurement", output)
            self.assertEqual(rc, 1, out + err)
            self.assertIn("REJECT exception-measurement-output", err)
            self.assertEqual(read_text(output, "measurement-format"), "keep")

    def test_an_unwidened_run_does_not_emit_a_measurement(self):
        with tempfile.TemporaryDirectory(prefix="perf-emit-none-") as scratch:
            output = os.path.join(scratch, "measurement.json")
            rc, out, err = self.evaluate(DEFAULT_LIMITS, "head-pass", "--emit-exception-measurement", output)
            self.assertEqual(rc, 0, out + err)
            self.assertFalse(os.path.exists(output))


class PerfGateRepeatControlsTests(unittest.TestCase):
    def evaluate_head(self, head):
        return run_cli(["--evaluate", "--limits", DEFAULT_LIMITS, "--base", os.path.join(DATA, "base"),
                        "--head", head, "--base-rev", POLICY_BASE_REV])

    def repeated_head(self, directory):
        copy_tree(os.path.join(DATA, "head-pass"), directory)
        for rom in ROMS:
            path = os.path.join(directory, rom + ".line")
            line = read_text(path, "measure-line-format")
            for repeat in (1, 2):
                with open(os.path.join(directory, "%s.line.%d" % (rom, repeat)), "w", encoding="utf-8") as handle:
                    handle.write(line)

    def test_second_repeat_digest_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="perf-repeat-digest-") as scratch:
            head = os.path.join(scratch, "head")
            self.repeated_head(head)
            path = os.path.join(head, "tracer.line.2")
            edit(path, "correctness_digest_fnv1a64=4c7a57ff3d50d228",
                 "correctness_digest_fnv1a64=0000000000000000")
            rc, out, err = self.evaluate_head(head)
        self.assertEqual(rc, 1, out + err)
        self.assertIn("REJECT workload-digest-mismatch", err)

    def test_matching_second_repeat_identity_is_a_passing_control(self):
        with tempfile.TemporaryDirectory(prefix="perf-repeat-matching-") as scratch:
            head = os.path.join(scratch, "head")
            self.repeated_head(head)
            rc, out, err = self.evaluate_head(head)
        self.assertEqual(rc, 0, out + err)
        self.assertIn("perf-gate pass", out)

    def test_second_repeat_workload_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="perf-repeat-workload-") as scratch:
            head = os.path.join(scratch, "head")
            self.repeated_head(head)
            path = os.path.join(head, "tracer.line.2")
            edit(path, "workload=original-wram-tracer-1m-half-dots-v1", "workload=other-workload")
            rc, out, err = self.evaluate_head(head)
        self.assertEqual(rc, 1, out + err)
        self.assertIn("REJECT workload-digest-mismatch", err)

    def test_second_repeat_consumption_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="perf-repeat-consumption-") as scratch:
            head = os.path.join(scratch, "head")
            self.repeated_head(head)
            path = os.path.join(head, "tracer.line.2")
            edit(path, "consumed_half_dots=1000000", "consumed_half_dots=999999")
            rc, out, err = self.evaluate_head(head)
        self.assertEqual(rc, 1, out + err)
        self.assertIn("REJECT proxy-vacuous", err)


def contract_self_test(test_case, label):
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(test_case)
    result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(suite)
    controls = max(0, result.testsRun - 1)
    if result.wasSuccessful() and controls > 0:
        print("perf-gate %s self-test pass controls=%d" % (label, controls))
        return 0
    return 1


def main(argv):
    def option(name):
        if name in argv:
            index = argv.index(name)
            if index + 1 >= len(argv):
                reject("usage", "%s needs a value" % name)
            return argv[index + 1]
        return None

    try:
        if argv == ["--self-test-limit-ratchet"]:
            return contract_self_test(PerfGateLimitRatchetTests, "limit-ratchet")
        elif argv == ["--self-test-exception-measurement"]:
            return contract_self_test(PerfGateExceptionMeasurementTests, "exception-measurement")
        elif argv == ["--self-test-repeat-controls"]:
            return contract_self_test(PerfGateRepeatControlsTests, "repeat-controls")
        elif "--self-test" in argv:
            self_test()
        elif "--check-attribution" in argv:
            _, (revisions, merges, _) = check_attribution(
                option("--check-attribution"), option("--repo") or REPO_ROOT, option("--limits") or DEFAULT_LIMITS)
            print("perf-attribution pass revisions=%d merges=%d" % (revisions, merges))
        elif "--emit-attribution" in argv:
            keys = ("--meas", "--out", "--head", "--realtime", "--runner-image", "--gcc-version",
                    "--valgrind-version", "--hardware-class", "--build-command")
            options = {key: option(key) for key in keys + ("--repo",)}
            if any(options[key] is None for key in keys):
                reject("usage", "--emit-attribution needs " + " ".join(keys))
            emit_attribution(options, option("--limits") or DEFAULT_LIMITS)
        elif "--print-selection" in argv:
            selection = derive_selection(option("--repo") or REPO_ROOT, option("--head") or "HEAD")
            for sha in selection["measured"]:
                print(sha)
        elif "--adapt-harness" in argv:
            with open(option("--adapt-harness"), encoding="utf-8") as handle:
                adapted, source_sha, adapted_sha = adapt_harness(handle.read())
            with open(option("--out"), "w", encoding="utf-8") as handle:
                handle.write(adapted)
            print("harness_source_sha256=%s harness_sha256=%s" % (source_sha, adapted_sha))
        elif "--check-limits" in argv:
            limits = check_limits(option("--check-limits"), option("--root"))
            if option("--base-rev") is not None:
                _, base = immutable_limits(option("--base-rev"))
                if check_policy_ratchet(limits, base):
                    reject("ir-limit-widening-unapproved", "ir_ratio_limit was widened without a deterministic exception receipt")
            print("perf-gate limits ok")
        elif "--evaluate" in argv:
            if None in (option("--limits"), option("--base"), option("--head")):
                reject("usage", "--evaluate needs --limits, --base and --head")
            evaluate(option("--limits"), option("--base"), option("--head"), option("--realtime"),
                     option("--base-rev"), option("--exception-receipt"),
                     option("--source-base-rev"), option("--source-head-rev"),
                     option("--build-base-identity"), option("--build-head-identity"),
                     option("--emit-exception-measurement"))
        else:
            reject("usage", "use --self-test, --check-limits, --evaluate, --check-attribution, --emit-attribution, --print-selection or --adapt-harness")
    except Rejected as error:
        sys.stderr.write("REJECT %s: %s\n" % (error.code, error))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
