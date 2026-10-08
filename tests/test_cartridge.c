#include "gabbaboy/gabbaboy.h"

#include <stdio.h>
#include <string.h>

#define REQUIRE(x) do { if (!(x)) { \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; \
} } while (0)

static void make_rom(uint8_t rom[32768], uint8_t cartridge_type,
                     const uint8_t *program, size_t program_size) {
    memset(rom, 0, 32768u);
    memcpy(rom + 0x100u, program, program_size);
    rom[0x147u] = cartridge_type;
    rom[0x148u] = 0u;
    rom[0x149u] = cartridge_type == 0x03u ? 0x02u : 0u;
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
}

static gbb_instance *new_machine(void) {
    gbb_instance *machine = NULL;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) != GBB_OK) return NULL;
    return machine;
}

static int cartridge_tracer(void) {
    /* Read and attempt a write while disabled, enable RAM, then write one byte. */
    static const uint8_t program[] = {
        0xFA, 0x00, 0xA0,             /* LD A,($A000): disabled reads as FF */
        0xEA, 0x00, 0xC0,             /* LD ($C000),A */
        0x3E, 0x99,                   /* LD A,$99 */
        0xEA, 0x00, 0xA0,             /* LD ($A000),A: disabled write ignored */
        0x3E, 0x0A,                   /* LD A,$0A */
        0xEA, 0x00, 0x00,             /* LD ($0000),A: enable RAM */
        0xFA, 0x00, 0xA0,             /* LD A,($A000): still FF */
        0xEA, 0x01, 0xC0,             /* LD ($C001),A */
        0x3E, 0x42,                   /* LD A,$42 */
        0xEA, 0x00, 0xA0,             /* LD ($A000),A */
        0x76                          /* HALT */
    };
    uint8_t rom[32768];
    make_rom(rom, 0x03u, program, sizeof(program));

    gbb_instance *machine = new_machine();
    REQUIRE(machine != NULL);
    REQUIRE(gbb_load_rom(machine, rom, sizeof(rom)) == GBB_OK);
    const gbb_run_result run = gbb_run(machine, 4096u, NULL, 0u);
    REQUIRE(run.reason == GBB_STOP_HALTED_IDLE);
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0xFFu);
    REQUIRE(gbb_peek_ram(machine, 0xC001u) == 0xFFu);

    size_t battery_size = 0u;
    uint64_t generation = 0u;
    uint8_t battery[8192];
    REQUIRE(gbb_battery_size(machine, &battery_size) == GBB_OK);
    REQUIRE(battery_size == sizeof(battery));
    REQUIRE(gbb_copy_battery(machine, battery, sizeof(battery)) == GBB_OK);
    REQUIRE(battery[0] == 0x42u);
    for (size_t i = 1u; i < sizeof(battery); ++i) REQUIRE(battery[i] == 0xFFu);
    REQUIRE(gbb_battery_generation(machine, &generation) == GBB_OK);
    REQUIRE(generation == 1u);

    gbb_instance *fresh = new_machine();
    REQUIRE(fresh != NULL);
    REQUIRE(gbb_load_rom(fresh, rom, sizeof(rom)) == GBB_OK);
    REQUIRE(gbb_import_battery(fresh, battery, sizeof(battery)) == GBB_OK);
    uint8_t restored[8192];
    REQUIRE(gbb_copy_battery(fresh, restored, sizeof(restored)) == GBB_OK);
    REQUIRE(memcmp(restored, battery, sizeof(battery)) == 0);

    /* ROM-only remains on the old path and never exposes battery RAM. */
    static const uint8_t rom_only_program[] = {
        0x3E, 0x3C,                   /* LD A,$3C */
        0xEA, 0x00, 0xC0,             /* LD ($C000),A */
        0x76                          /* HALT */
    };
    make_rom(rom, 0x00u, rom_only_program, sizeof(rom_only_program));
    REQUIRE(gbb_load_rom(fresh, rom, sizeof(rom)) == GBB_OK);
    const gbb_run_result rom_only_run = gbb_run(fresh, 4096u, NULL, 0u);
    REQUIRE(rom_only_run.reason == GBB_STOP_HALTED_IDLE);
    REQUIRE(gbb_peek_ram(fresh, 0xC000u) == 0x3Cu);
    REQUIRE(gbb_battery_size(fresh, &battery_size) == GBB_NO_BATTERY);

    gbb_destroy(fresh);
    gbb_destroy(machine);
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2 || strcmp(argv[1], "cartridge_tracer") != 0) return 2;
    return cartridge_tracer();
}
