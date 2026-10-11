#include "gabbaboy/gabbaboy.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define REQUIRE(x) do { if (!(x)) { \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; \
} } while (0)

/* Synthetic MBC3 images only: no assembled fixture, no commercial data. Bank
 * zero is never remapped, so guest programs run straight from ROM. */

typedef struct {
    uint8_t bytes[4096];
    size_t used;
} program;

static void emit_write(program *p, uint16_t address, uint8_t value) {
    const uint8_t b[] = {0x3Eu, value, 0xEAu, (uint8_t)address, (uint8_t)(address >> 8)};
    memcpy(p->bytes + p->used, b, sizeof(b));
    p->used += sizeof(b);
}

static void emit_read_to(program *p, uint16_t address, uint16_t destination) {
    const uint8_t b[] = {0xFAu, (uint8_t)address, (uint8_t)(address >> 8),
                         0xEAu, (uint8_t)destination, (uint8_t)(destination >> 8)};
    memcpy(p->bytes + p->used, b, sizeof(b));
    p->used += sizeof(b);
}

static void emit_halt(program *p) { p->bytes[p->used++] = 0x76u; }

static void fix_checksum(uint8_t *rom) {
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
}

/* Bank n carries stamp 0x40 + n (modulo 256) at offset $1000 inside the bank. */
static uint8_t *make_rom(uint8_t rom_code, uint8_t type, uint8_t ram_code,
                         size_t *out_size) {
    const size_t banks = (size_t)2u << rom_code;
    *out_size = banks * 0x4000u;
    uint8_t *rom = calloc(*out_size, 1u);
    if (rom == NULL) return NULL;
    for (size_t bank = 0u; bank < banks; ++bank)
        rom[bank * 0x4000u + 0x1000u] = (uint8_t)(0x40u + bank);
    rom[0x147u] = type;
    rom[0x148u] = rom_code;
    rom[0x149u] = ram_code;
    fix_checksum(rom);
    return rom;
}

/* JP $0200 from the entry point; the program lives past the header. */
static void install(uint8_t *rom, const program *p) {
    rom[0x100u] = 0xC3u;
    rom[0x101u] = 0x00u;
    rom[0x102u] = 0x02u;
    memcpy(rom + 0x200u, p->bytes, p->used);
}

static gbb_instance *new_machine(void) {
    gbb_instance *machine = NULL;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) != GBB_OK) return NULL;
    return machine;
}

/* Run in bounded slices; the slice cap bounds total work. Returns the stop reason
 * of the final slice, or -1 when the guest never settled. */
static int run_until_stop(gbb_instance *machine) {
    for (int slice = 0; slice < 64; ++slice) {
        const gbb_run_result run = gbb_run(machine, 1u << 20, NULL, 0u);
        if (run.reason != GBB_STOP_BUDGET) return (int)run.reason;
    }
    return -1;
}

static int run_to_halt(gbb_instance *machine) {
    return run_until_stop(machine) == (int)GBB_STOP_HALTED_IDLE;
}

static gbb_instance *load_program(uint8_t rom_code, uint8_t type, uint8_t ram_code,
                                  const program *p) {
    size_t size = 0u;
    uint8_t *rom = make_rom(rom_code, type, ram_code, &size);
    if (rom == NULL) return NULL;
    install(rom, p);
    gbb_instance *machine = new_machine();
    if (machine != NULL && gbb_load_rom(machine, rom, size) != GBB_OK) {
        gbb_destroy(machine);
        machine = NULL;
    }
    free(rom);
    return machine;
}

static int mbc3_tracer(void) {
    program p = {{0}, 0u};
    emit_write(&p, 0x0000u, 0x0Au);     /* RAM and RTC enable */
    emit_write(&p, 0x2000u, 0x7Fu);
    emit_read_to(&p, 0x5000u, 0xC000u); /* bank 127 stamp */
    emit_write(&p, 0x2000u, 0x80u);     /* bit 7 ignored: 0, which becomes 1 */
    emit_read_to(&p, 0x5000u, 0xC001u);
    emit_write(&p, 0x4000u, 0x02u);     /* RAM bank 2 */
    emit_write(&p, 0xA123u, 0xA5u);
    emit_write(&p, 0x4000u, 0x00u);
    emit_read_to(&p, 0xA123u, 0xC002u); /* bank 0 is untouched */
    emit_write(&p, 0x4000u, 0x02u);
    emit_read_to(&p, 0xA123u, 0xC003u);
    emit_halt(&p);

    gbb_instance *machine = load_program(6u, 0x13u, 0x03u, &p); /* 2 MiB, 32 KiB RAM */
    REQUIRE(machine != NULL);
    REQUIRE(run_to_halt(machine));
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == (uint8_t)(0x40u + 0x7Fu));
    REQUIRE(gbb_peek_ram(machine, 0xC001u) == 0x41u);
    REQUIRE(gbb_peek_ram(machine, 0xC002u) == 0xFFu);
    REQUIRE(gbb_peek_ram(machine, 0xC003u) == 0xA5u);
    gbb_destroy(machine);
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    if (strcmp(argv[1], "mbc3_tracer") == 0) return mbc3_tracer();
    return 2;
}
