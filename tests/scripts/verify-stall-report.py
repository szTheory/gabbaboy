#!/usr/bin/env python3
"""Check the bounded failure report and its deterministic runner output."""

from __future__ import annotations

import argparse
from collections import Counter
import re
import subprocess
import sys
from pathlib import Path


MAX_BYTES = 65536
MAX_TRACE_RECORDS = 4096
MAX_IO_WRITES = 64
MAX_HISTOGRAM_ENTRIES = 8
PPM_BYTES = 69135
PPM_HEADER = b"P6\n160 144\n255\n"

HEADER_RE = re.compile(
    r"stall id=([A-Za-z0-9][A-Za-z0-9._-]*) reason=([a-z0-9-]+) "
    r"window_start=(0|[1-9][0-9]*) t_end=(0|[1-9][0-9]*) trace_truncated=([01])"
)
TRACE_RE = re.compile(r"([0-9a-f]{6}) ([0-9a-f]{4}) ([0-9a-f]{2})")
IO_RE = re.compile(r"([0-9a-f]{6}) ([0-9a-f]{4}) (ff00|ff0f|ffff|ff40|ff41) ([0-9a-f]{2})")
HISTOGRAM_RE = re.compile(r"([0-9a-f]{4}) ([1-9][0-9]*)")


class ReportError(ValueError):
    pass


def _take_section(lines: list[str], index: int, label: str, limit: int) -> tuple[list[str], int]:
    if index >= len(lines):
        raise ReportError(f"missing {label} section")
    count_key = "entries" if label == "pc_histogram" else "records"
    match = re.fullmatch(rf"{label} {count_key}=([0-9]+)", lines[index])
    if match is None:
        raise ReportError(f"malformed {label} section header")
    count = int(match.group(1))
    if count < 1 or count > limit:
        raise ReportError(f"{label} count {count} is outside 1..{limit}")
    end = index + 1 + count
    if end > len(lines):
        raise ReportError(f"truncated {label} section: declared {count} rows")
    rows = lines[index + 1 : end]
    return rows, end


def validate_report(
    data: bytes, *, expected_id: str | None = None, expected_reason: str | None = None
) -> dict[str, int | str]:
    if not data:
        raise ReportError("report is empty")
    if len(data) > MAX_BYTES:
        raise ReportError(f"report is {len(data)} bytes, above {MAX_BYTES}")
    try:
        text = data.decode("ascii")
    except UnicodeDecodeError as exc:
        raise ReportError("report is not ASCII") from exc
    if "\r" in text or not text.endswith("\n"):
        raise ReportError("report must use complete LF-terminated lines")

    lines = text[:-1].split("\n")
    if not lines or (header := HEADER_RE.fullmatch(lines[0])) is None:
        raise ReportError("malformed stall header or missing trace_truncated flag")
    report_id, reason, window_start_raw, t_end_raw, truncated = header.groups()
    window_start, t_end = int(window_start_raw), int(t_end_raw)
    if t_end < window_start:
        raise ReportError("t_end precedes window_start")
    if expected_id is not None and report_id != expected_id:
        raise ReportError(f"report id is {report_id!r}, expected {expected_id!r}")
    if expected_reason is not None and reason != expected_reason:
        raise ReportError(f"report reason is {reason!r}, expected {expected_reason!r}")

    trace_rows, index = _take_section(lines, 1, "trace", MAX_TRACE_RECORDS)
    trace_times: list[int] = []
    for row in trace_rows:
        match = TRACE_RE.fullmatch(row)
        if match is None:
            raise ReportError("malformed trace row")
        trace_times.append(int(match.group(1), 16))
    if trace_times != sorted(trace_times):
        raise ReportError("trace rows are not in time order")

    io_rows, index = _take_section(lines, index, "io_writes", MAX_IO_WRITES)
    io_times: list[int] = []
    io_addresses: set[str] = set()
    for row in io_rows:
        match = IO_RE.fullmatch(row)
        if match is None:
            raise ReportError("malformed or out-of-scope I/O write row")
        io_times.append(int(match.group(1), 16))
        io_addresses.add(match.group(3))
    if io_times != sorted(io_times):
        raise ReportError("I/O write rows are not in time order")
    if "ff00" not in io_addresses:
        raise ReportError("Libbet failure report has no FF00 input write")

    histogram_rows, index = _take_section(lines, index, "pc_histogram", MAX_HISTOGRAM_ENTRIES)
    histogram: list[tuple[int, int]] = []
    for row in histogram_rows:
        match = HISTOGRAM_RE.fullmatch(row)
        if match is None:
            raise ReportError("malformed program-counter histogram row")
        histogram.append((int(match.group(1), 16), int(match.group(2))))
    if len({pc for pc, _ in histogram}) != len(histogram):
        raise ReportError("program-counter histogram contains duplicate PCs")
    if histogram != sorted(histogram, key=lambda item: (-item[1], item[0])):
        raise ReportError("program-counter histogram is not sorted by count and PC")
    if truncated == "0" and len(trace_rows) < MAX_TRACE_RECORDS:
        trace_pc_counts = Counter(int(row.split()[1], 16) for row in trace_rows)
        expected_histogram = sorted(trace_pc_counts.items(), key=lambda item: (-item[1], item[0]))[
            :MAX_HISTOGRAM_ENTRIES
        ]
        if histogram != expected_histogram:
            raise ReportError("program-counter histogram does not match the complete trace")
    if index != len(lines):
        raise ReportError("unexpected trailing lines after pc_histogram")

    return {
        "id": report_id,
        "reason": reason,
        "trace_truncated": int(truncated),
        "trace_records": len(trace_rows),
        "io_writes": len(io_rows),
        "histogram_entries": len(histogram_rows),
    }


def require_identical(first: bytes, second: bytes, label: str) -> None:
    if first != second:
        raise ReportError(f"repeated {label} bytes differ")


def _sample_report(
    trace_rows: list[str] | None = None,
    *,
    io_rows: list[str] | None = None,
    histogram_rows: list[str] | None = None,
    trace_count: int | None = None,
    io_count: int | None = None,
    histogram_count: int | None = None,
    flag: str = "0",
    tail: str = "",
) -> bytes:
    trace_rows = trace_rows if trace_rows is not None else ["000001 0100 00", "000002 0101 3e"]
    io_rows = io_rows if io_rows is not None else ["000002 0100 ff00 10", "000002 0100 ff40 81"]
    histogram_rows = histogram_rows if histogram_rows is not None else ["0100 1", "0101 1"]
    declared_trace = len(trace_rows) if trace_count is None else trace_count
    declared_io = len(io_rows) if io_count is None else io_count
    declared_histogram = len(histogram_rows) if histogram_count is None else histogram_count
    lines = [
        f"stall id=libbet reason=predicate-not-reached window_start=1 t_end=2 trace_truncated={flag}",
        f"trace records={declared_trace}",
        *trace_rows,
        f"io_writes records={declared_io}",
        *io_rows,
        f"pc_histogram entries={declared_histogram}",
        *histogram_rows,
    ]
    if tail:
        lines.append(tail)
    return ("\n".join(lines) + "\n").encode("ascii")


def run_self_test() -> None:
    valid = _sample_report()
    summary = validate_report(valid, expected_id="libbet", expected_reason="predicate-not-reached")
    if (summary["trace_records"], summary["io_writes"], summary["histogram_entries"]) != (2, 2, 2):
        raise ReportError("valid sample counts were not preserved")

    trace_rows_4097 = [f"{i:06x} 0100 00" for i in range(MAX_TRACE_RECORDS + 1)]
    io_rows_65 = [f"{i:06x} 0100 ff00 10" for i in range(MAX_IO_WRITES + 1)]
    histogram_rows_9 = [f"{i:04x} 1" for i in range(MAX_HISTOGRAM_ENTRIES + 1)]
    negatives = {
        "empty": b"",
        "missing sections": b"stall id=libbet reason=predicate-not-reached window_start=1 t_end=2 trace_truncated=0\n",
        "truncated trace section": _sample_report(trace_rows=["000001 0100 00"], trace_count=2),
        "truncated I/O section": _sample_report(io_rows=["000002 0100 ff00 10"], io_count=2),
        "truncated histogram section": _sample_report(histogram_rows=["0100 1"], histogram_count=2),
        "malformed trace row": _sample_report(trace_rows=["not a trace row"]),
        "incorrect trace count": _sample_report(trace_count=3),
        "malformed I/O row": _sample_report(io_rows=["000002 0100 ff02 01"]),
        "missing FF00 input": _sample_report(io_rows=["000002 0100 ff40 81"]),
        "incorrect histogram ordering": _sample_report(histogram_rows=["0101 1", "0100 2"]),
        "incorrect histogram counts": _sample_report(histogram_rows=["0100 2", "0101 1"]),
        "missing truncation flag": valid.replace(b" trace_truncated=0", b""),
        "invalid truncation flag": valid.replace(b"trace_truncated=0", b"trace_truncated=2"),
        "wrong id": _sample_report().replace(b"id=libbet", b"id=other"),
        "wrong reason": valid.replace(b"reason=predicate-not-reached", b"reason=frame-mismatch"),
        "4097 trace records": _sample_report(trace_rows=trace_rows_4097),
        "65 I/O writes": _sample_report(io_rows=io_rows_65),
        "9 histogram entries": _sample_report(histogram_rows=histogram_rows_9),
        "over 64 KiB": valid + b"x" * (MAX_BYTES - len(valid) + 1),
    }
    for label, sample in negatives.items():
        try:
            validate_report(sample, expected_id="libbet", expected_reason="predicate-not-reached")
        except ReportError:
            continue
        raise ReportError(f"negative control unexpectedly passed: {label}")

    try:
        require_identical(valid, valid + b" ", "report")
    except ReportError:
        pass
    else:
        raise ReportError("mismatching repeated reports unexpectedly passed")

    print(f"stall-report-selftest pass rejected={len(negatives) + 1} report-controls={len(negatives)} repeated-byte-mismatch=1")


def run_integration(args: argparse.Namespace) -> None:
    runner = Path(args.runner).resolve()
    cases = Path(args.cases).resolve()
    workdir = Path(args.workdir).resolve()
    failure_dir = Path(args.failure_dir).resolve()
    failure_dir.mkdir(parents=True, exist_ok=True)
    report_path = failure_dir / "libbet.stall.txt"
    ppm_path = failure_dir / "libbet.ppm"
    run_artifacts: list[tuple[bytes, bytes]] = []

    command = [
        str(runner),
        "--acceptance",
        str(cases),
        "--case",
        "libbet",
        "--mutate",
        "drop:START",
        "--failure-dir",
        str(failure_dir),
    ]
    for run_number in (1, 2):
        report_path.unlink(missing_ok=True)
        ppm_path.unlink(missing_ok=True)
        try:
            result = subprocess.run(
                command,
                cwd=workdir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=args.runner_timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise ReportError(f"runner timed out on repetition {run_number}") from exc
        if result.returncode != 1:
            raise ReportError(
                f"runner repetition {run_number} returned {result.returncode}, expected 1:\n{result.stdout}"
            )
        if not re.search(
            r"acceptance id=libbet status=fail model=dmg-cpu-b reason=predicate-not-reached\b",
            result.stdout,
        ):
            raise ReportError(f"runner repetition {run_number} missed the expected failure:\n{result.stdout}")
        if not report_path.is_file() or not ppm_path.is_file():
            raise ReportError(f"runner repetition {run_number} did not create fresh report and PPM files")

        report = report_path.read_bytes()
        summary = validate_report(report, expected_id="libbet", expected_reason="predicate-not-reached")
        if summary["trace_truncated"] != 0:
            raise ReportError("small Libbet report unexpectedly marked trace_truncated")
        ppm = ppm_path.read_bytes()
        if len(ppm) != PPM_BYTES or not ppm.startswith(PPM_HEADER):
            raise ReportError(f"failure PPM is not a complete 160x144 P6 image ({len(ppm)} bytes)")
        run_artifacts.append((report, ppm))

    require_identical(run_artifacts[0][0], run_artifacts[1][0], "stall report")
    require_identical(run_artifacts[0][1], run_artifacts[1][1], "failure PPM")
    summary = validate_report(
        run_artifacts[0][0], expected_id="libbet", expected_reason="predicate-not-reached"
    )
    print(
        "stall-report-integration pass "
        f"bytes={len(run_artifacts[0][0])} trace={summary['trace_records']} "
        f"io_writes={summary['io_writes']} pc_histogram={summary['histogram_entries']} "
        "fresh=2 deterministic=report+ppm"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--runner")
    parser.add_argument("--cases")
    parser.add_argument("--workdir")
    parser.add_argument("--failure-dir")
    parser.add_argument("--runner-timeout", type=int, default=300)
    args = parser.parse_args()
    try:
        if args.self_test:
            run_self_test()
        elif all((args.runner, args.cases, args.workdir, args.failure_dir)):
            run_integration(args)
        else:
            parser.error("use --self-test or provide --runner, --cases, --workdir and --failure-dir")
    except (OSError, ReportError) as exc:
        print(f"stall-report-check failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
