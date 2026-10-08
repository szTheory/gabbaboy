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
safe_extract() {
  python3 - "$1" "$2" <<'PY'
import pathlib, shutil, sys, tarfile
archive, destination = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
with tarfile.open(archive, "r:gz") as bundle:
    members = bundle.getmembers()
    if not members or len(members) > 1000:
        raise SystemExit("candidate archive is empty or has too many entries")
    seen, total_size = set(), 0
    for member in members:
        name = pathlib.PurePosixPath(member.name)
        parts = tuple(part for part in name.parts if part not in ("", "."))
        if name.is_absolute() or ".." in parts or not parts or parts[0].endswith(":"):
            raise SystemExit(f"unsafe archive path: {member.name}")
        if not (member.isdir() or member.isfile()):
            raise SystemExit(f"archive contains a link or special file: {member.name}")
        if member.name in seen:
            raise SystemExit(f"archive contains a duplicate path: {member.name}")
        seen.add(member.name)
        total_size += member.size
        if member.size < 0 or total_size > 64 * 1024 * 1024:
            raise SystemExit("candidate archive exceeds the uncompressed size limit")
    destination.mkdir()
    for member in members:
        parts = tuple(part for part in pathlib.PurePosixPath(member.name).parts if part not in ("", "."))
        target = destination.joinpath(*parts)
        if member.isdir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            with bundle.extractfile(member) as source, target.open("xb") as output:
                shutil.copyfileobj(source, output)
            target.chmod(member.mode & 0o777 & ~0o6000)
PY
}
if [[ "$MODE" == --extract ]]; then
  [[ $# -eq 3 ]] || fail 'usage: verify-release-candidate.sh --extract ARCHIVE DESTINATION'
  command -v python3 >/dev/null || fail 'Python 3 is required'
  safe_extract "$2" "$3"
  exit 0
fi
command -v cmake >/dev/null || fail 'CMake is required'
if [[ "$MODE" == --verify ]]; then
  [[ $# -eq 10 ]] || fail 'usage: verify-release-candidate.sh --verify RECEIPT ASSET VERSION TAG SOURCE_SHA RELEASE_ID NOTICE_FILE SOURCE_RECEIPT BUILD_RECEIPT'
  exec cmake \
    "-DGBB_RECEIPT=$2" "-DGBB_ASSET=$3" "-DGBB_EXPECTED_VERSION=$4" \
    "-DGBB_EXPECTED_TAG=$5" "-DGBB_EXPECTED_SOURCE_SHA=$6" \
    "-DGBB_EXPECTED_RELEASE_ID=$7" "-DGBB_NOTICE_FILE=$8" \
    "-DGBB_SOURCE_RECEIPT=$9" "-DGBB_BUILD_RECEIPT=${10}" \
    -P "$ROOT_DIR/cmake/VerifyReleaseReceipt.cmake"
fi
[[ "$MODE" == --self-test && $# -eq 1 ]] || fail 'usage: verify-release-candidate.sh --self-test | --verify RECEIPT ASSET VERSION TAG SOURCE_SHA RELEASE_ID NOTICE_FILE SOURCE_RECEIPT BUILD_RECEIPT'
command -v tar >/dev/null || fail 'tar is required'
command -v python3 >/dev/null || fail 'Python 3 is required'

VERSION=$(sed -nE 's/^project\(GabbaBoy VERSION ([0-9]+\.[0-9]+\.[0-9]+).*/\1/p' "$ROOT_DIR/CMakeLists.txt" | head -n 1)
[[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || fail 'could not read a semver CMake project version'
SOURCE_SHA=$(git -C "$ROOT_DIR" rev-parse HEAD)
[[ "$SOURCE_SHA" =~ ^[0-9a-f]{40}$ ]] || fail 'source revision is not a full Git SHA'
if [[ -n "$(git -C "$ROOT_DIR" status --porcelain --untracked-files=no -- src include fixtures tests cmake ':!cmake/VerifyReleaseReceipt.cmake' ':!tests/scripts/verify-release-candidate.sh')" ]]; then
  fail 'implementation source is dirty; release candidate requires a committed source tree'
fi
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
if not version or manifest.get(".") != version.group(1):
    raise SystemExit("release manifest and CMake PROJECT_VERSION do not match")
if package.get("draft") is not True or package.get("force-tag-creation") is not True or package.get("include-component-in-tag") is not False or package.get("include-v-in-tag") is not True:
    raise SystemExit("manifest release must use matching v<version> tag plus draft and immediate tag")
if not re.search(r"googleapis/release-please-action@[0-9a-f]{40}", workflow):
    raise SystemExit("release-please action is not pinned to a full commit SHA")
for required in ("outputs.release_created == 'true'", "api_commit", "draft", "commits/$SOURCE_SHA/pulls", "gh pr checks", "RETRY"):
    if required not in workflow:
        raise SystemExit(f"release route is missing fail-closed contract: {required}")
for required in (
    "runs-on: macos-14", "runs-on: windows-2022",
    "gabbaboy-core-macos-arm64.tar.gz", "gabbaboy-core-windows-x64.tar.gz",
    "gabbaboy-preview-macos-arm64.tar.gz", "candidate-platform-manifest.json",
    "--verify-package", "Visual Studio 17 2022", "--check",
    "REUSE_MACOS_CANDIDATE", "REUSE_WINDOWS_CANDIDATE",
    "refusing to rebuild or replace bytes",
):
    if required not in workflow:
        raise SystemExit(f"release route is missing downloaded platform qualification: {required}")
if "needs: [release, candidate-macos]" not in workflow:
    raise SystemExit("Windows downloaded-archive verification must run after the existing native Linux and macOS lanes")
for required in ("SDL_AUDIO_DRIVER=dummy", "SDL_VIDEO_DRIVER=dummy", "--smoke-package", "packaged MBC1 continuation fixture resumed in a fresh process"):
    if required not in player_verifier:
        raise SystemExit(f"downloaded player verification is missing scripted lifecycle evidence: {required}")
if "pull_request_target:" in workflow or "release: {" in workflow or "gh release edit" in workflow:
    raise SystemExit("candidate workflow contains a privileged PR route or an early publication path")
if "workflow_call:" not in workflow or "uses: ./.github/workflows/release.yml" not in entrypoint:
    raise SystemExit("release-please outputs and candidate jobs are not connected in one workflow run")
PY

TEMP_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/gabbaboy-release-candidate.XXXXXX")
trap 'rm -rf "$TEMP_ROOT"' EXIT HUP INT TERM
BUILD_DIR="$TEMP_ROOT/build"
STAGE_DIR="$TEMP_ROOT/stage"
ARCHIVE="$TEMP_ROOT/gabbaboy-core-linux-x64.tar.gz"
EXTRACT_DIR="$TEMP_ROOT/downloaded"
cmake -S "$ROOT_DIR" -B "$BUILD_DIR" -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF -DGABBABOY_BUILD_PLAYER=OFF
cmake --build "$BUILD_DIR" --parallel 2
cmake --install "$BUILD_DIR" --prefix "$STAGE_DIR"
(cd "$TEMP_ROOT" && tar -czf "$ARCHIVE" -C "$TEMP_ROOT" stage)

safe_extract "$ARCHIVE" "$EXTRACT_DIR"
EXTRACTED_PREFIX="$EXTRACT_DIR/stage"
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
python3 - "$SOURCE_RECEIPT" "$BUILD_RECEIPT" "$RECEIPT" "$VERSION" "$SOURCE_SHA" "$NOTICE_SHA" "$NOTES" "$TRACER_MANIFEST_SHA" "$BATTERY_MANIFEST_SHA" "$ASSET_SHA" "$COMPILER" "$CM_VERSION" <<'PY'
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
printf 'PASS: built archive, relocated external C/C++ consumers, receipt identity, digest tamper, and draft/proof negatives\n'
