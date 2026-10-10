#!/usr/bin/env bash
set -euo pipefail

fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
mode=${1:-}

check_config() {
  python3 - "$ROOT" <<'PY'
import json, pathlib, re, sys
root = pathlib.Path(sys.argv[1])
config = json.loads((root / "release-please-config.json").read_text())
package = config.get("packages", {}).get(".", {})
if package.get("draft") is not True or package.get("force-tag-creation") is not True:
    raise SystemExit("release-please must create one unpublished draft and immediate tag")
excluded = package.get("exclude-paths", [])
expected_excluded = {".github/workflows", ".github/scripts"}
if set(excluded) != expected_excluded:
    raise SystemExit("release-please must exclude only the workflow and release-control script paths")
def excluded_path(path):
    return any(path == prefix or path.startswith(prefix + "/") for prefix in excluded)
if not excluded_path(".github/workflows/release.yml") or not excluded_path(".github/scripts/verify-release-gates.sh"):
    raise SystemExit("release-control-plane paths are not excluded from release parsing")
if excluded_path("src/gabbaboy.c") or excluded_path("CMakeLists.txt"):
    raise SystemExit("release-please exclusion incorrectly hides product source/version paths")
workflow = (root / ".github/workflows/release.yml").read_text()
entrypoint = (root / ".github/workflows/release-please.yml").read_text()
gate_source = (root / ".github/scripts/verify-release-gates.sh").read_text()
aggregate_sidecar_route = '  check_required_asset_sidecars "$downloaded_dir"'
def validate_aggregate_sidecar_route(text):
    if aggregate_sidecar_route not in text:
        raise ValueError("aggregate draft/final inventory must use the strict platform sidecar helper")
try:
    validate_aggregate_sidecar_route(gate_source)
except ValueError as error:
    raise SystemExit(str(error))
try:
    validate_aggregate_sidecar_route(gate_source.replace(aggregate_sidecar_route, ""))
except ValueError:
    pass
else:
    raise SystemExit("release gate self-test accepted an aggregate inventory without strict sidecar validation")
def validate_verifier_invocations(text):
    if re.search(r"(?m)^\s*(?!bash\s)(?:python\S*\s+)?tests/scripts/verify-release-candidate\.sh\b", text):
        raise ValueError("release-candidate Bash verifier must be invoked explicitly with bash")
def validate_extractor_destinations(text):
    if re.search(r"(?m)^\s*mkdir(?:\s+-p)?\s+[^\n]*\bbuild/extracted(?:-core)?(?:\s|$)", text):
        raise ValueError("safe release extractor destination must not be pre-created")
def validate_performance_receipt_path(text):
    pattern = (r"bash tests/scripts/measure-release-baseline\.sh --self-test\s+"
               r"test -s build/release-measure/release-performance-receipt\.json\s+"
               r"cp build/release-measure/release-performance-receipt\.json build/\s+"
               r"cmp -s build/release-measure/release-performance-receipt\.json build/release-performance-receipt\.json")
    if not re.search(pattern, text):
        raise ValueError("generated performance receipt must be validated and copied byte-identically to its canonical build path")
def validate_downloaded_sidecars(text):
    required = (
        'bash "$RUNNER_TEMP/verify-release-gates.sh" --check-digest-sidecar \\\n            build/downloaded-core/gabbaboy-core-macos-arm64.tar.gz.sha256 \\\n            build/downloaded-core/gabbaboy-core-macos-arm64.tar.gz',
        'bash build/verify-release-gates.sh --check-digest-sidecar \\\n            build/downloaded/gabbaboy-core-windows-x64.tar.gz.sha256 \\\n            build/downloaded/gabbaboy-core-windows-x64.tar.gz',
        'bash build/verify-release-gates.sh --check-digest-sidecar \\\n            build/downloaded/gabbaboy-core-macos-arm64.tar.gz.sha256 \\\n            build/downloaded/gabbaboy-core-macos-arm64.tar.gz',
    )
    if "sha256sum --check" in text or any(call not in text for call in required):
        raise ValueError("every downloaded Mac/Windows digest-only sidecar must use the strict byte-check helper")
def validate_isolated_release_readbacks(text):
    validation_match = re.search(r'existing_performance_dir="([^"]+)"', text)
    if not validation_match:
        raise ValueError("existing performance receipt must use its dedicated validation download directory")
    validation_path = validation_match.group(1)
    section_start = text.find('for name in support-ledger.json release-performance-receipt.json; do')
    section_end = text.find('      - name: Validate the exact candidate asset set after platform smoke', section_start)
    if section_start < 0 or section_end < 0:
        raise ValueError("release evidence attachment/readback section is missing")
    section = text[section_start:section_end]
    readback_match = re.search(r'existing_dir="([^"]+)"', section)
    if not readback_match:
        raise ValueError("existing release evidence comparison has no per-asset readback directory")
    readback_path = readback_match.group(1)
    if "$name" not in readback_path:
        raise ValueError("later release evidence readbacks must isolate each asset by name")
    performance_asset_readback = readback_path.replace("$name", "release-performance-receipt.json")
    if validation_path == performance_asset_readback:
        raise ValueError("performance validation and later asset comparison must use different download directories")
    required = (
        'existing_dir="build/existing/asset-readback/$name"',
        'mkdir -p "$existing_dir"',
        '--pattern "$name" --dir "$existing_dir"',
        'cmp -s "build/$name" "$existing_dir/$name"',
    )
    if any(item not in section for item in required):
        raise ValueError("each existing release evidence asset must be downloaded into its own readback directory")
    if re.search(r'gh release download[^\\n]*--pattern "\$name"[^\\n]*--dir build/existing(?:\s|$)', section):
        raise ValueError("per-asset release downloads must not reuse the shared readback directory")
try:
    validate_verifier_invocations(workflow)
    validate_extractor_destinations(workflow)
    validate_performance_receipt_path(workflow)
    validate_downloaded_sidecars(workflow)
    validate_isolated_release_readbacks(workflow)
except ValueError as error:
    raise SystemExit(str(error))
mutated_workflow = workflow.replace("bash tests/scripts/verify-release-candidate.sh", "python tests/scripts/verify-release-candidate.sh", 1)
if mutated_workflow == workflow:
    raise SystemExit("release workflow self-test could not find a Bash verifier invocation")
try:
    validate_verifier_invocations(mutated_workflow)
except ValueError:
    pass
else:
    raise SystemExit("release workflow self-test accepted a Python invocation of a Bash verifier")
try:
    validate_extractor_destinations(workflow + "\n          mkdir -p build/extracted\n")
except ValueError:
    pass
else:
    raise SystemExit("release workflow self-test accepted a pre-created safe-extractor destination")
try:
    validate_performance_receipt_path(workflow.replace("cp build/release-measure/release-performance-receipt.json build/", "", 1))
except ValueError:
    pass
else:
    raise SystemExit("release workflow self-test accepted a missing performance receipt path mapping")
try:
    validate_downloaded_sidecars(workflow.replace("bash build/verify-release-gates.sh --check-digest-sidecar", "(cd build/downloaded && sha256sum --check", 1))
except ValueError:
    pass
else:
    raise SystemExit("release workflow self-test accepted sha256sum --check for a digest-only sidecar")
try:
    validate_isolated_release_readbacks(workflow.replace('existing_performance_dir="build/existing/performance-validation"', 'existing_performance_dir="build/existing/asset-readback/release-performance-receipt.json"', 1))
except ValueError:
    pass
else:
    raise SystemExit("release workflow self-test accepted a shared release evidence readback directory")
for output in ("release_created", "tag_name", "sha"):
    if f"${{{{ steps.release.outputs.{output} }}}}" not in workflow:
        raise SystemExit(f"same-workflow output is missing: {output}")
if "uses: ./.github/workflows/release.yml" not in entrypoint or "workflow_call:" not in workflow:
    raise SystemExit("release-please outputs are not routed through the same workflow run")
if 'git show "${GITHUB_SHA}:.github/scripts/verify-release-source-proof.py"' not in workflow:
    raise SystemExit("final lane does not load the trusted source-proof verifier from its workflow revision")
if not re.search(r'--check-merged-source "\$SOURCE_SHA" "\$RELEASE_TAG" "\$RELEASE_ID" \\\s+build/release-final/source-receipt\.json "\$RUNNER_TEMP/verify-release-source-proof\.py"', workflow):
    raise SystemExit("final lane does not validate its downloaded source receipt against live PR/check evidence")
source_mode_start = gate_source.find("\n  --check-merged-source)\n")
source_mode_end = gate_source.find("\n  --check-draft-final)\n", source_mode_start)
if source_mode_start < 0 or source_mode_end < 0:
    raise SystemExit("source-proof mode is missing")
source_mode = gate_source[source_mode_start + 1:source_mode_end]
def validate_source_proof_temp_paths(text):
    checks = [
        'tmp=$(mktemp -d "${TMPDIR:-/tmp}/gb-source-checks.XXXXXX")' in text,
        '"$tmp/pull-request.json"' in text,
        '"$tmp/check-runs.json"' in text,
        'trap \'rm -rf "$tmp"\' EXIT HUP INT TERM' in text,
        '"${receipt}.pull-request.json"' not in text,
        '"${receipt}.check-runs.json"' not in text,
    ]
    if not all(checks):
        raise ValueError("source-proof API responses must use a cleaned temporary directory outside the downloaded asset inventory")
try:
    validate_source_proof_temp_paths(source_mode)
except ValueError as error:
    raise SystemExit(str(error))
try:
    validate_source_proof_temp_paths(source_mode.replace('tmp=$(mktemp -d "${TMPDIR:-/tmp}/gb-source-checks.XXXXXX")', 'tmp="${receipt}.pull-request.json"', 1))
except ValueError:
    pass
else:
    raise SystemExit("release gate self-test accepted source-proof responses written into the asset inventory")
if 'branches/main/protection' in workflow[workflow.find('publish-qualified-release:'):]:
    raise SystemExit("final lane must not require admin-only branch protection API access")
if not re.search(r"googleapis/release-please-action@[0-9a-f]{40}", workflow):
    raise SystemExit("release-please action is not pinned to a full commit SHA")
if "pull_request_target:" in workflow:
    raise SystemExit("candidate workflow contains an untrusted privileged checkout")
if workflow.count("gh release edit") != 1:
    raise SystemExit("workflow must have exactly one durable publication transition")
publish = workflow.find("publish-qualified-release:")
transition = workflow.find("gh release edit", publish)
final_gate = workflow.find("--check-draft-final", publish)
if publish < 0 or final_gate < publish or transition < final_gate:
    raise SystemExit("publication is not downstream of the exact final downloaded-byte gate")
PY
}

check_required_checks() {
  local rules_json=$1 runs_json=$2 expected_sha=$3
  python3 - "$rules_json" "$runs_json" "$expected_sha" <<'PY'
import json, pathlib, re, sys
rules = json.loads(pathlib.Path(sys.argv[1]).read_text())
runs = json.loads(pathlib.Path(sys.argv[2]).read_text())
expected = sys.argv[3]
if not re.fullmatch(r"[0-9a-f]{40}", expected):
    raise SystemExit("expected PR head is not a full commit SHA")
checks = rules.get("required_status_checks", {}).get("checks")
if checks is None:
    checks = [{"context": name} for name in rules.get("required_status_checks", {}).get("contexts", [])]
required = {item.get("context"): item.get("app_id") for item in checks if item.get("context")}
if not {"required-native", "fixture-repro", "preview-package-smoke"}.issubset(required):
    raise SystemExit("repository branch rules omit one of the three recorded required contexts")
observed = {}
for run in runs.get("check_runs", []):
    if run.get("name") in required:
        observed.setdefault(run.get("name"), []).append(run)
for context, app_id in required.items():
    matches = observed.get(context, [])
    if not matches:
        raise SystemExit(f"required context {context!r} has no check-run evidence")
    for run in matches:
        if run.get("head_sha") != expected:
            raise SystemExit(f"required context {context!r} has stale check evidence")
        if run.get("status") != "completed" or run.get("conclusion") != "success":
            raise SystemExit(f"required context {context!r} is incomplete or concluded {run.get('conclusion')!r}")
        if app_id is not None and run.get("app", {}).get("id") != app_id:
            raise SystemExit(f"required context {context!r} came from the wrong GitHub App")
PY
}

check_asset_inventory() {
  local api_json=$1 downloaded_dir=$2 tag=$3 source_sha=$4 release_id=$5
  python3 - "$api_json" "$downloaded_dir" "$tag" "$source_sha" "$release_id" <<'PY'
import hashlib, json, pathlib, re, sys
api_path, directory, tag, source_sha, release_id = sys.argv[1:]
assets = json.loads(pathlib.Path(api_path).read_text())
root = pathlib.Path(directory)
required = {
    "candidate-receipt.json", "candidate-platform-manifest.json",
    "gabbaboy-core-linux-x64.tar.gz", "gabbaboy-notices.txt", "source-receipt.json",
    "build-receipt.json", "gabbaboy-core-macos-arm64.tar.gz",
    "gabbaboy-core-macos-arm64.tar.gz.sha256", "gabbaboy-build-receipt-macos-arm64.json",
    "gabbaboy-preview-macos-arm64.tar.gz", "gabbaboy-preview-macos-arm64-build-receipt.json",
    "gabbaboy-core-windows-x64.tar.gz", "gabbaboy-core-windows-x64.tar.gz.sha256",
    "gabbaboy-build-receipt-windows-x64.json", "support-ledger.json",
    "release-performance-receipt.json",
}
names = [asset.get("name") for asset in assets]
actual_names = set(names)
if len(names) != len(actual_names) or actual_names not in (required, required | {"SHA256SUMS", "release-receipt.json"}):
    raise SystemExit(f"draft asset inventory differs: missing={sorted(required-actual_names)}, extra={sorted(actual_names-required)}")
if not re.fullmatch(r"v\d+\.\d+\.\d+", tag) or not re.fullmatch(r"[0-9a-f]{40}", source_sha):
    raise SystemExit("release tag/source identity is malformed")
for asset in assets:
    path = root / asset["name"]
    if not path.is_file():
        raise SystemExit(f"downloaded draft asset is missing: {asset['name']}")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    api_digest = asset.get("digest")
    if api_digest and api_digest != "sha256:" + digest:
        raise SystemExit(f"GitHub API digest differs from downloaded bytes: {asset['name']}")
    if not isinstance(asset.get("id"), int):
        raise SystemExit(f"GitHub API asset ID is missing: {asset['name']}")
for name in ("source-receipt.json", "candidate-receipt.json"):
    receipt = json.loads((root / name).read_text())
    for field, value in (("tag_name", tag), ("source_sha", source_sha), ("release_id", release_id), ("draft", True)):
        if receipt.get(field) != value:
            raise SystemExit(f"{name} has mismatched {field}")
sidecar = json.loads((root / "support-ledger.json").read_text())
if sidecar.get("tag") != tag or sidecar.get("source_sha") != source_sha:
    raise SystemExit("support sidecar is not bound to the exact tag/source")
if not re.fullmatch(r"[0-9a-f]{40}", sidecar.get("ledger", {}).get("git_blob_oid", "")):
    raise SystemExit("support sidecar is missing its tagged ledger blob identity")
manifest = json.loads((root / "candidate-platform-manifest.json").read_text())
if manifest.get("source_sha") != source_sha:
    raise SystemExit("platform manifest source SHA differs from candidate")
listed = {item["name"]: item["sha256"] for item in manifest.get("assets", [])}
for name in required - {"candidate-platform-manifest.json"}:
    if name not in listed or listed[name] != hashlib.sha256((root / name).read_bytes()).hexdigest():
        raise SystemExit(f"platform manifest does not bind downloaded bytes: {name}")
PY
  check_required_asset_sidecars "$downloaded_dir"
}

check_final_receipt() {
  local assets_json=$1 directory=$2 tag=$3 source_sha=$4 release_id=$5
  python3 - "$assets_json" "$directory" "$tag" "$source_sha" "$release_id" <<'PY'
import hashlib, json, pathlib, sys
assets = json.loads(pathlib.Path(sys.argv[1]).read_text())
root = pathlib.Path(sys.argv[2])
tag, source, release_id = sys.argv[3:]
if len(assets) != 18 or len({a.get("name") for a in assets}) != 18:
    raise SystemExit("published candidate must contain exactly 18 unique assets including final receipts")
receipt = json.loads((root / "release-receipt.json").read_text())
if receipt.get("tag") != tag or receipt.get("source_sha") != source or str(receipt.get("release_id")) != release_id:
    raise SystemExit("release receipt tag, source SHA, or release ID mismatch")
manifest_sha = hashlib.sha256((root / "SHA256SUMS").read_bytes()).hexdigest()
if receipt.get("sha256sums_sha256") != manifest_sha:
    raise SystemExit("release receipt does not bind the final SHA256SUMS manifest")
listed = {}
for line in (root / "SHA256SUMS").read_text().splitlines():
    digest, name = line.split(None, 1)
    listed[name.lstrip("* ")] = digest
for name, digest in listed.items():
    if name not in {asset["name"] for asset in assets}:
        raise SystemExit(f"SHA256SUMS names an absent API asset: {name}")
    if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest:
        raise SystemExit(f"SHA256SUMS differs from downloaded bytes: {name}")
if set(listed) != {asset["name"] for asset in assets} - {"SHA256SUMS", "release-receipt.json"}:
    raise SystemExit("SHA256SUMS must cover every candidate asset and omit its own/final receipt digest")
for asset in assets:
    path = root / asset["name"]
    if not path.is_file():
        raise SystemExit(f"final downloaded asset missing: {asset['name']}")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if asset.get("digest") and asset["digest"] != "sha256:" + digest:
        raise SystemExit(f"GitHub API digest differs from final downloaded bytes: {asset['name']}")
PY
}

check_runner_evidence() {
  local receipt_path=$1 build_path=$2 tag=$3 source_sha=$4 smoke_runner=$5
  python3 - "$receipt_path" "$build_path" "$tag" "$source_sha" "$smoke_runner" <<'PY'
import hashlib, json, pathlib, re, sys
receipt_path, build_path, expected_tag, expected_source, expected_smoke_runner = sys.argv[1:]
receipt = json.loads(pathlib.Path(receipt_path).read_text())
build_receipt_bytes = pathlib.Path(build_path).read_bytes()
build_receipt = json.loads(build_receipt_bytes)
if receipt.get("tag_name") != expected_tag or receipt.get("source_sha") != expected_source:
    raise SystemExit("candidate runner evidence has a mismatched tag or source SHA")
if not re.fullmatch(r"v\d+\.\d+\.\d+", expected_tag) or not re.fullmatch(r"[0-9a-f]{40}", expected_source):
    raise SystemExit("expected tag/source identity is malformed")
if receipt.get("build_receipt_sha256") != hashlib.sha256(build_receipt_bytes).hexdigest():
    raise SystemExit("candidate does not bind the exact downloaded build receipt bytes")
candidate_build_runner = receipt.get("build", {}).get("runner")
recorded_build_runner = build_receipt.get("build", {}).get("runner")
if not recorded_build_runner or candidate_build_runner != recorded_build_runner:
    raise SystemExit("candidate build runner differs from the build receipt provenance")
if receipt.get("smoke", {}).get("runner") != expected_smoke_runner or not expected_smoke_runner:
    raise SystemExit("candidate smoke runner differs from the downloaded-byte smoke environment")
PY
}

check_digest_sidecar() {
  local sidecar=$1 archive=$2
  python3 - "$sidecar" "$archive" <<'PY'
import hashlib, pathlib, re, sys
sidecar_path, archive_path = map(pathlib.Path, sys.argv[1:])
contents = sidecar_path.read_bytes()
match = re.fullmatch(rb"([0-9a-fA-F]{64})\r?\n?", contents)
if not match:
    raise SystemExit("digest sidecar must contain exactly one 64-hex digest line")
expected = match.group(1).decode("ascii").lower()
actual = hashlib.sha256(archive_path.read_bytes()).hexdigest().lower()
if expected != actual:
    raise SystemExit("digest sidecar does not match downloaded archive bytes")
PY
}

check_required_asset_sidecars() {
  local directory=$1 platform
  for platform in macos-arm64 windows-x64; do
    check_digest_sidecar \
      "$directory/gabbaboy-core-$platform.tar.gz.sha256" \
      "$directory/gabbaboy-core-$platform.tar.gz" || return $?
  done
}

case "$mode" in
  --self-test)
    [[ $# -eq 1 ]] || fail 'usage: verify-release-gates.sh --self-test'
    check_config
    python3 "$ROOT/.github/scripts/verify-release-source-proof.py" --self-test
    temp=$(mktemp -d "${TMPDIR:-/tmp}/gb-release-gates.XXXXXX")
    trap 'rm -rf "$temp"' EXIT HUP INT TERM
    python3 - "$temp" <<'PY'
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
head = "a" * 40
rules = {"required_status_checks": {"checks": [
    {"context": "required-native", "app_id": 15368},
    {"context": "fixture-repro", "app_id": 15368},
    {"context": "preview-package-smoke", "app_id": None}]}}
runs = {"check_runs": [{"name": name, "head_sha": head, "status": "completed", "conclusion": "success",
                         "app": {"id": app_id}}
                        for name, app_id in (("required-native", 15368), ("fixture-repro", 15368),
                                             ("preview-package-smoke", 15368))]}
(root / "rules.json").write_text(json.dumps(rules))
(root / "runs.json").write_text(json.dumps(runs))
PY
    check_required_checks "$temp/rules.json" "$temp/runs.json" "$(printf 'a%.0s' {1..40})"
    cp "$temp/runs.json" "$temp/duplicate-success.json"
    python3 - "$temp/duplicate-success.json" <<'PY'
import json, pathlib, sys
path = pathlib.Path(sys.argv[1])
data = json.loads(path.read_text())
data["check_runs"].append(dict(data["check_runs"][0]))
path.write_text(json.dumps(data))
PY
    check_required_checks "$temp/rules.json" "$temp/duplicate-success.json" "$(printf 'a%.0s' {1..40})"
    cp "$temp/duplicate-success.json" "$temp/mixed-duplicate.json"
    python3 - "$temp/mixed-duplicate.json" <<'PY'
import json, pathlib, sys
path = pathlib.Path(sys.argv[1])
data = json.loads(path.read_text())
data["check_runs"][-1]["conclusion"] = "failure"
path.write_text(json.dumps(data))
PY
    if check_required_checks "$temp/rules.json" "$temp/mixed-duplicate.json" "$(printf 'a%.0s' {1..40})" >/dev/null 2>&1; then
      fail 'exact-head gate accepted mixed successful and failing duplicate check evidence'
    fi
    printf 'rejected: mixed duplicate required-check evidence\n'
    for mutation in stale failed omitted wrong-app; do
      cp "$temp/runs.json" "$temp/$mutation.json"
      python3 - "$temp/$mutation.json" "$mutation" <<'PY'
import json, pathlib, sys
path, kind = pathlib.Path(sys.argv[1]), sys.argv[2]
data = json.loads(path.read_text())
if kind == "stale": data["check_runs"][0]["head_sha"] = "b" * 40
elif kind == "failed": data["check_runs"][0]["conclusion"] = "failure"
elif kind == "omitted": data["check_runs"].pop()
elif kind == "wrong-app": data["check_runs"][0]["app"]["id"] = 1
path.write_text(json.dumps(data))
PY
      if check_required_checks "$temp/rules.json" "$temp/$mutation.json" "$(printf 'a%.0s' {1..40})" >/dev/null 2>&1; then
        fail "exact-head gate accepted $mutation required-check evidence"
      fi
      printf 'rejected: %s required-check evidence\n' "$mutation"
    done
    mkdir -p "$temp/runner"
    python3 - "$temp/runner" <<'PY'
import hashlib, json, pathlib, sys
root = pathlib.Path(sys.argv[1])
build = {"tag_name": "v0.1.0", "source_sha": "a" * 40,
         "build": {"runner": "ubuntu-22.04/ubuntu22/20261004.315.1"}}
(root / "build.json").write_text(json.dumps(build))
candidate = {"tag_name": "v0.1.0", "source_sha": "a" * 40,
             "build_receipt_sha256": hashlib.sha256((root / "build.json").read_bytes()).hexdigest(),
             "build": {"runner": build["build"]["runner"]},
             "smoke": {"runner": "Linux smoke-host 6.8.0 x86_64 GNU/Linux"}}
(root / "candidate.json").write_text(json.dumps(candidate))
PY
    check_runner_evidence "$temp/runner/candidate.json" "$temp/runner/build.json" \
      v0.1.0 "$(printf 'a%.0s' {1..40})" 'Linux smoke-host 6.8.0 x86_64 GNU/Linux'
    for mutation in tag source digest; do
      cp "$temp/runner/candidate.json" "$temp/runner/$mutation.json"
      python3 - "$temp/runner/$mutation.json" "$mutation" <<'PY'
import json, pathlib, sys
path, kind = pathlib.Path(sys.argv[1]), sys.argv[2]
data = json.loads(path.read_text())
if kind == "tag": data["tag_name"] = "v0.1.1"
elif kind == "source": data["source_sha"] = "b" * 40
elif kind == "digest": data["build_receipt_sha256"] = "0" * 64
path.write_text(json.dumps(data))
PY
      if check_runner_evidence "$temp/runner/$mutation.json" "$temp/runner/build.json" \
        v0.1.0 "$(printf 'a%.0s' {1..40})" 'Linux smoke-host 6.8.0 x86_64 GNU/Linux' >/dev/null 2>&1; then
        fail "runner evidence gate accepted $mutation mismatch"
      fi
      printf 'rejected: runner evidence %s mismatch\n' "$mutation"
    done
    printf 'PASS: distinct build/smoke runner identities and bound release evidence\n'
    printf 'release archive bytes\n' > "$temp/archive.tar.gz"
    python3 - "$temp" <<'PY'
import hashlib, pathlib, sys
root = pathlib.Path(sys.argv[1])
digest = hashlib.sha256((root / "archive.tar.gz").read_bytes()).hexdigest()
(root / "digest.sha256").write_text(digest + "\n")
PY
    check_digest_sidecar "$temp/digest.sha256" "$temp/archive.tar.gz"
    cp "$temp/digest.sha256" "$temp/digest-mismatch.sha256"
    printf '%064d\n' 0 > "$temp/digest-mismatch.sha256"
    if check_digest_sidecar "$temp/digest-mismatch.sha256" "$temp/archive.tar.gz" >/dev/null 2>&1; then
      fail 'digest sidecar gate accepted a mismatched archive digest'
    fi
    printf 'rejected: mismatched digest-only sidecar\n'
    for malformed in multiline malformed; do
      if [[ "$malformed" == multiline ]]; then
        printf '%s\n%s\n' "$(cat "$temp/digest.sha256")" "$(cat "$temp/digest.sha256")" > "$temp/$malformed.sha256"
      else
        printf '%064d\n' 0 > "$temp/$malformed.sha256"
      fi
      if check_digest_sidecar "$temp/$malformed.sha256" "$temp/archive.tar.gz" >/dev/null 2>&1; then
        fail "digest sidecar gate accepted $malformed sidecar"
      fi
      printf 'rejected: %s digest-only sidecar\n' "$malformed"
    done
    mkdir -p "$temp/aggregate"
    for platform in macos-arm64 windows-x64; do
      printf '%s archive bytes\n' "$platform" > "$temp/aggregate/gabbaboy-core-$platform.tar.gz"
      python3 - "$temp/aggregate" "$platform" <<'PY'
import hashlib, pathlib, sys
root, platform = pathlib.Path(sys.argv[1]), sys.argv[2]
archive = root / f"gabbaboy-core-{platform}.tar.gz"
(root / (archive.name + ".sha256")).write_text(hashlib.sha256(archive.read_bytes()).hexdigest() + "\n")
PY
    done
    check_required_asset_sidecars "$temp/aggregate"
    printf 'PASS: aggregate gate accepts Mac and Windows digest-only sidecars\n'
    printf '%064d\n' 0 > "$temp/aggregate/gabbaboy-core-macos-arm64.tar.gz.sha256"
    if check_required_asset_sidecars "$temp/aggregate" >/dev/null 2>&1; then
      fail 'aggregate release gate accepted a mismatched Mac digest sidecar'
    fi
    printf 'rejected: aggregate gate detects mismatched platform sidecar\n'
    printf 'PASS: one-line downloaded archive digest sidecar verification\n'
    printf 'PASS: release configuration and exact-head required-check gate\n'
    ;;
  --check-pr)
    [[ $# -eq 3 ]] || fail 'usage: verify-release-gates.sh --check-pr PR_NUMBER EXPECTED_HEAD_SHA'
    command -v gh >/dev/null || fail 'GitHub CLI is required'
    gh auth status >/dev/null 2>&1 || fail 'GitHub CLI authentication is unavailable'
    repo=$(gh repo view --json nameWithOwner --jq .nameWithOwner)
    rules=$(gh api "repos/$repo/branches/main/protection")
    pr=$(gh api "repos/$repo/pulls/$2")
    [[ $(jq -r .base.ref <<<"$pr") == main && $(jq -r .state <<<"$pr") == open ]] || fail 'version PR is not open against main'
    [[ $(jq -r .head.sha <<<"$pr") == "$3" ]] || fail 'version PR head differs from the expected final revision'
    [[ $(jq -r .draft <<<"$pr") == false ]] || fail 'version PR remains a draft'
    [[ $(jq -r .mergeable_state <<<"$pr") == clean ]] || fail 'GitHub does not report current merge eligibility'
    checks=$(gh api "repos/$repo/commits/$3/check-runs?per_page=100")
    tmp=$(mktemp -d "${TMPDIR:-/tmp}/gb-required-checks.XXXXXX")
    trap 'rm -rf "$tmp"' EXIT HUP INT TERM
    printf '%s\n' "$rules" > "$tmp/rules.json"
    printf '%s\n' "$checks" > "$tmp/checks.json"
    check_required_checks "$tmp/rules.json" "$tmp/checks.json" "$3"
    printf 'PASS: PR #%s exact head is eligible under current required checks\n' "$2"
    ;;
  --check-draft)
    [[ $# -eq 4 ]] || fail 'usage: verify-release-gates.sh --check-draft RELEASE_ID TAG SOURCE_SHA'
    command -v gh >/dev/null || fail 'GitHub CLI is required'
    repo=$(gh repo view --json nameWithOwner --jq .nameWithOwner)
    release=$(gh api "repos/$repo/releases/$2")
    [[ $(jq -r .draft <<<"$release") == true ]] || fail 'release is already published'
    [[ $(jq -r .tag_name <<<"$release") == "$3" ]] || fail 'draft release tag differs'
    [[ $(gh api "repos/$repo/commits/$3" --jq .sha) == "$4" ]] || fail 'release tag target differs from the frozen source SHA'
    assets=$(gh api "repos/$repo/releases/$2/assets?per_page=100")
    tmp=$(mktemp -d "${TMPDIR:-/tmp}/gb-release-assets.XXXXXX")
    trap 'rm -rf "$tmp"' EXIT HUP INT TERM
    gh release download "$3" --repo "$repo" --dir "$tmp"
    printf '%s\n' "$assets" > "$tmp/api-assets.json"
    check_asset_inventory "$tmp/api-assets.json" "$tmp" "$3" "$4" "$2"
    printf 'PASS: draft bytes and IDs match the frozen tag/source; no publication performed\n'
    ;;
  --check-merged-source)
    [[ $# -eq 6 ]] || fail 'usage: verify-release-gates.sh --check-merged-source SOURCE_SHA TAG RELEASE_ID SOURCE_RECEIPT PROOF_VERIFIER'
    command -v gh >/dev/null || fail 'GitHub CLI is required'
    repo=$(gh repo view --json nameWithOwner --jq .nameWithOwner)
    source_sha=$2 tag=$3 release_id=$4 receipt=$5 proof_verifier=$6
    proof=$(jq -er '.prior_pr_proof | select(.pr_number > 0 and (.head_sha | test("^[0-9a-f]{40}$")))' "$receipt")
    pr_number=$(jq -r .pr_number <<<"$proof")
    pr_head=$(jq -r .head_sha <<<"$proof")
    tmp=$(mktemp -d "${TMPDIR:-/tmp}/gb-source-checks.XXXXXX")
    trap 'rm -rf "$tmp"' EXIT HUP INT TERM
    gh api "repos/$repo/pulls/$pr_number" > "$tmp/pull-request.json"
    gh api "repos/$repo/commits/$pr_head/check-runs?per_page=100" > "$tmp/check-runs.json"
    python3 "$proof_verifier" --receipt "$receipt" --pull-request "$tmp/pull-request.json" \
      --check-runs "$tmp/check-runs.json" --tag "$tag" --source-sha "$source_sha" --release-id "$release_id"
    ;;
  --check-draft-final)
    [[ $# -eq 4 ]] || fail 'usage: verify-release-gates.sh --check-draft-final RELEASE_ID TAG SOURCE_SHA'
    command -v gh >/dev/null || fail 'GitHub CLI is required'
    repo=$(gh repo view --json nameWithOwner --jq .nameWithOwner)
    release=$(gh api "repos/$repo/releases/$2")
    [[ $(jq -r .draft <<<"$release") == true ]] || fail 'release is already published'
    [[ $(jq -r .tag_name <<<"$release") == "$3" ]] || fail 'draft release tag differs'
    [[ $(gh api "repos/$repo/commits/$3" --jq .sha) == "$4" ]] || fail 'release tag target differs from frozen source SHA'
    assets=$(gh api "repos/$repo/releases/$2/assets?per_page=100")
    tmp=$(mktemp -d "${TMPDIR:-/tmp}/gb-release-final.XXXXXX")
    trap 'rm -rf "$tmp"' EXIT HUP INT TERM
    gh release download "$3" --repo "$repo" --dir "$tmp"
    printf '%s\n' "$assets" > "$tmp/api-assets.json"
    check_asset_inventory "$tmp/api-assets.json" "$tmp" "$3" "$4" "$2"
    check_final_receipt "$tmp/api-assets.json" "$tmp" "$3" "$4" "$2"
    printf 'PASS: final draft receipt and all downloaded bytes qualify; no publication performed\n'
    ;;
  --check-runner-evidence)
    [[ $# -eq 6 ]] || fail 'usage: verify-release-gates.sh --check-runner-evidence CANDIDATE_RECEIPT BUILD_RECEIPT TAG SOURCE_SHA SMOKE_RUNNER'
    check_runner_evidence "$2" "$3" "$4" "$5" "$6"
    printf 'PASS: build and download-smoke runner evidence is independently bound\n'
    ;;
  --check-digest-sidecar)
    [[ $# -eq 3 ]] || fail 'usage: verify-release-gates.sh --check-digest-sidecar SIDECAR ARCHIVE'
    check_digest_sidecar "$2" "$3"
    printf 'PASS: downloaded archive matches its one-line digest sidecar\n'
    ;;
  *) fail 'usage: verify-release-gates.sh --self-test | --check-pr PR_NUMBER EXPECTED_HEAD_SHA | --check-merged-source SOURCE_SHA TAG RELEASE_ID SOURCE_RECEIPT PROOF_VERIFIER | --check-draft RELEASE_ID TAG SOURCE_SHA | --check-draft-final RELEASE_ID TAG SOURCE_SHA | --check-runner-evidence CANDIDATE_RECEIPT BUILD_RECEIPT TAG SOURCE_SHA SMOKE_RUNNER | --check-digest-sidecar SIDECAR ARCHIVE' ;;
esac
