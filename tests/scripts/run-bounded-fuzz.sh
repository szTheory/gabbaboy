#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
BUILD_DIR=${GBB_BUILD_DIR:-"$ROOT/build-asan"}
MODE=${1:-}

runtime_available() {
  command -v clang >/dev/null 2>&1 || return 1
  local probe_dir
  probe_dir=$(mktemp -d "${TMPDIR:-/tmp}/gbb-fuzzer-probe.XXXXXX")
  printf '%s\n' '#include <stddef.h>' '#include <stdint.h>' \
    'int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) { (void)data; (void)size; return 0; }' \
    > "$probe_dir/probe.c"
  if clang -fsanitize=fuzzer,address,undefined "$probe_dir/probe.c" \
       -o "$probe_dir/probe" >/dev/null 2>&1; then
    rm -rf "$probe_dir"
    return 0
  fi
  rm -rf "$probe_dir"
  return 1
}

fuzz_binary="$BUILD_DIR/tests/fuzz_core"
if [[ "$(uname -s)" == "Windows_NT" ]]; then
  fuzz_binary+=".exe"
fi

case "$MODE" in
  --self-test)
    grep -q '^loader_boundary_fuzz$' "$ROOT/tests/expected-tests.txt"
    grep -q '^battery_api_fuzz$' "$ROOT/tests/expected-tests.txt"
    grep -q 'FUZZ_INPUT_LIMIT 65536u' "$ROOT/tests/fuzz_core.c"
    grep -q 'FUZZ_OPERATION_LIMIT 16u' "$ROOT/tests/fuzz_core.c"
    grep -q 'FUZZ_RUN_LIMIT UINT64_C(2048)' "$ROOT/tests/fuzz_core.c"
    grep -q 'FUZZ_INPUT_HALF_DOT_LIMIT UINT64_C(8192)' "$ROOT/tests/fuzz_core.c"
    grep -q -- '-max_len=65536' "$ROOT/tests/scripts/run-bounded-fuzz.sh"
    grep -q -- '-max_total_time=60' "$ROOT/tests/scripts/run-bounded-fuzz.sh"
    grep -q -- '-rss_limit_mb=512' "$ROOT/tests/scripts/run-bounded-fuzz.sh"
    grep -q -- '-jobs=1' "$ROOT/tests/scripts/run-bounded-fuzz.sh"
    if runtime_available; then
      echo "self-test=pass libfuzzer_runtime=available limits=input:65536,operations:16,half_dots_per_input:8192,half_dots_per_run:2048,time:2s/60s,rss:512MiB,workers:1"
    else
      echo "self-test=pass libfuzzer_runtime=unsupported deterministic_regressions=required"
    fi
    ;;
  --fast)
    [[ -d "$BUILD_DIR" ]] || { echo "Build directory not found: $BUILD_DIR" >&2; exit 2; }
    cmake --build "$BUILD_DIR" --target test_loader_fuzz test_battery_fuzz
    ctest --test-dir "$BUILD_DIR" --output-on-failure --no-tests=error \
      -R '^(battery_api_fuzz|loader_boundary_fuzz)$'
    if grep -q '^GABBABOY_ENABLE_SANITIZERS:BOOL=ON$' "$BUILD_DIR/CMakeCache.txt"; then
      sanitizer_status=asan-ubsan
    else
      sanitizer_status=not-enabled
    fi
    if [[ -x "$fuzz_binary" ]]; then
      corpus=$(mktemp -d "${TMPDIR:-/tmp}/gbb-fuzz-seeds.XXXXXX")
      cp "$ROOT/fixtures/tracer/tracer.gb" "$corpus/tracer.gb"
      mkdir -p "$BUILD_DIR/fuzz-artifacts"
      "$fuzz_binary" "$corpus" -runs=128 -seed=1 -max_len=65536 \
        -timeout=2 -rss_limit_mb=512 -jobs=1 -workers=1 \
        -artifact_prefix="$BUILD_DIR/fuzz-artifacts/"
      rm -rf "$corpus"
    else
      echo "fuzzer=unsupported configured fuzz_core target unavailable; sanitizer=$sanitizer_status deterministic_regressions=passed"
    fi
    ;;
  --explore)
    [[ -x "$fuzz_binary" ]] || {
      echo "fuzzer=unsupported build a matching Clang libFuzzer target before exploration" >&2
      exit 2
    }
    corpus=$(mktemp -d "${TMPDIR:-/tmp}/gbb-fuzz-seeds.XXXXXX")
    cp "$ROOT/fixtures/tracer/tracer.gb" "$corpus/tracer.gb"
    mkdir -p "$BUILD_DIR/fuzz-artifacts"
    "$fuzz_binary" "$corpus" -max_len=65536 -max_total_time=60 \
      -timeout=2 -rss_limit_mb=512 -jobs=1 -workers=1 \
      -artifact_prefix="$BUILD_DIR/fuzz-artifacts/"
    rm -rf "$corpus"
    ;;
  *)
    echo "Usage: $0 --self-test | --fast | --explore" >&2
    exit 2
    ;;
esac
