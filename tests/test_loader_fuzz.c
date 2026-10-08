#include "gabbaboy/gabbaboy.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_ROM_BYTES (2u * 1024u * 1024u)
#define REQUIRE(x) do { if (!(x)) { \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; \
} } while (0)

static void fix_checksum(uint8_t *rom) {
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    FILE *file = fopen(argv[1], "rb");
    REQUIRE(file != NULL);
    REQUIRE(fseek(file, 0, SEEK_END) == 0);
    const long fixture_size = ftell(file);
    REQUIRE(fixture_size == 32768);
    REQUIRE(fseek(file, 0, SEEK_SET) == 0);
    uint8_t fixture[32768];
    REQUIRE(fread(fixture, 1u, sizeof(fixture), file) == sizeof(fixture));
    REQUIRE(fclose(file) == 0);

    uint8_t *maximum = calloc(MAX_ROM_BYTES, 1u);
    uint8_t *over = malloc(MAX_ROM_BYTES + 1u);
    REQUIRE(maximum != NULL && over != NULL);
    memcpy(maximum, fixture, sizeof(fixture));
    maximum[0x147u] = 0x01u;
    maximum[0x148u] = 0x06u;
    maximum[0x149u] = 0x00u;
    fix_checksum(maximum);
    memcpy(over, maximum, MAX_ROM_BYTES);
    over[MAX_ROM_BYTES] = 0xA5u;

    gbb_instance *machine = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) == GBB_OK);
    REQUIRE(gbb_load_rom(machine, fixture, sizeof(fixture)) == GBB_OK);
    REQUIRE(gbb_run(machine, 88u, NULL, 0u).consumed_half_dots == 88u);
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0x5Au);

    REQUIRE(gbb_load_rom(machine, NULL, sizeof(fixture)) == GBB_INVALID_ARGUMENT);
    REQUIRE(gbb_load_rom(machine, fixture, 0u) == GBB_INVALID_ARGUMENT);
    REQUIRE(gbb_load_rom(machine, fixture, 0x14Fu) == GBB_ROM_TRUNCATED);
    REQUIRE(gbb_load_rom(machine, fixture, sizeof(fixture) - 1u) == GBB_ROM_TRUNCATED);
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0x5Au);

    REQUIRE(gbb_load_rom(machine, maximum, MAX_ROM_BYTES) == GBB_OK);
    REQUIRE(gbb_load_rom(machine, over, MAX_ROM_BYTES + 1u) == GBB_ROM_TOO_LARGE);
    REQUIRE(gbb_load_rom(machine, over, SIZE_MAX) == GBB_ROM_TOO_LARGE);
    REQUIRE(gbb_run(machine, 4096u, NULL, 0u).reason == GBB_STOP_BUDGET);
    REQUIRE(gbb_peek_ram(machine, 0xC001u) == 0xA5u);

    gbb_destroy(machine);
    free(over);
    free(maximum);
    return 0;
}
