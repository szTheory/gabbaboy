#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
SELF_TEST=false
AB_MODE=false
QUALIFY_MODE=false
AB_BASE=""
AB_HEAD=""
QUALIFY_OUTPUT=""
QUALIFY_REVIEW=""
if [[ "${1:-}" == "--qualify-v02" ]]; then
  if [[ $# -eq 3 && "${2}" == "--output" && -n "${3}" ]]; then
    QUALIFY_MODE=true; QUALIFY_OUTPUT="$3"; shift 3
  elif [[ $# -eq 5 && "${2}" == "--output" && -n "${3}" &&
          "${4}" == "--review-regression" && -n "${5}" ]]; then
    QUALIFY_MODE=true; QUALIFY_OUTPUT="$3"; QUALIFY_REVIEW="$5"; shift 5
  else
    echo "usage: $0 --qualify-v02 --output <receipt.json> [--review-regression <evidence>]" >&2; exit 2
  fi
elif [[ "${1:-}" == "--self-test" ]]; then SELF_TEST=true; shift
elif [[ "${1:-}" == "--ab" ]]; then
  [[ $# -eq 3 && -x "${2}" && -x "${3}" ]] || { echo "usage: $0 --ab <base-measure_core> <head-measure_core>" >&2; exit 2; }
  AB_MODE=true; AB_BASE="$2"; AB_HEAD="$3"; shift 3
fi
[[ $# -eq 0 ]] || { echo "usage: $0 [--self-test | --ab <base-measure_core> <head-measure_core> | --qualify-v02 --output <receipt.json> [--review-regression <evidence>] ]" >&2; exit 2; }
BUILD_DIR="${GBB_RELEASE_MEASURE_BUILD_DIR:-${ROOT_DIR}/build/release-measure}"
ROM="${ROOT_DIR}/fixtures/tracer/tracer.gb"
MANIFEST="${ROOT_DIR}/fixtures/tracer/manifest.json"
TIMEOUT_SECONDS="${GBB_RELEASE_MEASURE_TIMEOUT_SECONDS:-30}"
TOTAL_TIMEOUT_SECONDS="${GBB_RELEASE_MEASURE_TOTAL_TIMEOUT_SECONDS:-900}"
if [[ "$AB_MODE" == true ]]; then
  SAMPLE_COUNT="${GBB_RELEASE_MEASURE_SAMPLES:-30}"
  WARMUP_COUNT="${GBB_RELEASE_MEASURE_WARMUPS:-3}"
else
  SAMPLE_COUNT="${GBB_RELEASE_MEASURE_SAMPLES:-10}"
  WARMUP_COUNT="${GBB_RELEASE_MEASURE_WARMUPS:-2}"
fi
[[ "$TIMEOUT_SECONDS" =~ ^[0-9]+$ ]] && (( TIMEOUT_SECONDS >= 1 && TIMEOUT_SECONDS <= 300 )) || { echo "timeout must be 1..300 seconds" >&2; exit 2; }
[[ "$TOTAL_TIMEOUT_SECONDS" =~ ^[0-9]+$ ]] && (( TOTAL_TIMEOUT_SECONDS >= 30 && TOTAL_TIMEOUT_SECONDS <= 3600 )) || { echo "total timeout must be 30..3600 seconds" >&2; exit 2; }
[[ "$SAMPLE_COUNT" =~ ^[0-9]+$ ]] && (( SAMPLE_COUNT >= 3 && SAMPLE_COUNT <= 30 )) || { echo "samples must be 3..30" >&2; exit 2; }
[[ "$WARMUP_COUNT" =~ ^[0-9]+$ ]] && (( WARMUP_COUNT >= 1 && WARMUP_COUNT <= 20 )) || { echo "warmups must be 1..20" >&2; exit 2; }

# D-22 advisory A/B mode: strictly interleaved pairs of two prebuilt measure_core binaries on the
# frozen DMG workload. Timing is reported, never asserted; only the output digest and the receipt
# shape can fail the run. Host facts are limited to a hardware class (no host or user names).
if [[ "$AB_MODE" == true ]]; then
python3 -I - "$ROOT_DIR" "$ROM" "$AB_BASE" "$AB_HEAD" "$SAMPLE_COUNT" "$WARMUP_COUNT" "$TIMEOUT_SECONDS" <<'PYAB'
import json
import os
import pathlib
import platform
import re
import statistics
import subprocess
import sys

_root, rom, base_bin, head_bin, samples_text, warmups_text, timeout_text = sys.argv[1:]
samples, warmups, timeout_s = int(samples_text), int(warmups_text), int(timeout_text)
WORKLOAD = "original-wram-tracer-1m-half-dots-v1"
expected_digest = "4c7a57ff3d50d228"
receipt_path = pathlib.Path(os.environ.get("GBB_AB_RECEIPT", "ab-receipt.json"))
drop_field = ""
# The digest and drop-field overrides exist only for the negative controls; a stray exported variable
# must not weaken the digest guard, so they are honoured only when GBB_AB_TEST_HOOKS=1 is also set.
if os.environ.get("GBB_AB_TEST_HOOKS") == "1":
    expected_digest = os.environ.get("GBB_AB_EXPECT_DIGEST", expected_digest)
    drop_field = os.environ.get("GBB_AB_DROP_FIELD", "")
FIELDS = ("revision", "build", "hardware", "workload", "model", "output_digest", "warmups",
          "samples", "uncertainty", "ratio", "noise_label", "review_trigger")

def run_once(label, binary):
    done = subprocess.run([binary, "--no-trace", rom], text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, timeout=timeout_s, check=False)
    if done.returncode != 0:
        raise SystemExit(f"ab-run-failed: {label} exited {done.returncode}")
    line = next((l for l in done.stdout.splitlines() if l.startswith("mode=")), "")
    fields = dict(p.split("=", 1) for p in line.split() if "=" in p)
    if fields.get("workload") != WORKLOAD:
        raise SystemExit(f"ab-workload-mismatch: {label}")
    if fields.get("correctness_digest_fnv1a64") != expected_digest:
        raise SystemExit(f"ab-digest-mismatch: {label} printed {fields.get('correctness_digest_fnv1a64')}")
    elapsed = fields.get("elapsed_ns", "")
    if not re.fullmatch(r"[0-9]+", elapsed):
        raise SystemExit(f"ab-field-missing: {label} elapsed_ns={elapsed or 'absent'}")
    return int(elapsed)

def validate_receipt(receipt):
    for field in FIELDS:
        if field not in receipt:
            raise SystemExit(f"ab-receipt-missing: {field}")
    for field in ("sd", "margin_95"):
        if field not in receipt["uncertainty"]:
            raise SystemExit(f"ab-receipt-missing: uncertainty.{field}")
    text = json.dumps(receipt)
    if re.search(r"/(Users|home)/", text):
        raise SystemExit("ab-receipt-private-path")

def hardware_class():
    brand = ""
    if sys.platform == "darwin":
        brand = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], text=True,
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).stdout.strip()
    elif os.path.exists("/proc/cpuinfo"):
        for l in open("/proc/cpuinfo", encoding="utf-8", errors="replace"):
            if l.startswith("model name"):
                brand = l.split(":", 1)[1].strip(); break
    return f"{platform.system()} {platform.machine()}; cpu={brand or 'unknown'}"

def build_string(binary):
    cache = pathlib.Path(binary).resolve().parent / "CMakeCache.txt"
    if not cache.is_file():
        return "unknown"
    keys = {}
    for l in cache.read_text(encoding="utf-8", errors="replace").splitlines():
        for k in ("CMAKE_BUILD_TYPE", "CMAKE_C_COMPILER", "CMAKE_C_FLAGS_RELEASE"):
            if l.startswith(k + ":"):
                keys[k] = l.split("=", 1)[1]
    compiler = keys.get("CMAKE_C_COMPILER", "")
    version = "unknown"
    if compiler:
        out = subprocess.run([compiler, "--version"], text=True, stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL).stdout.splitlines()
        version = out[0] if out else "unknown"
    return f"{keys.get('CMAKE_BUILD_TYPE', 'unknown')} flags={keys.get('CMAKE_C_FLAGS_RELEASE', 'unknown')} cc={version}"

builds = (("base", base_bin), ("head", head_bin))
for _ in range(warmups):
    for label, binary in builds:
        run_once(label, binary)
base_ns, head_ns = [], []
for index in range(samples):
    # Alternate which build runs first so drift and thermal state do not favour one side.
    order = builds if index % 2 == 0 else tuple(reversed(builds))
    got = {label: run_once(label, binary) for label, binary in order}
    base_ns.append(got["base"]); head_ns.append(got["head"])
pair_pct = [100.0 * h / b for h, b in zip(head_ns, base_ns)]
sd = statistics.stdev(pair_pct)
margin = 1.96 * sd / (len(pair_pct) ** 0.5)
median = statistics.median(pair_pct)
min_of_n = 100.0 * min(head_ns) / min(base_ns)
delta = median - 100.0
noise_label = ("within noise (under 3%)" if abs(delta) < 3.0 else
               ("slower than base by more than 3%" if delta > 0 else "faster than base by more than 3%"))
fired = median > 105.0 and (median - margin) > 100.0
receipt = {
    "revision": {"base": os.environ.get("GBB_AB_BASE_REVISION", "unknown"),
                 "head": os.environ.get("GBB_AB_HEAD_REVISION", "unknown")},
    "build": {"base": build_string(base_bin), "head": build_string(head_bin)},
    "hardware": hardware_class(), "workload": WORKLOAD, "model": "DMG-CPU-B",
    "output_digest": expected_digest, "warmups": warmups, "samples": samples,
    "uncertainty": {"sd": sd, "margin_95": margin, "unit": "percent of base time per pair"},
    "ratio": {"median": median, "min": min_of_n, "mean": statistics.mean(pair_pct),
              "unit": "head time as percent of base time"},
    "noise_label": noise_label, "review_trigger": fired,
    "raw_core_elapsed_ns": {"base": base_ns, "head": head_ns},
}
if drop_field:
    receipt.pop(drop_field, None)
validate_receipt(receipt)
receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(f"ab pass samples={samples} median_ratio_pct={median:.2f} min_of_n_ratio_pct={min_of_n:.2f} "
      f"sd_pct={sd:.2f} margin95_pct={margin:.2f} label='{noise_label}' review_trigger={str(fired).lower()}")
PYAB
exit $?
fi

if [[ "$QUALIFY_MODE" == true ]]; then
python3 -I - "$ROOT_DIR" "$QUALIFY_OUTPUT" "$QUALIFY_REVIEW" <<'PYQUAL'
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile

root = Path(sys.argv[1]).resolve()
output = Path(sys.argv[2])
review_notes = sys.argv[3]
if not output.is_absolute():
    output = root / output
output.parent.mkdir(parents=True, exist_ok=True)
if output.exists():
    raise SystemExit(f"qualify-v02-output-exists: {output.name}")

baseline_sha = "e30d168f7fc61de8db0a3801e7b1736362912cb7"
workload_id = "original-wram-tracer-1m-half-dots-v1"
expected_digest = "4c7a57ff3d50d228"
fixture_path = "fixtures/tracer/tracer.gb"
manifest_path = "fixtures/tracer/manifest.json"
harness_path = "tests/measure_core.c"

def run(command, *, cwd=None, env=None, timeout=600):
    done = subprocess.run(command, cwd=cwd, env=env, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          timeout=timeout, check=False)
    if done.returncode:
        raise SystemExit("qualify-v02-command-failed: " + " ".join(map(str, command)) +
                         "\n" + "\n".join((done.stdout or "").splitlines()[-30:]))
    return done.stdout or ""

def git(*args):
    return run(["git", *args], cwd=root, timeout=30).strip()

def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()

def git_blob(revision, path):
    return subprocess.check_output(["git", "show", f"{revision}:{path}"], cwd=root)

def source_record(revision, *, tag=None):
    record = {
        "sha": revision,
        "tree_sha": git("rev-parse", "--verify", f"{revision}^{{tree}}"),
        "harness_sha256": sha_bytes(git_blob(revision, harness_path)),
    }
    if tag:
        record["tag"] = tag
    return record

def parse_cache(path):
    values = {}
    for line in path.read_text(encoding="utf-8", errors="strict").splitlines():
        if ":" not in line or "=" not in line:
            continue
        key, value = line.split("=", 1)[0].split(":", 1)[0], line.split("=", 1)[1]
        values[key] = value
    return values

def build_identity(source, record):
    payload = {key: value for key, value in record.items() if key != "identity_sha256"}
    data = {"source_sha": source["sha"], "source_tree_sha": source["tree_sha"], **payload}
    encoded = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha_bytes(encoded)

baseline_tag_target = git("rev-parse", "v0.1.0^{commit}")
if baseline_tag_target != baseline_sha:
    raise SystemExit("qualify-v02-baseline-tag-mismatch")
candidate_sha = git("rev-parse", "HEAD")
if not re.fullmatch(r"[0-9a-f]{40}", candidate_sha):
    raise SystemExit("qualify-v02-candidate-revision-invalid")
if candidate_sha == baseline_sha:
    raise SystemExit("qualify-v02-source-pair-identical")

compiler_input = os.environ.get("CC", "cc")
compiler = shutil.which(compiler_input) or compiler_input
compiler = str(Path(compiler).resolve())
compiler_hash = sha_bytes(Path(compiler).read_bytes())
flags = os.environ.get("GBB_QUALIFY_C_FLAGS_RELEASE", "-O3 -DNDEBUG")
if "\n" in flags or "\r" in flags:
    raise SystemExit("qualify-v02-release-flags-invalid")

with tempfile.TemporaryDirectory(prefix="gabbaboy-v02-pair-") as temporary:
    temp = Path(temporary)
    baseline_src = temp / "baseline-src"
    candidate_src = temp / "candidate-src"
    baseline_build = temp / "baseline-build"
    candidate_build = temp / "candidate-build"
    base_worktree = False
    candidate_worktree = False
    try:
        run(["git", "worktree", "add", "--detach", str(baseline_src), baseline_sha], cwd=root)
        base_worktree = True
        run(["git", "worktree", "add", "--detach", str(candidate_src), candidate_sha], cwd=root)
        candidate_worktree = True

        base_fixture = git_blob(baseline_sha, fixture_path)
        candidate_fixture = git_blob(candidate_sha, fixture_path)
        base_manifest = git_blob(baseline_sha, manifest_path)
        candidate_manifest = git_blob(candidate_sha, manifest_path)
        if base_fixture != candidate_fixture or base_manifest != candidate_manifest:
            raise SystemExit("qualify-v02-covered-workload-inputs-differ")
        fixture_hash, manifest_hash = sha_bytes(base_fixture), sha_bytes(base_manifest)
        manifest = json.loads(base_manifest)
        if manifest.get("id") != "original-wram-tracer" or manifest.get("sha256") != fixture_hash:
            raise SystemExit("qualify-v02-workload-manifest-mismatch")

        common_cache_args = ["-DCMAKE_BUILD_TYPE=Release", "-DBUILD_TESTING=ON",
                             f"-DCMAKE_C_COMPILER={compiler}", f"-DCMAKE_C_FLAGS_RELEASE={flags}"]
        for source_dir, build_dir in ((baseline_src, baseline_build), (candidate_src, candidate_build)):
            run(["cmake", "-S", str(source_dir), "-B", str(build_dir), *common_cache_args])
            run(["cmake", "--build", str(build_dir), "--target", "measure_core", "--parallel", "2"])

        binaries = [baseline_build / "measure_core", candidate_build / "measure_core"]
        if os.name == "nt":
            binaries = [path.with_suffix(".exe") for path in binaries]
        if not all(path.is_file() and os.access(path, os.X_OK) for path in binaries):
            raise SystemExit("qualify-v02-measurement-binary-missing")

        base_source = source_record(baseline_sha, tag="v0.1.0")
        candidate_source = source_record(candidate_sha)
        builds = {}
        for label, source, build_dir, binary in (
            ("baseline", base_source, baseline_build, binaries[0]),
            ("candidate", candidate_source, candidate_build, binaries[1]),
        ):
            cache = parse_cache(build_dir / "CMakeCache.txt")
            if cache.get("CMAKE_BUILD_TYPE") != "Release":
                raise SystemExit(f"qualify-v02-{label}-not-release")
            actual_compiler = str(Path(cache.get("CMAKE_C_COMPILER", "")).resolve())
            if actual_compiler != compiler:
                raise SystemExit(f"qualify-v02-{label}-compiler-mismatch")
            if cache.get("CMAKE_C_FLAGS_RELEASE") != flags:
                raise SystemExit(f"qualify-v02-{label}-release-flags-mismatch")
            version_output = run([actual_compiler, "--version"], timeout=30).splitlines()
            cmake_output = run(["cmake", "--version"], timeout=30).splitlines()
            compiler_metadata = next(iter((build_dir / "CMakeFiles").glob("*/CMakeCCompiler.cmake")), None)
            if compiler_metadata is None:
                raise SystemExit(f"qualify-v02-{label}-compiler-metadata-missing")
            compiler_text = compiler_metadata.read_text(encoding="utf-8", errors="strict")
            compiler_id_match = re.search(r'set\(CMAKE_C_COMPILER_ID "([^"]+)"\)', compiler_text)
            compiler_version_match = re.search(r'set\(CMAKE_C_COMPILER_VERSION "([^"]+)"\)', compiler_text)
            record = {
                "configuration": "Release",
                "cmake_version": cmake_output[0] if cmake_output else "unknown",
                "generator": cache.get("CMAKE_GENERATOR", "unknown"),
                "compiler": {
                    "id": compiler_id_match.group(1) if compiler_id_match else "unknown",
                    "version": compiler_version_match.group(1) if compiler_version_match else "unknown",
                    "binary_sha256": sha_bytes(Path(actual_compiler).read_bytes()),
                },
                "c_flags_release": cache.get("CMAKE_C_FLAGS_RELEASE", "unknown"),
                "binary_sha256": sha_bytes(binary.read_bytes()),
                "harness_sha256": source["harness_sha256"],
            }
            if record["compiler"]["binary_sha256"] != compiler_hash:
                raise SystemExit(f"qualify-v02-{label}-compiler-binary-changed")
            if not record["compiler"]["id"] or not record["compiler"]["version"] or not version_output:
                raise SystemExit(f"qualify-v02-{label}-compiler-identity-unknown")
            record["identity_sha256"] = build_identity(source, record)
            builds[label] = record

        environment = os.environ.copy()
        environment["GBB_RELEASE_MEASURE_SAMPLES"] = "30"
        environment["GBB_RELEASE_MEASURE_WARMUPS"] = "3"
        environment["GBB_AB_BASE_REVISION"] = baseline_sha
        environment["GBB_AB_HEAD_REVISION"] = candidate_sha
        ab_path = temp / "interleaved-observation.json"
        environment["GBB_AB_RECEIPT"] = str(ab_path)
        script = root / "tests/scripts/measure-release-baseline.sh"
        output_text = run(["bash", str(script), "--ab", str(binaries[0]), str(binaries[1])],
                          cwd=root, env=environment, timeout=900)
        print(output_text.strip())
        ab = json.loads(ab_path.read_text(encoding="utf-8"))
        raw_base = ab["raw_core_elapsed_ns"]["base"]
        raw_candidate = ab["raw_core_elapsed_ns"]["head"]
        pairs = [
            {"baseline_ns": raw_base[index], "candidate_ns": raw_candidate[index],
             "first": "baseline" if index % 2 == 0 else "candidate"}
            for index in range(30)
        ]
        measurement_summary = {
            "median_candidate_to_baseline_percent": ab["ratio"]["median"],
            "mean_candidate_to_baseline_percent": ab["ratio"]["mean"],
            "sample_standard_deviation_percent": ab["uncertainty"]["sd"],
            "approx_95_percent_mean_margin": ab["uncertainty"]["margin_95"],
            "noise_label": ab["noise_label"],
            "review_trigger": ab["review_trigger"],
        }
        triggered = bool(ab["review_trigger"])
        if review_notes and ("\n" in review_notes or "\r" in review_notes or
                             re.search(r"/(Users|home|private|tmp)/|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+", review_notes)):
            raise SystemExit("qualify-v02-review-notes-not-private")
        estimate = ab["ratio"]["median"] - 100.0
        margin = ab["uncertainty"]["margin_95"]
        reviewed_trigger = triggered and bool(review_notes)
        disposition = {
            "review_trigger_percent": 5.0,
            "estimate_percent": estimate,
            "uncertainty_margin_percent": margin,
            "decision": "accepted-with-disclosed-regression" if reviewed_trigger else
                        ("investigation-required" if triggered else "within-noise"),
            "investigation": review_notes if reviewed_trigger else
                             ("The +5% trigger fired; automated qualification remains pending until a source and measurement review is recorded."
                              if triggered else
                              "The median estimate did not clear +5% after accounting for the approximate 95% mean margin."),
            "release_disposition": "accepted-with-disclosed-regression" if reviewed_trigger else
                                  ("pending-investigation" if triggered else "qualified-no-trigger"),
        }
        receipt = {
            "schema_version": 1,
            "result": "passed" if not triggered or reviewed_trigger else "pending-investigation",
            "source": {"baseline": base_source, "candidate": candidate_source},
            "builds": builds,
            "hardware_class": f"{platform.system()} {platform.machine()}",
            "workload": {
                "id": workload_id,
                "model": "DMG-CPU-B",
                "fixture": fixture_path,
                "fixture_sha256": fixture_hash,
                "fixture_manifest_sha256": manifest_hash,
                "budget_half_dots": 1_000_000,
                "correctness_digest_fnv1a64": expected_digest,
            },
            "measurement": {
                "warmups": 3,
                "paired_samples": 30,
                "pairs": pairs,
                "summary": measurement_summary,
                "uncertainty_method": "paired median, sample standard deviation and approximate 95% mean margin",
            },
            "regression_disposition": disposition,
        }
        text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
        temp_output = output.with_name(output.name + f".tmp-{os.getpid()}")
        with open(temp_output, "x", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temp_output, output)
        except FileExistsError:
            temp_output.unlink(missing_ok=True)
            raise SystemExit(f"qualify-v02-output-exists: {output.name}")
        temp_output.unlink()
        print(f"wrote provenance-bound candidate receipt: {output.name}")
        if triggered and not reviewed_trigger:
            raise SystemExit("qualify-v02-review-trigger-fired: receipt remains pending-investigation")
    finally:
        if candidate_worktree:
            subprocess.run(["git", "worktree", "remove", "--force", str(candidate_src)], cwd=root,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        if base_worktree:
            subprocess.run(["git", "worktree", "remove", "--force", str(baseline_src)], cwd=root,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
PYQUAL
exit $?
fi

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
expected_check_sha = os.environ.get("EXPECTED_CHECK_HEAD_SHA", "")
if expected_check_sha:
    require(re.fullmatch(r"[0-9a-f]{40}", expected_check_sha) is not None,
            "expected hosted-check head is not a full commit SHA")
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
    expected_check_head = expected_check_sha or revision
    require(hosted and all(row.get("head_sha") == expected_check_head for row in hosted),
            "tagged receipt requires successful hosted check durations on the exact merged PR head")
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
    "hosted_check_head_sha": expected_check_sha or (revision if expected_sha else None),
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
