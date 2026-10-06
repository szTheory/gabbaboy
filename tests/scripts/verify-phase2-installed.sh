#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "$0")/../.." && pwd)
helper_root="$repo_root/build/phase2-install-check"
original="$helper_root/original"
relocated="$helper_root/relocated"
installed_build="$helper_root/fresh-installed"
core_build="$helper_root/fresh-core"

# This directory is owned entirely by this verification helper.
cmake -E rm -rf "$helper_root"
mkdir -p "$helper_root"

# Clear any prior cache value so this build proves the core-only registration path.
cmake --preset phase1 -DGBB_TEST_INSTALL_PREFIX=
cmake --build --preset phase1
cmake --install "$repo_root/build" --prefix "$original"
test -s "$original/share/gabbaboy/fixtures/tracer/tracer.gb"
cmake -E rename "$original" "$relocated"
test -s "$relocated/share/gabbaboy/fixtures/tracer/tracer.gb"
test ! -e "$original"

# A new build tree sees only the populated relocated prefix and registers the
# installed consumer inventory from that real package.
cmake -S "$repo_root" -B "$installed_build" -G Ninja \
  -DCMAKE_BUILD_TYPE=Debug -DBUILD_TESTING=ON \
  "-DGBB_TEST_INSTALL_PREFIX=$relocated"
cmake --build "$installed_build"
ctest --test-dir "$installed_build" --output-on-failure --no-tests=error \
  --output-junit phase2-installed.xml
bash "$repo_root/.github/scripts/verify-test-inventory.sh" \
  "$installed_build/phase2-installed.xml" "$repo_root/tests/expected-tests.txt" --installed
for consumer in installed_consumer_phase2_c installed_consumer_phase2_cpp; do
  grep -F "name=\"$consumer\"" "$installed_build/phase2-installed.xml" >/dev/null || {
    echo "Installed CTest report is missing $consumer" >&2
    exit 1
  }
done

# Configure a second untouched build tree without any installed-prefix value.
cmake -S "$repo_root" -B "$core_build" -G Ninja \
  -DCMAKE_BUILD_TYPE=Debug -DBUILD_TESTING=ON -DGBB_TEST_INSTALL_PREFIX=
cmake --build "$core_build"
ctest --test-dir "$core_build" --output-on-failure --no-tests=error \
  --output-junit phase2-core.xml
bash "$repo_root/.github/scripts/verify-test-inventory.sh" \
  "$core_build/phase2-core.xml" "$repo_root/tests/expected-tests.txt" --core-only
for consumer in installed_consumer_phase2_c installed_consumer_phase2_cpp; do
  if grep -F "name=\"$consumer\"" "$core_build/phase2-core.xml" >/dev/null; then
    echo "Core-only CTest report unexpectedly contains $consumer" >&2
    exit 1
  fi
done
