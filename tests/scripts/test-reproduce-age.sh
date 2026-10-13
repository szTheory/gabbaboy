#!/usr/bin/env bash
# Offline negative controls for the AGE ROM rebuild gate.
set -euo pipefail
case_name=${1:?usage: test-reproduce-age.sh compare-tampered|selfcheck-tampered}
case "$case_name" in
  compare-tampered|selfcheck-tampered) ;;
  *) echo "usage: $0 compare-tampered|selfcheck-tampered" >&2; exit 2 ;;
esac
script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
repo_root=$(cd "$script_dir/../.." && pwd -P)
scratch=$(mktemp -d "${TMPDIR:-/tmp}/gabbaboy-age-negative.XXXXXXXX")
trap 'rm -rf -- "$scratch"' EXIT
mkdir -p "$scratch/tests/scripts" "$scratch/fixtures"
cp "$script_dir/reproduce-age.sh" "$scratch/tests/scripts/"
cp -R "$repo_root/fixtures/age" "$scratch/fixtures/"
if [ "$case_name" = compare-tampered ]; then
  mkdir "$scratch/rebuilt"
  cp "$scratch/fixtures/age/"*.gb "$scratch/rebuilt/"
  output=$(bash "$scratch/tests/scripts/reproduce-age.sh" --compare-built "$scratch/rebuilt")
  echo "$output" | grep -q '^result=byte-identical$'
  python3 -I - "$scratch/rebuilt/spsw-div-cgbBCE.gb" <<'PY'
import pathlib, sys
path = pathlib.Path(sys.argv[1])
data = bytearray(path.read_bytes())
data[0] ^= 1
path.write_bytes(data)
PY
  set +e
  output=$(bash "$scratch/tests/scripts/reproduce-age.sh" --compare-built "$scratch/rebuilt" 2>&1)
  status=$?
  set -e
  [ "$status" -eq 1 ] && echo "$output" | grep -q '^result=differs spsw-div-cgbBCE.gb '
else
  python3 -I - "$scratch/fixtures/age/manifest.json" <<'PY'
import json, pathlib, sys
path = pathlib.Path(sys.argv[1]); data = json.loads(path.read_text())
data['fixtures'][0]['source_path'] = 'src/../../evil.asm'
path.write_text(json.dumps(data))
PY
  set +e
  output=$(bash "$scratch/tests/scripts/reproduce-age.sh" --self-check 2>&1)
  status=$?
  set -e
  [ "$status" -eq 1 ] && echo "$output" | grep -q '^self-check=fail source_path-outside-allow-list$'
  python3 -I - "$scratch/fixtures/age/manifest.json" <<'PY'
import json, pathlib, sys
path = pathlib.Path(sys.argv[1]); data = json.loads(path.read_text())
data['fixtures'][0]['source_path'] = 'src/speed-switch/spsw-div-cgbBCE.asm'
data['fixtures'][0]['sha256'] = 'ABC'
path.write_text(json.dumps(data))
PY
  set +e
  output=$(bash "$scratch/tests/scripts/reproduce-age.sh" --self-check 2>&1)
  status=$?
  set -e
  [ "$status" -eq 1 ] && echo "$output" | grep -q '^self-check=fail invalid-sha256-spsw-div-cgbBCE.gb$'
fi
echo "reproduce-age negative control $case_name ok"
