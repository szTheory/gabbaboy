#include "gabbaboy/gabbaboy.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define REQUIRE(x) do { if (!(x)) { \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; \
} } while (0)

/* Synthetic MBC2 images only: no assembled fixture, no commercial data. Bank
 * zero is never remapped on MBC2, so guest programs run straight from ROM. */

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

static void emit_raw(program *p, const uint8_t *b, size_t n) {
    memcpy(p->bytes + p->used, b, n);
    p->used += n;
}

static void emit_halt(program *p) { p->bytes[p->used++] = 0x76u; }

static void fix_checksum(uint8_t *rom) {
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
}

/* Bank n carries stamp 0x40 + n at offset $1000 inside the bank. */
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

/* Run in bounded slices until the guest halts; the slice cap bounds total work. */
static int run_to_halt(gbb_instance *machine) {
    for (int slice = 0; slice < 64; ++slice) {
        const gbb_run_result run = gbb_run(machine, 1u << 20, NULL, 0u);
        if (run.reason == GBB_STOP_HALTED_IDLE) return 1;
        if (run.reason != GBB_STOP_BUDGET) return 0;
    }
    return 0;
}

static int mbc2_tracer(void) {
    size_t size = 0u;
    uint8_t *rom = make_rom(1u, 0x06u, 0u, &size); /* 64 KiB, 4 banks */
    REQUIRE(rom != NULL);
    program p = {{0}, 0u};
    emit_write(&p, 0x0000u, 0x0Au); /* bit 8 clear: RAM enable */
    emit_write(&p, 0xA000u, 0xA5u);
    emit_read_to(&p, 0xA200u, 0xC000u); /* echoes cell 0 */
    emit_read_to(&p, 0xBE00u, 0xC001u);
    emit_write(&p, 0x2100u, 0x02u);     /* bit 8 set: ROM bank 2 */
    emit_read_to(&p, 0x5000u, 0xC002u);
    emit_halt(&p);
    install(rom, &p);

    gbb_instance *machine = new_machine();
    REQUIRE(machine != NULL);
    REQUIRE(gbb_load_rom(machine, rom, size) == GBB_OK);
    const gbb_run_result run = gbb_run(machine, 1u << 20, NULL, 0u);
    REQUIRE(run.reason == GBB_STOP_HALTED_IDLE);
    REQUIRE(gbb_peek_ram(machine, 0xC000u) == 0xF5u);
    REQUIRE(gbb_peek_ram(machine, 0xC001u) == 0xF5u);
    REQUIRE(gbb_peek_ram(machine, 0xC002u) == 0x42u);
    size_t battery = 0u;
    REQUIRE(gbb_battery_size(machine, &battery) == GBB_OK);
    REQUIRE(battery == 512u);
    uint8_t image[512];
    REQUIRE(gbb_copy_battery(machine, image, sizeof(image)) == GBB_OK);
    REQUIRE(image[0] == 0xF5u);
    REQUIRE(run_to_halt(machine));
    gbb_destroy(machine);
    free(rom);
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    if (strcmp(argv[1], "mbc2_tracer") == 0) return mbc2_tracer();
    return 2;
}
