#!/usr/bin/env bash
set -euo pipefail

readonly version=3.25.3
readonly archive_name="cmake-${version}-linux-x86_64.tar.gz"
readonly archive_sha256=d4d2ba83301b215857d3b6590cd4434a414fa151c5807693abe587bd6c03581e
readonly checksum_url="https://cmake.org/files/v3.25/cmake-${version}-SHA-256.txt"
readonly archive_url="https://cmake.org/files/v3.25/${archive_name}"

if [[ "$(uname -s)" != Linux || "$(uname -m)" != x86_64 ]]; then
  echo "The CMake floor verifier requires Linux x86_64 (received $(uname -s) $(uname -m))." >&2
  exit 2
fi

repo_root=$(cd "$(dirname "$0")/../.." && pwd)
temp_root=$(mktemp -d "${TMPDIR:-/tmp}/gabbaboy-cmake-floor.XXXXXX")
trap 'rm -rf "$temp_root"' EXIT
archive="$temp_root/$archive_name"
checksum_file="$temp_root/cmake-SHA-256.txt"

curl --fail --location --silent --show-error "$checksum_url" -o "$checksum_file"
grep -Eq "^${archive_sha256}[[:space:]]+\*?${archive_name}$" "$checksum_file" || {
  echo "The official CMake checksum file does not publish the pinned digest for $archive_name" >&2
  exit 1
}
curl --fail --location --silent --show-error "$archive_url" -o "$archive"
printf '%s  %s\n' "$archive_sha256" "$archive" | sha256sum --check --status || {
  echo "CMake $version archive SHA-256 mismatch" >&2
  exit 1
}

tar -xzf "$archive" -C "$temp_root"
cmake_bin="$temp_root/cmake-${version}-linux-x86_64/bin/cmake"
ctest_bin="$temp_root/cmake-${version}-linux-x86_64/bin/ctest"
[[ -x "$cmake_bin" && -x "$ctest_bin" ]] || {
  echo "Verified CMake archive is missing cmake or ctest" >&2
  exit 1
}
"$cmake_bin" --version | head -n 1 | grep -F "cmake version $version"

stage="$temp_root/package-prefix"
relocated="$repo_root/build-cmake-3.25.3/package-prefix-relocated"
"$cmake_bin" --preset cmake-3.25.3 -S "$repo_root" \
  -B "$repo_root/build-cmake-3.25.3" -DCMAKE_INSTALL_PREFIX="$stage"
"$cmake_bin" --build "$repo_root/build-cmake-3.25.3" --verbose
"$ctest_bin" --test-dir "$repo_root/build-cmake-3.25.3" \
  --output-on-failure --no-tests=error --output-junit "$temp_root/floor-tests.xml"
bash "$repo_root/.github/scripts/verify-test-inventory.sh" \
  "$temp_root/floor-tests.xml" "$repo_root/tests/expected-tests.txt"
"$cmake_bin" --install "$repo_root/build-cmake-3.25.3" --prefix "$stage"

rm -rf "$relocated"
mv "$stage" "$relocated"
"$cmake_bin" --preset cmake-3.25.3-relocated -S "$repo_root"
"$cmake_bin" --build "$repo_root/build-cmake-3.25.3-relocated" --verbose
"$ctest_bin" --test-dir "$repo_root/build-cmake-3.25.3-relocated" \
  --output-on-failure --no-tests=error --output-junit "$temp_root/relocated-tests.xml"
bash "$repo_root/.github/scripts/verify-test-inventory.sh" \
  "$temp_root/relocated-tests.xml" "$repo_root/tests/expected-tests.txt" --installed
