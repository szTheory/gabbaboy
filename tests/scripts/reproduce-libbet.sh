#!/usr/bin/env bash
# Opt-in, networked rebuild of the vendored Libbet ROM with pinned RGBDS 0.7.0 and Pillow 12.3.0.
# Required CI never runs this. It only compares and never writes inside the repository.
set -euo pipefail

if [[ $# != 1 || $1 != --compare ]]; then
  echo "usage: $0 --compare" >&2
  exit 2
fi
repo_root=$(git rev-parse --show-toplevel)
[[ -d "$repo_root/fixtures/libbet" ]] || { echo 'fixtures/libbet not found' >&2; exit 2; }

commit=46a765a2c01701bffb8c0b7dd6e4be3a6b193090
# RGBDS 1.0.1 rejects `rgbasm -h`, which this tag's makefile uses, so this job pins 0.7.0.
case "$(uname -s)" in
  Linux)  archive=rgbds-0.7.0-linux-x86_64.tar.xz
          archive_sha=f67bc8fdd2b1521f0bed5a3750a09b206de760064fb95bb52790d375c3297210 ;;
  Darwin) archive=rgbds-0.7.0-macos-x86_64.zip
          archive_sha=f2aee8235db2e9f020708bcb3c74112366ca50f7eb880d7717d95e385a583a16 ;;
  *) echo 'unsupported-platform' >&2; exit 3 ;;
esac

sha256_file() { shasum -a 256 "$1" | cut -d ' ' -f 1; }

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

# Provenance first: nothing is downloaded, extracted or installed until both pins are confirmed
# against the official registries. Any mismatch or API failure fails closed.
download_url=$(python3 -I - "$repo_root/tests/scripts/libbet-repro-requirements.txt" "$archive" "$archive_sha" <<'PY'
import json, re, sys, urllib.request

req_path, archive, archive_sha = sys.argv[1:]
pypi = 'https://pypi.org/pypi/pillow/12.3.0/json'
github = 'https://api.github.com/repos/gbdev/rgbds/releases/tags/v0.7.0'
prefix = 'https://github.com/gbdev/rgbds/releases/download/v0.7.0/'

def fail(kind, detail):
    print(f'{kind}: {detail}', file=sys.stderr)
    raise SystemExit(1)

def fetch(url):
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'gabbaboy-libbet-repro'})
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.load(response)
    except Exception as error:  # network, TLS, HTTP or JSON failure
        fail('provenance-unavailable', f'{url}: {error}')

pins = set(re.findall(r'--hash=sha256:([0-9a-f]{64})', open(req_path).read()))
if not pins:
    fail('provenance-mismatch', 'no pinned Pillow hashes found')
published = {f['digests']['sha256'] for f in fetch(pypi).get('urls', [])}
missing = sorted(pins - published)
if missing:
    fail('provenance-mismatch', f'Pillow 12.3.0 hash not published on PyPI: {missing[0]}')

assets = [a for a in fetch(github).get('assets', []) if a.get('name') == archive]
if len(assets) != 1:
    fail('provenance-mismatch', f'{archive} is not a published asset of gbdev/rgbds v0.7.0')
url = assets[0].get('browser_download_url', '')
if not url.startswith(prefix):
    fail('provenance-mismatch', f'unexpected download URL {url}')
digest = assets[0].get('digest')
if digest is not None and digest != f'sha256:{archive_sha}':
    fail('provenance-mismatch', f'GitHub digest {digest} differs from the pin')
print(url)
PY
)
# Reached only when the check above exited 0 (set -e inside the command substitution aborts otherwise).
echo "provenance verified pypi=https://pypi.org/pypi/pillow/12.3.0/json github=https://api.github.com/repos/gbdev/rgbds/releases/tags/v0.7.0"

tools="$work/rgbds"
mkdir -p "$tools"
curl --fail --location --silent --show-error "$download_url" -o "$work/$archive"
[[ "$(sha256_file "$work/$archive")" == "$archive_sha" ]] || { echo "archive digest differs from the D-02 pin: $archive" >&2; exit 1; }
case "$archive" in
  *.zip) unzip -q "$work/$archive" -d "$tools" ;;
  *)     tar -xJf "$work/$archive" -C "$tools" ;;
esac
rgbasm_path=$(find "$tools" -type f -name rgbasm | head -n 1)
[[ -n "$rgbasm_path" ]] || { echo 'rgbasm not found in archive' >&2; exit 1; }
tools_bin=$(dirname "$rgbasm_path")
chmod +x "$tools_bin"/rgb* 2>/dev/null || true
"$tools_bin/rgbasm" --version

python3 -m venv "$work/venv"
"$work/venv/bin/python" -m pip install --quiet --require-hashes --no-deps \
  -r "$repo_root/tests/scripts/libbet-repro-requirements.txt"

git clone --quiet https://github.com/pinobatch/libbet.git "$work/libbet"
git -C "$work/libbet" checkout --quiet "$commit"
[[ "$(git -C "$work/libbet" rev-parse HEAD)" == "$commit" ]] || { echo 'checked-out commit differs from the pin' >&2; exit 1; }

# Closure completeness against the real pinned tree, before anything from the clone runs.
closure_line=$(python3 -I "$repo_root/tests/scripts/verify-libbet-admission.py" --derive-closure "$work/libbet" | grep '^libbet closure derived files=') \
  || { echo 'closure-derivation-mismatch: derivation did not succeed' >&2; exit 1; }
echo "$closure_line"

(cd "$work/libbet" && PATH="$work/venv/bin:$tools_bin:$PATH" make libbet.gb)

built=$(sha256_file "$work/libbet/libbet.gb")
vendored=$(sha256_file "$repo_root/fixtures/libbet/libbet.gb")
if cmp -s "$work/libbet/libbet.gb" "$repo_root/fixtures/libbet/libbet.gb"; then
  echo "libbet reproduction: identical sha256=$built"
else
  echo "libbet reproduction: differs built=$built vendored=$vendored"
  exit 1
fi
