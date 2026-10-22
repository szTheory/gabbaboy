#!/usr/bin/env bash
set -euo pipefail

fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
sha256_file() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | cut -d ' ' -f1
  else
    shasum -a 256 "$1" | cut -d ' ' -f1
  fi
}
ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
MODE=${1:-}
SOURCE_ARCHIVE_CHECKER="$ROOT_DIR/tests/scripts/verify-v02-source-archive.py"
USAGE='usage: verify-release-candidate.sh --self-test | --check-config | --verify RECEIPT ASSET VERSION TAG SOURCE_SHA RELEASE_ID NOTICE_FILE SOURCE_RECEIPT BUILD_RECEIPT | --verify-final <the --verify arguments> SOURCE_ARCHIVE SOURCE_ARCHIVE_RECEIPT [SOURCE_REPOSITORY]'
safe_extract() {
  python3 -I "$ROOT_DIR/tests/scripts/verify-v02-consumers.py" --extract "$1" "$2"
}
candidate_consumer_verify() {
  local build_receipt=$1 asset=$2 expected_source=$3 temp_root=$4
  local candidate_manifest="$temp_root/candidate-manifest.json"
  local consumer_output="$temp_root/consumer-receipt.json"
  python3 - "$build_receipt" "$asset" "$expected_source" "$candidate_manifest" <<'PY'
import hashlib, json, pathlib, re, sys
build_path, asset_path, expected_source, manifest_path = map(pathlib.Path, sys.argv[1:])
expected_source = sys.argv[3]
try:
    build_bytes = build_path.read_bytes()
    build = json.loads(build_bytes.decode("utf-8"))
    digest = hashlib.sha256()
    with asset_path.open("rb") as stream:
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
except (OSError, UnicodeError, ValueError) as error:
    raise SystemExit(f"candidate manifest input is unreadable: {type(error).__name__}")
archive_sha = digest.hexdigest()
if not re.fullmatch(r"[0-9a-f]{40,64}", expected_source):
    raise SystemExit("candidate source SHA is malformed")
if build.get("source_sha") != expected_source or build.get("asset_sha256") != archive_sha:
    raise SystemExit("validated build receipt identity differs from candidate inputs")
manifest = {
    "schema_version": 1,
    "candidate_source_sha": expected_source,
    "archive_sha256": archive_sha,
    "build_receipt_sha256": hashlib.sha256(build_bytes).hexdigest(),
}
manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
  python3 -I "$ROOT_DIR/tests/scripts/verify-v02-consumers.py" \
    --archive "$asset" --candidate-manifest "$candidate_manifest" --output "$consumer_output"
}
# The release configuration data contract: the release-please package settings and manifest version stay
# data checks here, while the executable wiring of release.yml (which job runs which command, on which runner,
# behind which guard) is judged from parsed workflow structure by .github/scripts/verify-workflow-policy.py.
# It runs without cmake so that --check-config can be exercised on fixture trees.
release_config_contract() {
python3 - "$ROOT_DIR" <<'PY'
import json, pathlib, re, sys
root = pathlib.Path(sys.argv[1])
config = json.loads((root / "release-please-config.json").read_text())
manifest = json.loads((root / ".release-please-manifest.json").read_text())
package = config.get("packages", {}).get(".", {})
version = re.search(r"^project\(GabbaBoy VERSION ([0-9]+\.[0-9]+\.[0-9]+)", (root / "CMakeLists.txt").read_text(), re.M)
workflow = (root / ".github/workflows/release.yml").read_text()
entrypoint = (root / ".github/workflows/release-please.yml").read_text()
player_verifier = (root / "tests/scripts/verify-phase3-player.sh").read_text()
published_asset_verifier = (root / ".github/scripts/verify-published-release-assets.py").read_text()
if not version or manifest.get(".") != version.group(1):
    raise SystemExit("release manifest and CMake PROJECT_VERSION do not match")
if package.get("draft") is not True or package.get("force-tag-creation") is not True or package.get("include-component-in-tag") is not False or package.get("include-v-in-tag") is not True:
    raise SystemExit("manifest release must use matching v<version> tag plus draft and immediate tag")
if "needs: [release, candidate-macos]" not in workflow:
    raise SystemExit("Windows downloaded-archive verification must run after the existing native Linux and macOS lanes")
for required in ("SDL_AUDIO_DRIVER=dummy", "SDL_VIDEO_DRIVER=dummy", "--smoke-package", "packaged MBC1 continuation fixture resumed in a fresh process"):
    if required not in player_verifier:
        raise SystemExit(f"downloaded player verification is missing scripted lifecycle evidence: {required}")
if "pull_request_target:" in workflow or "release: {" in workflow:
    raise SystemExit("candidate workflow contains a privileged PR route")
def validate_publication_contract(text):
    gate = text.find('bash trusted/.github/scripts/verify-release-gates.sh --check-draft-final "$RELEASE_ID" "$RELEASE_TAG" "$SOURCE_SHA"')
    publish = text.find('gh release edit "$RELEASE_TAG" --repo "$GH_REPO" --draft=false --verify-tag')
    if gate < 0 or publish < 0 or gate > publish:
        raise ValueError("publication must occur only after the final downloaded-byte gate")
    if 'python3 -I trusted/.github/scripts/verify-published-release-assets.py "$assets" build/release-final/api-assets.json' not in text:
        raise ValueError("published API response must use the tested direct-JSON inventory verifier")
    if "json.loads(after_json)" not in published_asset_verifier or "Path(after_json).is_file" in published_asset_verifier:
        raise ValueError("published API asset verifier must parse response JSON directly, not treat it as a path")
try:
    validate_publication_contract(workflow)
except ValueError as error:
    raise SystemExit(str(error))
gate_call = 'bash trusted/.github/scripts/verify-release-gates.sh --check-draft-final "$RELEASE_ID" "$RELEASE_TAG" "$SOURCE_SHA"'
publish_call = 'gh release edit "$RELEASE_TAG" --repo "$GH_REPO" --draft=false --verify-tag'
mutated_publication = workflow.replace(gate_call, "", 1).replace(publish_call, publish_call + "\n          " + gate_call, 1)
try:
    validate_publication_contract(mutated_publication)
except ValueError:
    pass
else:
    raise SystemExit("release workflow self-test accepted publication before the final downloaded-byte gate")
# A bare value may contain whole `${{ ... }}` expressions, whose spaces are part
# of the value in an unquoted YAML env entry such as preview.yml's.
VERIFIED_OUTPUT_VALUE = r"""(?:"([^"\n]*)"|'([^'\n]*)'|((?:\$\{\{[^}\n]*\}\}|[^\s"'])*))"""
def validate_verified_output_contract(text):
    # The player verifier helper rejects the checkout and its descendants, so a
    # checkout-relative output only fails after the draft and tag already exist.
    name = "GBB_VERIFIED_OUTPUT_DIR"
    assignments = re.findall(name + r"\s*[:=]\s*" + VERIFIED_OUTPUT_VALUE, text)
    if text.count(name) != len(assignments):
        raise ValueError(f"{name} is used in a form the release contract cannot check; assign it explicitly under $RUNNER_TEMP")
    for quoted_double, quoted_single, bare in assignments:
        value = quoted_double or quoted_single or bare
        if ".." in value.split("/") or not re.match(r"(\$RUNNER_TEMP|\$\{RUNNER_TEMP\}|\$\{\{\s*runner\.temp\s*\}\})(/|$)", value):
            raise ValueError(f"{name} must be rooted at a runner temp location, not the checkout: {value!r}")
try:
    validate_verified_output_contract(workflow)
except ValueError as error:
    raise SystemExit(str(error))
# Rewrite every existing assignment, or add one when the workflow relies on the verifier default.
mutated_output = re.sub(r"(GBB_VERIFIED_OUTPUT_DIR\s*[:=]\s*)" + VERIFIED_OUTPUT_VALUE, lambda m: m.group(1) + "build/release-player-downloaded", workflow)
if mutated_output == workflow:
    mutated_output = workflow + "\nGBB_VERIFIED_OUTPUT_DIR=build/release-player-downloaded\n"
try:
    validate_verified_output_contract(mutated_output)
except ValueError:
    pass
else:
    raise SystemExit("release workflow self-test accepted a verified output directory inside the checkout")
try:
    validate_verified_output_contract("    env:\n      GBB_VERIFIED_OUTPUT_DIR: ${{ runner.temp }}/verified-player-artifact\n")
except ValueError as error:
    raise SystemExit(f"release workflow self-test rejected an unquoted runner.temp YAML value: {error}")
if "workflow_call:" not in workflow or "uses: ./.github/workflows/release.yml" not in entrypoint:
    raise SystemExit("release-please outputs and candidate jobs are not connected in one workflow run")
PY
}
if [[ "$MODE" == --extract ]]; then
  [[ $# -eq 3 ]] || fail 'usage: verify-release-candidate.sh --extract ARCHIVE DESTINATION'
  command -v python3 >/dev/null || fail 'Python 3 is required'
  safe_extract "$2" "$3"
  exit 0
fi
if [[ "$MODE" == --check-config ]]; then
  [[ $# -eq 1 ]] || fail 'usage: verify-release-candidate.sh --check-config'
  command -v python3 >/dev/null || fail 'Python 3 is required'
  release_config_contract
  printf 'PASS: release configuration data contract\n'
  exit 0
fi
command -v cmake >/dev/null || fail 'CMake is required'
if [[ "$MODE" == --verify || "$MODE" == --verify-final ]]; then
  # The installed core archive is a product package: it must stay fixture-free. The licensed
  # source archive is a different artifact and is proved by --verify-final, never by this check.
  if [[ "$MODE" == --verify ]]; then
    [[ $# -eq 10 ]] || fail "$USAGE"
  else
    [[ $# -eq 12 || $# -eq 13 ]] || fail "--verify-final requires the source archive and its receipt as distinct final evidence; $USAGE"
  fi
  command -v python3 >/dev/null || fail 'Python 3 is required'
  python3 -I "$SOURCE_ARCHIVE_CHECKER" --check-product-archive "$3" --repo-root "$ROOT_DIR" || fail 'product package fixture-leak check failed'
  if [[ "$MODE" == --verify-final ]]; then
    bash "$ROOT_DIR/tests/scripts/verify-release-candidate.sh" --verify \
      "$2" "$3" "$4" "$5" "$6" "$7" "$8" "$9" "${10}" \
      || fail 'candidate product qualification failed'
    SOURCE_REPOSITORY=${13:-$ROOT_DIR}
    exec python3 -I "$SOURCE_ARCHIVE_CHECKER" --check-receipt "${12}" --archive "${11}" \
      --tag "$5" --source-sha "$6" --repo "$SOURCE_REPOSITORY"
  fi
  cmake \
    "-DGBB_RECEIPT=$2" "-DGBB_ASSET=$3" "-DGBB_EXPECTED_VERSION=$4" \
    "-DGBB_EXPECTED_TAG=$5" "-DGBB_EXPECTED_SOURCE_SHA=$6" \
    "-DGBB_EXPECTED_RELEASE_ID=$7" "-DGBB_NOTICE_FILE=$8" \
    "-DGBB_SOURCE_RECEIPT=$9" "-DGBB_BUILD_RECEIPT=${10}" \
    -P "$ROOT_DIR/cmake/VerifyReleaseReceipt.cmake"
  TEMP_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/gabbaboy-release-consumer.XXXXXX")
  trap 'rm -rf "$TEMP_ROOT"' EXIT HUP INT TERM
  candidate_consumer_verify "${10}" "$3" "$6" "$TEMP_ROOT" || fail 'installed consumer qualification failed'
  exit 0
fi
[[ "$MODE" == --self-test && $# -eq 1 ]] || fail "$USAGE"
command -v tar >/dev/null || fail 'tar is required'
command -v python3 >/dev/null || fail 'Python 3 is required'

VERSION=$(sed -nE 's/^project\(GabbaBoy VERSION ([0-9]+\.[0-9]+\.[0-9]+).*/\1/p' "$ROOT_DIR/CMakeLists.txt" | head -n 1)
[[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || fail 'could not read a semver CMake project version'
SOURCE_SHA=$(git -C "$ROOT_DIR" rev-parse HEAD)
[[ "$SOURCE_SHA" =~ ^[0-9a-f]{40}$ ]] || fail 'source revision is not a full Git SHA'
if [[ -n "$(git -C "$ROOT_DIR" status --porcelain --untracked-files=no -- src include fixtures tests cmake ':!cmake/VerifyReleaseReceipt.cmake' ':!tests/scripts/verify-release-candidate.sh')" ]]; then
  fail 'implementation source is dirty; release candidate requires a committed source tree'
fi
release_config_contract

TEMP_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/gabbaboy-release-candidate.XXXXXX")
trap 'rm -rf "$TEMP_ROOT"' EXIT HUP INT TERM
BUILD_DIR="$TEMP_ROOT/build"
STAGE_DIR="$TEMP_ROOT/stage"
ARCHIVE="$TEMP_ROOT/gabbaboy-core-linux-x64.tar.gz"
EXTRACT_DIR="$TEMP_ROOT/downloaded"
cmake -S "$ROOT_DIR" -B "$BUILD_DIR" -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF -DGABBABOY_BUILD_PLAYER=OFF
cmake --build "$BUILD_DIR" --parallel 2
cmake --install "$BUILD_DIR" --prefix "$STAGE_DIR"
# The shipped product package has no wrapper directory: release.yml tars the installed prefix's
# top-level entries exactly this way.
(cd "$TEMP_ROOT" && tar -czf "$ARCHIVE" -C "$STAGE_DIR" include lib bin share)

safe_extract "$ARCHIVE" "$EXTRACT_DIR"
EXTRACTED_PREFIX="$EXTRACT_DIR"
[[ -f "$EXTRACTED_PREFIX/include/gabbaboy/gabbaboy.h" ]] || fail 'downloaded archive lacks public header'
[[ -f "$EXTRACTED_PREFIX/share/gabbaboy/fixtures/tracer/manifest.json" ]] || fail 'downloaded archive lacks tracer manifest'
[[ -f "$EXTRACTED_PREFIX/share/gabbaboy/fixtures/mbc1-continuation/manifest.json" ]] || fail 'downloaded archive lacks battery manifest'

for language in c cpp; do
  consumer_build="$TEMP_ROOT/consumer-$language"
  cmake -S "$ROOT_DIR/tests/consumers/$language" -B "$consumer_build" \
    -DCMAKE_PREFIX_PATH="$EXTRACTED_PREFIX" \
    -DGBB_TRACER_ROM="$EXTRACTED_PREFIX/share/gabbaboy/fixtures/tracer/tracer.gb"
  cmake --build "$consumer_build" --parallel 2
  case "$language" in
    c) "$consumer_build/consumer-c" "$EXTRACTED_PREFIX/share/gabbaboy/fixtures/tracer/tracer.gb" ;;
    cpp) "$consumer_build/consumer-cpp" "$EXTRACTED_PREFIX/share/gabbaboy/fixtures/tracer/tracer.gb" ;;
  esac
done

TRACER_MANIFEST_SHA=$(sha256_file "$ROOT_DIR/fixtures/tracer/manifest.json")
BATTERY_MANIFEST_SHA=$(sha256_file "$ROOT_DIR/fixtures/mbc1-continuation/manifest.json")
ASSET_SHA=$(sha256_file "$ARCHIVE")
NOTICE="$ROOT_DIR/LICENSE"
[[ -s "$NOTICE" ]] || fail 'project notice is missing'
NOTICE_SHA=$(sha256_file "$NOTICE")
NOTES='Self-test candidate only; not a product release.'
NOTES_SHA=$(printf '%s' "$NOTES" | python3 -c 'import hashlib,sys; print(hashlib.sha256(sys.stdin.buffer.read()).hexdigest())')
COMPILER=$(cc --version | head -n1)
CM_VERSION=$(cmake --version | head -n1)
SOURCE_RECEIPT="$TEMP_ROOT/source-receipt.json"
BUILD_RECEIPT="$TEMP_ROOT/build-receipt.json"
RECEIPT="$TEMP_ROOT/receipt.json"
write_receipts() {
python3 - "$1" "$2" "$3" "$VERSION" "$SOURCE_SHA" "$NOTICE_SHA" "$NOTES" "$TRACER_MANIFEST_SHA" "$BATTERY_MANIFEST_SHA" "$4" "$COMPILER" "$CM_VERSION" <<'PY'
import hashlib, json, pathlib, sys
source_path, build_path, download_path = map(pathlib.Path, sys.argv[1:4])
version, source_sha, notice_sha, notes, tracer_sha, battery_sha, asset_sha, compiler, cmake_version = sys.argv[4:]
release_id, tag = "self-test-release", "v" + version
proof = {"head_sha": source_sha, "merge_commit_sha": source_sha, "required_checks": "passed"}
source = {
    "schema_version": 1, "version": version, "tag_name": tag,
    "source_sha": source_sha, "release_id": release_id, "draft": True,
    "source_clean": True, "notice_sha256": notice_sha,
    "release_notes": notes, "release_notes_sha256": hashlib.sha256(notes.encode()).hexdigest(),
    "prior_pr_proof": proof,
}
source_path.write_text(json.dumps(source, indent=2) + "\n")
source_digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
build_data = {
    "compiler": compiler, "cmake": cmake_version, "runner": "local-self-test",
    "configuration": "Release", "fixture_manifest_sha256": tracer_sha,
    "corpus_manifest_sha256": battery_sha,
}
fixtures = {"tracer_manifest_sha256": tracer_sha, "battery_manifest_sha256": battery_sha}
build = {
    "schema_version": 1, "version": version, "tag_name": tag,
    "source_sha": source_sha, "release_id": release_id,
    "source_receipt_sha256": source_digest,
    "asset_name": "gabbaboy-core-linux-x64.tar.gz", "asset_sha256": asset_sha,
    "build": build_data, "fixtures": fixtures,
}
build_path.write_text(json.dumps(build, indent=2) + "\n")
download = {
    "schema_version": 1, "version": version, "tag_name": tag,
    "source_sha": source_sha, "release_id": release_id, "draft": True,
    "source_clean": True, "smoke_result": "passed", "notice_file": "gabbaboy-notices.txt",
    "notice_sha256": notice_sha, "release_notes": notes,
    "release_notes_sha256": source["release_notes_sha256"],
    "source_receipt_sha256": source_digest,
    "build_receipt_sha256": hashlib.sha256(build_path.read_bytes()).hexdigest(),
    "build": build_data, "fixtures": fixtures,
    "assets": [{"name": "gabbaboy-core-linux-x64.tar.gz", "sha256": asset_sha}],
    "prior_pr_proof": proof,
}
download_path.write_text(json.dumps(download, indent=2) + "\n")
PY
}
write_receipts "$SOURCE_RECEIPT" "$BUILD_RECEIPT" "$RECEIPT" "$ASSET_SHA"

verify() {
  receipt_file=$1
  asset_file=$2
  source_file=${3:-$SOURCE_RECEIPT}
  build_file=${4:-$BUILD_RECEIPT}
  cmake \
    -DGBB_RECEIPT="$receipt_file" \
    -DGBB_ASSET="$asset_file" \
    -DGBB_EXPECTED_VERSION="$VERSION" \
    -DGBB_EXPECTED_TAG="v$VERSION" \
    -DGBB_EXPECTED_SOURCE_SHA="$SOURCE_SHA" \
    -DGBB_EXPECTED_RELEASE_ID=self-test-release \
    -DGBB_NOTICE_FILE="$NOTICE" \
    -DGBB_SOURCE_RECEIPT="$source_file" \
    -DGBB_BUILD_RECEIPT="$build_file" \
    -P "$ROOT_DIR/cmake/VerifyReleaseReceipt.cmake"
}
verify "$RECEIPT" "$ARCHIVE"

expect_reject() {
  name=$1
  receipt=$2
  asset=$3
  source_file=${4:-$SOURCE_RECEIPT}
  build_file=${5:-$BUILD_RECEIPT}
  if verify "$receipt" "$asset" "$source_file" "$build_file" >"$TEMP_ROOT/$name.log" 2>&1; then
    cat "$TEMP_ROOT/$name.log" >&2
    fail "receipt verifier accepted negative case: $name"
  fi
  printf 'rejected: %s\n' "$name"
}
cp "$ARCHIVE" "$TEMP_ROOT/altered.tar.gz"
python3 - "$TEMP_ROOT/altered.tar.gz" <<'PY'
import pathlib, sys
path = pathlib.Path(sys.argv[1])
data = bytearray(path.read_bytes())
data[0] ^= 1
path.write_bytes(data)
PY
expect_reject altered-archive "$RECEIPT" "$TEMP_ROOT/altered.tar.gz"
python3 - "$RECEIPT" "$TEMP_ROOT" <<'PY'
import json, pathlib, sys
source, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
receipt = json.loads(source.read_text())
for name, mutate in {
    "published": lambda value: value.update(draft=False),
    "duplicate-asset": lambda value: value["assets"].append(value["assets"][0]),
    "stale-proof": lambda value: value["prior_pr_proof"].update(merge_commit_sha="0" * 40),
    "missing-notes": lambda value: value.update(release_notes=""),
    "missing-source": lambda value: value.pop("source_sha"),
    "wrong-tag": lambda value: value.update(tag_name="v9.9.9"),
    "tampered-notice-digest": lambda value: value.update(notice_sha256="0" * 64),
}.items():
    value = json.loads(json.dumps(receipt))
    mutate(value)
    (out / f"{name}.json").write_text(json.dumps(value))
PY
for negative in published duplicate-asset stale-proof missing-notes missing-source wrong-tag tampered-notice-digest; do
  expect_reject "$negative" "$TEMP_ROOT/$negative.json" "$ARCHIVE"
done
python3 - "$SOURCE_RECEIPT" "$BUILD_RECEIPT" "$TEMP_ROOT" <<'PY'
import json, pathlib, sys
source_path, build_path, out = map(pathlib.Path, sys.argv[1:])
source = json.loads(source_path.read_text())
source["source_sha"] = "0" * 40
(out / "changed-source-receipt.json").write_text(json.dumps(source))
build = json.loads(build_path.read_text())
build["source_receipt_sha256"] = "0" * 64
(out / "changed-build-receipt.json").write_text(json.dumps(build))
PY
expect_reject changed-source-receipt "$RECEIPT" "$ARCHIVE" "$TEMP_ROOT/changed-source-receipt.json" "$BUILD_RECEIPT"
expect_reject changed-build-receipt "$RECEIPT" "$ARCHIVE" "$SOURCE_RECEIPT" "$TEMP_ROOT/changed-build-receipt.json"
python3 - "$TEMP_ROOT/escape.tar.gz" <<'PY'
import pathlib, sys, tarfile
with tarfile.open(sys.argv[1], "w:gz") as bundle:
    info = tarfile.TarInfo("../escaped-release-file")
    info.size = 1
    bundle.addfile(info, __import__("io").BytesIO(b"x"))
PY
if safe_extract "$TEMP_ROOT/escape.tar.gz" "$TEMP_ROOT/extract-negative" >/dev/null 2>&1; then
  fail 'safe extraction accepted a parent traversal path'
fi
[[ ! -e "$TEMP_ROOT/escaped-release-file" ]] || fail 'archive traversal wrote outside extraction destination'
printf 'rejected: archive traversal extraction escape\n'

# --- Source archive and product package are different artifacts (D-11/D-19/D-21). ---
SELF="$ROOT_DIR/tests/scripts/verify-release-candidate.sh"
entry_accept() {
  name=$1; shift
  bash "$SELF" "$@" >"$TEMP_ROOT/$name.log" 2>&1 || { cat "$TEMP_ROOT/$name.log" >&2; fail "release entry point rejected positive case: $name"; }
  printf 'accepted: %s\n' "$name"
}
entry_reject() {
  name=$1; expected=$2; shift 2
  if bash "$SELF" "$@" >"$TEMP_ROOT/$name.log" 2>&1; then
    cat "$TEMP_ROOT/$name.log" >&2
    fail "release entry point accepted negative case: $name"
  fi
  grep -q -- "$expected" "$TEMP_ROOT/$name.log" || { cat "$TEMP_ROOT/$name.log" >&2; fail "negative case $name was rejected for the wrong reason (expected: $expected)"; }
  printf 'rejected: %s (%s)\n' "$name" "$expected"
}
entry_accept clean-product-package --verify "$RECEIPT" "$ARCHIVE" "$VERSION" "v$VERSION" "$SOURCE_SHA" self-test-release "$NOTICE" "$SOURCE_RECEIPT" "$BUILD_RECEIPT"

# Fixture leak through --verify: the receipt is bound to the leaked bytes, so only the product
# fixture check can reject it. The receipt verifier alone must accept it (proving the control bites).
make_leaky_archive() {
  leak_dir="$TEMP_ROOT/$1"
  mkdir "$leak_dir"
  cp -R "$STAGE_DIR" "$leak_dir/stage"
  mkdir -p "$(dirname "$leak_dir/stage/$2")"
  cp "$ROOT_DIR/fixtures/libbet/libbet.gb" "$leak_dir/stage/$2"
  (cd "$leak_dir" && tar -czf "$leak_dir.tar.gz" -C stage include lib bin share)
  write_receipts "$leak_dir.source.json" "$leak_dir.build.json" "$leak_dir.receipt.json" "$(sha256_file "$leak_dir.tar.gz")"
}
for leak in "leaked-fixture-dir:share/gabbaboy/fixtures/libbet/libbet.gb" "leaked-renamed-rom:share/gabbaboy/notes.txt"; do
  leak_name=${leak%%:*}; leak_member=${leak#*:}
  make_leaky_archive "$leak_name" "$leak_member"
  verify "$TEMP_ROOT/$leak_name.receipt.json" "$TEMP_ROOT/$leak_name.tar.gz" "$TEMP_ROOT/$leak_name.source.json" "$TEMP_ROOT/$leak_name.build.json" >/dev/null 2>&1 \
    || fail "receipt verifier alone rejected $leak_name, so the fixture-leak control would not prove the product check"
  entry_reject "$leak_name" 'REJECT product-fixture-leak' --verify "$TEMP_ROOT/$leak_name.receipt.json" "$TEMP_ROOT/$leak_name.tar.gz" "$VERSION" "v$VERSION" "$SOURCE_SHA" self-test-release "$NOTICE" "$TEMP_ROOT/$leak_name.source.json" "$TEMP_ROOT/$leak_name.build.json"
done

# Omitted behavioral consumer evidence must not reduce to an inventory check.
python3 - "$RECEIPT" "$TEMP_ROOT" <<'PY'
import json, pathlib, sys
source, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
receipt = json.loads(source.read_text())
skipped = json.loads(json.dumps(receipt)); skipped["smoke_result"] = "skipped"
omitted = json.loads(json.dumps(receipt)); omitted.pop("smoke_result")
(out / "smoke-skipped.json").write_text(json.dumps(skipped))
(out / "smoke-omitted.json").write_text(json.dumps(omitted))
PY
entry_reject consumer-smoke-skipped 'consumer smoke did not pass' --verify "$TEMP_ROOT/smoke-skipped.json" "$ARCHIVE" "$VERSION" "v$VERSION" "$SOURCE_SHA" self-test-release "$NOTICE" "$SOURCE_RECEIPT" "$BUILD_RECEIPT"
entry_reject consumer-smoke-omitted 'smoke_result' --verify "$TEMP_ROOT/smoke-omitted.json" "$ARCHIVE" "$VERSION" "v$VERSION" "$SOURCE_SHA" self-test-release "$NOTICE" "$SOURCE_RECEIPT" "$BUILD_RECEIPT"

# A generated source archive of a private tagged clone of the committed tree.
SOURCE_TAG="v$VERSION"
CLONE="$TEMP_ROOT/source-clone"
git clone -q --no-hardlinks "$ROOT_DIR" "$CLONE"
git -C "$CLONE" -c user.name=selftest -c user.email=selftest@example.invalid tag -f "$SOURCE_TAG" "$SOURCE_SHA" >/dev/null
SOURCE_ARCHIVE="$TEMP_ROOT/gabbaboy-source.tar.gz"
git -C "$CLONE" archive --format=tar "--prefix=gabbaboy-$VERSION/" "$SOURCE_TAG" | python3 -c 'import gzip, sys; sys.stdout.buffer.write(gzip.compress(sys.stdin.buffer.read(), mtime=0))' >"$SOURCE_ARCHIVE"
ARCHIVE_RECEIPT="$TEMP_ROOT/source-archive-receipt.json"
python3 -I "$SOURCE_ARCHIVE_CHECKER" --archive "$SOURCE_ARCHIVE" --tag "$SOURCE_TAG" --source-sha "$SOURCE_SHA" --repo "$CLONE" --output "$ARCHIVE_RECEIPT"
final_args=("$RECEIPT" "$ARCHIVE" "$VERSION" "$SOURCE_TAG" "$SOURCE_SHA" self-test-release "$NOTICE" "$SOURCE_RECEIPT" "$BUILD_RECEIPT")
final_repo_args=("$SOURCE_ARCHIVE" "$ARCHIVE_RECEIPT" "$CLONE")
entry_accept final-source-archive-and-product --verify-final "${final_args[@]}" "${final_repo_args[@]}"

# The final gate requires the source archive receipt as its own evidence item.
entry_reject final-without-source-archive-receipt 'distinct final evidence' --verify-final "${final_args[@]}"
entry_reject final-with-source-receipt-as-archive-receipt 'REJECT receipt-invalid' --verify-final "${final_args[@]}" "$SOURCE_ARCHIVE" "$SOURCE_RECEIPT" "$CLONE"
entry_reject final-with-build-receipt-as-archive-receipt 'REJECT receipt-invalid' --verify-final "${final_args[@]}" "$SOURCE_ARCHIVE" "$BUILD_RECEIPT" "$CLONE"
python3 - "$ARCHIVE_RECEIPT" "$TEMP_ROOT" <<'PY'
import json, pathlib, sys
source, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
base = json.loads(source.read_text())
for name, mutate in {
    "stale-source-tree-digest": lambda v: v.update(source_tree_sha256="0" * 64),
    "other-tag": lambda v: v.update(tag="v9.9.9"),
    "other-source": lambda v: v.update(source_sha="0" * 40),
    "no-fixtures": lambda v: v.update(admitted_fixture_identities=[]),
}.items():
    value = json.loads(json.dumps(base)); mutate(value)
    (out / f"archive-receipt-{name}.json").write_text(json.dumps(value))
PY
for negative in stale-source-tree-digest other-tag other-source no-fixtures; do
  entry_reject "final-archive-receipt-$negative" 'REJECT receipt-invalid' --verify-final "${final_args[@]}" "$SOURCE_ARCHIVE" "$TEMP_ROOT/archive-receipt-$negative.json" "$CLONE"
done

# Substitution in both directions.
entry_reject final-product-package-as-source-archive 'REJECT' --verify-final "${final_args[@]}" "$ARCHIVE" "$ARCHIVE_RECEIPT" "$CLONE"
python3 - "$ARCHIVE" "$TEMP_ROOT/product-as-source.tar.gz" "$VERSION" "$SOURCE_SHA" <<'PY'
import sys, tarfile
src, dst, version, sha = sys.argv[1:]
with tarfile.open(src) as bundle, tarfile.open(dst, "w:gz", format=tarfile.PAX_FORMAT, pax_headers={"comment": sha}) as out:
    root = tarfile.TarInfo(f"gabbaboy-{version}")
    root.type, root.mode = tarfile.DIRTYPE, 0o755
    out.addfile(root)
    for member in bundle:
        member.name = f"gabbaboy-{version}/" + member.name
        out.addfile(member, bundle.extractfile(member) if member.isreg() else None)
PY
if python3 -I "$SOURCE_ARCHIVE_CHECKER" --archive "$TEMP_ROOT/product-as-source.tar.gz" --tag "$SOURCE_TAG" --source-sha "$SOURCE_SHA" --output "$TEMP_ROOT/product-as-source.json" >"$TEMP_ROOT/product-as-source.log" 2>&1 \
   || ! grep -q 'REJECT missing-notice' "$TEMP_ROOT/product-as-source.log"; then
  cat "$TEMP_ROOT/product-as-source.log" >&2
  fail 'a fixture-free product package with a source-shaped root was accepted as a source archive'
fi
printf 'rejected: product package repacked as a source archive (REJECT missing-notice)\n'
write_receipts "$TEMP_ROOT/src-as-product.source.json" "$TEMP_ROOT/src-as-product.build.json" "$TEMP_ROOT/src-as-product.receipt.json" "$(sha256_file "$SOURCE_ARCHIVE")"
entry_reject source-archive-as-core-package 'REJECT product-' --verify "$TEMP_ROOT/src-as-product.receipt.json" "$SOURCE_ARCHIVE" "$VERSION" "v$VERSION" "$SOURCE_SHA" self-test-release "$NOTICE" "$TEMP_ROOT/src-as-product.source.json" "$TEMP_ROOT/src-as-product.build.json"
printf 'PASS: built archive, relocated external C/C++ consumers, receipt identity, digest tamper, draft/proof, fixture-leak, source-archive and substitution negatives\n'
