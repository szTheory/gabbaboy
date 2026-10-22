#!/usr/bin/env bash
set -euo pipefail

# Shared, unprivileged setup for the release and rehearsal evidence producers.
#
# Every input is explicit: the subject tree (code under test), the source commit and tag it must be, the
# judge tree (trusted validators) and the output directory. The script never publishes: it has no network
# or GitHub-CLI use, never pushes, never edits remotes or credentials, and reads no token. A workflow that
# runs it holds at most contents: read. Writable jobs (attachers) must never run a copy taken from a
# subject checkout; verify-workflow-policy.py enforces both properties.
#
#   verify-subject --subject DIR --source-sha SHA --tag TAG [--local-tag]
#       Subject HEAD must be SHA. With --local-tag (rehearsal only) the runner-local tag is (re)pointed at SHA;
#       otherwise TAG must already resolve to SHA. Prints SOURCE_SHA=/RELEASE_TAG= lines.
#   corpus-build --subject DIR
#       Configure, build and install the native preset used by the corpus receipt run.
#   collect --subject DIR --output DIR
#       Copy exactly the six evidence families from DIR/build into the output; print an explicit inventory.
#   verify --judge DIR --subject DIR --source-sha SHA --tag TAG --evidence DIR --archive FILE
#       Run the judge tree's release gate over the evidence; the subject is only the tree being judged.
#   --self-test
#       Positive and intended-defect controls through this command line.

fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

EVIDENCE_NAMES="cgb-corpus-receipt.json support-ledger.json v02-performance-receipt.json v02-fuzz-receipt.json source-archive-receipt.json v02-consumer-receipt.json"

subject=""
judge=""
source_sha=""
tag=""
output=""
evidence=""
archive=""
local_tag=0

assign_once() {
  # $1 variable name, $2 option text, $3 value
  [[ -z "${!1}" ]] || fail "duplicate option: $2"
  [[ -n "$3" ]] || fail "empty value for $2"
  printf -v "$1" '%s' "$3"
}

parse_options() {
  while [[ $# -gt 0 ]]; do
    opt=$1
    if [[ "$opt" == --local-tag ]]; then
      [[ "$local_tag" == 0 ]] || fail "duplicate option: $opt"
      local_tag=1
      shift
      continue
    fi
    [[ $# -ge 2 ]] || fail "option $opt needs a value"
    if [[ "$opt" == --subject ]]; then assign_once subject "$opt" "$2"
    elif [[ "$opt" == --judge ]]; then assign_once judge "$opt" "$2"
    elif [[ "$opt" == --source-sha ]]; then assign_once source_sha "$opt" "$2"
    elif [[ "$opt" == --tag ]]; then assign_once tag "$opt" "$2"
    elif [[ "$opt" == --output ]]; then assign_once output "$opt" "$2"
    elif [[ "$opt" == --evidence ]]; then assign_once evidence "$opt" "$2"
    elif [[ "$opt" == --archive ]]; then assign_once archive "$opt" "$2"
    else fail "unknown option: $opt"
    fi
    shift 2
  done
}

require_set() {
  for name in "$@"; do
    [[ -n "${!name}" ]] || fail "--${name//_/-} is required"
  done
}

same_commit() {
  [[ "$1" == "$2" ]] || fail "$3"
}

require_identity() {
  [[ "$source_sha" =~ ^[0-9a-f]{40}$ ]] || fail "malformed source SHA"
  [[ "$tag" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || fail "malformed release tag"
}

cmd_verify_subject() {
  require_set subject source_sha tag
  require_identity
  [[ -d "$subject" ]] || fail "subject directory is missing: $subject"
  head=$(git -C "$subject" rev-parse HEAD)
  same_commit "$head" "$source_sha" "source mismatch: subject HEAD is not the requested source SHA"
  if [[ "$local_tag" == 1 ]]; then
    # Local only: this repoints the runner's checkout copy of the tag and is never pushed.
    git -C "$subject" tag -f "$tag" "$source_sha" > /dev/null
  fi
  tagged=$(git -C "$subject" rev-parse "$tag^{commit}")
  same_commit "$tagged" "$source_sha" "source mismatch: the tag does not resolve to the requested source SHA"
  printf 'SOURCE_SHA=%s\nRELEASE_TAG=%s\n' "$source_sha" "$tag"
}

cmd_corpus_build() {
  require_set subject
  [[ -d "$subject" ]] || fail "subject directory is missing: $subject"
  cd "$subject"
  mkdir -p build/package-prefix
  prefix="$PWD/build/package-prefix"
  cmake --preset phase1 "-DGBB_TEST_INSTALL_PREFIX=$prefix"
  cmake --build --preset phase1
  cmake --install build --prefix build/package-prefix
}

digest_of() {
  if command -v sha256sum > /dev/null; then
    sha256sum "$1" | cut -d ' ' -f 1
  else
    shasum -a 256 "$1" | cut -d ' ' -f 1
  fi
}

cmd_collect() {
  require_set subject output
  [[ -d "$subject/build" ]] || fail "subject has no build directory"
  mkdir -p "$output"
  for entry in "$output"/*; do
    [[ -e "$entry" ]] || continue
    known=0
    for name in $EVIDENCE_NAMES; do
      [[ "$entry" == "$output/$name" ]] && known=1
    done
    [[ "$known" == 1 ]] || fail "unexpected file in the evidence output: ${entry##*/}"
  done
  # Validate every family before copying anything, so a rejected run neither leaves a partial output nor prints one.
  for name in $EVIDENCE_NAMES; do
    source_file="$subject/build/$name"
    [[ -f "$source_file" && ! -L "$source_file" ]] || fail "missing evidence family: $name"
    [[ -s "$source_file" ]] || fail "empty evidence family: $name"
    if [[ -e "$output/$name" ]]; then
      cmp -s "$source_file" "$output/$name" || fail "conflicting evidence already collected: $name"
    fi
  done
  inventory=""
  for name in $EVIDENCE_NAMES; do
    [[ -e "$output/$name" ]] || cp "$subject/build/$name" "$output/$name"
    inventory="$inventory$name $(digest_of "$output/$name") $(wc -c < "$output/$name" | tr -d ' ')"$'\n'
  done
  printf '%s' "$inventory"
}

cmd_verify() {
  require_set judge subject source_sha tag evidence archive
  require_identity
  gate="$judge/.github/scripts/verify-release-gates.sh"
  [[ -f "$gate" ]] || fail "judge release gate is missing: $gate"
  [[ -d "$subject" && -d "$evidence" && -f "$archive" ]] || fail "subject, evidence directory or source archive is missing"
  gate=$(cd "$judge" && pwd)/.github/scripts/verify-release-gates.sh
  evidence=$(cd "$evidence" && pwd)
  archive=$(cd "$(dirname "$archive")" && pwd)/$(basename "$archive")
  cd "$subject"
  bash "$gate" --check-v02-evidence "$evidence" "$tag" "$source_sha" "$archive"
}

self_test() {
  script=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")
  work=$(mktemp -d "${TMPDIR:-/tmp}/gb-produce-evidence.XXXXXX")
  work=$(cd "$work" && pwd)
  trap 'rm -rf "$work"' EXIT HUP INT TERM
  repo="$work/repo"
  git init -q "$repo"
  git -C "$repo" -c user.name=fixture -c user.email=fixture@example.invalid commit -q --allow-empty -m one
  first=$(git -C "$repo" rev-parse HEAD)
  git -C "$repo" -c user.name=fixture -c user.email=fixture@example.invalid commit -q --allow-empty -m two
  head=$(git -C "$repo" rev-parse HEAD)
  rejected=0

  expect_reject() {
    # $1 label, $2 expected diagnostic, remaining arguments are the command line
    label=$1
    want=$2
    shift 2
    if bash "$script" "$@" > "$work/stdout" 2> "$work/stderr"; then
      fail "self-test accepted: $label"
    fi
    grep -q -- "$want" "$work/stderr" || fail "self-test rejected $label for the wrong reason: $(cat "$work/stderr")"
    [[ ! -s "$work/stdout" ]] || fail "self-test saw success output for rejected input: $label"
    rejected=$((rejected + 1))
    printf 'rejected: %s\n' "$label"
  }

  bash "$script" verify-subject --subject "$repo" --source-sha "$head" --tag v9.9.9 --local-tag > "$work/out1"
  bash "$script" verify-subject --subject "$repo" --source-sha "$head" --tag v9.9.9 --local-tag > "$work/out2"
  cmp -s "$work/out1" "$work/out2" || fail "repeated local tag setup was not idempotent"
  bash "$script" verify-subject --subject "$repo" --source-sha "$head" --tag v9.9.9 > /dev/null
  [[ "$(git -C "$repo" rev-parse "v9.9.9^{commit}")" == "$head" ]] || fail "local tag does not point at the source"
  printf 'PASS: local-only tag setup and a repeated run\n'

  expect_reject "malformed source SHA" "malformed source SHA" verify-subject --subject "$repo" --source-sha abc --tag v9.9.9
  expect_reject "malformed tag" "malformed release tag" verify-subject --subject "$repo" --source-sha "$head" --tag main
  expect_reject "source mismatch" "source mismatch" verify-subject --subject "$repo" --source-sha "$first" --tag v9.9.9 --local-tag
  git -C "$repo" tag -f v8.8.8 "$first" > /dev/null
  expect_reject "tag at another commit without --local-tag" "does not resolve" verify-subject --subject "$repo" --source-sha "$head" --tag v8.8.8
  expect_reject "missing subject" "subject directory is missing" verify-subject --subject "$work/absent" --source-sha "$head" --tag v9.9.9
  expect_reject "unknown option" "unknown option" verify-subject --subject "$repo" --source-sha "$head" --tag v9.9.9 --publish yes
  expect_reject "duplicate option" "duplicate option" verify-subject --subject "$repo" --subject "$repo" --source-sha "$head" --tag v9.9.9
  expect_reject "missing required option" "is required" verify-subject --subject "$repo" --tag v9.9.9
  expect_reject "unknown command" "usage" release-everything --subject "$repo"

  build="$repo/build"
  mkdir -p "$build"
  for name in $EVIDENCE_NAMES; do printf '{"family":"%s"}\n' "$name" > "$build/$name"; done
  bash "$script" collect --subject "$repo" --output "$work/evidence" > "$work/inventory"
  [[ "$(wc -l < "$work/inventory" | tr -d ' ')" == 6 ]] || fail "evidence inventory does not list six families"
  bash "$script" collect --subject "$repo" --output "$work/evidence" > "$work/inventory-again"
  cmp -s "$work/inventory" "$work/inventory-again" || fail "repeated collection changed the inventory"
  printf 'PASS: explicit six-family inventory and a repeated collection\n'
  : > "$build/v02-fuzz-receipt.json"
  expect_reject "empty evidence family" "empty evidence family" collect --subject "$repo" --output "$work/evidence-empty"
  printf '{"family":"v02-fuzz-receipt.json"}\n' > "$build/v02-fuzz-receipt.json"
  rm "$build/support-ledger.json"
  expect_reject "missing evidence family" "missing evidence family" collect --subject "$repo" --output "$work/evidence-missing"
  printf '{"family":"support-ledger.json"}\n' > "$build/support-ledger.json"
  printf '{"changed":true}\n' > "$build/v02-consumer-receipt.json"
  expect_reject "conflicting evidence from a second run" "conflicting evidence" collect --subject "$repo" --output "$work/evidence"
  mkdir -p "$work/evidence-extra"
  printf 'x\n' > "$work/evidence-extra/stray.json"
  expect_reject "unexpected file in the output" "unexpected file" collect --subject "$repo" --output "$work/evidence-extra"
  mkdir -p "$work/evidence-hidden"
  printf 'x\n' > "$work/evidence-hidden/.hidden"
  expect_reject "unexpected dotfile in the output" "unexpected file in the evidence output: .hidden" collect --subject "$repo" --output "$work/evidence-hidden"

  mkdir -p "$work/no-judge"
  : > "$work/archive.tar.gz"
  expect_reject "verification without the judge gate" "judge release gate is missing" verify --judge "$work/no-judge" \
    --subject "$repo" --source-sha "$head" --tag v9.9.9 --evidence "$work/evidence" --archive "$work/archive.tar.gz"
  expect_reject "verification with a source mismatch" "malformed source SHA" verify --judge "$work/no-judge" \
    --subject "$repo" --source-sha main --tag v9.9.9 --evidence "$work/evidence" --archive "$work/archive.tar.gz"
  # The judge gate runs with the subject as its working tree and exactly the explicit arguments; a stub records them.
  mkdir -p "$work/judge/.github/scripts"
  # shellcheck disable=SC2016
  printf '#!/usr/bin/env bash\nprintf "%%s\\n" "$PWD" "$@" > "%s/gate-record"\n' "$work" > "$work/judge/.github/scripts/verify-release-gates.sh"
  bash "$script" verify --judge "$work/judge" --subject "$repo" --source-sha "$head" --tag v9.9.9 \
    --evidence "$work/evidence" --archive "$work/archive.tar.gz"
  printf '%s\n' "$repo" --check-v02-evidence "$work/evidence" v9.9.9 "$head" "$work/archive.tar.gz" > "$work/gate-want"
  cmp -s "$work/gate-record" "$work/gate-want" || fail "the judge gate was not given the explicit subject and arguments: $(cat "$work/gate-record") // $(cat "$work/gate-want")"
  printf 'PASS: judge gate receives the subject as its working tree and explicit identities\n'
  printf 'PASS: producer contract self-test negative_controls=%s\n' "$rejected"
}

[[ $# -ge 1 ]] || fail "usage: produce-release-evidence.sh verify-subject|corpus-build|collect|verify OPTIONS | --self-test"
command=$1
shift
if [[ "$command" == --self-test ]]; then
  [[ $# -eq 0 ]] || fail "usage: produce-release-evidence.sh --self-test"
  self_test
elif [[ "$command" == verify-subject ]]; then
  parse_options "$@"
  cmd_verify_subject
elif [[ "$command" == corpus-build ]]; then
  parse_options "$@"
  cmd_corpus_build
elif [[ "$command" == collect ]]; then
  parse_options "$@"
  cmd_collect
elif [[ "$command" == verify ]]; then
  parse_options "$@"
  cmd_verify
else
  fail "usage: produce-release-evidence.sh verify-subject|corpus-build|collect|verify OPTIONS | --self-test (unknown command: $command)"
fi
