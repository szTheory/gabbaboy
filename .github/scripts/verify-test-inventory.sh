#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)

filter_expected_for_platform() {
  local platform=$1
  local expected_path=$2
  case "$platform" in
    MINGW*|MSYS*|CYGWIN*)
      sed -i.bak \
        -e '/^cgb_bench_ab_selftest$/d' \
        -e '/^cgb_bench_ab_wrong_digest$/d' \
        -e '/^cgb_bench_ab_missing_field$/d' \
        -e '/^cgb_bench_ab_missing_elapsed$/d' \
        -e '/^cgb_mooneye_repro_requires_manifest$/d' \
        -e '/^cgb_colour_repro_tool_failure$/d' \
        -e '/^cgb_colour_repro_missing_pin$/d' \
        -e '/^cgb_speed_repro_tool_failure$/d' \
        -e '/^cgb_speed_repro_missing_pin$/d' \
        -e '/^age_repro_selfcheck$/d' \
        -e '/^age_repro_selfcheck_tampered$/d' \
        -e '/^age_repro_compare_tampered$/d' \
        -e '/^core_linkage_links$/d' \
        -e '/^core_linkage_controls$/d' \
        -e '/^release_lifecycle_replay$/d' \
        -e '/^release_lifecycle_controls$/d' \
        -e '/^perf_advisory_pipeline$/d' \
        -e '/^perf_advisory_controls$/d' \
        -e '/^host_continuation$/d' \
        -e '/^host_rom_max_size$/d' \
        -e '/^host_rom_oversize$/d' \
        -e '/^host_rom_unreadable$/d' \
        -e '/^host_cli_stem_refusal$/d' \
        "$expected_path"
      rm -f "$expected_path.bak"
      ;;
  esac
}

_self_test_platform_filter_cases() {
  inventory_selftest_dir=$(mktemp -d "${TMPDIR:-/tmp}/gabbaboy-inventory-selftest.XXXXXXXXXX")
  trap 'rm -rf -- "$inventory_selftest_dir"' EXIT
  printf '%s\n' \
    cgb_bench_ab_selftest \
    cgb_bench_ab_wrong_digest \
    cgb_bench_ab_missing_field \
    cgb_bench_ab_missing_elapsed \
    cgb_mooneye_repro_requires_manifest \
    cgb_colour_repro_tool_failure \
    cgb_colour_repro_missing_pin \
    cgb_speed_repro_tool_failure \
    cgb_speed_repro_missing_pin \
    age_repro_selfcheck \
    age_repro_selfcheck_tampered \
    age_repro_compare_tampered \
    core_linkage_links \
    core_linkage_controls \
    release_lifecycle_replay \
    release_lifecycle_controls \
    perf_advisory_pipeline \
    perf_advisory_controls \
    host_continuation \
    host_rom_max_size \
    host_rom_oversize \
    host_rom_unreadable \
    host_cli_stem_refusal \
    age_stall_window \
    cgb_speed_fixture_digest > "$inventory_selftest_dir/expected"
  cp "$inventory_selftest_dir/expected" "$inventory_selftest_dir/windows-expected"
  cp "$inventory_selftest_dir/expected" "$inventory_selftest_dir/unix-expected"
  filter_expected_for_platform MINGW64_NT-10.0 "$inventory_selftest_dir/windows-expected"
  printf '%s\n' age_stall_window cgb_speed_fixture_digest > "$inventory_selftest_dir/window-survivors"
  cmp -s "$inventory_selftest_dir/windows-expected" "$inventory_selftest_dir/window-survivors" || {
    echo 'Windows inventory filter did not remove exactly the bash-only tests' >&2
    return 1
  }
  for test_name in \
    cgb_bench_ab_selftest \
    cgb_bench_ab_wrong_digest \
    cgb_bench_ab_missing_field \
    cgb_bench_ab_missing_elapsed \
    cgb_mooneye_repro_requires_manifest \
    cgb_colour_repro_tool_failure \
    cgb_colour_repro_missing_pin \
    cgb_speed_repro_tool_failure \
    cgb_speed_repro_missing_pin \
    age_repro_selfcheck \
    age_repro_selfcheck_tampered \
    age_repro_compare_tampered \
    core_linkage_links \
    core_linkage_controls \
    release_lifecycle_replay \
    release_lifecycle_controls \
    perf_advisory_pipeline \
    perf_advisory_controls \
    host_continuation \
    host_rom_max_size \
    host_rom_oversize \
    host_rom_unreadable \
    host_cli_stem_refusal; do
    if grep -Fqx "$test_name" "$inventory_selftest_dir/windows-expected"; then
      echo "Windows inventory filter retained bash-only test: $test_name" >&2
      return 1
    fi
  done
  grep -Fqx age_stall_window "$inventory_selftest_dir/windows-expected" || {
    echo 'Windows inventory filter removed a platform-independent test' >&2
    return 1
  }
  filter_expected_for_platform Darwin "$inventory_selftest_dir/unix-expected"
  cmp -s "$inventory_selftest_dir/unix-expected" "$inventory_selftest_dir/expected" || {
    echo 'non-Windows inventory filter changed the expected test list' >&2
    return 1
  }

  printf '%s\n' age_stall_window cgb_speed_fixture_digest > "$inventory_selftest_dir/required"
  cat > "$inventory_selftest_dir/complete.xml" <<'XML'
<testsuites><testsuite>
  <testcase name="age_stall_window"/>
  <testcase name="cgb_speed_fixture_digest"/>
</testsuite></testsuites>
XML
  bash "$0" "$inventory_selftest_dir/complete.xml" "$inventory_selftest_dir/required" --core-only >/dev/null || {
    echo 'inventory self-test rejected a complete required report' >&2
    return 1
  }
  cat > "$inventory_selftest_dir/missing.xml" <<'XML'
<testsuites><testsuite><testcase name="cgb_speed_fixture_digest"/></testsuite></testsuites>
XML
  if bash "$0" "$inventory_selftest_dir/missing.xml" "$inventory_selftest_dir/required" --core-only >/dev/null 2>&1; then
    echo 'inventory self-test accepted a genuinely missing required test' >&2
    return 1
  fi
  echo 'CTest platform inventory self-test passed; exclusions, platform-independent retention, and missing-test rejection verified.'
}

self_test_platform_filter() {
  _self_test_platform_filter_cases
  bash "$script_dir/test-inventory-cleanup.sh" "$0"
}

if [[ $# -eq 1 && "$1" == '--self-test-core' ]]; then
  _self_test_platform_filter_cases
  exit 0
fi

if [[ $# -eq 1 && "$1" == '--self-test' ]]; then
  self_test_platform_filter
  exit 0
fi

if [[ $# -lt 2 || $# -gt 3 ]]; then
  echo "Usage: $0 <junit-report> <expected-tests-file> [--core-only|--installed] | --self-test" >&2
  exit 2
fi

report=$1
expected_file=$2
inventory=${3:---core-only}
[[ -s "$report" ]] || { echo "Missing or empty CTest report: $report" >&2; exit 1; }
[[ -s "$expected_file" ]] || { echo "Missing or empty expected inventory: $expected_file" >&2; exit 1; }

if grep -Eq '<(failure|error)([[:space:]>]|/)' "$report"; then
  echo "CTest report contains failed or errored cases" >&2
  exit 1
fi

if grep -Eq '<skipped([[:space:]>]|/)' "$report"; then
  echo "CTest report contains skipped cases" >&2
  exit 1
fi

expected=$(mktemp)
actual=$(mktemp)
trap 'rm -f "$expected" "$actual"' EXIT
awk '{ sub(/\r$/, ""); print }' "$expected_file" > "$expected"
if [[ "$inventory" == "--core-only" ]]; then
  sed -i.bak '/^installed_/d' "$expected"
  rm -f "$expected.bak"
elif [[ "$inventory" != "--installed" ]]; then
  echo "Unknown inventory mode: $inventory" >&2
  exit 2
fi

# Bash-only tests omitted by CMake on Windows must also be omitted from the expected report list.
filter_expected_for_platform "$(uname -s)" "$expected"

sed -nE 's/.*<testcase[^>]*name="([^"]+)".*/\1/p' "$report" | LC_ALL=C sort > "$actual"
LC_ALL=C sort -o "$expected" "$expected"
if ! diff -u "$expected" "$actual"; then
  echo "Executed CTest inventory differs from the required inventory" >&2
  exit 1
fi

echo "Verified $(wc -l < "$actual" | tr -d ' ') executed CTest cases; none skipped."
