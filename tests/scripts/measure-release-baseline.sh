#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
SELF_TEST=false
if [[ "${1:-}" == "--self-test" ]]; then SELF_TEST=true; shift; fi
[[ $# -eq 0 ]] || { echo "usage: $0 [--self-test]" >&2; exit 2; }
BUILD_DIR="${GBB_RELEASE_MEASURE_BUILD_DIR:-${ROOT_DIR}/build/release-measure}"
ROM="${ROOT_DIR}/fixtures/tracer/tracer.gb"
MANIFEST="${ROOT_DIR}/fixtures/tracer/manifest.json"
TIMEOUT_SECONDS="${GBB_RELEASE_MEASURE_TIMEOUT_SECONDS:-30}"
TOTAL_TIMEOUT_SECONDS="${GBB_RELEASE_MEASURE_TOTAL_TIMEOUT_SECONDS:-900}"
SAMPLE_COUNT="${GBB_RELEASE_MEASURE_SAMPLES:-10}"
WARMUP_COUNT="${GBB_RELEASE_MEASURE_WARMUPS:-2}"
[[ "$TIMEOUT_SECONDS" =~ ^[0-9]+$ ]] && (( TIMEOUT_SECONDS >= 1 && TIMEOUT_SECONDS <= 300 )) || { echo "timeout must be 1..300 seconds" >&2; exit 2; }
[[ "$TOTAL_TIMEOUT_SECONDS" =~ ^[0-9]+$ ]] && (( TOTAL_TIMEOUT_SECONDS >= 30 && TOTAL_TIMEOUT_SECONDS <= 3600 )) || { echo "total timeout must be 30..3600 seconds" >&2; exit 2; }
[[ "$SAMPLE_COUNT" =~ ^[0-9]+$ ]] && (( SAMPLE_COUNT >= 3 && SAMPLE_COUNT <= 30 )) || { echo "samples must be 3..30" >&2; exit 2; }
[[ "$WARMUP_COUNT" =~ ^[0-9]+$ ]] && (( WARMUP_COUNT >= 1 && WARMUP_COUNT <= 20 )) || { echo "warmups must be 1..20" >&2; exit 2; }

python3 - "$ROOT_DIR" "$BUILD_DIR" "$ROM" "$MANIFEST" "$SELF_TEST" \
  "$TIMEOUT_SECONDS" "$TOTAL_TIMEOUT_SECONDS" "$SAMPLE_COUNT" "$WARMUP_COUNT" "${SOURCE_SHA:-}" \
  "${RELEASE_TAG:-}" "${HOSTED_CHECKS_JSON:-}" <<'PY'
import hashlib
import json
import os
import pathlib
import platform
import re
import shlex
import statistics
import subprocess
import sys
import time

root, build_text, rom_text, manifest_text, self_test, timeout_text, total_timeout_text, samples_text, warmups_text, expected_sha, tag, checks_file = sys.argv[1:]
root = pathlib.Path(root)
build = pathlib.Path(build_text)
rom = pathlib.Path(rom_text)
manifest = pathlib.Path(manifest_text)
timeout_s, total_timeout_s = int(timeout_text), int(total_timeout_text)
sample_count, warmup_count = int(samples_text), int(warmups_text)
deadline = time.monotonic() + total_timeout_s

def require(ok, message):
    if not ok:
        raise SystemExit(message)

def run(command, *, timeout=timeout_s, capture=True):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise SystemExit(f"total measurement deadline exceeded ({total_timeout_s}s)")
    timeout = min(timeout, remaining)
    try:
        return subprocess.run(command, cwd=root, text=True, stdout=subprocess.PIPE if capture else None,
                              stderr=subprocess.STDOUT if capture else None, timeout=timeout, check=False)
    except subprocess.TimeoutExpired as error:
        raise SystemExit(f"bounded measurement command timed out after {timeout}s: {shlex.join(command)}") from error

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def source_digest():
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()

def hosted_rows(path):
    if not path:
        return []
    rows = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not rows:
        raise SystemExit("hosted check-run data is empty or malformed")
    clean = []
    for row in rows:
        start, end = row.get("started_at"), row.get("completed_at")
        if row.get("conclusion") != "success" or not start or not end:
            continue
        from datetime import datetime
        parse = lambda value: datetime.fromisoformat(value.replace("Z", "+00:00"))
        duration = (parse(end) - parse(start)).total_seconds()
        if duration < 0:
            raise SystemExit("hosted check has negative duration")
        clean.append({"name": row.get("name"), "run_id": row.get("id"),
                      "started_at": start, "completed_at": end, "duration_seconds": duration,
                      "conclusion": row.get("conclusion"), "head_sha": row.get("head_sha")})
    if not clean:
        raise SystemExit("no successful completed hosted check durations were supplied")
    return clean

def sample_summary(values):
    require(bool(values), "zero samples cannot produce a summary")
    require(all(isinstance(v, (int, float)) and v > 0 for v in values), "sample values must be finite and positive")
    avg = statistics.mean(values)
    stdev = statistics.stdev(values) if len(values) > 1 else 0.0
    return {"count": len(values), "median": statistics.median(values), "min": min(values),
            "max": max(values), "mean": avg, "sample_standard_deviation": stdev,
            "approx_95_percent_mean_margin": 1.96 * stdev / (len(values) ** 0.5)}

def validate_pairs(records):
    require(len(records) == 2, "expected exactly trace-on and trace-off evidence")
    by_mode = {record["mode"]: record for record in records}
    require(set(by_mode) == {"trace", "no-trace"}, "measurement modes are missing or duplicate")
    a, b = by_mode["trace"], by_mode["no-trace"]
    require(a["correctness_digest"] == b["correctness_digest"], "trace-on/off correctness digest mismatch")
    require(a["workload"] == b["workload"] and a["fixture_sha256"] == b["fixture_sha256"],
            "trace-on/off workload or fixture mismatch")
    return by_mode

if self_test == "True":
    try:
        sample_summary([])
    except SystemExit:
        pass
    else:
        raise SystemExit("self-test: zero samples were accepted")
    try:
        validate_pairs([{"mode":"trace","correctness_digest":"a","workload":"w","fixture_sha256":"f"},
                        {"mode":"no-trace","correctness_digest":"b","workload":"w","fixture_sha256":"f"}])
    except SystemExit:
        pass
    else:
        raise SystemExit("self-test: differing trace digests were accepted")

revision = source_digest()
require(re.fullmatch(r"[0-9a-f]{40}", revision) is not None, "Git did not provide a full source SHA")
if expected_sha:
    require(expected_sha == revision and tag, "release source identity does not match checked out HEAD")
    require(subprocess.check_output(["git","rev-parse",f"{tag}^{{commit}}"],cwd=root,text=True).strip() == revision,
            "release tag does not resolve to the measurement source SHA")
    status = subprocess.check_output(["git","status","--porcelain","--untracked-files=all"],cwd=root,text=True)
    require(not status.strip(), "tagged release source tree is dirty")
manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
fixture_sha = sha(rom)
require(manifest_data.get("sha256") == fixture_sha and manifest_data.get("id") == "original-wram-tracer",
        "measurement fixture differs from its rights/digest manifest")
manifest_sha = sha(manifest)

configure_start = time.perf_counter()
configured = run(["cmake", "-S", str(root), "-B", str(build), "-DCMAKE_BUILD_TYPE=Release", "-DBUILD_TESTING=ON"], timeout=600)
configure_seconds = time.perf_counter() - configure_start
require(configured.returncode == 0, "CMake release configure failed:\n" + (configured.stdout or ""))
build_start = time.perf_counter()
built = run(["cmake", "--build", str(build), "--target", "measure_core", "test_audio_no_alloc", "--parallel", "2"], timeout=600)
build_seconds = time.perf_counter() - build_start
require(built.returncode == 0, "core measurement build failed:\n" + (built.stdout or ""))
allocation_test = run(["ctest", "--test-dir", str(build), "--output-on-failure", "--no-tests=error", "-R", "^audio_no_alloc$"])
require(allocation_test.returncode == 0, "existing hot-path allocation assertion failed:\n" + (allocation_test.stdout or ""))
binary = build / ("measure_core.exe" if os.name == "nt" else "measure_core")
require(binary.is_file(), "measurement executable is missing")
cache = (build / "CMakeCache.txt").read_text(encoding="utf-8", errors="strict")
compiler = next((line.split("=",1)[1] for line in cache.splitlines() if line.startswith("CMAKE_C_COMPILER:FILEPATH=")), "unknown")
compiler_version = run([compiler, "--version"]).stdout.splitlines()[0]
cmake_version = run(["cmake", "--version"]).stdout.splitlines()[0]
samples = {"trace": [], "no-trace": []}
for mode in ("trace", "no-trace"):
    for index in range(warmup_count + sample_count):
        command = [str(binary), f"--{mode}", str(rom)]
        started = time.perf_counter_ns()
        result = run(command)
        elapsed_ns = time.perf_counter_ns() - started
        require(result.returncode == 0, f"{mode} workload failed or exceeded timeout:\n{result.stdout}")
        lines = (result.stdout or "").splitlines()
        metric = next((line for line in lines if line.startswith("mode=")), None)
        require(metric is not None, "measurement program emitted no metric record")
        fields = dict(part.split("=", 1) for part in metric.split() if "=" in part)
        require(fields.get("mode") == mode and fields.get("workload") == "original-wram-tracer-1m-half-dots-v1",
                "workload or mode identity mismatch")
        require(fields.get("clock_method") == "monotonic" and int(fields.get("clock_resolution_ns", "0")) > 0,
                "measurement clock precision is absent or malformed")
        require(fields.get("stop_reason") == "0" and int(fields.get("consumed_half_dots", "0")) > 0,
                "measurement did not complete its bounded fixed guest workload")
        rss = int(fields.get("peak_rss_bytes", "0"))
        require(rss > 0, "per-process peak RSS measurement is missing")
        row = {"invocation_wall_seconds": elapsed_ns / 1e9, "core_elapsed_ns": int(fields["elapsed_ns"]),
               "peak_rss_bytes": rss, "consumed_half_dots": int(fields["consumed_half_dots"]),
               "trace_records": int(fields["trace_records"]),
               "correctness_digest": fields["correctness_digest_fnv1a64"]}
        if index >= warmup_count:
            samples[mode].append(row)
        print(f"{mode} {'warmup' if index < warmup_count else 'sample'} {index + 1}: "
              f"core_ns={row['core_elapsed_ns']} wall_s={row['invocation_wall_seconds']:.6f} rss_bytes={rss}")

summary = []
for mode in ("trace", "no-trace"):
    rows = samples[mode]
    summary.append({"mode": mode, "speed_samples_ns": [r["core_elapsed_ns"] for r in rows],
                    "workload": "original-wram-tracer-1m-half-dots-v1", "fixture_sha256": fixture_sha,
                    "invocation_wall_samples_seconds": [r["invocation_wall_seconds"] for r in rows],
                    "peak_rss_samples_bytes": [r["peak_rss_bytes"] for r in rows],
                    "speed_summary_ns": sample_summary([r["core_elapsed_ns"] for r in rows]),
                    "invocation_wall_summary_seconds": sample_summary([r["invocation_wall_seconds"] for r in rows]),
                    "peak_rss_summary_bytes": sample_summary([r["peak_rss_bytes"] for r in rows]),
                    "correctness_digest": rows[0]["correctness_digest"],
                    "trace_record_samples": [r["trace_records"] for r in rows]})
pairs = validate_pairs(summary)
for mode, row in pairs.items():
    print(f"{mode}: median_core_ns={row['speed_summary_ns']['median']:.0f}; "
          f"median peak RSS bytes={row['peak_rss_summary_bytes']['median']:.0f}")
trace_delta_ns = pairs["trace"]["speed_summary_ns"]["median"] - pairs["no-trace"]["speed_summary_ns"]["median"]
trace_delta_percent = 100.0 * trace_delta_ns / pairs["no-trace"]["speed_summary_ns"]["median"]
trace_memory_delta = pairs["trace"]["peak_rss_summary_bytes"]["median"] - pairs["no-trace"]["peak_rss_summary_bytes"]["median"]
print(f"observed trace delta: {trace_delta_ns:.0f} ns ({trace_delta_percent:.2f}%); "
      f"peak RSS delta={trace_memory_delta:.0f} bytes (advisory, not a budget)")

hosted = hosted_rows(checks_file)
if expected_sha:
    require(hosted and all(row.get("head_sha") in (None, revision) for row in hosted),
            "tagged receipt requires exact-source successful hosted check durations")
receipt = {
    "schema_version": 1, "result": "passed", "source_sha": revision,
    "release_tag": tag or None, "source_tree_state": "clean" if expected_sha else
        ("dirty" if subprocess.check_output(["git","status","--porcelain","--untracked-files=all"],cwd=root,text=True).strip() else "clean"),
    "build": {"configuration": "Release", "configure_seconds": configure_seconds,
              "build_seconds": build_seconds, "build_type": "Release",
              "targets": ["measure_core", "test_audio_no_alloc"],
              "compiler_path": compiler, "compiler_version": compiler_version,
              "cmake_version": cmake_version, "os": platform.platform(),
              "cpu": platform.processor() or platform.machine(), "architecture": platform.machine()},
    "workload": {"id": "original-wram-tracer-1m-half-dots-v1", "fixture": "fixtures/tracer/tracer.gb",
                 "fixture_sha256": fixture_sha, "fixture_manifest_sha256": manifest_sha,
                 "license": "MIT", "model": "bootless DMG-CPU-B deterministic software profile",
                 "budget_half_dots": 1000000, "emulated_workload_identical_between_modes": True},
    "warmup_count_per_mode": warmup_count, "sample_count_per_mode": sample_count,
    "samples": summary, "trace_pair_digest_equal": True,
    "observed_trace_delta_ns": trace_delta_ns,
    "observed_trace_delta_percent": trace_delta_percent,
    "observed_trace_peak_rss_delta_bytes": trace_memory_delta,
    "existing_allocation_assertion": {"test": "audio_no_alloc", "result": "passed",
                                      "scope": "gabbaboy_run_audio path only; separate from the timed gbb_run workload"},
    "allocation_measured_for_timed_workload": False,
    "uncertainty_method": "raw samples; median, min/max, sample standard deviation and approximate 95% mean margin (1.96*sd/sqrt(n)); advisory only",
    "interference_and_limits": ["host scheduling and concurrent load affect timing; no CPU isolation is claimed",
                                 "peak RSS includes executable, loader, ROM, and trace storage; it is not core heap-only memory",
                                 "allocation scope is covered by the separate audio_no_alloc regression, not inferred from RSS",
                                 "no budget is selected until repeated variance supports one"],
    "hosted_exact_source_check_durations": hosted,
}
output = build / "release-performance-receipt.json"
output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(f"wrote {output}")
if self_test == "True":
    require(receipt["trace_pair_digest_equal"] and all(len(item["speed_samples_ns"]) == sample_count for item in summary),
            "self-test did not produce complete trace-paired repeated measurements")
    print("release baseline self-test passed: bounded workload, repeated raw samples, memory, uncertainty and trace digest pairing")
PY
