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
  python3 -I - "$scratch/rebuilt/m3-bg-lcdc-cgbBCE.gb" <<'PY'
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
  actual=$(echo "$output" | grep '^result=differs m3-bg-lcdc-cgbBCE.gb ')
  [ "$status" -eq 1 ] && [ -n "$actual" ]
  echo "negative-control=pass $actual"
else
  reset_fixture() {
    rm -rf -- "$scratch/fixtures/age"
    cp -R "$repo_root/fixtures/age" "$scratch/fixtures/age"
  }
  expect_selfcheck_failure() {
    local expected=$1 output status actual
    set +e
    output=$(bash "$scratch/tests/scripts/reproduce-age.sh" --self-check 2>&1)
    status=$?
    set -e
    actual=$(echo "$output" | grep '^self-check=fail ' | head -n 1)
    [ "$status" -eq 1 ] && [ "$actual" = "self-check=fail $expected" ] || return 1
    echo "negative-control=pass $actual"
  }
  reset_fixture
  python3 -I - "$scratch/fixtures/age/manifest.json" <<'PY'
import json, pathlib, sys
path = pathlib.Path(sys.argv[1]); data = json.loads(path.read_text())
data['fixtures'][0]['source_path'] = 'src/../../evil.asm'
path.write_text(json.dumps(data))
PY
  expect_selfcheck_failure 'source_path-outside-allow-list'
  reset_fixture
  python3 -I - "$scratch/fixtures/age/manifest.json" <<'PY'
import json, pathlib, sys
path = pathlib.Path(sys.argv[1]); data = json.loads(path.read_text())
data['fixtures'][0]['source_path'] = 'src/speed-switch/spsw-div-cgbBCE.asm'
data['fixtures'][0]['sha256'] = 'ABC'
path.write_text(json.dumps(data))
PY
  expect_selfcheck_failure 'invalid-sha256-spsw-div-cgbBCE.gb'
  reset_fixture
  python3 -I - "$scratch/fixtures/age/manifest.json" <<'PY'
import json, pathlib, sys
path = pathlib.Path(sys.argv[1]); data = json.loads(path.read_text())
entry = next(row for row in data['fixtures'] if row.get('fixture_class') == 'age-m3-reference')
entry['reference']['file'] = 'references/m3-bg-scx-cgbBCE.png'
path.write_text(json.dumps(data))
PY
  expect_selfcheck_failure 'm3-reference-file-mismatch-m3-bg-lcdc-cgbBCE.gb'
  reset_fixture
  rm "$scratch/fixtures/age/m3-bg-lcdc-cgbBCE.gb"
  expect_selfcheck_failure 'committed-file-missing-m3-bg-lcdc-cgbBCE.gb'
  reset_fixture
  python3 -I - "$scratch/fixtures/age/references/m3-bg-lcdc-cgbBCE.png" <<'PY'
import pathlib, sys
path = pathlib.Path(sys.argv[1]); data = bytearray(path.read_bytes()); data[-1] ^= 1
path.write_bytes(data)
PY
  expect_selfcheck_failure 'committed-reference-digest-mismatch-m3-bg-lcdc-cgbBCE.gb'
  reset_fixture
  python3 -I - "$scratch/fixtures/age/manifest.json" <<'PY'
import json, pathlib, sys
path = pathlib.Path(sys.argv[1]); data = json.loads(path.read_text())
data['build']['archive_sha256'] = '0' * 64
path.write_text(json.dumps(data))
PY
  expect_selfcheck_failure 'RGBDS-build-pin-mismatch'
  reset_fixture
  python3 -I - "$scratch/fixtures/age/manifest.json" <<'PY'
import json, pathlib, sys
path = pathlib.Path(sys.argv[1]); data = json.loads(path.read_text())
entry = next(row for row in data['fixtures'] if row['file'] == 'm3-bg-lcdc-nocgb-ncmBCE.gb')
entry['mode'] = 'native-cgb'
path.write_text(json.dumps(data))
PY
  expect_selfcheck_failure 'm3-mode-mismatch-m3-bg-lcdc-nocgb-ncmBCE.gb'
  reset_fixture
  python3 -I - "$scratch/fixtures/age/manifest.json" <<'PY'
import json, pathlib, sys
path = pathlib.Path(sys.argv[1]); data = json.loads(path.read_text())
entry = next(row for row in data['fixtures'] if row['file'] == 'm3-bg-lcdc-cgbBCE.gb')
entry['qualification_status'] = 'admitted-not-executed'
path.write_text(json.dumps(data))
PY
  expect_selfcheck_failure 'm3-qualification-status-mismatch-m3-bg-lcdc-cgbBCE.gb'
  reset_fixture
  python3 -I - "$scratch/fixtures/age/manifest.json" <<'PY'
import json, pathlib, sys
path = pathlib.Path(sys.argv[1]); data = json.loads(path.read_text())
entry = next(row for row in data['fixtures'] if row['file'] == 'm3-bg-lcdc-cgbBCE.gb')
entry['case_id'] = 'wrong-case-identity'
path.write_text(json.dumps(data))
PY
  expect_selfcheck_failure 'm3-case-identity-mismatch-m3-bg-lcdc-cgbBCE.gb'
  reset_fixture
  python3 -I - "$scratch/fixtures/age/manifest.json" <<'PY'
import json, pathlib, sys
path = pathlib.Path(sys.argv[1]); data = json.loads(path.read_text())
entry = next(row for row in data['fixtures'] if row['file'] == 'm3-bg-lcdc-cgbBCE.gb')
entry['pixel_mismatch_signature_sha256'] = '0' * 64
path.write_text(json.dumps(data))
PY
  expect_selfcheck_failure 'm3-pixel-signature-mismatch-m3-bg-lcdc-cgbBCE.gb'
  reset_fixture
  python3 -I - "$scratch/fixtures/age/manifest.json" <<'PY'
import json, pathlib, sys
path = pathlib.Path(sys.argv[1]); data = json.loads(path.read_text())
data['fixtures'] = [row for row in data['fixtures'] if row['file'] != 'm3-bg-scx-ds-cgbBCE.gb']
path.write_text(json.dumps(data))
PY
  expect_selfcheck_failure 'm3-manifest-membership-mismatch'
  reset_fixture
  python3 -I - "$scratch/fixtures/age/manifest.json" <<'PY'
import json, pathlib, sys
path = pathlib.Path(sys.argv[1]); data = json.loads(path.read_text())
data['fixtures'][0]['fixture_class'] = 'age-unknown-protocol'
path.write_text(json.dumps(data))
PY
  expect_selfcheck_failure 'unsupported-fixture-class-age-unknown-protocol'
fi
echo "reproduce-age negative control $case_name ok"
