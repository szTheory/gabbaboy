#include "gabbaboy/gabbaboy.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define REQUIRE(x) do { if (!(x)) { fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; } } while (0)

static uint8_t *read_rom(const char *path, size_t *size) {
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
    size_t size = 0; uint8_t *rom = read_rom(argv[2], &size);
    REQUIRE(rom != NULL);
    if (strcmp(argv[1], "failure") == 0) rom[0x154] = 0x00; /* Guest stores/reads the wrong RAM value. */
    if (strcmp(argv[1], "unsupported") == 0) rom[0x150] = 0xD3;
    gbb_instance *m = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &m) == GBB_OK);
    REQUIRE(gbb_load_rom(m, rom, size) == GBB_OK);
    gbb_trace_record *trace = calloc(16384, sizeof(*trace));
    REQUIRE(trace != NULL);
    size_t capacity = strcmp(argv[1], "trace") == 0 ? 1 : 16384;
    uint64_t budget = strcmp(argv[1], "timeout") == 0 ? 1 : UINT64_C(200000);
    gbb_run_result r = gbb_run(m, budget, trace, capacity);
    uint8_t marker = gbb_peek_ram(m, 0xA001);
    if (strcmp(argv[1], "success") == 0) {
        REQUIRE(marker == 0xA5 && r.reason == GBB_STOP_BUDGET && r.trace_count > 0);
    } else if (strcmp(argv[1], "failure") == 0) {
        REQUIRE(gbb_peek_ram(m, 0xA000) == 0x00);
        REQUIRE(marker == 0xEE && marker != 0xA5);
    } else if (strcmp(argv[1], "unsupported") == 0) {
        REQUIRE(r.reason == GBB_STOP_UNSUPPORTED_OPCODE && marker != 0xA5);
    } else if (strcmp(argv[1], "timeout") == 0) {
        REQUIRE(r.reason == GBB_STOP_BUDGET && r.consumed_half_dots == 0 && marker == 0);
    } else if (strcmp(argv[1], "trace") == 0) {
        REQUIRE(r.reason == GBB_STOP_TRACE_FULL && r.trace_count == 1 && marker != 0xA5);
    } else return 2;
    gbb_destroy(m); free(trace); free(rom); return 0;
}
