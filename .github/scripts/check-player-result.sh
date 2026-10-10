#!/usr/bin/env bash
# Decides whether the macOS player package evidence in ci.yml required-native is acceptable.
# Usage: check-player-result.sh GATE_RESULT REQUIRED PLAYER_RESULT
#        check-player-result.sh --self-test
# GATE_RESULT is needs.player-gate.result, REQUIRED is its player_required output, and
# PLAYER_RESULT is needs.macos-player-package.result. Anything unexpected fails closed.
set -euo pipefail

decide() {
  local gate_result=$1 required=$2 player_result=$3
  # The gate must have succeeded: a failed or skipped gate leaves REQUIRED empty and would
  # otherwise be indistinguishable from a legitimately skipped push-run player job.
  if [[ "$gate_result" != success ]]; then
    echo "Player gating job did not succeed: $gate_result" >&2
    return 1
  fi
  case "$required:$player_result" in
    true:success | false:success | false:skipped) return 0 ;;
    true:*)
      echo "Required macOS player package evidence did not succeed: $player_result" >&2
      return 1
      ;;
    *)
      echo "Unexpected player gating state: required=$required result=$player_result" >&2
      return 1
      ;;
  esac
}

self_test() {
  local count=0 row gate required player expected status
  local rows=(
    "success|true|success|pass"
    "success|false|skipped|pass"
    "success|false|success|pass"
    "success|true|skipped|fail"
    "success|true|failure|fail"
    "success|true|cancelled|fail"
    "success||skipped|fail"
    "success||success|fail"
    "failure||skipped|fail"
    "cancelled||skipped|fail"
    "skipped||skipped|fail"
    "failure|true|success|fail"
    "cancelled|true|success|fail"
    "skipped|false|success|fail"
  )
  for row in "${rows[@]}"; do
    IFS='|' read -r gate required player expected <<<"$row"
    if decide "$gate" "$required" "$player" 2>/dev/null; then status=pass; else status=fail; fi
    if [[ "$status" != "$expected" ]]; then
      echo "FAIL: player result self-test: gate=$gate required=$required player=$player expected=$expected got=$status" >&2
      exit 1
    fi
    count=$((count + 1))
  done
  echo "PASS: player result self-test ($count cases)"
}

if [[ "${1:-}" == --self-test ]]; then
  self_test
  exit 0
fi

if [[ $# -ne 3 ]]; then
  echo "usage: check-player-result.sh GATE_RESULT REQUIRED PLAYER_RESULT | --self-test" >&2
  exit 2
fi
decide "$1" "$2" "$3"
