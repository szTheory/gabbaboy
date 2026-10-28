#!/usr/bin/env bash
# Hosted driver for the cumulative DMG performance gate (Phase 16, TUNE-03, D-13..D-17).
#
#   --gate                    cachegrind Ir of the checkout against a v0.2.0 build made in the same job, plus the
#                             native realtime floor (Linux with valgrind)
#   --seeded-regression       the same comparison with a scratch-tree patch that must fail ir-budget-exceeded
#   --noop-twin               the same comparison with a comment-only scratch patch that must pass
#   --attribution             measure the D-17 revision selection and write the attribution receipt (Linux)
#   --attribution-dry-run [--rev REV]
#                             build the selection (or one revision) with the DMG-only adapted harness and check
#                             each ROM's consumed_half_dots and digest pins; needs no valgrind
#
# The evaluator is tests/scripts/verify-perf-gate.py. This script only builds, runs and collects. It never
# writes the real repository tree: every patched or extracted tree lives in a temporary directory.
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
LIMITS="$ROOT/tests/baseline/perf-gate-v1.txt"
CHECKER="$ROOT/tests/scripts/verify-perf-gate.py"
GATES="$ROOT/tests/scripts/verify-release-gates.py"
V020_EXPECTED=ab301aa69b1f085050fd66bf7b1378863a0821f2
LIMITS_BASE_REV=947d6a9d177af6c04a5f9ea6abcc2c470ab9be57
ROMS=(tracer libbet visible-demo)
# Lines added to the seeded patch: about 12 Ir per half-dot. The iteration count per half-dot is sized from the
# first hosted gate run's ratio margin; override with GBB_SEED_ITERS_PER_HALF_DOT when resizing.
SEED_ITERS_PER_HALF_DOT=${GBB_SEED_ITERS_PER_HALF_DOT:-2}
SEED_ANCHOR='static void advance_devices_to(gbb_instance *m, uint64_t target) {'
BUILD_COMMAND='cmake -S $REV -B $BUILD -DCMAKE_BUILD_TYPE=Release; validate CMAKE_PROJECT_VERSION with cmake/StateVersion.cmake; cc -std=c17 -O3 -DNDEBUG -DGBB_STATE_RELEASE_MAJOR=$MAJOR -DGBB_STATE_RELEASE_MINOR=$MINOR -DGBB_STATE_RELEASE_PATCH=$PATCH -I$REV/include $HARNESS $REV/src/core/*.c'

WORK=$(mktemp -d "${TMPDIR:-/tmp}/gbb-perf-gate.XXXXXX")
trap 'rm -rf "$WORK"' EXIT

fail() { echo "REJECT $1: $2" >&2; exit 1; }

limit() { awk -F= -v key="$1" '$0 !~ /^#/ && $1 == key { print substr($0, length(key) + 2) }' "$LIMITS"; }

sha256_of() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | cut -d' ' -f1; else shasum -a 256 "$1" | cut -d' ' -f1; fi
}

check_rom_pins() {
  local rom
  for rom in "${ROMS[@]}"; do
    [[ "$(sha256_of "$ROOT/$(limit "rom.$rom.path")")" == "$(limit "rom.$rom.sha256")" ]] ||
      fail limits-schema "ROM $rom does not match its sha256 pin"
  done
}

validated_release_triplet() {
  local tree=$1 configure_dir=$2 revision=$3 output
  cmake -S "$tree" -B "$configure_dir" -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF \
    -DGABBABOY_BUILD_PLAYER=OFF >"$configure_dir.log" 2>&1 || {
      cat "$configure_dir.log" >&2
      fail harness-version-configure-failed "CMake could not resolve source version for $tree"
    }
  output=$(python3 -I "$ROOT/tests/scripts/verify-state-contract.py" \
    --state-release-from-cache "$configure_dir/CMakeCache.txt" \
    --version-module "$ROOT/cmake/StateVersion.cmake" --cmake cmake \
    --rev "$revision" --repo "$ROOT") ||
    fail harness-version-invalid "StateVersion.cmake rejected the release version in $tree"
  [[ "$output" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] ||
    fail harness-version-invalid "validated source release triplet was malformed for $tree"
  echo "$output"
}

# build_measure TREE HARNESS OUT: configure the source tree to obtain its own project version,
# validate it through StateVersion.cmake, then keep one fixed compiler command for every tree.
build_measure() {
  local tree=$1 harness=$2 out=$3 revision=$4 configure_dir="$WORK/cmake-measure-$(basename "$1")" triplet major minor patch
  rm -rf "$configure_dir" "$configure_dir.log"
  triplet=$(validated_release_triplet "$tree" "$configure_dir" "$revision")
  IFS=. read -r major minor patch <<<"$triplet"
  cc -std=c17 -O3 -DNDEBUG \
    -DGBB_STATE_RELEASE_MAJOR="$major" -DGBB_STATE_RELEASE_MINOR="$minor" \
    -DGBB_STATE_RELEASE_PATCH="$patch" -I"$tree/include" "$harness" "$tree"/src/core/*.c -o "$out" ||
    fail harness-build-failed "build failed for $tree"
}

require_valgrind() {
  command -v valgrind >/dev/null 2>&1 || fail valgrind-missing "valgrind is not installed"
}

# cachegrind_run BIN ROM OUTFILE: Ir only (--cache-sim=no); prints the measure_core line.
cachegrind_run() {
  valgrind --tool=cachegrind --cache-sim=no --cachegrind-out-file="$3" "$1" --no-trace "$2" 2>"$3.log"
}

# collect DIR BIN REPEATS: <rom>.cg.N and <rom>.line for every gated ROM.
collect() {
  local dir=$1 bin=$2 repeats=$3 rom repeat
  mkdir -p "$dir"
  for rom in "${ROMS[@]}"; do
    for ((repeat = 1; repeat <= repeats; repeat++)); do
      cachegrind_run "$bin" "$ROOT/$(limit "rom.$rom.path")" "$dir/$rom.cg.$repeat" >"$dir/$rom.line.$repeat"
    done
  done
}

# build_identity BIN REV: hash the exact executable together with its committed source identity,
# compiler identity, and the fixed command template. The receipt contains only this digest.
build_identity() {
  local binary=$1 revision=$2 compiler
  compiler=$(cc --version | head -n 1)
  python3 -I - "$binary" "$revision" "$compiler" "$BUILD_COMMAND" <<'PY'
import hashlib
import json
import sys

with open(sys.argv[1], "rb") as executable:
    binary_sha256 = hashlib.sha256(executable.read()).hexdigest()
identity = {
    "binary_sha256": binary_sha256,
    "source_revision": sys.argv[2],
    "compiler": sys.argv[3],
    "build_command": sys.argv[4],
}
payload = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
print(hashlib.sha256(payload).hexdigest())
PY
}

# timing_set BIN OUTFILE: one discarded warm-up run, then nine timed runs, for every ROM.
timing_set() {
  local bin=$1 out=$2 rom index
  : >"$out"
  for rom in "${ROMS[@]}"; do
    for ((index = 0; index < 10; index++)); do
      echo "rom=$rom $("$bin" --no-trace "$ROOT/$(limit "rom.$rom.path")")" >>"$out"
    done
  done
}

versions() {
  echo "compiler: $(cc --version | head -n 1)"
  echo "valgrind: $(valgrind --version)"
}

# evaluate_tree HEADTREE [realtime]: builds v0.2.0 and the head tree, collects Ir and runs the evaluator.
# Prints the evaluator's verdict; returns its exit status.
evaluate_tree() {
  local head_tree=$1 with_realtime=$2 status=1 attempt head_revision base_identity head_identity
  [[ "$(git -C "$ROOT" rev-parse 'v0.2.0^{commit}')" == "$V020_EXPECTED" ]] ||
    fail workload-digest-mismatch "v0.2.0 is not $V020_EXPECTED"
  rm -rf "$WORK/base-tree" "$WORK/base" "$WORK/head"
  mkdir -p "$WORK/base-tree"
  git -C "$ROOT" archive v0.2.0 CMakeLists.txt cmake src include | tar -x -C "$WORK/base-tree"
  build_measure "$WORK/base-tree" "$ROOT/tests/measure_core.c" "$WORK/base-measure" "$V020_EXPECTED"
  head_revision=$(git -C "$ROOT" rev-parse HEAD)
  build_measure "$head_tree" "$ROOT/tests/measure_core.c" "$WORK/head-measure" "$head_revision"
  base_identity=$(build_identity "$WORK/base-measure" "$V020_EXPECTED")
  head_identity=$(build_identity "$WORK/head-measure" "$head_revision")
  collect "$WORK/base" "$WORK/base-measure" 1
  collect "$WORK/head" "$WORK/head-measure" 2
  local args=(--evaluate --limits "$LIMITS" --base "$WORK/base" --head "$WORK/head"
    --base-rev "$LIMITS_BASE_REV" --source-base-rev "$V020_EXPECTED" --source-head-rev "$head_revision"
    --build-base-identity "$base_identity" --build-head-identity "$head_identity")
  # A widened Ir limit passes only with a deterministic exception receipt that verify-release-gates.py --review-approval
  # derived from a verified OWNER comment (D-22, RM-030): the evaluator writes the exact measurement the owner approves by
  # digest, the release gate checks the comment against it, and only the receipt that gate wrote reaches the ratchet. No
  # receipt can be handed to the evaluator directly, ordinary runs need no approval, and an approval never excuses a
  # correctness, safety or realtime failure: the evaluator below still judges all of those.
  if [[ -n "${GBB_IR_EXCEPTION_COMMENT_JSON:-}" || -n "${GBB_IR_EXCEPTION_DECISION:-}" ]]; then
    [[ -n "${GBB_IR_EXCEPTION_COMMENT_JSON:-}" && -n "${GBB_IR_EXCEPTION_DECISION:-}" ]] ||
      fail exception-approval-incomplete "GBB_IR_EXCEPTION_COMMENT_JSON and GBB_IR_EXCEPTION_DECISION are both required"
    rm -f "$WORK/exception-measurement.json" "$WORK/exception-decision.json" "$WORK/exception-receipt.json"
    python3 -I "$CHECKER" "${args[@]}" --emit-exception-measurement "$WORK/exception-measurement.json" \
      >"$WORK/exception-measure.out" 2>"$WORK/exception-measure.err" || true
    [[ -s "$WORK/exception-measurement.json" ]] ||
      fail exception-not-needed "no deterministic Ir exception is requested by this run: $(cat "$WORK/exception-measure.err")"
    python3 -I "$GATES" --review-approval --comment-json "$GBB_IR_EXCEPTION_COMMENT_JSON" \
      --decision "$GBB_IR_EXCEPTION_DECISION" --measurement "$WORK/exception-measurement.json" \
      --rev "$head_revision" --output "$WORK/exception-decision.json" --exception-receipt "$WORK/exception-receipt.json" ||
      fail exception-approval-refused "the OWNER approval was refused; the limit stays unapproved"
    args+=(--exception-receipt "$WORK/exception-receipt.json")
  fi
  if [[ "$with_realtime" == yes ]]; then
    for attempt in 1 2; do
      timing_set "$WORK/head-measure" "$WORK/realtime.txt"
      if python3 -I "$CHECKER" "${args[@]}" --realtime "$WORK/realtime.txt" >"$WORK/verdict" 2>"$WORK/verdict.err"; then
        status=0
        break
      fi
      # Only a realtime miss earns the one retry; an Ir verdict is deterministic.
      grep -q 'REJECT realtime-below-floor' "$WORK/verdict.err" || break
    done
    cat "$WORK/verdict" "$WORK/verdict.err" || true
    return "$status"
  fi
  python3 -I "$CHECKER" "${args[@]}" >"$WORK/verdict" 2>"$WORK/verdict.err" && status=0 || status=$?
  cat "$WORK/verdict" "$WORK/verdict.err" || true
  return "$status"
}

digests_equal() {
  local rom repeat
  for rom in "${ROMS[@]}"; do
    for repeat in 1 2; do
      [[ "$(grep -o 'correctness_digest_fnv1a64=[0-9a-f]*' "$WORK/base/$rom.line.1")" == \
         "$(grep -o 'correctness_digest_fnv1a64=[0-9a-f]*' "$WORK/head/$rom.line.$repeat")" ]] || return 1
    done
  done
}

# seeded_tree MODE: copy src and include into a scratch tree and patch the anchored definition.
seeded_tree() {
  local mode=$1 tree="$WORK/seeded-tree" file count
  rm -rf "$tree"
  mkdir -p "$tree"
  cp -R "$ROOT/CMakeLists.txt" "$ROOT/cmake" "$ROOT/src" "$ROOT/include" "$tree/"
  file="$tree/src/core/gabbaboy.c"
  count=$(grep -Fxc -- "$SEED_ANCHOR" "$file" || true)
  [[ "$count" == 1 ]] || fail seeded-anchor-missing "the definition anchor matched $count lines, expected 1"
  if [[ "$mode" == regression ]]; then
    # A volatile accumulator loop, SEED_ITERS_PER_HALF_DOT iterations per elapsed half-dot. The marker string
    # lets a test double recognise the patched binary; the loop never changes guest state.
    local patch="    static const char gbb_seed_marker[] __attribute__((used)) = \"GBB_SEEDED_REGRESSION_MARKER\"; volatile uint64_t gbb_seed_sink = (uint64_t)gbb_seed_marker[0]; for (uint64_t gbb_seed_i = 0, gbb_seed_n = (target > m->time_half_dots ? target - m->time_half_dots : 0) * ${SEED_ITERS_PER_HALF_DOT}u; gbb_seed_i < gbb_seed_n; ++gbb_seed_i) gbb_seed_sink += gbb_seed_i;"
  else
    local patch="    /* perf-gate no-op twin: a comment at the seeded anchor, no code change */"
  fi
  awk -v anchor="$SEED_ANCHOR" -v patch="$patch" '{ print } $0 == anchor { print patch }' "$file" >"$file.new"
  mv "$file.new" "$file"
  SEEDED_TREE=$tree
}

mode_gate() {
  require_valgrind
  versions
  check_rom_pins
  evaluate_tree "$ROOT" yes
}

mode_seeded() {
  require_valgrind
  versions
  check_rom_pins
  seeded_tree regression
  local status=0
  evaluate_tree "$SEEDED_TREE" no || status=$?
  [[ "$status" -ne 0 ]] && grep -q 'REJECT ir-budget-exceeded' "$WORK/verdict.err" ||
    fail seeded-not-rejected "the seeded regression was not rejected with ir-budget-exceeded"
  digests_equal || fail workload-digest-mismatch "the seeded regression changed the guest digest"
  echo "seeded regression rejected as expected with an unchanged digest (iterations per half-dot: $SEED_ITERS_PER_HALF_DOT)"
}

mode_noop() {
  require_valgrind
  versions
  check_rom_pins
  seeded_tree noop
  evaluate_tree "$SEEDED_TREE" no || fail noop-twin-rejected "the no-op twin patch was rejected"
  echo "no-op twin passed"
}

# ---------------------------------------------------------------- attribution (D-17)

adapt_harness() {
  python3 -I "$CHECKER" --adapt-harness "$ROOT/tests/measure_core.c" --out "$WORK/measure_core_dmg.c" ||
    fail harness-adapt-anchor "the DMG-only harness could not be derived"
}

# build_revision SHA: extract src and include of that revision and build the adapted harness against them.
build_revision() {
  local sha=$1 tree="$WORK/rev-$1"
  local configure_dir="$WORK/cmake-revision-$1" triplet major minor patch
  rm -rf "$tree"
  mkdir -p "$tree"
  git -C "$ROOT" archive "$sha" CMakeLists.txt cmake src include | tar -x -C "$tree"
  rm -rf "$configure_dir" "$configure_dir.log"
  triplet=$(validated_release_triplet "$tree" "$configure_dir" "$sha")
  IFS=. read -r major minor patch <<<"$triplet"
  cc -std=c17 -O3 -DNDEBUG \
    -DGBB_STATE_RELEASE_MAJOR="$major" -DGBB_STATE_RELEASE_MINOR="$minor" \
    -DGBB_STATE_RELEASE_PATCH="$patch" -I"$tree/include" \
    "$WORK/measure_core_dmg.c" "$tree"/src/core/*.c -o "$tree/measure" ||
    fail harness-build-failed "revision $sha did not build with the adapted harness"
}

# check_pins SHA: native run of every gated ROM must equal the consumed and digest pins.
check_pins() {
  local sha=$1 rom line
  for rom in "${ROMS[@]}"; do
    line=$("$WORK/rev-$sha/measure" --no-trace "$ROOT/$(limit "rom.$rom.path")")
    [[ "$line" == *" consumed_half_dots=$(limit "rom.$rom.consumed_half_dots") "* ]] ||
      fail proxy-vacuous "revision $sha $rom consumed_half_dots differs from its pin"
    [[ "$line" == *"correctness_digest_fnv1a64=$(limit "rom.$rom.digest")" ]] ||
      fail workload-digest-mismatch "revision $sha $rom digest differs from its pin"
  done
}

selection_list() {
  if [[ -n "${1:-}" ]]; then git -C "$ROOT" rev-parse "$1^{commit}"; else python3 -I "$CHECKER" --print-selection --head HEAD; fi
}

mode_dry_run() {
  local rev="" sha count=0 revisions
  if [[ "${1:-}" == --rev ]]; then rev=${2:?--rev needs a revision}; fi
  check_rom_pins
  adapt_harness >"$WORK/adapt.out"
  local harness_sha
  harness_sha=$(sed -n 's/.*harness_sha256=\([0-9a-f]*\).*/\1/p' "$WORK/adapt.out")
  revisions=$(selection_list "$rev")
  while read -r sha; do
    [[ -n "$sha" ]] || continue
    build_revision "$sha"
    check_pins "$sha"
    rm -rf "$WORK/rev-$sha"
    count=$((count + 1))
  done <<<"$revisions"
  echo "attribution dry-run pass revisions=$count harness_sha256=$harness_sha"
}

mode_attribution() {
  require_valgrind
  check_rom_pins
  adapt_harness >"$WORK/adapt.out"
  local sha
  mkdir -p "$WORK/meas"
  while read -r sha; do
    [[ -n "$sha" ]] || continue
    build_revision "$sha"
    check_pins "$sha"
    collect "$WORK/meas/$sha" "$WORK/rev-$sha/measure" 2
    rm -rf "$WORK/rev-$sha"
  done < <(selection_list "")
  # Realtime: one discarded warm-up run, then nine timed runs per ROM, at the head.
  build_revision "$(git -C "$ROOT" rev-parse HEAD)"
  timing_set "$WORK/rev-$(git -C "$ROOT" rev-parse HEAD)/measure" "$WORK/realtime.txt"
  local image="${ImageOS:-unknown}-${ImageVersion:-unknown}"
  local hardware
  hardware="$(uname -s) $(uname -m), $(nproc 2>/dev/null || echo unknown) vCPU hosted runner"
  python3 -I "$CHECKER" --emit-attribution --head HEAD --meas "$WORK/meas" --out "${GBB_ATTRIBUTION_OUT:-perf-attribution-v1.json}" \
    --realtime "$WORK/realtime.txt" --runner-image "$image" --gcc-version "$(cc --version | head -n 1)" \
    --valgrind-version "$(valgrind --version)" --hardware-class "$hardware" --build-command "$BUILD_COMMAND"
}

case "${1:-}" in
  --gate) mode_gate ;;
  --seeded-regression) mode_seeded ;;
  --noop-twin) mode_noop ;;
  --attribution) mode_attribution ;;
  --attribution-dry-run) shift; mode_dry_run "$@" ;;
  *) echo "usage: run-perf-gate.sh --gate | --seeded-regression | --noop-twin | --attribution | --attribution-dry-run [--rev REV]" >&2; exit 2 ;;
esac
