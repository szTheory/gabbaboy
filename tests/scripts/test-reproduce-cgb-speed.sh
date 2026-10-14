#!/usr/bin/env bash
# Negative controls for reproduce-cgb-speed.sh. Runs the script from a scratch copy of its inputs
# with stub RGBDS tools, so it needs no real RGBDS:
#   tool-failure : a failing rgbasm must report result=error (exit 2) with the tool's stderr,
#                  never result=differs;
#   missing-pin  : a build pin absent from BOTH manifests must report result=error, not pass as
#                  None == None.
set -euo pipefail
case_name=${1:?usage: test-reproduce-cgb-speed.sh tool-failure|missing-pin}
script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
repo_root=$(cd "$script_dir/../.." && pwd -P)
scratch=$(mktemp -d "${TMPDIR:-/tmp}/gabbaboy-repro-test.XXXXXXXX")
trap 'rm -rf -- "$scratch"' EXIT
mkdir -p "$scratch/tests/scripts" "$scratch/fixtures" "$scratch/bin"
cp "$script_dir/reproduce-cgb-speed.sh" "$scratch/tests/scripts/"
cp -R "$repo_root/fixtures/cgb-speed" "$repo_root/fixtures/cgb-banking" "$scratch/fixtures/"
for tool in rgbasm rgblink rgbfix; do
  printf '#!/bin/sh\nif [ "$1" = --version ]; then echo "%s v1.0.1"; exit 0; fi\necho "stub failure from %s" >&2\nexit 3\n' \
    "$tool" "$tool" >"$scratch/bin/$tool"
  chmod +x "$scratch/bin/$tool"
done
if [ "$case_name" = missing-pin ]; then
  python3 -I - "$scratch" <<'PY'
import json, sys
for f in ('fixtures/cgb-speed/manifest.json', 'fixtures/cgb-banking/manifest.json'):
    p = sys.argv[1] + '/' + f
    d = json.load(open(p)); d['build'].pop('archive_sha256', None); json.dump(d, open(p, 'w'))
PY
  want='result=error reason=build-pin-archive_sha256-missing'
elif [ "$case_name" = tool-failure ]; then
  want='result=error reason=tool-failed-rgbasm-.* stderr=stub failure from rgbasm'
else
  echo "unknown negative-control case: $case_name" >&2
  exit 2
fi
check_workflow_speed_pin() {
  python3 -I - "$repo_root" "$scratch/workflow-check" <<'PY'
import json
import pathlib
import re
import shutil
import subprocess
import sys
import textwrap

repo = pathlib.Path(sys.argv[1])
root = pathlib.Path(sys.argv[2])
workflow = (repo / '.github/workflows/fixture-repro.yml').read_text().splitlines()
start = next(i for i, line in enumerate(workflow) if "rgbds_pin=$(python3 <<'PY'" in line)
source = []
for line in workflow[start + 1:]:
    if line == '          PY':
        break
    source.append(line[10:])
else:
    raise SystemExit('fixture-repro embedded RGBDS pin block is incomplete')
program = textwrap.dedent('\n'.join(source))
for relative in set(re.findall(r"root / '([^']+)'", program)):
    source_path = repo / relative
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, target)

good = subprocess.run([sys.executable, '-'], input=program, text=True,
                      capture_output=True, cwd=root)
expected = '1.0.1\trgbds-linux-x86_64.tar.xz\t80a5cad8dae27e24e46a93041352c47cadbc165103983f41c2b3082c42f6dad9'
if good.returncode != 0 or expected not in good.stdout:
    raise SystemExit(f'fixture-repro pin positive failed: {good.stdout}{good.stderr}')

speed = root / 'fixtures/cgb-speed/manifest.json'
manifest = json.loads(speed.read_text())
manifest['build']['archive_sha256'] = '0' * 64
speed.write_text(json.dumps(manifest))
bad = subprocess.run([sys.executable, '-'], input=program, text=True,
                     capture_output=True, cwd=root)
if bad.returncode == 0 or 'CGB speed RGBDS pin archive_sha256 differs' not in bad.stderr:
    raise SystemExit(f'fixture-repro pin mismatch was accepted: {bad.stdout}{bad.stderr}')
print('fixture-repro cgb-speed pin positive and mismatch control ok')
PY
}
set +e
out=$(PATH="$scratch/bin:$PATH" bash "$scratch/tests/scripts/reproduce-cgb-speed.sh" 2>&1)
code=$?
set -e
echo "$out"
[ "$code" -eq 2 ] || { echo "expected exit 2, got $code" >&2; exit 1; }
echo "$out" | grep -q "result=differs" && { echo "harness error was reported as differs" >&2; exit 1; }
echo "$out" | grep -Eq "$want" || { echo "missing expected diagnostic: $want" >&2; exit 1; }
check_workflow_speed_pin
echo "reproduce-cgb-speed negative control $case_name ok"
