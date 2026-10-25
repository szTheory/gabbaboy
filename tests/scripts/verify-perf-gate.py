#!/usr/bin/env python3
"""Cumulative DMG performance gate (Phase 16 TUNE-03, decisions D-13..D-17).

The gate compares valgrind cachegrind instruction counts (Ir, --cache-sim=no) of the head build with a
v0.2.0 build made in the same job, plus a native realtime floor. Ir is a deterministic proxy: it does not
see cache or branch effects, so it is a regression tripwire, not a performance claim. The limitation note
lives in the header of tests/baseline/perf-gate-v1.txt.

Modes (stdlib only, refuses python -O):
  --check-limits FILE [--root DIR]   validate the limits file (and ROM sha256 pins under DIR)
  --evaluate --limits FILE --base DIR --head DIR [--realtime FILE]
  --self-test                        run every control through the real CLI

Every limit comparison is exact integer or fractions.Fraction arithmetic. No float decides a verdict.
"""
import fractions
import hashlib
import os
import re
import subprocess
import sys
import tempfile

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
    for rom in ROMS:
        irs = [parse_cachegrind(os.path.join(directory, "%s.cg.%d" % (rom, n)))
               for n in range(1, repeats + 1)]
        line = parse_measure_line(read_text(os.path.join(directory, rom + ".line"), "measure-line-format"),
                                  "%s/%s.line" % (name, rom))
        side[rom] = {"irs": irs, "line": line}
    return side


def guard_digest(side, name, limits):
    for rom in ROMS:
        line = side[rom]["line"]
        if line["workload"] != WORKLOAD or line["digest"] != limits["roms"][rom]["digest"]:
            reject("workload-digest-mismatch", "%s %s: workload %s digest %s, pinned digest %s" %
                   (name, rom, line["workload"], line["digest"], limits["roms"][rom]["digest"]))


def guard_vacuous(side, name, limits):
    for rom in ROMS:
        pinned = limits["roms"][rom]["consumed_half_dots"]
        if side[rom]["line"]["consumed"] != pinned:
            reject("proxy-vacuous", "%s %s: consumed_half_dots %d, pinned %d" %
                   (name, rom, side[rom]["line"]["consumed"], pinned))
        for ir in side[rom]["irs"]:
            if ir <= limits["ir_floor"]:
                reject("proxy-vacuous", "%s %s: Ir %d is not above the %d floor" %
                       (name, rom, ir, limits["ir_floor"]))


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


def evaluate(limits_path, base_dir, head_dir, realtime_path):
    limits = parse_limits(limits_path)
    base = read_side(base_dir, "base", 1, limits)
    head = read_side(head_dir, "head", 2, limits)
    guard_digest(base, "base", limits)
    guard_digest(head, "head", limits)
    guard_vacuous(base, "base", limits)
    guard_vacuous(head, "head", limits)
    guard_determinism(head, limits)
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
        arguments = ["--evaluate", "--limits", limits, "--base", base, "--head", head]
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
        edit(os.path.join(shifted, "tracer.line"), "consumed_half_dots=1000000", "consumed_half_dots=999999")
        expect("consumed 999999 on tracer is vacuous", 1, evaluate_args(base, shifted),
               stderr_has="REJECT proxy-vacuous")

        # Realtime exactly at the floor passes; one nanosecond slower fails. The floor is built as an exact
        # fraction from the elapsed time, so no rounding is involved.
        elapsed = 100000000
        exact_floor = fractions.Fraction(999992 * 10 ** 9, HALF_DOTS_PER_SECOND * elapsed)  # visible-demo is the tightest ROM
        floor_text = "%d/%d" % (exact_floor.numerator, exact_floor.denominator)
        at_floor = variant("at-floor.txt", realtime_text(elapsed, elapsed))
        below = variant("below-by-one.txt", realtime_text(elapsed + 1, elapsed + 1))
        floor_limits = variant("floor-limits.txt", re.sub(
            r"(?m)^realtime_floor=.*$", "realtime_floor=" + floor_text, original))
        # floor_text is a fraction; the realtime_floor grammar accepts decimals and fractions.
        expect("realtime exactly at the floor passes", 0,
               evaluate_args(base, head("pass"), at_floor, floor_limits), stdout_has="realtime_min=")
        expect("realtime one step below the floor fails", 1,
               evaluate_args(base, head("pass"), below, floor_limits), stderr_has="REJECT realtime-below-floor")

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

    if failures:
        for failure in failures:
            sys.stderr.write("self-test control failed: %s\n" % failure)
        reject("self-test-failed", "%d of %d controls failed" % (len(failures), controls))
    print("perf-gate self-test pass controls=%d" % controls)


def copy_tree(source, destination):
    os.makedirs(destination)
    for name in os.listdir(source):
        with open(os.path.join(source, name), "rb") as src, open(os.path.join(destination, name), "wb") as dst:
            dst.write(src.read())


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


def main(argv):
    def option(name):
        if name in argv:
            index = argv.index(name)
            if index + 1 >= len(argv):
                reject("usage", "%s needs a value" % name)
            return argv[index + 1]
        return None

    try:
        if "--self-test" in argv:
            self_test()
        elif "--check-limits" in argv:
            check_limits(option("--check-limits"), option("--root"))
            print("perf-gate limits ok")
        elif "--evaluate" in argv:
            if None in (option("--limits"), option("--base"), option("--head")):
                reject("usage", "--evaluate needs --limits, --base and --head")
            evaluate(option("--limits"), option("--base"), option("--head"), option("--realtime"))
        else:
            reject("usage", "use --self-test, --check-limits FILE or --evaluate")
    except Rejected as error:
        sys.stderr.write("REJECT %s: %s\n" % (error.code, error))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
