#!/usr/bin/env bash
set -euo pipefail

fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
mode=${1:-}
# One list for the draft inventory, the final inventory and the fixture the self-test builds from it.
# The v02 evidence family (corpus, performance, fuzz, source archive, consumer) is validated by its
# owner validators through tests/scripts/verify-v02-delivery.py; the names here only fix the inventory.
REQUIRED_ASSETS="candidate-receipt.json candidate-platform-manifest.json gabbaboy-core-linux-x64.tar.gz gabbaboy-notices.txt source-receipt.json build-receipt.json gabbaboy-core-macos-arm64.tar.gz gabbaboy-core-macos-arm64.tar.gz.sha256 gabbaboy-build-receipt-macos-arm64.json gabbaboy-preview-macos-arm64.tar.gz gabbaboy-preview-macos-arm64-build-receipt.json gabbaboy-core-windows-x64.tar.gz gabbaboy-core-windows-x64.tar.gz.sha256 gabbaboy-build-receipt-windows-x64.json support-ledger.json cgb-corpus-receipt.json v02-performance-receipt.json v02-fuzz-receipt.json source-archive-receipt.json v02-consumer-receipt.json"
export REQUIRED_ASSETS

check_config() {
  python3 - "$ROOT" <<'PY' || return $?
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
v02_route = '\n    check_v02_evidence "$tmp" "$3" "$4" "$src/source.tar.gz"'
def validate_v02_routes(text):
    if text.count(v02_route) != 2:
        raise ValueError("both the draft and the final gate must validate the v0.2 evidence through its owner validators")
try:
    validate_v02_routes(gate_source)
except ValueError as error:
    raise SystemExit(str(error))
try:
    validate_v02_routes(gate_source.replace(v02_route, "\n", 1))
except ValueError:
    pass
else:
    raise SystemExit("release gate self-test accepted a draft or final gate without v0.2 evidence validation")
delivery_source = (root / "tests/scripts/verify-v02-delivery.py").read_text()
for owner in ("verify-support-ledger.py", "verify-v02-performance.py", "verify-v02-fuzz.py", "verify-v02-source-archive.py"):
    if f"tests/scripts/{owner}" not in delivery_source:
        raise SystemExit(f"delivery checker does not call the owner validator {owner}")
def validate_verifier_invocations(text):
    if re.search(r"(?m)^\s*(?!bash\s)(?:python\S*\s+)?tests/scripts/verify-release-candidate\.sh\b", text):
        raise ValueError("release-candidate Bash verifier must be invoked explicitly with bash")
def validate_extractor_destinations(text):
    if re.search(r"(?m)^\s*mkdir(?:\s+-p)?\s+[^\n]*\bbuild/extracted(?:-core)?(?:\s|$)", text):
        raise ValueError("safe release extractor destination must not be pre-created")
# Executable wiring of the evidence producers, judges, attacher and gates (which job runs which command, with what
# authority, after which dependency) is judged by .github/scripts/verify-workflow-policy.py, not by counting text here.
V02_CONTRACTS = ("v02_game_claims", "v02_game_claims_controls", "v02_support_ledger", "v02_support_ledger_controls",
                 "v02_adoption_docs", "v02_adoption_docs_controls", "v02_consumer_controls", "v02_performance_controls",
                 "v02_fuzz_controls", "v02_source_archive_controls", "v02_delivery_controls")
def validate_v02_inventory(cmake_text, expected_text):
    registered = re.findall(r"(?m)^gbb_add_v02_contract\((v02_[a-z_]+) ", cmake_text)
    required = [line.strip() for line in expected_text.splitlines() if line.strip().startswith("v02_")]
    if sorted(registered) != sorted(V02_CONTRACTS):
        raise ValueError("the configured CTest set must register each of the eleven v0.2 contracts exactly once")
    if sorted(required) != sorted(V02_CONTRACTS):
        raise ValueError("the required inventory must name each of the eleven v0.2 contracts exactly once")
    if "-DGBB_EXPECT_CODE=0" not in cmake_text or "[1-9][0-9]*" not in cmake_text:
        raise ValueError("v0.2 contracts must require exit code 0 and a nonzero success count")
def validate_retained_platforms(text):
    # Downloaded-byte consumer and player smoke are required-call checks in verify-workflow-policy.py; only the
    # unsigned/not-notarized declaration literal is data and stays here.
    if text.count('"signed": False') < 2 or text.count('"notarized": False') < 2:
        raise ValueError("the unsigned and not-notarized declaration is not preserved")
def validate_downloaded_sidecars(text):
    required = (
        'bash "$RUNNER_TEMP/verify-release-gates.sh" --check-digest-sidecar \\\n            build/downloaded-core/gabbaboy-core-macos-arm64.tar.gz.sha256 \\\n            build/downloaded-core/gabbaboy-core-macos-arm64.tar.gz',
        'bash build/verify-release-gates.sh --check-digest-sidecar \\\n            build/downloaded/gabbaboy-core-windows-x64.tar.gz.sha256 \\\n            build/downloaded/gabbaboy-core-windows-x64.tar.gz',
        'bash build/verify-release-gates.sh --check-digest-sidecar \\\n            build/downloaded/gabbaboy-core-macos-arm64.tar.gz.sha256 \\\n            build/downloaded/gabbaboy-core-macos-arm64.tar.gz',
    )
    if "sha256sum --check" in text or any(call not in text for call in required):
        raise ValueError("every downloaded Mac/Windows digest-only sidecar must use the strict byte-check helper")
try:
    validate_verifier_invocations(workflow)
    validate_extractor_destinations(workflow)
    validate_retained_platforms(workflow)
    cmake_tests = (root / "tests/CMakeLists.txt").read_text()
    required_inventory = (root / "tests/expected-tests.txt").read_text()
    validate_v02_inventory(cmake_tests, required_inventory)
    validate_downloaded_sidecars(workflow)
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
mutation_count = 0
inventory_mutations = {
    "unregistered contract": (cmake_tests.replace("gbb_add_v02_contract(v02_delivery_controls", "gbb_add_v02_contract(v02_delivery_gone", 1), required_inventory),
    "duplicated registration": (cmake_tests + "\ngbb_add_v02_contract(v02_game_claims 60 x y)\n", required_inventory),
    "missing required name": (cmake_tests, required_inventory.replace("v02_fuzz_controls\n", "", 1)),
    "duplicated required name": (cmake_tests, required_inventory + "v02_support_ledger\n"),
    "exit code not asserted": (cmake_tests.replace("-DGBB_EXPECT_CODE=0", "-DGBB_EXPECT_CODE=none"), required_inventory),
}
for label, (mutated_cmake, mutated_expected) in inventory_mutations.items():
    try:
        validate_v02_inventory(mutated_cmake, mutated_expected)
    except ValueError:
        mutation_count += 1
    else:
        raise SystemExit(f"release workflow self-test accepted a v0.2 inventory with {label}")
if mutation_count < len(inventory_mutations):
    raise SystemExit("release workflow self-test did not execute its v0.2 wiring controls")
print(f"workflow-wiring-controls={mutation_count}")
try:
    validate_downloaded_sidecars(workflow.replace("bash build/verify-release-gates.sh --check-digest-sidecar", "(cd build/downloaded && sha256sum --check", 1))
except ValueError:
    pass
else:
    raise SystemExit("release workflow self-test accepted sha256sum --check for a digest-only sidecar")
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
  python3 - "$rules_json" "$runs_json" "$expected_sha" <<'PY' || return $?
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
  python3 - "$api_json" "$downloaded_dir" "$tag" "$source_sha" "$release_id" <<'PY' || return $?
import hashlib, json, os, pathlib, re, sys
api_path, directory, tag, source_sha, release_id = sys.argv[1:]
assets = json.loads(pathlib.Path(api_path).read_text())
root = pathlib.Path(directory)
required = set(os.environ["REQUIRED_ASSETS"].split())
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
if sidecar.get("schema_version") != 2:
    raise SystemExit("v0.2 release requires the schema-2 support sidecar")
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
  python3 - "$assets_json" "$directory" "$tag" "$source_sha" "$release_id" <<'PY' || return $?
import hashlib, json, os, pathlib, sys
assets = json.loads(pathlib.Path(sys.argv[1]).read_text())
root = pathlib.Path(sys.argv[2])
tag, source, release_id = sys.argv[3:]
expected_count = len(os.environ["REQUIRED_ASSETS"].split()) + 2
if len(assets) != expected_count or len({a.get("name") for a in assets}) != expected_count:
    raise SystemExit(f"published candidate must contain exactly {expected_count} unique assets including final receipts")
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
  python3 - "$receipt_path" "$build_path" "$tag" "$source_sha" "$smoke_runner" <<'PY' || return $?
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
  python3 - "$sidecar" "$archive" <<'PY' || return $?
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

# Owner validators for the sidecar, performance, fuzz and source-archive receipts run from the tagged
# checkout the caller is standing in (the performance and fuzz receipts bind that checkout's HEAD).
check_v02_evidence() {
  local directory=$1 tag=$2 source_sha=$3 archive=$4 repo_root
  repo_root=$(git rev-parse --show-toplevel 2>/dev/null) || fail 'v0.2 evidence validation must run in the exact tag checkout'
  [[ $(git -C "$repo_root" rev-parse HEAD) == "$source_sha" ]] || fail 'checkout HEAD differs from the frozen source SHA'
  # The entry point and every delegated validator come from this script's own checkout (the judge); the exact
  # tag checkout in the current directory is only the subject whose bytes are judged (Plan 05 separation).
  python3 -I "$ROOT/tests/scripts/verify-v02-delivery.py" --check-evidence "$directory" \
    --tag "$tag" --source-sha "$source_sha" --source-archive "$archive" \
    --judge-root "$ROOT" --source-root "$repo_root"
}

fetch_source_archive() {
  local repo=$1 tag=$2 destination=$3
  python3 -I "$ROOT/.github/scripts/download-release-artifact.py" "https://github.com/$repo/archive/refs/tags/$tag.tar.gz" "$destination" \
    --max-bytes 1073741824 --total-timeout 600
}

# Recovery after a publication or readback error. Live release state is read BEFORE any decision, and
# the only outcomes are: verify a published release, reuse an identical draft, or upload only the
# missing assets. Nothing here writes to GitHub. Only runs of the release workflow can block it; unrelated
# CI on the same commit never does. Runs in a subshell so the scratch directory trap is scoped to this call.
RELEASE_WORKFLOW_PATH=.github/workflows/release-please.yml
recovery_decision() (
  local release_id=$1 tag=$2 source_sha=$3 expected=$4 run_id=$5 run_attempt=$6 scope=$7 repo
  [[ "$release_id" =~ ^[0-9]+$ && "$run_id" =~ ^[0-9]+$ && "$run_attempt" =~ ^[0-9]+$ ]] || fail 'release, run and attempt identifiers must be numeric'
  [[ "$tag" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ && "$source_sha" =~ ^[0-9a-f]{40}$ ]] || fail 'release tag or source SHA is malformed'
  [[ "$scope" == full || "$scope" == subset ]] || fail 'recovery scope must be full or subset'
  [[ -s "$expected" ]] || fail 'the trusted expected inventory is missing'
  tmp=$(mktemp -d "${TMPDIR:-/tmp}/gb-recovery.XXXXXX")
  trap 'rm -rf "$tmp"' EXIT HUP INT TERM
  repo=$(gh repo view --json nameWithOwner --jq .nameWithOwner) || fail 'repository identity could not be read'
  gh api "repos/$repo/releases/$release_id" > "$tmp/release.json" || fail 'live release state could not be read'
  [[ $(jq -r .tag_name "$tmp/release.json") == "$tag" ]] || fail 'live release tag differs from the frozen tag'
  gh api "repos/$repo/releases/$release_id/assets?per_page=100" > "$tmp/assets.json" || fail 'live release assets could not be read'
  [[ $(gh api "repos/$repo/commits/$tag" --jq .sha) == "$source_sha" ]] || fail 'live tag does not resolve to the frozen source SHA'
  gh api "repos/$repo/actions/workflows/${RELEASE_WORKFLOW_PATH##*/}/runs?per_page=100" \
    --jq '[.workflow_runs[] | {id, run_attempt, status, head_sha, path, event}]' > "$tmp/runs.json" || fail 'live workflow runs could not be read'
  python3 -I "$ROOT/.github/scripts/verify-published-release-assets.py" --decide \
    "$tmp/release.json" "$tmp/assets.json" "$expected" "$tmp/runs.json" "$run_id" "$run_attempt" \
    "$RELEASE_WORKFLOW_PATH" "$source_sha" "$scope"
)

check_required_asset_sidecars() {
  local directory=$1 platform
  for platform in macos-arm64 windows-x64; do
    check_digest_sidecar \
      "$directory/gabbaboy-core-$platform.tar.gz.sha256" \
      "$directory/gabbaboy-core-$platform.tar.gz" || return $?
  done
}

# expect_reject LABEL REASON COMMAND...: the command must fail and its message must contain REASON.
expect_reject() {
  local label=$1 reason=$2 output
  shift 2
  if output=$("$@" 2>&1); then
    fail "gate accepted $label"
  fi
  [[ "$output" == *"$reason"* ]] || fail "gate rejected $label for the wrong reason: $output"
}

# Build one draft (or final) inventory from REQUIRED_ASSETS. $5 omits an asset, $6 breaks one binding.
inventory_fixture() {
  local dir=$1 tag=$2 sha=$3 release_id=$4 omit=${5:-} defect=${6:-} final=${7:-}
  python3 - "$dir" "$tag" "$sha" "$release_id" "$omit" "$defect" "$final" <<'PY' || return $?
import hashlib, json, os, pathlib, sys
root, tag, sha, release_id, omit, defect, final = sys.argv[1:]
directory = pathlib.Path(root) / "dir"
directory.mkdir(parents=True)
names = os.environ["REQUIRED_ASSETS"].split()
def digest(data): return hashlib.sha256(data).hexdigest()
content = {name: f"bytes of {name}\n".encode() for name in names}
for name in ("source-receipt.json", "candidate-receipt.json"):
    content[name] = json.dumps({"tag_name": tag, "source_sha": sha, "release_id": release_id, "draft": True}).encode()
content["support-ledger.json"] = json.dumps({"schema_version": 1 if defect == "schema1" else 2, "tag": tag, "source_sha": sha,
                                             "ledger": {"git_blob_oid": "d" * 40}}).encode()
for platform in ("macos-arm64", "windows-x64"):
    content[f"gabbaboy-core-{platform}.tar.gz.sha256"] = (digest(content[f"gabbaboy-core-{platform}.tar.gz"]) + "\n").encode()
content["candidate-platform-manifest.json"] = json.dumps({"source_sha": sha, "assets": [
    {"name": n, "sha256": digest(content[n])} for n in names if n != "candidate-platform-manifest.json"]}).encode()
if defect == "stale":
    content["v02-fuzz-receipt.json"] = b"altered after the platform manifest\n"
if final:
    sums = "".join(f"{digest(content[n])}  {n}\n" for n in sorted(names))
    content["SHA256SUMS"] = sums.encode()
    content["release-receipt.json"] = json.dumps({"tag": tag, "source_sha": sha, "release_id": release_id,
                                                  "sha256sums_sha256": digest(content["SHA256SUMS"])}).encode()
    if final == "final-short":
        del content["release-receipt.json"]
if omit:
    del content[omit]
api = []
for index, (name, data) in enumerate(sorted(content.items()), start=1):
    (directory / name).write_bytes(data)
    api.append({"id": index, "name": name, "digest": "sha256:" + digest(data)})
(pathlib.Path(root) / "api.json").write_text(json.dumps(api))
PY
}

# Drive the real --check-recovery CLI with an executable fake gh on PATH. The fake serves raw API-shaped documents and
# applies the caller's --jq, so the production queries are exercised; every call is logged to prove that live release
# state is read first, that nothing writes to GitHub, and that the scratch directory is removed on every exit path.
recovery_self_test() {
  local dir=$1 sha
  sha=$(printf 'c%.0s' {1..40})
  mkdir -p "$dir/bin" "$dir/tmp"
  python3 - "$dir" "$sha" <<'PY' || return $?
import hashlib, json, pathlib, sys
root = pathlib.Path(sys.argv[1])
sha = sys.argv[2]
other = "d" * 40
rows, expected = [], []
for index, name in enumerate(("a.tar.gz", "b.json"), 1):
    data = f"{name} bytes".encode()
    digest = hashlib.sha256(data).hexdigest()
    rows.append({"id": index, "name": name, "size": len(data), "digest": "sha256:" + digest})
    expected.append({"name": name, "size": len(data), "sha256": digest})
final = []
for index, name in ((90, "SHA256SUMS"), (91, "release-receipt.json")):
    data = f"{name} bytes".encode()
    final.append({"id": index, "name": name, "size": len(data), "digest": "sha256:" + hashlib.sha256(data).hexdigest()})
def dump(name, value): (root / name).write_text(json.dumps(value))
dump("assets-complete.json", rows)
dump("assets-changed.json", [dict(rows[0], digest="sha256:" + "0" * 64), rows[1]])
dump("assets-partial.json", rows[:1])
dump("assets-published.json", rows + final)
dump("assets-published-changed.json", [dict(rows[0], digest="sha256:" + "0" * 64), rows[1]] + final)
dump("expected.json", expected)
dump("commit.json", {"sha": sha})
dump("repo.json", {"nameWithOwner": "szTheory/gabbaboy"})
dump("release-draft.json", {"tag_name": "v0.2.0", "draft": True})
dump("release-published.json", {"tag_name": "v0.2.0", "draft": False})
RP = ".github/workflows/release-please.yml"
def run(index, status="completed", attempt=1, path=RP, head=sha, event="push"):
    return {"id": index, "run_attempt": attempt, "status": status, "path": path, "head_sha": head, "event": event}
def runs(*items): return {"total_count": len(items), "workflow_runs": list(items)}
dump("runs-quiet.json", runs(run(7)))
dump("runs-ci.json", runs(run(7), run(8, "in_progress", path=".github/workflows/ci.yml"), run(9, "queued", path=".github/workflows/ci.yml")))
dump("runs-other-push.json", runs(run(7), run(10, "in_progress", head=other)))
dump("runs-active.json", runs(run(7), run(11, "in_progress")))
dump("runs-dispatch.json", runs(run(7), run(12, "queued", head=other, event="workflow_dispatch")))
dump("runs-stale.json", runs(run(7, attempt=2)))
dump("runs-absent.json", runs(run(13)))
PY
  cat > "$dir/bin/gh" <<'GH'
#!/usr/bin/env bash
# Fake GitHub CLI: serves fixture documents and applies --jq, like the real one.
printf '%s\n' "$*" >> "$FAKE_LOG"
args=("$@"); jq_filter=''
for ((i = 0; i < ${#args[@]}; i++)); do [[ ${args[i]} == --jq ]] && jq_filter=${args[i+1]}; done
[[ -z "${FAKE_FAIL:-}" || "$*" != *"$FAKE_FAIL"* ]] || exit 1
case "$*" in
  'repo view'*) file=repo.json ;;
  *"/releases/424242/assets"*) file="$FAKE_ASSETS.json" ;;
  *"/releases/424242") file="release-$FAKE_RELEASE.json" ;;
  *"/commits/v0.2.0"*) file=commit.json ;;
  *"/actions/workflows/release-please.yml/runs"*) file="$FAKE_RUNS.json" ;;
  *) exit 1 ;;
esac
# Like gh --jq: strings print raw, other values print as compact JSON.
if [[ -n "$jq_filter" ]]; then jq -r "($jq_filter) | if type == \"string\" then . else tojson end" "$FAKE_DIR/$file"; else cat "$FAKE_DIR/$file"; fi
GH
  chmod +x "$dir/bin/gh"
  local row release assets runs outcome reason status log="$dir/gh-calls.log" fail_on
  # release | assets | runs | outcome (decision text or REJECT) | reason fragment | gh call that fails
  for row in "draft|assets-complete|runs-quiet|draft-reuse||" "draft|assets-complete|runs-quiet|draft-reuse||" \
             "draft|assets-complete|runs-ci|draft-reuse||" "draft|assets-complete|runs-other-push|draft-reuse||" \
             "draft|assets-partial|runs-quiet|draft-upload-missing:b.json||" \
             "published|assets-published|runs-quiet|published-verified||" \
             "draft|assets-changed|runs-quiet|REJECT|never overwritten|" \
             "draft|assets-complete|runs-active|REJECT|concurrent publication|" \
             "draft|assets-complete|runs-dispatch|REJECT|concurrent publication|" \
             "draft|assets-complete|runs-stale|REJECT|stale|" \
             "draft|assets-complete|runs-absent|REJECT|not in the live|" \
             "published|assets-published-changed|runs-quiet|REJECT|published release does not carry|" \
             "draft|assets-complete|runs-quiet|REJECT|live release assets could not be read|/releases/424242/assets" \
             "draft|assets-complete|runs-quiet|REJECT|live workflow runs could not be read|/actions/workflows/"; do
    IFS='|' read -r release assets runs outcome reason fail_on <<<"$row"
    : > "$log"
    rm -rf "$dir/tmp" && mkdir -p "$dir/tmp"
    output=$(PATH="$dir/bin:$PATH" FAKE_DIR="$dir" FAKE_LOG="$log" FAKE_RELEASE="$release" FAKE_ASSETS="$assets" FAKE_RUNS="$runs" \
             FAKE_FAIL="$fail_on" TMPDIR="$dir/tmp" \
             bash "$ROOT/.github/scripts/verify-release-gates.sh" --check-recovery 424242 v0.2.0 "$sha" "$dir/expected.json" 7 1 full 2>&1) && status=0 || status=$?
    if [[ $outcome == REJECT ]]; then
      [[ $status -ne 0 && "$output" == *"$reason"* && "$output" != *PASS* ]] || fail "recovery accepted or mis-diagnosed $row: $output"
    else
      [[ $status -eq 0 && "$output" == "$outcome" ]] || fail "recovery decided wrongly for $row: $output"
    fi
    [[ $(sed -n 2p "$log") == *'/releases/424242' ]] || fail "recovery did not read live release state first for $row"
    ! grep -Eq 'release (upload|edit|delete|create)|-X |--method|-f |--field|-F ' "$log" || fail "recovery wrote to GitHub for $row"
    ! compgen -G "$dir/tmp/*" >/dev/null || fail "recovery left scratch files behind for $row"
  done
  printf 'PASS: recovery CLI reads live release state first, writes nothing, ignores unrelated CI and cleans up on every exit\n'
  printf 'rejected: changed attachment, concurrent eligible release, concurrent retry dispatch, stale and absent attempt, changed published assets, unreadable live state\n'
}

# The gate's own source-archive fetch must go through the bounded helper with the byte and time caps. A shim python3
# records what the real fetch_source_archive runs; nothing here touches the network.
fetch_source_archive_self_test() {
  local dir=$1 log expect_text
  mkdir -p "$dir/bin"
  log="$dir/fetch-calls.log"
  cat > "$dir/bin/python3" <<'SHIM'
#!/usr/bin/env bash
printf '%s\n' "$*" >> "$FETCH_LOG"
SHIM
  chmod +x "$dir/bin/python3"
  : > "$log"
  PATH="$dir/bin:$PATH" FETCH_LOG="$log" fetch_source_archive szTheory/gabbaboy v0.2.0 "$dir/source.tar.gz"
  [[ $(wc -l < "$log") -eq 1 ]] || fail 'source archive fetch did not run exactly one download'
  expect_text=$(cat "$log")
  [[ "$expect_text" == "-I $ROOT/.github/scripts/download-release-artifact.py https://github.com/szTheory/gabbaboy/archive/refs/tags/v0.2.0.tar.gz $dir/source.tar.gz --max-bytes 1073741824 --total-timeout 600" ]] \
    || fail "source archive fetch bypassed the bounded helper: $expect_text"
  printf 'PASS: source archive fetch runs the bounded download helper with byte and time caps\n'
}

case "$mode" in
  --self-test)
    [[ $# -eq 1 ]] || fail 'usage: verify-release-gates.sh --self-test'
    check_config
    # Executable privilege/trust wiring is judged by the bounded policy reader, not by counting text above.
    python3 -I "$ROOT/.github/scripts/verify-workflow-policy.py" --check --root "$ROOT"
    python3 -I "$ROOT/.github/scripts/verify-workflow-policy.py" --self-test
    bash "$ROOT/.github/scripts/produce-release-evidence.sh" --self-test
    python3 -I "$ROOT/.github/scripts/download-release-artifact.py" --self-test
    python3 "$ROOT/.github/scripts/verify-release-source-proof.py" --self-test
    temp=$(mktemp -d "${TMPDIR:-/tmp}/gb-release-gates.XXXXXX")
    trap 'rm -rf "$temp"' EXIT HUP INT TERM
    fetch_source_archive_self_test "$temp/fetch"
    # The release-candidate data contract runs standalone (no cmake): positive on this tree, negative on a fixture
    # tree whose release-please package is not a draft.
    bash "$ROOT/tests/scripts/verify-release-candidate.sh" --check-config
    config_root="$temp/check-config"
    for file in release-please-config.json .release-please-manifest.json CMakeLists.txt \
        .github/workflows/release.yml .github/workflows/release-please.yml \
        tests/scripts/verify-phase3-player.sh .github/scripts/verify-published-release-assets.py \
        tests/scripts/verify-release-candidate.sh; do
      mkdir -p "$config_root/$(dirname "$file")"
      cp "$ROOT/$file" "$config_root/$file"
    done
    bash "$config_root/tests/scripts/verify-release-candidate.sh" --check-config >/dev/null
    python3 - "$config_root/release-please-config.json" <<'PY'
import json, pathlib, sys
path = pathlib.Path(sys.argv[1])
config = json.loads(path.read_text())
config["packages"]["."]["draft"] = False
path.write_text(json.dumps(config))
PY
    if config_output=$(bash "$config_root/tests/scripts/verify-release-candidate.sh" --check-config 2>&1); then
      fail 'release candidate config contract accepted a release-please package that is not a draft'
    fi
    [[ "$config_output" == *'plus draft and immediate tag'* ]] || fail "release candidate config contract rejected the non-draft package for the wrong reason: $config_output"
    printf 'rejected: release-please package that is not a draft (--check-config)\n'
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
    inventory_fixture "$temp/inventory" v0.2.0 "$(printf 'c%.0s' {1..40})" 424242
    check_asset_inventory "$temp/inventory/api.json" "$temp/inventory/dir" v0.2.0 "$(printf 'c%.0s' {1..40})" 424242
    printf 'PASS: complete v0.2 draft inventory reaches the aggregate gate\n'
    inventory_controls=0
    for asset in $REQUIRED_ASSETS; do
      inventory_fixture "$temp/omit-$asset" v0.2.0 "$(printf 'c%.0s' {1..40})" 424242 "$asset"
      expect_reject "omission of $asset" 'draft asset inventory differs' \
        check_asset_inventory "$temp/omit-$asset/api.json" "$temp/omit-$asset/dir" v0.2.0 "$(printf 'c%.0s' {1..40})" 424242
      inventory_controls=$((inventory_controls + 1))
    done
    printf 'rejected: %s single-asset omissions from the draft inventory\n' "$inventory_controls"
    inventory_fixture "$temp/stale-manifest" v0.2.0 "$(printf 'c%.0s' {1..40})" 424242 "" stale
    expect_reject 'evidence bytes altered after the platform manifest' 'platform manifest does not bind downloaded bytes' \
      check_asset_inventory "$temp/stale-manifest/api.json" "$temp/stale-manifest/dir" v0.2.0 "$(printf 'c%.0s' {1..40})" 424242
    printf 'rejected: evidence bytes altered after the platform manifest\n'
    inventory_fixture "$temp/schema1" v0.2.0 "$(printf 'c%.0s' {1..40})" 424242 "" schema1
    expect_reject 'a schema-1 support sidecar' 'schema-2 support sidecar' \
      check_asset_inventory "$temp/schema1/api.json" "$temp/schema1/dir" v0.2.0 "$(printf 'c%.0s' {1..40})" 424242
    printf 'rejected: schema-1 support sidecar\n'
    inventory_fixture "$temp/final" v0.2.0 "$(printf 'c%.0s' {1..40})" 424242 "" "" final
    check_final_receipt "$temp/final/api.json" "$temp/final/dir" v0.2.0 "$(printf 'c%.0s' {1..40})" 424242
    inventory_fixture "$temp/final-short" v0.2.0 "$(printf 'c%.0s' {1..40})" 424242 "" "" final-short
    expect_reject 'an incomplete final inventory' 'must contain exactly' \
      check_final_receipt "$temp/final-short/api.json" "$temp/final-short/dir" v0.2.0 "$(printf 'c%.0s' {1..40})" 424242
    printf 'PASS: final inventory binds every asset; rejected: incomplete final inventory\n'
    python3 -I "$ROOT/tests/scripts/verify-v02-delivery.py" --self-test
    python3 -I "$ROOT/.github/scripts/verify-published-release-assets.py" --self-test
    recovery_self_test "$temp/recovery"
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
    src=$(mktemp -d "${TMPDIR:-/tmp}/gb-source-archive.XXXXXX")
    trap 'rm -rf "$tmp" "$src"' EXIT HUP INT TERM
    fetch_source_archive "$repo" "$3" "$src/source.tar.gz"
    check_v02_evidence "$tmp" "$3" "$4" "$src/source.tar.gz"
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
    src=$(mktemp -d "${TMPDIR:-/tmp}/gb-source-archive.XXXXXX")
    trap 'rm -rf "$tmp" "$src"' EXIT HUP INT TERM
    fetch_source_archive "$repo" "$3" "$src/source.tar.gz"
    check_v02_evidence "$tmp" "$3" "$4" "$src/source.tar.gz"
    check_final_receipt "$tmp/api-assets.json" "$tmp" "$3" "$4" "$2"
    printf 'PASS: final draft receipt and all downloaded bytes qualify; no publication performed\n'
    ;;
  --check-v02-evidence)
    [[ $# -eq 5 ]] || fail 'usage: verify-release-gates.sh --check-v02-evidence EVIDENCE_DIR TAG SOURCE_SHA SOURCE_ARCHIVE'
    check_v02_evidence "$2" "$3" "$4" "$5"
    ;;
  --check-recovery)
    [[ $# -eq 8 ]] || fail 'usage: verify-release-gates.sh --check-recovery RELEASE_ID TAG SOURCE_SHA EXPECTED_INVENTORY_JSON RUN_ID RUN_ATTEMPT full|subset'
    command -v gh >/dev/null || fail 'GitHub CLI is required'
    command -v jq >/dev/null || fail 'jq is required'
    recovery_decision "$2" "$3" "$4" "$5" "$6" "$7" "$8"
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
  *) fail 'usage: verify-release-gates.sh --self-test | --check-pr PR_NUMBER EXPECTED_HEAD_SHA | --check-merged-source SOURCE_SHA TAG RELEASE_ID SOURCE_RECEIPT PROOF_VERIFIER | --check-draft RELEASE_ID TAG SOURCE_SHA | --check-draft-final RELEASE_ID TAG SOURCE_SHA | --check-v02-evidence EVIDENCE_DIR TAG SOURCE_SHA SOURCE_ARCHIVE | --check-recovery RELEASE_ID TAG SOURCE_SHA EXPECTED_INVENTORY_JSON RUN_ID RUN_ATTEMPT full|subset | --check-runner-evidence CANDIDATE_RECEIPT BUILD_RECEIPT TAG SOURCE_SHA SMOKE_RUNNER | --check-digest-sidecar SIDECAR ARCHIVE' ;;
esac
