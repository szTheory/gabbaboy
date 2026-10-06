#include "gabbaboy/gabbaboy.h"

#include <stdio.h>
#include <string.h>

#define REQUIRE(x) do { if (!(x)) { fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; } } while (0)

static void make_rom(uint8_t rom[32768], const uint8_t *program, size_t size) {
    memset(rom, 0, 32768);
    memcpy(rom + 0x100, program, size);
    uint8_t checksum = 0;
    for (size_t i = 0x134; i <= 0x14c; ++i) checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14d] = checksum;
}

static int call_stack(void) {
    uint8_t rom[32768];
    const uint8_t start[] = {0xcc, 0x50, 0x01, 0x00}; /* CALL Z,$0150; NOP */
    make_rom(rom, start, sizeof(start));
    rom[0x150] = 0xc9; /* RET */
    gbb_instance *m = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &m) == GBB_OK);
    REQUIRE(gbb_load_rom(m, rom, sizeof(rom)) == GBB_OK);
    gbb_trace_record trace[4] = {{0}};
    gbb_run_result r = gbb_run(m, 88, trace, 4);
    REQUIRE(r.reason == GBB_STOP_BUDGET);
    REQUIRE(r.consumed_half_dots == 88);
    REQUIRE(r.trace_count == 3);
    REQUIRE(trace[0].pc == 0x100 && trace[1].pc == 0x150 && trace[2].pc == 0x103);
    REQUIRE(gbb_peek_ram(m, 0xfffd) == 0x01);
    REQUIRE(gbb_peek_ram(m, 0xfffc) == 0x03);
    gbb_destroy(m);
    return 0;
}

static int conditional_budget(void) {
    uint8_t rom[32768];
    const uint8_t start[] = {0xc4, 0x50, 0x01}; /* CALL NZ,$0150; Z is set in post-boot state */
    make_rom(rom, start, sizeof(start));
    gbb_instance *m = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &m) == GBB_OK);
    REQUIRE(gbb_load_rom(m, rom, sizeof(rom)) == GBB_OK);
    gbb_trace_record trace[2] = {{0}};
    gbb_run_result r = gbb_run(m, 23, trace, 2);
    REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 0);
    REQUIRE(r.trace_count == 0);
    REQUIRE(gbb_peek_ram(m, 0xfffc) == 0 && gbb_peek_ram(m, 0xfffd) == 0);
    gbb_destroy(m);
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    if (strcmp(argv[1], "call_stack") == 0) return call_stack();
    if (strcmp(argv[1], "conditional_budget") == 0) return conditional_budget();
    return 2;
}
