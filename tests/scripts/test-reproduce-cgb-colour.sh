#!/usr/bin/env bash
# Negative controls for reproduce-cgb-colour.sh (review WR-03). Runs the script from a scratch copy
# of its inputs with stub RGBDS tools, so it needs no real RGBDS:
#   tool-failure : a failing rgbasm must report result=error (exit 2) with the tool's stderr,
#                  never result=differs;
#   missing-pin  : a build pin absent from BOTH manifests must report result=error, not pass as
#                  None == None.
set -euo pipefail
case_name=${1:?usage: test-reproduce-cgb-colour.sh tool-failure|missing-pin}
script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
repo_root=$(cd "$script_dir/../.." && pwd -P)
scratch=$(mktemp -d "${TMPDIR:-/tmp}/gabbaboy-repro-test.XXXXXXXX")
trap 'rm -rf -- "$scratch"' EXIT
mkdir -p "$scratch/tests/scripts" "$scratch/fixtures" "$scratch/bin"
cp "$script_dir/reproduce-cgb-colour.sh" "$scratch/tests/scripts/"
cp -R "$repo_root/fixtures/cgb-colour" "$repo_root/fixtures/cgb-banking" "$scratch/fixtures/"
for tool in rgbasm rgblink rgbfix; do
  printf '#!/bin/sh\nif [ "$1" = --version ]; then echo "%s v1.0.1"; exit 0; fi\necho "stub failure from %s" >&2\nexit 3\n' \
    "$tool" "$tool" >"$scratch/bin/$tool"
  chmod +x "$scratch/bin/$tool"
done
if [ "$case_name" = missing-pin ]; then
  python3 -I - "$scratch" <<'PY'
import json, sys
for f in ('fixtures/cgb-colour/manifest.json', 'fixtures/cgb-banking/manifest.json'):
    p = sys.argv[1] + '/' + f
    d = json.load(open(p)); d['build'].pop('archive_sha256', None); json.dump(d, open(p, 'w'))
PY
  want='result=error reason=build-pin-archive_sha256-missing'
else
  want='result=error reason=tool-failed-rgbasm-.* stderr=stub failure from rgbasm'
fi
set +e
out=$(PATH="$scratch/bin:$PATH" bash "$scratch/tests/scripts/reproduce-cgb-colour.sh" 2>&1)
code=$?
set -e
echo "$out"
[ "$code" -eq 2 ] || { echo "expected exit 2, got $code" >&2; exit 1; }
echo "$out" | grep -q "result=differs" && { echo "harness error was reported as differs" >&2; exit 1; }
echo "$out" | grep -Eq "$want" || { echo "missing expected diagnostic: $want" >&2; exit 1; }
echo "reproduce-cgb-colour negative control $case_name ok"
