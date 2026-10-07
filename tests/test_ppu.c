#include "gabbaboy/gabbaboy.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define WIDTH 160u
#define HEIGHT 144u
#define PIXELS (WIDTH * HEIGHT)
#define REQUIRE(x) do { if (!(x)) { \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; \
} } while (0)

typedef struct {
    uint8_t bytes[4096];
    size_t size;
} guest_program;

static void emit(guest_program *p, uint8_t byte) {
    if (p->size < sizeof(p->bytes)) p->bytes[p->size++] = byte;
}

static void emit_reg(guest_program *p, uint8_t address, uint8_t value) {
    emit(p, 0x3E); emit(p, value);       /* LD A,n */
    emit(p, 0xE0); emit(p, address);     /* LDH [n],A */
}

static void emit_bytes(guest_program *p, uint16_t address,
                       const uint8_t *bytes, size_t count) {
    emit(p, 0x21); emit(p, (uint8_t)address); emit(p, (uint8_t)(address >> 8));
    for (size_t i = 0; i < count; ++i) {
        emit(p, 0x3E); emit(p, bytes[i]);
        emit(p, 0x22);                 /* LD [HL+],A */
    }
}

static void emit_solid_tile(guest_program *p, uint16_t address, uint8_t color) {
    uint8_t data[16];
    for (unsigned row = 0; row < 8; ++row) {
        data[row * 2u] = (color & 1u) != 0 ? 0xFFu : 0u;
        data[row * 2u + 1u] = (color & 2u) != 0 ? 0xFFu : 0u;
    }
    emit_bytes(p, address, data, sizeof(data));
}

static void emit_row_tile(guest_program *p, uint16_t address,
                          unsigned row, uint8_t color, uint8_t mask) {
    uint8_t data[16] = {0};
    data[row * 2u] = (color & 1u) != 0 ? mask : 0u;
    data[row * 2u + 1u] = (color & 2u) != 0 ? mask : 0u;
    emit_bytes(p, address, data, sizeof(data));
}

static void start_guest(guest_program *p) {
    p->size = 0;
    emit(p, 0xAF);                     /* XOR A */
    emit(p, 0xE0); emit(p, 0x40);      /* LCD off while VRAM/OAM are authored */
}

static gbb_instance *load_guest(const guest_program *p, uint8_t lcdc) {
    if (p->size > sizeof(p->bytes) - 4u) return NULL;
    uint8_t rom[32768] = {0};
    /* Keep the guest body beyond the cartridge header and checksum bytes. */
    rom[0x100] = 0xC3; rom[0x101] = 0x50; rom[0x102] = 0x01;
    guest_program complete = *p;
    emit_reg(&complete, 0x40, lcdc);
    /* The LCDC write above must occur before the steady-state loop. */
    memcpy(rom + 0x150, complete.bytes, complete.size);
    size_t pc = 0x150u + complete.size;
    rom[pc++] = 0x18; rom[pc++] = 0xFE;
    rom[0x134] = 0xE7;
    uint8_t checksum = 0;
    for (size_t i = 0x134; i <= 0x14C; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14D] = checksum;

    gbb_instance *machine = NULL;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &machine) != GBB_OK ||
        gbb_load_rom(machine, rom, sizeof(rom)) != GBB_OK) {
        gbb_destroy(machine);
        return NULL;
    }
    return machine;
}

static int copy_completed_frame(gbb_instance *machine, uint8_t pixels[PIXELS]) {
    gbb_run_result run = gbb_run(machine, UINT64_C(180000), NULL, 0);
    if (run.reason != GBB_STOP_BUDGET) {
        fprintf(stderr, "guest stopped: reason=%d consumed=%llu\n", run.reason,
                (unsigned long long)run.consumed_half_dots);
        return 1;
    }
    gbb_frame_info info = {0};
    gbb_error error = gbb_copy_frame(machine, pixels, PIXELS, WIDTH, &info);
    if (error != GBB_OK || info.width != WIDTH || info.height != HEIGHT || info.generation == 0) {
        fprintf(stderr, "completed frame unavailable: error=%d generation=%llu\n", error,
                (unsigned long long)info.generation);
        return 1;
    }
    return 0;
}

static int compare_image(const char *name, const uint8_t actual[PIXELS],
                         const uint8_t expected[PIXELS]) {
    for (unsigned y = 0; y < HEIGHT; ++y) {
        for (unsigned x = 0; x < WIDTH; ++x) {
            size_t i = (size_t)y * WIDTH + x;
            if (actual[i] != expected[i]) {
                fprintf(stderr, "%s pixel (%u,%u): got %u expected %u\n",
                        name, x, y, actual[i], expected[i]);
                return 1;
            }
        }
    }
    return 0;
}

static int run_image(const char *name, guest_program *p, uint8_t lcdc,
                     const uint8_t expected[PIXELS], int test_reset) {
    gbb_instance *machine = load_guest(p, lcdc);
    REQUIRE(machine != NULL);
    uint8_t actual[PIXELS], repeated[PIXELS];
    REQUIRE(copy_completed_frame(machine, actual) == 0);
    REQUIRE(compare_image(name, actual, expected) == 0);
    gbb_frame_info info = {0};
    REQUIRE(gbb_copy_frame(machine, repeated, PIXELS, WIDTH, &info) == GBB_OK);
    REQUIRE(memcmp(actual, repeated, sizeof(actual)) == 0);
    if (test_reset) {
        REQUIRE(gbb_reset(machine) == GBB_OK);
        REQUIRE(copy_completed_frame(machine, repeated) == 0);
        REQUIRE(compare_image("reset", repeated, expected) == 0);
    }
    gbb_destroy(machine);
    return 0;
}

static int frame_composition_bg(void) {
    guest_program p = {0};
    uint8_t expected[PIXELS];

    /* Signed mode: tile 0 is fetched at $9000; SCX/SCY wrap to map row/column 31. */
    start_guest(&p);
    emit_solid_tile(&p, 0x9000, 3);
    emit_solid_tile(&p, 0x9010, 1);
    emit_solid_tile(&p, 0x8020, 2);    /* wrong BG map has a visibly different tile */
    const uint8_t map31_0 = 1, map31_31 = 0, other_map31_31 = 2;
    emit_bytes(&p, 0x9FE0, &map31_0, 1);
    emit_bytes(&p, 0x9FFF, &map31_31, 1);
    emit_bytes(&p, 0x9BFF, &other_map31_31, 1);
    emit_reg(&p, 0x47, 0x93);          /* color IDs 0,1,2,3 -> shades 3,0,1,2 */
    emit_reg(&p, 0x42, 255);
    emit_reg(&p, 0x43, 255);
    memset(expected, 2, sizeof(expected));
    memset(expected, 0, 9);            /* row 0, wrapped into map cell (31,0) */
    expected[0] = 2;                   /* signed tile 0 at $9000, palette color 3 */
    expected[9] = 2;                   /* wraps into map cell (0,1), tile 0 */
    REQUIRE(run_image("bg_signed_wrap_map_palette", &p, 0x89, expected, 1) == 0);

    /* Unsigned mode: tile 0 is fetched at $8000 and map $9C00 is selected. */
    memset(&p, 0, sizeof(p));
    start_guest(&p);
    emit_solid_tile(&p, 0x8000, 2);
    emit_solid_tile(&p, 0x8010, 1);
    const uint8_t selected = 0, alternate = 1;
    emit_bytes(&p, 0x9C00, &selected, 1);
    emit_bytes(&p, 0x9800, &alternate, 1);
    emit_reg(&p, 0x47, 0xE4);
    memset(expected, 2, sizeof(expected));
    REQUIRE(run_image("bg_unsigned_map_select", &p, 0x99, expected, 0) == 0);
    return 0;
}

static int frame_composition_window(void) {
    guest_program p = {0};
    uint8_t expected[PIXELS];
    start_guest(&p);
    emit_solid_tile(&p, 0x8000, 1);    /* BG tile 0 */
    uint8_t window_tile_data[16] = {0};
    window_tile_data[1] = 0xFF;        /* row 0: color 2 */
    window_tile_data[2] = 0xFF;        /* row 1: color 3 */
    window_tile_data[3] = 0xFF;
    for (unsigned row = 2; row < 8; ++row)
        window_tile_data[row * 2u] = 0xFF; /* remaining rows: color 1 */
    emit_bytes(&p, 0x8010, window_tile_data, sizeof(window_tile_data));
    const uint8_t window_tile = 1;
    emit_bytes(&p, 0x9C00, &window_tile, 1);
    emit_reg(&p, 0x47, 0xE4);
    emit_reg(&p, 0x4A, 1);             /* WY: line 0 remains background */
    emit_reg(&p, 0x4B, 0);             /* WX=0: the first 7 window pixels are clipped */
    memset(expected, 1, sizeof(expected));
    expected[0] = 1;                   /* (0,0), before WY */
    expected[WIDTH] = 2;               /* (0,1): window's clipped local pixel 7, row 0 */
    expected[WIDTH * 2u] = 3;          /* (0,2): window internal line 1 */
    REQUIRE(run_image("window_wx0_wy1_internal_line", &p, 0xF1, expected, 0) == 0);
    return 0;
}

static int frame_composition_sprites(void) {
    guest_program p = {0};
    uint8_t expected[PIXELS];
    uint8_t oam[16] = {
        16, 8, 1, 0,                 /* 8x8 solid color 2 */
        16, 16, 2, 0x30,             /* X flip and OBP1 */
        16, 24, 3, 0x40,             /* Y flip exposes source row 7 */
        16, 32, 5, 0                  /* fourth 8x8 object */
    };
    start_guest(&p);
    emit_solid_tile(&p, 0x8010, 2);
    emit_row_tile(&p, 0x8020, 0, 1, 0x80);
    emit_row_tile(&p, 0x8030, 7, 3, 0xFF);
    emit_solid_tile(&p, 0x8050, 3);
    emit_bytes(&p, 0xFE00, oam, sizeof(oam));
    emit_reg(&p, 0x47, 0xE4);
    emit_reg(&p, 0x48, 0xE4);
    emit_reg(&p, 0x49, 0xE4);
    memset(expected, 0, sizeof(expected));
    for (unsigned y = 0; y < 8; ++y) {
        for (unsigned x = 0; x < 8; ++x) expected[y * WIDTH + x] = 2;
        if (y == 0) expected[y * WIDTH + 15] = 1; /* X flip moves source x=0 to x=15 */
        if (y == 0)
            for (unsigned x = 16; x < 24; ++x) expected[y * WIDTH + x] = 3;
        for (unsigned x = 24; x < 32; ++x) expected[y * WIDTH + x] = 3;
    }
    REQUIRE(run_image("sprites_8x8_flip_palettes", &p, 0x93, expected, 0) == 0);

    memset(&p, 0, sizeof(p));
    start_guest(&p);
    emit_solid_tile(&p, 0x8040, 1);    /* 8x16 mode ignores tile ID bit 0 */
    emit_solid_tile(&p, 0x8050, 3);
    const uint8_t tall_object[] = {16, 8, 5, 0};
    emit_bytes(&p, 0xFE00, tall_object, sizeof(tall_object));
    emit_reg(&p, 0x47, 0xE4);
    emit_reg(&p, 0x48, 0xE4);
    memset(expected, 0, sizeof(expected));
    for (unsigned y = 0; y < 8; ++y)
        for (unsigned x = 0; x < 8; ++x) expected[y * WIDTH + x] = 1;
    for (unsigned y = 8; y < 16; ++y)
        for (unsigned x = 0; x < 8; ++x) expected[y * WIDTH + x] = 3;
    REQUIRE(run_image("sprites_8x16_even_tile", &p, 0x97, expected, 0) == 0);
    return 0;
}

static int frame_composition_priority(void) {
    guest_program p = {0};
    uint8_t expected[PIXELS];
    const uint8_t overlap_oam[] = {
        16, 8, 4, 0,                 /* transparent, but first in OAM */
        16, 16, 1, 0x80,             /* behind nonzero BG */
        16, 12, 2, 0,                 /* smaller X wins in overlap */
        16, 12, 1, 0                  /* equal X loses to lower OAM index */
    };
    start_guest(&p);
    emit_solid_tile(&p, 0x8000, 1);  /* nonzero BG color */
    emit_solid_tile(&p, 0x8010, 2);
    emit_solid_tile(&p, 0x8020, 3);
    emit_bytes(&p, 0xFE00, overlap_oam, sizeof(overlap_oam));
    emit_reg(&p, 0x47, 0xE4);
    emit_reg(&p, 0x48, 0xE7);        /* OBJ color 0 would be shade 3 if not transparent */
    memset(expected, 1, sizeof(expected));
    for (unsigned y = 0; y < 8; ++y)
        for (unsigned x = 4; x < 12; ++x) expected[y * WIDTH + x] = 3;
    REQUIRE(run_image("priority_transparency_x_and_oam", &p, 0x93, expected, 0) == 0);

    memset(&p, 0, sizeof(p));
    start_guest(&p);
    emit_solid_tile(&p, 0x8010, 1);
    emit_solid_tile(&p, 0x8020, 2);
    uint8_t ten[40] = {0};
    for (unsigned i = 0; i < 10; ++i) {
        ten[i * 4u] = 16;
        ten[i * 4u + 1u] = (uint8_t)(8u + i * 8u);
        ten[i * 4u + 2u] = 1;
    }
    uint8_t eleventh[] = {16, 120, 2, 0};
    emit_bytes(&p, 0xFE00, ten, sizeof(ten));
    emit_bytes(&p, 0xFE28, eleventh, sizeof(eleventh));
    emit_reg(&p, 0x47, 0xE4);
    emit_reg(&p, 0x48, 0xE4);
    memset(expected, 0, sizeof(expected));
    for (unsigned y = 0; y < 8; ++y)
        for (unsigned x = 0; x < 80; ++x) expected[y * WIDTH + x] = 1;
    REQUIRE(run_image("priority_ten_objects_per_line", &p, 0x93, expected, 0) == 0);
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    if (strcmp(argv[1], "frame_composition_bg") == 0) return frame_composition_bg();
    if (strcmp(argv[1], "frame_composition_window") == 0) return frame_composition_window();
    if (strcmp(argv[1], "frame_composition_sprites") == 0) return frame_composition_sprites();
    if (strcmp(argv[1], "frame_composition_priority") == 0) return frame_composition_priority();
    return 2;
}
