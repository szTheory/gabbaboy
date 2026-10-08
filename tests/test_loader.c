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

static void make_mbc1_header(uint8_t *candidate, size_t size,
                             const uint8_t base_rom[32768], uint8_t type,
                             uint8_t rom_code, uint8_t ram_code) {
    memset(candidate, 0, size);
    memcpy(candidate, base_rom, 32768u);
    candidate[0x147u] = type;
    candidate[0x148u] = rom_code;
    candidate[0x149u] = ram_code;
    fix_header_checksum(candidate);
}

static int mbc1_header_matrix(const uint8_t base_rom[32768], uint8_t *candidate,
                              size_t capacity) {
    gbb_instance *machine = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) == GBB_OK);
    REQUIRE(gbb_load_rom(machine, base_rom, 32768u) == GBB_OK);
    for (uint8_t code = 0u; code <= 6u; ++code) {
        const size_t size = ((size_t)32768u << code);
        REQUIRE(size <= capacity);
        const struct { uint8_t type, ram_code; } valid[] = {
            {0x01u, 0u}, {0x02u, 0x02u}, {0x03u, 0x02u}
        };
        for (size_t i = 0u; i < sizeof(valid) / sizeof(valid[0]); ++i) {
            make_mbc1_header(candidate, size, base_rom, valid[i].type, code,
                             valid[i].ram_code);
            REQUIRE(gbb_load_rom(machine, candidate, size) == GBB_OK);
        }
        if (code <= 4u) {
            for (uint8_t type = 0x02u; type <= 0x03u; ++type) {
                make_mbc1_header(candidate, size, base_rom, type, code, 0x03u);
                REQUIRE(gbb_load_rom(machine, candidate, size) == GBB_OK);
            }
        } else {
            for (uint8_t type = 0x02u; type <= 0x03u; ++type) {
                make_mbc1_header(candidate, size, base_rom, type, code, 0x03u);
                REQUIRE(gbb_load_rom(machine, candidate, size) == GBB_UNSUPPORTED_RAM_SIZE);
            }
        }
    }

    REQUIRE(gbb_load_rom(machine, base_rom, 32768u) == GBB_OK);
    REQUIRE(gbb_run(machine, 88u, NULL, 0u).consumed_half_dots == 88u);
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0x5Au);
    const struct { uint8_t type, code, ram; gbb_error result; } invalid[] = {
        {0x01u, 0u, 0x02u, GBB_UNSUPPORTED_RAM_SIZE},
        {0x02u, 0u, 0u, GBB_UNSUPPORTED_RAM_SIZE},
        {0x03u, 0u, 0x01u, GBB_UNSUPPORTED_RAM_SIZE},
        {0x04u, 0u, 0u, GBB_UNSUPPORTED_CARTRIDGE},
        {0x01u, 7u, 0u, GBB_UNSUPPORTED_ROM_SIZE},
        {0x03u, 0x52u, 0x02u, GBB_UNSUPPORTED_ROM_SIZE}
    };
    for (size_t i = 0u; i < sizeof(invalid) / sizeof(invalid[0]); ++i) {
        make_mbc1_header(candidate, 32768u, base_rom, invalid[i].type,
                         invalid[i].code, invalid[i].ram);
        REQUIRE(gbb_load_rom(machine, candidate, 32768u) == invalid[i].result);
        REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0x5Au);
    }
    REQUIRE(gbb_run(machine, 4096u, NULL, 0u).reason == GBB_STOP_BUDGET);
    REQUIRE(gbb_peek_ram(machine, 0xC001u) == 0xA5u);
    gbb_destroy(machine);
    return 0;
}

static int mbc1m_variant_rejected(gbb_instance *machine,
                                  const uint8_t base_rom[32768],
                                  uint8_t *candidate) {
    static const uint8_t canonical_logo[48] = {
        0xCEu,0xEDu,0x66u,0x66u,0xCCu,0x0Du,0x00u,0x0Bu,
        0x03u,0x73u,0x00u,0x83u,0x00u,0x0Cu,0x00u,0x0Du,
        0x00u,0x08u,0x11u,0x1Fu,0x88u,0x89u,0x00u,0x0Eu,
        0xDCu,0xCCu,0x6Eu,0xE6u,0xDDu,0xDDu,0xD9u,0x99u,
        0xBBu,0xBBu,0x67u,0x63u,0x6Eu,0x0Eu,0xECu,0xCCu,
        0xDDu,0xDCu,0x99u,0x9Fu,0xBBu,0xB9u,0x33u,0x3Eu
    };
    const size_t size = 512u * 1024u;
    make_mbc1_header(candidate, size, base_rom, 0x03u, 0x04u, 0x02u);
    const size_t bank16 = 0x10u * 0x4000u;
    memcpy(candidate + bank16 + 0x104u, canonical_logo, sizeof(canonical_logo));
    candidate[bank16 + 0x147u] = 0x03u;
    candidate[bank16 + 0x148u] = 0x04u;
    candidate[bank16 + 0x149u] = 0x02u;
    fix_header_checksum(candidate + bank16);
    fix_header_checksum(candidate);
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0u);
    REQUIRE(gbb_run(machine, 88u, NULL, 0u).consumed_half_dots == 88u);
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0x5Au);
    REQUIRE(gbb_load_rom(machine, candidate, size) == GBB_UNSUPPORTED_CARTRIDGE_VARIANT);
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0x5Au);
    REQUIRE(gbb_run(machine, 4096u, NULL, 0u).reason == GBB_STOP_BUDGET);
    REQUIRE(gbb_peek_ram(machine, 0xC001u) == 0xA5u);
    return 0;
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
    if (strcmp(argv[1], "mbc1_matrix") == 0) {
        const int result = mbc1_header_matrix(rom, bad, allocation_size);
        gbb_destroy(m); free(rom); free(bad); return result;
    }
    if (strcmp(argv[1], "mbc1m_variant") == 0) {
        const int result = mbc1m_variant_rejected(m, rom, bad);
        gbb_destroy(m); free(rom); free(bad); return result;
    }
    gbb_error expected = GBB_INVALID_ROM;
    size_t bad_size = size;
    if (strcmp(argv[1], "truncated") == 0) { bad_size = 0x14F; expected = GBB_ROM_TRUNCATED; }
    else if (strcmp(argv[1], "oversized") == 0) { bad_size = allocation_size; expected = GBB_ROM_TOO_LARGE; }
    else if (strcmp(argv[1], "invalid_header") == 0) { bad[0x134] ^= 1; expected = GBB_INVALID_ROM; }
    else if (strcmp(argv[1], "unsupported_cartridge") == 0) { bad[0x147] = 4; fix_header_checksum(bad); expected = GBB_UNSUPPORTED_CARTRIDGE; }
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
    else if (strcmp(argv[1], "non_destructive") == 0) { bad[0x147] = 4; fix_header_checksum(bad); expected = GBB_UNSUPPORTED_CARTRIDGE; }
    else return 2;
    REQUIRE(gbb_run(m, 88, NULL, 0).consumed_half_dots == 88);
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
