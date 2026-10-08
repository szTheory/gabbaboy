#include "gabbaboy/gabbaboy.h"

#include <stdio.h>
#include <stdlib.h>
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

static void fix_checksum(uint8_t *rom) {
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
}

static uint8_t *make_banked_rom(uint8_t rom_size_code, uint8_t type,
                                uint8_t ram_size_code) {
    const size_t bank_count = (size_t)2u << rom_size_code;
    const size_t size = bank_count * 0x4000u;
    uint8_t *rom = malloc(size);
    if (rom == NULL) return NULL;
    memset(rom, 0, size);
    for (size_t bank = 0u; bank < bank_count; ++bank)
        rom[bank * 0x4000u + 0x1000u] = (uint8_t)bank;
    rom[0x147u] = type;
    rom[0x148u] = rom_size_code;
    rom[0x149u] = ram_size_code;
    fix_checksum(rom);
    return rom;
}

static void emit_mapper_write(uint8_t program[64], size_t *used,
                              uint16_t address, uint8_t value) {
    const uint8_t bytes[] = {0x3Eu, value, 0xEAu,
        (uint8_t)address, (uint8_t)(address >> 8)};
    memcpy(program + *used, bytes, sizeof(bytes));
    *used += sizeof(bytes);
}

static void emit_guest_read(uint8_t program[64], size_t *used,
                            uint16_t address, uint16_t destination) {
    const uint8_t bytes[] = {0xFAu, (uint8_t)address,
        (uint8_t)(address >> 8), 0xEAu, (uint8_t)destination,
        (uint8_t)(destination >> 8)};
    memcpy(program + *used, bytes, sizeof(bytes));
    *used += sizeof(bytes);
}

static int run_bank_case(uint8_t rom_size_code, uint8_t low, uint8_t high,
                         uint8_t mode, uint8_t expected_lower,
                         uint8_t expected_upper) {
    uint8_t *rom = make_banked_rom(rom_size_code, 0x01u, 0u);
    REQUIRE(rom != NULL);
    uint8_t program[64];
    size_t used = 0u;
    emit_mapper_write(program, &used, 0x2000u, low);
    emit_mapper_write(program, &used, 0x4000u, high);
    emit_mapper_write(program, &used, 0x6000u, mode);
    emit_guest_read(program, &used, 0x1000u, 0xC100u);
    emit_guest_read(program, &used, 0x5000u, 0xC101u);
    program[used++] = 0x76u;

    /* Copy the mapper probe to WRAM before mode 1 can remap bank zero. */
    uint8_t bootstrap[256];
    size_t bootstrap_size = 0u;
    for (size_t i = 0u; i < used; ++i) {
        bootstrap[bootstrap_size++] = 0x3Eu;
        bootstrap[bootstrap_size++] = program[i];
        bootstrap[bootstrap_size++] = 0xEAu;
        const uint16_t destination = (uint16_t)(0xC000u + i);
        bootstrap[bootstrap_size++] = (uint8_t)destination;
        bootstrap[bootstrap_size++] = (uint8_t)(destination >> 8);
    }
    bootstrap[bootstrap_size++] = 0xC3u;
    bootstrap[bootstrap_size++] = 0x00u;
    bootstrap[bootstrap_size++] = 0xC0u;
    rom[0x100u] = 0xC3u; /* JP $0200 keeps the guest program clear of header bytes. */
    rom[0x101u] = 0x00u;
    rom[0x102u] = 0x02u;
    memcpy(rom + 0x200u, bootstrap, bootstrap_size);
    fix_checksum(rom);

    gbb_instance *machine = new_machine();
    REQUIRE(machine != NULL);
    const size_t rom_size = ((size_t)2u << rom_size_code) * 0x4000u;
    REQUIRE(gbb_load_rom(machine, rom, rom_size) == GBB_OK);
    const gbb_run_result run = gbb_run(machine, 4096u, NULL, 0u);
    REQUIRE(run.reason == GBB_STOP_HALTED_IDLE);
    REQUIRE(gbb_peek_ram(machine, 0xC100u) == expected_lower);
    REQUIRE(gbb_peek_ram(machine, 0xC101u) == expected_upper);
    gbb_destroy(machine);
    free(rom);
    return 0;
}

static int cartridge_bank_matrix(void) {
    /* Low-bank zero is translated before the physical ROM address mask. */
    REQUIRE(run_bank_case(0u, 0u, 0u, 0u, 0u, 1u) == 0);
    /* Small ROMs disconnect upper-bank lines; mode 1 also selects the lower window. */
    REQUIRE(run_bank_case(2u, 3u, 2u, 1u, 0u, 3u) == 0);
    REQUIRE(run_bank_case(5u, 3u, 1u, 1u, 32u, 35u) == 0);
    /* 2 MiB exposes all seven bank bits, including translated low-bank zero. */
    REQUIRE(run_bank_case(6u, 0u, 3u, 1u, 96u, 97u) == 0);
    REQUIRE(run_bank_case(6u, 31u, 3u, 0u, 0u, 127u) == 0);
    return 0;
}

static int run_ram_bank_case(uint8_t rom_size_code, uint8_t ram_size_code,
                             uint8_t expected_bank0, uint8_t expected_bank2) {
    uint8_t *rom = make_banked_rom(rom_size_code, 0x03u, ram_size_code);
    REQUIRE(rom != NULL);
    uint8_t program[64];
    size_t used = 0u;
    emit_mapper_write(program, &used, 0x0000u, 0x0Au);
    emit_mapper_write(program, &used, 0x6000u, 1u);
    emit_mapper_write(program, &used, 0x4000u, 2u);
    emit_mapper_write(program, &used, 0x0000u, 0x00u); /* disable RAM */
    emit_mapper_write(program, &used, 0x0000u, 0x1Au); /* low nibble enables */
    program[used++] = 0x3Eu;
    program[used++] = 0x5Au;
    program[used++] = 0xEAu;
    program[used++] = 0x00u;
    program[used++] = 0xA0u;
    emit_mapper_write(program, &used, 0x4000u, 0u);
    emit_guest_read(program, &used, 0xA000u, 0xC100u);
    emit_mapper_write(program, &used, 0x4000u, 2u);
    emit_guest_read(program, &used, 0xA000u, 0xC101u);
    program[used++] = 0x76u;

    uint8_t bootstrap[320];
    size_t bootstrap_size = 0u;
    for (size_t i = 0u; i < used; ++i) {
        bootstrap[bootstrap_size++] = 0x3Eu;
        bootstrap[bootstrap_size++] = program[i];
        bootstrap[bootstrap_size++] = 0xEAu;
        const uint16_t destination = (uint16_t)(0xC000u + i);
        bootstrap[bootstrap_size++] = (uint8_t)destination;
        bootstrap[bootstrap_size++] = (uint8_t)(destination >> 8);
    }
    bootstrap[bootstrap_size++] = 0xC3u;
    bootstrap[bootstrap_size++] = 0x00u;
    bootstrap[bootstrap_size++] = 0xC0u;
    rom[0x100u] = 0xC3u;
    rom[0x101u] = 0x00u;
    rom[0x102u] = 0x02u;
    memcpy(rom + 0x200u, bootstrap, bootstrap_size);
    fix_checksum(rom);

    gbb_instance *machine = new_machine();
    REQUIRE(machine != NULL);
    const size_t rom_size = ((size_t)2u << rom_size_code) * 0x4000u;
    REQUIRE(gbb_load_rom(machine, rom, rom_size) == GBB_OK);
    REQUIRE(gbb_run(machine, 8192u, NULL, 0u).reason == GBB_STOP_HALTED_IDLE);
    REQUIRE(gbb_peek_ram(machine, 0xC100u) == expected_bank0);
    REQUIRE(gbb_peek_ram(machine, 0xC101u) == expected_bank2);
    gbb_destroy(machine);
    free(rom);
    return 0;
}

static int cartridge_ram_banks(void) {
    /* 8 KiB RAM mirrors across the two-bit RAM bank selector. */
    REQUIRE(run_ram_bank_case(0u, 0x02u, 0x5Au, 0x5Au) == 0);
    /* 32 KiB RAM selects independent 8 KiB banks in mode 1. */
    REQUIRE(run_ram_bank_case(4u, 0x03u, 0xFFu, 0x5Au) == 0);
    return 0;
}

static int cartridge_no_ram_reads(void) {
    static const uint8_t program[] = {
        0xFA, 0x00, 0xA0,             /* no external RAM: deterministic FF read */
        0xEA, 0x00, 0xC0,
        0x3E, 0x0A,
        0xEA, 0x00, 0x00,             /* enable writes even though RAM is absent */
        0x3E, 0x55,
        0xEA, 0x00, 0xA0,
        0xFA, 0x00, 0xA0,
        0xEA, 0x01, 0xC0,
        0x76
    };
    uint8_t rom[32768];
    make_rom(rom, 0x01u, program, sizeof(program));
    gbb_instance *machine = new_machine();
    REQUIRE(machine != NULL);
    REQUIRE(gbb_load_rom(machine, rom, sizeof(rom)) == GBB_OK);
    REQUIRE(gbb_run(machine, 4096u, NULL, 0u).reason == GBB_STOP_HALTED_IDLE);
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0xFFu);
    REQUIRE(gbb_peek_ram(machine, 0xC001u) == 0xFFu);
    gbb_destroy(machine);
    return 0;
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
    if (argc != 2) return 2;
    if (strcmp(argv[1], "cartridge_tracer") == 0) return cartridge_tracer();
    if (strcmp(argv[1], "cartridge_bank_matrix") == 0) return cartridge_bank_matrix();
    if (strcmp(argv[1], "cartridge_ram_banks") == 0) return cartridge_ram_banks();
    if (strcmp(argv[1], "cartridge_no_ram_reads") == 0) return cartridge_no_ram_reads();
    return 2;
}
