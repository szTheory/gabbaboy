#!/usr/bin/env bash
# Networked, pinned source preparation followed by public-core protocol probes.
set -euo pipefail
repo_root=$(git rev-parse --show-toplevel)
cd "$repo_root"
work_dir=$(mktemp -d "${TMPDIR:-/tmp}/gabbaboy-candidate.XXXXXXXX")
GBB_REPRO_OUTPUT_DIR="$work_dir" bash tests/scripts/reproduce-mooneye.sh --candidate fixtures/mooneye

cat > "$work_dir/probe.c" <<'C'
#include "gabbaboy/gabbaboy.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static gbb_trace_record trace[8192];
static gbb_diagnostic_record diagnostics[32768];

int main(int argc, char **argv) {
    if (argc != 5) return 2;
    FILE *f = fopen(argv[1], "rb");
    if (!f) return 2;
    unsigned char rom[32768];
    size_t size = fread(rom, 1, sizeof rom, f);
    int extra = fgetc(f);
    fclose(f);
    if (size != sizeof rom || extra != EOF) return 2;
    unsigned long callback = strtoul(argv[2], NULL, 16);
    unsigned long breakpoint = strtoul(argv[3], NULL, 16);
    int expect_failure = strcmp(argv[4], "fail") == 0;
    gbb_instance *machine = NULL;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) != GBB_OK ||
        gbb_load_rom(machine, rom, sizeof rom) != GBB_OK) return 2;
    unsigned long long ticks = 0;
    int saw_callback = 0, saw_breakpoint = 0, ppu_access = 0;
    while (ticks < 3000000 && !saw_breakpoint) {
        gbb_run_result r = gbb_run_ex(machine, 50000, trace, 8192,
                                       diagnostics, 32768);
        ticks += r.consumed_half_dots;
        for (size_t i = 0; i < r.diagnostic_count; ++i) {
            gbb_diagnostic_record *d = &diagnostics[i];
            if (d->kind != GBB_DIAGNOSTIC_BUS_READ &&
                d->kind != GBB_DIAGNOSTIC_BUS_WRITE) continue;
            if ((d->address >= 0x8000 && d->address <= 0x9fff) ||
                (d->address >= 0xff40 && d->address <= 0xff4b) ||
                (d->address >= 0xff68 && d->address <= 0xff6b)) ppu_access = 1;
        }
        for (size_t i = 0; i < r.trace_count; ++i) {
            gbb_trace_record *t = &trace[i];
            if (t->pc == callback) saw_callback = 1;
            if (t->pc != breakpoint || t->opcode[0] != 0x40) continue;
            saw_breakpoint = 1;
            int pass_regs = t->b == 3 && t->c == 5 && t->d == 8 &&
                t->e == 13 && t->h == 21 && t->l == 34;
            int fail_regs = t->b == 0x42 && t->c == 0x42 && t->d == 0x42 &&
                t->e == 0x42 && t->h == 0x42 && t->l == 0x42;
            if ((expect_failure && !fail_regs) || (!expect_failure && !pass_regs)) {
                fprintf(stderr, "wrong breakpoint registers at %04x\n", t->pc);
                return 1;
            }
        }
        if (ppu_access) { fprintf(stderr, "PPU bus access observed\n"); return 1; }
        if (saw_breakpoint) break;
        if (r.reason != GBB_STOP_BUDGET && r.reason != GBB_STOP_OUTPUT_FULL &&
            r.reason != GBB_STOP_TRACE_FULL) {
            fprintf(stderr, "core stopped before protocol: reason=%d ticks=%llu last_pc=%04x last_opcode=%02x last_a=%02x\n", r.reason, ticks,
                    r.trace_count ? trace[r.trace_count - 1].pc : 0,
                    r.trace_count ? trace[r.trace_count - 1].opcode[0] : 0,
                    r.trace_count ? trace[r.trace_count - 1].a : 0);
            return 1;
        }
        if (!r.consumed_half_dots && r.reason == GBB_STOP_BUDGET) break;
    }
    gbb_destroy(machine);
    printf("probe=%s callback=%d breakpoint=%d ppu_access=%d ticks=%llu\n",
           expect_failure ? "fail" : "pass", saw_callback, saw_breakpoint,
           ppu_access, ticks);
    return saw_callback && saw_breakpoint && !ppu_access ? 0 : 1;
}
C
cc -std=c17 -O2 -I include src/core/gabbaboy.c "$work_dir/probe.c" -o "$work_dir/probe"
symbol() {
  awk -v label="$2" '$2 == label { split($1, a, ":"); print a[2]; exit }' "$1"
}
for case_name in daa tim00 tim00_div_trigger; do
  case_dir="$work_dir/$case_name"
  symbols="$case_dir/rebuilt.sym"
  breakpoint=$(symbol "$symbols" 'quit@serial_dump')
  [[ -n "$breakpoint" ]] || { echo 'missing pinned breakpoint symbol' >&2; exit 1; }
  if [[ "$case_name" == daa ]]; then
    callback=$(symbol "$symbols" 'main@quit_inline_1')
  else
    callback=$(symbol "$symbols" 'check_asserts_cb')
  fi
  [[ -n "$callback" ]] || { echo "missing callback symbol: $case_name" >&2; exit 1; }
  "$work_dir/probe" "$case_dir/rebuilt.gb" "$callback" "$breakpoint" pass
done

# Deliberate negative control: corrupt the first DAA table's expected result
# in a private ROM copy. Upstream acceptance source and tracked patch are intact.
cp "$work_dir/daa/rebuilt.gb" "$work_dir/daa/negative.gb"
python3 - "$work_dir/daa/negative.gb" "$(symbol "$work_dir/daa/rebuilt.sym" testcases1)" <<'PY'
from pathlib import Path
import sys
rom = Path(sys.argv[1])
base = int(sys.argv[2], 16)
data = bytearray(rom.read_bytes())
assert data[base:base + 4] == bytes((0, 0, 0, 8))
data[base + 2] ^= 1
rom.write_bytes(data)
PY
negative_callback=$(symbol "$work_dir/daa/rebuilt.sym" 'fail@quit_inline_2')
"$work_dir/probe" "$work_dir/daa/negative.gb" "$negative_callback" \
  "$(symbol "$work_dir/daa/rebuilt.sym" 'quit@serial_dump')" fail
echo "Candidate probe evidence: $work_dir"
