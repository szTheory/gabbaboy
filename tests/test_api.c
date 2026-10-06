#include "gabbaboy/gabbaboy.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define REQUIRE(x) do { if (!(x)) { fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; } } while (0)

static uint8_t *read_fixture(const char *path, size_t *size) {
    FILE *f = fopen(path, "rb");
    if (!f || fseek(f, 0, SEEK_END) != 0) return NULL;
    long n = ftell(f);
    if (n < 0 || fseek(f, 0, SEEK_SET) != 0) { fclose(f); return NULL; }
    uint8_t *p = malloc((size_t)n);
    if (!p || fread(p, 1, (size_t)n, f) != (size_t)n) { free(p); fclose(f); return NULL; }
    fclose(f); *size = (size_t)n; return p;
}

int main(int argc, char **argv) {
    if (argc != 3) return 2;
    size_t rom_size = 0;
    uint8_t *rom = read_fixture(argv[2], &rom_size);
    REQUIRE(rom != NULL);
    gbb_instance *a = NULL, *b = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &a) == GBB_OK);
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &b) == GBB_OK);
    REQUIRE(gbb_load_rom(a, rom, rom_size) == GBB_OK);
    REQUIRE(gbb_load_rom(b, rom, rom_size) == GBB_OK);
    if (strcmp(argv[1], "instance_lifecycle") == 0) {
        gbb_trace_record records[256];
        gbb_run_result first = gbb_run(a, 80, records, 256);
        REQUIRE(first.consumed_half_dots == 80 && first.trace_count > 0);
        REQUIRE(gbb_peek_ram(a, 0xC000) == 0x5A);
        REQUIRE(gbb_reset(a) == GBB_OK);
        REQUIRE(gbb_peek_ram(a, 0xC000) == 0);
        gbb_run_result reset = gbb_run(a, 32, records, 256);
        REQUIRE(reset.consumed_half_dots == 32 && records[0].pc == 0x0100 && records[0].time_half_dots == 0);
        gbb_destroy(a); gbb_destroy(b); free(rom); return 0;
    }
    if (strcmp(argv[1], "independent_instances") == 0) {
        REQUIRE(gbb_run(a, 80, NULL, 0).consumed_half_dots == 80);
        REQUIRE(gbb_peek_ram(a, 0xC000) == 0x5A);
        REQUIRE(gbb_peek_ram(b, 0xC000) == 0);
        REQUIRE(gbb_run(b, 32, NULL, 0).consumed_half_dots == 32);
        REQUIRE(gbb_peek_ram(b, 0xC000) == 0);
        gbb_destroy(a); gbb_destroy(b); free(rom); return 0;
    }
    if (strcmp(argv[1], "run_bounds") == 0) {
        gbb_run_result zero = gbb_run(a, 0, NULL, 0);
        REQUIRE(zero.reason == GBB_STOP_BUDGET && zero.consumed_half_dots == 0);
        gbb_run_result short_run = gbb_run(a, 31, NULL, 0);
        REQUIRE(short_run.reason == GBB_STOP_BUDGET && short_run.consumed_half_dots == 0);
        gbb_run_result exact = gbb_run(a, 32, NULL, 0);
        REQUIRE(exact.reason == GBB_STOP_BUDGET && exact.consumed_half_dots == 32);
        gbb_run_result enough = gbb_run(b, 33, NULL, 0);
        REQUIRE(enough.consumed_half_dots == 32 && enough.consumed_half_dots <= 33);
        gbb_destroy(a); gbb_destroy(b); free(rom); return 0;
    }
    if (strcmp(argv[1], "trace_capacity") == 0) {
        gbb_trace_record records[2] = {{0}};
        records[1].pc = 0xBEEF;
        gbb_run_result bad_pair = gbb_run(a, 32, NULL, 1);
        REQUIRE(bad_pair.reason == GBB_STOP_INVALID_STATE && bad_pair.consumed_half_dots == 0);
        gbb_run_result full = gbb_run(a, 64, records, 1);
        REQUIRE(full.reason == GBB_STOP_TRACE_FULL && full.trace_count == 1 && full.consumed_half_dots == 32);
        REQUIRE(records[1].pc == 0xBEEF);
        gbb_destroy(a); gbb_destroy(b); free(rom); return 0;
    }
    return 2;
}
