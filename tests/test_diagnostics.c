#include "gabbaboy/gabbaboy.h"

#include <stdio.h>
#include <string.h>

#define REQUIRE(x) do { if (!(x)) { fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; } } while (0)

static gbb_instance *new_nop_machine(void) {
    uint8_t rom[32768] = {0};
    rom[0x100] = 0x00;
    uint8_t checksum = 0;
    for (size_t i = 0x134; i <= 0x14c; ++i) checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14d] = checksum;
    gbb_instance *machine = NULL;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) != GBB_OK ||
        gbb_load_rom(machine, rom, sizeof(rom)) != GBB_OK) {
        gbb_destroy(machine);
        return NULL;
    }
    return machine;
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    gbb_instance *machine = new_nop_machine();
    REQUIRE(machine != NULL);
    if (strcmp(argv[1], "diagnostics_zero") == 0) {
        gbb_run_result r = gbb_run_ex(machine, 8, NULL, 0, NULL, 0);
        REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 8 && r.diagnostic_count == 0);
    } else if (strcmp(argv[1], "diagnostics_exact") == 0) {
        gbb_diagnostic_record records[16] = {{0}};
        gbb_run_result r = gbb_run_ex(machine, 8, NULL, 0, records, 16);
        REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 8 && r.diagnostic_count == 1);
        REQUIRE(records[0].kind == GBB_DIAGNOSTIC_INSTRUCTION && records[0].pc == 0x100 && records[0].opcode == 0);
    } else if (strcmp(argv[1], "diagnostics_short") == 0) {
        gbb_diagnostic_record records[16] = {{0}};
        gbb_run_result r = gbb_run_ex(machine, 8, NULL, 0, records, 15);
        REQUIRE(r.reason == GBB_STOP_OUTPUT_FULL && r.consumed_half_dots == 0 && r.diagnostic_count == 0);
        gbb_trace_record trace[1] = {{0}};
        r = gbb_run(machine, 8, trace, 1);
        REQUIRE(r.consumed_half_dots == 8 && trace[0].pc == 0x100);
    } else if (strcmp(argv[1], "diagnostics_null") == 0) {
        gbb_run_result r = gbb_run_ex(machine, 8, NULL, 0, NULL, 1);
        REQUIRE(r.reason == GBB_STOP_INVALID_STATE && r.consumed_half_dots == 0);
    } else if (strcmp(argv[1], "diagnostics_canary") == 0) {
        struct { uint64_t before; gbb_diagnostic_record records[16]; uint64_t after; } guarded;
        memset(&guarded, 0, sizeof(guarded));
        guarded.before = UINT64_C(0x1122334455667788);
        guarded.after = UINT64_C(0x8877665544332211);
        gbb_run_result r = gbb_run_ex(machine, 8, NULL, 0, guarded.records, 16);
        REQUIRE(r.diagnostic_count == 1 && guarded.before == UINT64_C(0x1122334455667788));
        REQUIRE(guarded.after == UINT64_C(0x8877665544332211));
    } else { gbb_destroy(machine); return 2; }
    gbb_destroy(machine);
    return 0;
}
