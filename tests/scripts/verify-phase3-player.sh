#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
SDL_VERSION="3.4.18"
SDL_SHA256="9c75cf16330322c217dedd2e0609f1124f1b54b8633e763467b4684d0f4334a3"
SDL_URL="https://github.com/libsdl-org/SDL/releases/download/release-${SDL_VERSION}/SDL3-${SDL_VERSION}.tar.gz"
BUILD_ROOT="${ROOT_DIR}/build/phase3-player"
SDL_ARCHIVE="${BUILD_ROOT}/SDL3-${SDL_VERSION}.tar.gz"
SDL_SOURCE="${BUILD_ROOT}/SDL3-${SDL_VERSION}"
SDL_BUILD="${BUILD_ROOT}/SDL3-build"
SDL_PREFIX="${BUILD_ROOT}/prefix"
APP_BUILD="${BUILD_ROOT}/gabbaboy"
ARTIFACT_DIR="${BUILD_ROOT}/preview-candidate"
FINAL_ARTIFACT_DIR="${GBB_VERIFIED_OUTPUT_DIR:-${BUILD_ROOT}/preview-verified-artifact}"
EXTRACT_DIR="${BUILD_ROOT}/downloaded-package"
EXPECTED_SOURCE_REVISION="${GBB_EXPECTED_SOURCE_REVISION:-}"

fail() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

sha256_file() {
  shasum -a 256 "$1" | awk '{print $1}'
}

verify_checkout() {
  SOURCE_REVISION=$(git -C "$ROOT_DIR" rev-parse HEAD)
  if [[ -n "$EXPECTED_SOURCE_REVISION" ]]; then
    [[ "$EXPECTED_SOURCE_REVISION" =~ ^[0-9a-f]{40}$ ]] ||
      fail 'GBB_EXPECTED_SOURCE_REVISION must be a full lowercase Git SHA'
    [[ "$SOURCE_REVISION" == "$EXPECTED_SOURCE_REVISION" ]] ||
      fail "checkout SHA $SOURCE_REVISION does not match expected $EXPECTED_SOURCE_REVISION"
    if [[ -n "$(git -C "$ROOT_DIR" status --porcelain --untracked-files=all -- \
        CMakeLists.txt LICENSE include src tests cmake fixtures docs/preview.md \
        .github/scripts/safe_extract_package.py \
        .github/workflows/ci.yml .github/workflows/preview.yml \
        tests/scripts/verify-phase3-player.sh)" ]]; then
      fail 'source tree or index has changes relative to the expected revision'
    fi
    SOURCE_TREE_STATE=clean
  elif [[ -z "$(git -C "$ROOT_DIR" status --porcelain --untracked-files=all -- \
      CMakeLists.txt LICENSE include src tests cmake fixtures docs/preview.md \
      .github/scripts/safe_extract_package.py \
      .github/workflows/ci.yml .github/workflows/preview.yml \
      tests/scripts/verify-phase3-player.sh)" ]]; then
    SOURCE_TREE_STATE=clean
  else
    SOURCE_TREE_STATE=dirty
  fi
}

verify_package() {
  local candidate_dir=$1 write_final_receipt=$2
  local archive="$candidate_dir/gabbaboy-preview-macos-arm64.tar.gz"
  local build_receipt="$candidate_dir/build-receipt.json"
  [[ -s "$archive" ]] || fail 'candidate package archive is missing or empty'
  [[ -s "$build_receipt" ]] || fail 'candidate build receipt is missing or empty'

  local expected_sha
  expected_sha=${EXPECTED_SOURCE_REVISION:-$SOURCE_REVISION}
  local require_clean_source=false
  if [[ -n "$EXPECTED_SOURCE_REVISION" ]]; then
    require_clean_source=true
  fi
  python3 - "$archive" "$build_receipt" "$expected_sha" \
    "$require_clean_source" <<'PY'
import hashlib
import json
import pathlib
import sys

archive_path, receipt_path = map(pathlib.Path, sys.argv[1:3])
expected_sha = sys.argv[3]
require_clean_source = sys.argv[4] == 'true'
try:
    receipt = json.loads(receipt_path.read_text())
except (OSError, json.JSONDecodeError) as error:
    raise SystemExit(f'candidate build receipt is unreadable: {error}')
digest = hashlib.sha256()
with archive_path.open('rb') as stream:
    for chunk in iter(lambda: stream.read(1024 * 1024), b''):
        digest.update(chunk)
if receipt.get('schema_version') != 1 or receipt.get('result') != 'passed':
    raise SystemExit('candidate build receipt has an unsupported schema or non-passing result')
if receipt.get('source_revision') != expected_sha:
    raise SystemExit('candidate package source revision differs from the exact checkout')
if require_clean_source and receipt.get('source_tree_state') != 'clean':
    raise SystemExit('candidate package was not built from a clean exact-revision source tree')
if receipt.get('package_sha256') != digest.hexdigest():
    raise SystemExit('candidate package archive digest differs from its build receipt')
PY
  rm -rf -- "$EXTRACT_DIR"
  mkdir -p "$EXTRACT_DIR"
  python3 "$ROOT_DIR/.github/scripts/safe_extract_package.py" "$archive" "$EXTRACT_DIR"
  local prefix="$EXTRACT_DIR/installed-prefix"
  local player_bin="$prefix/bin/gabbaboy-player"
  local demo_rom="$prefix/share/gabbaboy/fixtures/visible-demo/demo.gb"
  local fixture_manifest="$prefix/share/gabbaboy/fixtures/visible-demo/manifest.json"
  local demo_license="$prefix/share/licenses/GabbaBoy/visible-demo-LICENSE.txt"
  local project_license="$prefix/share/licenses/GabbaBoy/LICENSE.txt"
  local sdl_license="$prefix/share/licenses/SDL3/LICENSE.txt"
  local package_metadata="$prefix/share/gabbaboy/preview-metadata.json"
  [[ -x "$player_bin" ]] || fail 'extracted package has no executable player'
  [[ -s "$prefix/lib/libSDL3.0.dylib" ]] || fail 'extracted package has no SDL3 runtime library'
  [[ -s "$demo_rom" && -s "$fixture_manifest" ]] || fail 'extracted package is missing the demo fixture'
  [[ -s "$demo_license" && -s "$project_license" && -s "$sdl_license" ]] ||
    fail 'extracted package is missing a license notice'
  [[ -s "$package_metadata" ]] || fail 'extracted package is missing source and SDL metadata'
  otool -L "$player_bin" | grep -Fq '@rpath/libSDL3.0.dylib' ||
    fail 'packaged executable does not reference its bundled SDL3 library'
  otool -l "$player_bin" | grep -Fq '@executable_path/../lib' ||
    fail 'packaged executable does not resolve SDL3 through its relative package path'
  if otool -l "$player_bin" | grep -Fq "$SDL_PREFIX"; then
    fail 'packaged executable retains the build-host SDL path'
  fi

  python3 - "$ROOT_DIR" "$archive" "$build_receipt" "$fixture_manifest" \
    "$demo_rom" "$demo_license" "$project_license" "$sdl_license" "$package_metadata" \
    "$expected_sha" "$require_clean_source" <<'PY'
import hashlib
import json
import pathlib
import sys

root, archive, receipt_path, fixture_manifest_path, rom_path, demo_license_path, project_license_path, sdl_license_path, metadata_path = map(pathlib.Path, sys.argv[1:10])
expected_sha = sys.argv[10]
require_clean_source = sys.argv[11] == 'true'
receipt = json.loads(receipt_path.read_text())
metadata = json.loads(metadata_path.read_text())
fixture_manifest = json.loads(fixture_manifest_path.read_text())
repository_manifest = json.loads((root / 'fixtures/visible-demo/manifest.json').read_text())
digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()

if receipt.get('schema_version') != 1 or receipt.get('result') != 'passed':
    raise SystemExit('candidate build receipt has an unsupported schema or non-passing result')
if receipt.get('source_revision') != str(expected_sha):
    raise SystemExit('candidate package source revision differs from the exact checkout')
if receipt.get('source_tree_state') != metadata.get('source_tree_state'):
    raise SystemExit('build receipt and package metadata disagree about source-tree cleanliness')
if require_clean_source and receipt.get('source_tree_state') != 'clean':
    raise SystemExit('candidate package was not built from a clean exact-revision source tree')
if metadata.get('source_revision') != str(expected_sha):
    raise SystemExit('package metadata source revision differs from the exact checkout')
if metadata.get('sdl_version') != '3.4.18' or receipt.get('sdl_version') != '3.4.18':
    raise SystemExit('candidate package does not identify the pinned SDL3 version')
if metadata.get('sdl_archive_sha256') != '9c75cf16330322c217dedd2e0609f1124f1b54b8633e763467b4684d0f4334a3':
    raise SystemExit('package metadata SDL source archive digest differs from the pin')
if receipt.get('sdl_archive_sha256') != metadata.get('sdl_archive_sha256'):
    raise SystemExit('candidate receipt and package SDL archive identities differ')
if digest(sdl_license_path) != metadata.get('sdl_license_sha256') or receipt.get('sdl_license_sha256') != metadata.get('sdl_license_sha256'):
    raise SystemExit('bundled SDL license digest does not match package metadata')
if not demo_license_path.is_file() or metadata.get('demo_license') != 'MIT':
    raise SystemExit('package is missing the original fixture MIT notice')
if digest(demo_license_path) != digest(root / 'fixtures/visible-demo/LICENSE.txt'):
    raise SystemExit('bundled demo license differs from the checked-in fixture notice')
if digest(project_license_path) != digest(root / 'LICENSE'):
    raise SystemExit('bundled project license differs from the checked-in license')
if digest(rom_path) != repository_manifest.get('sha256') or digest(rom_path) != fixture_manifest.get('sha256'):
    raise SystemExit('extracted demo ROM does not match its exact manifest digest')
if len(rom_path.read_bytes()) != 32768 or metadata.get('demo_rom_sha256') != digest(rom_path):
    raise SystemExit('extracted demo ROM size or package metadata digest is incorrect')
if metadata.get('demo_source_sha256') != repository_manifest.get('source_sha256'):
    raise SystemExit('package metadata assembly source digest differs from the repository manifest')
if metadata.get('signed') is not False or metadata.get('notarized') is not False:
    raise SystemExit('preview package metadata must not claim signing or notarization')
if metadata.get('hardware_qualified') is not False:
    raise SystemExit('preview package metadata must not claim hardware qualification')
if receipt.get('github_run_id') != metadata.get('github_run_id') or receipt.get('github_run_attempt') != metadata.get('github_run_attempt'):
    raise SystemExit('candidate receipt and package metadata run identities differ')
print(f"candidate_package_sha256={digest(archive)}")
print(f"sdl_license_sha256={digest(sdl_license_path)}")
print(f"source_revision={expected_sha}")
PY

  local smoke_output="$BUILD_ROOT/downloaded-package-smoke.txt"
  "$player_bin" --smoke-package "$demo_license" >"$smoke_output" 2>&1 || {
    cat "$smoke_output" >&2
    fail 'downloaded package guest event/frame smoke failed'
  }
  grep -Fq 'player smoke passed:' "$smoke_output" || {
    cat "$smoke_output" >&2
    fail 'downloaded package smoke did not report its guest frame result'
  }
  cat "$smoke_output"

  if [[ "$write_final_receipt" == true ]]; then
    local build_run_id build_run_attempt consumer_run_id consumer_run_attempt
    local package_sdl_version package_sdl_archive_sha package_sdl_license_sha package_demo_rom_sha source_tree_state
    local -a package_claims=()
    while IFS= read -r claim; do
      package_claims+=("$claim")
    done < <(python3 - "$build_receipt" <<'PY'
import json, pathlib, sys
receipt = json.loads(pathlib.Path(sys.argv[1]).read_text())
for key in ('github_run_id', 'github_run_attempt', 'sdl_version',
            'sdl_archive_sha256', 'sdl_license_sha256', 'demo_rom_sha256',
            'source_tree_state'):
    print(receipt[key])
PY
)
    build_run_id=${package_claims[0]}
    build_run_attempt=${package_claims[1]}
    package_sdl_version=${package_claims[2]}
    package_sdl_archive_sha=${package_claims[3]}
    package_sdl_license_sha=${package_claims[4]}
    package_demo_rom_sha=${package_claims[5]}
    source_tree_state=${package_claims[6]}
    consumer_run_id=${GITHUB_RUN_ID:-local}
    consumer_run_attempt=${GITHUB_RUN_ATTEMPT:-local}
    if [[ -n "${GBB_EXPECTED_BUILD_RUN_ID:-}" &&
          "$build_run_id" != "$GBB_EXPECTED_BUILD_RUN_ID" ]]; then
      fail 'candidate package build run ID differs from the successful CI run selected by preview workflow'
    fi
    if [[ -n "${GBB_EXPECTED_BUILD_RUN_ATTEMPT:-}" &&
          "$build_run_attempt" != "$GBB_EXPECTED_BUILD_RUN_ATTEMPT" ]]; then
      fail 'candidate package build attempt differs from the selected CI run attempt'
    fi
    rm -rf -- "$FINAL_ARTIFACT_DIR"
    mkdir -p "$FINAL_ARTIFACT_DIR"
    cp "$archive" "$FINAL_ARTIFACT_DIR/gabbaboy-preview-macos-arm64.tar.gz"
    python3 - "$FINAL_ARTIFACT_DIR/verified-receipt.json" "$archive" \
      "$expected_sha" "$build_run_id" "$build_run_attempt" \
      "$consumer_run_id" "$consumer_run_attempt" \
      "$package_sdl_version" "$package_sdl_archive_sha" \
      "$package_sdl_license_sha" "$package_demo_rom_sha" \
      "$source_tree_state" <<'PY'
import hashlib
import json
import os
import pathlib
import sys
import tempfile

target, archive, source_sha, build_run_id, build_attempt, consumer_run_id, consumer_attempt, sdl_version, sdl_archive_sha, sdl_license_sha, demo_rom_sha, source_tree_state = sys.argv[1:]
archive_path = pathlib.Path(archive)
receipt = {
    'schema_version': 1,
    'result': 'passed',
    'source_revision': source_sha,
    'build_run_id': build_run_id,
    'build_run_attempt': build_attempt,
    'consumer_run_id': consumer_run_id,
    'consumer_run_attempt': consumer_attempt,
    'build_source_tree_state': source_tree_state,
    'package': 'gabbaboy-preview-macos-arm64.tar.gz',
    'package_sha256': hashlib.sha256(archive_path.read_bytes()).hexdigest(),
    'sdl_version': sdl_version,
    'sdl_archive_sha256': sdl_archive_sha,
    'sdl_license_sha256': sdl_license_sha,
    'demo_rom_sha256': demo_rom_sha,
    'smoke': 'SDL keyboard events reached the demo guest and extracted package produced a completed frame',
    'signed': False,
    'notarized': False,
    'hardware_qualified': False,
}
destination = pathlib.Path(target)
with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=destination.parent,
                                 prefix=f'.{destination.name}.', delete=False) as stream:
    temporary = pathlib.Path(stream.name)
    json.dump(receipt, stream, indent=2, sort_keys=True)
    stream.write('\n')
temporary.replace(destination)
PY
    printf 'Downloaded package smoke passed for source %s; final artifact is ready.\n' "$expected_sha"
  fi
}

mode=${1:---build-package}
case "$mode" in
  --build-package)
    [[ $# -eq 1 ]] || fail 'usage: verify-phase3-player.sh [--build-package] | --verify-package ARTIFACT-DIR'
    ;;
  --verify-package)
    [[ $# -eq 2 ]] || fail 'usage: verify-phase3-player.sh [--build-package] | --verify-package ARTIFACT-DIR'
    ;;
  *) fail 'usage: verify-phase3-player.sh [--build-package] | --verify-package ARTIFACT-DIR' ;;
esac

for tool in python3 shasum otool; do
  command -v "$tool" >/dev/null 2>&1 || fail "required macOS verification tool is missing: $tool"
done
[[ "$(uname -s)" == Darwin && "$(uname -m)" == arm64 ]] ||
  fail 'the optional SDL3 player package and consumer smoke require macOS arm64'
verify_checkout

if [[ "$mode" == --verify-package ]]; then
  verify_package "$2" true
  exit 0
fi

for tool in cmake ninja curl tar install_name_tool; do
  command -v "$tool" >/dev/null 2>&1 || fail "required player build tool is missing: $tool"
done
[[ -s "$ROOT_DIR/tests/player/expected-tests.txt" ]] || fail 'optional player test inventory is empty'
PLAYER_TEST_COUNT=$(awk 'NF && $1 !~ /^#/ { count++ } END { print count + 0 }' \
  "$ROOT_DIR/tests/player/expected-tests.txt")
[[ "$PLAYER_TEST_COUNT" -gt 0 ]] || fail 'optional player test selection is empty'

mkdir -p "$BUILD_ROOT"
if [[ ! -f "$SDL_ARCHIVE" ]] ||
   ! printf '%s  %s\n' "$SDL_SHA256" "$SDL_ARCHIVE" | shasum -a 256 --check --status; then
  rm -f "$SDL_ARCHIVE" "$SDL_ARCHIVE.partial"
  curl --fail --location --retry 3 --silent --show-error \
    --output "$SDL_ARCHIVE.partial" "$SDL_URL"
  printf '%s  %s\n' "$SDL_SHA256" "$SDL_ARCHIVE.partial" | shasum -a 256 --check
  mv "$SDL_ARCHIVE.partial" "$SDL_ARCHIVE"
fi
printf '%s  %s\n' "$SDL_SHA256" "$SDL_ARCHIVE" | shasum -a 256 --check

rm -rf -- "$SDL_SOURCE"
mkdir -p "$SDL_SOURCE"
tar -xzf "$SDL_ARCHIVE" --strip-components=1 -C "$SDL_SOURCE"
rm -rf -- "$SDL_PREFIX"
cmake --log-level=WARNING -S "$SDL_SOURCE" -B "$SDL_BUILD" -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX="$SDL_PREFIX" \
  -DSDL_SHARED=ON \
  -DSDL_STATIC=OFF \
  -DSDL_TEST_LIBRARY=OFF \
  -DSDL_TESTS=OFF \
  -DSDL_INSTALL_TESTS=OFF \
  -DSDL_INSTALL_DOCS=OFF
cmake --build "$SDL_BUILD" --parallel
cmake --install "$SDL_BUILD" >/dev/null
[[ -s "$SDL_SOURCE/LICENSE.txt" ]] || fail 'official SDL source archive has no LICENSE.txt'

cmake --log-level=WARNING -S "$ROOT_DIR" -B "$APP_BUILD" -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_PREFIX_PATH="$SDL_PREFIX" \
  -DGABBABOY_BUILD_PLAYER=ON \
  -DBUILD_TESTING=ON
cmake --build "$APP_BUILD" --parallel
ctest --test-dir "$APP_BUILD" --output-on-failure --no-tests=error -R '^player_'

SDL_LICENSE_SHA256=$(sha256_file "$SDL_SOURCE/LICENSE.txt")
PLAYER_BIN="$APP_BUILD/gabbaboy-player"
[[ -x "$PLAYER_BIN" ]] || fail 'player build did not produce gabbaboy-player'
[[ -s "$SDL_PREFIX/lib/libSDL3.0.dylib" ]] || fail 'pinned SDL build did not install libSDL3.0.dylib'

STAGE_ROOT="$BUILD_ROOT/package-stage"
PACKAGE_PREFIX="$STAGE_ROOT/installed-prefix"
PACKAGE_BIN="$PACKAGE_PREFIX/bin/gabbaboy-player"
PACKAGE_LIB="$PACKAGE_PREFIX/lib/libSDL3.0.dylib"
PACKAGE_SHARE="$PACKAGE_PREFIX/share/gabbaboy"
rm -rf -- "$STAGE_ROOT" "$ARTIFACT_DIR" "$EXTRACT_DIR"
mkdir -p "$PACKAGE_PREFIX/bin" "$PACKAGE_PREFIX/lib" \
  "$PACKAGE_SHARE/fixtures/visible-demo" \
  "$PACKAGE_PREFIX/share/licenses/GabbaBoy" \
  "$PACKAGE_PREFIX/share/licenses/SDL3" \
  "$PACKAGE_PREFIX/share/doc/GabbaBoy" "$ARTIFACT_DIR"
cp "$PLAYER_BIN" "$PACKAGE_BIN"
cp -L "$SDL_PREFIX/lib/libSDL3.0.dylib" "$PACKAGE_LIB"
cp "$ROOT_DIR/fixtures/visible-demo/demo.gb" \
  "$PACKAGE_SHARE/fixtures/visible-demo/demo.gb"
cp "$ROOT_DIR/fixtures/visible-demo/manifest.json" \
  "$PACKAGE_SHARE/fixtures/visible-demo/manifest.json"
cp "$ROOT_DIR/fixtures/visible-demo/LICENSE.txt" \
  "$PACKAGE_PREFIX/share/licenses/GabbaBoy/visible-demo-LICENSE.txt"
cp "$ROOT_DIR/LICENSE" "$PACKAGE_PREFIX/share/licenses/GabbaBoy/LICENSE.txt"
cp "$SDL_SOURCE/LICENSE.txt" "$PACKAGE_PREFIX/share/licenses/SDL3/LICENSE.txt"
cp "$ROOT_DIR/docs/preview.md" "$PACKAGE_PREFIX/share/doc/GabbaBoy/preview.md"
chmod 755 "$PACKAGE_BIN"

existing_rpaths=$(otool -l "$PACKAGE_BIN" | awk '
  /cmd LC_RPATH/ { getline; getline; if ($1 == "path") { $1 = ""; sub(/^ /, ""); sub(/ \(offset.*/, ""); print } }
')
while IFS= read -r old_rpath; do
  [[ -z "$old_rpath" ]] || install_name_tool -delete_rpath "$old_rpath" "$PACKAGE_BIN"
done <<< "$existing_rpaths"
install_name_tool -add_rpath '@executable_path/../lib' "$PACKAGE_BIN"

SOURCE_REVISION=${SOURCE_REVISION:-$(git -C "$ROOT_DIR" rev-parse HEAD)}
python3 - "$ROOT_DIR" "$PACKAGE_SHARE" "$PACKAGE_PREFIX" \
  "$SOURCE_REVISION" "$SOURCE_TREE_STATE" "$SDL_VERSION" "$SDL_SHA256" \
  "$SDL_LICENSE_SHA256" "${GITHUB_RUN_ID:-local}" \
  "${GITHUB_RUN_ATTEMPT:-local}" "$PLAYER_TEST_COUNT" <<'PY'
import hashlib
import json
import pathlib
import sys

root, share, prefix = map(pathlib.Path, sys.argv[1:4])
source_revision, source_state, sdl_version, sdl_archive_sha, sdl_license_sha = sys.argv[4:9]
run_id, attempt, test_count = sys.argv[9:12]
manifest = json.loads((root / 'fixtures/visible-demo/manifest.json').read_text())
rom = share / 'fixtures/visible-demo/demo.gb'
license_file = prefix / 'share/licenses/SDL3/LICENSE.txt'
digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
if digest(rom) != manifest.get('sha256') or len(rom.read_bytes()) != 32768:
    raise SystemExit('staged package demo ROM differs from the checked-in manifest')
if digest(root / 'fixtures/visible-demo/demo.asm') != manifest.get('source_sha256'):
    raise SystemExit('demo assembly source differs from its manifest digest')
if digest(license_file) != sdl_license_sha:
    raise SystemExit('staged SDL license differs from the recorded license digest')
metadata = {
    'schema_version': 1,
    'source_revision': source_revision,
    'source_tree_state': source_state,
    'platform': 'macos-arm64',
    'sdl_version': sdl_version,
    'sdl_archive_sha256': sdl_archive_sha,
    'sdl_license_sha256': sdl_license_sha,
    'demo_profile': 'bootless DMG-CPU-B',
    'demo_source_sha256': manifest['source_sha256'],
    'demo_rom_sha256': manifest['sha256'],
    'demo_rom_size_bytes': manifest['size_bytes'],
    'demo_license': 'MIT',
    'audio_implemented': False,
    'battery_persistence_implemented': False,
    'signed': False,
    'notarized': False,
    'hardware_qualified': False,
    'github_run_id': run_id,
    'github_run_attempt': attempt,
}
metadata_path = share / 'preview-metadata.json'
metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + '\n')
PY

PACKAGE_ARCHIVE="$ARTIFACT_DIR/gabbaboy-preview-macos-arm64.tar.gz"
tar -czf "$PACKAGE_ARCHIVE" -C "$STAGE_ROOT" installed-prefix
PACKAGE_SHA256=$(sha256_file "$PACKAGE_ARCHIVE")
python3 - "$ROOT_DIR" "$ARTIFACT_DIR/build-receipt.json" \
  "$PACKAGE_ARCHIVE" "$PACKAGE_SHA256" "$SOURCE_REVISION" \
  "$SOURCE_TREE_STATE" "$SDL_VERSION" "$SDL_SHA256" \
  "$SDL_LICENSE_SHA256" "${GITHUB_RUN_ID:-local}" \
  "${GITHUB_RUN_ATTEMPT:-local}" "$PLAYER_TEST_COUNT" <<'PY'
import hashlib
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
receipt_path = pathlib.Path(sys.argv[2])
archive = pathlib.Path(sys.argv[3])
package_sha, source_revision, source_state, sdl_version, sdl_archive_sha, sdl_license_sha = sys.argv[4:10]
run_id, attempt, test_count = sys.argv[10:13]
manifest = json.loads((root / 'fixtures/visible-demo/manifest.json').read_text())
if hashlib.sha256(archive.read_bytes()).hexdigest() != package_sha:
    raise SystemExit('package digest changed while writing build receipt')
receipt = {
    'schema_version': 1,
    'result': 'passed',
    'source_revision': source_revision,
    'source_tree_state': source_state,
    'github_run_id': run_id,
    'github_run_attempt': attempt,
    'package': archive.name,
    'package_sha256': package_sha,
    'sdl_version': sdl_version,
    'sdl_archive_sha256': sdl_archive_sha,
    'sdl_license_sha256': sdl_license_sha,
    'demo_source_sha256': manifest['source_sha256'],
    'demo_rom_sha256': manifest['sha256'],
    'player_test_count': int(test_count),
    'build_smoke': 'passed',
}
receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
PY

verify_package "$ARTIFACT_DIR" false
printf 'Player package built and extracted-byte smoke passed for SDL %s; package SHA-256 %s\n' \
  "$SDL_VERSION" "$PACKAGE_SHA256"
