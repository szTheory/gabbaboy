#include "gabbaboy/gabbaboy.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define REQUIRE(x) do { if (!(x)) { \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; \
} } while (0)

/* Black-box battery-image and catch-up tests on synthetic MBC3 images. The guest
 * programs touch the clock through the cartridge bus only, then spin so emulated
 * time keeps advancing. No assembled fixture, no commercial data. */

#define HALF_DOTS_PER_SECOND (1ull << 23)
#define BLOCK GBB_RTC_BLOCK_SIZE

typedef struct {
    uint8_t bytes[1024];
    size_t used;
} program;

static void emit_write(program *p, uint16_t address, uint8_t value) {
    const uint8_t b[] = {0x3Eu, value, 0xEAu, (uint8_t)address, (uint8_t)(address >> 8)};
    memcpy(p->bytes + p->used, b, sizeof(b));
    p->used += sizeof(b);
}

/* JR -2: spin forever so the emulated clock keeps running. */
static void emit_spin(program *p) {
    p->bytes[p->used++] = 0x18u;
    p->bytes[p->used++] = 0xFEu;
}

static void fix_checksum(uint8_t *rom) {
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
}

static void build_rom(uint8_t *rom, uint8_t type, uint8_t ram_code, const program *p) {
    memset(rom, 0, 0x8000u);
    rom[0x147u] = type;
    rom[0x148u] = 0x00u;
    rom[0x149u] = ram_code;
    fix_checksum(rom);
    rom[0x100u] = 0xC3u;
    rom[0x101u] = 0x00u;
    rom[0x102u] = 0x02u;
    if (p != NULL) memcpy(rom + 0x200u, p->bytes, p->used);
}

static uint8_t g_rom[0x8000];

static gbb_instance *load_type(uint8_t type, uint8_t ram_code, const program *p) {
    build_rom(g_rom, type, ram_code, p);
    gbb_instance *machine = NULL;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) != GBB_OK) return NULL;
    if (gbb_load_rom(machine, g_rom, sizeof(g_rom)) != GBB_OK) {
        gbb_destroy(machine);
        return NULL;
    }
    return machine;
}

/* A fresh timer cartridge whose guest only opens the gate and spins. */
static gbb_instance *load_idle(uint8_t type, uint8_t ram_code) {
    program p = {{0}, 0u};
    emit_write(&p, 0x0000u, 0x0Au);
    emit_spin(&p);
    return load_type(type, ram_code, &p);
}

static int run_for(gbb_instance *machine, uint64_t half_dots) {
    uint64_t done = 0u;
    while (done < half_dots) {
        const gbb_run_result run = gbb_run(machine, half_dots - done, NULL, 0u);
        if (run.reason != GBB_STOP_BUDGET) return 0;
        if (run.consumed_half_dots == 0u) break; /* remainder is below one instruction */
        done += run.consumed_half_dots;
    }
    return 1;
}

static int export_image(const gbb_instance *machine, uint8_t *out, size_t capacity,
                        size_t *out_size) {
    if (gbb_battery_size(machine, out_size) != GBB_OK) return 0;
    if (*out_size > capacity) return 0;
    return gbb_copy_battery(machine, out, *out_size) == GBB_OK;
}

/* Guest: RAM byte $5A at A000 (bank 0), seconds 10, hours 5 (live). */
static program roundtrip_program(void) {
    program p = {{0}, 0u};
    emit_write(&p, 0x0000u, 0x0Au);
    emit_write(&p, 0x4000u, 0x00u);
    emit_write(&p, 0xA000u, 0x5Au);
    emit_write(&p, 0x4000u, 0x08u);
    emit_write(&p, 0xA000u, 10u);
    emit_write(&p, 0x4000u, 0x0Au);
    emit_write(&p, 0xA000u, 5u);
    emit_spin(&p);
    return p;
}

static int rtc_block_roundtrip(void) {
    program p = roundtrip_program();
    gbb_instance *source = load_type(0x10u, 0x02u, &p);
    REQUIRE(source != NULL);
    REQUIRE(run_for(source, 7u * HALF_DOTS_PER_SECOND / 2u));

    size_t size = 0u;
    uint8_t image[8192u + BLOCK];
    REQUIRE(export_image(source, image, sizeof(image), &size));
    REQUIRE(size == 8192u + BLOCK);
    REQUIRE(image[0] == 0x5Au);
    REQUIRE(memcmp(image + 8192u, "GBRT", 4u) == 0);
    REQUIRE(image[8192u + 4u] == 1u);
    REQUIRE(image[8192u + 9u] == 13u); /* 10 s plus 3.5 s of spinning */
    REQUIRE(image[8192u + 11u] == 5u);
    REQUIRE(image[8192u + 20u] == 0u);

    /* Two exports at the same emulated time are byte-identical. */
    uint8_t again[8192u + BLOCK];
    REQUIRE(export_image(source, again, sizeof(again), &size));
    REQUIRE(memcmp(image, again, sizeof(image)) == 0);

    /* A fresh instance imports it and exports the same bytes. */
    gbb_instance *fresh = load_idle(0x10u, 0x02u);
    REQUIRE(fresh != NULL);
    REQUIRE(gbb_import_battery(fresh, image, sizeof(image)) == GBB_OK);
    REQUIRE(export_image(fresh, again, sizeof(again), &size));
    REQUIRE(memcmp(image, again, sizeof(image)) == 0);

    /* Importing back into the source after more time never advances the clock. */
    REQUIRE(run_for(source, 2u * HALF_DOTS_PER_SECOND));
    REQUIRE(gbb_import_battery(source, image, sizeof(image)) == GBB_OK);
    REQUIRE(export_image(source, again, sizeof(again), &size));
    REQUIRE(memcmp(image, again, sizeof(image)) == 0);

    gbb_destroy(fresh);
    gbb_destroy(source);

    /* $0F has a timer and battery but no RAM: the image is the block alone. */
    gbb_instance *timer_only = load_idle(0x0Fu, 0x00u);
    REQUIRE(timer_only != NULL);
    REQUIRE(gbb_battery_size(timer_only, &size) == GBB_OK);
    REQUIRE(size == BLOCK);
    uint8_t block[BLOCK];
    REQUIRE(gbb_copy_battery(timer_only, block, sizeof(block)) == GBB_OK);
    REQUIRE(memcmp(block, "GBRT", 4u) == 0);
    gbb_destroy(timer_only);
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    if (strcmp(argv[1], "rtc_block_roundtrip") == 0) return rtc_block_roundtrip();
    return 2;
}
