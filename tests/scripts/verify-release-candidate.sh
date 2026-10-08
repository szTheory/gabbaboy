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
import pathlib, sys, tarfile
archive, destination = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
with tarfile.open(archive, "r:gz") as bundle:
    members = bundle.getmembers()
    if not members:
        raise SystemExit("candidate archive is empty")
    for member in members:
        name = pathlib.PurePosixPath(member.name)
        if name.is_absolute() or ".." in name.parts or not name.parts:
            raise SystemExit(f"unsafe archive path: {member.name}")
        if not (member.isdir() or member.isfile()):
            raise SystemExit(f"archive contains a link or special file: {member.name}")
    destination.mkdir()
    bundle.extractall(destination, members=members)
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
  [[ $# -eq 8 ]] || fail 'usage: verify-release-candidate.sh --verify RECEIPT ASSET VERSION TAG SOURCE_SHA RELEASE_ID NOTICE_FILE'
  exec cmake \
    "-DGBB_RECEIPT=$2" "-DGBB_ASSET=$3" "-DGBB_EXPECTED_VERSION=$4" \
    "-DGBB_EXPECTED_TAG=$5" "-DGBB_EXPECTED_SOURCE_SHA=$6" \
    "-DGBB_EXPECTED_RELEASE_ID=$7" "-DGBB_NOTICE_FILE=$8" \
    -P "$ROOT_DIR/cmake/VerifyReleaseReceipt.cmake"
fi
[[ "$MODE" == --self-test && $# -eq 1 ]] || fail 'usage: verify-release-candidate.sh --self-test | --verify RECEIPT ASSET VERSION TAG SOURCE_SHA RELEASE_ID NOTICE_FILE'
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
if not version or manifest.get(".") != version.group(1):
    raise SystemExit("release manifest and CMake PROJECT_VERSION do not match")
if package.get("draft") is not True or package.get("force-tag-creation") is not True or package.get("include-component-in-tag") is not False:
    raise SystemExit("manifest release must use matching v<version> tag plus draft and immediate tag")
if not re.search(r"googleapis/release-please-action@[0-9a-f]{40}", workflow):
    raise SystemExit("release-please action is not pinned to a full commit SHA")
for required in ("outputs.release_created == 'true'", "api_commit", "draft", "commits/$SOURCE_SHA/pulls", "gh pr checks", "RETRY"):
    if required not in workflow:
        raise SystemExit(f"release route is missing fail-closed contract: {required}")
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
RECEIPT="$TEMP_ROOT/receipt.json"
cat > "$RECEIPT" <<EOF
{
  "schema_version": 1,
  "version": "$VERSION",
  "tag_name": "v$VERSION",
  "source_sha": "$SOURCE_SHA",
  "release_id": "self-test-release",
  "draft": true,
  "source_clean": true,
  "smoke_result": "passed",
  "notice_file": "gabbaboy-notices.txt",
  "notice_sha256": "$NOTICE_SHA",
  "release_notes": "Self-test candidate only; not a product release.",
  "release_notes_sha256": "$(python3 -c 'import hashlib; print(hashlib.sha256("Self-test candidate only; not a product release.".encode()).hexdigest())')",
  "build": {
    "compiler": "$(cc --version | head -n1 | sed 's/"/\\"/g')",
    "cmake": "$(cmake --version | head -n1)",
    "runner": "local-self-test",
    "configuration": "Release",
    "fixture_manifest_sha256": "$TRACER_MANIFEST_SHA",
    "corpus_manifest_sha256": "$BATTERY_MANIFEST_SHA"
  },
  "fixtures": {
    "tracer_manifest_sha256": "$TRACER_MANIFEST_SHA",
    "battery_manifest_sha256": "$BATTERY_MANIFEST_SHA"
  },
  "assets": [{"name": "gabbaboy-core-linux-x64.tar.gz", "sha256": "$ASSET_SHA"}],
  "prior_pr_proof": {"head_sha": "$SOURCE_SHA", "merge_commit_sha": "$SOURCE_SHA", "required_checks": "passed"}
}
EOF

verify() {
  cmake \
    -DGBB_RECEIPT="$1" \
    -DGBB_ASSET="$2" \
    -DGBB_EXPECTED_VERSION="$VERSION" \
    -DGBB_EXPECTED_TAG="v$VERSION" \
    -DGBB_EXPECTED_SOURCE_SHA="$SOURCE_SHA" \
    -DGBB_EXPECTED_RELEASE_ID=self-test-release \
    -DGBB_NOTICE_FILE="$NOTICE" \
    -P "$ROOT_DIR/cmake/VerifyReleaseReceipt.cmake"
}
verify "$RECEIPT" "$ARCHIVE"

expect_reject() {
  name=$1
  receipt=$2
  asset=$3
  if verify "$receipt" "$asset" >"$TEMP_ROOT/$name.log" 2>&1; then
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
