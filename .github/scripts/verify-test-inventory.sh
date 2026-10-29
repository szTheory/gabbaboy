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
        -e '/^host_api_surface$/d' \
        -e '/^host_api_surface_controls$/d' \
        -e '/^host_periodic_flush$/d' \
        -e '/^host_first_write$/d' \
        -e '/^host_idempotent_rerun$/d' \
        -e '/^host_sweep_after_checks$/d' \
        -e '/^host_writer_fault_temp$/d' \
        -e '/^host_writer_fault_write$/d' \
        -e '/^host_writer_fault_sync$/d' \
        -e '/^host_writer_fault_close$/d' \
        -e '/^host_writer_fault_target$/d' \
        -e '/^host_writer_fault_rename$/d' \
        -e '/^host_writer_fault_dirsync$/d' \
        -e '/^host_writer_eio_no_retry$/d' \
        -e '/^host_writer_eexist$/d' \
        -e '/^host_writer_target_not_regular$/d' \
        -e '/^host_sweep_exact_prefix$/d' \
        -e '/^host_rtc_final_compare$/d' \
        -e '/^host_savedir_missing$/d' \
        -e '/^host_savedir_not_directory$/d' \
        -e '/^host_savedir_symlink_path$/d' \
        -e '/^host_import_exact$/d' \
        -e '/^host_import_zero$/d' \
        -e '/^host_import_short$/d' \
        -e '/^host_import_long$/d' \
        -e '/^host_import_mgba_footer$/d' \
        -e '/^host_import_oversize$/d' \
        -e '/^host_import_bad_rtc$/d' \
        -e '/^host_import_symlink$/d' \
        -e '/^host_import_dangling_symlink$/d' \
        -e '/^host_import_fifo$/d' \
        -e '/^host_import_directory$/d' \
        -e '/^host_import_stray_nobattery$/d' \
        -e '/^host_import_device$/d' \
        -e '/^host_rom_fifo$/d' \
        -e '/^host_rom_directory$/d' \
        -e '/^host_savedir_mutant_mkdir$/d' \
        -e '/^host_import_mutant_follow$/d' \
        -e '/^host_continuation_mutant_ignore_import$/d' \
        -e '/^host_no_test_seams_shipped$/d' \
        -e '/^host_no_test_seams_shipped_control$/d' \
        -e '/^slot_roundtrip$/d' \
        -e '/^slot_empty$/d' \
        -e '/^slot_wrong_rom_untouched$/d' \
        -e '/^slot_refusal_dmg_in_cgb$/d' \
        -e '/^slot_refusal_version_token$/d' \
        -e '/^slot_refusal_text_file$/d' \
        -e '/^slot_refusal_flipped_byte$/d' \
        -e '/^slot_refusal_truncated$/d' \
        -e '/^slot_refusal_oversize$/d' \
        -e '/^slot_refusal_symlink$/d' \
        -e '/^slot_undo_write_failure$/d' \
        -e '/^slot_backup_write_failure$/d' \
        -e '/^slot_undo_swap$/d' \
        -e '/^slot_no_undo$/d' \
        -e '/^slot_battery_guard$/d' \
        -e '/^slot_unsafe_queued_input$/d' \
        -e '/^slot_save_failure_keeps_old$/d' \
        -e '/^slot_mutant_undo_before_load$/d' \
        -e '/^slot_mutant_preload_before_validate$/d' \
        -e '/^slot_mutant_no_guard$/d' \
        -e '/^slot_mutant_no_rollback$/d' \
        -e '/^slot_reanchor_later$/d' \
        -e '/^slot_reanchor_earlier$/d' \
        -e '/^slot_select_message$/d' \
        -e '/^slot_mutant_plan_ignores_last$/d' \
        -e '/^host_signal_term$/d' \
        -e '/^host_signal_int$/d' \
        -e '/^host_signal_inherited_ign$/d' \
        -e '/^host_exit_frames_clean$/d' \
        -e '/^host_exit_failure_readonly$/d' \
        -e '/^host_exit_core_stop$/d' \
        -e '/^host_exit_refusal$/d' \
        -e '/^host_exit_crash_storm$/d' \
        -e '/^host_signal_disposition$/d' \
        -e '/^host_exit_table_codes$/d' \
        -e '/^host_run_stop_before_first_frame$/d' \
        -e '/^host_signal_decoy_no_flush$/d' \
        -e '/^host_signal_decoy_partial_frame$/d' \
        -e '/^host_signal_decoy_exit0_after_failed_flush$/d' \
        -e '/^host_signal_decoy_in_place_write$/d' \
        -e '/^host_no_test_seams_shipped_run_control$/d' \
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
    host_api_surface \
    host_api_surface_controls \
    host_periodic_flush \
    host_first_write \
    host_idempotent_rerun \
    host_sweep_after_checks \
    host_writer_fault_temp \
    host_writer_fault_write \
    host_writer_fault_sync \
    host_writer_fault_close \
    host_writer_fault_target \
    host_writer_fault_rename \
    host_writer_fault_dirsync \
    host_writer_eio_no_retry \
    host_writer_eexist \
    host_writer_target_not_regular \
    host_sweep_exact_prefix \
    host_rtc_final_compare \
    host_savedir_missing \
    host_savedir_not_directory \
    host_savedir_symlink_path \
    host_import_exact \
    host_import_zero \
    host_import_short \
    host_import_long \
    host_import_mgba_footer \
    host_import_oversize \
    host_import_bad_rtc \
    host_import_symlink \
    host_import_dangling_symlink \
    host_import_fifo \
    host_import_directory \
    host_import_stray_nobattery \
    host_import_device \
    host_rom_fifo \
    host_rom_directory \
    host_savedir_mutant_mkdir \
    host_import_mutant_follow \
    host_continuation_mutant_ignore_import \
    host_no_test_seams_shipped \
    host_no_test_seams_shipped_control \
    slot_roundtrip \
    slot_empty \
    slot_wrong_rom_untouched \
    slot_refusal_dmg_in_cgb \
    slot_refusal_version_token \
    slot_refusal_text_file \
    slot_refusal_flipped_byte \
    slot_refusal_truncated \
    slot_refusal_oversize \
    slot_refusal_symlink \
    slot_undo_write_failure \
    slot_backup_write_failure \
    slot_undo_swap \
    slot_no_undo \
    slot_battery_guard \
    slot_unsafe_queued_input \
    slot_save_failure_keeps_old \
    slot_mutant_undo_before_load \
    slot_mutant_preload_before_validate \
    slot_mutant_no_guard \
    slot_mutant_no_rollback \
    slot_reanchor_later \
    slot_reanchor_earlier \
    slot_select_message \
    slot_mutant_plan_ignores_last \
    host_signal_term \
    host_signal_int \
    host_signal_inherited_ign \
    host_exit_frames_clean \
    host_exit_failure_readonly \
    host_exit_core_stop \
    host_exit_refusal \
    host_exit_crash_storm \
    host_signal_disposition \
    host_exit_table_codes \
    host_run_stop_before_first_frame \
    host_signal_decoy_no_flush \
    host_signal_decoy_partial_frame \
    host_signal_decoy_exit0_after_failed_flush \
    host_signal_decoy_in_place_write \
    host_no_test_seams_shipped_run_control \
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
    host_cli_stem_refusal \
    host_api_surface \
    host_api_surface_controls \
    host_periodic_flush \
    host_first_write \
    host_idempotent_rerun \
    host_sweep_after_checks \
    host_writer_fault_temp \
    host_writer_fault_write \
    host_writer_fault_sync \
    host_writer_fault_close \
    host_writer_fault_target \
    host_writer_fault_rename \
    host_writer_fault_dirsync \
    host_writer_eio_no_retry \
    host_writer_eexist \
    host_writer_target_not_regular \
    host_sweep_exact_prefix \
    host_rtc_final_compare \
    host_savedir_missing \
    host_savedir_not_directory \
    host_savedir_symlink_path \
    host_import_exact \
    host_import_zero \
    host_import_short \
    host_import_long \
    host_import_mgba_footer \
    host_import_oversize \
    host_import_bad_rtc \
    host_import_symlink \
    host_import_dangling_symlink \
    host_import_fifo \
    host_import_directory \
    host_import_stray_nobattery \
    host_import_device \
    host_rom_fifo \
    host_rom_directory \
    host_savedir_mutant_mkdir \
    host_import_mutant_follow \
    host_continuation_mutant_ignore_import \
    host_no_test_seams_shipped \
    host_no_test_seams_shipped_control \
    slot_roundtrip \
    slot_empty \
    slot_wrong_rom_untouched \
    slot_refusal_dmg_in_cgb \
    slot_refusal_version_token \
    slot_refusal_text_file \
    slot_refusal_flipped_byte \
    slot_refusal_truncated \
    slot_refusal_oversize \
    slot_refusal_symlink \
    slot_undo_write_failure \
    slot_backup_write_failure \
    slot_undo_swap \
    slot_no_undo \
    slot_battery_guard \
    slot_unsafe_queued_input \
    slot_save_failure_keeps_old \
    slot_mutant_undo_before_load \
    slot_mutant_preload_before_validate \
    slot_mutant_no_guard \
    slot_mutant_no_rollback \
    slot_reanchor_later \
    slot_reanchor_earlier \
    slot_select_message \
    slot_mutant_plan_ignores_last \
    host_signal_term \
    host_signal_int \
    host_signal_inherited_ign \
    host_exit_frames_clean \
    host_exit_failure_readonly \
    host_exit_core_stop \
    host_exit_refusal \
    host_exit_crash_storm \
    host_signal_disposition \
    host_exit_table_codes \
    host_run_stop_before_first_frame \
    host_signal_decoy_no_flush \
    host_signal_decoy_partial_frame \
    host_signal_decoy_exit0_after_failed_flush \
    host_signal_decoy_in_place_write \
    host_no_test_seams_shipped_run_control; do
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
