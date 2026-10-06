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

static void fix_header_checksum(uint8_t *rom) {
    uint8_t sum = 0;
    for (size_t i = 0x134; i <= 0x14C; ++i) sum = (uint8_t)(sum - rom[i] - 1u);
    rom[0x14D] = sum;
}

int main(int argc, char **argv) {
    if (argc != 3) return 2;
    size_t size = 0; uint8_t *rom = read_rom(argv[2], &size);
    REQUIRE(rom != NULL && size == 32768);
    gbb_instance *m = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &m) == GBB_OK);
    REQUIRE(gbb_load_rom(m, rom, size) == GBB_OK);
    size_t allocation_size = 8u * 1024u * 1024u + 1u;
    uint8_t *bad = malloc(allocation_size);
    REQUIRE(bad != NULL);
    memcpy(bad, rom, size);
    gbb_error expected = GBB_INVALID_ROM;
    size_t bad_size = size;
    if (strcmp(argv[1], "truncated") == 0) { bad_size = 0x14F; expected = GBB_ROM_TRUNCATED; }
    else if (strcmp(argv[1], "oversized") == 0) { bad_size = allocation_size; expected = GBB_ROM_TOO_LARGE; }
    else if (strcmp(argv[1], "invalid_header") == 0) { bad[0x134] ^= 1; expected = GBB_INVALID_ROM; }
    else if (strcmp(argv[1], "unsupported_cartridge") == 0) { bad[0x147] = 1; fix_header_checksum(bad); expected = GBB_UNSUPPORTED_CARTRIDGE; }
    else if (strcmp(argv[1], "unsupported_rom_size") == 0) { bad[0x148] = 9; fix_header_checksum(bad); expected = GBB_UNSUPPORTED_ROM_SIZE; }
    else if (strcmp(argv[1], "unsupported_declared_size") == 0) {
        bad_size = 64u * 1024u;
        memset(bad, 0, bad_size);
        memcpy(bad, rom, size);
        bad[0x148] = 1;
        fix_header_checksum(bad);
        expected = GBB_UNSUPPORTED_ROM_SIZE;
    }
    else if (strcmp(argv[1], "unsupported_ram_size") == 0) { bad[0x149] = 1; fix_header_checksum(bad); expected = GBB_UNSUPPORTED_RAM_SIZE; }
    else if (strcmp(argv[1], "length_mismatch") == 0) { bad_size = size - 1; expected = GBB_ROM_TRUNCATED; }
    else if (strcmp(argv[1], "excess_actual") == 0) { bad[size] = 0; bad_size = size + 1; expected = GBB_ROM_SIZE_MISMATCH; }
    else if (strcmp(argv[1], "null_arguments") == 0) {
        REQUIRE(gbb_load_rom(m, NULL, size) == GBB_INVALID_ARGUMENT);
        REQUIRE(gbb_load_rom(m, rom, 0) == GBB_INVALID_ARGUMENT);
        REQUIRE(gbb_peek_ram(m, 0xC000) == 0);
        gbb_destroy(m); free(rom); free(bad); return 0;
    }
    else if (strcmp(argv[1], "non_destructive") == 0) { bad[0x147] = 1; fix_header_checksum(bad); expected = GBB_UNSUPPORTED_CARTRIDGE; }
    else return 2;
    REQUIRE(gbb_run(m, 80, NULL, 0).consumed_half_dots == 80);
    REQUIRE(gbb_peek_ram(m, 0xC000) == 0x5A);
    REQUIRE(gbb_load_rom(m, bad, bad_size) == expected);
    REQUIRE(gbb_peek_ram(m, 0xC000) == 0x5A);
    if (strcmp(argv[1], "non_destructive") == 0 || strcmp(argv[1], "unsupported_declared_size") == 0) {
        gbb_run_result result = gbb_run(m, 4096, NULL, 0);
        REQUIRE(result.reason == GBB_STOP_BUDGET);
        REQUIRE(gbb_peek_ram(m, 0xC001) == 0xA5);
    }
    gbb_destroy(m); free(rom); free(bad); return 0;
}
